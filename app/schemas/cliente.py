from pydantic import BaseModel


class ClienteCreate(BaseModel):
    nome: str
    cidade: str
    limite_credito: float