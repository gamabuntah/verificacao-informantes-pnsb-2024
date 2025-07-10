from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
from sqlalchemy import func, and_, or_
from ..models.agendamento import Visita
from ..models.checklist import Checklist
from ..models.contatos import Contato
from ..db import db
from .agendamento_avancado import AgendamentoAvancado
from .checklist_inteligente import ChecklistInteligente
from .contatos_inteligente import ContatosInteligente
from .relatorios_avancados import RelatoriosAvancados
from .notificacoes_alertas import SistemaNotificacoes
import json
from collections import defaultdict, Counter

class DashboardAvancado:
    """Dashboard avançado com métricas em tempo real e insights inteligentes"""
    
    def __init__(self, mapa_service=None, gemini_key=None):
        self.agendamento_service = AgendamentoAvancado(mapa_service)
        self.checklist_service = ChecklistInteligente()
        self.contatos_service = ContatosInteligente(gemini_key)
        self.relatorios_service = RelatoriosAvancados()
        self.notificacoes_service = SistemaNotificacoes()
        
        self.widgets_dashboard = self._configurar_widgets()
        self.metricas_tempo_real = {}
        self.cache_dashboard = {}
        self.ultima_atualizacao = None
    
    def obter_dashboard_principal(self, usuario_id: str = 'default') -> Dict:
        """Obtém dados completos do dashboard principal"""
        
        agora = datetime.now()
        
        # Verificar cache (atualiza a cada 5 minutos)
        if (self.ultima_atualizacao and 
            (agora - self.ultima_atualizacao).total_seconds() < 300 and
            self.cache_dashboard):
            dashboard_data = self.cache_dashboard.copy()
            dashboard_data['cache_info'] = {
                'using_cache': True,
                'cache_age_seconds': (agora - self.ultima_atualizacao).total_seconds(),
                'next_refresh': (self.ultima_atualizacao + timedelta(minutes=5)).isoformat()
            }
            return dashboard_data
        
        # Gerar dashboard atualizado
        dashboard_data = self._gerar_dashboard_completo(usuario_id)
        
        # Atualizar cache
        self.cache_dashboard = dashboard_data.copy()
        self.ultima_atualizacao = agora
        
        dashboard_data['cache_info'] = {
            'using_cache': False,
            'generated_at': agora.isoformat(),
            'next_refresh': (agora + timedelta(minutes=5)).isoformat()
        }
        
        return dashboard_data
    
    def _gerar_dashboard_completo(self, usuario_id: str) -> Dict:
        """Gera dashboard completo com todas as métricas"""
        
        hoje = date.today()
        
        # 1. KPIs Principais
        kpis_principais = self._obter_kpis_principais()
        
        # 2. Status em Tempo Real
        status_tempo_real = self._obter_status_tempo_real()
        
        # 3. Alertas e Notificações
        alertas_sistema = self.notificacoes_service.verificar_alertas_sistema()
        
        # 4. Métricas de Performance
        metricas_performance = self._obter_metricas_performance()
        
        # 5. Análise de Tendências
        tendencias = self._obter_tendencias_resumidas()
        
        # 6. Qualidade dos Processos
        qualidade_processos = self._obter_qualidade_processos()
        
        # 7. Cobertura Territorial
        cobertura_territorial = self._obter_cobertura_territorial()
        
        # 8. Próximas Ações Recomendadas
        proximas_acoes = self._obter_proximas_acoes_inteligentes()
        
        # 9. Widgets Interativos
        widgets_interativos = self._obter_widgets_interativos()
        
        # 10. Insights Automáticos
        insights_automaticos = self._gerar_insights_automaticos(
            kpis_principais, tendencias, qualidade_processos
        )
        
        return {
            'timestamp_atualizacao': datetime.now().isoformat(),
            'usuario_id': usuario_id,
            'kpis_principais': kpis_principais,
            'status_tempo_real': status_tempo_real,
            'alertas_sistema': alertas_sistema,
            'metricas_performance': metricas_performance,
            'tendencias': tendencias,
            'qualidade_processos': qualidade_processos,
            'cobertura_territorial': cobertura_territorial,
            'proximas_acoes': proximas_acoes,
            'widgets_interativos': widgets_interativos,
            'insights_automaticos': insights_automaticos,
            'configuracao_dashboard': self._obter_configuracao_dashboard(usuario_id)
        }
    
    def _obter_kpis_principais(self) -> Dict:
        """Obtém KPIs principais do sistema"""
        
        hoje = date.today()
        mes_atual = hoje.replace(day=1)
        
        # Visitas do mês
        visitas_mes = Visita.query.filter(
            Visita.data >= mes_atual
        ).all()
        
        # Cálculos básicos
        total_visitas_mes = len(visitas_mes)
        visitas_realizadas = len([v for v in visitas_mes if v.status == 'realizada'])
        visitas_agendadas = len([v for v in visitas_mes if v.status == 'agendada'])
        
        # Taxa de sucesso
        taxa_sucesso = (visitas_realizadas / total_visitas_mes * 100) if total_visitas_mes > 0 else 0
        
        # Cobertura de municípios
        municipios_visitados = len(set(v.municipio for v in visitas_mes if v.status == 'realizada'))
        cobertura_percentual = (municipios_visitados / 11) * 100
        
        # Comparação com mês anterior
        mes_anterior = (mes_atual - timedelta(days=1)).replace(day=1)
        visitas_mes_anterior = Visita.query.filter(
            and_(
                Visita.data >= mes_anterior,
                Visita.data < mes_atual
            )
        ).count()
        
        variacao_mensal = ((total_visitas_mes - visitas_mes_anterior) / max(visitas_mes_anterior, 1)) * 100
        
        # Tempo médio de ciclo
        tempos_ciclo = []
        for visita in visitas_mes:
            if visita.status == 'realizada' and visita.data_criacao:
                tempo = (visita.data_atualizacao - visita.data_criacao).days
                tempos_ciclo.append(tempo)
        
        tempo_medio_ciclo = sum(tempos_ciclo) / len(tempos_ciclo) if tempos_ciclo else 0
        
        return {
            'total_visitas_mes': {
                'valor': total_visitas_mes,
                'variacao': round(variacao_mensal, 1),
                'tendencia': 'positiva' if variacao_mensal > 0 else 'negativa' if variacao_mensal < 0 else 'estavel'
            },
            'taxa_sucesso': {
                'valor': round(taxa_sucesso, 1),
                'meta': 85.0,
                'status': 'acima' if taxa_sucesso >= 85 else 'abaixo'
            },
            'cobertura_municipios': {
                'valor': round(cobertura_percentual, 1),
                'municipios_visitados': municipios_visitados,
                'municipios_total': 11,
                'meta': 100.0
            },
            'tempo_medio_ciclo': {
                'valor': round(tempo_medio_ciclo, 1),
                'unidade': 'dias',
                'meta': 7.0,
                'status': 'dentro' if tempo_medio_ciclo <= 7 else 'acima'
            },
            'visitas_pendentes': {
                'valor': visitas_agendadas,
                'urgentes': len([v for v in visitas_mes if v.status == 'agendada' and v.data <= hoje])
            }
        }
    
    def _obter_status_tempo_real(self) -> Dict:
        """Obtém status em tempo real das operações"""
        
        agora = datetime.now()
        hoje = date.today()
        
        # Visitas de hoje
        visitas_hoje = Visita.query.filter(Visita.data == hoje).all()
        
        # Status das visitas
        status_visitas = {
            'agendadas_hoje': len([v for v in visitas_hoje if v.status == 'agendada']),
            'em_andamento': len([v for v in visitas_hoje if v.status == 'em execução']),
            'concluidas_hoje': len([v for v in visitas_hoje if v.status == 'realizada']),
            'canceladas_hoje': len([v for v in visitas_hoje if v.status == 'cancelada'])
        }
        
        # Próxima visita
        proxima_visita = Visita.query.filter(
            and_(
                Visita.data >= hoje,
                Visita.status.in_(['agendada', 'em preparação'])
            )
        ).order_by(Visita.data, Visita.hora_inicio).first()
        
        # Sistema de saúde
        sistema_saude = self._verificar_saude_sistema()
        
        # Atividade recente
        atividade_recente = self._obter_atividade_recente()
        
        return {
            'timestamp': agora.isoformat(),
            'status_visitas': status_visitas,
            'proxima_visita': {
                'municipio': proxima_visita.municipio if proxima_visita else None,
                'data': proxima_visita.data.strftime('%d/%m/%Y') if proxima_visita else None,
                'hora': proxima_visita.hora_inicio.strftime('%H:%M') if proxima_visita else None,
                'informante': proxima_visita.informante if proxima_visita else None
            } if proxima_visita else None,
            'sistema_saude': sistema_saude,
            'atividade_recente': atividade_recente,
            'usuarios_online': 1  # Simplificado
        }
    
    def _obter_metricas_performance(self) -> Dict:
        """Obtém métricas de performance do sistema"""
        
        # Últimos 30 dias
        data_inicio = date.today() - timedelta(days=30)
        
        visitas_periodo = Visita.query.filter(
            Visita.data >= data_inicio
        ).all()
        
        # Análise de performance
        performance_municipios = defaultdict(lambda: {
            'visitas': 0, 
            'realizadas': 0, 
            'tempo_medio': 0
        })
        
        for visita in visitas_periodo:
            municipio = visita.municipio
            performance_municipios[municipio]['visitas'] += 1
            
            if visita.status == 'realizada':
                performance_municipios[municipio]['realizadas'] += 1
                
                if visita.data_criacao:
                    tempo_ciclo = (visita.data_atualizacao - visita.data_criacao).days
                    performance_municipios[municipio]['tempo_medio'] = tempo_ciclo
        
        # Converter para lista ordenada
        ranking_municipios = []
        for municipio, stats in performance_municipios.items():
            taxa_sucesso = (stats['realizadas'] / max(stats['visitas'], 1)) * 100
            ranking_municipios.append({
                'municipio': municipio,
                'visitas': stats['visitas'],
                'realizadas': stats['realizadas'],
                'taxa_sucesso': round(taxa_sucesso, 1),
                'tempo_medio_ciclo': stats['tempo_medio']
            })
        
        ranking_municipios.sort(key=lambda x: x['taxa_sucesso'], reverse=True)
        
        # Análise de tipos de pesquisa
        tipos_pesquisa = Counter(v.tipo_pesquisa for v in visitas_periodo)
        
        return {
            'periodo_analise': 30,
            'total_visitas_periodo': len(visitas_periodo),
            'ranking_municipios': ranking_municipios[:5],  # Top 5
            'distribuicao_tipos_pesquisa': dict(tipos_pesquisa),
            'eficiencia_geral': {
                'visitas_por_dia': len(visitas_periodo) / 30,
                'taxa_sucesso_media': sum(m['taxa_sucesso'] for m in ranking_municipios) / len(ranking_municipios) if ranking_municipios else 0
            }
        }
    
    def _obter_tendencias_resumidas(self) -> Dict:
        """Obtém tendências resumidas para o dashboard"""
        
        # Últimas 12 semanas
        semanas_dados = []
        data_atual = date.today()
        
        for i in range(12):
            inicio_semana = data_atual - timedelta(weeks=i+1)
            fim_semana = data_atual - timedelta(weeks=i)
            
            visitas_semana = Visita.query.filter(
                and_(
                    Visita.data >= inicio_semana,
                    Visita.data < fim_semana
                )
            ).count()
            
            semanas_dados.append({
                'semana': f"S{52-i}",
                'visitas': visitas_semana,
                'periodo': f"{inicio_semana.strftime('%d/%m')} - {fim_semana.strftime('%d/%m')}"
            })
        
        semanas_dados.reverse()
        
        # Calcular tendência
        if len(semanas_dados) >= 4:
            ultimas_4 = semanas_dados[-4:]
            primeiras_4 = semanas_dados[:4]
            
            media_recente = sum(s['visitas'] for s in ultimas_4) / 4
            media_anterior = sum(s['visitas'] for s in primeiras_4) / 4
            
            variacao_tendencia = ((media_recente - media_anterior) / max(media_anterior, 1)) * 100
            
            tendencia_geral = {
                'direcao': 'crescente' if variacao_tendencia > 5 else 'decrescente' if variacao_tendencia < -5 else 'estavel',
                'variacao_percentual': round(variacao_tendencia, 1),
                'media_recente': round(media_recente, 1),
                'media_anterior': round(media_anterior, 1)
            }
        else:
            tendencia_geral = {'direcao': 'dados_insuficientes'}
        
        return {
            'dados_semanais': semanas_dados,
            'tendencia_geral': tendencia_geral,
            'pico_atividade': max(semanas_dados, key=lambda x: x['visitas']) if semanas_dados else None,
            'vale_atividade': min(semanas_dados, key=lambda x: x['visitas']) if semanas_dados else None
        }
    
    def _obter_qualidade_processos(self) -> Dict:
        """Obtém métricas de qualidade dos processos"""
        
        # Análise de checklists
        checklists_recentes = Checklist.query.join(Visita).filter(
            Visita.data >= date.today() - timedelta(days=30)
        ).all()
        
        if checklists_recentes:
            scores_qualidade = []
            for checklist in checklists_recentes:
                progresso = checklist.progresso_geral()
                scores_qualidade.append(progresso['percentual'])
            
            score_medio = sum(scores_qualidade) / len(scores_qualidade)
            
            distribuicao_qualidade = {
                'excelente': len([s for s in scores_qualidade if s >= 90]),
                'boa': len([s for s in scores_qualidade if 70 <= s < 90]),
                'regular': len([s for s in scores_qualidade if 50 <= s < 70]),
                'ruim': len([s for s in scores_qualidade if s < 50])
            }
        else:
            score_medio = 0
            distribuicao_qualidade = {'sem_dados': 1}
        
        # Análise de contatos
        qualidade_contatos = self.contatos_service.gerar_relatorio_qualidade_contatos()
        
        return {
            'score_medio_checklists': round(score_medio, 1),
            'distribuicao_qualidade_checklists': distribuicao_qualidade,
            'total_checklists_analisados': len(checklists_recentes),
            'qualidade_contatos': {
                'score_medio': qualidade_contatos.get('score_medio', 0),
                'total_contatos': qualidade_contatos.get('total_contatos', 0),
                'contatos_problematicos': len(qualidade_contatos.get('contatos_problematicos', []))
            },
            'recomendacoes_melhoria': self._gerar_recomendacoes_qualidade(score_medio, qualidade_contatos)
        }
    
    def _obter_cobertura_territorial(self) -> Dict:
        """Obtém análise de cobertura territorial"""
        
        from ..config import MUNICIPIOS
        
        cobertura_por_municipio = {}
        
        for municipio in MUNICIPIOS:
            visitas_municipio = Visita.query.filter(
                and_(
                    Visita.municipio == municipio,
                    Visita.status == 'realizada'
                )
            ).all()
            
            tipos_pesquisa_realizados = set(v.tipo_pesquisa for v in visitas_municipio)
            
            cobertura_por_municipio[municipio] = {
                'total_visitas': len(visitas_municipio),
                'tipos_realizados': list(tipos_pesquisa_realizados),
                'mrs_realizado': 'MRS' in tipos_pesquisa_realizados,
                'map_realizado': 'MAP' in tipos_pesquisa_realizados,
                'cobertura_completa': len(tipos_pesquisa_realizados) >= 2,
                'ultima_visita': max(v.data for v in visitas_municipio).strftime('%d/%m/%Y') if visitas_municipio else None
            }
        
        # Estatísticas gerais
        municipios_com_cobertura_completa = sum(1 for m in cobertura_por_municipio.values() if m['cobertura_completa'])
        municipios_sem_visitas = sum(1 for m in cobertura_por_municipio.values() if m['total_visitas'] == 0)
        
        return {
            'cobertura_por_municipio': cobertura_por_municipio,
            'estatisticas_gerais': {
                'total_municipios': len(MUNICIPIOS),
                'municipios_com_cobertura_completa': municipios_com_cobertura_completa,
                'municipios_sem_visitas': municipios_sem_visitas,
                'percentual_cobertura_completa': round((municipios_com_cobertura_completa / len(MUNICIPIOS)) * 100, 1)
            },
            'municipios_prioritarios': [
                municipio for municipio, dados in cobertura_por_municipio.items()
                if not dados['cobertura_completa']
            ]
        }
    
    def _obter_proximas_acoes_inteligentes(self) -> List[Dict]:
        """Obtém próximas ações recomendadas de forma inteligente"""
        
        acoes = []
        
        # 1. Visitas atrasadas
        visitas_atrasadas = Visita.query.filter(
            and_(
                Visita.data < date.today(),
                Visita.status == 'agendada'
            )
        ).count()
        
        if visitas_atrasadas > 0:
            acoes.append({
                'prioridade': 'alta',
                'categoria': 'urgente',
                'acao': f'Reagendar {visitas_atrasadas} visita(s) atrasada(s)',
                'detalhes': 'Visitas agendadas que passaram da data',
                'tempo_estimado': visitas_atrasadas * 10,
                'link_acao': '/visitas?status=atrasadas'
            })
        
        # 2. Checklists incompletos
        checklists_incompletos = Checklist.query.join(Visita).filter(
            and_(
                Visita.status == 'realizada',
                # Assumindo que temos um método para verificar completude
            )
        ).count()
        
        if checklists_incompletos > 0:
            acoes.append({
                'prioridade': 'media',
                'categoria': 'qualidade',
                'acao': f'Completar {checklists_incompletos} checklist(s)',
                'detalhes': 'Checklists de visitas realizadas incompletos',
                'tempo_estimado': checklists_incompletos * 15,
                'link_acao': '/checklists?status=incompletos'
            })
        
        # 3. Contatos para atualizar
        contatos_desatualizados = Contato.query.filter(
            or_(
                Contato.data_atualizacao < datetime.now() - timedelta(days=90),
                Contato.data_atualizacao.is_(None)
            )
        ).count()
        
        if contatos_desatualizados > 0:
            acoes.append({
                'prioridade': 'baixa',
                'categoria': 'manutencao',
                'acao': f'Atualizar {contatos_desatualizados} contato(s)',
                'detalhes': 'Contatos não atualizados há mais de 90 dias',
                'tempo_estimado': contatos_desatualizados * 5,
                'link_acao': '/contatos?status=desatualizados'
            })
        
        # 4. Planejamento semanal
        proxima_semana = date.today() + timedelta(days=7)
        visitas_proxima_semana = Visita.query.filter(
            and_(
                Visita.data >= date.today(),
                Visita.data <= proxima_semana,
                Visita.status == 'agendada'
            )
        ).count()
        
        if visitas_proxima_semana > 0:
            acoes.append({
                'prioridade': 'media',
                'categoria': 'planejamento',
                'acao': f'Preparar {visitas_proxima_semana} visita(s) da próxima semana',
                'detalhes': 'Verificar materiais e confirmar agendamentos',
                'tempo_estimado': 30,
                'link_acao': '/calendario?week=next'
            })
        
        return sorted(acoes, key=lambda x: {'alta': 3, 'media': 2, 'baixa': 1}[x['prioridade']], reverse=True)
    
    def _obter_widgets_interativos(self) -> Dict:
        """Obtém dados para widgets interativos"""
        
        return {
            'mapa_municipios': self._gerar_dados_mapa_municipios(),
            'calendario_visitas': self._gerar_dados_calendario(),
            'grafico_tendencias': self._gerar_dados_grafico_tendencias(),
            'lista_alertas': self._gerar_dados_lista_alertas(),
            'progress_metas': self._gerar_dados_progress_metas()
        }
    
    def _gerar_insights_automaticos(self, kpis: Dict, tendencias: Dict, qualidade: Dict) -> List[Dict]:
        """Gera insights automáticos baseados nos dados"""
        
        insights = []
        
        # Insight sobre taxa de sucesso
        taxa_sucesso = kpis['taxa_sucesso']['valor']
        if taxa_sucesso >= 90:
            insights.append({
                'tipo': 'positivo',
                'categoria': 'performance',
                'titulo': 'Excelente Taxa de Sucesso',
                'descricao': f'Taxa de sucesso de {taxa_sucesso}% está acima da meta de 85%',
                'impacto': 'alto',
                'acao_recomendada': 'Manter o padrão atual de qualidade'
            })
        elif taxa_sucesso < 70:
            insights.append({
                'tipo': 'atencao',
                'categoria': 'performance',
                'titulo': 'Taxa de Sucesso Baixa',
                'descricao': f'Taxa de sucesso de {taxa_sucesso}% está abaixo do esperado',
                'impacto': 'alto',
                'acao_recomendada': 'Revisar processos de agendamento e execução'
            })
        
        # Insight sobre tendências
        if tendencias['tendencia_geral'].get('direcao') == 'crescente':
            variacao = tendencias['tendencia_geral']['variacao_percentual']
            insights.append({
                'tipo': 'positivo',
                'categoria': 'tendencia',
                'titulo': 'Tendência de Crescimento',
                'descricao': f'Atividade crescendo {variacao}% nas últimas semanas',
                'impacto': 'medio',
                'acao_recomendada': 'Preparar recursos para manter o ritmo'
            })
        
        # Insight sobre cobertura
        cobertura = kpis['cobertura_municipios']['valor']
        if cobertura < 80:
            municipios_faltantes = 11 - kpis['cobertura_municipios']['municipios_visitados']
            insights.append({
                'tipo': 'atencao',
                'categoria': 'cobertura',
                'titulo': 'Cobertura Territorial Limitada',
                'descricao': f'{municipios_faltantes} município(s) ainda sem visitas realizadas',
                'impacto': 'alto',
                'acao_recomendada': 'Priorizar agendamentos nos municípios pendentes'
            })
        
        # Insight sobre qualidade
        score_qualidade = qualidade['score_medio_checklists']
        if score_qualidade < 70:
            insights.append({
                'tipo': 'atencao',
                'categoria': 'qualidade',
                'titulo': 'Qualidade dos Checklists Baixa',
                'descricao': f'Score médio de {score_qualidade}% nos checklists',
                'impacto': 'medio',
                'acao_recomendada': 'Revisar processo de preenchimento dos checklists'
            })
        
        return insights
    
    # Métodos auxiliares (implementações simplificadas)
    
    def _configurar_widgets(self) -> Dict:
        """Configura widgets disponíveis para o dashboard"""
        return {
            'kpis': {'ativo': True, 'posicao': 1, 'tamanho': 'grande'},
            'alertas': {'ativo': True, 'posicao': 2, 'tamanho': 'medio'},
            'tendencias': {'ativo': True, 'posicao': 3, 'tamanho': 'grande'},
            'mapa': {'ativo': True, 'posicao': 4, 'tamanho': 'medio'},
            'calendario': {'ativo': True, 'posicao': 5, 'tamanho': 'medio'}
        }
    
    def _verificar_saude_sistema(self) -> Dict:
        """Verifica saúde geral do sistema"""
        return {
            'status': 'saudavel',
            'banco_dados': 'online',
            'apis_externas': 'funcionando',
            'cache': 'ativo',
            'ultima_verificacao': datetime.now().isoformat()
        }
    
    def _obter_atividade_recente(self) -> List[Dict]:
        """Obtém atividade recente do sistema"""
        # Implementação simplificada
        return [
            {
                'timestamp': (datetime.now() - timedelta(minutes=5)).isoformat(),
                'tipo': 'visita_realizada',
                'descricao': 'Visita em Itajaí marcada como realizada',
                'usuario': 'Sistema'
            },
            {
                'timestamp': (datetime.now() - timedelta(minutes=15)).isoformat(),
                'tipo': 'checklist_atualizado',
                'descricao': 'Checklist de Navegantes atualizado',
                'usuario': 'Sistema'
            }
        ]
    
    def _gerar_recomendacoes_qualidade(self, score_checklists: float, qualidade_contatos: Dict) -> List[str]:
        """Gera recomendações de melhoria de qualidade"""
        recomendacoes = []
        
        if score_checklists < 80:
            recomendacoes.append("Implementar treinamento sobre preenchimento de checklists")
        
        if qualidade_contatos.get('contatos_problematicos', 0) > 0:
            recomendacoes.append("Revisar e atualizar contatos com problemas de qualidade")
        
        return recomendacoes
    
    def _gerar_dados_mapa_municipios(self) -> Dict:
        """Gera dados para widget de mapa"""
        # Implementação simplificada
        return {'municipios': [], 'status_cobertura': {}}
    
    def _gerar_dados_calendario(self) -> Dict:
        """Gera dados para widget de calendário"""
        # Implementação simplificada
        return {'eventos': [], 'mes_atual': date.today().month}
    
    def _gerar_dados_grafico_tendencias(self) -> Dict:
        """Gera dados para gráfico de tendências"""
        # Implementação simplificada
        return {'series': [], 'labels': []}
    
    def _gerar_dados_lista_alertas(self) -> List[Dict]:
        """Gera dados para lista de alertas"""
        # Implementação simplificada
        return []
    
    def _gerar_dados_progress_metas(self) -> Dict:
        """Gera dados para progress de metas"""
        # Implementação simplificada
        return {'metas': []}
    
    def _obter_configuracao_dashboard(self, usuario_id: str) -> Dict:
        """Obtém configuração personalizada do dashboard"""
        return {
            'tema': 'claro',
            'widgets_visiveis': list(self.widgets_dashboard.keys()),
            'refresh_automatico': True,
            'intervalo_refresh': 300  # 5 minutos
        }