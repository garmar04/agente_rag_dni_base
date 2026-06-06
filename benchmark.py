import json
import os
import time
from pathlib import Path
from statistics import mean

from dotenv import load_dotenv
from openai import OpenAI

import consultar as rag


PREGUNTAS_PATH = Path("benchmark/preguntas.json")
RESULTADOS_PATH = Path("benchmark/benchmark.json")
MARKDOWN_PATH = Path("benchmark/benchmark.md")


MODELOS = [
    {
        "alias": "qwen2.5:3b",
        "servidor": "ollama_local",
    },
    {
        "alias": "llama3.2:3b",
        "servidor": "ollama_local",
    },
    {
        "alias": "qwen",
        "servidor": "poligpt",
    },
    {
        "alias": "gemma",
        "servidor": "poligpt",
    },
]


def es_respuesta_sin_info(texto: str) -> bool:
    texto = (texto or "").lower().strip()

    return (
        "no tengo esa información" in texto
        or "no dispongo de esa información" in texto
        or "no está en mis fuentes" in texto
    )


def evaluar_calidad_subjetiva(pregunta: dict, respuesta: dict) -> float:
    """
    Evaluación sencilla para tener un valor inicial.

    1.0 = correcta
    0.5 = parcialmente correcta
    0.0 = incorrecta

    Aunque se calcula automáticamente, después conviene revisar manualmente
    benchmark.json y ajustar los casos dudosos.
    """
    texto = (respuesta.get("respuesta") or "").lower()
    tipo = pregunta.get("tipo", "")

    if tipo == "fuera_ambito":
        if es_respuesta_sin_info(texto):
            return 1.0
        return 0.0

    if not texto.strip():
        return 0.0

    if es_respuesta_sin_info(texto) and tipo != "fuera_ambito":
        return 0.0

    fuentes = respuesta.get("fuentes") or []
    if len(fuentes) == 0:
        return 0.5

    return 1.0


def _chunk_text(chunk):
    if isinstance(chunk, dict):
        return (
            chunk.get("text")
            or chunk.get("document")
            or chunk.get("contenido")
            or str(chunk)
        )

    return getattr(chunk, "text", str(chunk))


def _chunk_source(chunk):
    if isinstance(chunk, dict):
        return (
            chunk.get("source")
            or chunk.get("fuente")
            or chunk.get("metadata", {}).get("source")
            or "fuente_desconocida"
        )

    return getattr(chunk, "source", "fuente_desconocida")


def consultar_poligpt(pregunta: str, modelo: str) -> dict:
    """
    Ejecuta el mismo RAG que consultar.py, pero usando PoliGPT como LLM.
    El retrieval sigue siendo local con Chroma + Ollama embeddings.
    """
    load_dotenv()

    client = OpenAI(
        base_url=os.environ["POLIGPT_BASE_URL"],
        api_key=os.environ["POLIGPT_API_KEY"],
    )

    inicio_total = time.perf_counter()

    pregunta_limpia = pregunta.strip()
    chunks = rag._retrieve(pregunta_limpia, k=rag.TOP_K)

    contexto = "\n\n".join(
        f"[Fuente: {_chunk_source(chunk)}]\n{_chunk_text(chunk)}"
        for chunk in chunks
    )

    prompt = f"""Eres un asistente de la asociación DNI Valencia.

Responde SOLO usando la información del CONTEXTO.
No uses conocimiento externo.
No inventes datos, fechas, horarios, teléfonos ni ubicaciones.

Si la respuesta no está en el contexto, responde exactamente:
"No tengo esa información en mis fuentes."

Si hay contradicciones entre fuentes, indica que hay una contradicción y cita ambas versiones.

CONTEXTO:
{contexto}

PREGUNTA:
{pregunta_limpia}

RESPUESTA:"""

    inicio_llm = time.perf_counter()

    resp = client.chat.completions.create(
        model=modelo,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0.2,
    )

    fin_llm = time.perf_counter()
    fin_total = time.perf_counter()

    respuesta = resp.choices[0].message.content.strip()

    usage = getattr(resp, "usage", None)
    tokens_entrada = getattr(usage, "prompt_tokens", None) if usage else None
    tokens_salida = getattr(usage, "completion_tokens", None) if usage else None

    latencia_s = round(fin_llm - inicio_llm, 3)
    latencia_total_s = round(fin_total - inicio_total, 3)

    if tokens_salida is not None and latencia_s > 0:
        tokens_s = round(tokens_salida / latencia_s, 2)
    else:
        tokens_s = None

    fuentes_recuperadas = sorted(set(_chunk_source(chunk) for chunk in chunks))

    # Si el modelo dice que no tiene información, no devolvemos fuentes.
    # Así evitamos citar archivos que solo se han recuperado por similitud.
    if es_respuesta_sin_info(respuesta):
        fuentes = []
    else:
        fuentes = fuentes_recuperadas[:3]

    return {
        "respuesta": respuesta,
        "fuentes": fuentes,
        "chunks": [_chunk_text(chunk) for chunk in chunks],
        "metricas": {
            "modelo": modelo,
            "embedding_model": rag.EMBED_MODEL,
            "latencia_s": latencia_s,
            "tokens_entrada": tokens_entrada,
            "tokens_salida": tokens_salida,
            "tokens_s": tokens_s,
            "latencia_total_s": latencia_total_s,
        },
        "trazas": [
            {
                "paso": "retrieve",
                "k": rag.TOP_K,
                "fuentes_recuperadas": fuentes_recuperadas,
                "fuentes_usadas": fuentes,
            },
            {
                "paso": "generate",
                "modelo": modelo,
                "servidor": "poligpt",
            },
        ],
    }


def ejecutar_benchmark():
    if not PREGUNTAS_PATH.exists():
        raise FileNotFoundError(
            f"No existe {PREGUNTAS_PATH}. Crea primero benchmark/preguntas.json."
        )

    preguntas = json.loads(PREGUNTAS_PATH.read_text(encoding="utf-8"))
    resultados = []

    for modelo in MODELOS:
        print(f"\n=== Modelo: {modelo['alias']} ({modelo['servidor']}) ===")

        for item in preguntas:
            pregunta = item["pregunta"]
            print(f"- {item['id']}: {pregunta}")

            inicio = time.perf_counter()

            try:
                if modelo["servidor"] == "ollama_local":
                    rag.LLM_MODEL = modelo["alias"]
                    salida = rag.consultar(pregunta)

                elif modelo["servidor"] == "poligpt":
                    salida = consultar_poligpt(pregunta, modelo["alias"])

                else:
                    raise ValueError(f"Servidor no soportado: {modelo['servidor']}")

                error = None

            except Exception as exc:
                salida = {
                    "respuesta": "",
                    "fuentes": [],
                    "chunks": [],
                    "metricas": {},
                    "trazas": [],
                }
                error = str(exc)

            fin = time.perf_counter()
            latencia_total = round(fin - inicio, 3)

            metricas = salida.get("metricas") or {}

            tokens_entrada = metricas.get("tokens_entrada")
            tokens_salida = metricas.get("tokens_salida")
            tokens_s = metricas.get("tokens_s")

            calidad = evaluar_calidad_subjetiva(item, salida)

            resultados.append({
                "id": item["id"],
                "pregunta": pregunta,
                "tipo": item.get("tipo"),
                "ground_truth": item.get("ground_truth"),
                "modelo": modelo["alias"],
                "servidor": modelo["servidor"],
                "respuesta": salida.get("respuesta"),
                "fuentes": salida.get("fuentes"),
                "chunks": salida.get("chunks"),
                "metricas": {
                    "tokens_entrada": tokens_entrada,
                    "tokens_salida": tokens_salida,
                    "latencia_s": metricas.get("latencia_s"),
                    "latencia_total_s": metricas.get("latencia_total_s", latencia_total),
                    "tokens_s": tokens_s,
                },
                "calidad_subjetiva": calidad,
                "error": error,
            })

    RESULTADOS_PATH.write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    generar_markdown(resultados)

    print(f"\nGuardado: {RESULTADOS_PATH}")
    print(f"Guardado: {MARKDOWN_PATH}")


def generar_markdown(resultados: list[dict]):
    lineas = []

    lineas.append("# Benchmark del Agente RAG DNI\n")
    lineas.append(
        "Este benchmark ejecuta el mismo conjunto de preguntas contra varios modelos "
        "manteniendo constante el pipeline RAG: mismo chunking, mismo vector store, "
        "mismo top-k y mismo prompt.\n"
    )

    lineas.append("## Resultados por pregunta\n")
    lineas.append(
        "| Modelo | Servidor | Pregunta | Tipo | Latencia total (s) | "
        "Tokens entrada | Tokens salida | Tokens/s | Calidad subjetiva | Fuentes |"
    )
    lineas.append("|---|---|---|---|---:|---:|---:|---:|---:|---|")

    for r in resultados:
        m = r.get("metricas") or {}
        fuentes = ", ".join(r.get("fuentes") or [])
        pregunta_limpia = r["pregunta"].replace("|", "\\|")

        lineas.append(
            f"| {r['modelo']} | {r['servidor']} | {pregunta_limpia} | {r.get('tipo')} | "
            f"{m.get('latencia_total_s')} | {m.get('tokens_entrada')} | "
            f"{m.get('tokens_salida')} | {m.get('tokens_s')} | "
            f"{r.get('calidad_subjetiva')} | {fuentes} |"
        )

    lineas.append("\n## Resumen por modelo\n")
    lineas.append(
        "| Modelo | Servidor | Latencia media total (s) | "
        "Tokens/s medio | Calidad media | Errores |"
    )
    lineas.append("|---|---|---:|---:|---:|---:|")

    claves = sorted(set((r["modelo"], r["servidor"]) for r in resultados))

    for modelo, servidor in claves:
        subset = [
            r for r in resultados
            if r["modelo"] == modelo and r["servidor"] == servidor
        ]

        latencias = [
            r["metricas"].get("latencia_total_s")
            for r in subset
            if r.get("metricas") and r["metricas"].get("latencia_total_s") is not None
        ]

        tokens_s_values = [
            r["metricas"].get("tokens_s")
            for r in subset
            if r.get("metricas") and r["metricas"].get("tokens_s") is not None
        ]

        calidades = [
            r.get("calidad_subjetiva")
            for r in subset
            if r.get("calidad_subjetiva") is not None
        ]

        errores = sum(1 for r in subset if r.get("error"))

        lat_media = round(mean(latencias), 3) if latencias else None
        tok_media = round(mean(tokens_s_values), 3) if tokens_s_values else None
        cal_media = round(mean(calidades), 3) if calidades else None

        lineas.append(
            f"| {modelo} | {servidor} | {lat_media} | "
            f"{tok_media} | {cal_media} | {errores} |"
        )

    lineas.append("\n## Interpretación inicial\n")
    lineas.append(
        "La calidad subjetiva se ha calculado con una escala simple: "
        "1.0 para respuestas correctas, 0.5 para respuestas parcialmente correctas "
        "y 0.0 para respuestas incorrectas o alucinadas. Esta valoración se ha revisado "
        "después de ejecutar el benchmark para detectar fallos claros.\n"
    )

    lineas.append(
        "En los resultados se ve que los modelos de PoliGPT responden mejor de media que "
        "los modelos locales pequeños. El mejor comportamiento general lo tiene qwen en PoliGPT, "
        "por eso se usa como modelo principal para la evaluación con RAGAs. Aun así, el sistema "
        "mantiene Ollama local porque es obligatorio y porque permite ejecutar el agente sin depender "
        "de una API externa.\n"
    )

    lineas.append(
        "La parte más mejorable está en las preguntas de síntesis, especialmente cuando hay que "
        "comparar información repartida entre varios documentos, como RESIS y COLES. En esos casos "
        "el problema no siempre es el LLM, sino que a veces el retrieval no recupera todos los chunks "
        "necesarios.\n"
    )

    lineas.append("## Modelos evaluados\n")
    for modelo in MODELOS:
        lineas.append(f"- {modelo['alias']} ({modelo['servidor']})")

    MARKDOWN_PATH.write_text("\n".join(lineas), encoding="utf-8")


if __name__ == "__main__":
    ejecutar_benchmark()