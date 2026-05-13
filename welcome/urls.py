from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome_f, name='welcome'),
    path('registration/', views.registration_f, name='registration'),
    path('log_in/', views.log_in_f, name='log_in'),
    path('support', views.support_f, name='support')
]