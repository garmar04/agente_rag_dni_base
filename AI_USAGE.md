## Herramientas usadas
Durante la práctica hemos usado ChatGPT. No se ha usado para entregar código sin revisar, sino para ayudarnos a entender mejor el enunciado, organizar los pasos de la práctica y resolver errores que iban saliendo durante la instalación y ejecución.

se ha utilizado para:

entender mejor los requisitos de cada banda de evaluación;
preparar una primera estructura del proyecto;
revisar cómo debía funcionar el pipeline RAG;
resolver errores de instalación en Windows, sobre todo con dependencias como ChromaDB, tokenizers, LangChain y RAGAs;
preparar el script de benchmark con varios modelos;
adaptar el benchmark para comparar modelos locales de Ollama y modelos de PoliGPT;
plantear las métricas propias para la banda 8;

La IA ha ayudado especialmente en estos archivos:

consultar.py: apoyo en la estructura del pipeline RAG, el prompt anti-alucinación, la recuperación de chunks y el formato de salida.
benchmark.py: ayuda para crear el script de benchmark, registrar métricas como latencia, tokens y calidad subjetiva, y corregir errores al añadir PoliGPT.
benchmark/preguntas.json: ayuda para plantear un conjunto de preguntas variadas, incluyendo preguntas factuales, de síntesis y fuera de ámbito.
evaluacion/evaluar_ragas.py: ayuda para preparar la evaluación con RAGAs y guardar los resultados en JSON.
evaluacion/metricas_propias.md: ayuda para definir y justificar las dos métricas propias.
README.md e informe.pdf: apoyo en la organización del contenido y en la forma de explicar las decisiones tomadas.

## Revisión humana

Todo el código generado o propuesto con ayuda de IA ha sido revisado y probado por nosotros. Durante la práctica hemos ejecutado el agente con preguntas reales del corpus, hemos comprobado que responde con fuentes y hemos revisado los casos en los que el retrieval no recuperaba bien la información.

También hemos ejecutado el benchmark con cuatro modelos y la evaluación con RAGAs antes de dar por válida la entrega. Cuando aparecieron errores, por ejemplo al conectar PoliGPT o al usar RAGAs, los fuimos corrigiendo y volviendo a probar hasta que los scripts funcionaron correctamente.

Reparto de trabajo
Joel García Martí — evaluación, revisión de fuentes, desarrollo del pipeline RAG y pruebas.
Mario Luis Mesa — revisión de fuentes y presentación, documentación, benchmark e informe.