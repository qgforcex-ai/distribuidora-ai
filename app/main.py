from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Cliente(BaseModel):
    nome: str
    cidade: str
    limite_credito: float


@app.get("/")
def inicio():
    return {"message": "Hot reload funcionando!"}


@app.get("/clientes/{cliente_id}")
def buscar_cliente(cliente_id: int):
    return {
        "cliente_id": cliente_id,
        "mensagem": f"Buscando cliente {cliente_id}"
    }    


@app.get("/clientes")
def listar_clientes(cidade: str | None = None, limite: int = 10):
    return {
        "cidade": cidade,
        "limite": limite
    }    

#######################################################################

@app.post("/clientes", status_code=201)
def criar_cliente(cliente: Cliente):
    return {
        "mensagem": "Cliente recebido com sucesso",
        "cliente": cliente
    }   

@app.put("/clientes/{cliente_id}")
def atualizar_cliente(cliente_id: int, cliente: Cliente):
    return {
        "mensagem": "Cliente atualizado com sucesso",
        "cliente_id": cliente_id,
        "novos_dados": cliente
    }     
@app.delete("/clientes/{cliente_id}")
def excluir_cliente(cliente_id: int):
    return {
        "mensagem": "Cliente excluído com sucesso",
        "cliente_id": cliente_id
    }