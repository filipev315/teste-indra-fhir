FROM python:3.11-slim

# Instala OpenJDK 11 (necessário para PySpark)
RUN apt-get update && \
    apt-get install -y openjdk-11-jre-headless curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Define JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

# Define diretório de trabalho
WORKDIR /app

# Copia requirements e instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia scripts e dados
COPY scripts/ ./scripts/
COPY data/ ./data/

# Comando padrão
CMD ["python", "scripts/etl_pipeline.py"]
