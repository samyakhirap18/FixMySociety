from django.contrib import admin
from .models import Category, Complaint, ComplaintHistory, ComplaintVote

admin.site.register(Category)
admin.site.register(Complaint)
admin.site.register(ComplaintVote)
admin.site.register(ComplaintHistory)
