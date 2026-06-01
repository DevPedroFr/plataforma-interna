from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_whatsappnotification_assignment_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='whatsappnotification',
            name='queue_status',
            field=models.CharField(
                choices=[('pending', 'Pendente'), ('assigned', 'Em atendimento'), ('completed', 'Finalizado')],
                default='pending',
                max_length=20,
            ),
        ),
    ]