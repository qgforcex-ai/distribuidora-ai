from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.venda import VendaCreate
from app.services import venda_service


router = APIRouter(
    prefix="/vendas",
    tags=["Vendas"]
)


@router.post("", status_code=201)
def criar_venda(
    venda: VendaCreate,
    db: Session = Depends(get_db)
):
    try:

        nova_venda = venda_service.criar_venda(
            db,
            venda
        )

        return {
            "mensagem": "Venda cadastrada com sucesso",
            "venda_id": nova_venda.id,
            "cliente_id": nova_venda.cliente_id,
            "valor_total": float(nova_venda.valor_total)
        }

    except ValueError as erro:

        raise HTTPException(
            status_code=400,
            detail=str(erro)
        )

@router.get("/{venda_id}")
def buscar_venda(
    venda_id: int,
    db: Session = Depends(get_db)
):
    venda = venda_service.buscar_venda(
        db,
        venda_id
    )

    if venda is None:
        raise HTTPException(
            status_code=404,
            detail="Venda não encontrada"
        )

    return {
        "id": venda.id,

        "data_venda": venda.data_venda,

        "valor_total": float(venda.valor_total),

        "cliente": {
            "id": venda.cliente.id,
            "nome": venda.cliente.nome,
            "cidade": venda.cliente.cidade
        },

        "itens": [
            {
                "id": item.id,

                "produto": {
                    "id": item.produto.id,
                    "codigo": item.produto.codigo,
                    "descricao": item.produto.descricao,
                    "categoria": item.produto.categoria
                },

                "quantidade": item.quantidade,

                "preco_unitario": float(
                    item.preco_unitario
                ),

                "subtotal": float(
                    item.subtotal
                )
            }

            for item in venda.itens
        ]
    }    