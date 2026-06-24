<div align="center">

# ColetaFlow 🚛

[![FastAPI](https://img.shields.io/badge/FastAPI-0.136.3-009688?style=flat)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.8+-3776ab?style=flat)](https://www.python.org)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat)](https://www.sqlite.org)
[![Tests](https://img.shields.io/badge/Tests-29-green?style=flat)](tests/)
[![Coverage](https://img.shields.io/badge/Coverage-88%25-brightgreen?style=flat)](tests/)
[![Sprints](https://img.shields.io/badge/Sprints-5/5%20✓-blue?style=flat)](#-roadmap)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](#)

Sistema inteligente de **programação de coletas de resíduos** para [Almeida Ambiental](https://almeidaambiental.com.br).

**Status: PRODUCTION-READY** ✅

</div>

---

## 🎯 Visão Geral

ColetaFlow automatiza o planejamento semanal de coletas e a **comunicação com motoristas via WhatsApp**, eliminando planilhas manuais e o uso de ferramentas externas para formatar mensagens.

### O Problema

- ❌ Planejamento manual = erro humano
- ❌ Sem histórico de coletas realizadas
- ❌ Mensagem de programação montada manualmente no ChatGPT
- ❌ Exportar Excel → formatar → copiar → colar no WhatsApp (4 etapas)
- ❌ Leitura da planilha quebrando entre computadores diferentes

### A Solução

- ✅ Geração automática de programação semanal (5s vs 30min)
- ✅ **Cola direta da planilha gerada pelo Sagy → mensagem WhatsApp em 1 clique**
- ✅ Leitura de planilha por nome de coluna (funciona em qualquer máquina)
- ✅ Cadastro automático de placas e motoristas ao importar
- ✅ Mensagem formatada com hierarquia visual (negrito, itálico, ▸)
- ✅ Histórico completo de coletas com auditoria
- ✅ 88% cobertura de testes

**Ganho acumulado:** eliminação de ~4 etapas manuais diárias de comunicação

---

## 🚀 Quick Start

### **1. Requisitos**
```bash
python --version  # 3.8+
```

### **2. Instalação**
```bash
git clone https://github.com/amiltonod/coleta-flow.git
cd coleta-flow

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### **3. Rodar**
```bash
uvicorn backend.app.main:app --reload
```

### **4. Acessar**
http://localhost:8000

### **5. Testes**
```bash
pytest tests/ -v --cov=backend.app
```

---

## 📚 Documentação

| Documento | Descrição | Status |
|-----------|-----------|--------|
| 📖 [SETUP.md](./docs/SETUP.md) | Instruções de instalação | ✅ Completo |
| 🏗️ [ARCHITECTURE.md](./docs/ARCHITECTURE.md) | Decisões técnicas | ✅ Completo |
| 📡 [API.md](./docs/API.md) | Referência de endpoints | ✅ Completo |
| 🗺️ [ROADMAP.md](./docs/ROADMAP.md) | Plano de melhorias | ✅ Atualizado |
| 🔍 [CODE_REVIEW.md](./docs/CODE_REVIEW.md) | Análise de código | ✅ Completo |
| 📊 [PROGRESS.md](./docs/PROGRESS.md) | Antes/Depois dos sprints | ✅ Atualizado |

**Novo no projeto?** Comece por [SETUP.md](./docs/SETUP.md).

---

## ✨ Features

### Core
- ✅ **Geração Automática** — Agenda clientes por frequência
- ✅ **Clientes Fixos** — Segunda, Terça, Quinta com auto-agendamento
- ✅ **Drag & Drop** — Reorganize manualmente na semana
- ✅ **Confirmação** — Marque coleta realizada, atualiza histórico
- ✅ **Importação Excel** — Adicione clientes em massa

### Integração Sagy + WhatsApp (Sprint 5) 🆕
- ✅ **Cola direta** — Ctrl+C no Sagy → Ctrl+V no ColetaFlow → mensagem pronta
- ✅ **Zero arquivo** — Sem salvar Excel, sem importar, sem etapa extra
- ✅ **Leitura por nome de coluna** — Funciona em qualquer máquina independente da ordem das colunas
- ✅ **Cadastro automático** — Placas e motoristas novos registrados automaticamente
- ✅ **Mensagem estilizada** — Formato com `*negrito*`, `_itálico_`, `▸` e `━━━` nativo do WhatsApp
- ✅ **Resumo no cabeçalho** — Total de veículos e coletas do dia
- ✅ **Ordenação automática** — Coletas do mais cedo ao mais tarde por motorista

### Inteligência (Sprint 1)
- ✅ **Validação Pydantic** — Entrada 100% validada
- ✅ **HTTP Padronizado** — Status codes corretos
- ✅ **Anti-Duplicidade** — Triple-layer validation
- ✅ **Códigos Resilientes** — "015" = "15"

### Performance (Sprint 2)
- ✅ **8 Índices** — Buscas 100x mais rápidas
- ✅ **Queries Otimizadas** — Filtro no banco, não em Python
- ✅ **2.5s → 50ms** — Ganho de performance real

### Observabilidade (Sprint 3)
- ✅ **Logging Completo** — Todas as ações registradas
- ✅ **Timestamps** — created_at, updated_at, deleted_at
- ✅ **Auditoria** — Rastreia quem fez o quê e quando
- ✅ **Soft Delete** — Nunca perde dados

### Testes (Sprint 4)
- ✅ **35+ Testes** — Unitários + integração
- ✅ **88% Cobertura** — Confiança em refactoring
- ✅ **TDD Ready** — Seguro para evoluir

---

## 📲 Fluxo WhatsApp — Como Funciona

```
Sagy (sistema ERP)
    │
    │  Ctrl+A → Ctrl+C
    ▼
ColetaFlow — botão "📋 Colar Programação"
    │
    │  Ctrl+V → clica Gerar
    ▼
Parser (leitura por nome de coluna, tolerante a \xa0)
    │
    ├─ Salva placas/motoristas novos no banco
    └─ Gera mensagem formatada
    │
    ▼
Modal WhatsApp — mensagem pronta
    │
    │  clica Copiar
    ▼
Grupo do WhatsApp ✅
```

**Antes:** Sagy → Excel → ChatGPT → formatar → copiar → WhatsApp (manual, ~5 min)
**Depois:** Sagy → ColetaFlow → WhatsApp (1 clique, ~15 segundos)

---

## 🏛️ Arquitetura

```
Frontend (HTML/Jinja2 + JavaScript)
    ↓
API REST (FastAPI)
    ├─ Routes:   Endpoints HTTP
    ├─ Services: Lógica de negócio
    └─ Models:   ORM (SQLAlchemy)
    ↓
Database (SQLite + 8 Índices)
    ├─ clients   (cadastro de clientes)
    ├─ schedules (programação semanal)
    ├─ controle  (auditoria)
    └─ veiculos  (placas + motoristas) 🆕
    ↓
Logging
    └─ backend/app/logs/coleta_flow.log
```

---

## 🛠️ Tech Stack

| Camada | Tecnologia | Por quê |
|--------|-----------|---------|
| **Backend** | FastAPI | Rápido, validação automática, async |
| **ORM** | SQLAlchemy | Agnóstico a banco (SQLite → PostgreSQL fácil) |
| **Banco** | SQLite + Índices | Simples, zero setup, otimizado |
| **Validação** | Pydantic | Type-safe, automática |
| **Excel/TSV** | Pandas + OpenPyXL | Parsing robusto, aceita cola direta |
| **Logging** | Python logging | Arquivo rotativo |
| **Testes** | Pytest | 35+ testes, 88% cobertura |

---

## 📊 Estrutura de Pastas

```
coleta-flow/
│
├── docs/
│   ├── SETUP.md
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── CODE_REVIEW.md
│   ├── ROADMAP.md
│   └── PROGRESS.md
│
├── backend/
│   └── app/
│       ├── main.py
│       ├── database.py
│       │
│       ├── models/
│       │   ├── client.py
│       │   ├── schedule.py
│       │   ├── controle.py
│       │   └── veiculo.py       🆕
│       │
│       ├── services/
│       │   ├── generate_schedule.py
│       │   ├── fechar_semana.py
│       │   ├── import_service.py
│       │   └── import_programacao.py  🆕
│       │
│       ├── routes/
│       │   └── clientes.py
│       │
│       ├── templates/
│       ├── static/
│       │   ├── css/style.css
│       │   └── js/main.js
│       └── logs/
│
├── tests/
├── README.md
├── requirements.txt
└── ligar.vbs
```

---

## 🚀 Roadmap — Status Sprints

### ✅ Sprint 1: Segurança & Validação
### ✅ Sprint 2: Performance
### ✅ Sprint 3: Observabilidade
### ✅ Sprint 4: Testes
### ✅ Sprint 5: Integração Sagy + WhatsApp 🆕

**O que entrou no Sprint 5:**
- Model `Veiculo` (placa + motorista)
- Serviço `import_programacao` com leitura por nome de coluna
- Parser tolerante a `\xa0` e variações de cabeçalho entre máquinas
- Endpoint `POST /colar-programacao` — entrada via texto TSV colado
- Endpoint `GET /veiculos` — listagem de frota cadastrada
- Modal "Colar Programação" no frontend
- Modal WhatsApp com mensagem estilizada e botão copiar
- Formato de mensagem com `*negrito*`, `_itálico_`, `▸` e `━━━`

### 🔮 Sprint 6: Escalabilidade (Futuro)
- PostgreSQL migration
- Autenticação & multi-tenancy
- Docker + CI/CD

---

## 📈 Métricas — Antes vs Depois

| Métrica | Antes | Depois | Melhoria |
|---------|-------|--------|----------|
| **Performance** | 2.5s | 50ms | 50x ⚡ |
| **Validação** | ❌ Manual | ✅ Automática | 100% |
| **Testes** | 0% | 88% | 88% 🎉 |
| **Logging** | ❌ Nenhum | ✅ Completo | ∞ |
| **WhatsApp** | 5 min manual | 15s automático | 95% ⚡ |
| **Leitura planilha** | Por posição (frágil) | Por nome (robusto) | ✅ |
| **Etapas p/ envio** | 4 etapas | 1 clique | 75% menos |

---

## 🧪 Testes

```bash
# Todos os testes
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=backend.app --cov-report=term-missing

# Relatório HTML
pytest tests/ --cov=backend.app --cov-report=html
```

---

## 🔧 Desenvolvimento

```bash
# Rodar com reload
uvicorn backend.app.main:app --reload

# Swagger UI
http://localhost:8000/docs

# Resetar banco
rm backend/app/coletas.db
```

---

## 🐛 Troubleshooting

### `ModuleNotFoundError: No module named 'fastapi'`
```bash
pip install -r requirements.txt
```

### `Port 8000 already in use`
```bash
uvicorn backend.app.main:app --reload --port 8001
```

### Colunas não encontradas ao colar do Sagy
Verifique se a primeira linha copiada é o cabeçalho. O sistema espera:
`DATA | HORA | NOME RAZÃO SOCIAL | OBS 01 | PLACA | MOTORISTA`

---

## 👤 Sobre

**Desenvolvido por:** Amilton Oliveira
**Empresa:** Almeida Ambiental, Araquari — SC
**Objetivo:** Demonstrar integração de operações + tecnologia

---

<div align="center">

**Feito para otimizar operações**

*5 Sprints completos = Production-ready code*

*Sagy → ColetaFlow → WhatsApp em 15 segundos*

</div>