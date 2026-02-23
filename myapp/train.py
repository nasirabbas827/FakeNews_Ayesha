import pickle
import re
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
from .models import ModelPerformance

# Download stopwords once
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

# ---------------------------
# Text Preprocessing Function
# ---------------------------
def preprocess_text(text):
    """
    Clean and preprocess text:
    - Lowercase
    - Remove URLs
    - Remove punctuation/numbers
    - Remove stopwords
    """
    text = str(text).lower()
    text = re.sub(r'http\S+', '', text)  # Remove URLs
    text = re.sub(r'[^a-z\s]', '', text)  # Remove punctuation/numbers
    words = text.split()
    words = [w for w in words if w not in stop_words]
    return " ".join(words)

# ---------------------------
# Training Function
# ---------------------------
def train_model(texts, labels, test_size=0.2, random_state=42):
    """
    Train AI model using lists of texts and labels
    Steps:
    1. Preprocess text
    2. Remove duplicates and empty texts
    3. Split into train/test
    4. Vectorize with TF-IDF
    5. Train Logistic Regression (class-balanced)
    6. Evaluate metrics
    7. Save model & log performance
    """
    print("Step 1: Preprocessing texts...")
    texts_cleaned = [preprocess_text(t) for t in texts]

    # Remove duplicates and empty
    combined = list(zip(texts_cleaned, labels))
    combined = [t for t in combined if t[0].strip() != '']  # remove empty
    unique_combined = list(dict.fromkeys(combined))  # remove duplicates
    texts_cleaned, labels = zip(*unique_combined)
    print(f"Preprocessing complete. {len(texts_cleaned)} unique, non-empty articles remain.")

    print("Step 2: Splitting data into training and test sets...")
    X_train, X_test, y_train, y_test = train_test_split(
        texts_cleaned, labels, test_size=test_size, random_state=random_state, stratify=labels
    )
    print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")

    print("Step 3: Vectorizing text with TF-IDF...")
    vectorizer = TfidfVectorizer(
        max_features=10000,
        ngram_range=(1,3),
        strip_accents='unicode',
        sublinear_tf=True
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    print(f"Vectorization complete. Vocabulary size: {len(vectorizer.vocabulary_)}")

    print("Step 4: Training Logistic Regression model...")
    clf = LogisticRegression(
        max_iter=1000,
        solver='liblinear',
        class_weight='balanced',
        verbose=1
    )
    clf.fit(X_train_vec, y_train)
    print("[Training complete]")

    print("Step 5: Evaluating model...")
    y_pred = clf.predict(X_test_vec)
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    print("\nClassification Report:\n")
    print(classification_report(y_test, y_pred))
    print(f"Accuracy: {acc:.4f}, Precision: {prec:.4f}, Recall: {rec:.4f}, F1-score: {f1:.4f}")

    print("Step 6: Saving model and vectorizer to 'fake_news_model.pkl'...")
    with open('fake_news_model.pkl', 'wb') as f:
        pickle.dump({'vectorizer': vectorizer, 'model': clf}, f)
    print("Model saved successfully.")

    print("Logging performance in database...")
    ModelPerformance.objects.create(
        accuracy=acc,
        precision=prec,
        recall=rec,
        f1_score=f1,
        notes=f"Trained on {len(texts_cleaned)} articles, test_size={test_size}"
    )
    print("Performance logged in database.")
    print("Training process finished successfully!")
