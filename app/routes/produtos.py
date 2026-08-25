from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.produto import ProdutoCreate
from app.services import produto_service


router = APIRouter(
    prefix="/produtos",
    tags=["Produtos"]
)


# CREATE
@router.post("", status_code=201)
def criar_produto(
    produto: ProdutoCreate,
    db: Session = Depends(get_db)
):
    novo_produto = produto_service.criar_produto(
        db,
        produto
    )

    return {
        "mensagem": "Produto cadastrado com sucesso",
        "produto": novo_produto
    }


# READ - LISTAR
@router.get("")
def listar_produtos(
    categoria: str | None = None,
    limite: int = 10,
    db: Session = Depends(get_db)
):
    return produto_service.listar_produtos(
        db,
        categoria,
        limite
    )


# READ - POR ID
@router.get("/{produto_id}")
def buscar_produto(
    produto_id: int,
    db: Session = Depends(get_db)
):
    produto = produto_service.buscar_produto(
        db,
        produto_id
    )

    if produto is None:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado"
        )

    return produto


# UPDATE
@router.put("/{produto_id}")
def atualizar_produto(
    produto_id: int,
    dados: ProdutoCreate,
    db: Session = Depends(get_db)
):
    produto = produto_service.buscar_produto(
        db,
        produto_id
    )

    if produto is None:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado"
        )

    produto = produto_service.atualizar_produto(
        db,
        produto,
        dados
    )

    return {
        "mensagem": "Produto atualizado com sucesso",
        "produto": produto
    }


# DELETE
@router.delete("/{produto_id}")
def excluir_produto(
    produto_id: int,
    db: Session = Depends(get_db)
):
    produto = produto_service.buscar_produto(
        db,
        produto_id
    )

    if produto is None:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado"
        )

    produto_service.excluir_produto(
        db,
        produto
    )

    return {
        "mensagem": "Produto excluído com sucesso",
        "produto_id": produto_id
    }