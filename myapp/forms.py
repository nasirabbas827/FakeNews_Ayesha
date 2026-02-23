from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, NewsSubmission

# -----------------------------
# User Registration Form
# -----------------------------
class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email'
    }))
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your username'
    }))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter password'
    }))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm password'
    }))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


# -----------------------------
# User Profile Update Form
# -----------------------------
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email'
    }))
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your username'
    }))

    class Meta:
        model = User
        fields = ['username', 'email']


# -----------------------------
# Profile Update Form (extra fields like phone)
# -----------------------------
class ProfileUpdateForm(forms.ModelForm):
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter phone number'
    }))

    class Meta:
        model = Profile
        fields = ['phone']


# -----------------------------
# News Submission Form
# -----------------------------
class NewsSubmissionForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter news title'
    }))
    content = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'form-control',
        'rows': 5,
        'placeholder': 'Enter news content here...'
    }))

    class Meta:
        model = NewsSubmission
        fields = ['title', 'content']
