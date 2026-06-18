from django.db import models

class Report(models.Model):
    class ReportType(models.TextChoices):
        DAILY = 'DAILY', 'Daily Report'
        CONFLICT = 'CONFLICT', 'Conflict Report'
        TRAIN = 'TRAIN', 'Train Performance'

    report_type = models.CharField(max_length=20, choices=ReportType.choices)
    title = models.CharField(max_length=200)
    from_date = models.DateField()
    to_date = models.DateField()
    generated_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reports'
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.title} ({self.generated_at.strftime('%d %b %Y')})"
