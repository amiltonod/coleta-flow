# Roadmap & Melhorias — ColetaFlow 🗺️

---

## 📊 Visão Geral

Roadmap em 4 fases, alinhado com padrões de qualidade profissional e escalabilidade.

```
MVP (Atual)          Qualidade           Escalabilidade      Enterprise
    ↓                    ↓                    ↓                  ↓
Sprint 1-2        Sprint 3-4          Sprint 5-6            Sprint 7+
(1-2 semanas)   (2-3 semanas)       (1-2 meses)         (3+ meses)

✅ Segurança       ✅ Logging          ✅ Múltiplos          ✅ Kubernetes
✅ Validação       ✅ Testes           usuários             ✅ Monitoring
✅ Estrutura       ✅ Docs             ✅ PostgreSQL        ✅ Analytics
```

---

## 🔴 **Sprint 1: Segurança & Validação** (4 horas)

**Status:** ⏳ Planejado  
**Prioridade:** 🔴 Crítica  
**Impacto:** Alto

### O que fazer:

#### **1.1 Adicionar validação Pydantic**

Criar schemas para validar entrada nos endpoints POST/PUT.

**Arquivo:** `backend/app/schemas.py` (novo)

```python
from pydantic import BaseModel, Field, validator
from datetime import date
from typing import Optional

class ClienteCreate(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=20)
    nome: str = Field(..., min_length=1, max_length=200)
    cidade: Optional[str] = Field(None, max_length=100)
    unidade: Optional[str] = Field(None, max_length=100)
    observacao: Optional[str] = Field(None, max_length=500)
    frequencia_dias: Optional[int] = Field(None, ge=1, le=365)
    fixo: Optional[bool] = False
    dia_fixo: Optional[str] = None
    
    @validator("codigo")
    def codigo_nao_vazio(cls, v):
        if not v.strip():
            raise ValueError("Código não pode ser vazio")
        return v.strip()

class ClienteUpdate(BaseModel):
    nome: Optional[str] = Field(None, max_length=200)
    cidade: Optional[str] = Field(None, max_length=100)
    unidade: Optional[str] = Field(None, max_length=100)
    observacao: Optional[str] = Field(None, max_length=500)
    frequencia_dias: Optional[int] = Field(None, ge=1, le=365)
    ultima_coleta: Optional[date] = None
    proxima_coleta: Optional[date] = None
    fixo: Optional[bool] = None
    dia_fixo: Optional[str] = None

class ConfirmarColeta(BaseModel):
    data_realizada: date
```

**Uso em rotas:**

```python
# Antes (❌ INSEGURO)
@router.post("/clientes/adicionar")
async def adicionar_cliente(dados: dict, db: Session = Depends(get_db)):
    pass

# Depois (✅ SEGURO)
@router.post("/clientes/adicionar")
async def adicionar_cliente(
    dados: ClienteCreate,  # ← Validado automaticamente
    db: Session = Depends(get_db)
):
    # dados.codigo, dados.nome já validados
    pass
```

**Tempo:** ~1.5h

---

#### **1.2 Padronizar respostas de erro**

Todos os endpoints devem retornar `HTTPException` com status code apropriado.

**Padrão:**

```python
from fastapi import HTTPException

# ✅ BOM
if not cliente:
    raise HTTPException(
        status_code=404,
        detail=f"Cliente {cliente_id} não encontrado"
    )

# ❌ RUIM (evitar)
if not cliente:
    return {"erro": "Cliente não encontrado"}  # Status 200 errado!
```

**Refatorar em:**
- `POST /clientes/adicionar`
- `PUT /clientes/{cliente_id}`
- `DELETE /clientes/{cliente_id}`
- `POST /confirmar-coleta/{schedule_id}`
- `DELETE /programacao/{schedule_id}`

**Tempo:** ~1h

---

#### **1.3 Remover lógica de fechamento duplicada**

Há dois algoritmos fazendo o mesmo:
- `realizar_fechamento_automatico()` em `clientes.py`
- `fechar_semana()` em `services/fechar_semana.py`

**Ação:** Delete `realizar_fechamento_automatico()`, use apenas `fechar_semana()`.

```python
# Em clientes.py, remova essa função (linhas 59-97)
def realizar_fechamento_automatico(db: Session):
    # DELETE THIS

# Na rota GET /, chame a versão de service:
from backend.app.services.fechar_semana import processar_fechamento

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    # Chama serviço em vez de duplicar lógica
    resultado = processar_fechamento(db)
    
    # ... resto do código
```

**Tempo:** ~1.5h

---

### ✅ Checklist Sprint 1

- [ ] Criar `backend/app/schemas.py` com classes Pydantic
- [ ] Atualizar rotas para usar schemas
- [ ] Padronizar todas as respostas de erro em HTTPException
- [ ] Remover `realizar_fechamento_automatico()` de clientes.py
- [ ] Testar manualmente todos endpoints
- [ ] Commit: `feat: adicionar validação pydantic e padronizar erros`

---

## 🟠 **Sprint 2: Performance & Arquitetura** (3 horas)

**Status:** ⏳ Planejado  
**Prioridade:** 🟠 Alta  
**Impacto:** Médio (futuro)

### O que fazer:

#### **2.1 Otimizar query em `programacao_semana`**

**Problema atual:**
```python
schedules = db.query(Schedule).all()  # ← Carrega TUDO
for s in schedules:
    if s.data_coleta in dias_semana:
        resultado[s.data_coleta.isoformat()].append(...)
```

**Solução:**
```python
@router.get("/programacao-semana")
async def programacao_semana(
    offset: int = 0,
    db: Session = Depends(get_db)
):
    hoje = date.today()
    dias_ate_segunda = (7 - hoje.weekday()) % 7 or 7
    segunda_base = hoje + timedelta(days=dias_ate_segunda)
    segunda = segunda_base + timedelta(weeks=offset)
    dias_semana = [segunda + timedelta(days=i) for i in range(5)]

    resultado = {dia.isoformat(): [] for dia in dias_semana}

    # ✅ OTIMIZADO: filtro no banco
    schedules = db.query(Schedule).filter(
        Schedule.data_coleta.in_(dias_semana)
    ).all()
    
    for s in schedules:
        resultado[s.data_coleta.isoformat()].append({
            "id": s.id,
            "codigo": s.codigo_cliente,
            "cliente": s.cliente,
            "unidade": s.unidade or "",
            "status": s.status,
            "fixo": s.fixo or False,
        })

    for dia in resultado:
        resultado[dia].sort(key=lambda x: (not x["fixo"], x["cliente"]))

    return {
        "dias": [d.isoformat() for d in dias_semana],
        "programacao": resultado,
        "offset": offset,
        "semana_atual": offset == -1,
    }
```

**Benefício:** Com 10.000 schedules, reduz de ~2.5s para ~50ms.

**Tempo:** ~30min

---

#### **2.2 Adicionar índices no banco**

Melhorar velocidade de buscas frequentes.

```python
# Em models/client.py
from sqlalchemy import Index

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, nullable=False, index=True)  # ← Busca frequente
    nome = Column(String, nullable=False)
    # ...
    
    __table_args__ = (
        Index('idx_codigo', 'codigo'),  # Busca por código
        Index('idx_fixo', 'fixo'),      # Filtrar fixos
    )

# Em models/schedule.py
class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo_cliente = Column(String, nullable=False, index=True)
    data_coleta = Column(Date, nullable=True, index=True)
    status = Column(String, default="Programado", index=True)
    
    __table_args__ = (
        Index('idx_coleta_data', 'codigo_cliente', 'data_coleta'),
    )
```

**Tempo:** ~1.5h (inclui testes)

---

### ✅ Checklist Sprint 2

- [ ] Refatorar `programacao_semana` com filtro no banco
- [ ] Adicionar índices aos modelos
- [ ] Testar performance com 1.000+ schedules
- [ ] Commit: `perf: otimizar queries e adicionar índices`

---

## 🟡 **Sprint 3: Observabilidade & Auditoria** (3 horas)

**Status:** ⏳ Planejado  
**Prioridade:** 🟡 Média  
**Impacto:** Médio (debugging)

### O que fazer:

#### **3.1 Adicionar logging**

Rastrear ações críticas para debugging.

**Arquivo:** `backend/app/logging_config.py` (novo)

```python
import logging
import logging.handlers

def setup_logging():
    logger = logging.getLogger("coleta_flow")
    logger.setLevel(logging.DEBUG)
    
    # Handler para arquivo
    handler = logging.handlers.RotatingFileHandler(
        filename="backend/app/logs/coleta_flow.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    
    # Formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
```

**Uso em rotas:**

```python
import logging

logger = logging.getLogger("coleta_flow")

@router.post("/confirmar-coleta/{schedule_id}")
async def confirmar_coleta(
    schedule_id: int,
    dados: ConfirmarColeta,
    db: Session = Depends(get_db)
):
    logger.info(f"Confirmando coleta: schedule_id={schedule_id}")
    
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        logger.warning(f"Schedule não encontrado: {schedule_id}")
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    
    logger.debug(f"Status anterior: {schedule.status}")
    schedule.status = "Concluído"
    schedule.data_coleta = dados.data_realizada
    
    # Atualizar cliente
    cliente = db.query(Client).filter(Client.codigo == schedule.codigo_cliente).first()
    if cliente:
        cliente.ultima_coleta = dados.data_realizada
        logger.info(f"Atualizando ultima_coleta para cliente {cliente.codigo}")
    
    db.commit()
    logger.info(f"Coleta confirmada: schedule_id={schedule_id}, status=Concluído")
    
    return {"mensagem": "Coleta confirmada com sucesso"}
```

**Tempo:** ~1.5h

---

#### **3.2 Adicionar timestamps aos modelos**

Rastrear quando registros foram criados/modificados.

```python
# Em models/client.py
from datetime import datetime

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    # ... campos existentes ...
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

# Em models/schedule.py
class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    # ... campos existentes ...
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Em models/controle.py
class Controle(Base):
    __tablename__ = "controle"
    
    id = Column(Integer, primary_key=True)
    ultima_semana_fechada = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Nota:** Após adicionar colunas, o banco será migrado automaticamente na primeira inicialização.

**Tempo:** ~1.5h

---

### ✅ Checklist Sprint 3

- [ ] Criar `backend/app/logging_config.py`
- [ ] Integrar logging em principais endpoints
- [ ] Adicionar colunas `created_at`, `updated_at` em models
- [ ] Testar logging com arquivo em `backend/app/logs/`
- [ ] Commit: `feat: adicionar logging e timestamps de auditoria`

---

## 🟢 **Sprint 4: Testing & Confiabilidade** (4+ horas)

**Status:** ⏳ Planejado  
**Prioridade:** 🟢 Alta  
**Impacto:** Alto (confiança)

### O que fazer:

#### **4.1 Estrutura de testes**

Criar pasta `tests/` com testes unitários e de integração.

```
tests/
├── __init__.py
├── conftest.py                      # Fixtures compartilhadas
├── test_generate_schedule.py        # Testes de geração
├── test_fechar_semana.py            # Testes de fechamento
├── test_import_service.py           # Testes de importação
├── test_routes_clientes.py          # Testes de API
└── fixtures/
    └── sample_data.xlsx
```

---

#### **4.2 Exemplo: Testar geração de programação**

**Arquivo:** `tests/test_generate_schedule.py`

```python
import pytest
from datetime import date, timedelta
from backend.app.models.client import Client
from backend.app.models.schedule import Schedule
from backend.app.services.generate_schedule import (
    gerar_programacao,
    ja_agendado_na_data
)

@pytest.fixture
def db_com_clientes(db_session):
    """Prepara banco com dados de teste"""
    cliente_fixo = Client(
        codigo="L001",
        nome="Cliente Fixo",
        fixo=True,
        dia_fixo="Segunda,Quinta"
    )
    cliente_frequencia = Client(
        codigo="L002",
        nome="Cliente Frequência",
        fixo=False,
        frequencia_dias=7,
        ultima_coleta=date.today() - timedelta(days=7)
    )
    db_session.add(cliente_fixo)
    db_session.add(cliente_frequencia)
    db_session.commit()
    
    return db_session

def test_gerar_programacao_cliente_fixo(db_com_clientes):
    """Testa se cliente fixo é agendado corretamente"""
    resultado = gerar_programacao(db_com_clientes)
    
    assert resultado["gerados"] >= 2  # Pelo menos 2 (segunda e quinta)
    assert resultado["ignorados"] == 0
    
    # Verificar que schedules foram criados
    schedules = db_com_clientes.query(Schedule).filter(
        Schedule.codigo_cliente == "L001"
    ).all()
    assert len(schedules) >= 2

def test_ja_agendado_com_zeros_esquerda(db_com_clientes):
    """Testa se códigos "015" e "15" são tratados como iguais"""
    # Criar agenda para código "15"
    db_com_clientes.add(Schedule(
        codigo_cliente="15",
        data_coleta=date.today()
    ))
    db_com_clientes.commit()
    
    # Verificar se "015" é detectado como duplicado
    assert ja_agendado_na_data(db_com_clientes, "015", date.today())
    assert ja_agendado_na_data(db_com_clientes, "15", date.today())

def test_ignorar_por_solicitacao(db_session):
    """Testa se clientes 'Por solicitação' são ignorados"""
    cliente = Client(
        codigo="L003",
        nome="Cliente Solicitação",
        observacao="Por solicitação",
        fixo=False,
        frequencia_dias=7,
        ultima_coleta=date.today() - timedelta(days=7)
    )
    db_session.add(cliente)
    db_session.commit()
    
    resultado = gerar_programacao(db_session)
    
    # Não deve gerar agendamento para "Por solicitação"
    assert resultado["por_solicitacao"] >= 1
```

**Rodar testes:**
```bash
pytest tests/ -v --cov=backend.app.services
```

**Tempo:** ~2-3h

---

#### **4.3 Exemplo: Testar import de Excel**

**Arquivo:** `tests/test_import_service.py`

```python
import pytest
from pathlib import Path
import openpyxl
from backend.app.services.import_service import importar_clientes_excel

@pytest.fixture
def arquivo_excel_teste(tmp_path):
    """Cria arquivo Excel de teste"""
    arquivo = tmp_path / "clientes_teste.xlsx"
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws['A1'] = "Código"
    ws['B1'] = "Nome"
    ws['C1'] = "Cidade"
    ws['D1'] = "Observação"
    
    ws['A2'] = "L001"
    ws['B2'] = "Cliente Teste"
    ws['C2'] = "Araquari"
    ws['D2'] = ""
    
    wb.save(arquivo)
    return str(arquivo)

def test_importar_clientes_validos(db_session, arquivo_excel_teste):
    """Testa importação de clientes válidos"""
    resultado = importar_clientes_excel(arquivo_excel_teste, db_session)
    
    assert resultado["importados"] >= 1
    assert resultado["erros"] == []
    
    # Verificar que cliente foi criado
    from backend.app.models.client import Client
    cliente = db_session.query(Client).filter_by(codigo="L001").first()
    assert cliente is not None
    assert cliente.nome == "Cliente Teste"

def test_importar_com_duplicados(db_session, arquivo_excel_teste):
    """Testa que duplicados são atualizados, não duplicados"""
    # Primeira importação
    resultado1 = importar_clientes_excel(arquivo_excel_teste, db_session)
    
    # Segunda importação
    resultado2 = importar_clientes_excel(arquivo_excel_teste, db_session)
    
    # Primeira vez: importado
    assert resultado1["importados"] == 1
    # Segunda vez: atualizado
    assert resultado2["atualizados"] == 1
```

**Tempo:** ~1.5h

---

#### **4.4 Configuração de testes**

**Arquivo:** `tests/conftest.py`

```python
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models import client, schedule, controle

@pytest.fixture(scope="function")
def db_session():
    """Cria banco SQLite em memória para testes"""
    engine = create_engine("sqlite:///:memory:")
    
    # Criar tabelas
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()

@pytest.fixture
def client():
    """Cliente HTTP para testes de API"""
    from fastapi.testclient import TestClient
    from backend.app.main import app
    
    return TestClient(app)
```

---

### ✅ Checklist Sprint 4

- [ ] Criar estrutura `tests/`
- [ ] Implementar fixtures em `conftest.py`
- [ ] Escrever testes para `generate_schedule.py` (min 80% coverage)
- [ ] Escrever testes para `import_service.py`
- [ ] Escrever testes para rotas críticas
- [ ] Rodar `pytest` com cobertura
- [ ] Commit: `test: adicionar testes unitários e de integração`

---

## 🚀 **Sprint 5+: Escalabilidade** (Futuro, 1-2 meses)

### **5.1 Migrar para PostgreSQL**

Quando tiver múltiplos usuários simultâneos.

```python
# Mudar apenas uma linha em database.py
# De:
DATABASE_URL = "sqlite:///coletas.db"

# Para:
DATABASE_URL = "postgresql://user:password@localhost/coleta_flow"

# Resto do código fica igual! (SQLAlchemy)
```

---

### **5.2 Adicionar Autenticação & Autorização**

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)):
    token = credentials.credentials
    # Validar token (JWT, OAuth2, etc)
    # ...
    return user

@router.get("/clientes")
async def listar_clientes(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Filtrar por user.empresa_id
    pass
```

---

### **5.3 Docker + CI/CD**

Dockerfile para ambiente reproduzível:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

GitHub Actions para testes automáticos:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov
```

---

## 📈 Timeline Sugerido

| Sprint | Nome | Semanas | Status |
|--------|------|---------|--------|
| 1 | Segurança & Validação | 1 | ⏳ Próximo |
| 2 | Performance | 1 | ⏳ Após Sprint 1 |
| 3 | Observabilidade | 1 | ⏳ Após Sprint 2 |
| 4 | Testes | 2 | ⏳ Após Sprint 3 |
| 5 | Escalabilidade | 4-6 | 🔮 Futuro |

**Total:** ~6 semanas para production-ready.

---

## 🎯 Priorização

Se quiser fazer **apenas 2-3 sprints**, priorize:

1. ✅ **Sprint 1** — Segurança (obrigatório)
2. ✅ **Sprint 4** — Testes (confiança)
3. ✅ **Sprint 3** — Logging (debugging)

---

## 💼 Para o Portfólio

Quando publicar, destaque:
- ✅ Identificação de débitos técnicos
- ✅ Planejamento iterativo
- ✅ Priorização por impacto
- ✅ Execução com testes

Isso mostra pensamento sênior.

---

## 📚 Referências

- **Testing:** https://docs.pytest.org/
- **Logging:** https://docs.python.org/3/library/logging.html
- **PostgreSQL:** https://www.postgresql.org/
- **Docker:** https://docs.docker.com/

---

**Próximo:** Comece com [Sprint 1](#-sprint-1-segurança--validação) agora! 🚀