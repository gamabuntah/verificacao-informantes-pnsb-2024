"""
Serviço de Verificação por WhatsApp
==================================

Gerencia a verificação se o responsável recebeu o e-mail com instruções
do sistema IBGE antes de entrar em follow-up.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os

class VerificacaoWhatsAppService:
    """Serviço para verificar recebimento de e-mail via WhatsApp."""
    
    def __init__(self):
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '472473086265676')
        self.api_version = 'v21.0'
        self.base_url = f'https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages'
        
        # Templates de mensagens
        self.templates = {
            'verificacao_email': {
                'primeira_tentativa': """🏛️ *IBGE - PNSB 2024*

Olá! Sou da equipe do IBGE responsável pela Pesquisa Nacional de Saneamento Básico.

Enviamos recentemente um e-mail com instruções para preenchimento do questionário da pesquisa para o município de *{municipio}*.

✉️ Você recebeu nosso e-mail com as instruções?

Por favor, responda:
• *SIM* - se recebeu o e-mail
• *NÃO* - se não recebeu

Isso nos ajuda a garantir que todas as informações cheguem até vocês! 📋""",
                
                'segunda_tentativa': """🏛️ *IBGE - PNSB 2024*

Olá novamente! 

Estamos verificando se você recebeu nosso e-mail com as instruções do questionário PNSB para *{municipio}*.

Caso não tenha recebido, podemos reenviar ou fornecer as instruções por outro meio.

✉️ Confirma o recebimento do e-mail?
• *SIM* - recebi
• *NÃO* - não recebi

Aguardamos seu retorno! 📞""",
                
                'confirmacao_sim': """✅ *Ótimo!*

Obrigado por confirmar o recebimento do e-mail.

Agora daremos continuidade ao acompanhamento do preenchimento do questionário.

Em breve entraremos em contato para verificar o andamento.

*IBGE - PNSB 2024* 🏛️""",
                
                'confirmacao_nao': """📧 *Sem problemas!*

Vamos providenciar o reenvio do e-mail com as instruções.

Também podemos fornecer as informações por WhatsApp se preferir.

Entraremos em contato em breve com as instruções.

*IBGE - PNSB 2024* 🏛️""",
                
                'timeout': """⏰ *IBGE - PNSB 2024*

Como não recebemos resposta sobre o e-mail com instruções para *{municipio}*, assumiremos que você recebeu e daremos continuidade ao processo.

Caso tenha alguma dúvida, entre em contato conosco.

Obrigado! 🏛️"""
            }
        }
    
    def pode_enviar_verificacao(self, visita) -> Tuple[bool, str]:
        """Verifica se pode enviar verificação por WhatsApp."""
        if not self.access_token:
            return False, "WhatsApp não configurado"
            
        if not visita.telefone_responsavel:
            return False, "Telefone do responsável não cadastrado"
            
        if not visita.email_enviado_em:
            return False, "E-mail ainda não foi enviado pelo IBGE"
            
        # Verificar se já passou tempo mínimo desde envio do e-mail (ex: 2 horas)
        tempo_minimo = timedelta(hours=2)
        if datetime.now() - visita.email_enviado_em < tempo_minimo:
            return False, f"Aguarde {tempo_minimo} após envio do e-mail"
            
        # Verificar se não enviou verificação recentemente (evitar spam)
        if visita.whatsapp_verificacao_enviado:
            ultimo_envio = visita.whatsapp_verificacao_enviado
            if datetime.now() - ultimo_envio < timedelta(hours=4):
                return False, "Verificação já enviada recentemente"
                
        return True, "Pode enviar verificação"
    
    def enviar_verificacao_email(self, visita) -> Tuple[bool, str]:
        """Envia verificação por WhatsApp se responsável recebeu e-mail."""
        pode_enviar, motivo = self.pode_enviar_verificacao(visita)
        if not pode_enviar:
            return False, motivo
            
        # Determinar qual template usar (primeira ou segunda tentativa)
        tentativa = 'primeira_tentativa'
        if visita.whatsapp_verificacao_enviado:
            tentativa = 'segunda_tentativa'
            
        # Formatar mensagem
        template = self.templates['verificacao_email'][tentativa]
        mensagem = template.format(municipio=visita.municipio)
        
        # Enviar WhatsApp
        sucesso, resultado = self._enviar_mensagem_whatsapp(
            visita.telefone_responsavel, 
            mensagem
        )
        
        if sucesso:
            # Atualizar visita
            visita.enviar_verificacao_whatsapp()
            return True, "Verificação enviada com sucesso"
        else:
            return False, f"Erro ao enviar: {resultado}"
    
    def processar_resposta_verificacao(self, telefone: str, mensagem: str) -> Dict:
        """Processa resposta do usuário sobre recebimento do e-mail."""
        # Normalizar resposta
        resposta_normalizada = mensagem.lower().strip()
        
        # Identificar se é SIM ou NÃO
        respostas_sim = ['sim', 's', 'yes', 'y', 'recebi', 'recebido', '✅', 'ok']
        respostas_nao = ['não', 'nao', 'n', 'no', 'não recebi', 'nao recebi', '❌']
        
        email_recebido = None
        resposta_reconhecida = False
        
        if any(r in resposta_normalizada for r in respostas_sim):
            email_recebido = True
            resposta_reconhecida = True
        elif any(r in resposta_normalizada for r in respostas_nao):
            email_recebido = False
            resposta_reconhecida = True
            
        return {
            'email_recebido': email_recebido,
            'resposta_reconhecida': resposta_reconhecida,
            'mensagem_original': mensagem,
            'telefone': telefone
        }
    
    def confirmar_recebimento_email(self, visita, email_recebido: bool) -> Tuple[bool, str]:
        """Confirma se o responsável recebeu o e-mail e envia resposta."""
        # Atualizar visita
        visita.confirmar_email_recebido(email_recebido)
        
        # Enviar mensagem de confirmação
        if email_recebido:
            template = self.templates['verificacao_email']['confirmacao_sim']
        else:
            template = self.templates['verificacao_email']['confirmacao_nao']
            
        sucesso, resultado = self._enviar_mensagem_whatsapp(
            visita.telefone_responsavel,
            template
        )
        
        if sucesso:
            status_msg = "recebeu" if email_recebido else "não recebeu"
            return True, f"Confirmação processada: responsável {status_msg} o e-mail"
        else:
            return False, f"Erro ao enviar confirmação: {resultado}"
    
    def processar_timeout_verificacao(self, visita) -> Tuple[bool, str]:
        """Processa timeout quando não há resposta à verificação."""
        # Assumir que recebeu e-mail (padrão otimista)
        visita.confirmar_email_recebido(True)
        
        # Enviar mensagem de timeout
        template = self.templates['verificacao_email']['timeout']
        mensagem = template.format(municipio=visita.municipio)
        
        sucesso, resultado = self._enviar_mensagem_whatsapp(
            visita.telefone_responsavel,
            mensagem
        )
        
        return sucesso, "Timeout processado - assumindo e-mail recebido"
    
    def _enviar_mensagem_whatsapp(self, telefone: str, mensagem: str) -> Tuple[bool, str]:
        """Envia mensagem via WhatsApp Business API."""
        if not self.access_token:
            return False, "WhatsApp não configurado"
            
        # Formatar telefone (remover caracteres especiais)
        telefone_limpo = ''.join(filter(str.isdigit, telefone))
        
        # Adicionar código do país se necessário
        if not telefone_limpo.startswith('55'):
            telefone_limpo = '55' + telefone_limpo
            
        payload = {
            "messaging_product": "whatsapp",
            "to": telefone_limpo,
            "type": "text",
            "text": {
                "body": mensagem
            }
        }
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(self.base_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                return True, "Mensagem enviada com sucesso"
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else response.text
                return False, f"Erro HTTP {response.status_code}: {error_data}"
                
        except Exception as e:
            return False, f"Erro na requisição: {str(e)}"
    
    def obter_visitas_para_verificacao(self) -> List:
        """Retorna visitas que precisam de verificação por WhatsApp."""
        from gestao_visitas.models.agendamento import Visita
        
        # Buscar visitas realizadas que podem precisar de verificação
        visitas_candidatas = Visita.query.filter(
            Visita.status.in_(['realizada', 'resultados visita'])
        ).all()
        
        visitas_para_verificacao = []
        
        for visita in visitas_candidatas:
            pode_verificar, motivo = self.pode_enviar_verificacao(visita)
            if pode_verificar:
                visitas_para_verificacao.append({
                    'visita': visita,
                    'motivo': 'Pronta para verificação'
                })
                
        return visitas_para_verificacao
    
    def obter_estatisticas_verificacao(self) -> Dict:
        """Retorna estatísticas das verificações por WhatsApp."""
        from gestao_visitas.models.agendamento import Visita
        
        total_visitas = Visita.query.count()
        
        com_telefone = Visita.query.filter(
            Visita.telefone_responsavel.isnot(None)
        ).count()
        
        email_enviado = Visita.query.filter(
            Visita.email_enviado_em.isnot(None)
        ).count()
        
        verificacao_enviada = Visita.query.filter(
            Visita.whatsapp_verificacao_enviado.isnot(None)
        ).count()
        
        resposta_recebida = Visita.query.filter(
            Visita.whatsapp_resposta_recebida.isnot(None)
        ).count()
        
        email_confirmado = Visita.query.filter(
            Visita.email_recebido_confirmado == True
        ).count()
        
        return {
            'total_visitas': total_visitas,
            'com_telefone': com_telefone,
            'email_enviado': email_enviado,
            'verificacao_enviada': verificacao_enviada,
            'resposta_recebida': resposta_recebida,
            'email_confirmado': email_confirmado,
            'taxa_resposta': (resposta_recebida / verificacao_enviada * 100) if verificacao_enviada > 0 else 0,
            'configurado': bool(self.access_token)
        }

# Instância global do serviço
verificacao_service = VerificacaoWhatsAppService()