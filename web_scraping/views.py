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
from datetime import datetime, timezone


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
def update_stock_item(request):
    """Atualiza um item no estoque interno (JSON).

    Requer usuário autenticado e com permissão de admin.
    Campos aceitos (opcionais): laboratory, current_stock, available_stock, min_stock,
    purchase_price, sale_price, min_age_months, max_age_months.
    Identificação do item: name (obrigatório).
    """
    if not request.session.get('user_authenticated'):
        return JsonResponse({'status': 'error', 'message': 'Não autenticado'}, status=401)

    session_user = request.session.get('user', {}) or {}
    if not _is_admin(session_user):
        return JsonResponse({'status': 'error', 'message': 'Apenas administradores podem atualizar o estoque.'}, status=403)

    try:
        try:
            payload = json.loads((request.body or b'').decode('utf-8') or '{}')
        except Exception:
            return JsonResponse({'status': 'error', 'message': 'JSON inválido.'}, status=400)

        name = (payload.get('name') or '').strip()
        if not name:
            return JsonResponse({'status': 'error', 'message': 'Campo "name" é obrigatório.'}, status=400)

        json_path = getattr(settings, 'INTERNAL_STOCK_JSON', None)
        if not json_path:
            json_path = os.path.join(settings.BASE_DIR, 'data', 'vaccines.json')

        if not os.path.exists(json_path):
            return JsonResponse({'status': 'error', 'message': f'Arquivo de estoque não encontrado: {json_path}'}, status=404)

        with open(json_path, 'r', encoding='utf-8') as f:
            doc = json.load(f) or {}

        items = doc.get('items', [])
        if not isinstance(items, list):
            return JsonResponse({'status': 'error', 'message': 'Formato inválido do arquivo de estoque (items).'}, status=500)

        needle = name.casefold()
        idx = next((i for i, it in enumerate(items) if (it.get('name') or '').strip().casefold() == needle), None)
        if idx is None:
            return JsonResponse({'status': 'error', 'message': 'Item não encontrado no estoque interno.'}, status=404)

        item = items[idx]

        def to_int(v, *, field_name: str):
            if v in (None, ''):
                return None
            try:
                iv = int(v)
            except (TypeError, ValueError):
                raise ValueError(f'Campo "{field_name}" deve ser inteiro.')
            if iv < 0:
                raise ValueError(f'Campo "{field_name}" não pode ser negativo.')
            return iv

        def to_float(v, *, field_name: str):
            if v in (None, ''):
                return None
            try:
                fv = float(str(v).replace(',', '.'))
            except (TypeError, ValueError):
                raise ValueError(f'Campo "{field_name}" deve ser numérico.')
            if fv < 0:
                raise ValueError(f'Campo "{field_name}" não pode ser negativo.')
            return round(fv, 2)

        # Strings
        if 'laboratory' in payload:
            item['laboratory'] = (payload.get('laboratory') or '').strip()

        # Inteiros
        if 'current_stock' in payload:
            item['current_stock'] = to_int(payload.get('current_stock'), field_name='current_stock')
        if 'available_stock' in payload:
            item['available_stock'] = to_int(payload.get('available_stock'), field_name='available_stock')
        if 'min_stock' in payload:
            item['min_stock'] = to_int(payload.get('min_stock'), field_name='min_stock')
        if 'min_age_months' in payload:
            item['min_age_months'] = to_int(payload.get('min_age_months'), field_name='min_age_months')
        if 'max_age_months' in payload:
            item['max_age_months'] = to_int(payload.get('max_age_months'), field_name='max_age_months')

        # Preços
        if 'purchase_price' in payload:
            item['purchase_price'] = to_float(payload.get('purchase_price'), field_name='purchase_price')
        if 'sale_price' in payload:
            item['sale_price'] = to_float(payload.get('sale_price'), field_name='sale_price')

        # Regras de consistência
        if item.get('current_stock') is not None and item.get('available_stock') is None:
            item['available_stock'] = item.get('current_stock')
        if item.get('available_stock') is not None and item.get('current_stock') is None:
            item['current_stock'] = item.get('available_stock')
        if (item.get('available_stock') is not None) and (item.get('current_stock') is not None):
            if int(item['available_stock']) > int(item['current_stock']):
                return JsonResponse({'status': 'error', 'message': 'available_stock não pode ser maior que current_stock.'}, status=400)

        # Salva de forma atômica
        items[idx] = item
        doc['items'] = items
        doc['last_updated'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        doc['source'] = doc.get('source') or 'internal-inventory'
        doc['total_items'] = len(items)

        tmp_path = f"{json_path}.tmp"
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, json_path)

        return JsonResponse({
            'status': 'success',
            'message': 'Item de estoque atualizado com sucesso.',
            'item': item,
            'last_updated': doc.get('last_updated'),
        })

    except ValueError as ve:
        return JsonResponse({'status': 'error', 'message': str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Erro ao atualizar item: {str(e)}'}, status=500)

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