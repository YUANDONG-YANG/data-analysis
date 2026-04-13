# `services/` architecture

## Design patterns in this layer

| Pattern | Where |
|---------|--------|
| **Application service** | `DataService` / `MetricsService` — use-case operations coordinating repos and domain helpers |
| **Orchestration / workflow** | `PipelineService.execute()` drives fixed steps (lightweight **template method** / process script) |
| **Facade** | `PipelineService` exposes a single `execute()` to `main` |
| **Graceful degradation** | Missing API repo or CRM/traffic failures yield empty tables with logging (`DataService`) |
| **Medallion Architecture** | `DataService` persists Silver layer outputs (cleaned DataFrames) to `data/processed/` |

## Component architecture (diagram)

```mermaid
flowchart TB
    subgraph Orchestration["Orchestration layer"]
        PS[PipelineService]
    end

    subgraph Application["Application service layer"]
        DS[DataService]
        MS[MetricsService]
    end

    subgraph Configuration["Configuration"]
        CFG[AppConfig]
    end

    subgraph Repositories["Data repositories"]
        FR[FileRepository]
        AR[APIRepository]
    end

    subgraph Domain["Domain components"]
        IDP{{IDataProcessor}}
        IMC{{IMetricsCalculator}}
    end

    subgraph Silver["🥈 Silver layer (data/silver/)"]
        SALES_P[(sales_processed.csv)]
        TARGETS_P[(targets_processed.csv)]
        CRM_P[(crm_processed.csv)]
        TRAFFIC_P[(web_traffic_processed.csv)]
    end

    subgraph Gold["🥇 Gold layer (data/gold/)"]
        CSV[(final_dataframe.csv)]
        JSON[(pipeline_steps_report.json)]
        STATUS[(pipeline_runtime_status.json)]
    end

    PS -->|calls load_and_process_*| DS
    PS -->|calls calculate_metrics| MS
    PS -->|reads output_path| CFG
    DS --> FR
    DS --> AR
    DS -.->|depends on via DI| IDP
    MS -.->|depends on via DI| IMC
    DS -->|writes cleaned data| SALES_P
    DS -->|writes cleaned data| TARGETS_P
    DS -->|writes cleaned data| CRM_P
    DS -->|writes cleaned data| TRAFFIC_P
    PS -->|writes aggregated metrics| CSV
    PS -->|writes reports| JSON
    PS -->|writes status| STATUS
```

## Six-step execution flow (diagram)

```mermaid
%%{init: {'theme':'dark', 'themeVariables': { 'primaryColor':'#1e3a5f','primaryTextColor':'#e5eefc','primaryBorderColor':'#4a90e2','lineColor':'#6b9bd1','secondaryColor':'#2a4a6f','tertiaryColor':'#1a2332'}}}%%
flowchart TB
    Start([🚀 PipelineService.execute]):::startNode
    
    subgraph DataIngestion["📥 Data Ingestion · Steps 1-4<br/><small>🥉 Bronze → 🥈 Silver layer</small>"]
        S1["⚡ Step 1: Load Sales<br/><i>FileRepository → DataProcessor</i><br/>→ sales_processed.csv"]:::dataNode
        S2["⚡ Step 2: Load Targets<br/><i>FileRepository → DataProcessor</i><br/>→ targets_processed.csv"]:::dataNode
        S3["🔌 Step 3: Load CRM<br/><i>APIRepository → DataProcessor</i><br/>→ crm_processed.csv<br/><small>optional empty</small>"]:::optionalNode
        S4["🔌 Step 4: Load Traffic<br/><i>APIRepository → DataProcessor</i><br/>→ web_traffic_processed.csv<br/><small>optional empty</small>"]:::optionalNode
    end
    
    S5["🧮 Step 5: Calculate Metrics<br/><i>MetricsService.calculate_metrics</i><br/>Aggregate 4 DataFrames<br/><small>🥈 Silver → 🥇 Gold transformation</small>"]:::metricsNode
    
    S6["💾 Step 6: Persist Gold Layer<br/><i>sort · write CSV · MD5 checksum</i><br/>quality report · business summary<br/>→ final_dataframe.csv"]:::outputNode
    
    End([✅ return metrics DataFrame]):::endNode
    
    Start --> S1
    S1 --> S2
    S2 --> S3
    S3 --> S4
    S4 --> S5
    S5 --> S6
    S6 --> End
    
    classDef startNode fill:#2563eb,stroke:#3b82f6,stroke-width:3px,color:#fff
    classDef dataNode fill:#1e40af,stroke:#3b82f6,stroke-width:2px,color:#e5eefc
    classDef optionalNode fill:#1e3a5f,stroke:#6366f1,stroke-width:2px,color:#c7d2fe,stroke-dasharray: 5 5
    classDef metricsNode fill:#7c3aed,stroke:#a78bfa,stroke-width:2px,color:#e9d5ff
    classDef outputNode fill:#059669,stroke:#10b981,stroke-width:2px,color:#d1fae5
    classDef endNode fill:#16a34a,stroke:#22c55e,stroke-width:3px,color:#fff
```

## Silver layer persistence (Medallion Architecture)

### Purpose

The **Silver layer** (`data/silver/`) stores cleaned and standardized DataFrames after transformation, providing:

- **Audit trail**: Intermediate data for debugging and quality validation
- **Reusability**: Cleaned data can be consumed by other downstream processes
- **Data lineage**: Clear separation between raw ingestion and business aggregation

### Implementation

`DataService._save_to_silver_layer()` is called after each data processing step:

| Step | Input (Bronze) | Output (Silver) | Transformations |
|------|---------------|-----------------|-----------------|
| 1. Sales | `data/bronze/sales_builder_*.csv` | `data/silver/sales_processed.csv` | Deduplication, date standardization, community normalization |
| 2. Targets | `data/bronze/target_sales_builder_*.*` | `data/silver/targets_processed.csv` | Community normalization, month column addition |
| 3. CRM | API `/crm` | `data/silver/crm_processed.csv` | Date standardization, community mapping, column unification |
| 4. Traffic | API `/web-traffic` | `data/silver/web_traffic_processed.csv` | Community mapping, year_month extraction |

### Configuration

Silver layer path is configured in `config.yaml`:

```yaml
data:
  processed_path: "data/silver"  # Silver layer
```

The `DIContainer` passes `config.data.get_processed_path()` to `DataService` during initialization.
