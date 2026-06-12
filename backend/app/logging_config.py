"""
LOGGING CONFIGURATION — Sprint 3

Configuração centralizada de logging para ColetaFlow.

Logs são salvos em: backend/app/logs/coleta_flow.log

O que fica registrado:
- Todas as ações (criar, atualizar, deletar cliente)
- Confirmação de coletas
- Erros e exceções
- Tempo de execução
- Quem fez o quê e quando

Níveis de log:
- DEBUG: Informações detalhadas (desenvolvimento)
- INFO: Ações importantes
- WARNING: Algo não esperado
- ERROR: Erro que não interrompeu execução
- CRITICAL: Erro crítico
"""

import logging
import logging.handlers
import os
from datetime import datetime


def setup_logging():
    """
    Configura logging centralizado para a aplicação.
    
    Cria arquivo de logs em: backend/app/logs/coleta_flow.log
    Rotaciona arquivo quando atinge 10MB (mantém 5 backups)
    """
    
    # Nome do logger
    logger = logging.getLogger("coleta_flow")
    logger.setLevel(logging.DEBUG)  # Captura tudo
    
    # Criar diretório de logs se não existir
    logs_dir = os.path.join(
        os.path.dirname(__file__), 
        "logs"
    )
    os.makedirs(logs_dir, exist_ok=True)
    
    log_file = os.path.join(logs_dir, "coleta_flow.log")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # HANDLER 1: Arquivo (Persistent)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    # Rotating file handler (tira backup quando atinge tamanho)
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=10_000_000,  # 10 MB
        backupCount=5,        # Mantém 5 backups (coleta_flow.log.1, .2, etc)
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)  # Arquivo registra TUDO
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # HANDLER 2: Console (Development)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Console mostra só INFO+
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # FORMATO DAS MENSAGENS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    # Formato detalhado para arquivo
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Formato simples para console
    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    file_handler.setFormatter(detailed_formatter)
    console_handler.setFormatter(simple_formatter)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # ADICIONAR HANDLERS AO LOGGER
    # ═══════════════════════════════════════════════════════════════════════════════
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log inicial
    logger.info("=" * 80)
    logger.info(f"ColetaFlow Logger iniciado - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    return logger


# ═══════════════════════════════════════════════════════════════════════════════
# CRIAR LOGGER GLOBAL
# ═══════════════════════════════════════════════════════════════════════════════

logger = setup_logging()


# ═══════════════════════════════════════════════════════════════════════════════
# EXEMPLOS DE USO
# ═══════════════════════════════════════════════════════════════════════════════

"""
Em qualquer arquivo (ex: routes/clientes.py):

import logging
logger = logging.getLogger("coleta_flow")

@router.post("/clientes/adicionar")
async def adicionar_cliente(...):
    logger.info(f"Adicionando novo cliente: {dados.codigo} - {dados.nome}")
    
    try:
        novo_cliente = Client(...)
        db.add(novo_cliente)
        db.commit()
        logger.info(f"Cliente criado com sucesso: ID={novo_cliente.id}")
        return {...}
    
    except Exception as e:
        logger.error(f"Erro ao adicionar cliente: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno")

@router.post("/confirmar-coleta/{schedule_id}")
async def confirmar_coleta(...):
    logger.info(f"Confirmando coleta: schedule_id={schedule_id}")
    
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        logger.warning(f"Schedule não encontrado: {schedule_id}")
        raise HTTPException(status_code=404, detail="...")
    
    logger.debug(f"Status anterior: {schedule.status}")
    schedule.status = "Concluído"
    db.commit()
    logger.info(f"Coleta confirmada: schedule_id={schedule_id}, novo status=Concluído")
    return {...}
"""


# ═══════════════════════════════════════════════════════════════════════════════
# ARQUIVO DE LOG EXEMPLO
# ═══════════════════════════════════════════════════════════════════════════════

"""
Conteúdo de backend/app/logs/coleta_flow.log:

================================================================================
2026-06-11 14:30:15 - coleta_flow - INFO - [logging_config.py:95] - ColetaFlow Logger iniciado - 2026-06-11 14:30:15
================================================================================
2026-06-11 14:30:25 - coleta_flow - INFO - [clientes.py:45] - Adicionando novo cliente: L001 - Supermercado ABC
2026-06-11 14:30:25 - coleta_flow - DEBUG - [clientes.py:50] - Validando código único...
2026-06-11 14:30:26 - coleta_flow - INFO - [clientes.py:52] - Cliente criado com sucesso: ID=1
2026-06-11 14:31:10 - coleta_flow - INFO - [clientes.py:85] - Confirmando coleta: schedule_id=5
2026-06-11 14:31:10 - coleta_flow - DEBUG - [clientes.py:87] - Status anterior: Programado
2026-06-11 14:31:11 - coleta_flow - INFO - [clientes.py:92] - Coleta confirmada: schedule_id=5, novo status=Concluído
2026-06-11 14:32:45 - coleta_flow - WARNING - [clientes.py:120] - Schedule não encontrado: 999
2026-06-11 14:35:20 - coleta_flow - ERROR - [clientes.py:150] - Erro ao deletar cliente: Database locked
"""