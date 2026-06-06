import json
import os
from pathlib import Path
from statistics import mean

from dotenv import load_dotenv
from datasets import Dataset

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)


BENCHMARK_PATH = Path("benchmark/benchmark.json")
OUTPUT_PATH = Path("evaluacion/ragas_results.json")

# Según el benchmark, el mejor modelo general es qwen en PoliGPT.
MODELO_A_EVALUAR = "qwen"


def cargar_resultados_modelo():
    datos = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))

    filtrados = [
        r for r in datos
        if r.get("modelo") == MODELO_A_EVALUAR
    ]

    if not filtrados:
        modelos = sorted(set(r.get("modelo") for r in datos))
        raise ValueError(
            f"No hay resultados para el modelo {MODELO_A_EVALUAR}. "
            f"Modelos disponibles: {modelos}"
        )

    return filtrados


def preparar_dataset(resultados):
    filas = []

    for r in resultados:
        chunks = r.get("chunks") or []
        if not chunks:
            chunks = [""]

        filas.append({
            "user_input": r.get("pregunta", ""),
            "response": r.get("respuesta", ""),
            "retrieved_contexts": chunks,
            "reference": r.get("ground_truth", ""),
        })

    return Dataset.from_list(filas)


def main():
    load_dotenv()

    if "POLIGPT_API_KEY" not in os.environ:
        raise RuntimeError("Falta POLIGPT_API_KEY en .env")

    if "POLIGPT_BASE_URL" not in os.environ:
        raise RuntimeError("Falta POLIGPT_BASE_URL en .env")

    resultados = cargar_resultados_modelo()
    dataset = preparar_dataset(resultados)

    # LLM evaluador. Uso qwen como juez porque en las pruebas ha sido el más estable.
    llm = ChatOpenAI(
        model="qwen",
        base_url=os.environ["POLIGPT_BASE_URL"],
        api_key=os.environ["POLIGPT_API_KEY"],
        temperature=0,
    )

    # Embeddings usados por RAGAs para calcular las métricas semánticas.
    embeddings = OpenAIEmbeddings(
        model="bge-m3",
        base_url=os.environ["POLIGPT_BASE_URL"],
        api_key=os.environ["POLIGPT_API_KEY"],
    )

    resultado = evaluate(
        dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        ],
        llm=llm,
        embeddings=embeddings,
    )

    df = resultado.to_pandas()

    columnas_metricas = [
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
    ]

    salida = {
        "modelo_evaluado": MODELO_A_EVALUAR,
        "llm_evaluador": "qwen",
        "embedding_evaluador": "bge-m3",
        "num_preguntas": len(resultados),
        "promedios": {},
        "resultados_por_pregunta": [],
    }

    for col in columnas_metricas:
        if col in df.columns:
            valores = []

            for v in df[col].tolist():
                try:
                    fv = float(v)
                    if str(fv).lower() != "nan":
                        valores.append(fv)
                except Exception:
                    pass

            salida["promedios"][col] = round(mean(valores), 4) if valores else None

    for i, row in df.iterrows():
        original = resultados[i]

        item = {
            "id": original.get("id"),
            "pregunta": original.get("pregunta"),
            "modelo": original.get("modelo"),
            "respuesta": original.get("respuesta"),
            "fuentes": original.get("fuentes"),
            "ground_truth": original.get("ground_truth"),
            "metricas_ragas": {},
        }

        for col in columnas_metricas:
            if col in df.columns:
                try:
                    item["metricas_ragas"][col] = round(float(row[col]), 4)
                except Exception:
                    item["metricas_ragas"][col] = None

        salida["resultados_por_pregunta"].append(item)

    OUTPUT_PATH.write_text(
        json.dumps(salida, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(json.dumps(salida["promedios"], ensure_ascii=False, indent=2))
    print(f"\nGuardado en: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()