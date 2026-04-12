"""
API client module for interacting with external APIs.
"""
import requests
from typing import Dict, Any, Optional, List
import pandas as pd
import logging
import time
import math
from ..exceptions import APIClientError, NetworkError, TimeoutError


class APIClient:
    """API client class for making HTTP requests."""
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 30,
        max_retries: int = 3,
        retry_backoff_factor: float = 1.0,
        retry_status_codes: Optional[List[int]] = None
    ):
        """
        Initialize API client.
        
        Args:
            base_url: API base URL
            api_key: API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_backoff_factor: Backoff factor for exponential retry delay
            retry_status_codes: HTTP status codes that should trigger retry
        """
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor
        self.retry_status_codes = retry_status_codes or [500, 502, 503, 504]
        self.headers = {
            "Authorization": f"Bearer {api_key}"
        }
        self.logger = logging.getLogger(__name__)
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send GET request to API endpoint with retry mechanism.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            API response data as dictionary
            
        Raises:
            APIClientError: If request fails after all retries
            NetworkError: For network-related errors
            TimeoutError: For timeout errors
        """
        url = f"{self.base_url}{endpoint}"
        request_id = str(time.time_ns())[-12:]  # Unique request ID
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            # Log request details
            self.logger.info(
                f"API Request: {endpoint}",
                extra={
                    'context': {
                        'request_id': request_id,
                        'endpoint': endpoint,
                        'url': url,
                        'method': 'GET',
                        'params': params,
                        'retry_attempt': attempt,
                        'max_retries': self.max_retries,
                        'timeout_seconds': self.timeout
                    }
                }
            )
            
            start_time = time.time()
            try:
                response = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
                elapsed_time = time.time() - start_time
                
                # Log response details
                response_size = len(response.content) if response.content else 0
                self.logger.info(
                    f"API Response: {endpoint} - Status {response.status_code}",
                    extra={
                        'context': {
                            'request_id': request_id,
                            'endpoint': endpoint,
                            'status_code': response.status_code,
                            'retry_attempt': attempt,
                            'timeout_seconds': self.timeout
                        },
                        'performance': {
                            'response_time_seconds': round(elapsed_time, 3),
                            'response_size_bytes': response_size
                        }
                    }
                )
                
                # Check if status code indicates retryable error
                if response.status_code in self.retry_status_codes and attempt < self.max_retries:
                    wait_time = self.retry_backoff_factor * (2 ** attempt)
                    self.logger.warning(
                        f"API returned retryable status {response.status_code}, retrying in {wait_time}s",
                        extra={
                            'context': {
                                'request_id': request_id,
                                'endpoint': endpoint,
                                'status_code': response.status_code,
                                'retry_attempt': attempt,
                                'next_retry_in_seconds': wait_time
                            }
                        }
                    )
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                
                data = response.json()
                
                # Log data structure information
                data_info = self._extract_data_info(data)
                self.logger.debug(
                    f"API Data Structure: {endpoint}",
                    extra={
                        'context': {
                            'request_id': request_id,
                            'endpoint': endpoint,
                            **data_info
                        }
                    }
                )
                
                return data
                
            except requests.exceptions.Timeout as e:
                elapsed_time = time.time() - start_time
                last_exception = TimeoutError(
                    f"API request timeout: {endpoint}",
                    endpoint=endpoint,
                    timeout=self.timeout,
                    context={
                        'request_id': request_id,
                        'retry_attempt': attempt,
                        'elapsed_seconds': round(elapsed_time, 3)
                    }
                )
                
                if attempt < self.max_retries:
                    wait_time = self.retry_backoff_factor * (2 ** attempt)
                    self.logger.warning(
                        f"API request timeout, retrying in {wait_time}s",
                        extra={
                            'context': {
                                'request_id': request_id,
                                'endpoint': endpoint,
                                'retry_attempt': attempt,
                                'next_retry_in_seconds': wait_time,
                                'timeout_seconds': self.timeout
                            }
                        }
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(
                        f"API request timeout after {self.max_retries} retries: {endpoint}",
                        extra={
                            'context': {
                                'request_id': request_id,
                                'endpoint': endpoint,
                                'retry_attempt': attempt,
                                'timeout_seconds': self.timeout
                            },
                            'performance': {
                                'failed_after_seconds': round(elapsed_time, 3)
                            }
                        },
                        exc_info=True
                    )
                    raise last_exception
                    
            except requests.exceptions.ConnectionError as e:
                elapsed_time = time.time() - start_time
                last_exception = NetworkError(
                    f"API connection error: {endpoint} - {str(e)}",
                    endpoint=endpoint,
                    context={
                        'request_id': request_id,
                        'retry_attempt': attempt,
                        'elapsed_seconds': round(elapsed_time, 3)
                    }
                )
                
                if attempt < self.max_retries:
                    wait_time = self.retry_backoff_factor * (2 ** attempt)
                    self.logger.warning(
                        f"API connection error, retrying in {wait_time}s",
                        extra={
                            'context': {
                                'request_id': request_id,
                                'endpoint': endpoint,
                                'retry_attempt': attempt,
                                'next_retry_in_seconds': wait_time
                            }
                        }
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(
                        f"API connection error after {self.max_retries} retries: {endpoint}",
                        extra={
                            'context': {
                                'request_id': request_id,
                                'endpoint': endpoint,
                                'retry_attempt': attempt
                            },
                            'performance': {
                                'failed_after_seconds': round(elapsed_time, 3)
                            }
                        },
                        exc_info=True
                    )
                    raise last_exception
                    
            except requests.exceptions.HTTPError as e:
                elapsed_time = time.time() - start_time
                status_code = e.response.status_code if hasattr(e, 'response') and e.response else None
                
                # Only retry on server errors (5xx)
                if status_code and status_code >= 500 and attempt < self.max_retries:
                    wait_time = self.retry_backoff_factor * (2 ** attempt)
                    self.logger.warning(
                        f"API HTTP error {status_code}, retrying in {wait_time}s",
                        extra={
                            'context': {
                                'request_id': request_id,
                                'endpoint': endpoint,
                                'status_code': status_code,
                                'retry_attempt': attempt,
                                'next_retry_in_seconds': wait_time
                            }
                        }
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    # Client errors (4xx) are not retryable
                    error = APIClientError(
                        f"API HTTP error: {endpoint} - {str(e)}",
                        endpoint=endpoint,
                        status_code=status_code,
                        retryable=False,
                        context={
                            'request_id': request_id,
                            'retry_attempt': attempt
                        }
                    )
                    self.logger.error(
                        f"API HTTP error: {endpoint}",
                        extra={
                            'context': {
                                'request_id': request_id,
                                'endpoint': endpoint,
                                'status_code': status_code,
                                'retry_attempt': attempt
                            },
                            'performance': {
                                'failed_after_seconds': round(elapsed_time, 3)
                            }
                        },
                        exc_info=True
                    )
                    raise error
                    
            except requests.exceptions.RequestException as e:
                elapsed_time = time.time() - start_time
                last_exception = NetworkError(
                    f"API request failed: {endpoint} - {str(e)}",
                    endpoint=endpoint,
                    context={
                        'request_id': request_id,
                        'retry_attempt': attempt,
                        'error_type': type(e).__name__,
                        'elapsed_seconds': round(elapsed_time, 3)
                    }
                )
                
                if attempt < self.max_retries:
                    wait_time = self.retry_backoff_factor * (2 ** attempt)
                    self.logger.warning(
                        f"API request failed, retrying in {wait_time}s",
                        extra={
                            'context': {
                                'request_id': request_id,
                                'endpoint': endpoint,
                                'retry_attempt': attempt,
                                'next_retry_in_seconds': wait_time,
                                'error_type': type(e).__name__
                            }
                        }
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(
                        f"API request failed after {self.max_retries} retries: {endpoint}",
                        extra={
                            'context': {
                                'request_id': request_id,
                                'endpoint': endpoint,
                                'retry_attempt': attempt,
                                'error_type': type(e).__name__
                            },
                            'performance': {
                                'failed_after_seconds': round(elapsed_time, 3)
                            }
                        },
                        exc_info=True
                    )
                    raise last_exception
        
        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
        raise APIClientError(f"API request failed after {self.max_retries} retries: {endpoint}", endpoint=endpoint)
    
    def _extract_data_info(self, data: Any) -> Dict[str, Any]:
        """Extract data structure information for logging."""
        info = {}
        
        if isinstance(data, list):
            info['data_type'] = 'list'
            info['record_count'] = len(data)
            if len(data) > 0 and isinstance(data[0], dict):
                info['sample_keys'] = list(data[0].keys())[:10]  # First 10 keys
        elif isinstance(data, dict):
            info['data_type'] = 'dict'
            info['keys'] = list(data.keys())
            if 'data' in data and isinstance(data['data'], list):
                info['record_count'] = len(data['data'])
        else:
            info['data_type'] = type(data).__name__
        
        return info

    def _enforce_builder_consistency(
        self,
        df: pd.DataFrame,
        requested_builder: str,
        data_type: str,
        request_id: Optional[str] = None,
        mismatch_error_threshold: float = 0.2,
    ) -> pd.DataFrame:
        """
        Prevent cross-builder data leakage.

        Some APIs may include a builder field (or a variant) in the payload. If present,
        verify it matches the requested builder. Mismatching rows are filtered and a
        warning is logged. If the mismatch ratio is high, raise to avoid silently
        polluting downstream metrics.

        Notes:
        - This does not replace setting `df['builder'] = requested_builder`; it
          validates the upstream payload when it provides builder attribution.
        - If the payload does not include any builder attribution, this is a no-op.
        """
        if df is None or df.empty:
            return df

        requested = str(requested_builder).strip().lower()
        if requested not in {"a", "b"}:
            # Avoid false positives if caller uses unexpected builder identifiers.
            return df

        # Common builder field names we might see in payloads
        candidate_cols = [c for c in ["builder", "builder_id", "builderId"] if c in df.columns]
        if not candidate_cols:
            return df

        col = candidate_cols[0]
        series = df[col]
        # Normalize to 'a'/'b' when possible (e.g. 'builder_a', 'A', 'a')
        normalized = series.astype(str).str.strip().str.lower()
        normalized = normalized.str[-1].where(normalized.str[-1].isin(["a", "b"]), normalized)

        mismatched_mask = (normalized.notna()) & (normalized != "") & (normalized != requested)
        mismatched_count = int(mismatched_mask.sum())
        total = int(len(df))

        if mismatched_count <= 0:
            return df

        mismatch_ratio = mismatched_count / max(total, 1)
        sample_rows = (
            df.loc[mismatched_mask, [col]]
            .head(5)
            .to_dict(orient="records")
        )

        self.logger.warning(
            "Builder mismatch detected in API payload; filtering mismatched rows to prevent data leakage",
            extra={
                "context": {
                    "request_id": request_id,
                    "data_type": data_type,
                    "requested_builder": requested,
                    "builder_field": col,
                    "total_rows": total,
                    "mismatched_rows": mismatched_count,
                    "mismatch_ratio": round(mismatch_ratio, 6),
                    "mismatched_samples": sample_rows,
                }
            },
        )

        if mismatch_ratio >= mismatch_error_threshold:
            raise APIClientError(
                f"Builder mismatch ratio too high for {data_type}: {mismatch_ratio:.2%}",
                endpoint=data_type,
                retryable=False,
                context={
                    "request_id": request_id,
                    "requested_builder": requested,
                    "builder_field": col,
                    "total_rows": total,
                    "mismatched_rows": mismatched_count,
                    "mismatch_ratio": mismatch_ratio,
                },
            )

        return df.loc[~mismatched_mask].copy()
    
    def get_crm_data(self, builder: str) -> pd.DataFrame:
        """
        Get CRM data for specified builder.
        
        Args:
            builder: Builder identifier ('a' or 'b')
            
        Returns:
            CRM data as DataFrame with builder column
        """
        self.logger.info(
            f"Loading CRM data for builder {builder.upper()}",
            extra={'context': {'builder': builder, 'data_type': 'crm'}}
        )
        
        params = {"builder": builder}
        data = self.get("/crm", params=params)
        
        # Convert JSON data to DataFrame
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict) and 'data' in data:
            df = pd.DataFrame(data['data'])
        else:
            df = pd.DataFrame([data])
        
        # Add builder identifier
        if not df.empty:
            # If upstream payload includes builder attribution, validate before overriding.
            df = self._enforce_builder_consistency(df, builder, data_type="crm")
            df['builder'] = builder
            # Standardize column names for different builders
            df = self._standardize_crm_columns(df, builder)
        
        # Log DataFrame information
        self.logger.info(
            f"Loaded CRM DataFrame for builder {builder.upper()}",
            extra={
                'context': {
                    'builder': builder,
                    'data_type': 'crm',
                    'rows': len(df),
                    'columns': len(df.columns) if not df.empty else 0,
                    'column_names': list(df.columns) if not df.empty else []
                }
            }
        )
        
        return df
    
    def _standardize_crm_columns(self, df: pd.DataFrame, builder: str) -> pd.DataFrame:
        """
        Standardize CRM column names for different builders.
        
        Args:
            df: CRM DataFrame
            builder: Builder identifier
            
        Returns:
            DataFrame with standardized column names
        """
        if df.empty:
            return df
        
        df = df.copy()
        
        if builder == 'a':
            # Builder A: createdate -> create_date
            if 'createdate' in df.columns:
                df['create_date'] = df['createdate']
                # Keep original for backwards compatibility if needed
        elif builder == 'b':
            # Builder B: create_at -> create_date
            if 'create_at' in df.columns:
                df['create_date'] = df['create_at']
        
        # Log standardization results
        self.logger.info(
            f"Standardized CRM data for builder {builder}",
            extra={
                'context': {
                    'builder': builder,
                    'rows_after_standardization': len(df),
                    'has_create_date_column': 'create_date' in df.columns,
                    'sample_communities': df['community'].unique()[:5].tolist() if 'community' in df.columns else []
                }
            }
        )
        
        return df
    
    def get_web_traffic_data(self, builder: str) -> pd.DataFrame:
        """
        Get Web Traffic data for specified builder.
        
        Args:
            builder: Builder identifier ('a' or 'b')
            
        Returns:
            Web Traffic data as DataFrame with builder column
        """
        self.logger.info(
            f"Loading Web Traffic data for builder {builder.upper()}",
            extra={'context': {'builder': builder, 'data_type': 'web_traffic'}}
        )
        
        params = {"builder": builder}
        data = self.get("/web-traffic", params=params)
        
        # Convert JSON data to DataFrame
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict) and 'data' in data:
            df = pd.DataFrame(data['data'])
        else:
            df = pd.DataFrame([data])
        
        # Add builder identifier
        if not df.empty:
            # If upstream payload includes builder attribution, validate before overriding.
            df = self._enforce_builder_consistency(df, builder, data_type="web_traffic")
            df['builder'] = builder
        
        # Log DataFrame information
        self.logger.info(
            f"Loaded Web Traffic DataFrame for builder {builder.upper()}",
            extra={
                'context': {
                    'builder': builder,
                    'data_type': 'web_traffic',
                    'rows': len(df),
                    'columns': len(df.columns) if not df.empty else 0,
                    'column_names': list(df.columns) if not df.empty else []
                }
            }
        )
        
        return df
