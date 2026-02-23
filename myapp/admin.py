from django.contrib import admin, messages
from .models import Profile, DatasetCSVUpload, NewsSubmission, ModelPerformance
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
import csv, io, datetime
from django.http import HttpResponse
from .train import train_model

# ---------------------------
# Profile inline for User
# ---------------------------
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Profile)

# ---------------------------
# CSV Upload Admin
# ---------------------------
@admin.register(DatasetCSVUpload)
class DatasetCSVUploadAdmin(admin.ModelAdmin):
    list_display = ('csv_file', 'uploaded_at')
    actions = ['train_from_csv']

    def train_from_csv(self, request, queryset):
        for csv_obj in queryset:
            try:
                file = csv_obj.csv_file
                decoded_file = file.read().decode('utf-8')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)
                texts, labels = [], []
                skipped_rows = 0
                seen_texts = set()

                for row in reader:
                    text = row.get('text')
                    label = row.get('label')
                    if text and label is not None and label != '':
                        text = text.strip()
                        if text in seen_texts:
                            skipped_rows += 1
                            continue
                        seen_texts.add(text)
                        try:
                            texts.append(text)
                            labels.append(int(label))
                        except Exception:
                            skipped_rows += 1
                            continue
                    else:
                        skipped_rows += 1

                if not texts or not labels:
                    self.message_user(request, f"No valid data found in {csv_obj.csv_file.name}", level=messages.WARNING)
                    continue

                train_model(texts, labels)
                msg = f"Trained AI on CSV: {csv_obj.csv_file.name} ({len(texts)} rows)"
                if skipped_rows > 0:
                    msg += f", skipped {skipped_rows} empty/duplicate/malformed rows"
                self.message_user(request, msg, level=messages.SUCCESS)

            except Exception as e:
                self.message_user(request, f"Error processing {csv_obj.csv_file.name}: {e}", level=messages.ERROR)

    train_from_csv.short_description = "Train AI model using selected CSV(s)"

# ---------------------------
# News Submission Admin
# ---------------------------
@admin.register(NewsSubmission)
class NewsSubmissionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'submitted_at', 'is_fake', 'confidence')
    list_filter = ('is_fake', 'submitted_at', 'user')
    search_fields = ('title', 'content', 'user__username')
    actions = ['export_usage_report', 'generate_summary']

    # Export all submissions to CSV
    def export_usage_report(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="usage_report_{datetime.date.today()}.csv"'

        writer = csv.writer(response)
        writer.writerow(['User', 'Title', 'Submitted At', 'Result', 'Confidence'])

        for s in queryset:
            writer.writerow([s.user.username, s.title, s.submitted_at, 'Fake' if s.is_fake else 'Real', s.confidence or 0])

        return response
    export_usage_report.short_description = "Export selected submissions to CSV"

    # Generate a quick summary in admin message
    def generate_summary(self, request, queryset):
        total = queryset.count()
        fake = queryset.filter(is_fake=True).count()
        real = queryset.filter(is_fake=False).count()
        self.message_user(request, f"Summary of selected: Total={total}, Fake={fake}, Real={real}")
    generate_summary.short_description = "Generate summary of selected submissions"

# ---------------------------
# Model Performance Admin
# ---------------------------
@admin.register(ModelPerformance)
class ModelPerformanceAdmin(admin.ModelAdmin):
    list_display = ('trained_on', 'accuracy', 'precision', 'recall', 'f1_score')
    ordering = ('-trained_on',)