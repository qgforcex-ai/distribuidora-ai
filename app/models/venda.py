from sqlalchemy import Column, Integer, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Venda(Base):
    __tablename__ = "vendas"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    cliente_id = Column(
        Integer,
        ForeignKey("clientes.id"),
        nullable=False
    )

    data_venda = Column(
        DateTime,
        default=datetime.now,
        nullable=False
    )

    valor_total = Column(
        Numeric(10, 2),
        nullable=False,
        default=0
    )

    cliente = relationship(
        "Cliente",
        back_populates="vendas"
    )

    itens = relationship(
        "ItemVenda",
        back_populates="venda",
        cascade="all, delete-orphan"
    )