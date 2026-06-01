from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_whatsappnotification_message_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='whatsappnotification',
            name='assigned_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='whatsappnotification',
            name='assigned_to_name',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='whatsappnotification',
            name='assigned_to_username',
            field=models.CharField(blank=True, default='', max_length=150),
        ),
        migrations.AddField(
            model_name='whatsappnotification',
            name='queue_status',
            field=models.CharField(choices=[('pending', 'Pendente'), ('assigned', 'Em atendimento')], default='pending', max_length=20),
        ),
    ]
