# ⚡ Quick Reference — Desenvolvimento Rápido

**Guia de bolso para desenvolver em ColetaFlow**

---

## 🚀 Rodar o Projeto

```bash
# Setup (primeira vez)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Rodar servidor
uvicorn backend.app.main:app --reload

# Acessar
http://localhost:8000         # Aplicação
http://localhost:8000/docs    # API Swagger
http://localhost:8000/redoc   # API ReDoc
```

---

## 🧪 Testes

```bash
# Todos os testes
pytest tests/ -v

# Com cobertura (terminal)
pytest tests/ --cov=backend.app --cov-report=term-missing

# Com cobertura (HTML)
pytest tests/ --cov=backend.app --cov-report=html
# Abrir: htmlcov/index.html

# Um teste específico
pytest tests/test_routes_clientes.py::TestAdicionarCliente::test_adiciona_com_dados_validos -v

# Com output (prints, etc)
pytest tests/ -v -s
```

---

## 📁 Estrutura de Pastas

```
backend/app/
├── main.py                 # Entrada FastAPI
├── database.py             # SQLAlchemy config
├── schemas.py              # Validação Pydantic ✨
│
├── models/
│   ├── client.py           # Cliente (com timestamps ✨)
│   ├── schedule.py         # Agendamento (com timestamps ✨)
│   └── controle.py         # Controle
│
├── services/
│   ├── generate_schedule.py # Geração automática
│   ├── fechar_semana.py     # Fechamento
│   └── import_service.py    # Importação Excel
│
├── routes/
│   └── clientes.py         # Endpoints (com logging ✨)
│
├── templates/
│   └── index.html          # Frontend
│
├── static/
│   ├── css/style.css
│   └── js/main.js
│
└── logs/
    └── coleta_flow.log     # Arquivo de logs ✨
```

---

## 🛣️ Rotas Principais

### Clientes
```
GET    /clientes                    # Listar todos
GET    /clientes/buscar?q=termo     # Buscar
GET    /clientes/fixos              # Apenas fixos
POST   /clientes/adicionar          # Criar
PUT    /clientes/{id}               # Atualizar
DELETE /clientes/{id}               # Deletar
POST   /upload                      # Import Excel
```

### Programação
```
GET    /programacao-semana          # Semana (otimizado! ✨)
POST   /gerar-programacao           # Gerar automática
POST   /fechar-semana               # Fechar semana
POST   /confirmar-coleta/{id}       # Confirmar realizada
DELETE /programacao/{id}            # Deletar agendamento
```

---

## 📝 Adicionar Novo Endpoint

### 1. Schema (Pydantic)
```python
# backend/app/schemas.py
class MeuSchema(BaseModel):
    campo_obrigatorio: str = Field(..., min_length=1)
    campo_opcional: Optional[int] = Field(None, ge=1, le=365)
```

### 2. Rota (FastAPI)
```python
# backend/app/routes/clientes.py
import logging
logger = logging.getLogger("coleta_flow")

@router.post("/meu-endpoint", status_code=201)
async def meu_endpoint(dados: MeuSchema, db: Session = Depends(get_db)):
    """Descrição do endpoint"""
    
    logger.info(f"Iniciando ação: {dados.campo_obrigatorio}")
    
    try:
        # Lógica aqui
        resultado = alguma_coisa()
        
        logger.info(f"Sucesso: {resultado}")
        return {"mensagem": "OK", "resultado": resultado}
    
    except Exception as e:
        logger.error(f"Erro: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno")
```

### 3. Teste
```python
# tests/test_meu_endpoint.py
@pytest.mark.integration
def test_meu_endpoint(test_client):
    """Testa novo endpoint"""
    dados = {"campo_obrigatorio": "valor"}
    response = test_client.post("/meu-endpoint", json=dados)
    
    assert response.status_code == 201
    assert "resultado" in response.json()
```

---

## 🗄️ Database

### Verificar Banco
```bash
# Abrir SQLite
sqlite3 backend/app/coletas.db

# Ver tabelas
.tables

# Ver schema
.schema clients

# Query
SELECT * FROM clients LIMIT 5;

# Sair
.quit
```

### Resetar Banco
```bash
# Delete
rm backend/app/coletas.db

# Será recriado vazio na próxima inicialização
```

### Adicionar Campo
```python
# 1. Atualizar model
class Client(Base):
    # ... campos existentes ...
    novo_campo = Column(String, nullable=True)

# 2. Deletar banco (perderá dados)
# rm backend/app/coletas.db

# 3. Rodar servidor
# uvicorn backend.app.main:app --reload
# Banco será recriado com novo campo
```

---

## 🔍 Logging

### Ver Logs
```bash
# Terminal (últimas 50 linhas)
tail -n 50 backend/app/logs/coleta_flow.log

# Abrir arquivo
notepad backend/app/logs/coleta_flow.log  # Windows
open backend/app/logs/coleta_flow.log     # Mac
cat backend/app/logs/coleta_flow.log      # Linux
```

### Escrever Log
```python
import logging
logger = logging.getLogger("coleta_flow")

logger.debug("Detalhes do desenvolvimento")
logger.info("Ação importante")
logger.warning("Algo anômalo mas esperado")
logger.error("Erro que aconteceu", exc_info=True)
```

---

## 🧩 Componentes Principais

### Service: Gerar Programação
```python
# backend/app/services/generate_schedule.py
from backend.app.services.generate_schedule import gerar_programacao

resultado = gerar_programacao(db)
# {
#   "gerados": 15,
#   "ignorados": 2,
#   "duplicados": 0,
#   "por_solicitacao": 1
# }
```

### Service: Fechar Semana
```python
# backend/app/services/fechar_semana.py
from backend.app.services.fechar_semana import fechar_semana

resultado = fechar_semana(db)
# Atualiza ultima_coleta dos clientes
# Registra em Controle.ultima_semana_fechada
```

### Service: Importar Excel
```python
# backend/app/services/import_service.py
from backend.app.services.import_service import importar_clientes

resultado = importar_clientes("caminho/arquivo.xlsx", db)
# {
#   "importados": 10,
#   "atualizados": 5,
#   "erros": []
# }
```

---

## 🐛 Debug

### Print Debug
```python
# Não use prints em produção!
# Use logging!

logger.debug(f"Valor: {valor}")
logger.debug(f"Query: {query}")
logger.debug(f"DB count: {db.query(Client).count()}")
```

### Breakpoint (Desenvolvimento)
```python
# Para na linha e permite inspecionar
breakpoint()

# Ou com pdb
import pdb; pdb.set_trace()

# Então use no terminal:
# (Pdb) p variavel  # Print
# (Pdb) l           # List code
# (Pdb) c           # Continue
```

### Ver SQL Gerado
```python
from sqlalchemy.dialects import sqlite

query = db.query(Client).filter(Client.codigo == "L001")
print(query.statement.compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True}))
```

---

## 📦 Dependências

### Ver instaladas
```bash
pip list
```

### Atualizar requirements.txt
```bash
pip freeze > requirements.txt
```

### Instalar nova dependência
```bash
pip install novo-pacote
pip freeze > requirements.txt
```

---

## 🔗 Git Workflow

```bash
# Clone (primeira vez)
git clone https://github.com/amiltonod/coleta-flow.git
cd coleta-flow

# Criar branch
git checkout -b feature/minha-feature

# Develop... (fazer mudanças)

# Verificar mudanças
git status

# Adicionar e commit
git add .
git commit -m "feat: descrição clara da mudança"

# Push
git push origin feature/minha-feature

# Abrir Pull Request no GitHub
```

### Commit Messages (Convenção)
```
feat:  nova feature
fix:   bug fix
docs:  documentação
test:  testes
perf:  performance
refactor: refatoração
style: formatação
chore: atualização deps
ci:    CI/CD
```

**Exemplo:**
```
git commit -m "feat: adicionar validação em novo endpoint"
git commit -m "fix: corrigir bug na geração de programação"
git commit -m "test: adicionar testes para schema ClienteCreate"
```

---

## 🎯 Common Tasks

### Adicionar Novo Cliente via API
```bash
curl -X POST http://localhost:8000/clientes/adicionar \
  -H "Content-Type: application/json" \
  -d '{
    "codigo": "L999",
    "nome": "Novo Cliente",
    "cidade": "Araquari",
    "frequencia_dias": 7
  }'
```

### Listar Clientes
```bash
curl http://localhost:8000/clientes
```

### Buscar Cliente
```bash
curl "http://localhost:8000/clientes/buscar?q=ABC"
```

### Importar Excel
```bash
# Via interface: http://localhost:8000
# Upload do arquivo .xlsx
```

### Gerar Programação
```bash
curl -X POST http://localhost:8000/gerar-programacao
```

### Confirmar Coleta
```bash
curl -X POST http://localhost:8000/confirmar-coleta/1 \
  -H "Content-Type: application/json" \
  -d '{"data_realizada": "2026-06-11"}'
```

---

## 📊 Performance

### Benchmarking
```bash
# Instalar
pip install locust

# Criar arquivo locustfile.py
# Rodar
locust -f locustfile.py --host=http://localhost:8000
```

### Ver SQL Lento
```python
# Em logging_config.py, adicionar:
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Ver queries SQL no console
```

---

## 🔐 Segurança

### Validações já implementadas
- ✅ Pydantic (tipo, tamanho)
- ✅ HTTP (status codes corretos)
- ✅ SQL Injection (SQLAlchemy)
- ✅ Anti-duplicidade (triple layer)

### Para adicionar (Phase 2)
- [ ] Authentication (JWT/OAuth2)
- [ ] CORS
- [ ] Rate limiting
- [ ] HTTPS

---

## 📚 Arquivos Importantes

| Arquivo | Descrição | Editar? |
|---------|-----------|---------|
| `main.py` | Entrada | ⚠️ Cuidado |
| `database.py` | DB config | ⚠️ Cuidado |
| `schemas.py` | Validação | ✅ Sim |
| `routes/clientes.py` | Endpoints | ✅ Sim |
| `services/*.py` | Lógica | ✅ Sim |
| `models/*.py` | ORM | ⚠️ Cuidado |
| `requirements.txt` | Deps | ✅ Sim |
| `tests/*.py` | Testes | ✅ Sim |

---

## 🚨 Erros Comuns

### `ModuleNotFoundError: No module named 'fastapi'`
```bash
pip install -r requirements.txt
```

### `Port 8000 already in use`
```bash
# Use outra porta
uvicorn backend.app.main:app --reload --port 8001

# Ou mate processo
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill
```

### `sqlite3.OperationalError: no such table`
```bash
# Banco vazio/corrompido
rm backend/app/coletas.db
# Será recriado
```

### Teste falha com `fixture 'db_session' not found`
```bash
# conftest.py não está em tests/
# Copie: tests/conftest.py
```

---

## 💡 Tips & Tricks

### Reload automático + debugger
```bash
# No PyCharm/VSCode
# F5 ou Run → Debug
# Breakpoint funcionará
```

### Ignorar arquivos no Git
```bash
# .gitignore já tem:
*.pyc
__pycache__/
*.db
venv/
.DS_Store
htmlcov/
.pytest_cache/
```

### Formatar código
```bash
# Instalar
pip install black

# Formatar
black backend/app/
```

### Lint
```bash
# Instalar
pip install flake8

# Verificar
flake8 backend/app/
```

---

<div align="center">

**ColetaFlow Quick Reference**

*Desenvolvendo rápido, com confiança*

</div>