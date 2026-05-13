from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login


def welcome_f(request):
    return render(request, 'welcome/welcome.html')

def registration_f(request):
    return render(request, 'welcome/registration.html')





def log_in_f(request):
    error = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/main/')
        else:
            error = "Wrong login or password"

    return render(request, 'welcome/log_in.html', {'error': error})


def support_f(request):
    return render(request, 'main/main.html')


