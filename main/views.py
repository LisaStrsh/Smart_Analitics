import json
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.http import JsonResponse
from .models import UserProfile, Dataset, ColumnMapping, DashboardWidget
from .analytics_catalog import get_by_id
from .analytics_engine import get_ranked_analytics, get_top_recommendations, get_by_category_ranked
from .chart_generator import generate_plotly_chart


@login_required
def main_f(request):
    """
    Главная страница (автоматические дашборды).
    Выводит сетку выбранных визуализаций и проранжированные рекомендации.
    """
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    datasets = Dataset.objects.filter(user=request.user, status='ready')
    active_dataset = None
    
    # Разрешаем выбрать активный датасет из выпадающего списка
    dataset_id = request.GET.get('dataset_id')
    if dataset_id:
        active_dataset = datasets.filter(id=dataset_id).first()
        
    if not active_dataset:
        active_dataset = datasets.first()
        
    widgets = []
    recommendations = []
    
    if active_dataset:
        widgets = DashboardWidget.objects.filter(user=request.user, dataset=active_dataset).order_by('position')
        
        # Получаем рекомендации (топ-4 доступных и не добавленных)
        recommendations, _ = get_top_recommendations(request.user, active_dataset.id, limit=4)
        
        # Обогащаем виджеты данными графиков Plotly и метаданными из каталога
        for w in widgets:
            w.chart_json = generate_plotly_chart(w.analytics_id, active_dataset)
            cat_item = get_by_id(w.analytics_id)
            if cat_item:
                w.name = cat_item['name']
                w.short_desc = cat_item['short_desc']
                w.icon = cat_item['icon']
            else:
                w.name = w.analytics_id
                w.short_desc = ""
                w.icon = "fa-chart-simple"
                
    # Все датасеты пользователя для селектора (даже в процессе обработки)
    all_datasets = Dataset.objects.filter(user=request.user)
    
    return render(request, 'main/main.html', {
        'profile': profile,
        'datasets': all_datasets,
        'ready_datasets': datasets,
        'active_dataset': active_dataset,
        'widgets': widgets,
        'recommendations': recommendations,
    })


@login_required
def catalog_f(request, dataset_id):
    """
    Каталог всех видов аналитики (100 штук), проранжированных
    под конкретный датасет и разбитых по 5 категориям.
    """
    dataset = get_object_or_404(Dataset, id=dataset_id, user=request.user)
    categorized_analytics, _ = get_by_category_ranked(request.user, dataset.id)
    
    return render(request, 'main/catalog.html', {
        'dataset': dataset,
        'categorized_analytics': categorized_analytics,
    })


@login_required
def add_widget_f(request):
    """Добавление визуализации на дашборд."""
    if request.method == "POST":
        dataset_id = request.POST.get('dataset_id')
        analytics_id = request.POST.get('analytics_id')
        
        dataset = get_object_or_404(Dataset, id=dataset_id, user=request.user)
        
        # Проверяем на дубликаты
        exists = DashboardWidget.objects.filter(
            user=request.user, dataset=dataset, analytics_id=analytics_id
        ).exists()
        
        if not exists:
            count = DashboardWidget.objects.filter(user=request.user, dataset=dataset).count()
            DashboardWidget.objects.create(
                user=request.user,
                dataset=dataset,
                analytics_id=analytics_id,
                position=count
            )
            
        next_url = request.POST.get('next', f'/main/?dataset_id={dataset_id}')
        return redirect(next_url)
        
    return redirect('/main/')


@login_required
def remove_widget_f(request, widget_id):
    """Удаление визуализации с дашборда."""
    widget = get_object_or_404(DashboardWidget, id=widget_id, user=request.user)
    dataset_id = widget.dataset.id
    widget.delete()
    
    # Пересчитываем позиции
    widgets = DashboardWidget.objects.filter(user=request.user, dataset_id=dataset_id).order_by('position')
    for i, w in enumerate(widgets):
        w.position = i
        w.save()
        
    next_url = request.GET.get('next', f'/main/?dataset_id={dataset_id}')
    return redirect(next_url)


@login_required
def clear_dashboard_f(request, dataset_id):
    """Удаление всех визуализаций с дашборда."""
    dataset = get_object_or_404(Dataset, id=dataset_id, user=request.user)
    DashboardWidget.objects.filter(user=request.user, dataset=dataset).delete()
    return redirect(f'/main/?dataset_id={dataset.id}')


@login_required
def reorder_widgets_f(request):
    """Сортировка виджетов через Drag-and-Drop (AJAX)."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            widget_ids = data.get('widget_ids', [])
            for index, w_id in enumerate(widget_ids):
                DashboardWidget.objects.filter(
                    id=w_id, user=request.user
                ).update(position=index)
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def data_f(request):
    """
    Страница данных — список загруженных файлов.
    Отсюда можно загрузить новый файл или посмотреть существующие.
    """
    datasets = Dataset.objects.filter(user=request.user)
    return render(request, 'main/data.html', {'datasets': datasets})


@login_required
def upload_dataset_f(request):
    """
    Загрузка нового файла (Excel/CSV).
    
    Что происходит:
    1. Пользователь выбирает файл и нажимает "Загрузить"
    2. Django принимает файл через request.FILES
    3. Мы сохраняем файл на диск (в папку media/datasets/)
    4. Читаем файл через pandas чтобы узнать количество строк/колонок
    5. Создаём ColumnMapping для каждой колонки — пока без маппинга (standard_name='other')
    6. Пользователь потом сам назначит каждой колонке стандартное имя
    """
    if request.method == "POST":
        file = request.FILES.get('file')
        name = request.POST.get('name', '').strip()

        if not file:
            return redirect('/main/data/')

        if not name:
            name = file.name  # если имя не указали — берём имя файла

        # Создаём запись в БД
        dataset = Dataset.objects.create(
            user=request.user,
            name=name,
            file=file,
            original_filename=file.name,
            status='processing'
        )

        try:
            # Читаем файл через pandas
            file_path = dataset.file.path
            if file.name.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            # Сохраняем метаданные
            dataset.rows_count = len(df)
            dataset.columns_count = len(df.columns)
            dataset.status = 'ready'
            dataset.save()

            # Создаём маппинг для каждой колонки
            for col_name in df.columns:
                ColumnMapping.objects.create(
                    dataset=dataset,
                    user_column_name=str(col_name),
                    standard_name='other'  # по умолчанию — "прочее", потом пользователь сам укажет
                )

        except Exception as e:
            dataset.status = 'error'
            dataset.save()

        return redirect('/main/data/')

    return redirect('/main/data/')


@login_required
def dataset_detail_f(request, dataset_id):
    """
    Просмотр конкретного датасета: таблица с данными + маппинг колонок.
    
    get_object_or_404 — если датасет не найден или принадлежит другому 
    пользователю, Django покажет страницу "404 Not Found".
    """
    dataset = get_object_or_404(Dataset, id=dataset_id, user=request.user)
    mappings = dataset.column_mappings.all()

    # Читаем первые 50 строк для предпросмотра
    preview_data = []
    columns = []
    try:
        file_path = dataset.file.path
        if dataset.original_filename.endswith('.csv'):
            df = pd.read_csv(file_path, nrows=50)
        else:
            df = pd.read_excel(file_path, nrows=50)
        columns = list(df.columns)
        preview_data = df.fillna('').values.tolist()
    except Exception:
        pass

    return render(request, 'main/dataset_detail.html', {
        'dataset': dataset,
        'mappings': mappings,
        'columns': columns,
        'preview_data': preview_data,
        'standard_columns': ColumnMapping.STANDARD_COLUMNS,
    })


@login_required
def update_mapping_f(request, dataset_id):
    """
    Обновление маппинга колонок (AJAX-запрос).
    Пользователь выбирает для каждой колонки стандартное имя из выпадающего списка.
    """
    if request.method == "POST":
        dataset = get_object_or_404(Dataset, id=dataset_id, user=request.user)
        data = json.loads(request.body)

        for mapping_data in data.get('mappings', []):
            mapping_id = mapping_data.get('id')
            standard_name = mapping_data.get('standard_name')
            if mapping_id and standard_name:
                ColumnMapping.objects.filter(
                    id=mapping_id,
                    dataset=dataset
                ).update(standard_name=standard_name)

        return JsonResponse({'status': 'ok'})

    return JsonResponse({'status': 'error'}, status=400)


@login_required
def delete_dataset_f(request, dataset_id):
    """Удаление датасета."""
    if request.method == "POST":
        dataset = get_object_or_404(Dataset, id=dataset_id, user=request.user)
        dataset.file.delete()  # удаляем файл с диска
        dataset.delete()       # удаляем запись из БД
    return redirect('/main/data/')


@login_required
def settings_f(request):
    """
    Страница настроек профиля.
    Пользователь может изменить название компании и загрузить аватарку.
    """
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    success = False

    if request.method == "POST":
        company = request.POST.get('company_name', '').strip()
        avatar = request.FILES.get('avatar')

        profile.company_name = company
        if avatar:
            profile.avatar = avatar
        profile.save()
        success = True

    return render(request, 'main/settings.html', {
        'profile': profile,
        'success': success,
    })


def about_f(request):
    """Страница 'О проекте' — доступна всем."""
    return render(request, 'main/about.html')


def logout_f(request):
    """
    Выход из аккаунта.
    auth_logout() — функция Django которая:
    1. Очищает данные сессии (удаляет "пропуск" пользователя)
    2. Перенаправляет на приветственную страницу
    """
    auth_logout(request)
    return redirect('/')
