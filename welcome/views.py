from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from main.models import UserProfile


def welcome_f(request):
    """Main welcome page - visible to everyone without authorization."""
    return render(request, 'welcome/welcome.html')


def registration_f(request):
    """
    Registration of a new user.
    
    What happens:
    1. User fills the form (username, email, password, company)
    2. We check that such a username is not yet taken
    3. We create a User (standard Django model - stores login/password)
    4. We create a UserProfile (our model - stores company name)
    5. Automatically log the user in and redirect to the main page
    """
    errors = {}

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")
        company = request.POST.get("company", "").strip()

        # Validation - checking that all fields are filled correctly
        if not username:
            errors['username'] = 'Enter username'
        elif User.objects.filter(username=username).exists():
            errors['username'] = 'This username is already taken'

        if not email:
            errors['email'] = 'Enter email'

        if not password1:
            errors['password1'] = 'Enter password'
        elif len(password1) < 6:
            errors['password1'] = 'Password is too short (minimum 6 characters)'

        if password1 != password2:
            errors['password2'] = 'Passwords do not match'

        # If there are no errors - create the user
        if not errors:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1  # Django hashes the password itself!
            )
            # Create a profile with the company name
            UserProfile.objects.create(
                user=user,
                company_name=company
            )
            # Automatically log into the account
            login(request, user)
            return redirect('/main/')

    return render(request, 'welcome/registration.html', {'errors': errors})


def log_in_f(request):
    """
    Account login.
    Takes username + password, checks via Django authenticate.
    Employees are redirected to the data entry form.
    """
    error = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # If the user is an employee, redirect to the form
            if hasattr(user, 'employee_profile'):
                return redirect('/main/employee/form/')
            return redirect('/main/')
        else:
            error = "Invalid username or password"

    return render(request, 'welcome/log_in.html', {'error': error})


def support_f(request):
    """Support page - available without authorization."""
    return render(request, 'welcome/support.html')
