# `factories/` architecture

## Design patterns in this layer

| Pattern | Where |
|---------|--------|
| **Simple / static factory** | Static methods create objects and hide construction details |
| **Single entry for config** | Factories take `AppConfig` (and optional `IAPIClient`) so paths and API stay consistent |

## Factories and products (diagram)

```mermaid
flowchart TB
    subgraph Factories["factories/"]
        RF[RepositoryFactory]
        SF[ServiceFactory]
    end
    subgraph Products["Created objects"]
        FR[FileRepository]
        AR[APIRepository]
        DS[DataService]
        MS[MetricsService]
        PS[PipelineService]
    end
    CFG[AppConfig]
    API[IAPIClient]

    RF -->|create_file_repository| FR
    RF -->|create_api_repository| AR
    AR --> API
    SF -->|create_data_service| DS
    SF -->|create_metrics_service| MS
    SF -->|create_pipeline_service| PS
    DS --> FR
    DS --> AR
    PS --> DS
    PS --> MS
    PS --> CFG
    RF --> CFG
```

## Creation order (sequence)

```mermaid
sequenceDiagram
    participant CNT as DIContainer
    participant RF as RepositoryFactory
    participant SF as ServiceFactory
    participant FR as FileRepository
    participant AR as APIRepository

    CNT->>RF: create_file_repository(config)
    RF-->>CNT: FileRepository
    CNT->>RF: create_api_repository(config, api_client)
    RF-->>CNT: APIRepository or null
    CNT->>SF: create_data_service(FR, AR, processor)
    CNT->>SF: create_metrics_service(calculator)
    CNT->>SF: create_pipeline_service(data_svc, metrics_svc, config)
```
