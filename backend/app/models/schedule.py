from sqlalchemy import Column, Integer, String, Date, Boolean, Index
from backend.app.database import Base


class Schedule(Base):
    """Agendamento com índices para buscas rápidas"""
    
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    
    # ✅ ÍNDICE: Relacionamento com cliente
    codigo_cliente = Column(String, nullable=False, index=True)
    
    cliente = Column(String, nullable=False)
    unidade = Column(String, nullable=True)
    
    # ✅ ÍNDICE: Filtrar por data (MUITO usado!)
    data_coleta = Column(Date, nullable=True, index=True)
    
    dia_semana = Column(String, nullable=True)
    
    # ✅ ÍNDICE: Filtrar por status
    status = Column(String, default="Programado", index=True)
    
    fixo = Column(Boolean, default=False)
    
    # ✅ ÍNDICES COMPOSTOS
    __table_args__ = (
        # Validar duplicação (cliente + data)
        Index('idx_codigo_data', 'codigo_cliente', 'data_coleta'),
        
        # Filtrar por status + data
        Index('idx_status_data', 'status', 'data_coleta'),
    )