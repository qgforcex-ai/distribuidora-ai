import requests
from lab_embeddings import gerar_embedding

QDRANT_URL = "http://localhost:6333"
COLLECTION = "lab_embeddings"

OLLAMA_URL = "http://localhost:11434"
MODELO = "nomic-embed-text:latest"

FRASES = [
    "Cliente está com pagamento atrasado",
    "PDV possui débito vencido",
    "Cerveja retornável de 600 ml",
    "O cliente não pagou a duplicata",
    "Volume comercial vendido em hectolitros",
]


def info_collection():
    url = f"{QDRANT_URL}/collections/{COLLECTION}"

    response = requests.get(url)
    response.raise_for_status()

    return response.json()

def inserir_point(point_id: int, texto: str):
    # 1. Transforma o texto em um vetor de 768 dimensões
    vetor = gerar_embedding(
        texto=texto,
        modelo=MODELO,
        ollama_url=OLLAMA_URL,
    )

    print(f"Embedding gerado: {len(vetor)} dimensões")

    # 2. Endpoint do Qdrant onde gravamos os points
    url = f"{QDRANT_URL}/collections/{COLLECTION}/points"

    # 3. Montamos o point
    dados = {
        "points": [
            {
                "id": point_id,
                "vector": vetor,
                "payload": {
                    "texto": texto
                }
            }
        ]
    }

    # 4. Enviamos para o Qdrant
    response = requests.put(
        url,
        params={"wait": "true"},
        json=dados,
    )

    response.raise_for_status()

    return response.json()


def buscar_point(point_id: int):
    url = f"{QDRANT_URL}/collections/{COLLECTION}/points/{point_id}"

    response = requests.get(url)
    response.raise_for_status()

    return response.json()


def inserir_frases():
    points = []

    for point_id, texto in enumerate(FRASES, start=1):
        print(f"Gerando embedding: {texto}")

        vetor = gerar_embedding(
            texto=texto,
            modelo=MODELO,
            ollama_url=OLLAMA_URL,
        )

        points.append(
            {
                "id": point_id,
                "vector": vetor,
                "payload": {
                    "texto": texto
                }
            }
        )

    url = f"{QDRANT_URL}/collections/{COLLECTION}/points"

    response = requests.put(
        url,
        params={"wait": "true"},
        json={"points": points},
    )

    response.raise_for_status()

    return response.json()

def buscar_similares(texto_busca: str, limite: int = 3):
    vetor_busca = gerar_embedding(
        texto=texto_busca,
        modelo=MODELO,
        ollama_url=OLLAMA_URL,
    )

    url = f"{QDRANT_URL}/collections/{COLLECTION}/points/query"

    dados = {
        "query": vetor_busca,
        "limit": limite,
        "with_payload": True,
    }

    response = requests.post(
        url,
        json=dados,
    )

    response.raise_for_status()

    return response.json()

if __name__ == "__main__":
    busca = "Quem está devendo?"

    resultado = buscar_similares(
        texto_busca=busca,
        limite=3,
    )

    print(resultado)

#if __name__ == "__main__":
 #   texto = "Cliente está com pagamento atrasado"

  #  resultado = inserir_point(
   #     point_id=1,
    #    texto=texto,
    #)

    #print(resultado)