from sqlalchemy import Column, Integer, Date, DateTime, Numeric, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Venda(Base):
    __tablename__ = "vendas"
    __table_args__ = (
        UniqueConstraint(
            "cliente_id",
            "periodo",
            "operacao",
            "origem",
            name="uk_vendas_cliente_periodo_operacao_origem"
        ),
        Index("idx_vendas_cliente_periodo", "cliente_id", "periodo"),
        Index("idx_vendas_periodo_operacao", "periodo", "operacao"),
        Index("idx_vendas_periodo", "periodo"),
        Index("idx_vendas_importacao_id", "importacao_id"),
    )

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

    periodo = Column(
        Date,
        nullable=False
    )

    data_venda = Column(
        DateTime,
        default=datetime.now,
        nullable=True
    )

    valor_total = Column(
        Numeric(10, 2),
        nullable=False,
        default=0
    )

    operacao = Column(
        Integer,
        nullable=False,
        default=1
    )

    origem = Column(
        String(50),
        nullable=True
    )

    importacao_id = Column(
        Integer,
        ForeignKey("importacoes.id"),
        nullable=True
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

    importacao = relationship(
        "Importacao",
        back_populates="vendas"
    )
