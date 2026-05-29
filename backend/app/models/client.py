from sqlalchemy import Column, Integer, String, Date
from backend.app.database import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String)
    nome = Column(String)
    cidade = Column(String)
    ultima_coleta = Column(Date)
    proxima_coleta = Column(Date)