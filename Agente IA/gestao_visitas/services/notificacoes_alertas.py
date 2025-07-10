from datetime import datetime, timedelta, date, time
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from sqlalchemy import and_, or_
from ..models.agendamento import Visita
from ..models.checklist import Checklist
from ..models.contatos import Contato
from ..db import db
import json
from collections import defaultdict

class TipoNotificacao(Enum):
    LEMBRETE = "lembrete"
    ALERTA = "alerta"
    AVISO = "aviso"
    CRITICO = "critico"
    INFORMATIVO = "informativo"

class CanalNotificacao(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    SISTEMA = "sistema"
    WEBHOOK = "webhook"

class SistemaNotificacoes:
    """Sistema inteligente de notificações e alertas"""
    
    def __init__(self):
        self.regras_notificacao = self._carregar_regras_notificacao()
        self.templates_mensagens = self._carregar_templates_mensagens()
        self.configuracoes_usuario = {}
        self.historico_notificacoes = []
    
    def configurar_usuario(self, usuario_id: str, configuracoes: Dict) -> Dict:
        """Configura preferências de notificação do usuário"""
        
        config_padrao = {
            'canais_preferidos': [CanalNotificacao.SISTEMA.value, CanalNotificacao.EMAIL.value],
            'horario_nao_perturbar': {'inicio': '22:00', 'fim': '06:00'},
            'frequencia_resumos': 'diario',
            'tipos_habilitados': [tipo.value for tipo in TipoNotificacao],
            'alertas_criticos_sempre': True,
            'email': '',
            'telefone': '',
            'fuso_horario': 'America/Sao_Paulo'
        }
        
        # Mesclar com configurações fornecidas
        config_final = {**config_padrao, **configuracoes}
        self.configuracoes_usuario[usuario_id] = config_final
        
        return {
            'usuario_id': usuario_id,
            'configuracoes_aplicadas': config_final,
            'status': 'configurado',
            'canais_testados': self._testar_canais_notificacao(config_final)
        }
    
    def verificar_alertas_sistema(self) -> List[Dict]:
        """Verifica e gera alertas do sistema"""
        
        alertas = []
        agora = datetime.now()
        
        # 1. Visitas atrasadas
        alertas.extend(self._verificar_visitas_atrasadas())
        
        # 2. Checklists incompletos
        alertas.extend(self._verificar_checklists_incompletos())
        
        # 3. Contatos desatualizados
        alertas.extend(self._verificar_contatos_desatualizados())
        
        # 4. Metas não cumpridas
        alertas.extend(self._verificar_metas_nao_cumpridas())
        
        # 5. Conflitos de agendamento
        alertas.extend(self._verificar_conflitos_agendamento())
        
        # 6. Problemas de qualidade
        alertas.extend(self._verificar_problemas_qualidade())
        
        # Processar alertas e gerar notificações
        notificacoes_geradas = []
        for alerta in alertas:
            notificacao = self._processar_alerta_para_notificacao(alerta)
            if notificacao:
                notificacoes_geradas.append(notificacao)
        
        return {
            'timestamp_verificacao': agora.isoformat(),
            'total_alertas': len(alertas),
            'alertas_detectados': alertas,
            'notificacoes_geradas': len(notificacoes_geradas),
            'notificacoes': notificacoes_geradas
        }
    
    def gerar_lembretes_inteligentes(self) -> List[Dict]:
        """Gera lembretes inteligentes baseados em contexto"""
        
        lembretes = []
        agora = datetime.now()
        
        # Lembretes de visitas próximas
        lembretes.extend(self._gerar_lembretes_visitas_proximas())
        
        # Lembretes de preparação
        lembretes.extend(self._gerar_lembretes_preparacao())
        
        # Lembretes de follow-up
        lembretes.extend(self._gerar_lembretes_followup())
        
        # Lembretes de revisão
        lembretes.extend(self._gerar_lembretes_revisao())
        
        # Lembretes sazonais/contextuais
        lembretes.extend(self._gerar_lembretes_contextuais())
        
        return {
            'timestamp_geracao': agora.isoformat(),
            'total_lembretes': len(lembretes),
            'lembretes_ativos': lembretes,
            'proxima_verificacao': (agora + timedelta(hours=1)).isoformat()
        }
    
    def enviar_notificacao(self, notificacao: Dict, usuario_id: str = 'default') -> Dict:
        """Envia notificação através dos canais configurados"""
        
        config_usuario = self.configuracoes_usuario.get(usuario_id, {})
        
        # Verificar se deve enviar agora
        if not self._deve_enviar_agora(notificacao, config_usuario):
            return self._agendar_notificacao(notificacao, config_usuario)
        
        # Selecionar canais apropriados
        canais_selecionados = self._selecionar_canais_notificacao(notificacao, config_usuario)
        
        resultados_envio = {}
        
        for canal in canais_selecionados:
            try:
                resultado = self._enviar_por_canal(notificacao, canal, config_usuario)
                resultados_envio[canal] = resultado
            except Exception as e:
                resultados_envio[canal] = {'status': 'erro', 'erro': str(e)}
        
        # Registrar no histórico
        self._registrar_historico_notificacao(notificacao, resultados_envio, usuario_id)
        
        return {
            'notificacao_id': notificacao.get('id'),
            'timestamp_envio': datetime.now().isoformat(),
            'canais_utilizados': list(resultados_envio.keys()),
            'resultados_envio': resultados_envio,
            'status_geral': 'sucesso' if any(r.get('status') == 'sucesso' for r in resultados_envio.values()) else 'falha'
        }
    
    def gerar_resumo_diario(self, data: date = None) -> Dict:
        """Gera resumo diário de atividades"""
        
        if not data:
            data = date.today()
        
        # Visitas do dia
        visitas_dia = Visita.query.filter(Visita.data == data).all()
        
        # Estatísticas do dia
        stats_dia = {
            'visitas_agendadas': len([v for v in visitas_dia if v.status == 'agendada']),
            'visitas_realizadas': len([v for v in visitas_dia if v.status == 'realizada']),
            'visitas_canceladas': len([v for v in visitas_dia if v.status == 'cancelada']),
            'municipios_visitados': len(set(v.municipio for v in visitas_dia if v.status == 'realizada'))
        }
        
        # Próximas ações
        proximas_acoes = self._identificar_proximas_acoes(data)
        
        # Alertas pendentes
        alertas_pendentes = self._obter_alertas_pendentes()
        
        # Resumo de qualidade
        resumo_qualidade = self._gerar_resumo_qualidade_dia(visitas_dia)
        
        return {
            'data_resumo': data.strftime('%d/%m/%Y'),
            'estatisticas_dia': stats_dia,
            'proximas_acoes': proximas_acoes,
            'alertas_pendentes': len(alertas_pendentes),
            'resumo_qualidade': resumo_qualidade,
            'recomendacoes_dia': self._gerar_recomendacoes_dia(stats_dia, proximas_acoes),
            'gerado_em': datetime.now().isoformat()
        }
    
    def configurar_alertas_personalizados(self, usuario_id: str, alertas_config: List[Dict]) -> Dict:
        """Configura alertas personalizados para o usuário"""
        
        alertas_validos = []
        erros_validacao = []
        
        for alerta_config in alertas_config:
            try:
                alerta_validado = self._validar_configuracao_alerta(alerta_config)
                alertas_validos.append(alerta_validado)
            except Exception as e:
                erros_validacao.append({
                    'alerta': alerta_config,
                    'erro': str(e)
                })
        
        # Salvar configurações válidas
        if usuario_id not in self.configuracoes_usuario:
            self.configuracoes_usuario[usuario_id] = {}
        
        self.configuracoes_usuario[usuario_id]['alertas_personalizados'] = alertas_validos
        
        return {
            'usuario_id': usuario_id,
            'alertas_configurados': len(alertas_validos),
            'alertas_com_erro': len(erros_validacao),
            'erros_validacao': erros_validacao,
            'status': 'configurado' if alertas_validos else 'erro'
        }
    
    def obter_historico_notificacoes(self, usuario_id: str = 'default', 
                                   periodo_dias: int = 7) -> Dict:
        """Obtém histórico de notificações do usuário"""
        
        data_inicio = datetime.now() - timedelta(days=periodo_dias)
        
        historico_filtrado = [
            notif for notif in self.historico_notificacoes
            if (notif.get('usuario_id') == usuario_id and 
                datetime.fromisoformat(notif.get('timestamp', '1970-01-01')) >= data_inicio)
        ]
        
        # Estatísticas do histórico
        total_notificacoes = len(historico_filtrado)
        notif_por_tipo = defaultdict(int)
        notif_por_canal = defaultdict(int)
        taxa_sucesso_canal = defaultdict(lambda: {'enviados': 0, 'sucesso': 0})
        
        for notif in historico_filtrado:
            tipo = notif.get('tipo', 'desconhecido')
            notif_por_tipo[tipo] += 1
            
            for canal, resultado in notif.get('resultados_envio', {}).items():
                notif_por_canal[canal] += 1
                taxa_sucesso_canal[canal]['enviados'] += 1
                if resultado.get('status') == 'sucesso':
                    taxa_sucesso_canal[canal]['sucesso'] += 1
        
        # Calcular taxas de sucesso
        taxas_sucesso = {}
        for canal, stats in taxa_sucesso_canal.items():
            taxa = (stats['sucesso'] / stats['enviados'] * 100) if stats['enviados'] > 0 else 0
            taxas_sucesso[canal] = round(taxa, 1)
        
        return {
            'usuario_id': usuario_id,
            'periodo_dias': periodo_dias,
            'total_notificacoes': total_notificacoes,
            'distribuicao_por_tipo': dict(notif_por_tipo),
            'distribuicao_por_canal': dict(notif_por_canal),
            'taxas_sucesso_canal': taxas_sucesso,
            'historico_detalhado': historico_filtrado[-20:],  # Últimas 20
            'recomendacoes_otimizacao': self._gerar_recomendacoes_otimizacao(taxas_sucesso, notif_por_tipo)
        }
    
    # Métodos auxiliares de verificação de alertas
    
    def _verificar_visitas_atrasadas(self) -> List[Dict]:
        """Verifica visitas atrasadas"""
        
        hoje = date.today()
        visitas_atrasadas = Visita.query.filter(
            and_(
                Visita.data < hoje,
                Visita.status.in_(['agendada', 'em preparação'])
            )
        ).all()
        
        alertas = []
        for visita in visitas_atrasadas:
            dias_atraso = (hoje - visita.data).days
            
            alertas.append({
                'id': f"atraso_visita_{visita.id}",
                'tipo': TipoNotificacao.ALERTA.value,
                'severidade': 'alta' if dias_atraso > 7 else 'media',
                'titulo': f"Visita atrasada - {visita.municipio}",
                'mensagem': f"Visita agendada para {visita.data.strftime('%d/%m/%Y')} está {dias_atraso} dia(s) em atraso",
                'dados_contexto': {
                    'visita_id': visita.id,
                    'municipio': visita.municipio,
                    'dias_atraso': dias_atraso,
                    'informante': visita.informante
                },
                'acoes_sugeridas': [
                    {'acao': 'reagendar', 'texto': 'Reagendar visita'},
                    {'acao': 'cancelar', 'texto': 'Cancelar visita'},
                    {'acao': 'contatar', 'texto': 'Contatar informante'}
                ],
                'timestamp_deteccao': datetime.now().isoformat()
            })
        
        return alertas
    
    def _verificar_checklists_incompletos(self) -> List[Dict]:
        """Verifica checklists incompletos em visitas realizadas"""
        
        alertas = []
        
        # Buscar visitas realizadas com checklists incompletos
        visitas_realizadas = Visita.query.filter(
            Visita.status == 'realizada'
        ).all()
        
        for visita in visitas_realizadas:
            if visita.checklist:
                progresso = visita.checklist.progresso_geral()
                
                if progresso['percentual'] < 80:  # Menos de 80% completo
                    alertas.append({
                        'id': f"checklist_incompleto_{visita.id}",
                        'tipo': TipoNotificacao.AVISO.value,
                        'severidade': 'media',
                        'titulo': f"Checklist incompleto - {visita.municipio}",
                        'mensagem': f"Checklist da visita realizada está {progresso['percentual']:.1f}% completo",
                        'dados_contexto': {
                            'visita_id': visita.id,
                            'municipio': visita.municipio,
                            'percentual_completo': progresso['percentual'],
                            'itens_faltantes': progresso['total_itens'] - progresso['itens_concluidos']
                        },
                        'acoes_sugeridas': [
                            {'acao': 'completar', 'texto': 'Completar checklist'},
                            {'acao': 'revisar', 'texto': 'Revisar itens faltantes'}
                        ],
                        'timestamp_deteccao': datetime.now().isoformat()
                    })
        
        return alertas
    
    def _verificar_contatos_desatualizados(self) -> List[Dict]:
        """Verifica contatos que precisam de atualização"""
        
        alertas = []
        limite_dias = 90  # 3 meses
        data_limite = datetime.now() - timedelta(days=limite_dias)
        
        contatos_desatualizados = Contato.query.filter(
            or_(
                Contato.data_atualizacao < data_limite,
                Contato.data_atualizacao.is_(None)
            )
        ).all()
        
        if len(contatos_desatualizados) > 0:
            alertas.append({
                'id': "contatos_desatualizados",
                'tipo': TipoNotificacao.INFORMATIVO.value,
                'severidade': 'baixa',
                'titulo': f"{len(contatos_desatualizados)} contato(s) desatualizado(s)",
                'mensagem': f"Contatos não atualizados há mais de {limite_dias} dias",
                'dados_contexto': {
                    'total_desatualizados': len(contatos_desatualizados),
                    'municipios_afetados': list(set(c.municipio for c in contatos_desatualizados)),
                    'limite_dias': limite_dias
                },
                'acoes_sugeridas': [
                    {'acao': 'atualizar_todos', 'texto': 'Atualizar todos os contatos'},
                    {'acao': 'revisar_lista', 'texto': 'Revisar lista de contatos'}
                ],
                'timestamp_deteccao': datetime.now().isoformat()
            })
        
        return alertas
    
    def _verificar_metas_nao_cumpridas(self) -> List[Dict]:
        """Verifica metas não cumpridas"""
        
        alertas = []
        
        # Meta: todos os 11 municípios devem ter pelo menos uma visita realizada
        municipios_sem_visita = []
        from ..config import MUNICIPIOS
        
        for municipio in MUNICIPIOS:
            visitas_realizadas = Visita.query.filter(
                and_(
                    Visita.municipio == municipio,
                    Visita.status == 'realizada'
                )
            ).count()
            
            if visitas_realizadas == 0:
                municipios_sem_visita.append(municipio)
        
        if municipios_sem_visita:
            alertas.append({
                'id': "meta_cobertura_municipios",
                'tipo': TipoNotificacao.ALERTA.value,
                'severidade': 'alta',
                'titulo': f"{len(municipios_sem_visita)} município(s) sem visitas realizadas",
                'mensagem': f"Meta de cobertura não atingida: {municipios_sem_visita}",
                'dados_contexto': {
                    'municipios_pendentes': municipios_sem_visita,
                    'cobertura_atual': ((11 - len(municipios_sem_visita)) / 11) * 100,
                    'meta_cobertura': 100
                },
                'acoes_sugeridas': [
                    {'acao': 'agendar_visitas', 'texto': 'Agendar visitas para municípios pendentes'},
                    {'acao': 'priorizar_municipios', 'texto': 'Priorizar municípios sem cobertura'}
                ],
                'timestamp_deteccao': datetime.now().isoformat()
            })
        
        return alertas
    
    def _verificar_conflitos_agendamento(self) -> List[Dict]:
        """Verifica conflitos de agendamento"""
        
        alertas = []
        
        # Buscar visitas agendadas para os próximos 7 dias
        data_inicio = date.today()
        data_fim = data_inicio + timedelta(days=7)
        
        visitas_proximas = Visita.query.filter(
            and_(
                Visita.data >= data_inicio,
                Visita.data <= data_fim,
                Visita.status.in_(['agendada', 'em preparação'])
            )
        ).order_by(Visita.data, Visita.hora_inicio).all()
        
        # Verificar sobreposições
        conflitos_detectados = []
        for i, visita1 in enumerate(visitas_proximas):
            for visita2 in visitas_proximas[i+1:]:
                if (visita1.data == visita2.data and 
                    self._horarios_sobrepostos(visita1, visita2)):
                    
                    conflitos_detectados.append({
                        'visita1': visita1,
                        'visita2': visita2,
                        'tipo_conflito': 'sobreposicao_horario'
                    })
        
        if conflitos_detectados:
            alertas.append({
                'id': "conflitos_agendamento",
                'tipo': TipoNotificacao.ALERTA.value,
                'severidade': 'alta',
                'titulo': f"{len(conflitos_detectados)} conflito(s) de agendamento detectado(s)",
                'mensagem': "Visitas com horários sobrepostos identificadas",
                'dados_contexto': {
                    'total_conflitos': len(conflitos_detectados),
                    'conflitos': [
                        {
                            'data': c['visita1'].data.strftime('%d/%m/%Y'),
                            'municipio1': c['visita1'].municipio,
                            'municipio2': c['visita2'].municipio,
                            'horario1': c['visita1'].hora_inicio.strftime('%H:%M'),
                            'horario2': c['visita2'].hora_inicio.strftime('%H:%M')
                        }
                        for c in conflitos_detectados
                    ]
                },
                'acoes_sugeridas': [
                    {'acao': 'resolver_conflitos', 'texto': 'Resolver conflitos de horário'},
                    {'acao': 'reagendar_automatico', 'texto': 'Sugerir reagendamento automático'}
                ],
                'timestamp_deteccao': datetime.now().isoformat()
            })
        
        return alertas
    
    def _verificar_problemas_qualidade(self) -> List[Dict]:
        """Verifica problemas recorrentes de qualidade"""
        
        alertas = []
        
        # Verificar taxa de cancelamento alta
        ultima_semana = date.today() - timedelta(days=7)
        visitas_semana = Visita.query.filter(Visita.data >= ultima_semana).all()
        
        if visitas_semana:
            visitas_canceladas = [v for v in visitas_semana if v.status == 'cancelada']
            taxa_cancelamento = (len(visitas_canceladas) / len(visitas_semana)) * 100
            
            if taxa_cancelamento > 20:  # Mais de 20% de cancelamento
                alertas.append({
                    'id': "alta_taxa_cancelamento",
                    'tipo': TipoNotificacao.AVISO.value,
                    'severidade': 'media',
                    'titulo': f"Alta taxa de cancelamento: {taxa_cancelamento:.1f}%",
                    'mensagem': f"Taxa de cancelamento acima do esperado na última semana",
                    'dados_contexto': {
                        'taxa_cancelamento': taxa_cancelamento,
                        'visitas_canceladas': len(visitas_canceladas),
                        'total_visitas': len(visitas_semana),
                        'periodo': '7 dias'
                    },
                    'acoes_sugeridas': [
                        {'acao': 'analisar_causas', 'texto': 'Analisar causas dos cancelamentos'},
                        {'acao': 'melhorar_processo', 'texto': 'Revisar processo de agendamento'}
                    ],
                    'timestamp_deteccao': datetime.now().isoformat()
                })
        
        return alertas
    
    # Métodos auxiliares de lembretes
    
    def _gerar_lembretes_visitas_proximas(self) -> List[Dict]:
        """Gera lembretes para visitas próximas"""
        
        lembretes = []
        amanha = date.today() + timedelta(days=1)
        
        visitas_amanha = Visita.query.filter(
            and_(
                Visita.data == amanha,
                Visita.status.in_(['agendada', 'em preparação'])
            )
        ).all()
        
        for visita in visitas_amanha:
            lembretes.append({
                'id': f"lembrete_visita_{visita.id}",
                'tipo': TipoNotificacao.LEMBRETE.value,
                'titulo': f"Visita amanhã - {visita.municipio}",
                'mensagem': f"Visita agendada para {visita.data.strftime('%d/%m/%Y')} às {visita.hora_inicio.strftime('%H:%M')}",
                'dados_contexto': {
                    'visita_id': visita.id,
                    'municipio': visita.municipio,
                    'informante': visita.informante,
                    'tipo_pesquisa': visita.tipo_pesquisa
                },
                'acoes_sugeridas': [
                    {'acao': 'ver_checklist', 'texto': 'Ver checklist de preparação'},
                    {'acao': 'confirmar_visita', 'texto': 'Confirmar com informante'}
                ],
                'agendado_para': (datetime.combine(amanha, time(8, 0)) - timedelta(days=1)).isoformat()
            })
        
        return lembretes
    
    def _gerar_lembretes_preparacao(self) -> List[Dict]:
        """Gera lembretes de preparação para visitas"""
        
        lembretes = []
        proxima_semana = date.today() + timedelta(days=7)
        
        visitas_proxima_semana = Visita.query.filter(
            and_(
                Visita.data <= proxima_semana,
                Visita.data > date.today(),
                Visita.status == 'agendada'
            )
        ).all()
        
        for visita in visitas_proxima_semana:
            # Verificar se checklist está preparado
            if not visita.checklist or visita.checklist.progresso_geral()['percentual'] < 50:
                lembretes.append({
                    'id': f"preparacao_visita_{visita.id}",
                    'tipo': TipoNotificacao.LEMBRETE.value,
                    'titulo': f"Preparar visita - {visita.municipio}",
                    'mensagem': f"Completar preparação para visita em {visita.municipio}",
                    'dados_contexto': {
                        'visita_id': visita.id,
                        'municipio': visita.municipio,
                        'data_visita': visita.data.strftime('%d/%m/%Y'),
                        'dias_restantes': (visita.data - date.today()).days
                    },
                    'acoes_sugeridas': [
                        {'acao': 'completar_checklist', 'texto': 'Completar checklist'},
                        {'acao': 'verificar_materiais', 'texto': 'Verificar materiais necessários'}
                    ],
                    'prioridade': 'alta' if (visita.data - date.today()).days <= 2 else 'media'
                })
        
        return lembretes
    
    # Métodos auxiliares de processamento
    
    def _processar_alerta_para_notificacao(self, alerta: Dict) -> Optional[Dict]:
        """Processa alerta e converte para notificação"""
        
        # Verificar se já foi enviado recentemente
        if self._alerta_ja_enviado_recentemente(alerta['id']):
            return None
        
        # Converter alerta para formato de notificação
        notificacao = {
            'id': f"notif_{alerta['id']}_{int(datetime.now().timestamp())}",
            'tipo': alerta['tipo'],
            'severidade': alerta['severidade'],
            'titulo': alerta['titulo'],
            'mensagem': alerta['mensagem'],
            'dados_contexto': alerta['dados_contexto'],
            'acoes_sugeridas': alerta.get('acoes_sugeridas', []),
            'timestamp_criacao': datetime.now().isoformat(),
            'origem': 'sistema_alertas'
        }
        
        return notificacao
    
    def _deve_enviar_agora(self, notificacao: Dict, config_usuario: Dict) -> bool:
        """Verifica se deve enviar notificação agora"""
        
        # Alertas críticos sempre enviam
        if notificacao.get('severidade') == 'critica' and config_usuario.get('alertas_criticos_sempre', True):
            return True
        
        # Verificar horário de não perturbar
        agora = datetime.now().time()
        horario_nao_perturbar = config_usuario.get('horario_nao_perturbar', {})
        
        if horario_nao_perturbar:
            inicio = datetime.strptime(horario_nao_perturbar.get('inicio', '22:00'), '%H:%M').time()
            fim = datetime.strptime(horario_nao_perturbar.get('fim', '06:00'), '%H:%M').time()
            
            if inicio <= fim:  # Mesmo dia
                if inicio <= agora <= fim:
                    return False
            else:  # Atravessa meia-noite
                if agora >= inicio or agora <= fim:
                    return False
        
        return True
    
    def _selecionar_canais_notificacao(self, notificacao: Dict, config_usuario: Dict) -> List[str]:
        """Seleciona canais apropriados para a notificação"""
        
        canais_preferidos = config_usuario.get('canais_preferidos', [CanalNotificacao.SISTEMA.value])
        severidade = notificacao.get('severidade', 'baixa')
        
        # Para severidade crítica, usar todos os canais disponíveis
        if severidade == 'critica':
            return [canal for canal in canais_preferidos if self._canal_disponivel(canal, config_usuario)]
        
        # Para outras severidades, usar canais padrão
        canais_selecionados = []
        
        # Sistema sempre disponível
        if CanalNotificacao.SISTEMA.value in canais_preferidos:
            canais_selecionados.append(CanalNotificacao.SISTEMA.value)
        
        # Email para severidade alta ou média
        if (severidade in ['alta', 'media'] and 
            CanalNotificacao.EMAIL.value in canais_preferidos and
            config_usuario.get('email')):
            canais_selecionados.append(CanalNotificacao.EMAIL.value)
        
        return canais_selecionados
    
    # Métodos de envio por canal (simplificados)
    
    def _enviar_por_canal(self, notificacao: Dict, canal: str, config_usuario: Dict) -> Dict:
        """Envia notificação por canal específico"""
        
        if canal == CanalNotificacao.SISTEMA.value:
            return self._enviar_notificacao_sistema(notificacao)
        elif canal == CanalNotificacao.EMAIL.value:
            return self._enviar_notificacao_email(notificacao, config_usuario)
        elif canal == CanalNotificacao.SMS.value:
            return self._enviar_notificacao_sms(notificacao, config_usuario)
        else:
            return {'status': 'erro', 'erro': f'Canal {canal} não implementado'}
    
    def _enviar_notificacao_sistema(self, notificacao: Dict) -> Dict:
        """Envia notificação no sistema"""
        # Implementação simplificada
        return {
            'status': 'sucesso',
            'canal': 'sistema',
            'timestamp_envio': datetime.now().isoformat()
        }
    
    def _enviar_notificacao_email(self, notificacao: Dict, config_usuario: Dict) -> Dict:
        """Envia notificação por email"""
        # Implementação simplificada
        return {
            'status': 'sucesso',
            'canal': 'email',
            'destinatario': config_usuario.get('email'),
            'timestamp_envio': datetime.now().isoformat()
        }
    
    def _enviar_notificacao_sms(self, notificacao: Dict, config_usuario: Dict) -> Dict:
        """Envia notificação por SMS"""
        # Implementação simplificada
        return {
            'status': 'sucesso',
            'canal': 'sms',
            'destinatario': config_usuario.get('telefone'),
            'timestamp_envio': datetime.now().isoformat()
        }
    
    # Métodos auxiliares (implementações simplificadas)
    
    def _carregar_regras_notificacao(self) -> Dict:
        """Carrega regras de notificação"""
        return {}
    
    def _carregar_templates_mensagens(self) -> Dict:
        """Carrega templates de mensagens"""
        return {}
    
    def _testar_canais_notificacao(self, config: Dict) -> Dict:
        """Testa canais de notificação configurados"""
        return {'email': True, 'sms': False, 'sistema': True}
    
    def _horarios_sobrepostos(self, visita1: Visita, visita2: Visita) -> bool:
        """Verifica se horários de duas visitas se sobrepõem"""
        return (visita1.hora_inicio <= visita2.hora_inicio <= visita1.hora_fim or
                visita2.hora_inicio <= visita1.hora_inicio <= visita2.hora_fim)
    
    def _alerta_ja_enviado_recentemente(self, alerta_id: str) -> bool:
        """Verifica se alerta já foi enviado recentemente"""
        # Implementação simplificada
        return False
    
    def _registrar_historico_notificacao(self, notificacao: Dict, resultados: Dict, usuario_id: str):
        """Registra notificação no histórico"""
        self.historico_notificacoes.append({
            'notificacao_id': notificacao.get('id'),
            'usuario_id': usuario_id,
            'tipo': notificacao.get('tipo'),
            'timestamp': datetime.now().isoformat(),
            'resultados_envio': resultados
        })
    
    def _gerar_recomendacoes_otimizacao(self, taxas_sucesso: Dict, notif_por_tipo: Dict) -> List[str]:
        """Gera recomendações para otimização das notificações"""
        recomendacoes = []
        
        # Verificar canais com baixa taxa de sucesso
        for canal, taxa in taxas_sucesso.items():
            if taxa < 80:
                recomendacoes.append(f"Verificar configuração do canal {canal} (taxa de sucesso: {taxa}%)")
        
        return recomendacoes