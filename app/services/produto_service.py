from sqlalchemy.orm import Session

from app import models
from app.schemas.produto import ProdutoCreate


def criar_produto(
    db: Session,
    dados: ProdutoCreate
):
    produto = models.Produto(
        codigo=dados.codigo,
        descricao=dados.descricao,
        categoria=dados.categoria,
        preco=dados.preco
    )

    db.add(produto)
    db.commit()
    db.refresh(produto)

    return produto


def listar_produtos(
    db: Session,
    categoria: str | None = None,
    limite: int = 10
):
    query = db.query(models.Produto)

    if categoria:
        query = query.filter(
            models.Produto.categoria == categoria
        )

    return query.limit(limite).all()


def buscar_produto(
    db: Session,
    produto_id: int
):
    return (
        db.query(models.Produto)
        .filter(models.Produto.id == produto_id)
        .first()
    )


def atualizar_produto(
    db: Session,
    produto,
    dados: ProdutoCreate
):
    produto.codigo = dados.codigo
    produto.descricao = dados.descricao
    produto.categoria = dados.categoria
    produto.preco = dados.preco

    db.commit()
    db.refresh(produto)

    return produto


def excluir_produto(
    db: Session,
    produto
):
    db.delete(produto)
    db.commit()