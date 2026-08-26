from sqlalchemy import Column, Integer, String, Numeric
from sqlalchemy.orm import relationship

from app.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    cidade = Column(String(100), nullable=False)
    limite_credito = Column(Numeric(10, 2), nullable=False)
    vendas = relationship("Venda", back_populates="cliente")