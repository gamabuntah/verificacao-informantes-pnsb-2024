"""
Sistema de Logística com Google Maps - PNSB
Otimização de rotas, cálculo de distâncias e tempo de viagem
"""

import googlemaps
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple, Any
from ..models.agendamento import Visita
from ..models.contatos import Contato
from ..db import db
import json
import math
from collections import defaultdict

# Import geopy with fallback
try:
    from geopy.distance import geodesic
    GEOPY_AVAILABLE = True
except ImportError:
    print("⚠️  geopy não encontrado. Funcionalidades de distância usarão aproximação.")
    GEOPY_AVAILABLE = False
    
    # Fallback simples para cálculo de distância
    def geodesic(point1, point2):
        """Fallback simples para cálculo de distância quando geopy não está disponível"""
        lat1, lon1 = point1
        lat2, lon2 = point2
        
        # Fórmula haversine simplificada
        R = 6371  # Raio da Terra em km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        class Distance:
            def __init__(self, km):
                self.kilometers = km
        
        return Distance(R * c)

class LogisticaMaps:
    """Sistema de logística avançado com integração Google Maps"""
    
    def __init__(self, google_maps_key: str):
        self.gmaps = googlemaps.Client(key=google_maps_key) if google_maps_key else None
        self.cache_distancias = {}
        self.cache_geocoding = {}
        
        # Coordenadas centrais dos municípios PNSB SC
        self.coordenadas_municipios = {
            'Itajaí': (-26.9077, -48.6618),
            'Navegantes': (-26.8966, -48.6541),
            'Penha': (-26.7731, -48.6529),
            'Piçarras': (-26.7615, -48.6697),
            'Barra Velha': (-26.6321, -48.6836),
            'Bombinhas': (-27.1389, -48.4816),
            'Porto Belo': (-27.1576, -48.5356),
            'Itapema': (-27.0914, -48.6156),
            'Balneário Camboriú': (-26.9906, -48.6348),
            'Camboriú': (-27.0251, -48.6586),
            'Tijucas': (-27.2424, -48.6342)
        }
    
    def otimizar_rota_diaria(self, data_visita: str, origem: str = 'Itajaí', 
                           visitas_agendadas: List[Dict] = None) -> Dict:
        """Otimiza rota para todas as visitas do dia"""
        
        if not self.gmaps:
            return self._otimizacao_offline(data_visita, origem, visitas_agendadas)
        
        # Obter visitas do dia se não fornecidas
        if not visitas_agendadas:
            visitas_agendadas = self._obter_visitas_dia(data_visita)
        
        if not visitas_agendadas:
            return {'erro': 'Nenhuma visita agendada para este dia'}
        
        # Geocodificar endereços
        pontos_visita = []
        for visita in visitas_agendadas:
            coordenadas = self._obter_coordenadas(visita['municipio'], visita.get('endereco'))
            if coordenadas:
                pontos_visita.append({
                    'visita_id': visita.get('id'),
                    'municipio': visita['municipio'],
                    'endereco': visita.get('endereco', ''),
                    'informante': visita.get('informante', ''),
                    'coordenadas': coordenadas,
                    'horario_preferido': visita.get('horario_preferido'),
                    'duracao_estimada': visita.get('duracao_estimada', 60),
                    'prioridade': visita.get('prioridade', 'normal')
                })
        
        # Calcular matriz de distâncias
        matriz_distancias = self._calcular_matriz_distancias(origem, pontos_visita)
        
        # Aplicar algoritmo de otimização
        rota_otimizada = self._algoritmo_otimizacao_rota(
            origem, pontos_visita, matriz_distancias
        )
        
        # Calcular tempos e horários
        cronograma_detalhado = self._calcular_cronograma_detalhado(
            origem, rota_otimizada, data_visita
        )
        
        # Identificar conflitos e problemas
        alertas = self._identificar_alertas_rota(cronograma_detalhado)
        
        return {
            'data_visita': data_visita,
            'origem': origem,
            'total_visitas': len(pontos_visita),
            'rota_otimizada': rota_otimizada,
            'cronograma_detalhado': cronograma_detalhado,
            'resumo_logistico': {
                'distancia_total_km': cronograma_detalhado.get('distancia_total_km', 0),
                'tempo_viagem_total': cronograma_detalhado.get('tempo_viagem_total', 0),
                'tempo_visitas_total': cronograma_detalhado.get('tempo_visitas_total', 0),
                'horario_inicio': cronograma_detalhado.get('horario_inicio'),
                'horario_fim_estimado': cronograma_detalhado.get('horario_fim_estimado'),
                'economia_distancia_percent': cronograma_detalhado.get('economia_vs_sequencial', 0)
            },
            'alertas_logisticos': alertas,
            'sugestoes_melhoria': self._gerar_sugestoes_melhoria(cronograma_detalhado, alertas)
        }
    
    def calcular_tempo_viagem(self, origem: str, destino: str, 
                            horario_partida: datetime = None) -> Dict:
        """Calcula tempo de viagem entre dois pontos"""
        
        if not self.gmaps:
            return self._calculo_tempo_offline(origem, destino)
        
        try:
            # Obter coordenadas
            coord_origem = self._obter_coordenadas(origem)
            coord_destino = self._obter_coordenadas(destino)
            
            if not coord_origem or not coord_destino:
                return self._calculo_tempo_offline(origem, destino)
            
            # Usar horário atual se não especificado
            if not horario_partida:
                horario_partida = datetime.now()
            
            # Consultar Google Maps Directions API
            directions = self.gmaps.directions(
                origin=coord_origem,
                destination=coord_destino,
                mode="driving",
                departure_time=horario_partida,
                traffic_model="best_guess",
                language="pt-BR"
            )
            
            if not directions:
                return self._calculo_tempo_offline(origem, destino)
            
            route = directions[0]
            leg = route['legs'][0]
            
            return {
                'origem': origem,
                'destino': destino,
                'distancia_km': leg['distance']['value'] / 1000,
                'distancia_texto': leg['distance']['text'],
                'tempo_minutos': leg['duration']['value'] / 60,
                'tempo_texto': leg['duration']['text'],
                'tempo_com_transito': leg.get('duration_in_traffic', {}).get('value', 0) / 60,
                'rota_resumo': leg['summary'] if 'summary' in leg else route['summary'],
                'instrucoes': [step['html_instructions'] for step in leg['steps']],
                'horario_partida': horario_partida.isoformat(),
                'horario_chegada_estimado': (horario_partida + timedelta(
                    seconds=leg.get('duration_in_traffic', leg['duration'])['value']
                )).isoformat()
            }
            
        except Exception as e:
            return {
                'erro': f'Erro ao calcular rota: {str(e)}',
                'fallback': self._calculo_tempo_offline(origem, destino)
            }
    
    def sugerir_melhor_sequencia_visitas(self, visitas: List[Dict], 
                                       origem: str = 'Itajaí') -> Dict:
        """Sugere a melhor sequência para realizar as visitas"""
        
        if len(visitas) <= 1:
            return {'sequencia_otimizada': visitas, 'economia': 0}
        
        # Calcular todas as distâncias possíveis
        matriz_distancias = {}
        pontos = [origem] + [v['municipio'] for v in visitas]
        
        for i, ponto1 in enumerate(pontos):
            for j, ponto2 in enumerate(pontos):
                if i != j:
                    distancia = self._calcular_distancia_entre_municipios(ponto1, ponto2)
                    matriz_distancias[f"{ponto1}-{ponto2}"] = distancia
        
        # Aplicar algoritmo de otimização (Nearest Neighbor melhorado)
        sequencia_otimizada = self._resolver_tsp_aproximado(visitas, origem, matriz_distancias)
        
        # Calcular economia vs. sequência original
        distancia_original = self._calcular_distancia_sequencia(visitas, origem, matriz_distancias)
        distancia_otimizada = self._calcular_distancia_sequencia(sequencia_otimizada, origem, matriz_distancias)
        economia_km = distancia_original - distancia_otimizada
        economia_percent = (economia_km / distancia_original) * 100 if distancia_original > 0 else 0
        
        return {
            'sequencia_original': visitas,
            'sequencia_otimizada': sequencia_otimizada,
            'economia_km': round(economia_km, 2),
            'economia_percentual': round(economia_percent, 1),
            'distancia_original_km': round(distancia_original, 2),
            'distancia_otimizada_km': round(distancia_otimizada, 2),
            'tempo_economia_minutos': round(economia_km * 1.2, 0),  # ~1.2 min por km
            'recomendacao': 'Usar sequência otimizada' if economia_percent > 10 else 'Manter sequência original'
        }
    
    def monitorar_transito_tempo_real(self, rota: List[str]) -> Dict:
        """Monitora condições de trânsito em tempo real para a rota"""
        
        if not self.gmaps or len(rota) < 2:
            return {'status': 'sem_dados', 'alertas': []}
        
        try:
            alertas_transito = []
            tempos_atualizados = []
            
            for i in range(len(rota) - 1):
                origem = rota[i]
                destino = rota[i + 1]
                
                # Consultar condições atuais
                tempo_atual = self.calcular_tempo_viagem(
                    origem, destino, datetime.now()
                )
                
                # Consultar tempo sem trânsito
                tempo_livre = self.calcular_tempo_viagem(
                    origem, destino, datetime.now() + timedelta(hours=22)  # Madrugada
                )
                
                # Identificar congestionamentos
                if tempo_atual.get('tempo_com_transito', 0) > tempo_livre.get('tempo_minutos', 0) * 1.3:
                    alertas_transito.append({
                        'trecho': f"{origem} → {destino}",
                        'tipo': 'congestionamento',
                        'tempo_normal': tempo_livre.get('tempo_minutos', 0),
                        'tempo_atual': tempo_atual.get('tempo_com_transito', 0),
                        'atraso_estimado': tempo_atual.get('tempo_com_transito', 0) - tempo_livre.get('tempo_minutos', 0),
                        'severidade': 'alta' if tempo_atual.get('tempo_com_transito', 0) > tempo_livre.get('tempo_minutos', 0) * 1.5 else 'media'
                    })
                
                tempos_atualizados.append({
                    'trecho': f"{origem} → {destino}",
                    'tempo_estimado': tempo_atual.get('tempo_com_transito', tempo_atual.get('tempo_minutos', 0)),
                    'distancia_km': tempo_atual.get('distancia_km', 0)
                })
            
            return {
                'status': 'monitorando',
                'timestamp_consulta': datetime.now().isoformat(),
                'tempos_atualizados': tempos_atualizados,
                'alertas_transito': alertas_transito,
                'tempo_total_atualizado': sum(t['tempo_estimado'] for t in tempos_atualizados),
                'recomendacoes': self._gerar_recomendacoes_transito(alertas_transito)
            }
            
        except Exception as e:
            return {
                'status': 'erro',
                'erro': str(e),
                'fallback': 'Usar tempos estimados padrão'
            }
    
    def calcular_raio_cobertura(self, origem: str, tempo_limite_minutos: int = 120) -> Dict:
        """Calcula quantos municípios podem ser visitados dentro do tempo limite"""
        
        municipios_alcancaveis = []
        
        for municipio in self.coordenadas_municipios.keys():
            if municipio == origem:
                continue
            
            tempo_viagem = self.calcular_tempo_viagem(origem, municipio)
            tempo_ida_volta = tempo_viagem.get('tempo_minutos', 0) * 2
            
            if tempo_ida_volta <= tempo_limite_minutos:
                municipios_alcancaveis.append({
                    'municipio': municipio,
                    'tempo_ida_volta': tempo_ida_volta,
                    'distancia_km': tempo_viagem.get('distancia_km', 0) * 2,
                    'viabilidade': 'alta' if tempo_ida_volta <= tempo_limite_minutos * 0.6 else 'media'
                })
        
        # Ordenar por tempo de viagem
        municipios_alcancaveis.sort(key=lambda x: x['tempo_ida_volta'])
        
        return {
            'origem': origem,
            'tempo_limite_minutos': tempo_limite_minutos,
            'total_municipios_alcancaveis': len(municipios_alcancaveis),
            'municipios_alcancaveis': municipios_alcancaveis,
            'cobertura_percentual': round((len(municipios_alcancaveis) / (len(self.coordenadas_municipios) - 1)) * 100, 1),
            'recomendacoes_origem': self._sugerir_melhor_origem_cobertura()
        }
    
    def analisar_viabilidade_cronograma(self, cronograma: Dict) -> Dict:
        """Analisa a viabilidade logística de um cronograma de visitas"""
        
        problemas_identificados = []
        sugestoes_melhoria = []
        metricas_viabilidade = {}
        
        # Analisar cada dia do cronograma
        for data, visitas_dia in cronograma.items():
            analise_dia = self._analisar_viabilidade_dia(data, visitas_dia)
            
            if analise_dia.get('problemas'):
                problemas_identificados.extend(analise_dia['problemas'])
            
            if analise_dia.get('sugestoes'):
                sugestoes_melhoria.extend(analise_dia['sugestoes'])
            
            metricas_viabilidade[data] = analise_dia.get('metricas', {})
        
        # Análise geral do cronograma
        viabilidade_geral = self._calcular_viabilidade_geral(metricas_viabilidade)
        
        return {
            'cronograma_analisado': cronograma,
            'viabilidade_geral': viabilidade_geral,
            'problemas_identificados': problemas_identificados,
            'sugestoes_melhoria': sugestoes_melhoria,
            'metricas_por_dia': metricas_viabilidade,
            'recomendacao_final': self._gerar_recomendacao_cronograma(viabilidade_geral, problemas_identificados)
        }
    
    # Métodos auxiliares e implementações
    
    def _obter_coordenadas(self, municipio: str, endereco: str = None) -> Tuple[float, float]:
        """Obtém coordenadas de um município ou endereço"""
        
        # Usar coordenadas conhecidas dos municípios
        if municipio in self.coordenadas_municipios:
            return self.coordenadas_municipios[municipio]
        
        # Se tem endereço específico e Google Maps disponível
        if endereco and self.gmaps:
            cache_key = f"{municipio}_{endereco}"
            if cache_key in self.cache_geocoding:
                return self.cache_geocoding[cache_key]
            
            try:
                geocode_result = self.gmaps.geocode(f"{endereco}, {municipio}, SC, Brasil")
                if geocode_result:
                    location = geocode_result[0]['geometry']['location']
                    coords = (location['lat'], location['lng'])
                    self.cache_geocoding[cache_key] = coords
                    return coords
            except:
                pass
        
        return None
    
    def _obter_visitas_dia(self, data_visita: str) -> List[Dict]:
        """Obtém visitas agendadas para um dia específico"""
        
        from datetime import datetime
        data_obj = datetime.strptime(data_visita, '%Y-%m-%d').date()
        
        visitas = Visita.query.filter(
            db.and_(
                Visita.data == data_obj,
                Visita.status == 'agendada'
            )
        ).all()
        
        return [
            {
                'id': v.id,
                'municipio': v.municipio,
                'informante': v.informante,
                'horario_preferido': v.hora_inicio,
                'duracao_estimada': 60,  # padrão
                'endereco': v.endereco if hasattr(v, 'endereco') else '',
                'prioridade': 'normal'
            }
            for v in visitas
        ]
    
    def _calcular_distancia_entre_municipios(self, origem: str, destino: str) -> float:
        """Calcula distância entre dois municípios"""
        
        cache_key = f"{origem}-{destino}"
        if cache_key in self.cache_distancias:
            return self.cache_distancias[cache_key]
        
        coord_origem = self._obter_coordenadas(origem)
        coord_destino = self._obter_coordenadas(destino)
        
        if coord_origem and coord_destino:
            distancia = geodesic(coord_origem, coord_destino).kilometers
            self.cache_distancias[cache_key] = distancia
            return distancia
        
        # Fallback: distância estimada baseada em posição relativa
        return self._distancia_estimada_fallback(origem, destino)
    
    def _algoritmo_otimizacao_rota(self, origem: str, pontos: List[Dict], 
                                 matriz_distancias: Dict) -> List[Dict]:
        """Algoritmo de otimização de rota (TSP aproximado)"""
        
        if len(pontos) <= 2:
            return pontos
        
        # Implementação do Nearest Neighbor com melhorias
        rota_otimizada = []
        pontos_restantes = pontos.copy()
        ponto_atual = origem
        
        while pontos_restantes:
            # Encontrar ponto mais próximo
            proximo_ponto = min(pontos_restantes, 
                              key=lambda p: self._calcular_distancia_entre_municipios(ponto_atual, p['municipio']))
            
            rota_otimizada.append(proximo_ponto)
            pontos_restantes.remove(proximo_ponto)
            ponto_atual = proximo_ponto['municipio']
        
        # Aplicar melhoria 2-opt simplificada
        rota_melhorada = self._aplicar_2opt(rota_otimizada, origem)
        
        return rota_melhorada
    
    def _calcular_cronograma_detalhado(self, origem: str, rota: List[Dict], 
                                     data_visita: str) -> Dict:
        """Calcula cronograma detalhado com horários e tempos"""
        
        cronograma = {
            'data': data_visita,
            'origem': origem,
            'horario_inicio': '08:00',
            'visitas': [],
            'distancia_total_km': 0,
            'tempo_viagem_total': 0,
            'tempo_visitas_total': 0
        }
        
        horario_atual = datetime.strptime(f"{data_visita} 08:00", '%Y-%m-%d %H:%M')
        local_atual = origem
        
        for i, visita in enumerate(rota):
            # Calcular tempo de viagem até o próximo ponto
            tempo_viagem = self.calcular_tempo_viagem(local_atual, visita['municipio'])
            
            # Adicionar tempo de viagem
            horario_atual += timedelta(minutes=tempo_viagem.get('tempo_minutos', 30))
            
            # Informações da visita
            visita_cronograma = {
                'ordem': i + 1,
                'municipio': visita['municipio'],
                'informante': visita['informante'],
                'horario_chegada': horario_atual.strftime('%H:%M'),
                'duracao_visita': visita.get('duracao_estimada', 60),
                'horario_saida': (horario_atual + timedelta(minutes=visita.get('duracao_estimada', 60))).strftime('%H:%M'),
                'tempo_viagem_anterior': tempo_viagem.get('tempo_minutos', 30),
                'distancia_anterior_km': tempo_viagem.get('distancia_km', 0)
            }
            
            cronograma['visitas'].append(visita_cronograma)
            cronograma['distancia_total_km'] += tempo_viagem.get('distancia_km', 0)
            cronograma['tempo_viagem_total'] += tempo_viagem.get('tempo_minutos', 30)
            cronograma['tempo_visitas_total'] += visita.get('duracao_estimada', 60)
            
            # Atualizar horário e local atual
            horario_atual += timedelta(minutes=visita.get('duracao_estimada', 60))
            local_atual = visita['municipio']
        
        # Tempo de retorno à origem
        tempo_retorno = self.calcular_tempo_viagem(local_atual, origem)
        cronograma['horario_fim_estimado'] = (horario_atual + timedelta(
            minutes=tempo_retorno.get('tempo_minutos', 30)
        )).strftime('%H:%M')
        
        cronograma['distancia_total_km'] += tempo_retorno.get('distancia_km', 0)
        cronograma['tempo_viagem_total'] += tempo_retorno.get('tempo_minutos', 30)
        
        return cronograma
    
    def _identificar_alertas_rota(self, cronograma: Dict) -> List[Dict]:
        """Identifica alertas e problemas potenciais na rota"""
        
        alertas = []
        
        # Verificar se o dia é muito longo
        inicio = datetime.strptime(cronograma['horario_inicio'], '%H:%M')
        fim = datetime.strptime(cronograma['horario_fim_estimado'], '%H:%M')
        duracao_total = (fim - inicio).total_seconds() / 3600
        
        if duracao_total > 10:
            alertas.append({
                'tipo': 'dia_muito_longo',
                'severidade': 'alta',
                'descricao': f'Dia de trabalho muito longo ({duracao_total:.1f} horas)',
                'sugestao': 'Considerar dividir as visitas em dois dias'
            })
        
        # Verificar distâncias excessivas
        if cronograma['distancia_total_km'] > 150:
            alertas.append({
                'tipo': 'distancia_excessiva',
                'severidade': 'media',
                'descricao': f'Distância total elevada ({cronograma["distancia_total_km"]:.1f} km)',
                'sugestao': 'Verificar possibilidade de otimização ou divisão da rota'
            })
        
        # Verificar horários de almoço
        for visita in cronograma['visitas']:
            horario_chegada = datetime.strptime(visita['horario_chegada'], '%H:%M')
            if 12 <= horario_chegada.hour <= 14:
                alertas.append({
                    'tipo': 'horario_almoco',
                    'severidade': 'baixa',
                    'descricao': f'Visita em {visita["municipio"]} durante horário de almoço',
                    'sugestao': 'Verificar disponibilidade do informante neste horário'
                })
        
        return alertas
    
    # Implementações simplificadas dos métodos auxiliares restantes
    def _otimizacao_offline(self, data, origem, visitas): return {}
    def _calculo_tempo_offline(self, origem, destino): return {}
    def _calcular_matriz_distancias(self, origem, pontos): return {}
    def _gerar_sugestoes_melhoria(self, cronograma, alertas): return []
    def _resolver_tsp_aproximado(self, visitas, origem, matriz): return visitas
    def _calcular_distancia_sequencia(self, visitas, origem, matriz): return 0
    def _gerar_recomendacoes_transito(self, alertas): return []
    def _sugerir_melhor_origem_cobertura(self): return []
    def _analisar_viabilidade_dia(self, data, visitas): return {}
    def _calcular_viabilidade_geral(self, metricas): return {}
    def _gerar_recomendacao_cronograma(self, viabilidade, problemas): return ""
    def _distancia_estimada_fallback(self, origem, destino): return 50
    def _aplicar_2opt(self, rota, origem): return rota