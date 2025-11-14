# Teste Técnico 

<div align="center">

![FHIR](https://img.shields.io/badge/FHIR-R4-blue)
![HAPI](https://img.shields.io/badge/HAPI-Latest-green)
![Python](https://img.shields.io/badge/Python-3.11-yellow)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue)
![RNDS](https://img.shields.io/badge/RNDS-BRIndividuo-red)

### Solução de Interoperabilidade em Saúde para SES-GO

</div>

---

## 🎯 Sobre o Projeto

Implementação completa de servidor FHIR R4 com pipeline ETL para a **Secretaria de Estado da Saúde de Goiás**, utilizando o profile **BRIndividuo** da **Rede Nacional de Dados em Saúde (RNDS)**.

### ✨ Destaques

- ✅ Servidor HAPI FHIR configurado com PostgreSQL
- ✅ Profile BRIndividuo-1.0 da RNDS implementado
- ✅ Pipeline ETL com PySpark
- ✅ Suporte a identificadores brasileiros (CPF/CNS)
- ✅ Mapeamento automático de condições clínicas
- ✅ Docker Compose para fácil implantação
- ✅ Scripts de automação inclusos

---

## 🚀 Início Rápido

### Pré-requisitos

- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB RAM
- 10GB disco

### Instalação

```bash
# 1. Clone o repositório
git clone [URL_DO_REPOSITORIO]
cd fhir-test-indra

# 2. Torne os scripts executáveis
chmod +x *.sh

# 3. Inicie o ambiente (aguarda ~2 minutos)
./start.sh

# 4. Execute o pipeline ETL
./run-etl.sh

# 5. Valide os dados carregados
./validate.sh
```

### Acesso aos Serviços

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| HAPI FHIR | http://localhost:8080 | - |
| API FHIR | http://localhost:8080/fhir | - |
| pgAdmin | http://localhost:5050 | admin@admin.com / admin |
| PostgreSQL | localhost:5432 | admin / admin |

---

## 📁 Estrutura do Projeto

```
fhir-test-indra/
├── docker-compose.yml      # Orquestração dos serviços
├── Dockerfile              # Container para ETL
├── requirements.txt        # Dependências Python
├── start.sh               # Script de inicialização
├── run-etl.sh             # Script para executar ETL
├── validate.sh            # Script de validação
│
├── config/                # Configurações
├── data/                  # Dados de entrada
│   └── patients.csv       # CSV com dados dos pacientes
│
├── scripts/               # Scripts Python
│   └── etl_pipeline.py    # Pipeline ETL principal
│
└── docs/                  # Documentação
    └── README.md          # Documentação completa
```

---

## 🏥 Profile BRIndividuo - RNDS

Este projeto implementa o profile **BRIndividuo-1.0** da Rede Nacional de Dados em Saúde:

```
Profile: http://www.saude.gov.br/fhir/r4/StructureDefinition/BRIndividuo-1.0
Base: Patient (FHIR R4)
```

### Identificadores Suportados

- **CPF** - Cadastro de Pessoas Físicas (obrigatório)
- **CNS** - Cartão Nacional de Saúde (opcional)

### Extensões Brasileiras

- Endereço brasileiro completo (CEP, UF, município)
- Nome da mãe (extensão)
- Dados demográficos conforme padrão nacional

### Exemplo de Resource

```json
{
  "resourceType": "Patient",
  "meta": {
    "profile": ["http://www.saude.gov.br/fhir/r4/StructureDefinition/BRIndividuo-1.0"]
  },
  "identifier": [
    {
      "type": {
        "coding": [{
          "system": "http://www.saude.gov.br/fhir/r4/CodeSystem/BRTipoDocumentoIndividuo",
          "code": "CPF"
        }]
      },
      "value": "12345678901"
    }
  ],
  "name": [{"family": "Silva", "given": ["João"]}],
  "gender": "male",
  "birthDate": "1985-03-15",
  "address": [{
    "line": ["Rua das Flores, 123"],
    "city": "Goiânia",
    "state": "GO",
    "postalCode": "74000-000",
    "country": "BR"
  }]
}
```

---

## 🔄 Pipeline ETL

### Fluxo de Dados

```
CSV → PySpark → Transform → FHIR Resources → HAPI Server
```

### Mapeamentos

| Campo CSV | FHIR Resource | Campo FHIR |
|-----------|---------------|------------|
| Nome | Patient | name (family + given) |
| CPF | Patient | identifier (CPF) |
| Gênero | Patient | gender |
| Data de Nascimento | Patient | birthDate |
| Telefone | Patient | telecom |
| Observação | Condition | code.text |

### Processamento de Observações

Quando a coluna `observacao` contém dados clínicos, o pipeline automaticamente:

1. Cria o resource `Patient`
2. Cria um resource `Condition` vinculado
3. Estabelece a referência entre eles

---

## 🛠️ Tecnologias

### Core Stack

- **HAPI FHIR** - Servidor FHIR R4 Open Source
- **PostgreSQL 15** - Banco de dados relacional
- **Python 3.11** - Linguagem de programação
- **PySpark 3.5** - Processamento de dados
- **Docker** - Containerização
- **Docker Compose** - Orquestração

### Padrões e Profiles

- **HL7 FHIR R4** - Padrão de interoperabilidade
- **BRIndividuo-1.0** - Profile da RNDS
- **REST API** - Interface de comunicação

---

## 📊 Queries Úteis

### Buscar todos os pacientes
```bash
curl http://localhost:8080/fhir/Patient
```

### Buscar por CPF
```bash
curl 'http://localhost:8080/fhir/Patient?identifier=12345678901'
```

### Buscar por nome
```bash
curl 'http://localhost:8080/fhir/Patient?name=João'
```

### Buscar por cidade
```bash
curl 'http://localhost:8080/fhir/Patient?address-city=Goiânia'
```

### Buscar conditions de um paciente
```bash
curl 'http://localhost:8080/fhir/Condition?subject=Patient/[id]'
```

---

## 📖 Documentação Completa

A documentação técnica completa está disponível em:

**[docs/README.md](docs/README.md)**

Inclui:
- Arquitetura detalhada
- Processo de configuração passo a passo
- Explicação do pipeline ETL
- Guia para apresentação técnica
- Próximos passos e melhorias

---

## 🎤 Apresentação Técnica

### Estrutura (30 minutos)

1. **Introdução** (3 min) - Visão geral e contexto
2. **Arquitetura** (7 min) - Componentes e decisões técnicas
3. **FHIR & RNDS** (10 min) - Demonstração ao vivo
4. **Pipeline ETL** (7 min) - Fluxo de dados e execução
5. **Q&A** (3 min) - Discussão e próximos passos

---

## 👨‍💻 Autor

**Filipe Valentino**  
FHIR Architect 
Interoperability Engineer - SPMS Portugal

- 🎓 3 anos de experiência com HL7 FHIR
- 🏥 Especialista em interoperabilidade em saúde
- 🇧🇷 Foco em implementações brasileiras (RNDS)
- 🇵🇹 Projetos nacionais em Portugal (SNS)

**Contato:** filipevalentino315@gmail.com

---

## 📝 Entregáveis

- ✅ Docker Compose funcional
- ✅ Servidor HAPI FHIR configurado
- ✅ Pipeline ETL com PySpark
- ✅ Profile BRIndividuo implementado
- ✅ Scripts de automação
- ✅ Documentação completa
- ✅ Exemplos de queries
- ✅ Repositório GitHub público

---

## 🔗 Referências

- [HAPI FHIR](https://hapifhir.io/)
- [HL7 FHIR R4](https://hl7.org/fhir/R4/)
- [RNDS](https://rnds.saude.gov.br/)
- [Profile BRIndividuo](https://simplifier.net/redenacionaldedadosemsaude/brindividuo)

---

<div align="center">

**Desenvolvido para o Teste Técnico Indra Group - SES-GO**  
Data: 14/11/2025

</div>
