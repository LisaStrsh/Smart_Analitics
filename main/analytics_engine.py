"""
Движок ранжирования визуализаций.
Анализирует данные пользователя и определяет какие визуализации возможны/полезны.
"""
import pandas as pd
from .models import Dataset, ColumnMapping, DashboardWidget
from .analytics_catalog import ANALYTICS_CATALOG, CATEGORIES, get_by_id


def get_dataset_profile(dataset):
    """Собирает профиль датасета: какие маппинги есть, сколько строк, типы данных."""
    mappings = dataset.column_mappings.exclude(standard_name='other')
    mapped_names = set(mappings.values_list('standard_name', flat=True))
    
    profile = {
        'mapped_names': mapped_names,
        'rows_count': dataset.rows_count,
        'has_numeric': bool(mapped_names & {'price', 'total', 'quantity'}),
        'has_date': 'date' in mapped_names,
        'has_money': bool(mapped_names & {'price', 'total'}),
    }
    return profile


IMPLEMENTED_ANALYTICS = {
    'total_revenue', 'total_orders', 'avg_check', 'total_quantity', 'unique_products',
    'revenue_by_category', 'top10_products_revenue', 'top10_products_qty', 'category_share',
    'price_distribution', 'revenue_by_date', 'orders_by_date', 'revenue_by_month', 'weekday_analysis',
    'price_anomalies', 'revenue_regression', 'abc_analysis', 'product_table', 'rfm_analysis',
    'customer_segments', 'revenue_drop_alert', 'pareto_analysis', 'yoy_comparison', 'customer_ltv',
    'customer_concentration'
}

def score_analytics(analytics_item, profile, existing_items):
    """
    Считает score для одной визуализации на основе принципов рекомендательных систем Visual Analytics.
    Возвращает dict с feasibility и итоговым score.
    """
    if analytics_item['id'] not in IMPLEMENTED_ANALYTICS:
        return {'feasible': False, 'score': 0, 'reason': 'В разработке (Скоро)', 'missing_mappings': []}
        
    required = set(analytics_item['required_mappings'])
    available = profile['mapped_names']
    
    # Жесткие фильтры (Hard Constraints)
    if required and not required.issubset(available):
        missing = required - available
        return {'feasible': False, 'score': 0, 'reason': f"Нет маппингов: {', '.join(missing)}", 'missing_mappings': list(missing)}
    
    if profile['rows_count'] < analytics_item['min_rows']:
        return {'feasible': False, 'score': 0, 'reason': f"Нужно минимум {analytics_item['min_rows']} строк", 'missing_mappings': []}
    
    # Мягкие эвристики (Soft Scoring)
    score = analytics_item['usefulness']
    
    # 1. Комплементарность (Penalty for Redundancy)
    # Штрафуем графики из категорий, которыми уже перенасыщен дашборд.
    same_category_count = sum(1 for item in existing_items if item['category'] == analytics_item['category'])
    score -= (same_category_count * 1.5)
    
    # 2. Новизна измерений (Dimension Novelty)
    # Поощряем использование еще не задействованных колонок данных.
    used_columns = set()
    for item in existing_items:
        used_columns.update(item['required_mappings'])
    
    novel_columns = required - used_columns
    score += (len(novel_columns) * 2.0)
    
    # 3. Фазовый сдвиг / Эволюция (Complexity Progression)
    # На старте нужны базовые метрики. При заполненном дашборде нужны глубокие инсайты.
    total_widgets = len(existing_items)
    if total_widgets < 3 and analytics_item['category'] == 'overview':
        score += 20.0  # Огромный фокус на базу (строго заставляет вывести KPI сначала)
    elif total_widgets >= 3 and analytics_item['category'] in ['opportunities', 'risks']:
        score += 5.0  # Фокус на поиск точек роста и проблем

    return {
        'feasible': True,
        'score': max(round(score, 2), 0.1),
        'reason': 'Доступно',
        'missing_mappings': [],
    }


def get_ranked_analytics(user, dataset_id=None):
    """
    Возвращает проранжированный список визуализаций для пользователя.
    Если dataset_id указан — анализирует конкретный датасет.
    Иначе — берёт первый готовый датасет.
    """
    if dataset_id:
        try:
            dataset = Dataset.objects.get(id=dataset_id, user=user, status='ready')
        except Dataset.DoesNotExist:
            return [], None
    else:
        dataset = Dataset.objects.filter(user=user, status='ready').first()
        if not dataset:
            return [], None
    
    profile = get_dataset_profile(dataset)
    
    existing_widgets = DashboardWidget.objects.filter(user=user, dataset=dataset)
    existing_map = {w.analytics_id: w.id for w in existing_widgets}
    
    # Собираем полные объекты из каталога для алгоритма
    existing_items = [item for item in ANALYTICS_CATALOG if item['id'] in existing_map]
    
    results = []
    for item in ANALYTICS_CATALOG:
        score_info = score_analytics(item, profile, existing_items)
        results.append({
            **item,
            **score_info,
            'is_added': item['id'] in existing_map,
            'widget_id': existing_map.get(item['id']),
        })
    
    # Сортируем: сначала доступные (по score desc), потом недоступные
    results.sort(key=lambda x: (x['feasible'], x['score']), reverse=True)
    
    return results, dataset


def get_top_recommendations(user, dataset_id=None, limit=6):
    """Возвращает топ-N рекомендаций (только feasible и не добавленные)."""
    results, dataset = get_ranked_analytics(user, dataset_id)
    recommendations = [r for r in results if r['feasible'] and not r['is_added']]
    return recommendations[:limit], dataset


def get_by_category_ranked(user, dataset_id=None):
    """Группирует визуализации по категориям с ранжированием внутри каждой."""
    results, dataset = get_ranked_analytics(user, dataset_id)
    
    categorized = {}
    for cat_id, cat_info in CATEGORIES.items():
        cat_items = [r for r in results if r['category'] == cat_id]
        categorized[cat_id] = {
            'info': cat_info,
            'items': cat_items,
            'feasible_count': sum(1 for r in cat_items if r['feasible']),
            'total_count': len(cat_items),
        }
    
    return categorized, dataset
