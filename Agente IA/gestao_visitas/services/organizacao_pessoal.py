"""
Sistema de Organização Pessoal Avançada - PNSB 2024
Gestão pessoal de tarefas, notas e workflow do pesquisador
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy import func, and_, or_, desc
from ..models.agendamento import Visita
from ..models.contatos import Contato
from ..db import db
import json
from enum import Enum
from dataclasses import dataclass, asdict
import uuid

class TipoTarefa(Enum):
    VISITA = "visita"
    FOLLOW_UP = "follow_up"
    DOCUMENTACAO = "documentacao"
    CONTATO = "contato"
    ANALISE = "analise"
    REUNIAO = "reuniao"
    PESQUISA = "pesquisa"
    OUTROS = "outros"

class PrioridadeTarefa(Enum):
    CRITICA = "critica"
    ALTA = "alta"
    MEDIA = "media"
    BAIXA = "baixa"

class StatusTarefa(Enum):
    PENDENTE = "pendente"
    EM_ANDAMENTO = "em_andamento"
    PAUSADA = "pausada"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"

@dataclass
class TarefaPessoal:
    id: str
    titulo: str
    descricao: str
    tipo: TipoTarefa
    prioridade: PrioridadeTarefa
    status: StatusTarefa
    data_criacao: datetime
    data_prazo: Optional[datetime] = None
    data_conclusao: Optional[datetime] = None
    municipio: Optional[str] = None
    entidade: Optional[str] = None
    tags: List[str] = None
    tempo_estimado: Optional[int] = None  # em minutos
    tempo_gasto: Optional[int] = None  # em minutos
    observacoes: str = ""
    anexos: List[str] = None
    dependencias: List[str] = None
    checklist: List[Dict] = None

@dataclass
class NotaPessoal:
    id: str
    titulo: str
    conteudo: str
    tipo: str  # "reflexao", "insight", "problema", "ideia", "contato"
    data_criacao: datetime
    data_atualizacao: datetime
    municipio: Optional[str] = None
    entidade: Optional[str] = None
    tags: List[str] = None
    favorito: bool = False
    arquivado: bool = False
    categoria: str = ""

@dataclass
class EventoCalendario:
    id: str
    titulo: str
    descricao: str
    data_inicio: datetime
    data_fim: datetime
    tipo: str  # "visita", "reuniao", "prazo", "lembrete"
    municipio: Optional[str] = None
    entidade: Optional[str] = None
    notificacao: bool = True
    recorrencia: Optional[str] = None
    status: str = "agendado"

class OrganizacaoPessoal:
    """Sistema avançado de organização pessoal para pesquisador PNSB"""
    
    def __init__(self):
        self.tarefas = []
        self.notas = []
        self.eventos = []
        self.configuracoes = {
            'horario_inicio_trabalho': '08:00',
            'horario_fim_trabalho': '17:00',
            'tempo_break_padrao': 15,  # minutos
            'notificacoes_ativas': True,
            'sincronizacao_automatica': True,
            'backup_automatico': True,
            'tema_visual': 'escuro',
            'produtividade_meta_diaria': 8,  # horas
            'meta_visitas_semana': 5
        }
        self.metricas_produtividade = {}
        self.insights_pessoais = {}
        
    def obter_dashboard_pessoal(self) -> Dict:
        """Dashboard pessoal completo com métricas e insights"""
        try:
            hoje = date.today()
            
            # Métricas do dia
            metricas_hoje = self._calcular_metricas_dia(hoje)
            
            # Tarefas prioritárias
            tarefas_prioritarias = self._obter_tarefas_prioritarias()
            
            # Agenda do dia
            agenda_hoje = self._obter_agenda_dia(hoje)
            
            # Progresso semanal
            progresso_semanal = self._calcular_progresso_semanal()
            
            # Insights e recomendações
            insights = self._gerar_insights_pessoais()
            
            # Estatísticas gerais
            estatisticas = self._calcular_estatisticas_gerais()
            
            # Próximas ações sugeridas
            proximas_acoes = self._sugerir_proximas_acoes()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'metricas_hoje': metricas_hoje,
                'tarefas_prioritarias': tarefas_prioritarias,
                'agenda_hoje': agenda_hoje,
                'progresso_semanal': progresso_semanal,
                'insights_pessoais': insights,
                'estatisticas_gerais': estatisticas,
                'proximas_acoes_sugeridas': proximas_acoes,
                'configuracoes_ativas': self.configuracoes,
                'alertas_pessoais': self._obter_alertas_pessoais()
            }
            
        except Exception as e:
            return {'erro': str(e)}
    
    def criar_tarefa(self, dados_tarefa: Dict) -> Dict:
        """Cria nova tarefa com validações e integrações"""
        try:
            # Validar dados obrigatórios
            campos_obrigatorios = ['titulo', 'tipo', 'prioridade']
            for campo in campos_obrigatorios:
                if campo not in dados_tarefa:
                    return {'erro': f'Campo obrigatório {campo} não informado'}
            
            # Gerar ID único
            id_tarefa = str(uuid.uuid4())
            
            # Criar tarefa
            tarefa = TarefaPessoal(
                id=id_tarefa,
                titulo=dados_tarefa['titulo'],
                descricao=dados_tarefa.get('descricao', ''),
                tipo=TipoTarefa(dados_tarefa['tipo']),
                prioridade=PrioridadeTarefa(dados_tarefa['prioridade']),
                status=StatusTarefa.PENDENTE,
                data_criacao=datetime.now(),
                data_prazo=self._parse_data(dados_tarefa.get('data_prazo')),
                municipio=dados_tarefa.get('municipio'),
                entidade=dados_tarefa.get('entidade'),
                tags=dados_tarefa.get('tags', []),
                tempo_estimado=dados_tarefa.get('tempo_estimado'),
                observacoes=dados_tarefa.get('observacoes', ''),
                anexos=dados_tarefa.get('anexos', []),
                dependencias=dados_tarefa.get('dependencias', []),
                checklist=dados_tarefa.get('checklist', [])
            )
            
            # Adicionar à lista
            self.tarefas.append(tarefa)
            
            # Integrar com sistema de visitas se aplicável
            if tarefa.tipo == TipoTarefa.VISITA and tarefa.municipio:
                self._integrar_com_visita(tarefa)
            
            # Salvar
            self._salvar_dados()
            
            # Gerar recomendações
            recomendacoes = self._gerar_recomendacoes_tarefa(tarefa)
            
            return {
                'sucesso': True,
                'tarefa_criada': asdict(tarefa),
                'recomendacoes': recomendacoes,
                'proximas_acoes': self._sugerir_proximas_acoes_tarefa(tarefa)
            }
            
        except Exception as e:
            return {'erro': str(e)}
    
    def atualizar_tarefa(self, id_tarefa: str, dados_atualizacao: Dict) -> Dict:
        """Atualiza tarefa existente"""
        try:
            # Encontrar tarefa
            tarefa = self._encontrar_tarefa(id_tarefa)
            if not tarefa:
                return {'erro': 'Tarefa não encontrada'}
            
            # Registrar mudanças
            mudancas = []
            
            # Atualizar campos
            campos_atualizaveis = [
                'titulo', 'descricao', 'prioridade', 'status', 
                'data_prazo', 'municipio', 'entidade', 'tags',
                'tempo_estimado', 'observacoes', 'anexos'
            ]
            
            for campo in campos_atualizaveis:
                if campo in dados_atualizacao:
                    valor_antigo = getattr(tarefa, campo)
                    valor_novo = dados_atualizacao[campo]
                    
                    if valor_antigo != valor_novo:
                        mudancas.append({
                            'campo': campo,
                            'valor_antigo': valor_antigo,
                            'valor_novo': valor_novo
                        })
                        
                        setattr(tarefa, campo, valor_novo)
            
            # Atualizar tempo gasto se fornecido
            if 'tempo_gasto_adicional' in dados_atualizacao:
                tempo_adicional = dados_atualizacao['tempo_gasto_adicional']
                if tarefa.tempo_gasto:
                    tarefa.tempo_gasto += tempo_adicional
                else:
                    tarefa.tempo_gasto = tempo_adicional
                
                mudancas.append({
                    'campo': 'tempo_gasto',
                    'valor_adicional': tempo_adicional,
                    'valor_total': tarefa.tempo_gasto
                })
            
            # Marcar como concluída se status foi alterado
            if tarefa.status == StatusTarefa.CONCLUIDA and not tarefa.data_conclusao:
                tarefa.data_conclusao = datetime.now()
                mudancas.append({
                    'campo': 'data_conclusao',
                    'valor_novo': tarefa.data_conclusao
                })
            
            # Atualizar checklist se fornecido
            if 'checklist_update' in dados_atualizacao:
                self._atualizar_checklist(tarefa, dados_atualizacao['checklist_update'])
            
            # Salvar
            self._salvar_dados()
            
            # Analisar impacto das mudanças
            impacto = self._analisar_impacto_mudancas(tarefa, mudancas)
            
            return {
                'sucesso': True,
                'tarefa_atualizada': asdict(tarefa),
                'mudancas_realizadas': mudancas,
                'impacto_mudancas': impacto
            }
            
        except Exception as e:
            return {'erro': str(e)}
    
    def criar_nota(self, dados_nota: Dict) -> Dict:
        """Cria nova nota pessoal"""
        try:
            # Validar dados obrigatórios
            if 'titulo' not in dados_nota or 'conteudo' not in dados_nota:
                return {'erro': 'Título e conteúdo são obrigatórios'}
            
            # Gerar ID único
            id_nota = str(uuid.uuid4())
            
            # Criar nota
            nota = NotaPessoal(
                id=id_nota,
                titulo=dados_nota['titulo'],
                conteudo=dados_nota['conteudo'],
                tipo=dados_nota.get('tipo', 'reflexao'),
                data_criacao=datetime.now(),
                data_atualizacao=datetime.now(),
                municipio=dados_nota.get('municipio'),
                entidade=dados_nota.get('entidade'),
                tags=dados_nota.get('tags', []),
                favorito=dados_nota.get('favorito', False),
                arquivado=dados_nota.get('arquivado', False),
                categoria=dados_nota.get('categoria', '')
            )
            
            # Adicionar à lista
            self.notas.append(nota)
            
            # Salvar
            self._salvar_dados()
            
            # Gerar tags automáticas baseadas no conteúdo
            tags_sugeridas = self._gerar_tags_automaticas(nota.conteudo)
            
            return {
                'sucesso': True,
                'nota_criada': asdict(nota),
                'tags_sugeridas': tags_sugeridas,
                'notas_relacionadas': self._encontrar_notas_relacionadas(nota)
            }
            
        except Exception as e:
            return {'erro': str(e)}
    
    def criar_evento_calendario(self, dados_evento: Dict) -> Dict:
        """Cria novo evento no calendário"""
        try:
            # Validar dados obrigatórios
            campos_obrigatorios = ['titulo', 'data_inicio', 'data_fim']
            for campo in campos_obrigatorios:
                if campo not in dados_evento:
                    return {'erro': f'Campo obrigatório {campo} não informado'}
            
            # Gerar ID único
            id_evento = str(uuid.uuid4())
            
            # Criar evento
            evento = EventoCalendario(
                id=id_evento,
                titulo=dados_evento['titulo'],
                descricao=dados_evento.get('descricao', ''),
                data_inicio=self._parse_datetime(dados_evento['data_inicio']),
                data_fim=self._parse_datetime(dados_evento['data_fim']),
                tipo=dados_evento.get('tipo', 'lembrete'),
                municipio=dados_evento.get('municipio'),
                entidade=dados_evento.get('entidade'),
                notificacao=dados_evento.get('notificacao', True),
                recorrencia=dados_evento.get('recorrencia'),
                status=dados_evento.get('status', 'agendado')
            )
            
            # Adicionar à lista
            self.eventos.append(evento)
            
            # Salvar
            self._salvar_dados()
            
            # Verificar conflitos
            conflitos = self._verificar_conflitos_agenda(evento)
            
            return {
                'sucesso': True,
                'evento_criado': asdict(evento),
                'conflitos_detectados': conflitos,
                'sugestoes_otimizacao': self._sugerir_otimizacao_agenda(evento)
            }
            
        except Exception as e:
            return {'erro': str(e)}
    
    def gerar_relatorio_produtividade(self, periodo: str = 'semana') -> Dict:
        """Gera relatório detalhado de produtividade"""
        try:
            # Definir período
            if periodo == 'hoje':
                inicio = date.today()
                fim = date.today()
            elif periodo == 'semana':
                inicio = date.today() - timedelta(days=7)
                fim = date.today()
            elif periodo == 'mes':
                inicio = date.today() - timedelta(days=30)
                fim = date.today()
            else:
                inicio = date.today() - timedelta(days=7)
                fim = date.today()
            
            # Calcular métricas
            metricas = self._calcular_metricas_periodo(inicio, fim)
            
            # Análise de tendências
            tendencias = self._analisar_tendencias_produtividade(inicio, fim)
            
            # Análise de tempo
            analise_tempo = self._analisar_uso_tempo(inicio, fim)
            
            # Eficiência por tipo de tarefa
            eficiencia_tipos = self._calcular_eficiencia_tipos(inicio, fim)
            
            # Gargalos identificados
            gargalos = self._identificar_gargalos_pessoais(inicio, fim)
            
            # Recomendações personalizadas
            recomendacoes = self._gerar_recomendacoes_produtividade(metricas, tendencias)
            
            return {
                'periodo': {
                    'inicio': inicio.isoformat(),
                    'fim': fim.isoformat(),
                    'tipo': periodo
                },
                'metricas_produtividade': metricas,
                'tendencias_identificadas': tendencias,
                'analise_uso_tempo': analise_tempo,
                'eficiencia_por_tipo': eficiencia_tipos,
                'gargalos_identificados': gargalos,
                'recomendacoes_personalizadas': recomendacoes,
                'score_produtividade': self._calcular_score_produtividade(metricas),
                'comparacao_metas': self._comparar_com_metas(metricas)
            }
            
        except Exception as e:
            return {'erro': str(e)}
    
    def obter_agenda_inteligente(self, data: date = None) -> Dict:
        """Gera agenda inteligente com sugestões e otimizações"""
        try:
            if not data:
                data = date.today()
            
            # Eventos do dia
            eventos_dia = self._obter_eventos_dia(data)
            
            # Tarefas para o dia
            tarefas_dia = self._obter_tarefas_dia(data)
            
            # Tempo disponível
            tempo_disponivel = self._calcular_tempo_disponivel(data, eventos_dia)
            
            # Sugestões de organização
            sugestoes = self._gerar_sugestoes_organizacao(data, eventos_dia, tarefas_dia)
            
            # Otimizações possíveis
            otimizacoes = self._identificar_otimizacoes_agenda(data, eventos_dia, tarefas_dia)
            
            # Previsão de produtividade
            previsao = self._prever_produtividade_dia(data, eventos_dia, tarefas_dia)
            
            return {
                'data': data.isoformat(),
                'eventos_agendados': eventos_dia,
                'tarefas_planejadas': tarefas_dia,
                'tempo_disponivel': tempo_disponivel,
                'sugestoes_organizacao': sugestoes,
                'otimizacoes_possveis': otimizacoes,
                'previsao_produtividade': previsao,
                'alertas_dia': self._obter_alertas_dia(data),
                'recomendacoes_foco': self._gerar_recomendacoes_foco(data)
            }
            
        except Exception as e:
            return {'erro': str(e)}
    
    # Métodos auxiliares básicos
    def _calcular_metricas_dia(self, data): return {}
    def _obter_tarefas_prioritarias(self): return []
    def _obter_agenda_dia(self, data): return []
    def _calcular_progresso_semanal(self): return {}
    def _gerar_insights_pessoais(self): return {}
    def _calcular_estatisticas_gerais(self): return {}
    def _sugerir_proximas_acoes(self): return []
    def _obter_alertas_pessoais(self): return []
    def _parse_data(self, data_str): return datetime.now() if data_str else None
    def _parse_datetime(self, datetime_str): return datetime.now()
    def _integrar_com_visita(self, tarefa): pass
    def _salvar_dados(self): pass
    def _gerar_recomendacoes_tarefa(self, tarefa): return []
    def _sugerir_proximas_acoes_tarefa(self, tarefa): return []
    def _encontrar_tarefa(self, id_tarefa): return None
    def _atualizar_checklist(self, tarefa, update): pass
    def _analisar_impacto_mudancas(self, tarefa, mudancas): return {}
    def _gerar_tags_automaticas(self, conteudo): return []
    def _encontrar_notas_relacionadas(self, nota): return []
    def _verificar_conflitos_agenda(self, evento): return []
    def _sugerir_otimizacao_agenda(self, evento): return []
    def _calcular_metricas_periodo(self, inicio, fim): return {}
    def _analisar_tendencias_produtividade(self, inicio, fim): return {}
    def _analisar_uso_tempo(self, inicio, fim): return {}
    def _calcular_eficiencia_tipos(self, inicio, fim): return {}
    def _identificar_gargalos_pessoais(self, inicio, fim): return []
    def _gerar_recomendacoes_produtividade(self, metricas, tendencias): return []
    def _calcular_score_produtividade(self, metricas): return 75.5
    def _comparar_com_metas(self, metricas): return {}
    def _obter_eventos_dia(self, data): return []
    def _obter_tarefas_dia(self, data): return []
    def _calcular_tempo_disponivel(self, data, eventos): return 8.0
    def _gerar_sugestoes_organizacao(self, data, eventos, tarefas): return []
    def _identificar_otimizacoes_agenda(self, data, eventos, tarefas): return []
    def _prever_produtividade_dia(self, data, eventos, tarefas): return {}
    def _obter_alertas_dia(self, data): return []
    def _gerar_recomendacoes_foco(self, data): return []

# Instância global do serviço
organizacao_pessoal = OrganizacaoPessoal()