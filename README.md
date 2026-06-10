# ColetaFlow 🚛
 
> Sistema web de gestão e programação de coletas de resíduos desenvolvido para a **Almeida Ambiental — Araquari/SC**.
 
---
 
## Sobre o Projeto
 
O **ColetaFlow** nasceu de uma necessidade real: eliminar o processo manual de montagem da programação semanal de coletas, que era feito em planilhas Excel sujeitas a erros, duplicidades e retrabalho.
 
O sistema lê os históricos de coletas anteriores, calcula automaticamente as próximas datas com base na frequência de cada cliente e gera uma grade semanal visual e editável — tudo isso em uma interface web acessível pelo navegador, sem necessidade de instalação por parte do usuário final.
 
O projeto foi desenvolvido do zero como aplicação real de uso interno, e também como portfólio de transição para uma carreira em desenvolvimento de software, aplicando boas práticas de arquitetura, separação de responsabilidades e código limpo.
 
---
 
## Funcionalidades
 
### Importação de Dados
- Upload de planilha Excel com histórico de coletas
- Processamento via Pandas com tratamento de datas e campos nulos
- Separação automática de nome, cidade e unidade a partir de campos compostos
- Upsert inteligente: atualiza o cliente se o código já existe, insere se for novo — **nunca duplica**
### Geração Automática de Programação
- Cálculo da próxima coleta com base em `última coleta + frequência em dias`
- Suporte a clientes com **dia fixo** da semana (ex: sempre na Terça)
- Exclusão automática de finais de semana — coletas são movidas para o próximo dia útil
- Programação sempre calculada para a **semana seguinte**
- Motor anti-duplicidade: não gera coleta se o cliente já está agendado naquele dia
### Grade Semanal Interativa
- Visualização em colunas (Segunda a Sexta) com data exibida no cabeçalho
- **Drag and drop** para mover coletas entre dias com atualização imediata no banco
- **Replicar coleta** para outro dia da semana com validação de duplicidade
- **Adicionar coleta manualmente** com busca por código ou nome do cliente
- **Excluir coleta** da grade sem afetar o cadastro do cliente
- Coletas fixas destacadas visualmente no topo de cada coluna
- Atualização sem recarregar a página (requisições assíncronas via Fetch API)
### Banco de Dados de Clientes
- Tabela completa com todos os campos do cadastro
- Edição inline diretamente na célula: nome, cidade, frequência, última coleta, observação
- Seleção de dia fixo via dropdown com salvamento automático
- Feedback visual de sucesso/erro ao salvar
- Coluna de programação da semana atualizada em tempo real
### Cadastro e Busca de Clientes
- Busca por código ou nome com debounce (300ms) para não sobrecarregar o servidor
- Cadastro de novo cliente direto pelo modal de adição manual
### Impressão
- Layout otimizado para impressão — controles e tabelas de gestão ocultados automaticamente
---
 
## Arquitetura e Decisões Técnicas
 
O projeto foi estruturado em camadas com separação clara de responsabilidades:
 
```
coleta-flow/
├── backend/
│   └── app/
│       ├── database.py              # Configuração SQLAlchemy + get_db (dependency injection)
│       ├── main.py                  # Ponto de entrada FastAPI
│       ├── models/
│       │   ├── client.py            # Modelo da tabela clients
│       │   └── schedule.py          # Modelo da tabela schedules
│       ├── routes/
│       │   └── clientes.py          # Rotas da API REST (CRUD completo)
│       ├── services/
│       │   ├── import_service.py    # Lógica de importação e upsert via Excel
│       │   └── generate_schedule.py # Motor de geração da programação semanal
│       ├── templates/
│       │   └── index.html           # Interface principal (Jinja2 + Bootstrap + JS)
│       └── uploads/                 # Diretório para arquivos Excel recebidos
```
 
**Principais decisões:**
 
- **Caminho absoluto para o banco** via `os.path.abspath(__file__)` — o banco sempre fica em `app/coletas.db`, independente de onde o servidor é iniciado
- **Dependency injection** com `get_db()` — a sessão do banco é aberta e fechada automaticamente pelo FastAPI em cada requisição
- **Upsert por código** na importação — o campo `codigo` é a chave de negócio; se já existe, atualiza; se não existe, insere
- **Trava anti-duplicidade em três camadas**: na geração automática, na adição manual e na replicação — nenhuma delas permite dois agendamentos do mesmo cliente na mesma data
- **Fetch API com async/await** no frontend — toda interação com a grade (mover, adicionar, excluir) acontece sem recarregar a página
---
 
## Tecnologias
 
| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.x · FastAPI · Uvicorn |
| Banco de dados | SQLite · SQLAlchemy ORM |
| Processamento de dados | Pandas · OpenPyXL |
| Frontend | HTML5 · Bootstrap 5 · Jinja2 · Fetch API |
| Controle de versão | Git · GitHub |
 
---
 
## Instalação
 
**1. Clone o repositório**
 
```bash
git clone https://github.com/amiltonod/coleta-flow.git
cd coleta-flow
git checkout refatoracao
```
 
**2. Crie e ative o ambiente virtual**
 
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate
 
# Linux / Mac
python -m venv venv
source venv/bin/activate
```
 
**3. Instale as dependências**
 
```bash
pip install fastapi uvicorn sqlalchemy pandas openpyxl jinja2 python-multipart
```
 
**4. Inicie o servidor**
 
```bash
python -m uvicorn backend.app.main:app --reload
```
 
**5. Acesse no navegador**
 
```
http://127.0.0.1:8000
```
 
---
 
## Fluxo de Uso
 
```
1. Importar planilha Excel com histórico de coletas
        ↓
2. Sistema processa e popula o banco de clientes
        ↓
3. Clicar em "Gerar Coletas" → programação da próxima semana é calculada
        ↓
4. Grade semanal exibe os agendamentos por dia
        ↓
5. Ajustes manuais: mover, adicionar, replicar ou excluir coletas
        ↓
6. Imprimir a grade para uso operacional
```
 
---
 
## API — Principais Endpoints
 
| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/` | Interface principal |
| `POST` | `/upload` | Importa planilha Excel |
| `POST` | `/gerar-programacao` | Gera programação da próxima semana |
| `GET` | `/programacao-semana` | Retorna grade semanal em JSON |
| `PUT` | `/programacao/{id}` | Atualiza data/status de um agendamento |
| `DELETE` | `/programacao/{id}` | Remove agendamento da grade |
| `POST` | `/programacao/{id}/replicar` | Copia agendamento para outro dia |
| `POST` | `/programacao/adicionar` | Adiciona coleta manual |
| `GET` | `/clientes/buscar?q=` | Busca clientes por código ou nome |
| `PUT` | `/clientes/{id}` | Atualiza cadastro do cliente |
| `PUT` | `/clientes/{id}/fixar` | Define/remove dia fixo do cliente |
 
---
 
## Modelo de Dados
 
**clients**
 
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `codigo` | String | Código único do cliente |
| `nome` | String | Nome do cliente/fornecedor |
| `cidade` | String | Cidade |
| `unidade` | String | Unidade/filial |
| `frequencia_dias` | Integer | Intervalo em dias entre coletas |
| `ultima_coleta` | Date | Data da última coleta realizada |
| `proxima_coleta` | Date | Sugestão calculada da próxima coleta |
| `fixo` | Boolean | Se possui dia fixo na semana |
| `dia_fixo` | String | Nome do dia fixo (ex: "Terça") |
 
**schedules**
 
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `codigo_cliente` | String | Referência ao código do cliente |
| `cliente` | String | Nome do cliente no momento do agendamento |
| `unidade` | String | Unidade no momento do agendamento |
| `data_coleta` | Date | Data agendada |
| `dia_semana` | String | Nome do dia da semana |
| `status` | String | Status do agendamento (padrão: "Programado") |
| `fixo` | Boolean | Se é uma coleta fixa |
 
---
 
## Próximas Melhorias
 
- [ ] Histórico de coletas realizadas por cliente
- [ ] Dashboard com indicadores operacionais (volume por dia, por cidade)
- [ ] Filtros na grade por cidade ou rota
- [ ] Exportação da programação para Excel
- [ ] Otimização automática de rotas integrada
- [ ] Controle de acesso por usuário
- [ ] Integração com Google Maps para visualização geográfica
---
 
## Autor
 
**Amilton Carvalho Jr.**
 
Tecnólogo em Logística · Pós-graduado em Gestão Ambiental e Gestão de Transporte
 
Projeto desenvolvido como ferramenta real de uso interno e como portfólio de transição para desenvolvimento de software — aplicando Python, FastAPI, SQLAlchemy e boas práticas de arquitetura em um problema logístico real.
 
[![GitHub](https://img.shields.io/badge/GitHub-amiltonod-181717?style=flat&logo=github)](https://github.com/amiltonod)
