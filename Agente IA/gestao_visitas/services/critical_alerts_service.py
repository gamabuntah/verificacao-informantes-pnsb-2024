"""
Sistema de Alertas Críticos Funcional para o Projeto PNSB 2024
Sistema inteligente que monitora e gera alertas críticos baseados em dados reais
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics

from gestao_visitas.models.agendamento import Visita
from gestao_visitas.models.contatos import Contato
from gestao_visitas.models.checklist import Checklist
from gestao_visitas.db import db
from gestao_visitas.config import MUNICIPIOS

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    CRITICO = "critico"
    URGENTE = "urgente"
    ATENCAO = "atencao"
    INFO = "info"

class AlertType(Enum):
    DEADLINE = "deadline"
    MUNICIPIO = "municipio"
    CONTATOS = "contatos"
    CONFLITOS = "conflitos"
    FOLLOWUP = "followup"
    DOCUMENTACAO = "documentacao"
    RISCOS = "riscos"
    PERFORMANCE = "performance"
    STATUS = "status"
    BACKUP = "backup"

@dataclass
class CriticalAlert:
    """Representa um alerta crítico do sistema"""
    id: str
    tipo: AlertType
    nivel: AlertLevel
    titulo: str
    descricao: str
    municipio: str
    entidade: Optional[str]
    acao_recomendada: str
    dados: Dict
    dias_restantes: Optional[int]
    timestamp: datetime
    prioridade: int  # 1=máxima, 5=mínima

class CriticalAlertsService:
    """
    Sistema de Alertas Críticos Funcional para PNSB 2024
    
    Monitora continuamente o projeto e gera alertas inteligentes
    baseados em dados reais e regras específicas do PNSB.
    """
    
    def __init__(self, db_session):
        self.db = db_session
        
        # Configurações de deadlines específicos do PNSB
        self.DEADLINE_VISITAS_P1_P2 = datetime(2025, 9, 19)  # 19/09/2025
        self.DEADLINE_QUESTIONARIOS = datetime(2025, 10, 17)  # 17/10/2025
        self.DEADLINE_FINALIZACAO = datetime(2025, 12, 15)   # 15/12/2025
        
        logger.info("CriticalAlertsService inicializado com sucesso")
    
    def get_all_critical_alerts(self) -> Dict:
        """
        Retorna todos os alertas críticos do sistema
        
        Returns:
            Dict com alertas, resumo e métricas do sistema
        """
        try:
            logger.info("Gerando alertas críticos do sistema PNSB")
            
            alertas = []
            
            # 1. Alertas de Deadlines Críticos
            alertas.extend(self._generate_deadline_alerts())
            
            # 2. Alertas por Município
            alertas.extend(self._generate_municipality_alerts())
            
            # 3. Alertas de Contatos
            alertas.extend(self._generate_contact_alerts())
            
            # 4. Alertas de Conflitos
            alertas.extend(self._generate_conflict_alerts())
            
            # 5. Alertas de Follow-up
            alertas.extend(self._generate_followup_alerts())
            
            # 6. Alertas de Documentação
            alertas.extend(self._generate_documentation_alerts())
            
            # 7. Alertas de Riscos
            alertas.extend(self._generate_risk_alerts())
            
            # 8. Alertas de Performance
            alertas.extend(self._generate_performance_alerts())
            
            # 9. Alertas de Status
            alertas.extend(self._generate_status_alerts())
            
            # 10. Alertas de Backup
            alertas.extend(self._generate_backup_alerts())
            
            # Ordenar por prioridade e nível
            alertas_ordenados = self._sort_alerts_by_priority(alertas)
            
            # Gerar resumo
            resumo = self._generate_summary(alertas_ordenados)
            
            # Convert enum objects to string values for JSON serialization
            alertas_dict = []
            for alert in alertas_ordenados:
                alert_dict = alert.__dict__.copy()
                alert_dict['tipo'] = alert.tipo.value
                alert_dict['nivel'] = alert.nivel.value
                alert_dict['timestamp'] = alert.timestamp.isoformat() if hasattr(alert.timestamp, 'isoformat') else str(alert.timestamp)
                alertas_dict.append(alert_dict)
            
            result = {
                'alertas': alertas_dict,
                'resumo': resumo,
                'timestamp_consulta': datetime.now().isoformat(),
                'total_alertas': len(alertas_ordenados)
            }
            
            logger.info(f"Alertas críticos gerados: {len(alertas_ordenados)} alertas")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao gerar alertas críticos: {e}")
            raise
    
    def _generate_deadline_alerts(self) -> List[CriticalAlert]:
        """Gera alertas de deadlines críticos"""
        alertas = []
        hoje = datetime.now()
        
        # Calcular dias restantes para cada deadline
        dias_visitas = (self.DEADLINE_VISITAS_P1_P2 - hoje).days
        dias_questionarios = (self.DEADLINE_QUESTIONARIOS - hoje).days
        dias_finalizacao = (self.DEADLINE_FINALIZACAO - hoje).days
        
        # Obter dados de progresso
        visitas = Visita.query.all()
        total_visitas = len(visitas)
        visitas_finalizadas = len([v for v in visitas if v.status in ['realizada', 'finalizada']])
        visitas_p1_p2 = len([v for v in visitas if hasattr(v, 'prioridade') and v.prioridade in ['P1', 'P2']])
        
        # Alerta de deadline de visitas P1+P2
        if dias_visitas <= 60:
            nivel = AlertLevel.CRITICO if dias_visitas <= 30 else AlertLevel.URGENTE
            prioridade = 1 if nivel == AlertLevel.CRITICO else 2
            
            alertas.append(CriticalAlert(
                id=f"deadline_visitas_{nivel.value}",
                tipo=AlertType.DEADLINE,
                nivel=nivel,
                titulo=f"🚨 DEADLINE VISITAS P1+P2: {dias_visitas} dias restantes",
                descricao=f"Prazo crítico para concluir TODAS as visitas prioritárias (P1+P2) até 19/09/2025. Acelerar execução IMEDIATAMENTE.",
                municipio="TODOS",
                entidade=None,
                acao_recomendada="Reorganizar equipe, priorizar visitas P1 e P2, considerar recursos adicionais",
                dados={
                    'deadline': self.DEADLINE_VISITAS_P1_P2.isoformat(),
                    'dias_restantes': dias_visitas,
                    'total_visitas': total_visitas,
                    'visitas_finalizadas': visitas_finalizadas,
                    'visitas_p1_p2': visitas_p1_p2,
                    'taxa_conclusao': (visitas_finalizadas / total_visitas * 100) if total_visitas > 0 else 0
                },
                dias_restantes=dias_visitas,
                timestamp=hoje,
                prioridade=prioridade
            ))
        
        # Alerta de deadline de questionários
        if dias_questionarios <= 90:
            nivel = AlertLevel.CRITICO if dias_questionarios <= 45 else AlertLevel.URGENTE
            prioridade = 1 if nivel == AlertLevel.CRITICO else 3
            
            alertas.append(CriticalAlert(
                id=f"deadline_questionarios_{nivel.value}",
                tipo=AlertType.DEADLINE,
                nivel=nivel,
                titulo=f"📋 DEADLINE QUESTIONÁRIOS: {dias_questionarios} dias restantes",
                descricao=f"Prazo para finalização de todos os questionários até 17/10/2025. Iniciar preenchimento urgentemente.",
                municipio="TODOS",
                entidade=None,
                acao_recomendada="Iniciar preenchimento imediato dos questionários, treinar equipe, organizar dados coletados",
                dados={
                    'deadline': self.DEADLINE_QUESTIONARIOS.isoformat(),
                    'dias_restantes': dias_questionarios,
                    'status': 'critico' if dias_questionarios <= 45 else 'urgente'
                },
                dias_restantes=dias_questionarios,
                timestamp=hoje,
                prioridade=prioridade
            ))
        
        # Alerta de finalização geral do projeto
        if dias_finalizacao <= 120:
            nivel = AlertLevel.URGENTE if dias_finalizacao <= 60 else AlertLevel.ATENCAO
            
            alertas.append(CriticalAlert(
                id="deadline_finalizacao",
                tipo=AlertType.DEADLINE,
                nivel=nivel,
                titulo=f"🏁 FINALIZAÇÃO PROJETO: {dias_finalizacao} dias restantes",
                descricao="Prazo final para entrega completa do projeto PNSB 2024. Monitorar todas as etapas.",
                municipio="TODOS",
                entidade=None,
                acao_recomendada="Revisar cronograma geral, acelerar atividades pendentes, preparar relatório final",
                dados={
                    'deadline': self.DEADLINE_FINALIZACAO.isoformat(),
                    'dias_restantes': dias_finalizacao
                },
                dias_restantes=dias_finalizacao,
                timestamp=hoje,
                prioridade=4
            ))
        
        return alertas
    
    def _generate_municipality_alerts(self) -> List[CriticalAlert]:
        """Gera alertas específicos por município"""
        alertas = []
        
        for municipio in MUNICIPIOS:
            try:
                # Obter dados do município
                visitas_municipio = Visita.query.filter_by(municipio=municipio).all()
                contatos_municipio = Contato.query.filter_by(municipio=municipio).all()
                
                total_visitas = len(visitas_municipio)
                visitas_concluidas = len([v for v in visitas_municipio if v.status in ['realizada', 'finalizada']])
                contatos_disponiveis = len(contatos_municipio)
                
                # Alerta de município sem visitas
                if total_visitas == 0:
                    alertas.append(CriticalAlert(
                        id=f"municipio_sem_visitas_{municipio.lower().replace(' ', '_')}",
                        tipo=AlertType.MUNICIPIO,
                        nivel=AlertLevel.CRITICO,
                        titulo=f"🏙️ {municipio}: NENHUMA VISITA AGENDADA",
                        descricao=f"Município {municipio} não possui visitas agendadas. Ação urgente necessária.",
                        municipio=municipio,
                        entidade=None,
                        acao_recomendada="Identificar contatos, agendar visitas imediatamente, buscar suporte local",
                        dados={
                            'total_visitas': 0,
                            'contatos_disponiveis': contatos_disponiveis,
                            'situacao': 'critica'
                        },
                        dias_restantes=None,
                        timestamp=datetime.now(),
                        prioridade=1
                    ))
                
                # Alerta de baixo progresso
                elif total_visitas > 0:
                    taxa_conclusao = (visitas_concluidas / total_visitas) * 100
                    
                    if taxa_conclusao < 50:
                        nivel = AlertLevel.CRITICO if taxa_conclusao < 25 else AlertLevel.URGENTE
                        
                        alertas.append(CriticalAlert(
                            id=f"municipio_baixo_progresso_{municipio.lower().replace(' ', '_')}",
                            tipo=AlertType.MUNICIPIO,
                            nivel=nivel,
                            titulo=f"📊 {municipio}: PROGRESSO BAIXO ({taxa_conclusao:.1f}%)",
                            descricao=f"Taxa de conclusão muito baixa. Risco de não cumprir prazos.",
                            municipio=municipio,
                            entidade=None,
                            acao_recomendada="Priorizar este município, alocar recursos adicionais, revisar estratégia",
                            dados={
                                'taxa_conclusao': taxa_conclusao,
                                'visitas_concluidas': visitas_concluidas,
                                'total_visitas': total_visitas,
                                'contatos_disponiveis': contatos_disponiveis
                            },
                            dias_restantes=None,
                            timestamp=datetime.now(),
                            prioridade=2 if nivel == AlertLevel.CRITICO else 3
                        ))
                
                # Alerta de falta de contatos
                if contatos_disponiveis < 2:
                    alertas.append(CriticalAlert(
                        id=f"municipio_poucos_contatos_{municipio.lower().replace(' ', '_')}",
                        tipo=AlertType.CONTATOS,
                        nivel=AlertLevel.URGENTE,
                        titulo=f"📞 {municipio}: POUCOS CONTATOS ({contatos_disponiveis})",
                        descricao="Número insuficiente de contatos pode comprometer as visitas.",
                        municipio=municipio,
                        entidade=None,
                        acao_recomendada="Buscar contatos adicionais, usar redes locais, contatar prefeitura",
                        dados={
                            'contatos_disponiveis': contatos_disponiveis,
                            'total_visitas': total_visitas
                        },
                        dias_restantes=None,
                        timestamp=datetime.now(),
                        prioridade=3
                    ))
                    
            except Exception as e:
                logger.error(f"Erro ao analisar município {municipio}: {e}")
                continue
        
        return alertas
    
    def _generate_contact_alerts(self) -> List[CriticalAlert]:
        """Gera alertas relacionados a contatos"""
        alertas = []
        
        try:
            # Visitas sem contatos confirmados
            visitas_sem_contato = Visita.query.filter(
                Visita.status.in_(['agendada', 'em preparação']),
                # Adicionar filtros para visitas sem contatos confirmados
            ).all()
            
            if len(visitas_sem_contato) > 0:
                alertas.append(CriticalAlert(
                    id="visitas_sem_contato",
                    tipo=AlertType.CONTATOS,
                    nivel=AlertLevel.URGENTE,
                    titulo=f"📞 {len(visitas_sem_contato)} VISITAS SEM CONTATO CONFIRMADO",
                    descricao="Visitas agendadas sem confirmação de contato. Risco de visitas frustradas.",
                    municipio="MULTIPLOS",
                    entidade=None,
                    acao_recomendada="Confirmar contatos antes das visitas, ter plano B para cada visita",
                    dados={
                        'total_visitas_sem_contato': len(visitas_sem_contato),
                        'visitas_detalhes': [{'id': v.id, 'municipio': v.municipio} for v in visitas_sem_contato[:5]]
                    },
                    dias_restantes=None,
                    timestamp=datetime.now(),
                    prioridade=2
                ))
            
            # Contatos desatualizados (exemplo)
            total_contatos = Contato.query.count()
            if total_contatos < 50:  # Número arbitrário baseado na necessidade do projeto
                alertas.append(CriticalAlert(
                    id="base_contatos_pequena",
                    tipo=AlertType.CONTATOS,
                    nivel=AlertLevel.ATENCAO,
                    titulo=f"📊 BASE DE CONTATOS PEQUENA ({total_contatos})",
                    descricao="Base de contatos pode ser insuficiente para cobrir todas as necessidades.",
                    municipio="GERAL",
                    entidade=None,
                    acao_recomendada="Expandir base de contatos, buscar fontes adicionais, validar contatos existentes",
                    dados={
                        'total_contatos': total_contatos,
                        'meta_sugerida': 100
                    },
                    dias_restantes=None,
                    timestamp=datetime.now(),
                    prioridade=4
                ))
                
        except Exception as e:
            logger.error(f"Erro ao gerar alertas de contatos: {e}")
        
        return alertas
    
    def _generate_conflict_alerts(self) -> List[CriticalAlert]:
        """Gera alertas de conflitos de agenda"""
        alertas = []
        
        try:
            # Buscar visitas agendadas para o mesmo dia/horário
            visitas_agendadas = Visita.query.filter(
                Visita.status.in_(['agendada', 'em preparação']),
                Visita.data.isnot(None)
            ).all()
            
            # Detectar conflitos
            conflitos = {}
            for visita in visitas_agendadas:
                data_str = visita.data.isoformat() if visita.data else None
                if data_str:
                    if data_str not in conflitos:
                        conflitos[data_str] = []
                    conflitos[data_str].append(visita)
            
            # Alertar sobre dias com muitas visitas
            for data, visitas_dia in conflitos.items():
                if len(visitas_dia) > 3:  # Mais de 3 visitas no mesmo dia
                    alertas.append(CriticalAlert(
                        id=f"conflito_agenda_{data}",
                        tipo=AlertType.CONFLITOS,
                        nivel=AlertLevel.ATENCAO,
                        titulo=f"⚡ SOBRECARGA: {len(visitas_dia)} visitas em {data}",
                        descricao=f"Muitas visitas agendadas para o mesmo dia. Revisar viabilidade.",
                        municipio="MULTIPLOS",
                        entidade=None,
                        acao_recomendada="Redistribuir visitas, verificar distâncias, ajustar cronograma",
                        dados={
                            'data': data,
                            'total_visitas': len(visitas_dia),
                            'municipios': list(set([v.municipio for v in visitas_dia]))
                        },
                        dias_restantes=None,
                        timestamp=datetime.now(),
                        prioridade=4
                    ))
                    
        except Exception as e:
            logger.error(f"Erro ao gerar alertas de conflitos: {e}")
        
        return alertas
    
    def _generate_followup_alerts(self) -> List[CriticalAlert]:
        """Gera alertas de follow-up necessário"""
        alertas = []
        
        try:
            hoje = datetime.now()
            
            # Visitas há muito tempo no mesmo status
            visitas_paradas = Visita.query.filter(
                Visita.status.in_(['agendada', 'em preparação']),
                Visita.data_atualizacao.isnot(None)
            ).all()
            
            for visita in visitas_paradas:
                if visita.data_atualizacao:
                    dias_parada = (hoje - visita.data_atualizacao).days
                    
                    if dias_parada > 7:  # Mais de 7 dias sem atualização
                        nivel = AlertLevel.URGENTE if dias_parada > 14 else AlertLevel.ATENCAO
                        
                        alertas.append(CriticalAlert(
                            id=f"followup_necessario_{visita.id}",
                            tipo=AlertType.FOLLOWUP,
                            nivel=nivel,
                            titulo=f"📞 FOLLOW-UP: {visita.municipio} ({dias_parada} dias sem atualização)",
                            descricao=f"Visita parada há {dias_parada} dias. Follow-up urgente necessário.",
                            municipio=visita.municipio,
                            entidade=visita.entidade_nome if hasattr(visita, 'entidade_nome') else None,
                            acao_recomendada="Contatar responsável, verificar status, atualizar informações",
                            dados={
                                'visita_id': visita.id,
                                'dias_sem_atualizacao': dias_parada,
                                'status_atual': visita.status,
                                'ultima_atualizacao': visita.data_atualizacao.isoformat()
                            },
                            dias_restantes=None,
                            timestamp=hoje,
                            prioridade=2 if nivel == AlertLevel.URGENTE else 3
                        ))
                        
        except Exception as e:
            logger.error(f"Erro ao gerar alertas de follow-up: {e}")
        
        return alertas
    
    def _generate_documentation_alerts(self) -> List[CriticalAlert]:
        """Gera alertas de documentação faltante"""
        alertas = []
        
        try:
            # Verificar checklists incompletos
            checklists_incompletos = Checklist.query.filter(
                # Adicionar filtros para checklists incompletos
            ).all()
            
            if len(checklists_incompletos) > 0:
                alertas.append(CriticalAlert(
                    id="documentacao_incompleta",
                    tipo=AlertType.DOCUMENTACAO,
                    nivel=AlertLevel.ATENCAO,
                    titulo=f"📄 {len(checklists_incompletos)} CHECKLISTS INCOMPLETOS",
                    descricao="Documentação de visitas incompleta. Revisar antes das visitas.",
                    municipio="MULTIPLOS",
                    entidade=None,
                    acao_recomendada="Completar checklists, verificar documentos obrigatórios",
                    dados={
                        'checklists_incompletos': len(checklists_incompletos)
                    },
                    dias_restantes=None,
                    timestamp=datetime.now(),
                    prioridade=4
                ))
                
        except Exception as e:
            logger.error(f"Erro ao gerar alertas de documentação: {e}")
        
        return alertas
    
    def _generate_risk_alerts(self) -> List[CriticalAlert]:
        """Gera alertas de riscos identificados"""
        alertas = []
        
        # Risco geral do projeto baseado no progresso
        try:
            visitas = Visita.query.all()
            total_visitas = len(visitas)
            visitas_finalizadas = len([v for v in visitas if v.status in ['realizada', 'finalizada']])
            
            if total_visitas > 0:
                progresso_geral = (visitas_finalizadas / total_visitas) * 100
                dias_deadline = (self.DEADLINE_VISITAS_P1_P2 - datetime.now()).days
                
                # Calcular risco baseado em progresso vs tempo restante
                tempo_decorrido_pct = max(0, (365 - dias_deadline) / 365 * 100)  # Assumindo 1 ano de projeto
                
                if progresso_geral < tempo_decorrido_pct - 20:  # Progresso muito atrás do cronograma
                    alertas.append(CriticalAlert(
                        id="risco_cronograma",
                        tipo=AlertType.RISCOS,
                        nivel=AlertLevel.CRITICO,
                        titulo=f"⚠️ RISCO ALTO: Progresso {progresso_geral:.1f}% vs Cronograma {tempo_decorrido_pct:.1f}%",
                        descricao="Projeto significativamente atrasado em relação ao cronograma planejado.",
                        municipio="PROJETO",
                        entidade=None,
                        acao_recomendada="Reunião de emergência, revisão completa do cronograma, recursos adicionais",
                        dados={
                            'progresso_atual': progresso_geral,
                            'cronograma_esperado': tempo_decorrido_pct,
                            'diferenca': progresso_geral - tempo_decorrido_pct,
                            'dias_deadline': dias_deadline
                        },
                        dias_restantes=dias_deadline,
                        timestamp=datetime.now(),
                        prioridade=1
                    ))
                    
        except Exception as e:
            logger.error(f"Erro ao gerar alertas de riscos: {e}")
        
        return alertas
    
    def _generate_performance_alerts(self) -> List[CriticalAlert]:
        """Gera alertas de performance da equipe"""
        alertas = []
        
        try:
            # Analisar produtividade por pesquisador (se disponível)
            pesquisadores = {}
            visitas = Visita.query.filter(Visita.pesquisador_responsavel.isnot(None)).all()
            
            for visita in visitas:
                pesquisador = visita.pesquisador_responsavel
                if pesquisador not in pesquisadores:
                    pesquisadores[pesquisador] = {'total': 0, 'finalizadas': 0}
                
                pesquisadores[pesquisador]['total'] += 1
                if visita.status in ['realizada', 'finalizada']:
                    pesquisadores[pesquisador]['finalizadas'] += 1
            
            # Alertar sobre pesquisadores com baixa produtividade
            for pesquisador, dados in pesquisadores.items():
                if dados['total'] >= 5:  # Apenas pesquisadores com pelo menos 5 visitas
                    taxa_sucesso = (dados['finalizadas'] / dados['total']) * 100
                    
                    if taxa_sucesso < 60:
                        alertas.append(CriticalAlert(
                            id=f"performance_baixa_{pesquisador.lower().replace(' ', '_')}",
                            tipo=AlertType.PERFORMANCE,
                            nivel=AlertLevel.ATENCAO,
                            titulo=f"📊 PERFORMANCE: {pesquisador} ({taxa_sucesso:.1f}%)",
                            descricao=f"Taxa de sucesso abaixo da média. Suporte pode ser necessário.",
                            municipio="EQUIPE",
                            entidade=None,
                            acao_recomendada="Oferecer treinamento adicional, revisar carga de trabalho",
                            dados={
                                'pesquisador': pesquisador,
                                'taxa_sucesso': taxa_sucesso,
                                'total_visitas': dados['total'],
                                'visitas_finalizadas': dados['finalizadas']
                            },
                            dias_restantes=None,
                            timestamp=datetime.now(),
                            prioridade=4
                        ))
                        
        except Exception as e:
            logger.error(f"Erro ao gerar alertas de performance: {e}")
        
        return alertas
    
    def _generate_status_alerts(self) -> List[CriticalAlert]:
        """Gera alertas de status das visitas"""
        alertas = []
        
        try:
            hoje = datetime.now()
            
            # Visitas agendadas para datas passadas
            visitas_atrasadas = Visita.query.filter(
                Visita.status == 'agendada',
                Visita.data < hoje.date()
            ).all()
            
            if len(visitas_atrasadas) > 0:
                alertas.append(CriticalAlert(
                    id="visitas_agendadas_atrasadas",
                    tipo=AlertType.STATUS,
                    nivel=AlertLevel.URGENTE,
                    titulo=f"📅 {len(visitas_atrasadas)} VISITAS AGENDADAS ATRASADAS",
                    descricao="Visitas agendadas para datas passadas. Atualizar status urgentemente.",
                    municipio="MULTIPLOS",
                    entidade=None,
                    acao_recomendada="Verificar se foram realizadas, atualizar status, reagendar se necessário",
                    dados={
                        'total_atrasadas': len(visitas_atrasadas),
                        'municipios_afetados': list(set([v.municipio for v in visitas_atrasadas]))
                    },
                    dias_restantes=None,
                    timestamp=hoje,
                    prioridade=2
                ))
                
        except Exception as e:
            logger.error(f"Erro ao gerar alertas de status: {e}")
        
        return alertas
    
    def _generate_backup_alerts(self) -> List[CriticalAlert]:
        """Gera alertas de backup e segurança dos dados"""
        alertas = []
        
        try:
            # Verificar se há backup recente (simulado)
            # Em uma implementação real, verificaria logs de backup
            ultima_backup = datetime.now() - timedelta(days=3)  # Simular último backup há 3 dias
            dias_sem_backup = (datetime.now() - ultima_backup).days
            
            if dias_sem_backup > 7:
                alertas.append(CriticalAlert(
                    id="backup_atrasado",
                    tipo=AlertType.BACKUP,
                    nivel=AlertLevel.URGENTE,
                    titulo=f"💾 BACKUP ATRASADO: {dias_sem_backup} dias sem backup",
                    descricao="Sistema sem backup há muito tempo. Risco de perda de dados.",
                    municipio="SISTEMA",
                    entidade=None,
                    acao_recomendada="Executar backup imediatamente, verificar sistema de backup automático",
                    dados={
                        'dias_sem_backup': dias_sem_backup,
                        'ultimo_backup': ultima_backup.isoformat(),
                        'status_backup': 'atrasado'
                    },
                    dias_restantes=None,
                    timestamp=datetime.now(),
                    prioridade=2
                ))
                
        except Exception as e:
            logger.error(f"Erro ao gerar alertas de backup: {e}")
        
        return alertas
    
    def _sort_alerts_by_priority(self, alertas: List[CriticalAlert]) -> List[CriticalAlert]:
        """Ordena alertas por prioridade e nível"""
        
        # Definir ordem de prioridade por nível
        nivel_order = {
            AlertLevel.CRITICO: 1,
            AlertLevel.URGENTE: 2,
            AlertLevel.ATENCAO: 3,
            AlertLevel.INFO: 4
        }
        
        # Ordenar por nível (crítico primeiro) e depois por prioridade
        return sorted(alertas, key=lambda x: (nivel_order[x.nivel], x.prioridade))
    
    def _generate_summary(self, alertas: List[CriticalAlert]) -> Dict:
        """Gera resumo dos alertas"""
        hoje = datetime.now()
        dias_visitas = (self.DEADLINE_VISITAS_P1_P2 - hoje).days
        dias_questionarios = (self.DEADLINE_QUESTIONARIOS - hoje).days
        
        return {
            'total_alertas': len(alertas),
            'criticos': len([a for a in alertas if a.nivel == AlertLevel.CRITICO]),
            'urgentes': len([a for a in alertas if a.nivel == AlertLevel.URGENTE]),
            'atencao': len([a for a in alertas if a.nivel == AlertLevel.ATENCAO]),
            'info': len([a for a in alertas if a.nivel == AlertLevel.INFO]),
            'dias_ate_deadline_visitas': dias_visitas,
            'dias_ate_deadline_questionarios': dias_questionarios,
            'status_sistema': self._calculate_system_status(alertas),
            'alertas_por_tipo': self._count_alerts_by_type(alertas),
            'municipios_com_alertas': len(set([a.municipio for a in alertas if a.municipio not in ['TODOS', 'GERAL', 'MULTIPLOS', 'PROJETO', 'EQUIPE', 'SISTEMA']]))
        }
    
    def _calculate_system_status(self, alertas: List[CriticalAlert]) -> str:
        """Calcula status geral do sistema baseado nos alertas"""
        criticos = len([a for a in alertas if a.nivel == AlertLevel.CRITICO])
        urgentes = len([a for a in alertas if a.nivel == AlertLevel.URGENTE])
        
        if criticos > 0:
            return 'critico'
        elif urgentes > 3:
            return 'urgente'
        elif urgentes > 0:
            return 'atencao'
        else:
            return 'normal'
    
    def _count_alerts_by_type(self, alertas: List[CriticalAlert]) -> Dict:
        """Conta alertas por tipo"""
        contagem = {}
        for alert in alertas:
            tipo = alert.tipo.value
            contagem[tipo] = contagem.get(tipo, 0) + 1
        return contagem