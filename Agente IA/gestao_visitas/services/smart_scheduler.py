"""
Sistema de Sugestões de Horários Otimizadas - PNSB 2024
Sugere horários ideais baseados em disponibilidade, otimização e histórico
"""

from datetime import datetime, timedelta, time, date
from typing import List, Dict, Optional, Tuple, Any
from sqlalchemy import and_, or_, func
from ..models.agendamento import Visita
from ..models.contatos import Contato
from ..db import db
from .conflict_detector import ConflictDetector, TipoConflito, SeveridadeConflito
from dataclasses import dataclass
from enum import Enum
import logging

class CriterioOtimizacao(Enum):
    TEMPO_MINIMO = "tempo_minimo"
    PRODUTIVIDADE_MAXIMA = "produtividade_maxima" 
    MENOR_VIAGEM = "menor_viagem"
    EQUILIBRIO = "equilibrio"
    PRIORIDADE_PNSB = "prioridade_pnsb"

class TipoSugestao(Enum):
    HORARIO_IDEAL = "horario_ideal"
    ALTERNATIVA_VIAVEL = "alternativa_viavel"
    OTIMIZACAO_ROTA = "otimizacao_rota"
    REAGENDAMENTO = "reagendamento"

@dataclass
class SugestaoHorario:
    hora_inicio: time
    hora_fim: time
    score_otimizacao: float
    motivos_escolha: List[str]
    vantagens: List[str]
    consideracoes: List[str]
    conflitos_resolvidos: List[str]
    impacto_viagem: Dict[str, Any]
    tipo_sugestao: TipoSugestao
    metadados: Dict[str, Any]

class SmartScheduler:
    """Sistema inteligente de sugestões de horários otimizadas"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.conflict_detector = ConflictDetector()
        
        # Configurações de otimização
        self.config = {
            'horario_ideal_inicio': time(8, 30),
            'horario_ideal_fim': time(16, 30),
            'slots_horario_minutos': 30,  # Incrementos de 30 min
            'max_sugestoes': 5,
            'buffer_minimo_visitas': 30,  # minutos entre visitas
            'tempo_almoco_inicio': time(12, 0),
            'tempo_almoco_fim': time(13, 0),
            'horarios_preferidos': [
                time(9, 0), time(10, 0), time(14, 0), time(15, 0)
            ],
            'penalidade_horario_cedo': 0.1,
            'penalidade_horario_tarde': 0.15,
            'bonus_horario_ideal': 0.2,
            'peso_viagem': 0.3,
            'peso_produtividade': 0.4,
            'peso_conflitos': 0.3
        }
        
        # Perfis de funcionamento por tipo de entidade
        self.perfis_funcionamento = {
            'prefeitura': {
                'abertura': time(8, 0),
                'fechamento': time(17, 0),
                'almoco': (time(12, 0), time(13, 0)),
                'dias_funcionamento': [0, 1, 2, 3, 4],  # Seg-Sex
                'melhor_horario': time(9, 0),
                'evitar_horarios': [time(12, 0), time(17, 0)]
            },
            'empresa_terceirizada': {
                'abertura': time(8, 0),
                'fechamento': time(18, 0),
                'almoco': (time(12, 0), time(13, 0)),
                'dias_funcionamento': [0, 1, 2, 3, 4, 5],  # Seg-Sab
                'melhor_horario': time(14, 0),
                'evitar_horarios': [time(12, 0)]
            },
            'entidade_catadores': {
                'abertura': time(7, 0),
                'fechamento': time(16, 0),
                'almoco': (time(11, 30), time(12, 30)),
                'dias_funcionamento': [0, 1, 2, 3, 4, 5],
                'melhor_horario': time(9, 0),
                'evitar_horarios': [time(11, 30), time(16, 0)]
            },
            'empresa_nao_vinculada': {
                'abertura': time(8, 0),
                'fechamento': time(17, 30),
                'almoco': (time(12, 0), time(13, 0)),
                'dias_funcionamento': [0, 1, 2, 3, 4],
                'melhor_horario': time(10, 0),
                'evitar_horarios': [time(12, 0), time(17, 0)]
            }
        }
    
    def sugerir_horarios_visita(self, municipio: str, data_visita: date,
                               duracao_minutos: int = 90,
                               tipo_entidade: str = 'prefeitura',
                               prioridade: str = 'p2',
                               criterio: CriterioOtimizacao = CriterioOtimizacao.EQUILIBRIO) -> List[SugestaoHorario]:
        """Sugerir horários otimizados para uma nova visita"""
        
        try:
            self.logger.info(f"🕐 Gerando sugestões para {municipio} em {data_visita}")
            
            # Obter visitas existentes do dia
            visitas_existentes = self._obter_visitas_dia(data_visita)
            
            # Gerar slots de horários disponíveis
            slots_disponiveis = self._gerar_slots_disponiveis(
                data_visita, duracao_minutos, visitas_existentes
            )
            
            # Avaliar cada slot
            sugestoes = []
            for slot_inicio in slots_disponiveis:
                slot_fim = self._adicionar_minutos(slot_inicio, duracao_minutos)
                
                # Calcular score de otimização
                score = self._calcular_score_slot(
                    municipio, slot_inicio, slot_fim, data_visita,
                    visitas_existentes, tipo_entidade, prioridade, criterio
                )
                
                # Gerar metadados da sugestão
                metadados = self._gerar_metadados_slot(
                    municipio, slot_inicio, slot_fim, visitas_existentes, tipo_entidade
                )
                
                sugestao = SugestaoHorario(
                    hora_inicio=slot_inicio,
                    hora_fim=slot_fim,
                    score_otimizacao=score['score_total'],
                    motivos_escolha=score['motivos'],
                    vantagens=score['vantagens'],
                    consideracoes=score['consideracoes'],
                    conflitos_resolvidos=score['conflitos_resolvidos'],
                    impacto_viagem=score['impacto_viagem'],
                    tipo_sugestao=self._classificar_tipo_sugestao(score['score_total']),
                    metadados=metadados
                )
                
                sugestoes.append(sugestao)
            
            # Ordenar por score e retornar as melhores
            sugestoes_ordenadas = sorted(
                sugestoes, 
                key=lambda s: s.score_otimizacao, 
                reverse=True
            )[:self.config['max_sugestoes']]
            
            self.logger.info(f"✅ Geradas {len(sugestoes_ordenadas)} sugestões otimizadas")
            
            return sugestoes_ordenadas
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao gerar sugestões: {str(e)}")
            return []
    
    def otimizar_cronograma_dia(self, data_visita: date,
                               criterio: CriterioOtimizacao = CriterioOtimizacao.EQUILIBRIO) -> Dict[str, Any]:
        """Otimizar cronograma completo de um dia"""
        
        try:
            # Obter todas as visitas do dia
            visitas_dia = self._obter_visitas_dia(data_visita)
            
            if not visitas_dia:
                return {
                    'status': 'dia_livre',
                    'message': 'Nenhuma visita agendada para este dia',
                    'sugestoes': ['Aproveite para planejamento ou adição de novas visitas']
                }
            
            # Analisar cronograma atual
            analise_atual = self._analisar_cronograma_atual(visitas_dia)
            
            # Detectar problemas
            conflitos = self.conflict_detector.detectar_conflitos_dia(data_visita)
            
            # Gerar cronograma otimizado
            cronograma_otimizado = self._gerar_cronograma_otimizado(visitas_dia, criterio)
            
            # Calcular métricas de melhoria
            metricas_melhoria = self._calcular_metricas_melhoria(
                analise_atual, cronograma_otimizado
            )
            
            return {
                'data': data_visita.isoformat(),
                'analise_atual': analise_atual,
                'conflitos_detectados': conflitos['conflitos_detalhados'],
                'cronograma_otimizado': cronograma_otimizado,
                'metricas_melhoria': metricas_melhoria,
                'recomendacoes': self._gerar_recomendacoes_dia(analise_atual, conflitos),
                'score_otimizacao': cronograma_otimizado['score_total']
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro na otimização do cronograma: {str(e)}")
            return {'erro': str(e)}
    
    def sugerir_reagendamento_conflitos(self, data_visita: date) -> Dict[str, Any]:
        """Sugerir reagendamentos para resolver conflitos"""
        
        try:
            # Detectar conflitos
            conflitos_info = self.conflict_detector.detectar_conflitos_dia(data_visita)
            conflitos = conflitos_info['conflitos_detalhados']
            
            if not conflitos:
                return {
                    'status': 'sem_conflitos',
                    'message': 'Nenhum conflito detectado neste dia'
                }
            
            sugestoes_reagendamento = []
            
            # Para cada conflito, gerar sugestões
            for conflito in conflitos:
                if conflito['severidade'] in ['critico', 'alto']:
                    visita_id = conflito['visita_principal']
                    visita = Visita.query.get(visita_id)
                    
                    if visita:
                        # Sugerir novos horários
                        novos_horarios = self.sugerir_horarios_visita(
                            visita.municipio,
                            visita.data,
                            visita.duracao_estimada or 90,
                            visita.tipo_informante or 'prefeitura',
                            visita.prioridade or 'p2'
                        )
                        
                        # Sugerir datas alternativas
                        datas_alternativas = self._sugerir_datas_alternativas(visita)
                        
                        sugestao = {
                            'visita_id': visita_id,
                            'conflito_id': conflito['id'],
                            'municipio': visita.municipio,
                            'horario_atual': f"{visita.hora_inicio} - {visita.hora_fim}",
                            'novos_horarios_mesmo_dia': [
                                {
                                    'horario': f"{s.hora_inicio} - {s.hora_fim}",
                                    'score': s.score_otimizacao,
                                    'vantagens': s.vantagens[:2]  # Top 2 vantagens
                                } for s in novos_horarios[:3]  # Top 3 sugestões
                            ],
                            'datas_alternativas': datas_alternativas,
                            'motivo_reagendamento': conflito['descricao'],
                            'impacto_estimado': conflito['impacto_estimado']
                        }
                        
                        sugestoes_reagendamento.append(sugestao)
            
            return {
                'status': 'conflitos_detectados',
                'total_conflitos': len(conflitos),
                'conflitos_criticos': len([c for c in conflitos if c['severidade'] == 'critico']),
                'sugestoes_reagendamento': sugestoes_reagendamento,
                'resumo_problemas': self._resumir_problemas(conflitos)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro nas sugestões de reagendamento: {str(e)}")
            return {'erro': str(e)}
    
    def _gerar_slots_disponiveis(self, data_visita: date, duracao_minutos: int,
                                visitas_existentes: List[Visita]) -> List[time]:
        """Gerar slots de horários disponíveis"""
        
        slots = []
        hora_atual = self.config['horario_ideal_inicio']
        hora_limite = time(17, 0)  # Até 17h
        incremento = self.config['slots_horario_minutos']
        
        while hora_atual <= hora_limite:
            hora_fim_slot = self._adicionar_minutos(hora_atual, duracao_minutos)
            
            # Verificar se cabe no horário de trabalho
            if hora_fim_slot <= time(18, 0):
                # Verificar disponibilidade
                if self._slot_disponivel(hora_atual, hora_fim_slot, visitas_existentes):
                    slots.append(hora_atual)
            
            hora_atual = self._adicionar_minutos(hora_atual, incremento)
        
        return slots
    
    def _slot_disponivel(self, hora_inicio: time, hora_fim: time,
                        visitas_existentes: List[Visita]) -> bool:
        """Verificar se um slot está disponível"""
        
        for visita in visitas_existentes:
            # Adicionar buffer mínimo
            visita_inicio_buffer = self._subtrair_minutos(
                visita.hora_inicio, self.config['buffer_minimo_visitas']
            )
            visita_fim_buffer = self._adicionar_minutos(
                visita.hora_fim, self.config['buffer_minimo_visitas']
            )
            
            # Verificar sobreposição com buffer
            if not (hora_fim <= visita_inicio_buffer or hora_inicio >= visita_fim_buffer):
                return False
        
        return True
    
    def _calcular_score_slot(self, municipio: str, hora_inicio: time, hora_fim: time,
                           data_visita: date, visitas_existentes: List[Visita],
                           tipo_entidade: str, prioridade: str,
                           criterio: CriterioOtimizacao) -> Dict[str, Any]:
        """Calcular score de otimização para um slot"""
        
        score_components = {
            'horario_ideal': 0,
            'viagem_otima': 0,
            'produtividade': 0,
            'conflitos': 0,
            'funcionamento': 0
        }
        
        motivos = []
        vantagens = []
        consideracoes = []
        conflitos_resolvidos = []
        
        # 1. Score do horário ideal
        perfil = self.perfis_funcionamento.get(tipo_entidade, self.perfis_funcionamento['prefeitura'])
        
        if perfil['melhor_horario'] <= hora_inicio <= self._adicionar_minutos(perfil['melhor_horario'], 60):
            score_components['horario_ideal'] = 0.9
            motivos.append("Horário ideal para este tipo de entidade")
            vantagens.append("Melhor momento para atendimento")
        elif perfil['abertura'] <= hora_inicio <= perfil['fechamento']:
            score_components['horario_ideal'] = 0.7
            motivos.append("Horário de funcionamento normal")
        else:
            score_components['horario_ideal'] = 0.3
            consideracoes.append("Fora do horário ideal de funcionamento")
        
        # 2. Score de viagem
        impacto_viagem = self._calcular_impacto_viagem(
            municipio, hora_inicio, hora_fim, visitas_existentes
        )
        score_components['viagem_otima'] = impacto_viagem['score']
        
        if impacto_viagem['tempo_total'] < 30:
            vantagens.append("Pouco tempo de viagem")
        elif impacto_viagem['tempo_total'] > 90:
            consideracoes.append("Tempo de viagem significativo")
        
        # 3. Score de produtividade
        if self._evita_horario_almoco(hora_inicio, hora_fim):
            score_components['produtividade'] = 0.8
            vantagens.append("Não interfere no horário de almoço")
        else:
            score_components['produtividade'] = 0.4
            consideracoes.append("Coincide com horário de almoço")
        
        # 4. Score de conflitos
        conflitos_detectados = self.conflict_detector.detectar_conflitos_visita(
            municipio=municipio,
            data_visita=data_visita,
            hora_inicio=hora_inicio,
            hora_fim=hora_fim
        )
        
        if not conflitos_detectados:
            score_components['conflitos'] = 1.0
            vantagens.append("Sem conflitos detectados")
        else:
            score_components['conflitos'] = max(0.1, 1.0 - len(conflitos_detectados) * 0.2)
            for conflito in conflitos_detectados:
                consideracoes.append(f"Conflito: {conflito.descricao}")
        
        # 5. Score de funcionamento
        if hora_inicio in perfil.get('evitar_horarios', []):
            score_components['funcionamento'] = 0.3
            consideracoes.append("Horário não recomendado para este tipo de entidade")
        else:
            score_components['funcionamento'] = 0.8
        
        # Calcular score total baseado no critério
        score_total = self._calcular_score_final(score_components, criterio)
        
        return {
            'score_total': score_total,
            'score_components': score_components,
            'motivos': motivos,
            'vantagens': vantagens,
            'consideracoes': consideracoes,
            'conflitos_resolvidos': conflitos_resolvidos,
            'impacto_viagem': impacto_viagem
        }
    
    def _calcular_impacto_viagem(self, municipio: str, hora_inicio: time, hora_fim: time,
                               visitas_existentes: List[Visita]) -> Dict[str, Any]:
        """Calcular impacto de viagem do slot"""
        
        if not visitas_existentes:
            return {
                'tempo_total': 0,
                'score': 1.0,
                'otimizacao': 'Primeira visita do dia'
            }
        
        # Encontrar visitas antes e depois
        visita_anterior = None
        visita_posterior = None
        
        for visita in visitas_existentes:
            if visita.hora_fim <= hora_inicio:
                if not visita_anterior or visita.hora_fim > visita_anterior.hora_fim:
                    visita_anterior = visita
            elif visita.hora_inicio >= hora_fim:
                if not visita_posterior or visita.hora_inicio < visita_posterior.hora_inicio:
                    visita_posterior = visita
        
        tempo_total = 0
        detalhes = []
        
        # Tempo de viagem da visita anterior
        if visita_anterior:
            tempo_anterior = self.conflict_detector._obter_tempo_viagem(
                visita_anterior.municipio, municipio
            )
            tempo_total += tempo_anterior
            detalhes.append(f"{visita_anterior.municipio} → {municipio}: {tempo_anterior}min")
        
        # Tempo de viagem para próxima visita
        if visita_posterior:
            tempo_posterior = self.conflict_detector._obter_tempo_viagem(
                municipio, visita_posterior.municipio
            )
            tempo_total += tempo_posterior
            detalhes.append(f"{municipio} → {visita_posterior.municipio}: {tempo_posterior}min")
        
        # Calcular score (menor tempo = melhor score)
        if tempo_total == 0:
            score = 1.0
        elif tempo_total <= 30:
            score = 0.9
        elif tempo_total <= 60:
            score = 0.7
        elif tempo_total <= 120:
            score = 0.5
        else:
            score = 0.2
        
        return {
            'tempo_total': tempo_total,
            'score': score,
            'detalhes': detalhes,
            'otimizacao': 'Boa posição na rota' if score > 0.7 else 'Requer viagem adicional'
        }
    
    def _evita_horario_almoco(self, hora_inicio: time, hora_fim: time) -> bool:
        """Verificar se evita horário de almoço"""
        
        almoco_inicio = self.config['tempo_almoco_inicio']
        almoco_fim = self.config['tempo_almoco_fim']
        
        return hora_fim <= almoco_inicio or hora_inicio >= almoco_fim
    
    def _calcular_score_final(self, components: Dict[str, float],
                            criterio: CriterioOtimizacao) -> float:
        """Calcular score final baseado no critério"""
        
        # Pesos baseados no critério
        pesos = {
            CriterioOtimizacao.TEMPO_MINIMO: {
                'viagem_otima': 0.5, 'horario_ideal': 0.2, 'produtividade': 0.1,
                'conflitos': 0.1, 'funcionamento': 0.1
            },
            CriterioOtimizacao.PRODUTIVIDADE_MAXIMA: {
                'produtividade': 0.4, 'horario_ideal': 0.3, 'funcionamento': 0.2,
                'conflitos': 0.1, 'viagem_otima': 0.0
            },
            CriterioOtimizacao.MENOR_VIAGEM: {
                'viagem_otima': 0.6, 'conflitos': 0.2, 'horario_ideal': 0.1,
                'produtividade': 0.1, 'funcionamento': 0.0
            },
            CriterioOtimizacao.EQUILIBRIO: {
                'horario_ideal': 0.25, 'viagem_otima': 0.25, 'produtividade': 0.2,
                'conflitos': 0.2, 'funcionamento': 0.1
            },
            CriterioOtimizacao.PRIORIDADE_PNSB: {
                'funcionamento': 0.3, 'horario_ideal': 0.3, 'conflitos': 0.25,
                'produtividade': 0.1, 'viagem_otima': 0.05
            }
        }
        
        peso = pesos.get(criterio, pesos[CriterioOtimizacao.EQUILIBRIO])
        
        score_final = sum(components[comp] * peso[comp] for comp in components)
        
        return round(min(1.0, max(0.0, score_final)), 3)
    
    def _classificar_tipo_sugestao(self, score: float) -> TipoSugestao:
        """Classificar tipo de sugestão baseado no score"""
        
        if score >= 0.8:
            return TipoSugestao.HORARIO_IDEAL
        elif score >= 0.6:
            return TipoSugestao.ALTERNATIVA_VIAVEL
        elif score >= 0.4:
            return TipoSugestao.OTIMIZACAO_ROTA
        else:
            return TipoSugestao.REAGENDAMENTO
    
    def _gerar_metadados_slot(self, municipio: str, hora_inicio: time, hora_fim: time,
                            visitas_existentes: List[Visita], tipo_entidade: str) -> Dict[str, Any]:
        """Gerar metadados adicionais do slot"""
        
        return {
            'municipio': municipio,
            'tipo_entidade': tipo_entidade,
            'posicao_no_dia': len([v for v in visitas_existentes if v.hora_inicio < hora_inicio]) + 1,
            'total_visitas_dia': len(visitas_existentes) + 1,
            'horario_formatado': f"{hora_inicio.strftime('%H:%M')} - {hora_fim.strftime('%H:%M')}",
            'periodo_dia': self._classificar_periodo_dia(hora_inicio)
        }
    
    def _classificar_periodo_dia(self, horario: time) -> str:
        """Classificar período do dia"""
        
        if horario < time(10, 0):
            return "manhã_cedo"
        elif horario < time(12, 0):
            return "manhã"
        elif horario < time(14, 0):
            return "almoço"
        elif horario < time(16, 0):
            return "tarde"
        else:
            return "tarde_final"
    
    def _obter_visitas_dia(self, data_visita: date) -> List[Visita]:
        """Obter visitas do dia"""
        
        return Visita.query.filter(
            and_(
                Visita.data == data_visita,
                Visita.status.in_(['agendada', 'em preparação', 'em execução'])
            )
        ).order_by(Visita.hora_inicio).all()
    
    def _adicionar_minutos(self, horario: time, minutos: int) -> time:
        """Adicionar minutos a um horário"""
        
        dt = datetime.combine(date.today(), horario)
        dt += timedelta(minutes=minutos)
        return dt.time()
    
    def _subtrair_minutos(self, horario: time, minutos: int) -> time:
        """Subtrair minutos de um horário"""
        
        dt = datetime.combine(date.today(), horario)
        dt -= timedelta(minutes=minutos)
        return dt.time()
    
    def _analisar_cronograma_atual(self, visitas_dia: List[Visita]) -> Dict[str, Any]:
        """Analisar cronograma atual do dia"""
        
        if not visitas_dia:
            return {'status': 'vazio'}
        
        # Análise básica
        total_visitas = len(visitas_dia)
        tempo_total_visitas = sum([v.duracao_estimada or 90 for v in visitas_dia])
        
        # Tempo de viagem total
        tempo_viagem = 0
        for i in range(len(visitas_dia) - 1):
            tempo_viagem += self.conflict_detector._obter_tempo_viagem(
                visitas_dia[i].municipio, visitas_dia[i + 1].municipio
            )
        
        # Análise de eficiência
        eficiencia = (tempo_total_visitas / (tempo_total_visitas + tempo_viagem)) * 100 if tempo_viagem > 0 else 100
        
        return {
            'total_visitas': total_visitas,
            'tempo_visitas_minutos': tempo_total_visitas,
            'tempo_viagem_minutos': tempo_viagem,
            'eficiencia_percentual': round(eficiencia, 1),
            'horario_inicio': visitas_dia[0].hora_inicio.strftime('%H:%M'),
            'horario_fim': visitas_dia[-1].hora_fim.strftime('%H:%M'),
            'municipios_visitados': list(set([v.municipio for v in visitas_dia])),
            'status': self._classificar_status_cronograma(eficiencia, total_visitas)
        }
    
    def _classificar_status_cronograma(self, eficiencia: float, total_visitas: int) -> str:
        """Classificar status do cronograma"""
        
        if eficiencia >= 80 and 3 <= total_visitas <= 6:
            return 'otimo'
        elif eficiencia >= 60 and total_visitas <= 7:
            return 'bom'
        elif eficiencia >= 40:
            return 'regular'
        else:
            return 'precisa_otimizacao'
    
    def _gerar_cronograma_otimizado(self, visitas_dia: List[Visita],
                                  criterio: CriterioOtimizacao) -> Dict[str, Any]:
        """Gerar versão otimizada do cronograma"""
        
        # Para cada visita, encontrar melhor horário
        sugestoes_otimizacao = []
        
        for visita in visitas_dia:
            outras_visitas = [v for v in visitas_dia if v.id != visita.id]
            
            sugestoes = self.sugerir_horarios_visita(
                visita.municipio,
                visita.data,
                visita.duracao_estimada or 90,
                visita.tipo_informante or 'prefeitura',
                visita.prioridade or 'p2',
                criterio
            )
            
            if sugestoes:
                melhor_sugestao = sugestoes[0]
                melhoria = melhor_sugestao.score_otimizacao > 0.7
                
                sugestoes_otimizacao.append({
                    'visita_id': visita.id,
                    'municipio': visita.municipio,
                    'horario_atual': f"{visita.hora_inicio} - {visita.hora_fim}",
                    'horario_otimizado': f"{melhor_sugestao.hora_inicio} - {melhor_sugestao.hora_fim}",
                    'score_melhoria': melhor_sugestao.score_otimizacao,
                    'requer_mudanca': melhoria,
                    'vantagens': melhor_sugestao.vantagens[:2]
                })
        
        # Calcular score total do cronograma otimizado
        score_total = sum([s['score_melhoria'] for s in sugestoes_otimizacao]) / len(sugestoes_otimizacao) if sugestoes_otimizacao else 0
        
        return {
            'sugestoes_otimizacao': sugestoes_otimizacao,
            'score_total': round(score_total, 3),
            'visitas_requerem_mudanca': len([s for s in sugestoes_otimizacao if s['requer_mudanca']]),
            'status_otimizacao': 'recomendado' if score_total > 0.7 else 'opcional'
        }
    
    def _calcular_metricas_melhoria(self, analise_atual: Dict, cronograma_otimizado: Dict) -> Dict[str, Any]:
        """Calcular métricas de melhoria"""
        
        if analise_atual.get('status') == 'vazio':
            return {'sem_dados': True}
        
        return {
            'score_atual': analise_atual.get('eficiencia_percentual', 0) / 100,
            'score_otimizado': cronograma_otimizado['score_total'],
            'melhoria_percentual': ((cronograma_otimizado['score_total'] - analise_atual.get('eficiencia_percentual', 0) / 100) * 100),
            'visitas_afetadas': cronograma_otimizado['visitas_requerem_mudanca'],
            'recomendacao': 'Aplicar otimização' if cronograma_otimizado['score_total'] > 0.7 else 'Manter atual'
        }
    
    def _gerar_recomendacoes_dia(self, analise_atual: Dict, conflitos_info: Dict) -> List[str]:
        """Gerar recomendações para o dia"""
        
        recomendacoes = []
        
        if conflitos_info['total_conflitos'] > 0:
            recomendacoes.append(f"🚨 Resolver {conflitos_info['total_conflitos']} conflitos detectados")
        
        if analise_atual.get('eficiencia_percentual', 100) < 60:
            recomendacoes.append("📊 Otimizar sequência de visitas para reduzir tempo de viagem")
        
        if analise_atual.get('total_visitas', 0) > 6:
            recomendacoes.append("⚠️ Considerar redistribuir visitas - dia muito carregado")
        
        if not recomendacoes:
            recomendacoes.append("✅ Cronograma bem estruturado")
        
        return recomendacoes
    
    def _sugerir_datas_alternativas(self, visita: Visita) -> List[Dict[str, Any]]:
        """Sugerir datas alternativas para reagendamento"""
        
        datas_sugeridas = []
        data_atual = visita.data
        
        # Próximos 7 dias úteis
        for i in range(1, 15):
            nova_data = data_atual + timedelta(days=i)
            
            # Pular fins de semana (simplificado)
            if nova_data.weekday() < 5:  # Segunda a sexta
                # Verificar disponibilidade básica
                visitas_dia = self._obter_visitas_dia(nova_data)
                
                if len(visitas_dia) < 5:  # Não muito carregado
                    datas_sugeridas.append({
                        'data': nova_data.isoformat(),
                        'dia_semana': nova_data.strftime('%A'),
                        'visitas_existentes': len(visitas_dia),
                        'disponibilidade': 'boa' if len(visitas_dia) < 3 else 'moderada'
                    })
        
        return datas_sugeridas[:5]  # Top 5 datas
    
    def _resumir_problemas(self, conflitos: List[Dict]) -> Dict[str, int]:
        """Resumir tipos de problemas detectados"""
        
        resumo = {
            'sobreposicao_horario': 0,
            'viagem_impossivel': 0,
            'excesso_visitas': 0,
            'horario_inadequado': 0
        }
        
        for conflito in conflitos:
            tipo = conflito['tipo']
            if 'sobreposicao' in tipo:
                resumo['sobreposicao_horario'] += 1
            elif 'viagem' in tipo:
                resumo['viagem_impossivel'] += 1
            elif 'excesso' in tipo:
                resumo['excesso_visitas'] += 1
            elif 'funcionamento' in tipo:
                resumo['horario_inadequado'] += 1
        
        return resumo