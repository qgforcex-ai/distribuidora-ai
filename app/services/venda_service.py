from decimal import Decimal

from sqlalchemy.orm import Session

from app import models
from app.schemas.venda import VendaCreate


def criar_venda(
    db: Session,
    dados: VendaCreate
):
    # --------------------------------------------------------
    # 1. Verifica se o cliente existe
    # --------------------------------------------------------

    cliente = (
        db.query(models.Cliente)
        .filter(models.Cliente.id == dados.cliente_id)
        .first()
    )

    if cliente is None:
        raise ValueError("Cliente não encontrado")


    # --------------------------------------------------------
    # 2. Cria a venda inicialmente com total zero
    # --------------------------------------------------------

    venda = models.Venda(
        cliente_id=dados.cliente_id,
        valor_total=Decimal("0.00")
    )

    db.add(venda)

    # Precisamos do ID da venda antes do commit final
    db.flush()


    # --------------------------------------------------------
    # 3. Processa os produtos
    # --------------------------------------------------------

    valor_total = Decimal("0.00")

    for item in dados.itens:

        produto = (
            db.query(models.Produto)
            .filter(models.Produto.id == item.produto_id)
            .first()
        )

        if produto is None:
            db.rollback()
            raise ValueError(
                f"Produto {item.produto_id} não encontrado"
            )

        preco = produto.preco

        subtotal = preco * item.quantidade

        novo_item = models.ItemVenda(
            venda_id=venda.id,
            produto_id=produto.id,
            quantidade=item.quantidade,
            preco_unitario=preco,
            subtotal=subtotal
        )

        db.add(novo_item)

        valor_total += subtotal


    # --------------------------------------------------------
    # 4. Atualiza total da venda
    # --------------------------------------------------------

    venda.valor_total = valor_total


    # --------------------------------------------------------
    # 5. Confirma tudo
    # --------------------------------------------------------

    db.commit()
    db.refresh(venda)

    return venda

def buscar_venda(
    db: Session,
    venda_id: int
):
    return (
        db.query(models.Venda)
        .filter(models.Venda.id == venda_id)
        .first()
    )