from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy import func
from app import models
from datetime import date, datetime, time


def total_comprado_por_cliente(db: Session):

    resultado = (
        db.query(
            models.Cliente.id.label("cliente_id"),
            models.Cliente.nome.label("cliente_nome"),
            models.Cliente.cidade.label("cidade"),
            func.sum(
                models.Venda.valor_total
            ).label("total_comprado")
        )
        .join(
            models.Venda,
            models.Venda.cliente_id == models.Cliente.id
        )
        .group_by(
            models.Cliente.id,
            models.Cliente.nome,
            models.Cliente.cidade
        )
        .order_by(
            func.sum(models.Venda.valor_total).desc()
        )
        .all()
    )

    return resultado

def total_por_cliente_categoria(
    db: Session,
    categoria: str
):

    resultado = (
        db.query(
            models.Cliente.id.label("cliente_id"),
            models.Cliente.nome.label("cliente_nome"),
            func.sum(
                models.ItemVenda.subtotal
            ).label("total_comprado")
        )

        .join(
            models.Venda,
            models.Venda.cliente_id == models.Cliente.id
        )

        .join(
            models.ItemVenda,
            models.ItemVenda.venda_id == models.Venda.id
        )

        .join(
            models.Produto,
            models.Produto.id == models.ItemVenda.produto_id
        )

        .filter(
            models.Produto.categoria == categoria
        )

        .group_by(
            models.Cliente.id,
            models.Cliente.nome
        )

        .order_by(
            func.sum(models.ItemVenda.subtotal).desc()
        )

        .all()
    )

    return resultado
def ranking_clientes(
    db: Session,
    data_inicio: date,
    data_fim: date,
    limite: int = 10
):
    inicio = datetime.combine(
        data_inicio,
        time.min
    )

    fim = datetime.combine(
        data_fim,
        time.max
    )

    resultado = (
        db.query(
            models.Cliente.id.label("cliente_id"),
            models.Cliente.nome.label("cliente_nome"),
            models.Cliente.cidade.label("cidade"),

            func.count(
                models.Venda.id
            ).label("quantidade_vendas"),

            func.sum(
                models.Venda.valor_total
            ).label("total_comprado")
        )

        .join(
            models.Venda,
            models.Venda.cliente_id == models.Cliente.id
        )

        .filter(
            models.Venda.data_venda >= inicio,
            models.Venda.data_venda <= fim
        )

        .group_by(
            models.Cliente.id,
            models.Cliente.nome,
            models.Cliente.cidade
        )

        .order_by(
            func.sum(
                models.Venda.valor_total
            ).desc()
        )

        .limit(limite)

        .all()
    )

    return resultado

def clientes_sem_compra(
    db: Session,
    data_inicio: date,
    data_fim: date
):
    inicio = datetime.combine(
        data_inicio,
        time.min
    )

    fim = datetime.combine(
        data_fim,
        time.max
    )

    resultado = (
        db.query(
            models.Cliente.id.label("cliente_id"),
            models.Cliente.nome.label("cliente_nome"),
            models.Cliente.cidade.label("cidade")
        )

        .outerjoin(
            models.Venda,
            (
                (models.Venda.cliente_id == models.Cliente.id)
                &
                (models.Venda.data_venda >= inicio)
                &
                (models.Venda.data_venda <= fim)
            )
        )

        .filter(
            models.Venda.id.is_(None)
        )

        .order_by(
            models.Cliente.nome
        )

        .all()
    )

    return resultado

def comparar_periodos_clientes(
    db: Session,
    anterior_inicio: date,
    anterior_fim: date,
    atual_inicio: date,
    atual_fim: date
):
    ant_inicio = datetime.combine(
        anterior_inicio,
        time.min
    )

    ant_fim = datetime.combine(
        anterior_fim,
        time.max
    )

    atu_inicio = datetime.combine(
        atual_inicio,
        time.min
    )

    atu_fim = datetime.combine(
        atual_fim,
        time.max
    )


    clientes = db.query(models.Cliente).all()

    resultado = []


    for cliente in clientes:

        # ==========================================
        # TOTAL DO PERÍODO ANTERIOR
        # ==========================================

        total_anterior = (
            db.query(
                func.sum(models.Venda.valor_total)
            )
            .filter(
                models.Venda.cliente_id == cliente.id,
                models.Venda.data_venda >= ant_inicio,
                models.Venda.data_venda <= ant_fim
            )
            .scalar()
        )

        # Se SUM retornar NULL
        if total_anterior is None:
            total_anterior = 0


        # ==========================================
        # TOTAL DO PERÍODO ATUAL
        # ==========================================

        total_atual = (
            db.query(
                func.sum(models.Venda.valor_total)
            )
            .filter(
                models.Venda.cliente_id == cliente.id,
                models.Venda.data_venda >= atu_inicio,
                models.Venda.data_venda <= atu_fim
            )
            .scalar()
        )

        if total_atual is None:
            total_atual = 0


        # ==========================================
        # VARIAÇÃO
        # ==========================================

        if total_anterior > 0:

            variacao_percentual = (
                (total_atual - total_anterior)
                / total_anterior
            ) * 100

        else:
            variacao_percentual = None


        resultado.append({
            "cliente_id": cliente.id,
            "cliente": cliente.nome,
            "cidade": cliente.cidade,

            "total_anterior": float(
                total_anterior
            ),

            "total_atual": float(
                total_atual
            ),

            "variacao_percentual": (
                round(
                    float(variacao_percentual),
                    2
                )
                if variacao_percentual is not None
                else None
            )
        })


    return resultado