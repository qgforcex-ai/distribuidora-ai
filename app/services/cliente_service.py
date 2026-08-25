from sqlalchemy.orm import Session
from app import models
from app.schemas.cliente import ClienteCreate


def criar_cliente(db: Session, dados: ClienteCreate):

    cliente = models.Cliente(
        nome=dados.nome,
        cidade=dados.cidade,
        limite_credito=dados.limite_credito
    )

    db.add(cliente)
    db.commit()
    db.refresh(cliente)

    return cliente


def listar_clientes(
    db: Session,
    cidade: str | None = None,
    limite: int = 10
):
    query = db.query(models.Cliente)

    if cidade:
        query = query.filter(
            models.Cliente.cidade == cidade
        )

    return query.limit(limite).all()


def buscar_cliente(db: Session, cliente_id: int):

    return (
        db.query(models.Cliente)
        .filter(models.Cliente.id == cliente_id)
        .first()
    )


def atualizar_cliente(
    db: Session,
    cliente,
    dados: ClienteCreate
):
    cliente.nome = dados.nome
    cliente.cidade = dados.cidade
    cliente.limite_credito = dados.limite_credito

    db.commit()
    db.refresh(cliente)

    return cliente


def excluir_cliente(db: Session, cliente):

    db.delete(cliente)
    db.commit()