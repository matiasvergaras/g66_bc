# One Pager — Primera Línea de Defensa contra Fraude en Tiempo Real

## Contexto

Global66 revisa manualmente solo el 10% de los mensajes de soporte, con una brecha promedio de 48 horas. Para la mayoría de categorías esto genera frustración; para **fraude**, genera daño financiero directo. En 48 horas un atacante ya vació la cuenta y el usuario se convirtió en detractor.

## Diagnóstico

Se analizaron las 250 conversaciones del dataset proporcionado, clasificándolas por categoría, sentimiento y urgencia. El análisis reveló distintos **Weak Points** (disponibles en el documento `analysis.ipynb`, sección 4), de los cuales los temas asociados a Seguridad y Fraudes mostrarían la mayor concentración de riesgo: 100% sentimiento negativo, 96% urgencia crítica. Es además el único problema donde existe un *next step* claro y automatizable (bloquear la cuenta, notificar al usuario, escalar al equipo de fraude), y donde el costo de un falso positivo por parte del agente (bloqueo innecesario, reversible) es órdenes de magnitud menor que el costo de no actuar a tiempo.

## Problema raíz escogido

El problema raíz a resolver es que no existe una primera línea de defensa que monitoree mensajes entrantes en tiempo real. El 90% no se revisa manualmente, y el 10% que sí se revisa llega tarde. Para un escenario de fraude, llegar tarde implica daño real, lo cual nos lleva a perder un usuario y ganar un posible detractor.

## Solución

Una API reactiva que se conecta al flujo de soporte existente. Cada mensaje entrante pasa por el endpoint `POST /sofia/classify`, que:

1. **Acumula contexto**: almacena cada mensaje en memoria, reconstruyendo la conversación completa del caso.
2. **Clasifica con el LLM**: para cada mensaje del usuario, analiza la conversación mediante Claude, obteniendo categoría, subcategoría, sentimiento, urgencia y un flag de fraude — todo validado contra un schema Pydantic.
3. **Decide**: si detecta fraude o riesgo de seguridad, simula el bloqueo de la cuenta y entrega un texto de respuesta inmediata para el usuario. Si no, deja que el ticket siga su flujo normal, siendo atendido por humano en el mediano plazo. La API sigue escuchando futuras intervenciones en caso de que se declare riesgo de fraude.

La API no sustituye al equipo humano: lo potencia. Monitorea de forma continua, interviene de manera ágil y precisa solo ante indicios de fraude, y deja trazabilidad de cada decisión. Así, se reduce significativamente el riesgo de que un cliente quede expuesto a fraude durante 48 horas por falta de soporte.

## Arquitectura y herramientas

| Componente | Elección | Justificación |
|---|---|---|
| **LLM** | Claude Haiku 4.5 | Modelo económico (~$0.003/caso) con capacidad suficiente para clasificación. El patrón lingüístico de fraude es distintivo y no requiere un modelo más costoso. |
| **Structured output** | Anthropic `tool_use` + Pydantic | Elimina la fragilidad de parsear texto libre. El LLM está forzado a devolver un JSON validado contra el schema, con enums estrictos para categoría, sentimiento y urgencia. |
| **Prompt caching** | `cache_control: ephemeral` | El system prompt (taxonomía + instrucciones) se cachea entre llamadas, reduciendo tokens facturados y latencia en mensajes consecutivos del mismo caso. |
| **Framework** | FastAPI | Ligero, tipado, con docs autogeneradas. Ideal para un microservicio con pocos endpoints. |
| **Persistencia** | CSV thread-safe | Suficiente para el MVP. Cada fila registra el mensaje y la decisión del modelo, permitiendo auditoría completa. |
| **Deploy** | Cloud Run + Secret Manager | Escala a cero cuando no hay tráfico, escala horizontalmente bajo carga. El secreto de la API key nunca toca el código. |

## Escalabilidad

La solución está pensada para crecer en dos ejes:

**Volumen**: Cloud Run escala automáticamente. Con la configuración actual (1 CPU, 512 MB), cada instancia es capaz de procesar ~30 msg/min. Para 100K mensajes/mes bastan 2-3 instancias concurrentes, con un costo de infraestructura estimado de ~$10 USD/mes (Véase [Calculadora de Pricing de Google](https://cloud.google.com/products/calculator?hl=es&dl=CjhDaVExTUdVNU9HSmhPQzB3WlRBMUxUUXhaREV0WWprME1TMWtPR1ZrWm1Rek9HSTFaRGtRQVE9PRAcGiRBQUJGMTkzOS0xQjAyLTQ4RjItOUQyRi01MzMxMkM4MTUwQUE)).

**Alcance**: el agente hoy solo interviene en fraude, pero la arquitectura (taxonomía en JSON, prompt en archivo de texto, schema extensible) permite incorporar nuevos flujos — respuestas automáticas para consultas informativas, escalación diferenciada para reclamos regulatorios, integración con RAG para base de conocimiento — sin modificar la estructura de la API.

---

**Autor:** Matias Vergara · matiasvergara@ug.uchile.cl
