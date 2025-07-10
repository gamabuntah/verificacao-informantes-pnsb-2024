"""
Sistema de Alertas Preventivos - PNSB 2024
Alertas inteligentes para prazos, problemas e oportunidades
"""

from datetime import datetime, timedelta, date, time
from typing import Dict, List, Optional, Any, Callable
from sqlalchemy import and_, or_, func
from ..models.agendamento import Visita
from ..models.checklist import Checklist
from ..models.questionarios_obrigatorios import QuestionarioObrigatorio, EntidadeIdentificada, ProgressoQuestionarios
from ..db import db
from .conflict_detector import ConflictDetector
from .smart_scheduler import SmartScheduler
from .weather_service import WeatherService
from dataclasses import dataclass
from enum import Enum
import logging
import json

class TipoAlerta(Enum):
    PRAZO_CRITICO = "prazo_critico"
    CONFLITO_AGENDAMENTO = "conflito_agendamento"
    CLIMA_DESFAVORAVEL = "clima_desfavoravel"
    PRODUTIVIDADE_BAIXA = "produtividade_baixa"
    QUESTIONARIO_PENDENTE = "questionario_pendente"
    VISITA_ATRASADA = "visita_atrasada"
    OPORTUNIDADE_OTIMIZACAO = "oportunidade_otimizacao"
    META_RISCO = "meta_risco"
    ENTIDADE_PROBLEMATICA = "entidade_problematica"
    DOCUMENTACAO_INCOMPLETA = "documentacao_incompleta"

class PrioridadeAlerta(Enum):
    CRITICA = "critica"
    ALTA = "alta"
    MEDIA = "media"
    BAIXA = "baixa"
    INFORMATIVA = "informativa"

class StatusAlerta(Enum):
    ATIVO = "ativo"
    RESOLVIDO = "resolvido"
    IGNORADO = "ignorado"
    EXPIRADO = "expirado"

@dataclass
class Alerta:
    id: str
    tipo: TipoAlerta
    prioridade: PrioridadeAlerta
    titulo: str
    descricao: str
    detalhes: Dict[str, Any]
    acoes_sugeridas: List[str]
    data_criacao: datetime
    data_expiracao: Optional[datetime]
    entidades_afetadas: List[str]
    visitas_afetadas: List[int]
    automatico: bool
    resolvivel_automaticamente: bool
    callback_resolucao: Optional[str]
    metadados: Dict[str, Any]

class AlertSystem:
    """Sistema inteligente de alertas preventivos"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.conflict_detector = ConflictDetector()
        self.smart_scheduler = SmartScheduler()
        self.weather_service = WeatherService()
        
        # Cache de alertas ativos
        self.alertas_ativos = {}
        self.historico_alertas = []
        
        # Configurações de alertas
        self.config = {
            'prazo_alerta_dias': {
                'critico': 3,
                'urgente': 7,
                'atencao': 14
            },
            'limite_visitas_atrasadas': 2,
            'limite_questionarios_pendentes': 5,
            'meta_visitas_diarias': 4,
            'meta_questionarios_semanais': 20,
            'score_produtividade_minimo': 0.6,
            'max_alertas_ativos': 50
        }
        
        # Prazos críticos PNSB 2024
        self.prazos_pnsb = {
            'inicio_campo': date(2024, 8, 1),
            'prazo_visitas_p1': date(2024, 9, 15),
            'prazo_visitas_p2': date(2024, 10, 31),
            'prazo_questionarios': date(2024, 11, 30),
            'fim_pesquisa': date(2024, 12, 15)
        }
        
        # Registrar verificadores de alertas
        self.verificadores = {
            TipoAlerta.PRAZO_CRITICO: self._verificar_prazos_criticos,
            TipoAlerta.CONFLITO_AGENDAMENTO: self._verificar_conflitos,
            TipoAlerta.CLIMA_DESFAVORAVEL: self._verificar_clima,
            TipoAlerta.PRODUTIVIDADE_BAIXA: self._verificar_produtividade,
            TipoAlerta.QUESTIONARIO_PENDENTE: self._verificar_questionarios_pendentes,
            TipoAlerta.VISITA_ATRASADA: self._verificar_visitas_atrasadas,
            TipoAlerta.OPORTUNIDADE_OTIMIZACAO: self._verificar_oportunidades,
            TipoAlerta.META_RISCO: self._verificar_metas,
            TipoAlerta.ENTIDADE_PROBLEMATICA: self._verificar_entidades_problematicas,
            TipoAlerta.DOCUMENTACAO_INCOMPLETA: self._verificar_documentacao
        }
    
    def executar_verificacao_completa(self) -> Dict[str, Any]:
        """Executar verificação completa de todos os tipos de alertas"""
        
        try:
            self.logger.info("🔍 Iniciando verificação completa de alertas...")
            
            novos_alertas = []
            alertas_resolvidos = []
            
            # Executar cada verificador
            for tipo_alerta, verificador in self.verificadores.items():
                try:
                    alertas_tipo = verificador()
                    novos_alertas.extend(alertas_tipo)
                except Exception as e:
                    self.logger.error(f"❌ Erro no verificador {tipo_alerta.value}: {str(e)}")
            
            # Processar novos alertas
            for alerta in novos_alertas:
                if self._deve_criar_alerta(alerta):
                    self._criar_alerta(alerta)
            
            # Verificar alertas resolvidos
            alertas_resolvidos = self._verificar_alertas_resolvidos()
            
            # Limpar alertas expirados
            self._limpar_alertas_expirados()
            
            # Gerar relatório
            relatorio = self._gerar_relatorio_verificacao(novos_alertas, alertas_resolvidos)
            
            self.logger.info(f"✅ Verificação concluída: {len(novos_alertas)} novos alertas")
            
            return relatorio
            
        except Exception as e:
            self.logger.error(f"❌ Erro na verificação de alertas: {str(e)}")
            return {'erro': str(e)}
    
    def obter_alertas_ativos(self, filtros: Dict[str, Any] = None) -> List[Alerta]:
        """Obter alertas ativos com filtros opcionais"""
        
        alertas = list(self.alertas_ativos.values())
        
        if not filtros:
            return sorted(alertas, key=lambda a: (a.prioridade.value, a.data_criacao), reverse=True)
        
        # Aplicar filtros
        if 'prioridade' in filtros:
            alertas = [a for a in alertas if a.prioridade == filtros['prioridade']]
        
        if 'tipo' in filtros:
            alertas = [a for a in alertas if a.tipo == filtros['tipo']]
        
        if 'municipio' in filtros:
            alertas = [a for a in alertas if filtros['municipio'] in a.entidades_afetadas]
        
        if 'data_inicio' in filtros:
            alertas = [a for a in alertas if a.data_criacao >= filtros['data_inicio']]
        
        return sorted(alertas, key=lambda a: (a.prioridade.value, a.data_criacao), reverse=True)
    
    def obter_dashboard_alertas(self) -> Dict[str, Any]:
        """Obter dashboard resumido de alertas"""
        
        alertas_ativos = list(self.alertas_ativos.values())
        
        # Contar por prioridade
        contadores = {
            'critica': len([a for a in alertas_ativos if a.prioridade == PrioridadeAlerta.CRITICA]),
            'alta': len([a for a in alertas_ativos if a.prioridade == PrioridadeAlerta.ALTA]),
            'media': len([a for a in alertas_ativos if a.prioridade == PrioridadeAlerta.MEDIA]),
            'baixa': len([a for a in alertas_ativos if a.prioridade == PrioridadeAlerta.BAIXA]),
            'total': len(alertas_ativos)
        }
        
        # Contar por tipo
        tipos = {}
        for alerta in alertas_ativos:
            tipo = alerta.tipo.value
            tipos[tipo] = tipos.get(tipo, 0) + 1
        
        # Alertas mais recentes
        alertas_recentes = sorted(alertas_ativos, key=lambda a: a.data_criacao, reverse=True)[:5]
        
        # Alertas críticos que requerem ação imediata
        alertas_criticos = [a for a in alertas_ativos if a.prioridade == PrioridadeAlerta.CRITICA]
        
        return {
            'contadores': contadores,
            'tipos': tipos,
            'alertas_recentes': [self._alerta_to_dict(a) for a in alertas_recentes],
            'alertas_criticos': [self._alerta_to_dict(a) for a in alertas_criticos],
            'status_geral': self._avaliar_status_geral(contadores),
            'ultima_verificacao': datetime.now().isoformat()
        }
    
    def resolver_alerta(self, alerta_id: str, metodo_resolucao: str = 'manual',
                       dados_resolucao: Dict[str, Any] = None) -> bool:
        """Resolver um alerta específico"""
        
        try:
            if alerta_id not in self.alertas_ativos:
                return False
            
            alerta = self.alertas_ativos[alerta_id]
            
            # Executar callback de resolução se disponível
            if alerta.callback_resolucao and metodo_resolucao == 'automatico':
                sucesso = self._executar_callback_resolucao(alerta, dados_resolucao)
                if not sucesso:
                    return False
            
            # Marcar como resolvido
            alerta.metadados['status'] = StatusAlerta.RESOLVIDO.value
            alerta.metadados['data_resolucao'] = datetime.now().isoformat()
            alerta.metadados['metodo_resolucao'] = metodo_resolucao
            
            if dados_resolucao:
                alerta.metadados['dados_resolucao'] = dados_resolucao
            
            # Mover para histórico
            self.historico_alertas.append(alerta)
            del self.alertas_ativos[alerta_id]
            
            self.logger.info(f"✅ Alerta {alerta_id} resolvido via {metodo_resolucao}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao resolver alerta {alerta_id}: {str(e)}")
            return False
    
    def _verificar_prazos_criticos(self) -> List[Alerta]:
        """Verificar prazos críticos PNSB"""
        
        alertas = []
        hoje = date.today()
        
        for prazo_nome, prazo_data in self.prazos_pnsb.items():
            dias_restantes = (prazo_data - hoje).days
            
            if dias_restantes <= 0:
                # Prazo já passou
                prioridade = PrioridadeAlerta.CRITICA
                titulo = f"⚠️ PRAZO VENCIDO: {prazo_nome.replace('_', ' ').title()}"
                descricao = f"O prazo para {prazo_nome} venceu há {abs(dias_restantes)} dias"
            elif dias_restantes <= self.config['prazo_alerta_dias']['critico']:
                prioridade = PrioridadeAlerta.CRITICA
                titulo = f"🚨 PRAZO CRÍTICO: {prazo_nome.replace('_', ' ').title()}"
                descricao = f"Restam apenas {dias_restantes} dias para {prazo_nome}"
            elif dias_restantes <= self.config['prazo_alerta_dias']['urgente']:
                prioridade = PrioridadeAlerta.ALTA
                titulo = f"⚠️ PRAZO URGENTE: {prazo_nome.replace('_', ' ').title()}"
                descricao = f"Restam {dias_restantes} dias para {prazo_nome}"
            elif dias_restantes <= self.config['prazo_alerta_dias']['atencao']:
                prioridade = PrioridadeAlerta.MEDIA
                titulo = f"📅 ATENÇÃO: {prazo_nome.replace('_', ' ').title()}"
                descricao = f"Restam {dias_restantes} dias para {prazo_nome}"
            else:
                continue  # Prazo ainda longe
            
            # Definir ações baseadas no tipo de prazo
            acoes = self._gerar_acoes_prazo(prazo_nome, dias_restantes)
            
            alerta = Alerta(
                id=f"prazo_{prazo_nome}_{hoje.isoformat()}",
                tipo=TipoAlerta.PRAZO_CRITICO,
                prioridade=prioridade,
                titulo=titulo,
                descricao=descricao,
                detalhes={
                    'prazo_nome': prazo_nome,
                    'data_prazo': prazo_data.isoformat(),
                    'dias_restantes': dias_restantes,
                    'percentual_tempo_restante': max(0, dias_restantes / 30 * 100)
                },
                acoes_sugeridas=acoes,
                data_criacao=datetime.now(),
                data_expiracao=datetime.combine(prazo_data + timedelta(days=7), time.max),
                entidades_afetadas=['TODAS'],
                visitas_afetadas=[],
                automatico=True,
                resolvivel_automaticamente=False,
                callback_resolucao=None,
                metadados={'categoria': 'prazo_pnsb'}
            )
            
            alertas.append(alerta)
        
        return alertas
    
    def _verificar_conflitos(self) -> List[Alerta]:
        """Verificar conflitos de agendamento"""
        
        alertas = []
        
        # Verificar próximos 7 dias
        for i in range(7):
            data_verificacao = date.today() + timedelta(days=i)
            
            try:
                conflitos_info = self.conflict_detector.detectar_conflitos_dia(data_verificacao)
                conflitos = conflitos_info.get('conflitos_detalhados', [])
                
                for conflito in conflitos:
                    if conflito['severidade'] in ['critico', 'alto']:
                        
                        prioridade = PrioridadeAlerta.CRITICA if conflito['severidade'] == 'critico' else PrioridadeAlerta.ALTA
                        
                        alerta = Alerta(
                            id=f"conflito_{conflito['id']}_{data_verificacao.isoformat()}",
                            tipo=TipoAlerta.CONFLITO_AGENDAMENTO,
                            prioridade=prioridade,
                            titulo=f"🚨 Conflito de Agendamento - {data_verificacao.strftime('%d/%m')}",
                            descricao=conflito['descricao'],
                            detalhes=conflito,
                            acoes_sugeridas=[
                                "Revisar horários das visitas conflitantes",
                                "Considerar reagendamento",
                                "Verificar viabilidade de viagem entre locais"
                            ],
                            data_criacao=datetime.now(),
                            data_expiracao=datetime.combine(data_verificacao + timedelta(days=1), time.max),
                            entidades_afetadas=[],
                            visitas_afetadas=conflito.get('visitas_conflitantes', []),
                            automatico=True,
                            resolvivel_automaticamente=True,
                            callback_resolucao='resolver_conflito_agendamento',
                            metadados={'data_conflito': data_verificacao.isoformat()}
                        )
                        
                        alertas.append(alerta)
                        
            except Exception as e:
                self.logger.error(f"Erro ao verificar conflitos para {data_verificacao}: {str(e)}")
        
        return alertas
    
    def _verificar_clima(self) -> List[Alerta]:
        """Verificar condições climáticas desfavoráveis"""
        
        alertas = []
        
        # Verificar próximos 3 dias
        for i in range(3):
            data_verificacao = date.today() + timedelta(days=i)
            
            # Buscar visitas do dia
            visitas_dia = Visita.query.filter(
                and_(
                    Visita.data == data_verificacao,
                    Visita.status.in_(['agendada', 'em preparação'])
                )
            ).all()
            
            for visita in visitas_dia:
                try:
                    recomendacao = self.weather_service.analisar_impacto_visita(
                        visita.municipio,
                        visita.data,
                        visita.hora_inicio,
                        visita.hora_fim
                    )
                    
                    if recomendacao.impacto_visita.value in ['problematico', 'cancelar']:
                        
                        prioridade = PrioridadeAlerta.CRITICA if recomendacao.impacto_visita.value == 'cancelar' else PrioridadeAlerta.ALTA
                        
                        alerta = Alerta(
                            id=f"clima_{visita.id}_{data_verificacao.isoformat()}",
                            tipo=TipoAlerta.CLIMA_DESFAVORAVEL,
                            prioridade=prioridade,
                            titulo=f"🌧️ Clima Desfavorável - {visita.municipio}",
                            descricao=f"Condições climáticas problemáticas previstas para visita em {visita.municipio}",
                            detalhes={
                                'municipio': visita.municipio,
                                'impacto': recomendacao.impacto_visita.value,
                                'score_condicoes': recomendacao.score_condicoes,
                                'alertas_clima': recomendacao.alertas
                            },
                            acoes_sugeridas=recomendacao.recomendacoes + ["Considerar reagendamento"],
                            data_criacao=datetime.now(),
                            data_expiracao=datetime.combine(data_verificacao + timedelta(days=1), time.max),
                            entidades_afetadas=[visita.municipio],
                            visitas_afetadas=[visita.id],
                            automatico=True,
                            resolvivel_automaticamente=True,
                            callback_resolucao='reagendar_por_clima',
                            metadados={'previsao_clima': recomendacao.observacoes}
                        )
                        
                        alertas.append(alerta)
                        
                except Exception as e:
                    self.logger.error(f"Erro ao verificar clima para visita {visita.id}: {str(e)}")
        
        return alertas
    
    def _verificar_produtividade(self) -> List[Alerta]:
        """Verificar produtividade baixa"""
        
        alertas = []
        
        # Analisar últimos 7 dias
        data_inicio = date.today() - timedelta(days=7)
        
        # Calcular métricas de produtividade
        visitas_periodo = Visita.query.filter(
            and_(
                Visita.data >= data_inicio,
                Visita.data <= date.today()
            )
        ).all()
        
        if visitas_periodo:
            # Calcular scores
            visitas_por_dia = len(visitas_periodo) / 7
            visitas_concluidas = len([v for v in visitas_periodo if v.status == 'realizada'])
            taxa_conclusao = visitas_concluidas / len(visitas_periodo) if visitas_periodo else 0
            
            # Verificar se está abaixo das metas
            if visitas_por_dia < self.config['meta_visitas_diarias'] * 0.7:
                alerta = Alerta(
                    id=f"produtividade_baixa_{date.today().isoformat()}",
                    tipo=TipoAlerta.PRODUTIVIDADE_BAIXA,
                    prioridade=PrioridadeAlerta.MEDIA,
                    titulo="📊 Produtividade Abaixo da Meta",
                    descricao=f"Média de {visitas_por_dia:.1f} visitas/dia (meta: {self.config['meta_visitas_diarias']})",
                    detalhes={
                        'visitas_por_dia_atual': visitas_por_dia,
                        'meta_visitas_diarias': self.config['meta_visitas_diarias'],
                        'taxa_conclusao': taxa_conclusao * 100,
                        'periodo_analise': '7 dias'
                    },
                    acoes_sugeridas=[
                        "Revisar planejamento semanal",
                        "Otimizar rotas diárias",
                        "Identificar gargalos no processo",
                        "Considerar redistribuição de visitas"
                    ],
                    data_criacao=datetime.now(),
                    data_expiracao=datetime.now() + timedelta(days=3),
                    entidades_afetadas=[],
                    visitas_afetadas=[],
                    automatico=True,
                    resolvivel_automaticamente=False,
                    callback_resolucao=None,
                    metadados={'metricas_produtividade': True}
                )
                
                alertas.append(alerta)
        
        return alertas
    
    def _verificar_questionarios_pendentes(self) -> List[Alerta]:
        """Verificar questionários pendentes"""
        
        alertas = []
        
        try:
            # Contar questionários por status
            questionarios_pendentes = QuestionarioObrigatorio.query.filter(
                QuestionarioObrigatorio.status.in_(['pendente', 'em_andamento'])
            ).count()
            
            if questionarios_pendentes > self.config['limite_questionarios_pendentes']:
                
                # Verificar distribuição por município
                pendentes_por_municipio = db.session.query(
                    QuestionarioObrigatorio.municipio,
                    func.count(QuestionarioObrigatorio.id).label('count')
                ).filter(
                    QuestionarioObrigatorio.status.in_(['pendente', 'em_andamento'])
                ).group_by(QuestionarioObrigatorio.municipio).all()
                
                alerta = Alerta(
                    id=f"questionarios_pendentes_{date.today().isoformat()}",
                    tipo=TipoAlerta.QUESTIONARIO_PENDENTE,
                    prioridade=PrioridadeAlerta.MEDIA,
                    titulo=f"📋 {questionarios_pendentes} Questionários Pendentes",
                    descricao=f"Número alto de questionários não finalizados ({questionarios_pendentes})",
                    detalhes={
                        'total_pendentes': questionarios_pendentes,
                        'limite_configurado': self.config['limite_questionarios_pendentes'],
                        'distribuicao_municipios': dict(pendentes_por_municipio)
                    },
                    acoes_sugeridas=[
                        "Priorizar finalização de questionários",
                        "Verificar pendências por município",
                        "Contactar entidades com questionários em andamento",
                        "Revisar processo de preenchimento"
                    ],
                    data_criacao=datetime.now(),
                    data_expiracao=datetime.now() + timedelta(days=7),
                    entidades_afetadas=[m[0] for m in pendentes_por_municipio],
                    visitas_afetadas=[],
                    automatico=True,
                    resolvivel_automaticamente=False,
                    callback_resolucao=None,
                    metadados={'questionarios_analytics': True}
                )
                
                alertas.append(alerta)
                
        except Exception as e:
            self.logger.error(f"Erro ao verificar questionários pendentes: {str(e)}")
        
        return alertas
    
    def _verificar_visitas_atrasadas(self) -> List[Alerta]:
        """Verificar visitas atrasadas"""
        
        alertas = []
        
        # Buscar visitas que deveriam ter sido realizadas
        hoje = date.today()
        ontem = hoje - timedelta(days=1)
        
        visitas_atrasadas = Visita.query.filter(
            and_(
                Visita.data < hoje,
                Visita.status.in_(['agendada', 'em preparação'])
            )
        ).all()
        
        if len(visitas_atrasadas) > self.config['limite_visitas_atrasadas']:
            
            municipios_afetados = list(set([v.municipio for v in visitas_atrasadas]))
            
            alerta = Alerta(
                id=f"visitas_atrasadas_{hoje.isoformat()}",
                tipo=TipoAlerta.VISITA_ATRASADA,
                prioridade=PrioridadeAlerta.ALTA,
                titulo=f"⏰ {len(visitas_atrasadas)} Visitas Atrasadas",
                descricao=f"Visitas agendadas que não foram realizadas ou atualizadas",
                detalhes={
                    'total_atrasadas': len(visitas_atrasadas),
                    'municipios_afetados': municipios_afetados,
                    'visitas_detalhes': [
                        {
                            'id': v.id,
                            'municipio': v.municipio,
                            'data_prevista': v.data.isoformat(),
                            'dias_atraso': (hoje - v.data).days
                        } for v in visitas_atrasadas
                    ]
                },
                acoes_sugeridas=[
                    "Atualizar status das visitas realizadas",
                    "Reagendar visitas não realizadas",
                    "Verificar motivos dos atrasos",
                    "Revisar planejamento"
                ],
                data_criacao=datetime.now(),
                data_expiracao=datetime.now() + timedelta(days=5),
                entidades_afetadas=municipios_afetados,
                visitas_afetadas=[v.id for v in visitas_atrasadas],
                automatico=True,
                resolvivel_automaticamente=True,
                callback_resolucao='processar_visitas_atrasadas',
                metadados={'analise_atrasos': True}
            )
            
            alertas.append(alerta)
        
        return alertas
    
    def _verificar_oportunidades(self) -> List[Alerta]:
        """Verificar oportunidades de otimização"""
        
        alertas = []
        
        # Analisar próximos 5 dias para oportunidades
        for i in range(1, 6):
            data_analise = date.today() + timedelta(days=i)
            
            try:
                # Verificar se há poucos agendamentos
                visitas_dia = Visita.query.filter(
                    and_(
                        Visita.data == data_analise,
                        Visita.status.in_(['agendada', 'em preparação'])
                    )
                ).count()
                
                if visitas_dia < 2:  # Dia com poucas visitas
                    alerta = Alerta(
                        id=f"oportunidade_dia_{data_analise.isoformat()}",
                        tipo=TipoAlerta.OPORTUNIDADE_OTIMIZACAO,
                        prioridade=PrioridadeAlerta.BAIXA,
                        titulo=f"💡 Oportunidade - {data_analise.strftime('%d/%m')}",
                        descricao=f"Dia com apenas {visitas_dia} visitas - oportunidade para adicionar mais",
                        detalhes={
                            'data': data_analise.isoformat(),
                            'visitas_atuais': visitas_dia,
                            'capacidade_disponivel': self.config['meta_visitas_diarias'] - visitas_dia
                        },
                        acoes_sugeridas=[
                            "Verificar entidades disponíveis para agendamento",
                            "Considerar adiantar visitas de outros dias",
                            "Aproveitar para planejamento e preparação"
                        ],
                        data_criacao=datetime.now(),
                        data_expiracao=datetime.combine(data_analise, time.max),
                        entidades_afetadas=[],
                        visitas_afetadas=[],
                        automatico=True,
                        resolvivel_automaticamente=False,
                        callback_resolucao=None,
                        metadados={'tipo_oportunidade': 'dia_disponivel'}
                    )
                    
                    alertas.append(alerta)
                    
            except Exception as e:
                self.logger.error(f"Erro ao verificar oportunidades para {data_analise}: {str(e)}")
        
        return alertas
    
    def _verificar_metas(self) -> List[Alerta]:
        """Verificar risco de não atingir metas"""
        
        alertas = []
        
        try:
            # Calcular progresso em relação às metas PNSB
            hoje = date.today()
            
            # Total de entidades que precisam ser visitadas
            total_entidades = EntidadeIdentificada.query.count()
            
            # Visitas realizadas
            visitas_realizadas = Visita.query.filter(
                Visita.status == 'realizada'
            ).count()
            
            # Calcular taxa de progresso
            if total_entidades > 0:
                taxa_progresso = visitas_realizadas / total_entidades
                
                # Calcular tempo decorrido vs tempo total disponível
                inicio_pesquisa = self.prazos_pnsb['inicio_campo']
                fim_pesquisa = self.prazos_pnsb['fim_pesquisa']
                
                if hoje >= inicio_pesquisa:
                    dias_decorridos = (hoje - inicio_pesquisa).days
                    dias_totais = (fim_pesquisa - inicio_pesquisa).days
                    tempo_decorrido_pct = dias_decorridos / dias_totais if dias_totais > 0 else 0
                    
                    # Se o progresso está muito abaixo do tempo decorrido
                    if taxa_progresso < tempo_decorrido_pct * 0.7:  # 70% do esperado
                        
                        deficit = (tempo_decorrido_pct - taxa_progresso) * total_entidades
                        
                        alerta = Alerta(
                            id=f"meta_risco_{hoje.isoformat()}",
                            tipo=TipoAlerta.META_RISCO,
                            prioridade=PrioridadeAlerta.ALTA,
                            titulo="🎯 Risco de Não Atingir Meta",
                            descricao=f"Progresso atual ({taxa_progresso:.1%}) abaixo do esperado ({tempo_decorrido_pct:.1%})",
                            detalhes={
                                'total_entidades': total_entidades,
                                'visitas_realizadas': visitas_realizadas,
                                'taxa_progresso': taxa_progresso * 100,
                                'tempo_decorrido_pct': tempo_decorrido_pct * 100,
                                'deficit_estimado': int(deficit),
                                'dias_restantes': (fim_pesquisa - hoje).days
                            },
                            acoes_sugeridas=[
                                "Intensificar cronograma de visitas",
                                "Revisar estratégia de abordagem",
                                "Priorizar entidades P1 e P2",
                                "Considerar apoio adicional"
                            ],
                            data_criacao=datetime.now(),
                            data_expiracao=datetime.now() + timedelta(days=7),
                            entidades_afetadas=['TODAS'],
                            visitas_afetadas=[],
                            automatico=True,
                            resolvivel_automaticamente=False,
                            callback_resolucao=None,
                            metadados={'analise_metas': True}
                        )
                        
                        alertas.append(alerta)
                        
        except Exception as e:
            self.logger.error(f"Erro ao verificar metas: {str(e)}")
        
        return alertas
    
    def _verificar_entidades_problematicas(self) -> List[Alerta]:
        """Verificar entidades com problemas recorrentes"""
        
        alertas = []
        
        try:
            # Buscar visitas canceladas ou com problemas frequentes
            visitas_problematicas = Visita.query.filter(
                and_(
                    Visita.status.in_(['cancelada', 'reagendada']),
                    Visita.data >= date.today() - timedelta(days=30)
                )
            ).all()
            
            # Agrupar por entidade/município
            problemas_por_entidade = {}
            for visita in visitas_problematicas:
                chave = f"{visita.municipio}_{visita.local or 'N/A'}"
                if chave not in problemas_por_entidade:
                    problemas_por_entidade[chave] = []
                problemas_por_entidade[chave].append(visita)
            
            # Identificar entidades com muitos problemas
            for entidade, visitas in problemas_por_entidade.items():
                if len(visitas) >= 3:  # 3 ou mais problemas em 30 dias
                    
                    municipio = visitas[0].municipio
                    local = visitas[0].local
                    
                    alerta = Alerta(
                        id=f"entidade_problematica_{entidade}_{date.today().isoformat()}",
                        tipo=TipoAlerta.ENTIDADE_PROBLEMATICA,
                        prioridade=PrioridadeAlerta.MEDIA,
                        titulo=f"⚠️ Entidade com Problemas Recorrentes",
                        descricao=f"{len(visitas)} problemas em 30 dias - {municipio} ({local})",
                        detalhes={
                            'municipio': municipio,
                            'local': local,
                            'numero_problemas': len(visitas),
                            'periodo_dias': 30,
                            'historico_problemas': [
                                {
                                    'data': v.data.isoformat(),
                                    'status': v.status,
                                    'observacoes': v.observacoes
                                } for v in visitas
                            ]
                        },
                        acoes_sugeridas=[
                            "Revisar estratégia de abordagem para esta entidade",
                            "Verificar dados de contato atualizados",
                            "Considerar contato prévio mais detalhado",
                            "Avaliar necessidade de visita presencial"
                        ],
                        data_criacao=datetime.now(),
                        data_expiracao=datetime.now() + timedelta(days=14),
                        entidades_afetadas=[municipio],
                        visitas_afetadas=[v.id for v in visitas],
                        automatico=True,
                        resolvivel_automaticamente=False,
                        callback_resolucao=None,
                        metadados={'analise_comportamental': True}
                    )
                    
                    alertas.append(alerta)
                    
        except Exception as e:
            self.logger.error(f"Erro ao verificar entidades problemáticas: {str(e)}")
        
        return alertas
    
    def _verificar_documentacao(self) -> List[Alerta]:
        """Verificar documentação incompleta"""
        
        alertas = []
        
        try:
            # Verificar visitas sem checklist completo
            visitas_sem_checklist = Visita.query.outerjoin(Checklist).filter(
                and_(
                    Visita.status == 'realizada',
                    Checklist.id.is_(None)
                )
            ).count()
            
            if visitas_sem_checklist > 0:
                alerta = Alerta(
                    id=f"documentacao_incompleta_{date.today().isoformat()}",
                    tipo=TipoAlerta.DOCUMENTACAO_INCOMPLETA,
                    prioridade=PrioridadeAlerta.MEDIA,
                    titulo=f"📝 {visitas_sem_checklist} Visitas sem Checklist",
                    descricao="Visitas realizadas sem checklist completo",
                    detalhes={
                        'visitas_sem_checklist': visitas_sem_checklist,
                        'impacto_qualidade': 'Redução na qualidade da documentação'
                    },
                    acoes_sugeridas=[
                        "Completar checklists pendentes",
                        "Revisar processo de documentação",
                        "Treinar sobre importância do checklist"
                    ],
                    data_criacao=datetime.now(),
                    data_expiracao=datetime.now() + timedelta(days=10),
                    entidades_afetadas=[],
                    visitas_afetadas=[],
                    automatico=True,
                    resolvivel_automaticamente=False,
                    callback_resolucao=None,
                    metadados={'qualidade_documentacao': True}
                )
                
                alertas.append(alerta)
                
        except Exception as e:
            self.logger.error(f"Erro ao verificar documentação: {str(e)}")
        
        return alertas
    
    def _deve_criar_alerta(self, alerta: Alerta) -> bool:
        """Verificar se deve criar o alerta (evitar duplicatas)"""
        
        # Verificar se já existe alerta similar ativo
        for alerta_ativo in self.alertas_ativos.values():
            if (alerta_ativo.tipo == alerta.tipo and 
                alerta_ativo.entidades_afetadas == alerta.entidades_afetadas and
                alerta_ativo.visitas_afetadas == alerta.visitas_afetadas):
                return False
        
        return True
    
    def _criar_alerta(self, alerta: Alerta) -> bool:
        """Criar e armazenar novo alerta"""
        
        try:
            # Verificar limite de alertas ativos
            if len(self.alertas_ativos) >= self.config['max_alertas_ativos']:
                # Remover alertas mais antigos de baixa prioridade
                self._limpar_alertas_antigos()
            
            # Adicionar aos alertas ativos
            self.alertas_ativos[alerta.id] = alerta
            
            self.logger.info(f"➕ Novo alerta criado: {alerta.titulo}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao criar alerta: {str(e)}")
            return False
    
    def _verificar_alertas_resolvidos(self) -> List[str]:
        """Verificar alertas que foram resolvidos automaticamente"""
        
        alertas_resolvidos = []
        
        for alerta_id, alerta in list(self.alertas_ativos.items()):
            if self._alerta_foi_resolvido(alerta):
                self.resolver_alerta(alerta_id, 'automatico')
                alertas_resolvidos.append(alerta_id)
        
        return alertas_resolvidos
    
    def _alerta_foi_resolvido(self, alerta: Alerta) -> bool:
        """Verificar se um alerta foi resolvido automaticamente"""
        
        # Verificação específica por tipo de alerta
        if alerta.tipo == TipoAlerta.CONFLITO_AGENDAMENTO:
            # Verificar se o conflito ainda existe
            for visita_id in alerta.visitas_afetadas:
                conflitos = self.conflict_detector.detectar_conflitos_visita(visita_id)
                if conflitos:
                    return False
            return True
        
        elif alerta.tipo == TipoAlerta.VISITA_ATRASADA:
            # Verificar se as visitas foram atualizadas
            for visita_id in alerta.visitas_afetadas:
                visita = Visita.query.get(visita_id)
                if visita and visita.status in ['agendada', 'em preparação']:
                    return False
            return True
        
        return False
    
    def _limpar_alertas_expirados(self):
        """Limpar alertas expirados"""
        
        agora = datetime.now()
        alertas_expirados = []
        
        for alerta_id, alerta in list(self.alertas_ativos.items()):
            if alerta.data_expiracao and agora > alerta.data_expiracao:
                alertas_expirados.append(alerta_id)
                alerta.metadados['status'] = StatusAlerta.EXPIRADO.value
                self.historico_alertas.append(alerta)
                del self.alertas_ativos[alerta_id]
        
        if alertas_expirados:
            self.logger.info(f"🗑️ {len(alertas_expirados)} alertas expirados removidos")
    
    def _limpar_alertas_antigos(self):
        """Limpar alertas antigos de baixa prioridade"""
        
        # Ordenar por prioridade e data (mais antigos primeiro)
        alertas_ordenados = sorted(
            self.alertas_ativos.items(),
            key=lambda x: (x[1].prioridade.value, x[1].data_criacao)
        )
        
        # Remover os 10 mais antigos de baixa prioridade
        removidos = 0
        for alerta_id, alerta in alertas_ordenados:
            if alerta.prioridade in [PrioridadeAlerta.BAIXA, PrioridadeAlerta.INFORMATIVA] and removidos < 10:
                alerta.metadados['status'] = StatusAlerta.EXPIRADO.value
                alerta.metadados['motivo_expiracao'] = 'limite_alertas_atingido'
                self.historico_alertas.append(alerta)
                del self.alertas_ativos[alerta_id]
                removidos += 1
    
    def _gerar_relatorio_verificacao(self, novos_alertas: List[Alerta], alertas_resolvidos: List[str]) -> Dict[str, Any]:
        """Gerar relatório da verificação"""
        
        return {
            'timestamp_verificacao': datetime.now().isoformat(),
            'novos_alertas': len(novos_alertas),
            'alertas_resolvidos': len(alertas_resolvidos),
            'total_alertas_ativos': len(self.alertas_ativos),
            'alertas_por_prioridade': {
                prioridade.value: len([a for a in self.alertas_ativos.values() if a.prioridade == prioridade])
                for prioridade in PrioridadeAlerta
            },
            'alertas_criticos': [
                self._alerta_to_dict(alerta) for alerta in self.alertas_ativos.values()
                if alerta.prioridade == PrioridadeAlerta.CRITICA
            ],
            'status_sistema': self._avaliar_status_geral({
                'critica': len([a for a in self.alertas_ativos.values() if a.prioridade == PrioridadeAlerta.CRITICA]),
                'alta': len([a for a in self.alertas_ativos.values() if a.prioridade == PrioridadeAlerta.ALTA])
            })
        }
    
    def _avaliar_status_geral(self, contadores: Dict[str, int]) -> str:
        """Avaliar status geral do sistema"""
        
        if contadores.get('critica', 0) > 0:
            return 'critico'
        elif contadores.get('alta', 0) > 5:
            return 'atencao'
        elif contadores.get('total', 0) > 20:
            return 'monitoramento'
        else:
            return 'normal'
    
    def _gerar_acoes_prazo(self, prazo_nome: str, dias_restantes: int) -> List[str]:
        """Gerar ações específicas para cada tipo de prazo"""
        
        acoes_base = [
            "Revisar cronograma e acelerar atividades",
            "Priorizar tarefas críticas",
            "Considerar recursos adicionais"
        ]
        
        acoes_especificas = {
            'prazo_visitas_p1': [
                "Focar exclusivamente em entidades P1",
                "Reorganizar agenda para maximizar visitas P1",
                "Verificar entidades P1 ainda não visitadas"
            ],
            'prazo_questionarios': [
                "Intensificar follow-up de questionários pendentes",
                "Contactar entidades com questionários incompletos",
                "Priorizar finalização sobre novas visitas"
            ]
        }
        
        return acoes_base + acoes_especificas.get(prazo_nome, [])
    
    def _executar_callback_resolucao(self, alerta: Alerta, dados: Dict[str, Any] = None) -> bool:
        """Executar callback de resolução automática"""
        
        try:
            callback = alerta.callback_resolucao
            
            if callback == 'resolver_conflito_agendamento':
                # Implementar resolução automática de conflitos
                return self._resolver_conflito_automatico(alerta, dados)
            
            elif callback == 'reagendar_por_clima':
                # Implementar reagendamento por clima
                return self._reagendar_por_clima_automatico(alerta, dados)
            
            # Adicionar outros callbacks conforme necessário
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Erro no callback de resolução: {str(e)}")
            return False
    
    def _resolver_conflito_automatico(self, alerta: Alerta, dados: Dict[str, Any] = None) -> bool:
        """Resolver conflito de agendamento automaticamente"""
        
        # Implementação simplificada - na prática, integraria com SmartScheduler
        self.logger.info(f"🔧 Tentativa de resolução automática de conflito: {alerta.id}")
        return True  # Placeholder
    
    def _reagendar_por_clima_automatico(self, alerta: Alerta, dados: Dict[str, Any] = None) -> bool:
        """Reagendar visita por condições climáticas automaticamente"""
        
        # Implementação simplificada - na prática, integraria com SmartScheduler e WeatherService
        self.logger.info(f"🌧️ Tentativa de reagendamento por clima: {alerta.id}")
        return True  # Placeholder
    
    def _alerta_to_dict(self, alerta: Alerta) -> Dict[str, Any]:
        """Converter alerta para dicionário"""
        
        return {
            'id': alerta.id,
            'tipo': alerta.tipo.value,
            'prioridade': alerta.prioridade.value,
            'titulo': alerta.titulo,
            'descricao': alerta.descricao,
            'detalhes': alerta.detalhes,
            'acoes_sugeridas': alerta.acoes_sugeridas,
            'data_criacao': alerta.data_criacao.isoformat(),
            'data_expiracao': alerta.data_expiracao.isoformat() if alerta.data_expiracao else None,
            'entidades_afetadas': alerta.entidades_afetadas,
            'visitas_afetadas': alerta.visitas_afetadas,
            'automatico': alerta.automatico,
            'resolvivel_automaticamente': alerta.resolvivel_automaticamente,
            'metadados': alerta.metadados
        }