# `services/` architecture

## Design patterns in this layer

| Pattern | Where |
|---------|--------|
| **Application service** | `DataService` / `MetricsService` — use-case operations coordinating repos and domain helpers |
| **Orchestration / workflow** | `PipelineService.execute()` drives fixed steps (lightweight **template method** / process script) |
| **Facade** | `PipelineService` exposes a single `execute()` to `main` |
| **Graceful degradation** | Missing API repo or CRM/traffic failures yield empty tables with logging (`DataService`) |

## Collaboration (diagram)

```mermaid
flowchart LR
    subgraph services["src/services"]
        PS[PipelineService]
        DS[DataService]
        MS[MetricsService]
    end
    subgraph deps["Dependencies"]
        FR[FileRepository]
        AR[APIRepository]
        DP[IDataProcessor]
        MC[IMetricsCalculator]
        CFG[AppConfig]
    end

    PS --> DS
    PS --> MS
    PS --> CFG
    DS --> FR
    DS --> AR
    DS --> DP
    MS --> MC
```

## Pipeline execution (diagram)

```mermaid
flowchart TD
    Start([execute]) --> S1[1 load & process sales]
    S1 --> S2[2 load & process targets]
    S2 --> S3[3 load & process CRM]
    S3 --> S4[4 load & process web traffic]
    S4 --> S5[5 MetricsService.calculate_metrics]
    S5 --> S6[6 sort & write final_dataframe.csv]
    S6 --> S7[quality + business summary logs]
    S7 --> End([return metrics DataFrame])
```
