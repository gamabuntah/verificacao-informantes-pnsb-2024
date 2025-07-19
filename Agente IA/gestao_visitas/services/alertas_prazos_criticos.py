"""
Sistema de Alertas Proativos para Prazos Críticos PNSB 2024
Monitoramento automático dos deadlines 19/09 e 17/10
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy import func, and_, or_, desc
from ..models.agendamento import Visita
from ..models.questionarios_obrigatorios import QuestionarioObrigatorio, EntidadeIdentificada, ProgressoQuestionarios
from ..db import db
import json
from enum import Enum
from dataclasses import dataclass, asdict

class NivelAlerta(Enum):
    CRITICO = "critico"      # < 7 dias
    URGENTE = "urgente"      # 7-14 dias
    ATENCAO = "atencao"      # 15-30 dias
    NORMAL = "normal"        # > 30 dias

class TipoAlerta(Enum):
    DEADLINE_VISITAS = "deadline_visitas"           # 19/09/2025
    DEADLINE_QUESTIONARIOS = "deadline_questionarios"  # 17/10/2025
    MUNICIPIO_ATRASADO = "municipio_atrasado"
    ENTIDADE_SEM_VISITA = "entidade_sem_visita"
    QUESTIONARIO_PENDENTE = "questionario_pendente"
    META_MENSAL = "meta_mensal"

@dataclass
class AlertaPrazo:
    id: str
    tipo: TipoAlerta
    nivel: NivelAlerta
    titulo: str
    descricao: str
    municipio: str
    entidade: Optional[str] = None
    dias_restantes: int = 0
    data_limite: date = None
    acao_recomendada: str = ""
    metadata: Dict = None
    criado_em: datetime = None

class AlertasPrazosCriticos:
    """Sistema de alertas para monitorar prazos críticos PNSB 2024"""
    
    # Deadlines críticos PNSB 2024
    DEADLINE_VISITAS = date(2025, 9, 19)      # Todas as visitas P1+P2
    DEADLINE_QUESTIONARIOS = date(2025, 10, 17)  # Todos os questionários
    
    def __init__(self):
        self.alertas_ativos = []
        
    def verificar_todos_alertas(self) -> List[AlertaPrazo]:
        """Verifica todos os tipos de alertas críticos"""
        hoje = date.today()
        self.alertas_ativos = []
        
        # 1. Alertas de deadline geral
        self._verificar_deadline_geral()
        
        # 2. Alertas por município
        self._verificar_alertas_municipios()
        
        # 3. Alertas de entidades sem visita
        self._verificar_entidades_sem_visita()
        
        # 4. Alertas de questionários pendentes
        self._verificar_questionarios_pendentes()
        
        # 5. Alertas de metas mensais
        self._verificar_metas_mensais()
        
        # Ordenar por prioridade
        self.alertas_ativos.sort(key=lambda x: (
            0 if x.nivel == NivelAlerta.CRITICO else
            1 if x.nivel == NivelAlerta.URGENTE else
            2 if x.nivel == NivelAlerta.ATENCAO else 3,
            x.dias_restantes
        ))
        
        return self.alertas_ativos
    
    def _verificar_deadline_geral(self):
        """Verifica proximidade dos deadlines principais"""
        hoje = date.today()
        
        # Deadline de visitas (19/09/2025)
        dias_visitas = (self.DEADLINE_VISITAS - hoje).days
        nivel_visitas = self._calcular_nivel_alerta(dias_visitas)
        
        if nivel_visitas in [NivelAlerta.CRITICO, NivelAlerta.URGENTE]:
            self.alertas_ativos.append(AlertaPrazo(
                id=f"deadline_visitas_{hoje}",
                tipo=TipoAlerta.DEADLINE_VISITAS,
                nivel=nivel_visitas,
                titulo=f"⚠️ DEADLINE VISITAS: {dias_visitas} dias restantes",
                descricao=f"Todas as visitas P1 e P2 devem estar concluídas até 19/09/2025. Restam apenas {dias_visitas} dias!",
                municipio="TODOS",
                dias_restantes=dias_visitas,
                data_limite=self.DEADLINE_VISITAS,
                acao_recomendada="Acelerar agendamento e execução de visitas pendentes",
                criado_em=datetime.now()
            ))
        
        # Deadline de questionários (17/10/2025)
        dias_questionarios = (self.DEADLINE_QUESTIONARIOS - hoje).days
        nivel_questionarios = self._calcular_nivel_alerta(dias_questionarios)
        
        if nivel_questionarios in [NivelAlerta.CRITICO, NivelAlerta.URGENTE]:
            self.alertas_ativos.append(AlertaPrazo(
                id=f"deadline_questionarios_{hoje}",
                tipo=TipoAlerta.DEADLINE_QUESTIONARIOS,
                nivel=nivel_questionarios,
                titulo=f"📋 DEADLINE QUESTIONÁRIOS: {dias_questionarios} dias restantes",
                descricao=f"Todos os questionários devem estar finalizados até 17/10/2025. Restam apenas {dias_questionarios} dias!",
                municipio="TODOS",
                dias_restantes=dias_questionarios,
                data_limite=self.DEADLINE_QUESTIONARIOS,
                acao_recomendada="Acelerar follow-up com informantes para finalização",
                criado_em=datetime.now()
            ))
    
    def _verificar_alertas_municipios(self):
        """Verifica alertas específicos por município"""
        municipios_pnsb = [
            'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas',
            'Camboriú', 'Itajaí', 'Itapema', 'Luiz Alves',
            'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
        ]
        
        hoje = date.today()
        
        for municipio in municipios_pnsb:
            # Verificar status das visitas
            visitas = Visita.query.filter_by(municipio=municipio).all()
            
            visitas_pendentes = [v for v in visitas if v.status in ['agendada', 'em preparação']]
            visitas_executadas = [v for v in visitas if v.status in ['realizada', 'em follow-up', 'finalizada']]
            
            # Alerta: município sem visitas agendadas
            if len(visitas) == 0:
                self.alertas_ativos.append(AlertaPrazo(
                    id=f"sem_visitas_{municipio}_{hoje}",
                    tipo=TipoAlerta.ENTIDADE_SEM_VISITA,
                    nivel=NivelAlerta.CRITICO,
                    titulo=f"🚨 {municipio}: SEM VISITAS AGENDADAS",
                    descricao=f"Município {municipio} não possui nenhuma visita agendada",
                    municipio=municipio,
                    dias_restantes=(self.DEADLINE_VISITAS - hoje).days,
                    data_limite=self.DEADLINE_VISITAS,
                    acao_recomendada="Agendar visitas imediatamente",
                    criado_em=datetime.now()
                ))
            
            # Alerta: muitas visitas pendentes próximo ao deadline
            elif len(visitas_pendentes) > 0:
                dias_restantes = (self.DEADLINE_VISITAS - hoje).days
                nivel = self._calcular_nivel_alerta(dias_restantes)
                
                if nivel in [NivelAlerta.CRITICO, NivelAlerta.URGENTE]:
                    self.alertas_ativos.append(AlertaPrazo(
                        id=f"visitas_pendentes_{municipio}_{hoje}",
                        tipo=TipoAlerta.MUNICIPIO_ATRASADO,
                        nivel=nivel,
                        titulo=f"⏰ {municipio}: {len(visitas_pendentes)} visitas pendentes",
                        descricao=f"Município possui {len(visitas_pendentes)} visitas ainda não executadas",
                        municipio=municipio,
                        dias_restantes=dias_restantes,
                        data_limite=self.DEADLINE_VISITAS,
                        acao_recomendada=f"Executar {len(visitas_pendentes)} visitas urgentemente",
                        metadata={
                            "visitas_pendentes": len(visitas_pendentes),
                            "visitas_executadas": len(visitas_executadas)
                        },
                        criado_em=datetime.now()
                    ))
    
    def _verificar_entidades_sem_visita(self):
        """Verifica entidades identificadas mas sem visita agendada"""
        hoje = date.today()
        dias_restantes = (self.DEADLINE_VISITAS - hoje).days
        
        # Buscar entidades identificadas
        entidades = EntidadeIdentificada.query.all()
        
        for entidade in entidades:
            # Verificar se tem visita agendada
            visita_existe = Visita.query.filter(
                and_(
                    Visita.municipio == entidade.municipio,
                    or_(
                        Visita.local.ilike(f"%{entidade.nome_entidade}%"),
                        Visita.observacoes.ilike(f"%{entidade.nome_entidade}%")
                    )
                )
            ).first()
            
            if not visita_existe and entidade.prioridade <= 2:  # Apenas P1 e P2
                nivel = self._calcular_nivel_alerta(dias_restantes)
                
                if nivel in [NivelAlerta.CRITICO, NivelAlerta.URGENTE, NivelAlerta.ATENCAO]:
                    self.alertas_ativos.append(AlertaPrazo(
                        id=f"entidade_sem_visita_{entidade.id}_{hoje}",
                        tipo=TipoAlerta.ENTIDADE_SEM_VISITA,
                        nivel=nivel,
                        titulo=f"🏢 {entidade.municipio}: Entidade P{entidade.prioridade} sem visita",
                        descricao=f"Entidade '{entidade.nome_entidade}' (P{entidade.prioridade}) não possui visita agendada",
                        municipio=entidade.municipio,
                        entidade=entidade.nome_entidade,
                        dias_restantes=dias_restantes,
                        data_limite=self.DEADLINE_VISITAS,
                        acao_recomendada="Agendar visita para esta entidade",
                        metadata={
                            "prioridade": entidade.prioridade,
                            "tipo_entidade": entidade.tipo_entidade,
                            "entidade_id": entidade.id
                        },
                        criado_em=datetime.now()
                    ))
    
    def _verificar_questionarios_pendentes(self):
        """Verifica questionários não finalizados próximos ao deadline"""
        hoje = date.today()
        dias_restantes = (self.DEADLINE_QUESTIONARIOS - hoje).days
        
        # Buscar visitas com questionários pendentes
        visitas_com_questionarios = Visita.query.filter(
            Visita.status.in_(['em follow-up', 'verificação whatsapp', 'resultados visita'])
        ).all()
        
        for visita in visitas_com_questionarios:
            # Calcular dias desde a visita
            if visita.data_atualizacao:
                dias_desde_visita = (hoje - visita.data_atualizacao.date()).days
            else:
                dias_desde_visita = 0
            
            nivel = self._calcular_nivel_alerta(dias_restantes)
            
            # Alerta se questionário está pendente há muito tempo
            if dias_desde_visita > 7 and nivel in [NivelAlerta.CRITICO, NivelAlerta.URGENTE]:
                self.alertas_ativos.append(AlertaPrazo(
                    id=f"questionario_pendente_{visita.id}_{hoje}",
                    tipo=TipoAlerta.QUESTIONARIO_PENDENTE,
                    nivel=nivel,
                    titulo=f"📋 {visita.municipio}: Questionário há {dias_desde_visita} dias",
                    descricao=f"Questionário de '{visita.local}' pendente há {dias_desde_visita} dias",
                    municipio=visita.municipio,
                    entidade=visita.local,
                    dias_restantes=dias_restantes,
                    data_limite=self.DEADLINE_QUESTIONARIOS,
                    acao_recomendada="Fazer follow-up urgente com informante",
                    metadata={
                        "visita_id": visita.id,
                        "status_visita": visita.status,
                        "dias_desde_visita": dias_desde_visita
                    },
                    criado_em=datetime.now()
                ))
    
    def _verificar_metas_mensais(self):
        """Verifica se as metas mensais estão sendo cumpridas"""
        hoje = date.today()
        inicio_mes = hoje.replace(day=1)
        
        # Calcular visitas realizadas no mês
        visitas_mes = Visita.query.filter(
            and_(
                Visita.data_atualizacao >= inicio_mes,
                Visita.status.in_(['realizada', 'finalizada'])
            )
        ).count()
        
        # Calcular meta mensal baseada no tempo restante
        dias_ate_deadline = (self.DEADLINE_VISITAS - hoje).days
        meses_restantes = max(1, dias_ate_deadline / 30)
        
        total_visitas_necessarias = Visita.query.filter(
            Visita.status.in_(['agendada', 'em preparação'])
        ).count()
        
        meta_mensal = max(1, int(total_visitas_necessarias / meses_restantes))
        
        if visitas_mes < meta_mensal * 0.5:  # 50% da meta
            self.alertas_ativos.append(AlertaPrazo(
                id=f"meta_mensal_{hoje.strftime('%Y_%m')}",
                tipo=TipoAlerta.META_MENSAL,
                nivel=NivelAlerta.ATENCAO,
                titulo=f"📊 META MENSAL: {visitas_mes}/{meta_mensal} visitas",
                descricao=f"Realizadas apenas {visitas_mes} de {meta_mensal} visitas necessárias este mês",
                municipio="GERAL",
                dias_restantes=dias_ate_deadline,
                data_limite=self.DEADLINE_VISITAS,
                acao_recomendada="Acelerar ritmo de visitas para cumprir meta",
                metadata={
                    "visitas_realizadas": visitas_mes,
                    "meta_mensal": meta_mensal,
                    "percentual_cumprido": round((visitas_mes / meta_mensal) * 100, 1)
                },
                criado_em=datetime.now()
            ))
    
    def _calcular_nivel_alerta(self, dias_restantes: int) -> NivelAlerta:
        """Calcula o nível de alerta baseado nos dias restantes"""
        if dias_restantes < 7:
            return NivelAlerta.CRITICO
        elif dias_restantes < 14:
            return NivelAlerta.URGENTE
        elif dias_restantes < 30:
            return NivelAlerta.ATENCAO
        else:
            return NivelAlerta.NORMAL
    
    def get_alertas_por_nivel(self, nivel: NivelAlerta) -> List[AlertaPrazo]:
        """Retorna alertas de um nível específico"""
        return [alerta for alerta in self.alertas_ativos if alerta.nivel == nivel]
    
    def get_alertas_por_municipio(self, municipio: str) -> List[AlertaPrazo]:
        """Retorna alertas de um município específico"""
        return [alerta for alerta in self.alertas_ativos if alerta.municipio == municipio]
    
    def get_resumo_alertas(self) -> Dict[str, Any]:
        """Retorna resumo dos alertas ativos"""
        total = len(self.alertas_ativos)
        criticos = len(self.get_alertas_por_nivel(NivelAlerta.CRITICO))
        urgentes = len(self.get_alertas_por_nivel(NivelAlerta.URGENTE))
        atencao = len(self.get_alertas_por_nivel(NivelAlerta.ATENCAO))
        
        return {
            "total_alertas": total,
            "criticos": criticos,
            "urgentes": urgentes,
            "atencao": atencao,
            "dias_ate_deadline_visitas": (self.DEADLINE_VISITAS - date.today()).days,
            "dias_ate_deadline_questionarios": (self.DEADLINE_QUESTIONARIOS - date.today()).days,
            "nivel_risco_geral": "CRÍTICO" if criticos > 0 else "URGENTE" if urgentes > 0 else "ATENÇÃO" if atencao > 0 else "NORMAL"
        }
    
    def exportar_alertas_json(self) -> str:
        """Exporta alertas para JSON"""
        alertas_dict = [asdict(alerta) for alerta in self.alertas_ativos]
        # Converter datetime para string
        for alerta in alertas_dict:
            if alerta['criado_em']:
                alerta['criado_em'] = alerta['criado_em'].isoformat()
            if alerta['data_limite']:
                alerta['data_limite'] = alerta['data_limite'].isoformat()
        
        return json.dumps({
            "alertas": alertas_dict,
            "resumo": self.get_resumo_alertas(),
            "gerado_em": datetime.now().isoformat()
        }, indent=2, ensure_ascii=False)

# Instância global para uso no sistema
sistema_alertas = AlertasPrazosCriticos()