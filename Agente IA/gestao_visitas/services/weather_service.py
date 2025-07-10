"""
Sistema de Condições Climáticas - PNSB 2024
Integração com APIs de clima para planejamento inteligente de visitas
"""

from datetime import datetime, timedelta, date, time
from typing import Dict, List, Optional, Any, Tuple
import requests
import json
import logging
from dataclasses import dataclass
from enum import Enum
from ..models.agendamento import Visita
from ..db import db

class CondicaoClimatica(Enum):
    ENSOLARADO = "ensolarado"
    PARCIALMENTE_NUBLADO = "parcialmente_nublado"
    NUBLADO = "nublado"
    CHUVA_LEVE = "chuva_leve"
    CHUVA_MODERADA = "chuva_moderada"
    CHUVA_FORTE = "chuva_forte"
    TEMPESTADE = "tempestade"
    NEVOA = "nevoa"

class ImpactoVisita(Enum):
    IDEAL = "ideal"
    BOM = "bom"
    ACEITAVEL = "aceitavel"
    PROBLEMÁTICO = "problematico"
    CANCELAR = "cancelar"

@dataclass
class PrevisaoTempo:
    data: date
    municipio: str
    temperatura_min: float
    temperatura_max: float
    condicao: CondicaoClimatica
    chance_chuva: int  # 0-100%
    velocidade_vento: float  # km/h
    umidade: int  # 0-100%
    pressao: float  # hPa
    nascer_sol: time
    por_sol: time
    indice_uv: int
    visibilidade: float  # km
    fonte_dados: str
    timestamp_atualizacao: datetime

@dataclass
class RecomendacaoClimatica:
    impacto_visita: ImpactoVisita
    score_condicoes: float  # 0-1
    recomendacoes: List[str]
    alertas: List[str]
    equipamentos_sugeridos: List[str]
    melhor_horario: Optional[Tuple[time, time]]
    evitar_horarios: List[Tuple[time, time]]
    observacoes: List[str]

class WeatherService:
    """Serviço de integração com APIs climáticas"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        
        # URLs das APIs (usando OpenWeatherMap como exemplo)
        self.base_urls = {
            'current': 'https://api.openweathermap.org/data/2.5/weather',
            'forecast': 'https://api.openweathermap.org/data/2.5/forecast',
            'onecall': 'https://api.openweathermap.org/data/3.0/onecall'
        }
        
        # Coordenadas dos municípios SC
        self.coordenadas_municipios = {
            'Itajaí': (-26.9077, -48.6618),
            'Navegantes': (-26.8966, -48.6541),
            'Penha': (-26.7731, -48.6529),
            'Balneário Piçarras': (-26.7615, -48.6697),
            'Bombinhas': (-27.1389, -48.4816),
            'Porto Belo': (-27.1576, -48.5356),
            'Itapema': (-27.0914, -48.6156),
            'Balneário Camboriú': (-26.9906, -48.6348),
            'Camboriú': (-27.0251, -48.6586),
            'Luiz Alves': (-26.7169, -48.9357),
            'Ilhota': (-26.8984, -48.8269)
        }
        
        # Cache de previsões (válido por 1 hora)
        self.cache_previsoes = {}
        self.cache_timeout = 3600  # segundos
        
        # Configurações de impacto
        self.config_impacto = {
            'temperatura_ideal': (18, 28),  # °C
            'temperatura_aceitavel': (12, 35),
            'chance_chuva_problematica': 70,  # %
            'velocidade_vento_problematica': 40,  # km/h
            'visibilidade_minima': 5,  # km
            'indice_uv_alto': 8
        }
    
    def obter_previsao_dia(self, municipio: str, data_visita: date) -> Optional[PrevisaoTempo]:
        """Obter previsão do tempo para um município e data específicos"""
        
        try:
            # Verificar cache
            cache_key = f"{municipio}_{data_visita.isoformat()}"
            if self._cache_valido(cache_key):
                return self.cache_previsoes[cache_key]['dados']
            
            if not self.api_key:
                # Retornar dados simulados se não tiver API key
                return self._gerar_previsao_simulada(municipio, data_visita)
            
            # Obter coordenadas
            coords = self.coordenadas_municipios.get(municipio)
            if not coords:
                self.logger.warning(f"Coordenadas não encontradas para {municipio}")
                return None
            
            lat, lon = coords
            
            # Calcular dias de diferença
            dias_diferenca = (data_visita - date.today()).days
            
            if dias_diferenca == 0:
                # Clima atual
                previsao = self._obter_clima_atual(lat, lon, municipio)
            elif dias_diferenca <= 5:
                # Previsão de 5 dias
                previsao = self._obter_previsao_5_dias(lat, lon, municipio, data_visita)
            else:
                # Previsão histórica/climatológica
                previsao = self._obter_previsao_climatologica(municipio, data_visita)
            
            # Salvar no cache
            if previsao:
                self.cache_previsoes[cache_key] = {
                    'dados': previsao,
                    'timestamp': datetime.now()
                }
            
            return previsao
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter previsão para {municipio}: {str(e)}")
            return self._gerar_previsao_simulada(municipio, data_visita)
    
    def analisar_impacto_visita(self, municipio: str, data_visita: date,
                               hora_inicio: time, hora_fim: time,
                               tipo_atividade: str = 'visita_tecnica') -> RecomendacaoClimatica:
        """Analisar impacto climático em uma visita"""
        
        try:
            # Obter previsão
            previsao = self.obter_previsao_dia(municipio, data_visita)
            
            if not previsao:
                return self._gerar_recomendacao_padrao()
            
            # Analisar cada aspecto climático
            score_temperatura = self._avaliar_temperatura(previsao.temperatura_min, previsao.temperatura_max)
            score_chuva = self._avaliar_chuva(previsao.chance_chuva, previsao.condicao)
            score_vento = self._avaliar_vento(previsao.velocidade_vento)
            score_visibilidade = self._avaliar_visibilidade(previsao.visibilidade)
            score_uv = self._avaliar_indice_uv(previsao.indice_uv)
            
            # Score geral (média ponderada)
            score_geral = (
                score_temperatura * 0.25 +
                score_chuva * 0.35 +
                score_vento * 0.15 +
                score_visibilidade * 0.15 +
                score_uv * 0.10
            )
            
            # Determinar impacto
            impacto = self._determinar_impacto_visita(score_geral, previsao)
            
            # Gerar recomendações
            recomendacoes = self._gerar_recomendacoes_clima(previsao, hora_inicio, hora_fim)
            alertas = self._gerar_alertas_clima(previsao, hora_inicio, hora_fim)
            equipamentos = self._sugerir_equipamentos(previsao)
            horarios = self._sugerir_melhor_horario(previsao, hora_inicio, hora_fim)
            observacoes = self._gerar_observacoes_clima(previsao, tipo_atividade)
            
            return RecomendacaoClimatica(
                impacto_visita=impacto,
                score_condicoes=score_geral,
                recomendacoes=recomendacoes,
                alertas=alertas,
                equipamentos_sugeridos=equipamentos,
                melhor_horario=horarios['melhor'],
                evitar_horarios=horarios['evitar'],
                observacoes=observacoes
            )
            
        except Exception as e:
            self.logger.error(f"❌ Erro na análise climática: {str(e)}")
            return self._gerar_recomendacao_padrao()
    
    def obter_previsao_semana(self, municipio: str, data_inicio: date) -> Dict[date, PrevisaoTempo]:
        """Obter previsão para uma semana"""
        
        previsoes = {}
        
        for i in range(7):
            data_atual = data_inicio + timedelta(days=i)
            previsao = self.obter_previsao_dia(municipio, data_atual)
            
            if previsao:
                previsoes[data_atual] = previsao
        
        return previsoes
    
    def analisar_semana_visitas(self, visitas_semana: List[Visita]) -> Dict[str, Any]:
        """Analisar impacto climático de uma semana de visitas"""
        
        analise = {
            'visitas_analisadas': len(visitas_semana),
            'visitas_por_impacto': {
                'ideal': 0,
                'bom': 0,
                'aceitavel': 0,
                'problematico': 0,
                'cancelar': 0
            },
            'alertas_gerais': [],
            'sugestoes_reagendamento': [],
            'dias_problematicos': [],
            'score_medio_semana': 0
        }
        
        scores_totais = []
        
        for visita in visitas_semana:
            recomendacao = self.analisar_impacto_visita(
                visita.municipio,
                visita.data,
                visita.hora_inicio,
                visita.hora_fim
            )
            
            # Contar por impacto
            analise['visitas_por_impacto'][recomendacao.impacto_visita.value] += 1
            scores_totais.append(recomendacao.score_condicoes)
            
            # Verificar se precisa reagendamento
            if recomendacao.impacto_visita in [ImpactoVisita.PROBLEMÁTICO, ImpactoVisita.CANCELAR]:
                analise['sugestoes_reagendamento'].append({
                    'visita_id': visita.id,
                    'municipio': visita.municipio,
                    'data': visita.data.isoformat(),
                    'motivo': recomendacao.alertas[0] if recomendacao.alertas else 'Condições climáticas desfavoráveis',
                    'score': recomendacao.score_condicoes
                })
            
            # Marcar dias problemáticos
            if recomendacao.impacto_visita == ImpactoVisita.PROBLEMÁTICO:
                if visita.data not in analise['dias_problematicos']:
                    analise['dias_problematicos'].append(visita.data.isoformat())
        
        # Score médio da semana
        if scores_totais:
            analise['score_medio_semana'] = round(sum(scores_totais) / len(scores_totais), 3)
        
        # Alertas gerais
        if len(analise['sugestoes_reagendamento']) > 3:
            analise['alertas_gerais'].append("🌧️ Semana com muitas condições climáticas desfavoráveis")
        
        if analise['score_medio_semana'] < 0.6:
            analise['alertas_gerais'].append("⚠️ Score climático baixo para a semana")
        
        return analise
    
    def _obter_clima_atual(self, lat: float, lon: float, municipio: str) -> Optional[PrevisaoTempo]:
        """Obter clima atual via API"""
        
        try:
            url = self.base_urls['current']
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'pt_br'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._processar_dados_api(data, municipio, date.today())
            else:
                self.logger.warning(f"API retornou status {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro na API de clima atual: {str(e)}")
            return None
    
    def _obter_previsao_5_dias(self, lat: float, lon: float, municipio: str, data_alvo: date) -> Optional[PrevisaoTempo]:
        """Obter previsão de 5 dias via API"""
        
        try:
            url = self.base_urls['forecast']
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'pt_br'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Encontrar dados para a data específica
                for item in data['list']:
                    item_date = datetime.fromtimestamp(item['dt']).date()
                    if item_date == data_alvo:
                        return self._processar_dados_api_forecast(item, municipio, data_alvo)
                
                return None
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Erro na API de previsão: {str(e)}")
            return None
    
    def _obter_previsao_climatologica(self, municipio: str, data_visita: date) -> PrevisaoTempo:
        """Gerar previsão baseada em dados climatológicos históricos"""
        
        # Dados climatológicos médios para Santa Catarina
        mes = data_visita.month
        
        # Temperaturas médias por mês (aproximadas para SC)
        temperaturas_medias = {
            1: (20, 28), 2: (20, 28), 3: (19, 27), 4: (16, 24),
            5: (13, 21), 6: (11, 19), 7: (11, 19), 8: (12, 20),
            9: (14, 22), 10: (16, 24), 11: (18, 26), 12: (19, 27)
        }
        
        # Chance de chuva por mês
        chance_chuva_mes = {
            1: 45, 2: 40, 3: 35, 4: 25, 5: 20, 6: 15,
            7: 15, 8: 20, 9: 30, 10: 35, 11: 40, 12: 45
        }
        
        temp_min, temp_max = temperaturas_medias.get(mes, (15, 25))
        chance_chuva = chance_chuva_mes.get(mes, 30)
        
        # Determinar condição baseada na chance de chuva
        if chance_chuva > 60:
            condicao = CondicaoClimatica.CHUVA_MODERADA
        elif chance_chuva > 40:
            condicao = CondicaoClimatica.PARCIALMENTE_NUBLADO
        else:
            condicao = CondicaoClimatica.ENSOLARADO
        
        return PrevisaoTempo(
            data=data_visita,
            municipio=municipio,
            temperatura_min=temp_min,
            temperatura_max=temp_max,
            condicao=condicao,
            chance_chuva=chance_chuva,
            velocidade_vento=15.0,
            umidade=70,
            pressao=1013.25,
            nascer_sol=time(6, 30),
            por_sol=time(18, 30),
            indice_uv=6,
            visibilidade=10.0,
            fonte_dados='climatologia_historica',
            timestamp_atualizacao=datetime.now()
        )
    
    def _gerar_previsao_simulada(self, municipio: str, data_visita: date) -> PrevisaoTempo:
        """Gerar previsão simulada quando API não está disponível"""
        
        import random
        
        # Simular baseado na época do ano
        mes = data_visita.month
        
        if mes in [12, 1, 2]:  # Verão
            temp_min, temp_max = 20, 30
            chance_chuva = random.randint(30, 60)
        elif mes in [3, 4, 5]:  # Outono
            temp_min, temp_max = 15, 25
            chance_chuva = random.randint(20, 40)
        elif mes in [6, 7, 8]:  # Inverno
            temp_min, temp_max = 10, 20
            chance_chuva = random.randint(10, 30)
        else:  # Primavera
            temp_min, temp_max = 15, 25
            chance_chuva = random.randint(25, 45)
        
        condicoes = [
            CondicaoClimatica.ENSOLARADO,
            CondicaoClimatica.PARCIALMENTE_NUBLADO,
            CondicaoClimatica.NUBLADO
        ]
        
        if chance_chuva > 50:
            condicoes.append(CondicaoClimatica.CHUVA_LEVE)
        
        return PrevisaoTempo(
            data=data_visita,
            municipio=municipio,
            temperatura_min=temp_min + random.randint(-3, 3),
            temperatura_max=temp_max + random.randint(-3, 3),
            condicao=random.choice(condicoes),
            chance_chuva=chance_chuva,
            velocidade_vento=random.randint(5, 25),
            umidade=random.randint(50, 85),
            pressao=1013.25 + random.randint(-20, 20),
            nascer_sol=time(6, 30),
            por_sol=time(18, 30),
            indice_uv=random.randint(3, 9),
            visibilidade=random.randint(8, 15),
            fonte_dados='simulacao',
            timestamp_atualizacao=datetime.now()
        )
    
    def _cache_valido(self, cache_key: str) -> bool:
        """Verificar se o cache está válido"""
        
        if cache_key not in self.cache_previsoes:
            return False
        
        timestamp = self.cache_previsoes[cache_key]['timestamp']
        return (datetime.now() - timestamp).total_seconds() < self.cache_timeout
    
    def _avaliar_temperatura(self, temp_min: float, temp_max: float) -> float:
        """Avaliar score da temperatura"""
        
        ideal_min, ideal_max = self.config_impacto['temperatura_ideal']
        aceitavel_min, aceitavel_max = self.config_impacto['temperatura_aceitavel']
        
        # Verificar se está na faixa ideal
        if ideal_min <= temp_min and temp_max <= ideal_max:
            return 1.0
        
        # Verificar se está na faixa aceitável
        if aceitavel_min <= temp_min and temp_max <= aceitavel_max:
            return 0.7
        
        # Temperaturas extremas
        if temp_max > 35 or temp_min < 5:
            return 0.2
        
        return 0.5
    
    def _avaliar_chuva(self, chance_chuva: int, condicao: CondicaoClimatica) -> float:
        """Avaliar score da chuva"""
        
        if condicao in [CondicaoClimatica.CHUVA_FORTE, CondicaoClimatica.TEMPESTADE]:
            return 0.1
        elif condicao == CondicaoClimatica.CHUVA_MODERADA:
            return 0.3
        elif condicao == CondicaoClimatica.CHUVA_LEVE:
            return 0.6
        elif chance_chuva > self.config_impacto['chance_chuva_problematica']:
            return 0.4
        elif chance_chuva > 40:
            return 0.7
        else:
            return 1.0
    
    def _avaliar_vento(self, velocidade_vento: float) -> float:
        """Avaliar score do vento"""
        
        if velocidade_vento > self.config_impacto['velocidade_vento_problematica']:
            return 0.2
        elif velocidade_vento > 25:
            return 0.6
        else:
            return 1.0
    
    def _avaliar_visibilidade(self, visibilidade: float) -> float:
        """Avaliar score da visibilidade"""
        
        if visibilidade < self.config_impacto['visibilidade_minima']:
            return 0.3
        elif visibilidade < 8:
            return 0.7
        else:
            return 1.0
    
    def _avaliar_indice_uv(self, indice_uv: int) -> float:
        """Avaliar score do índice UV"""
        
        if indice_uv > self.config_impacto['indice_uv_alto']:
            return 0.6  # Alto, mas manejável com proteção
        elif indice_uv > 5:
            return 0.8
        else:
            return 1.0
    
    def _determinar_impacto_visita(self, score_geral: float, previsao: PrevisaoTempo) -> ImpactoVisita:
        """Determinar impacto da visita baseado no score"""
        
        # Condições que forçam cancelamento
        if previsao.condicao == CondicaoClimatica.TEMPESTADE:
            return ImpactoVisita.CANCELAR
        
        if previsao.velocidade_vento > 50:
            return ImpactoVisita.CANCELAR
        
        # Baseado no score geral
        if score_geral >= 0.8:
            return ImpactoVisita.IDEAL
        elif score_geral >= 0.6:
            return ImpactoVisita.BOM
        elif score_geral >= 0.4:
            return ImpactoVisita.ACEITAVEL
        elif score_geral >= 0.2:
            return ImpactoVisita.PROBLEMÁTICO
        else:
            return ImpactoVisita.CANCELAR
    
    def _gerar_recomendacoes_clima(self, previsao: PrevisaoTempo, 
                                 hora_inicio: time, hora_fim: time) -> List[str]:
        """Gerar recomendações baseadas no clima"""
        
        recomendacoes = []
        
        # Recomendações por temperatura
        if previsao.temperatura_max > 30:
            recomendacoes.append("🌡️ Levar água e manter-se hidratado")
            recomendacoes.append("🧢 Usar protetor solar e chapéu")
        elif previsao.temperatura_min < 15:
            recomendacoes.append("🧥 Levar agasalho adequado")
        
        # Recomendações por chuva
        if previsao.chance_chuva > 60:
            recomendacoes.append("☂️ Levar guarda-chuva ou capa de chuva")
            recomendacoes.append("👟 Usar calçado antiderrapante")
        elif previsao.chance_chuva > 30:
            recomendacoes.append("🌦️ Considerar levar guarda-chuva")
        
        # Recomendações por vento
        if previsao.velocidade_vento > 25:
            recomendacoes.append("💨 Cuidado com objetos soltos devido ao vento")
        
        # Recomendações por UV
        if previsao.indice_uv > 6:
            recomendacoes.append("🕶️ Usar óculos de sol e protetor solar")
        
        return recomendacoes
    
    def _gerar_alertas_clima(self, previsao: PrevisaoTempo,
                           hora_inicio: time, hora_fim: time) -> List[str]:
        """Gerar alertas baseados no clima"""
        
        alertas = []
        
        # Alertas críticos
        if previsao.condicao == CondicaoClimatica.TEMPESTADE:
            alertas.append("⚠️ ALERTA: Tempestade prevista - considere cancelar")
        
        if previsao.velocidade_vento > 40:
            alertas.append("⚠️ ALERTA: Ventos fortes - cuidado com deslocamentos")
        
        if previsao.chance_chuva > 80:
            alertas.append("⚠️ ALERTA: Alta probabilidade de chuva forte")
        
        if previsao.temperatura_max > 35:
            alertas.append("⚠️ ALERTA: Temperatura muito alta - risco de insolação")
        
        if previsao.temperatura_min < 10:
            alertas.append("⚠️ ALERTA: Temperatura muito baixa")
        
        if previsao.visibilidade < 5:
            alertas.append("⚠️ ALERTA: Visibilidade reduzida - cuidado no trânsito")
        
        return alertas
    
    def _sugerir_equipamentos(self, previsao: PrevisaoTempo) -> List[str]:
        """Sugerir equipamentos baseados no clima"""
        
        equipamentos = []
        
        # Equipamentos básicos sempre
        equipamentos.extend(["📱 Celular carregado", "🎒 Mochila impermeável"])
        
        # Por temperatura
        if previsao.temperatura_max > 28:
            equipamentos.extend(["🧴 Protetor solar", "💧 Garrafa de água", "🧢 Chapéu/boné"])
        elif previsao.temperatura_min < 15:
            equipamentos.extend(["🧥 Casaco", "🧤 Luvas (se necessário)"])
        
        # Por chuva
        if previsao.chance_chuva > 50:
            equipamentos.extend(["☂️ Guarda-chuva", "🦺 Capa de chuva", "👟 Calçado impermeável"])
        
        # Por vento
        if previsao.velocidade_vento > 25:
            equipamentos.append("🎒 Mochila bem fechada")
        
        # Por UV
        if previsao.indice_uv > 6:
            equipamentos.extend(["🕶️ Óculos de sol", "👕 Roupa com proteção UV"])
        
        return equipamentos
    
    def _sugerir_melhor_horario(self, previsao: PrevisaoTempo,
                              hora_inicio: time, hora_fim: time) -> Dict[str, Any]:
        """Sugerir melhor horário baseado no clima"""
        
        resultado = {
            'melhor': None,
            'evitar': []
        }
        
        # Horário ideal por temperatura
        if previsao.temperatura_max > 30:
            # Evitar horário de pico de calor
            resultado['evitar'].append((time(11, 0), time(15, 0)))
            resultado['melhor'] = (time(8, 0), time(10, 0))
        
        # Por índice UV
        if previsao.indice_uv > 8:
            resultado['evitar'].append((time(10, 0), time(16, 0)))
        
        # Por chuva (se prevista para horários específicos)
        if previsao.chance_chuva > 70:
            # Sugerir horário de manhã se possível
            if hora_inicio >= time(8, 0):
                resultado['melhor'] = (time(8, 0), time(11, 0))
        
        return resultado
    
    def _gerar_observacoes_clima(self, previsao: PrevisaoTempo, tipo_atividade: str) -> List[str]:
        """Gerar observações específicas"""
        
        observacoes = []
        
        observacoes.append(f"🌤️ Condição prevista: {previsao.condicao.value.replace('_', ' ').title()}")
        observacoes.append(f"🌡️ Temperatura: {previsao.temperatura_min}°C - {previsao.temperatura_max}°C")
        observacoes.append(f"🌧️ Chance de chuva: {previsao.chance_chuva}%")
        
        if previsao.velocidade_vento > 15:
            observacoes.append(f"💨 Vento: {previsao.velocidade_vento} km/h")
        
        if previsao.fonte_dados == 'simulacao':
            observacoes.append("ℹ️ Dados simulados - confirmar previsão atualizada")
        
        return observacoes
    
    def _gerar_recomendacao_padrao(self) -> RecomendacaoClimatica:
        """Gerar recomendação padrão quando não há dados"""
        
        return RecomendacaoClimatica(
            impacto_visita=ImpactoVisita.BOM,
            score_condicoes=0.7,
            recomendacoes=["Verificar condições climáticas antes da visita"],
            alertas=[],
            equipamentos_sugeridos=["📱 Celular", "🎒 Documentos protegidos"],
            melhor_horario=None,
            evitar_horarios=[],
            observacoes=["Dados climáticos não disponíveis"]
        )
    
    def _processar_dados_api(self, data: Dict, municipio: str, data_visita: date) -> PrevisaoTempo:
        """Processar dados da API do OpenWeatherMap"""
        
        # Mapear condições
        condicao_map = {
            'clear': CondicaoClimatica.ENSOLARADO,
            'clouds': CondicaoClimatica.NUBLADO,
            'rain': CondicaoClimatica.CHUVA_MODERADA,
            'thunderstorm': CondicaoClimatica.TEMPESTADE,
            'mist': CondicaoClimatica.NEVOA
        }
        
        main_weather = data['weather'][0]['main'].lower()
        condicao = condicao_map.get(main_weather, CondicaoClimatica.PARCIALMENTE_NUBLADO)
        
        return PrevisaoTempo(
            data=data_visita,
            municipio=municipio,
            temperatura_min=data['main']['temp_min'],
            temperatura_max=data['main']['temp_max'],
            condicao=condicao,
            chance_chuva=data.get('rain', {}).get('1h', 0) * 10,  # Aproximação
            velocidade_vento=data['wind']['speed'] * 3.6,  # m/s para km/h
            umidade=data['main']['humidity'],
            pressao=data['main']['pressure'],
            nascer_sol=datetime.fromtimestamp(data['sys']['sunrise']).time(),
            por_sol=datetime.fromtimestamp(data['sys']['sunset']).time(),
            indice_uv=data.get('uvi', 5),
            visibilidade=data.get('visibility', 10000) / 1000,  # metros para km
            fonte_dados='openweathermap',
            timestamp_atualizacao=datetime.now()
        )
    
    def _processar_dados_api_forecast(self, data: Dict, municipio: str, data_visita: date) -> PrevisaoTempo:
        """Processar dados de previsão da API"""
        
        # Similar ao _processar_dados_api mas para dados de forecast
        # Implementação simplificada
        return self._processar_dados_api(data, municipio, data_visita)