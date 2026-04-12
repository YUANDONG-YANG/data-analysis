# `core/clients/` architecture

## Design patterns in this layer

| Pattern | Where |
|---------|--------|
| **Gateway / adapter** | `APIClient` maps HTTP JSON to `pandas.DataFrame` |
| **Retry + backoff** | Limited retries on timeout, connection errors, and selected 5xx |
| **Guard / defensive filter** | `_enforce_builder_consistency` prevents cross-builder data leakage |

## Classes and protocol (diagram)

```mermaid
classDiagram
    class IAPIClient {
        <<Protocol>>
        +get_crm_data(builder)
        +get_web_traffic_data(builder)
    }
    class APIClient {
        +get(endpoint, params)
        +get_crm_data(builder)
        +get_web_traffic_data(builder)
        -_enforce_builder_consistency(df, builder, ...)
        -_standardize_crm_columns(df, builder)
    }
    IAPIClient <.. APIClient : implements
```

## HTTP call flow (diagram)

```mermaid
flowchart TD
    A[get_crm / get_web_traffic] --> B[Build URL + Bearer]
    B --> C{GET attempt}
    C -->|2xx| D[response.json]
    C -->|retryable| E[sleep exponential backoff]
    E --> C
    C -->|fatal| F[Raise APIClientError / NetworkError / TimeoutError]
    D --> G[Parse list or data key to DataFrame]
    G --> H[_enforce_builder_consistency]
    H --> I[Set builder column + column rename]
    I --> J[Return DataFrame]
```
