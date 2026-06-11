# Arquitetura — ColetaFlow 🏗️
 
---
 
## 📐 Visão Geral
 
ColetaFlow é um **sistema web monolítico** estruturado em camadas, separando apresentação, lógica de negócio e persistência de dados.
 
```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (HTML/JS)                      │
│            (Grade semanal, drag & drop, forms)           │
└──────────────────────┬──────────────────────────────────┘
                       │ (Fetch API, JSON)
                       ↓
┌─────────────────────────────────────────────────────────┐
│              FastAPI Application                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Routes (clientes.py)                            │   │
│  │  • GET /programacao-semana                       │   │
│  │  • POST /clientes/adicionar                      │   │
│  │  • PUT /clientes/{id}                            │   │
│  │  • DELETE /programacao/{id}                      │   │
│  └──────────────────────────────────────────────────┘   │
│                       ↓                                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Services (Lógica de Negócio)                    │   │
│  │  • generate_schedule.py → Gera programação      │   │
│  │  • fechar_semana.py → Finaliza semana          │   │
│  │  • import_service.py → Importa Excel            │   │
│  └──────────────────────────────────────────────────┘   │
│                       ↓                                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Models (ORM - SQLAlchemy)                       │   │
│  │  • Client → Tabela clients                       │   │
│  │  • Schedule → Tabela schedules                   │   │
│  │  • Controle → Tabela controle                    │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │ (SQL)
                       ↓
┌─────────────────────────────────────────────────────────┐
│               SQLite Database                            │
│  • coletas.db (persiste em disco)                       │
└─────────────────────────────────────────────────────────┘
```
 
---
 
## 📂 Estrutura de Pastas
 
```
coleta-flow/
│
├── backend/
│   └── app/
│       ├── __init__.py
│       ├── main.py                 # Ponto de entrada FastAPI
│       ├── database.py             # Configuração SQLAlchemy + get_db
│       │
│       ├── models/                 # Camada de Dados (ORM)
│       │   ├── __init__.py
│       │   ├── client.py           # Modelo Client
│       │   ├── schedule.py         # Modelo Schedule
│       │   └── controle.py         # Modelo Controle
│       │
│       ├── services/               # Camada de Negócio
│       │   ├── __init__.py
│       │   ├── generate_schedule.py    # Geração de programação
│       │   ├── fechar_semana.py       # Fechamento automático
│       │   └── import_service.py      # Importação Excel
│       │
│       ├── routes/                 # Camada de API (HTTP)
│       │   ├── __init__.py
│       │   └── clientes.py         # Rotas REST
│       │
│       ├── templates/              # Frontend
│       │   └── index.html
│       │
│       ├── static/                 # CSS, JS, imagens
│       │   ├── css/
│       │   ├── js/
│       │   └── images/
│       │
│       ├── uploads/                # Diretório temporário de Excel
│       │
│       └── coletas.db              # Banco SQLite (gerado automaticamente)
│
├── docs/                           # Documentação
│   ├── ARCHITECTURE.md             # Este arquivo
│   ├── SETUP.md                    # Como configurar
│   ├── API.md                      # Referência de endpoints
│   ├── CODE_REVIEW.md              # Análise de código
│   └── ROADMAP.md                  # Plano de melhorias
│
├── .gitignore
├── README.md
└── requirements.txt
```
 
---
 
## 🔑 Decisões Técnicas
 
### 1. **Por que FastAPI?**
 
| Critério | FastAPI | Django | Flask |
|----------|---------|--------|-------|
| Validação automática | ✅ Pydantic | ⚠️ Manual | ⚠️ Manual |
| Documentação OpenAPI | ✅ Automática | ⚠️ Plugins | ❌ Nenhuma |
| Performance | ✅ ~3x Flask | ⚠️ Mais lento | ⚠️ Mais lento |
| Curva de aprendizado | ✅ Rápida | ❌ Longa | ✅ Rápida |
| Tamanho | ✅ Mínimo | ❌ Pesado | ✅ Mínimo |
 
**Escolha:** FastAPI minimiza boilerplate, força boas práticas, e é rápido.
 
---
 
### 2. **Por que SQLite?**
 
| Caso | SQLite | PostgreSQL | MySQL |
|------|--------|-----------|-------|
| **MVP/Prototipo** | ✅ Perfeito | ⚠️ Overkill | ⚠️ Overkill |
| **Deploy simples** | ✅ Um arquivo | ❌ Servidor externo | ❌ Servidor externo |
| **Sem infraestrutura** | ✅ Sim | ❌ Precisa DB server | ❌ Precisa DB server |
| **Escalabilidade** | ❌ Até ~10GB | ✅ Ilimitada | ✅ Ilimitada |
| **Concorrência pesada** | ⚠️ Limitada | ✅ Sim | ✅ Sim |
 
**Escolha:** SQLite é perfeito para MVP em uma empresa. Quando escalar para múltiplos usuários simultâneos, migra para PostgreSQL.
 
**Migração futura será fácil** porque usamos SQLAlchemy (agnostic ao banco).
 
---
 
### 3. **Por que separar Services?**
 
**Arquitetura sem Services (❌ BAD):**
```python
@router.post("/gerar-programacao")
async def processar_geracao_automatica(db: Session = Depends(get_db)):
    # 100+ linhas de lógica de negócio aqui
    # Impossível testar sem HTTP
    # Impossível reutilizar
    pass
```
 
**Arquitetura com Services (✅ GOOD):**
```python
# services/generate_schedule.py
def gerar_programacao(db: Session) -> dict:
    # Lógica pura, testável, reutilizável
    pass
 
# routes/clientes.py
@router.post("/gerar-programacao")
async def processar_geracao_automatica(db: Session = Depends(get_db)):
    resultado = gerar_programacao(db)
    return resultado
```
 
**Benefícios:**
- ✅ Testável com pytest (sem mock de HTTP)
- ✅ Reutilizável (pode chamar de CLI, jobs, etc)
- ✅ Fácil de debugar
- ✅ Responsabilidade clara
---
 
### 4. **Por que Dependency Injection com `get_db()`?**
 
**Sem DI (❌ BAD):**
```python
def buscar_clientes():
    engine = create_engine(...)  # Novo a cada chamada
    session = Session(engine)
    # ...
    session.close()  # Fácil esquecer
```
 
**Com DI (✅ GOOD):**
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # Garantido
 
@router.get("/clientes")
async def listar_clientes(db: Session = Depends(get_db)):
    # FastAPI injeta db, garante limpeza
    pass
```
 
**Benefícios:**
- ✅ Sessão sempre limpa (finally garante)
- ✅ Uma única engine compartilhada
- ✅ Fácil mockar em testes
- ✅ FastAPI gerencia automaticamente
---
 
### 5. **Caminho Absoluto para o Banco**
 
**Problema sem isso (❌ BAD):**
```python
DATABASE_URL = "sqlite:///coletas.db"  # Relativo
# Se rodar de outro diretório, quebra
```
 
**Solução (✅ GOOD):**
```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "coletas.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
 
# Sempre fica em app/coletas.db, independente de onde roda
```
 
---
 
### 6. **Triple-Layer Anti-Duplicidade**
 
Garante que **nunca** agende um cliente 2x no mesmo dia:
 
1. **Camada de Negócio** (`generate_schedule.py`):
```python
   if ja_agendado_na_data(db, cliente.codigo, data_coleta):
       duplicados += 1
       continue  # Pula se já existe
```
 
2. **Camada de API** (`clientes.py`, adicionar manualmente):
```python
   if ja_agendado_na_data(db, dados.codigo_cliente, data_dt):
       raise HTTPException(status_code=400, detail="Já agendado")
```
 
3. **Camada de BD** (índice único no banco):
```python
   # Futura melhoria:
   class Schedule(Base):
       __table_args__ = (
           UniqueConstraint('codigo_cliente', 'data_coleta', name='uc_cliente_data'),
       )
```
 
**Por que 3 camadas?**
- Cada uma protege de um tipo diferente de bug
- Se uma falha, outras ainda seguram
- Defensão em profundidade
---
 
## 🔄 Fluxo de Dados
 
### **Caso 1: Importar Excel**
 
```
User seleciona arquivo.xlsx
    ↓
POST /upload (file stream)
    ↓
Routes: upload_file()
    ↓
Services: importar_clientes(file_path, db)
    - Lê com Pandas
    - Parse de campos compostos (nome - cidade - unidade)
    - Upsert por código (update se existe, insert se novo)
    ↓
Models: Client criados/atualizados
    ↓
SQLite: INSERT/UPDATE na tabela clients
    ↓
Response: {"importados": 5, "atualizados": 2, "erros": []}
    ↓
Frontend: Mostra alerta de sucesso
```
 
---
 
### **Caso 2: Gerar Programação Automática**
 
```
User clica "Gerar Programação"
    ↓
POST /gerar-programacao (sem body)
    ↓
Routes: processar_geracao_automatica(db)
    ↓
Services: gerar_programacao(db)
    - Loop cada cliente
    - Se fixo: agendas nos dias fixos
    - Se frequência: ultima_coleta + dias
    - Ajusta para dia útil (pula fim de semana)
    - Valida anti-duplicidade
    ↓
Models: Schedule criados
    ↓
SQLite: INSERT na tabela schedules
    ↓
Response: {"gerados": 15, "ignorados": 3, "duplicados": 0}
    ↓
Frontend: Atualiza grid com novas coletas
```
 
---
 
### **Caso 3: Confirmar Coleta Realizada**
 
```
User clica botão "✓ Concluído" na grade
    ↓
POST /confirmar-coleta/{schedule_id}
    ↓
Routes: confirmar_coleta(schedule_id, data_realizada)
    ↓
Models:
  - Schedule.status = "Concluído"
  - Client.ultima_coleta = data_realizada
  - Client.proxima_coleta = ultima_coleta + frequencia_dias
    ↓
SQLite: UPDATE schedules + clients
    ↓
Response: {"mensagem": "Coleta confirmada com sucesso"}
    ↓
Frontend: Mostra visual de sucesso, atualiza grid
```
 
---
 
## 🔐 Segurança (Atual vs Ideal)
 
| Aspecto | Status Atual | Ideal | Prioridade |
|--------|------------|--------|-----------|
| Validação de entrada | ⚠️ Dict genérico | ✅ Pydantic | 🔴 Alta |
| SQL Injection | ✅ SQLAlchemy (safe) | ✅ Mantém | ✅ OK |
| Autenticação | ❌ Nenhuma | ✅ JWT/Session | 🟡 Média |
| Rate limiting | ❌ Nenhum | ✅ Middleware | 🟡 Média |
| CORS | ✅ Padrão (localhost) | ✅ Restritivo | 🟡 Média |
| Logs de auditoria | ❌ Nenhum | ✅ Logger | 🟡 Média |
 
---
 
## 🚀 Plano de Escalabilidade
 
### **Fase 1: MVP (ATUAL)**
- ✅ SQLite
- ✅ Monolito FastAPI
- ✅ 1 usuário por vez
- ✅ Deploy simples (1 arquivo .vbs)
### **Fase 2: Múltiplos Usuários** (~6-12 meses)
```python
# Migrar para PostgreSQL
DATABASE_URL = "postgresql://user:pass@localhost/coleta_flow"
# Resto do código fica igual (thanks SQLAlchemy!)
 
# Adicionar autenticação
@router.get("/clientes")
async def listar_clientes(
    user: User = Depends(get_current_user),  # ← Novo
    db: Session = Depends(get_db)
):
    # Filtrar por user.empresa_id
    pass
```
 
### **Fase 3: Múltiplas Empresas** (~18+ meses)
- Adicionar coluna `empresa_id` em todos os modelos
- Multi-tenancy (isolamento de dados)
- Dashboard admin
### **Fase 4: Kubernetes** (~24+ meses, se necessário)
- Containerizar com Docker
- Orquestração com K8s
- Cache com Redis
- Fila com Celery
---
 
## 📊 Decisões de Performance
 
### **Índices no Banco**
 
```python
# Futuro: adicionar em models/
class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, nullable=False, index=True)  # ← Busca rápida
    nome = Column(String, nullable=False)
    # ...
 
class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo_cliente = Column(String, nullable=False, index=True)  # ← FK lookup
    data_coleta = Column(Date, nullable=True, index=True)  # ← Range queries
```
 
### **Caching**
 
Futura otimização (não é preciso agora):
```python
from functools import lru_cache
 
@lru_cache(maxsize=128)
def get_dias_semana():
    return {
        0: "Segunda", 1: "Terça", ...
    }
```
 
---
 
## 🧪 Testabilidade
 
Cada camada é testável independentemente:
 
```python
# test_generate_schedule.py
def test_gerar_programacao_cliente_fixo(db_session):
    cliente = Client(
        codigo="L001",
        nome="Test",
        fixo=True,
        dia_fixo="Segunda,Quinta"
    )
    db_session.add(cliente)
    db_session.commit()
    
    resultado = gerar_programacao(db_session)
    
    assert resultado["gerados"] == 2
    assert resultado["solicitacao"] == 0
 
# test_routes.py (integração)
def test_upload_endpoint(client, tmp_path):
    arquivo = tmp_path / "clientes.xlsx"
    # ... criar arquivo mock ...
    
    response = client.post("/upload", files={"file": arquivo})
    assert response.status_code == 200
```
 
---
 
## 🎓 Aprendizados Arquiteturais
 
### O que este projeto ensina:
 
1. **Separação de Responsabilidades** ← Cada camada tem um job
2. **Dependency Injection** ← Código desacoplado, testável
3. **ORM (SQLAlchemy)** ← Abstração de banco agnóstica
4. **Validação com Pydantic** ← Type-safety no Python
5. **FastAPI Modernos** ← Async/await, automatizado
6. **Lógica de Negócio** ← Tratamento de edge cases (zeros à esquerda, "Por solicitação")
---
 
## 📖 Referências & Recursos
 
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **SQLAlchemy ORM:** https://docs.sqlalchemy.org/en/20/orm/
- **Pydantic:** https://docs.pydantic.dev
- **Clean Architecture:** https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
---
 
**Próximo:** Veja [SETUP.md](./SETUP.md) para instruções de instalação.