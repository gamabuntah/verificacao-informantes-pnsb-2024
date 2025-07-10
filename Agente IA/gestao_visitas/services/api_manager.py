"""
Gerenciador centralizado das APIs externas do projeto PNSB
Gerencia Google Maps, Gemini AI e outras integrações
"""

import os
import requests
import logging
from typing import Optional, Dict, Any
from ..config.security import SecurityConfig

logger = logging.getLogger(__name__)

class APIManager:
    """Gerenciador centralizado de APIs externas"""
    
    def __init__(self):
        self.google_maps_key = SecurityConfig.get_google_maps_key()
        self.google_gemini_key = SecurityConfig.get_google_gemini_key()
        
        # Status das APIs
        self._apis_status = {
            'google_maps': False,
            'google_gemini': False
        }
        
        # Verificar disponibilidade das APIs
        self._check_apis_availability()
    
    def _check_apis_availability(self):
        """Verifica se as APIs estão disponíveis e configuradas"""
        
        # Verificar Google Maps
        if self.google_maps_key and self.google_maps_key != 'your_google_maps_api_key_here':
            try:
                # Teste rápido da API
                import googlemaps
                client = googlemaps.Client(key=self.google_maps_key)
                # Fazer uma requisição simples para testar
                result = client.geocode("Itajaí, SC, Brasil")
                if result:
                    self._apis_status['google_maps'] = True
                    logger.info("✅ Google Maps API disponível")
                else:
                    logger.warning("⚠️ Google Maps API configurada mas não funcionando")
            except Exception as e:
                logger.warning(f"⚠️ Google Maps API não disponível: {e}")
        else:
            logger.info("📋 Google Maps API não configurada")
        
        # Verificar Google Gemini
        if self.google_gemini_key and self.google_gemini_key != 'your_google_gemini_api_key_here':
            try:
                # Teste rápido da API
                url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.google_gemini_key}"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    self._apis_status['google_gemini'] = True
                    logger.info("✅ Google Gemini API disponível")
                else:
                    logger.warning("⚠️ Google Gemini API configurada mas não funcionando")
            except Exception as e:
                logger.warning(f"⚠️ Google Gemini API não disponível: {e}")
        else:
            logger.info("📋 Google Gemini API não configurada")
    
    def get_apis_status(self) -> Dict[str, bool]:
        """Retorna status atual das APIs"""
        return self._apis_status.copy()
    
    def is_google_maps_available(self) -> bool:
        """Verifica se Google Maps está disponível"""
        return self._apis_status['google_maps']
    
    def is_google_gemini_available(self) -> bool:
        """Verifica se Google Gemini está disponível"""
        return self._apis_status['google_gemini']
    
    def get_maps_client(self):
        """Retorna cliente do Google Maps ou None se não disponível"""
        if not self.is_google_maps_available():
            return None
        
        try:
            import googlemaps
            return googlemaps.Client(key=self.google_maps_key)
        except Exception as e:
            logger.error(f"Erro ao criar cliente Google Maps: {e}")
            return None
    
    def send_gemini_request(self, message: str, model: str = "gemini-1.5-flash-latest") -> Optional[str]:
        """Envia requisição para o Gemini AI"""
        if not self.is_google_gemini_available():
            return None
        
        try:
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": message}]}
                ]
            }
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.google_gemini_key}"
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                logger.error("Resposta do Gemini sem candidatos válidos")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Erro na requisição Gemini: {e}")
            return None
        except KeyError as e:
            logger.error(f"Erro no formato da resposta Gemini: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado no Gemini: {e}")
            return None
    
    def calculate_route(self, origin: str, destination: str) -> Dict[str, Any]:
        """Calcula rota usando Google Maps com fallback"""
        if not self.is_google_maps_available():
            return {
                'erro': 'Serviço de mapas não disponível',
                'fallback': True,
                'message': 'Configure a chave do Google Maps para cálculos de rota'
            }
        
        try:
            client = self.get_maps_client()
            if not client:
                return {'erro': 'Cliente Google Maps não disponível'}
            
            directions_result = client.directions(
                origin,
                destination,
                mode="driving"
            )
            
            if directions_result:
                route = directions_result[0]
                leg = route['legs'][0]
                
                return {
                    'success': True,
                    'distancia': leg['distance']['text'],
                    'duracao': leg['duration']['text'],
                    'distancia_metros': leg['distance']['value'],
                    'duracao_segundos': leg['duration']['value'],
                    'passos': [step['html_instructions'] for step in leg['steps']],
                    'overview_polyline': route['overview_polyline']['points']
                }
            else:
                return {'erro': 'Rota não encontrada'}
                
        except Exception as e:
            logger.error(f"Erro ao calcular rota: {e}")
            return {'erro': f'Erro no cálculo da rota: {str(e)}'}
    
    def estimate_travel_time(self, origin: str, destination: str) -> Dict[str, Any]:
        """Estima tempo de viagem com fallback"""
        if not self.is_google_maps_available():
            return {
                'erro': 'Serviço de estimativa não disponível',
                'fallback': True,
                'estimativa_aproximada': '30-60 minutos (estimativa padrão)',
                'message': 'Configure a chave do Google Maps para estimativas precisas'
            }
        
        try:
            client = self.get_maps_client()
            if not client:
                return {'erro': 'Cliente Google Maps não disponível'}
            
            matrix = client.distance_matrix(
                origin,
                destination,
                mode="driving"
            )
            
            if matrix['status'] == 'OK':
                element = matrix['rows'][0]['elements'][0]
                if element['status'] == 'OK':
                    return {
                        'success': True,
                        'distancia': element['distance']['text'],
                        'duracao': element['duration']['text'],
                        'distancia_metros': element['distance']['value'],
                        'duracao_segundos': element['duration']['value']
                    }
            
            return {'erro': 'Não foi possível estimar o tempo'}
            
        except Exception as e:
            logger.error(f"Erro ao estimar tempo: {e}")
            return {'erro': f'Erro na estimativa: {str(e)}'}
    
    def chat_with_ai(self, message: str, context: str = None) -> Dict[str, Any]:
        """Chat com IA com fallback para respostas padrão"""
        if not self.is_google_gemini_available():
            return {
                'success': False,
                'fallback': True,
                'response': self._get_fallback_response(message),
                'message': 'IA não disponível - resposta padrão fornecida'
            }
        
        # Preparar mensagem com contexto se fornecido
        full_message = message
        if context:
            full_message = f"Contexto: {context}\n\nPergunta: {message}"
        
        ai_response = self.send_gemini_request(full_message)
        
        if ai_response:
            return {
                'success': True,
                'response': ai_response,
                'source': 'gemini_ai'
            }
        else:
            return {
                'success': False,
                'fallback': True,
                'response': self._get_fallback_response(message),
                'message': 'Erro na IA - resposta padrão fornecida'
            }
    
    def _get_fallback_response(self, message: str) -> str:
        """Gera resposta padrão quando IA não está disponível"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['olá', 'oi', 'bom dia', 'boa tarde', 'boa noite']):
            return "Olá! Sou o assistente do sistema PNSB. Como posso ajudá-lo com suas visitas de pesquisa?"
        
        elif any(word in message_lower for word in ['rota', 'caminho', 'direção']):
            return "Para calcular rotas precisas, é necessário configurar a API do Google Maps. Por enquanto, recomendo usar aplicativos de navegação externos."
        
        elif any(word in message_lower for word in ['visita', 'agendamento', 'pesquisa']):
            return "Posso ajudá-lo com o gerenciamento de visitas. Use o sistema para criar, editar e acompanhar suas visitas de pesquisa PNSB."
        
        elif any(word in message_lower for word in ['contato', 'informante']):
            return "Para gerenciar contatos de informantes, use a seção de contatos do sistema. Lá você pode visualizar e filtrar todas as informações dos municípios."
        
        elif any(word in message_lower for word in ['ajuda', 'help', 'socorro']):
            return "Estou aqui para ajudar! Você pode perguntar sobre visitas, contatos, rotas ou qualquer funcionalidade do sistema PNSB."
        
        else:
            return "Desculpe, não posso processar sua solicitação no momento. Por favor, configure as APIs do Google para funcionalidades completas ou reformule sua pergunta."
    
    def get_system_status(self) -> Dict[str, Any]:
        """Retorna status completo do sistema de APIs"""
        return {
            'google_maps': {
                'available': self.is_google_maps_available(),
                'configured': bool(self.google_maps_key and self.google_maps_key != 'your_google_maps_api_key_here'),
                'features': ['Cálculo de rotas', 'Estimativa de tempo', 'Geocodificação']
            },
            'google_gemini': {
                'available': self.is_google_gemini_available(),
                'configured': bool(self.google_gemini_key and self.google_gemini_key != 'your_google_gemini_api_key_here'),
                'features': ['Chat inteligente', 'Assistente de abordagem', 'Análise de dados']
            },
            'fallback_enabled': True,
            'system_operational': True
        }

# Instância global do gerenciador
api_manager = APIManager()