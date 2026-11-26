import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = [('accounts', '0004_society_and_user_roles'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='Category', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('name', models.CharField(max_length=80, unique=True)), ('description', models.CharField(blank=True, max_length=255)),
        ]),
        migrations.CreateModel(name='Complaint', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('title', models.CharField(max_length=180)), ('description', models.TextField()),
            ('severity', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='medium', max_length=12)),
            ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], default='medium', max_length=12)),
            ('status', models.CharField(choices=[('open', 'Open'), ('assigned', 'Assigned'), ('in_progress', 'In Progress'), ('resolved', 'Resolved'), ('verified', 'Verified')], default='open', max_length=15)),
            ('image', models.ImageField(blank=True, null=True, upload_to='complaints/')),
            ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)),
            ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_complaints', to=settings.AUTH_USER_MODEL)),
            ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='complaints', to='complaints.category')),
            ('reported_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reported_complaints', to=settings.AUTH_USER_MODEL)),
            ('society', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='complaints', to='accounts.society')),
        ], options={'ordering': ['-created_at'], 'indexes': [models.Index(fields=['society', 'status'], name='complaint_society_status_idx'), models.Index(fields=['priority'], name='complaint_priority_idx')]}),
        migrations.CreateModel(name='ComplaintHistory', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('previous_status', models.CharField(blank=True, max_length=15)), ('new_status', models.CharField(max_length=15)), ('remarks', models.CharField(blank=True, max_length=500)), ('created_at', models.DateTimeField(auto_now_add=True)),
            ('complaint', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='complaints.complaint')),
            ('updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
        ], options={'ordering': ['created_at']}),
        migrations.CreateModel(name='ComplaintVote', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('complaint', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='complaints.complaint')),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='complaint_votes', to=settings.AUTH_USER_MODEL)),
        ], options={'constraints': [models.UniqueConstraint(fields=('complaint', 'user'), name='unique_complaint_vote')]}),
    ]
