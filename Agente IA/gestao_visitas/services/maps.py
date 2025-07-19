import googlemaps
from datetime import datetime, timedelta
import logging

class MapaService:
    def __init__(self, api_key):
        self.client = googlemaps.Client(key=api_key)
        self.logger = logging.getLogger(__name__)
    
    def calcular_rota(self, origem, destino, departure_time=None):
        """
        Calcula rota com trânsito em tempo real para PNSB 2024
        """
        try:
            # Usar departure_time fornecido ou atual
            if departure_time is None:
                departure_time = datetime.now()
            
            self.logger.info(f"🗺️ Calculando rota: {origem} → {destino}")
            
            directions_result = self.client.directions(
                origem,
                destino,
                mode="driving",
                departure_time=departure_time,
                traffic_model="best_guess",  # Modelo de trânsito
                # avoid=["tolls"]  # Removido temporariamente para evitar erro
            )
            
            if directions_result:
                rota = directions_result[0]
                leg = rota['legs'][0]
                
                # Extrair informações de trânsito
                duracao_normal = leg['duration']['value']  # segundos
                duracao_com_transito = leg.get('duration_in_traffic', {}).get('value', duracao_normal)
                
                # Calcular impacto do trânsito
                impacto_transito = duracao_com_transito - duracao_normal
                percentual_transito = (impacto_transito / duracao_normal) * 100 if duracao_normal > 0 else 0
                
                return {
                    'distancia': leg['distance']['text'],
                    'distancia_metros': leg['distance']['value'],
                    'duracao': leg['duration']['text'],
                    'duracao_segundos': duracao_normal,
                    'duracao_com_transito': self._seconds_to_text(duracao_com_transito),
                    'duracao_com_transito_segundos': duracao_com_transito,
                    'impacto_transito_minutos': round(impacto_transito / 60, 1),
                    'percentual_transito': round(percentual_transito, 1),
                    'status_transito': self._classificar_transito(percentual_transito),
                    'passos': [step['html_instructions'] for step in leg['steps']],
                    'overview_polyline': rota['overview_polyline']['points'],
                    'warnings': rota.get('warnings', []),
                    'horario_partida': departure_time.strftime('%H:%M'),
                    'horario_chegada': (departure_time + timedelta(seconds=duracao_com_transito)).strftime('%H:%M')
                }
            return {'erro': 'Rota não encontrada'}
        except Exception as e:
            self.logger.error(f"❌ Erro ao calcular rota: {str(e)}")
            return {'erro': str(e)}
    
    def estimar_tempo(self, origem, destino, departure_time=None):
        """
        Estima tempo com trânsito em tempo real
        """
        try:
            if departure_time is None:
                departure_time = datetime.now()
            
            self.logger.info(f"⏱️ Estimando tempo: {origem} → {destino}")
            
            matrix = self.client.distance_matrix(
                origem,
                destino,
                mode="driving",
                departure_time=departure_time,
                traffic_model="best_guess",
                # avoid=["tolls"]  # Removido para evitar erro de restriction
            )
            
            if matrix['status'] == 'OK':
                elemento = matrix['rows'][0]['elements'][0]
                if elemento['status'] == 'OK':
                    duracao_normal = elemento['duration']['value']
                    duracao_com_transito = elemento.get('duration_in_traffic', {}).get('value', duracao_normal)
                    
                    impacto_transito = duracao_com_transito - duracao_normal
                    percentual_transito = (impacto_transito / duracao_normal) * 100 if duracao_normal > 0 else 0
                    
                    return {
                        'distancia': elemento['distance']['text'],
                        'distancia_metros': elemento['distance']['value'],
                        'duracao': elemento['duration']['text'],
                        'duracao_segundos': duracao_normal,
                        'duracao_com_transito': self._seconds_to_text(duracao_com_transito),
                        'duracao_com_transito_segundos': duracao_com_transito,
                        'impacto_transito_minutos': round(impacto_transito / 60, 1),
                        'percentual_transito': round(percentual_transito, 1),
                        'status_transito': self._classificar_transito(percentual_transito),
                        'recomendacao': self._gerar_recomendacao_transito(percentual_transito, departure_time)
                    }
            return {'erro': 'Não foi possível estimar o tempo'}
        except Exception as e:
            self.logger.error(f"❌ Erro ao estimar tempo: {str(e)}")
            return {'erro': str(e)}
    
    def calcular_rota_multipla(self, pontos, departure_time=None):
        """
        Calcula rota otimizada para múltiplos pontos com trânsito
        """
        try:
            if len(pontos) < 2:
                return {'erro': 'Pelo menos 2 pontos são necessários'}
            
            if departure_time is None:
                departure_time = datetime.now()
            
            self.logger.info(f"🗺️ Calculando rota múltipla para {len(pontos)} pontos")
            
            # Separar origem, destino e waypoints
            origem = pontos[0]
            destino = pontos[-1]
            waypoints = pontos[1:-1] if len(pontos) > 2 else []
            
            directions_result = self.client.directions(
                origem,
                destino,
                waypoints=waypoints,
                optimize_waypoints=True,
                mode="driving",
                departure_time=departure_time,
                traffic_model="best_guess",
                # avoid=["tolls"]  # Removido para evitar erro de restriction
            )
            
            if directions_result:
                rota = directions_result[0]
                
                # Calcular totais
                distancia_total = sum(leg['distance']['value'] for leg in rota['legs'])
                duracao_total = sum(leg['duration']['value'] for leg in rota['legs'])
                duracao_com_transito_total = sum(
                    leg.get('duration_in_traffic', {}).get('value', leg['duration']['value']) 
                    for leg in rota['legs']
                )
                
                # Processar cada trecho
                trechos = []
                horario_atual = departure_time
                
                for i, leg in enumerate(rota['legs']):
                    duracao_trecho = leg.get('duration_in_traffic', {}).get('value', leg['duration']['value'])
                    
                    trechos.append({
                        'origem': leg['start_address'],
                        'destino': leg['end_address'],
                        'distancia': leg['distance']['text'],
                        'duracao': self._seconds_to_text(duracao_trecho),
                        'horario_partida': horario_atual.strftime('%H:%M'),
                        'horario_chegada': (horario_atual + timedelta(seconds=duracao_trecho)).strftime('%H:%M'),
                        'instrucoes': [step['html_instructions'] for step in leg['steps'][:3]]  # Primeiras 3 instruções
                    })
                    
                    horario_atual += timedelta(seconds=duracao_trecho)
                
                impacto_transito = duracao_com_transito_total - duracao_total
                percentual_transito = (impacto_transito / duracao_total) * 100 if duracao_total > 0 else 0
                
                return {
                    'distancia_total': f"{distancia_total / 1000:.1f} km",
                    'duracao_total': self._seconds_to_text(duracao_total),
                    'duracao_com_transito_total': self._seconds_to_text(duracao_com_transito_total),
                    'impacto_transito_minutos': round(impacto_transito / 60, 1),
                    'percentual_transito': round(percentual_transito, 1),
                    'status_transito': self._classificar_transito(percentual_transito),
                    'trechos': trechos,
                    'overview_polyline': rota['overview_polyline']['points'],
                    'waypoint_order': rota.get('waypoint_order', []),
                    'warnings': rota.get('warnings', []),
                    'horario_partida': departure_time.strftime('%H:%M'),
                    'horario_chegada': (departure_time + timedelta(seconds=duracao_com_transito_total)).strftime('%H:%M'),
                    'recomendacao': self._gerar_recomendacao_transito(percentual_transito, departure_time)
                }
            
            return {'erro': 'Rota não encontrada'}
        except Exception as e:
            self.logger.error(f"❌ Erro ao calcular rota múltipla: {str(e)}")
            return {'erro': str(e)}
    
    def obter_condicoes_transito(self, pontos, departure_time=None):
        """
        Obtém condições de trânsito para uma lista de pontos
        """
        try:
            if departure_time is None:
                departure_time = datetime.now()
            
            self.logger.info(f"🚦 Verificando condições de trânsito para {len(pontos)} pontos")
            
            # Usar Distance Matrix para obter condições de trânsito
            # Corrigir: não consultar pontos para eles mesmos, mas entre pontos diferentes
            if len(pontos) < 2:
                # Se só há um ponto, simular dados básicos
                return {
                    'condicoes': [{
                        'origem': pontos[0],
                        'destino': pontos[0],
                        'duracao_normal_minutos': 0,
                        'duracao_com_transito_minutos': 0,
                        'impacto_transito_minutos': 0,
                        'percentual_transito': 0,
                        'status_transito': {'status': 'fluido', 'cor': 'success', 'icone': '🟢'}
                    }],
                    'resumo': {
                        'impacto_medio': 0,
                        'status_geral': {'status': 'fluido', 'cor': 'success', 'icone': '🟢'},
                        'total_trechos': 0,
                        'trechos_problematicos': 0
                    },
                    'horario_consulta': departure_time.strftime('%H:%M') if departure_time else '08:00',
                    'recomendacoes': []
                }
            
            # Fazer consulta correta: do primeiro ponto para todos os outros
            origins = [pontos[0]]  # Começar do primeiro ponto
            destinations = pontos[1:]  # Para todos os outros pontos
            
            matrix = self.client.distance_matrix(
                origins,
                destinations,
                mode="driving",
                departure_time=departure_time,
                traffic_model="best_guess"
            )
            
            if matrix['status'] == 'OK':
                condicoes = []
                
                # Processar resultados corretamente (origem única para múltiplos destinos)
                origem = pontos[0]
                row = matrix['rows'][0]  # Primeira (e única) linha de resultados
                
                for j, destino in enumerate(destinations):
                    elemento = row['elements'][j]
                    if elemento['status'] == 'OK':
                        duracao_normal = elemento['duration']['value']
                        duracao_com_transito = elemento.get('duration_in_traffic', {}).get('value', duracao_normal)
                        
                        impacto_transito = duracao_com_transito - duracao_normal
                        percentual_transito = (impacto_transito / duracao_normal) * 100 if duracao_normal > 0 else 0
                        
                        condicoes.append({
                            'origem': origem,
                            'destino': destino,
                            'duracao_normal_minutos': round(duracao_normal / 60, 1),
                            'duracao_com_transito_minutos': round(duracao_com_transito / 60, 1),
                            'impacto_transito_minutos': round(impacto_transito / 60, 1),
                            'percentual_transito': round(percentual_transito, 1),
                            'status_transito': self._classificar_transito(percentual_transito)
                        })
                
                return {
                    'condicoes': condicoes,
                    'resumo': self._gerar_resumo_transito(condicoes),
                    'horario_consulta': departure_time.strftime('%H:%M'),
                    'recomendacoes': self._gerar_recomendacoes_gerais(condicoes)
                }
            
            return {'erro': 'Não foi possível obter condições de trânsito'}
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter condições de trânsito: {str(e)}")
            return {'erro': str(e)}
    
    def _seconds_to_text(self, seconds):
        """Converte segundos em texto legível"""
        if seconds < 60:
            return f"{seconds} seg"
        elif seconds < 3600:
            minutes = round(seconds / 60)
            return f"{minutes} min"
        else:
            hours = seconds // 3600
            minutes = round((seconds % 3600) / 60)
            return f"{hours}h {minutes}min"
    
    def _classificar_transito(self, percentual):
        """Classifica o status do trânsito"""
        if percentual < 10:
            return {'status': 'fluido', 'cor': 'success', 'icone': '🟢'}
        elif percentual < 25:
            return {'status': 'moderado', 'cor': 'warning', 'icone': '🟡'}
        elif percentual < 50:
            return {'status': 'congestionado', 'cor': 'danger', 'icone': '🟠'}
        else:
            return {'status': 'muito_congestionado', 'cor': 'danger', 'icone': '🔴'}
    
    def _gerar_recomendacao_transito(self, percentual, departure_time):
        """Gera recomendação baseada no trânsito"""
        if percentual < 10:
            return "Condições ideais para viagem"
        elif percentual < 25:
            return "Trânsito normal, sem alterações necessárias"
        elif percentual < 50:
            return f"Considere partir 15 minutos mais cedo"
        else:
            return f"Trânsito intenso, considere partir 30 minutos mais cedo ou escolher outro horário"
    
    def _gerar_resumo_transito(self, condicoes):
        """Gera resumo das condições de trânsito"""
        if not condicoes:
            return "Nenhuma condição disponível"
        
        percentuais = [c['percentual_transito'] for c in condicoes]
        media = sum(percentuais) / len(percentuais)
        
        return {
            'impacto_medio': round(media, 1),
            'status_geral': self._classificar_transito(media),
            'total_trechos': len(condicoes),
            'trechos_problematicos': len([c for c in condicoes if c['percentual_transito'] > 25])
        }
    
    def _gerar_recomendacoes_gerais(self, condicoes):
        """Gera recomendações gerais baseadas nas condições"""
        if not condicoes:
            return []
        
        recomendacoes = []
        
        # Verificar trechos problemáticos
        problematicos = [c for c in condicoes if c['percentual_transito'] > 25]
        
        if problematicos:
            recomendacoes.append({
                'tipo': 'warning',
                'icone': '⚠️',
                'titulo': 'Trechos com trânsito intenso',
                'descricao': f'{len(problematicos)} trechos com atrasos significativos'
            })
        
        # Verificar horário de pico
        agora = datetime.now()
        if 7 <= agora.hour <= 9 or 17 <= agora.hour <= 19:
            recomendacoes.append({
                'tipo': 'info',
                'icone': '🕐',
                'titulo': 'Horário de pico',
                'descricao': 'Considere ajustar horários para evitar trânsito intenso'
            })
        
        return recomendacoes 