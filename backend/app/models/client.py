from sqlalchemy import Column, Integer, String, Date, Boolean, Index
from backend.app.database import Base


class Client(Base):
    """Cliente com índices para buscas rápidas"""
    
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    
    # ✅ ÍNDICE: Buscas por código
    codigo = Column(String, nullable=False, index=True)
    
    nome = Column(String, nullable=False)
    cidade = Column(String, nullable=True)
    unidade = Column(String, nullable=True)
    observacao = Column(String, nullable=True)
    frequencia_dias = Column(Integer, nullable=True)
    ultima_coleta = Column(Date, nullable=True)
    proxima_coleta = Column(Date, nullable=True)
    
    # ✅ ÍNDICE: Filtrar clientes fixos
    fixo = Column(Boolean, default=False, index=True)
    
    dia_fixo = Column(String, nullable=True)
    
    # ✅ ÍNDICE COMPOSTO: Código + fixo
    __table_args__ = (
        Index('idx_codigo_fixo', 'codigo', 'fixo'),
    )