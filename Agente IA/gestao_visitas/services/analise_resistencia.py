"""
Sistema de Análise de Resistência e Soluções - PNSB
Mapeamento de objeções e estratégias de superação
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
from sqlalchemy import func, and_, or_
from ..models.agendamento import Visita
from ..models.contatos import Contato
from ..db import db
import json
from collections import defaultdict, Counter

class AnaliseResistencia:
    """Sistema de análise de resistência e estratégias de persuasão"""
    
    def __init__(self):
        # Categorias de objeções/resistências
        self.categorias_objecoes = {
            'tempo': {
                'palavras_chave': ['tempo', 'ocupado', 'corrido', 'agenda', 'compromisso', 'reunião'],
                'nivel_dificuldade': 'medio',
                'estrategias_superacao': [
                    'Oferecer flexibilidade total de horário',
                    'Enfatizar que leva apenas 30-45 minutos',
                    'Propor horário no início ou fim do expediente',
                    'Sugerir fazer por etapas/partes'
                ]
            },
            'autoridade': {
                'palavras_chave': ['autorização', 'superior', 'chefe', 'secretário', 'prefeito', 'permissão'],
                'nivel_dificuldade': 'alto',
                'estrategias_superacao': [
                    'Solicitar contato do responsável',
                    'Enviar ofício formal via protocolo',
                    'Explicar que é obrigatório por lei federal',
                    'Agendar reunião com tomador de decisão'
                ]
            },
            'desconfianca': {
                'palavras_chave': ['desconfiança', 'golpe', 'fraude', 'verificar', 'suspeito', 'estranho'],
                'nivel_dificuldade': 'alto',
                'estrategias_superacao': [
                    'Mostrar credenciais oficiais do IBGE',
                    'Fornecer telefone do IBGE para verificação',
                    'Enviar documentação oficial prévia',
                    'Explicar que dados no site do IBGE'
                ]
            },
            'conhecimento': {
                'palavras_chave': ['não sei', 'não conheço', 'não entendo', 'explicar', 'o que é'],
                'nivel_dificuldade': 'baixo',
                'estrategias_superacao': [
                    'Explicar importância da pesquisa',
                    'Enviar material explicativo',
                    'Dar exemplos práticos de benefícios',
                    'Usar linguagem simples e clara'
                ]
            },
            'interesse': {
                'palavras_chave': ['não vejo utilidade', 'não serve', 'perda de tempo', 'desnecessário'],
                'nivel_dificuldade': 'medio',
                'estrategias_superacao': [
                    'Destacar benefícios para o município',
                    'Explicar como dados podem gerar recursos',
                    'Mostrar resultados de outros municípios',
                    'Enfatizar caráter oficial e obrigatório'
                ]
            },
            'momento': {
                'palavras_chave': ['momento ruim', 'depois', 'mais tarde', 'outro dia', 'semana que vem'],
                'nivel_dificuldade': 'baixo',
                'estrategias_superacao': [
                    'Agendar para data específica futura',
                    'Perguntar quando seria melhor',
                    'Oferecer várias opções de datas',
                    'Ligar novamente conforme combinado'
                ]
            },
            'dados': {
                'palavras_chave': ['não tenho dados', 'informação', 'documento', 'sistema', 'arquivo'],
                'nivel_dificuldade': 'medio',
                'estrategias_superacao': [
                    'Listar documentos necessários',
                    'Agendar após reunir informações',
                    'Explicar que dados básicos são suficientes',
                    'Oferecer ajuda para localizar informações'
                ]
            }
        }
        
        # Banco de soluções por perfil socioeconômico/município
        self.estrategias_por_perfil = {
            'municipio_pequeno': {
                'abordagem': 'informal_proximidade',
                'argumentos_eficazes': [
                    'Importância para o município no cenário estadual',
                    'Oportunidade de mostrar a realidade local',
                    'Dados podem ajudar a conseguir recursos'
                ],
                'canais_preferidos': ['telefone', 'presencial']
            },
            'municipio_turistico': {
                'abordagem': 'impacto_ambiental',
                'argumentos_eficazes': [
                    'Relevância para sustentabilidade turística',
                    'Importância para imagem do município',
                    'Dados sobre saneamento afetam turismo'
                ],
                'canais_preferidos': ['email', 'whatsapp']
            },
            'alta_rotatividade': {
                'abordagem': 'urgencia_institucional',
                'argumentos_eficazes': [
                    'Pesquisa oficial obrigatória',
                    'Prazo determinado por lei federal',
                    'Responsabilidade institucional'
                ],
                'canais_preferidos': ['telefone', 'presencial']
            }
        }
    
    def mapear_objecoes_informante(self, informante_nome: str, municipio: str) -> Dict:
        """Mapeia objeções históricas de um informante específico"""
        
        # Obter histórico de tentativas
        contato = Contato.query.filter_by(
            nome=informante_nome,
            municipio=municipio
        ).first()
        
        if not contato:
            return {'erro': 'Informante não encontrado'}
        
        # Analisar histórico de abordagens
        objecoes_identificadas = []
        padroes_resistencia = defaultdict(int)
        
        if contato.historico_abordagens:
            historico = json.loads(contato.historico_abordagens)
            
            for tentativa in historico:
                if tentativa.get('resultado') in ['recusou', 'adiou', 'sem_resposta']:
                    # Analisar observações para identificar objeções
                    observacoes = tentativa.get('observacoes', '').lower()
                    objecoes_tentativa = self._identificar_objecoes_texto(observacoes)
                    
                    for objecao in objecoes_tentativa:
                        padroes_resistencia[objecao['categoria']] += 1
                        objecoes_identificadas.append({
                            'data': tentativa.get('timestamp'),
                            'categoria': objecao['categoria'],
                            'objecao_especifica': objecao['texto_identificado'],
                            'estrategias_testadas': tentativa.get('estrategias_utilizadas', []),
                            'resultado': tentativa.get('resultado')
                        })
        
        # Identificar padrão principal de resistência
        padrao_principal = max(padroes_resistencia.items(), key=lambda x: x[1])[0] if padroes_resistencia else None
        
        # Gerar estratégias personalizadas
        estrategias_personalizadas = self._gerar_estrategias_personalizadas(
            padrao_principal, padroes_resistencia, municipio
        )
        
        return {
            'informante': informante_nome,
            'municipio': municipio,
            'objecoes_historicas': objecoes_identificadas,
            'padroes_resistencia': dict(padroes_resistencia),
            'padrao_principal': padrao_principal,
            'nivel_resistencia_geral': self._calcular_nivel_resistencia(padroes_resistencia),
            'estrategias_personalizadas': estrategias_personalizadas,
            'proxima_abordagem_recomendada': self._recomendar_proxima_abordagem(
                padrao_principal, estrategias_personalizadas
            )
        }
    
    def analisar_padroes_municipio(self, municipio: str) -> Dict:
        """Analisa padrões de resistência em um município específico"""
        
        # Obter todos os contatos do município
        contatos_municipio = Contato.query.filter_by(municipio=municipio).all()
        
        objecoes_municipio = defaultdict(int)
        informantes_problematicos = []
        fatores_influencia = []
        
        for contato in contatos_municipio:
            if contato.historico_abordagens:
                historico = json.loads(contato.historico_abordagens)
                
                tentativas_sem_sucesso = 0
                for tentativa in historico:
                    if tentativa.get('resultado') in ['recusou', 'adiou', 'sem_resposta']:
                        tentativas_sem_sucesso += 1
                        
                        # Identificar objeções
                        observacoes = tentativa.get('observacoes', '').lower()
                        objecoes_tentativa = self._identificar_objecoes_texto(observacoes)
                        
                        for objecao in objecoes_tentativa:
                            objecoes_municipio[objecao['categoria']] += 1
                
                # Identificar informantes problemáticos
                if tentativas_sem_sucesso >= 3:
                    informantes_problematicos.append({
                        'nome': contato.nome,
                        'tentativas_sem_sucesso': tentativas_sem_sucesso,
                        'principal_objecao': self._identificar_principal_objecao_contato(contato)
                    })
        
        # Analisar fatores de influência específicos do município
        fatores_influencia = self._analisar_fatores_influencia_municipio(municipio, objecoes_municipio)
        
        # Gerar recomendações específicas para o município
        recomendacoes_municipio = self._gerar_recomendacoes_municipio(
            municipio, objecoes_municipio, fatores_influencia
        )
        
        return {
            'municipio': municipio,
            'objecoes_mais_frequentes': dict(sorted(objecoes_municipio.items(), key=lambda x: x[1], reverse=True)),
            'total_informantes_analisados': len(contatos_municipio),
            'informantes_problematicos': informantes_problematicos,
            'fatores_influencia_local': fatores_influencia,
            'nivel_resistencia_municipal': self._calcular_nivel_resistencia_municipal(objecoes_municipio, len(contatos_municipio)),
            'recomendacoes_estrategicas': recomendacoes_municipio,
            'perfil_municipio': self._classificar_perfil_municipio(municipio, objecoes_municipio)
        }
    
    def gerar_banco_solucoes(self, filtros: Dict = None) -> Dict:
        """Gera banco de soluções baseado em sucessos históricos"""
        
        # Obter tentativas bem-sucedidas
        tentativas_sucesso = self._obter_tentativas_sucesso(filtros)
        
        # Agrupar soluções por categoria de objeção
        solucoes_por_categoria = defaultdict(list)
        
        for tentativa in tentativas_sucesso:
            categoria_objecao = tentativa.get('objecao_superada')
            estrategia_usada = tentativa.get('estrategia_eficaz')
            
            if categoria_objecao and estrategia_usada:
                solucoes_por_categoria[categoria_objecao].append({
                    'estrategia': estrategia_usada,
                    'contexto': tentativa.get('contexto', ''),
                    'municipio': tentativa.get('municipio'),
                    'eficacia': tentativa.get('taxa_sucesso', 100),
                    'tempo_para_sucesso': tentativa.get('tempo_conversao_horas', 24)
                })
        
        # Ordenar soluções por eficácia
        for categoria in solucoes_por_categoria:
            solucoes_por_categoria[categoria].sort(key=lambda x: x['eficacia'], reverse=True)
        
        # Identificar melhores práticas gerais
        melhores_praticas = self._identificar_melhores_praticas_gerais(solucoes_por_categoria)
        
        return {
            'timestamp_geracao': datetime.now().isoformat(),
            'solucoes_por_categoria': dict(solucoes_por_categoria),
            'melhores_praticas_gerais': melhores_praticas,
            'total_casos_analisados': len(tentativas_sucesso),
            'categorias_com_solucoes': len(solucoes_por_categoria),
            'recomendacoes_aplicacao': self._gerar_recomendacoes_aplicacao_solucoes(solucoes_por_categoria)
        }
    
    def calcular_indicadores_persuasao(self, periodo_dias: int = 30) -> Dict:
        """Calcula indicadores de eficácia por tipo de abordagem"""
        
        data_inicio = date.today() - timedelta(days=periodo_dias)
        
        # Obter visitas do período
        visitas_periodo = Visita.query.filter(
            Visita.data >= data_inicio
        ).all()
        
        # Analisar por tipo de abordagem
        indicadores_abordagem = defaultdict(lambda: {
            'tentativas': 0,
            'sucessos': 0,
            'taxa_conversao': 0,
            'tempo_medio_conversao': 0,
            'objecoes_mais_comuns': Counter()
        })
        
        # Analisar por estratégia utilizada
        indicadores_estrategia = defaultdict(lambda: {
            'utilizacoes': 0,
            'sucessos': 0,
            'eficacia': 0
        })
        
        for visita in visitas_periodo:
            # Simular tipo de abordagem baseado no histórico
            tipo_abordagem = self._inferir_tipo_abordagem(visita)
            sucesso = 1 if visita.status == 'realizada' else 0
            
            indicadores_abordagem[tipo_abordagem]['tentativas'] += 1
            indicadores_abordagem[tipo_abordagem]['sucessos'] += sucesso
            
            # Analisar objeções se houver observações
            if visita.observacoes and not sucesso:
                objecoes = self._identificar_objecoes_texto(visita.observacoes.lower())
                for objecao in objecoes:
                    indicadores_abordagem[tipo_abordagem]['objecoes_mais_comuns'][objecao['categoria']] += 1
        
        # Calcular taxas de conversão
        for tipo, dados in indicadores_abordagem.items():
            if dados['tentativas'] > 0:
                dados['taxa_conversao'] = round((dados['sucessos'] / dados['tentativas']) * 100, 1)
        
        # Identificar abordagem mais eficaz
        abordagem_mais_eficaz = max(
            indicadores_abordagem.items(), 
            key=lambda x: x[1]['taxa_conversao']
        )[0] if indicadores_abordagem else None
        
        # Gerar recomendações de otimização
        recomendacoes_otimizacao = self._gerar_recomendacoes_otimizacao_persuasao(
            indicadores_abordagem, indicadores_estrategia
        )
        
        return {
            'periodo_analise': {
                'data_inicio': data_inicio.isoformat(),
                'data_fim': date.today().isoformat(),
                'total_tentativas': len(visitas_periodo)
            },
            'indicadores_por_abordagem': dict(indicadores_abordagem),
            'indicadores_por_estrategia': dict(indicadores_estrategia),
            'abordagem_mais_eficaz': abordagem_mais_eficaz,
            'taxa_conversao_geral': round(sum(v.status == 'realizada' for v in visitas_periodo) / len(visitas_periodo) * 100, 1) if visitas_periodo else 0,
            'recomendacoes_otimizacao': recomendacoes_otimizacao,
            'tendencias_identificadas': self._identificar_tendencias_persuasao(indicadores_abordagem)
        }
    
    def sugerir_estrategia_diferenciada(self, municipio: str, perfil_socioeconomico: str = None) -> Dict:
        """Sugere estratégia diferenciada baseada no perfil do município"""
        
        # Classificar perfil do município se não fornecido
        if not perfil_socioeconomico:
            perfil_socioeconomico = self._classificar_perfil_socioeconomico_municipio(municipio)
        
        # Obter estratégia base para o perfil
        estrategia_base = self.estrategias_por_perfil.get(perfil_socioeconomico, {})
        
        # Analisar padrões específicos do município
        padroes_municipio = self.analisar_padroes_municipio(municipio)
        
        # Personalizar estratégia baseada nos padrões locais
        estrategia_personalizada = self._personalizar_estrategia_padroes_locais(
            estrategia_base, padroes_municipio
        )
        
        # Gerar plano de ação específico
        plano_acao = self._gerar_plano_acao_municipio(municipio, estrategia_personalizada)
        
        return {
            'municipio': municipio,
            'perfil_identificado': perfil_socioeconomico,
            'estrategia_base': estrategia_base,
            'padroes_locais_considerados': padroes_municipio.get('objecoes_mais_frequentes', {}),
            'estrategia_personalizada': estrategia_personalizada,
            'plano_acao_especifico': plano_acao,
            'indicadores_monitoramento': self._definir_indicadores_monitoramento(estrategia_personalizada)
        }
    
    # Métodos auxiliares
    
    def _identificar_objecoes_texto(self, texto: str) -> List[Dict]:
        """Identifica objeções em um texto usando palavras-chave"""
        
        objecoes_encontradas = []
        
        for categoria, info in self.categorias_objecoes.items():
            palavras_chave = info['palavras_chave']
            
            for palavra in palavras_chave:
                if palavra in texto:
                    objecoes_encontradas.append({
                        'categoria': categoria,
                        'texto_identificado': palavra,
                        'nivel_dificuldade': info['nivel_dificuldade'],
                        'confianca': 0.8  # Simplificado
                    })
                    break  # Evitar duplicatas na mesma categoria
        
        return objecoes_encontradas
    
    def _calcular_nivel_resistencia(self, padroes_resistencia: Dict) -> str:
        """Calcula nível geral de resistência"""
        
        if not padroes_resistencia:
            return 'baixo'
        
        total_objecoes = sum(padroes_resistencia.values())
        objecoes_dificeis = sum(v for k, v in padroes_resistencia.items() 
                               if self.categorias_objecoes.get(k, {}).get('nivel_dificuldade') == 'alto')
        
        if objecoes_dificeis / total_objecoes > 0.5:
            return 'alto'
        elif total_objecoes > 5:
            return 'medio'
        else:
            return 'baixo'
    
    def _classificar_perfil_municipio(self, municipio: str, objecoes: Dict) -> str:
        """Classifica o perfil do município baseado em características"""
        
        # Mapeamento simplificado dos municípios PNSB
        perfis_municipios = {
            'Itajaí': 'municipio_turistico',
            'Balneário Camboriú': 'municipio_turistico',
            'Bombinhas': 'municipio_turistico',
            'Penha': 'municipio_turistico',
            'Piçarras': 'municipio_pequeno',
            'Barra Velha': 'municipio_pequeno',
            'Navegantes': 'alta_rotatividade',
            'Porto Belo': 'municipio_pequeno',
            'Itapema': 'municipio_turistico',
            'Camboriú': 'municipio_pequeno',
            'Tijucas': 'municipio_pequeno'
        }
        
        return perfis_municipios.get(municipio, 'municipio_pequeno')
    
    # Implementações simplificadas dos métodos auxiliares restantes
    def _gerar_estrategias_personalizadas(self, padrao, padroes, municipio): return []
    def _recomendar_proxima_abordagem(self, padrao, estrategias): return {}
    def _analisar_fatores_influencia_municipio(self, municipio, objecoes): return []
    def _gerar_recomendacoes_municipio(self, municipio, objecoes, fatores): return []
    def _calcular_nivel_resistencia_municipal(self, objecoes, total): return "medio"
    def _identificar_principal_objecao_contato(self, contato): return "tempo"
    def _obter_tentativas_sucesso(self, filtros): return []
    def _identificar_melhores_praticas_gerais(self, solucoes): return []
    def _gerar_recomendacoes_aplicacao_solucoes(self, solucoes): return []
    def _inferir_tipo_abordagem(self, visita): return "telefonica_inicial"
    def _gerar_recomendacoes_otimizacao_persuasao(self, abordagem, estrategia): return []
    def _identificar_tendencias_persuasao(self, indicadores): return []
    def _classificar_perfil_socioeconomico_municipio(self, municipio): return self._classificar_perfil_municipio(municipio, {})
    def _personalizar_estrategia_padroes_locais(self, base, padroes): return base
    def _gerar_plano_acao_municipio(self, municipio, estrategia): return {}
    def _definir_indicadores_monitoramento(self, estrategia): return []