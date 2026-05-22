import json
import string
import random
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import UserProfile, Dataset, ColumnMapping, DashboardWidget, Employee
from .analytics_catalog import get_by_id
from .analytics_engine import get_ranked_analytics, get_top_recommendations, get_by_category_ranked
from .chart_generator import generate_plotly_chart


def _generate_credentials():
    """Generate random username and password for an employee."""
    prefix = 'emp_'
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    username = prefix + suffix
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return username, password


def _is_employee(user):
    """Check if the user is an employee."""
    return hasattr(user, 'employee_profile')


@login_required
def main_f(request):
    """
    Main page (automatic dashboards).
    If the user is an employee, redirect to the data entry form.
    """
    if _is_employee(request.user):
        return redirect('employee_form')

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    datasets = Dataset.objects.filter(user=request.user, status='ready')
    active_dataset = None
    
    dataset_id = request.GET.get('dataset_id')
    if dataset_id:
        active_dataset = datasets.filter(id=dataset_id).first()
        
    if not active_dataset:
        active_dataset = datasets.first()
        
    widgets = []
    recommendations = []
    
    if active_dataset:
        widgets = DashboardWidget.objects.filter(user=request.user, dataset=active_dataset).order_by('position')
        recommendations, _ = get_top_recommendations(request.user, active_dataset.id, limit=4)
        
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
    """Catalog of all analytics types."""
    dataset = get_object_or_404(Dataset, id=dataset_id, user=request.user)
    categorized_analytics, _ = get_by_category_ranked(request.user, dataset.id)
    
    return render(request, 'main/catalog.html', {
        'dataset': dataset,
        'categorized_analytics': categorized_analytics,
    })


@login_required
def add_widget_f(request):
    """Add visualization to the dashboard."""
    if request.method == "POST":
        dataset_id = request.POST.get('dataset_id')
        analytics_id = request.POST.get('analytics_id')
        
        dataset = get_object_or_404(Dataset, id=dataset_id, user=request.user)
        
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
    """Remove visualization from the dashboard."""
    widget = get_object_or_404(DashboardWidget, id=widget_id, user=request.user)
    dataset_id = widget.dataset.id
    widget.delete()
    
    widgets = DashboardWidget.objects.filter(user=request.user, dataset_id=dataset_id).order_by('position')
    for i, w in enumerate(widgets):
        w.position = i
        w.save()
        
    next_url = request.GET.get('next', f'/main/?dataset_id={dataset_id}')
    return redirect(next_url)


@login_required
def clear_dashboard_f(request, dataset_id):
    """Remove all visualizations from the dashboard."""
    dataset = get_object_or_404(Dataset, id=dataset_id, user=request.user)
    DashboardWidget.objects.filter(user=request.user, dataset=dataset).delete()
    return redirect(f'/main/?dataset_id={dataset.id}')


@login_required
def reorder_widgets_f(request):
    """Sort widgets via Drag-and-Drop (AJAX)."""
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
    """Data page — list of uploaded files."""
    datasets = Dataset.objects.filter(user=request.user)
    return render(request, 'main/data.html', {'datasets': datasets})


@login_required
def upload_dataset_f(request):
    """Upload a new file (Excel/CSV)."""
    if request.method == "POST":
        file = request.FILES.get('file')
        name = request.POST.get('name', '').strip()

        if not file:
            return redirect('/main/data/')

        if not name:
            name = file.name

        dataset = Dataset.objects.create(
            user=request.user,
            name=name,
            file=file,
            original_filename=file.name,
            status='processing'
        )

        try:
            file_path = dataset.file.path
            if file.name.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            dataset.rows_count = len(df)
            dataset.columns_count = len(df.columns)
            dataset.status = 'ready'
            dataset.save()

            for col_name in df.columns:
                ColumnMapping.objects.create(
                    dataset=dataset,
                    user_column_name=str(col_name),
                    standard_name='other'
                )

        except Exception as e:
            dataset.status = 'error'
            dataset.save()

        return redirect('/main/data/')

    return redirect('/main/data/')


@login_required
def dataset_detail_f(request, dataset_id):
    """View a specific dataset."""
    dataset = get_object_or_404(Dataset, id=dataset_id, user=request.user)
    mappings = dataset.column_mappings.all()

    preview_data = []
    columns = []
    try:
        file_path = dataset.file.path
        if dataset.original_filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
            
        # Sort by date if mapped date column exists
        date_mapping = mappings.filter(standard_name='date').first()
        if date_mapping and date_mapping.user_column_name in df.columns:
            date_col = date_mapping.user_column_name
            temp_date = pd.to_datetime(df[date_col], errors='coerce')
            df['__temp_parsed_date__'] = temp_date
            df = df.sort_values(by='__temp_parsed_date__', ascending=False, na_position='last')
            df = df.drop(columns=['__temp_parsed_date__'])
            
        columns = list(df.columns)
        
        # Prepare preview data with original indices
        for idx, row in df.head(50).iterrows():
            preview_data.append({
                'index': idx,
                'cells': row.fillna('').tolist()
            })
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
    """Update column mapping (AJAX request)."""
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
    """Delete dataset."""
    if request.method == "POST":
        dataset = get_object_or_404(Dataset, id=dataset_id, user=request.user)
        dataset.file.delete()
        dataset.delete()
    return redirect('/main/data/')


@login_required
def settings_f(request):
    """Profile settings page with employee management."""
    if _is_employee(request.user):
        return redirect('employee_form')

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

    employees = Employee.objects.filter(owner=request.user).select_related('user', 'dataset')
    datasets = Dataset.objects.filter(user=request.user, status='ready')

    return render(request, 'main/settings.html', {
        'profile': profile,
        'success': success,
        'employees': employees,
        'datasets': datasets,
    })


@login_required
def create_employee_f(request):
    """Create a new employee with autogenerated credentials."""
    if request.method == "POST":
        dataset_id = request.POST.get('dataset_id')
        display_name = request.POST.get('display_name', '').strip()

        dataset = get_object_or_404(Dataset, id=dataset_id, user=request.user, status='ready')

        username, password = _generate_credentials()

        emp_user = User.objects.create_user(
            username=username,
            password=password
        )

        Employee.objects.create(
            owner=request.user,
            user=emp_user,
            dataset=dataset,
            display_name=display_name or username,
            generated_password=password
        )

    return redirect('settings')


@login_required
def delete_employee_f(request, employee_id):
    """Delete an employee."""
    if request.method == "POST":
        employee = get_object_or_404(Employee, id=employee_id, owner=request.user)
        emp_user = employee.user
        employee.delete()
        emp_user.delete()

    return redirect('settings')


@login_required
def employee_form_f(request):
    """
    Data entry form for the employee.
    The employee sees a form with fields = dataset column names.
    Upon submission, data is added to the dataset file.
    """
    if not _is_employee(request.user):
        return redirect('home')

    employee = request.user.employee_profile
    dataset = employee.dataset

    columns = []
    try:
        file_path = dataset.file.path
        if dataset.original_filename.endswith('.csv'):
            df = pd.read_csv(file_path, nrows=0)
        else:
            df = pd.read_excel(file_path, nrows=0)
        columns = list(df.columns)
    except Exception:
        pass

    success = False
    if request.method == "POST":
        try:
            file_path = dataset.file.path
            if dataset.original_filename.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            new_row = {}
            for col in df.columns:
                value = request.POST.get(f'col_{col}', '')
                try:
                    value = float(value)
                    if value == int(value):
                        value = int(value)
                except (ValueError, TypeError):
                    pass
                new_row[col] = value

            new_df = pd.DataFrame([new_row])
            df = pd.concat([df, new_df], ignore_index=True)

            if dataset.original_filename.endswith('.csv'):
                df.to_csv(file_path, index=False)
            else:
                df.to_excel(file_path, index=False)

            dataset.rows_count = len(df)
            dataset.save()

            success = True
        except Exception as e:
            pass

    return render(request, 'main/employee_form.html', {
        'employee': employee,
        'dataset': dataset,
        'columns': columns,
        'success': success,
    })


def about_f(request):
    """'About' page - available to everyone."""
    return render(request, 'main/about.html')


def logout_f(request):
    """Log out of the account."""
    auth_logout(request)
    return redirect('/')


@login_required
def delete_row_f(request, dataset_id, row_idx):
    """Delete a specific row from the dataset file."""
    if request.method == "POST":
        dataset = get_object_or_404(Dataset, id=dataset_id, user=request.user)
        try:
            file_path = dataset.file.path
            if dataset.original_filename.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            if row_idx in df.index:
                df = df.drop(index=row_idx)
                
                if dataset.original_filename.endswith('.csv'):
                    df.to_csv(file_path, index=False)
                else:
                    df.to_excel(file_path, index=False)
                
                dataset.rows_count = len(df)
                dataset.save()
        except Exception:
            pass
            
    return redirect('dataset_detail', dataset_id=dataset_id)
