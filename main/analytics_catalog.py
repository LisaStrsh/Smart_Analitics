"""
Catalog of analytical visualizations.
Each entry: id, name, short_desc, category, icon, required_mappings, min_rows, usefulness.
Categories: overview, trends, risks, opportunities, details
"""

CATEGORIES = {
    'overview': {'name': 'Overview', 'icon': 'fa-chart-pie', 'color': '#4e79a7'},
    'trends': {'name': 'Trends', 'icon': 'fa-chart-line', 'color': '#59a14f'},
    'risks': {'name': 'Risks', 'icon': 'fa-triangle-exclamation', 'color': '#e15759'},
    'opportunities': {'name': 'Opportunities', 'icon': 'fa-lightbulb', 'color': '#f28e2b'},
    'details': {'name': 'Details', 'icon': 'fa-magnifying-glass', 'color': '#76b7b2'},
}

def _e(id, name, short, cat, icon, mappings, min_rows=5, usefulness=5, needs_numeric=False):
    return {
        'id': id, 'name': name, 'short_desc': short, 'category': cat,
        'icon': icon, 'required_mappings': mappings, 'min_rows': min_rows,
        'usefulness': usefulness, 'needs_numeric': needs_numeric,
    }

ANALYTICS_CATALOG = [
    # ===== OVERVIEW =====
    _e('total_revenue', 'Total Revenue', 'Total revenue for the entire period', 'overview', 'fa-coins', ['total'], 1, 10, True),
    _e('total_orders', 'Total Orders', 'Total number of orders', 'overview', 'fa-receipt', ['order_id'], 1, 9),
    _e('avg_check', 'Average Check', 'Average order amount', 'overview', 'fa-calculator', ['total', 'order_id'], 5, 9, True),
    _e('total_quantity', 'Total Quantity', 'Number of items sold', 'overview', 'fa-boxes-stacked', ['quantity'], 1, 7, True),
    _e('unique_products', 'Unique Products', 'Number of unique products', 'overview', 'fa-tags', ['goods_name'], 1, 6),
    _e('revenue_by_category', 'Revenue by Category', 'Revenue distribution across product categories', 'overview', 'fa-chart-pie', ['total', 'goods_category'], 5, 9, True),
    _e('top10_products_revenue', 'Top 10 Products by Revenue', 'Most profitable products', 'overview', 'fa-ranking-star', ['goods_name', 'total'], 10, 9, True),
    _e('top10_products_qty', 'Top 10 Products by Quantity', 'Best-selling products', 'overview', 'fa-arrow-up-9-1', ['goods_name', 'quantity'], 10, 8, True),
    _e('category_share', 'Category Share', 'Percentage ratio of categories', 'overview', 'fa-chart-pie', ['goods_category', 'total'], 5, 8, True),
    _e('price_distribution', 'Price Distribution', 'Histogram of product prices', 'overview', 'fa-chart-bar', ['price'], 10, 6, True),

    # ===== TRENDS =====
    _e('revenue_by_date', 'Revenue by Date', 'Revenue dynamics over time', 'trends', 'fa-chart-line', ['total', 'date'], 10, 10, True),
    _e('orders_by_date', 'Orders by Date', 'Number of orders by days', 'trends', 'fa-chart-line', ['order_id', 'date'], 10, 9),
    _e('revenue_by_month', 'Revenue by Month', 'Monthly revenue dynamics', 'trends', 'fa-calendar', ['total', 'date'], 30, 9, True),
    _e('weekday_analysis', 'Weekday Analysis', 'Sales broken down by days of the week', 'trends', 'fa-calendar-days', ['total', 'date'], 14, 7, True),
    _e('yoy_comparison', 'Year over Year', 'Comparison of periods year over year', 'trends', 'fa-code-compare', ['total', 'date'], 365, 9, True),

    # ===== RISKS =====
    _e('revenue_drop_alert', 'Revenue Drop', 'Detection of significant downturns', 'risks', 'fa-arrow-trend-down', ['total', 'date'], 30, 10, True),
    _e('price_anomalies', 'Price Anomalies', 'Products with suspiciously high/low prices', 'risks', 'fa-bug', ['goods_name', 'price'], 10, 8, True),
    _e('customer_concentration', 'Customer Concentration', 'Dependence on large clients', 'risks', 'fa-person-circle-exclamation', ['customer', 'total'], 10, 9, True),

    # ===== OPPORTUNITIES =====
    _e('abc_analysis', 'ABC Analysis', 'Classification of products by revenue contribution', 'opportunities', 'fa-layer-group', ['goods_name', 'total'], 10, 10, True),
    _e('rfm_analysis', 'RFM Analysis', 'Recency-Frequency-Monetary customer analysis', 'opportunities', 'fa-bullseye', ['customer', 'total', 'date'], 30, 10, True),
    _e('pareto_analysis', 'Pareto Analysis', '80/20 — which products provide 80% of revenue', 'opportunities', 'fa-chart-bar', ['goods_name', 'total'], 10, 9, True),
    _e('customer_segments', 'Customer Segments', 'Grouping of clients by purchase volume', 'opportunities', 'fa-people-group', ['customer', 'total'], 20, 9, True),
    _e('customer_ltv', 'Customer LTV', 'Estimation of customer Lifetime Value', 'opportunities', 'fa-sack-dollar', ['customer', 'total'], 30, 9, True),
    
    # ===== DETAILS =====
    _e('product_table', 'Product Table', 'Detailed table of all products with metrics', 'details', 'fa-table', ['goods_name', 'total'], 1, 7),
]

def get_catalog():
    return ANALYTICS_CATALOG

def get_by_id(analytics_id):
    for item in ANALYTICS_CATALOG:
        if item['id'] == analytics_id:
            return item
    return None

def get_by_category(category):
    return [a for a in ANALYTICS_CATALOG if a['category'] == category]
