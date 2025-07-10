import googlemaps
from datetime import datetime

class MapaService:
    def __init__(self, api_key):
        self.client = googlemaps.Client(key=api_key)
    
    def calcular_rota(self, origem, destino):
        try:
            directions_result = self.client.directions(
                origem,
                destino,
                mode="driving",
                departure_time=datetime.now()
            )
            
            if directions_result:
                rota = directions_result[0]
                return {
                    'distancia': rota['legs'][0]['distance']['text'],
                    'duracao': rota['legs'][0]['duration']['text'],
                    'passos': [step['html_instructions'] for step in rota['legs'][0]['steps']]
                }
            return {'erro': 'Rota não encontrada'}
        except Exception as e:
            return {'erro': str(e)}
    
    def estimar_tempo(self, origem, destino):
        try:
            matrix = self.client.distance_matrix(
                origem,
                destino,
                mode="driving",
                departure_time=datetime.now()
            )
            
            if matrix['status'] == 'OK':
                elemento = matrix['rows'][0]['elements'][0]
                if elemento['status'] == 'OK':
                    return {
                        'distancia': elemento['distance']['text'],
                        'duracao': elemento['duration']['text']
                    }
            return {'erro': 'Não foi possível estimar o tempo'}
        except Exception as e:
            return {'erro': str(e)} 