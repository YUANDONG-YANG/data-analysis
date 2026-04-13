# `core/processors/` architecture

## Design patterns in this layer

| Pattern | Where |
|---------|--------|
| **Strategy (interface-level)** | `DataProcessor` implements `IDataProcessor`; swap at composition root |
| **Configurable transformation** | Community aliases and URL slugs come from `CommunityNamesConfig`, not hard-coded in class |

## Classes and config (diagram)

```mermaid
classDiagram
    class IDataProcessor {
        <<Protocol>>
        +clean_data(df)
        +process_sales_data(df)
        +process_targets_data(df)
        +process_crm_data(df)
        +process_web_traffic_data(df)
        +merge_dataframes(list)
    }
    class DataProcessor {
        -_community_aliases: dict
        -_path_slugs_sorted: list
        +from_config(config) DataProcessor
        +standardize_date(str)
        +standardize_community_name(str)
        +merge_dataframes(...)
        +clean_data(df)
        +process_* per domain
        -_extract_community_from_path(str)
    }
    class CommunityNamesConfig {
        +aliases
        +path_slugs
    }
    IDataProcessor <.. DataProcessor : implements
    DataProcessor ..> CommunityNamesConfig : reads
```

## Component architecture (diagram)

```mermaid
flowchart TB
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
    DS -->|calls merge/clean/process_*| DP
```

## Four-path processing architecture (diagram)

```mermaid
flowchart LR
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
    end
```

**Key differences:**
- Sales and targets use `clean_data` for outlier filtering; CRM and traffic skip it.
- Targets do not call `standardize_date`; they only standardize community names and ensure numeric target values.
- CRM and traffic pick date/community columns dynamically based on what the API response contains.
- Traffic uses `_extract_community_from_path` for `page_path` columns, matching `path_slugs` longest-first.
