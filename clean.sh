#!/bin/bash

echo "=========================================="
echo "Limpeza do Ambiente FHIR"
echo "=========================================="
echo ""

read -p "Deseja remover TODOS os containers e volumes? (s/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]
then
    echo "Operação cancelada."
    exit 1
fi

echo ""
echo "🛑 Parando containers..."
docker-compose down

echo ""
echo "🗑️  Removendo volumes..."
docker-compose down -v

echo ""
echo "🧹 Limpando imagens não utilizadas..."
docker image prune -f

echo ""
echo "✅ Limpeza concluída!"
echo ""
echo "Para reiniciar o ambiente, execute:"
echo "  ./start.sh"
echo ""
