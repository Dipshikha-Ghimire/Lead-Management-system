from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm, SignupForm


# ---------- AUTH VIEWS ----------

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            # If form is valid, user is already authenticated in the form's clean method
            user = form.user
            login(request, user)

            remember_me = form.cleaned_data.get('remember_me', False)
            if not remember_me:
                request.session.set_expiry(0)

            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect to next parameter if available, else dashboard
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = LoginForm()
    
    return render(request, 'core/login.html', {'form': form})


def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            # Create the user
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password1']
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            messages.success(request, 'Account created successfully! Please login with your credentials.')
            return redirect('login')
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = SignupForm()
    
    return render(request, 'core/signup.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ---------- PROTECTED PAGES ----------

@login_required(login_url='login')
def dashboard(request):
    return render(request, 'core/dashboard.html')


@login_required(login_url='login')
def leads(request):
    return render(request, 'core/leads.html')


@login_required(login_url='login')
def applications(request):
    return render(request, 'core/applications.html')


@login_required(login_url='login')
def exams(request):
    return render(request, 'core/exams.html')


@login_required(login_url='login')
def finance(request):
    return render(request, 'core/finance.html')


@login_required(login_url='login')
def settings(request):
    return render(request, 'core/settings.html')


def home(request):
    return render(request, 'core/homepage.html')
