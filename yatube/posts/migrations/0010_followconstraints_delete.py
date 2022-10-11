from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0009_followconstrains'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='follow',
            name='no_self_subscribe',
        ),
    ]
