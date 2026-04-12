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

## Metrics flow (diagram)

```mermaid
flowchart TD
    A[Four input tables] --> B{sales & targets both empty?}
    B -->|yes| Z[empty result schema]
    B -->|no| C[groupby sales: actual + revenue]
    C --> D[groupby targets]
    D --> E[groupby CRM leads]
    E --> F[groupby traffic]
    F --> G[outer merge sales + targets]
    G --> H[left merge leads + traffic]
    H --> I[fillna 0 + derived ratios]
    I --> J[rename columns + sort]
    J --> K[wide output table]
```
