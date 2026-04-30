# twimood/models.py
from django.db import models

class Tweet(models.Model):
    date = models.DateTimeField()
    text = models.TextField()
    labels = models.TextField(blank=True, default="")

    def __str__(self):
        return f"{self.date.date()} - {self.text[:30]}"
