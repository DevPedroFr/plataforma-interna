import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='sua-chave-secreta-aqui-desenvolva-2024')

DEBUG = config('DEBUG', default=True, cast=bool)

# =========================================================================
# AUTENTICAÇÃO (users.json)
# =========================================================================
# Usuário "dono" (único com permissão para ver/resetar senhas de outros).
SUPERADMIN_USERNAME = config('SUPERADMIN_USERNAME', default='admin')

# Senha padrão para usuários criados (se não informada ou se o criador não for SUPERADMIN)
DEFAULT_USER_PASSWORD = config('DEFAULT_USER_PASSWORD', default='123456')

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = [
    'https://prettied-unsensitively-kerstin.ngrok-free.dev',
]

# vacination_system/settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'user_auth',
    'core',
    'web_scraping',
    'chatbot_whatsapp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'user_auth.middleware.AuthenticationMiddleware',
]

ROOT_URLCONF = 'vacination_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'vacination_system.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# ============================================================================
# CONFIGURAÇÕES DE SESSÃO E SEGURANÇA
# ============================================================================
# Timeout de sessão: 1 hora (3600 segundos)
SESSION_COOKIE_AGE = 3600
# Não renovar a sessão a cada request - força logout após 1 hora
SESSION_SAVE_EVERY_REQUEST = False
# Expirar sessão ao fechar o navegador
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
# Nome do cookie de sessão
SESSION_COOKIE_NAME = 'vaccinecare_sessionid'
# Segurança do cookie
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================================
# INTEGRAÇÕES EXTERNAS
# ============================================================================
# N8N (Automação)
N8N_WEBHOOK_URL = config('N8N_WEBHOOK_URL', default='')
N8N_API_KEY = config('N8N_API_KEY', default='')

# Sistema Matriz GoC Franquias (Web Scraping)
# IMPORTANTE: Configure estas variáveis no arquivo .env
MATRIX_SYSTEM_URL = config('MATRIX_SYSTEM_URL', default='https://aruja.gocfranquias.com.br')
MATRIX_SYSTEM_USERNAME = config('MATRIX_SYSTEM_USERNAME', default='')  # Obrigatório para sync
MATRIX_SYSTEM_PASSWORD = config('MATRIX_SYSTEM_PASSWORD', default='')  # Obrigatório para sync

# Validação das credenciais do sistema matriz (apenas warning, não bloqueia)
if not MATRIX_SYSTEM_USERNAME or not MATRIX_SYSTEM_PASSWORD:
    import warnings
    warnings.warn(
        "⚠️ Credenciais do Sistema Matriz não configuradas!\n"
        "   O registro automático de pacientes no sistema legado não funcionará.\n"
        "   Configure MATRIX_SYSTEM_USERNAME e MATRIX_SYSTEM_PASSWORD no arquivo .env"
    )
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')

WAHA_URL = "http://localhost:3000"  # URL do seu WAHA
WAHA_SESSION = "default"

# ============================================================================
# CELERY CONFIGURATION
# ============================================================================
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutos
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# ============================================================================
# GOOGLE FORMS / SHEETS CONFIGURATION
# ============================================================================
# Caminhos e IDs para coleta de dados do Google Forms/Sheets
GOOGLE_SERVICE_ACCOUNT_FILE = config('GOOGLE_SERVICE_ACCOUNT_FILE', default='vaccinecare-478508-d91d0618f96c.json')
GOOGLE_SHEET_ID = config('GOOGLE_SHEET_ID', default='16LDp9i6FKn8R2fNOEJt_wyCm-RNOqfxfeew_NvZxGoQ')
GOOGLE_SHEET_NAME = config('GOOGLE_SHEET_NAME', default='Respostas ao formulário 1')
FORMS_RESPONSES_DIR = config('FORMS_RESPONSES_DIR', default='forms_responses')

# Validação do arquivo de credenciais Google (apenas warning, não bloqueia)
_google_creds_path = BASE_DIR / GOOGLE_SERVICE_ACCOUNT_FILE if GOOGLE_SERVICE_ACCOUNT_FILE else None
if _google_creds_path and not _google_creds_path.exists():
    import warnings
    warnings.warn(
        f"⚠️ Arquivo de credenciais Google não encontrado: {GOOGLE_SERVICE_ACCOUNT_FILE}\n"
        f"   A sincronização com Google Forms não funcionará.\n"
        f"   Esperado em: {_google_creds_path}"
    )

ALLOWED_HOSTS = ['plataforma-plataforma-jm.z5ydgz.easypanel.host']

# Configurações do scraper de estoque
STOCK_SCRAPER_MAX_PAGES = 100  # Número máximo de páginas a processar
STOCK_SCRAPER_AJAX_WAIT_SECONDS = 2.0  # Tempo de espera entre páginas

# Banco interno de estoque (JSON)
# Se não definido em tempo de execução, a view usa BASE_DIR/data/vaccines.json
INTERNAL_STOCK_JSON = str(BASE_DIR / 'data' / 'vaccines.json')