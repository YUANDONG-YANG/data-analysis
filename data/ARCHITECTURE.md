# `data/` directory (layout)

## Role

Not a code package: holds **batch pipeline inputs and outputs**. Paths are defined by root `config.yaml`: `data.raw_path`, `data.processed_path`, `data.output_path`.

## Directory structure (diagram)

```mermaid
flowchart TB
    subgraph data["data/"]
        R[raw/ archive or source]
        P[processed/ CSV inputs read by pipeline]
        O[output/ final_dataframe.csv]
    end
    R -.->|per config| P
    P -->|FileRepository| PIPE[Pipeline]
    PIPE --> O
```

## Data flow (diagram)

```mermaid
flowchart LR
    S[Sales / target files] --> P[data/processed or configured path]
    P --> L[Load & clean]
    L --> M[Metrics merge]
    M --> OUT[data/output/final_dataframe.csv]
```
