# 🚀 GUIA DE CORREÇÃO - Erro iOS no Easypanel

## ❌ Problema
Clientes com dispositivos iOS recebem o erro `ERR_TUNNEL_CONNECTION_FAILED` ao tentar acessar a plataforma.

## ✅ Solução Implementada

Foram adicionadas configurações de segurança HTTPS necessárias para compatibilidade com iOS no arquivo `settings.py`:

1. **SECURE_PROXY_SSL_HEADER** - Detecta HTTPS através do proxy Nginx do Easypanel
2. **SECURE_SSL_REDIRECT** - Força redirecionamento para HTTPS em produção
3. **SESSION_COOKIE_SECURE** - Cookies de sessão seguros
4. **CSRF_COOKIE_SECURE** - Tokens CSRF seguros
5. **HSTS Headers** - Força HTTPS por 1 ano

## 📋 Passos para Deploy no Easypanel

### 1. Configurar Variáveis de Ambiente no Easypanel

Acesse seu projeto no Easypanel e vá em **Environment Variables**. Configure:

```
DEBUG=False
SECRET_KEY=sua-chave-secreta-muito-forte-aqui
```

**⚠️ IMPORTANTE**: Gere uma nova SECRET_KEY para produção! Use:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2. Fazer Commit e Push das Alterações

```bash
git add .
git commit -m "fix: Adiciona configurações HTTPS para compatibilidade iOS"
git push origin main
```

### 3. Fazer Rebuild no Easypanel

1. Acesse seu projeto no Easypanel
2. Clique em **Deploy** ou **Rebuild**
3. Aguarde o build completar

### 4. Verificar o Certificado SSL

Certifique-se de que:
- O domínio `plataformavaccine.z5ydgz.easypanel.host` tem certificado SSL válido
- O certificado está ativo e não expirado
- O Easypanel está configurado para HTTPS

### 5. Testar no iOS

Após o deploy, teste em um dispositivo iOS:
- Use Safari ou Chrome no iOS
- Acesse: `https://plataformavaccine.z5ydgz.easypanel.host`
- Verifique se carrega corretamente

## 🔍 Troubleshooting

### Se ainda der erro:

1. **Verificar logs do Django**:
   - No Easypanel, vá em **Logs** do serviço
   - Procure por erros de SSL ou CSRF

2. **Limpar cache do navegador iOS**:
   - Settings > Safari > Clear History and Website Data

3. **Verificar CORS**:
   - Se usar API externa, pode precisar configurar CORS

4. **Certificado SSL**:
   - Confirme que o Easypanel renovou o certificado Let's Encrypt
   - Verifique em: https://www.ssllabs.com/ssltest/

## 📝 Notas Importantes

- As configurações de segurança **só são aplicadas quando DEBUG=False**
- Em desenvolvimento local (DEBUG=True), continua funcionando normalmente
- iOS é mais rigoroso com segurança SSL que Android/Desktop
- Nunca use `DEBUG=True` em produção

## ✨ Configurações Adicionadas

As seguintes configurações foram adicionadas ao `settings.py`:

```python
# Proxy SSL Header (Easypanel usa Nginx)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Segurança HTTPS (apenas em produção)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
```

## 🆘 Suporte

Se o problema persistir após seguir todos os passos:
1. Verifique os logs do Easypanel
2. Teste em diferentes dispositivos iOS
3. Verifique se há firewall ou VPN bloqueando a conexão
