# core/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import User, Appointment, Vaccine, ChatMessage
from django.db.models import Count
import random
from datetime import datetime, timedelta
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from web_scraping.services.calendar_scraper import CalendarScraper
from web_scraping.utils.browser_manager import BrowserManager
from user_auth.decorators import login_required
from user_auth.user_manager import user_manager
import calendar
from django.conf import settings


def _is_admin(session_user: dict) -> bool:
    """Verifica se o usuário é admin ou superadmin"""
    if not session_user:
        return False
    # Verifica se é superadmin
    if session_user.get('is_superadmin') or session_user.get('role') == 'SUPERADMIN':
        return True
    if getattr(settings, 'SUPERADMIN_USERNAME', '') and session_user.get('username') == settings.SUPERADMIN_USERNAME:
        return True
    # Verifica se é admin
    return session_user.get('position') == 'Administrador' or session_user.get('role') == 'ADMIN'


@login_required
def dashboard(request):
    # Real data for dashboard
    today = timezone.now().date()
    total_appointments = Appointment.objects.count()
    total_users = User.objects.count()
    pending_chats = ChatMessage.objects.filter(needs_human=True, resolved=False).count()
    success_rate = 94  # Placeholder, calculate as needed

    # Get current user from session
    current_user = request.session.get('user', {})
    is_admin = _is_admin(current_user)

    # Stock info
    vaccine_names = list(Vaccine.objects.values_list('name', flat=True))
    vaccine_stock = list(Vaccine.objects.values_list('current_stock', flat=True))
    vaccine_min_stock = list(Vaccine.objects.values_list('minimum_stock', flat=True))

    # Notifications (last 3 chat messages needing human)
    notifications = []
    for msg in ChatMessage.objects.filter(needs_human=True).order_by('-timestamp')[:3]:
        notifications.append({
            'name': msg.user.name if msg.user else 'Desconhecido',
            'type': 'Atendimento Humano',
            'time': msg.timestamp.strftime('%H:%M') if msg.timestamp else '',
            'priority': 'high',
        })

    # Recent users (last 20)
    recent_users = []
    for u in User.objects.order_by('-created_at')[:20]:
        recent_users.append({
            'name': u.name,
            'phone': u.phone,
            'vaccine': u.last_vaccine or '',
            'date': u.created_at.strftime('%d/%m/%Y') if u.created_at else '',
            'synced': u.synced,
        })

    # Appointments for calendar (next 30 days)
    appointments = Appointment.objects.filter(appointment_date__gte=today, appointment_date__lte=today+timedelta(days=30)).select_related('user', 'vaccine').order_by('appointment_date', 'appointment_time')
    appointments_list = []
    for a in appointments:
        appointments_list.append({
            'patient': a.user.name,
            'vaccine': a.vaccine.name if a.vaccine else 'Vacina não especificada',
            'date': a.appointment_date.strftime('%d/%m/%Y'),
            'time': a.appointment_time,
            'status': a.get_status_display(),  # Mostrar em português
            'status_raw': a.status,
        })

    # Dashboard metrics
    vaccines_applied = Appointment.objects.filter(status='completed').count()
    patients_registered = total_users
    stock_percentage = int((sum(vaccine_stock) / (sum(vaccine_min_stock) or 1)) * 100) if vaccine_min_stock else 0
    next_vaccinations = Appointment.objects.filter(appointment_date__gte=today).count()

    # Series for charts (real data)
    # Completed appointments over last 7 days
    completed_series_labels = []
    completed_series_values = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = Appointment.objects.filter(status='completed', appointment_date=day).count()
        completed_series_labels.append(day.strftime('%d/%m'))
        completed_series_values.append(count)

    # New patients registered over last 7 days
    patients_series_labels = []
    patients_series_values = []
    for i in range(6, -1, -1):
        day_start = timezone.make_aware(datetime.combine(today - timedelta(days=i), datetime.min.time()))
        day_end = timezone.make_aware(datetime.combine(today - timedelta(days=i), datetime.max.time()))
        count = User.objects.filter(created_at__gte=day_start, created_at__lte=day_end).count()
        patients_series_labels.append((today - timedelta(days=i)).strftime('%d/%m'))
        patients_series_values.append(count)

    # Stock per vaccine (current vs minimum)
    stock_chart_labels = list(Vaccine.objects.values_list('name', flat=True))
    stock_chart_current = list(Vaccine.objects.values_list('current_stock', flat=True))
    stock_chart_minimum = list(Vaccine.objects.values_list('minimum_stock', flat=True))

    # Upcoming vaccinations next 7 days
    upcoming_series_labels = []
    upcoming_series_values = []
    for i in range(0, 7):
        day = today + timedelta(days=i)
        count = Appointment.objects.filter(appointment_date=day).count()
        upcoming_series_labels.append(day.strftime('%d/%m'))
        upcoming_series_values.append(count)

    vaccines = Vaccine.objects.all()

    # Calendar data (dashboard tab) - supports retroactive months via GET
    cal_year = request.GET.get('cal_year', today.year)
    cal_month = request.GET.get('cal_month', today.month)
    try:
        current_year = int(cal_year)
        current_month = int(cal_month)
        if current_month < 1 or current_month > 12:
            raise ValueError('Invalid month')
    except (ValueError, TypeError):
        current_year = today.year
        current_month = today.month

    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(current_year, current_month)

    month_appointments = Appointment.objects.filter(
        appointment_date__year=current_year,
        appointment_date__month=current_month
    ).select_related('user', 'vaccine')

    # Marca agendamentos em atraso (não concluídos, horário já passou)
    now_dt = timezone.localtime()
    for ap in month_appointments:
        is_past_date = ap.appointment_date < now_dt.date()
        is_today = ap.appointment_date == now_dt.date()
        is_overdue = False
        if ap.status not in ('completed', 'cancelled'):
            if is_past_date:
                is_overdue = True
            elif is_today:
                try:
                    ap_time = datetime.strptime(ap.appointment_time, '%H:%M').time()
                    if ap_time < now_dt.time():
                        is_overdue = True
                except Exception:
                    pass
        ap.is_overdue = is_overdue

    appointments_by_day = {}
    for appointment in month_appointments:
        d = appointment.appointment_date.day
        appointments_by_day.setdefault(d, []).append(appointment)

    today_appointments = Appointment.objects.filter(
        appointment_date=today
    ).select_related('user', 'vaccine').order_by('appointment_time')
    
    # Users tab: carregar todos usuários da plataforma (users.json)
    raw_users = user_manager.list_all_users()
    users_list = []
    for u in raw_users:
        name = u.get('name') or u.get('username') or 'Usuário'
        initials = (name[:2]).upper()
        role = u.get('role') or u.get('position') or 'Usuário'
        users_list.append({
            'name': name,
            'username': u.get('username', ''),
            'initials': initials,
            'role': role,
        })

    context = {
        'total_appointments': total_appointments,
        'total_users': total_users,
        'pending_chats': pending_chats,
        'success_rate': success_rate,
        'vaccine_names': vaccine_names,
        'vaccine_stock': vaccine_stock,
        'vaccine_min_stock': vaccine_min_stock,
        'notifications': notifications,
        'recent_users': recent_users,
        'appointments': appointments_list,
        'vaccines_applied': vaccines_applied,
        'patients_registered': patients_registered,
        'stock_percentage': stock_percentage,
        'next_vaccinations': next_vaccinations,
        'vaccines': vaccines,
        'users': users_list,
        'current_user': current_user,
        'is_admin': is_admin,
        # Chart data
        'completed_series_labels': completed_series_labels,
        'completed_series_values': completed_series_values,
        'patients_series_labels': patients_series_labels,
        'patients_series_values': patients_series_values,
        'stock_chart_labels': stock_chart_labels,
        'stock_chart_current': stock_chart_current,
        'stock_chart_minimum': stock_chart_minimum,
        'upcoming_series_labels': upcoming_series_labels,
        'upcoming_series_values': upcoming_series_values,
        # Calendar context
        'month_days': month_days,
        'current_year': current_year,
        'current_month': current_month,
        'current_month_name': calendar.month_name[current_month],
        'appointments_by_day': appointments_by_day,
        'today': today,
        'today_appointments': today_appointments,
        'all_users': User.objects.all(),
        'month_appointments': month_appointments,
        'prev_month': current_month - 1 if current_month > 1 else 12,
        'prev_year': current_year if current_month > 1 else current_year - 1,
        'next_month': current_month + 1 if current_month < 12 else 1,
        'next_year': current_year if current_month < 12 else current_year + 1,
    }
    return render(request, 'main_dashboard.html', context)

@method_decorator(csrf_exempt, name='dispatch')
class SyncCalendarView(View):
    def post(self, request):
        try:
            browser_manager = BrowserManager()
            calendar_scraper = CalendarScraper(browser_manager)
            
            appointments = calendar_scraper.scrape_calendar()
            
            return JsonResponse({
                'status': 'success',
                'message': f'Calendário sincronizado com sucesso. {len(appointments)} agendamentos encontrados.',
                'appointments_count': len(appointments)
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Erro ao sincronizar calendário: {str(e)}'
            }, status=500)

class CalendarAppointmentsView(View):
    def get(self, request):
        try:
            # Filtra por mês atual ou parâmetro específico
            month = request.GET.get('month')
            year = request.GET.get('year')
            
            appointments = Appointment.objects.all()
            
            if month and year:
                appointments = appointments.filter(
                    appointment_date__month=month,
                    appointment_date__year=year
                )
            else:
                # Mês atual por padrão
                today = datetime.now()
                appointments = appointments.filter(
                    appointment_date__month=today.month,
                    appointment_date__year=today.year
                )
            
            appointments_data = []
            for appointment in appointments:
                appointments_data.append({
                    'id': appointment.id,
                    'patient': appointment.user.name,
                    'vaccine': appointment.vaccine.name if appointment.vaccine else 'Vacina não especificada',
                    'date': appointment.appointment_date.strftime('%d/%m/%Y'),
                    'time': appointment.appointment_time,
                    'status': appointment.get_status_display(),
                    'status_raw': appointment.status,
                    'observations': appointment.observations
                })
            
            return JsonResponse({
                'status': 'success',
                'appointments': appointments_data
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Erro ao carregar agendamentos: {str(e)}'
            }, status=500)

def calendar_view(request):
    # Obtém o mês e ano atual
    today = timezone.now().date()
    year = request.GET.get('year', today.year)
    month = request.GET.get('month', today.month)
    
    try:
        year = int(year)
        month = int(month)
    except (ValueError, TypeError):
        year = today.year
        month = today.month
    
    # Cria o calendário
    cal = calendar.Calendar(firstweekday=6)  # Domingo como primeiro dia
    month_days = cal.monthdayscalendar(year, month)
    
    # Obtém agendamentos do mês atual
    appointments = Appointment.objects.filter(
        appointment_date__year=year,
        appointment_date__month=month
    ).select_related('user', 'vaccine')
    
    # Organiza agendamentos por dia
    appointments_by_day = {}
    for appointment in appointments:
        day = appointment.appointment_date.day
        if day not in appointments_by_day:
            appointments_by_day[day] = []
        appointments_by_day[day].append(appointment)
    
    # Agendamentos de hoje
    today_appointments = Appointment.objects.filter(
        appointment_date=today
    ).select_related('user', 'vaccine').order_by('appointment_time')
    
    # Todos os usuários e vacinas para os selects do modal
    all_users = User.objects.all()
    vaccines = Vaccine.objects.all()
    
    context = {
        'month_days': month_days,
        'current_year': year,
        'current_month': month,
        'current_month_name': calendar.month_name[month],
        'today': today,
        'appointments_by_day': appointments_by_day,
        'today_appointments': today_appointments,
        'prev_month': month - 1 if month > 1 else 12,
        'prev_year': year if month > 1 else year - 1,
        'next_month': month + 1 if month < 12 else 1,
        'next_year': year if month < 12 else year + 1,
        'all_users': all_users,
        'vaccines': vaccines,
        'appointments': appointments,
    }
    
    return render(request, 'core/calendar.html', context)

def users_view(request):
    # Remover dados fictícios. Exibir apenas Admin e Padrão.
    current_user = request.session.get('user', {})
    admin_name = current_user.get('name') or 'Admin'
    users = [
        {
            'name': admin_name,
            'phone': '',
            'cpf': '',
            'birth_date': '',
            'source': 'Sistema',
            'status': 'active'
        },
        {
            'name': 'Padrão',
            'phone': '',
            'cpf': '',
            'birth_date': '',
            'source': 'Sistema',
            'status': 'active'
        },
    ]
    context = {
        'users': users,
    }
    return render(request, 'users.html', context)

def whatsapp_view(request):
    # Dados mock para WhatsApp
    conversations = [
        {
            'name': 'Maria Silva',
            'time': '14:30',
            'last_message': 'Preciso de atendimento humano...',
            'priority': 'high',
            'unread': True,
            'active': True
        },
        {
            'name': 'João Santos',
            'time': '15:45',
            'last_message': 'Erro ao agendar...',
            'priority': 'medium',
            'unread': True,
            'active': False
        },
        {
            'name': 'Ana Costa',
            'time': '16:20',
            'last_message': 'Tenho uma dúvida sobre...',
            'priority': 'low',
            'unread': True,
            'active': False
        },
    ]
    
    chat_messages = [
        {'sender': 'client', 'message': 'Olá, gostaria de agendar uma vacina', 'time': '14:25'},
        {'sender': 'bot', 'message': 'Olá! Claro, posso te ajudar. Qual vacina você gostaria de agendar?', 'time': '14:25'},
        {'sender': 'client', 'message': 'COVID-19, por favor', 'time': '14:26'},
        {'sender': 'bot', 'message': 'Perfeito! Para qual data você gostaria de agendar?', 'time': '14:26'},
        {'sender': 'client', 'message': 'Amanhã, se possível', 'time': '14:27'},
        {'sender': 'bot', 'message': 'Tenho os seguintes horários disponíveis para amanhã (23/10):<br><br>• 09:00<br>• 11:00<br>• 14:30<br>• 16:00<br><br>Qual horário prefere?', 'time': '14:27'},
        {'sender': 'client', 'message': 'Na verdade, estou com dúvidas sobre o pagamento. Preciso falar com alguém', 'time': '14:30'},
        {'sender': 'bot', 'message': '⚠️ Atendimento Humano Solicitado<br><br>O cliente solicitou atendimento humano sobre dúvidas de pagamento.<br><br>Um atendente será notificado em breve.', 'time': '14:30', 'urgent': True},
    ]
    
    context = {
        'conversations': conversations,
        'chat_messages': chat_messages,
        'active_conversation': 'Maria Silva'
    }
    return render(request, 'whatsapp.html', context)

# ===================== NOVAS VIEWS PARA AGENDAMENTOS =====================

@require_http_methods(["POST"])
def create_appointment(request):
    """Cria um novo agendamento"""
    try:
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        user_id = request.POST.get('user_id')
        vaccine_id = request.POST.get('vaccine_id')
        patient_name = request.POST.get('patient_name')
        vaccine_name = request.POST.get('vaccine_name')
        dose = request.POST.get('dose', '')
        status = request.POST.get('status', 'scheduled')
        observations = request.POST.get('observations', '')
        
        # Validações
        if not all([appointment_date, appointment_time]):
            return JsonResponse({'status': 'error','message': 'Data e horário são obrigatórios'}, status=400)
        
        # Resolver paciente
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({'status': 'error','message': 'Paciente não encontrado'}, status=404)
        elif patient_name:
            try:
                user = User.objects.get(name__iexact=patient_name.strip())
            except User.DoesNotExist:
                return JsonResponse({'status': 'error','message': 'Paciente não encontrado pelo nome'}, status=404)
        else:
            return JsonResponse({'status': 'error','message': 'Informe o paciente'}, status=400)

        # Resolver vacina
        if vaccine_id:
            try:
                vaccine = Vaccine.objects.get(id=vaccine_id)
            except Vaccine.DoesNotExist:
                return JsonResponse({'status': 'error','message': 'Vacina não encontrada'}, status=404)
        elif vaccine_name:
            try:
                vaccine = Vaccine.objects.get(name__iexact=vaccine_name.strip())
            except Vaccine.DoesNotExist:
                return JsonResponse({'status': 'error','message': 'Vacina não encontrada pelo nome'}, status=404)
        else:
            return JsonResponse({'status': 'error','message': 'Informe a vacina'}, status=400)
        
        # Cria o agendamento
        appointment = Appointment.objects.create(
            user=user,
            vaccine=vaccine,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            dose=dose,
            status=status,
            observations=observations
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Agendamento criado com sucesso',
            'appointment_id': appointment.id
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao criar agendamento: {str(e)}'
        }, status=500)

@require_http_methods(["GET"])
def get_appointment(request, appointment_id):
    """Obtém detalhes de um agendamento específico"""
    try:
        appointment = Appointment.objects.select_related('user', 'vaccine').get(id=appointment_id)
        
        return JsonResponse({
            'status': 'success',
            'appointment': {
                'id': appointment.id,
                'user_name': appointment.user.name,
                'user_phone': appointment.user.phone,
                'vaccine_name': appointment.vaccine.name if appointment.vaccine else 'N/A',
                'appointment_date': appointment.appointment_date.strftime('%d/%m/%Y'),
                'appointment_time': appointment.appointment_time,
                'dose': appointment.dose,
                'status': appointment.status,
                'observations': appointment.observations,
            }
        })
    
    except Appointment.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Agendamento não encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao buscar agendamento: {str(e)}'
        }, status=500)

@require_http_methods(["POST"])
def update_appointment(request, appointment_id):
    """Atualiza um agendamento existente"""
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        
        # Atualiza os campos fornecidos
        if 'appointment_date' in request.POST:
            appointment.appointment_date = request.POST.get('appointment_date')
        if 'appointment_time' in request.POST:
            appointment.appointment_time = request.POST.get('appointment_time')
        if 'vaccine_id' in request.POST:
            try:
                vaccine = Vaccine.objects.get(id=request.POST.get('vaccine_id'))
                appointment.vaccine = vaccine
            except Vaccine.DoesNotExist:
                pass
        if 'dose' in request.POST:
            appointment.dose = request.POST.get('dose')
        if 'status' in request.POST:
            appointment.status = request.POST.get('status')
        if 'observations' in request.POST:
            appointment.observations = request.POST.get('observations')
        
        appointment.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Agendamento atualizado com sucesso'
        })
    
    except Appointment.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Agendamento não encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao atualizar agendamento: {str(e)}'
        }, status=500)

@require_http_methods(["POST"])
def delete_appointment(request, appointment_id):
    """Deleta um agendamento"""
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        appointment.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Agendamento deletado com sucesso'
        })
    
    except Appointment.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Agendamento não encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao deletar agendamento: {str(e)}'
        }, status=500)

@require_http_methods(["GET"])
def list_appointments_by_date(request):
    """Lista agendamentos por data"""
    try:
        date = request.GET.get('date')
        
        if not date:
            return JsonResponse({
                'status': 'error',
                'message': 'Data não fornecida'
            }, status=400)
        
        appointments = Appointment.objects.filter(
            appointment_date=date
        ).select_related('user', 'vaccine').order_by('appointment_time')
        
        now_dt = timezone.localtime()
        appointments_data = []
        for appointment in appointments:
            is_overdue = False
            if appointment.status not in ('completed', 'cancelled'):
                if appointment.appointment_date < now_dt.date():
                    is_overdue = True
                elif appointment.appointment_date == now_dt.date():
                    try:
                        ap_time = datetime.strptime(appointment.appointment_time, '%H:%M').time()
                        if ap_time < now_dt.time():
                            is_overdue = True
                    except Exception:
                        pass
            appointments_data.append({
                'id': appointment.id,
                'user_name': appointment.user.name,
                'vaccine_name': appointment.vaccine.name if appointment.vaccine else 'N/A',
                'appointment_time': appointment.appointment_time,
                'status': appointment.status,
                'is_overdue': is_overdue,
            })
        
        return JsonResponse({
            'status': 'success',
            'appointments': appointments_data,
            'count': len(appointments_data)
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao listar agendamentos: {str(e)}'
        }, status=500)

# ===================== ESTOQUE: CRIAR VACINA =====================
@require_http_methods(["POST"])
def create_vaccine(request):
    """Cria um novo item de estoque (Vaccine)."""
    try:
        name = (request.POST.get('name') or '').strip()
        laboratory = (request.POST.get('laboratory') or '').strip()
        lot_number = (request.POST.get('lot_number') or '').strip()
        expiry_date = (request.POST.get('expiry_date') or '').strip()
        min_stock = request.POST.get('minimum_stock') or request.POST.get('min_stock')
        current_stock = request.POST.get('current_stock')
        sale_price = request.POST.get('sale_price')
        purchase_price = request.POST.get('purchase_price')

        if not name:
            return JsonResponse({'status': 'error', 'message': 'Nome da vacina é obrigatório'}, status=400)

        # Conversões seguras
        def to_int(v, default=0):
            try:
                return int(v)
            except (TypeError, ValueError):
                return default

        def to_decimal(v):
            from decimal import Decimal, InvalidOperation
            try:
                return Decimal(str(v).replace(',', '.')) if v not in (None, '') else None
            except InvalidOperation:
                return None

        min_stock_i = to_int(min_stock, 0)
        current_stock_i = to_int(current_stock, 0)
        sale_price_d = to_decimal(sale_price)
        purchase_price_d = to_decimal(purchase_price)

        exp_date_obj = None
        if expiry_date:
            try:
                # aceita formatos YYYY-MM-DD ou DD/MM/YYYY
                if '-' in expiry_date:
                    exp_date_obj = datetime.strptime(expiry_date, '%Y-%m-%d').date()
                else:
                    exp_date_obj = datetime.strptime(expiry_date, '%d/%m/%Y').date()
            except Exception:
                pass

        vaccine = Vaccine.objects.create(
            name=name,
            laboratory=laboratory or None,
            lot_number=lot_number or None,
            expiry_date=exp_date_obj,
            current_stock=current_stock_i,
            available_stock=current_stock_i,
            minimum_stock=min_stock_i,
            min_stock=min_stock_i,
            sale_price=sale_price_d,
            purchase_price=purchase_price_d,
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Vacina criada com sucesso',
            'vaccine_id': vaccine.id
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao criar item de estoque: {str(e)}'
        }, status=500)

# ===================== ESTOQUE: ATUALIZAR VACINA =====================
@require_http_methods(["POST", "PATCH"])
def update_vaccine(request, vaccine_id: int):
    """Atualiza campos de um item de estoque (Vaccine).

    Campos aceitos (opcionais):
    - name, laboratory, lot_number, expiry_date
    - current_stock, available_stock, minimum_stock/min_stock
    - sale_price, purchase_price

    Regras:
    - Se apenas um entre current_stock/available_stock for fornecido, o outro mantém valor atual.
    - available_stock não pode ser maior que current_stock.
    - expiry_date aceita formatos YYYY-MM-DD ou DD/MM/YYYY.
    """
    try:
        vaccine = Vaccine.objects.filter(id=vaccine_id).first()
        if not vaccine:
            return JsonResponse({'status': 'error', 'message': 'Vacina não encontrada.'}, status=404)

        payload = request.POST if request.method == 'POST' else None
        if request.method == 'PATCH':
            # Para PATCH via JSON
            import json
            try:
                payload = json.loads(request.body.decode('utf-8') or '{}')
            except Exception:
                payload = {}

        def to_int(v, default=None):
            try:
                return int(v)
            except (TypeError, ValueError):
                return default

        def to_decimal(v):
            from decimal import Decimal, InvalidOperation
            try:
                return Decimal(str(v).replace(',', '.')) if v not in (None, '') else None
            except InvalidOperation:
                return None

        # Campos textuais
        name = (payload.get('name') or '').strip() if isinstance(payload, dict) else (payload.get('name') or '').strip()
        laboratory = (payload.get('laboratory') or '').strip() if isinstance(payload, dict) else (payload.get('laboratory') or '').strip()
        lot_number = (payload.get('lot_number') or '').strip() if isinstance(payload, dict) else (payload.get('lot_number') or '').strip()
        expiry_date = (payload.get('expiry_date') or '').strip() if isinstance(payload, dict) else (payload.get('expiry_date') or '').strip()

        if name:
            vaccine.name = name
        if laboratory:
            vaccine.laboratory = laboratory
        if lot_number:
            vaccine.lot_number = lot_number

        # Datas
        if expiry_date:
            try:
                if '-' in expiry_date:
                    vaccine.expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
                else:
                    vaccine.expiry_date = datetime.strptime(expiry_date, '%d/%m/%Y').date()
            except Exception:
                pass

        # Quantidades
        current_stock_in = payload.get('current_stock') if isinstance(payload, dict) else payload.get('current_stock')
        available_stock_in = payload.get('available_stock') if isinstance(payload, dict) else payload.get('available_stock')
        min_stock_in = payload.get('minimum_stock') if isinstance(payload, dict) else payload.get('minimum_stock')
        if min_stock_in is None:
            min_stock_in = payload.get('min_stock') if isinstance(payload, dict) else payload.get('min_stock')

        new_current = to_int(current_stock_in, default=vaccine.current_stock)
        new_available = to_int(available_stock_in, default=vaccine.available_stock)
        new_min = to_int(min_stock_in, default=vaccine.minimum_stock)

        # Preços
        sale_price_in = payload.get('sale_price') if isinstance(payload, dict) else payload.get('sale_price')
        purchase_price_in = payload.get('purchase_price') if isinstance(payload, dict) else payload.get('purchase_price')
        new_sale = to_decimal(sale_price_in)
        new_purchase = to_decimal(purchase_price_in)

        # Regra de estoque: available <= current
        if new_available is not None and new_current is not None and int(new_available) > int(new_current):
            return JsonResponse({'status': 'error', 'message': 'available_stock não pode ser maior que current_stock.'}, status=400)

        # Atribuições
        if new_current is not None:
            vaccine.current_stock = new_current
        if new_available is not None:
            vaccine.available_stock = new_available
        if new_min is not None:
            vaccine.minimum_stock = new_min
            vaccine.min_stock = new_min
        if new_sale is not None:
            vaccine.sale_price = new_sale
        if new_purchase is not None:
            vaccine.purchase_price = new_purchase

        vaccine.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Vacina atualizada com sucesso.',
            'vaccine': {
                'id': vaccine.id,
                'name': vaccine.name,
                'laboratory': vaccine.laboratory,
                'lot_number': vaccine.lot_number,
                'expiry_date': vaccine.expiry_date.isoformat() if vaccine.expiry_date else None,
                'current_stock': vaccine.current_stock,
                'available_stock': vaccine.available_stock,
                'minimum_stock': vaccine.minimum_stock,
                'sale_price': str(vaccine.sale_price) if vaccine.sale_price is not None else None,
                'purchase_price': str(vaccine.purchase_price) if vaccine.purchase_price is not None else None,
            }
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao atualizar item de estoque: {str(e)}'
        }, status=500)