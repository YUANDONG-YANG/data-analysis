# 03 Data ingestion

## Role

Turn raw records from **files** and the **HTTP API** into `pandas.DataFrame` instances for downstream steps.

## Flow

```mermaid
flowchart TD
    subgraph FileRepo["FileRepository"]
        S["sales_builder_a / b.csv"] --> SA[with builder column]
        T[targets: xlsx/csv] --> TB[long: year_month + community + target]
    end
    subgraph APIRepo["APIRepository"]
        C1[get_crm_data a,b] --> CM[CRM DataFrame list]
        W1[get_web_traffic_data a,b] --> WM[Traffic DataFrame list]
    end
    subgraph DS["DataService"]
        M1[merge_dataframes sales/targets]
        M2[merge_dataframes CRM/traffic]
    end
    SA --> M1
    TB --> M1
    CM --> M2
    WM --> M2
```

- Sales and targets: loaded per builder, merged in `DataService` via `DataProcessor.merge_dataframes`.
- CRM / traffic: empty DataFrames if no API client; on failure, log a warning and degrade to empty tables.

## Deeper architecture

- [`src/repositories/ARCHITECTURE.md`](reference/architecture-repositories.md)
- HTTP adapter: [`src/core/clients/ARCHITECTURE.md`](reference/architecture-clients.md)

---

**Previous:** [02-startup-and-config](02-startup-and-config.md)  
**Next:** [04-cleaning-and-transformation](04-cleaning-and-transformation.md)
