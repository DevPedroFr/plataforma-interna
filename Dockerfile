# Imagem base Python
FROM python:3.11-slim

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema, Google Chrome e ChromeDriver
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub > /tmp/google.pub \
    && gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg /tmp/google.pub \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/* /tmp/google.pub

# Instalar ChromeDriver compatível com a versão do Chrome instalada
RUN CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+') \
    && CHROMEDRIVER_MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d. -f1) \
    && CHROMEDRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROMEDRIVER_MAJOR_VERSION}") \
    && wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip" -O /tmp/chromedriver.zip \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf /tmp/chromedriver* \
    && chromedriver --version

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Copiar e dar permissão ao script de entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Coletar arquivos estáticos
RUN python manage.py collectstatic --noinput || true

# Porta da aplicação
EXPOSE 8000

# Comando padrão
CMD ["/entrypoint.sh"]
