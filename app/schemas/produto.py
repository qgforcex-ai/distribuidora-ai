from pydantic import BaseModel

class ProdutoCreate(BaseModel):
    codigo: str
    descricao: str
    categoria: str
    preco: float