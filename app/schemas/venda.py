from pydantic import BaseModel


class ItemVendaCreate(BaseModel):
    produto_id: int
    quantidade: int


class VendaCreate(BaseModel):
    cliente_id: int
    itens: list[ItemVendaCreate]