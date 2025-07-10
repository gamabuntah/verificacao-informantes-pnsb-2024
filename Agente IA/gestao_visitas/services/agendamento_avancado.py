from datetime import datetime, timedelta, time, date
from typing import List, Dict, Optional, Tuple
from sqlalchemy import and_, or_
from ..models.agendamento import Visita
from ..models.contatos import Contato
from ..config import MUNICIPIOS, HORARIO_INICIO_DIA, HORARIO_FIM_DIA, DURACAO_PADRAO_VISITA
from ..db import db
from .maps import MapaService

class AgendamentoAvancado:
    """Sistema avançado de agendamento de visitas"""
    
    def __init__(self, mapa_service: Optional[MapaService] = None):
        self.mapa_service = mapa_service
    
    def sugerir_horarios(self, municipio: str, data_visita: date, duracao_minutos: int = 60) -> List[Dict]:
        """Sugere horários disponíveis para uma visita"""
        
        # Buscar visitas já agendadas no dia
        visitas_existentes = Visita.query.filter(
            and_(
                Visita.data == data_visita,
                Visita.municipio == municipio,
                Visita.status.in_(['agendada', 'em preparação', 'em execução'])
            )
        ).order_by(Visita.hora_inicio).all()
        
        horarios_sugeridos = []
        hora_atual = HORARIO_INICIO_DIA
        hora_limite = time(HORARIO_FIM_DIA.hour - 1, 0)  # Uma hora antes do fim
        
        for visita in visitas_existentes:
            # Se há tempo suficiente antes da próxima visita
            if self._minutos_entre_horarios(hora_atual, visita.hora_inicio) >= duracao_minutos:
                horarios_sugeridos.append({
                    'hora_inicio': hora_atual.strftime('%H:%M'),
                    'hora_fim': self._adicionar_minutos(hora_atual, duracao_minutos).strftime('%H:%M'),
                    'disponivel': True,
                    'motivo': 'Horário livre'
                })
            
            # Próximo horário disponível após esta visita
            hora_atual = self._adicionar_minutos(visita.hora_fim, 30)  # 30 min buffer
        
        # Verificar se ainda há tempo no final do dia
        if hora_atual <= hora_limite:
            horarios_sugeridos.append({
                'hora_inicio': hora_atual.strftime('%H:%M'),
                'hora_fim': self._adicionar_minutos(hora_atual, duracao_minutos).strftime('%H:%M'),
                'disponivel': True,
                'motivo': 'Horário livre no final do dia'
            })
        
        return horarios_sugeridos
    
    def otimizar_rota_diaria(self, data_visita: date, origem: str = "Itajaí") -> Dict:
        """Otimiza rota para visitas do dia"""
        
        visitas_dia = Visita.query.filter(
            and_(
                Visita.data == data_visita,
                Visita.status.in_(['agendada', 'em preparação'])
            )
        ).order_by(Visita.hora_inicio).all()
        
        if not visitas_dia:
            return {'visitas': [], 'rota_otimizada': [], 'tempo_total': 0, 'distancia_total': 0}
        
        rota_otimizada = []
        tempo_total = 0
        distancia_total = 0
        local_atual = origem
        
        for visita in visitas_dia:
            if self.mapa_service:
                rota = self.mapa_service.calcular_rota(local_atual, visita.municipio)
                if 'erro' not in rota:
                    tempo_viagem = self._extrair_minutos_duracao(rota.get('duracao', '0 min'))
                    distancia = self._extrair_km_distancia(rota.get('distancia', '0 km'))
                    
                    rota_otimizada.append({
                        'visita_id': visita.id,
                        'municipio': visita.municipio,
                        'informante': visita.informante,
                        'hora_inicio': visita.hora_inicio.strftime('%H:%M'),
                        'tempo_viagem': f"{tempo_viagem} min",
                        'distancia': rota.get('distancia', 'N/A'),
                        'chegada_sugerida': self._calcular_chegada_sugerida(visita.hora_inicio, tempo_viagem)
                    })
                    
                    tempo_total += tempo_viagem
                    distancia_total += distancia
                    local_atual = visita.municipio
        
        return {
            'visitas': len(visitas_dia),
            'rota_otimizada': rota_otimizada,
            'tempo_total_viagem': f"{tempo_total} min",
            'distancia_total': f"{distancia_total:.1f} km",
            'sugestoes': self._gerar_sugestoes_otimizacao(rota_otimizada)
        }
    
    def detectar_conflitos_agendamento(self, municipio: str, data: date, hora_inicio: time, hora_fim: time, excluir_visita_id: int = None) -> Dict:
        """Detecta conflitos de agendamento"""
        
        query = Visita.query.filter(
            and_(
                Visita.data == data,
                or_(
                    # Sobreposição de horários
                    and_(Visita.hora_inicio <= hora_inicio, Visita.hora_fim > hora_inicio),
                    and_(Visita.hora_inicio < hora_fim, Visita.hora_fim >= hora_fim),
                    and_(Visita.hora_inicio >= hora_inicio, Visita.hora_fim <= hora_fim)
                ),
                Visita.status.in_(['agendada', 'em preparação', 'em execução'])
            )
        )
        
        if excluir_visita_id:
            query = query.filter(Visita.id != excluir_visita_id)
        
        conflitos = query.all()
        
        # Conflitos no mesmo município (mais graves)
        conflitos_mesmo_municipio = [v for v in conflitos if v.municipio == municipio]
        
        # Conflitos em municípios próximos (verificar viabilidade de viagem)
        conflitos_viagem = []
        if self.mapa_service:
            for visita in conflitos:
                if visita.municipio != municipio:
                    tempo_viagem = self._calcular_tempo_viagem(municipio, visita.municipio)
                    if tempo_viagem and tempo_viagem < 60:  # Menos de 1h de viagem
                        conflitos_viagem.append({
                            'visita': visita,
                            'tempo_viagem': tempo_viagem,
                            'viavel': self._verificar_viabilidade_viagem(hora_inicio, hora_fim, visita, tempo_viagem)
                        })
        
        return {
            'tem_conflitos': len(conflitos) > 0,
            'conflitos_mesmo_municipio': conflitos_mesmo_municipio,
            'conflitos_viagem': conflitos_viagem,
            'recomendacoes': self._gerar_recomendacoes_conflito(conflitos_mesmo_municipio, conflitos_viagem)
        }
    
    def criar_template_visita(self, tipo_pesquisa: str, tipo_informante: str) -> Dict:
        """Cria template padrão para visita baseado no tipo"""
        
        templates = {
            ('MRS', 'prefeitura'): {
                'duracao_sugerida': 90,
                'materiais_obrigatorios': [
                    'cracha_ibge', 'recibo_entrega', 'questionario_mrs_impresso',
                    'carta_oficial', 'manual_pnsb', 'audio_explicativo'
                ],
                'pontos_atenção': [
                    'Validar prestadores de serviço atual',
                    'Verificar contratos de terceirização',
                    'Mapear entidades de catadores'
                ],
                'observacoes_padrao': 'Visita MRS - Foco em gestão de resíduos sólidos'
            },
            ('MAP', 'prefeitura'): {
                'duracao_sugerida': 60,
                'materiais_obrigatorios': [
                    'cracha_ibge', 'recibo_entrega', 'questionario_map_impresso',
                    'carta_oficial', 'manual_pnsb'
                ],
                'pontos_atenção': [
                    'Verificar sistema de drenagem urbana',
                    'Mapear pontos de alagamento',
                    'Identificar obras de macrodrenagem'
                ],
                'observacoes_padrao': 'Visita MAP - Foco em manejo de águas pluviais'
            }
        }
        
        return templates.get((tipo_pesquisa, tipo_informante), {
            'duracao_sugerida': 60,
            'materiais_obrigatorios': ['cracha_ibge', 'recibo_entrega', 'carta_oficial'],
            'pontos_atenção': ['Verificar informações básicas'],
            'observacoes_padrao': f'Visita {tipo_pesquisa} - {tipo_informante}'
        })
    
    def gerar_cronograma_semanal(self, data_inicio: date, data_fim: date) -> Dict:
        """Gera cronograma otimizado para a semana"""
        
        cronograma = {}
        current_date = data_inicio
        
        while current_date <= data_fim:
            visitas_dia = Visita.query.filter(
                and_(
                    Visita.data == current_date,
                    Visita.status.in_(['agendada', 'em preparação'])
                )
            ).order_by(Visita.hora_inicio).all()
            
            estatisticas_dia = self._calcular_estatisticas_dia(visitas_dia)
            rota_otimizada = self.otimizar_rota_diaria(current_date) if visitas_dia else {}
            
            cronograma[current_date.strftime('%Y-%m-%d')] = {
                'data': current_date.strftime('%d/%m/%Y'),
                'dia_semana': current_date.strftime('%A'),
                'total_visitas': len(visitas_dia),
                'visitas': [v.to_dict() for v in visitas_dia],
                'estatisticas': estatisticas_dia,
                'rota_otimizada': rota_otimizada,
                'carga_trabalho': self._avaliar_carga_trabalho(len(visitas_dia), estatisticas_dia)
            }
            
            current_date += timedelta(days=1)
        
        return {
            'cronograma': cronograma,
            'resumo_semanal': self._gerar_resumo_semanal(cronograma),
            'recomendacoes': self._gerar_recomendacoes_semanais(cronograma)
        }
    
    def validar_disponibilidade_informante(self, municipio: str, data: date, hora: time) -> Dict:
        """Valida disponibilidade baseada no histórico de contatos"""
        
        contato = Contato.query.filter_by(municipio=municipio).first()
        if not contato:
            return {
                'disponivel': None,
                'motivo': 'Informações de contato não encontradas',
                'recomendacao': 'Realizar pesquisa de contatos antes do agendamento'
            }
        
        # Verificar horário de funcionamento
        horario_funcionamento = contato.horario_mais_provavel or contato.horario_chatgpt
        if horario_funcionamento:
            disponivel = self._verificar_horario_funcionamento(hora, horario_funcionamento)
            if not disponivel:
                return {
                    'disponivel': False,
                    'motivo': f'Fora do horário de funcionamento: {horario_funcionamento}',
                    'recomendacao': 'Agendar dentro do horário de funcionamento'
                }
        
        # Verificar histórico de visitas no mesmo dia da semana
        dia_semana = data.weekday()
        visitas_historico = Visita.query.filter(
            and_(
                Visita.municipio == municipio,
                Visita.status == 'realizada'
            )
        ).all()
        
        sucesso_dia_semana = [v for v in visitas_historico if v.data.weekday() == dia_semana]
        
        if visitas_historico and sucesso_dia_semana:
            taxa_sucesso = len(sucesso_dia_semana) / len(visitas_historico) * 100
            return {
                'disponivel': taxa_sucesso > 50,
                'motivo': f'Taxa de sucesso em {data.strftime("%A")}: {taxa_sucesso:.1f}%',
                'recomendacao': 'Boa disponibilidade baseada no histórico' if taxa_sucesso > 50 else 'Considerar outro dia da semana'
            }
        
        return {
            'disponivel': True,
            'motivo': 'Sem histórico anterior, assumindo disponibilidade',
            'recomendacao': 'Confirmar disponibilidade diretamente com o informante'
        }
    
    # Métodos auxiliares
    
    def _minutos_entre_horarios(self, hora1: time, hora2: time) -> int:
        """Calcula minutos entre dois horários"""
        dt1 = datetime.combine(date.today(), hora1)
        dt2 = datetime.combine(date.today(), hora2)
        return int((dt2 - dt1).total_seconds() / 60)
    
    def _adicionar_minutos(self, hora: time, minutos: int) -> time:
        """Adiciona minutos a um horário"""
        dt = datetime.combine(date.today(), hora)
        dt += timedelta(minutes=minutos)
        return dt.time()
    
    def _extrair_minutos_duracao(self, duracao_str: str) -> int:
        """Extrai minutos de string de duração"""
        if 'hour' in duracao_str or 'hora' in duracao_str:
            return int(duracao_str.split()[0]) * 60
        elif 'min' in duracao_str:
            return int(duracao_str.split()[0])
        return 0
    
    def _extrair_km_distancia(self, distancia_str: str) -> float:
        """Extrai quilômetros de string de distância"""
        try:
            return float(distancia_str.replace('km', '').replace(',', '.').strip())
        except:
            return 0.0
    
    def _calcular_chegada_sugerida(self, hora_visita: time, tempo_viagem: int) -> str:
        """Calcula horário sugerido de saída"""
        hora_saida = self._adicionar_minutos(hora_visita, -tempo_viagem - 15)  # 15 min buffer
        return hora_saida.strftime('%H:%M')
    
    def _gerar_sugestoes_otimizacao(self, rota: List[Dict]) -> List[str]:
        """Gera sugestões para otimização da rota"""
        sugestoes = []
        
        if len(rota) > 3:
            sugestoes.append("Considere agrupar visitas por região para reduzir tempo de viagem")
        
        for i, visita in enumerate(rota[:-1]):
            proxima = rota[i + 1]
            if self._extrair_minutos_duracao(visita.get('tempo_viagem', '0 min')) > 45:
                sugestoes.append(f"Viagem longa para {proxima['municipio']} - considere reagendar")
        
        return sugestoes
    
    def _calcular_tempo_viagem(self, origem: str, destino: str) -> Optional[int]:
        """Calcula tempo de viagem entre dois municípios"""
        if not self.mapa_service or origem == destino:
            return 0
        
        resultado = self.mapa_service.estimar_tempo(origem, destino)
        if 'erro' not in resultado:
            return self._extrair_minutos_duracao(resultado.get('duracao', '0 min'))
        return None
    
    def _verificar_viabilidade_viagem(self, hora_inicio: time, hora_fim: time, visita_conflito: Visita, tempo_viagem: int) -> bool:
        """Verifica se é viável fazer viagem entre visitas"""
        
        # Tempo disponível entre visitas
        if hora_inicio < visita_conflito.hora_fim:
            tempo_disponivel = self._minutos_entre_horarios(visita_conflito.hora_fim, hora_inicio)
        else:
            tempo_disponivel = self._minutos_entre_horarios(hora_fim, visita_conflito.hora_inicio)
        
        return tempo_disponivel >= tempo_viagem + 30  # 30 min buffer
    
    def _gerar_recomendacoes_conflito(self, conflitos_municipio: List, conflitos_viagem: List) -> List[str]:
        """Gera recomendações para resolver conflitos"""
        recomendacoes = []
        
        if conflitos_municipio:
            recomendacoes.append("⚠️ Conflito no mesmo município - reagendamento obrigatório")
        
        for conflito in conflitos_viagem:
            if not conflito['viavel']:
                recomendacoes.append(f"⚠️ Tempo insuficiente para viagem de/para {conflito['visita'].municipio}")
            else:
                recomendacoes.append(f"⚡ Viagem viável para {conflito['visita'].municipio} em {conflito['tempo_viagem']} min")
        
        return recomendacoes
    
    def _calcular_estatisticas_dia(self, visitas: List[Visita]) -> Dict:
        """Calcula estatísticas do dia"""
        if not visitas:
            return {'municipios': 0, 'tipos_pesquisa': {}, 'tempo_total_estimado': '0 min'}
        
        municipios_unicos = len(set(v.municipio for v in visitas))
        tipos_pesquisa = {}
        for v in visitas:
            tipos_pesquisa[v.tipo_pesquisa] = tipos_pesquisa.get(v.tipo_pesquisa, 0) + 1
        
        return {
            'municipios': municipios_unicos,
            'tipos_pesquisa': tipos_pesquisa,
            'tempo_total_estimado': f"{len(visitas) * 60} min"
        }
    
    def _avaliar_carga_trabalho(self, num_visitas: int, estatisticas: Dict) -> str:
        """Avalia carga de trabalho do dia"""
        if num_visitas == 0:
            return "Livre"
        elif num_visitas <= 2:
            return "Leve"
        elif num_visitas <= 4:
            return "Moderada"
        elif num_visitas <= 6:
            return "Pesada"
        else:
            return "Sobrecarga"
    
    def _gerar_resumo_semanal(self, cronograma: Dict) -> Dict:
        """Gera resumo da semana"""
        total_visitas = sum(dia['total_visitas'] for dia in cronograma.values())
        municipios_unicos = set()
        tipos_pesquisa = {}
        
        for dia in cronograma.values():
            for visita in dia['visitas']:
                municipios_unicos.add(visita['municipio'])
                tipo = visita['tipo_pesquisa']
                tipos_pesquisa[tipo] = tipos_pesquisa.get(tipo, 0) + 1
        
        return {
            'total_visitas': total_visitas,
            'municipios_cobertos': len(municipios_unicos),
            'tipos_pesquisa': tipos_pesquisa,
            'dias_com_visitas': sum(1 for dia in cronograma.values() if dia['total_visitas'] > 0)
        }
    
    def _gerar_recomendacoes_semanais(self, cronograma: Dict) -> List[str]:
        """Gera recomendações para a semana"""
        recomendacoes = []
        
        dias_sobrecarregados = [
            dia for dia_data, dia in cronograma.items() 
            if dia['carga_trabalho'] in ['Pesada', 'Sobrecarga']
        ]
        
        if dias_sobrecarregados:
            recomendacoes.append(f"⚠️ {len(dias_sobrecarregados)} dia(s) com sobrecarga de trabalho")
        
        dias_livres = [
            dia for dia_data, dia in cronograma.items() 
            if dia['carga_trabalho'] == 'Livre'
        ]
        
        if dias_livres and dias_sobrecarregados:
            recomendacoes.append("💡 Considere redistribuir visitas dos dias sobrecarregados")
        
        return recomendacoes
    
    def _verificar_horario_funcionamento(self, hora: time, horario_funcionamento: str) -> bool:
        """Verifica se horário está dentro do funcionamento"""
        try:
            # Parsing básico de horários como "8h às 17h"
            if 'às' in horario_funcionamento or 'as' in horario_funcionamento:
                partes = horario_funcionamento.lower().replace('h', ':00').split(' às ' if 'às' in horario_funcionamento else ' as ')
                inicio = datetime.strptime(partes[0].strip(), '%H:%M').time()
                fim = datetime.strptime(partes[1].strip(), '%H:%M').time()
                return inicio <= hora <= fim
        except:
            pass
        
        return True  # Assume disponível se não conseguir parsear