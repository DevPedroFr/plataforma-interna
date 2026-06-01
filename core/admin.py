from django.contrib import admin
from .models import User, Vaccine, Appointment, ChatMessage, WhatsappNotification

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'cpf', 'via_chatbot', 'synced', 'created_at']
    list_filter = ['via_chatbot', 'synced', 'created_at']
    search_fields = ['name', 'phone', 'cpf']

@admin.register(Vaccine)
class VaccineAdmin(admin.ModelAdmin):
    list_display = ['name', 'lot_number', 'current_stock', 'minimum_stock', 'expiry_date']
    list_filter = ['expiry_date']
    search_fields = ['name', 'lot_number']

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'vaccine', 'appointment_date', 'appointment_time', 'status', 'via_chatbot']
    list_filter = ['status', 'via_chatbot', 'appointment_date']
    search_fields = ['user__name', 'vaccine__name']

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'message_short', 'from_user', 'needs_human', 'resolved', 'timestamp']
    list_filter = ['from_user', 'needs_human', 'resolved', 'timestamp']
    search_fields = ['user__name', 'message']
    
    def message_short(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_short.short_description = 'Mensagem'


@admin.register(WhatsappNotification)
class WhatsappNotificationAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'instance', 'message_type', 'queue_status', 'assigned_to_name', 'message_id', 'read', 'created_at']
    list_filter = ['instance', 'message_type', 'queue_status', 'read', 'created_at']
    search_fields = ['name', 'phone', 'message', 'message_id', 'assigned_to_name', 'assigned_to_username']