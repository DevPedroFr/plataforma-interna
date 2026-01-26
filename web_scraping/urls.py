# web_scraping/urls.py
from django.urls import path
from . import views
from . import views_google_forms

app_name = 'scraping'

urlpatterns = [
    # Calendário
    path('sync-calendar/', views.sync_calendar, name='sync_calendar'),
    
    # Estoque
    path('sync-stock/', views.sync_stock, name='sync_stock'),
    path('stock-data/', views.stock_data, name='stock_data'),
    path('stock-item/update/', views.update_stock_item, name='update_stock_item'),
    
    # Usuários recentes
    path('sync-recent-users/', views.sync_recent_users, name='sync_recent_users'),
    path('recent-users-data/', views.recent_users_data, name='recent_users_data'),

    # Busca por CPF (paciente)
    path('search-patient/', views.search_patient_by_cpf, name='search_patient_by_cpf'),
    
    # Google Forms - Sincronização e Registro de Pacientes
    path('sync-google-forms/', views_google_forms.trigger_google_forms_sync, name='sync_google_forms'),
    path('sync-status/', views_google_forms.sync_status, name='sync_status'),
    path('processed-patients/', views_google_forms.processed_patients_list, name='processed_patients_list'),
    path('processed-patients/<int:patient_id>/', views_google_forms.patient_detail, name='patient_detail'),
    path('processed-patients/<int:patient_id>/retry/', views_google_forms.retry_patient_registration, name='retry_patient'),
    path('dashboard/', views_google_forms.dashboard, name='dashboard'),
]