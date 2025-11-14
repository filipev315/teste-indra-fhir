#!/bin/bash

echo "=========================================="
echo "Validando Dados no Servidor FHIR"
echo "=========================================="
echo ""

FHIR_URL="http://localhost:8080/fhir"

# Verifica se o servidor está acessível
if ! curl -s ${FHIR_URL}/metadata > /dev/null 2>&1; then
    echo "❌ Servidor FHIR não está acessível."
    exit 1
fi

echo "✅ Servidor FHIR está acessível"
echo ""

# Busca pacientes
echo "📋 Buscando pacientes..."
PATIENT_RESPONSE=$(curl -s "${FHIR_URL}/Patient?_count=100")
PATIENT_COUNT=$(echo $PATIENT_RESPONSE | grep -o '"total":[0-9]*' | grep -o '[0-9]*')

echo "   Total de pacientes: ${PATIENT_COUNT:-0}"
echo ""

# Busca conditions
echo "🏥 Buscando conditions..."
CONDITION_RESPONSE=$(curl -s "${FHIR_URL}/Condition?_count=100")
CONDITION_COUNT=$(echo $CONDITION_RESPONSE | grep -o '"total":[0-9]*' | grep -o '[0-9]*')

echo "   Total de conditions: ${CONDITION_COUNT:-0}"
echo ""

echo "=========================================="
echo "Exemplos de queries úteis:"
echo "=========================================="
echo ""
echo "Buscar todos os pacientes:"
echo "  curl '${FHIR_URL}/Patient'"
echo ""
echo "Buscar paciente por CPF:"
echo "  curl '${FHIR_URL}/Patient?identifier=12345678901'"
echo ""
echo "Buscar paciente por nome:"
echo "  curl '${FHIR_URL}/Patient?name=João'"
echo ""
echo "Buscar conditions de um paciente:"
echo "  curl '${FHIR_URL}/Condition?subject=Patient/[id]'"
echo ""
echo "Buscar pacientes do sexo feminino:"
echo "  curl '${FHIR_URL}/Patient?gender=female'"
echo ""
echo "Interface web para visualização:"
echo "  http://localhost:8080"
echo ""
