from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Carga variables desde .env si existe. El .env real no se sube al repo.
load_dotenv()

# Evita avisos molestos de telemetría de ChromaDB.
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import chromadb
import requests
from langchain_text_splitters import RecursiveCharacterTextSplitter


# =========================
# Configuración general
# =========================

BASE_DIR = Path(__file__).resolve().parent
CORPUS_DIR = BASE_DIR / "base_conocimiento"
CHROMA_DIR = BASE_DIR / ".chroma_dni"

COLLECTION_NAME = "dni_rag"

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "nomic-embed-text")
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen2.5:3b")


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


CHUNK_SIZE = _env_int("CHUNK_SIZE", 500)
CHUNK_OVERLAP = _env_int("CHUNK_OVERLAP", 100)
TOP_K = _env_int("TOP_K", 5)

MAX_CONTEXT_CHUNKS = TOP_K

TEMPERATURE = 0.2
NUM_PREDICT = 500

NO_INFO_TEXT = "No tengo esa información en mis fuentes."


@dataclass
class Chunk:
    id: str
    text: str
    source: str
    distance: float | None = None


# =========================
# Utilidades
# =========================

def _ollama_post(endpoint: str, payload: dict[str, Any], timeout: int = 300) -> dict[str, Any]:
    url = f"{OLLAMA_URL}/{endpoint}"

    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as exc:
        raise RuntimeError(
            "No se puede conectar con Ollama. "
            "Comprueba que Ollama está instalado, abierto y escuchando en "
            "http://localhost:11434. También revisa que los modelos estén descargados."
        ) from exc


def embed(text: str) -> list[float]:
    data = _ollama_post(
        "embeddings",
        {
            "model": EMBED_MODEL,
            "prompt": text,
        },
    )

    if "embedding" not in data:
        raise RuntimeError(f"Ollama no devolvió embedding. Respuesta: {data}")

    return data["embedding"]


def _read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _normalizar_texto(texto: str) -> str:
    return "\n".join(line.rstrip() for line in texto.splitlines()).strip()


# =========================
# Carga y chunking
# =========================

def _split_qa_blocks(text: str) -> list[str]:
    """
    Intenta respetar bloques Q:/A: para no separar una pregunta de su respuesta.
    Si el documento no tiene ese formato, devuelve lista vacía.
    """
    lines = text.splitlines()
    blocks: list[str] = []
    current: list[str] = []

    has_qa = any(line.strip().startswith("Q:") for line in lines) and any(
        line.strip().startswith("A:") for line in lines
    )

    if not has_qa:
        return []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("Q:") and current:
            blocks.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)

    if current:
        blocks.append("\n".join(current).strip())

    return [b for b in blocks if b]


def _chunk_document(source: str, text: str) -> list[Chunk]:
    """
    Hace chunking especial para documentos Q:/A: y chunking normal para documentos narrativos.
    """
    text = _normalizar_texto(text)
    qa_blocks = _split_qa_blocks(text)

    chunks: list[Chunk] = []

    if qa_blocks:
        buffer = ""
        idx = 0

        for block in qa_blocks:
            if not buffer:
                buffer = block
            elif len(buffer) + len(block) + 2 <= CHUNK_SIZE:
                buffer += "\n\n" + block
            else:
                chunks.append(
                    Chunk(
                        id=f"{source}__chunk_{idx}",
                        text=buffer.strip(),
                        source=source,
                    )
                )
                idx += 1
                buffer = block

        if buffer:
            chunks.append(
                Chunk(
                    id=f"{source}__chunk_{idx}",
                    text=buffer.strip(),
                    source=source,
                )
            )

        return chunks

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    parts = splitter.split_text(text)

    for idx, part in enumerate(parts):
        clean = part.strip()
        if clean:
            chunks.append(
                Chunk(
                    id=f"{source}__chunk_{idx}",
                    text=clean,
                    source=source,
                )
            )

    return chunks


def _load_corpus_chunks() -> list[Chunk]:
    if not CORPUS_DIR.exists():
        raise FileNotFoundError(
            f"No existe la carpeta {CORPUS_DIR}. "
            "Debe estar en la raíz del proyecto y contener los .txt del corpus DNI."
        )

    txt_files = sorted(CORPUS_DIR.glob("*.txt"))

    if not txt_files:
        raise FileNotFoundError(
            f"No se encontraron archivos .txt en {CORPUS_DIR}."
        )

    chunks: list[Chunk] = []

    for path in txt_files:
        text = _read_txt(path)
        chunks.extend(_chunk_document(path.name, text))

    return chunks


def _corpus_signature() -> str:
    """
    Firma del índice. Si cambia el corpus, el chunking o el modelo de embeddings,
    se fuerza la reindexación.
    """
    h = hashlib.sha256()

    h.update(f"embed_model={EMBED_MODEL}".encode("utf-8"))
    h.update(f"chunk_size={CHUNK_SIZE}".encode("utf-8"))
    h.update(f"chunk_overlap={CHUNK_OVERLAP}".encode("utf-8"))
    h.update(f"index_version=3".encode("utf-8"))

    for path in sorted(CORPUS_DIR.glob("*.txt")):
        h.update(path.name.encode("utf-8"))
        h.update(_read_txt(path).encode("utf-8", errors="ignore"))

    return h.hexdigest()


# =========================
# ChromaDB
# =========================

_client: chromadb.PersistentClient | None = None
_collection: Any | None = None


def _get_client() -> chromadb.PersistentClient:
    global _client

    if _client is None:
        CHROMA_DIR.mkdir(exist_ok=True)
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    return _client


def _collection_needs_reindex(collection: Any, expected_signature: str) -> bool:
    try:
        count = collection.count()
    except Exception:
        return True

    if count == 0:
        return True

    metadata = getattr(collection, "metadata", None) or {}
    current_signature = metadata.get("index_signature")

    return current_signature != expected_signature


def _create_collection(client: chromadb.PersistentClient, signature: str):
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "index_signature": signature,
            "embed_model": EMBED_MODEL,
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
        },
    )


def _index_chunks(collection: Any, chunks: list[Chunk]) -> None:
    for ch in chunks:
        collection.add(
            ids=[ch.id],
            documents=[ch.text],
            metadatas=[
                {
                    "source": ch.source,
                }
            ],
            embeddings=[embed(ch.text)],
        )


def _get_collection():
    """
    Devuelve la colección Chroma. Si la firma del índice no coincide, borra y reindexa.
    """
    global _collection

    if _collection is not None:
        return _collection

    client = _get_client()
    signature = _corpus_signature()

    try:
        collection = client.get_collection(COLLECTION_NAME)

        if _collection_needs_reindex(collection, signature):
            client.delete_collection(COLLECTION_NAME)
            collection = _create_collection(client, signature)
            chunks = _load_corpus_chunks()
            _index_chunks(collection, chunks)

    except Exception:
        collection = _create_collection(client, signature)
        chunks = _load_corpus_chunks()
        _index_chunks(collection, chunks)

    _collection = collection
    return _collection


# =========================
# Retrieval
# =========================

def _retrieve_raw(query: str, k: int = TOP_K) -> list[Chunk]:
    collection = _get_collection()
    query_embedding = embed(query)

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    chunks: list[Chunk] = []

    for idx, doc in enumerate(docs):
        metadata = metas[idx] if idx < len(metas) else {}
        distance = distances[idx] if idx < len(distances) else None
        source = metadata.get("source", "fuente_desconocida")

        chunks.append(
            Chunk(
                id=f"retrieved_{idx}",
                text=doc,
                source=source,
                distance=distance,
            )
        )

    return chunks


def _filter_relevant_chunks(chunks: list[Chunk]) -> list[Chunk]:
    """
    No aplico un umbral duro porque las distancias de ChromaDB pueden variar.
    Para evitar rechazar preguntas válidas, uso los mejores chunks recuperados.
    """
    return chunks[:MAX_CONTEXT_CHUNKS]


def _retrieve(query: str, k: int = TOP_K) -> list[Chunk]:
    raw_chunks = _retrieve_raw(query, k=k)
    return _filter_relevant_chunks(raw_chunks)


# =========================
# Prompt y generación
# =========================

def _build_prompt(question: str, chunks: list[Chunk]) -> str:
    context = "\n\n".join(
        f"[Fuente: {chunk.source}]\n{chunk.text}"
        for chunk in chunks
    )

    return f"""Eres un asistente de la asociación DNI Valencia.

Responde SOLO usando la información del CONTEXTO.
No uses conocimiento externo.
No inventes datos, fechas, horarios, teléfonos, ubicaciones ni nombres propios que no aparezcan en el contexto.

Si la respuesta no está en el contexto, responde exactamente:
"{NO_INFO_TEXT}"

Si hay contradicciones entre fuentes, no las ocultes: explica que hay una contradicción y cita las dos versiones.

No cites fuentes dentro del texto si no es necesario, porque las fuentes se devuelven aparte en el campo "fuentes".

CONTEXTO:
{context}

PREGUNTA:
{question}

RESPUESTA:"""


def _generate(prompt: str) -> tuple[str, dict[str, Any]]:
    start = time.perf_counter()

    data = _ollama_post(
        "generate",
        {
            "model": LLM_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": TEMPERATURE,
                "num_predict": NUM_PREDICT,
            },
        },
        timeout=300,
    )

    end = time.perf_counter()

    response_text = data.get("response", "").strip()

    prompt_tokens = data.get("prompt_eval_count")
    output_tokens = data.get("eval_count")

    eval_duration_ns = data.get("eval_duration")
    eval_duration_s = None
    tokens_s = None

    if eval_duration_ns:
        eval_duration_s = eval_duration_ns / 1_000_000_000

    if output_tokens and eval_duration_s and eval_duration_s > 0:
        tokens_s = output_tokens / eval_duration_s

    metrics = {
        "modelo": LLM_MODEL,
        "embedding_model": EMBED_MODEL,
        "latencia_s": round(end - start, 3),
        "tokens_entrada": prompt_tokens,
        "tokens_salida": output_tokens,
        "tokens_s": round(tokens_s, 2) if tokens_s is not None else None,
    }

    return response_text, metrics


def _is_no_info_answer(answer: str) -> bool:
    normalized = (answer or "").lower().strip()

    return (
        "no tengo esa información" in normalized
        or "no dispongo de esa información" in normalized
        or "no está en mis fuentes" in normalized
    )


def _unique_sources(chunks: list[Chunk]) -> list[str]:
    sources: list[str] = []

    for ch in chunks:
        if ch.source not in sources:
            sources.append(ch.source)

    return sources


# =========================
# Contrato obligatorio
# =========================

def consultar(pregunta: str, conversation_id: str | None = None) -> dict:
    """
    Contrato obligatorio de la práctica.

    Recibe una pregunta y devuelve:
    - respuesta: texto generado
    - fuentes: archivos fuente usados
    - chunks: fragmentos recuperados
    - metricas: tokens y latencia
    - trazas: pasos básicos del agente
    """
    total_start = time.perf_counter()

    pregunta_limpia = (pregunta or "").strip()

    if not pregunta_limpia:
        return {
            "respuesta": NO_INFO_TEXT,
            "fuentes": [],
            "chunks": [],
            "metricas": {
                "modelo": LLM_MODEL,
                "embedding_model": EMBED_MODEL,
                "latencia_s": 0,
                "tokens_entrada": 0,
                "tokens_salida": 0,
                "tokens_s": None,
                "latencia_total_s": 0,
            },
            "trazas": [
                {
                    "paso": "validacion",
                    "detalle": "pregunta_vacia",
                }
            ],
        }

    raw_chunks = _retrieve_raw(pregunta_limpia, k=TOP_K)
    relevant_chunks = _filter_relevant_chunks(raw_chunks)

    raw_sources = _unique_sources(raw_chunks)
    relevant_sources = _unique_sources(relevant_chunks)

    best_distance = raw_chunks[0].distance if raw_chunks else None

    prompt = _build_prompt(pregunta_limpia, relevant_chunks)
    answer, metrics = _generate(prompt)

    total_end = time.perf_counter()

    # Si el propio LLM rechaza, no citamos fuentes irrelevantes.
    if _is_no_info_answer(answer):
        final_sources: list[str] = []
    else:
        # Para no citar demasiados archivos, dejamos solo las fuentes de los chunks más relevantes.
        final_sources = relevant_sources[:3]

    metrics["latencia_total_s"] = round(total_end - total_start, 3)
    metrics["best_distance"] = best_distance
    metrics["similarity_threshold"] = None
    metrics["nota_umbral"] = "No se aplica umbral duro; se usan los mejores chunks recuperados."
    metrics["chunks_recuperados"] = len(raw_chunks)
    metrics["chunks_usados"] = len(relevant_chunks)

    return {
        "respuesta": answer,
        "fuentes": final_sources,
        "chunks": [chunk.text for chunk in relevant_chunks],
        "metricas": metrics,
        "trazas": [
            {
                "paso": "retrieve",
                "k": TOP_K,
                "fuentes_recuperadas": raw_sources,
                "best_distance": best_distance,
            },
            {
                "paso": "seleccion_contexto",
                "criterio": "top chunks recuperados sin umbral duro",
                "chunks_recuperados": len(raw_chunks),
                "chunks_usados": len(relevant_chunks),
                "fuentes_usadas": final_sources,
            },
            {
                "paso": "generate",
                "modelo": LLM_MODEL,
            },
        ],
    }


# =========================
# Modo manual
# =========================

if __name__ == "__main__":
    q = input("Pregunta: ")
    print(json.dumps(consultar(q), ensure_ascii=False, indent=2))