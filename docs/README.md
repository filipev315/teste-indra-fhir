# Teste Técnico - Engenheiro de Dados FHIR
## Indra Group - Secretaria de Estado da Saúde de Goiás

**Candidato:** Filipe Valentino
**Data:** 14/11/2025  
**Contato:** filipevalentino315@gmail.com

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Parte 1 - Configuração do Servidor FHIR](#parte-1---configuração-do-servidor-fhir)
3. [Parte 2 - Pipeline ETL](#parte-2---pipeline-etl)
4. [Parte 3 - Apresentação Técnica](#parte-3---apresentação-técnica)
5. [Instruções de Uso](#instruções-de-uso)
6. [Arquitetura da Solução](#arquitetura-da-solução)
7. [Tecnologias Utilizadas](#tecnologias-utilizadas)
8. [Próximos Passos](#próximos-passos)

---

## 🎯 Visão Geral

Este projeto implementa uma solução completa de interoperabilidade em saúde utilizando o padrão HL7 FHIR R4, especificamente configurada para atender às necessidades da Secretaria de Estado da Saúde de Goiás. A solução inclui:

- **Servidor FHIR:** HAPI FHIR com PostgreSQL
- **Pipeline ETL:** PySpark com mapeamento para o profile BRIndividuo da RNDS
- **Infraestrutura:** Docker Compose para orquestração
- **Validação:** Scripts automatizados de validação e consulta

### Destaques da Implementação

✅ **Profile RNDS:** Utiliza o profile `BRIndividuo-1.0` da Rede Nacional de Dados em Saúde  
✅ **Identificadores Brasileiros:** Suporte completo para CPF e CNS  
✅ **Condições de Saúde:** Mapeamento automático de observações para resource Condition  
✅ **Endereço Brasileiro:** Implementação conforme padrão nacional (CEP, UF, município)  
✅ **Validação FHIR:** Validação automática contra o profile da RNDS

---

## 🏗️ Parte 1 - Configuração do Servidor FHIR

### Arquitetura

A solução utiliza uma arquitetura de microserviços containerizada:

```
┌─────────────────────────────────────────────┐
│           Docker Compose Network            │
│                                             │
│  ┌──────────────┐      ┌────────────────┐  │
│  │  HAPI FHIR   │◄────►│  PostgreSQL    │  │
│  │   Server     │      │   Database     │  │
│  │  (Port 8080) │      │   (Port 5432)  │  │
│  └──────────────┘      └────────────────┘  │
│         ▲                      ▲            │
│         │                      │            │
│         ▼                      ▼            │
│  ┌──────────────┐      ┌────────────────┐  │
│  │  ETL Script  │      │    pgAdmin     │  │
│  │   (Python)   │      │   (Port 5050)  │  │
│  └──────────────┘      └────────────────┘  │
└─────────────────────────────────────────────┘
```

### Componentes

#### 1. HAPI FHIR Server

**Imagem:** `hapiproject/hapi:latest`  
**Porta:** 8080  
**Versão FHIR:** R4

**Configurações principais:**
- Persistência em PostgreSQL
- Validação de recursos habilitada
- Suporte a referências externas
- CORS habilitado para integrações
- Subscription REST Hook e WebSocket
- Cache de busca otimizado

#### 2. PostgreSQL

**Imagem:** `postgres:15-alpine`  
**Porta:** 5432  
**Banco de dados:** hapi

**Configurações:**
- Volume persistente para dados
- Health check configurado
- Otimizado para operações FHIR

#### 3. pgAdmin

**Imagem:** `dpage/pgadmin4:latest`  
**Porta:** 5050

Interface web para gerenciamento do banco de dados.

### Processo de Instalação

#### Pré-requisitos

- Docker Engine 20.10 ou superior
- Docker Compose 2.0 ou superior
- 4GB RAM disponível
- 10GB espaço em disco

#### Passo a Passo

1. **Clone o repositório:**
```bash
git clone [URL_DO_REPOSITORIO]
cd fhir-test-indra
```

2. **Inicie o ambiente:**
```bash
chmod +x start.sh
./start.sh
```

3. **Aguarde a inicialização:**
   - O script aguarda automaticamente o HAPI FHIR ficar pronto
   - Tempo médio: 1-2 minutos

4. **Verifique a instalação:**
```bash
curl http://localhost:8080/fhir/metadata
```

### Configuração do HAPI FHIR

O servidor é configurado através de variáveis de ambiente no `docker-compose.yml`:

```yaml
environment:
  # Conexão com banco
  spring.datasource.url: jdbc:postgresql://postgres:5432/hapi
  
  # Versão FHIR
  hapi.fhir.fhir_version: R4
  
  # Validação
  hapi.fhir.validation.enabled: true
  hapi.fhir.validation.requests_enabled: true
  
  # Performance
  hapi.fhir.max_page_size: 200
  hapi.fhir.reuse_cached_search_results_millis: 60000
```

### Endpoints Disponíveis

| Endpoint | Descrição |
|----------|-----------|
| `http://localhost:8080` | Interface web do HAPI FHIR |
| `http://localhost:8080/fhir` | Base URL da API FHIR |
| `http://localhost:8080/fhir/metadata` | Capability Statement |
| `http://localhost:5050` | pgAdmin |

---

## 🔄 Parte 2 - Pipeline ETL

### Visão Geral do Pipeline

O pipeline ETL foi desenvolvido em Python usando PySpark e implementa:

1. **Extract:** Leitura de dados do CSV
2. **Transform:** Mapeamento para recursos FHIR com profile RNDS
3. **Load:** Envio para o servidor HAPI FHIR

### Fluxo de Dados

```
CSV File
   │
   ├─► PySpark DataFrame
   │
   ├─► Validação de Dados
   │
   ├─► Transform
   │    ├─► Patient Resource (BRIndividuo)
   │    │    ├─► CPF (identifier)
   │    │    ├─► CNS (identifier)
   │    │    ├─► Nome completo
   │    │    ├─► Dados demográficos
   │    │    └─► Endereço brasileiro
   │    │
   │    └─► Condition Resource (se aplicável)
   │         ├─► Referência ao Patient
   │         ├─► Texto da observação
   │         └─► Status e categoria
   │
   └─► Load
        └─► HAPI FHIR Server (REST API)
```

### Mapeamento para BRIndividuo

O profile `BRIndividuo-1.0` da RNDS estende o resource Patient padrão FHIR com especificidades brasileiras:

#### Identificadores

**CPF (Obrigatório):**
```json
{
  "identifier": [{
    "use": "official",
    "type": {
      "coding": [{
        "system": "http://www.saude.gov.br/fhir/r4/CodeSystem/BRTipoDocumentoIndividuo",
        "code": "CPF"
      }]
    },
    "value": "12345678901"
  }]
}
```

**CNS (Opcional):**
```json
{
  "identifier": [{
    "type": {
      "coding": [{
        "system": "http://www.saude.gov.br/fhir/r4/CodeSystem/BRTipoDocumentoIndividuo",
        "code": "CNS"
      }]
    },
    "value": "123456789012345"
  }]
}
```

#### Endereço Brasileiro

```json
{
  "address": [{
    "use": "home",
    "type": "physical",
    "line": ["Rua das Flores, 123, Apto 101"],
    "district": "Centro",
    "city": "Goiânia",
    "state": "GO",
    "postalCode": "74000-000",
    "country": "BR"
  }]
}
```

### Mapeamento de Observações

Quando a coluna `observacao` contém dados, o pipeline cria um resource `Condition`:

```json
{
  "resourceType": "Condition",
  "clinicalStatus": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
      "code": "active"
    }]
  },
  "code": {
    "text": "Hipertensão arterial sistêmica em tratamento"
  },
  "subject": {
    "reference": "Patient/[id]"
  }
}
```

### Estrutura do CSV

O arquivo `data/patients.csv` contém 50 pacientes com os seguintes campos:

```csv
Nome,CPF,Gênero,Data de Nascimento,Telefone,País de Nascimento,Observação
```

**Campos:**
- **Nome**: Nome completo do paciente
- **CPF**: CPF formatado (XXX.XXX.XXX-XX)
- **Gênero**: Masculino ou Feminino
- **Data de Nascimento**: Formato DD/MM/YYYY
- **Telefone**: Telefone formatado (XX) XXXX-XXXX
- **País de Nascimento**: País (Brasil)
- **Observação**: Condições de saúde separadas por pipe (|)
  - Exemplos: "Gestante", "Diabético", "Hipertenso", "Gestante|Diabético"

**Observações especiais:**
- Múltiplas condições são separadas por pipe (|)
- O pipeline cria um Condition resource para cada observação
- CPF é limpo automaticamente (remove pontos e hífen)
- Data é convertida para formato FHIR (YYYY-MM-DD)

### Código ETL

O script `etl_pipeline.py` implementa:

1. **Classe `FHIRETLPipeline`:** Pipeline principal
2. **Método `create_br_individuo_resource()`:** Cria Patient conforme profile RNDS
3. **Método `create_condition_resource()`:** Cria Condition para observações
4. **Método `send_to_fhir_server()`:** Envia recursos via REST API

### Execução do Pipeline

**Opção 1 - Python Local:**
```bash
./run-etl.sh
```

**Opção 2 - Docker:**
```bash
docker build -t fhir-etl .
docker run --network fhir-test-indra_fhir-network fhir-etl
```

### Validação

Após a execução, valide os dados:

```bash
./validate.sh
```

Ou manualmente:

```bash
# Listar todos os pacientes
curl http://localhost:8080/fhir/Patient

# Buscar paciente por CPF
curl 'http://localhost:8080/fhir/Patient?identifier=12345678901'

# Buscar conditions de um paciente
curl 'http://localhost:8080/fhir/Condition?subject=Patient/[id]'
```

---

## 🎤 Parte 3 - Apresentação Técnica

### Estrutura da Apresentação (30 minutos)

#### 1. Introdução (3 minutos)
- Apresentação pessoal
- Visão geral da solução
- Contexto: RNDS e interoperabilidade no SUS

#### 2. Arquitetura (7 minutos)
- Diagrama da solução
- Componentes e suas responsabilidades
- Decisões arquiteturais
- Escalabilidade e performance

#### 3. Implementação FHIR (10 minutos)
- Demonstração ao vivo do servidor HAPI
- Profile BRIndividuo da RNDS
- Exemplos de recursos criados
- Queries e validações

#### 4. Pipeline ETL (7 minutos)
- Fluxo de dados
- Mapeamentos implementados
- Tratamento de erros
- Demonstração da execução

#### 5. Q&A e Discussão (3 minutos)
- Dúvidas e esclarecimentos
- Melhorias futuras
- Integração com sistemas existentes

### Demonstrações ao Vivo

1. **Servidor FHIR em funcionamento**
   - Capability Statement
   - Interface web do HAPI

2. **Execução do ETL**
   - Logs em tempo real
   - Validação dos dados carregados

3. **Consultas FHIR**
   - Busca por CPF
   - Busca por condição
   - Busca por município

### Pontos de Destaque

- ✅ Conformidade com RNDS
- ✅ Identificadores brasileiros (CPF/CNS)
- ✅ Endereçamento conforme padrão nacional
- ✅ Mapeamento de condições clínicas
- ✅ Pipeline robusto e escalável
- ✅ Validação automática
- ✅ Documentação completa

---

## 🚀 Instruções de Uso

### Início Rápido

```bash
# 1. Tornar scripts executáveis
chmod +x *.sh

# 2. Iniciar ambiente
./start.sh

# 3. Executar ETL
./run-etl.sh

# 4. Validar dados
./validate.sh
```

### Comandos Úteis

**Ver logs do HAPI FHIR:**
```bash
docker-compose logs -f hapi-fhir
```

**Parar ambiente:**
```bash
docker-compose down
```

**Parar e remover volumes:**
```bash
docker-compose down -v
```

**Acessar banco de dados:**
```bash
docker exec -it fhir-postgres psql -U admin -d hapi
```

### Queries FHIR Úteis

**Buscar pacientes por cidade:**
```bash
curl 'http://localhost:8080/fhir/Patient?address-city=Goiânia'
```

**Buscar pacientes por estado:**
```bash
curl 'http://localhost:8080/fhir/Patient?address-state=GO'
```

**Buscar conditions ativas:**
```bash
curl 'http://localhost:8080/fhir/Condition?clinical-status=active'
```

**Buscar por nome:**
```bash
curl 'http://localhost:8080/fhir/Patient?name=João'
```

---

## 🏛️ Arquitetura da Solução

### Camadas

```
┌─────────────────────────────────────┐
│     Interface / Apresentação        │
│  (HAPI FHIR Web UI, pgAdmin)        │
└─────────────────────────────────────┘
              ▼
┌─────────────────────────────────────┐
│         API FHIR (REST)             │
│      (HAPI FHIR Server R4)          │
└─────────────────────────────────────┘
              ▼
┌─────────────────────────────────────┐
│      Camada de Negócios             │
│  (Validação, Profile RNDS)          │
└─────────────────────────────────────┘
              ▼
┌─────────────────────────────────────┐
│     Camada de Persistência          │
│        (PostgreSQL)                 │
└─────────────────────────────────────┘
```

### Padrões Implementados

- **RESTful API:** Operações CRUD via HTTP
- **Profile-based Validation:** Validação contra BRIndividuo
- **Microserviços:** Componentes isolados e escaláveis
- **Infrastructure as Code:** Docker Compose
- **ETL Pattern:** Extract, Transform, Load
- **Idempotência:** IDs determinísticos baseados em CPF

### Segurança

**Implementado:**
- Network isolation via Docker
- Health checks automáticos
- Validação de dados FHIR

**Recomendações para produção:**
- Autenticação OAuth 2.0
- Autorização RBAC
- TLS/HTTPS
- Criptografia de dados sensíveis (CPF, CNS)
- Audit logging conforme LGPD
- Rate limiting
- WAF (Web Application Firewall)

---

## 🛠️ Tecnologias Utilizadas

### Core

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| HAPI FHIR | Latest | Servidor FHIR R4 |
| PostgreSQL | 15 | Banco de dados |
| Python | 3.11 | Scripts ETL |
| PySpark | 3.5.0 | Processamento de dados |
| Docker | 20.10+ | Containerização |
| Docker Compose | 2.0+ | Orquestração |

### Bibliotecas Python

- **pyspark:** Processamento distribuído
- **requests:** Cliente HTTP para API FHIR
- **pandas:** Manipulação de dados
- **python-dateutil:** Manipulação de datas

### Padrões e Perfis

- **HL7 FHIR R4:** Padrão de interoperabilidade
- **BRIndividuo-1.0:** Profile da RNDS
- **BRTipoDocumentoIndividuo:** CodeSystem brasileiro
- **LOINC/SNOMED CT:** Terminologias médicas (preparado para uso)

---

## 📊 Próximos Passos

### Melhorias Técnicas

1. **Enriquecimento de Dados**
   - Integração com API ViaCEP para validação de endereços
   - Busca de códigos SNOMED CT para condições
   - Validação de CPF/CNS contra bases nacionais

2. **Pipeline Avançado**
   - Implementação com Apache Airflow para orquestração
   - Kafka para streaming de dados
   - Apache NiFi para fluxos complexos
   - Monitoramento com Prometheus/Grafana

3. **Validação e Qualidade**
   - Integração com FHIR Validator
   - Testes automatizados (unittest, pytest)
   - CI/CD com GitHub Actions
   - Validação contra Simplifier.net

4. **Performance**
   - Bulk loading com FHIR Batch/Transaction
   - Otimização de índices PostgreSQL
   - Caching com Redis
   - Load balancing

### Integração com SES-GO

1. **Conectividade**
   - VPN/VPC para acesso seguro
   - Integração com sistemas legados
   - Adaptadores HL7 v2 para FHIR

2. **Conformidade**
   - Adequação à LGPD
   - Políticas de retenção de dados
   - Auditoria e rastreabilidade
   - Backup e disaster recovery

3. **Operação**
   - Kubernetes para orquestração em produção
   - Monitoramento 24/7
   - Documentação operacional
   - Treinamento de equipes

---



---

## 📝 Licença e Referências

### Licença
Este projeto foi desenvolvido para fins de avaliação técnica.

### Referências

- [HAPI FHIR Documentation](https://hapifhir.io/)
- [HL7 FHIR R4 Specification](https://hl7.org/fhir/R4/)
- [RNDS - Rede Nacional de Dados em Saúde](https://rnds.saude.gov.br/)
- [Profile BRIndividuo](https://simplifier.net/redenacionaldedadosemsaude/brindividuo)
- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [Docker Documentation](https://docs.docker.com/)

---

**Desenvolvido com ❤️ e expertise em FHIR por Filipe Valentino**  
**Data: 14/11/2025**
