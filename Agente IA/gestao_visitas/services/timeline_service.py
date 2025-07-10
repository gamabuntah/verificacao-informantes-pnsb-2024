"""
Sistema de Timeline de Progresso Funcional para o Projeto PNSB 2024
Calcula e monitora o progresso temporal das visitas e questionários
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from gestao_visitas.models.agendamento import Visita
from gestao_visitas.models.questionarios_obrigatorios import ProgressoQuestionarios
from gestao_visitas.db import db
from gestao_visitas.config import MUNICIPIOS

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimelinePhase(Enum):
    INICIO = "inicio"
    PLANEJAMENTO = "planejamento"
    EXECUCAO_INICIAL = "execucao_inicial"
    ACELERACAO = "aceleracao"
    RETA_FINAL = "reta_final"
    CONCLUSAO = "conclusao"

@dataclass
class TimelineMilestone:
    """Representa um marco temporal do projeto"""
    id: str
    nome: str
    data_prevista: datetime
    data_real: Optional[datetime]
    progresso_necessario: float  # Porcentagem de progresso necessária
    status: str  # 'pendente', 'em_andamento', 'concluido', 'atrasado'
    descricao: str
    criticidade: str  # 'baixa', 'media', 'alta', 'critica'

@dataclass
class TimelineMetrics:
    """Métricas calculadas do timeline"""
    progresso_atual: float
    progresso_esperado: float
    dias_decorridos: int
    dias_restantes_visitas: int
    dias_restantes_questionarios: int
    velocidade_diaria: float
    velocidade_semanal: float
    previsao_conclusao: datetime
    status_geral: str
    fase_atual: TimelinePhase
    atraso_dias: int
    risco_nivel: str

class TimelineService:
    """
    Sistema de Timeline de Progresso Funcional para PNSB 2024
    
    Monitora e calcula métricas temporais específicas do projeto,
    incluindo prazos reais, milestones e previsões inteligentes.
    """
    
    def __init__(self, db_session):
        self.db = db_session
        
        # Datas críticas reais do PNSB 2024
        self.DATA_INICIO = datetime(2025, 6, 9)  # Início efetivo da pesquisa
        self.DATA_DEADLINE_VISITAS = datetime(2025, 9, 19)  # Deadline visitas P1+P2
        self.DATA_DEADLINE_QUESTIONARIOS = datetime(2025, 10, 17)  # Deadline questionários
        self.DATA_FINALIZACAO = datetime(2025, 12, 15)  # Entrega final do projeto
        
        # Milestones do projeto
        self.milestones = self._initialize_milestones()
        
        logger.info("TimelineService inicializado com sucesso")
    
    def _initialize_milestones(self) -> List[TimelineMilestone]:
        """Inicializa os milestones do projeto PNSB"""
        return [
            TimelineMilestone(
                id="inicio_projeto",
                nome="Início do Projeto",
                data_prevista=self.DATA_INICIO,
                data_real=self.DATA_INICIO,
                progresso_necessario=0.0,
                status="concluido",
                descricao="Marco inicial da pesquisa PNSB 2024",
                criticidade="baixa"
            ),
            TimelineMilestone(
                id="25_questionarios",
                nome="25% dos Questionários",
                data_prevista=self.DATA_INICIO + timedelta(days=30),
                data_real=None,
                progresso_necessario=25.0,
                status="pendente",
                descricao="Primeiro quartil de questionários concluídos",
                criticidade="media"
            ),
            TimelineMilestone(
                id="50_questionarios",
                nome="50% dos Questionários",
                data_prevista=self.DATA_INICIO + timedelta(days=60),
                data_real=None,
                progresso_necessario=50.0,
                status="pendente",
                descricao="Metade dos questionários concluídos",
                criticidade="alta"
            ),
            TimelineMilestone(
                id="deadline_visitas",
                nome="Deadline Visitas P1+P2",
                data_prevista=self.DATA_DEADLINE_VISITAS,
                data_real=None,
                progresso_necessario=85.0,
                status="pendente",
                descricao="Prazo final para visitas prioritárias",
                criticidade="critica"
            ),
            TimelineMilestone(
                id="75_questionarios",
                nome="75% dos Questionários",
                data_prevista=self.DATA_DEADLINE_VISITAS + timedelta(days=14),
                data_real=None,
                progresso_necessario=75.0,
                status="pendente",
                descricao="Terceiro quartil de questionários concluídos",
                criticidade="alta"
            ),
            TimelineMilestone(
                id="deadline_questionarios",
                nome="Deadline Questionários",
                data_prevista=self.DATA_DEADLINE_QUESTIONARIOS,
                data_real=None,
                progresso_necessario=100.0,
                status="pendente",
                descricao="Prazo final para questionários",
                criticidade="critica"
            ),
            TimelineMilestone(
                id="finalizacao_projeto",
                nome="Finalização do Projeto",
                data_prevista=self.DATA_FINALIZACAO,
                data_real=None,
                progresso_necessario=100.0,
                status="pendente",
                descricao="Entrega final completa",
                criticidade="critica"
            )
        ]
    
    def get_timeline_metrics(self) -> TimelineMetrics:
        """
        Calcula todas as métricas do timeline baseadas nos dados atuais
        
        Returns:
            TimelineMetrics com todos os cálculos atualizados
        """
        try:
            logger.info("Calculando métricas do timeline PNSB")
            
            # Data atual
            hoje = datetime.now()
            
            # Calcular progresso atual baseado nos questionários
            progresso_atual = self._calculate_current_progress()
            
            # Calcular progresso esperado baseado no tempo
            progresso_esperado = self._calculate_expected_progress(hoje)
            
            # Calcular dias
            dias_decorridos = (hoje - self.DATA_INICIO).days
            dias_restantes_visitas = max(0, (self.DATA_DEADLINE_VISITAS - hoje).days)
            dias_restantes_questionarios = max(0, (self.DATA_DEADLINE_QUESTIONARIOS - hoje).days)
            
            # Calcular velocidades
            velocidade_diaria = progresso_atual / max(1, dias_decorridos)
            velocidade_semanal = velocidade_diaria * 7
            
            # Calcular previsão de conclusão
            previsao_conclusao = self._calculate_completion_forecast(
                progresso_atual, velocidade_diaria, hoje
            )
            
            # Determinar status geral
            status_geral = self._determine_overall_status(
                progresso_atual, progresso_esperado, dias_restantes_questionarios
            )
            
            # Determinar fase atual
            fase_atual = self._determine_current_phase(progresso_atual, dias_decorridos)
            
            # Calcular atraso
            atraso_dias = max(0, int((progresso_esperado - progresso_atual) / velocidade_diaria)) if velocidade_diaria > 0 else 0
            
            # Avaliar nível de risco
            risco_nivel = self._assess_risk_level(
                progresso_atual, progresso_esperado, dias_restantes_questionarios
            )
            
            metrics = TimelineMetrics(
                progresso_atual=progresso_atual,
                progresso_esperado=progresso_esperado,
                dias_decorridos=dias_decorridos,
                dias_restantes_visitas=dias_restantes_visitas,
                dias_restantes_questionarios=dias_restantes_questionarios,
                velocidade_diaria=velocidade_diaria,
                velocidade_semanal=velocidade_semanal,
                previsao_conclusao=previsao_conclusao,
                status_geral=status_geral,
                fase_atual=fase_atual,
                atraso_dias=atraso_dias,
                risco_nivel=risco_nivel
            )
            
            logger.info(f"Métricas calculadas: {progresso_atual:.1f}% progresso, fase {fase_atual.value}")
            return metrics
            
        except Exception as e:
            logger.error(f"Erro ao calcular métricas do timeline: {e}")
            raise
    
    def _calculate_current_progress(self) -> float:
        """Calcula o progresso atual baseado nos questionários concluídos"""
        try:
            total_questionarios = 0
            questionarios_concluidos = 0
            
            for municipio in MUNICIPIOS:
                # Usar a função estática que retorna um dicionário
                progresso_dict = ProgressoQuestionarios.calcular_progresso_municipio(municipio)
                
                # Somar questionários obrigatórios
                mrs_obrigatorios = progresso_dict.get('total_mrs_obrigatorios', 0)
                map_obrigatorios = progresso_dict.get('total_map_obrigatorios', 0)
                mrs_concluidos = progresso_dict.get('mrs_concluidos', 0)
                map_concluidos = progresso_dict.get('map_concluidos', 0)
                
                total_questionarios += mrs_obrigatorios + map_obrigatorios
                questionarios_concluidos += mrs_concluidos + map_concluidos
            
            return (questionarios_concluidos / total_questionarios * 100) if total_questionarios > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Erro ao calcular progresso atual: {e}")
            return 0.0
    
    def _calculate_expected_progress(self, hoje: datetime) -> float:
        """Calcula o progresso esperado baseado no cronograma ideal"""
        # Tempo total do projeto (início até deadline de questionários)
        tempo_total = (self.DATA_DEADLINE_QUESTIONARIOS - self.DATA_INICIO).days
        tempo_decorrido = (hoje - self.DATA_INICIO).days
        
        # Curva de progresso não-linear (aceleração no meio do projeto)
        if tempo_decorrido <= 0:
            return 0.0
        elif tempo_decorrido >= tempo_total:
            return 100.0
        else:
            # Curva sigmoidal suave para simular aceleração realística
            progress_ratio = tempo_decorrido / tempo_total
            # Ajustar para cronograma mais realístico (início mais lento, aceleração no meio)
            return min(100.0, progress_ratio * 85 + (progress_ratio ** 2) * 15)
    
    def _calculate_completion_forecast(self, progresso_atual: float, velocidade_diaria: float, hoje: datetime) -> datetime:
        """Calcula previsão de conclusão baseada na velocidade atual"""
        if velocidade_diaria <= 0:
            return self.DATA_DEADLINE_QUESTIONARIOS + timedelta(days=90)  # Estimativa pessimista
        
        progresso_restante = 100.0 - progresso_atual
        dias_para_conclusao = progresso_restante / velocidade_diaria
        
        return hoje + timedelta(days=int(dias_para_conclusao))
    
    def _determine_overall_status(self, progresso_atual: float, progresso_esperado: float, dias_restantes: int) -> str:
        """Determina o status geral do projeto"""
        diferenca = progresso_atual - progresso_esperado
        
        if progresso_atual >= 100:
            return "concluido"
        elif dias_restantes <= 7 and progresso_atual < 95:
            return "critico"
        elif diferenca < -15:
            return "atrasado"
        elif diferenca < -5:
            return "atencao"
        elif diferenca > 10:
            return "adiantado"
        else:
            return "no_prazo"
    
    def _determine_current_phase(self, progresso_atual: float, dias_decorridos: int) -> TimelinePhase:
        """Determina a fase atual do projeto"""
        if progresso_atual >= 95:
            return TimelinePhase.CONCLUSAO
        elif progresso_atual >= 75:
            return TimelinePhase.RETA_FINAL
        elif progresso_atual >= 40:
            return TimelinePhase.ACELERACAO
        elif progresso_atual >= 15:
            return TimelinePhase.EXECUCAO_INICIAL
        elif dias_decorridos > 14:
            return TimelinePhase.PLANEJAMENTO
        else:
            return TimelinePhase.INICIO
    
    def _assess_risk_level(self, progresso_atual: float, progresso_esperado: float, dias_restantes: int) -> str:
        """Avalia o nível de risco do projeto"""
        atraso = progresso_esperado - progresso_atual
        
        if dias_restantes <= 7 and progresso_atual < 90:
            return "critico"
        elif dias_restantes <= 21 and progresso_atual < 70:
            return "alto"
        elif atraso > 20:
            return "alto"
        elif atraso > 10:
            return "medio"
        elif atraso > 0:
            return "baixo"
        else:
            return "normal"
    
    def get_updated_milestones(self) -> List[Dict]:
        """Retorna milestones atualizados com status atual"""
        try:
            progresso_atual = self._calculate_current_progress()
            hoje = datetime.now()
            
            milestones_updated = []
            
            for milestone in self.milestones:
                milestone_dict = {
                    'id': milestone.id,
                    'nome': milestone.nome,
                    'data_prevista': milestone.data_prevista.isoformat(),
                    'data_real': milestone.data_real.isoformat() if milestone.data_real else None,
                    'progresso_necessario': milestone.progresso_necessario,
                    'descricao': milestone.descricao,
                    'criticidade': milestone.criticidade
                }
                
                # Atualizar status baseado no progresso atual
                if progresso_atual >= milestone.progresso_necessario:
                    milestone_dict['status'] = 'concluido'
                elif progresso_atual >= milestone.progresso_necessario - 5:
                    milestone_dict['status'] = 'em_andamento'
                elif milestone.data_prevista < hoje and progresso_atual < milestone.progresso_necessario:
                    milestone_dict['status'] = 'atrasado'
                else:
                    milestone_dict['status'] = 'pendente'
                
                milestones_updated.append(milestone_dict)
            
            return milestones_updated
            
        except Exception as e:
            logger.error(f"Erro ao atualizar milestones: {e}")
            return []
    
    def get_weekly_breakdown(self) -> Dict:
        """Retorna breakdown semanal do progresso"""
        try:
            hoje = datetime.now()
            metrics = self.get_timeline_metrics()
            
            # Calcular semanas
            semanas_total = ((self.DATA_DEADLINE_QUESTIONARIOS - self.DATA_INICIO).days + 6) // 7
            semanas_decorridas = max(1, ((hoje - self.DATA_INICIO).days + 6) // 7)
            
            # Projeções semanais
            semanas_restantes = max(0, semanas_total - semanas_decorridas)
            progresso_necessario_por_semana = (100 - metrics.progresso_atual) / max(1, semanas_restantes)
            
            return {
                'semanas_total': semanas_total,
                'semanas_decorridas': semanas_decorridas,
                'semanas_restantes': semanas_restantes,
                'progresso_semanal_atual': metrics.velocidade_semanal,
                'progresso_semanal_necessario': progresso_necessario_por_semana,
                'eficiencia_semanal': (metrics.velocidade_semanal / progresso_necessario_por_semana * 100) if progresso_necessario_por_semana > 0 else 100,
                'previsao_conclusao_semanas': int((100 - metrics.progresso_atual) / max(0.1, metrics.velocidade_semanal))
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular breakdown semanal: {e}")
            return {}
    
    def get_phase_description(self, fase: TimelinePhase) -> str:
        """Retorna descrição da fase atual"""
        descriptions = {
            TimelinePhase.INICIO: "🏁 Início da Jornada - Planejamento e organização inicial",
            TimelinePhase.PLANEJAMENTO: "📋 Planejamento Ativo - Definindo estratégias e recursos",
            TimelinePhase.EXECUCAO_INICIAL: "🚀 Execução Inicial - Primeiras visitas e coleta de dados",
            TimelinePhase.ACELERACAO: "⚡ Fase de Aceleração - Ritmo intenso de trabalho",
            TimelinePhase.RETA_FINAL: "🎯 Reta Final - Foco na conclusão dos objetivos",
            TimelinePhase.CONCLUSAO: "🏆 Conclusão - Finalizando e entregando resultados"
        }
        return descriptions.get(fase, "📊 Fase em Progresso")