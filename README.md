# Coleta Flow 🚛

O **Coleta Flow** é um sistema web logístico desenvolvido para automatizar, processar e gerenciar a programação semanal de coletas de resíduos a partir de planilhas Excel. A aplicação transforma dados brutos de históricos anteriores em uma grade de programação visual, inteligente e altamente editável.

## 🎯 Objetivo do Projeto

Desenvolvido especificamente para otimizar o planejamento da área logística da **Almeida Ambiental**, o sistema visa eliminar processos manuais suscetíveis a falhas, reduzir o tempo de roteirização e garantir a consistência das informações de coleta de clientes e fornecedores.

---

## ✨ Funcionalidades Implementadas (O que já funciona)

* **Importação Inteligente via Excel:** Leitura automatizada de planilhas de programações anteriores com mapeamento de colunas via Pandas, tratando de forma inteligente nomes compostos (separação de cliente, cidade e unidade).

* **Geração Automática de Programação Semanal:** Motor de cálculo que prevê de forma preditiva a próxima data útil de coleta baseando-se na *Última Coleta + Frequência em Dias* ou alocando clientes em seus *Dias Fixos* da semana seguinte.

* **Sistema Robusto Anti-Duplicidade (Back-end):** Mecanismo de segurança implementado diretamente nas rotas e nos serviços de geração de cronograma. O sistema consulta o banco de dados antes de qualquer inserção (`INSERT`), bloqueando registros repetidos para o mesmo cliente na mesma data, mesmo se houver cliques duplos na interface ou reenvio de requisições.

* **Edição Inline em Tempo Real (Interface Tabela):** Modificação direta na planilha visual da tela. Campos cruciais como *Frequência*, *Dia Fixo*, *Observações* e a própria data da *Última Coleta* podem ser editados e salvos instantaneamente via requisições assíncronas (`onblur` / AJAX).

* **Adição Manual na Grade:** Permite incluir coletas extras ou avulsas na programação informando apenas o código do cliente e a data desejada.

* **Replicação de Coletas:** Opção de copiar e espelhar um agendamento existente para outro dia da semana com validação automática de consistência.

---

## 🛠️ Tecnologias Utilizadas

### Backend

* Python 3.x
* FastAPI (Framework de alto desempenho)
* Uvicorn (Servidor ASGI)

### Análise e Manipulação de Dados

* Pandas
* OpenPyXL

### Banco de Dados & ORM

* SQLite (Armazenamento local persistente)
* SQLAlchemy (Mapeamento Objeto-Relacional)

### Frontend

* HTML5
* Bootstrap 5 (Estilização responsiva)
* Jinja2 Templates (Renderização dinâmica pelo servidor)

---

## 📂 Estrutura Atualizada do Projeto

```text
coleta-flow/
│
├── backend/
│   └── app/
│       ├── models/
│       │   ├── client.py          # Modelo da tabela de clientes (cadastro base)
│       │   └── schedule.py        # Modelo da tabela de agendamentos/programação
│       │
│       ├── routers/
│       │   └── clientes.py        # Rotas da API (Home, CRUD, Replicar, Adicionar)
│       │
│       ├── services/
│       │   ├── import_service.py   # Lógica de processamento e atualização do Excel
│       │   └── generate_schedule.py# Regras de negócio e motor anti-duplicidade
│       │
│       ├── database.py            # Configuração da conexão com o SQLite
│       └── main.py                # Ponto de entrada do FastAPI
│
├── templates/
│   └── index.html                 # Interface visual principal da aplicação
│
├── uploads/                       # Diretório temporário de armazenamento de planilhas
├── coletas.db                     # Arquivo de banco de dados SQLite persistente
├── requirements.txt               # Lista de dependências do projeto
└── README.md                      # Documentação do sistema
```

---

## ⚙️ Instalação

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/coleta-flow.git
cd coleta-flow
```ta-flow
```

### 2. Criar ambiente virtual

```bash
python -m venv venv
```

### 3. Ativar ambiente virtual

Windows:

```bash
venv\Scripts\activate
```

Linux/Mac:

```bash
source venv/bin/activate
```

### 4. Instalar dependências

```bash
pip install -r requirements.txt
```

---

## ▶️ Executando o Projeto

Inicie o servidor:

```bash
python -m uvicorn backend.app.main:app --reload
```

Acesse no navegador:

```text
http://127.0.0.1:8000
```

---

## 🗄 Banco de Dados

O sistema utiliza SQLite.

Arquivo gerado:

```text
coletas.db
```

As tabelas são criadas automaticamente pelo SQLAlchemy:

```python
Base.metadata.create_all(bind=engine)
```

---

## 🔄 Fluxo de Funcionamento

### Importação

1. O usuário seleciona a planilha da semana anterior.
2. O sistema realiza o upload do arquivo.
3. Os dados são processados utilizando Pandas.
4. Os clientes são armazenados no banco de dados.

### Processamento

Após a importação:

- Identificação da última coleta
- Tratamento dos dados
- Cálculo da próxima coleta
- Geração da programação semanal

### Visualização

A programação é exibida na interface web contendo:

- Código
- Cliente
- Cidade
- Última coleta
- Próxima coleta

---

## 📤 Exportação

O sistema permite gerar uma planilha Excel com a programação processada.

Arquivo gerado:

```text
programacao_coletas.xlsx
```

---

## 📚 Aprendizados Aplicados

Durante o desenvolvimento foram utilizados conceitos de:

- Estruturação de projetos Python
- Programação orientada a objetos
- FastAPI
- SQLAlchemy ORM
- SQLite
- Manipulação de Excel com Pandas
- Templates Jinja2
- Upload de arquivos
- Organização em camadas (Models, Services e Views)
- Git e GitHub

---

## 🔮 Próximas Melhorias

- [ ] Histórico de coletas
- [ ] Dashboard de indicadores
- [ ] Filtros por cidade
- [ ] Controle de usuários e permissões
- [ ] Integração com Google Maps
- [ ] Otimização automática de rotas

---

## 👨‍💻 Autor

**Amilton Carvalho Jr.**

- Tecnólogo em Logística
- Pós-graduado em Gestão Ambiental Empresarial
- Pós-graduado em Gestão de Transporte

Projeto desenvolvido para estudo de Python, automação logística e desenvolvimento web com FastAPI.
