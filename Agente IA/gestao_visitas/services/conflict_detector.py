"""
Sistema de Detecção de Conflitos Automática - PNSB 2024
Detecta e resolve conflitos de agendamento de visitas automaticamente
"""

from datetime import datetime, timedelta, time, date
from typing import List, Dict, Optional, Tuple, Any
from sqlalchemy import and_, or_, func
from ..models.agendamento import Visita
from ..models.contatos import Contato
from ..db import db
from dataclasses import dataclass
from enum import Enum
import logging

class TipoConflito(Enum):
    SOBREPOSICAO_HORARIO = "sobreposicao_horario"
    VIAGEM_IMPOSSIVEL = "viagem_impossivel"
    MESMO_MUNICIPIO_HORARIO = "mesmo_municipio_horario"
    PRAZO_INSUFICIENTE = "prazo_insuficiente"
    EXCESSO_VISITAS_DIA = "excesso_visitas_dia"
    HORARIO_FORA_FUNCIONAMENTO = "horario_fora_funcionamento"

class SeveridadeConflito(Enum):
    CRITICO = "critico"      # Impossível realizar
    ALTO = "alto"            # Muito difícil, precisa reorganizar
    MEDIO = "medio"          # Possível mas não recomendado
    BAIXO = "baixo"          # Apenas um aviso

@dataclass
class Conflito:
    id: str
    tipo: TipoConflito
    severidade: SeveridadeConflito
    visita_principal: int
    visitas_conflitantes: List[int]
    descricao: str
    sugestoes_resolucao: List[str]
    impacto_estimado: str
    dados_detalhes: Dict[str, Any]

class ConflictDetector:
    """Sistema inteligente de detecção de conflitos de agendamento"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Configurações de limites
        self.config = {
            'max_visitas_por_dia': 6,
            'tempo_minimo_entre_visitas': 30,  # minutos
            'tempo_buffer_viagem': 15,  # minutos extras para viagem
            'horario_inicio_padrao': time(8, 0),
            'horario_fim_padrao': time(17, 0),
            'duracao_visita_padrao': 90,  # minutos
            'tempo_almoco_inicio': time(12, 0),
            'tempo_almoco_fim': time(13, 0)
        }
        
        # Tempos de viagem estimados entre municípios (em minutos)
        self.tempos_viagem = {
            ('Itajaí', 'Navegantes'): 15,
            ('Itajaí', 'Balneário Camboriú'): 25,
            ('Itajaí', 'Camboriú'): 30,
            ('Itajaí', 'Penha'): 20,
            ('Itajaí', 'Piçarras'): 25,
            ('Itajaí', 'Bombinhas'): 45,
            ('Itajaí', 'Porto Belo'): 35,
            ('Itajaí', 'Itapema'): 35,
            ('Itajaí', 'Luiz Alves'): 40,
            ('Itajaí', 'Ilhota'): 35,
            ('Navegantes', 'Balneário Camboriú'): 30,
            ('Navegantes', 'Penha'): 10,
            ('Navegantes', 'Piçarras'): 15,
            ('Penha', 'Piçarras'): 10,
            ('Balneário Camboriú', 'Camboriú'): 15,
            ('Balneário Camboriú', 'Itapema'): 20,
            ('Itapema', 'Porto Belo'): 15,
            ('Porto Belo', 'Bombinhas'): 20,
            ('Camboriú', 'Luiz Alves'): 25,
            ('Ilhota', 'Luiz Alves'): 20
        }
    
    def detectar_conflitos_visita(self, visita_id: int = None, 
                                 municipio: str = None, 
                                 data_visita: date = None,
                                 hora_inicio: time = None, 
                                 hora_fim: time = None,
                                 duracao_minutos: int = None) -> List[Conflito]:
        """Detectar conflitos para uma visita específica ou nova"""
        
        conflitos = []
        
        try:
            # Se é uma visita existente, obter dados
            if visita_id:
                visita = Visita.query.get(visita_id)
                if not visita:
                    return []
                
                municipio = visita.municipio
                data_visita = visita.data
                hora_inicio = visita.hora_inicio
                hora_fim = visita.hora_fim
                duracao_minutos = visita.duracao_estimada or self.config['duracao_visita_padrao']
            
            # Validar dados obrigatórios
            if not all([municipio, data_visita, hora_inicio]):
                return []
            
            if not hora_fim and duracao_minutos:
                hora_fim = self._adicionar_minutos(hora_inicio, duracao_minutos)
            
            # Buscar visitas do mesmo dia
            visitas_dia = self._obter_visitas_dia(data_visita, excluir_id=visita_id)
            
            # 1. Detectar sobreposições de horário
            conflitos.extend(self._detectar_sobreposicao_horario(
                municipio, hora_inicio, hora_fim, visitas_dia, visita_id
            ))
            
            # 2. Detectar problemas de viagem
            conflitos.extend(self._detectar_problemas_viagem(
                municipio, hora_inicio, hora_fim, visitas_dia, visita_id
            ))
            
            # 3. Detectar excesso de visitas no dia
            conflitos.extend(self._detectar_excesso_visitas(
                data_visita, visitas_dia, visita_id
            ))
            
            # 4. Detectar horários fora do funcionamento
            conflitos.extend(self._detectar_horario_funcionamento(
                municipio, hora_inicio, hora_fim, visita_id
            ))
            
            self.logger.info(f"🔍 Detectados {len(conflitos)} conflitos para visita em {municipio}")
            
            return conflitos
            
        except Exception as e:
            self.logger.error(f"❌ Erro na detecção de conflitos: {str(e)}")
            return []
    
    def detectar_conflitos_dia(self, data_visita: date) -> Dict[str, Any]:
        """Detectar todos os conflitos de um dia específico"""
        
        try:
            visitas_dia = self._obter_visitas_dia(data_visita)
            conflitos_totais = []
            conflitos_por_visita = {}
            
            # Analisar cada visita
            for visita in visitas_dia:
                conflitos_visita = self.detectar_conflitos_visita(visita.id)
                conflitos_totais.extend(conflitos_visita)
                conflitos_por_visita[visita.id] = conflitos_visita
            
            # Análise geral do dia
            analise_dia = self._analisar_produtividade_dia(visitas_dia)
            
            # Sugestões de otimização
            sugestoes_otimizacao = self._gerar_sugestoes_otimizacao_dia(visitas_dia, conflitos_totais)
            
            return {
                'data': data_visita.isoformat(),
                'total_visitas': len(visitas_dia),
                'total_conflitos': len(conflitos_totais),
                'conflitos_criticos': len([c for c in conflitos_totais if c.severidade == SeveridadeConflito.CRITICO]),
                'conflitos_por_visita': conflitos_por_visita,
                'conflitos_detalhados': [self._conflito_to_dict(c) for c in conflitos_totais],
                'analise_produtividade': analise_dia,
                'sugestoes_otimizacao': sugestoes_otimizacao,
                'status_dia': self._avaliar_status_dia(conflitos_totais)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro na análise do dia {data_visita}: {str(e)}")
            return {'erro': str(e)}
    
    def _detectar_sobreposicao_horario(self, municipio: str, hora_inicio: time, 
                                     hora_fim: time, visitas_dia: List[Visita], 
                                     excluir_id: int = None) -> List[Conflito]:
        """Detectar sobreposições diretas de horário"""
        
        conflitos = []
        
        for visita in visitas_dia:
            if excluir_id and visita.id == excluir_id:
                continue
            
            # Verificar sobreposição
            if self._horarios_sobrepoem(hora_inicio, hora_fim, visita.hora_inicio, visita.hora_fim):
                
                # Determinar severidade
                if municipio == visita.municipio:
                    severidade = SeveridadeConflito.CRITICO
                    descricao = f"Sobreposição total de horários no mesmo município ({municipio})"
                else:
                    tempo_viagem = self._obter_tempo_viagem(municipio, visita.municipio)
                    if tempo_viagem and tempo_viagem > 60:
                        severidade = SeveridadeConflito.CRITICO
                        descricao = f"Sobreposição com viagem impossível ({tempo_viagem}min entre {municipio} e {visita.municipio})"
                    else:
                        severidade = SeveridadeConflito.ALTO
                        descricao = f"Sobreposição com viagem apertada ({tempo_viagem}min entre municípios)"
                
                sugestoes = [
                    "Reagendar uma das visitas para outro horário",
                    "Considerar trocar a ordem das visitas",
                    "Avaliar se é possível reduzir duração de uma visita"
                ]
                
                if municipio != visita.municipio:
                    sugestoes.append("Verificar disponibilidade de transporte mais rápido")
                
                conflito = Conflito(
                    id=f"overlap_{excluir_id or 'nova'}_{visita.id}",
                    tipo=TipoConflito.SOBREPOSICAO_HORARIO,
                    severidade=severidade,
                    visita_principal=excluir_id or 0,
                    visitas_conflitantes=[visita.id],
                    descricao=descricao,
                    sugestoes_resolucao=sugestoes,
                    impacto_estimado="Impossível realizar ambas visitas conforme agendado",
                    dados_detalhes={
                        'municipio_1': municipio,
                        'municipio_2': visita.municipio,
                        'horario_1': f"{hora_inicio} - {hora_fim}",
                        'horario_2': f"{visita.hora_inicio} - {visita.hora_fim}",
                        'tempo_viagem_estimado': self._obter_tempo_viagem(municipio, visita.municipio)
                    }
                )
                
                conflitos.append(conflito)
        
        return conflitos
    
    def _detectar_problemas_viagem(self, municipio: str, hora_inicio: time, 
                                 hora_fim: time, visitas_dia: List[Visita],
                                 excluir_id: int = None) -> List[Conflito]:
        """Detectar problemas de tempo de viagem"""
        
        conflitos = []
        
        # Ordenar visitas por horário
        visitas_ordenadas = sorted(visitas_dia, key=lambda v: v.hora_inicio)
        
        for i, visita in enumerate(visitas_ordenadas):
            if excluir_id and visita.id == excluir_id:
                continue
            
            # Verificar viagem da visita anterior
            if i > 0:
                visita_anterior = visitas_ordenadas[i-1]
                tempo_disponivel = self._calcular_minutos_entre_horarios(
                    visita_anterior.hora_fim, visita.hora_inicio
                )
                tempo_viagem_necessario = self._obter_tempo_viagem(
                    visita_anterior.municipio, visita.municipio
                ) + self.config['tempo_buffer_viagem']
                
                if tempo_disponivel < tempo_viagem_necessario:
                    conflito = Conflito(
                        id=f"travel_{visita_anterior.id}_{visita.id}",
                        tipo=TipoConflito.VIAGEM_IMPOSSIVEL,
                        severidade=SeveridadeConflito.ALTO,
                        visita_principal=visita.id,
                        visitas_conflitantes=[visita_anterior.id],
                        descricao=f"Tempo insuficiente para viagem: {tempo_disponivel}min disponível, {tempo_viagem_necessario}min necessário",
                        sugestoes_resolucao=[
                            "Aumentar intervalo entre visitas",
                            "Reorganizar ordem das visitas por proximidade",
                            "Considerar adiar uma das visitas"
                        ],
                        impacto_estimado="Atraso provável na segunda visita",
                        dados_detalhes={
                            'origem': visita_anterior.municipio,
                            'destino': visita.municipio,
                            'tempo_disponivel': tempo_disponivel,
                            'tempo_necessario': tempo_viagem_necessario,
                            'deficit_tempo': tempo_viagem_necessario - tempo_disponivel
                        }
                    )
                    
                    conflitos.append(conflito)
        
        return conflitos
    
    def _detectar_excesso_visitas(self, data_visita: date, visitas_dia: List[Visita],
                                excluir_id: int = None) -> List[Conflito]:
        """Detectar excesso de visitas em um dia"""
        
        conflitos = []
        total_visitas = len(visitas_dia)
        
        if excluir_id is None:  # Nova visita sendo adicionada
            total_visitas += 1
        
        if total_visitas > self.config['max_visitas_por_dia']:
            conflito = Conflito(
                id=f"excess_{data_visita.isoformat()}",
                tipo=TipoConflito.EXCESSO_VISITAS_DIA,
                severidade=SeveridadeConflito.MEDIO if total_visitas <= self.config['max_visitas_por_dia'] + 2 else SeveridadeConflito.ALTO,
                visita_principal=excluir_id or 0,
                visitas_conflitantes=[v.id for v in visitas_dia],
                descricao=f"Excesso de visitas: {total_visitas} visitas agendadas (máximo recomendado: {self.config['max_visitas_por_dia']})",
                sugestoes_resolucao=[
                    "Redistribuir algumas visitas para outros dias",
                    "Verificar se algumas visitas podem ser combinadas",
                    "Considerar aumentar duração do dia de trabalho",
                    "Priorizar visitas P1 e reagendar P3 para outro dia"
                ],
                impacto_estimado="Sobrecarga de trabalho, possível cansaço e redução de qualidade",
                dados_detalhes={
                    'total_visitas': total_visitas,
                    'maximo_recomendado': self.config['max_visitas_por_dia'],
                    'excesso': total_visitas - self.config['max_visitas_por_dia']
                }
            )
            
            conflitos.append(conflito)
        
        return conflitos
    
    def _detectar_horario_funcionamento(self, municipio: str, hora_inicio: time,
                                      hora_fim: time, visita_id: int = None) -> List[Conflito]:
        """Detectar visitas fora do horário de funcionamento"""
        
        conflitos = []
        
        # Verificar horário muito cedo
        if hora_inicio < self.config['horario_inicio_padrao']:
            conflito = Conflito(
                id=f"early_{visita_id or 'nova'}",
                tipo=TipoConflito.HORARIO_FORA_FUNCIONAMENTO,
                severidade=SeveridadeConflito.MEDIO,
                visita_principal=visita_id or 0,
                visitas_conflitantes=[],
                descricao=f"Visita muito cedo: {hora_inicio} (recomendado após {self.config['horario_inicio_padrao']})",
                sugestoes_resolucao=[
                    "Reagendar para após 8:00",
                    "Confirmar horário de funcionamento da entidade",
                    "Verificar se há flexibilidade de horário"
                ],
                impacto_estimado="Entidade pode estar fechada ou indisponível",
                dados_detalhes={
                    'horario_visita': str(hora_inicio),
                    'horario_recomendado': str(self.config['horario_inicio_padrao'])
                }
            )
            conflitos.append(conflito)
        
        # Verificar horário muito tarde
        if hora_fim > self.config['horario_fim_padrao']:
            conflito = Conflito(
                id=f"late_{visita_id or 'nova'}",
                tipo=TipoConflito.HORARIO_FORA_FUNCIONAMENTO,
                severidade=SeveridadeConflito.MEDIO,
                visita_principal=visita_id or 0,
                visitas_conflitantes=[],
                descricao=f"Visita muito tarde: termina às {hora_fim} (recomendado até {self.config['horario_fim_padrao']})",
                sugestoes_resolucao=[
                    "Reagendar para terminar antes das 17:00",
                    "Reduzir duração da visita se possível",
                    "Confirmar disponibilidade da entidade após horário comercial"
                ],
                impacto_estimado="Entidade pode fechar antes do término",
                dados_detalhes={
                    'horario_fim_visita': str(hora_fim),
                    'horario_recomendado': str(self.config['horario_fim_padrao'])
                }
            )
            conflitos.append(conflito)
        
        # Verificar conflito com horário de almoço
        if (hora_inicio < self.config['tempo_almoco_fim'] and 
            hora_fim > self.config['tempo_almoco_inicio']):
            
            conflito = Conflito(
                id=f"lunch_{visita_id or 'nova'}",
                tipo=TipoConflito.HORARIO_FORA_FUNCIONAMENTO,
                severidade=SeveridadeConflito.BAIXO,
                visita_principal=visita_id or 0,
                visitas_conflitantes=[],
                descricao=f"Visita durante horário de almoço ({self.config['tempo_almoco_inicio']} - {self.config['tempo_almoco_fim']})",
                sugestoes_resolucao=[
                    "Reagendar para antes das 12:00 ou após 13:00",
                    "Confirmar se a entidade funciona durante o almoço",
                    "Considerar levar lanche para não interromper"
                ],
                impacto_estimado="Possível indisponibilidade durante o almoço",
                dados_detalhes={
                    'horario_almoco': f"{self.config['tempo_almoco_inicio']} - {self.config['tempo_almoco_fim']}",
                    'sobreposicao': True
                }
            )
            conflitos.append(conflito)
        
        return conflitos
    
    def _obter_visitas_dia(self, data_visita: date, excluir_id: int = None) -> List[Visita]:
        """Obter todas as visitas de um dia"""
        
        query = Visita.query.filter(
            and_(
                Visita.data == data_visita,
                Visita.status.in_(['agendada', 'em preparação', 'em execução'])
            )
        )
        
        if excluir_id:
            query = query.filter(Visita.id != excluir_id)
        
        return query.order_by(Visita.hora_inicio).all()
    
    def _horarios_sobrepoem(self, inicio1: time, fim1: time, 
                          inicio2: time, fim2: time) -> bool:
        """Verificar se dois horários se sobrepõem"""
        
        return not (fim1 <= inicio2 or inicio1 >= fim2)
    
    def _obter_tempo_viagem(self, origem: str, destino: str) -> int:
        """Obter tempo de viagem entre dois municípios"""
        
        if origem == destino:
            return 5  # Tempo mínimo para deslocamento dentro do município
        
        # Tentar ambas as direções
        tempo = self.tempos_viagem.get((origem, destino))
        if tempo is None:
            tempo = self.tempos_viagem.get((destino, origem))
        
        return tempo or 45  # Tempo padrão se não encontrar
    
    def _adicionar_minutos(self, horario: time, minutos: int) -> time:
        """Adicionar minutos a um horário"""
        
        dt = datetime.combine(date.today(), horario)
        dt += timedelta(minutes=minutos)
        return dt.time()
    
    def _calcular_minutos_entre_horarios(self, inicio: time, fim: time) -> int:
        """Calcular minutos entre dois horários"""
        
        dt_inicio = datetime.combine(date.today(), inicio)
        dt_fim = datetime.combine(date.today(), fim)
        
        if dt_fim < dt_inicio:  # Próximo dia
            dt_fim += timedelta(days=1)
        
        return int((dt_fim - dt_inicio).total_seconds() / 60)
    
    def _analisar_produtividade_dia(self, visitas_dia: List[Visita]) -> Dict[str, Any]:
        """Analisar produtividade do dia"""
        
        if not visitas_dia:
            return {'status': 'dia_livre', 'score': 100}
        
        total_tempo_visitas = sum([90 for _ in visitas_dia])  # 90min por visita
        total_tempo_viagem = 0
        
        # Calcular tempo total de viagem
        for i in range(len(visitas_dia) - 1):
            tempo_viagem = self._obter_tempo_viagem(
                visitas_dia[i].municipio, 
                visitas_dia[i+1].municipio
            )
            total_tempo_viagem += tempo_viagem
        
        tempo_total = total_tempo_visitas + total_tempo_viagem
        eficiencia = (total_tempo_visitas / tempo_total * 100) if tempo_total > 0 else 0
        
        # Calcular score de produtividade
        score = min(100, eficiencia)
        
        if len(visitas_dia) > self.config['max_visitas_por_dia']:
            score -= 20
        
        if total_tempo_viagem > total_tempo_visitas:
            score -= 15
        
        return {
            'total_visitas': len(visitas_dia),
            'tempo_visitas_horas': round(total_tempo_visitas / 60, 1),
            'tempo_viagem_horas': round(total_tempo_viagem / 60, 1),
            'tempo_total_horas': round(tempo_total / 60, 1),
            'eficiencia_percentual': round(eficiencia, 1),
            'score_produtividade': round(score, 1),
            'status': self._classificar_produtividade(score)
        }
    
    def _classificar_produtividade(self, score: float) -> str:
        """Classificar produtividade baseado no score"""
        
        if score >= 85:
            return 'excelente'
        elif score >= 70:
            return 'boa'
        elif score >= 50:
            return 'media'
        else:
            return 'baixa'
    
    def _gerar_sugestoes_otimizacao_dia(self, visitas_dia: List[Visita], 
                                      conflitos: List[Conflito]) -> List[str]:
        """Gerar sugestões de otimização para o dia"""
        
        sugestoes = []
        
        if not visitas_dia:
            return ["Dia livre - aproveite para planejamento ou descanso"]
        
        # Sugestões baseadas em conflitos
        if len(conflitos) > 0:
            sugestoes.append(f"❗ {len(conflitos)} conflitos detectados - revisar agendamentos")
        
        # Sugestões baseadas em número de visitas
        if len(visitas_dia) > self.config['max_visitas_por_dia']:
            sugestoes.append(f"📊 Muitas visitas ({len(visitas_dia)}) - considerar redistribuir")
        elif len(visitas_dia) < 3:
            sugestoes.append("📈 Poucas visitas - oportunidade para adicionar mais")
        
        # Sugestões baseadas em geografia
        municipios_unicos = set([v.municipio for v in visitas_dia])
        if len(municipios_unicos) > 4:
            sugestoes.append("🗺️ Muitos municípios - otimizar rota por proximidade")
        
        # Sugestões baseadas em horários
        horarios = [(v.hora_inicio, v.hora_fim) for v in visitas_dia]
        if any(h[0] < time(8, 30) for h in horarios):
            sugestoes.append("🌅 Visitas muito cedo - confirmar funcionamento")
        if any(h[1] > time(16, 30) for h in horarios):
            sugestoes.append("🌆 Visitas muito tarde - confirmar disponibilidade")
        
        return sugestoes or ["✅ Cronograma bem organizado"]
    
    def _avaliar_status_dia(self, conflitos: List[Conflito]) -> str:
        """Avaliar status geral do dia"""
        
        conflitos_criticos = sum(1 for c in conflitos if c.severidade == SeveridadeConflito.CRITICO)
        conflitos_altos = sum(1 for c in conflitos if c.severidade == SeveridadeConflito.ALTO)
        
        if conflitos_criticos > 0:
            return 'critico'
        elif conflitos_altos > 2:
            return 'problematico'
        elif len(conflitos) > 3:
            return 'atencao'
        elif len(conflitos) > 0:
            return 'revisao'
        else:
            return 'otimo'
    
    def _conflito_to_dict(self, conflito: Conflito) -> Dict[str, Any]:
        """Converter conflito para dicionário"""
        
        return {
            'id': conflito.id,
            'tipo': conflito.tipo.value,
            'severidade': conflito.severidade.value,
            'visita_principal': conflito.visita_principal,
            'visitas_conflitantes': conflito.visitas_conflitantes,
            'descricao': conflito.descricao,
            'sugestoes_resolucao': conflito.sugestoes_resolucao,
            'impacto_estimado': conflito.impacto_estimado,
            'dados_detalhes': conflito.dados_detalhes
        }