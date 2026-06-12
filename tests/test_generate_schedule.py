"""
TESTES: generate_schedule.py — Serviço de Geração de Programação

Testa a lógica de geração automática de agendamentos.

Como rodar:
    pytest tests/test_generate_schedule.py -v
    pytest tests/test_generate_schedule.py -v --cov=backend.app.services.generate_schedule
"""

import pytest
from datetime import date, timedelta

from backend.app.models.client import Client
from backend.app.models.schedule import Schedule
from backend.app.services.generate_schedule import (
    gerar_programacao,
    ja_agendado_na_data,
    proxima_data_para_dia,
    ajustar_para_dia_util
)


# ═══════════════════════════════════════════════════════════════════════════════
# TESTES: ja_agendado_na_data() — Validação Anti-Duplicidade
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
class TestJaAgendadoNaData:
    """Testes para detecção de duplicidade"""
    
    def test_nao_agendado_quando_vazio(self, db_session):
        """Schedule vazio não deve detectar agendamento"""
        resultado = ja_agendado_na_data(db_session, "L001", date.today())
        assert resultado == False
    
    def test_detecta_agendamento_exato(self, db_session, schedule_programado):
        """Deve detectar agendamento na mesma data"""
        codigo = schedule_programado.codigo_cliente
        data = schedule_programado.data_coleta
        
        resultado = ja_agendado_na_data(db_session, codigo, data)
        assert resultado == True
    
    def test_nao_detecta_data_diferente(self, db_session, schedule_programado):
        """Não deve detectar agendamento em data diferente"""
        codigo = schedule_programado.codigo_cliente
        data_diferente = schedule_programado.data_coleta + timedelta(days=1)
        
        resultado = ja_agendado_na_data(db_session, codigo, data_diferente)
        assert resultado == False
    
    def test_trata_codigo_com_zeros_esquerda(self, db_session):
        """Deve tratar '015' e '15' como iguais"""
        # Criar agendamento com código "15"
        schedule = Schedule(
            codigo_cliente="15",
            cliente="Teste",
            data_coleta=date.today()
        )
        db_session.add(schedule)
        db_session.commit()
        
        # Verificar que "015" é detectado como duplicado
        assert ja_agendado_na_data(db_session, "015", date.today()) == True
        assert ja_agendado_na_data(db_session, "15", date.today()) == True
    
    def test_nao_detecta_codigo_diferente(self, db_session, schedule_programado):
        """Não deve detectar agendamento de código diferente na mesma data"""
        data = schedule_programado.data_coleta
        codigo_diferente = "L999"
        
        resultado = ja_agendado_na_data(db_session, codigo_diferente, data)
        assert resultado == False


# ═══════════════════════════════════════════════════════════════════════════════
# TESTES: calcular_proxima_data() — Cálculo de Próxima Coleta
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
class TestCalcularProximaData:
    """Testes para cálculo de próxima data de coleta"""
    
    def test_calcula_proxima_frequencia_3_dias(self):
        """Próxima coleta = última + frequência"""
        ultima = date(2026, 6, 10)  # Quarta
        frequencia = 3
        
        proxima = calcular_proxima_data(ultima, frequencia)
        
        assert proxima == date(2026, 6, 13)  # Sábado (3 dias depois)
    
    def test_pula_fim_de_semana(self):
        """Deve ajustar para dia útil se cair no fim de semana"""
        ultima = date(2026, 6, 12)  # Sexta
        frequencia = 3
        
        proxima = calcular_proxima_data(ultima, frequencia)
        
        # 12 + 3 = 15 (segunda), não cai em fim de semana
        assert proxima == date(2026, 6, 15)
        assert proxima.weekday() < 5  # Segunda a sexta
    
    def test_calcula_frequencia_7_dias(self):
        """Frequência de 7 dias = mesma semana do mês anterior"""
        ultima = date(2026, 6, 1)  # Segunda
        frequencia = 7
        
        proxima = calcular_proxima_data(ultima, frequencia)
        
        assert proxima == date(2026, 6, 8)


# ═══════════════════════════════════════════════════════════════════════════════
# TESTES: gerar_programacao() — Geração Completa
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
class TestGerarProgramacao:
    """Testes para geração completa de programação"""
    
    def test_gera_programacao_cliente_fixo(self, db_session, cliente_fixo):
        """Cliente fixo deve gerar agendamentos nos dias fixos"""
        resultado = gerar_programacao(db_session)
        
        assert resultado["gerados"] >= 2  # Pelo menos 2 (Segunda e Quinta)
        assert resultado["ignorados"] == 0
        assert resultado["por_solicitacao"] == 0
        
        # Verificar que schedules foram criados
        schedules = db_session.query(Schedule).filter(
            Schedule.codigo_cliente == cliente_fixo.codigo
        ).all()
        assert len(schedules) >= 2
    
    def test_gera_programacao_cliente_frequencia(self, db_session, cliente_frequencia):
        """Cliente com frequência deve gerar próximas coletas"""
        resultado = gerar_programacao(db_session)
        
        # Deve ter gerado pelo menos 1
        assert resultado["gerados"] >= 1
        
        # Verificar schedule criado
        schedules = db_session.query(Schedule).filter(
            Schedule.codigo_cliente == cliente_frequencia.codigo
        ).all()
        assert len(schedules) >= 1
    
    def test_ignora_cliente_por_solicitacao(self, db_session, cliente_por_solicitacao):
        """Clientes 'Por solicitação' devem ser ignorados"""
        resultado = gerar_programacao(db_session)
        
        assert resultado["por_solicitacao"] >= 1
        
        # Não deve criar agendamentos
        schedules = db_session.query(Schedule).filter(
            Schedule.codigo_cliente == cliente_por_solicitacao.codigo
        ).all()
        assert len(schedules) == 0
    
    def test_evita_duplicacao(self, db_session, cliente_fixo):
        """Não deve duplicar agendamentos"""
        # Primeira geração
        resultado1 = gerar_programacao(db_session)
        
        # Segunda geração
        resultado2 = gerar_programacao(db_session)
        
        # Primeira vez: gerados
        assert resultado1["gerados"] > 0
        
        # Segunda vez: duplicados (não deve gerar de novo)
        assert resultado2["duplicados"] > 0 or resultado2["gerados"] == 0
    
    def test_retorna_estrutura_correta(self, db_com_clientes):
        """Resultado deve ter estrutura correta"""
        resultado = gerar_programacao(db_com_clientes)
        
        assert isinstance(resultado, dict)
        assert "gerados" in resultado
        assert "ignorados" in resultado
        assert "duplicados" in resultado
        assert "por_solicitacao" in resultado
        
        # Valores devem ser inteiros
        assert isinstance(resultado["gerados"], int)
        assert isinstance(resultado["ignorados"], int)
        assert isinstance(resultado["duplicados"], int)
        assert isinstance(resultado["por_solicitacao"], int)


# ═══════════════════════════════════════════════════════════════════════════════
# TESTES: Casos Extremos (Edge Cases)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
class TestEdgeCases:
    """Testes para casos extremos e situações raras"""
    
    def test_banco_vazio_nao_quebra(self, db_session):
        """Geração com banco vazio deve retornar sucesso, não erro"""
        resultado = gerar_programacao(db_session)
        
        assert resultado["gerados"] == 0
        assert isinstance(resultado, dict)
    
    def test_cliente_sem_frequencia(self, db_session):
        """Cliente sem frequência definida deve ser ignorado"""
        cliente = Client(
            codigo="L999",
            nome="Cliente Sem Frequência",
            fixo=False
            # frequencia_dias não preenchido (None)
        )
        db_session.add(cliente)
        db_session.commit()
        
        resultado = gerar_programacao(db_session)
        
        # Não deve tentar gerar
        schedules = db_session.query(Schedule).filter(
            Schedule.codigo_cliente == cliente.codigo
        ).all()
        assert len(schedules) == 0
    
    def test_cliente_fixo_sem_dias_fixos(self, db_session):
        """Cliente fixo sem dias definidos não deve quebrar"""
        cliente = Client(
            codigo="L888",
            nome="Fixo Sem Dias",
            fixo=True
            # dia_fixo não preenchido (None)
        )
        db_session.add(cliente)
        db_session.commit()
        
        # Não deve lançar exceção
        resultado = gerar_programacao(db_session)
        assert isinstance(resultado, dict)