from sqlalchemy import Column, Integer, String, Numeric

from app.database import Base


class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)

    codigo = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True
    )

    descricao = Column(
        String(200),
        nullable=False
    )

    categoria = Column(
        String(100),
        nullable=False
    )

    preco = Column(
        Numeric(10, 2),
        nullable=False
    )