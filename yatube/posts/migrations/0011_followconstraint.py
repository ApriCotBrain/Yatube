from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0010_followconstraints_delete'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('author', 'user'), name='unique subscription'),
        ),
    ]
