from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from main.models import UserProfile


def welcome_f(request):
    """Главная приветственная страница — видна всем без авторизации."""
    return render(request, 'welcome/welcome.html')


def registration_f(request):
    """
    Регистрация нового пользователя.
    
    Что происходит:
    1. Пользователь заполняет форму (username, email, password, company)
    2. Мы проверяем, что такой username ещё не занят
    3. Создаём User (стандартная модель Django — хранит логин/пароль)
    4. Создаём UserProfile (наша модель — хранит название компании)
    5. Автоматически логиним пользователя и отправляем на главную
    """
    errors = {}

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")
        company = request.POST.get("company", "").strip()

        # Валидация — проверяем что все поля заполнены корректно
        if not username:
            errors['username'] = 'Введите имя пользователя'
        elif User.objects.filter(username=username).exists():
            errors['username'] = 'Это имя уже занято'

        if not email:
            errors['email'] = 'Введите email'

        if not password1:
            errors['password1'] = 'Введите пароль'
        elif len(password1) < 6:
            errors['password1'] = 'Пароль слишком короткий (минимум 6 символов)'

        if password1 != password2:
            errors['password2'] = 'Пароли не совпадают'

        # Если ошибок нет — создаём пользователя
        if not errors:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1  # Django сам хеширует пароль!
            )
            # Создаём профиль с названием компании
            UserProfile.objects.create(
                user=user,
                company_name=company
            )
            # Автоматически входим в аккаунт
            login(request, user)
            return redirect('/main/')

    return render(request, 'welcome/registration.html', {'errors': errors})


def log_in_f(request):
    """
    Вход в аккаунт.
    Принимает username + password, проверяет через Django authenticate.
    """
    error = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/main/')
        else:
            error = "Неверный логин или пароль"

    return render(request, 'welcome/log_in.html', {'error': error})


def support_f(request):
    """Страница поддержки — доступна без авторизации."""
    return render(request, 'welcome/support.html')
