"""
PYTEST CONFIGURATION — conftest.py

Configuração centralizada e fixtures compartilhadas para todos os testes.

Fixtures são funções que preparam dados para teste (tipo setup/teardown).
Compartilhadas automaticamente por todos os testes.

Como rodar testes:
    pytest tests/ -v                    # Todos os testes com verbosidade
    pytest tests/ --cov=backend.app     # Com cobertura
    pytest tests/ --cov=backend.app -v  # Ambos
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import date, timedelta

from backend.app.database import Base
from backend.app.models.client import Client
from backend.app.models.schedule import Schedule
from backend.app.models.controle import Controle


# ═══════════════════════════════════════════════════════════════════════════════
# BANCO DE DADOS DE TESTE (EM MEMÓRIA)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="function")
def db_session():
    """
    Cria um banco SQLite EM MEMÓRIA para cada teste.
    
    Vantagens:
    - Rápido (não toca disco)
    - Isolado (cada teste começa limpo)
    - Determinístico (sem dependências entre testes)
    
    Uso: passar 'db_session' como parâmetro em qualquer teste
    """
    # Criar engine em memória
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    
    # Criar tabelas
    Base.metadata.create_all(engine)
    
    # Criar session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    # Cleanup
    session.close()


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES DE DADOS DE TESTE
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def cliente_fixo(db_session):
    """Cria cliente com coleta FIXA (Segunda, Quinta)"""
    cliente = Client(
        codigo="L001",
        nome="Cliente Fixo",
        cidade="Araquari",
        unidade="Matriz",
        fixo=True,
        dia_fixo="Segunda,Quinta"
    )
    db_session.add(cliente)
    db_session.commit()
    db_session.refresh(cliente)
    return cliente


@pytest.fixture
def cliente_frequencia(db_session):
    """Cria cliente com coleta POR FREQUÊNCIA (a cada 7 dias)"""
    cliente = Client(
        codigo="L002",
        nome="Cliente Frequência",
        cidade="Joinville",
        frequencia_dias=7,
        ultima_coleta=date.today() - timedelta(days=7),
        fixo=False
    )
    db_session.add(cliente)
    db_session.commit()
    db_session.refresh(cliente)
    return cliente


@pytest.fixture
def cliente_por_solicitacao(db_session):
    """Cria cliente 'Por solicitação' (não deve agendar automaticamente)"""
    cliente = Client(
        codigo="L003",
        nome="Cliente Solicitação",
        observacao="Por solicitação",
        frequencia_dias=7,
        ultima_coleta=date.today() - timedelta(days=7),
        fixo=False
    )
    db_session.add(cliente)
    db_session.commit()
    db_session.refresh(cliente)
    return cliente


@pytest.fixture
def schedule_programado(db_session, cliente_fixo):
    """Cria agendamento em status 'Programado'"""
    schedule = Schedule(
        codigo_cliente=cliente_fixo.codigo,
        cliente=cliente_fixo.nome,
        unidade=cliente_fixo.unidade,
        data_coleta=date.today(),
        dia_semana="Segunda",
        status="Programado",
        fixo=True
    )
    db_session.add(schedule)
    db_session.commit()
    db_session.refresh(schedule)
    return schedule


@pytest.fixture
def schedule_concluido(db_session, cliente_frequencia):
    """Cria agendamento em status 'Concluído'"""
    schedule = Schedule(
        codigo_cliente=cliente_frequencia.codigo,
        cliente=cliente_frequencia.nome,
        data_coleta=date.today() - timedelta(days=1),
        status="Concluído"
    )
    db_session.add(schedule)
    db_session.commit()
    db_session.refresh(schedule)
    return schedule


@pytest.fixture
def db_com_clientes(db_session, cliente_fixo, cliente_frequencia, cliente_por_solicitacao):
    """Prepara banco com 3 tipos de clientes"""
    return db_session


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES PARA TESTES DE API (FastAPI TestClient)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def test_client(db_session):
    """
    Cria um TestClient FastAPI para testes de integração HTTP.
    
    Uso: 
        response = test_client.get("/clientes")
        response = test_client.post("/clientes/adicionar", json={...})
    """
    from fastapi.testclient import TestClient
    from backend.app.main import app
    from backend.app.database import get_db
    
    # Override o get_db para usar nosso banco de teste
    def override_get_db():
        return db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    return TestClient(app)


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO GLOBAL DO PYTEST
# ═══════════════════════════════════════════════════════════════════════════════

def pytest_configure(config):
    """Configuração inicial do pytest"""
    config.addinivalue_line(
        "markers", "unit: marca teste unitário"
    )
    config.addinivalue_line(
        "markers", "integration: marca teste de integração"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# EXEMPLO DE COMO USAR FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

"""
def test_cliente_fixo_tem_dias_fixos(cliente_fixo):
    '''Testa que cliente fixo tem dias fixos configurados'''
    assert cliente_fixo.fixo == True
    assert cliente_fixo.dia_fixo == "Segunda,Quinta"

def test_banco_vazio(db_session):
    '''Testa que cada teste começa com banco vazio'''
    clientes = db_session.query(Client).all()
    assert len(clientes) == 0

def test_db_com_clientes_populado(db_com_clientes):
    '''Testa que fixture prepara dados corretamente'''
    clientes = db_com_clientes.query(Client).all()
    assert len(clientes) == 3
    assert clientes[0].fixo == True
    assert clientes[1].fixo == False

def test_rotas_com_client(test_client):
    '''Testa rotas HTTP com TestClient'''
    response = test_client.get("/clientes")
    assert response.status_code == 200
    data = response.json()
    assert "clientes" in data
"""