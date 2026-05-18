import json
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.utils import PlotlyJSONEncoder
from .models import Dataset, ColumnMapping

def get_mapped_df(dataset):
    """
    Загружает датасет и переименовывает колонки в соответствии с маппингом.
    Возвращает DataFrame и словарь обратного маппинга.
    """
    file_path = dataset.file.path
    if dataset.original_filename.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)
    
    # Получаем маппинги
    mappings = dataset.column_mappings.exclude(standard_name='other')
    rename_dict = {}
    reverse_rename = {}
    
    for m in mappings:
        rename_dict[m.user_column_name] = m.standard_name
        reverse_rename[m.standard_name] = m.user_column_name
        
    # Удаляем из датафрейма все оригинальные колонки, имена которых случайно совпадают с целевыми
    # (но при этом они не являются теми колонками, которые мы переименовываем сами в себя)
    target_names = set(rename_dict.values())
    cols_to_drop = [c for c in df.columns if c in target_names and rename_dict.get(c) != c]
    df = df.drop(columns=cols_to_drop)
        
    df = df.rename(columns=rename_dict)
    
    # Удаляем дублирующиеся колонки (на случай, если пользователь всё-таки замапил две колонки на одно имя)
    df = df.loc[:, ~df.columns.duplicated()]
    
    
    # Приводим типы
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date']).sort_values('date')
        
    for col in ['price', 'total', 'quantity', 'cost', 'discount']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    return df, reverse_rename

def generate_plotly_chart(analytics_id, dataset):
    """
    Генерирует Plotly-график для конкретного вида аналитики.
    Возвращает JSON-строку графика (или словарь) для Plotly.js.
    """
    try:
        df, reverse_rename = get_mapped_df(dataset)
        if df.empty:
            return get_error_chart("Данные в файле отсутствуют или повреждены.")
        
        # Получаем исходные имена колонок для подписей осей
        def get_label(std_name, default):
            return reverse_rename.get(std_name, default)

        # Шаблон оформления ( Sleek Dark / Premium Glass )
        layout_theme = dict(
            paper_bgcolor='rgba(255,255,255,0)',
            plot_bgcolor='rgba(255,255,255,0)',
            font=dict(family='Segoe UI, Tahoma, Geneva, sans-serif', color='#2b2d42', size=12),
            margin=dict(l=40, r=20, t=40, b=40),
            hovermode='closest',
            xaxis=dict(gridcolor='#eef2f7', zeroline=False),
            yaxis=dict(gridcolor='#eef2f7', zeroline=False)
        )

        # 1. total_revenue
        if analytics_id == 'total_revenue':
            total = df['total'].sum()
            fig = go.Figure(go.Indicator(
                mode = "number",
                value = total,
                number = {'valueformat': ',.2f', 'suffix': ' ₽', 'font': {'size': 48, 'color': '#15388c'}},
                title = {"text": "Общая выручка", "font": {"size": 16, "color": "#8d99ae"}}
            ))
            fig.update_layout(height=200, **layout_theme)

        # 2. total_orders
        elif analytics_id == 'total_orders':
            orders = df['order_id'].nunique() if 'order_id' in df.columns else len(df)
            fig = go.Figure(go.Indicator(
                mode = "number",
                value = orders,
                number = {'valueformat': ',', 'font': {'size': 48, 'color': '#15388c'}},
                title = {"text": "Всего заказов", "font": {"size": 16, "color": "#8d99ae"}}
            ))
            fig.update_layout(height=200, **layout_theme)

        # 3. avg_check
        elif analytics_id == 'avg_check':
            if 'order_id' in df.columns and 'total' in df.columns:
                avg = df.groupby('order_id')['total'].sum().mean()
            else:
                avg = df['total'].mean()
            fig = go.Figure(go.Indicator(
                mode = "number",
                value = avg,
                number = {'valueformat': ',.2f', 'suffix': ' ₽', 'font': {'size': 48, 'color': '#15388c'}},
                title = {"text": "Средний чек", "font": {"size": 16, "color": "#8d99ae"}}
            ))
            fig.update_layout(height=200, **layout_theme)

        # 4. total_quantity
        elif analytics_id == 'total_quantity':
            qty = df['quantity'].sum()
            fig = go.Figure(go.Indicator(
                mode = "number",
                value = qty,
                number = {'valueformat': ',', 'font': {'size': 48, 'color': '#59a14f'}},
                title = {"text": "Продано товаров (шт)", "font": {"size": 16, "color": "#8d99ae"}}
            ))
            fig.update_layout(height=200, **layout_theme)

        # 5. unique_products
        elif analytics_id == 'unique_products':
            uniq = df['goods_name'].nunique()
            fig = go.Figure(go.Indicator(
                mode = "number",
                value = uniq,
                number = {'valueformat': ',', 'font': {'size': 48, 'color': '#76b7b2'}},
                title = {"text": "Уникальные товары", "font": {"size": 16, "color": "#8d99ae"}}
            ))
            fig.update_layout(height=200, **layout_theme)

        # 9. revenue_by_category
        elif analytics_id == 'revenue_by_category':
            gp = df.groupby('goods_category')['total'].sum().reset_index().sort_values('total', ascending=False)
            fig = px.bar(
                gp, x='goods_category', y='total',
                labels={'goods_category': get_label('goods_category', 'Категория'), 'total': 'Выручка (₽)'},
                color_discrete_sequence=['#4e79a7']
            )
            fig.update_layout(**layout_theme)

        # 11. top10_products_revenue
        elif analytics_id == 'top10_products_revenue':
            gp = df.groupby('goods_name')['total'].sum().reset_index().sort_values('total', ascending=False).head(10)
            fig = px.bar(
                gp, y='goods_name', x='total', orientation='h',
                labels={'goods_name': get_label('goods_name', 'Товар'), 'total': 'Выручка (₽)'},
                color_discrete_sequence=['#15388c']
            )
            fig.update_layout(**layout_theme)
            fig.update_yaxes(categoryorder='total ascending')

        # 12. top10_products_qty
        elif analytics_id == 'top10_products_qty':
            gp = df.groupby('goods_name')['quantity'].sum().reset_index().sort_values('quantity', ascending=False).head(10)
            fig = px.bar(
                gp, y='goods_name', x='quantity', orientation='h',
                labels={'goods_name': get_label('goods_name', 'Товар'), 'quantity': 'Количество'},
                color_discrete_sequence=['#59a14f']
            )
            fig.update_layout(**layout_theme)
            fig.update_yaxes(categoryorder='total ascending')

        # 14. category_share
        elif analytics_id == 'category_share':
            gp = df.groupby('goods_category')['total'].sum().reset_index()
            fig = px.pie(
                gp, names='goods_category', values='total',
                labels={'goods_category': get_label('goods_category', 'Категория'), 'total': 'Выручка (₽)'},
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_layout(**layout_theme)

        # 17. price_distribution
        elif analytics_id == 'price_distribution':
            fig = px.histogram(
                df, x='price',
                labels={'price': get_label('price', 'Цена')},
                color_discrete_sequence=['#76b7b2']
            )
            fig.update_layout(**layout_theme)

        # 21. revenue_by_date
        elif analytics_id == 'revenue_by_date':
            gp = df.groupby('date')['total'].sum().reset_index()
            fig = px.line(
                gp, x='date', y='total',
                labels={'date': get_label('date', 'Дата'), 'total': 'Выручка (₽)'},
                color_discrete_sequence=['#15388c']
            )
            fig.update_traces(mode='lines+markers', marker=dict(size=4))
            fig.update_layout(**layout_theme)

        # 22. orders_by_date
        elif analytics_id == 'orders_by_date':
            col = 'order_id' if 'order_id' in df.columns else 'total'
            gp = df.groupby('date')[col].nunique() if 'order_id' in df.columns else df.groupby('date')[col].count()
            gp = gp.reset_index(name='orders_count')
            fig = px.line(
                gp, x='date', y='orders_count',
                labels={'date': get_label('date', 'Дата'), 'orders_count': 'Заказы'},
                color_discrete_sequence=['#59a14f']
            )
            fig.update_layout(**layout_theme)

        # 25. revenue_by_month
        elif analytics_id == 'revenue_by_month':
            df['month'] = df['date'].dt.to_period('M').astype(str)
            gp = df.groupby('month')['total'].sum().reset_index()
            fig = px.bar(
                gp, x='month', y='total',
                labels={'month': 'Месяц', 'total': 'Выручка (₽)'},
                color_discrete_sequence=['#f28e2b']
            )
            fig.update_layout(**layout_theme)

        # 28. weekday_analysis
        elif analytics_id == 'weekday_analysis':
            df['weekday'] = df['date'].dt.day_name()
            # Для сортировки дней
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            days_ru = {'Monday': 'Пн', 'Tuesday': 'Вт', 'Wednesday': 'Ср', 'Thursday': 'Чт', 'Friday': 'Пт', 'Saturday': 'Сб', 'Sunday': 'Вс'}
            
            gp = df.groupby('weekday')['total'].sum().reindex(days_order).reset_index()
            gp['weekday_ru'] = gp['weekday'].map(days_ru)
            fig = px.bar(
                gp, x='weekday_ru', y='total',
                labels={'weekday_ru': 'День недели', 'total': 'Выручка (₽)'},
                color_discrete_sequence=['#e15759']
            )
            fig.update_layout(**layout_theme)

        # 43. price_anomalies
        elif analytics_id == 'price_anomalies':
            # Считаем Z-score
            mean = df['price'].mean()
            std = df['price'].std()
            if std > 0:
                df['z_score'] = (df['price'] - mean) / std
                anomalies = df[df['z_score'].abs() > 2]
            else:
                anomalies = pd.DataFrame()
                
            if anomalies.empty:
                fig = go.Figure()
                fig.add_annotation(text="Аномальных цен не обнаружено", showarrow=False, font=dict(size=14))
            else:
                fig = px.scatter(
                    anomalies, x='goods_name', y='price', size='quantity', color='price',
                    labels={'goods_name': get_label('goods_name', 'Товар'), 'price': get_label('price', 'Цена')},
                    title="Выявленные аномалии цен (>2 стандартных отклонений)"
                )
            fig.update_layout(**layout_theme)

        # 61. revenue_regression (Регрессия / Прогноз)


        # 71. abc_analysis (ABC-анализ товаров)
        elif analytics_id == 'abc_analysis':
            gp = df.groupby('goods_name')['total'].sum().reset_index().sort_values('total', ascending=False)
            gp['share'] = gp['total'] / gp['total'].sum()
            gp['cum_share'] = gp['share'].cumsum()
            
            def get_abc(cum_share):
                if cum_share <= 0.8: return 'A (80% выручки)'
                elif cum_share <= 0.95: return 'B (15% выручки)'
                return 'C (5% выручки)'
                
            gp['Group'] = gp['cum_share'].apply(get_abc)
            
            fig = px.bar(
                gp, x='goods_name', y='total', color='Group',
                labels={'goods_name': get_label('goods_name', 'Товар'), 'total': 'Выручка (₽)', 'Group': 'Группа ABC'},
                color_discrete_map={'A (80% выручки)': '#e15759', 'B (15% выручки)': '#f28e2b', 'C (5% выручки)': '#76b7b2'}
            )
            fig.update_layout(**layout_theme)
            fig.update_xaxes(showticklabels=False)

        # 81. product_table (Детальная таблица товаров)
        elif analytics_id == 'product_table':
            agg_dict = {'total': 'sum'}
            if 'quantity' in df.columns: agg_dict['quantity'] = 'sum'
            if 'price' in df.columns: agg_dict['price'] = 'mean'
            
            gp = df.groupby('goods_name').agg(agg_dict).reset_index()
            gp = gp.sort_values('total', ascending=False).head(15)
            
            header_vals = [get_label('goods_name', 'Товар'), 'Выручка (₽)']
            cell_vals = [gp.goods_name, gp.total.round(2)]
            
            if 'quantity' in df.columns:
                header_vals.append('Количество')
                cell_vals.append(gp.quantity)
            if 'price' in df.columns:
                header_vals.append('Средняя цена')
                cell_vals.append(gp.price.round(2))
            
            fig = go.Figure(data=[go.Table(
                header=dict(values=header_vals, fill_color='#15388c', align='left', font=dict(color='white', size=12)),
                cells=dict(values=cell_vals, fill_color='#f8fafe', align='left'))
            ])
            fig.update_layout(height=350, **layout_theme)

        # 82. RFM Analysis
        elif analytics_id == 'rfm_analysis':
            if 'customer' in df.columns and 'total' in df.columns and 'date' in df.columns:
                last_date = df['date'].max()
                rfm = df.groupby('customer').agg({
                    'date': lambda x: (last_date - x.max()).days, # Recency
                    'total': ['count', 'sum'] # Frequency, Monetary
                }).reset_index()
                rfm.columns = ['customer', 'Recency', 'Frequency', 'Monetary']
                
                fig = px.scatter(
                    rfm, x='Recency', y='Frequency', size='Monetary', color='Monetary',
                    hover_name='customer',
                    labels={'Recency': 'Дней с последней покупки', 'Frequency': 'Частота покупок', 'Monetary': 'Выручка (₽)'},
                    title="RFM Анализ клиентов"
                )
            else:
                fig = go.Figure()
                fig.add_annotation(text="Недостаточно данных для RFM-анализа", showarrow=False)
            fig.update_layout(**layout_theme)

        # 83. Customer Segments
        elif analytics_id == 'customer_segments':
            if 'customer' in df.columns and 'total' in df.columns:
                gp = df.groupby('customer')['total'].sum().reset_index()
                try:
                    gp['segment'] = pd.qcut(gp['total'], q=3, labels=['Bronze (Нижние 33%)', 'Silver (Средние 33%)', 'Gold (Топ 33%)'])
                except:
                    gp['segment'] = 'Обычные'
                seg = gp.groupby('segment')['total'].sum().reset_index()
                fig = px.pie(
                    seg, names='segment', values='total', hole=0.4, color='segment',
                    color_discrete_map={
                        'Bronze (Нижние 33%)': '#CD7F32', 
                        'Silver (Средние 33%)': '#C0C0C0', 
                        'Gold (Топ 33%)': '#FFD700',
                        'Обычные': '#8d99ae'
                    }
                )
                fig.update_layout(title="Сегментация клиентов по выручке", **layout_theme)
            else:
                fig = go.Figure()
                fig.add_annotation(text="Недостаточно данных для Сегментации", showarrow=False)
                fig.update_layout(**layout_theme)

        # 84. Revenue Drop Alert
        elif analytics_id == 'revenue_drop_alert':
            if 'date' in df.columns and 'total' in df.columns:
                gp = df.groupby('date')['total'].sum().reset_index()
                gp['prev_total'] = gp['total'].shift(1)
                gp['drop'] = gp['total'] - gp['prev_total']
                gp['color'] = np.where(gp['drop'] < 0, '#e15759', '#59a14f')
                fig = px.bar(
                    gp, x='date', y='drop', 
                    title="Изменения выручки (рост и падение)",
                    labels={'date': 'Дата', 'drop': 'Изменение (₽)'}
                )
                fig.update_traces(marker_color=gp['color'])
            else:
                fig = go.Figure()
                fig.add_annotation(text="Недостаточно данных для отчета о падениях", showarrow=False)
            fig.update_layout(**layout_theme)

        # 102. pareto_analysis
        elif analytics_id == 'pareto_analysis':
            if 'goods_name' in df.columns and 'total' in df.columns:
                gp = df.groupby('goods_name')['total'].sum().reset_index().sort_values('total', ascending=False)
                gp['cum_pct'] = gp['total'].cumsum() / gp['total'].sum() * 100
                gp = gp.head(30) # Берем топ-30 для читаемости
                
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(go.Bar(x=gp['goods_name'], y=gp['total'], name='Выручка (₽)', marker_color='#4e79a7'), secondary_y=False)
                fig.add_trace(go.Scatter(x=gp['goods_name'], y=gp['cum_pct'], name='Кумулятивный %', mode='lines+markers', marker_color='#e15759'), secondary_y=True)
                
                fig.update_layout(
                    title="Парето-анализ товаров (Топ-30)",
                    **layout_theme
                )
                fig.update_yaxes(title_text="Кумулятивный процент", range=[0, 105], secondary_y=True)
                fig.update_xaxes(showticklabels=False, type='category')
            else:
                fig = go.Figure()
                fig.add_annotation(text="Недостаточно данных для графика Парето", showarrow=False)
                fig.update_layout(**layout_theme)

        # 60. yoy_comparison
        elif analytics_id == 'yoy_comparison':
            if 'date' in df.columns and 'total' in df.columns:
                df['year'] = df['date'].dt.year.astype(str)
                df['month_name'] = df['date'].dt.strftime('%b')
                df['month'] = df['date'].dt.month
                gp = df.groupby(['year', 'month', 'month_name'])['total'].sum().reset_index()
                
                fig = px.bar(
                    gp, x='month_name', y='total', color='year', barmode='group',
                    title="Сравнение выручки год к году (YoY)",
                    labels={'month_name': 'Месяц', 'total': 'Выручка (₽)', 'year': 'Год'},
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig.update_layout(**layout_theme)
                fig.update_xaxes(categoryorder='array', categoryarray=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
            else:
                fig = go.Figure()
                fig.add_annotation(text="Недостаточно данных для сравнения год к году", showarrow=False)
                fig.update_layout(**layout_theme)

        # 107. customer_ltv
        elif analytics_id == 'customer_ltv':
            if 'customer' in df.columns and 'total' in df.columns:
                gp = df.groupby('customer')['total'].sum().reset_index()
                fig = px.histogram(
                    gp, x='total', nbins=30,
                    title="Распределение LTV (Пожизненной ценности) клиентов",
                    labels={'total': 'Общая выручка от клиента (₽)'},
                    color_discrete_sequence=['#59a14f']
                )
                fig.update_layout(**layout_theme)
            else:
                fig = go.Figure()
                fig.add_annotation(text="Недостаточно данных для расчета LTV", showarrow=False)
                fig.update_layout(**layout_theme)

        # 71. customer_concentration
        elif analytics_id == 'customer_concentration':
            if 'customer' in df.columns and 'total' in df.columns:
                gp = df.groupby('customer')['total'].sum().reset_index().sort_values('total', ascending=False)
                gp['cum_pct'] = gp['total'].cumsum() / gp['total'].sum() * 100
                gp['customer_pct'] = np.arange(1, len(gp) + 1) / len(gp) * 100
                
                fig = px.line(
                    gp, x='customer_pct', y='cum_pct', 
                    title="Концентрация клиентов (Кривая Лоренца)",
                    labels={'customer_pct': '% от всех клиентов', 'cum_pct': 'Кумулятивный % выручки'},
                    color_discrete_sequence=['#15388c']
                )
                fig.add_trace(go.Scatter(x=[0, 100], y=[0, 100], mode='lines', name='Идеальное распределение', line=dict(color='gray', dash='dash')))
                fig.update_layout(**layout_theme)
            else:
                fig = go.Figure()
                fig.add_annotation(text="Недостаточно данных для оценки концентрации", showarrow=False)
                fig.update_layout(**layout_theme)

        else:
            return get_error_chart(f"График '{analytics_id}' не реализован.")

        return json.dumps(fig, cls=PlotlyJSONEncoder)

    except Exception as e:
        return get_error_chart(f"Ошибка построения графика: {str(e)}")

def get_error_chart(message):
    fig = go.Figure()
    fig.add_annotation(
        text=f"⚠️ {message}",
        showarrow=False,
        font=dict(size=14, color="#dc3545")
    )
    fig.update_layout(
        paper_bgcolor='rgba(255,255,255,0)',
        plot_bgcolor='rgba(255,255,255,0)',
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )
    return json.dumps(fig, cls=PlotlyJSONEncoder)
