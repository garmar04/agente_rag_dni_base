# Agente RAG DNI

## Descripción del proyecto

Este proyecto consiste en un agente RAG que responde preguntas sobre la asociación DNI Valencia usando una base de conocimiento formada por documentos de texto. La idea es que el sistema no responda solo con conocimiento interno del modelo, sino que primero busque información en los documentos del corpus y después genere una respuesta usando esos fragmentos como contexto.

El agente está pensado para contestar preguntas sobre qué es DNI, sus proyectos principales, desayunos solidarios, RESIS, COLES, horarios, formas de participar, valores de la asociación y otras cuestiones que aparecen en los documentos proporcionados.

El objetivo de esta entrega ha sido llegar a Banda 8, por lo que además del pipeline RAG básico se ha añadido un benchmark con cuatro modelos, una evaluación con RAGAs y dos métricas propias.

## Ejecución rápida desde cero en Windows

Esta sección está pensada para poder levantar el proyecto desde cero en un ordenador Windows, como el del aula.

### 1. Clonar el repositorio

```bash
git clone https://github.com/garmar04/agente_rag_dni_base.git
cd agente_rag_dni_base
```

### 2. Crear el entorno virtual

```bash
python -m venv .venv
```

### 3. Activar el entorno virtual

En Windows:

```bash
.venv\Scripts\activate
```

Si PowerShell da problemas de permisos, se puede activar desde `cmd` con:

```bash
.venv\Scripts\activate.bat
```

Cuando esté activado, debería aparecer `(.venv)` al principio de la línea de comandos.

### 4. Instalar dependencias

Para levantar el agente principal, se pueden instalar primero las dependencias mínimas:

```bash
python -m pip install requests==2.32.3 python-dotenv==1.0.1 chromadb==0.5.23 langchain-text-splitters==0.3.5
```

Después se instalan las dependencias principales del agente:

```bash
python -m pip install requests==2.32.3 python-dotenv==1.0.1 chromadb==0.5.23 langchain-text-splitters==0.3.5
```

Si durante la instalación completa aparece algún error relacionado con paquetes auxiliares de RAGAs o `datasets`, el agente principal puede seguir funcionando siempre que las dependencias mínimas anteriores estén instaladas.

### 5. Preparar Ollama

El sistema principal funciona con Ollama local. Primero hay que comprobar que Ollama está instalado:

```bash
ollama --version
```

Si Ollama no está en ejecución, se puede arrancar con:

```bash
ollama serve
```

Después, en otra terminal, hay que descargar los modelos necesarios:

```bash
ollama pull nomic-embed-text
ollama pull qwen2.5:3b
```

El modelo `nomic-embed-text` se usa para generar los embeddings y `qwen2.5:3b` es el modelo local utilizado por defecto para generar las respuestas.

Para repetir también el benchmark local completo, se necesita además:

```bash
ollama pull llama3.2:3b
```

### 6. Ejecutar una consulta de prueba

Desde la raíz del proyecto:

```bash
python -c "from consultar import consultar; print(consultar('¿Qué es DNI?'))"
```

También se puede ejecutar:

```bash
python consultar.py
```

La primera ejecución puede tardar un poco más porque se genera el índice vectorial con ChromaDB a partir de los documentos de `base_conocimiento/`. En mi caso, después de esperar un rato, la consulta terminó respondiendo correctamente. Las siguientes ejecuciones deberían ser más rápidas porque el índice ya queda generado.

## Estructura del proyecto

La estructura principal del repositorio es la siguiente:

```text
.
├── base_conocimiento/
│   └── documentos .txt del corpus DNI
├── benchmark/
│   ├── benchmark.json
│   ├── benchmark.md
│   └── preguntas.json
├── evaluacion/
│   ├── evaluar_ragas.py
│   ├── ragas_results.json
│   └── metricas_propias.md
├── benchmark.py
├── consultar.py
├── features.json
├── requirements.txt
├── README.md
├── AI_USAGE.md
├── GRUPO.md
└── .env.example
```

El fichero principal es `consultar.py`, que expone la función obligatoria:

```python
def consultar(pregunta: str, conversation_id: str | None = None) -> dict:
```

Esta función devuelve un diccionario con la respuesta generada, las fuentes usadas, los chunks recuperados, métricas básicas y trazas del proceso.

## Funcionamiento general del agente

El agente sigue un flujo RAG bastante clásico:

1. Carga los documentos `.txt` de la carpeta `base_conocimiento`.
2. Divide los documentos en fragmentos más pequeños.
3. Genera embeddings de esos fragmentos usando Ollama.
4. Guarda los vectores en ChromaDB.
5. Cuando llega una pregunta, genera el embedding de la pregunta.
6. Busca los chunks más parecidos en la base vectorial.
7. Construye un prompt con la pregunta y el contexto recuperado.
8. Llama al modelo de lenguaje.
9. Devuelve la respuesta junto con fuentes, chunks, métricas y trazas.

También se ha intentado que el agente no invente información. Si la respuesta no aparece en el corpus, el prompt fuerza al modelo a contestar:

```text
No tengo esa información en mis fuentes.
```

Además, si el modelo responde eso, el sistema devuelve la lista de fuentes vacía para no citar documentos que realmente no justifican la respuesta.

## Decisiones de chunking

Para dividir los documentos se ha usado `RecursiveCharacterTextSplitter`, con esta configuración:

```python
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
```

He elegido un tamaño de 500 caracteres porque permite que cada chunk tenga suficiente contexto sin ser demasiado largo. El overlap de 100 ayuda a que no se pierda información importante cuando una frase queda justo en el límite entre dos fragmentos.

Además, se ha añadido un tratamiento especial para documentos con formato `Q:` / `A:`. Esto ayuda a mantener juntas las preguntas y sus respuestas en documentos tipo FAQ, porque si se separan demasiado el retrieval puede recuperar una pregunta sin su respuesta o al revés.

Aun así, el retrieval no es perfecto. En algunas preguntas de comparación, por ejemplo entre RESIS y COLES, el sistema no siempre recupera los documentos más adecuados. Esa es una de las limitaciones principales que se comentan más adelante.

## ChromaDB e indexado

El proyecto usa ChromaDB persistente para guardar los embeddings de los chunks. La carpeta del índice es:

```text
.chroma_dni/
```

Esta carpeta no se incluye en la entrega final porque se puede regenerar automáticamente al ejecutar el proyecto. Así se evita entregar una base vectorial antigua si cambia el corpus, el modelo de embeddings o la forma de hacer chunking.

En la primera ejecución puede tardar un poco más porque tiene que indexar todos los documentos. Las siguientes ejecuciones son más rápidas.

## Modelos utilizados

Para el benchmark se han probado cuatro modelos, dos locales con Ollama y dos mediante PoliGPT:

| Modelo        | Servidor     |
| ------------- | ------------ |
| `qwen2.5:3b`  | Ollama local |
| `llama3.2:3b` | Ollama local |
| `qwen`        | PoliGPT      |
| `gemma`       | PoliGPT      |

La idea era comparar modelos pequeños ejecutados en local con modelos disponibles mediante PoliGPT. Para que la comparación fuera lo más justa posible, se mantuvo el mismo pipeline RAG en todos los casos: mismos documentos, mismo chunking, mismo retrieval y mismas preguntas. Lo único que cambia es el modelo que genera la respuesta final.

## Modelo elegido

En el benchmark final, el modelo con mejor calidad subjetiva fue `qwen` en PoliGPT. En general dio respuestas más completas y resolvió mejor algunas preguntas que los modelos locales pequeños.

Aun así, también se ha tenido en cuenta que `gemma` en PoliGPT responde de forma más corta y con menor latencia media. Por eso se ha mantenido `gemma` como modelo evaluado en RAGAs, ya que permite analizar un modelo más rápido y estable en generación, aunque `qwen` haya obtenido la mejor puntuación subjetiva en el benchmark.

Por otro lado, `consultar.py` funciona por defecto con Ollama local usando:

```text
qwen2.5:3b
```

Esto es importante porque la práctica exige que el sistema pueda funcionar con Ollama local y no dependa únicamente de PoliGPT.

## Instalación

Se recomienda usar Python 3.11, porque con versiones más nuevas pueden aparecer problemas con algunas dependencias.

Primero se crea un entorno virtual:

```bash
python -m venv .venv
```

Activarlo en Windows:

```bash
.venv\Scripts\activate
```

Activarlo en Linux o macOS:

```bash
source .venv/bin/activate
```

Después se instalan las dependencias:

```bash
pip install -r requirements.txt
```

También es necesario tener Ollama instalado y descargar el modelo de embeddings:

```bash
ollama pull nomic-embed-text
```

Para usar el modelo local por defecto:

```bash
ollama pull qwen2.5:3b
```

Y para el benchmark local también se ha usado:

```bash
ollama pull llama3.2:3b
```

## Configuración de variables de entorno

El proyecto incluye un archivo `.env.example` con las variables necesarias. No se debe subir nunca un `.env` real con claves privadas.

Ejemplo:

```env
LLM_MODEL=qwen2.5:3b
EMBED_MODEL=nomic-embed-text
OLLAMA_URL=http://localhost:11434/api

POLIGPT_API_KEY=tu_clave_aqui
POLIGPT_BASE_URL=https://api.poligpt.upv.es/v1
```

Para la ejecución principal con Ollama local no hace falta crear un archivo `.env`, porque el sistema ya usa valores por defecto.

Para usar PoliGPT hace falta tener una clave válida. Si se está fuera del campus, también hace falta estar conectado a la VPN de la UPV.

## Cómo ejecutar una consulta

Se puede probar el agente ejecutando directamente:

```bash
python consultar.py
```

También se puede importar la función desde otro script:

```python
from consultar import consultar

resultado = consultar("¿Qué es DNI?")
print(resultado["respuesta"])
print(resultado["fuentes"])
```

La salida tiene una forma parecida a esta:

```python
{
    "respuesta": "Texto de la respuesta generada...",
    "fuentes": ["archivo_origen.txt"],
    "chunks": ["fragmento recuperado 1", "fragmento recuperado 2"],
    "metricas": {
        "latencia_s": 2.31,
        "modelo": "qwen2.5:3b"
    },
    "trazas": [...]
}
```

Si la pregunta está fuera del corpus, por ejemplo sobre alquileres o datos privados, el sistema debe responder que no tiene esa información en sus fuentes.

Ejemplo:

```text
¿Cuánto cuesta el alquiler en Valencia?
```

Respuesta esperada:

```text
No tengo esa información en mis fuentes.
```

## Preguntas de prueba recomendadas

Estas preguntas pueden servir para comprobar rápidamente el funcionamiento del agente durante la defensa:

```text
¿Qué es DNI?
```

```text
¿Cómo me apunto a los desayunos solidarios?
```

```text
¿Qué es COLES?
```

```text
¿Qué actividades se hacen en residencias de mayores?
```

```text
¿En qué se diferencian RESIS y COLES?
```

```text
¿Cuánto cuesta el alquiler en Valencia?
```

La pregunta sobre RESIS y COLES es una de las más difíciles, porque requiere recuperar información de varios documentos. En el benchmark se vio que este tipo de preguntas depende mucho de que el retrieval encuentre los chunks adecuados.

## Benchmark

Para la Banda 7 se ha incluido un benchmark con varias preguntas de prueba. Estas preguntas mezclan casos distintos:

* preguntas factuales directas;
* preguntas sobre logística;
* preguntas de comparación entre proyectos;
* preguntas fuera de ámbito;
* preguntas donde el corpus puede contener contradicciones.

El benchmark se ejecuta desde la raíz del proyecto con:

```bash
python benchmark.py
```

Los resultados se guardan en:

```text
benchmark/benchmark.json
benchmark/benchmark.md
```

El archivo `benchmark.json` contiene los resultados en formato estructurado, mientras que `benchmark.md` tiene una tabla más cómoda de leer.

En el benchmark se registran métricas como latencia, tokens de entrada, tokens de salida, tokens por segundo y una valoración subjetiva de la calidad de cada respuesta.

## Evaluación con RAGAs

Para la Banda 8 se ha añadido una evaluación con RAGAs. Esta evaluación usa las preguntas del benchmark, las respuestas generadas, los chunks recuperados y unas respuestas de referencia redactadas manualmente.

Las métricas utilizadas son:

* `faithfulness`: mide si la respuesta es fiel al contexto recuperado.
* `answer_relevancy`: mide si la respuesta responde realmente a la pregunta.
* `context_precision`: mide si los chunks recuperados son útiles.
* `context_recall`: mide si el contexto recuperado contiene la información necesaria.

Para ejecutar la evaluación:

```bash
python evaluacion/evaluar_ragas.py
```

Los resultados se guardan en:

```text
evaluacion/ragas_results.json
```

En la última ejecución, los resultados medios fueron:

```text
faithfulness: 0.7321
answer_relevancy: 0.4845
context_precision: 0.3531
context_recall: 0.3333
```

Estos resultados indican que el sistema suele ser bastante fiel al contexto cuando responde, pero que la recuperación todavía se puede mejorar. Esto se ve sobre todo en `context_precision` y `context_recall`, que son más bajas que `faithfulness`.

## Métricas propias

Además de RAGAs, he definido dos métricas propias:

### 1. Rechazo correcto fuera de ámbito

Mide si el sistema responde correctamente cuando la pregunta no puede contestarse con el corpus. Por ejemplo, preguntas sobre alquileres, teléfonos personales o información privada.

### 2. Precisión de fuentes

Mide si los archivos citados como fuente contienen realmente información útil para responder a la pregunta.

Estas métricas se explican con más detalle en:

```text
evaluacion/metricas_propias.md
```

Las he añadido porque me parecen importantes para este caso concreto. No basta con que el modelo dé una respuesta bien escrita: también debe saber cuándo no responder y debe citar fuentes que tengan sentido.

## Resultados generales

En general, los resultados del sistema son buenos en preguntas directas como:

```text
¿Qué es DNI?
¿Cómo me apunto a los desayunos solidarios?
¿Qué valores tiene DNI?
¿Qué proyectos principales tiene DNI?
```

También funciona bien en preguntas fuera de ámbito, ya que suele responder que no tiene información en sus fuentes.

Los principales problemas aparecen en preguntas de síntesis o comparación, por ejemplo cuando hay que diferenciar RESIS y COLES. En esos casos el retrieval a veces no recupera todos los documentos necesarios, y entonces el modelo responde de forma incompleta o directamente indica que no tiene información suficiente.

También se ha visto que los modelos de PoliGPT suelen responder mejor que los modelos locales pequeños. Aun así, los modelos locales son importantes porque permiten que el sistema funcione sin depender de una API externa.

## Limitaciones

La principal limitación del sistema está en la recuperación de contexto. Aunque el agente funciona, no siempre recupera los chunks más adecuados, sobre todo en preguntas donde la información está repartida entre varios documentos.

Otra limitación es la selección de fuentes. El sistema devuelve las fuentes de los chunks usados como contexto, pero no siempre puede saber con exactitud qué fuente ha influido más en la respuesta final. Por eso a veces aparecen más fuentes de las estrictamente necesarias.

También se probó la idea de añadir un umbral de similitud para rechazar preguntas fuera de ámbito antes de llamar al modelo. Sin embargo, en las pruebas las distancias devueltas por ChromaDB no resultaron fáciles de interpretar para fijar un umbral estable. Por eso se decidió no aplicar un umbral duro y dejar que el prompt anti-alucinación controle el rechazo final.

Por último, los modelos locales pequeños tienen más tendencia a responder de forma incompleta o menos precisa. Esto se nota especialmente en preguntas de comparación o síntesis.

## Posibles mejoras futuras

Algunas mejoras que se podrían añadir en el futuro son:

* usar recuperación híbrida combinando embeddings y BM25;
* añadir un re-ranker de chunks antes de construir el prompt;
* mejorar la selección final de fuentes para citar solo las más relevantes;
* ajustar dinámicamente el número de chunks recuperados según el tipo de pregunta;
* añadir más preguntas de evaluación para que el benchmark sea más completo;
* mejorar las respuestas de referencia usadas por RAGAs;
* crear una interfaz sencilla con Streamlit o Gradio.

## Uso de IA

El uso de herramientas de IA está documentado en el archivo:

```text
AI_USAGE.md
```

En ese archivo se explica qué herramientas se han usado, para qué tareas y qué partes se han revisado después manualmente.

## Integrantes

Los integrantes y roles del grupo están indicados en:

```text
GRUPO.md
```

## Declaración de funcionalidades

Las funcionalidades declaradas para la corrección están en:

```text
features.json
```

En esta entrega se declara arquitectura `single_agent` y Banda 8. No se declara Banda 10 porque no se ha implementado arquitectura hexagonal completa.

## Conclusión

El proyecto implementa un agente RAG funcional sobre el corpus de DNI. El sistema carga documentos, recupera contexto, genera respuestas con un LLM y devuelve fuentes, chunks, métricas y trazas. Además, se ha evaluado con un benchmark de cuatro modelos, RAGAs y métricas propias.

Aunque todavía hay margen de mejora en la parte de retrieval y selección de fuentes, considero que la práctica cumple los requisitos principales de Banda 8 y deja una base bastante clara para seguir mejorándola.
