from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class Complaint(models.Model):
    SEVERITY_CHOICES = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')]
    PRIORITY_CHOICES = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')]
    STATUS_CHOICES = [('open', 'Open'), ('assigned', 'Assigned'), ('in_progress', 'In Progress'), ('resolved', 'Resolved'), ('verified', 'Verified')]

    title = models.CharField(max_length=180)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='complaints')
    severity = models.CharField(max_length=12, choices=SEVERITY_CHOICES, default='medium')
    priority = models.CharField(max_length=12, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='open')
    image = models.ImageField(upload_to='complaints/', blank=True, null=True)
    society = models.ForeignKey('accounts.Society', on_delete=models.CASCADE, related_name='complaints')
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='reported_complaints')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['society', 'status'], name='complaint_society_status_idx'),
            models.Index(fields=['priority'], name='complaint_priority_idx'),
        ]

    def __str__(self):
        return self.title


class ComplaintVote(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='complaint_votes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['complaint', 'user'], name='unique_complaint_vote')]


class ComplaintHistory(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='history')
    previous_status = models.CharField(max_length=15, blank=True)
    new_status = models.CharField(max_length=15)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    remarks = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
