"""
Generic helper functions for sample registration notebooks.

These functions are schema-agnostic and work with any sample type.
"""

import pandas as pd
from IPython.display import HTML


def extract_grid_frame(grid, col_labels):
    """Extract the current grid data as a DataFrame.
    
    Args:
        grid: The ipyaggrid.Grid widget instance
        col_labels: List of column labels for empty DataFrame fallback
    
    Returns:
        pd.DataFrame: Grid data extracted and reset with clean index
    """
    if grid is None:
        return pd.DataFrame(columns=col_labels)

    grid_data_out = getattr(grid, 'grid_data_out', {}) or {}
    candidate = grid_data_out.get('grid') if isinstance(grid_data_out, dict) else None

    if isinstance(candidate, pd.DataFrame):
        return candidate.copy().reset_index(drop=True)
    if isinstance(candidate, list):
        return pd.DataFrame(candidate).reset_index(drop=True)
    if isinstance(getattr(grid, 'grid_data', None), pd.DataFrame):
        return grid.grid_data.copy().reset_index(drop=True)
    return pd.DataFrame(columns=col_labels)


def validate_row(schema_name, schema, row_by_key):
    """Validate a row against schema requirements.
    
    Args:
        schema_name: Name of the schema (for error messages)
        schema: Schema dict with 'required_keys' and 'columns'
        row_by_key: Dict mapping column keys to values
    
    Returns:
        str or None: Error message if validation fails, None if valid
    """
    missing = [key for key in schema['required_keys'] if not row_by_key.get(key)]
    if missing:
        missing_labels = []
        for key in missing:
            for column_key, column_label, _dtype in schema['columns']:
                if column_key == key:
                    missing_labels.append(column_label)
                    break
        return f"Missing required fields: {', '.join(missing_labels)}"
    return None


def render_status(kind, message):
    """Render a colored status message box.
    
    Args:
        kind: Message type ('error', 'warning', 'success', 'info')
        message: Message text (can include HTML)
    
    Returns:
        HTML: Formatted HTML widget with styled status box
    """
    colors = {
        'error': '#f8d7da',
        'warning': '#fff3cd',
        'success': '#d4edda',
        'info': '#d1ecf1',
    }
    return HTML(
        f'<div style="background:{colors[kind]};padding:10px;border-radius:6px;margin-bottom:6px">{message}</div>'
    )
