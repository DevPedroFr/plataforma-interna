"""user_auth/views.py

Autenticação baseada em session + users.json.

Regras:
- USER: acesso normal.
- ADMIN: pode criar/editar/excluir usuários (dados), mas NÃO pode ver/resetar senha.
- SUPERADMIN: único que pode ver/resetar senha de outros.
- Usuários criados com senha padrão devem trocar no primeiro acesso (must_change_password).
"""

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from .user_manager import user_manager


def _is_superadmin(session_user: dict) -> bool:
    if not session_user:
        return False
    if session_user.get('is_superadmin') or session_user.get('role') == 'SUPERADMIN':
        return True
    return bool(getattr(settings, 'SUPERADMIN_USERNAME', '') and session_user.get('username') == settings.SUPERADMIN_USERNAME)


def _is_admin(session_user: dict) -> bool:
    if not session_user:
        return False
    if _is_superadmin(session_user):
        return True
    return session_user.get('position') == 'Administrador' or session_user.get('role') == 'ADMIN'


@csrf_protect
@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Tela de login.
    GET: Renderiza o formulário de login
    POST: Processa o login
    """
    # Se já está autenticado, redireciona para dashboard
    if request.session.get('user_authenticated'):
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            return render(request, 'user_auth/login.html', {
                'error': 'Por favor, preencha todos os campos.'
            })
        
        # Tenta autenticar
        user = user_manager.authenticate(username, password)
        
        if user:
            # Login bem-sucedido
            user_manager.update_last_login(username)
            request.session['user_authenticated'] = True
            request.session['user'] = user
            request.session['username'] = username
            if user.get('must_change_password'):
                return redirect('auth:change_password')
            return redirect('core:dashboard')
        else:
            # Falha na autenticação
            return render(request, 'user_auth/login.html', {
                'error': 'Usuário ou senha inválidos.',
                'username': username
            })
    
    return render(request, 'user_auth/login.html')


def logout_view(request):
    """
    Logout - limpa a sessão e redireciona para o login
    """
    request.session.flush()
    return redirect('auth:login')


def profile_view(request):
    """
    Exibe o perfil do usuário logado
    """
    if not request.session.get('user_authenticated'):
        return redirect('auth:login')
    
    user = request.session.get('user', {})
    
    context = {
        'user': user,
    }
    
    return render(request, 'user_auth/profile.html', context)


@csrf_protect
@require_http_methods(["GET", "POST"])
def change_password_view(request):
    """Troca a senha do usuário logado.

    - Se must_change_password=True: não exige senha antiga.
    - Caso contrário: exige old_password.
    """
    if not request.session.get('user_authenticated'):
        return redirect('auth:login')

    session_user = request.session.get('user', {}) or {}
    username = request.session.get('username')
    if not username:
        request.session.flush()
        return redirect('auth:login')

    must_change = bool(session_user.get('must_change_password'))

    if request.method == 'POST':
        old_password = request.POST.get('old_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not new_password or not confirm_password:
            return render(request, 'user_auth/change_password.html', {
                'error': 'Preencha a nova senha e a confirmação.',
                'must_change': must_change,
            })

        if new_password != confirm_password:
            return render(request, 'user_auth/change_password.html', {
                'error': 'A confirmação não confere.',
                'must_change': must_change,
            })

        if len(new_password) < 6:
            return render(request, 'user_auth/change_password.html', {
                'error': 'A senha deve ter pelo menos 6 caracteres.',
                'must_change': must_change,
            })

        if must_change:
            ok = user_manager.set_password_self(username, new_password)
        else:
            if not old_password:
                return render(request, 'user_auth/change_password.html', {
                    'error': 'Informe a senha atual.',
                    'must_change': must_change,
                })
            ok = user_manager.change_password(username, old_password, new_password)

        if not ok:
            return render(request, 'user_auth/change_password.html', {
                'error': 'Não foi possível alterar a senha. Verifique a senha atual.',
                'must_change': must_change,
            })

        # Atualiza sessão
        request.session['user'] = user_manager.get_user_by_username(username) or {}
        return redirect('core:dashboard')

    return render(request, 'user_auth/change_password.html', {
        'must_change': must_change,
    })


from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

@csrf_exempt
@require_POST
def delete_user_view(request):
    """
    Exclui um usuário (paciente ou admin) se o logado for administrador
    """
    if not request.session.get('user_authenticated'):
        return JsonResponse({'success': False, 'message': 'Usuário não autenticado.'}, status=403)

    user = request.session.get('user', {})
    # Verifica se o usuário é ADMIN/SUPERADMIN
    if not _is_admin(user):
        return JsonResponse({'success': False, 'message': 'Apenas adms podem fazer isso.', 'is_admin': False}, status=403)

    # Tenta obter username/identificador de várias fontes
    username_to_delete = None
    
    # Primeiro tenta POST
    username_to_delete = request.POST.get('username')
    
    # Se não encontrou, tenta JSON no body
    if not username_to_delete:
        try:
            import json
            data = json.loads(request.body.decode('utf-8'))
            username_to_delete = data.get('username')
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            pass
    
    # Se ainda não encontrou, tenta GET
    if not username_to_delete:
        username_to_delete = request.GET.get('username')
    
    if not username_to_delete:
        return JsonResponse({'success': False, 'message': 'Usuário para exclusão não informado.'}, status=400)

    if username_to_delete == user.get('username'):
        return JsonResponse({'success': False, 'message': 'Você não pode excluir a si mesmo.'}, status=400)

    # Tenta deletar como paciente (User do banco de dados) primeiro
    from core.models import User as PatientUser
    from django.db.models import Q
    
    try:
        # Tenta encontrar por nome exato ou similar
        patient = PatientUser.objects.get(Q(name=username_to_delete) | Q(name__iexact=username_to_delete))
        patient.delete()
        return JsonResponse({'success': True, 'message': 'Paciente excluído com sucesso.'})
    except PatientUser.DoesNotExist:
        pass
    except PatientUser.MultipleObjectsReturned:
        return JsonResponse({'success': False, 'message': 'Múltiplos pacientes encontrados com esse nome.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao excluir paciente: {str(e)}'}, status=500)

    # Se não encontrou como paciente, tenta deletar como usuário admin
    deleted = user_manager.delete_user(username_to_delete)
    if deleted:
        return JsonResponse({'success': True, 'message': 'Usuário excluído com sucesso.'})
    else:
        return JsonResponse({'success': False, 'message': 'Usuário não encontrado.'}, status=404)


@csrf_exempt
@require_POST
def create_user_view(request):
    """
    Cria um novo usuário da plataforma (não paciente) e salva em users.json.
    Espera JSON com: username, password, name, position (opcional).
    """
    if not request.session.get('user_authenticated'):
        return JsonResponse({'success': False, 'message': 'Usuário não autenticado.'}, status=403)

    # Regra: apenas ADMIN/SUPERADMIN pode criar novos usuários
    current_user = request.session.get('user', {})
    if not _is_admin(current_user):
        return JsonResponse({'success': False, 'message': 'Apenas Administrador pode criar usuários.'}, status=403)

    try:
        import json as _json
        data = _json.loads(request.body.decode('utf-8'))
    except Exception:
        # fallback para form-encoded
        data = {
            'username': request.POST.get('username'),
            'password': request.POST.get('password'),
            'name': request.POST.get('name'),
            'position': request.POST.get('position'),
        }

    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()
    name = (data.get('name') or '').strip()
    position = (data.get('position') or 'Operador').strip()

    if not username or not name:
        return JsonResponse({'success': False, 'message': 'Campos obrigatórios: username, name.'}, status=400)

    # Senha: SUPERADMIN pode definir; ADMIN usa senha padrão
    is_superadmin = _is_superadmin(current_user)
    if not is_superadmin:
        password = getattr(settings, 'DEFAULT_USER_PASSWORD', '123456')
    if not password:
        password = getattr(settings, 'DEFAULT_USER_PASSWORD', '123456')

    # Verifica duplicidade
    if user_manager.user_exists(username):
        return JsonResponse({'success': False, 'message': 'Usuário já existe.'}, status=409)

    try:
        created = user_manager.create_user(
            username=username,
            password=password,
            name=name,
            position=position,
            must_change_password=True,
        )
        payload = {'success': True, 'message': 'Usuário criado com sucesso.', 'user': created}
        # Só o SUPERADMIN recebe a senha de volta
        if is_superadmin:
            payload['password'] = password
        return JsonResponse(payload)
    except ValueError as ve:
        return JsonResponse({'success': False, 'message': str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao criar usuário: {str(e)}'}, status=500)


@csrf_exempt
@require_POST
def update_user_view(request):
    """
    Atualiza dados do usuário da plataforma. Apenas Administrador pode editar.
    Aceita JSON com: username (obrigatório), name (opcional), position (opcional),
    new_password (opcional), old_password (opcional se exigir confirmação).
    """
    if not request.session.get('user_authenticated'):
        return JsonResponse({'success': False, 'message': 'Usuário não autenticado.'}, status=403)

    current_user = request.session.get('user', {})
    if not _is_admin(current_user):
        return JsonResponse({'success': False, 'message': 'Apenas Administrador pode editar usuários.'}, status=403)

    try:
        import json as _json
        data = _json.loads(request.body.decode('utf-8'))
    except Exception:
        data = {
            'username': request.POST.get('username'),
            'name': request.POST.get('name'),
            'position': request.POST.get('position'),
            'new_password': request.POST.get('new_password'),
            'old_password': request.POST.get('old_password'),
        }

    username = (data.get('username') or '').strip()
    if not username:
        return JsonResponse({'success': False, 'message': 'Username é obrigatório.'}, status=400)

    # Atualiza campos básicos
    name = data.get('name')
    position = data.get('position')
    updated_user = None
    if name or position:
        updated_user = user_manager.update_user(username, **{k: v for k, v in [('name', name), ('position', position)] if v})
        if not updated_user:
            return JsonResponse({'success': False, 'message': 'Usuário não encontrado para atualização.'}, status=404)

    # Altera senha se fornecida (somente SUPERADMIN)
    new_password = (data.get('new_password') or '').strip()
    if new_password:
        if not _is_superadmin(current_user):
            return JsonResponse({'success': False, 'message': 'Somente o SUPERADMIN pode alterar senha.'}, status=403)
        force_user_reset = bool(data.get('force_user_reset', True))
        if not user_manager.set_password_admin(username, new_password, force_user_reset=force_user_reset):
            return JsonResponse({'success': False, 'message': 'Usuário não encontrado para troca de senha.'}, status=404)

    # Retorna usuário atualizado
    if not updated_user:
        updated_user = user_manager.get_user_by_username(username)

    return JsonResponse({'success': True, 'message': 'Usuário atualizado com sucesso.', 'user': updated_user})


@csrf_protect
@require_http_methods(["POST"])
def user_password_view(request):
    """Retorna a senha atual de um usuário (apenas SUPERADMIN)."""
    if not request.session.get('user_authenticated'):
        return JsonResponse({'success': False, 'message': 'Usuário não autenticado.'}, status=403)

    current_user = request.session.get('user', {}) or {}
    if not _is_superadmin(current_user):
        return JsonResponse({'success': False, 'message': 'Somente o SUPERADMIN pode ver senhas.'}, status=403)

    username = (request.POST.get('username') or '').strip()
    if not username:
        try:
            import json as _json
            data = _json.loads(request.body.decode('utf-8'))
            username = (data.get('username') or '').strip()
        except Exception:
            username = ''

    if not username:
        return JsonResponse({'success': False, 'message': 'Username é obrigatório.'}, status=400)

    pwd = user_manager.get_user_password_for_superadmin(username)
    if pwd is None:
        return JsonResponse({'success': False, 'message': 'Usuário não encontrado.'}, status=404)
    return JsonResponse({'success': True, 'username': username, 'password': pwd})
