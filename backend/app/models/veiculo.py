from sqlalchemy import Column, Integer, String, Index
from backend.app.database import Base


class Veiculo(Base):
    __tablename__ = "veiculos"

    id       = Column(Integer, primary_key=True, index=True)
    placa    = Column(String, nullable=False, unique=True, index=True)
    motorista = Column(String, nullable=True)

    __table_args__ = (
        Index("idx_placa_motorista", "placa", "motorista"),
    )