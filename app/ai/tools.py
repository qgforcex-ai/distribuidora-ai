from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.venda import Venda


def ranking_clientes(
    db: Session,
    data_inicio: str,
    data_fim: str
):
    from sqlalchemy import func

    resultado = (
        db.query(
            Cliente.id,
            Cliente.nome,
            func.sum(Venda.valor_total).label("total_comprado")
        )
        .join(Venda, Venda.cliente_id == Cliente.id)
        .filter(Venda.data_venda >= data_inicio)
        .filter(Venda.data_venda <= f"{data_fim} 23:59:59")
        .group_by(Cliente.id, Cliente.nome)
        .order_by(func.sum(Venda.valor_total).desc())
        .all()
    )

    return [
        {
            "cliente_id": item.id,
            "cliente": item.nome,
            "total_comprado": float(item.total_comprado)
        }
        for item in resultado
    ]