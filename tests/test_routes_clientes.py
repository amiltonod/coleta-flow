"""
TESTES: Rotas HTTP — Testes de Integração

Testa endpoints completos via HTTP (não unitário).

Como rodar:
    pytest tests/test_routes_clientes.py -v
    pytest tests/test_routes_clientes.py::test_listar_clientes -v
"""

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORTS NECESSÁRIOS
# ═══════════════════════════════════════════════════════════════════════════════

# Estes imports são necessários para o pytest
from backend.app.models.client import Client
from backend.app.models.schedule import Schedule

import pytest
from datetime import date


# ═══════════════════════════════════════════════════════════════════════════════
# TESTES: GET /clientes — Listar Todos
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestListarClientes:
    """Testes para GET /clientes"""
    
    def test_listar_vazio(self, test_client):
        """Retorna lista vazia quando não há clientes"""
        response = test_client.get("/clientes")
        
        assert response.status_code == 200
        data = response.json()
        assert data["clientes"] == []
    
    def test_listar_com_clientes(self, test_client, db_session, cliente_fixo):
        """Retorna clientes quando existem"""
        response = test_client.get("/clientes")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["clientes"]) == 1
        assert data["clientes"][0]["codigo"] == "L001"
        assert data["clientes"][0]["nome"] == "Cliente Fixo"


# ═══════════════════════════════════════════════════════════════════════════════
# TESTES: GET /clientes/buscar — Busca
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestBuscarClientes:
    """Testes para GET /clientes/buscar"""
    
    def test_busca_minimo_2_caracteres(self, test_client):
        """Rejeita busca com menos de 2 caracteres"""
        response = test_client.get("/clientes/buscar?q=a")
        
        assert response.status_code == 400
        assert "pelo menos 2 caracteres" in response.json()["detail"]
    
    def test_busca_por_codigo(self, test_client, db_session, cliente_fixo):
        """Encontra cliente por código"""
        response = test_client.get("/clientes/buscar?q=L001")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["resultados"]) == 1
        assert data["resultados"][0]["codigo"] == "L001"
    
    def test_busca_por_nome(self, test_client, db_session, cliente_fixo):
        """Encontra cliente por nome"""
        response = test_client.get("/clientes/buscar?q=Cliente")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["resultados"]) == 1
    
    def test_busca_vazia(self, test_client, db_session):
        """Retorna vazio quando não encontra"""
        response = test_client.get("/clientes/buscar?q=INEXISTENTE")
        
        assert response.status_code == 200
        data = response.json()
        assert data["resultados"] == []


# ═══════════════════════════════════════════════════════════════════════════════
# TESTES: POST /clientes/adicionar — Criar
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestAdicionarCliente:
    """Testes para POST /clientes/adicionar"""
    
    def test_adiciona_com_dados_validos(self, test_client):
        """Cria cliente com dados válidos"""
        dados = {
            "codigo": "L100",
            "nome": "Novo Cliente",
            "cidade": "Araquari",
            "frequencia_dias": 7
        }
        response = test_client.post("/clientes/adicionar", json=dados)
        
        assert response.status_code == 201
        data = response.json()
        assert data["mensagem"] == "Cliente adicionado com sucesso"
        assert data["cliente_id"] == 1
        assert data["codigo"] == "L100"
    
    def test_rejeita_codigo_vazio(self, test_client):
        """Rejeita cliente sem código"""
        dados = {
            "codigo": "",
            "nome": "Teste"
        }
        response = test_client.post("/clientes/adicionar", json=dados)
        
        assert response.status_code == 422  # Validation error
    
    def test_rejeita_duplicado(self, test_client, db_session, cliente_fixo):
        """Rejeita cliente com código duplicado"""
        dados = {
            "codigo": "L001",  # Código que já existe
            "nome": "Outro Cliente"
        }
        response = test_client.post("/clientes/adicionar", json=dados)
        
        assert response.status_code == 400
        assert "já existe" in response.json()["detail"]
    
    def test_valida_frequencia_minima(self, test_client):
        """Rejeita frequência < 1"""
        dados = {
            "codigo": "L200",
            "nome": "Cliente",
            "frequencia_dias": 0  # Inválido
        }
        response = test_client.post("/clientes/adicionar", json=dados)
        
        assert response.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# TESTES: PUT /clientes/{id} — Atualizar
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestAtualizarCliente:
    """Testes para PUT /clientes/{id}"""
    
    def test_atualiza_com_sucesso(self, test_client, db_session, cliente_fixo):
        """Atualiza cliente com dados válidos"""
        dados = {
            "frequencia_dias": 5,
            "observacao": "Mudou frequência"
        }
        response = test_client.put("/clientes/1", json=dados)
        
        assert response.status_code == 200
        data = response.json()
        assert data["mensagem"] == "Cliente atualizado com sucesso"
    
    def test_cliente_inexistente(self, test_client):
        """Retorna 404 para cliente que não existe"""
        dados = {"frequencia_dias": 5}
        response = test_client.put("/clientes/999", json=dados)
        
        assert response.status_code == 404
        assert "não encontrado" in response.json()["detail"]
    
    def test_valida_tipos(self, test_client, db_session, cliente_fixo):
        """Rejeita tipo de dado inválido"""
        dados = {
            "frequencia_dias": "não é número"  # Inválido
        }
        response = test_client.put("/clientes/1", json=dados)
        
        assert response.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# TESTES: DELETE /clientes/{id} — Deletar
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestDeletarCliente:
    """Testes para DELETE /clientes/{id}"""
    
    def test_deleta_com_sucesso(self, test_client, db_session, cliente_fixo):
        """Deleta cliente e retorna sucesso"""
        response = test_client.delete("/clientes/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["mensagem"] == "Cliente deletado com sucesso"
    
    def test_cliente_inexistente(self, test_client):
        """Retorna 404 para cliente que não existe"""
        response = test_client.delete("/clientes/999")
        
        assert response.status_code == 404
        assert "não encontrado" in response.json()["detail"]
    
    def test_deleta_agendamentos_associados(self, test_client, db_session, schedule_programado):
        """Deleta também agendamentos do cliente"""
        # Verificar que existe agendamento
        schedules_antes = db_session.query(Schedule).count()
        assert schedules_antes > 0
        
        response = test_client.delete("/clientes/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["agendamentos_removidos"] > 0


# ═══════════════════════════════════════════════════════════════════════════════
# TESTES: POST /confirmar-coleta/{id} — Confirmar
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestConfirmarColeta:
    """Testes para POST /confirmar-coleta/{id}"""
    
    def test_confirma_coleta(self, test_client, db_session, schedule_programado):
        """Confirma coleta e atualiza status"""
        dados = {"data_realizada": "2026-06-11"}
        response = test_client.post("/confirmar-coleta/1", json=dados)
        
        assert response.status_code == 200
        data = response.json()
        assert data["mensagem"] == "Coleta confirmada com sucesso"
        assert data["status"] == "Concluído"
    
    def test_atualiza_cliente_ultima_coleta(self, test_client, db_session, schedule_programado, cliente_fixo):
        """Atualiza ultima_coleta do cliente"""
        dados = {"data_realizada": "2026-06-11"}
        response = test_client.post("/confirmar-coleta/1", json=dados)
        
        assert response.status_code == 200
        
        # Verificar que cliente foi atualizado
        cliente_atualizado = db_session.query(Client).filter(Client.id == cliente_fixo.id).first()
        assert cliente_atualizado.ultima_coleta == date(2026, 6, 11)
    
    def test_schedule_inexistente(self, test_client):
        """Retorna 404 para schedule que não existe"""
        dados = {"data_realizada": "2026-06-11"}
        response = test_client.post("/confirmar-coleta/999", json=dados)
        
        assert response.status_code == 404
        assert "não encontrado" in response.json()["detail"]
    
    def test_data_invalida(self, test_client, db_session, schedule_programado):
        """Rejeita data inválida"""
        dados = {"data_realizada": "data-invalida"}
        response = test_client.post("/confirmar-coleta/1", json=dados)
        
        assert response.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# TESTES: Fluxo Completo (End-to-End)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestFluxoCompleto:
    """Testes de fluxo completo: criar → atualizar → confirmar → deletar"""
    
    def test_fluxo_criar_atualizar_deletar(self, test_client):
        """Teste E2E: criar cliente, atualizar, depois deletar"""
        
        # 1. CRIAR
        dados_criar = {
            "codigo": "L999",
            "nome": "Cliente Teste",
            "frequencia_dias": 7
        }
        response = test_client.post("/clientes/adicionar", json=dados_criar)
        assert response.status_code == 201
        cliente_id = response.json()["cliente_id"]
        
        # 2. VERIFICAR que foi criado
        response = test_client.get("/clientes")
        assert len(response.json()["clientes"]) == 1
        
        # 3. ATUALIZAR
        dados_atualizar = {"frequencia_dias": 5}
        response = test_client.put(f"/clientes/{cliente_id}", json=dados_atualizar)
        assert response.status_code == 200
        
        # 4. DELETAR
        response = test_client.delete(f"/clientes/{cliente_id}")
        assert response.status_code == 200
        
        # 5. VERIFICAR que foi deletado
        response = test_client.get("/clientes")
        assert len(response.json()["clientes"]) == 0


