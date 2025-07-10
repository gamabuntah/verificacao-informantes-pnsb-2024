"""
Assistente de Abordagem e Persuasão - PNSB
Scripts personalizados e estratégias para abordar informantes
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from ..models.agendamento import Visita
from ..models.contatos import Contato
from .perfil_informante import PerfilInformante
import json
from collections import defaultdict

class AssistenteAbordagem:
    """Assistente inteligente para abordagem e persuasão de informantes"""
    
    def __init__(self):
        self.perfil_service = PerfilInformante()
        
        # Banco de argumentos eficazes por categoria
        self.argumentos_persuasao = {
            'importancia_pesquisa': [
                "Esta pesquisa é fundamental para melhorar o saneamento em todo o Brasil",
                "Os dados coletados vão ajudar a direcionar investimentos para sua região",
                "É uma oportunidade única de contribuir para políticas públicas de saneamento",
                "Seu município foi selecionado por sua relevância para o estudo nacional"
            ],
            'beneficios_municipio': [
                "Os resultados vão mostrar as necessidades específicas do seu município",
                "Pode ajudar a conseguir mais recursos federais para saneamento",
                "Vai gerar dados oficiais que podem embasar projetos locais",
                "É uma forma de dar visibilidade às demandas da região"
            ],
            'praticidade': [
                "O processo é rápido, leva em média 30-45 minutos",
                "Podemos agendar no horário que for melhor para você",
                "Todas as informações são tratadas com total confidencialidade",
                "Não há custos ou obrigações adicionais para o município"
            ],
            'autoridade': [
                "Esta pesquisa é conduzida pelo IBGE, órgão oficial do governo federal",
                "É parte do Sistema Nacional de Informações sobre Saneamento",
                "Os dados são utilizados pelo Ministério do Desenvolvimento Regional",
                "É uma pesquisa oficial, prevista em lei federal"
            ],
            'urgencia': [
                "O prazo para coleta está se encerrando",
                "Outros municípios da região já participaram",
                "É importante não perder esta oportunidade de participação",
                "A próxima pesquisa só acontecerá daqui a alguns anos"
            ]
        }
        
        # Scripts por tipo de abordagem
        self.scripts_abordagem = self._carregar_scripts_abordagem()
        
        # Técnicas de contorno para objeções
        self.tecnicas_contorno = self._carregar_tecnicas_contorno()
    
    def gerar_script_personalizado(self, informante_nome: str, municipio: str, 
                                 contexto: Dict = None) -> Dict:
        """Gera script personalizado para abordar um informante específico"""
        
        # Obter perfil do informante
        perfil = self.perfil_service.obter_perfil_completo(informante_nome, municipio)
        
        # Analisar histórico de abordagens
        historico_abordagens = perfil.get('historico_visitas', [])
        dificuldades_conhecidas = perfil.get('dificuldades_conhecidas', [])
        
        # Determinar tipo de abordagem baseado no perfil
        tipo_abordagem = self._determinar_tipo_abordagem(perfil, contexto)
        
        # Selecionar argumentos mais eficazes
        argumentos_selecionados = self._selecionar_argumentos_eficazes(
            perfil, dificuldades_conhecidas, contexto
        )
        
        # Gerar script estruturado
        script_estruturado = self._gerar_script_estruturado(
            tipo_abordagem, argumentos_selecionados, perfil, contexto
        )
        
        # Identificar pontos de atenção
        pontos_atencao = self._identificar_pontos_atencao_abordagem(
            perfil, dificuldades_conhecidas
        )
        
        # Preparar materiais de apoio
        materiais_apoio = self._definir_materiais_apoio(perfil, tipo_abordagem)
        
        return {
            'informante': informante_nome,
            'municipio': municipio,
            'tipo_abordagem_recomendado': tipo_abordagem,
            'script_estruturado': script_estruturado,
            'argumentos_personalizados': argumentos_selecionados,
            'pontos_atencao': pontos_atencao,
            'materiais_apoio': materiais_apoio,
            'tempo_estimado_abordagem': self._estimar_tempo_abordagem(tipo_abordagem, perfil),
            'probabilidade_sucesso': self._estimar_probabilidade_sucesso(perfil, tipo_abordagem),
            'planos_contingencia': self._gerar_planos_contingencia(dificuldades_conhecidas),
            'timing_recomendado': self._recomendar_timing(perfil),
            'followup_sugerido': self._definir_followup(perfil, tipo_abordagem)
        }
    
    def obter_argumentos_por_objecao(self, tipo_objecao: str) -> Dict:
        """Obtém argumentos específicos para diferentes tipos de objeção"""
        
        argumentos_por_objecao = {
            'falta_tempo': {
                'contornos': [
                    "Entendo que o tempo é precioso. Podemos agendar para o horário que for melhor",
                    "O processo é bem rápido, leva cerca de 30 minutos apenas",
                    "Posso ir até você, no local e horário de sua preferência",
                    "É um investimento pequeno de tempo que pode trazer grandes benefícios para o município"
                ],
                'argumentos_apoio': self.argumentos_persuasao['praticidade'],
                'tecnica_recomendada': 'reduzir_barreira_tempo'
            },
            'nao_conhece_pesquisa': {
                'contornos': [
                    "É normal não conhecer, esta é uma pesquisa específica do IBGE sobre saneamento",
                    "Deixe-me explicar rapidamente a importância desta pesquisa",
                    "É uma oportunidade de participar de algo que vai beneficiar todo o país",
                    "Vou enviar um material explicativo antes da nossa conversa"
                ],
                'argumentos_apoio': self.argumentos_persuasao['importancia_pesquisa'],
                'tecnica_recomendada': 'educacao_e_esclarecimento'
            },
            'desconfianca': {
                'contornos': [
                    "Entendo a precaução, é sempre bom verificar. Esta pesquisa é oficial do IBGE",
                    "Posso fornecer todas as credenciais e documentação oficial",
                    "Você pode verificar no site do IBGE ou ligar para confirmar",
                    "Todas as informações são tratadas com total confidencialidade"
                ],
                'argumentos_apoio': self.argumentos_persuasao['autoridade'],
                'tecnica_recomendada': 'construcao_confianca'
            },
            'nao_autorizado': {
                'contornos': [
                    "Entendo, quem seria a pessoa mais adequada para me ajudar?",
                    "Posso agendar com a pessoa responsável?",
                    "Você poderia me orientar sobre o processo interno para autorização?",
                    "Posso enviar a solicitação formal via ofício?"
                ],
                'argumentos_apoio': self.argumentos_persuasao['autoridade'],
                'tecnica_recomendada': 'identificacao_decisor'
            },
            'momento_ruim': {
                'contornos': [
                    "Compreendo perfeitamente. Quando seria um momento melhor?",
                    "Podemos agendar para a próxima semana?",
                    "Qual período costuma ser mais tranquilo para vocês?",
                    "Posso ligar novamente em outro momento?"
                ],
                'argumentos_apoio': self.argumentos_persuasao['praticidade'],
                'tecnica_recomendada': 'flexibilidade_timing'
            },
            'ja_participou': {
                'contornos': [
                    "Que ótimo que já participaram! Esta é uma atualização importante",
                    "Os dados precisam ser atualizados periodicamente",
                    "Houve mudanças no município desde a última coleta?",
                    "É importante manter as informações sempre atualizadas"
                ],
                'argumentos_apoio': self.argumentos_persuasao['importancia_pesquisa'],
                'tecnica_recomendada': 'atualizacao_dados'
            }
        }
        
        return argumentos_por_objecao.get(tipo_objecao, {
            'contornos': ["Entendo sua posição. Posso esclarecer alguma dúvida específica?"],
            'argumentos_apoio': self.argumentos_persuasao['importancia_pesquisa'],
            'tecnica_recomendada': 'esclarecimento_geral'
        })
    
    def gerar_checklist_preparacao(self, informante_nome: str, municipio: str, 
                                 tipo_abordagem: str) -> Dict:
        """Gera checklist de preparação para a abordagem"""
        
        perfil = self.perfil_service.obter_perfil_completo(informante_nome, municipio)
        
        checklist_basico = [
            "Verificar credenciais e documentação oficial",
            "Preparar material explicativo sobre a pesquisa PNSB",
            "Confirmar dados de contato do informante",
            "Verificar melhor horário e canal de contato",
            "Preparar argumentos personalizados"
        ]
        
        checklist_personalizado = self._personalizar_checklist_preparacao(
            checklist_basico, perfil, tipo_abordagem
        )
        
        materiais_necessarios = self._listar_materiais_necessarios(perfil, tipo_abordagem)
        
        informacoes_importantes = self._compilar_informacoes_importantes(perfil)
        
        return {
            'informante': informante_nome,
            'municipio': municipio,
            'tipo_abordagem': tipo_abordagem,
            'checklist_preparacao': checklist_personalizado,
            'materiais_necessarios': materiais_necessarios,
            'informacoes_importantes': informacoes_importantes,
            'tempo_preparacao_estimado': self._estimar_tempo_preparacao(tipo_abordagem, perfil),
            'pontos_criticos': self._identificar_pontos_criticos_preparacao(perfil),
            'contatos_emergencia': self._definir_contatos_emergencia(municipio),
            'plano_b': self._definir_plano_b_abordagem(perfil)
        }
    
    def analisar_eficacia_abordagens(self, periodo_dias: int = 30) -> Dict:
        """Analisa eficácia das diferentes abordagens utilizadas"""
        
        from datetime import date
        data_inicio = date.today() - timedelta(days=periodo_dias)
        
        # Obter visitas do período
        visitas_periodo = Visita.query.filter(
            Visita.data >= data_inicio
        ).all()
        
        # Analisar por tipo de abordagem
        analise_por_tipo = defaultdict(lambda: {
            'tentativas': 0, 
            'sucessos': 0, 
            'taxa_sucesso': 0,
            'tempo_medio': 0
        })
        
        # Analisar por argumentos utilizados
        analise_argumentos = defaultdict(lambda: {
            'utilizacoes': 0,
            'sucessos': 0,
            'taxa_sucesso': 0
        })
        
        # Analisar por dificuldades encontradas
        dificuldades_frequentes = defaultdict(int)
        
        for visita in visitas_periodo:
            # Análise simplificada baseada no status da visita
            sucesso = 1 if visita.status == 'realizada' else 0
            
            # Simular tipo de abordagem baseado no município e informante
            tipo_abordagem = self._inferir_tipo_abordagem_historico(visita)
            
            analise_por_tipo[tipo_abordagem]['tentativas'] += 1
            analise_por_tipo[tipo_abordagem]['sucessos'] += sucesso
            
            if visita.observacoes:
                # Analisar dificuldades nas observações
                dificuldades_encontradas = self._extrair_dificuldades_observacoes(visita.observacoes)
                for dificuldade in dificuldades_encontradas:
                    dificuldades_frequentes[dificuldade] += 1
        
        # Calcular taxas de sucesso
        for tipo, dados in analise_por_tipo.items():
            if dados['tentativas'] > 0:
                dados['taxa_sucesso'] = round((dados['sucessos'] / dados['tentativas']) * 100, 1)
        
        # Identificar melhores práticas
        melhores_praticas = self._identificar_melhores_praticas(analise_por_tipo, analise_argumentos)
        
        # Gerar recomendações de melhoria
        recomendacoes_melhoria = self._gerar_recomendacoes_melhoria_abordagem(
            analise_por_tipo, dificuldades_frequentes
        )
        
        return {
            'periodo_analise': {
                'data_inicio': data_inicio.isoformat(),
                'data_fim': date.today().isoformat(),
                'total_visitas_analisadas': len(visitas_periodo)
            },
            'analise_por_tipo_abordagem': dict(analise_por_tipo),
            'analise_argumentos': dict(analise_argumentos),
            'dificuldades_mais_frequentes': dict(dificuldades_frequentes),
            'melhores_praticas_identificadas': melhores_praticas,
            'recomendacoes_melhoria': recomendacoes_melhoria,
            'estatisticas_gerais': {
                'taxa_sucesso_geral': round(sum(v.status == 'realizada' for v in visitas_periodo) / len(visitas_periodo) * 100, 1) if visitas_periodo else 0,
                'tipo_abordagem_mais_eficaz': max(analise_por_tipo.items(), key=lambda x: x[1]['taxa_sucesso'])[0] if analise_por_tipo else None,
                'principal_dificuldade': max(dificuldades_frequentes.items(), key=lambda x: x[1])[0] if dificuldades_frequentes else None
            }
        }
    
    # Métodos auxiliares
    
    def _carregar_scripts_abordagem(self) -> Dict:
        """Carrega scripts estruturados por tipo de abordagem"""
        return {
            'telefonica_inicial': {
                'abertura': "Bom dia/Boa tarde, meu nome é [NOME], sou pesquisador do IBGE. Estou ligando sobre a Pesquisa Nacional de Saneamento Básico.",
                'apresentacao': "O IBGE foi designado para coletar informações sobre saneamento em municípios selecionados, incluindo {municipio}.",
                'objetivo': "Precisamos de alguns dados sobre manejo de resíduos sólidos e águas pluviais do município.",
                'tempo': "O processo é rápido, leva cerca de 30-45 minutos.",
                'fechamento': "Podemos agendar um horário que seja conveniente para você?"
            },
            'presencial_formal': {
                'abertura': "Bom dia/Boa tarde, sou [NOME], pesquisador credenciado do IBGE.",
                'apresentacao': "Estou aqui para conduzir a Pesquisa Nacional de Saneamento Básico em {municipio}.",
                'credencial': "Aqui estão minhas credenciais oficiais e documentação da pesquisa.",
                'objetivo': "Precisamos coletar dados oficiais sobre o sistema de saneamento do município.",
                'tempo': "O questionário leva aproximadamente 30-45 minutos para ser preenchido.",
                'fechamento': "Quando seria o melhor momento para realizarmos a entrevista?"
            },
            'email_formal': {
                'assunto': "IBGE - Pesquisa Nacional de Saneamento Básico - {municipio}",
                'abertura': "Prezado(a) [NOME],",
                'apresentacao': "O Instituto Brasileiro de Geografia e Estatística (IBGE) está conduzindo a Pesquisa Nacional de Saneamento Básico 2024.",
                'objetivo': "Seu município foi selecionado para participar desta importante pesquisa sobre manejo de resíduos sólidos e águas pluviais.",
                'tempo': "O processo é simples e leva aproximadamente 30-45 minutos.",
                'fechamento': "Gostaria de agendar uma data e horário convenientes para a coleta dos dados."
            }
        }
    
    def _carregar_tecnicas_contorno(self) -> Dict:
        """Carrega técnicas para contornar objeções"""
        return {
            'reduzir_barreira_tempo': {
                'tecnica': 'Fracionamento',
                'aplicacao': 'Dividir o tempo em pequenos blocos para parecer menor',
                'exemplo': 'São apenas 3 etapas de 10 minutos cada'
            },
            'construcao_confianca': {
                'tecnica': 'Prova social e autoridade',
                'aplicacao': 'Mostrar credenciais e mencionar outros participantes',
                'exemplo': 'Outros municípios da região já participaram, como Itajaí e Navegantes'
            },
            'flexibilidade_timing': {
                'tecnica': 'Acomodação total',
                'aplicacao': 'Mostrar flexibilidade extrema para acomodar o informante',
                'exemplo': 'Posso ir no horário, local e dia que for melhor para você'
            }
        }
    
    def _determinar_tipo_abordagem(self, perfil: Dict, contexto: Dict = None) -> str:
        """Determina o melhor tipo de abordagem baseado no perfil"""
        
        # Analisar preferências conhecidas
        preferencias = perfil.get('preferencias_contato', {})
        canal_preferido = preferencias.get('canal_preferido', 'telefone')
        
        # Analisar histórico de sucesso
        historico = perfil.get('historico_visitas', [])
        
        # Considerar contexto atual
        if contexto and contexto.get('urgencia') == 'alta':
            return 'telefonica_urgente'
        
        # Mapear canal preferido para tipo de abordagem
        mapping_abordagem = {
            'telefone': 'telefonica_inicial',
            'email': 'email_formal',
            'presencial': 'presencial_formal',
            'whatsapp': 'whatsapp_informal'
        }
        
        return mapping_abordagem.get(canal_preferido, 'telefonica_inicial')
    
    def _selecionar_argumentos_eficazes(self, perfil: Dict, dificuldades: List, 
                                      contexto: Dict = None) -> List[str]:
        """Seleciona argumentos mais eficazes baseado no perfil e contexto"""
        
        argumentos_selecionados = []
        
        # Sempre incluir importância da pesquisa
        argumentos_selecionados.extend(self.argumentos_persuasao['importancia_pesquisa'][:2])
        
        # Adicionar argumentos específicos baseados nas dificuldades conhecidas
        categorias_dificuldades = [d.get('tipo', '') for d in dificuldades]
        
        if 'tempo' in str(categorias_dificuldades):
            argumentos_selecionados.extend(self.argumentos_persuasao['praticidade'][:2])
        
        if 'confianca' in str(categorias_dificuldades):
            argumentos_selecionados.extend(self.argumentos_persuasao['autoridade'][:2])
        
        # Adicionar argumentos de benefício local
        argumentos_selecionados.extend(self.argumentos_persuasao['beneficios_municipio'][:1])
        
        return argumentos_selecionados[:6]  # Máximo 6 argumentos
    
    def _gerar_script_estruturado(self, tipo_abordagem: str, argumentos: List, 
                                perfil: Dict, contexto: Dict = None) -> Dict:
        """Gera script estruturado personalizado"""
        
        script_base = self.scripts_abordagem.get(tipo_abordagem, self.scripts_abordagem['telefonica_inicial'])
        
        # Personalizar com informações específicas
        script_personalizado = {}
        for fase, texto in script_base.items():
            script_personalizado[fase] = texto.format(
                municipio=perfil.get('dados_basicos', {}).get('municipio', ''),
                informante=perfil.get('dados_basicos', {}).get('nome', '')
            )
        
        # Adicionar seção de argumentos personalizados
        script_personalizado['argumentos_personalizados'] = argumentos
        
        # Adicionar fechamento específico
        script_personalizado['fechamento_personalizado'] = self._gerar_fechamento_personalizado(perfil, contexto)
        
        return script_personalizado
    
    # Implementações simplificadas dos métodos auxiliares restantes
    def _identificar_pontos_atencao_abordagem(self, perfil, dificuldades): return []
    def _definir_materiais_apoio(self, perfil, tipo): return []
    def _estimar_tempo_abordagem(self, tipo, perfil): return 30
    def _estimar_probabilidade_sucesso(self, perfil, tipo): return 70
    def _gerar_planos_contingencia(self, dificuldades): return []
    def _recomendar_timing(self, perfil): return {}
    def _definir_followup(self, perfil, tipo): return {}
    def _personalizar_checklist_preparacao(self, checklist, perfil, tipo): return checklist
    def _listar_materiais_necessarios(self, perfil, tipo): return []
    def _compilar_informacoes_importantes(self, perfil): return []
    def _estimar_tempo_preparacao(self, tipo, perfil): return 15
    def _identificar_pontos_criticos_preparacao(self, perfil): return []
    def _definir_contatos_emergencia(self, municipio): return []
    def _definir_plano_b_abordagem(self, perfil): return {}
    def _inferir_tipo_abordagem_historico(self, visita): return "telefonica_inicial"
    def _extrair_dificuldades_observacoes(self, observacoes): return []
    def _identificar_melhores_praticas(self, tipos, argumentos): return []
    def _gerar_recomendacoes_melhoria_abordagem(self, tipos, dificuldades): return []
    def _gerar_fechamento_personalizado(self, perfil, contexto): return ""