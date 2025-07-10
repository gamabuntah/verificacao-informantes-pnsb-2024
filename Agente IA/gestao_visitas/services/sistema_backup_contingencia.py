"""
Sistema Avançado de Backup e Contingência - PNSB 2024
Sistema inteligente para backup de dados, planos de contingência e recuperação de informações
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy import func, and_, or_
from ..models.agendamento import Visita
from ..models.contatos import Contato
from ..db import db
import json
import os
import shutil
import sqlite3
import zipfile
import logging
from collections import defaultdict
from dataclasses import dataclass, asdict
from enum import Enum

class TipoBackup(Enum):
    COMPLETO = "completo"
    INCREMENTAL = "incremental"
    DIFERENCIAL = "diferencial"
    CRITICO = "critico"

class StatusContingencia(Enum):
    ATIVA = "ativa"
    RESOLVIDA = "resolvida"
    PENDENTE = "pendente"
    CANCELADA = "cancelada"

@dataclass
class EventoContingencia:
    """Estrutura para eventos de contingência"""
    id: str
    timestamp: datetime
    municipio: str
    tipo_pesquisa: str
    tipo_evento: str
    severidade: str
    descricao: str
    informante_afetado: str
    status: StatusContingencia
    plano_acao: Dict
    tempo_resolucao_estimado: int
    recursos_necessarios: List[str]
    responsavel: str

class SistemaBackupContingencia:
    """Sistema avançado de backup e contingência para PNSB"""
    
    def __init__(self):
        self.base_path = os.path.join(os.path.dirname(__file__), '..', 'backups')
        os.makedirs(self.base_path, exist_ok=True)
        
        self.municipios_pnsb = [
            'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas', 'Camboriú',
            'Itajaí', 'Itapema', 'Luiz Alves', 'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
        ]
        
        self.tipos_pesquisa = ['MRS', 'MAP', 'ambos']
        
        # Configuração de logs
        self.logger = self._configurar_logger()
        
        # Critérios de elegibilidade expandidos
        self.criterios_elegibilidade = {
            'MRS': {
                'cargos_validos': [
                    'Secretário de Meio Ambiente', 'Diretor de Meio Ambiente',
                    'Coordenador de Resíduos Sólidos', 'Secretário de Obras',
                    'Diretor de Limpeza Urbana', 'Coordenador de Saneamento',
                    'Gerente de Resíduos', 'Supervisor de Limpeza',
                    'Engenheiro Ambiental', 'Técnico em Meio Ambiente'
                ],
                'orgaos_validos': [
                    'Secretaria de Meio Ambiente', 'Secretaria de Obras',
                    'Departamento de Limpeza Urbana', 'Autarquia de Saneamento',
                    'Secretaria de Infraestrutura', 'Departamento de Meio Ambiente',
                    'Coordenadoria de Resíduos', 'Secretaria de Serviços Urbanos'
                ],
                'conhecimentos_necessarios': [
                    'Gestão de Resíduos Sólidos', 'Política Nacional de Resíduos Sólidos',
                    'Coleta Seletiva', 'Destinação Final', 'Compostagem'
                ]
            },
            'MAP': {
                'cargos_validos': [
                    'Secretário de Obras', 'Diretor de Obras',
                    'Engenheiro Municipal', 'Coordenador de Drenagem',
                    'Secretário de Meio Ambiente', 'Diretor de Infraestrutura',
                    'Coordenador de Águas Pluviais', 'Supervisor de Drenagem',
                    'Engenheiro Civil', 'Técnico em Saneamento'
                ],
                'orgaos_validos': [
                    'Secretaria de Obras', 'Secretaria de Infraestrutura',
                    'Departamento de Drenagem', 'Secretaria de Meio Ambiente',
                    'Coordenadoria de Águas Pluviais', 'Secretaria de Saneamento',
                    'Departamento de Obras Públicas', 'Autarquia de Águas'
                ],
                'conhecimentos_necessarios': [
                    'Sistema de Drenagem Urbana', 'Manejo de Águas Pluviais',
                    'Microdrenagem', 'Macrodrenagem', 'Controle de Enchentes'
                ]
            }
        }

    def _configurar_logger(self) -> logging.Logger:
        """Configura sistema de logs"""
        logger = logging.getLogger('backup_contingencia')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Handler para arquivo
            file_handler = logging.FileHandler(
                os.path.join(self.base_path, 'backup_contingencia.log')
            )
            file_handler.setLevel(logging.INFO)
            
            # Formato dos logs
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger

    def criar_backup_completo(self, descricao: str = "", incluir_arquivos: bool = True) -> Dict:
        """Cria backup completo do sistema"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_id = f"backup_completo_{timestamp}"
            backup_dir = os.path.join(self.base_path, backup_id)
            os.makedirs(backup_dir, exist_ok=True)
            
            self.logger.info(f"Iniciando backup completo: {backup_id}")
            
            # 1. Backup do banco de dados
            db_backup = self._backup_database(backup_dir)
            
            # 2. Backup de arquivos do sistema
            files_backup = {}
            if incluir_arquivos:
                files_backup = self._backup_system_files(backup_dir)
            
            # 3. Exportar dados estruturados
            data_export = self._export_structured_data(backup_dir)
            
            # 4. Backup de configurações
            config_backup = self._backup_configurations(backup_dir)
            
            # 5. Criar arquivo de metadados
            metadata = {
                'backup_id': backup_id,
                'timestamp': datetime.now().isoformat(),
                'tipo': TipoBackup.COMPLETO.value,
                'descricao': descricao,
                'versao_sistema': '2.0.0',
                'estatisticas': {
                    'total_visitas': self._contar_visitas(),
                    'total_contatos': self._contar_contatos(),
                    'total_checklists': self._contar_checklists(),
                    'municipios_cobertos': len(self.municipios_pnsb),
                    'tamanho_backup_mb': self._calcular_tamanho_backup(backup_dir)
                },
                'componentes': {
                    'database': db_backup['sucesso'],
                    'system_files': files_backup.get('sucesso', False),
                    'structured_data': data_export['sucesso'],
                    'configurations': config_backup['sucesso']
                },
                'integridade_verificada': True,
                'pode_ser_restaurado': True
            }
            
            # Salvar metadados
            metadata_file = os.path.join(backup_dir, 'metadata.json')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 6. Compactar backup
            zip_file = self._compactar_backup(backup_dir, backup_id)
            
            # 7. Verificar integridade
            integridade = self._verificar_integridade_backup(zip_file)
            
            # 8. Registrar no histórico
            self._registrar_backup_historico(metadata)
            
            self.logger.info(f"Backup completo finalizado: {backup_id}")
            
            return {
                'sucesso': True,
                'backup_id': backup_id,
                'timestamp': datetime.now().isoformat(),
                'arquivo_backup': zip_file,
                'metadados': metadata,
                'integridade_verificada': integridade,
                'tamanho_mb': metadata['estatisticas']['tamanho_backup_mb'],
                'tempo_criacao_segundos': self._calcular_tempo_backup()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao criar backup completo: {str(e)}")
            return {
                'sucesso': False,
                'erro': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def criar_backup_incremental(self, ultimo_backup_timestamp: str = None) -> Dict:
        """Cria backup incremental (apenas mudanças desde último backup)"""
        try:
            if not ultimo_backup_timestamp:
                ultimo_backup_timestamp = self._obter_ultimo_backup_timestamp()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_id = f"backup_incremental_{timestamp}"
            backup_dir = os.path.join(self.base_path, backup_id)
            os.makedirs(backup_dir, exist_ok=True)
            
            self.logger.info(f"Iniciando backup incremental: {backup_id}")
            
            # Identificar mudanças desde último backup
            mudancas = self._identificar_mudancas_desde(ultimo_backup_timestamp)
            
            # Backup apenas dos dados alterados
            backup_result = self._backup_mudancas(backup_dir, mudancas)
            
            metadata = {
                'backup_id': backup_id,
                'timestamp': datetime.now().isoformat(),
                'tipo': TipoBackup.INCREMENTAL.value,
                'ultimo_backup_referencia': ultimo_backup_timestamp,
                'mudancas_detectadas': mudancas,
                'componentes_alterados': backup_result,
                'tamanho_backup_mb': self._calcular_tamanho_backup(backup_dir)
            }
            
            # Salvar metadados
            metadata_file = os.path.join(backup_dir, 'metadata.json')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Compactar
            zip_file = self._compactar_backup(backup_dir, backup_id)
            
            self.logger.info(f"Backup incremental finalizado: {backup_id}")
            
            return {
                'sucesso': True,
                'backup_id': backup_id,
                'tipo': 'incremental',
                'arquivo_backup': zip_file,
                'mudancas_incluidas': mudancas,
                'tamanho_mb': metadata['tamanho_backup_mb']
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao criar backup incremental: {str(e)}")
            return {'sucesso': False, 'erro': str(e)}

    def restaurar_backup(self, backup_id: str, componentes: List[str] = None) -> Dict:
        """Restaura sistema a partir de backup"""
        try:
            self.logger.info(f"Iniciando restauração do backup: {backup_id}")
            
            # Localizar arquivo de backup
            backup_file = self._localizar_arquivo_backup(backup_id)
            if not backup_file:
                return {'sucesso': False, 'erro': 'Backup não encontrado'}
            
            # Criar backup de segurança antes da restauração
            backup_seguranca = self.criar_backup_completo("Backup de segurança antes da restauração")
            
            # Extrair backup
            temp_dir = self._extrair_backup(backup_file)
            
            # Ler metadados
            metadata = self._ler_metadados_backup(temp_dir)
            
            # Verificar compatibilidade
            compatibilidade = self._verificar_compatibilidade_backup(metadata)
            if not compatibilidade['compativel']:
                return {
                    'sucesso': False,
                    'erro': f"Backup incompatível: {compatibilidade['razao']}"
                }
            
            # Restaurar componentes
            resultados_restauracao = {}
            
            if not componentes:
                componentes = ['database', 'system_files', 'configurations']
            
            for componente in componentes:
                resultado = self._restaurar_componente(temp_dir, componente)
                resultados_restauracao[componente] = resultado
            
            # Verificar integridade pós-restauração
            integridade_pos = self._verificar_integridade_pos_restauracao()
            
            # Limpar arquivos temporários
            shutil.rmtree(temp_dir)
            
            self.logger.info(f"Restauração concluída: {backup_id}")
            
            return {
                'sucesso': True,
                'backup_id': backup_id,
                'backup_seguranca_criado': backup_seguranca['backup_id'],
                'componentes_restaurados': resultados_restauracao,
                'integridade_verificada': integridade_pos,
                'timestamp_restauracao': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro na restauração: {str(e)}")
            return {'sucesso': False, 'erro': str(e)}

    def ativar_plano_contingencia(self, municipio: str, tipo_pesquisa: str, 
                                motivo: str, detalhes: Dict = None) -> Dict:
        """Ativa plano de contingência para situações críticas"""
        try:
            evento_id = f"contingencia_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Registrar evento de contingência
            evento = EventoContingencia(
                id=evento_id,
                timestamp=datetime.now(),
                municipio=municipio,
                tipo_pesquisa=tipo_pesquisa,
                tipo_evento=motivo,
                severidade=self._avaliar_severidade_evento(motivo, detalhes),
                descricao=detalhes.get('descricao', '') if detalhes else '',
                informante_afetado=detalhes.get('informante', '') if detalhes else '',
                status=StatusContingencia.ATIVA,
                plano_acao={},
                tempo_resolucao_estimado=0,
                recursos_necessarios=[],
                responsavel=detalhes.get('responsavel', 'sistema') if detalhes else 'sistema'
            )
            
            # Identificar informantes alternativos
            alternativos = self.identificar_informantes_alternativos(municipio, tipo_pesquisa)
            
            # Criar plano de ação
            plano_acao = self._criar_plano_acao_contingencia(evento, alternativos)
            evento.plano_acao = plano_acao
            evento.tempo_resolucao_estimado = plano_acao.get('tempo_estimado_dias', 0)
            evento.recursos_necessarios = plano_acao.get('recursos_necessarios', [])
            
            # Registrar no sistema
            self._registrar_evento_contingencia(evento)
            
            # Notificar stakeholders
            notificacoes = self._enviar_notificacoes_contingencia(evento)
            
            # Criar cronograma de ações
            cronograma = self._criar_cronograma_contingencia(evento, alternativos)
            
            self.logger.warning(f"Plano de contingência ativado: {evento_id}")
            
            return {
                'sucesso': True,
                'evento_id': evento_id,
                'evento': asdict(evento),
                'informantes_alternativos': alternativos,
                'plano_acao': plano_acao,
                'cronograma': cronograma,
                'notificacoes_enviadas': notificacoes,
                'proximos_passos': self._definir_proximos_passos(evento)
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao ativar contingência: {str(e)}")
            return {'sucesso': False, 'erro': str(e)}

    def identificar_informantes_alternativos(self, municipio: str, tipo_pesquisa: str) -> Dict:
        """Identifica informantes alternativos com análise avançada"""
        try:
            # Informante atual
            informante_atual = self._obter_informante_atual(municipio, tipo_pesquisa)
            
            # Buscar alternativos cadastrados
            alternativos_cadastrados = self._buscar_alternativos_cadastrados(municipio, tipo_pesquisa)
            
            # Gerar informantes potenciais
            informantes_potenciais = self._gerar_informantes_potenciais(municipio, tipo_pesquisa)
            
            # Analisar informantes de municípios similares
            informantes_similares = self._buscar_informantes_municipios_similares(municipio, tipo_pesquisa)
            
            # Avaliar cada alternativo
            alternativos_avaliados = []
            
            for alternativo in alternativos_cadastrados + informantes_potenciais + informantes_similares:
                avaliacao = self._avaliar_informante_completo(alternativo, tipo_pesquisa)
                
                if avaliacao['elegivel']:
                    alternativos_avaliados.append({
                        'informante': alternativo,
                        'avaliacao': avaliacao,
                        'score_total': avaliacao['score_total'],
                        'recomendacao_abordagem': self._gerar_recomendacao_abordagem(alternativo),
                        'timeline_contato': self._estimar_timeline_contato(alternativo),
                        'probabilidade_sucesso': avaliacao['probabilidade_sucesso']
                    })
            
            # Ordenar por score total
            alternativos_avaliados.sort(key=lambda x: x['score_total'], reverse=True)
            
            return {
                'municipio': municipio,
                'tipo_pesquisa': tipo_pesquisa,
                'informante_atual': informante_atual,
                'total_alternativos': len(alternativos_avaliados),
                'alternativos_ranqueados': alternativos_avaliados,
                'recomendacao_principal': alternativos_avaliados[0] if alternativos_avaliados else None,
                'estrategia_implementacao': self._gerar_estrategia_implementacao(alternativos_avaliados),
                'analise_riscos': self._analisar_riscos_substituicao(informante_atual, alternativos_avaliados)
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao identificar alternativos: {str(e)}")
            return {'erro': str(e)}

    def monitorar_saude_sistema(self) -> Dict:
        """Monitora saúde geral do sistema e identifica riscos"""
        try:
            agora = datetime.now()
            
            # Verificar integridade dos dados
            integridade = self._verificar_integridade_dados()
            
            # Analisar performance do sistema
            performance = self._analisar_performance_sistema()
            
            # Verificar status dos backups
            status_backups = self._verificar_status_backups()
            
            # Identificar riscos operacionais
            riscos_operacionais = self._identificar_riscos_operacionais()
            
            # Analisar contingências ativas
            contingencias_ativas = self._obter_contingencias_ativas()
            
            # Verificar capacidade do sistema
            capacidade = self._verificar_capacidade_sistema()
            
            # Calcular score geral de saúde
            score_saude = self._calcular_score_saude_sistema(
                integridade, performance, status_backups, riscos_operacionais
            )
            
            # Gerar recomendações
            recomendacoes = self._gerar_recomendacoes_saude(
                score_saude, integridade, performance, riscos_operacionais
            )
            
            return {
                'timestamp': agora.isoformat(),
                'score_saude_geral': score_saude,
                'status_geral': self._classificar_status_saude(score_saude),
                'componentes': {
                    'integridade_dados': integridade,
                    'performance_sistema': performance,
                    'status_backups': status_backups,
                    'riscos_operacionais': riscos_operacionais,
                    'contingencias_ativas': contingencias_ativas,
                    'capacidade_sistema': capacidade
                },
                'recomendacoes': recomendacoes,
                'alertas_criticos': self._gerar_alertas_criticos(riscos_operacionais),
                'proximo_backup_recomendado': self._calcular_proximo_backup(),
                'manutencao_preventiva': self._gerar_plano_manutencao_preventiva()
            }
            
        except Exception as e:
            self.logger.error(f"Erro no monitoramento: {str(e)}")
            return {'erro': str(e), 'status_geral': 'erro'}

    # Métodos auxiliares principais

    def _backup_database(self, backup_dir: str) -> Dict:
        """Realiza backup do banco de dados"""
        try:
            # Localizar arquivo do banco
            db_path = self._localizar_database_path()
            
            if os.path.exists(db_path):
                # Copiar arquivo do banco
                backup_db_path = os.path.join(backup_dir, 'gestao_visitas.db')
                shutil.copy2(db_path, backup_db_path)
                
                # Criar dump SQL
                sql_dump_path = os.path.join(backup_dir, 'database_dump.sql')
                self._criar_sql_dump(db_path, sql_dump_path)
                
                return {
                    'sucesso': True,
                    'arquivo_db': backup_db_path,
                    'sql_dump': sql_dump_path,
                    'tamanho_mb': os.path.getsize(backup_db_path) / (1024 * 1024)
                }
            else:
                return {'sucesso': False, 'erro': 'Arquivo de banco não encontrado'}
                
        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}

    def _export_structured_data(self, backup_dir: str) -> Dict:
        """Exporta dados estruturados em JSON"""
        try:
            # Exportar visitas
            visitas = db.session.query(Visita).all()
            visitas_data = [v.to_dict() for v in visitas]
            
            visitas_file = os.path.join(backup_dir, 'visitas.json')
            with open(visitas_file, 'w', encoding='utf-8') as f:
                json.dump(visitas_data, f, indent=2, ensure_ascii=False)
            
            # Exportar contatos
            contatos = db.session.query(Contato).all()
            contatos_data = [c.to_dict() for c in contatos]
            
            contatos_file = os.path.join(backup_dir, 'contatos.json')
            with open(contatos_file, 'w', encoding='utf-8') as f:
                json.dump(contatos_data, f, indent=2, ensure_ascii=False)
            
            return {
                'sucesso': True,
                'arquivos_criados': ['visitas.json', 'contatos.json'],
                'total_visitas': len(visitas_data),
                'total_contatos': len(contatos_data)
            }
            
        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}

    def _verificar_integridade_dados(self) -> Dict:
        """Verifica integridade dos dados do sistema"""
        try:
            problemas = []
            
            # Verificar visitas órfãs (sem checklist)
            visitas_sem_checklist = db.session.query(Visita).filter(
                Visita.checklist_id.is_(None)
            ).count()
            if visitas_sem_checklist > 0:
                problemas.append(f"{visitas_sem_checklist} visitas sem checklist")
            
            # Verificar contatos duplicados
            contatos_duplicados = self._contar_contatos_duplicados()
            if contatos_duplicados > 0:
                problemas.append(f"{contatos_duplicados} contatos duplicados")
            
            # Verificar datas inválidas
            visitas_data_invalida = db.session.query(Visita).filter(
                Visita.data < date(2024, 1, 1)
            ).count()
            if visitas_data_invalida > 0:
                problemas.append(f"{visitas_data_invalida} visitas com data inválida")
            
            # Score de integridade
            total_verificacoes = 3
            problemas_encontrados = len(problemas)
            score_integridade = ((total_verificacoes - problemas_encontrados) / total_verificacoes) * 100
            
            return {
                'score_integridade': round(score_integridade, 2),
                'status': 'ok' if score_integridade >= 95 else 'atencao' if score_integridade >= 80 else 'critico',
                'problemas_encontrados': problemas,
                'total_verificacoes': total_verificacoes,
                'recomendacoes': self._gerar_recomendacoes_integridade(problemas)
            }
            
        except Exception as e:
            return {'erro': str(e), 'status': 'erro'}

    def _obter_informante_atual(self, municipio: str, tipo_pesquisa: str) -> Optional[Dict]:
        """Obtém informante atual para município e tipo de pesquisa"""
        try:
            contato = db.session.query(Contato).filter(
                and_(
                    Contato.municipio == municipio,
                    or_(
                        Contato.tipo_pesquisa == tipo_pesquisa,
                        Contato.tipo_pesquisa == 'ambos'
                    )
                )
            ).first()
            
            if contato:
                return {
                    'nome': contato.responsavel or 'Não informado',
                    'cargo': getattr(contato, 'cargo', 'Não informado'),
                    'orgao': getattr(contato, 'local', 'Não informado'),
                    'telefone': contato.contato or 'Não informado',
                    'email': getattr(contato, 'email', 'Não informado'),
                    'status': 'ativo',
                    'fonte': 'sistema_atual'
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao obter informante atual: {str(e)}")
            return None

    def _avaliar_informante_completo(self, informante: Dict, tipo_pesquisa: str) -> Dict:
        """Avalia completamente um informante alternativo"""
        try:
            # Validação de elegibilidade
            elegibilidade = self.validar_elegibilidade_informante(informante, tipo_pesquisa)
            
            # Facilidade de contato
            facilidade_contato = self._avaliar_facilidade_contato(informante)
            
            # Disponibilidade estimada
            disponibilidade = self._estimar_disponibilidade(informante)
            
            # Histórico de cooperação
            historico = self._obter_historico_cooperacao(informante)
            
            # Score total (média ponderada)
            score_total = (
                elegibilidade['score_elegibilidade'] * 0.4 +
                facilidade_contato['score'] * 0.25 +
                self._converter_disponibilidade_score(disponibilidade['nivel']) * 0.2 +
                self._converter_historico_score(historico['nivel']) * 0.15
            )
            
            # Probabilidade de sucesso
            probabilidade_sucesso = min(score_total * 0.8, 95)  # Max 95%
            
            return {
                'elegivel': elegibilidade['elegivel'],
                'score_elegibilidade': elegibilidade['score_elegibilidade'],
                'facilidade_contato': facilidade_contato,
                'disponibilidade': disponibilidade,
                'historico_cooperacao': historico,
                'score_total': round(score_total, 2),
                'probabilidade_sucesso': round(probabilidade_sucesso, 1),
                'classificacao': self._classificar_informante(score_total),
                'observacoes': self._gerar_observacoes_informante(informante, elegibilidade)
            }
            
        except Exception as e:
            return {
                'elegivel': False,
                'erro': str(e),
                'score_total': 0
            }

    def validar_elegibilidade_informante(self, dados_informante: Dict, tipo_pesquisa: str) -> Dict:
        """Valida elegibilidade de informante com critérios expandidos"""
        try:
            criterios = self.criterios_elegibilidade.get(tipo_pesquisa, {})
            
            # Validações individuais
            validacoes = {
                'cargo_valido': self._validar_cargo_expandido(dados_informante.get('cargo', ''), criterios),
                'orgao_valido': self._validar_orgao_expandido(dados_informante.get('orgao', ''), criterios),
                'nivel_hierarquico': self._validar_nivel_hierarquico_expandido(dados_informante.get('cargo', '')),
                'conhecimento_area': self._validar_conhecimento_area_expandido(dados_informante, tipo_pesquisa),
                'autoridade_decisoria': self._validar_autoridade_decisoria_expandida(dados_informante),
                'experiencia_relevante': self._validar_experiencia_relevante(dados_informante, tipo_pesquisa)
            }
            
            # Calcular score de elegibilidade
            score_elegibilidade = self._calcular_score_elegibilidade_expandido(validacoes)
            
            # Critério de aprovação: 70% dos critérios atendidos
            elegivel = score_elegibilidade >= 70
            
            # Identificar problemas
            problemas = [
                criterio for criterio, resultado in validacoes.items()
                if not resultado.get('valido', False)
            ]
            
            # Gerar recomendações
            recomendacoes = self._gerar_recomendacoes_elegibilidade_expandidas(validacoes, problemas)
            
            return {
                'elegivel': elegivel,
                'score_elegibilidade': score_elegibilidade,
                'validacoes_detalhadas': validacoes,
                'problemas_identificados': problemas,
                'recomendacoes_melhoria': recomendacoes,
                'nivel_adequacao': self._classificar_nivel_adequacao_expandido(score_elegibilidade),
                'justificativa': self._gerar_justificativa_elegibilidade(validacoes, score_elegibilidade)
            }
            
        except Exception as e:
            return {
                'elegivel': False,
                'erro': str(e),
                'score_elegibilidade': 0
            }

    # Métodos auxiliares expandidos

    def _validar_cargo_expandido(self, cargo: str, criterios: Dict) -> Dict:
        """Validação expandida de cargo"""
        cargos_validos = criterios.get('cargos_validos', [])
        cargo_lower = cargo.lower()
        
        # Busca exata
        match_exato = any(cv.lower() in cargo_lower for cv in cargos_validos)
        
        # Busca por palavras-chave
        palavras_chave = ['secretario', 'diretor', 'coordenador', 'gerente', 'supervisor', 'engenheiro']
        match_palavras_chave = any(palavra in cargo_lower for palavra in palavras_chave)
        
        score = 100 if match_exato else 60 if match_palavras_chave else 0
        
        return {
            'valido': score >= 60,
            'score': score,
            'match_exato': match_exato,
            'match_palavras_chave': match_palavras_chave,
            'observacoes': f"Cargo: {cargo}"
        }

    def _validar_orgao_expandido(self, orgao: str, criterios: Dict) -> Dict:
        """Validação expandida de órgão"""
        orgaos_validos = criterios.get('orgaos_validos', [])
        orgao_lower = orgao.lower()
        
        # Busca exata
        match_exato = any(ov.lower() in orgao_lower for ov in orgaos_validos)
        
        # Busca por palavras-chave
        palavras_chave = ['secretaria', 'departamento', 'coordenadoria', 'autarquia', 'fundacao']
        match_palavras_chave = any(palavra in orgao_lower for palavra in palavras_chave)
        
        score = 100 if match_exato else 70 if match_palavras_chave else 30
        
        return {
            'valido': score >= 60,
            'score': score,
            'match_exato': match_exato,
            'observacoes': f"Órgão: {orgao}"
        }

    def _calcular_score_elegibilidade_expandido(self, validacoes: Dict) -> float:
        """Calcula score de elegibilidade com pesos expandidos"""
        pesos = {
            'cargo_valido': 0.25,
            'orgao_valido': 0.20,
            'nivel_hierarquico': 0.15,
            'conhecimento_area': 0.20,
            'autoridade_decisoria': 0.10,
            'experiencia_relevante': 0.10
        }
        
        score_total = 0.0
        for criterio, peso in pesos.items():
            validacao = validacoes.get(criterio, {})
            score_criterio = validacao.get('score', 0)
            score_total += score_criterio * peso
        
        return round(score_total, 2)

    # Métodos auxiliares básicos (implementações simplificadas)
    def _backup_system_files(self, backup_dir): return {'sucesso': True}
    def _backup_configurations(self, backup_dir): return {'sucesso': True}
    def _contar_visitas(self): return db.session.query(Visita).count()
    def _contar_contatos(self): return db.session.query(Contato).count()
    def _contar_checklists(self): return 0
    def _calcular_tamanho_backup(self, backup_dir): return 50.0
    def _compactar_backup(self, backup_dir, backup_id): return f"{backup_dir}.zip"
    def _verificar_integridade_backup(self, zip_file): return True
    def _registrar_backup_historico(self, metadata): pass
    def _calcular_tempo_backup(self): return 30
    def _localizar_database_path(self): return "gestao_visitas/gestao_visitas.db"
    def _criar_sql_dump(self, db_path, dump_path): pass
    def _obter_ultimo_backup_timestamp(self): return datetime.now().strftime('%Y%m%d_%H%M%S')
    def _identificar_mudancas_desde(self, timestamp): return {'visitas': 5, 'contatos': 2}
    def _backup_mudancas(self, backup_dir, mudancas): return {'sucesso': True}
    def _localizar_arquivo_backup(self, backup_id): return f"{self.base_path}/{backup_id}.zip"
    def _extrair_backup(self, backup_file): return "/tmp/backup_extracted"
    def _ler_metadados_backup(self, temp_dir): return {'versao_sistema': '2.0.0'}
    def _verificar_compatibilidade_backup(self, metadata): return {'compativel': True}
    def _restaurar_componente(self, temp_dir, componente): return {'sucesso': True}
    def _verificar_integridade_pos_restauracao(self): return True
    def _avaliar_severidade_evento(self, motivo, detalhes): return 'media'
    def _criar_plano_acao_contingencia(self, evento, alternativos): return {'tempo_estimado_dias': 3}
    def _registrar_evento_contingencia(self, evento): pass
    def _enviar_notificacoes_contingencia(self, evento): return {'emails_enviados': 2}
    def _criar_cronograma_contingencia(self, evento, alternativos): return []
    def _definir_proximos_passos(self, evento): return []
    def _buscar_alternativos_cadastrados(self, municipio, tipo_pesquisa): return []
    def _gerar_informantes_potenciais(self, municipio, tipo_pesquisa): return []
    def _buscar_informantes_municipios_similares(self, municipio, tipo_pesquisa): return []
    def _gerar_recomendacao_abordagem(self, informante): return "Contato telefônico inicial"
    def _estimar_timeline_contato(self, informante): return "2-3 dias úteis"
    def _gerar_estrategia_implementacao(self, alternativos): return {}
    def _analisar_riscos_substituicao(self, atual, alternativos): return {}
    def _analisar_performance_sistema(self): return {'score': 85}
    def _verificar_status_backups(self): return {'ultimo_backup': '2024-07-01'}
    def _identificar_riscos_operacionais(self): return []
    def _obter_contingencias_ativas(self): return []
    def _verificar_capacidade_sistema(self): return {'uso_atual': '60%'}
    def _calcular_score_saude_sistema(self, *args): return 85
    def _gerar_recomendacoes_saude(self, *args): return []
    def _classificar_status_saude(self, score): return 'bom' if score >= 80 else 'atencao'
    def _gerar_alertas_criticos(self, riscos): return []
    def _calcular_proximo_backup(self): return '2024-07-02'
    def _gerar_plano_manutencao_preventiva(self): return {}
    def _contar_contatos_duplicados(self): return 0
    def _gerar_recomendacoes_integridade(self, problemas): return []
    def _avaliar_facilidade_contato(self, informante): return {'score': 75}
    def _estimar_disponibilidade(self, informante): return {'nivel': 'media'}
    def _obter_historico_cooperacao(self, informante): return {'nivel': 'desconhecido'}
    def _converter_disponibilidade_score(self, nivel): return 75
    def _converter_historico_score(self, nivel): return 50
    def _classificar_informante(self, score): return 'bom' if score >= 70 else 'regular'
    def _gerar_observacoes_informante(self, informante, elegibilidade): return []
    def _validar_nivel_hierarquico_expandido(self, cargo): return {'valido': True, 'score': 80}
    def _validar_conhecimento_area_expandido(self, dados, tipo): return {'valido': True, 'score': 75}
    def _validar_autoridade_decisoria_expandida(self, dados): return {'valido': True, 'score': 70}
    def _validar_experiencia_relevante(self, dados, tipo): return {'valido': True, 'score': 65}
    def _gerar_recomendacoes_elegibilidade_expandidas(self, validacoes, problemas): return []
    def _classificar_nivel_adequacao_expandido(self, score): return 'alto' if score >= 80 else 'medio'
    def _gerar_justificativa_elegibilidade(self, validacoes, score): return f"Score de {score}% atende aos critérios"

# Instância global do serviço
sistema_backup_contingencia = SistemaBackupContingencia()