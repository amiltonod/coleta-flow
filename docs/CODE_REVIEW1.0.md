# Code Review — ColetaFlow 🔍
 
**Projeto:** Sistema de Programação de Coletas de Resíduos  
**Data:** Junho 2026  
**Escopo:** Backend (FastAPI), Models, Services, Routes  
**Versão analisada:** main / refatoracao
 
---
 
## 📋 Executive Summary
 
O ColetaFlow é um projeto **bem estruturado e funcional** com arquitetura clara em camadas. O código demonstra compreensão sólida de padrões FastAPI e SQLAlchemy. Identificamos oportunidades para melhorar robustez, testabilidade e manutenibilidade — típicas de um projeto em transição de Nível 1 (funcionamento) para Nível 2 (production-ready).
 
**Pontuação geral: 7.5/10**
 
---
 
## ✅ Fortalezas
 
### 1. **Arquitetura em Camadas Bem Definida**
- ✓ Separação clara: `models/` → `services/` → `routes/`
- ✓ Dependency injection (`get_db`) implementada corretamente
- ✓ Caminho absoluto do banco via `os.path.abspath()` evita bugs de path relativo
**Código exemplar:**
```python
# database.py — robusto e portável
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "coletas.db")
```
 
### 2. **Lógica de Negócio Defensiva**
- ✓ **Triple-layer anti-duplicidade**: na geração automática, adição manual e replicação
- ✓ Validação robusta de "Por solicitação" com fallback de checagem (obs + dia_fixo)
- ✓ Tratamento inteligente de códigos com zeros à esquerda:
```python
cod_limpo = str(codigo).strip()
cod_alternativo = str(int(cod_limpo)) if cod_limpo.isdigit() else cod_limpo
```
 
### 3. **Tratamento de Dados Sensível**
- ✓ `import_service.py` usa `pd.to_datetime(..., errors="coerce")` para datas inválidas
- ✓ Validação de integridade com `try/except/rollback`
- ✓ Upsert inteligente: atualiza se existe, insere se novo — nunca duplica
### 4. **Lógica de Fechamento Automático**
- ✓ Funciona em segundo plano no carregamento (`/` route)
- ✓ Marca semanas como fechadas para evitar reprocessamento
- ✓ Recalcula `proxima_coleta` com base em frequência
---
 
## ⚠️ Problemas Críticos
 
### 1. **Falta de Validação de Entrada (Input Validation)**
 
**Problema:** Endpoints POST/PUT recebem `dict` genéricos sem Pydantic validation.
 
```python
# ❌ INSEGURO — clientes.py, linhas 216-256
@router.put("/clientes/{cliente_id}")
async def atualizar_cliente(
    cliente_id: int,
    dados: dict,  # ← Aceita QUALQUER coisa
    db: Session = Depends(get_db)
):
```
 
**Risco:** 
- Injection de campos não esperados
- Sem coerção de tipo
- Sem limite de tamanho
**Solução:**
```python
class ClienteUpdate(BaseModel):
    nome: Optional[str] = None
    cidade: Optional[str] = None
    unidade: Optional[str] = None
    observacao: Optional[str] = None
    frequencia_dias: Optional[int] = None
    ultima_coleta: Optional[date] = None
    
    class Config:
        max_any_str_length = 200  # Limita strings
 
@router.put("/clientes/{cliente_id}")
async def atualizar_cliente(
    cliente_id: int,
    dados: ClienteUpdate,  # ← Validado
    db: Session = Depends(get_db)
):
```
 
**Impacto:** 🔴 Alto — Abre porta a bugs de type mismatch e potencial SQL injection
 
---
 
### 2. **Ausência de HTTP Exception Consistency**
 
**Problema:** Alguns endpoints retornam `{"erro": "..."}`, outros usam `HTTPException`.
 
```python
# ❌ INCONSISTENTE — clientes.py
# Linha 223: retorna dict
if not cliente:
    return {"erro": "Cliente não encontrado"}
 
# Linha 283: lança exception
if not cliente:
    raise HTTPException(status_code=404, detail="Cliente não encontrado")
```
 
**Risco:**
- Cliente frontend não sabe como tratar erro
- Código HTTP inesperado (200 em vez de 404)
- Difícil manutenção
**Solução:** Padronize em **todas** as rotas:
```python
@router.put("/clientes/{cliente_id}")
async def atualizar_cliente(...):
    cliente = db.query(Client).filter(...).first()
    if not cliente:
        raise HTTPException(
            status_code=404,
            detail=f"Cliente {cliente_id} não encontrado"
        )
```
 
**Impacto:** 🟠 Médio — Afeta integração frontend e debugging
 
---
 
### 3. **Lógica de Fechamento Automático Redundante**
 
**Problema:** Há **dois** algoritmos de fechamento:
1. `realizar_fechamento_automatico()` em `clientes.py` (linhas 59–97)
2. `fechar_semana()` em `services/fechar_semana.py` (linhas 13–88)
Ambos fazem essencialmente a mesma coisa com diferenças sutis:
 
```python
# ❌ DUPLICADO — clientes.py (linhas 59-97)
def realizar_fechamento_automatico(db: Session):
    # ... mesma lógica que fechar_semana.py
    # Sem registrar em Controle
    
# ✓ EM SERVIÇO — services/fechar_semana.py
def fechar_semana(db: Session):
    # ... mesma lógica + registro em Controle
```
 
**Risco:**
- Bugs diferindo entre dois caminhos
- Código não-DRY
- Confusão sobre qual usar
**Solução:**
```python
# Em clientes.py, linha 104:
@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    # Use apenas a versão de serviço
    resultado = processar_fechamento(db)
    # Não precisa fazer nada com resultado; é silencioso
    
    clientes = db.query(Client).all()
    schedules = db.query(Schedule).all()
    fixos = db.query(Client).filter(Client.fixo == True).all()
    return templates.TemplateResponse(
        name="index.html",
        request=request,
        context={"clientes": clientes, "schedules": schedules, "fixos": fixos}
    )
 
# Delete realizar_fechamento_automatico() completamente
```
 
**Impacto:** 🟠 Médio — Risco de inconsistência lógica
 
---
 
### 4. **N+1 Query Problem em `programacao_semana`**
 
**Problema:** Linha 147-149 carrega **todos** os schedules do banco, depois filtra em Python:
 
```python
# ❌ INEFICIENTE — clientes.py, linha 147-149
schedules = db.query(Schedule).all()  # ← Carrega TUDO
for s in schedules:
    if s.data_coleta and s.data_coleta in dias_semana:  # ← Filtra em Python
        resultado[s.data_coleta.isoformat()].append({...})
```
 
**Risco:**
- Com 10.000 schedules, carrega tudo na memória
- Lentidão com crescimento de dados
- Falha silenciosa se banco ficar grande
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
 
    resultado = {}
    for dia in dias_semana:
        resultado[dia.isoformat()] = []
 
    # ✓ FILTRADO NO BANCO
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
 
**Impacto:** 🟡 Médio (por enquanto) — Será crítico com dados maiores
 
---
 
### 5. **Sem Logging ou Auditoria**
 
**Problema:** Não há registro de mudanças críticas:
 
```python
# ❌ SEM LOG
@router.post("/confirmar-coleta/{schedule_id}")
async def confirmar_coleta(
    schedule_id: int,
    dados: dict,
    db: Session = Depends(get_db)
):
    # ... atualiza ultima_coleta, mas ninguém sabe quem, quando, o quê antes
    schedule.status = "Concluído"
    schedule.data_coleta = data_realizada
    db.commit()
    return {"mensagem": "Coleta confirmada com sucesso"}
```
 
**Risco:**
- Impossível rastrear quem mudou o quê
- Debug de bugs de dados fica impossível
- Não-conformidade com boas práticas
**Solução:**
```python
import logging
logger = logging.getLogger("coleta_flow")
 
@router.post("/confirmar-coleta/{schedule_id}")
async def confirmar_coleta(...):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        logger.warning(f"Tentativa de confirmar schedule inexistente: {schedule_id}")
        return {"erro": "Agendamento não encontrado"}
    
    logger.info(f"Confirmar coleta: schedule_id={schedule_id}, status={schedule.status} → Concluído")
    schedule.status = "Concluído"
    schedule.data_coleta = data_realizada
    db.commit()
```
 
**Impacto:** 🟡 Médio — Afeta manutenibilidade e debugging
 
---
 
## 🟡 Questões de Design
 
### 1. **Falta de Testes Unitários**
 
Não há testes para:
- `generate_schedule.py` (lógica complexa de datas)
- `fechar_semana.py` (Estado do controle)
- `import_service.py` (Parsing e upsert)
**Recomendação:**
```bash
# Estrutura sugerida
coleta-flow/
├── tests/
│   ├── test_generate_schedule.py
│   ├── test_fechar_semana.py
│   ├── test_import_service.py
│   └── conftest.py  # Fixtures compartilhadas
```
 
**Exemplo:**
```python
# tests/test_generate_schedule.py
import pytest
from datetime import date, timedelta
from backend.app.models.client import Client
from backend.app.services.generate_schedule import ja_agendado_na_data
 
def test_ja_agendado_codigo_com_zeros_esquerda(db_session):
    """Testa se códigos "015" e "15" são tratados como iguais"""
    # Setup
    client = Client(codigo="15", nome="Test")
    db_session.add(client)
    db_session.commit()
    
    # Teste
    assert ja_agendado_na_data(db_session, "015", date.today()) == False
```
 
**Impacto:** 🟡 Médio — Fundamental para refactoring com segurança
 
---
 
### 2. **Formato de Data Hardcoded na Frontend**
 
Cliente assume sempre `ISO 8601` (YYYY-MM-DD), mas Python pode retornar outros formatos:
 
```python
# ❌ FRÁGIL — clientes.py, linha 240
cliente.ultima_coleta = date.fromisoformat(dados["ultima_coleta"])
```
 
**Recomendação:** Documente ou use Pydantic `validator`:
```python
from pydantic import field_validator
 
class ClienteUpdate(BaseModel):
    ultima_coleta: Optional[date] = None
    
    @field_validator("ultima_coleta", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            try:
                return date.fromisoformat(v)
            except ValueError:
                raise ValueError(f"Data deve estar em ISO 8601: {v}")
        return v
```
 
**Impacto:** 🟡 Baixo (por enquanto) — Será issue com timezone/locale
 
---
 
### 3. **Modelo `Schedule` Sem Timestamps**
 
```python
# ❌ SEM RASTREABILIDADE — models/schedule.py
class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    # ... sem created_at, updated_at, deleted_at
```
 
**Recomendação:**
```python
from datetime import datetime
from sqlalchemy import DateTime
 
class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    # ... campos existentes ...
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete
```
 
**Impacto:** 🟡 Baixo — Boa prática para auditoria
 
---
 
## 🟢 Recomendações Positivas
 
### 1. **Padrão de Tratamento de Erro em Import**
 
```python
# ✓ BOM — import_service.py, linhas 79-80
except Exception as e:
    erros.append({"linha": index, "erro": str(e)})
```
Continua importando mesmo com erros. Muito bom para robustez.
 
### 2. **Uso de Enums para Dias da Semana**
 
```python
# ✓ BOM — clientes.py, linhas 31-34
DIAS_SEMANA = {
    0: "Segunda", 1: "Terça", 2: "Quarta", 
    3: "Quinta", 4: "Sexta", 5: "Sábado", 6: "Domingo"
}
```
Centralizado e reutilizável. Considere elevar a constante global.
 
### 3. **Calcular `dia_semana` Automaticamente**
 
```python
# ✓ BOM — generate_schedule.py, linha 104
dia_semana=dia_nome.strip().capitalize()
```
Evita divergências manuais.
 
---
 
## 📊 Matriz de Problemas vs Impacto
 
| Problema | Severidade | Impacto | Esforço Fix |
|----------|-----------|--------|------------|
| Falta validação Pydantic | 🔴 Alto | Security/stability | 2h |
| HTTP status code inconsistente | 🟠 Médio | Integração | 1h |
| Lógica fechamento duplicada | 🟠 Médio | Maintainability | 1.5h |
| N+1 query | 🟡 Médio | Performance (futuro) | 30min |
| Sem logging | 🟡 Médio | Debug | 1h |
| Sem testes | 🟡 Médio | Confidence | 4h+ |
| Sem timestamps | 🟡 Baixo | Auditoria | 1h |
 
---
 
## 🎯 Plano de Ação (Priorizado)
 
### Sprint 1 (Segurança & Stabilidade) — 4 horas
1. **Adicionar Pydantic schemas para todos os PUT/POST**
   - `ClienteUpdate`, `ScheduleUpdate`, `ConfirmarColeta`
   - Valida tipo, tamanho, formato
   
2. **Padronizar respostas de erro**
   - Sempre `HTTPException` com status code apropriado
   - Mensagens consistentes
### Sprint 2 (Qualidade & Performance) — 3 horas
3. **Remover fechamento duplicado**
   - Delete `realizar_fechamento_automatico()` de clientes.py
   - Use apenas `fechar_semana()` de services
4. **Otimizar query em `programacao_semana`**
   - Filtrar no banco, não em Python
### Sprint 3 (Observability) — 3 horas
5. **Adicionar logging**
   - Configuração centralizada
   - Log de ações críticas (confirmar, excluir, atualizar)
6. **Adicionar timestamps aos modelos**
   - `created_at`, `updated_at`
### Sprint 4 (Testing) — 4+ horas
7. **Escrever testes unitários**
   - Mínimo: 80% coverage de `services/`
   - Use pytest + pytest-sqlalchemy
---
 
## 📈 Próximos Passos para Portfólio
 
1. **Documentação de API**
   - Adicione docstrings a cada rota (OpenAPI auto-gera)
   - Exemplo:
```python
   @router.get("/clientes/buscar")
   async def buscar_clientes(q: str, db: Session = Depends(get_db)):
       """
       Busca clientes por nome ou código.
       
       Args:
           q: String de busca (min 2 caracteres)
           
       Returns:
           Lista de clientes com campos codigo e nome
           
       Example:
           GET /clientes/buscar?q=Ambiental
       """
```
 
2. **Docker + GitHub Actions**
   - Dockerfile para reproduzibilidade
   - CI/CD para rodar testes automaticamente
3. **Alerta de Erro no Frontend**
   - Mostre `detail` do erro para o usuário (não stack trace)
   - Tente novamente com exponential backoff
4. **Versionamento de API**
   - Use `/v1/` nas rotas para facilitar evolução futura
---
 
## 💡 Aprendizados Transferíveis
 
Este projeto demonstra bem:
- ✓ Separação de responsabilidades (models/services/routes)
- ✓ Dependency injection com FastAPI
- ✓ ORM com SQLAlchemy
- ✓ Validação de dados com Pydantic
- ✓ Testes de integração com banco de dados
Para **demonstrar no portfólio**, enfatize:
1. **Como você pensou em edge cases** (códigos com zeros, validação de "Por solicitação")
2. **Decisões arquitetônicas** (por que separou services?)
3. **Trade-offs considerados** (SQLite vs. PostgreSQL, quando escalar)
---
 
## 📝 Conclusão
 
**ColetaFlow é um projeto sólido que mostra compreensão real de negócio + código bem estruturado.** Os problemas identificados são típicos de um MVP evoluindo para production, e todos têm fix claro.
 
Seu **diferencial** é ter construído algo que **realmente resolve um problema** (automation de planejamento semanal). Isso vale mais do que code perfection.
 
**Próximo passo:** Escolha **2-3 problemas** acima (de preferência dos Sprints 1 e 2), fix com TDD, commite com mensagem descritiva e atualize o portfolio.
 
---
 
**Review realizado em:** 11 de Junho de 2026  
**Revisor:** Claude (Anthropic)