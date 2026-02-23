import re
import pickle
import nltk
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from nltk.corpus import stopwords

# Import your forms and models
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, NewsSubmissionForm
from .models import NewsSubmission , Profile

# ----------------------------------------------------------------
# Initialize NLP Resources (Do this once at startup)
# ----------------------------------------------------------------
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

stop_words = set(stopwords.words('english'))

# ----------------------------------------------------------------
# ML Model Loading
# ----------------------------------------------------------------
MODEL_PATH = 'fake_news_model.pkl'

def load_ml_assets():
    """Load the trained vectorizer and model."""
    try:
        with open(MODEL_PATH, 'rb') as f:
            data = pickle.load(f)
            return data['vectorizer'], data['model']
    except (FileNotFoundError, KeyError, Exception) as e:
        print(f"Error loading ML assets: {e}")
        return None, None

vectorizer, model = load_ml_assets()

# ----------------------------------------------------------------
# Logic Helpers
# ----------------------------------------------------------------
def preprocess_text(text):
    """Clean and tokenize news content."""
    text = text.lower()
    text = re.sub(r'http\S+', '', text)  # Remove URLs
    text = re.sub(r'[^a-z\s]', '', text) # Remove special chars/numbers
    words = text.split()
    words = [w for w in words if w not in stop_words]
    return " ".join(words)

# ----------------------------------------------------------------
# Auth Views
# ----------------------------------------------------------------


def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()  # Save the user
            # Create Profile immediately after user is created
            Profile.objects.create(user=user)
            
            messages.success(request, 'Account created! You can now login.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

from django.db.models import Count, Avg
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    user_submissions = NewsSubmission.objects.filter(user=request.user).order_by('-submitted_at')

    # Summary stats
    total_submissions = user_submissions.count()
    fake_count = user_submissions.filter(is_fake=True).count()
    real_count = user_submissions.filter(is_fake=False).count()
    avg_confidence = user_submissions.aggregate(Avg('confidence'))['confidence__avg'] or 0

    # Chart data
    chart_data = {
        'labels': [s.submitted_at.strftime('%b %d') for s in user_submissions],
        'fake_counts': [1 if s.is_fake else 0 for s in user_submissions],
        'real_counts': [0 if s.is_fake else 1 for s in user_submissions],
        'confidences': [s.confidence or 0 for s in user_submissions],
    }

    context = {
        'total_submissions': total_submissions,
        'fake_count': fake_count,
        'real_count': real_count,
        'avg_confidence': avg_confidence,
        'recent_submissions': user_submissions[:5],  # latest 5
        'chart_data': chart_data,
    }

    return render(request, 'dashboard.html', context)

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')

@login_required
def profile_view(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        # Assuming Profile is linked to User via OneToOneField
        p_form = ProfileUpdateForm(request.POST, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    
    return render(request, 'profile.html', {'u_form': u_form, 'p_form': p_form})

# ----------------------------------------------------------------
# Core AI Logic
# ----------------------------------------------------------------


@login_required
def submit_news(request):
    if request.method == 'POST':
        form = NewsSubmissionForm(request.POST)
        if form.is_valid():
            news = form.save(commit=False)
            news.user = request.user

            if vectorizer and model:
                # Perform AI Analysis
                clean_text = preprocess_text(news.content)
                vec = vectorizer.transform([clean_text])
                
                prediction = model.predict(vec)[0]
                # Probability of the selected class
                confidence = model.predict_proba(vec).max() * 100 
                
                # Logic: If prediction is 0, it's Fake (depending on your model's labels)
                news.is_fake = bool(prediction == 0)
                news.confidence = float(confidence)
                
                news.save()
                messages.success(request, f'Analysis complete: This news looks { "Fake" if news.is_fake else "Real" }.')
                return redirect('history')
            else:
                messages.error(request, 'AI Model is currently offline. Please contact admin.')
    else:
        form = NewsSubmissionForm()
    return render(request, 'submit_news.html', {'form': form})

import io
import pandas as pd
from django.http import HttpResponse, JsonResponse

@login_required
def history(request):
    submissions = NewsSubmission.objects.filter(user=request.user).order_by('-submitted_at')
    
    # Prepare chart data
    chart_data = {
        'labels': [s.submitted_at.strftime('%b %d') for s in submissions],
        'fake_counts': [1 if s.is_fake else 0 for s in submissions],
        'real_counts': [0 if s.is_fake else 1 for s in submissions],
        'confidences': [s.confidence or 0 for s in submissions],
    }

    return render(request, 'history.html', {
        'submissions': submissions,
        'chart_data': chart_data
    })


@login_required
def export_history(request, file_type='excel'):
    submissions = NewsSubmission.objects.filter(user=request.user).order_by('-submitted_at')
    
    df = pd.DataFrame([{
        'Title': s.title,
        'Content': s.content,
        'Date': s.submitted_at.strftime('%Y-%m-%d %H:%M'),
        'Result': 'Fake' if s.is_fake else 'Real',
        'Confidence (%)': s.confidence or 0
    } for s in submissions])

    if file_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="news_history.csv"'
        df.to_csv(path_or_buf=response, index=False)
    else:  # Default to Excel
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="news_history.xlsx"'
        with io.BytesIO() as b:
            with pd.ExcelWriter(b, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='History', index=False)
            response.write(b.getvalue())
    return response