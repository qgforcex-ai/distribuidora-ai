from sqlalchemy import Column, Integer, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class ItemVenda(Base):
    __tablename__ = "itens_venda"
    __table_args__ = (
        UniqueConstraint(
            "venda_id",
            "produto_id",
            name="uk_itens_venda_produto"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    venda_id = Column(
        Integer,
        ForeignKey("vendas.id"),
        nullable=False
    )

    produto_id = Column(
        Integer,
        ForeignKey("produtos.id"),
        nullable=False
    )

    quantidade = Column(
        Numeric(15, 4),
        nullable=False
    )

    fator_hl = Column(
        Numeric(15, 6),
        nullable=True
    )

    volume_hl = Column(
        Numeric(15, 6),
        nullable=False,
        default=0
    )

    preco_unitario = Column(
        Numeric(15, 6),
        nullable=False
    )

    subtotal = Column(
        Numeric(15, 2),
        nullable=False
    )

    venda = relationship(
        "Venda",
        back_populates="itens"
    )

    produto = relationship(
        "Produto",
        back_populates="itens_venda"
    )
