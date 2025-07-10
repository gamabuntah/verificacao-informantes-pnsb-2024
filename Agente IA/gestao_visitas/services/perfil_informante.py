"""
Sistema de Perfil Inteligente do Informante - PNSB
Controle detalhado do histórico e características de cada informante
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import func, and_, or_
from ..models.agendamento import Visita
from ..models.contatos import Contato
from ..db import db
import json
from collections import defaultdict, Counter

class PerfilInformante:
    """Gerencia perfis inteligentes dos informantes para otimizar abordagens"""
    
    def __init__(self):
        self.historico_abordagens = {}
        self.perfis_comportamentais = {}
        self.preferencias_contato = {}
        self.dificuldades_mapeadas = {}
    
    def obter_perfil_completo(self, informante_nome: str, municipio: str) -> Dict:
        """Obtém perfil completo do informante com histórico e recomendações"""
        
        # Buscar dados básicos do informante
        contato = Contato.query.filter_by(
            nome=informante_nome,
            municipio=municipio
        ).first()
        
        if not contato:
            return self._criar_perfil_novo(informante_nome, municipio)
        
        # Histórico de visitas
        historico_visitas = Visita.query.filter_by(
            informante=informante_nome,
            municipio=municipio
        ).order_by(Visita.data_criacao.desc()).all()
        
        # Análise comportamental
        perfil_comportamental = self._analisar_comportamento(historico_visitas)
        
        # Preferências de contato
        preferencias = self._identificar_preferencias_contato(historico_visitas, contato)
        
        # Dificuldades conhecidas
        dificuldades = self._mapear_dificuldades(historico_visitas)
        
        # Contexto atual
        contexto_atual = self._obter_contexto_atual(contato, historico_visitas)
        
        # Estratégia recomendada
        estrategia_recomendada = self._gerar_estrategia_abordagem(
            perfil_comportamental, preferencias, dificuldades, contexto_atual
        )
        
        return {
            'dados_basicos': {
                'nome': informante_nome,
                'municipio': municipio,
                'telefone': contato.telefone,
                'email': contato.email,
                'endereco': contato.endereco,
                'tipo_pesquisa': contato.tipo_pesquisa,
                'cargo': contato.cargo,
                'orgao': contato.orgao
            },
            'historico_visitas': self._formatar_historico_visitas(historico_visitas),
            'perfil_comportamental': perfil_comportamental,
            'preferencias_contato': preferencias,
            'dificuldades_conhecidas': dificuldades,
            'contexto_atual': contexto_atual,
            'estrategia_recomendada': estrategia_recomendada,
            'metricas_sucesso': self._calcular_metricas_sucesso(historico_visitas),
            'ultima_atualizacao': datetime.now().isoformat()
        }
    
    def registrar_tentativa_abordagem(self, informante_nome: str, municipio: str, 
                                    dados_tentativa: Dict) -> Dict:
        """Registra uma tentativa de abordagem com detalhes"""
        
        contato = Contato.query.filter_by(
            nome=informante_nome,
            municipio=municipio
        ).first()
        
        if not contato:
            return {'success': False, 'error': 'Informante não encontrado'}
        
        # Criar registro da tentativa
        tentativa = {
            'timestamp': datetime.now().isoformat(),
            'tipo_contato': dados_tentativa.get('tipo_contato', 'presencial'),
            'resultado': dados_tentativa.get('resultado', 'sem_resposta'),
            'observacoes': dados_tentativa.get('observacoes', ''),
            'duracao_tentativa': dados_tentativa.get('duracao_minutos', 0),
            'horario_tentativa': dados_tentativa.get('horario'),
            'dia_semana': datetime.now().strftime('%A'),
            'reacao_informante': dados_tentativa.get('reacao_informante', ''),
            'obstaculos_encontrados': dados_tentativa.get('obstaculos', []),
            'proximos_passos': dados_tentativa.get('proximos_passos', '')
        }
        
        # Atualizar histórico do contato
        if not contato.historico_abordagens:
            contato.historico_abordagens = '[]'
        
        historico = json.loads(contato.historico_abordagens)
        historico.append(tentativa)
        contato.historico_abordagens = json.dumps(historico)
        
        # Atualizar última tentativa
        contato.data_ultima_tentativa = datetime.now()
        contato.status_ultimo_contato = dados_tentativa.get('resultado', 'sem_resposta')
        
        db.session.commit()
        
        # Atualizar perfil comportamental
        self._atualizar_perfil_comportamental(informante_nome, municipio, tentativa)
        
        return {
            'success': True,
            'tentativa_registrada': tentativa,
            'total_tentativas': len(historico),
            'recomendacoes_futuras': self._gerar_recomendacoes_proxima_tentativa(
                informante_nome, municipio, tentativa
            )
        }
    
    def obter_melhores_horarios(self, informante_nome: str, municipio: str) -> Dict:
        """Obtém os melhores horários para abordar o informante"""
        
        historico_visitas = Visita.query.filter_by(
            informante=informante_nome,
            municipio=municipio
        ).all()
        
        if not historico_visitas:
            return self._horarios_padrao()
        
        # Analisar padrões de sucesso por horário
        sucesso_por_horario = defaultdict(list)
        sucesso_por_dia_semana = defaultdict(list)
        
        for visita in historico_visitas:
            if visita.hora_inicio and visita.status:
                hora = visita.hora_inicio.hour
                sucesso = 1 if visita.status in ['realizada', 'agendada'] else 0
                sucesso_por_horario[hora].append(sucesso)
                
                if visita.data:
                    dia_semana = visita.data.strftime('%A')
                    sucesso_por_dia_semana[dia_semana].append(sucesso)
        
        # Calcular médias de sucesso
        melhores_horarios = []
        for hora, resultados in sucesso_por_horario.items():
            taxa_sucesso = sum(resultados) / len(resultados) * 100
            melhores_horarios.append({
                'hora': f"{hora:02d}:00",
                'taxa_sucesso': round(taxa_sucesso, 1),
                'tentativas': len(resultados)
            })
        
        melhores_horarios.sort(key=lambda x: x['taxa_sucesso'], reverse=True)
        
        melhores_dias = []
        for dia, resultados in sucesso_por_dia_semana.items():
            taxa_sucesso = sum(resultados) / len(resultados) * 100
            melhores_dias.append({
                'dia_semana': dia,
                'taxa_sucesso': round(taxa_sucesso, 1),
                'tentativas': len(resultados)
            })
        
        melhores_dias.sort(key=lambda x: x['taxa_sucesso'], reverse=True)
        
        return {
            'melhores_horarios': melhores_horarios[:3],
            'melhores_dias_semana': melhores_dias[:3],
            'recomendacao_principal': self._gerar_recomendacao_horario(
                melhores_horarios, melhores_dias
            ),
            'horarios_evitar': [h for h in melhores_horarios if h['taxa_sucesso'] < 30]
        }
    
    def identificar_barreiras_principais(self, informante_nome: str, municipio: str) -> Dict:
        """Identifica as principais barreiras para coleta com este informante"""
        
        contato = Contato.query.filter_by(
            nome=informante_nome,
            municipio=municipio
        ).first()
        
        if not contato or not contato.historico_abordagens:
            return {'barreiras': [], 'sem_historico': True}
        
        historico = json.loads(contato.historico_abordagens)
        
        # Analisar obstáculos recorrentes
        obstaculos_frequentes = Counter()
        tipos_problema = Counter()
        padroes_comportamento = []
        
        for tentativa in historico:
            if tentativa.get('resultado') in ['sem_resposta', 'recusou', 'adiou']:
                obstaculos = tentativa.get('obstaculos_encontrados', [])
                for obstaculo in obstaculos:
                    obstaculos_frequentes[obstaculo] += 1
                
                tipos_problema[tentativa.get('resultado')] += 1
                
                if tentativa.get('reacao_informante'):
                    padroes_comportamento.append(tentativa['reacao_informante'])
        
        # Classificar barreiras por categoria
        barreiras_categorizadas = {
            'disponibilidade': [],
            'resistencia': [],
            'tecnicas': [],
            'comunicacao': [],
            'outras': []
        }
        
        for obstaculo, frequencia in obstaculos_frequentes.most_common():
            categoria = self._categorizar_barreira(obstaculo)
            barreiras_categorizadas[categoria].append({
                'barreira': obstaculo,
                'frequencia': frequencia,
                'percentual': round((frequencia / len(historico)) * 100, 1)
            })
        
        return {
            'barreiras_por_categoria': barreiras_categorizadas,
            'problema_principal': tipos_problema.most_common(1)[0] if tipos_problema else None,
            'padroes_comportamento': list(set(padroes_comportamento)),
            'total_tentativas': len(historico),
            'taxa_sucesso_geral': self._calcular_taxa_sucesso_geral(historico),
            'recomendacoes_superacao': self._gerar_recomendacoes_superacao_barreiras(
                barreiras_categorizadas, tipos_problema
            )
        }
    
    def sugerir_estrategia_abordagem(self, informante_nome: str, municipio: str, 
                                   contexto_visita: Dict = None) -> Dict:
        """Sugere estratégia personalizada de abordagem"""
        
        perfil = self.obter_perfil_completo(informante_nome, municipio)
        barreiras = self.identificar_barreiras_principais(informante_nome, municipio)
        melhores_horarios = self.obter_melhores_horarios(informante_nome, municipio)
        
        # Construir estratégia baseada no perfil
        estrategia = {
            'abordagem_recomendada': self._definir_tipo_abordagem(perfil, barreiras),
            'timing_ideal': self._definir_timing_ideal(melhores_horarios, perfil),
            'argumentos_personalizados': self._gerar_argumentos_personalizados(perfil, barreiras),
            'preparacao_necessaria': self._definir_preparacao_necessaria(perfil, barreiras),
            'contingencias': self._definir_planos_contingencia(barreiras),
            'materiais_apoio': self._listar_materiais_apoio(perfil),
            'pontos_atencao': self._identificar_pontos_atencao(perfil, barreiras),
            'followup_recomendado': self._sugerir_followup(perfil)
        }
        
        # Personalizar para contexto específico
        if contexto_visita:
            estrategia = self._personalizar_para_contexto(estrategia, contexto_visita)
        
        return {
            'estrategia_personalizada': estrategia,
            'nivel_dificuldade': self._avaliar_nivel_dificuldade(perfil, barreiras),
            'tempo_estimado': self._estimar_tempo_necessario(perfil, barreiras),
            'probabilidade_sucesso': self._calcular_probabilidade_sucesso(perfil, barreiras),
            'alertas_especiais': self._gerar_alertas_especiais(perfil, barreiras)
        }
    
    # Métodos auxiliares
    
    def _criar_perfil_novo(self, nome: str, municipio: str) -> Dict:
        """Cria perfil básico para novo informante"""
        return {
            'dados_basicos': {
                'nome': nome,
                'municipio': municipio,
                'status': 'novo_informante'
            },
            'historico_visitas': [],
            'perfil_comportamental': self._perfil_comportamental_padrao(),
            'preferencias_contato': self._preferencias_padrao(),
            'dificuldades_conhecidas': [],
            'contexto_atual': {'status': 'primeiro_contato'},
            'estrategia_recomendada': self._estrategia_primeiro_contato(),
            'metricas_sucesso': {'tentativas': 0, 'sucessos': 0},
            'nova_criacao': True
        }
    
    def _analisar_comportamento(self, historico_visitas: List) -> Dict:
        """Analisa padrões comportamentais baseado no histórico"""
        if not historico_visitas:
            return self._perfil_comportamental_padrao()
        
        # Análise de responsividade
        total_visitas = len(historico_visitas)
        visitas_realizadas = len([v for v in historico_visitas if v.status == 'realizada'])
        visitas_canceladas = len([v for v in historico_visitas if v.status == 'cancelada'])
        
        return {
            'responsividade': 'alta' if visitas_realizadas/total_visitas > 0.8 else 'media' if visitas_realizadas/total_visitas > 0.5 else 'baixa',
            'pontualidade': self._avaliar_pontualidade(historico_visitas),
            'disponibilidade': self._avaliar_disponibilidade(historico_visitas),
            'cooperacao': self._avaliar_cooperacao(historico_visitas),
            'padroes_temporais': self._identificar_padroes_temporais(historico_visitas)
        }
    
    def _identificar_preferencias_contato(self, historico_visitas: List, contato: Any) -> Dict:
        """Identifica preferências de contato baseado no histórico"""
        return {
            'canal_preferido': self._identificar_canal_preferido(contato),
            'horario_preferido': self._identificar_horario_preferido(historico_visitas),
            'frequencia_contato': self._identificar_frequencia_ideal(historico_visitas),
            'tipo_abordagem': self._identificar_tipo_abordagem_eficaz(historico_visitas)
        }
    
    def _mapear_dificuldades(self, historico_visitas: List) -> List[Dict]:
        """Mapeia dificuldades recorrentes"""
        dificuldades = []
        
        for visita in historico_visitas:
            if visita.status in ['cancelada', 'reagendada'] and visita.observacoes:
                dificuldades.append({
                    'data': visita.data.strftime('%d/%m/%Y') if visita.data else 'N/A',
                    'tipo': self._classificar_dificuldade(visita.observacoes),
                    'descricao': visita.observacoes,
                    'impacto': self._avaliar_impacto_dificuldade(visita)
                })
        
        return dificuldades
    
    def _gerar_estrategia_abordagem(self, comportamental: Dict, preferencias: Dict, 
                                  dificuldades: List, contexto: Dict) -> Dict:
        """Gera estratégia personalizada de abordagem"""
        return {
            'tipo_abordagem': 'presencial' if comportamental.get('responsividade') == 'baixa' else 'telefonica',
            'momento_ideal': preferencias.get('horario_preferido', 'manha'),
            'argumentos_chave': self._selecionar_argumentos_eficazes(comportamental, dificuldades),
            'preparacao_necessaria': self._definir_preparacao(dificuldades),
            'tempo_estimado': self._estimar_tempo_abordagem(comportamental, dificuldades)
        }
    
    def _horarios_padrao(self) -> Dict:
        """Retorna horários padrão quando não há histórico"""
        return {
            'melhores_horarios': [
                {'hora': '09:00', 'taxa_sucesso': 75, 'tentativas': 0},
                {'hora': '14:00', 'taxa_sucesso': 70, 'tentativas': 0},
                {'hora': '10:00', 'taxa_sucesso': 65, 'tentativas': 0}
            ],
            'melhores_dias_semana': [
                {'dia_semana': 'Tuesday', 'taxa_sucesso': 75, 'tentativas': 0},
                {'dia_semana': 'Wednesday', 'taxa_sucesso': 70, 'tentativas': 0},
                {'dia_semana': 'Thursday', 'taxa_sucesso': 65, 'tentativas': 0}
            ],
            'recomendacao_principal': 'Tentar terça-feira às 9h (baseado em padrões gerais)',
            'horarios_evitar': []
        }
    
    def _perfil_comportamental_padrao(self) -> Dict:
        """Perfil comportamental padrão para novos informantes"""
        return {
            'responsividade': 'media',
            'pontualidade': 'desconhecida',
            'disponibilidade': 'comercial',
            'cooperacao': 'neutra',
            'padroes_temporais': 'indefinidos'
        }
    
    def _preferencias_padrao(self) -> Dict:
        """Preferências padrão para novos informantes"""
        return {
            'canal_preferido': 'telefone',
            'horario_preferido': 'comercial',
            'frequencia_contato': 'moderada',
            'tipo_abordagem': 'formal'
        }
    
    def _estrategia_primeiro_contato(self) -> Dict:
        """Estratégia padrão para primeiro contato"""
        return {
            'tipo_abordagem': 'telefonica',
            'momento_ideal': 'manha',
            'argumentos_chave': ['importancia_pesquisa', 'contribuicao_municipio', 'praticidade'],
            'preparacao_necessaria': ['apresentacao_clara', 'documentos_identificacao'],
            'tempo_estimado': 15
        }
    
    # Implementações simplificadas dos métodos auxiliares
    def _formatar_historico_visitas(self, visitas): return []
    def _obter_contexto_atual(self, contato, historico): return {}
    def _calcular_metricas_sucesso(self, historico): return {}
    def _atualizar_perfil_comportamental(self, nome, municipio, tentativa): pass
    def _gerar_recomendacoes_proxima_tentativa(self, nome, municipio, tentativa): return []
    def _gerar_recomendacao_horario(self, horarios, dias): return ""
    def _categorizar_barreira(self, obstaculo): return "outras"
    def _calcular_taxa_sucesso_geral(self, historico): return 0
    def _gerar_recomendacoes_superacao_barreiras(self, barreiras, tipos): return []
    def _definir_tipo_abordagem(self, perfil, barreiras): return {}
    def _definir_timing_ideal(self, horarios, perfil): return {}
    def _gerar_argumentos_personalizados(self, perfil, barreiras): return []
    def _definir_preparacao_necessaria(self, perfil, barreiras): return []
    def _definir_planos_contingencia(self, barreiras): return []
    def _listar_materiais_apoio(self, perfil): return []
    def _identificar_pontos_atencao(self, perfil, barreiras): return []
    def _sugerir_followup(self, perfil): return {}
    def _personalizar_para_contexto(self, estrategia, contexto): return estrategia
    def _avaliar_nivel_dificuldade(self, perfil, barreiras): return "medio"
    def _estimar_tempo_necessario(self, perfil, barreiras): return 30
    def _calcular_probabilidade_sucesso(self, perfil, barreiras): return 70
    def _gerar_alertas_especiais(self, perfil, barreiras): return []
    def _avaliar_pontualidade(self, historico): return "media"
    def _avaliar_disponibilidade(self, historico): return "comercial"
    def _avaliar_cooperacao(self, historico): return "neutra"
    def _identificar_padroes_temporais(self, historico): return {}
    def _identificar_canal_preferido(self, contato): return "telefone"
    def _identificar_horario_preferido(self, historico): return "manha"
    def _identificar_frequencia_ideal(self, historico): return "moderada"
    def _identificar_tipo_abordagem_eficaz(self, historico): return "formal"
    def _classificar_dificuldade(self, observacoes): return "disponibilidade"
    def _avaliar_impacto_dificuldade(self, visita): return "medio"
    def _selecionar_argumentos_eficazes(self, comportamental, dificuldades): return []
    def _definir_preparacao(self, dificuldades): return []
    def _estimar_tempo_abordagem(self, comportamental, dificuldades): return 30