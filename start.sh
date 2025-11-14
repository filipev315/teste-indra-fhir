#!/bin/bash

echo "=========================================="
echo "Iniciando Ambiente FHIR - Teste Indra"
echo "=========================================="
echo ""

# Verifica se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado. Por favor, instale o Docker primeiro."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose não está instalado. Por favor, instale o Docker Compose primeiro."
    exit 1
fi

echo "✅ Docker e Docker Compose detectados"
echo ""

# Para containers existentes
echo "🛑 Parando containers existentes..."
docker-compose down

echo ""
echo "🚀 Iniciando containers..."
echo ""

# Inicia os containers
docker-compose up -d

echo ""
echo "⏳ Aguardando serviços ficarem prontos..."
echo ""

# Aguarda o HAPI FHIR ficar pronto
echo "Aguardando HAPI FHIR inicializar (isso pode levar 1-2 minutos)..."
attempt=0
max_attempts=40

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8080/fhir/metadata > /dev/null 2>&1; then
        echo "✅ HAPI FHIR está pronto!"
        break
    fi
    attempt=$((attempt + 1))
    echo -n "."
    sleep 3
done

if [ $attempt -eq $max_attempts ]; then
    echo ""
    echo "⚠️  HAPI FHIR demorou mais que o esperado. Verifique os logs:"
    echo "   docker-compose logs hapi-fhir"
    exit 1
fi

echo ""
echo ""
echo "=========================================="
echo "✅ Ambiente iniciado com sucesso!"
echo "=========================================="
echo ""
echo "Serviços disponíveis:"
echo ""
echo "  🏥 HAPI FHIR Server:"
echo "     http://localhost:8080/fhir"
echo ""
echo "  📊 Interface Web HAPI:"
echo "     http://localhost:8080"
echo ""
echo "  🗄️  pgAdmin (gerenciamento do banco):"
echo "     http://localhost:5050"
echo "     Email: admin@admin.com"
echo "     Senha: admin"
echo ""
echo "  🐘 PostgreSQL:"
echo "     Host: localhost"
echo "     Port: 5432"
echo "     Database: hapi"
echo "     User: admin"
echo "     Password: admin"
echo ""
echo "=========================================="
echo ""
echo "Para executar o ETL, use:"
echo "  ./run-etl.sh"
echo ""
echo "Para parar o ambiente:"
echo "  docker-compose down"
echo ""
echo "Para visualizar logs:"
echo "  docker-compose logs -f hapi-fhir"
echo ""
echo "=========================================="
