from django.db import migrations

def add_default_categories(apps, schema_editor):
    Category = apps.get_model('complaints', 'Category')
    defaults = [
        ('Water', 'Leaks, water supply and drainage'),
        ('Plumbing', 'Pipes, taps and sanitation'),
        ('Lift', 'Lift and elevator faults'),
        ('Electrical', 'Power, wiring and common lights'),
        ('Waste', 'Garbage collection and cleanliness'),
        ('Security', 'Gates, alarms and shared safety equipment'),
        ('Other', 'Other society maintenance'),
    ]
    for name, description in defaults:
        Category.objects.get_or_create(name=name, defaults={'description': description})

class Migration(migrations.Migration):
    dependencies = [('complaints', '0001_initial')]
    operations = [migrations.RunPython(add_default_categories, migrations.RunPython.noop)]
