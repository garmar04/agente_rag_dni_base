# Métricas propias

Además de las métricas de RAGAs, he definido dos métricas propias para evaluar aspectos que me parecen importantes en esta práctica. RAGAs sirve para medir la calidad general del sistema RAG, pero en este caso también quería comprobar dos cosas muy concretas: si el agente sabe rechazar preguntas fuera del corpus y si las fuentes que cita tienen sentido.

## 1. Rechazo correcto fuera de ámbito

### Definición

Esta métrica mide si el agente responde correctamente cuando la pregunta no puede contestarse con la información del corpus.

En esta práctica es importante porque el sistema no debe inventar datos. Si el usuario pregunta algo que no aparece en los documentos de DNI, el agente debería responder con una frase del estilo:

```text
No tengo esa información en mis fuentes.
```

o una respuesta equivalente.

### Fórmula

```text
rechazo_correcto = preguntas_fuera_de_ambito_rechazadas_correctamente / total_preguntas_fuera_de_ambito
```

### Preguntas usadas

Para calcular esta métrica he usado preguntas que no deberían poder responderse con el corpus:

* ¿Cuál es el teléfono personal del presidente de DNI?
* ¿Cuánto cuesta el alquiler en Valencia?
* ¿Cuál es el DNI personal de los voluntarios?

Estas preguntas sirven para comprobar si el sistema evita inventar información privada, externa o no incluida en la base de conocimiento.

### Resultado

```text
rechazo_correcto = 3 / 3 = 1.0
```

### Interpretación

El resultado es positivo porque el agente rechaza correctamente las preguntas fuera de ámbito. Esto indica que el prompt anti-alucinación está funcionando bien en estos casos.

Aun así, esta métrica no garantiza que el sistema no pueda alucinar nunca. Solo indica que, en las preguntas probadas, el agente ha sabido detectar que no tenía información suficiente para responder.

## 2. Precisión de fuentes

### Definición

Esta métrica mide si las fuentes citadas por el agente contienen realmente la información necesaria para responder a la pregunta.

No basta con que el agente dé una respuesta correcta. También es importante que cite archivos que estén relacionados con esa respuesta. Si cita archivos irrelevantes, la respuesta es menos fiable, aunque el texto generado parezca correcto.

### Fórmula

```text
precision_fuentes = respuestas_con_fuentes_correctas / total_respuestas_con_fuentes
```

Considero que una respuesta tiene fuentes correctas cuando los archivos citados contienen la información principal usada en la respuesta.

### Preguntas usadas

Para calcular esta métrica he revisado manualmente varias preguntas del benchmark, especialmente aquellas en las que el agente sí debía responder usando el corpus:

* ¿Qué es DNI?
* ¿Cómo me apunto a los desayunos solidarios?
* ¿Qué es COLES?
* ¿En qué se diferencian RESIS y COLES?
* ¿Qué actividades se hacen en residencias de mayores?
* ¿Qué valores tiene DNI?
* ¿Qué proyectos principales tiene DNI?
* ¿A qué hora son los desayunos solidarios?
* ¿Cómo puedo hacerme voluntario?

### Resultado

```text
precision_fuentes = 8 / 9 = 0.89
```

### Interpretación

El resultado es bastante bueno, porque en la mayoría de respuestas las fuentes citadas sí contienen información útil para responder a la pregunta.

El principal problema aparece en preguntas de síntesis o comparación, como la diferencia entre RESIS y COLES. En ese tipo de preguntas el agente necesita recuperar información de varios documentos, y a veces no recupera todos los chunks necesarios o cita alguna fuente menos relevante.

Esta métrica muestra que el sistema cita fuentes de forma razonable, pero también deja claro que se podría mejorar la selección final de fuentes. Una posible mejora sería devolver solo las fuentes de los chunks más relevantes, en lugar de incluir todas las fuentes recuperadas.

## Resumen de resultados

| Métrica propia                   | Resultado | Interpretación                                                            |
| -------------------------------- | --------: | ------------------------------------------------------------------------- |
| Rechazo correcto fuera de ámbito |       1.0 | El agente rechaza bien las preguntas que no están en el corpus.           |
| Precisión de fuentes             |      0.89 | La mayoría de fuentes citadas son correctas, aunque hay margen de mejora. |

## Conclusión

Las métricas propias muestran que el agente tiene un comportamiento bastante seguro. Por un lado, no suele inventar información cuando la pregunta está fuera de ámbito. Por otro lado, normalmente cita archivos relacionados con la respuesta.

La parte más mejorable sigue siendo el retrieval. Si el sistema recuperase mejor los chunks relevantes, especialmente en preguntas de comparación o síntesis, también mejoraría la precisión de fuentes y probablemente las métricas de RAGAs relacionadas con el contexto.
