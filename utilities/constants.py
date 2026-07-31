"""Centralized constants for sample registration notebooks.

Includes:
- UI styling (CSS, spinner HTML)
- Column definitions for data grids
- Schema configuration constants
"""

# ===== UI COMPONENTS =====

# Dashboard layout configuration
DASHBOARD_WIDTH = '2300px'

# Spinner HTML for async operation feedback
SPINNER_HTML = '''
<div style="display:flex;align-items:center;gap:12px;background:#fff3cd;padding:12px 16px;border-radius:6px">
  <div style="width:22px;height:22px;border:3px solid #ffc107;border-top-color:transparent;
              border-radius:50%;animation:spin 0.8s linear infinite"></div>
  <span>{msg}</span>
</div>
<style>@keyframes spin {{ to {{ transform: rotate(360deg); }} }}</style>
'''

# Common CSS styling for all notebooks
COMMON_CSS = """
    <style>
        /* General styling improvements */
        .jupyter-widgets {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* Button styling */
        .widget-button {
            background: linear-gradient(135deg, #274b8e 0%, #3b6db0 100%) !important;
            border: none !important;
            border-radius: 8px !important;
            color: white !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
        }
        
        .widget-button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
        }
        
        /* Dropdown styling */
        .widget-dropdown select {
            border: 2px solid #e1e8ed !important;
            border-radius: 8px !important;
            padding: 8px 12px !important;
            font-size: 14px !important;
        }
        
        /* Output area styling */
        .jupyter-widgets-output-area {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #28a745;
        }
    </style>
"""

# ===== SCHEMA DEFINITIONS =====

# Schema package prefixes
PLUGIN_PREFIX = 'nomad_battery_space.schema_packages.hzb_bs_package'
GEOMETRY_PREFIX = 'nomad_battery_space.schema_packages.utilities.geometry'


# ===== COLUMN DEFINITIONS =====
# Format: (database_key, display_label, data_type)

# Shape-specific columns (selected based on user choice)
SHAPE_COLUMNS = {
    'Circle': [
        ('diameter_mm', 'Diameter [mm]', 'float'),
    ],
    'Rectangle': [
        ('length_mm', 'Length [mm]', 'float'),
        ('width_mm', 'Width [mm]', 'float'),
    ],
    'Other': [
        ('shape_description', 'Shape Description', 'str'),
    ],
}

# Product information columns (optional, enabled by checkbox)
PRODUCT_INFO_COLUMNS = [
    ('product_number', 'Product Number', 'str'),
    ('lot_number', 'Lot Number', 'str'),
    ('product_volume', 'Product Volume [ml]', 'float'),
    ('product_weight', 'Product Weight [g]', 'float'),
    ('shipping_date', 'Shipping Date [YYYY-MM-DD]', 'str'),
    ('opening_date', 'Opening Date [YYYY-MM-DD]', 'str'),
    ('supplier', 'Supplier', 'str'),
    ('product_description', 'Product Description', 'str'),
    ('cost', 'Cost [EUR]', 'float'),
]