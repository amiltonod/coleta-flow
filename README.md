# ColetaFlow 🚛

[![FastAPI](https://img.shields.io/badge/FastAPI-0.136.3-009688?style=flat)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.8+-3776ab?style=flat)](https://www.python.org)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat)](https://www.sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](#)

Sistema inteligente de **programação de coletas de resíduos** para [Almeida Ambiental](https://almeidaambiental.com.br).

---

## 🎯 Visão Geral

ColetaFlow automatiza o planejamento semanal de coletas, que antes era feito **manualmente em Excel**.

### O Problema

- ❌ Planejamento manual = erro humano
- ❌ Sem histórico de coletas realizadas
- ❌ Difícil rastrear clientes que não aparecem
- ❌ Perda de tempo em cálculos de datas

### A Solução

- ✅ Geração automática de programação (5 segundos vs 30 minutos)
- ✅ Histórico completo de coletas (auditoria)
- ✅ Drag & drop para ajustar manualmente
- ✅ Importação de Excel (em massa)
- ✅ Fechamento automático de semana

**Ganho:** 30 minutos/semana = ~2.5h/mês = ~30h/ano

---

## 🚀 Quick Start

### **1. Requisitos**
```bash
# Verificar Python
python --version  # Deve ser 3.8+
```

### **2. Instalação**
```bash
# Clone
git clone https://github.com/amiltonod/coleta-flow.git
cd coleta-flow

# Venv
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependências
pip install -r requirements.txt
```

### **3. Rodar**
```bash
uvicorn backend.app.main:app --reload
```

### **4. Acessar**
Abra http://localhost:8000 no navegador.

---

## 📚 Documentação

| Documento | Descrição |
|-----------|-----------|
| 📖 [SETUP.md](./docs/SETUP.md) | Instruções completas de instalação e troubleshooting |
| 🏗️ [ARCHITECTURE.md](./docs/ARCHITECTURE.md) | Decisões técnicas, diagrama de arquitetura |
| 📡 [API.md](./docs/API.md) | Referência completa de endpoints REST |
| 🗺️ [ROADMAP.md](./docs/ROADMAP.md) | Plano de melhorias em 4 sprints |
| 🔍 [CODE_REVIEW.md](./docs/CODE_REVIEW.md) | Análise de código e oportunidades de melhoria |

**Novo no projeto?** Comece por [SETUP.md](./docs/SETUP.md).

---

## ✨ Features

### Core
- ✅ **Geração Automática** — Agenda clientes por frequência (a cada 3, 7, 15 dias)
- ✅ **Clientes Fixos** — Segunda, Terça, Quinta com auto-agendamento
- ✅ **Drag & Drop** — Reorganize manualmente na semana
- ✅ **Confirmação** — Marque coleta realizada e atualiza histórico
- ✅ **Importação Excel** — Adicione clientes em massa

### Inteligência
- ✅ **Anti-Duplicidade** — Triple-layer validation (negócio, API, BD)
- ✅ **Validação "Por Solicitação"** — Pula auto-agenda se marcado
- ✅ **Códigos Resilientes** — Trata "015" como "15" automaticamente
- ✅ **Fechamento Automático** — Atualiza `ultima_coleta` toda segunda-feira

### Operacional
- ✅ **Histórico Completo** — Rastra todas as coletas realizadas
- ✅ **Branding Almeida** — Logo e watermark personalizados
- ✅ **Sem Dependências Externas** — Roda offline com SQLite
- ✅ **Deploy Simples** — Um clique (.vbs) no Windows

---

## 🏛️ Arquitetura

```
Frontend (HTML/Jinja2 + JavaScript)
    ↓
API REST (FastAPI)
    ├─ Routes: Endpoints HTTP
    ├─ Services: Lógica de negócio
    └─ Models: ORM (SQLAlchemy)
    ↓
Database (SQLite)
```

### Camadas

**Routes** → Validação HTTP, respostas  
**Services** → Algoritmos, decisões de negócio  
**Models** → Estrutura de dados

---

## 🛠️ Tech Stack

| Camada | Tecnologia | Por quê |
|--------|-----------|--------|
| Backend | **FastAPI** | Rápido, validação automática, async |
| ORM | **SQLAlchemy** | Agnóstico a banco (SQLite → PostgreSQL fácil) |
| Banco | **SQLite** | Simples, zero setup, perfeito para MVP |
| Excel | **Pandas + OpenPyXL** | Parsing robusto, cálculos datas |
| Server | **Uvicorn** | ASGI moderno |

---

## 📊 Estrutura de Pastas

```
coleta-flow/
├── docs/                          # Documentação
│   ├── SETUP.md
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── CODE_REVIEW.md
│   └── ROADMAP.md
│
├── backend/
│   └── app/
│       ├── main.py               # Entrada FastAPI
│       ├── database.py           # Configuração SQLAlchemy
│       │
│       ├── models/               # ORM
│       │   ├── client.py
│       │   ├── schedule.py
│       │   └── controle.py
│       │
│       ├── services/             # Lógica de negócio
│       │   ├── generate_schedule.py
│       │   ├── fechar_semana.py
│       │   └── import_service.py
│       │
│       ├── routes/               # Endpoints REST
│       │   └── clientes.py
│       │
│       ├── templates/            # Frontend (HTML/Jinja2)
│       │   └── index.html
│       │
│       ├── static/               # CSS, JS
│       │   ├── css/
│       │   └── js/
│       │
│       └── coletas.db            # Banco (gerado automaticamente)
│
├── tests/                         # Testes (futuro)
│
├── README.md                      # Este arquivo
├── requirements.txt               # Dependências Python
└── ligar.vbs                      # Launch script (Windows)
```

---

## 📈 Roadmap

### **Sprint 1** — Segurança & Validação ✅ (4h)
- Validação com Pydantic
- HTTP status codes consistentes
- Remover duplicação de código

### **Sprint 2** — Performance ⏳ (3h)
- Otimizar queries (N+1 problem)
- Adicionar índices ao banco

### **Sprint 3** — Observabilidade 🔮 (3h)
- Logging de ações críticas
- Timestamps de auditoria

### **Sprint 4** — Testes 🔮 (4h)
- Testes unitários
- Cobertura >80%

[Detalhes completos em ROADMAP.md](./docs/ROADMAP.md)

---

## 🚀 Como Usar

### **Caso 1: Importar clientes novos**

1. Prepare arquivo Excel:
   ```
   Código  | Nome              | Cidade    | Observação
   L001    | Supermercado ABC  | Araquari  | Segunda,Quinta
   L002    | Indústria XYZ     | Joinville | Por solicitação
   ```

2. Vá para http://localhost:8000
3. Clique "📁 Importar"
4. Selecione arquivo → Clique "Upload"

### **Caso 2: Gerar programação**

1. Clique "🔄 Gerar Programação"
2. Sistema agenda clientes por frequência + fixos
3. Veja grade semanal com drag & drop

### **Caso 3: Confirmar coleta**

1. Na grade semanal, clique "✓ Concluído"
2. Sistema atualiza `ultima_coleta`
3. Próxima coleta é calculada automaticamente

---

## 🔧 Desenvolvimento

### **Rodar com reload automático**
```bash
uvicorn backend.app.main:app --reload
```

### **Ver documentação da API (Swagger)**
```
http://localhost:8000/docs
```

### **Resetar banco**
```bash
rm backend/app/coletas.db
# Será recriado vazio na próxima inicialização
```

### **Instalar dependência nova**
```bash
pip install nova_lib
pip freeze > requirements.txt
git add requirements.txt
git commit -m "deps: adicionar nova_lib"
```

---

## 🧪 Testes (Futuro)

Quando implementar:

```bash
# Rodar testes
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=backend.app --cov-report=html
```

---

## 📡 API

### Endpoints principais:

```bash
# Ver programação da semana
GET /programacao-semana

# Adicionar cliente
POST /clientes/adicionar

# Gerar programação automática
POST /gerar-programacao

# Confirmar coleta realizada
POST /confirmar-coleta/{schedule_id}

# Importar Excel
POST /upload
```

**Referência completa:** [API.md](./docs/API.md)

---

## 🐛 Troubleshooting

### Erro: `ModuleNotFoundError: No module named 'fastapi'`
```bash
pip install -r requirements.txt
```

### Erro: `Port 8000 already in use`
```bash
uvicorn backend.app.main:app --reload --port 8001
```

### Mais dúvidas?
Veja [SETUP.md → Troubleshooting](./docs/SETUP.md#-troubleshooting)

---

## 🎓 O que este projeto ensina

✅ **FastAPI** — Framework web moderno  
✅ **SQLAlchemy** — ORM agnóstico a banco  
✅ **Separation of Concerns** — Routes / Services / Models  
✅ **Dependency Injection** — Código desacoplado  
✅ **Pydantic** — Validação de dados  
✅ **Business Logic** — Tratamento de edge cases  
✅ **Clean Code** — Legibilidade e manutenibilidade  

---

## 📋 Checklist de Melhoria

- [x] Projeto funcional ✅
- [x] Lógica defensiva ✅
- [x] Documentação básica ✅
- [ ] Validação Pydantic (Sprint 1)
- [ ] Logging/Auditoria (Sprint 3)
- [ ] Testes unitários (Sprint 4)
- [ ] CI/CD (Sprint 5)
- [ ] Docker (Sprint 5)

---

## 🤝 Contribuindo

Este é um projeto em evolução. Ideias?

1. Fork o repositório
2. Crie branch: `git checkout -b feature/sua-feature`
3. Commit: `git commit -m "feat: descrição"`
4. Push: `git push origin feature/sua-feature`
5. Abra Pull Request

---

## 📄 Licença

MIT License — Sinta-se livre para usar e modificar.

---

## 👤 Sobre

**Desenvolvido por:** Amilton Oliveira   
**Objetivo:** Demonstrar integração de operações + tecnologia + estudo de engenharia de software e integração de IA

---

## 🔗 Links Úteis

- 📖 [FastAPI Docs](https://fastapi.tiangolo.com)
- 🐘 [SQLAlchemy Docs](https://docs.sqlalchemy.org)
- 🧪 [Pytest Docs](https://docs.pytest.org)
- 🎨 [Code Review (detalhado)](./docs/CODE_REVIEW.md)

---

## 💡 Próximos Passos

1. **Setup** → [SETUP.md](./docs/SETUP.md)
2. **Entender** → [ARCHITECTURE.md](./docs/ARCHITECTURE.md)
3. **Usar** → [API.md](./docs/API.md)
4. **Melhorar** → [ROADMAP.md](./docs/ROADMAP.md)

---

**Pronto para começar?** Execute:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```

Depois abra http://localhost:8000 🚀

---

<div align="center">

**Feito para otimizar operações**

*Demonstrando que bom código + lógica de negócio = diferencial profissional*

</div>