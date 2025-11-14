"""
ETL Pipeline para carga de dados de pacientes no servidor HAPI FHIR
Utilizando o profile BRIndividuo da RNDS (Rede Nacional de Dados em Saúde)
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, when, lit
from pyspark.sql.types import StringType
import requests
import json
from datetime import datetime
import hashlib
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FHIRETLPipeline:
    """Pipeline ETL para carregar dados de pacientes no servidor FHIR"""
    
    def __init__(self, fhir_server_url: str = "http://localhost:8080/fhir"):
        self.fhir_server_url = fhir_server_url
        self.spark = self._create_spark_session()
        
    def _create_spark_session(self):
        """Cria sessão Spark"""
        return SparkSession.builder \
            .appName("FHIR-ETL-Pipeline") \
            .config("spark.driver.memory", "2g") \
            .config("spark.executor.memory", "2g") \
            .getOrCreate()
    
    def read_csv_data(self, csv_path: str):
        """Lê dados do arquivo CSV"""
        logger.info(f"Lendo dados de {csv_path}")
        df = self.spark.read.csv(
            csv_path,
            header=True,
            inferSchema=True,
            encoding='UTF-8'
        )
        logger.info(f"Total de registros lidos: {df.count()}")
        return df
    
    def generate_fhir_id(self, cpf: str) -> str:
        """Gera ID único para o resource baseado no CPF"""
        return hashlib.sha256(cpf.encode()).hexdigest()[:16]
    
    def clean_cpf(self, cpf: str) -> str:
        """Remove formatação do CPF"""
        if not cpf:
            return ""
        return cpf.replace('.', '').replace('-', '').strip()
    
    def parse_date(self, date_str: str) -> str:
        """Converte data DD/MM/YYYY para YYYY-MM-DD"""
        if not date_str:
            return ""
        try:
            day, month, year = date_str.split('/')
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            return date_str
    
    def parse_name(self, full_name: str) -> tuple:
        """Separa nome completo em nome e sobrenome"""
        if not full_name:
            return ("", "")
        parts = full_name.strip().split()
        if len(parts) == 1:
            return (parts[0], "")
        return (parts[0], " ".join(parts[1:]))
    
    def map_gender(self, genero: str) -> str:
        """Mapeia gênero para o padrão FHIR"""
        mapping = {
            'Masculino': 'male',
            'M': 'male',
            'Feminino': 'female',
            'F': 'female',
            'O': 'other',
            'U': 'unknown'
        }
        return mapping.get(genero.strip() if genero else '', 'unknown')
    
    def create_br_individuo_resource(self, row) -> dict:
        """
        Cria resource Patient seguindo o profile BRIndividuo da RNDS
        Profile: https://simplifier.net/redenacionaldedadosemsaude/brindividuo
        
        Mapeia os campos do CSV:
        - Nome -> name
        - CPF -> identifier
        - Gênero -> gender
        - Data de Nascimento -> birthDate
        - Telefone -> telecom
        """
        
        # Limpa e processa dados
        cpf_limpo = self.clean_cpf(row['CPF'])
        if not cpf_limpo:
            raise ValueError("CPF é obrigatório")
            
        patient_id = self.generate_fhir_id(cpf_limpo)
        nome, sobrenome = self.parse_name(row['Nome'])
        birth_date = self.parse_date(row['Data de Nascimento'])
        
        # Estrutura base do resource Patient com profile BRIndividuo
        patient = {
            "resourceType": "Patient",
            "id": patient_id,
            "meta": {
                "profile": [
                    "http://www.saude.gov.br/fhir/r4/StructureDefinition/BRIndividuo-1.0"
                ]
            },
            "identifier": [
                {
                    "use": "official",
                    "type": {
                        "coding": [
                            {
                                "system": "http://www.saude.gov.br/fhir/r4/CodeSystem/BRTipoDocumentoIndividuo",
                                "code": "CPF",
                                "display": "Cadastro de Pessoas Físicas"
                            }
                        ]
                    },
                    "system": "http://www.saude.gov.br/fhir/r4/StructureDefinition/BRIndividuo-1.0",
                    "value": cpf_limpo
                }
            ],
            "active": True,
            "name": [
                {
                    "use": "official",
                    "text": row['Nome'],
                    "family": sobrenome,
                    "given": [nome]
                }
            ],
            "gender": self.map_gender(row.get('Gênero', '')),
            "birthDate": birth_date
        }
        
        # Adiciona telefone se disponível
        telecom = []
        if row.get('Telefone'):
            telecom.append({
                "system": "phone",
                "value": row['Telefone'],
                "use": "mobile"
            })
        if telecom:
            patient["telecom"] = telecom
        
        return patient
    
    def create_condition_resource(self, patient_id: str, observation_text: str, row) -> dict:
        """
        Cria resource Condition para observações de saúde do paciente
        """
        condition_id = hashlib.sha256(
            f"{patient_id}-{observation_text}".encode()
        ).hexdigest()[:16]
        
        condition = {
            "resourceType": "Condition",
            "id": condition_id,
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active",
                        "display": "Active"
                    }
                ]
            },
            "verificationStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        "code": "confirmed",
                        "display": "Confirmed"
                    }
                ]
            },
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                            "code": "problem-list-item",
                            "display": "Problem List Item"
                        }
                    ]
                }
            ],
            "code": {
                "text": observation_text
            },
            "subject": {
                "reference": f"Patient/{patient_id}",
                "display": row['Nome']
            },
            "recordedDate": datetime.now().isoformat()
        }
        
        return condition
    
    def send_to_fhir_server(self, resource: dict) -> bool:
        """Envia resource para o servidor FHIR"""
        try:
            resource_type = resource['resourceType']
            resource_id = resource['id']
            
            url = f"{self.fhir_server_url}/{resource_type}/{resource_id}"
            
            headers = {
                'Content-Type': 'application/fhir+json',
                'Accept': 'application/fhir+json'
            }
            
            response = requests.put(url, json=resource, headers=headers)
            
            if response.status_code in [200, 201]:
                logger.info(f"✓ {resource_type}/{resource_id} criado com sucesso")
                return True
            else:
                logger.error(
                    f"✗ Erro ao criar {resource_type}/{resource_id}: "
                    f"{response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            logger.error(f"✗ Exceção ao enviar resource: {str(e)}")
            return False
    
    def process_and_load(self, csv_path: str):
        """Processa os dados e carrega no servidor FHIR"""
        
        # Verifica conectividade com o servidor FHIR
        try:
            response = requests.get(f"{self.fhir_server_url}/metadata")
            if response.status_code != 200:
                logger.error("Servidor FHIR não está acessível")
                return
            logger.info("✓ Servidor FHIR está acessível")
        except Exception as e:
            logger.error(f"Erro ao conectar com servidor FHIR: {str(e)}")
            return
        
        # Lê dados do CSV
        df = self.read_csv_data(csv_path)
        
        # Processa cada linha
        patients_df = df.collect()
        
        total_patients = len(patients_df)
        patients_success = 0
        conditions_success = 0
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Iniciando carga de {total_patients} pacientes")
        logger.info(f"{'='*60}\n")
        
        for idx, row_data in enumerate(patients_df, 1):
            row = row_data.asDict()
            
            logger.info(f"\n[{idx}/{total_patients}] Processando: {row['Nome']}")
            
            try:
                # Cria e envia Patient resource
                patient = self.create_br_individuo_resource(row)
                if self.send_to_fhir_server(patient):
                    patients_success += 1
                    
                    # Se houver observação, cria Condition resource(s)
                    observacao = row.get('Observação', '').strip()
                    if observacao:
                        patient_id = patient['id']
                        
                        # Separa múltiplas observações por pipe
                        observacoes = [obs.strip() for obs in observacao.split('|') if obs.strip()]
                        
                        for obs_text in observacoes:
                            condition = self.create_condition_resource(
                                patient_id,
                                obs_text,
                                row
                            )
                            if self.send_to_fhir_server(condition):
                                conditions_success += 1
            except Exception as e:
                logger.error(f"✗ Erro ao processar paciente: {str(e)}")
        
        # Relatório final
        logger.info(f"\n{'='*60}")
        logger.info(f"RESUMO DA CARGA")
        logger.info(f"{'='*60}")
        logger.info(f"Pacientes processados: {total_patients}")
        logger.info(f"Pacientes carregados: {patients_success}")
        logger.info(f"Conditions carregadas: {conditions_success}")
        logger.info(f"Taxa de sucesso: {(patients_success/total_patients)*100:.1f}%")
        logger.info(f"{'='*60}\n")


def main():
    """Função principal"""
    
    # Configurações
    FHIR_SERVER_URL = "http://localhost:8080/fhir"
    CSV_PATH = "data/patients.csv"  # Caminho relativo ou absoluto
    
    # Tenta diferentes caminhos
    import os
    possible_paths = [
        CSV_PATH,
        "/home/claude/fhir-test-indra/data/patients.csv",
        "/app/data/patients.csv"
    ]
    
    csv_file = None
    for path in possible_paths:
        if os.path.exists(path):
            csv_file = path
            break
    
    if not csv_file:
        logger.error(f"Arquivo CSV não encontrado. Tentou: {possible_paths}")
        return
    
    logger.info(f"Usando arquivo: {csv_file}")
    
    # Cria pipeline e executa
    pipeline = FHIRETLPipeline(FHIR_SERVER_URL)
    pipeline.process_and_load(csv_file)
    
    # Encerra sessão Spark
    pipeline.spark.stop()


if __name__ == "__main__":
    main()
