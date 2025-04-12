FROM python:3.9-slim-buster

WORKDIR /app

# 1. Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Copia primeiro o requirements.txt para aproveitar cache
COPY requirements.txt .

# 3. Instala dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. Copia o restante da aplicação
COPY . .

# 5. Configura variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

CMD ["python", "main.py"]