from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0004_sorlthumbnail'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, upload_to='posts/', verbose_name='Картинка'),
        ),
    ]
