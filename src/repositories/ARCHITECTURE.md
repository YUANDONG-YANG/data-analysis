# `repositories/` architecture

## Design patterns in this layer

| Pattern | Where |
|---------|--------|
| **Repository** | Hides data source details; exposes “load per builder” semantics |
| **Abstract class + template method** | `DataRepository` provides default `load_all_sales_data` / `load_all_targets_data` |
| **Specialized repository** | `FileRepository` (CSV/Excel), `APIRepository` (delegates to `IAPIClient`) |

## Class diagram

```mermaid
classDiagram
    class DataRepository {
        <<abstract>>
        +load_sales_data(builder)*
        +load_targets_data(builder)*
        +load_all_sales_data()
        +load_all_targets_data()
    }
    class FileRepository {
        +load_csv / load_excel
        +load_sales_data(builder)
        +load_targets_data(builder)
    }
    class APIRepository {
        -api_client: IAPIClient
        +load_crm_data(builder)
        +load_web_traffic_data(builder)
        +load_all_crm_data()
        +load_all_web_traffic_data()
    }
    class IAPIClient {
        <<Protocol>>
    }
    DataRepository <|-- FileRepository
    DataRepository <|-- APIRepository
    APIRepository --> IAPIClient : uses
```

## Load flow (diagram)

```mermaid
flowchart TD
    subgraph File["FileRepository"]
        F1["sales: sales_builder_a|b.csv"] --> F2[add builder column]
        F3[targets: xlsx/csv parsers] --> F4[long: year_month + community + target]
    end
    subgraph API["APIRepository"]
        A1[load_all_crm_data] --> A2[load_crm a then b]
        A3[load_all_web_traffic_data] --> A4[load_traffic a then b]
        A2 --> A5[api_client.get_crm_data]
        A4 --> A6[api_client.get_web_traffic_data]
    end
```
