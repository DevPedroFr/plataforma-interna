# core/models.py
from django.db import models

class User(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    cpf = models.CharField(max_length=14, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    via_chatbot = models.BooleanField(default=False)
    synced = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_vaccine = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name

class Vaccine(models.Model):
    name = models.CharField(max_length=100)
    lot_number = models.CharField(max_length=50, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    current_stock = models.IntegerField(default=0)
    available_stock = models.IntegerField(default=0)
    minimum_stock = models.IntegerField(default=10)
    min_stock = models.IntegerField(default=10)  # Alias para compatibilidade
    laboratory = models.CharField(max_length=100, blank=True, null=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return self.name

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Agendado'),
        ('confirmed', 'Confirmado'),
        ('completed', 'Concluído'),
        ('cancelled', 'Cancelado'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vaccine = models.ForeignKey(Vaccine, on_delete=models.SET_NULL, null=True, blank=True)
    appointment_date = models.DateField()
    appointment_time = models.CharField(max_length=8)
    dose = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    via_chatbot = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    observations = models.TextField(blank=True)

    class Meta:
        ordering = ['appointment_date', 'appointment_time']

    def __str__(self):
        return f"{self.user.name} - {self.appointment_date} {self.appointment_time}"

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    from_user = models.BooleanField(default=False)
    needs_human = models.BooleanField(default=False)
    resolved = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name if self.user else 'Unknown'} - {self.timestamp}"


class WhatsappNotification(models.Model):
    name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30)
    message = models.TextField()
    instance = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.phone} - {self.created_at:%d/%m/%Y %H:%M}"