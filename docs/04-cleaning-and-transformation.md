# 04 Cleaning and transformation

## Role

`DataProcessor` (inside `DataService`) **deduplicates**, **filters outliers**, **standardizes dates and community names**, and derives fields such as `year_month`.

## Flow

```mermaid
flowchart TD
    A[merge_dataframes] --> B[clean_data dedupe / price·sqft bounds]
    B --> C{Domain}
    C -->|sales| D[process_sales_data]
    C -->|targets| E[process_targets_data]
    C -->|CRM| F[process_crm_data]
    C -->|traffic| G[process_web_traffic_data]
    D --> H[standardize_date + community + year_month]
    E --> H
    F --> H
    G --> I[when page_path: _extract_community_from_path]
```

- Display names: generic regex + `community_names.aliases` in `config.yaml`.
- URL paths: match `path_slugs` longest-first to reduce false matches.

## Deeper architecture

- [`src/core/processors/ARCHITECTURE.md`](reference/architecture-processors.md)

---

**Previous:** [03-data-ingestion](03-data-ingestion.md)  
**Next:** [05-metrics](05-metrics.md)
