from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date
from app.database import get_db
from app.services import analise_service


router = APIRouter(
    prefix="/analises",
    tags=["Análises"]
)


@router.get("/clientes/total-comprado")
def total_comprado_por_cliente(
    db: Session = Depends(get_db)
):

    resultados = (
        analise_service.total_comprado_por_cliente(db)
    )

    return [
        {
            "cliente_id": linha.cliente_id,
            "cliente": linha.cliente_nome,
            "cidade": linha.cidade,
            "total_comprado": float(linha.total_comprado)
        }
        for linha in resultados
    ]


@router.get("/clientes/por-categoria")
def total_por_cliente_categoria(
    categoria: str,
    db: Session = Depends(get_db)
):
    resultados = (
        analise_service.total_por_cliente_categoria(
            db,
            categoria
        )
    )

    return [
        {
            "cliente_id": linha.cliente_id,
            "cliente": linha.cliente_nome,
            "categoria": categoria,
            "total_comprado": float(linha.total_comprado)
        }
        for linha in resultados
    ]


@router.get("/clientes/ranking")
def ranking_clientes(
    data_inicio: date,
    data_fim: date,
    limite: int = 10,
    db: Session = Depends(get_db)
):
    resultados = analise_service.ranking_clientes(
        db,
        data_inicio,
        data_fim,
        limite
    )

    return [
        {
            "posicao": posicao,
            "cliente_id": linha.cliente_id,
            "cliente": linha.cliente_nome,
            "cidade": linha.cidade,
            "quantidade_vendas": linha.quantidade_vendas,
            "total_comprado": float(
                linha.total_comprado
            )
        }

        for posicao, linha in enumerate(
            resultados,
            start=1
        )
    ]


@router.get("/clientes/sem-compra")
def clientes_sem_compra(
    data_inicio: date,
    data_fim: date,
    db: Session = Depends(get_db)
):
    resultados = analise_service.clientes_sem_compra(
        db,
        data_inicio,
        data_fim
    )

    return [
        {
            "cliente_id": linha.cliente_id,
            "cliente": linha.cliente_nome,
            "cidade": linha.cidade
        }
        for linha in resultados
    ]


@router.get("/clientes/comparar-periodos")
def comparar_periodos_clientes(
    anterior_inicio: date,
    anterior_fim: date,
    atual_inicio: date,
    atual_fim: date,
    db: Session = Depends(get_db)
):
    return analise_service.comparar_periodos_clientes(
        db,
        anterior_inicio,
        anterior_fim,
        atual_inicio,
        atual_fim
    )