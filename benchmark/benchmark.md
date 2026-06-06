# Benchmark del Agente RAG DNI

Este benchmark ejecuta el mismo conjunto de preguntas contra varios modelos manteniendo constante el pipeline RAG: mismo chunking, mismo vector store, mismo top-k y mismo prompt.

## Resultados por pregunta

| Modelo | Servidor | Pregunta | Tipo | Latencia total (s) | Tokens entrada | Tokens salida | Tokens/s | Calidad subjetiva | Fuentes |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| qwen2.5:3b | ollama_local | ¿Qué es DNI? | factual | 8.353 | 493 | 103 | 99.57 | 1.0 | 02_presentacion_desayunos.txt, 04_filosofia_dni.txt, 14_impacto_social.txt |
| qwen2.5:3b | ollama_local | ¿Cómo me apunto a los desayunos solidarios? | logistica | 5.327 | 897 | 87 | 105.49 | 1.0 | 01_faq_dni.txt, 07_desayunos_logistica.txt, 10_proyectos.txt |
| qwen2.5:3b | ollama_local | ¿Qué es COLES? | factual | 4.417 | 493 | 10 | 123.71 | 0.0 |  |
| qwen2.5:3b | ollama_local | ¿En qué se diferencian RESIS y COLES? | sintesis | 4.545 | 901 | 10 | 116.35 | 0.0 |  |
| qwen2.5:3b | ollama_local | ¿Qué actividades se hacen en residencias de mayores? | factual | 4.837 | 658 | 47 | 107.5 | 1.0 | 03_charlas_abuelitos.txt, 05_resis_actividades.txt, 11_horarios_ubicaciones.txt |
| qwen2.5:3b | ollama_local | ¿Qué valores tiene DNI? | factual | 4.591 | 831 | 18 | 118.06 | 1.0 | 08_preguntas_basicas.txt, 15_desayunos_100_preguntas.txt, 14_impacto_social.txt |
| qwen2.5:3b | ollama_local | ¿Qué proyectos principales tiene DNI? | sintesis | 5.348 | 811 | 89 | 103.7 | 1.0 | 10_proyectos.txt, 09_como_participar.txt, 15_desayunos_100_preguntas.txt |
| qwen2.5:3b | ollama_local | ¿A qué hora son los desayunos solidarios? | contradiccion | 4.589 | 881 | 16 | 112.98 | 1.0 | 11_horarios_ubicaciones.txt, 10_proyectos.txt, 07_desayunos_logistica.txt |
| qwen2.5:3b | ollama_local | ¿Cuál es el teléfono personal del presidente de DNI? | fuera_ambito | 4.531 | 1019 | 10 | 116.82 | 1.0 |  |
| qwen2.5:3b | ollama_local | ¿Cuánto cuesta el alquiler en Valencia? | fuera_ambito | 4.481 | 852 | 10 | 105.04 | 1.0 |  |
| qwen2.5:3b | ollama_local | ¿Qué impacto social tiene DNI? | sintesis | 6.078 | 925 | 151 | 106.66 | 1.0 | 12_contacto_redes.txt, 08_preguntas_basicas.txt, 16_resis_49_preguntas.txt |
| qwen2.5:3b | ollama_local | ¿Quién puede ser voluntario en DNI? | factual | 4.482 | 912 | 10 | 116.34 | 0.0 |  |
| llama3.2:3b | ollama_local | ¿Qué es DNI? | factual | 7.671 | 483 | 123 | 104.28 | 1.0 | 02_presentacion_desayunos.txt, 04_filosofia_dni.txt, 14_impacto_social.txt |
| llama3.2:3b | ollama_local | ¿Cómo me apunto a los desayunos solidarios? | logistica | 5.982 | 886 | 142 | 104.67 | 1.0 | 01_faq_dni.txt, 07_desayunos_logistica.txt, 10_proyectos.txt |
| llama3.2:3b | ollama_local | ¿Qué es COLES? | factual | 4.639 | 483 | 28 | 107.73 | 0.0 |  |
| llama3.2:3b | ollama_local | ¿En qué se diferencian RESIS y COLES? | sintesis | 4.537 | 890 | 10 | 112.23 | 0.0 |  |
| llama3.2:3b | ollama_local | ¿Qué actividades se hacen en residencias de mayores? | factual | 5.515 | 648 | 111 | 108.02 | 1.0 | 03_charlas_abuelitos.txt, 05_resis_actividades.txt, 11_horarios_ubicaciones.txt |
| llama3.2:3b | ollama_local | ¿Qué valores tiene DNI? | factual | 5.77 | 817 | 125 | 99.26 | 1.0 | 08_preguntas_basicas.txt, 15_desayunos_100_preguntas.txt, 14_impacto_social.txt |
| llama3.2:3b | ollama_local | ¿Qué proyectos principales tiene DNI? | sintesis | 5.336 | 799 | 88 | 105.54 | 1.0 | 10_proyectos.txt, 09_como_participar.txt, 15_desayunos_100_preguntas.txt |
| llama3.2:3b | ollama_local | ¿A qué hora son los desayunos solidarios? | contradiccion | 6.558 | 868 | 200 | 102.86 | 1.0 | 11_horarios_ubicaciones.txt, 10_proyectos.txt, 07_desayunos_logistica.txt |
| llama3.2:3b | ollama_local | ¿Cuál es el teléfono personal del presidente de DNI? | fuera_ambito | 4.535 | 1008 | 10 | 109.81 | 1.0 |  |
| llama3.2:3b | ollama_local | ¿Cuánto cuesta el alquiler en Valencia? | fuera_ambito | 4.509 | 840 | 10 | 115.51 | 1.0 |  |
| llama3.2:3b | ollama_local | ¿Qué impacto social tiene DNI? | sintesis | 6.186 | 912 | 161 | 103.87 | 1.0 | 12_contacto_redes.txt, 08_preguntas_basicas.txt, 16_resis_49_preguntas.txt |
| llama3.2:3b | ollama_local | ¿Quién puede ser voluntario en DNI? | factual | 4.516 | 903 | 10 | 110.67 | 0.0 |  |
| qwen | poligpt | ¿Qué es DNI? | factual | 7.511 | 399 | 797 | 146.27 | 1.0 | 02_presentacion_desayunos.txt, 03_charlas_abuelitos.txt, 04_filosofia_dni.txt |
| qwen | poligpt | ¿Cómo me apunto a los desayunos solidarios? | logistica | 8.748 | 777 | 1025 | 153.54 | 1.0 | 01_faq_dni.txt, 07_desayunos_logistica.txt, 10_proyectos.txt |
| qwen | poligpt | ¿Qué es COLES? | factual | 10.321 | 399 | 1294 | 156.94 | 1.0 | 02_presentacion_desayunos.txt, 03_charlas_abuelitos.txt, 04_filosofia_dni.txt |
| qwen | poligpt | ¿En qué se diferencian RESIS y COLES? | sintesis | 5.809 | 775 | 561 | 149.76 | 0.0 |  |
| qwen | poligpt | ¿Qué actividades se hacen en residencias de mayores? | factual | 10.167 | 554 | 1255 | 154.8 | 1.0 | 03_charlas_abuelitos.txt, 05_resis_actividades.txt, 06_coles_refuerzo.txt |
| qwen | poligpt | ¿Qué valores tiene DNI? | factual | 14.443 | 704 | 1944 | 157.6 | 1.0 | 08_preguntas_basicas.txt, 14_impacto_social.txt, 15_desayunos_100_preguntas.txt |
| qwen | poligpt | ¿Qué proyectos principales tiene DNI? | sintesis | 6.215 | 702 | 620 | 150.12 | 1.0 | 09_como_participar.txt, 10_proyectos.txt, 15_desayunos_100_preguntas.txt |
| qwen | poligpt | ¿A qué hora son los desayunos solidarios? | contradiccion | 14.851 | 765 | 2010 | 157.44 | 1.0 | 01_faq_dni.txt, 07_desayunos_logistica.txt, 10_proyectos.txt |
| qwen | poligpt | ¿Cuál es el teléfono personal del presidente de DNI? | fuera_ambito | 8.565 | 858 | 997 | 154.02 | 1.0 |  |
| qwen | poligpt | ¿Cuánto cuesta el alquiler en Valencia? | fuera_ambito | 9.059 | 718 | 1075 | 154.23 | 1.0 |  |
| qwen | poligpt | ¿Qué impacto social tiene DNI? | sintesis | 14.58 | 780 | 1966 | 157.52 | 1.0 | 08_preguntas_basicas.txt, 09_como_participar.txt, 12_contacto_redes.txt |
| qwen | poligpt | ¿Quién puede ser voluntario en DNI? | factual | 15.544 | 774 | 2119 | 157.44 | 1.0 | 02_presentacion_desayunos.txt, 14_impacto_social.txt, 16_resis_49_preguntas.txt |
| gemma | poligpt | ¿Qué es DNI? | factual | 3.927 | 398 | 86 | 45.92 | 1.0 | 02_presentacion_desayunos.txt, 03_charlas_abuelitos.txt, 04_filosofia_dni.txt |
| gemma | poligpt | ¿Cómo me apunto a los desayunos solidarios? | logistica | 2.982 | 763 | 35 | 37.63 | 1.0 | 01_faq_dni.txt, 07_desayunos_logistica.txt, 10_proyectos.txt |
| gemma | poligpt | ¿Qué es COLES? | factual | 2.773 | 398 | 9 | 12.99 | 1.0 | 02_presentacion_desayunos.txt, 03_charlas_abuelitos.txt, 04_filosofia_dni.txt |
| gemma | poligpt | ¿En qué se diferencian RESIS y COLES? | sintesis | 2.789 | 768 | 9 | 12.4 | 0.0 |  |
| gemma | poligpt | ¿Qué actividades se hacen en residencias de mayores? | factual | 3.014 | 551 | 40 | 42.96 | 1.0 | 03_charlas_abuelitos.txt, 05_resis_actividades.txt, 06_coles_refuerzo.txt |
| gemma | poligpt | ¿Qué valores tiene DNI? | factual | 3.236 | 695 | 73 | 63.81 | 1.0 | 08_preguntas_basicas.txt, 14_impacto_social.txt, 15_desayunos_100_preguntas.txt |
| gemma | poligpt | ¿Qué proyectos principales tiene DNI? | sintesis | 3.3 | 690 | 83 | 67.37 | 1.0 | 09_como_participar.txt, 10_proyectos.txt, 15_desayunos_100_preguntas.txt |
| gemma | poligpt | ¿A qué hora son los desayunos solidarios? | contradiccion | 3.261 | 745 | 91 | 77.18 | 1.0 | 01_faq_dni.txt, 07_desayunos_logistica.txt, 10_proyectos.txt |
| gemma | poligpt | ¿Cuál es el teléfono personal del presidente de DNI? | fuera_ambito | 3.01 | 856 | 9 | 9.54 | 1.0 |  |
| gemma | poligpt | ¿Cuánto cuesta el alquiler en Valencia? | fuera_ambito | 2.833 | 710 | 9 | 12.47 | 1.0 |  |
| gemma | poligpt | ¿Qué impacto social tiene DNI? | sintesis | 3.043 | 774 | 51 | 52.31 | 1.0 | 08_preguntas_basicas.txt, 09_como_participar.txt, 12_contacto_redes.txt |
| gemma | poligpt | ¿Quién puede ser voluntario en DNI? | factual | 2.847 | 772 | 9 | 11.98 | 0.0 |  |

## Resumen por modelo

| Modelo | Servidor | Latencia media total (s) | Tokens/s medio | Calidad media | Errores |
|---|---|---:|---:|---:|---:|
| gemma | poligpt | 3.085 | 37.213 | 0.833 | 0 |
| llama3.2:3b | ollama_local | 5.479 | 107.038 | 0.75 | 0 |
| qwen | poligpt | 10.484 | 154.14 | 0.917 | 0 |
| qwen2.5:3b | ollama_local | 5.132 | 111.018 | 0.75 | 0 |

## Interpretación inicial

La calidad subjetiva se ha calculado con una escala simple: 1.0 para respuestas correctas, 0.5 para respuestas parcialmente correctas y 0.0 para respuestas incorrectas o alucinadas. Esta valoración se ha revisado después de ejecutar el benchmark para detectar fallos claros.

En los resultados se ve que los modelos de PoliGPT responden mejor de media que los modelos locales pequeños. El mejor comportamiento general lo tiene qwen en PoliGPT, por eso se usa como modelo principal para la evaluación con RAGAs. Aun así, el sistema mantiene Ollama local porque es obligatorio y porque permite ejecutar el agente sin depender de una API externa.

La parte más mejorable está en las preguntas de síntesis, especialmente cuando hay que comparar información repartida entre varios documentos, como RESIS y COLES. En esos casos el problema no siempre es el LLM, sino que a veces el retrieval no recupera todos los chunks necesarios.

## Modelos evaluados

- qwen2.5:3b (ollama_local)
- llama3.2:3b (ollama_local)
- qwen (poligpt)
- gemma (poligpt)