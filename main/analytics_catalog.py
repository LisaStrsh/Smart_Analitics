"""
Каталог аналитических визуализаций.
Каждая запись: id, name, short_desc, category, icon, required_mappings, min_rows, usefulness.
Категории: overview, trends, risks, opportunities, details
"""

CATEGORIES = {
    'overview': {'name': 'Обзор', 'icon': 'fa-chart-pie', 'color': '#4e79a7'},
    'trends': {'name': 'Тренды', 'icon': 'fa-chart-line', 'color': '#59a14f'},
    'risks': {'name': 'Риски', 'icon': 'fa-triangle-exclamation', 'color': '#e15759'},
    'opportunities': {'name': 'Возможности', 'icon': 'fa-lightbulb', 'color': '#f28e2b'},
    'details': {'name': 'Детализация', 'icon': 'fa-magnifying-glass', 'color': '#76b7b2'},
}

def _e(id, name, short, cat, icon, mappings, min_rows=5, usefulness=5, needs_numeric=False):
    return {
        'id': id, 'name': name, 'short_desc': short, 'category': cat,
        'icon': icon, 'required_mappings': mappings, 'min_rows': min_rows,
        'usefulness': usefulness, 'needs_numeric': needs_numeric,
    }

ANALYTICS_CATALOG = [
    # ===== OVERVIEW =====
    _e('total_revenue', 'Общая выручка', 'Суммарная выручка за весь период', 'overview', 'fa-coins', ['total'], 1, 10, True),
    _e('total_orders', 'Количество заказов', 'Общее число заказов', 'overview', 'fa-receipt', ['order_id'], 1, 9),
    _e('avg_check', 'Средний чек', 'Средняя сумма заказа', 'overview', 'fa-calculator', ['total', 'order_id'], 5, 9, True),
    _e('total_quantity', 'Общее количество товаров', 'Сколько единиц товара продано', 'overview', 'fa-boxes-stacked', ['quantity'], 1, 7, True),
    _e('unique_products', 'Уникальные товары', 'Количество уникальных наименований', 'overview', 'fa-tags', ['goods_name'], 1, 6),
    _e('revenue_by_category', 'Выручка по категориям', 'Распределение выручки по категориям товаров', 'overview', 'fa-chart-pie', ['total', 'goods_category'], 5, 9, True),
    _e('top10_products_revenue', 'Топ-10 товаров по выручке', 'Самые прибыльные товары', 'overview', 'fa-ranking-star', ['goods_name', 'total'], 10, 9, True),
    _e('top10_products_qty', 'Топ-10 товаров по количеству', 'Самые продаваемые товары', 'overview', 'fa-arrow-up-9-1', ['goods_name', 'quantity'], 10, 8, True),
    _e('category_share', 'Доли категорий', 'Процентное соотношение категорий', 'overview', 'fa-chart-pie', ['goods_category', 'total'], 5, 8, True),
    _e('price_distribution', 'Распределение цен', 'Гистограмма цен товаров', 'overview', 'fa-chart-bar', ['price'], 10, 6, True),

    # ===== TRENDS =====
    _e('revenue_by_date', 'Выручка по дням', 'Динамика выручки во времени', 'trends', 'fa-chart-line', ['total', 'date'], 10, 10, True),
    _e('orders_by_date', 'Заказы по дням', 'Количество заказов по дням', 'trends', 'fa-chart-line', ['order_id', 'date'], 10, 9),
    _e('revenue_by_month', 'Выручка по месяцам', 'Помесячная динамика выручки', 'trends', 'fa-calendar', ['total', 'date'], 30, 9, True),
    _e('weekday_analysis', 'Анализ по дням недели', 'Продажи в разрезе дней недели', 'trends', 'fa-calendar-days', ['total', 'date'], 14, 7, True),
    _e('yoy_comparison', 'Год к году', 'Сравнение периодов год к году', 'trends', 'fa-code-compare', ['total', 'date'], 365, 9, True),

    # ===== RISKS =====
    _e('revenue_drop_alert', 'Падение выручки', 'Обнаружение значительных спадов', 'risks', 'fa-arrow-trend-down', ['total', 'date'], 30, 10, True),
    _e('price_anomalies', 'Аномалии цен', 'Товары с подозрительно высокими/низкими ценами', 'risks', 'fa-bug', ['goods_name', 'price'], 10, 8, True),
    _e('customer_concentration', 'Концентрация клиентов', 'Зависимость от крупных клиентов', 'risks', 'fa-person-circle-exclamation', ['customer', 'total'], 10, 9, True),

    # ===== OPPORTUNITIES =====
    _e('abc_analysis', 'ABC-анализ', 'Классификация товаров по вкладу в выручку', 'opportunities', 'fa-layer-group', ['goods_name', 'total'], 10, 10, True),
    _e('rfm_analysis', 'RFM-анализ', 'Recency-Frequency-Monetary анализ клиентов', 'opportunities', 'fa-bullseye', ['customer', 'total', 'date'], 30, 10, True),
    _e('pareto_analysis', 'Парето-анализ', '80/20 — какие товары дают 80% выручки', 'opportunities', 'fa-chart-bar', ['goods_name', 'total'], 10, 9, True),
    _e('customer_segments', 'Сегменты клиентов', 'Группировка клиентов по объёму покупок', 'opportunities', 'fa-people-group', ['customer', 'total'], 20, 9, True),
    _e('customer_ltv', 'Пожизненная ценность клиента', 'Оценка LTV клиентов', 'opportunities', 'fa-sack-dollar', ['customer', 'total'], 30, 9, True),
    
    # ===== DETAILS =====
    _e('product_table', 'Таблица товаров', 'Детальная таблица всех товаров с метриками', 'details', 'fa-table', ['goods_name', 'total'], 1, 7),
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
