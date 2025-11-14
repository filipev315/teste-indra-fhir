#!/bin/bash

echo "=========================================="
echo "Executando Pipeline ETL FHIR"
echo "=========================================="
echo ""

# Verifica se o servidor FHIR está rodando
if ! curl -s http://localhost:8080/fhir/metadata > /dev/null 2>&1; then
    echo "❌ Servidor HAPI FHIR não está acessível."
    echo "   Por favor, execute ./start.sh primeiro."
    exit 1
fi

echo "✅ Servidor HAPI FHIR está acessível"
echo ""

# Verifica se o arquivo CSV existe
if [ ! -f "data/patients.csv" ]; then
    echo "❌ Arquivo data/patients.csv não encontrado."
    exit 1
fi

echo "✅ Arquivo de dados encontrado"
echo ""

# Opção 1: Executar com Python local (se disponível)
if command -v python3 &> /dev/null; then
    echo "🐍 Executando ETL com Python local..."
    echo ""
    
    # Instala dependências se necessário
    pip3 install -q -r requirements.txt
    
    # Executa o script
    python3 scripts/etl_pipeline.py
    
# Opção 2: Executar com Docker
else
    echo "🐳 Python não encontrado localmente. Executando com Docker..."
    echo ""
    
    # Constrói a imagem se necessário
    if ! docker images | grep -q fhir-etl; then
        echo "Construindo imagem Docker..."
        docker build -t fhir-etl .
        echo ""
    fi
    
    # Executa o container
    docker run --rm \
        --network fhir-test-indra_fhir-network \
        -v $(pwd)/data:/app/data \
        -v $(pwd)/scripts:/app/scripts \
        -e FHIR_SERVER_URL=http://hapi-fhir:8080/fhir \
        fhir-etl
fi

echo ""
echo "=========================================="
echo "Pipeline ETL concluído!"
echo "=========================================="
echo ""
echo "Para verificar os dados carregados, acesse:"
echo "  http://localhost:8080/fhir/Patient"
echo "  http://localhost:8080/fhir/Condition"
echo ""
