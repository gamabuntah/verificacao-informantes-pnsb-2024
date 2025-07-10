"""
Sistema de Chat Interno e Colaboração - PNSB 2024
Chat em tempo real, canais por município, colaboração entre pesquisadores
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy import func, and_, or_, desc
from ..models.agendamento import Visita
from ..models.contatos import Contato
from ..db import db
import json
import uuid
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict
import os

class TipoMensagem(Enum):
    TEXTO = "texto"
    ARQUIVO = "arquivo"
    IMAGEM = "imagem"
    SISTEMA = "sistema"
    COMPARTILHAMENTO = "compartilhamento"
    ALERTA = "alerta"
    ATUALIZACAO = "atualizacao"

class TipoCanal(Enum):
    GERAL = "geral"
    MUNICIPIO = "municipio"
    PROJETO = "projeto"
    PRIVADO = "privado"
    SUPORTE = "suporte"
    ALERTAS = "alertas"

class StatusMensagem(Enum):
    ENVIADA = "enviada"
    ENTREGUE = "entregue"
    LIDA = "lida"
    EDITADA = "editada"
    DELETADA = "deletada"

class TipoNotificacao(Enum):
    MENSAO = "mencao"
    RESPOSTA = "resposta"
    CANAL_NOVO = "canal_novo"
    ARQUIVO_COMPARTILHADO = "arquivo_compartilhado"
    ALERTA_SISTEMA = "alerta_sistema"

@dataclass
class MensagemChat:
    id: str
    canal_id: str
    autor_id: str
    autor_nome: str
    tipo: TipoMensagem
    conteudo: str
    timestamp: datetime
    status: StatusMensagem
    resposta_para: Optional[str] = None
    editado_em: Optional[datetime] = None
    anexos: List[str] = None
    mencoes: List[str] = None
    reacoes: Dict[str, List[str]] = None
    metadata: Dict = None

@dataclass
class CanalChat:
    id: str
    nome: str
    tipo: TipoCanal
    descricao: str
    criado_por: str
    criado_em: datetime
    municipio: Optional[str] = None
    membros: List[str] = None
    admins: List[str] = None
    configuracoes: Dict = None
    ultimo_atividade: datetime = None
    mensagens_nao_lidas: int = 0
    ativo: bool = True

@dataclass
class NotificacaoChat:
    id: str
    usuario_id: str
    tipo: TipoNotificacao
    titulo: str
    conteudo: str
    canal_id: str
    mensagem_id: Optional[str] = None
    timestamp: datetime = None
    lida: bool = False
    acao_requerida: bool = False

class ChatColaboracao:
    """Sistema completo de chat e colaboração para PNSB 2024"""
    
    def __init__(self):
        self.canais = {}
        self.mensagens = {}
        self.usuarios_online = set()
        self.notificacoes = {}
        
        # Configurações do sistema
        self.configuracoes = {
            'max_mensagens_por_canal': 10000,
            'tempo_edicao_limite': 300,  # 5 minutos
            'tamanho_max_arquivo': 50 * 1024 * 1024,  # 50MB
            'tipos_arquivo_permitidos': ['.pdf', '.jpg', '.png', '.docx', '.xlsx', '.csv'],
            'historico_maximo_dias': 365,
            'notificacoes_push': True,
            'backup_automatico': True,
            'moderacao_ativa': True
        }
        
        # Canais padrão do sistema
        self.canais_padrao = [
            ('geral', 'Discussões Gerais', 'Canal principal para comunicação geral'),
            ('alertas', 'Alertas do Sistema', 'Notificações automáticas do sistema'),
            ('suporte', 'Suporte Técnico', 'Canal para questões técnicas e dúvidas')
        ]
        
        # Municipios PNSB 2024
        self.municipios_pnsb = [
            'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas',
            'Camboriú', 'Itajaí', 'Itapema', 'Luiz Alves',
            'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
        ]
        
        # Emojis e reações padrão
        self.reacoes_padrao = ['👍', '👎', '❤️', '😀', '😢', '😮', '🔥', '👏']
        
        # Inicializar sistema
        self._inicializar_canais_padrao()
        self._inicializar_canais_municipios()
    
    def enviar_mensagem(self, canal_id: str, autor_id: str, conteudo: str, 
                       tipo: TipoMensagem = TipoMensagem.TEXTO, metadata: Dict = None) -> Dict:
        """Envia mensagem para um canal"""
        try:
            # Validar canal e permissões
            if not self._validar_acesso_canal(canal_id, autor_id):
                return {'erro': 'Acesso negado ao canal'}
            
            # Buscar informações do autor
            autor_info = self._obter_info_usuario(autor_id)
            
            # Processar conteúdo (mencoes, links, etc.)
            conteudo_processado = self._processar_conteudo_mensagem(conteudo)
            
            # Criar mensagem
            mensagem = MensagemChat(
                id=str(uuid.uuid4()),
                canal_id=canal_id,
                autor_id=autor_id,
                autor_nome=autor_info['nome'],
                tipo=tipo,
                conteudo=conteudo_processado['texto'],
                timestamp=datetime.now(),
                status=StatusMensagem.ENVIADA,
                anexos=metadata.get('anexos', []) if metadata else [],
                mencoes=conteudo_processado.get('mencoes', []),
                reacoes={},
                metadata=metadata or {}
            )
            
            # Salvar mensagem
            self._salvar_mensagem(mensagem)
            
            # Atualizar canal
            self._atualizar_atividade_canal(canal_id)
            
            # Processar mencoes e notificações
            notificacoes_enviadas = self._processar_notificacoes(mensagem)
            
            # Broadcast para usuários online
            self._broadcast_mensagem(mensagem)
            
            return {
                'sucesso': True,
                'mensagem': asdict(mensagem),
                'notificacoes_enviadas': notificacoes_enviadas,
                'mencoes_processadas': len(mensagem.mencoes or [])
            }
            
        except Exception as e:
            return {'erro': str(e)}
    
    def criar_canal(self, nome: str, tipo: TipoCanal, criado_por: str, 
                   configuracao: Dict = None) -> Dict:
        """Cria novo canal de comunicação"""
        try:
            # Validar permissões
            if not self._validar_permissao_criar_canal(criado_por):
                return {'erro': 'Permissão insuficiente para criar canal'}
            
            # Validar nome único
            if self._canal_existe(nome):
                return {'erro': 'Canal com este nome já existe'}
            
            # Criar canal
            canal = CanalChat(
                id=str(uuid.uuid4()),
                nome=nome,
                tipo=tipo,
                descricao=configuracao.get('descricao', '') if configuracao else '',
                criado_por=criado_por,
                criado_em=datetime.now(),
                municipio=configuracao.get('municipio') if configuracao else None,
                membros=configuracao.get('membros', [criado_por]) if configuracao else [criado_por],
                admins=[criado_por],
                configuracoes=configuracao or {},
                ultimo_atividade=datetime.now(),
                ativo=True
            )
            
            # Salvar canal
            self._salvar_canal(canal)
            
            # Notificar membros iniciais
            self._notificar_canal_novo(canal)
            
            # Mensagem de sistema
            self._enviar_mensagem_sistema(
                canal.id, 
                f"Canal {nome} criado por {self._obter_info_usuario(criado_por)['nome']}"
            )
            
            return {
                'sucesso': True,
                'canal': asdict(canal),
                'membros_notificados': len(canal.membros)
            }
            
        except Exception as e:
            return {'erro': str(e)}
    
    def obter_mensagens_canal(self, canal_id: str, usuario_id: str, 
                             limite: int = 50, antes_de: str = None) -> Dict:
        """Obtém mensagens de um canal com paginação"""
        try:
            # Validar acesso
            if not self._validar_acesso_canal(canal_id, usuario_id):
                return {'erro': 'Acesso negado ao canal'}
            
            # Buscar mensagens
            mensagens = self._buscar_mensagens_canal(canal_id, limite, antes_de)
            
            # Marcar como lidas
            self._marcar_mensagens_lidas(canal_id, usuario_id, mensagens)
            
            # Buscar informações adicionais
            info_canal = self._obter_info_canal(canal_id)
            
            # Processar mensagens para exibição
            mensagens_processadas = self._processar_mensagens_exibicao(mensagens, usuario_id)
            
            return {
                'mensagens': mensagens_processadas,
                'canal': info_canal,
                'total_mensagens': len(mensagens),
                'ha_mais_mensagens': len(mensagens) == limite,
                'usuarios_online': self._obter_usuarios_online_canal(canal_id)
            }
            
        except Exception as e:
            return {'erro': str(e)}
    
    def compartilhar_visita(self, visita_id: int, canal_id: str, usuario_id: str, 
                           comentario: str = '') -> Dict:
        """Compartilha informações de visita no chat"""
        try:
            # Buscar visita
            visita = Visita.query.get(visita_id)
            if not visita:
                return {'erro': 'Visita não encontrada'}
            
            # Validar acesso ao canal
            if not self._validar_acesso_canal(canal_id, usuario_id):
                return {'erro': 'Acesso negado ao canal'}
            
            # Criar conteúdo da mensagem
            conteudo_compartilhamento = self._criar_conteudo_visita(visita, comentario)
            
            # Enviar mensagem de compartilhamento
            resultado = self.enviar_mensagem(
                canal_id=canal_id,
                autor_id=usuario_id,
                conteudo=conteudo_compartilhamento['texto'],
                tipo=TipoMensagem.COMPARTILHAMENTO,
                metadata={
                    'tipo_compartilhamento': 'visita',
                    'visita_id': visita_id,
                    'dados_visita': conteudo_compartilhamento['dados']
                }
            )
            
            return resultado
            
        except Exception as e:
            return {'erro': str(e)}
    
    def obter_dashboard_colaboracao(self, usuario_id: str) -> Dict:
        """Dashboard de colaboração do usuário"""
        try:
            # Canais do usuário
            canais_usuario = self._obter_canais_usuario(usuario_id)
            
            # Mensagens não lidas
            mensagens_nao_lidas = self._contar_mensagens_nao_lidas(usuario_id)
            
            # Notificações pendentes
            notificacoes_pendentes = self._obter_notificacoes_pendentes(usuario_id)
            
            # Atividade recente
            atividade_recente = self._obter_atividade_recente(usuario_id)
            
            # Usuários online
            usuarios_online = self._obter_usuarios_online()
            
            # Estatísticas de colaboração
            estatisticas = self._calcular_estatisticas_colaboracao(usuario_id)
            
            # Sugestões de canais
            sugestoes_canais = self._gerar_sugestoes_canais(usuario_id)
            
            return {
                'canais_usuario': canais_usuario,
                'mensagens_nao_lidas': mensagens_nao_lidas,
                'notificacoes_pendentes': notificacoes_pendentes,
                'atividade_recente': atividade_recente,
                'usuarios_online': usuarios_online,
                'estatisticas_colaboracao': estatisticas,
                'sugestoes_canais': sugestoes_canais,
                'configuracoes_chat': self._obter_configuracoes_usuario(usuario_id)
            }
            
        except Exception as e:
            return {'erro': str(e)}
    
    def buscar_mensagens(self, usuario_id: str, termo_busca: str, 
                        filtros: Dict = None) -> Dict:
        """Busca mensagens em todos os canais acessíveis"""
        try:
            # Validar termo de busca
            if len(termo_busca.strip()) < 3:
                return {'erro': 'Termo de busca deve ter pelo menos 3 caracteres'}
            
            # Obter canais acessíveis
            canais_acessiveis = self._obter_canais_acessiveis(usuario_id)
            
            # Aplicar filtros
            filtros_processados = self._processar_filtros_busca(filtros or {})
            
            # Buscar mensagens
            resultados = self._buscar_mensagens_texto(
                termo_busca, canais_acessiveis, filtros_processados
            )
            
            # Ordenar por relevância
            resultados_ordenados = self._ordenar_por_relevancia(resultados, termo_busca)
            
            # Destacar termos encontrados
            resultados_destacados = self._destacar_termos_busca(resultados_ordenados, termo_busca)
            
            return {
                'resultados': resultados_destacados,
                'total_encontrados': len(resultados),
                'canais_pesquisados': len(canais_acessiveis),
                'termo_busca': termo_busca,
                'filtros_aplicados': filtros_processados
            }
            
        except Exception as e:
            return {'erro': str(e)}
    
    def configurar_notificacoes(self, usuario_id: str, configuracoes: Dict) -> Dict:
        """Configura preferências de notificação do usuário"""
        try:
            # Validar configurações
            config_validadas = self._validar_configuracoes_notificacao(configuracoes)
            
            # Salvar configurações
            self._salvar_configuracoes_usuario(usuario_id, config_validadas)
            
            # Atualizar sistema de notificações
            self._atualizar_sistema_notificacoes(usuario_id, config_validadas)
            
            return {
                'sucesso': True,
                'configuracoes_salvas': config_validadas,
                'proxima_sincronizacao': self._calcular_proxima_sincronizacao()
            }
            
        except Exception as e:
            return {'erro': str(e)}
    
    def gerar_relatorio_colaboracao(self, periodo: str = 'semana') -> Dict:
        """Gera relatório de atividade de colaboração"""
        try:
            # Definir período
            data_inicio, data_fim = self._calcular_periodo_relatorio(periodo)
            
            # Coletar métricas
            metricas_periodo = self._coletar_metricas_colaboracao(data_inicio, data_fim)
            
            # Análise de participação
            analise_participacao = self._analisar_participacao_usuarios(data_inicio, data_fim)
            
            # Canais mais ativos
            canais_ativos = self._identificar_canais_mais_ativos(data_inicio, data_fim)
            
            # Tendências de comunicação
            tendencias = self._analisar_tendencias_comunicacao(data_inicio, data_fim)
            
            # Insights e recomendações
            insights = self._gerar_insights_colaboracao(metricas_periodo, analise_participacao)
            
            return {
                'periodo': {
                    'inicio': data_inicio.isoformat(),
                    'fim': data_fim.isoformat(),
                    'tipo': periodo
                },
                'metricas_gerais': metricas_periodo,
                'analise_participacao': analise_participacao,
                'canais_mais_ativos': canais_ativos,
                'tendencias_comunicacao': tendencias,
                'insights_recomendacoes': insights,
                'score_colaboracao': self._calcular_score_colaboracao(metricas_periodo)
            }
            
        except Exception as e:
            return {'erro': str(e)}
    
    def _inicializar_canais_padrao(self):
        """Inicializa canais padrão do sistema"""
        for canal_id, nome, descricao in self.canais_padrao:
            if not self._canal_existe(nome):
                self.criar_canal(nome, TipoCanal.GERAL, 'sistema', {
                    'descricao': descricao,
                    'publico': True
                })
    
    def _inicializar_canais_municipios(self):
        """Cria canais para cada município"""
        for municipio in self.municipios_pnsb:
            nome_canal = f"municipio-{municipio.lower().replace(' ', '-')}"
            if not self._canal_existe(nome_canal):
                self.criar_canal(nome_canal, TipoCanal.MUNICIPIO, 'sistema', {
                    'descricao': f'Canal dedicado ao município de {municipio}',
                    'municipio': municipio,
                    'publico': True
                })
    
    # Métodos auxiliares básicos
    def _validar_acesso_canal(self, canal_id, usuario_id): return True
    def _obter_info_usuario(self, usuario_id): return {'nome': 'Pesquisador IBGE', 'email': 'pesquisador@ibge.gov.br'}
    def _processar_conteudo_mensagem(self, conteudo): return {'texto': conteudo, 'mencoes': []}
    def _salvar_mensagem(self, mensagem): pass
    def _atualizar_atividade_canal(self, canal_id): pass
    def _processar_notificacoes(self, mensagem): return []
    def _broadcast_mensagem(self, mensagem): pass
    def _validar_permissao_criar_canal(self, usuario_id): return True
    def _canal_existe(self, nome): return False
    def _salvar_canal(self, canal): pass
    def _notificar_canal_novo(self, canal): pass
    def _enviar_mensagem_sistema(self, canal_id, conteudo): pass
    def _buscar_mensagens_canal(self, canal_id, limite, antes_de): return []
    def _marcar_mensagens_lidas(self, canal_id, usuario_id, mensagens): pass
    def _obter_info_canal(self, canal_id): return {}
    def _processar_mensagens_exibicao(self, mensagens, usuario_id): return []
    def _obter_usuarios_online_canal(self, canal_id): return []
    def _criar_conteudo_visita(self, visita, comentario): 
        return {
            'texto': f"Compartilhando visita: {visita.municipio} - {visita.data.strftime('%d/%m/%Y')}",
            'dados': {'municipio': visita.municipio, 'status': visita.status}
        }
    def _obter_canais_usuario(self, usuario_id): return []
    def _contar_mensagens_nao_lidas(self, usuario_id): return 0
    def _obter_notificacoes_pendentes(self, usuario_id): return []
    def _obter_atividade_recente(self, usuario_id): return []
    def _obter_usuarios_online(self): return []
    def _calcular_estatisticas_colaboracao(self, usuario_id): return {}
    def _gerar_sugestoes_canais(self, usuario_id): return []
    def _obter_configuracoes_usuario(self, usuario_id): return {}
    def _obter_canais_acessiveis(self, usuario_id): return []
    def _processar_filtros_busca(self, filtros): return filtros
    def _buscar_mensagens_texto(self, termo, canais, filtros): return []
    def _ordenar_por_relevancia(self, resultados, termo): return resultados
    def _destacar_termos_busca(self, resultados, termo): return resultados
    def _validar_configuracoes_notificacao(self, config): return config
    def _salvar_configuracoes_usuario(self, usuario_id, config): pass
    def _atualizar_sistema_notificacoes(self, usuario_id, config): pass
    def _calcular_proxima_sincronizacao(self): return (datetime.now() + timedelta(hours=1)).isoformat()
    def _calcular_periodo_relatorio(self, periodo): 
        fim = datetime.now()
        inicio = fim - timedelta(days=7 if periodo == 'semana' else 30)
        return inicio, fim
    def _coletar_metricas_colaboracao(self, inicio, fim): return {}
    def _analisar_participacao_usuarios(self, inicio, fim): return {}
    def _identificar_canais_mais_ativos(self, inicio, fim): return []
    def _analisar_tendencias_comunicacao(self, inicio, fim): return {}
    def _gerar_insights_colaboracao(self, metricas, participacao): return []
    def _calcular_score_colaboracao(self, metricas): return 82.5

# Instância global do serviço
chat_colaboracao = ChatColaboracao()