import argparse
import math
import os
import sys
from typing import Iterable

import requests


FRASES = [
    "Cliente está com pagamento atrasado",
    "PDV possui débito vencido",
    "Cerveja retornável de 600 ml",
    "O cliente não pagou a duplicata",
    "Volume comercial vendido em hectolitros",
]

BUSCA = "Quem está devendo?"


def gerar_embedding(texto: str, modelo: str, ollama_url: str) -> list[float]:
    # Embedding e a representacao numerica de um texto.
    # O vetor resultante captura caracteristicas semanticas do texto.
    response = requests.post(
        f"{ollama_url.rstrip('/')}/api/embeddings",
        json={
            "model": modelo,
            "prompt": texto,
        },
        timeout=120,
    )
    response.raise_for_status()

    return response.json()["embedding"]


def similaridade_cosseno(vetor_a: Iterable[float], vetor_b: Iterable[float]) -> float:
    # Similaridade de cosseno compara a direcao de dois vetores.
    # Quanto mais perto de 1, mais semanticamente proximos eles tendem a ser.
    a = list(vetor_a)
    b = list(vetor_b)

    produto_interno = sum(x * y for x, y in zip(a, b))
    norma_a = math.sqrt(sum(x * x for x in a))
    norma_b = math.sqrt(sum(y * y for y in b))

    if norma_a == 0 or norma_b == 0:
        return 0.0

    return produto_interno / (norma_a * norma_b)


def mostrar_embedding(texto: str, vetor: list[float]) -> None:
    # Dimensao e a quantidade de numeros do vetor.
    # Aqui mostramos poucos valores para nao poluir o terminal.
    amostra = ", ".join(f"{valor:.5f}" for valor in vetor[:6])
    print(f"Frase: {texto}")
    print(f"Dimensão do vetor: {len(vetor)}")
    print(f"Primeiros valores: [{amostra}, ...]")
    print()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Laboratorio didatico de embeddings com Ollama."
    )
    parser.add_argument(
        "--modelo",
        default=os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest"),
        help="Modelo de embedding do Ollama.",
    )
    parser.add_argument(
        "--ollama-url",
        default=os.getenv("OLLAMA_URL", "http://localhost:11434"),
        help="URL da API do Ollama.",
    )
    args = parser.parse_args()

    print("LABORATÓRIO DE EMBEDDINGS")
    print(f"Modelo: {args.modelo}")
    print(f"Ollama URL: {args.ollama_url}")
    print()

    embeddings = {
        frase: gerar_embedding(frase, args.modelo, args.ollama_url)
        for frase in FRASES
    }

    print("EMBEDDINGS GERADOS")
    print("=" * 60)
    for frase, vetor in embeddings.items():
        mostrar_embedding(frase, vetor)

    print("SIMILARIDADE ENTRE FRASES")
    print("=" * 60)
    for indice, frase_a in enumerate(FRASES):
        for frase_b in FRASES[indice + 1:]:
            similaridade = similaridade_cosseno(
                embeddings[frase_a],
                embeddings[frase_b],
            )
            print(f"{similaridade:.4f} | {frase_a}  <->  {frase_b}")
    print()

    print("BUSCA SEMÂNTICA")
    print("=" * 60)
    print(f"BUSCA: {BUSCA}")
    print()

    embedding_busca = gerar_embedding(BUSCA, args.modelo, args.ollama_url)
    ranking = sorted(
        (
            (similaridade_cosseno(embedding_busca, vetor), frase)
            for frase, vetor in embeddings.items()
        ),
        reverse=True,
    )

    print("RANKING:")
    for posicao, (similaridade, frase) in enumerate(ranking, start=1):
        print(f"{posicao}. {frase}")
        print(f"   similaridade: {similaridade:.4f}")


if __name__ == "__main__":
    main()
