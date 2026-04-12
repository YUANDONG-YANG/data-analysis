# `di/` architecture

## Design patterns in this layer

| Pattern | Where |
|---------|--------|
| **Lightweight DI container** | `DIContainer` holds `AppConfig` and resolves the graph in `build_pipeline_service` |
| **Service locator (sketch)** | `register_singleton` / `register_factory` / `get` reserved; main path uses `build_pipeline_service` |

## Container responsibilities (diagram)

```mermaid
flowchart LR
    subgraph DI["di/container.py"]
        CNT[DIContainer]
        REG1[_instances]
        REG2[_factories]
    end
    CNT --> REG1
    CNT --> REG2
    CNT -->|build_pipeline_service| PS[PipelineService]
```

## Wiring flow (diagram)

```mermaid
flowchart TD
    A[DIContainer constructed with AppConfig] --> B[build_pipeline_service]
    B --> C[RepositoryFactory creates FR / AR]
    C --> D[ServiceFactory creates DataService]
    D --> E[ServiceFactory creates MetricsService]
    E --> F[ServiceFactory creates PipelineService]
    F --> G[Return PipelineService to main]
```
