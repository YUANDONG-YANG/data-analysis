/**
 * Pipeline tour content — adapted from docs/*.md (MkDocs).
 * Diagrams use Mermaid source strings identical to the markdown files.
 */

export type TourStep = {
  id: string;
  path: string;
  number: string;
  title: string;
  subtitle?: string;
  sections: {
    heading: string;
    body?: string;
    mermaid?: string;
    table?: { headers: string[]; rows: string[][] };
    list?: string[];
    footnote?: string;
  }[];
  prevId?: string;
  nextId?: string;
};

/** Inline snippets as plain strings; pages render with <Code /> */
export const tourSteps: TourStep[] = [
  {
    id: "pipeline-overview",
    path: "/tour/pipeline-overview",
    number: "01",
    title: "Pipeline overview",
    subtitle: "End-to-end data flow and code layers",
    sections: [
      {
        heading: "Medallion Architecture (Three-tier data pipeline)",
        body: "This project follows the **Medallion Architecture** pattern with Bronze → Silver → Gold layers for progressive data quality improvement.",
        mermaid: `%%{init: {'theme':'base', 'themeVariables': {'primaryColor':'#1a1a2e','primaryTextColor':'#fff','primaryBorderColor':'#4a90e2','lineColor':'#4a90e2','secondaryColor':'#16213e','tertiaryColor':'#0f3460','background':'#1a1a2e','mainBkg':'#1a1a2e','secondBkg':'#16213e','tertiaryBkg':'#0f3460','textColor':'#e0e0e0','fontSize':'14px'}}}%%
flowchart LR
    subgraph Bronze["🥉 Bronze Layer<br/>(data/bronze/)"]
        direction TB
        CSV[Sales CSV<br/>Targets Excel/CSV]
        API[CRM API<br/>Web Traffic API]
    end
    
    subgraph Silver["🥈 Silver Layer<br/>(data/silver/)"]
        direction TB
        SP[sales_processed.csv<br/>✓ Deduplicated<br/>✓ Standardized dates]
        TP[targets_processed.csv<br/>✓ Community normalized]
        CP[crm_processed.csv<br/>✓ Unified date formats]
        WP[web_traffic_processed.csv<br/>✓ Community mapping]
    end
    
    subgraph Gold["🥇 Gold Layer<br/>(data/gold/)"]
        direction TB
        FD[final_dataframe.csv<br/>✓ Month × Community × Builder<br/>✓ KPIs & derived rates]
        RPT[pipeline_analysis_report.html<br/>pipeline_steps_report.json]
    end
    
    CSV --> SP
    API --> CP
    API --> WP
    CSV --> TP
    
    SP --> FD
    TP --> FD
    CP --> FD
    WP --> FD
    
    FD --> RPT
    
    classDef bronzeStyle fill:#3d2817,stroke:#d4a574,stroke-width:2px,color:#fff
    classDef silverStyle fill:#2c3e50,stroke:#95a5a6,stroke-width:2px,color:#fff
    classDef goldStyle fill:#1a472a,stroke:#f39c12,stroke-width:2px,color:#fff
    
    class Bronze,CSV,API bronzeStyle
    class Silver,SP,TP,CP,WP silverStyle
    class Gold,FD,RPT goldStyle`,
      },
      {
        heading: "End-to-end data flow",
        mermaid: `flowchart LR
    subgraph In["Input"]
        CSV[Sales / targets CSV·Excel]
        API[CRM / traffic API]
    end
    subgraph Load["Load"]
        FR[FileRepository]
        AR[APIRepository]
    end
    subgraph Transform["Transform"]
        DP[DataProcessor]
    end
    subgraph Metrics["Metrics"]
        MC[MetricsCalculator]
    end
    subgraph Out["Output"]
        CSV2[final_dataframe.csv]
    end
    CSV --> FR
    API --> AR
    FR --> DP
    AR --> DP
    DP --> MC
    MC --> CSV2`,
      },
      {
        heading: "Mapping to source layout",
        table: {
          headers: ["Stage", "Role", "Read next"],
          rows: [
            ["Startup", "main.py, config validation", "02 Startup and configuration"],
            ["Ingestion", "File + API repositories", "03 Data ingestion"],
            ["Cleaning", "Dates, community names, merges", "04 Cleaning and transformation"],
            ["Metrics", "Group, merge, derived columns", "05 Metrics"],
            ["Orchestration", "Six-step pipeline, CSV, logs", "06 Orchestration and output"],
            ["Wiring", "DI, factories", "07 DI and factories"],
          ],
        },
      },
      {
        heading: "Design patterns (short)",
        body: "Composition root (main) + DI (DIContainer) + factories (RepositoryFactory / ServiceFactory) + repositories (FileRepository / APIRepository) + application services (DataService / PipelineService) + protocol-based strategies (processor, calculator, API client).",
      },
    ],
    nextId: "startup-and-config",
  },
  {
    id: "startup-and-config",
    path: "/tour/startup-and-config",
    number: "02",
    title: "Startup and configuration",
    sections: [
      {
        heading: "Flow",
        list: [
          "main.py loads config.yaml → AppConfig.from_yaml().",
          "validate() checks API and logging settings.",
          "Build APIClient (if base_url and api_key are set), DataProcessor.from_config(config), and MetricsCalculator().",
          "DIContainer(config).build_pipeline_service(...) wires PipelineService and runs execute().",
        ],
        mermaid: `sequenceDiagram
    participant M as main
    participant CFG as AppConfig
    participant CNT as DIContainer
    participant PS as PipelineService

    M->>CFG: from_yaml + validate
    M->>CNT: build_pipeline_service(...)
    CNT->>CNT: RepositoryFactory + ServiceFactory
    CNT-->>M: PipelineService
    M->>PS: execute()`,
      },
      {
        heading: "Key configuration",
        list: [
          "api: base URL, key, timeout, endpoints.",
          "data: Bronze (raw_path), Silver (processed_path), Gold (output_path) — Medallion Architecture layers.",
          "community_names: aliases and URL path_slugs for DataProcessor.",
          "logging: level and format.",
        ],
      },
      {
        heading: "Data layer architecture (Medallion pattern)",
        body: "**Bronze layer** (data/bronze/): Immutable source data from files and APIs, no transformations. **Silver layer** (data/silver/): Cleaned, deduplicated, standardized DataFrames after DataProcessor transformation. **Gold layer** (data/gold/): Final aggregated metrics table consumed by dashboards and downstream systems.",
      },
      {
        heading: "Deeper architecture",
        list: [
          "Application composition: src/ARCHITECTURE.md",
          "Config and protocols: src/core/ARCHITECTURE.md",
        ],
      },
    ],
    prevId: "pipeline-overview",
    nextId: "data-ingestion",
  },
  {
    id: "data-ingestion",
    path: "/tour/data-ingestion",
    number: "03",
    title: "Data ingestion",
    sections: [
      {
        heading: "Role",
        body: "Turn raw records from files and the HTTP API into pandas.DataFrame instances for downstream steps.",
      },
      {
        heading: "Flow",
        mermaid: `flowchart TD
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
    WM --> M2`,
        footnote:
          "Sales and targets: loaded per builder, merged in DataService via DataProcessor.merge_dataframes. CRM / traffic: empty DataFrames if no API client; on failure, log a warning and degrade to empty tables.",
      },
      {
        heading: "Deeper architecture",
        list: [
          "src/repositories/ARCHITECTURE.md",
          "HTTP adapter: src/core/clients/ARCHITECTURE.md",
        ],
      },
    ],
    prevId: "startup-and-config",
    nextId: "cleaning-and-transformation",
  },
  {
    id: "cleaning-and-transformation",
    path: "/tour/cleaning-and-transformation",
    number: "04",
    title: "Cleaning and transformation",
    sections: [
      {
        heading: "Role",
        body: "DataProcessor (inside DataService) deduplicates, filters outliers, standardizes dates and community names, and derives fields such as `year_month`. A key goal in this stage is to turn many raw naming variants into one canonical business key: `community_name`.",
      },
      {
        heading: "Community name adaptation",
        body: "The pipeline treats community-name adaptation as a canonicalization step, not as a cosmetic rename. Sales files, target files, CRM records, and web-traffic paths all need to resolve to the same `community_name` before any merge or metric calculation can be trusted.",
        list: [
          "Config-driven aliases map known variants to one canonical name, for example `Maplewood-Heights` -> `Maplewood Heights`, `Fairview Est.` -> `Fairview Estates`, and `Riverbend TH` -> `Riverbend Townhomes`.",
          "The processor also removes noisy suffixes such as `(FVE)`, `Community`, and `- Phase 2`, then re-checks the cleaned value against the canonical lookup.",
          "URL traffic data is adapted through `path_slugs`, so a page path like `maplewood-heights` still lands on the same canonical community used by sales and targets.",
          "This makes `community_name` a stable integration key across sales, targets, CRM, and traffic instead of letting each source keep its own local label.",
        ],
      },
      {
        heading: "Component architecture",
        mermaid: `flowchart TB
    subgraph Application["Application service layer"]
        DS[DataService]
    end

    subgraph Contract["Core contract · Protocol"]
        IDP{{IDataProcessor}}
    end

    subgraph Domain["Domain transformation layer"]
        DP[DataProcessor]
    end

    subgraph Config["Configuration"]
        CNC[CommunityNamesConfig<br/>aliases + path_slugs]
    end

    subgraph Repositories["Data repositories"]
        FR[FileRepository]
        AR[APIRepository]
    end

    DS -.->|depends on via DI| IDP
    DP -.->|implements| IDP
    DP -->|reads| CNC
    DS -->|calls load_all_*| FR
    DS -->|calls load_all_*| AR
    DS -->|calls merge/clean/process_*| DP`,
      },
      {
        heading: "Four-path processing architecture",
        mermaid: `flowchart LR
    subgraph Sales["sales path"]
        S1[FileRepository] --> S2[merge_dataframes]
        S2 --> S3[clean_data<br/>dedupe + price/sqft bounds]
        S3 --> S4[process_sales_data<br/>standardize_date<br/>standardize_community_name<br/>derive year_month]
    end

    subgraph Targets["targets path"]
        T1[FileRepository] --> T2[merge_dataframes]
        T2 --> T3[clean_data<br/>dedupe + price/sqft bounds]
        T3 --> T4[process_targets_data<br/>standardize_community_name<br/>copy year_month if exists<br/>numeric target_sales]
    end

    subgraph CRM["crm path"]
        C1[APIRepository] --> C2[merge_dataframes]
        C2 --> C3[process_crm_data<br/>pick date column + standardize_date<br/>derive year_month<br/>pick community column + standardize_community_name]
    end

    subgraph Traffic["traffic path"]
        W1[APIRepository] --> W2[merge_dataframes]
        W2 --> W3[process_web_traffic_data<br/>pick date column + standardize_date<br/>derive year_month<br/>if page_path: _extract_community_from_path<br/>else: standardize_community_name]
    end`,
        footnote:
          "Sales and targets use clean_data for outlier filtering; CRM and traffic skip clean_data. Community name standardization uses config-driven aliases + regex patterns. Traffic extraction uses path_slugs longest-first matching.",
      },
      {
        heading: "Why this matters for modeling and governance",
        table: {
          headers: ["Capability", "How community-name adaptation supports it"],
          rows: [
            [
              "Data modeling",
              "Creates one canonical `community_name` dimension so every source can join on the same reporting key.",
            ],
            [
              "Architecture design",
              "Keeps standardization rules in `DataProcessor` and `config.yaml`, separate from repositories, metrics, and UI code.",
            ],
            [
              "Conflict resolution",
              "Resolves naming conflicts such as abbreviations, hyphen variants, phase labels, and parenthetical labels before merging datasets.",
            ],
            [
              "Data governance",
              "Makes the transformation deterministic, configurable, and auditable through centralized alias rules plus before/after pipeline snapshots.",
            ],
          ],
        },
      },
      {
        heading: "Deeper architecture",
        list: ["src/core/processors/ARCHITECTURE.md"],
      },
    ],
    prevId: "data-ingestion",
    nextId: "metrics",
  },
  {
    id: "metrics",
    path: "/tour/metrics",
    number: "05",
    title: "Metrics",
    sections: [
      {
        heading: "Role",
        body: "`MetricsService` is a thin application service. It delegates all metric construction to `MetricsCalculator`, which acts as a pure domain component over processed pandas DataFrames and returns one business-readable monthly metrics table.",
      },
      {
        heading: "Architecture",
        mermaid: `flowchart TB
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
    MC --> RESULT`,
      },
      {
        heading: "Deeper architecture",
        list: [
          "src/core/calculators/ARCHITECTURE.md",
          "Thin service layer: src/services/ARCHITECTURE.md (includes MetricsService)",
        ],
      },
    ],
    prevId: "cleaning-and-transformation",
    nextId: "orchestration-and-output",
  },
  {
    id: "orchestration-and-output",
    path: "/tour/orchestration-and-output",
    number: "06",
    title: "Orchestration and output",
    sections: [
      {
        heading: "Role",
        body: "PipelineService.execute() calls DataService and MetricsService in fixed steps, writes data/gold/final_dataframe.csv, and logs quality and business summaries.",
      },
      {
        heading: "Component architecture",
        mermaid: `flowchart TB
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

    subgraph Output["Output artifacts"]
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
    PS -->|writes| CSV
    PS -->|writes| JSON
    PS -->|writes| STATUS`,
      },
      {
        heading: "Six-step execution flow",
        mermaid: `%%{init: {'theme':'dark', 'themeVariables': { 'primaryColor':'#1e3a5f','primaryTextColor':'#e5eefc','primaryBorderColor':'#4a90e2','lineColor':'#6b9bd1','secondaryColor':'#2a4a6f','tertiaryColor':'#1a2332'}}}%%
flowchart TB
    Start([🚀 PipelineService.execute]):::startNode
    
    subgraph DataIngestion["📥 Data Ingestion · Steps 1-4"]
        S1["⚡ Step 1: Load Sales<br/><i>FileRepository → DataProcessor</i>"]:::dataNode
        S2["⚡ Step 2: Load Targets<br/><i>FileRepository → DataProcessor</i>"]:::dataNode
        S3["🔌 Step 3: Load CRM<br/><i>APIRepository → DataProcessor</i><br/><small>optional empty</small>"]:::optionalNode
        S4["🔌 Step 4: Load Traffic<br/><i>APIRepository → DataProcessor</i><br/><small>optional empty</small>"]:::optionalNode
    end
    
    S5["🧮 Step 5: Calculate Metrics<br/><i>MetricsService.calculate_metrics</i><br/>Aggregate 4 DataFrames"]:::metricsNode
    
    S6["💾 Step 6: Persist Output<br/><i>sort · write CSV · MD5 checksum</i><br/>quality report · business summary"]:::outputNode
    
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
    classDef endNode fill:#16a34a,stroke:#22c55e,stroke-width:3px,color:#fff`,
      },
      {
        heading: "Output",
        body: "Path from config.data.output_path, file name final_dataframe.csv. Data layout: data/ARCHITECTURE.md",
      },
      {
        heading: "Deeper architecture",
        list: ["src/services/ARCHITECTURE.md"],
      },
    ],
    prevId: "metrics",
    nextId: "di-and-factories",
  },
  {
    id: "di-and-factories",
    path: "/tour/di-and-factories",
    number: "07",
    title: "Dependency injection and factories",
    sections: [
      {
        heading: "Role",
        body: "Without changing domain constructor signatures, DIContainer uses factories to create FileRepository, APIRepository, DataService, MetricsService, and PipelineService and wire the full graph.",
      },
      {
        heading: "Flow",
        mermaid: `flowchart TD
    A[DIContainer holds AppConfig] --> B[RepositoryFactory]
    B --> C[FileRepository]
    B --> D[APIRepository]
    A --> E[ServiceFactory]
    E --> F[DataService]
    E --> G[MetricsService]
    E --> H[PipelineService]
    C --> F
    D --> F
    H --> F
    H --> G`,
      },
      {
        heading: "Deeper architecture",
        list: [
          "src/di/ARCHITECTURE.md",
          "src/factories/ARCHITECTURE.md",
          "Full-stack dependency graph: src/ARCHITECTURE.md",
        ],
      },
    ],
    prevId: "orchestration-and-output",
  },
];

export const tourById = Object.fromEntries(tourSteps.map((s) => [s.id, s]));

export const homeContent = {
  title: "Real Estate Heterogeneous Data Analytics",
  lead:
    "Documentation experience aligned with PipelineService.execute() — seven chapters, interactive diagrams, and typography tuned for long reads.",
  bullets: [
    {
      title: "Pipeline tour",
      text: "End-to-end flow in seven chapters — same narrative as the MkDocs site.",
    },
    {
      title: "Architecture",
      text: "ARCHITECTURE.md files live next to the code; consult the repository or MkDocs for the full tree.",
    },
    {
      title: "Diagrams",
      text: "Mermaid renders in-browser with a dark theme to match this UI.",
    },
  ],
};
