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
        from datetime import date, timedelta
        
        # 1. Pegamos o cliente do banco de teste
        cliente_real = db_session.query(Client).first()
        
        # 2. Descobrimos qual é a segunda-feira da semana passada baseada em hoje
        hoje = date.today()
        segunda_atual = hoje - timedelta(days=hoje.weekday())
        segunda_semana_passada = segunda_atual - timedelta(weeks=1)
        
        # 3. Amarramos o agendamento a esse cliente usando a data correta (semana passada)
        schedule_programado.codigo_cliente = cliente_real.codigo
        schedule_programado.status = "Concluído"
        schedule_programado.data_coleta = segunda_semana_passada  # Cai direto na lista da semana passada
            
        db_session.commit()

        # 4. Executa a função do backend
        fechar_semana(db_session)
        
        # 5. Recarrega o cliente da sessão para ler as mudanças físicas do banco
        db_session.refresh(cliente_real)
        
        # 6. Validação final
        assert cliente_real.ultima_coleta is not None
        assert cliente_real.ultima_coleta == segunda_semana_passada