"""
Sistema de Dashboard Preditivo PNSB 2024
Análise preditiva com IA para projeção de prazos, identificação de riscos e alertas críticos
"""

from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Tuple, Any
from sqlalchemy import func, and_, or_
from ..models.agendamento import Visita
from ..models.checklist import Checklist
from ..models.questionarios_obrigatorios import EntidadeIdentificada, ProgressoQuestionarios
from ..models.contatos import Contato
from .. import db
import json
import logging

logger = logging.getLogger(__name__)

class DashboardPreditivo:
    """Sistema inteligente de análise preditiva para PNSB 2024"""
    
    def __init__(self):
        self.prazo_final_pnsb = datetime(2025, 12, 31)
        self.prazo_p1_p2 = datetime(2025, 9, 19)
        self.prazo_questionarios = datetime(2025, 10, 17)
        self.municipios_sc = [
            'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas', 'Camboriú',
            'Itajaí', 'Itapema', 'Luiz Alves', 'Navegantes', 'Penha', 
            'Porto Belo', 'Ilhota'
        ]
        
    def gerar_dashboard_completo(self) -> Dict[str, Any]:
        """Gera dashboard preditivo completo com todas as análises"""
        try:
            hoje = datetime.now()
            
            # 1. Análise de Prazos
            analise_prazos = self._analisar_prazos()
            
            # 2. Identificação de Riscos
            riscos = self._identificar_riscos()
            
            # 3. Projeções de Progresso
            projecoes = self._projetar_progresso()
            
            # 4. Alertas Críticos
            alertas = self._gerar_alertas_criticos()
            
            # 5. Métricas de Velocidade
            velocidade = self._calcular_velocidade_progresso()
            
            # 6. Previsão de Conclusão
            previsao = self._prever_conclusao()
            
            # 7. Análise por Município
            analise_municipios = self._analisar_municipios()
            
            # 8. Score de Saúde do Projeto
            score_saude = self._calcular_score_saude()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'analise_prazos': analise_prazos,
                'riscos_identificados': riscos,
                'projecoes_progresso': projecoes,
                'alertas_criticos': alertas,
                'velocidade_atual': velocidade,
                'previsao_conclusao': previsao,
                'analise_municipios': analise_municipios,
                'score_saude': score_saude,
                'recomendacoes': self._gerar_recomendacoes(score_saude, riscos)
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar dashboard preditivo: {e}")
            return {'error': str(e)}
    
    def _analisar_prazos(self) -> Dict[str, Any]:
        """Analisa prazos e projeta cumprimento"""
        hoje = datetime.now()
        
        # Dias restantes para cada prazo
        dias_final = (self.prazo_final_pnsb - hoje).days
        dias_p1_p2 = (self.prazo_p1_p2 - hoje).days
        dias_questionarios = (self.prazo_questionarios - hoje).days
        
        # Análise de progresso atual
        total_visitas = Visita.query.count()
        visitas_concluidas = Visita.query.filter_by(status='finalizada').count()
        progresso_visitas = (visitas_concluidas / total_visitas * 100) if total_visitas > 0 else 0
        
        # Entidades P1/P2
        entidades_p1_p2 = EntidadeIdentificada.query.filter(
            EntidadeIdentificada.prioridade.in_([1, 2])
        ).count()
        entidades_p1_p2_concluidas = EntidadeIdentificada.query.filter(
            and_(
                EntidadeIdentificada.prioridade.in_([1, 2]),
                EntidadeIdentificada.status_mrs == 'validado_concluido',
                EntidadeIdentificada.status_map == 'validado_concluido'
            )
        ).count()
        progresso_p1_p2 = (entidades_p1_p2_concluidas / entidades_p1_p2 * 100) if entidades_p1_p2 > 0 else 0
        
        # Questionários
        total_questionarios = EntidadeIdentificada.query.filter(
            or_(
                EntidadeIdentificada.mrs_obrigatorio == True,
                EntidadeIdentificada.map_obrigatorio == True
            )
        ).count()
        questionarios_concluidos = EntidadeIdentificada.query.filter(
            or_(
                EntidadeIdentificada.status_mrs == 'validado_concluido',
                EntidadeIdentificada.status_map == 'validado_concluido'
            )
        ).count()
        progresso_questionarios = (questionarios_concluidos / total_questionarios * 100) if total_questionarios > 0 else 0
        
        # Projeção de cumprimento
        velocidade_diaria = self._calcular_velocidade_diaria()
        
        # Calcular se vai cumprir os prazos
        dias_necessarios_p1_p2 = ((100 - progresso_p1_p2) / velocidade_diaria['p1_p2']) if velocidade_diaria['p1_p2'] > 0 else float('inf')
        dias_necessarios_questionarios = ((100 - progresso_questionarios) / velocidade_diaria['questionarios']) if velocidade_diaria['questionarios'] > 0 else float('inf')
        
        cumprimento_p1_p2 = dias_necessarios_p1_p2 <= dias_p1_p2
        cumprimento_questionarios = dias_necessarios_questionarios <= dias_questionarios
        
        return {
            'prazos': {
                'final_pnsb': {
                    'data': self.prazo_final_pnsb.strftime('%d/%m/%Y'),
                    'dias_restantes': dias_final,
                    'status': 'normal' if dias_final > 180 else 'atencao' if dias_final > 90 else 'critico'
                },
                'p1_p2': {
                    'data': self.prazo_p1_p2.strftime('%d/%m/%Y'),
                    'dias_restantes': dias_p1_p2,
                    'progresso_atual': round(progresso_p1_p2, 1),
                    'projecao_cumprimento': cumprimento_p1_p2,
                    'dias_necessarios': round(dias_necessarios_p1_p2) if dias_necessarios_p1_p2 != float('inf') else 'Indefinido',
                    'status': 'ok' if cumprimento_p1_p2 else 'risco'
                },
                'questionarios': {
                    'data': self.prazo_questionarios.strftime('%d/%m/%Y'),
                    'dias_restantes': dias_questionarios,
                    'progresso_atual': round(progresso_questionarios, 1),
                    'projecao_cumprimento': cumprimento_questionarios,
                    'dias_necessarios': round(dias_necessarios_questionarios) if dias_necessarios_questionarios != float('inf') else 'Indefinido',
                    'status': 'ok' if cumprimento_questionarios else 'risco'
                }
            },
            'progresso_geral': {
                'visitas': round(progresso_visitas, 1),
                'p1_p2': round(progresso_p1_p2, 1),
                'questionarios': round(progresso_questionarios, 1)
            }
        }
    
    def _identificar_riscos(self) -> List[Dict[str, Any]]:
        """Identifica riscos ao projeto usando análise preditiva"""
        riscos = []
        hoje = datetime.now()
        
        # 1. Risco de prazo P1/P2
        dias_p1_p2 = (self.prazo_p1_p2 - hoje).days
        entidades_p1_p2_pendentes = EntidadeIdentificada.query.filter(
            and_(
                EntidadeIdentificada.prioridade.in_([1, 2]),
                or_(
                    EntidadeIdentificada.status_mrs != 'validado_concluido',
                    EntidadeIdentificada.status_map != 'validado_concluido'
                )
            )
        ).count()
        
        if entidades_p1_p2_pendentes > 0 and dias_p1_p2 < 60:
            nivel_risco = 'critico' if dias_p1_p2 < 30 else 'alto'
            riscos.append({
                'id': 'prazo_p1_p2',
                'tipo': 'prazo',
                'nivel': nivel_risco,
                'titulo': 'Risco de não cumprimento do prazo P1/P2',
                'descricao': f'{entidades_p1_p2_pendentes} entidades P1/P2 pendentes com apenas {dias_p1_p2} dias restantes',
                'impacto': 'Descumprimento de prazo obrigatório IBGE',
                'probabilidade': 85 if dias_p1_p2 < 30 else 60,
                'acao_recomendada': 'Priorizar imediatamente visitas P1/P2 pendentes'
            })
        
        # 2. Risco de velocidade insuficiente
        velocidade = self._calcular_velocidade_diaria()
        if velocidade['geral'] < 1.0:  # Menos de 1% por dia
            riscos.append({
                'id': 'velocidade_baixa',
                'tipo': 'performance',
                'nivel': 'alto',
                'titulo': 'Velocidade de progresso insuficiente',
                'descricao': f'Velocidade atual de {velocidade["geral"]:.2f}% por dia é insuficiente',
                'impacto': 'Projeto não será concluído no prazo',
                'probabilidade': 90,
                'acao_recomendada': 'Aumentar recursos ou otimizar processos urgentemente'
            })
        
        # 3. Risco de municípios sem progresso
        municipios_sem_progresso = []
        for municipio in self.municipios_sc:
            visitas_mun = Visita.query.filter_by(municipio=municipio, status='finalizada').count()
            if visitas_mun == 0:
                municipios_sem_progresso.append(municipio)
        
        if len(municipios_sem_progresso) > 5:
            riscos.append({
                'id': 'municipios_parados',
                'tipo': 'cobertura',
                'nivel': 'alto',
                'titulo': 'Múltiplos municípios sem progresso',
                'descricao': f'{len(municipios_sem_progresso)} municípios ainda não iniciados',
                'impacto': 'Cobertura incompleta da pesquisa',
                'probabilidade': 75,
                'acao_recomendada': 'Planejar visitas urgentes para municípios não iniciados',
                'municipios': municipios_sem_progresso
            })
        
        # 4. Risco de qualidade de dados
        entidades_sem_contato = EntidadeIdentificada.query.filter(
            and_(
                EntidadeIdentificada.telefone == None,
                EntidadeIdentificada.email == None
            )
        ).count()
        
        if entidades_sem_contato > 10:
            riscos.append({
                'id': 'qualidade_dados',
                'tipo': 'qualidade',
                'nivel': 'medio',
                'titulo': 'Dados de contato incompletos',
                'descricao': f'{entidades_sem_contato} entidades sem informações de contato',
                'impacto': 'Dificuldade para agendar visitas',
                'probabilidade': 60,
                'acao_recomendada': 'Enriquecer dados de contato urgentemente'
            })
        
        # 5. Risco de resistência alta
        visitas_remarcadas = Visita.query.filter_by(status='remarcada').count()
        if visitas_remarcadas > 5:
            riscos.append({
                'id': 'resistencia_alta',
                'tipo': 'operacional',
                'nivel': 'medio',
                'titulo': 'Alta taxa de remarcações',
                'descricao': f'{visitas_remarcadas} visitas foram remarcadas',
                'impacto': 'Atraso no cronograma geral',
                'probabilidade': 50,
                'acao_recomendada': 'Revisar estratégia de abordagem e agendamento'
            })
        
        # Ordenar riscos por nível e probabilidade
        ordem_nivel = {'critico': 0, 'alto': 1, 'medio': 2, 'baixo': 3}
        riscos.sort(key=lambda x: (ordem_nivel.get(x['nivel'], 99), -x['probabilidade']))
        
        return riscos
    
    def _projetar_progresso(self) -> Dict[str, Any]:
        """Projeta progresso futuro baseado em tendências atuais"""
        hoje = datetime.now()
        
        # Coletar dados históricos (últimos 30 dias)
        inicio_analise = hoje - timedelta(days=30)
        
        # Progresso de visitas ao longo do tempo
        visitas_por_semana = []
        for i in range(4):  # 4 semanas
            inicio_semana = inicio_analise + timedelta(weeks=i)
            fim_semana = inicio_semana + timedelta(days=7)
            
            visitas_semana = Visita.query.filter(
                and_(
                    Visita.data >= inicio_semana.date(),
                    Visita.data < fim_semana.date(),
                    Visita.status == 'finalizada'
                )
            ).count()
            
            visitas_por_semana.append({
                'semana': i + 1,
                'visitas': visitas_semana,
                'inicio': inicio_semana.strftime('%d/%m'),
                'fim': fim_semana.strftime('%d/%m')
            })
        
        # Calcular tendência (regressão linear simples)
        if len(visitas_por_semana) > 1:
            x = np.array([s['semana'] for s in visitas_por_semana])
            y = np.array([s['visitas'] for s in visitas_por_semana])
            
            # Evitar divisão por zero
            if len(x) > 1 and np.std(x) > 0:
                coef = np.polyfit(x, y, 1)
                tendencia = coef[0]  # Inclinação da reta
            else:
                tendencia = 0
        else:
            tendencia = 0
        
        # Projetar próximas 4 semanas
        projecao_proximas_semanas = []
        total_visitas = Visita.query.count()
        visitas_concluidas_atual = Visita.query.filter_by(status='finalizada').count()
        
        for i in range(4):
            semana_futura = i + 5  # Continuando da semana 5
            visitas_projetadas = max(0, int(y[-1] + tendencia * (i + 1))) if len(visitas_por_semana) > 0 else 0
            
            projecao_proximas_semanas.append({
                'semana': f'Semana {i + 1}',
                'data_inicio': (hoje + timedelta(weeks=i)).strftime('%d/%m'),
                'visitas_projetadas': visitas_projetadas,
                'acumulado_projetado': visitas_concluidas_atual + sum([p['visitas_projetadas'] for p in projecao_proximas_semanas[:i+1]])
            })
        
        # Calcular data prevista de conclusão
        if tendencia > 0:
            visitas_restantes = total_visitas - visitas_concluidas_atual
            semanas_necessarias = visitas_restantes / (tendencia * 7) if tendencia > 0 else float('inf')
            data_conclusao_prevista = hoje + timedelta(weeks=semanas_necessarias)
        else:
            data_conclusao_prevista = None
            semanas_necessarias = float('inf')
        
        return {
            'historico_semanas': visitas_por_semana,
            'tendencia': {
                'valor': round(tendencia, 2),
                'interpretacao': 'crescente' if tendencia > 0 else 'decrescente' if tendencia < 0 else 'estável',
                'visitas_por_semana_media': round(np.mean(y) if len(visitas_por_semana) > 0 else 0, 1)
            },
            'projecao_futuro': projecao_proximas_semanas,
            'conclusao_prevista': {
                'data': data_conclusao_prevista.strftime('%d/%m/%Y') if data_conclusao_prevista and data_conclusao_prevista.year < 2030 else 'Indeterminada',
                'semanas_necessarias': round(semanas_necessarias) if semanas_necessarias != float('inf') else 'Indefinido',
                'dentro_do_prazo': data_conclusao_prevista < self.prazo_final_pnsb if data_conclusao_prevista else False
            }
        }
    
    def _gerar_alertas_criticos(self) -> List[Dict[str, Any]]:
        """Gera alertas críticos que requerem ação imediata"""
        alertas = []
        hoje = datetime.now()
        
        # Alerta 1: Prazo P1/P2 crítico
        dias_p1_p2 = (self.prazo_p1_p2 - hoje).days
        if dias_p1_p2 <= 30:
            entidades_p1_p2_pendentes = EntidadeIdentificada.query.filter(
                and_(
                    EntidadeIdentificada.prioridade.in_([1, 2]),
                    or_(
                        EntidadeIdentificada.status_mrs != 'validado_concluido',
                        EntidadeIdentificada.status_map != 'validado_concluido'
                    )
                )
            ).all()
            
            if entidades_p1_p2_pendentes:
                alertas.append({
                    'id': 'prazo_p1_p2_critico',
                    'nivel': 'critico',
                    'tipo': 'prazo',
                    'titulo': f'CRÍTICO: {dias_p1_p2} dias para prazo P1/P2',
                    'mensagem': f'{len(entidades_p1_p2_pendentes)} entidades P1/P2 ainda pendentes!',
                    'acao_necessaria': 'Mobilizar toda equipe para visitas P1/P2',
                    'entidades_afetadas': [{'id': e.id, 'nome': e.nome_entidade, 'municipio': e.municipio} for e in entidades_p1_p2_pendentes[:5]],
                    'timestamp': datetime.now().isoformat()
                })
        
        # Alerta 2: Municípios não iniciados
        municipios_nao_iniciados = []
        for municipio in self.municipios_sc:
            visitas = Visita.query.filter_by(municipio=municipio).count()
            if visitas == 0:
                municipios_nao_iniciados.append(municipio)
        
        if municipios_nao_iniciados and dias_p1_p2 < 60:
            alertas.append({
                'id': 'municipios_nao_iniciados',
                'nivel': 'alto',
                'tipo': 'cobertura',
                'titulo': f'{len(municipios_nao_iniciados)} municípios ainda não iniciados',
                'mensagem': 'Risco de cobertura incompleta da pesquisa',
                'acao_necessaria': 'Agendar visitas urgentes nestes municípios',
                'municipios': municipios_nao_iniciados,
                'timestamp': datetime.now().isoformat()
            })
        
        # Alerta 3: Velocidade crítica
        velocidade = self._calcular_velocidade_diaria()
        if velocidade['geral'] < 0.5:  # Menos de 0.5% por dia
            alertas.append({
                'id': 'velocidade_critica',
                'nivel': 'critico',
                'tipo': 'performance',
                'titulo': 'Velocidade de progresso crítica',
                'mensagem': f'Apenas {velocidade["geral"]:.2f}% de progresso por dia',
                'acao_necessaria': 'Revisar processos e aumentar produtividade urgentemente',
                'metricas': {
                    'velocidade_necessaria': 1.5,
                    'velocidade_atual': velocidade['geral'],
                    'deficit': 1.5 - velocidade['geral']
                },
                'timestamp': datetime.now().isoformat()
            })
        
        # Alerta 4: Questionários sem resposta
        questionarios_pendentes_ha_muito = EntidadeIdentificada.query.filter(
            and_(
                EntidadeIdentificada.status_mrs == 'respondido',
                EntidadeIdentificada.identificado_em < (hoje - timedelta(days=14))
            )
        ).count()
        
        if questionarios_pendentes_ha_muito > 5:
            alertas.append({
                'id': 'questionarios_pendentes',
                'nivel': 'alto',
                'tipo': 'follow_up',
                'titulo': 'Questionários aguardando validação há mais de 14 dias',
                'mensagem': f'{questionarios_pendentes_ha_muito} questionários precisam follow-up',
                'acao_necessaria': 'Contatar informantes para finalização',
                'timestamp': datetime.now().isoformat()
            })
        
        # Alerta 5: Taxa de sucesso baixa
        total_visitas = Visita.query.count()
        visitas_finalizadas = Visita.query.filter_by(status='finalizada').count()
        taxa_sucesso = (visitas_finalizadas / total_visitas * 100) if total_visitas > 0 else 0
        
        if taxa_sucesso < 50 and total_visitas > 10:
            alertas.append({
                'id': 'taxa_sucesso_baixa',
                'nivel': 'medio',
                'tipo': 'qualidade',
                'titulo': 'Taxa de sucesso de visitas baixa',
                'mensagem': f'Apenas {taxa_sucesso:.1f}% das visitas são finalizadas',
                'acao_necessaria': 'Revisar estratégia de abordagem',
                'metricas': {
                    'total_visitas': total_visitas,
                    'finalizadas': visitas_finalizadas,
                    'taxa_sucesso': taxa_sucesso
                },
                'timestamp': datetime.now().isoformat()
            })
        
        # Ordenar alertas por nível de criticidade
        ordem_nivel = {'critico': 0, 'alto': 1, 'medio': 2, 'baixo': 3}
        alertas.sort(key=lambda x: ordem_nivel.get(x['nivel'], 99))
        
        return alertas
    
    def _calcular_velocidade_progresso(self) -> Dict[str, float]:
        """Calcula velocidade de progresso em diferentes métricas"""
        hoje = datetime.now()
        inicio_projeto = datetime(2025, 1, 1)  # Ajustar conforme data real
        dias_decorridos = max((hoje - inicio_projeto).days, 1)
        
        # Velocidade geral
        total_visitas = Visita.query.count()
        visitas_concluidas = Visita.query.filter_by(status='finalizada').count()
        progresso_visitas = (visitas_concluidas / total_visitas * 100) if total_visitas > 0 else 0
        velocidade_geral = progresso_visitas / dias_decorridos
        
        # Velocidade P1/P2
        entidades_p1_p2 = EntidadeIdentificada.query.filter(
            EntidadeIdentificada.prioridade.in_([1, 2])
        ).count()
        entidades_p1_p2_concluidas = EntidadeIdentificada.query.filter(
            and_(
                EntidadeIdentificada.prioridade.in_([1, 2]),
                EntidadeIdentificada.status_mrs == 'validado_concluido',
                EntidadeIdentificada.status_map == 'validado_concluido'
            )
        ).count()
        progresso_p1_p2 = (entidades_p1_p2_concluidas / entidades_p1_p2 * 100) if entidades_p1_p2 > 0 else 0
        velocidade_p1_p2 = progresso_p1_p2 / dias_decorridos
        
        # Velocidade questionários
        total_questionarios = EntidadeIdentificada.query.filter(
            or_(
                EntidadeIdentificada.mrs_obrigatorio == True,
                EntidadeIdentificada.map_obrigatorio == True
            )
        ).count()
        questionarios_concluidos = EntidadeIdentificada.query.filter(
            or_(
                EntidadeIdentificada.status_mrs == 'validado_concluido',
                EntidadeIdentificada.status_map == 'validado_concluido'
            )
        ).count()
        progresso_questionarios = (questionarios_concluidos / total_questionarios * 100) if total_questionarios > 0 else 0
        velocidade_questionarios = progresso_questionarios / dias_decorridos
        
        # Velocidade últimos 7 dias
        visitas_ultimos_7_dias = Visita.query.filter(
            and_(
                Visita.data >= (hoje - timedelta(days=7)).date(),
                Visita.status == 'finalizada'
            )
        ).count()
        velocidade_semanal = (visitas_ultimos_7_dias / total_visitas * 100 * 7) if total_visitas > 0 else 0
        
        return {
            'geral': round(velocidade_geral, 2),
            'p1_p2': round(velocidade_p1_p2, 2),
            'questionarios': round(velocidade_questionarios, 2),
            'semanal': round(velocidade_semanal, 2),
            'interpretacao': self._interpretar_velocidade(velocidade_geral)
        }
    
    def _calcular_velocidade_diaria(self) -> Dict[str, float]:
        """Calcula velocidade diária de progresso"""
        velocidade = self._calcular_velocidade_progresso()
        return {
            'geral': velocidade['geral'],
            'p1_p2': velocidade['p1_p2'],
            'questionarios': velocidade['questionarios']
        }
    
    def _interpretar_velocidade(self, velocidade: float) -> str:
        """Interpreta a velocidade de progresso"""
        if velocidade >= 1.5:
            return 'Excelente - Acima da meta'
        elif velocidade >= 1.0:
            return 'Boa - Dentro do esperado'
        elif velocidade >= 0.5:
            return 'Regular - Precisa melhorar'
        else:
            return 'Crítica - Ação urgente necessária'
    
    def _prever_conclusao(self) -> Dict[str, Any]:
        """Prevê datas de conclusão baseado em tendências"""
        velocidade = self._calcular_velocidade_progresso()
        hoje = datetime.now()
        
        # Previsão para visitas
        total_visitas = Visita.query.count()
        visitas_concluidas = Visita.query.filter_by(status='finalizada').count()
        visitas_restantes = total_visitas - visitas_concluidas
        
        if velocidade['geral'] > 0:
            dias_necessarios_visitas = (visitas_restantes / total_visitas * 100) / velocidade['geral']
            data_conclusao_visitas = hoje + timedelta(days=dias_necessarios_visitas)
        else:
            dias_necessarios_visitas = float('inf')
            data_conclusao_visitas = None
        
        # Previsão para P1/P2
        entidades_p1_p2 = EntidadeIdentificada.query.filter(
            EntidadeIdentificada.prioridade.in_([1, 2])
        ).count()
        entidades_p1_p2_pendentes = EntidadeIdentificada.query.filter(
            and_(
                EntidadeIdentificada.prioridade.in_([1, 2]),
                or_(
                    EntidadeIdentificada.status_mrs != 'validado_concluido',
                    EntidadeIdentificada.status_map != 'validado_concluido'
                )
            )
        ).count()
        
        if velocidade['p1_p2'] > 0 and entidades_p1_p2 > 0:
            progresso_restante_p1_p2 = (entidades_p1_p2_pendentes / entidades_p1_p2 * 100)
            dias_necessarios_p1_p2 = progresso_restante_p1_p2 / velocidade['p1_p2']
            data_conclusao_p1_p2 = hoje + timedelta(days=dias_necessarios_p1_p2)
        else:
            dias_necessarios_p1_p2 = float('inf')
            data_conclusao_p1_p2 = None
        
        # Análise de cenários
        cenarios = self._analisar_cenarios_conclusao(velocidade)
        
        return {
            'previsao_atual': {
                'visitas': {
                    'data_prevista': data_conclusao_visitas.strftime('%d/%m/%Y') if data_conclusao_visitas and data_conclusao_visitas.year < 2030 else 'Indeterminada',
                    'dias_necessarios': round(dias_necessarios_visitas) if dias_necessarios_visitas != float('inf') else 'Indefinido',
                    'dentro_prazo': data_conclusao_visitas < self.prazo_final_pnsb if data_conclusao_visitas else False
                },
                'p1_p2': {
                    'data_prevista': data_conclusao_p1_p2.strftime('%d/%m/%Y') if data_conclusao_p1_p2 and data_conclusao_p1_p2.year < 2030 else 'Indeterminada',
                    'dias_necessarios': round(dias_necessarios_p1_p2) if dias_necessarios_p1_p2 != float('inf') else 'Indefinido',
                    'dentro_prazo': data_conclusao_p1_p2 < self.prazo_p1_p2 if data_conclusao_p1_p2 else False
                }
            },
            'cenarios': cenarios,
            'recomendacao': self._gerar_recomendacao_conclusao(velocidade, dias_necessarios_visitas, dias_necessarios_p1_p2)
        }
    
    def _analisar_cenarios_conclusao(self, velocidade_atual: Dict[str, float]) -> Dict[str, Any]:
        """Analisa diferentes cenários de conclusão"""
        hoje = datetime.now()
        
        # Cenário otimista (velocidade aumenta 50%)
        velocidade_otimista = {k: v * 1.5 for k, v in velocidade_atual.items()}
        
        # Cenário pessimista (velocidade cai 30%)
        velocidade_pessimista = {k: v * 0.7 for k, v in velocidade_atual.items()}
        
        # Cenário ideal (velocidade necessária para cumprir prazos)
        dias_ate_p1_p2 = (self.prazo_p1_p2 - hoje).days
        dias_ate_final = (self.prazo_final_pnsb - hoje).days
        
        # Calcular progresso restante
        total_visitas = Visita.query.count()
        visitas_concluidas = Visita.query.filter_by(status='finalizada').count()
        progresso_atual = (visitas_concluidas / total_visitas * 100) if total_visitas > 0 else 0
        progresso_restante = 100 - progresso_atual
        
        velocidade_ideal = {
            'geral': progresso_restante / dias_ate_final if dias_ate_final > 0 else 0,
            'p1_p2': progresso_restante / dias_ate_p1_p2 if dias_ate_p1_p2 > 0 else 0
        }
        
        return {
            'otimista': {
                'velocidade': velocidade_otimista['geral'],
                'dias_conclusao': round((100 - progresso_atual) / velocidade_otimista['geral']) if velocidade_otimista['geral'] > 0 else 'Indefinido',
                'probabilidade': 30
            },
            'realista': {
                'velocidade': velocidade_atual['geral'],
                'dias_conclusao': round((100 - progresso_atual) / velocidade_atual['geral']) if velocidade_atual['geral'] > 0 else 'Indefinido',
                'probabilidade': 50
            },
            'pessimista': {
                'velocidade': velocidade_pessimista['geral'],
                'dias_conclusao': round((100 - progresso_atual) / velocidade_pessimista['geral']) if velocidade_pessimista['geral'] > 0 else 'Indefinido',
                'probabilidade': 20
            },
            'ideal': {
                'velocidade_necessaria': round(velocidade_ideal['geral'], 2),
                'aumento_necessario': round((velocidade_ideal['geral'] / velocidade_atual['geral'] - 1) * 100) if velocidade_atual['geral'] > 0 else 'Indefinido',
                'viavel': velocidade_ideal['geral'] < velocidade_atual['geral'] * 2
            }
        }
    
    def _gerar_recomendacao_conclusao(self, velocidade: Dict[str, float], dias_visitas: float, dias_p1_p2: float) -> str:
        """Gera recomendação baseada nas previsões"""
        if dias_p1_p2 != float('inf') and dias_p1_p2 > (self.prazo_p1_p2 - datetime.now()).days:
            return "URGENTE: Aumentar imediatamente foco em entidades P1/P2 para cumprir prazo obrigatório"
        elif velocidade['geral'] < 0.5:
            return "CRÍTICO: Velocidade atual muito baixa. Implementar medidas emergenciais de aceleração"
        elif velocidade['geral'] < 1.0:
            return "ATENÇÃO: Aumentar produtividade em 50% para garantir cumprimento de prazos"
        else:
            return "Manter ritmo atual e monitorar progresso diariamente"
    
    def _analisar_municipios(self) -> List[Dict[str, Any]]:
        """Analisa situação individual de cada município"""
        analise = []
        
        for municipio in self.municipios_sc:
            # Estatísticas do município
            visitas_total = Visita.query.filter_by(municipio=municipio).count()
            visitas_concluidas = Visita.query.filter_by(municipio=municipio, status='finalizada').count()
            
            entidades = EntidadeIdentificada.query.filter_by(municipio=municipio).all()
            entidades_p1 = [e for e in entidades if e.prioridade == 1]
            entidades_concluidas = [e for e in entidades if e.status_mrs == 'validado_concluido' or e.status_map == 'validado_concluido']
            
            # Calcular progresso
            progresso_visitas = (visitas_concluidas / visitas_total * 100) if visitas_total > 0 else 0
            progresso_entidades = (len(entidades_concluidas) / len(entidades) * 100) if entidades else 0
            
            # Determinar status
            if progresso_entidades >= 80:
                status = 'concluido'
                cor = 'success'
            elif progresso_entidades >= 50:
                status = 'andamento'
                cor = 'warning'
            elif progresso_entidades > 0:
                status = 'iniciado'
                cor = 'info'
            else:
                status = 'pendente'
                cor = 'danger'
            
            # Calcular score de prioridade
            score_prioridade = self._calcular_score_prioridade_municipio(
                municipio, len(entidades_p1), progresso_entidades, visitas_total
            )
            
            analise.append({
                'municipio': municipio,
                'status': status,
                'cor': cor,
                'metricas': {
                    'visitas_total': visitas_total,
                    'visitas_concluidas': visitas_concluidas,
                    'progresso_visitas': round(progresso_visitas, 1),
                    'total_entidades': len(entidades),
                    'entidades_p1': len(entidades_p1),
                    'entidades_concluidas': len(entidades_concluidas),
                    'progresso_entidades': round(progresso_entidades, 1)
                },
                'score_prioridade': score_prioridade,
                'acao_recomendada': self._recomendar_acao_municipio(status, progresso_entidades, len(entidades_p1))
            })
        
        # Ordenar por score de prioridade
        analise.sort(key=lambda x: x['score_prioridade'], reverse=True)
        
        return analise
    
    def _calcular_score_prioridade_municipio(self, municipio: str, entidades_p1: int, 
                                            progresso: float, visitas: int) -> int:
        """Calcula score de prioridade para um município"""
        score = 0
        
        # Mais P1 = maior prioridade
        score += entidades_p1 * 10
        
        # Menos progresso = maior prioridade
        score += (100 - progresso)
        
        # Sem visitas = prioridade máxima
        if visitas == 0:
            score += 50
        
        # Municípios maiores = maior prioridade
        if municipio in ['Itajaí', 'Balneário Camboriú', 'Camboriú']:
            score += 20
        
        return score
    
    def _recomendar_acao_municipio(self, status: str, progresso: float, entidades_p1: int) -> str:
        """Recomenda ação para um município específico"""
        if status == 'pendente':
            return "Iniciar visitas urgentemente"
        elif status == 'iniciado' and entidades_p1 > 0:
            return "Priorizar entidades P1"
        elif status == 'andamento' and progresso < 70:
            return "Intensificar visitas"
        elif status == 'andamento':
            return "Finalizar pendências"
        else:
            return "Monitorar qualidade"
    
    def _calcular_score_saude(self) -> Dict[str, Any]:
        """Calcula score geral de saúde do projeto"""
        # Coletar métricas
        velocidade = self._calcular_velocidade_progresso()
        riscos = self._identificar_riscos()
        alertas = self._gerar_alertas_criticos()
        
        # Calcular scores individuais
        score_velocidade = min(100, velocidade['geral'] * 100)  # 1% por dia = 100 pontos
        score_riscos = max(0, 100 - len([r for r in riscos if r['nivel'] in ['critico', 'alto']]) * 20)
        score_alertas = max(0, 100 - len([a for a in alertas if a['nivel'] == 'critico']) * 30)
        
        # Progresso geral
        total_visitas = Visita.query.count()
        visitas_concluidas = Visita.query.filter_by(status='finalizada').count()
        score_progresso = (visitas_concluidas / total_visitas * 100) if total_visitas > 0 else 0
        
        # Score final (média ponderada)
        score_final = (
            score_velocidade * 0.3 +
            score_riscos * 0.3 +
            score_alertas * 0.2 +
            score_progresso * 0.2
        )
        
        # Classificação
        if score_final >= 80:
            classificacao = 'Excelente'
            cor = 'success'
        elif score_final >= 60:
            classificacao = 'Bom'
            cor = 'info'
        elif score_final >= 40:
            classificacao = 'Regular'
            cor = 'warning'
        else:
            classificacao = 'Crítico'
            cor = 'danger'
        
        return {
            'score_final': round(score_final, 1),
            'classificacao': classificacao,
            'cor': cor,
            'componentes': {
                'velocidade': round(score_velocidade, 1),
                'riscos': round(score_riscos, 1),
                'alertas': round(score_alertas, 1),
                'progresso': round(score_progresso, 1)
            },
            'interpretacao': self._interpretar_score_saude(score_final)
        }
    
    def _interpretar_score_saude(self, score: float) -> str:
        """Interpreta o score de saúde do projeto"""
        if score >= 80:
            return "Projeto saudável e no caminho certo"
        elif score >= 60:
            return "Projeto estável mas requer atenção"
        elif score >= 40:
            return "Projeto em risco - ações corretivas necessárias"
        else:
            return "Projeto em situação crítica - intervenção urgente"
    
    def _gerar_recomendacoes(self, score_saude: Dict[str, Any], riscos: List[Dict[str, Any]]) -> List[str]:
        """Gera recomendações baseadas na análise completa"""
        recomendacoes = []
        
        # Baseadas no score de saúde
        if score_saude['score_final'] < 40:
            recomendacoes.append("🚨 Convocar reunião de emergência para revisar estratégia")
            recomendacoes.append("🚀 Implementar plano de aceleração imediato")
        
        # Baseadas nos riscos
        riscos_criticos = [r for r in riscos if r['nivel'] == 'critico']
        if riscos_criticos:
            recomendacoes.append(f"⚠️ Endereçar {len(riscos_criticos)} riscos críticos imediatamente")
        
        # Baseadas na velocidade
        if score_saude['componentes']['velocidade'] < 50:
            recomendacoes.append("📈 Aumentar recursos ou otimizar processos para melhorar velocidade")
        
        # Baseadas no progresso
        if score_saude['componentes']['progresso'] < 20:
            recomendacoes.append("🎯 Focar em quick wins para aumentar progresso rapidamente")
        
        # Sempre incluir
        recomendacoes.append("📊 Monitorar dashboard diariamente")
        recomendacoes.append("🔄 Atualizar estratégia semanalmente baseado nos dados")
        
        return recomendacoes[:5]  # Limitar a 5 recomendações principais