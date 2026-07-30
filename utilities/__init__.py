"""Shared utilities for NOMAD sample registration notebooks."""

# Re-export UI components from shared_css
from .shared_css import (
    SPINNER_HTML,
    COMMON_CSS,
)

# Re-export from api_calls (API client and utility functions)
from .api_calls import (
    NOMADAPIClient,
    clean_text,
    normalize_value,
    normalize_sample_id,
    coerce_value,
    make_row_by_key,
    wait_for_sample_ids,
    resolve_name_to_reference,
    resolve_reference_to_name,
)

# Re-export from help_functions (generic helper functions)
from .help_functions import (
    extract_grid_frame,
    validate_row,
    render_status,
)

__all__ = [
    'SPINNER_HTML',
    'COMMON_CSS',
    'NOMADAPIClient',
    'clean_text',
    'normalize_value',
    'normalize_sample_id',
    'coerce_value',
    'make_row_by_key',
    'wait_for_sample_ids',
    'resolve_name_to_reference',
    'resolve_reference_to_name',
    'extract_grid_frame',
    'validate_row',
    'render_status',
]
