from sqlalchemy import Boolean, Column, Date, Integer, String, Numeric
from sqlalchemy.orm import relationship

from app.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    codigo_pdv = Column(String(50), nullable=False, unique=True, index=True)
    nome = Column(String(150), nullable=True)
    cidade = Column(String(100), nullable=True)
    bairro = Column(String(150), nullable=True)
    status_cliente = Column(String(50), nullable=True)
    rn = Column(String(20), nullable=True)
    proxima_visita = Column(Date, nullable=True)
    base_pdv_atual = Column(Boolean, nullable=False, default=False)
    limite_credito = Column(Numeric(10, 2), nullable=False)
    vendas = relationship("Venda", back_populates="cliente")
    base_pdv_periodos = relationship("BasePdvPeriodo", back_populates="cliente")
