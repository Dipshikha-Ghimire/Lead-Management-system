from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
import re


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username',
            'id': 'username'
        }),
        error_messages={
            'required': 'Username is required.',
            'max_length': 'Username cannot exceed 150 characters.'
        }
    )
    
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password',
            'id': 'password'
        }),
        error_messages={
            'required': 'Password is required.'
        }
    )

    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'id': 'remember'
        })
    )
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            username = username.strip()
            if not username:
                raise ValidationError('Username cannot be empty or contain only spaces.')
        return username
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            # Attempt to authenticate
            user = authenticate(username=username, password=password)
            if user is None:
                raise ValidationError('Invalid username or password. Please try again.')
            elif not user.is_active:
                raise ValidationError('This account has been disabled.')
            
            # Store the authenticated user for later use in the view
            self.user = user
        
        return cleaned_data


class SignupForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        min_length=3,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username',
            'id': 'username'
        }),
        error_messages={
            'required': 'Username is required.',
            'min_length': 'Username must be at least 3 characters long.',
            'max_length': 'Username cannot exceed 150 characters.'
        }
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address',
            'id': 'email'
        }),
        error_messages={
            'required': 'Email is required.',
            'invalid': 'Please enter a valid email address.'
        }
    )
    
    password1 = forms.CharField(
        min_length=8,
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password',
            'id': 'password1'
        }),
        error_messages={
            'required': 'Password is required.',
            'min_length': 'Password must be at least 8 characters long.'
        },
        label='Password'
    )
    
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password',
            'id': 'password2'
        }),
        error_messages={
            'required': 'Please confirm your password.'
        },
        label='Confirm Password'
    )
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        if username:
            username = username.strip()
            
            # Check if username is empty after stripping
            if not username:
                raise ValidationError('Username cannot be empty or contain only spaces.')
            
            # Check for valid characters (alphanumeric, underscore, hyphen)
            if not re.match(r'^[a-zA-Z0-9_-]+$', username):
                raise ValidationError('Username can only contain letters, numbers, underscores, and hyphens.')
            
            # Check if username starts with a letter
            if not username[0].isalpha():
                raise ValidationError('Username must start with a letter.')
            
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                raise ValidationError('This username is already taken. Please choose another.')
        
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        if email:
            email = email.lower().strip()
            
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                raise ValidationError('An account with this email already exists.')
        
        return email
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        
        if password:
            # Check for at least one uppercase letter
            if not re.search(r'[A-Z]', password):
                raise ValidationError('Password must contain at least one uppercase letter.')
            
            # Check for at least one lowercase letter
            if not re.search(r'[a-z]', password):
                raise ValidationError('Password must contain at least one lowercase letter.')
            
            # Check for at least one digit
            if not re.search(r'\d', password):
                raise ValidationError('Password must contain at least one number.')
            
            # Check for at least one special character
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                raise ValidationError('Password must contain at least one special character (!@#$%^&*(),.?":{}|<>).')
        
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        # Check if passwords match
        if password1 and password2 and password1 != password2:
            raise ValidationError('Passwords do not match. Please try again.')
        
        return cleaned_data
