# web_scraping/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .utils.browser_manager import BrowserManager
from .services.stock_scraper import StockScraper
from .services.users_scraper import UsersScraper
from .services.calendar_scraper import CalendarScraper
from .services.patient_search_scraper import PatientSearchScraper
from core.models import Vaccine, Appointment
from django.conf import settings
import os
import json
import time

@require_http_methods(["POST"])
@csrf_exempt
def sync_calendar(request):
    """Sincroniza agendamentos do sistema matriz"""
    browser = None
    try:
        # Inicializa o browser com retry
        for attempt in range(3):
            try:
                browser = BrowserManager()
                browser.start_browser(headless=True)
                if browser.driver:
                    break
            except Exception as e:
                print(f"Tentativa {attempt + 1} falhou: {e}")
                if browser:
                    browser.quit_browser()
                browser = None
                time.sleep(1)
        
        if not browser or not browser.driver:
            return JsonResponse({
                'status': 'error',
                'message': 'Não foi possível inicializar o navegador após 3 tentativas'
            }, status=500)
        
        scraper = CalendarScraper(browser)
        
        # Armazena contagem antes de sincronizar
        before_count = Appointment.objects.count()
        
        # Executa scraping
        appointments = scraper.scrape_calendar()
        
        # Conta novo após sincronizar
        after_count = Appointment.objects.count()
        new_appointments = after_count - before_count
        
        if appointments is None or len(appointments) == 0:
            return JsonResponse({
                'status': 'warning',
                'message': 'Nenhum agendamento encontrado para sincronizar',
                'appointments_count': 0,
                'new_appointments': 0
            })
        
        return JsonResponse({
            'status': 'success',
            'message': f'Sincronizados {len(appointments)} agendamentos',
            'appointments': appointments,
            'appointments_count': len(appointments),
            'new_appointments': new_appointments,
            'total_appointments': after_count,
        })
        
    except Exception as e:
        print(f"Erro na sincronização: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Erro na sincronização do calendário: {str(e)}'
        }, status=500)
    finally:
        if browser:
            try:
                browser.quit_browser()
            except:
                pass

@require_http_methods(["POST"])
@csrf_exempt
def sync_stock(request):
    """Sincroniza dados de estoque do sistema matriz"""
    browser = None
    try:
        browser = BrowserManager()
        browser.start_browser(headless=True)
        
        scraper = StockScraper(browser)
        result = scraper.sync_stock_to_database()
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro na sincronização: {str(e)}'
        }, status=500)
    finally:
        if browser and browser.driver:
            browser.quit_browser()

@require_http_methods(["GET"])
def stock_data(request):
    """Retorna dados do estoque atual a partir do banco interno (JSON)."""
    try:
        json_path = getattr(settings, 'INTERNAL_STOCK_JSON', None)
        if not json_path:
            # padrão: BASE_DIR/data/vaccines.json
            json_path = os.path.join(settings.BASE_DIR, 'data', 'vaccines.json')

        if not os.path.exists(json_path):
            return JsonResponse({
                'status': 'error',
                'message': f'Arquivo de estoque não encontrado: {json_path}'
            }, status=404)

        with open(json_path, 'r', encoding='utf-8') as f:
            payload = json.load(f)

        items = payload.get('items', [])
        vaccines_data = []
        summary = {
            'total_items': len(items),
            'items_out': 0,
            'items_low': 0,
            'inventory_value': 0.0,      # soma(current_stock * purchase_price)
            'potential_revenue': 0.0      # soma(available_stock * sale_price)
        }

        for item in items:
            name = item.get('name') or 'Item'
            lab = item.get('laboratory') or 'N/A'
            current = int(item.get('current_stock', 0) or 0)
            available = int(item.get('available_stock', current) or current)
            min_stock = int(item.get('min_stock', 0) or 0)
            purchase = float(item.get('purchase_price', 0) or 0)
            sale = float(item.get('sale_price', 0) or 0)
            min_age_m = int(item.get('min_age_months', 0) or 0)
            max_age_m = int(item.get('max_age_months', 0) or 0)
            unit_margin = round(sale - purchase, 2)
            inv_value = round(current * purchase, 2)
            pot_revenue = round(available * sale, 2)

            if current <= 0:
                status_class = 'status-out'
                status_text = 'Esgotado'
            elif current < min_stock:
                status_class = 'status-low'
                status_text = f'Estoque Baixo ({current} unidades)'
            else:
                status_class = 'status-available'
                status_text = f'Disponível ({current} unidades)'

            vaccines_data.append({
                'name': name,
                'laboratory': lab,
                'current_stock': current,
                'stock': current,  # Alias para compatibilidade com frontend
                'available_stock': available,
                'min_stock': min_stock,
                'purchase_price': purchase,
                'sale_price': sale,
                'unit_margin': unit_margin,
                'inventory_value': inv_value,
                'potential_revenue': pot_revenue,
                'min_age_months': min_age_m,
                'max_age_months': max_age_m,
                'status_class': status_class,
                'status_text': status_text
            })

            # Atualiza resumo
            summary['inventory_value'] += inv_value
            summary['potential_revenue'] += pot_revenue
            if current == 0:
                summary['items_out'] += 1
            elif current < min_stock:
                summary['items_low'] += 1

        return JsonResponse({
            'status': 'success',
            'source': 'json',
            'vaccines': vaccines_data,
            'summary': summary,
            'last_updated': payload.get('last_updated')
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao carregar dados: {str(e)}'
        }, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def sync_recent_users(request):
    """Sincroniza os últimos 20 usuários cadastrados"""
    browser = None
    try:
        browser = BrowserManager()
        browser.start_browser(headless=True)
        
        scraper = UsersScraper(browser)
        result = scraper.get_recent_users_for_display()
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro na sincronização: {str(e)}'
        }, status=500)
    finally:
        if browser and browser.driver:
            browser.quit_browser()

@require_http_methods(["GET"])
def recent_users_data(request):
    """Retorna dados dos últimos usuários (cache se disponível)"""
    try:
        # Aqui você pode implementar cache se desejar
        # Por enquanto retorna vazio até que seja feita uma sincronização
        
        return JsonResponse({
            'status': 'success',
            'users': [],
            'message': 'Nenhum dado em cache. Execute a sincronização.'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao carregar dados: {str(e)}'
        }, status=500)

# Rotas de geração de dados fictícios foram removidas para garantir que
# todo dado exibido no dashboard venha exclusivamente de scraping.

@require_http_methods(["POST"])
@csrf_exempt
def search_patient_by_cpf(request):
    """Busca paciente no sistema legado por CPF (web scraping)"""
    browser = None
    try:
        body = request.body.decode('utf-8') if request.body else ''
        cpf = request.POST.get('cpf') or (json.loads(body).get('cpf') if body else None)
        if not cpf:
            return JsonResponse({
                'status': 'error',
                'message': 'Informe o CPF.'
            }, status=400)

        browser = BrowserManager()
        browser.start_browser(headless=True)

        scraper = PatientSearchScraper(browser)
        result = scraper.search_by_cpf(cpf)

        if not result:
            return JsonResponse({
                'status': 'not_found',
                'message': 'Nenhum paciente encontrado para este CPF.'
            })

        return JsonResponse({
            'status': 'success',
            'patient': result
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao buscar paciente: {str(e)}'
        }, status=500)
    finally:
        if browser and browser.driver:
            try:
                browser.quit_browser()
            except Exception:
                pass