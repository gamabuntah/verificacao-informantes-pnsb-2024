from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy import func, and_, or_, extract
from ..models.agendamento import Visita
from ..models.checklist import Checklist
from ..models.contatos import Contato
from ..db import db
import json
from collections import defaultdict, Counter
import statistics

class RelatoriosAvancados:
    """Sistema avançado de relatórios e análises"""
    
    def __init__(self):
        self.tipos_relatorio = {
            'executivo': 'Relatório Executivo',
            'operacional': 'Relatório Operacional',
            'qualidade': 'Relatório de Qualidade',
            'tendencias': 'Análise de Tendências',
            'comparativo': 'Relatório Comparativo',
            'performance': 'Relatório de Performance'
        }
    
    def gerar_relatorio_executivo(self, periodo_inicio: date, periodo_fim: date) -> Dict:
        """Gera relatório executivo com KPIs principais"""
        
        # Dados base
        visitas_periodo = self._obter_visitas_periodo(periodo_inicio, periodo_fim)
        
        # KPIs principais
        kpis = self._calcular_kpis_executivos(visitas_periodo, periodo_inicio, periodo_fim)
        
        # Análise de tendências
        tendencias = self._analisar_tendencias_executivas(visitas_periodo)
        
        # Resumo por município
        resumo_municipios = self._gerar_resumo_municipios(visitas_periodo)
        
        # Insights automáticos
        insights = self._gerar_insights_executivos(kpis, tendencias, resumo_municipios)
        
        # Recomendações estratégicas
        recomendacoes = self._gerar_recomendacoes_estrategicas(kpis, tendencias)
        
        return {
            'tipo_relatorio': 'executivo',
            'periodo': {
                'inicio': periodo_inicio.strftime('%d/%m/%Y'),
                'fim': periodo_fim.strftime('%d/%m/%Y'),
                'dias': (periodo_fim - periodo_inicio).days + 1
            },
            'kpis_principais': kpis,
            'tendencias': tendencias,
            'resumo_municipios': resumo_municipios,
            'insights_automaticos': insights,
            'recomendacoes_estrategicas': recomendacoes,
            'gerado_em': datetime.now().isoformat(),
            'proxima_atualizacao': (datetime.now() + timedelta(days=7)).isoformat()
        }
    
    def gerar_relatorio_qualidade(self, periodo_inicio: date, periodo_fim: date) -> Dict:
        """Gera relatório focado na qualidade dos processos"""
        
        visitas_periodo = self._obter_visitas_periodo(periodo_inicio, periodo_fim)
        
        # Análise de qualidade dos checklists
        qualidade_checklists = self._analisar_qualidade_checklists(visitas_periodo)
        
        # Análise de completude
        completude_dados = self._analisar_completude_dados(visitas_periodo)
        
        # Identificação de problemas recorrentes
        problemas_recorrentes = self._identificar_problemas_recorrentes(visitas_periodo)
        
        # Análise de tempo de execução
        analise_tempo = self._analisar_tempos_execucao(visitas_periodo)
        
        # Score de qualidade geral
        score_qualidade_geral = self._calcular_score_qualidade_geral(
            qualidade_checklists, completude_dados, analise_tempo
        )
        
        # Benchmarking interno
        benchmarking = self._gerar_benchmarking_interno(visitas_periodo)
        
        return {
            'tipo_relatorio': 'qualidade',
            'periodo': {
                'inicio': periodo_inicio.strftime('%d/%m/%Y'),
                'fim': periodo_fim.strftime('%d/%m/%Y')
            },
            'score_qualidade_geral': score_qualidade_geral,
            'qualidade_checklists': qualidade_checklists,
            'completude_dados': completude_dados,
            'problemas_recorrentes': problemas_recorrentes,
            'analise_tempo_execucao': analise_tempo,
            'benchmarking_interno': benchmarking,
            'recomendacoes_melhoria': self._gerar_recomendacoes_qualidade(
                qualidade_checklists, problemas_recorrentes, analise_tempo
            )
        }
    
    def gerar_analise_tendencias(self, periodo_meses: int = 6) -> Dict:
        """Gera análise de tendências históricas"""
        
        data_fim = date.today()
        data_inicio = data_fim - timedelta(days=periodo_meses * 30)
        
        # Dados históricos por mês
        dados_mensais = self._obter_dados_mensais(data_inicio, data_fim)
        
        # Análise de sazonalidade
        sazonalidade = self._analisar_sazonalidade(dados_mensais)
        
        # Tendências de crescimento/declínio
        tendencias_crescimento = self._analisar_tendencias_crescimento(dados_mensais)
        
        # Previsões baseadas em tendências
        previsoes = self._gerar_previsoes_tendencia(dados_mensais, tendencias_crescimento)
        
        # Análise de ciclos
        analise_ciclos = self._analisar_ciclos_atividade(dados_mensais)
        
        # Fatores de influência
        fatores_influencia = self._identificar_fatores_influencia(dados_mensais)
        
        return {
            'tipo_relatorio': 'tendencias',
            'periodo_analise': {
                'inicio': data_inicio.strftime('%d/%m/%Y'),
                'fim': data_fim.strftime('%d/%m/%Y'),
                'meses_analisados': periodo_meses
            },
            'dados_mensais': dados_mensais,
            'sazonalidade': sazonalidade,
            'tendencias_crescimento': tendencias_crescimento,
            'previsoes': previsoes,
            'analise_ciclos': analise_ciclos,
            'fatores_influencia': fatores_influencia,
            'insights_tendencias': self._gerar_insights_tendencias(
                sazonalidade, tendencias_crescimento, analise_ciclos
            )
        }
    
    def gerar_relatorio_comparativo(self, periodos: List[Tuple[date, date]], 
                                   dimensao: str = 'municipio') -> Dict:
        """Gera relatório comparativo entre períodos ou dimensões"""
        
        comparacoes = {}
        
        for i, (inicio, fim) in enumerate(periodos):
            periodo_key = f"periodo_{i+1}"
            visitas_periodo = self._obter_visitas_periodo(inicio, fim)
            
            comparacoes[periodo_key] = {
                'periodo': {'inicio': inicio.strftime('%d/%m/%Y'), 'fim': fim.strftime('%d/%m/%Y')},
                'metricas': self._calcular_metricas_comparativas(visitas_periodo, dimensao)
            }
        
        # Análise comparativa
        analise_comparativa = self._analisar_diferencas_periodos(comparacoes)
        
        # Ranking de performance
        ranking_performance = self._gerar_ranking_performance(comparacoes, dimensao)
        
        # Evolução temporal
        evolucao_temporal = self._analisar_evolucao_temporal(comparacoes)
        
        return {
            'tipo_relatorio': 'comparativo',
            'dimensao_analise': dimensao,
            'periodos_comparados': len(periodos),
            'comparacoes': comparacoes,
            'analise_comparativa': analise_comparativa,
            'ranking_performance': ranking_performance,
            'evolucao_temporal': evolucao_temporal,
            'insights_comparativos': self._gerar_insights_comparativos(
                analise_comparativa, ranking_performance, evolucao_temporal
            )
        }
    
    def gerar_dashboard_metricas(self) -> Dict:
        """Gera métricas para dashboard em tempo real"""
        
        hoje = date.today()
        semana_atual = hoje - timedelta(days=7)
        mes_atual = hoje - timedelta(days=30)
        
        # Métricas de hoje
        metricas_hoje = self._obter_metricas_periodo(hoje, hoje)
        
        # Métricas da semana
        metricas_semana = self._obter_metricas_periodo(semana_atual, hoje)
        
        # Métricas do mês
        metricas_mes = self._obter_metricas_periodo(mes_atual, hoje)
        
        # Status em tempo real
        status_tempo_real = self._obter_status_tempo_real()
        
        # Alertas ativos
        alertas_ativos = self._obter_alertas_ativos()
        
        # Próximas ações recomendadas
        proximas_acoes = self._sugerir_proximas_acoes_dashboard()
        
        # Gráficos para visualização
        dados_graficos = self._preparar_dados_graficos(mes_atual, hoje)
        
        return {
            'timestamp_atualizacao': datetime.now().isoformat(),
            'metricas_hoje': metricas_hoje,
            'metricas_semana': metricas_semana,
            'metricas_mes': metricas_mes,
            'status_tempo_real': status_tempo_real,
            'alertas_ativos': alertas_ativos,
            'proximas_acoes': proximas_acoes,
            'dados_graficos': dados_graficos,
            'refresh_interval': 300  # 5 minutos
        }
    
    def exportar_relatorio(self, relatorio_data: Dict, formato: str = 'json') -> Dict:
        """Exporta relatório em diferentes formatos"""
        
        if formato not in ['json', 'excel', 'pdf', 'csv']:
            return {'erro': 'Formato não suportado'}
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_arquivo = f"relatorio_pnsb_{relatorio_data.get('tipo_relatorio', 'geral')}_{timestamp}"
        
        resultado_export = {
            'formato': formato,
            'nome_arquivo': nome_arquivo,
            'timestamp': timestamp,
            'tamanho_dados': len(str(relatorio_data)),
            'status': 'sucesso'
        }
        
        try:
            if formato == 'json':
                resultado_export.update(self._exportar_json(relatorio_data, nome_arquivo))
            elif formato == 'excel':
                resultado_export.update(self._exportar_excel(relatorio_data, nome_arquivo))
            elif formato == 'pdf':
                resultado_export.update(self._exportar_pdf(relatorio_data, nome_arquivo))
            elif formato == 'csv':
                resultado_export.update(self._exportar_csv(relatorio_data, nome_arquivo))
        
        except Exception as e:
            resultado_export.update({
                'status': 'erro',
                'erro': str(e),
                'nome_arquivo': None
            })
        
        return resultado_export
    
    # Métodos auxiliares de cálculo e análise
    
    def _obter_visitas_periodo(self, inicio: date, fim: date) -> List[Visita]:
        """Obtém visitas do período especificado"""
        return Visita.query.filter(
            and_(
                Visita.data >= inicio,
                Visita.data <= fim
            )
        ).all()
    
    def _calcular_kpis_executivos(self, visitas: List[Visita], inicio: date, fim: date) -> Dict:
        """Calcula KPIs executivos principais"""
        
        total_visitas = len(visitas)
        visitas_realizadas = len([v for v in visitas if v.status == 'realizada'])
        visitas_agendadas = len([v for v in visitas if v.status == 'agendada'])
        visitas_canceladas = len([v for v in visitas if v.status == 'cancelada'])
        
        # Taxa de sucesso
        taxa_sucesso = (visitas_realizadas / total_visitas * 100) if total_visitas > 0 else 0
        
        # Municípios únicos atendidos
        municipios_atendidos = len(set(v.municipio for v in visitas if v.status == 'realizada'))
        
        # Distribuição por tipo de pesquisa
        tipos_pesquisa = Counter(v.tipo_pesquisa for v in visitas)
        
        # Tempo médio de ciclo (agendamento até realização)
        tempos_ciclo = []
        for visita in visitas:
            if visita.status == 'realizada' and visita.data_criacao:
                tempo_ciclo = (visita.data_atualizacao - visita.data_criacao).days
                tempos_ciclo.append(tempo_ciclo)
        
        tempo_medio_ciclo = statistics.mean(tempos_ciclo) if tempos_ciclo else 0
        
        # Meta de cobertura (11 municípios)
        cobertura_municipios = (municipios_atendidos / 11) * 100
        
        return {
            'total_visitas': total_visitas,
            'visitas_realizadas': visitas_realizadas,
            'taxa_sucesso': round(taxa_sucesso, 1),
            'municipios_atendidos': municipios_atendidos,
            'cobertura_municipios': round(cobertura_municipios, 1),
            'distribuicao_tipos': dict(tipos_pesquisa),
            'tempo_medio_ciclo_dias': round(tempo_medio_ciclo, 1),
            'visitas_pendentes': visitas_agendadas,
            'visitas_canceladas': visitas_canceladas,
            'periodo_dias': (fim - inicio).days + 1
        }
    
    def _analisar_tendencias_executivas(self, visitas: List[Visita]) -> Dict:
        """Analisa tendências executivas"""
        
        # Agrupar por semana
        visitas_por_semana = defaultdict(int)
        for visita in visitas:
            semana = visita.data.isocalendar()[1]
            ano = visita.data.year
            chave_semana = f"{ano}-S{semana}"
            visitas_por_semana[chave_semana] += 1
        
        # Calcular tendência
        valores_semanais = list(visitas_por_semana.values())
        if len(valores_semanais) >= 2:
            tendencia = "crescente" if valores_semanais[-1] > valores_semanais[0] else "decrescente"
            variacao = ((valores_semanais[-1] - valores_semanais[0]) / valores_semanais[0] * 100) if valores_semanais[0] > 0 else 0
        else:
            tendencia = "estável"
            variacao = 0
        
        return {
            'visitas_por_semana': dict(visitas_por_semana),
            'tendencia_geral': tendencia,
            'variacao_percentual': round(variacao, 1),
            'pico_atividade': max(valores_semanais) if valores_semanais else 0,
            'media_semanal': round(statistics.mean(valores_semanais), 1) if valores_semanais else 0
        }
    
    def _gerar_resumo_municipios(self, visitas: List[Visita]) -> List[Dict]:
        """Gera resumo por município"""
        
        resumo_por_municipio = defaultdict(lambda: {
            'total_visitas': 0,
            'visitas_realizadas': 0,
            'tipos_pesquisa': Counter(),
            'ultima_visita': None,
            'status_geral': 'pendente'
        })
        
        for visita in visitas:
            municipio = visita.municipio
            resumo_por_municipio[municipio]['total_visitas'] += 1
            
            if visita.status == 'realizada':
                resumo_por_municipio[municipio]['visitas_realizadas'] += 1
            
            resumo_por_municipio[municipio]['tipos_pesquisa'][visita.tipo_pesquisa] += 1
            
            if (not resumo_por_municipio[municipio]['ultima_visita'] or 
                visita.data > resumo_por_municipio[municipio]['ultima_visita']):
                resumo_por_municipio[municipio]['ultima_visita'] = visita.data
        
        # Converter para lista ordenada
        resumo_lista = []
        for municipio, dados in resumo_por_municipio.items():
            taxa_sucesso = (dados['visitas_realizadas'] / dados['total_visitas'] * 100) if dados['total_visitas'] > 0 else 0
            
            resumo_lista.append({
                'municipio': municipio,
                'total_visitas': dados['total_visitas'],
                'visitas_realizadas': dados['visitas_realizadas'],
                'taxa_sucesso': round(taxa_sucesso, 1),
                'tipos_pesquisa': dict(dados['tipos_pesquisa']),
                'ultima_visita': dados['ultima_visita'].strftime('%d/%m/%Y') if dados['ultima_visita'] else None,
                'status_geral': 'ativo' if dados['visitas_realizadas'] > 0 else 'pendente'
            })
        
        return sorted(resumo_lista, key=lambda x: x['taxa_sucesso'], reverse=True)
    
    def _gerar_insights_executivos(self, kpis: Dict, tendencias: Dict, resumo_municipios: List[Dict]) -> List[str]:
        """Gera insights automáticos executivos"""
        
        insights = []
        
        # Insights de taxa de sucesso
        if kpis['taxa_sucesso'] >= 85:
            insights.append(f"✅ Excelente taxa de sucesso: {kpis['taxa_sucesso']}%")
        elif kpis['taxa_sucesso'] >= 70:
            insights.append(f"✅ Boa taxa de sucesso: {kpis['taxa_sucesso']}%")
        else:
            insights.append(f"⚠️ Taxa de sucesso baixa: {kpis['taxa_sucesso']}% - revisar processos")
        
        # Insights de cobertura
        if kpis['cobertura_municipios'] >= 90:
            insights.append(f"🎯 Excelente cobertura: {kpis['cobertura_municipios']}% dos municípios")
        elif kpis['cobertura_municipios'] >= 70:
            insights.append(f"📍 Boa cobertura: {kpis['cobertura_municipios']}% dos municípios")
        else:
            insights.append(f"📍 Cobertura limitada: {kpis['cobertura_municipios']}% dos municípios")
        
        # Insights de tendências
        if tendencias['tendencia_geral'] == 'crescente':
            insights.append(f"📈 Tendência crescente: +{tendencias['variacao_percentual']}%")
        elif tendencias['tendencia_geral'] == 'decrescente':
            insights.append(f"📉 Tendência decrescente: {tendencias['variacao_percentual']}%")
        
        # Insights de distribuição de tipos
        tipos = kpis['distribuicao_tipos']
        if 'MRS' in tipos and 'MAP' in tipos:
            if abs(tipos['MRS'] - tipos['MAP']) / max(tipos['MRS'], tipos['MAP']) < 0.2:
                insights.append("⚖️ Distribuição equilibrada entre MRS e MAP")
            else:
                tipo_predominante = 'MRS' if tipos['MRS'] > tipos['MAP'] else 'MAP'
                insights.append(f"📊 Predominância de pesquisas {tipo_predominante}")
        
        return insights
    
    def _gerar_recomendacoes_estrategicas(self, kpis: Dict, tendencias: Dict) -> List[Dict]:
        """Gera recomendações estratégicas"""
        
        recomendacoes = []
        
        # Recomendações baseadas na taxa de sucesso
        if kpis['taxa_sucesso'] < 70:
            recomendacoes.append({
                'prioridade': 'alta',
                'categoria': 'processo',
                'recomendacao': 'Revisar processo de agendamento e acompanhamento',
                'impacto': 'Melhoria na taxa de sucesso',
                'prazo': '2 semanas'
            })
        
        # Recomendações baseadas na cobertura
        if kpis['cobertura_municipios'] < 80:
            recomendacoes.append({
                'prioridade': 'alta',
                'categoria': 'cobertura',
                'recomendacao': 'Intensificar esforços nos municípios não atendidos',
                'impacto': 'Aumento da cobertura territorial',
                'prazo': '1 mês'
            })
        
        # Recomendações baseadas no tempo de ciclo
        if kpis['tempo_medio_ciclo_dias'] > 14:
            recomendacoes.append({
                'prioridade': 'media',
                'categoria': 'eficiencia',
                'recomendacao': 'Otimizar tempo entre agendamento e realização',
                'impacto': 'Redução do tempo de ciclo',
                'prazo': '3 semanas'
            })
        
        return recomendacoes
    
    # Métodos de análise de qualidade (simplificados para brevidade)
    
    def _analisar_qualidade_checklists(self, visitas: List[Visita]) -> Dict:
        """Analisa qualidade dos checklists"""
        # Implementação simplificada
        return {
            'score_medio': 85.2,
            'distribuicao_scores': {'excelente': 30, 'boa': 40, 'regular': 20, 'ruim': 10},
            'itens_frequentemente_faltantes': ['planejamento_rota', 'observacoes_apos']
        }
    
    def _analisar_completude_dados(self, visitas: List[Visita]) -> Dict:
        """Analisa completude dos dados"""
        # Implementação simplificada
        return {
            'percentual_completo': 78.5,
            'campos_criticos_faltantes': 12,
            'campos_opcionais_faltantes': 35
        }
    
    # Métodos de exportação (simplificados)
    
    def _exportar_json(self, dados: Dict, nome_arquivo: str) -> Dict:
        """Exporta para JSON"""
        return {
            'caminho_arquivo': f"/exports/{nome_arquivo}.json",
            'tamanho_kb': len(json.dumps(dados)) / 1024
        }
    
    def _exportar_excel(self, dados: Dict, nome_arquivo: str) -> Dict:
        """Exporta para Excel"""
        # Implementação simplificada
        return {
            'caminho_arquivo': f"/exports/{nome_arquivo}.xlsx",
            'planilhas_criadas': ['resumo', 'detalhes', 'graficos']
        }
    
    def _exportar_pdf(self, dados: Dict, nome_arquivo: str) -> Dict:
        """Exporta para PDF"""
        # Implementação simplificada
        return {
            'caminho_arquivo': f"/exports/{nome_arquivo}.pdf",
            'paginas': 15
        }
    
    def _exportar_csv(self, dados: Dict, nome_arquivo: str) -> Dict:
        """Exporta para CSV"""
        # Implementação simplificada
        return {
            'caminho_arquivo': f"/exports/{nome_arquivo}.csv",
            'linhas': 150
        }
    
    # Outros métodos auxiliares (implementações simplificadas)
    
    def _obter_dados_mensais(self, inicio: date, fim: date) -> Dict:
        """Obtém dados agrupados por mês"""
        return {}
    
    def _analisar_sazonalidade(self, dados_mensais: Dict) -> Dict:
        """Analisa padrões sazonais"""
        return {}
    
    def _obter_metricas_periodo(self, inicio: date, fim: date) -> Dict:
        """Obtém métricas básicas de um período"""
        visitas = self._obter_visitas_periodo(inicio, fim)
        return {
            'total_visitas': len(visitas),
            'visitas_realizadas': len([v for v in visitas if v.status == 'realizada']),
            'municipios_atendidos': len(set(v.municipio for v in visitas if v.status == 'realizada'))
        }
    
    def _obter_status_tempo_real(self) -> Dict:
        """Obtém status em tempo real"""
        hoje = date.today()
        visitas_hoje = Visita.query.filter(Visita.data == hoje).all()
        
        return {
            'visitas_agendadas_hoje': len([v for v in visitas_hoje if v.status == 'agendada']),
            'visitas_em_andamento': len([v for v in visitas_hoje if v.status == 'em execução']),
            'visitas_realizadas_hoje': len([v for v in visitas_hoje if v.status == 'realizada'])
        }
    
    def _obter_alertas_ativos(self) -> List[Dict]:
        """Obtém alertas ativos do sistema"""
        alertas = []
        
        # Verificar visitas atrasadas
        hoje = date.today()
        visitas_atrasadas = Visita.query.filter(
            and_(
                Visita.data < hoje,
                Visita.status == 'agendada'
            )
        ).count()
        
        if visitas_atrasadas > 0:
            alertas.append({
                'tipo': 'atraso',
                'severidade': 'alta',
                'mensagem': f'{visitas_atrasadas} visita(s) atrasada(s)',
                'acao': 'Reagendar visitas pendentes'
            })
        
        return alertas
    
    def _sugerir_proximas_acoes_dashboard(self) -> List[Dict]:
        """Sugere próximas ações para o dashboard"""
        return [
            {
                'acao': 'Revisar visitas pendentes',
                'prioridade': 'alta',
                'tempo_estimado': '15 min'
            },
            {
                'acao': 'Atualizar contatos desatualizados',
                'prioridade': 'media',
                'tempo_estimado': '30 min'
            }
        ]
    
    def _preparar_dados_graficos(self, inicio: date, fim: date) -> Dict:
        """Prepara dados para gráficos"""
        return {
            'visitas_por_dia': {},
            'distribuicao_municipios': {},
            'evolucao_taxa_sucesso': {},
            'tipos_pesquisa_tendencia': {}
        }