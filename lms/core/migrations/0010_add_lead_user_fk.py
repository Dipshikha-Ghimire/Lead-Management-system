from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency('auth.User'),
        ('core', '0009_remove_staff_profile_picture_application_exam_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='user',
            field=models.OneToOneField(
                blank=True,
                help_text='Linked user account for lead users',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='lead_profile',
                to='auth.user'
            ),
        ),
    ]
