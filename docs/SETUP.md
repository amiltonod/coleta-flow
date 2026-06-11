# Setup & Instalação — ColetaFlow 🚀

---

## 📋 Pré-requisitos

- **Python 3.8+** (testado com 3.9, 3.10, 3.11)
- **pip** (gerenciador de pacotes Python)
- **Git** (opcional, para clonar o repo)
- **Navegador moderno** (Chrome, Firefox, Edge)

### ✅ Verificar se tem Python

Abra **Terminal/Prompt de Comando** e rode:

```bash
python --version
```

Se retornar `Python 3.8.x` ou superior, está ok. Caso contrário, baixe em: https://www.python.org/downloads/

---

## 🔧 Instalação Passo a Passo

### **Passo 1: Clone o repositório**

```bash
git clone https://github.com/amiltonod/coleta-flow.git
cd coleta-flow
```

(Ou baixe como ZIP e extraia)

---

### **Passo 2: Crie um ambiente virtual (RECOMENDADO)**

Um **venv** isola as dependências do ColetaFlow das outras coisas do seu Python.

**No Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**No macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

Após ativar, você verá `(venv)` no início da linha do terminal.

> **Por que venv?** Evita conflitos de versão com outros projetos. Cada projeto tem suas dependências isoladas.

---

### **Passo 3: Instale as dependências**

Com o venv ativado, rode:

```bash
pip install -r requirements.txt
```

Isso vai instalar:
- `fastapi` — framework web
- `uvicorn` — servidor ASGI
- `sqlalchemy` — ORM para banco de dados
- `pandas` — leitura de Excel
- `openpyxl` — suporte a .xlsx
- ... e outras

Leva ~2-3 minutos na primeira vez.

---

### **Passo 4: Rode o servidor**

```bash
uvicorn backend.app.main:app --reload
```

Você verá algo assim:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete
```

**Parabéns!** O servidor está rodando. 🎉

---

## 🌐 Acessar o ColetaFlow

Abra seu navegador e vá para:

```
http://localhost:8000
```

Você verá a interface de programação de coletas.

---

## 📚 Comandos Úteis

### **Parar o servidor**
```bash
CTRL + C
```

### **Reativar o venv** (em nova janela de terminal)

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### **Ver documentação interativa da API**

O FastAPI gera documentação automática. Acesse:

```
http://localhost:8000/docs
```

(Swagger UI)

ou

```
http://localhost:8000/redoc
```

(ReDoc)

---

## 🗄️ Banco de Dados

### **Onde fica?**

O banco SQLite é criado automaticamente:

```
coleta-flow/
└── backend/
    └── app/
        └── coletas.db  ← Aqui
```

### **Ver dados do banco** (ferramentas gratuitas)

1. **DBeaver** (mais completo)
   - Download: https://dbeaver.io
   - Interface gráfica, SQL direto

2. **SQLiteStudio** (mais leve)
   - Download: https://sqlitestudio.pl

3. **Pela linha de comando:**
   ```bash
   sqlite3 backend/app/coletas.db
   > SELECT * FROM clients;
   > .exit
   ```

### **Resetar o banco** (apaga TUDO)

```python
# 1. Delete o arquivo
rm backend/app/coletas.db

# 2. Rode o servidor
uvicorn backend.app.main:app --reload
# Será recriado automaticamente vazio
```

> ⚠️ Cuidado: isso **deleta todos os dados**. Use só em desenvolvimento.

---

## 🐛 Troubleshooting

### **Erro: `ModuleNotFoundError: No module named 'fastapi'`**

**Causa:** Esqueceu de instalar dependências ou venv não está ativado.

**Solução:**
```bash
# Verifique que venv está ativado (venv) na linha
pip install -r requirements.txt
```

---

### **Erro: `Port 8000 already in use`**

**Causa:** Outro processo está usando porta 8000 (ou ColetaFlow já aberto em outra janela).

**Solução:**
```bash
# Use outra porta
uvicorn backend.app.main:app --reload --port 8001
# Depois acesse http://localhost:8001
```

---

### **Erro: `FileNotFoundError: coletas.db`**

**Causa:** Banco não foi criado ou está em outro lugar.

**Solução:**
```bash
# Verifique que rodou uvicorn com sucesso
# O banco é criado automaticamente na primeira inicialização
uvicorn backend.app.main:app --reload
```

---

### **Erro: `No module named 'backend'`**

**Causa:** Rodou do diretório errado.

**Solução:**
```bash
# Certifique que está na raiz do projeto
cd coleta-flow
uvicorn backend.app.main:app --reload
```

---

## 📦 Upgrade de Dependências

Ocasionalmente, você pode querer atualizar bibliotecas para correções de segurança:

```bash
# Listar versões novas disponíveis
pip list --outdated

# Atualizar um pacote específico
pip install --upgrade fastapi

# Salvar novas versões no requirements.txt
pip freeze > requirements.txt
```

---

## 🔄 Deploy em Produção

> ℹ️ Para rodar em produção (ex: servidor Linux), veja [ROADMAP.md](./ROADMAP.md).

---

## ⚡ Dicas de Desenvolvimento

### **Recarregar automático**

```bash
uvicorn backend.app.main:app --reload
```

A flag `--reload` monitora mudanças de arquivo e reinicia o servidor automaticamente. Perfeito para desenvolvimento.

### **Ativar logs verbose**

```bash
uvicorn backend.app.main:app --reload --log-level debug
```

---

## 🧪 Rodando Testes (Futuro)

Quando houver testes:

```bash
pytest tests/ -v
```

---

## 📖 Próximos Passos

1. ✅ Servidor rodando → Vá para http://localhost:8000
2. 📖 Entender API → Veja [API.md](./API.md)
3. 🏗️ Entender arquitetura → Veja [ARCHITECTURE.md](./ARCHITECTURE.md)
4. 🗺️ Plano de melhorias → Veja [ROADMAP.md](./ROADMAP.md)

---

## 💬 Precisa de Ajuda?

1. Verifique o [Troubleshooting](#-troubleshooting) acima
2. Veja logs do terminal (mensagens de erro)
3. Confira [ARCHITECTURE.md](./ARCHITECTURE.md) para entender estrutura
4. Consulte docs oficiais:
   - FastAPI: https://fastapi.tiangolo.com
   - SQLAlchemy: https://docs.sqlalchemy.org

---

**Pronto para codar?** Vá para [ARCHITECTURE.md](./ARCHITECTURE.md) ou comece importando um Excel! 🚀