import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('accounts', '0003_user_case_insensitive_unique')]
    operations = [
        migrations.CreateModel(name='Society', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('name', models.CharField(max_length=150, unique=True)),
            ('address', models.TextField()),
            ('contact_information', models.CharField(max_length=255)),
        ]),
        migrations.AddField(model_name='user', name='role', field=models.CharField(choices=[('resident', 'Resident'), ('manager', 'Society Manager'), ('worker', 'Maintenance Worker')], default='resident', max_length=20)),
        migrations.AddField(model_name='user', name='society', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='members', to='accounts.society')),
    ]
