# core/urls.py
from django.urls import path
from . import views
from .views import SyncCalendarView, CalendarAppointmentsView

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('users/', views.users_view, name='users'),
    path('whatsapp/', views.whatsapp_view, name='whatsapp'),
    path('sync-calendar/', SyncCalendarView.as_view(), name='sync_calendar'),
    path('calendar-appointments/', CalendarAppointmentsView.as_view(), name='calendar_appointments'),
    
    # Novas rotas para manipulação de agendamentos
    path('appointment/create/', views.create_appointment, name='create_appointment'),
    path('appointment/<int:appointment_id>/', views.get_appointment, name='get_appointment'),
    path('appointment/<int:appointment_id>/update/', views.update_appointment, name='update_appointment'),
    path('appointment/<int:appointment_id>/delete/', views.delete_appointment, name='delete_appointment'),
    path('appointments-by-date/', views.list_appointments_by_date, name='list_appointments_by_date'),
    # Vaccines (stock)
    path('vaccine/create/', views.create_vaccine, name='create_vaccine'),
]