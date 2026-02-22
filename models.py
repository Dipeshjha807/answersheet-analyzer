from django.db import models

# Create your models here.
from django.db import models

class StudentResult(models.Model):
    student_name = models.CharField(max_length=255)
    total_marks = models.FloatField()
    percentage = models.FloatField()
    date_analyzed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.student_name