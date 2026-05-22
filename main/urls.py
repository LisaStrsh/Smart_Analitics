from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_f, name='home'),
    path('data/', views.data_f, name='data'),
    path('data/upload/', views.upload_dataset_f, name='upload_dataset'),
    path('data/<int:dataset_id>/', views.dataset_detail_f, name='dataset_detail'),
    path('data/<int:dataset_id>/mapping/', views.update_mapping_f, name='update_mapping'),
    path('data/<int:dataset_id>/delete/', views.delete_dataset_f, name='delete_dataset'),
    path('data/<int:dataset_id>/delete_row/<int:row_idx>/', views.delete_row_f, name='delete_row'),
    path('settings/', views.settings_f, name='settings'),
    path('about/', views.about_f, name='about'),
    path('logout/', views.logout_f, name='logout'),
    
    # Automatic dashboards
    path('catalog/<int:dataset_id>/', views.catalog_f, name='catalog'),
    path('widget/add/', views.add_widget_f, name='add_widget'),
    path('widget/remove/<int:widget_id>/', views.remove_widget_f, name='remove_widget'),
    path('widget/clear/<int:dataset_id>/', views.clear_dashboard_f, name='clear_dashboard'),
    path('widget/reorder/', views.reorder_widgets_f, name='reorder_widgets'),

    # Employees
    path('employee/create/', views.create_employee_f, name='create_employee'),
    path('employee/delete/<int:employee_id>/', views.delete_employee_f, name='delete_employee'),
    path('employee/form/', views.employee_form_f, name='employee_form'),
]