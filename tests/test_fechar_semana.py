import pytest
from datetime import date
from backend.app.services.fechar_semana import fechar_semana
from backend.app.models.controle import Controle
from backend.app.models.client import Client

@pytest.mark.unit
class TestFecharSemana:
    """Testes para fechar_semana service"""
    
    def test_marca_semana_fechada(self, db_session, schedule_programado):
        """Deve marcar última semana como fechada"""
        resultado = fechar_semana(db_session)
        
        assert resultado is not None
        
        # Verificar que registrou em Controle
        controle = db_session.query(Controle).first()
        assert controle is not None
        assert controle.ultima_semana_fechada is not None
    
    def test_atualiza_ultima_coleta(self, db_session, schedule_programado):
        """Deve atualizar ultima_coleta dos clientes"""
        fechar_semana(db_session)
        
        # Verificar que cliente foi atualizado
        cliente = db_session.query(Client).first()
        assert cliente.ultima_coleta is not None