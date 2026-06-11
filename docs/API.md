# Documentação da API — ColetaFlow 📡

---

## 📌 Base URL

```
http://localhost:8000
```

Quando em produção, substitua `localhost:8000` pela URL do seu servidor.

---

## 🔍 Índice de Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/` | Página inicial (HTML) |
| `GET` | `/docs` | Documentação interativa (Swagger) |
| `GET` | `/programacao-semana` | Programação da semana atual/próximas |
| `POST` | `/clientes/adicionar` | Adicionar novo cliente |
| `PUT` | `/clientes/{cliente_id}` | Atualizar cliente |
| `DELETE` | `/clientes/{cliente_id}` | Deletar cliente |
| `POST` | `/gerar-programacao` | Gerar programação automática |
| `POST` | `/confirmar-coleta/{schedule_id}` | Marcar coleta como realizada |
| `DELETE` | `/programacao/{schedule_id}` | Remover agendamento |
| `POST` | `/upload` | Importar clientes via Excel |
| `GET` | `/clientes` | Listar todos os clientes |
| `GET` | `/clientes/buscar` | Buscar cliente por nome/código |
| `GET` | `/clientes/fixos` | Listar apenas clientes fixos |

---

## 📖 Detalhamento por Endpoint

### **1. GET `/`**

Retorna a página inicial (HTML) com interface de programação.

**Função:** Exibir a interface web

**Response:**
```
HTTP/1.1 200 OK
Content-Type: text/html

<!DOCTYPE html>
<html>
...
</html>
```

---

### **2. GET `/programacao-semana`**

Retorna a programação de coletas da semana (5 dias úteis).

**URL:**
```
http://localhost:8000/programacao-semana?offset=0
```

**Query Parameters:**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `offset` | int | `0` | Deslocamento de semanas. 0=próxima, -1=atual, -2=anterior |

**Response (200 OK):**
```json
{
  "dias": [
    "2026-06-15",
    "2026-06-16",
    "2026-06-17",
    "2026-06-18",
    "2026-06-19"
  ],
  "programacao": {
    "2026-06-15": [
      {
        "id": 1,
        "codigo": "L001",
        "cliente": "Supermercado ABC",
        "unidade": "Matriz",
        "status": "Programado",
        "fixo": true
      }
    ],
    "2026-06-16": [
      {
        "id": 2,
        "codigo": "L002",
        "cliente": "Indústria XYZ",
        "unidade": "Filial 2",
        "status": "Programado",
        "fixo": false
      }
    ],
    "2026-06-17": [],
    "2026-06-18": [],
    "2026-06-19": []
  },
  "offset": 0,
  "semana_atual": false
}
```

**Exemplo de uso:**
```bash
# Programação da próxima semana
curl http://localhost:8000/programacao-semana?offset=0

# Programação da semana atual
curl http://localhost:8000/programacao-semana?offset=-1

# Programação de 2 semanas atrás
curl http://localhost:8000/programacao-semana?offset=-2
```

---

### **3. GET `/clientes`**

Retorna lista de **todos os clientes** cadastrados.

**Response (200 OK):**
```json
{
  "clientes": [
    {
      "id": 1,
      "codigo": "L001",
      "nome": "Supermercado ABC",
      "cidade": "Araquari",
      "unidade": "Matriz",
      "observacao": "Segunda e Quinta",
      "frequencia_dias": 3,
      "ultima_coleta": "2026-06-10",
      "proxima_coleta": "2026-06-13",
      "fixo": true,
      "dia_fixo": "Segunda,Quinta"
    }
  ]
}
```

---

### **4. GET `/clientes/buscar`**

Busca cliente por **nome** ou **código**.

**URL:**
```
http://localhost:8000/clientes/buscar?q=ABC
```

**Query Parameters:**

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `q` | string | ✅ Sim | Termo de busca (mín 2 caracteres) |

**Response (200 OK):**
```json
{
  "resultados": [
    {
      "id": 1,
      "codigo": "L001",
      "nome": "Supermercado ABC",
      "cidade": "Araquari",
      "unidade": "Matriz"
    }
  ]
}
```

**Exemplos:**
```bash
# Buscar por código
curl http://localhost:8000/clientes/buscar?q=L001

# Buscar por nome
curl http://localhost:8000/clientes/buscar?q=Supermercado

# Buscar por cidade
curl http://localhost:8000/clientes/buscar?q=Araquari
```

---

### **5. GET `/clientes/fixos`**

Retorna apenas clientes com **coletas fixas** (Segunda, Terça, etc).

**Response (200 OK):**
```json
{
  "fixos": [
    {
      "id": 1,
      "codigo": "L001",
      "nome": "Supermercado ABC",
      "dia_fixo": "Segunda,Quinta",
      "ultima_coleta": "2026-06-10"
    }
  ]
}
```

---

### **6. POST `/clientes/adicionar`**

Adiciona um **novo cliente** ao banco.

**URL:**
```
POST http://localhost:8000/clientes/adicionar
Content-Type: application/json
```

**Body:**
```json
{
  "codigo": "L003",
  "nome": "Nova Empresa Ltda",
  "cidade": "Joinville",
  "unidade": "Filial 1",
  "observacao": "Coleta segunda e quinta",
  "frequencia_dias": 3,
  "fixo": true,
  "dia_fixo": "Segunda,Quinta"
}
```

**Response (201 Created):**
```json
{
  "mensagem": "Cliente adicionado com sucesso",
  "cliente_id": 3,
  "codigo": "L003"
}
```

**Response (400 Bad Request):**
```json
{
  "erro": "Cliente com código L003 já existe"
}
```

**Campos:**

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `codigo` | string | ✅ Sim | Código único (ex: L001, 15, ABC) |
| `nome` | string | ✅ Sim | Nome do cliente |
| `cidade` | string | ⬜ Não | Cidade |
| `unidade` | string | ⬜ Não | Unidade/Filial |
| `observacao` | string | ⬜ Não | Observações (ex: "Por solicitação") |
| `frequencia_dias` | int | ⬜ Não | Dias entre coletas (ex: 7, 3) |
| `fixo` | bool | ⬜ Não | True se coleta em dias fixos |
| `dia_fixo` | string | ⬜ Não | Dias da semana separados por vírgula (Segunda,Quinta) |

---

### **7. PUT `/clientes/{cliente_id}`**

Atualiza um cliente existente.

**URL:**
```
PUT http://localhost:8000/clientes/1
Content-Type: application/json
```

**Body (atualizar apenas alguns campos):**
```json
{
  "frequencia_dias": 5,
  "observacao": "Aumentou frequência"
}
```

**Response (200 OK):**
```json
{
  "mensagem": "Cliente atualizado com sucesso",
  "cliente_id": 1
}
```

**Response (404 Not Found):**
```json
{
  "erro": "Cliente 999 não encontrado"
}
```

---

### **8. DELETE `/clientes/{cliente_id}`**

Deleta um cliente e seus agendamentos associados.

**URL:**
```
DELETE http://localhost:8000/clientes/1
```

**Response (200 OK):**
```json
{
  "mensagem": "Cliente deletado com sucesso",
  "agendamentos_removidos": 5
}
```

**Response (404 Not Found):**
```json
{
  "erro": "Cliente 999 não encontrado"
}
```

---

### **9. POST `/gerar-programacao`**

Gera automaticamente a programação semanal com base em:
- Clientes fixos (Segunda, Quinta, etc)
- Clientes por frequência (a cada 3 dias, 7 dias, etc)

**URL:**
```
POST http://localhost:8000/gerar-programacao
```

**Body:** (vazio)
```json
{}
```

**Response (200 OK):**
```json
{
  "mensagem": "Programação gerada com sucesso",
  "gerados": 12,
  "ignorados": 2,
  "duplicados": 0,
  "por_solicitacao": 1
}
```

**Detalhes:**
- `gerados`: Novos agendamentos criados
- `ignorados`: Clientes com "Por solicitação" na observação
- `duplicados`: Já estavam agendados (validação)
- `por_solicitacao`: Pulados por conter "Por solicitação"

---

### **10. POST `/confirmar-coleta/{schedule_id}`**

Marca uma coleta como **"Concluído"** e atualiza `ultima_coleta` do cliente.

**URL:**
```
POST http://localhost:8000/confirmar-coleta/1
Content-Type: application/json
```

**Body:**
```json
{
  "data_realizada": "2026-06-15"
}
```

**Response (200 OK):**
```json
{
  "mensagem": "Coleta confirmada com sucesso",
  "schedule_id": 1,
  "status": "Concluído",
  "proxima_coleta_calculada": "2026-06-18"
}
```

**Response (404 Not Found):**
```json
{
  "erro": "Agendamento 999 não encontrado"
}
```

---

### **11. DELETE `/programacao/{schedule_id}`**

Remove um agendamento específico.

**URL:**
```
DELETE http://localhost:8000/programacao/1
```

**Response (200 OK):**
```json
{
  "mensagem": "Agendamento removido com sucesso",
  "schedule_id": 1
}
```

**Response (404 Not Found):**
```json
{
  "erro": "Agendamento 999 não encontrado"
}
```

---

### **12. POST `/upload`**

Importa clientes via arquivo **Excel** (.xlsx).

**URL:**
```
POST http://localhost:8000/upload
Content-Type: multipart/form-data
```

**Body (form-data):**
```
file: [arquivo.xlsx]
```

**Formato esperado do Excel:**

| Coluna A | Coluna B | Coluna C | Coluna D |
|----------|----------|----------|----------|
| Código | Nome | Cidade | Observação |
| L001 | Supermercado ABC | Araquari | Segunda e Quinta |
| 15 | Indústria XYZ | Joinville | Por solicitação |
| L003 | Farmácia 24h | Brusque | |

**Response (200 OK):**
```json
{
  "mensagem": "Importação concluída",
  "importados": 10,
  "atualizados": 5,
  "erros": [
    {
      "linha": 3,
      "erro": "Código vazio"
    }
  ],
  "total_linhas": 18
}
```

**Response (400 Bad Request):**
```json
{
  "erro": "Nenhum arquivo enviado"
}
```

---

## 🔄 Fluxo Típico de Uso

### **Cenário: Segunda-feira pela manhã**

1. **Importar clientes** (se houver novos)
   ```bash
   POST /upload [arquivo.xlsx]
   ```

2. **Gerar programação**
   ```bash
   POST /gerar-programacao
   ```

3. **Ver programação da semana**
   ```bash
   GET /programacao-semana?offset=0
   ```

4. **Durante a semana: confirmar coletas**
   ```bash
   POST /confirmar-coleta/1 {"data_realizada": "2026-06-15"}
   POST /confirmar-coleta/2 {"data_realizada": "2026-06-15"}
   ```

5. **Remover se necessário**
   ```bash
   DELETE /programacao/3
   ```

---

## 🛠️ Ferramenta de Teste

### **Opção 1: Interface Swagger (Recomendado)**

Acesse: http://localhost:8000/docs

Você pode:
- Ver todos os endpoints
- Clicar em "Try it out"
- Enviar requests com JSON
- Ver respostas em tempo real

### **Opção 2: Linha de comando (curl)**

```bash
# GET
curl http://localhost:8000/clientes

# POST
curl -X POST http://localhost:8000/clientes/adicionar \
  -H "Content-Type: application/json" \
  -d '{"codigo":"L001","nome":"Teste"}'

# DELETE
curl -X DELETE http://localhost:8000/clientes/1
```

### **Opção 3: Insomnia / Postman**

Ferramentas gráficas para testar APIs:
- Insomnia: https://insomnia.rest
- Postman: https://www.postman.com

---

## 🔐 Códigos HTTP

| Código | Significado | Exemplo |
|--------|-----------|---------|
| `200` | OK — Sucesso | GET, PUT, DELETE bem-sucedidos |
| `201` | Created — Criado | POST que cria novo recurso |
| `400` | Bad Request — Erro na requisição | Dados inválidos, campo obrigatório faltando |
| `404` | Not Found — Não encontrado | Cliente/agendamento inexistente |
| `422` | Unprocessable Entity — Dados inválidos | Tipo de dado errado (string em campo int) |
| `500` | Internal Server Error — Erro do servidor | Bug no código |

---

## 📝 Exemplos Práticos

### **Exemplo 1: Adicionar cliente e gerar programação**

```bash
# 1. Adicionar cliente
curl -X POST http://localhost:8000/clientes/adicionar \
  -H "Content-Type: application/json" \
  -d '{
    "codigo": "L100",
    "nome": "Novo Cliente",
    "cidade": "Araquari",
    "frequencia_dias": 7,
    "fixo": false
  }'

# Resposta: {"cliente_id": 5, ...}

# 2. Gerar programação
curl -X POST http://localhost:8000/gerar-programacao

# Resposta: {"gerados": 1, "ignorados": 0, ...}

# 3. Ver programação
curl http://localhost:8000/programacao-semana

# Resposta: Programação com o novo cliente
```

---

### **Exemplo 2: Confirmar coleta via JavaScript (Frontend)**

```javascript
// No navegador, console ou script
fetch('http://localhost:8000/confirmar-coleta/1', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ data_realizada: '2026-06-15' })
})
  .then(res => res.json())
  .then(data => console.log('Sucesso:', data))
  .catch(err => console.error('Erro:', err));
```

---

## 🚨 Tratamento de Erros Comuns

### **"Cliente com código já existe"**
```json
{
  "erro": "Cliente com código L001 já existe"
}
```
**Solução:** Use um código único ou use PUT para atualizar.

---

### **"Agendamento não encontrado"**
```json
{
  "erro": "Agendamento 999 não encontrado"
}
```
**Solução:** Verifique o ID do agendamento em `/programacao-semana`.

---

### **"Nenhum arquivo enviado"**
```json
{
  "erro": "Nenhum arquivo enviado"
}
```
**Solução:** Certifique-se de estar enviando um arquivo Excel válido.

---

## 📚 Próximos Passos

- Veja [ARCHITECTURE.md](./ARCHITECTURE.md) para entender como funcionam os endpoints internamente
- Veja [SETUP.md](./SETUP.md) para dúvidas de instalação
- Veja [ROADMAP.md](./ROADMAP.md) para melhorias planejadas

---

**Precisa testar?** Acesse http://localhost:8000/docs e clique em "Try it out"! 🚀