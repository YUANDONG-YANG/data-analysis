# `src/` architecture

## Design patterns in this layer

| Pattern | Where |
|---------|--------|
| **Composition root** | `main.py` wires config, clients, container, and services at process entry |
| **Dependency injection** | `DIContainer` injects repositories and services into `PipelineService` |
| **Abstract factory (lightweight)** | `RepositoryFactory` / `ServiceFactory` create families of objects from config |
| **Facade** | `PipelineService` hides multi-step load, compute, and persist details |

## Module dependency (diagram)

```mermaid
flowchart TB
    subgraph Entry["Composition root main.py"]
        M[main]
    end
    subgraph CoreInfra["core"]
        CFG[AppConfig]
        API[APIClient]
        DP[DataProcessor]
        MC[MetricsCalculator]
    end
    subgraph DI["di"]
        CNT[DIContainer]
    end
    subgraph Fact["factories"]
        RF[RepositoryFactory]
        SF[ServiceFactory]
    end
    subgraph App["services"]
        PS[PipelineService]
        DS[DataService]
        MS[MetricsService]
    end
    subgraph Repo["repositories"]
        FR[FileRepository]
        AR[APIRepository]
    end

    M --> CFG
    M --> API
    M --> DP
    M --> MC
    M --> CNT
    CNT --> RF
    CNT --> SF
    RF --> FR
    RF --> AR
    SF --> DS
    SF --> MS
    SF --> PS
    AR --> API
    DS --> FR
    DS --> AR
    DS --> DP
    MS --> MC
    PS --> DS
    PS --> MS
    PS --> CFG
```

## Startup and orchestration (sequence)

```mermaid
sequenceDiagram
    participant Main as main
    participant CFG as AppConfig
    participant CNT as DIContainer
    participant PS as PipelineService
    participant DS as DataService
    participant MS as MetricsService

    Main->>CFG: from_yaml + validate
    Main->>CNT: build_pipeline_service(...)
    CNT->>CNT: RepositoryFactory + ServiceFactory
    CNT-->>Main: PipelineService
    Main->>PS: execute()
    PS->>DS: load sales / targets / crm / traffic
    PS->>MS: calculate_metrics
    PS->>PS: save CSV + quality logging
    PS-->>Main: DataFrame
```
