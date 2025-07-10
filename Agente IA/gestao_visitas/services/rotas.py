from datetime import datetime, timedelta
from ..config import MUNICIPIOS

class RotaService:
    def __init__(self, maps_service):
        self.maps_service = maps_service
        self.rotas = {}
        self.visitas_agendadas = {}

    def calcular_rota_otima(self, visitas, data):
        """Calcula a rota otimizada para um conjunto de visitas em uma data."""
        if not visitas:
            return None

        # Agrupa visitas por município
        visitas_por_municipio = {}
        for visita in visitas:
            if visita.municipio not in visitas_por_municipio:
                visitas_por_municipio[visita.municipio] = []
            visitas_por_municipio[visita.municipio].append(visita)

        # Calcula rotas para cada município
        rotas_municipios = {}
        for municipio, visitas_municipio in visitas_por_municipio.items():
            rota = self._calcular_rota_municipio(municipio, visitas_municipio)
            if rota:
                rotas_municipios[municipio] = rota

        # Gera ID único para a rota
        rota_id = f"rota_{data.strftime('%Y%m%d')}"
        rota = {
            'id': rota_id,
            'data': data,
            'rotas_municipios': rotas_municipios,
            'estatisticas': self._calcular_estatisticas_rota(rotas_municipios),
            'data_criacao': datetime.now()
        }

        self.rotas[rota_id] = rota
        return rota

    def _calcular_rota_municipio(self, municipio, visitas):
        """Calcula a rota otimizada para visitas em um município."""
        if not visitas:
            return None

        # Ordena visitas por horário
        visitas_ordenadas = sorted(visitas, key=lambda v: v.hora_inicio)

        # Calcula distâncias e tempos entre pontos
        pontos = []
        for i, visita in enumerate(visitas_ordenadas):
            ponto = {
                'visita_id': visita.id,
                'municipio': visita.municipio,
                'endereco': visita.endereco if hasattr(visita, 'endereco') and visita.endereco else visita.municipio,
                'hora_inicio': visita.hora_inicio,
                'hora_fim': visita.hora_fim,
                'ordem': i + 1
            }
            pontos.append(ponto)

        # Calcula rotas entre pontos consecutivos
        rotas = []
        for i in range(len(pontos) - 1):
            origem = pontos[i]['endereco']
            destino = pontos[i + 1]['endereco']
            
            if self.maps_service:
                rota = self.maps_service.calcular_rota(origem, destino)
                if rota:
                    rotas.append({
                        'origem': pontos[i],
                        'destino': pontos[i + 1],
                        'distancia': rota['distancia'],
                        'duracao': rota['duracao'],
                        'instrucoes': rota['instrucoes']
                    })
            else:
                # Fallback quando Google Maps não está disponível
                rotas.append({
                    'origem': pontos[i],
                    'destino': pontos[i + 1],
                    'distancia': 'N/A',
                    'duracao': 'N/A',
                    'instrucoes': ['Rota não calculada - Google Maps não configurado']
                })

        return {
            'municipio': municipio,
            'pontos': pontos,
            'rotas': rotas,
            'estatisticas': self._calcular_estatisticas_municipio(pontos, rotas)
        }

    def _calcular_estatisticas_rota(self, rotas_municipios):
        """Calcula estatísticas gerais da rota."""
        total_visitas = 0
        total_distancia = 0
        total_duracao = 0
        visitas_por_municipio = {}

        for municipio, rota in rotas_municipios.items():
            total_visitas += len(rota['pontos'])
            visitas_por_municipio[municipio] = len(rota['pontos'])

            for rota_segmento in rota['rotas']:
                total_distancia += rota_segmento['distancia']
                total_duracao += rota_segmento['duracao']

        return {
            'total_visitas': total_visitas,
            'total_distancia': total_distancia,
            'total_duracao': total_duracao,
            'visitas_por_municipio': visitas_por_municipio
        }

    def _calcular_estatisticas_municipio(self, pontos, rotas):
        """Calcula estatísticas da rota em um município."""
        total_distancia = sum(rota['distancia'] for rota in rotas)
        total_duracao = sum(rota['duracao'] for rota in rotas)

        return {
            'total_pontos': len(pontos),
            'total_distancia': total_distancia,
            'total_duracao': total_duracao
        }

    def obter_rota(self, rota_id):
        """Retorna uma rota específica."""
        return self.rotas.get(rota_id)

    def obter_rotas_por_data(self, data):
        """Retorna todas as rotas de uma data específica."""
        return [
            rota
            for rota in self.rotas.values()
            if rota['data'].date() == data.date()
        ]

    def obter_rotas_por_municipio(self, municipio):
        """Retorna todas as rotas de um município."""
        return [
            rota
            for rota in self.rotas.values()
            if municipio in rota['rotas_municipios']
        ]

    def atualizar_rota(self, rota_id, visitas):
        """Atualiza uma rota existente com novas visitas."""
        rota = self.obter_rota(rota_id)
        if not rota:
            return None

        return self.calcular_rota_otima(visitas, rota['data'])

    def verificar_viabilidade(self, visitas, data):
        """Verifica a viabilidade de realizar todas as visitas em um dia."""
        if not visitas:
            return False

        # Agrupa visitas por município
        visitas_por_municipio = {}
        for visita in visitas:
            if visita.municipio not in visitas_por_municipio:
                visitas_por_municipio[visita.municipio] = []
            visitas_por_municipio[visita.municipio].append(visita)

        # Verifica viabilidade para cada município
        for municipio, visitas_municipio in visitas_por_municipio.items():
            if not self._verificar_viabilidade_municipio(municipio, visitas_municipio):
                return False

        return True

    def _verificar_viabilidade_municipio(self, municipio, visitas):
        """Verifica a viabilidade de realizar visitas em um município."""
        if not visitas:
            return True

        # Ordena visitas por horário
        visitas_ordenadas = sorted(visitas, key=lambda v: v.hora_inicio)

        # Verifica sobreposição de horários
        for i in range(len(visitas_ordenadas) - 1):
            visita_atual = visitas_ordenadas[i]
            proxima_visita = visitas_ordenadas[i + 1]

            # Calcula tempo de deslocamento
            origem = visita_atual.endereco if hasattr(visita_atual, 'endereco') and visita_atual.endereco else visita_atual.municipio
            destino = proxima_visita.endereco if hasattr(proxima_visita, 'endereco') and proxima_visita.endereco else proxima_visita.municipio
            
            if self.maps_service:
                tempo_deslocamento = self.maps_service.estimar_tempo(origem, destino)
            else:
                # Fallback: assumir 30 minutos para deslocamento quando Google Maps não disponível
                tempo_deslocamento = 30

            # Verifica se há tempo suficiente entre as visitas
            tempo_disponivel = (proxima_visita.hora_inicio - visita_atual.hora_fim).total_seconds() / 60
            
            # Extrair duração dependendo do formato retornado
            if isinstance(tempo_deslocamento, dict):
                duracao_minutos = tempo_deslocamento.get('duracao', 30)
            else:
                duracao_minutos = tempo_deslocamento
            
            if tempo_disponivel < duracao_minutos:
                return False

        return True 