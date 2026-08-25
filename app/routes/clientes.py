from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.cliente import ClienteCreate
from app.services import cliente_service


router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"]
)





# CREATE
@router.post("", status_code=201)
def criar_cliente(
    cliente: ClienteCreate,
    db: Session = Depends(get_db)
):
    novo_cliente = cliente_service.criar_cliente(
        db,
        cliente
    )

    return {
        "mensagem": "Cliente cadastrado com sucesso",
        "cliente": novo_cliente
    }


# READ - LISTAR
@router.get("")
def listar_clientes(
    cidade: str | None = None,
    limite: int = 10,
    db: Session = Depends(get_db)
):
    return cliente_service.listar_clientes(
        db,
        cidade,
        limite
    )


# READ - POR ID
@router.get("/{cliente_id}")
def buscar_cliente(
    cliente_id: int,
    db: Session = Depends(get_db)
):
    cliente = cliente_service.buscar_cliente(
        db,
        cliente_id
    )

    if cliente is None:
        raise HTTPException(
            status_code=404,
            detail="Cliente não encontrado"
        )

    return cliente


# UPDATE
@router.put("/{cliente_id}")
def atualizar_cliente(
    cliente_id: int,
    dados: ClienteCreate,
    db: Session = Depends(get_db)
):
    cliente = cliente_service.buscar_cliente(
        db,
        cliente_id
    )

    if cliente is None:
        raise HTTPException(
            status_code=404,
            detail="Cliente não encontrado"
        )

    cliente = cliente_service.atualizar_cliente(
        db,
        cliente,
        dados
    )

    return {
        "mensagem": "Cliente atualizado com sucesso",
        "cliente": cliente
    }


# DELETE
@router.delete("/{cliente_id}")
def excluir_cliente(
    cliente_id: int,
    db: Session = Depends(get_db)
):
    cliente = cliente_service.buscar_cliente(
        db,
        cliente_id
    )

    if cliente is None:
        raise HTTPException(
            status_code=404,
            detail="Cliente não encontrado"
        )

    cliente_service.excluir_cliente(
        db,
        cliente
    )

    return {
        "mensagem": "Cliente excluído com sucesso",
        "cliente_id": cliente_id
    }