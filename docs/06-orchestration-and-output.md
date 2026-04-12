# 06 Orchestration and output

## Role

`PipelineService.execute()` calls `DataService` and `MetricsService` in fixed steps, writes `data/output/final_dataframe.csv`, and logs quality and business summaries.

## Six-step pipeline

```mermaid
flowchart LR
    S1[1 Sales] --> S2[2 Targets]
    S2 --> S3[3 CRM]
    S3 --> S4[4 Traffic]
    S4 --> S5[5 Metrics]
    S5 --> S6[6 Persist]
```

1. Load and process sales  
2. Load and process targets  
3. Load and process CRM (optional empty)  
4. Load and process web traffic (optional empty)  
5. Calculate metrics  
6. Sort, write CSV, checksum and schema logging  

## Output

- Path from `config.data.output_path`, file name `final_dataframe.csv`.
- Data layout: [`data/ARCHITECTURE.md`](reference/architecture-data.md)

## Deeper architecture

- [`src/services/ARCHITECTURE.md`](reference/architecture-services.md)

---

**Previous:** [05-metrics](05-metrics.md)  
**Next:** [07-di-and-factories](07-di-and-factories.md)
