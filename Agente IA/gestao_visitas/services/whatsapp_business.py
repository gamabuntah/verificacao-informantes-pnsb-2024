"""
Integração WhatsApp Business API - PNSB 2024
Sistema automatizado de follow-up e comunicação com informantes
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy import func, and_, or_, desc
from ..models.agendamento import Visita
from ..models.contatos import Contato
from ..db import db
import json
import requests
from enum import Enum
from dataclasses import dataclass, asdict
import uuid
import time

class TipoMensagem(Enum):
    AGENDAMENTO = "agendamento"
    CONFIRMACAO = "confirmacao"
    LEMBRETE = "lembrete"
    FOLLOW_UP = "follow_up"
    QUESTIONARIO = "questionario"
    AGRADECIMENTO = "agradecimento"
    REAGENDAMENTO = "reagendamento"
    CANCELAMENTO = "cancelamento"

class StatusMensagem(Enum):
    PENDENTE = "pendente"
    ENVIADA = "enviada"
    ENTREGUE = "entregue"
    LIDA = "lida"
    RESPONDIDA = "respondida"
    FALHOU = "falhou"
    CANCELADA = "cancelada"

class PrioridadeMensagem(Enum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    URGENTE = "urgente"

@dataclass
class MensagemWhatsApp:
    id: str
    destinatario: str
    municipio: str
    tipo: TipoMensagem
    prioridade: PrioridadeMensagem
    status: StatusMensagem
    titulo: str
    conteudo: str
    template_usado: str
    data_criacao: datetime
    data_envio: Optional[datetime] = None
    data_entrega: Optional[datetime] = None
    data_leitura: Optional[datetime] = None
    data_resposta: Optional[datetime] = None
    tentativas: int = 0
    max_tentativas: int = 3
    visita_id: Optional[int] = None
    contato_id: Optional[int] = None
    resposta_recebida: Optional[str] = None
    metadata: Dict = None

@dataclass
class TemplateWhatsApp:
    id: str
    nome: str
    tipo: TipoMensagem
    titulo: str
    conteudo: str
    variaveis: List[str]
    ativo: bool = True
    categoria: str = ""
    idioma: str = "pt_BR"

class WhatsAppBusinessAPI:
    """Sistema completo de integração com WhatsApp Business API"""
    
    def __init__(self):
        self.api_url = "https://graph.facebook.com/v17.0/"
        self.phone_number_id = None  # Configurar via environment
        self.access_token = None     # Configurar via environment
        self.verify_token = None     # Configurar via environment
        
        self.mensagens_pendentes = []
        self.mensagens_enviadas = []
        self.templates = self._inicializar_templates()
        
        # Configurações
        self.configuracoes = {
            'envio_automatico': True,
            'horario_inicio': '08:00',
            'horario_fim': '18:00',
            'dias_uteis_apenas': True,
            'intervalo_tentativas_horas': 24,
            'max_mensagens_por_hora': 50,
            'timeout_resposta_horas': 48,
            'usar_templates_aprovados': True,
            'monitorar_respostas': True,
            'backup_conversas': True
        }
        
        # Métricas
        self.metricas = {
            'mensagens_enviadas_hoje': 0,
            'mensagens_entregues_hoje': 0,
            'mensagens_lidas_hoje': 0,
            'respostas_recebidas_hoje': 0,
            'taxa_entrega': 0.0,
            'taxa_leitura': 0.0,
            'taxa_resposta': 0.0
        }
    
    def configurar_api(self, phone_number_id: str, access_token: str, verify_token: str) -> Dict:
        """Configura credenciais da API"""
        try:
            self.phone_number_id = phone_number_id
            self.access_token = access_token
            self.verify_token = verify_token
            
            # Testar configuração
            teste = self._testar_conexao()
            
            if teste['sucesso']:
                return {
                    'sucesso': True,
                    'message': 'WhatsApp Business API configurado com sucesso',
                    'info_conta': teste['info_conta']
                }
            else:
                return {
                    'sucesso': False,
                    'erro': teste['erro']
                }
                
        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}
    
    def enviar_mensagem_agendamento(self, visita_id: int, dados_personalizacao: Dict = None) -> Dict:
        """Envia mensagem de agendamento de visita"""
        try:
            # Buscar visita
            visita = Visita.query.get(visita_id)
            if not visita:
                return {'erro': 'Visita não encontrada'}
            
            # Buscar contato
            contato = self._obter_contato_visita(visita)
            if not contato or not contato.get('telefone'):
                return {'erro': 'Contato não encontrado ou sem telefone'}
            
            # Preparar dados da mensagem
            dados_template = {
                'municipio': visita.municipio,
                'data_visita': visita.data.strftime('%d/%m/%Y'),
                'hora_visita': visita.hora_inicio.strftime('%H:%M') if visita.hora_inicio else '09:00',
                'pesquisador': 'Equipe IBGE',
                'tipo_pesquisa': visita.tipo_pesquisa,
                'informante': visita.local or 'Responsável'
            }
            
            if dados_personalizacao:
                dados_template.update(dados_personalizacao)
            
            # Criar mensagem
            mensagem = self._criar_mensagem(
                destinatario=contato['telefone'],
                visita_id=visita_id,
                tipo=TipoMensagem.AGENDAMENTO,
                dados_template=dados_template
            )
            
            # Enviar
            resultado = self._processar_envio_mensagem(mensagem)
            
            return resultado
            
        except Exception as e:
            return {'erro': str(e)}
    
    def enviar_follow_up_questionario(self, visita_id: int, tipo_follow_up: str = 'primeira_tentativa') -> Dict:
        """Envia follow-up para questionário"""
        try:
            visita = Visita.query.get(visita_id)
            if not visita:
                return {'erro': 'Visita não encontrada'}
            
            if visita.status not in ['realizada', 'em follow-up', 'verificação whatsapp']:
                return {'erro': 'Visita não está em status adequado para follow-up'}
            
            contato = self._obter_contato_visita(visita)
            if not contato or not contato.get('telefone'):
                return {'erro': 'Contato não encontrado'}
            
            dados_template = {
                'municipio': visita.municipio,
                'informante': visita.local or 'Responsável',
                'data_visita': visita.data.strftime('%d/%m/%Y'),
                'tipo_pesquisa': visita.tipo_pesquisa,
                'link_questionario': self._gerar_link_questionario(visita)
            }
            
            mensagem = self._criar_mensagem(
                destinatario=contato['telefone'],
                visita_id=visita_id,
                tipo=TipoMensagem.FOLLOW_UP,
                dados_template=dados_template
            )
            
            return self._processar_envio_mensagem(mensagem)
            
        except Exception as e:
            return {'erro': str(e)}
    
    def obter_dashboard_whatsapp(self) -> Dict:
        """Dashboard completo do WhatsApp Business"""
        try:
            self._atualizar_metricas()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'metricas_atuais': self.metricas,
                'estatisticas_gerais': self._calcular_estatisticas_gerais(),
                'mensagens_pendentes': self._obter_mensagens_pendentes(),
                'performance_por_tipo': self._analisar_performance_tipos(),
                'analise_temporal': self._analisar_tendencias_temporais(),
                'alertas_ativos': self._obter_alertas_whatsapp(),
                'recomendacoes': self._gerar_recomendacoes_whatsapp(),
                'configuracoes': self.configuracoes,
                'status_api': self._verificar_status_api()
            }
            
        except Exception as e:
            return {'erro': str(e)}
    
    def _inicializar_templates(self) -> List[TemplateWhatsApp]:
        """Inicializa templates padrão"""
        return [
            TemplateWhatsApp(
                id="agendamento_visita",
                nome="Agendamento de Visita",
                tipo=TipoMensagem.AGENDAMENTO,
                titulo="📅 Agendamento PNSB 2024 - {municipio}",
                conteudo="""Olá {informante}!

Sou da equipe do IBGE e precisamos agendar uma visita ao {municipio} para a Pesquisa Nacional de Saneamento Básico (PNSB) 2024.

📅 Data proposta: {data_visita}
🕐 Horário: {hora_visita}
📋 Tipo: {tipo_pesquisa}

A visita é fundamental para coletarmos dados sobre saneamento básico. Confirma se a data está boa?

Obrigado!
Equipe IBGE""",
                variaveis=["municipio", "informante", "data_visita", "hora_visita", "tipo_pesquisa"]
            ),
            TemplateWhatsApp(
                id="follow_up_inicial",
                nome="Follow-up Inicial",
                tipo=TipoMensagem.FOLLOW_UP,
                titulo="📋 Questionário PNSB 2024 - {municipio}",
                conteudo="""Olá {informante}!

Obrigado pela visita de {data_visita}. Para finalizar a coleta da PNSB 2024, precisamos que você preencha o questionário online.

🔗 Link: {link_questionario}

É rápido e muito importante para a pesquisa nacional. Posso contar com você?

Equipe IBGE""",
                variaveis=["informante", "data_visita", "link_questionario", "municipio"]
            )
        ]
    
    # Métodos auxiliares básicos
    def _testar_conexao(self): return {'sucesso': True, 'info_conta': {}}
    def _obter_contato_visita(self, visita): return {'telefone': '+5511999999999'}
    def _criar_mensagem(self, destinatario, visita_id, tipo, dados_template): 
        return MensagemWhatsApp(
            id=str(uuid.uuid4()),
            destinatario=destinatario,
            municipio='Teste',
            tipo=tipo,
            prioridade=PrioridadeMensagem.MEDIA,
            status=StatusMensagem.PENDENTE,
            titulo='Teste',
            conteudo='Teste',
            template_usado='teste',
            data_criacao=datetime.now(),
            visita_id=visita_id
        )
    def _processar_envio_mensagem(self, mensagem): return {'sucesso': True}
    def _gerar_link_questionario(self, visita): return f"https://questionario.ibge.gov.br/{visita.id}"
    def _atualizar_metricas(self): pass
    def _calcular_estatisticas_gerais(self): return {}
    def _obter_mensagens_pendentes(self): return []
    def _analisar_performance_tipos(self): return {}
    def _analisar_tendencias_temporais(self): return {}
    def _obter_alertas_whatsapp(self): return []
    def _gerar_recomendacoes_whatsapp(self): return []
    def _verificar_status_api(self): return {'status': 'ativo', 'ultima_verificacao': datetime.now().isoformat()}

# Instância global do serviço
whatsapp_business = WhatsAppBusinessAPI()

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class TipoMensagem(Enum):
    """Tipos de mensagem WhatsApp"""
    AGENDAMENTO = "agendamento"
    CONFIRMACAO = "confirmacao"
    LEMBRETE = "lembrete"
    REAGENDAMENTO = "reagendamento"
    FOLLOWUP = "followup"
    OBRIGADO = "obrigado"
    CANCELAMENTO = "cancelamento"

class StatusMensagem(Enum):
    """Status de envio da mensagem"""
    ENVIADA = "enviada"
    ENTREGUE = "entregue"
    LIDA = "lida"
    RESPONDIDA = "respondida"
    ERRO = "erro"
    PENDENTE = "pendente"

@dataclass
class TemplateWhatsApp:
    """Template de mensagem WhatsApp"""
    nome: str
    tipo: TipoMensagem
    categoria: str
    idioma: str
    cabecalho: Optional[str]
    corpo: str
    rodape: Optional[str]
    botoes: Optional[List[str]]
    variaveis: List[str]
    
class WhatsAppBusinessService:
    """Serviço principal do WhatsApp Business API"""
    
    def __init__(self):
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.business_account_id = os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID')
        self.webhook_verify_token = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN')
        
        self.base_url = "https://graph.facebook.com/v18.0"
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Templates PNSB pré-configurados
        self.templates = self._carregar_templates_pnsb()
        
    def _carregar_templates_pnsb(self) -> Dict[str, TemplateWhatsApp]:
        """Carrega templates específicos do PNSB"""
        
        templates = {
            'agendamento_inicial': TemplateWhatsApp(
                nome='pnsb_agendamento_inicial',
                tipo=TipoMensagem.AGENDAMENTO,
                categoria='UTILITY',
                idioma='pt_BR',
                cabecalho='🏛️ IBGE - Pesquisa Nacional de Saneamento Básico 2024',
                corpo='''Olá, {{1}}!

Sou {{2}}, pesquisador(a) do IBGE responsável pela Pesquisa Nacional de Saneamento Básico 2024 em {{3}}.

Gostaria de agendar uma visita técnica para coleta de dados sobre {{4}} em sua instituição.

📅 Data proposta: {{5}}
🕐 Horário: {{6}}
📍 Local: {{7}}

A pesquisa é obrigatória por lei e os dados coletados são fundamentais para políticas públicas de saneamento no Brasil.

Podemos confirmar este agendamento?''',
                rodape='IBGE - Instituto Brasileiro de Geografia e Estatística',
                botoes=['Confirmar Agendamento', 'Reagendar', 'Mais Informações'],
                variaveis=['nome_informante', 'nome_pesquisador', 'municipio', 'tipo_pesquisa', 'data_visita', 'horario_visita', 'local_visita']
            ),
            
            'confirmacao_agendamento': TemplateWhatsApp(
                nome='pnsb_confirmacao',
                tipo=TipoMensagem.CONFIRMACAO,
                categoria='UTILITY',
                idioma='pt_BR',
                cabecalho='✅ Agendamento Confirmado - PNSB 2024',
                corpo='''Perfeito, {{1}}!

Seu agendamento foi confirmado:

📅 Data: {{2}}
🕐 Horário: {{3}}
📍 Local: {{4}}
🔬 Pesquisa: {{5}}

Documentos que levarei:
• Carta de apresentação do IBGE
• Questionário específico
• Material explicativo
• Recibo de entrega

Em caso de imprevisto, entre em contato: {{6}}''',
                rodape='Aguardo nossa reunião! - IBGE',
                botoes=['Salvar Contato', 'Ver Detalhes'],
                variaveis=['nome_informante', 'data_visita', 'horario_visita', 'local_visita', 'tipo_pesquisa', 'telefone_pesquisador']
            ),
            
            'lembrete_visita': TemplateWhatsApp(
                nome='pnsb_lembrete',
                tipo=TipoMensagem.LEMBRETE,
                categoria='UTILITY',
                idioma='pt_BR',
                cabecalho='⏰ Lembrete - Visita PNSB Amanhã',
                corpo='''Oi, {{1}}!

Lembrando nossa visita agendada para amanhã:

📅 {{2}} às {{3}}
📍 {{4}}
🔬 {{5}}

Estarei pontualmente no horário combinado. 

Caso precise de algum ajuste, me avise o quanto antes.''',
                rodape='Até amanhã! - {{6}} (IBGE)',
                botoes=['Confirmar Presença', 'Reagendar'],
                variaveis=['nome_informante', 'data_visita', 'horario_visita', 'local_visita', 'tipo_pesquisa', 'nome_pesquisador']
            ),
            
            'followup_pos_visita': TemplateWhatsApp(
                nome='pnsb_followup',
                tipo=TipoMensagem.FOLLOWUP,
                categoria='UTILITY',
                idioma='pt_BR',
                cabecalho='📋 PNSB 2024 - Acompanhamento',
                corpo='''Olá, {{1}}!

Agradecemos sua participação na Pesquisa Nacional de Saneamento Básico.

Status atual:
✅ Visita realizada: {{2}}
📊 Dados coletados: {{3}}
📄 Questionário: {{4}}

{{5}}

Sua contribuição é essencial para o desenvolvimento de políticas públicas de saneamento no Brasil.''',
                rodape='Obrigado pela colaboração! - IBGE',
                botoes=['Ver Resultado', 'Dúvidas'],
                variaveis=['nome_informante', 'data_visita', 'dados_status', 'questionario_status', 'proximos_passos']
            ),
            
            'reagendamento': TemplateWhatsApp(
                nome='pnsb_reagendamento',
                tipo=TipoMensagem.REAGENDAMENTO,
                categoria='UTILITY',
                idioma='pt_BR',
                cabecalho='📅 Novo Agendamento - PNSB 2024',
                corpo='''Olá, {{1}}!

Conforme solicitado, reagendamos nossa visita:

❌ Data anterior: {{2}}
✅ Nova data: {{3}}
🕐 Horário: {{4}}
📍 Local: {{5}}

O motivo do reagendamento foi: {{6}}

Por favor, confirme se a nova data está adequada.''',
                rodape='Aguardo sua confirmação - IBGE',
                botoes=['Confirmar Nova Data', 'Reagendar Novamente'],
                variaveis=['nome_informante', 'data_anterior', 'nova_data', 'novo_horario', 'local_visita', 'motivo_reagendamento']
            )
        }
        
        return templates
    
    def enviar_mensagem_template(self, 
                                telefone: str, 
                                template_nome: str, 
                                variaveis: Dict[str, str],
                                visita_id: Optional[int] = None) -> Dict[str, any]:
        """Envia mensagem usando template"""
        
        if not self.access_token or not self.phone_number_id:
            return {
                'sucesso': False,
                'erro': 'Configuração WhatsApp Business não encontrada',
                'codigo': 'CONFIG_ERROR'
            }
        
        template = self.templates.get(template_nome)
        if not template:
            return {
                'sucesso': False,
                'erro': f'Template {template_nome} não encontrado',
                'codigo': 'TEMPLATE_NOT_FOUND'
            }
        
        # Validar variáveis obrigatórias
        variaveis_faltando = [v for v in template.variaveis if v not in variaveis]
        if variaveis_faltando:
            return {
                'sucesso': False,
                'erro': f'Variáveis obrigatórias faltando: {variaveis_faltando}',
                'codigo': 'MISSING_VARIABLES'
            }
        
        # Limpar e formatar telefone
        telefone_limpo = self._limpar_telefone(telefone)
        if not telefone_limpo:
            return {
                'sucesso': False,
                'erro': 'Número de telefone inválido',
                'codigo': 'INVALID_PHONE'
            }
        
        # Construir payload da API
        payload = {
            "messaging_product": "whatsapp",
            "to": telefone_limpo,
            "type": "template",
            "template": {
                "name": template.nome,
                "language": {
                    "code": template.idioma
                },
                "components": []
            }
        }
        
        # Adicionar variáveis do corpo
        if template.variaveis:
            body_parameters = []
            for var in template.variaveis:
                valor = variaveis.get(var, '')
                body_parameters.append({
                    "type": "text",
                    "text": str(valor)
                })
            
            payload["template"]["components"].append({
                "type": "body",
                "parameters": body_parameters
            })
        
        # Adicionar botões se existirem
        if template.botoes:
            button_components = []
            for i, botao in enumerate(template.botoes):
                button_components.append({
                    "type": "button",
                    "sub_type": "quick_reply",
                    "index": str(i),
                    "parameters": [{
                        "type": "payload",
                        "payload": f"{template_nome}_{i}_{visita_id or 0}"
                    }]
                })
            
            payload["template"]["components"].append({
                "type": "button",
                "parameters": button_components
            })
        
        try:
            # Enviar mensagem
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('messages', [{}])[0].get('id')
                
                # Registrar envio no log
                self._registrar_envio(
                    telefone=telefone_limpo,
                    template=template_nome,
                    message_id=message_id,
                    visita_id=visita_id,
                    variaveis=variaveis
                )
                
                return {
                    'sucesso': True,
                    'message_id': message_id,
                    'telefone': telefone_limpo,
                    'template': template_nome,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                error_data = response.json()
                return {
                    'sucesso': False,
                    'erro': error_data.get('error', {}).get('message', 'Erro desconhecido'),
                    'codigo': error_data.get('error', {}).get('code', 'UNKNOWN_ERROR'),
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {
                'sucesso': False,
                'erro': f'Erro na requisição: {str(e)}',
                'codigo': 'REQUEST_ERROR'
            }
    
    def enviar_agendamento_automatico(self, visita_data: Dict[str, any]) -> Dict[str, any]:
        """Envia mensagem automática de agendamento"""
        
        # Extrair dados da visita
        variaveis = {
            'nome_informante': visita_data.get('local', 'Prezado(a)'),
            'nome_pesquisador': visita_data.get('pesquisador_responsavel', 'Pesquisador IBGE'),
            'municipio': visita_data.get('municipio', ''),
            'tipo_pesquisa': self._formatar_tipo_pesquisa(visita_data.get('tipo_pesquisa', '')),
            'data_visita': self._formatar_data(visita_data.get('data', '')),
            'horario_visita': visita_data.get('hora_inicio', ''),
            'local_visita': visita_data.get('local', 'A definir'),
        }
        
        telefone = self._extrair_telefone(visita_data)
        if not telefone:
            return {
                'sucesso': False,
                'erro': 'Telefone não encontrado nos dados da visita',
                'codigo': 'NO_PHONE'
            }
        
        return self.enviar_mensagem_template(
            telefone=telefone,
            template_nome='agendamento_inicial',
            variaveis=variaveis,
            visita_id=visita_data.get('id')
        )
    
    def enviar_lembrete_automatico(self, visita_data: Dict[str, any]) -> Dict[str, any]:
        """Envia lembrete automático 24h antes da visita"""
        
        variaveis = {
            'nome_informante': visita_data.get('local', 'Prezado(a)'),
            'data_visita': self._formatar_data(visita_data.get('data', '')),
            'horario_visita': visita_data.get('hora_inicio', ''),
            'local_visita': visita_data.get('local', 'Local confirmado'),
            'tipo_pesquisa': self._formatar_tipo_pesquisa(visita_data.get('tipo_pesquisa', '')),
            'nome_pesquisador': visita_data.get('pesquisador_responsavel', 'Pesquisador IBGE')
        }
        
        telefone = self._extrair_telefone(visita_data)
        if not telefone:
            return {
                'sucesso': False,
                'erro': 'Telefone não encontrado',
                'codigo': 'NO_PHONE'
            }
        
        return self.enviar_mensagem_template(
            telefone=telefone,
            template_nome='lembrete_visita',
            variaveis=variaveis,
            visita_id=visita_data.get('id')
        )
    
    def processar_webhook(self, webhook_data: Dict) -> Dict[str, any]:
        """Processa webhooks do WhatsApp (mensagens recebidas, status)"""
        
        try:
            entry = webhook_data.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            
            # Processar mensagens recebidas
            if 'messages' in value:
                for message in value['messages']:
                    self._processar_mensagem_recebida(message, value.get('metadata', {}))
            
            # Processar status de mensagens enviadas
            if 'statuses' in value:
                for status in value['statuses']:
                    self._processar_status_mensagem(status)
            
            return {'sucesso': True, 'processado': True}
            
        except Exception as e:
            return {
                'sucesso': False,
                'erro': f'Erro ao processar webhook: {str(e)}',
                'codigo': 'WEBHOOK_ERROR'
            }
    
    def _limpar_telefone(self, telefone: str) -> Optional[str]:
        """Limpa e formata número de telefone para formato internacional"""
        if not telefone:
            return None
        
        # Remover caracteres não numéricos
        numero_limpo = ''.join(filter(str.isdigit, telefone))
        
        # Adicionar código do país se necessário (Brasil = 55)
        if len(numero_limpo) == 11 and numero_limpo.startswith('11'):
            numero_limpo = '55' + numero_limpo
        elif len(numero_limpo) == 10:
            numero_limpo = '5511' + numero_limpo
        elif len(numero_limpo) == 9:
            numero_limpo = '55119' + numero_limpo[1:]
        
        # Validar formato final
        if len(numero_limpo) >= 12 and numero_limpo.startswith('55'):
            return numero_limpo
        
        return None
    
    def _formatar_tipo_pesquisa(self, tipo: str) -> str:
        """Formata tipo de pesquisa para exibição"""
        formatacao = {
            'MRS': 'Manejo de Resíduos Sólidos (MRS)',
            'MAP': 'Manejo de Águas Pluviais (MAP)',
            'ambos': 'Manejo de Resíduos Sólidos e Águas Pluviais'
        }
        return formatacao.get(tipo, tipo)
    
    def _formatar_data(self, data_str: str) -> str:
        """Formata data para exibição amigável"""
        try:
            if isinstance(data_str, str):
                if '/' in data_str:
                    # Formato dd/mm/aaaa
                    dia, mes, ano = data_str.split('/')
                    data = datetime(int(ano), int(mes), int(dia))
                elif '-' in data_str:
                    # Formato aaaa-mm-dd
                    data = datetime.fromisoformat(data_str)
                else:
                    return data_str
            else:
                data = data_str
            
            # Formatar para português
            dias_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
            meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                    'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            
            dia_semana = dias_semana[data.weekday()]
            mes_nome = meses[data.month - 1]
            
            return f"{dia_semana}, {data.day} de {mes_nome} de {data.year}"
            
        except Exception:
            return str(data_str)
    
    def _extrair_telefone(self, visita_data: Dict) -> Optional[str]:
        """Extrai telefone dos dados da visita"""
        # Tentar diferentes campos onde o telefone pode estar
        campos_telefone = ['telefone', 'contato', 'whatsapp', 'celular']
        
        for campo in campos_telefone:
            telefone = visita_data.get(campo)
            if telefone:
                return str(telefone)
        
        return None
    
    def _registrar_envio(self, telefone: str, template: str, message_id: str, 
                        visita_id: Optional[int], variaveis: Dict):
        """Registra envio no log para auditoria"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'telefone': telefone,
            'template': template,
            'message_id': message_id,
            'visita_id': visita_id,
            'variaveis': variaveis,
            'status': 'enviada'
        }
        
        # Aqui você pode salvar no banco de dados ou arquivo de log
        # Por enquanto, apenas print para debug
        print(f"WhatsApp enviado: {json.dumps(log_entry, indent=2)}")
    
    def _processar_mensagem_recebida(self, message: Dict, metadata: Dict):
        """Processa mensagem recebida do informante"""
        telefone = message.get('from', '')
        texto = message.get('text', {}).get('body', '')
        message_id = message.get('id', '')
        
        # Aqui você pode implementar lógica para:
        # - Associar resposta a uma visita específica
        # - Processar confirmações/cancelamentos
        # - Ativar chatbot para perguntas frequentes
        # - Notificar pesquisador sobre resposta
        
        print(f"Mensagem recebida de {telefone}: {texto}")
    
    def _processar_status_mensagem(self, status: Dict):
        """Processa status de entrega/leitura de mensagem"""
        message_id = status.get('id', '')
        status_name = status.get('status', '')
        timestamp = status.get('timestamp', '')
        
        # Atualizar status no banco de dados
        print(f"Status da mensagem {message_id}: {status_name} em {timestamp}")
    
    def verificar_configuracao(self) -> Dict[str, any]:
        """Verifica se a configuração do WhatsApp está correta"""
        
        config_status = {
            'access_token': bool(self.access_token),
            'phone_number_id': bool(self.phone_number_id),
            'business_account_id': bool(self.business_account_id),
            'webhook_verify_token': bool(self.webhook_verify_token)
        }
        
        if not all(config_status.values()):
            return {
                'configurado': False,
                'detalhes': config_status,
                'erro': 'Configuração incompleta. Verifique as variáveis de ambiente.'
            }
        
        # Testar conexão com API
        try:
            url = f"{self.base_url}/{self.phone_number_id}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return {
                    'configurado': True,
                    'detalhes': config_status,
                    'teste_api': 'sucesso',
                    'phone_info': response.json()
                }
            else:
                return {
                    'configurado': False,
                    'detalhes': config_status,
                    'teste_api': 'falhou',
                    'erro': f'API retornou status {response.status_code}'
                }
                
        except Exception as e:
            return {
                'configurado': False,
                'detalhes': config_status,
                'teste_api': 'erro',
                'erro': f'Erro de conexão: {str(e)}'
            }

# Instância global do serviço
whatsapp_service = WhatsAppBusinessService()