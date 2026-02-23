from django.db import models
from django.contrib.auth.models import User

# ---------------------------
# User Profile
# ---------------------------
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20,blank=True,null=True,default="0000000000")

    def __str__(self):
        return self.user.username



# ---------------------------
# CSV Upload Model
# ---------------------------
class DatasetCSVUpload(models.Model):
    csv_file = models.FileField(upload_to='datasets/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"CSV uploaded on {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"

# ---------------------------
# User Submitted News
# ---------------------------
class NewsSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_fake = models.BooleanField(null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.user.username}"
    

# ---------------------------
# AI Model Performance Tracking
# ---------------------------
class ModelPerformance(models.Model):
    trained_on = models.DateTimeField(auto_now_add=True)
    accuracy = models.FloatField()
    precision = models.FloatField()
    recall = models.FloatField()
    f1_score = models.FloatField()
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Model Performance on {self.trained_on.strftime('%Y-%m-%d %H:%M')}"
