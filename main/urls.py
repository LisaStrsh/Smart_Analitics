from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_f, name='home'),
    path('data/', views.data_f, name='data'),
    path('data/upload/', views.upload_dataset_f, name='upload_dataset'),
    path('data/<int:dataset_id>/', views.dataset_detail_f, name='dataset_detail'),
    path('data/<int:dataset_id>/mapping/', views.update_mapping_f, name='update_mapping'),
    path('data/<int:dataset_id>/delete/', views.delete_dataset_f, name='delete_dataset'),
    path('settings/', views.settings_f, name='settings'),
    path('about/', views.about_f, name='about'),
    path('logout/', views.logout_f, name='logout'),
]