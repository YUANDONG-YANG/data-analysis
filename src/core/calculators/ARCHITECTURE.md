# `core/calculators/` architecture

## Design patterns in this layer

| Pattern | Where |
|---------|--------|
| **Strategy** | `MetricsCalculator` implements `IMetricsCalculator`; replace the whole formula set |
| **Pure domain service** | No I/O; only group, merge, and derive columns on DataFrames |

## Class diagram

```mermaid
classDiagram
    class IMetricsCalculator {
        <<Protocol>>
        +calculate_monthly_community_metrics(sales, targets, crm, traffic)
    }
    class MetricsCalculator {
        +calculate_monthly_community_metrics(...)
    }
    IMetricsCalculator <.. MetricsCalculator : implements
```

## Metrics architecture (diagram)

```mermaid
flowchart TB
    subgraph Orchestration["Orchestration layer"]
        PS[PipelineService]
    end

    subgraph Application["Application service layer"]
        MS[MetricsService]
    end

    subgraph Contract["Core contract · Protocol"]
        IMC{{IMetricsCalculator}}
    end

    subgraph Domain["Domain calculation layer"]
        MC[MetricsCalculator]
    end

    subgraph Inputs["Processed input DataFrames<br/><i>produced by DataService</i>"]
        SALES[(sales_df)]
        TARGETS[(targets_df)]
        CRM[(crm_df)]
        TRAFFIC[(web_traffic_df)]
    end

    subgraph Output["Reporting output"]
        RESULT[(monthly metrics DataFrame)]
    end

    PS -->|calls calculate_metrics| MS
    MS -.->|depends on via DI| IMC
    MC -.->|implements| IMC
    SALES --> MC
    TARGETS --> MC
    CRM --> MC
    TRAFFIC --> MC
    MC --> RESULT
```
