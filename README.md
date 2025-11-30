## Decisiones Técnicas

### RAG: Router Semántico + Recuperación vs. Búsqueda Vectorial Simple

En lugar de utilizar una búsqueda vectorial simple (RAG tradicional) donde se busca similitud contra toda la base de conocimiento, optamos por un enfoque de **Enrutamiento Semántico**:

1.  **Clasificación**: Un LLM clasifica la intención del usuario en categorías predefinidas (e.g., `locations`, `financing`, `app_services`).
2.  **Recuperación Dirigida**: Se recupera únicamente el documento maestro correspondiente a esa categoría.

**¿Por qué?**
La búsqueda vectorial simple tiende a "alucinar" o traer contextos irrelevantes cuando la pregunta no tiene una similitud semántica fuerte con la respuesta correcta (e.g., preguntar por una ciudad que no existe en la lista de sedes). El enrutamiento hace la respuesta más **predecible y controlada**: si el router clasifica como `locations` y la ciudad no está en el documento, el modelo puede responder con certeza que no tenemos sede ahí, en lugar de intentar adivinar basándose en palabras clave de otros documentos.

### Arquitectura "Stateless Graph"
En lugar de utilizar LangGraph como una máquina de estados persistente (donde el usuario "navega" entre nodos y el estado se guarda en `Checkpoints`), optamos por un enfoque donde **el grafo se ejecuta de principio a fin en cada petición**.

**Ventajas:**
- **Simplicidad**: No necesitamos gestionar persistencia compleja de grafos ni migraciones de estado si cambiamos la lógica.
- **Robustez**: El estado se reconstruye en cada turno basándose en el historial de chat crudo.
- **Flexibilidad**: El router evalúa la intención con todo el contexto actualizado en cada interacción.

### Resolución de Contexto (Financiamiento)
Para calcular financiamiento sin guardar estado, implementamos el nodo `resolve_car_context`. Este nodo analiza el historial de la conversación con un LLM para identificar cuál fue el último auto mencionado (por el usuario o el bot) y extrae sus datos (Marca, Modelo, Precio).

*Nota: No es una solución infalible (depende de la ventana de contexto y la precisión del modelo), pero para el objetivo de esta prueba técnica funciona de manera excelente y evita la complejidad de una base de datos de sesiones.*

### Diagrama de Flujo
```ascii
                            [ START ]
                                |
                                v
                     +----------------------+
                     |   detect_intention   |
                     | (Router Classifier)  |
                     +----------------------+
                                |
          +---------------------+---------------------+---------------------+
          |                     |                     |                     |
          v                     v                     v                     v
   [ intent="faq" ]      [ intent="buy" ]    [ intent="financing" ]  [ intent="general" ]
          |                     |                     |                     |
          v                     v                     v                     v
 +------------------+  +------------------+  +-------------------+  +------------------+
 |    handle_faq    |  | reason_about_car |  |resolve_car_context|  |  handle_general  |
 | (RAG Retrieval)  |  | (Extract & Find) |  | (History Analysis)|  | (Chitchat/Help)  |
 +------------------+  +------------------+  +-------------------+  +------------------+
          |                     |                     |                     |
          |                     v                     v                     |
          |            +------------------+  +------------------+           |
          |            |respond_with_options|| handle_financing |           |
          |            | (Format Results) |  | (Calc Payments)  |           |
          |            +------------------+  +------------------+           |
          |                     |                     |                     |
          +---------------------+---------------------+---------------------+
                                |
                                v
                             [ END ]
```

## Screenshots

### RAG
![Sedes](specs/img/sedes.png)
![Mantenimiento](specs/img/mantenimiento.png)
![General Info](specs/img/general.png)

### Compra de Carro
![Carro 1](specs/img/carro1.png)
![Carro 2](specs/img/carro2.png)
