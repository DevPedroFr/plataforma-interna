# 💉 Plataforma JM - Sistema de Gestão para Clínica de Vacinação

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Django](https://img.shields.io/badge/Django-4.x-green.svg)
![Celery](https://img.shields.io/badge/Celery-5.x-brightgreen.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**Plataforma integrada de gestão para clínicas de vacinação com chatbot WhatsApp, integração com sistemas legados e automação de processos.**

</div>

---

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Funcionalidades](#-funcionalidades)
- [Arquitetura](#-arquitetura)
- [Tecnologias](#-tecnologias)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Configuração](#%EF%B8%8F-configuração)
- [Uso](#-uso)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [API Endpoints](#-api-endpoints)
- [Contribuição](#-contribuição)

---

## 🎯 Sobre o Projeto

A **Plataforma JM** é um sistema de gestão integrada desenvolvido para clínicas de vacinação que resolve o problema de **fragmentação operacional** ao:

- ✅ **Automatizar atendimento ao cliente** via WhatsApp com Inteligência Artificial (Google Gemini)
- ✅ **Centralizar gestão de agendamentos** de vacinação
- ✅ **Sincronizar dados** com sistemas externos via web scraping
- ✅ **Capturar leads/cadastros** automaticamente via Google Forms
- ✅ **Gerenciar estoque** de vacinas em tempo real
- ✅ **Fornecer dashboard operacional** unificado para equipe interna

---

## ✨ Funcionalidades

### 🤖 Chatbot WhatsApp Inteligente
- Processamento de linguagem natural com Google Gemini
- Fluxo conversacional para agendamento de vacinas
- Cadastro automático de novos pacientes
- Detecção de intenções e encaminhamento para atendimento humano

### 📅 Gestão de Agendamentos
- Calendário visual interativo
- CRUD completo de agendamentos
- Sincronização com sistema externo (GoC Franquias)
- Visualização por dia/semana/mês

### 📦 Controle de Estoque
- Monitoramento de níveis de estoque
- Alertas de estoque baixo
- Sincronização automática com sistema matriz

### 👥 Gestão de Pacientes
- Cadastro via chatbot ou manual
- Histórico de vacinação
- Integração com Google Forms para captação de leads

### 📊 Dashboard Operacional
- Métricas em tempo real
- Vacinas aplicadas
- Pacientes cadastrados
- Próximos agendamentos
- Notificações de atendimento pendente

---

## 🏗 Arquitetura

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   WhatsApp      │────▶│     WAHA        │────▶│   Django App    │
│   (Cliente)     │     │   (API HTTP)    │     │   (Backend)     │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
┌─────────────────┐     ┌─────────────────┐              │
│  Google Forms   │────▶│  Celery Task    │──────────────┤
│   (Captação)    │     │  (Agendado)     │              │
└─────────────────┘     └─────────────────┘              │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Sistema GoC    │◀───▶│  Web Scraping   │◀────│    Database     │
│   (Legado)      │     │   (Selenium)    │     │    (SQLite)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## 🛠 Tecnologias

| Camada | Tecnologia |
|--------|------------|
| **Backend** | Django 4.x, Python 3.10+ |
| **Banco de Dados** | SQLite (dev) / PostgreSQL (prod) |
| **Filas/Tarefas** | Celery + Redis |
| **IA/NLP** | Google Gemini API |
| **WhatsApp** | WAHA (WhatsApp HTTP API) |
| **Web Scraping** | Selenium WebDriver |
| **Google APIs** | Sheets API v4 |
| **Frontend** | HTML5, CSS3, JavaScript, Font Awesome |

---

## 📦 Pré-requisitos

- Docker e Docker Compose
- Conta Google Cloud (para Gemini API e Sheets API)

---

## 🚀 Instalação e Execução

```bash
# 1. Clone o repositório
git clone https://github.com/DevPedroFr/plataforma-jm-novo.git
cd plataforma-jm-novo

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas credenciais

# 3. Suba todos os serviços
docker-compose up -d

# 4. Veja os logs (opcional)
docker-compose logs -f

# 5. Para parar
docker-compose down

# 6. Rebuild (após alterações no código)
docker-compose up -d --build
```

### 📋 Serviços Iniciados

| Serviço | URL | Função |
|---------|-----|--------|
| **Redis** | - | Broker de mensagens |
| **Django** | http://localhost:8000 | Aplicação web |
| **Celery Worker** | - | Executa tarefas em background |
| **Celery Beat** | - | Agenda sincronização a cada 1 min |
| **WAHA** | http://localhost:3000 | API WhatsApp (chatbot) |

### 🔧 Comandos Úteis

```bash
# Ver status dos containers
docker-compose ps

# Ver logs de um serviço específico
docker-compose logs -f celery-worker
docker-compose logs -f web

# Executar comando dentro do container
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# Reiniciar um serviço
docker-compose restart celery-worker
```

---

## ⚙️ Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto (ou copie de `.env.example`):

```env
# Django
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True

# Celery/Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Google Sheets/Forms (OBRIGATÓRIO para sincronização)
GOOGLE_SERVICE_ACCOUNT_FILE=vaccinecare-478508-d91d0618f96c.json
GOOGLE_SHEET_ID=seu-sheet-id
GOOGLE_SHEET_NAME=Respostas ao formulário 1

# Sistema Matriz GoC (OBRIGATÓRIO para registro automático)
MATRIX_SYSTEM_URL=https://aruja.gocfranquias.com.br
MATRIX_SYSTEM_USERNAME=seu_usuario
MATRIX_SYSTEM_PASSWORD=sua_senha

# WAHA (WhatsApp) - Opcional
WAHA_URL=http://localhost:3000
WAHA_SESSION=default

# Gemini API - Opcional (para chatbot)
GEMINI_API_KEY=sua-api-key-gemini
```

---

## 🔄 Sincronização Automática

O sistema sincroniza automaticamente os dados do Google Forms com o sistema legado (GoC Franquias) **a cada 5 minutos**.

### Como funciona:

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUXO DE SINCRONIZAÇÃO                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ⏰ Celery Beat (a cada 1 min)                                  │
│       │                                                         │
│       ▼                                                         │
│  📋 Coleta respostas do Google Forms                            │
│       │                                                         │
│       ▼                                                         │
│  🔍 Verifica duplicatas (por CPF)                               │
│       │                                                         │
│       ▼                                                         │
│  🔐 Faz login no sistema GoC Franquias                          │
│       │                                                         │
│       ▼                                                         │
│  📝 Preenche formulário de cadastro automaticamente             │
│       │                                                         │
│       ▼                                                         │
│  ✅ Registra resultado no banco de dados                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Verificar status da sincronização:

```bash
# Ver logs do Celery Worker
docker-compose logs -f celery-worker

# Ou se usando script
tail -f logs/celery_worker.log
```

### Endpoints de monitoramento:

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/scraping/sync-google-forms/` | Disparar sincronização manual |
| `GET` | `/scraping/sync-status/` | Status da última sincronização |
| `GET` | `/scraping/processed-patients/` | Lista pacientes processados |

---

## 📖 Uso

### URLs Principais

| URL | Descrição |
|-----|-----------|
| `/` | Dashboard Principal |
| `/admin/` | Painel Administrativo Django |
| `/calendar/` | Calendário de Agendamentos |
| `/chatbot/webhook/whatsapp/` | Webhook para WAHA |
| `/scraping/stock-data/` | Dados de Estoque (JSON interno) |
| `/scraping/sync-calendar/` | Sincronizar Calendário |

### Fluxo do Chatbot

1. Cliente envia mensagem no WhatsApp
2. WAHA encaminha para o webhook
3. Gemini processa a intenção
4. Sistema executa ação (agendamento, cadastro, FAQ)
5. Resposta enviada de volta ao cliente

---

## 📁 Estrutura do Projeto

```
plataforma-jm-novo/
├── chatbot_whatsapp/          # Módulo do chatbot
│   ├── handlers/              # Processadores de mensagem
│   ├── services/              # Serviços (Gemini, WAHA)
│   └── views.py               # Webhook endpoint
│
├── core/                      # Módulo principal
│   ├── models.py              # User, Vaccine, Appointment, ChatMessage
│   ├── views.py               # Dashboard, CRUD de agendamentos
│   ├── tasks.py               # Celery tasks (deprecado)
│   └── google_forms_tasks.py  # Task principal de sincronização
│
├── web_scraping/              # Módulo de integração
│   ├── services/              # Scrapers
│   │   ├── base_scraper.py
│   │   ├── calendar_scraper.py
│   │   ├── patient_registration_scraper.py
│   │   ├── stock_scraper.py
│   │   └── users_scraper.py
│   ├── models.py              # ProcessedGoogleFormSubmission, etc.
│   └── utils/                 # Browser manager
│
├── vacination_system/         # Configurações Django
│   ├── settings.py
│   ├── urls.py
│   └── celery.py              # Configuração do Celery Beat
│
├── templates/                 # Templates HTML
├── static/                    # Arquivos estáticos (CSS, JS)
├── forms_responses/           # Respostas do Google Forms (JSON)
├── logs/                      # Logs dos serviços Celery
│
├── docker-compose.yml         # Orquestração de containers
├── Dockerfile                 # Imagem Docker da aplicação
├── .env.example               # Exemplo de variáveis de ambiente
├── manage.py
├── requirements.txt
└── README.md
```

---

## 🔌 API Endpoints

### Agendamentos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/calendar-appointments/` | Lista agendamentos |
| `POST` | `/appointments/create/` | Criar agendamento |
| `GET` | `/appointments/<id>/` | Detalhes do agendamento |
| `POST` | `/appointments/<id>/update/` | Atualizar agendamento |
| `POST` | `/appointments/<id>/delete/` | Deletar agendamento |
| `GET` | `/appointments/by-date/?date=YYYY-MM-DD` | Agendamentos por data |

### Estoque (JSON interno)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/scraping/stock-data/` | Retorna os itens do arquivo JSON interno |

O painel lê o arquivo `data/vaccines.json` por padrão. Para apontar outro arquivo, defina `INTERNAL_STOCK_JSON` em `vacination_system/settings.py`.

Formato do JSON:

```
{
    "last_updated": "2026-01-18T00:00:00Z",
    "items": [
        {
            "name": "DTPa + IPV - Refortrix IPV",
            "laboratory": "GSK",
            "purchase_price": 117.00,
            "sale_price": 215.00,
            "current_stock": 20,
            "available_stock": 20,
            "min_stock": 2
        }
    ]
}
```

Para atualizar o painel:
- Edite `data/vaccines.json`
- No painel de Estoque, clique em “Atualizar Estoque”

### Sincronização

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/sync-calendar/` | Sincronizar calendário |
| `POST` | `/scraping/sync-stock/` | Sincronizar estoque |
| `POST` | `/scraping/sync-recent-users/` | Sincronizar usuários |

### Chatbot

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/chatbot/webhook/whatsapp/` | Webhook WAHA |
| `GET` | `/chatbot/dashboard/` | Dashboard do chatbot |

---

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👨‍💻 Autor

Desenvolvido por **Pedro França** - [@DevPedroFr](https://github.com/DevPedroFr)

---