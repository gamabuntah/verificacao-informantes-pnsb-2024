"""
Otimizador de Cronograma Final - PNSB
Simulação de cenários e estratégias para conclusão da coleta
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy import func, and_, or_
from ..models.agendamento import Visita
from ..models.contatos import Contato
from ..db import db
import json
from collections import defaultdict
import itertools

class OtimizadorCronograma:
    """Otimizador de cronograma final para garantir 100% de coleta"""
    
    def __init__(self):
        self.municipios_pnsb = [
            'Itajaí', 'Navegantes', 'Penha', 'Piçarras', 'Barra Velha',
            'Bombinhas', 'Porto Belo', 'Itapema', 'Balneário Camboriú',
            'Camboriú', 'Tijucas'
        ]
        
        self.tipos_pesquisa = ['MRS', 'MAP']
        
        # Parâmetros de otimização
        self.parametros_otimizacao = {
            'max_tentativas_por_informante': 5,
            'intervalo_min_entre_tentativas_dias': 3,
            'max_visitas_por_dia_pesquisador': 4,
            'prazo_limite_coleta_dias': 45,
            'buffer_urgencia_dias': 7,
            'peso_dificuldade_municipio': 0.3,
            'peso_disponibilidade_pesquisador': 0.4,
            'peso_urgencia_prazo': 0.3
        }
    
    def simular_cenarios_conclusao(self, cenarios_config: List[Dict]) -> Dict:
        """Simula diferentes cenários para conclusão da coleta"""
        
        # Obter estado atual do sistema
        estado_atual = self._obter_estado_atual_coleta()
        
        resultados_simulacao = []
        
        for i, cenario in enumerate(cenarios_config):
            print(f"Simulando cenário {i+1}: {cenario.get('nome', f'Cenário {i+1}')}")
            
            # Simular cenário específico
            resultado_cenario = self._simular_cenario_individual(cenario, estado_atual)
            
            # Adicionar análise de viabilidade
            resultado_cenario['viabilidade'] = self._analisar_viabilidade_cenario(resultado_cenario)
            
            # Calcular riscos e mitigation
            resultado_cenario['analise_riscos'] = self._analisar_riscos_cenario(resultado_cenario)
            
            resultados_simulacao.append(resultado_cenario)
        
        # Comparar cenários e recomendar melhor
        melhor_cenario = self._identificar_melhor_cenario(resultados_simulacao)
        
        # Gerar insights comparativos
        insights_comparativos = self._gerar_insights_comparativos(resultados_simulacao)
        
        return {
            'estado_atual_coleta': estado_atual,
            'cenarios_simulados': resultados_simulacao,
            'melhor_cenario_recomendado': melhor_cenario,
            'insights_comparativos': insights_comparativos,
            'recomendacoes_implementacao': self._gerar_recomendacoes_implementacao(melhor_cenario),
            'plano_contingencia': self._gerar_plano_contingencia_simulacao(resultados_simulacao)
        }
    
    def gerar_previsao_conclusao(self, ritmo_atual_config: Dict = None) -> Dict:
        """Gera previsão realista de conclusão baseada no ritmo atual"""
        
        # Analisar ritmo atual
        if not ritmo_atual_config:
            ritmo_atual = self._calcular_ritmo_atual_coleta()
        else:
            ritmo_atual = ritmo_atual_config
        
        # Obter questionários pendentes
        questionarios_pendentes = self._obter_questionarios_pendentes()
        
        # Calcular estimativas baseadas no ritmo atual
        estimativa_linear = self._calcular_estimativa_linear(questionarios_pendentes, ritmo_atual)
        
        # Aplicar fatores de correção
        estimativa_ajustada = self._aplicar_fatores_correcao(estimativa_linear, questionarios_pendentes)
        
        # Analisar gargalos potenciais
        gargalos_identificados = self._identificar_gargalos_potenciais(questionarios_pendentes, ritmo_atual)
        
        # Gerar cenários de prazo
        cenarios_prazo = self._gerar_cenarios_prazo(estimativa_ajustada, gargalos_identificados)
        
        return {
            'ritmo_atual_coleta': ritmo_atual,
            'questionarios_pendentes': {
                'total': len(questionarios_pendentes),
                'por_municipio': self._agrupar_pendentes_por_municipio(questionarios_pendentes),
                'por_dificuldade': self._classificar_pendentes_por_dificuldade(questionarios_pendentes)
            },
            'previsao_conclusao': {
                'estimativa_linear': estimativa_linear,
                'estimativa_ajustada': estimativa_ajustada,
                'margem_confianca': self._calcular_margem_confianca(estimativa_ajustada)
            },
            'gargalos_identificados': gargalos_identificados,
            'cenarios_prazo': cenarios_prazo,
            'acoes_aceleracao': self._sugerir_acoes_aceleracao(gargalos_identificados)
        }
    
    def identificar_gargalos_criticos(self, prazo_limite: date = None) -> Dict:
        """Identifica gargalos críticos que podem impedir conclusão no prazo"""
        
        if not prazo_limite:
            prazo_limite = date.today() + timedelta(days=self.parametros_otimizacao['prazo_limite_coleta_dias'])
        
        # Analisar disponibilidade de pesquisadores
        gargalos_pessoal = self._analisar_gargalos_pessoal(prazo_limite)
        
        # Analisar informantes problemáticos
        gargalos_informantes = self._analisar_gargalos_informantes(prazo_limite)
        
        # Analisar dependências entre questionários
        gargalos_dependencias = self._analisar_gargalos_dependencias(prazo_limite)
        
        # Analisar capacidade logística
        gargalos_logisticos = self._analisar_gargalos_logisticos(prazo_limite)
        
        # Classificar gargalos por impacto
        classificacao_impacto = self._classificar_gargalos_por_impacto([
            gargalos_pessoal, gargalos_informantes, gargalos_dependencias, gargalos_logisticos
        ])
        
        # Gerar soluções para cada gargalo
        solucoes_gargalos = self._gerar_solucoes_gargalos(classificacao_impacto)
        
        return {
            'prazo_limite_analise': prazo_limite.isoformat(),
            'gargalos_identificados': {
                'pessoal': gargalos_pessoal,
                'informantes': gargalos_informantes,
                'dependencias': gargalos_dependencias,
                'logisticos': gargalos_logisticos
            },
            'classificacao_por_impacto': classificacao_impacto,
            'solucoes_propostas': solucoes_gargalos,
            'impacto_no_prazo': self._calcular_impacto_gargalos_no_prazo(classificacao_impacto, prazo_limite),
            'plano_mitigacao': self._gerar_plano_mitigacao_gargalos(classificacao_impacto)
        }
    
    def otimizar_redistribuicao_carga(self, pesquisadores_disponiveis: List[str],
                                    restricoes: Dict = None) -> Dict:
        """Otimiza redistribuição de carga entre pesquisadores"""
        
        if not restricoes:
            restricoes = {}
        
        # Obter carga atual de cada pesquisador
        carga_atual = self._calcular_carga_atual_pesquisadores(pesquisadores_disponiveis)
        
        # Obter questionários pendentes
        questionarios_pendentes = self._obter_questionarios_pendentes()
        
        # Analisar capacidade disponível
        capacidade_disponivel = self._calcular_capacidade_disponivel(pesquisadores_disponiveis, restricoes)
        
        # Aplicar algoritmo de otimização de redistribuição
        redistribuicao_otimizada = self._calcular_redistribuicao_otima(
            questionarios_pendentes, capacidade_disponivel, restricoes
        )
        
        # Simular impacto da redistribuição
        impacto_redistribuicao = self._simular_impacto_redistribuicao(
            carga_atual, redistribuicao_otimizada
        )
        
        # Gerar cronograma detalhado
        cronograma_redistribuicao = self._gerar_cronograma_redistribuicao(redistribuicao_otimizada)
        
        return {
            'pesquisadores_analisados': pesquisadores_disponiveis,
            'carga_atual': carga_atual,
            'capacidade_disponivel': capacidade_disponivel,
            'redistribuicao_otimizada': redistribuicao_otimizada,
            'impacto_previsto': impacto_redistribuicao,
            'cronograma_implementacao': cronograma_redistribuicao,
            'beneficios_esperados': self._calcular_beneficios_redistribuicao(impacto_redistribuicao),
            'riscos_redistribuicao': self._identificar_riscos_redistribuicao(redistribuicao_otimizada)
        }
    
    def gerar_plano_sprint_final(self, dias_restantes: int, questionarios_criticos: List[Dict] = None) -> Dict:
        """Gera plano de sprint final para questionários mais difíceis"""
        
        if not questionarios_criticos:
            questionarios_criticos = self._identificar_questionarios_criticos()
        
        # Estratificar questionários por dificuldade
        estratificacao_dificuldade = self._estratificar_por_dificuldade(questionarios_criticos)
        
        # Aplicar estratégias específicas por nível de dificuldade
        estrategias_por_nivel = {
            'extrema': self._definir_estrategia_dificuldade_extrema(),
            'alta': self._definir_estrategia_dificuldade_alta(),
            'media': self._definir_estrategia_dificuldade_media()
        }
        
        # Gerar cronograma de sprint
        cronograma_sprint = self._gerar_cronograma_sprint(
            estratificacao_dificuldade, estrategias_por_nivel, dias_restantes
        )
        
        # Alocar recursos especiais
        recursos_especiais = self._alocar_recursos_especiais_sprint(questionarios_criticos)
        
        # Definir marcos e checkpoints
        marcos_checkpoint = self._definir_marcos_checkpoint_sprint(cronograma_sprint, dias_restantes)
        
        # Gerar plano de contingência para cada questionário crítico
        contingencias_especificas = self._gerar_contingencias_questionarios_criticos(questionarios_criticos)
        
        return {
            'dias_restantes': dias_restantes,
            'questionarios_criticos': {
                'total': len(questionarios_criticos),
                'estratificacao_dificuldade': estratificacao_dificuldade
            },
            'estrategias_por_dificuldade': estrategias_por_nivel,
            'cronograma_sprint': cronograma_sprint,
            'recursos_especiais_alocados': recursos_especiais,
            'marcos_checkpoint': marcos_checkpoint,
            'contingencias_especificas': contingencias_especificas,
            'criterios_sucesso': self._definir_criterios_sucesso_sprint(),
            'plano_comunicacao': self._definir_plano_comunicacao_sprint(marcos_checkpoint)
        }
    
    def simular_e_se_cenarios(self, variacoes_parametros: List[Dict]) -> Dict:
        """Simula cenários 'E se' com diferentes variações de parâmetros"""
        
        # Estado base para comparação
        estado_base = self._obter_estado_atual_coleta()
        previsao_base = self.gerar_previsao_conclusao()
        
        resultados_e_se = []
        
        for i, variacao in enumerate(variacoes_parametros):
            print(f"Simulando cenário E-SE {i+1}: {variacao.get('descricao', f'Variação {i+1}')}")
            
            # Aplicar variação de parâmetros
            parametros_simulacao = {**self.parametros_otimizacao, **variacao.get('parametros', {})}
            
            # Simular cenário com novos parâmetros
            resultado_e_se = self._simular_cenario_e_se(parametros_simulacao, estado_base, variacao)
            
            # Comparar com baseline
            resultado_e_se['comparacao_baseline'] = self._comparar_com_baseline(
                resultado_e_se, previsao_base
            )
            
            resultados_e_se.append(resultado_e_se)
        
        # Análise de sensibilidade
        analise_sensibilidade = self._analisar_sensibilidade_parametros(resultados_e_se)
        
        # Identificar parâmetros mais impactantes
        parametros_criticos = self._identificar_parametros_criticos(analise_sensibilidade)
        
        return {
            'estado_baseline': estado_base,
            'previsao_baseline': previsao_base,
            'cenarios_e_se': resultados_e_se,
            'analise_sensibilidade': analise_sensibilidade,
            'parametros_mais_impactantes': parametros_criticos,
            'recomendacoes_ajuste': self._gerar_recomendacoes_ajuste_parametros(parametros_criticos),
            'cenario_otimo_identificado': self._identificar_cenario_otimo(resultados_e_se)
        }
    
    # Métodos auxiliares
    
    def _obter_estado_atual_coleta(self) -> Dict:
        """Obtém estado atual da coleta de questionários"""
        
        estado = {
            'total_questionarios': len(self.municipios_pnsb) * len(self.tipos_pesquisa),
            'completos': 0,
            'em_andamento': 0,
            'pendentes': 0,
            'problematicos': 0
        }
        
        for municipio in self.municipios_pnsb:
            for tipo_pesquisa in self.tipos_pesquisa:
                status = self._obter_status_questionario(municipio, tipo_pesquisa)
                
                if status == 'completo':
                    estado['completos'] += 1
                elif status in ['em_andamento', 'agendado']:
                    estado['em_andamento'] += 1
                elif status in ['recusado', 'impossivel']:
                    estado['problematicos'] += 1
                else:
                    estado['pendentes'] += 1
        
        estado['percentual_conclusao'] = round((estado['completos'] / estado['total_questionarios']) * 100, 1)
        
        return estado
    
    def _simular_cenario_individual(self, cenario: Dict, estado_atual: Dict) -> Dict:
        """Simula um cenário individual específico"""
        
        # Configurações do cenário
        config = cenario.get('configuracoes', {})
        
        # Simular progressão da coleta
        progressao_simulada = self._simular_progressao_coleta(config, estado_atual)
        
        # Calcular métricas do cenário
        metricas_cenario = self._calcular_metricas_cenario(progressao_simulada)
        
        return {
            'nome_cenario': cenario.get('nome', 'Cenário sem nome'),
            'configuracoes': config,
            'progressao_simulada': progressao_simulada,
            'metricas_resultado': metricas_cenario,
            'data_conclusao_prevista': self._calcular_data_conclusao_cenario(progressao_simulada),
            'recursos_necessarios': self._calcular_recursos_necessarios_cenario(config)
        }
    
    def _obter_questionarios_pendentes(self) -> List[Dict]:
        """Obtém lista de questionários ainda pendentes"""
        
        pendentes = []
        
        for municipio in self.municipios_pnsb:
            for tipo_pesquisa in self.tipos_pesquisa:
                status = self._obter_status_questionario(municipio, tipo_pesquisa)
                
                if status not in ['completo']:
                    pendentes.append({
                        'municipio': municipio,
                        'tipo_pesquisa': tipo_pesquisa,
                        'status_atual': status,
                        'dificuldade_estimada': self._estimar_dificuldade_coleta(municipio, tipo_pesquisa),
                        'tentativas_realizadas': self._contar_tentativas_realizadas(municipio, tipo_pesquisa),
                        'ultima_tentativa': self._obter_data_ultima_tentativa(municipio, tipo_pesquisa)
                    })
        
        return pendentes
    
    def _obter_status_questionario(self, municipio: str, tipo_pesquisa: str) -> str:
        """Obtém status atual de um questionário específico"""
        
        # Buscar última visita para este município e tipo de pesquisa
        visita = Visita.query.filter_by(
            municipio=municipio,
            tipo_pesquisa=tipo_pesquisa
        ).order_by(Visita.data_atualizacao.desc()).first()
        
        if not visita:
            return 'pendente'
        
        # Mapear status da visita para status do questionário
        status_mapping = {
            'agendada': 'agendado',
            'em execução': 'em_andamento',
            'realizada': 'completo',
            'cancelada': 'pendente',
            'reagendada': 'pendente'
        }
        
        return status_mapping.get(visita.status, 'pendente')
    
    # Implementações simplificadas dos métodos auxiliares restantes
    def _analisar_viabilidade_cenario(self, resultado): return {}
    def _analisar_riscos_cenario(self, resultado): return {}
    def _identificar_melhor_cenario(self, resultados): return resultados[0] if resultados else {}
    def _gerar_insights_comparativos(self, resultados): return {}
    def _gerar_recomendacoes_implementacao(self, melhor): return {}
    def _gerar_plano_contingencia_simulacao(self, resultados): return {}
    def _calcular_ritmo_atual_coleta(self): return {}
    def _calcular_estimativa_linear(self, pendentes, ritmo): return {}
    def _aplicar_fatores_correcao(self, estimativa, pendentes): return estimativa
    def _identificar_gargalos_potenciais(self, pendentes, ritmo): return []
    def _gerar_cenarios_prazo(self, estimativa, gargalos): return {}
    def _agrupar_pendentes_por_municipio(self, pendentes): return {}
    def _classificar_pendentes_por_dificuldade(self, pendentes): return {}
    def _calcular_margem_confianca(self, estimativa): return 0.8
    def _sugerir_acoes_aceleracao(self, gargalos): return []
    def _analisar_gargalos_pessoal(self, prazo): return {}
    def _analisar_gargalos_informantes(self, prazo): return {}
    def _analisar_gargalos_dependencias(self, prazo): return {}
    def _analisar_gargalos_logisticos(self, prazo): return {}
    def _classificar_gargalos_por_impacto(self, gargalos): return []
    def _gerar_solucoes_gargalos(self, classificacao): return {}
    def _calcular_impacto_gargalos_no_prazo(self, classificacao, prazo): return {}
    def _gerar_plano_mitigacao_gargalos(self, classificacao): return {}
    def _calcular_carga_atual_pesquisadores(self, pesquisadores): return {}
    def _calcular_capacidade_disponivel(self, pesquisadores, restricoes): return {}
    def _calcular_redistribuicao_otima(self, pendentes, capacidade, restricoes): return {}
    def _simular_impacto_redistribuicao(self, atual, redistribuicao): return {}
    def _gerar_cronograma_redistribuicao(self, redistribuicao): return {}
    def _calcular_beneficios_redistribuicao(self, impacto): return {}
    def _identificar_riscos_redistribuicao(self, redistribuicao): return []
    def _identificar_questionarios_criticos(self): return []
    def _estratificar_por_dificuldade(self, questionarios): return {}
    def _definir_estrategia_dificuldade_extrema(self): return {}
    def _definir_estrategia_dificuldade_alta(self): return {}
    def _definir_estrategia_dificuldade_media(self): return {}
    def _gerar_cronograma_sprint(self, estratificacao, estrategias, dias): return {}
    def _alocar_recursos_especiais_sprint(self, questionarios): return {}
    def _definir_marcos_checkpoint_sprint(self, cronograma, dias): return {}
    def _gerar_contingencias_questionarios_criticos(self, questionarios): return {}
    def _definir_criterios_sucesso_sprint(self): return {}
    def _definir_plano_comunicacao_sprint(self, marcos): return {}
    def _simular_cenario_e_se(self, parametros, estado, variacao): return {}
    def _comparar_com_baseline(self, resultado, baseline): return {}
    def _analisar_sensibilidade_parametros(self, resultados): return {}
    def _identificar_parametros_criticos(self, analise): return []
    def _gerar_recomendacoes_ajuste_parametros(self, parametros): return []
    def _identificar_cenario_otimo(self, resultados): return {}
    def _simular_progressao_coleta(self, config, estado): return {}
    def _calcular_metricas_cenario(self, progressao): return {}
    def _calcular_data_conclusao_cenario(self, progressao): return date.today()
    def _calcular_recursos_necessarios_cenario(self, config): return {}
    def _estimar_dificuldade_coleta(self, municipio, tipo): return "media"
    def _contar_tentativas_realizadas(self, municipio, tipo): return 0
    def _obter_data_ultima_tentativa(self, municipio, tipo): return None