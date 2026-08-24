from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app import models
from app.schemas.cliente import ClienteCreate


router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"]
)


# ============================================================
# SESSÃO COM O BANCO
# ============================================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# CREATE
# POST /clientes
# ============================================================

@router.post("", status_code=201)
def criar_cliente(
    cliente: ClienteCreate,
    db: Session = Depends(get_db)
):
    novo_cliente = models.Cliente(
        nome=cliente.nome,
        cidade=cliente.cidade,
        limite_credito=cliente.limite_credito
    )

    db.add(novo_cliente)
    db.commit()
    db.refresh(novo_cliente)

    return {
        "mensagem": "Cliente cadastrado com sucesso",
        "cliente": novo_cliente
    }


# ============================================================
# READ - LISTAR
# GET /clientes
# ============================================================

@router.get("")
def listar_clientes(
    cidade: str | None = None,
    limite: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(models.Cliente)

    if cidade:
        query = query.filter(
            models.Cliente.cidade == cidade
        )

    return query.limit(limite).all()


# ============================================================
# READ - POR ID
# GET /clientes/1
# ============================================================

@router.get("/{cliente_id}")
def buscar_cliente(
    cliente_id: int,
    db: Session = Depends(get_db)
):
    cliente = (
        db.query(models.Cliente)
        .filter(models.Cliente.id == cliente_id)
        .first()
    )

    if cliente is None:
        raise HTTPException(
            status_code=404,
            detail="Cliente não encontrado"
        )

    return cliente


# ============================================================
# UPDATE
# PUT /clientes/1
# ============================================================

@router.put("/{cliente_id}")
def atualizar_cliente(
    cliente_id: int,
    dados: ClienteCreate,
    db: Session = Depends(get_db)
):
    cliente = (
        db.query(models.Cliente)
        .filter(models.Cliente.id == cliente_id)
        .first()
    )

    if cliente is None:
        raise HTTPException(
            status_code=404,
            detail="Cliente não encontrado"
        )

    cliente.nome = dados.nome
    cliente.cidade = dados.cidade
    cliente.limite_credito = dados.limite_credito

    db.commit()
    db.refresh(cliente)

    return {
        "mensagem": "Cliente atualizado com sucesso",
        "cliente": cliente
    }


# ============================================================
# DELETE
# DELETE /clientes/1
# ============================================================

@router.delete("/{cliente_id}")
def excluir_cliente(
    cliente_id: int,
    db: Session = Depends(get_db)
):
    cliente = (
        db.query(models.Cliente)
        .filter(models.Cliente.id == cliente_id)
        .first()
    )

    if cliente is None:
        raise HTTPException(
            status_code=404,
            detail="Cliente não encontrado"
        )

    db.delete(cliente)
    db.commit()

    return {
        "mensagem": "Cliente excluído com sucesso",
        "cliente_id": cliente_id
    }