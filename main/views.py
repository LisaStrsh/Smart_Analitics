from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

@login_required
def main_f(request):
    return render(request, 'main/main.html')

def about_f(request):
    return render(request, 'main/about.html')

def registration_f(request):
    return render(request, 'main/reg.html')

def logout_f(request):
    return render(request, 'welcome/welcome.html')
