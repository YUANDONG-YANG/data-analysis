# `core/` architecture

## Design patterns in this layer

| Pattern | Where |
|---------|--------|
| **Protocol (structural typing)** | `IDataProcessor`, `IAPIClient`, `IMetricsCalculator`, etc. — pluggable implementations |
| **ABC / template** | `IConfiguration`, `DataRepository` (under `repositories`), and other contracts |
| **Configuration aggregate** | `AppConfig` and nested dataclasses (`APIConfig`, `DataConfig`, `CommunityNamesConfig`) |
| **Centralized error model** | Layered exceptions in `exceptions.py` for consistent handling upstream |

## Package layout (diagram)

```mermaid
flowchart LR
    subgraph core["src/core"]
        IF["interfaces.py<br/>Protocol & ABC"]
        CFG["config.py<br/>AppConfig"]
        EX["exceptions.py"]
        LOG["logger.py<br/>structured_logger.py"]
        U["utils.py"]
        subgraph calc["calculators/"]
            MC[MetricsCalculator]
        end
        subgraph proc["processors/"]
            DP[DataProcessor]
        end
        subgraph cli["clients/"]
            AC[APIClient]
        end
    end

    IF -.->|implements| DP
    IF -.->|implements| MC
    IF -.->|implements| AC
    DP --> CFG
    AC -.->|raises| EX
    MC -.->|Protocol| IF
```

## Configuration load flow (diagram)

```mermaid
flowchart TD
    A[Read config.yaml] --> B[safe_load to dict]
    B --> C[APIConfig + DataConfig + LoggingConfig]
    B --> D[CommunityNamesConfig parse / defaults]
    C --> E[AppConfig aggregate]
    D --> E
    E --> F[validate: API & logging]
    F --> G[Used by main / DataProcessor.from_config]
```
