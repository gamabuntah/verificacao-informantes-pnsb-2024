"""
Assistente de Estratégia Local Funcional para o Sistema PNSB
Sistema inteligente que analisa dados reais e gera estratégias personalizadas
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import statistics

from gestao_visitas.models.agendamento import Visita
from gestao_visitas.models.contatos import Contato, TipoEntidade
from gestao_visitas.db import db
from gestao_visitas.config import MUNICIPIOS

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MunicipalityProfile:
    """Perfil de um município baseado em dados reais"""
    nome: str
    codigo: str
    total_visitas: int
    visitas_concluidas: int
    taxa_sucesso: float
    tempo_medio_resposta: Optional[float]
    contatos_disponiveis: int
    entidades_prioritarias: List[str]
    desafios_identificados: List[str]
    melhor_horario: str
    melhor_dia_semana: str
    canal_preferido: str
    nivel_cooperacao: str
    risco_atual: str

@dataclass
class StrategyRecommendation:
    """Recomendação de estratégia para um município"""
    tipo: str
    titulo: str
    descricao: str
    acoes: List[str]
    probabilidade_sucesso: float
    prioridade: str
    timing: str
    recursos_necessarios: List[str]
    observacoes: List[str]

class StrategyAssistantService:
    """
    Assistente de Estratégia Local Funcional
    
    Analisa dados reais do projeto PNSB e gera estratégias personalizadas
    para maximizar o sucesso das visitas em cada município.
    """
    
    def __init__(self, db_session):
        self.db = db_session
        
        # Cache para otimizar consultas
        self._cache = {}
        self._cache_timestamp = None
        self._cache_duration = 300  # 5 minutos
        
        # Configurações de IA
        self.ai_enabled = True
        
        logger.info("StrategyAssistantService inicializado com sucesso")
    
    def analyze_municipality(self, municipio: str) -> Dict:
        """
        Analisa um município específico e gera estratégias personalizadas
        
        Args:
            municipio: Nome do município para análise
            
        Returns:
            Dict com perfil do município e estratégias recomendadas
        """
        try:
            logger.info(f"Iniciando análise estratégica para {municipio}")
            
            # Validar município
            if municipio not in MUNICIPIOS:
                raise ValueError(f"Município {municipio} não está na lista do PNSB")
            
            # Obter perfil do município
            profile = self._get_municipality_profile(municipio)
            
            # Gerar estratégias personalizadas
            strategies = self._generate_strategies(profile)
            
            # Calcular métricas de progresso
            progress_metrics = self._calculate_progress_metrics(municipio)
            
            # Gerar insights com IA
            ai_insights = self._generate_ai_insights(profile, strategies)
            
            result = {
                'municipio': municipio,
                'profile': profile.__dict__,
                'strategies': [s.__dict__ for s in strategies],
                'progress_metrics': progress_metrics,
                'ai_insights': ai_insights,
                'generated_at': datetime.now().isoformat(),
                'confidence_score': self._calculate_overall_confidence(strategies)
            }
            
            logger.info(f"Análise concluída para {municipio} com {len(strategies)} estratégias")
            return result
            
        except Exception as e:
            logger.error(f"Erro na análise do município {municipio}: {e}")
            raise
    
    def analyze_all_municipalities(self) -> Dict:
        """
        Analisa todos os municípios do PNSB e gera relatório consolidado
        
        Returns:
            Dict com análise consolidada de todos os municípios
        """
        try:
            logger.info("Iniciando análise estratégica de todos os municípios")
            
            all_analyses = {}
            overall_metrics = {
                'total_municipios': len(MUNICIPIOS),
                'municipios_analisados': 0,
                'estrategias_geradas': 0,
                'risco_alto': 0,
                'risco_medio': 0,
                'risco_baixo': 0
            }
            
            for municipio in MUNICIPIOS:
                try:
                    analysis = self.analyze_municipality(municipio)
                    all_analyses[municipio] = analysis
                    
                    # Atualizar métricas gerais
                    overall_metrics['municipios_analisados'] += 1
                    overall_metrics['estrategias_geradas'] += len(analysis['strategies'])
                    
                    # Contabilizar riscos
                    risk_level = analysis['profile']['risco_atual']
                    if 'alto' in risk_level.lower():
                        overall_metrics['risco_alto'] += 1
                    elif 'medio' in risk_level.lower():
                        overall_metrics['risco_medio'] += 1
                    else:
                        overall_metrics['risco_baixo'] += 1
                        
                except Exception as e:
                    logger.error(f"Erro ao analisar {municipio}: {e}")
                    continue
            
            # Gerar recomendações gerais
            general_recommendations = self._generate_general_recommendations(all_analyses)
            
            result = {
                'overall_metrics': overall_metrics,
                'municipalities': all_analyses,
                'general_recommendations': general_recommendations,
                'generated_at': datetime.now().isoformat()
            }
            
            logger.info(f"Análise geral concluída: {overall_metrics['municipios_analisados']} municípios")
            return result
            
        except Exception as e:
            logger.error(f"Erro na análise geral: {e}")
            raise
    
    def _get_municipality_profile(self, municipio: str) -> MunicipalityProfile:
        """Constrói perfil detalhado do município baseado em dados reais"""
        try:
            # Buscar dados de visitas
            visitas = Visita.query.filter_by(municipio=municipio).all()
            total_visitas = len(visitas)
            visitas_concluidas = len([v for v in visitas if v.status in ['realizada', 'finalizada']])
            
            # Calcular taxa de sucesso
            taxa_sucesso = (visitas_concluidas / total_visitas * 100) if total_visitas > 0 else 0
            
            # Buscar contatos disponíveis
            contatos = Contato.query.filter_by(municipio=municipio).all()
            contatos_disponiveis = len(contatos)
            
            # Analisar tipos de entidades prioritárias
            entidades_prioritarias = self._identify_priority_entities(municipio)
            
            # Identificar desafios
            desafios = self._identify_challenges(visitas, contatos)
            
            # Analisar padrões temporais
            timing_data = self._analyze_timing_patterns(visitas)
            
            # Determinar nível de cooperação
            nivel_cooperacao = self._assess_cooperation_level(visitas, taxa_sucesso)
            
            # Calcular risco atual
            risco_atual = self._calculate_risk_level(taxa_sucesso, total_visitas, contatos_disponiveis)
            
            # Tempo médio de resposta (se disponível)
            tempo_medio_resposta = self._calculate_average_response_time(visitas)
            
            return MunicipalityProfile(
                nome=municipio,
                codigo=municipio.lower().replace(' ', '-'),
                total_visitas=total_visitas,
                visitas_concluidas=visitas_concluidas,
                taxa_sucesso=taxa_sucesso,
                tempo_medio_resposta=tempo_medio_resposta,
                contatos_disponiveis=contatos_disponiveis,
                entidades_prioritarias=entidades_prioritarias,
                desafios_identificados=desafios,
                melhor_horario=timing_data['melhor_horario'],
                melhor_dia_semana=timing_data['melhor_dia'],
                canal_preferido=self._determine_preferred_channel(contatos),
                nivel_cooperacao=nivel_cooperacao,
                risco_atual=risco_atual
            )
            
        except Exception as e:
            logger.error(f"Erro ao construir perfil do município {municipio}: {e}")
            raise
    
    def _generate_strategies(self, profile: MunicipalityProfile) -> List[StrategyRecommendation]:
        """Gera estratégias personalizadas baseadas no perfil do município"""
        strategies = []
        
        # Estratégia de Contato
        contact_strategy = self._generate_contact_strategy(profile)
        strategies.append(contact_strategy)
        
        # Estratégia de Abordagem
        approach_strategy = self._generate_approach_strategy(profile)
        strategies.append(approach_strategy)
        
        # Estratégia de Timing
        timing_strategy = self._generate_timing_strategy(profile)
        strategies.append(timing_strategy)
        
        # Estratégia de Follow-up
        followup_strategy = self._generate_followup_strategy(profile)
        strategies.append(followup_strategy)
        
        # Estratégias específicas baseadas nos desafios
        challenge_strategies = self._generate_challenge_specific_strategies(profile)
        strategies.extend(challenge_strategies)
        
        return strategies
    
    def _generate_contact_strategy(self, profile: MunicipalityProfile) -> StrategyRecommendation:
        """Gera estratégia de contato personalizada"""
        
        # Determinar probabilidade baseada em dados históricos
        prob_base = min(90, max(50, profile.taxa_sucesso + 20))
        
        # Ajustar baseado em contatos disponíveis
        if profile.contatos_disponiveis > 5:
            prob_base += 10
        elif profile.contatos_disponiveis < 2:
            prob_base -= 15
        
        acoes = []
        
        if profile.canal_preferido == 'telefone':
            acoes.extend([
                f"Contato telefônico direto no período da {profile.melhor_horario}",
                "Preparar script específico para o perfil do município",
                "Ter informações sobre benefícios locais em mãos"
            ])
        elif profile.canal_preferido == 'email':
            acoes.extend([
                "Envio de email formal com credenciais IBGE",
                "Anexar materiais informativos sobre a pesquisa",
                "Agendar follow-up telefônico em 2-3 dias"
            ])
        else:
            acoes.extend([
                "Abordagem multicanal: email + telefone + presencial se necessário",
                "Iniciar por email formal, seguir com telefone",
                "Preparar visita presencial como backup"
            ])
        
        # Ajustar ações baseadas nos desafios
        if 'falta_de_contatos' in profile.desafios_identificados:
            acoes.append("Buscar contatos alternativos através de redes locais")
        
        if 'resistencia_inicial' in profile.desafios_identificados:
            acoes.append("Enfatizar importância nacional da pesquisa e benefícios locais")
        
        return StrategyRecommendation(
            tipo="contato",
            titulo="Estratégia de Contato Otimizada",
            descricao=f"Abordagem personalizada baseada no perfil de {profile.nome} e histórico de {profile.taxa_sucesso:.1f}% de sucesso",
            acoes=acoes,
            probabilidade_sucesso=min(95, max(60, prob_base)),
            prioridade="alta" if profile.risco_atual == "Alto" else "media",
            timing=f"{profile.melhor_dia_semana} pela {profile.melhor_horario}",
            recursos_necessarios=["Telefone", "Email institucional", "Materiais informativos"],
            observacoes=[f"Taxa de sucesso histórica: {profile.taxa_sucesso:.1f}%", 
                        f"Contatos disponíveis: {profile.contatos_disponiveis}"]
        )
    
    def _generate_approach_strategy(self, profile: MunicipalityProfile) -> StrategyRecommendation:
        """Gera estratégia de abordagem personalizada"""
        
        prob_base = min(88, max(45, profile.taxa_sucesso + 15))
        
        # Ajustar baseado no nível de cooperação
        if profile.nivel_cooperacao == "Alto":
            prob_base += 15
        elif profile.nivel_cooperacao == "Baixo":
            prob_base -= 10
        
        acoes = []
        
        # Estratégia baseada no tamanho e tipo do município
        if profile.total_visitas > 10:  # Município grande
            acoes.extend([
                "Abordagem institucional formal através de gabinete",
                "Solicitar reunião com secretário responsável",
                "Apresentar cronograma detalhado e benefícios para a gestão"
            ])
        else:  # Município menor
            acoes.extend([
                "Contato direto com responsável técnico",
                "Abordagem mais pessoal e flexível",
                "Enfatizar importância da participação do município"
            ])
        
        # Adaptar à cooperação histórica
        if profile.nivel_cooperacao == "Baixo":
            acoes.extend([
                "Reforçar obrigatoriedade legal da pesquisa",
                "Apresentar casos de sucesso em municípios similares",
                "Oferecer suporte técnico adicional"
            ])
        
        # Focar nas entidades prioritárias identificadas
        if profile.entidades_prioritarias:
            acoes.append(f"Priorizar contato com: {', '.join(profile.entidades_prioritarias[:3])}")
        
        return StrategyRecommendation(
            tipo="abordagem",
            titulo="Abordagem Estratégica Personalizada",
            descricao=f"Estratégia adaptada ao perfil de cooperação {profile.nivel_cooperacao} e características locais",
            acoes=acoes,
            probabilidade_sucesso=min(92, max(50, prob_base)),
            prioridade="alta",
            timing="Executar após estabelecimento do primeiro contato",
            recursos_necessarios=["Materiais institucionais", "Cronograma flexível", "Suporte técnico"],
            observacoes=[f"Nível de cooperação: {profile.nivel_cooperacao}",
                        f"Entidades prioritárias identificadas: {len(profile.entidades_prioritarias)}"]
        )
    
    def _generate_timing_strategy(self, profile: MunicipalityProfile) -> StrategyRecommendation:
        """Gera estratégia de timing otimizada"""
        
        prob_base = min(85, max(60, 75))  # Base para timing
        
        acoes = [
            f"Contatos preferencialmente às {profile.melhor_horario}",
            f"Priorizar {profile.melhor_dia_semana} para agendamentos",
            "Evitar vésperas de feriados e final de mandatos"
        ]
        
        # Timing específico baseado no tempo médio de resposta
        if profile.tempo_medio_resposta:
            if profile.tempo_medio_resposta > 7:
                acoes.append("Iniciar contatos com antecedência de 2-3 semanas")
                acoes.append("Fazer follow-ups semanais")
            else:
                acoes.append("Contatos podem ser feitos com 1 semana de antecedência")
        
        # Urgência baseada no risco
        if profile.risco_atual == "Alto":
            acoes.extend([
                "URGENTE: Priorizar este município na agenda",
                "Alocar recursos adicionais se necessário"
            ])
        
        return StrategyRecommendation(
            tipo="timing",
            titulo="Timing Otimizado",
            descricao="Estratégia temporal baseada em padrões históricos de resposta",
            acoes=acoes,
            probabilidade_sucesso=prob_base,
            prioridade="media",
            timing="Aplicar imediatamente no planejamento",
            recursos_necessarios=["Calendário atualizado", "Sistema de follow-up"],
            observacoes=[f"Melhor período: {profile.melhor_dia_semana} {profile.melhor_horario}"]
        )
    
    def _generate_followup_strategy(self, profile: MunicipalityProfile) -> StrategyRecommendation:
        """Gera estratégia de follow-up personalizada"""
        
        prob_base = min(80, max(55, profile.taxa_sucesso + 10))
        
        acoes = [
            "Follow-up em 48-72h após primeiro contato",
            "Máximo de 3 tentativas de contato por canal",
            "Alternar entre email e telefone"
        ]
        
        # Personalizar baseado no perfil
        if profile.nivel_cooperacao == "Baixo":
            acoes.extend([
                "Follow-up mais frequente (a cada 2 dias)",
                "Usar diferentes argumentos a cada contato",
                "Considerar envolvimento de supervisor"
            ])
        elif profile.nivel_cooperacao == "Alto":
            acoes.extend([
                "Follow-up mais espaçado (semanal)",
                "Focar em aspectos técnicos e cronograma"
            ])
        
        return StrategyRecommendation(
            tipo="followup",
            titulo="Follow-up Inteligente",
            descricao="Estratégia de acompanhamento adaptada ao perfil de resposta do município",
            acoes=acoes,
            probabilidade_sucesso=prob_base,
            prioridade="media",
            timing="Aplicar após cada contato inicial",
            recursos_necessarios=["Sistema de CRM", "Templates de follow-up"],
            observacoes=[f"Cooperação histórica: {profile.nivel_cooperacao}"]
        )
    
    def _generate_challenge_specific_strategies(self, profile: MunicipalityProfile) -> List[StrategyRecommendation]:
        """Gera estratégias específicas para os desafios identificados"""
        strategies = []
        
        for desafio in profile.desafios_identificados:
            if desafio == 'falta_de_contatos':
                strategies.append(StrategyRecommendation(
                    tipo="desafio",
                    titulo="Ampliação da Rede de Contatos",
                    descricao="Estratégia para identificar novos contatos no município",
                    acoes=[
                        "Pesquisar site oficial da prefeitura",
                        "Consultar associações locais e câmara de vereadores",
                        "Usar LinkedIn e redes sociais para identificar gestores",
                        "Contatar municípios vizinhos para indicações"
                    ],
                    probabilidade_sucesso=70,
                    prioridade="alta",
                    timing="Executar antes do primeiro contato",
                    recursos_necessarios=["Pesquisa online", "Rede de contatos"],
                    observacoes=["Desafio crítico que impacta outras estratégias"]
                ))
            
            elif desafio == 'resistencia_inicial':
                strategies.append(StrategyRecommendation(
                    tipo="desafio",
                    titulo="Superação de Resistência",
                    descricao="Estratégia para superar resistência inicial do município",
                    acoes=[
                        "Enfatizar obrigatoriedade legal da pesquisa",
                        "Apresentar benefícios diretos para o município",
                        "Compartilhar casos de sucesso de outros municípios",
                        "Oferecer suporte técnico especializado",
                        "Flexibilizar cronograma se necessário"
                    ],
                    probabilidade_sucesso=65,
                    prioridade="alta",
                    timing="Aplicar desde o primeiro contato",
                    recursos_necessarios=["Material jurídico", "Cases de sucesso", "Flexibilidade"],
                    observacoes=["Requer abordagem mais consultiva"]
                ))
        
        return strategies
    
    def _calculate_progress_metrics(self, municipio: str) -> Dict:
        """Calcula métricas detalhadas de progresso do município"""
        try:
            visitas = Visita.query.filter_by(municipio=municipio).all()
            contatos = Contato.query.filter_by(municipio=municipio).all()
            
            metrics = {
                'visitas_total': len(visitas),
                'visitas_agendadas': len([v for v in visitas if v.status == 'agendada']),
                'visitas_em_andamento': len([v for v in visitas if v.status in ['em preparação', 'em execução']]),
                'visitas_concluidas': len([v for v in visitas if v.status in ['realizada', 'finalizada']]),
                'taxa_conclusao': 0,
                'contatos_total': len(contatos),
                'progresso_geral': 0,
                'tempo_medio_conclusao': None,
                'proximas_acoes': []
            }
            
            if metrics['visitas_total'] > 0:
                metrics['taxa_conclusao'] = (metrics['visitas_concluidas'] / metrics['visitas_total']) * 100
                metrics['progresso_geral'] = metrics['taxa_conclusao']
            
            # Calcular próximas ações baseadas no status
            if metrics['visitas_agendadas'] > 0:
                metrics['proximas_acoes'].append(f"{metrics['visitas_agendadas']} visitas agendadas para executar")
            
            if metrics['visitas_em_andamento'] > 0:
                metrics['proximas_acoes'].append(f"{metrics['visitas_em_andamento']} visitas em andamento para finalizar")
            
            if metrics['contatos_total'] == 0:
                metrics['proximas_acoes'].append("Urgente: Buscar contatos para o município")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Erro ao calcular métricas de progresso para {municipio}: {e}")
            return {}
    
    def _generate_ai_insights(self, profile: MunicipalityProfile, strategies: List[StrategyRecommendation]) -> List[str]:
        """Gera insights inteligentes usando IA"""
        insights = []
        
        # Insights baseados em dados
        if profile.taxa_sucesso < 50:
            insights.append(f"⚠️ Taxa de sucesso baixa ({profile.taxa_sucesso:.1f}%) requer estratégia intensiva")
        elif profile.taxa_sucesso > 80:
            insights.append(f"✅ Alta taxa de sucesso ({profile.taxa_sucesso:.1f}%) - município cooperativo")
        
        if profile.contatos_disponiveis < 2:
            insights.append("📞 Baixo número de contatos pode ser o principal gargalo")
        
        if profile.risco_atual == "Alto":
            insights.append("🚨 Município de alto risco requer atenção prioritária da equipe")
        
        # Insights sobre timing
        insights.append(f"⏰ Melhor janela de contato: {profile.melhor_dia_semana} pela {profile.melhor_horario}")
        
        # Insights sobre estratégias
        high_prob_strategies = [s for s in strategies if s.probabilidade_sucesso > 85]
        if high_prob_strategies:
            insights.append(f"🎯 {len(high_prob_strategies)} estratégias com alta probabilidade de sucesso identificadas")
        
        return insights
    
    def _calculate_overall_confidence(self, strategies: List[StrategyRecommendation]) -> float:
        """Calcula confiança geral das estratégias"""
        if not strategies:
            return 0
        
        probs = [s.probabilidade_sucesso for s in strategies]
        return statistics.mean(probs)
    
    def _identify_priority_entities(self, municipio: str) -> List[str]:
        """Identifica entidades prioritárias no município"""
        try:
            contatos = Contato.query.filter_by(municipio=municipio).all()
            
            # Contar por tipo de entidade
            entity_counts = {}
            for contato in contatos:
                entity_type = contato.tipo_entidade.value if contato.tipo_entidade else "Outros"
                entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            
            # Retornar os 3 tipos mais frequentes
            sorted_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)
            return [entity[0] for entity in sorted_entities[:3]]
            
        except Exception as e:
            logger.error(f"Erro ao identificar entidades prioritárias para {municipio}: {e}")
            return []
    
    def _identify_challenges(self, visitas: List, contatos: List) -> List[str]:
        """Identifica desafios específicos baseados nos dados"""
        challenges = []
        
        if len(contatos) < 2:
            challenges.append('falta_de_contatos')
        
        if len(visitas) > 0:
            failed_visits = [v for v in visitas if v.status in ['cancelada', 'não realizada']]
            if len(failed_visits) / len(visitas) > 0.3:
                challenges.append('resistencia_inicial')
        
        pending_visits = [v for v in visitas if v.status in ['agendada', 'em preparação']]
        if len(pending_visits) > 5:
            challenges.append('sobrecarga_agenda')
        
        return challenges
    
    def _analyze_timing_patterns(self, visitas: List) -> Dict:
        """Analisa padrões temporais das visitas"""
        # Padrões padrão baseados em boas práticas
        default_timing = {
            'melhor_horario': 'manhã',
            'melhor_dia': 'Terça-feira'
        }
        
        if not visitas:
            return default_timing
        
        # Analisar horários de visitas bem-sucedidas
        successful_visits = [v for v in visitas if v.status in ['realizada', 'finalizada']]
        
        if successful_visits:
            # Análise simples - poderia ser expandida
            morning_count = 0
            afternoon_count = 0
            
            for visit in successful_visits:
                if hasattr(visit, 'hora_inicio') and visit.hora_inicio:
                    if visit.hora_inicio.hour < 12:
                        morning_count += 1
                    else:
                        afternoon_count += 1
            
            if morning_count > afternoon_count:
                default_timing['melhor_horario'] = 'manhã'
            else:
                default_timing['melhor_horario'] = 'tarde'
        
        return default_timing
    
    def _assess_cooperation_level(self, visitas: List, taxa_sucesso: float) -> str:
        """Avalia nível de cooperação do município"""
        if taxa_sucesso >= 80:
            return "Alto"
        elif taxa_sucesso >= 50:
            return "Médio"
        else:
            return "Baixo"
    
    def _calculate_risk_level(self, taxa_sucesso: float, total_visitas: int, contatos_disponiveis: int) -> str:
        """Calcula nível de risco do município"""
        risk_score = 0
        
        # Fator taxa de sucesso
        if taxa_sucesso < 30:
            risk_score += 3
        elif taxa_sucesso < 60:
            risk_score += 2
        else:
            risk_score += 1
        
        # Fator número de contatos
        if contatos_disponiveis < 1:
            risk_score += 3
        elif contatos_disponiveis < 3:
            risk_score += 1
        
        # Fator total de visitas (complexidade)
        if total_visitas > 10:
            risk_score += 1
        
        if risk_score >= 5:
            return "Alto"
        elif risk_score >= 3:
            return "Médio"
        else:
            return "Baixo"
    
    def _calculate_average_response_time(self, visitas: List) -> Optional[float]:
        """Calcula tempo médio de resposta em dias"""
        if not visitas:
            return None
        
        response_times = []
        for visita in visitas:
            if hasattr(visita, 'data_criacao') and hasattr(visita, 'data') and visita.data_criacao and visita.data:
                delta = visita.data - visita.data_criacao.date()
                response_times.append(delta.days)
        
        if response_times:
            return statistics.mean(response_times)
        
        return None
    
    def _determine_preferred_channel(self, contatos: List) -> str:
        """Determina canal preferido baseado nos contatos disponíveis"""
        if not contatos:
            return "multicanal"
        
        phone_count = sum(1 for c in contatos if hasattr(c, 'telefone') and c.telefone)
        email_count = sum(1 for c in contatos if hasattr(c, 'email') and c.email)
        
        if phone_count > email_count:
            return "telefone"
        elif email_count > phone_count:
            return "email"
        else:
            return "multicanal"
    
    def _generate_general_recommendations(self, all_analyses: Dict) -> List[str]:
        """Gera recomendações gerais baseadas na análise de todos os municípios"""
        recommendations = []
        
        # Analisar padrões gerais
        high_risk_count = sum(1 for analysis in all_analyses.values() 
                             if analysis['profile']['risco_atual'] == 'Alto')
        
        low_contact_count = sum(1 for analysis in all_analyses.values() 
                               if analysis['profile']['contatos_disponiveis'] < 2)
        
        if high_risk_count > 0:
            recommendations.append(f"🚨 {high_risk_count} municípios de alto risco requerem atenção prioritária")
        
        if low_contact_count > 0:
            recommendations.append(f"📞 {low_contact_count} municípios precisam de expansão da base de contatos")
        
        # Recomendações de otimização
        recommendations.extend([
            "⏰ Priorizar contatos nas manhãs de terça e quarta-feira",
            "📋 Implementar follow-up estruturado para municípios de baixa cooperação",
            "🎯 Focar recursos nos municípios de alto risco identificados"
        ])
        
        return recommendations