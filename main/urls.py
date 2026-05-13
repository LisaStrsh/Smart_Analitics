from django.urls import path
from . import views
from .views import logout_f

urlpatterns = [
    path('', views.main_f, name='home'),
    path('registration', views.registration_f),   #поправить
    path('about', views.about_f, name='about'),
    path('logout', logout_f, name='logout')
]