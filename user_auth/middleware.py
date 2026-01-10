"""
Middleware de autenticação que redireciona para login se necessário
"""

from django.shortcuts import redirect
from django.conf import settings


class AuthenticationMiddleware:
    """
    Middleware que protege as rotas exigindo autenticação.
    Rotas públicas (login, logout) são isentas.
    """
    
    # Rotas que não requerem autenticação
    PUBLIC_URLS = [
        '/auth/login/',
        '/auth/logout/',
        '/auth/change-password/',
        '/admin/',  # O Django admin cuida da própria autenticação
    ]

    # URLs que podem ser acessadas mesmo quando o usuário precisa trocar a senha
    PASSWORD_CHANGE_ALLOWED_URLS = [
        '/auth/logout/',
        '/auth/change-password/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Verifica se a URL atual é pública
        is_public = any(request.path.startswith(url) for url in self.PUBLIC_URLS)
        
        # Se não é pública e não está autenticado, redireciona para login
        if not is_public and not request.session.get('user_authenticated'):
            return redirect('auth:login')

        # Se está autenticado mas precisa trocar senha, força fluxo
        if request.session.get('user_authenticated'):
            user = request.session.get('user', {}) or {}
            must_change_password = bool(user.get('must_change_password'))
            if must_change_password:
                is_allowed = any(request.path.startswith(url) for url in self.PASSWORD_CHANGE_ALLOWED_URLS)
                is_asset = request.path.startswith('/static/')
                if not is_allowed and not is_asset:
                    return redirect('auth:change_password')
        
        response = self.get_response(request)
        return response
