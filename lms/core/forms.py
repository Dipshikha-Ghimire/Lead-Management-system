from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
import re
from .models import Lead, Program, Staff



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


class LeadSubmissionForm(forms.Form):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=False)
    phone = forms.CharField(max_length=20, required=True)
    date_of_birth = forms.DateField(required=False, input_formats=['%Y-%m-%d'])
    gender = forms.ChoiceField(required=False, choices=Lead.GENDER_CHOICES)
    address = forms.CharField(required=False)
    nationality = forms.CharField(max_length=100, required=False)
    alternate_contact = forms.CharField(max_length=20, required=False)
    program_interest = forms.CharField(max_length=255, required=True)
    education_level = forms.ChoiceField(required=True, choices=Lead.EDUCATION_LEVEL_CHOICES)
    gpa_or_percentage = forms.CharField(max_length=50, required=False)
    previous_institution = forms.CharField(max_length=255, required=False)
    education_document = forms.FileField(required=False)
    scholarship_interest = forms.ChoiceField(required=False, choices=Lead.SCHOLARSHIP_INTEREST_CHOICES)
    study_mode = forms.ChoiceField(required=False, choices=Lead.STUDY_MODE_CHOICES)
    lead_source = forms.ChoiceField(required=True, choices=Lead.SOURCE_CHOICES)
    lead_status = forms.ChoiceField(required=False, choices=Lead.STATUS_CHOICES)
    counselor = forms.IntegerField(required=False)
    followup_date = forms.DateField(required=False, input_formats=['%Y-%m-%d'])
    notes = forms.CharField(required=False)

    def __init__(self, *args, user_role='lead', **kwargs):
        self.user_role = user_role
        super().__init__(*args, **kwargs)

    def clean_first_name(self):
        value = (self.cleaned_data.get('first_name') or '').strip()
        if not value:
            raise ValidationError('First name is required.')
        return value

    def clean_last_name(self):
        value = (self.cleaned_data.get('last_name') or '').strip()
        if not value:
            raise ValidationError('Last name is required.')
        return value

    def clean_phone(self):
        value = (self.cleaned_data.get('phone') or '').strip()
        if not value:
            raise ValidationError('Phone number is required.')
        return value

    def clean_program_interest(self):
        value = (self.cleaned_data.get('program_interest') or '').strip()
        if not value:
            raise ValidationError('Please select a program.')

        program = Program.objects.filter(name__iexact=value).first()
        if not program:
            program = Program.objects.filter(name__icontains=value).first()
        if not program:
            raise ValidationError('Selected program is invalid.')

        self.cleaned_data['program_obj'] = program
        return value

    def clean_counselor(self):
        counselor_id = self.cleaned_data.get('counselor')
        if not counselor_id:
            return None

        counselor = Staff.objects.filter(staff_id=counselor_id).first()
        if not counselor:
            raise ValidationError('Selected counselor is invalid.')
        return counselor

    def clean(self):
        cleaned_data = super().clean()

        education_level = cleaned_data.get('education_level')
        education_document = cleaned_data.get('education_document')
        if education_level and not education_document:
            self.add_error('education_document', 'Education document is required after selecting highest education level.')

        # Lead users cannot assign workflow-only fields.
        if self.user_role == 'lead':
            cleaned_data['lead_status'] = 'new'
            cleaned_data['counselor'] = None
            cleaned_data['followup_date'] = None
            cleaned_data['notes'] = None
        elif not cleaned_data.get('lead_status'):
            cleaned_data['lead_status'] = 'new'

        return cleaned_data
