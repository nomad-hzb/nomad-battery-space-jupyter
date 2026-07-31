"""Shared utilities for NOMAD sample registration notebooks."""

# Re-export constants (UI components, column definitions)
from .constants import (
    SPINNER_HTML,
    COMMON_CSS,
    SHAPE_COLUMNS,
    PRODUCT_INFO_COLUMNS,
    DASHBOARD_WIDTH,
    PLUGIN_PREFIX,
    GEOMETRY_PREFIX,
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
    # Constants
    'SPINNER_HTML',
    'COMMON_CSS',
    'SHAPE_COLUMNS',
    'PRODUCT_INFO_COLUMNS',
    'DASHBOARD_WIDTH',
    'PLUGIN_PREFIX',
    'GEOMETRY_PREFIX',
    # API client
    'NOMADAPIClient',
    # API utilities
    'clean_text',
    'normalize_value',
    'normalize_sample_id',
    'coerce_value',
    'make_row_by_key',
    'wait_for_sample_ids',
    'resolve_name_to_reference',
    'resolve_reference_to_name',
    # Grid & validation
    'extract_grid_frame',
    'validate_row',
    'render_status',
]
