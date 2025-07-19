"""
KPIs Estratégicos IBGE - PNSB 2024 (Versão Melhorada)
Adequados especificamente para o contexto da Pesquisa Nacional de Saneamento Básico
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import json
from sqlalchemy import func, and_, or_
from ..models.agendamento import Visita
from ..models.checklist import Checklist  
from ..models.questionarios_obrigatorios import QuestionarioObrigatorio, EntidadeIdentificada, ProgressoQuestionarios
from ..models.contatos import Contato
from .. import db

kpis_pnsb_bp = Blueprint('kpis_pnsb_melhorados', __name__, url_prefix='/api/kpis-pnsb')

@kpis_pnsb_bp.route('/estrategicos', methods=['GET'])
def obter_kpis_estrategicos_pnsb():
    """
    KPIs Estratégicos específicos para PNSB 2024
    Adequados para pesquisa oficial do IBGE
    """
    try:
        hoje = datetime.now()
        prazo_ibge = datetime(2025, 12, 31)
        dias_restantes = (prazo_ibge - hoje).days
        
        # 1. CRONOGRAMA IBGE
        cronograma_ibge = calcular_cronograma_ibge(hoje, prazo_ibge)
        
        # 2. COBERTURA TERRITORIAL
        cobertura_territorial = calcular_cobertura_territorial()
        
        # 3. COMPLIANCE PNSB
        compliance_pnsb = calcular_compliance_pnsb()
        
        # 4. INSTRUMENTOS DE PESQUISA (MRS/MAP)
        instrumentos_pesquisa = calcular_instrumentos_pesquisa()
        
        # 5. QUALIDADE DOS DADOS
        qualidade_dados = calcular_qualidade_dados_pnsb()
        
        # 6. EFETIVIDADE OPERACIONAL
        efetividade_operacional = calcular_efetividade_operacional()
        
        return jsonify({
            'success': True,
            'data': {
                'cronograma_ibge': cronograma_ibge,
                'cobertura_territorial': cobertura_territorial,
                'compliance_pnsb': compliance_pnsb,
                'instrumentos_pesquisa': instrumentos_pesquisa,
                'qualidade_dados': qualidade_dados,
                'efetividade_operacional': efetividade_operacional
            },
            'metadata': {
                'gerado_em': datetime.now().isoformat(),
                'versao': '2.0_pnsb_especializada',
                'cobertura': 'Santa Catarina - 11 municípios',
                'instrumentos': ['MRS', 'MAP']
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao calcular KPIs PNSB: {str(e)}'
        }), 500

def calcular_cronograma_ibge(hoje, prazo_ibge):
    """Indicadores específicos do cronograma IBGE"""
    dias_restantes = max(0, (prazo_ibge - hoje).days)
    dias_totais = (prazo_ibge - datetime(2025, 1, 1)).days
    progresso_temporal = min(100, ((datetime(2025, 1, 1) - hoje).days / dias_totais) * 100)
    
    # Municípios em risco (< 50% progresso com < 30% do prazo)
    municipios_em_risco = calcular_municipios_em_risco(dias_restantes, dias_totais)
    
    # Status do cronograma
    if dias_restantes < 30:
        status = "CRÍTICO"
    elif dias_restantes < 60:
        status = "ATENÇÃO"
    elif municipios_em_risco > 0:
        status = "CUIDADO"
    else:
        status = "NORMAL"
    
    return {
        'dias_restantes': dias_restantes,
        'data_limite': prazo_ibge.strftime('%d/%m/%Y'),
        'progresso_temporal': round(progresso_temporal, 1),
        'municipios_em_risco': municipios_em_risco,
        'status_cronograma': status,
        'fase_atual': determinar_fase_atual(),
        'prazo_proximo_milestone': calcular_proximo_milestone()
    }

def calcular_cobertura_territorial():
    """Cobertura territorial específica para PNSB"""
    municipios_sc = [
        'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas', 'Camboriú',
        'Itajaí', 'Itapema', 'Luiz Alves', 'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
    ]
    
    municipios_concluidos = 0
    municipios_em_andamento = 0
    municipios_criticos = []
    
    for municipio in municipios_sc:
        progresso = calcular_progresso_municipio(municipio)
        
        if progresso >= 100:
            municipios_concluidos += 1
        elif progresso >= 30:
            municipios_em_andamento += 1
        else:
            municipios_criticos.append(municipio)
    
    return {
        'municipios_concluidos': municipios_concluidos,
        'municipios_total': len(municipios_sc),
        'municipios_em_andamento': municipios_em_andamento,
        'percentual_cobertura': round((municipios_concluidos / len(municipios_sc)) * 100, 1),
        'municipios_criticos': municipios_criticos,
        'distribuicao_regional': calcular_distribuicao_regional()
    }

def calcular_compliance_pnsb():
    """Compliance específico para normas PNSB"""
    # Entidades P1 são obrigatórias para o IBGE
    entidades_p1 = EntidadeIdentificada.query.filter_by(prioridade=1).all()
    
    p1_finalizadas = [e for e in entidades_p1 if 
                     e.status_mrs == 'validado_concluido' and 
                     e.status_map == 'validado_concluido']
    
    p1_em_andamento = [e for e in entidades_p1 if 
                      e.status_mrs in ['respondido', 'em_validacao'] or 
                      e.status_map in ['respondido', 'em_validacao']]
    
    p1_nao_iniciadas = [e for e in entidades_p1 if 
                       e.status_mrs == 'nao_iniciado' and 
                       e.status_map == 'nao_iniciado']
    
    # Validação metodológica IBGE
    validacao_ibge = calcular_validacao_metodologica_ibge()
    
    return {
        'p1_finalizadas': len(p1_finalizadas),
        'p1_total': len(entidades_p1),
        'p1_em_andamento': len(p1_em_andamento),
        'p1_nao_iniciadas': len(p1_nao_iniciadas),
        'percentual_p1': round((len(p1_finalizadas) / len(entidades_p1)) * 100, 1) if entidades_p1 else 0,
        'validacao_ibge': validacao_ibge,
        'compliance_metodologico': calcular_compliance_metodologico(),
        'entidades_resistentes': calcular_entidades_resistentes()
    }

def calcular_instrumentos_pesquisa():
    """Análise específica dos instrumentos MRS e MAP"""
    # Dados MRS
    mrs_total = EntidadeIdentificada.query.filter_by(mrs_obrigatorio=True).count()
    mrs_respondidos = EntidadeIdentificada.query.filter(
        EntidadeIdentificada.mrs_obrigatorio == True,
        EntidadeIdentificada.status_mrs.in_(['respondido', 'em_validacao', 'validado_concluido'])
    ).count()
    mrs_validados = EntidadeIdentificada.query.filter(
        EntidadeIdentificada.mrs_obrigatorio == True,
        EntidadeIdentificada.status_mrs == 'validado_concluido'
    ).count()
    
    # Dados MAP
    map_total = EntidadeIdentificada.query.filter_by(map_obrigatorio=True).count()
    map_respondidos = EntidadeIdentificada.query.filter(
        EntidadeIdentificada.map_obrigatorio == True,
        EntidadeIdentificada.status_map.in_(['respondido', 'em_validacao', 'validado_concluido'])
    ).count()
    map_validados = EntidadeIdentificada.query.filter(
        EntidadeIdentificada.map_obrigatorio == True,
        EntidadeIdentificada.status_map == 'validado_concluido'
    ).count()
    
    return {
        'mrs': {
            'obrigatorios': mrs_total,
            'respondidos': mrs_respondidos,
            'validados': mrs_validados,
            'taxa_resposta': round((mrs_respondidos / mrs_total) * 100, 1) if mrs_total > 0 else 0,
            'taxa_validacao': round((mrs_validados / mrs_total) * 100, 1) if mrs_total > 0 else 0,
            'status': avaliar_status_instrumento(mrs_respondidos, mrs_total)
        },
        'map': {
            'obrigatorios': map_total,
            'respondidos': map_respondidos,
            'validados': map_validados,
            'taxa_resposta': round((map_respondidos / map_total) * 100, 1) if map_total > 0 else 0,
            'taxa_validacao': round((map_validados / map_total) * 100, 1) if map_total > 0 else 0,
            'status': avaliar_status_instrumento(map_respondidos, map_total)
        },
        'resumo': {
            'instrumentos_completos': calcular_instrumentos_completos(),
            'cobertura_combinada': calcular_cobertura_combinada(mrs_validados, mrs_total, map_validados, map_total)
        }
    }

def calcular_qualidade_dados_pnsb():
    """Qualidade dos dados específica para critérios PNSB"""
    entidades = EntidadeIdentificada.query.all()
    
    if not entidades:
        return criar_qualidade_vazia()
    
    # Critérios específicos IBGE
    geocodificacao = sum(1 for e in entidades if e.latitude and e.longitude)
    completude_dados = sum(1 for e in entidades if e.nome_entidade and e.endereco)
    validacao_tecnica = sum(1 for e in entidades if 
                           e.status_mrs == 'validado_concluido' or 
                           e.status_map == 'validado_concluido')
    
    # Inconsistências críticas
    inconsistencias = calcular_inconsistencias_criticas(entidades)
    
    # Score metodológico IBGE
    score_metodologico = calcular_score_metodologico_ibge(entidades)
    
    return {
        'score_metodologico': score_metodologico,
        'geocodificacao': {
            'total': geocodificacao,
            'percentual': round((geocodificacao / len(entidades)) * 100, 1)
        },
        'completude_dados': {
            'total': completude_dados,
            'percentual': round((completude_dados / len(entidades)) * 100, 1)
        },
        'validacao_tecnica': {
            'total': validacao_tecnica,
            'percentual': round((validacao_tecnica / len(entidades)) * 100, 1)
        },
        'inconsistencias_criticas': inconsistencias,
        'criterios_ibge': avaliar_criterios_ibge(entidades)
    }

def calcular_efetividade_operacional():
    """Efetividade operacional da equipe de pesquisa"""
    # Visitas realizadas
    visitas_total = Visita.query.count()
    visitas_realizadas = Visita.query.filter_by(status='realizada').count()
    
    # Taxa de contato
    entidades_contactadas = EntidadeIdentificada.query.filter(
        or_(
            EntidadeIdentificada.status_mrs != 'nao_iniciado',
            EntidadeIdentificada.status_map != 'nao_iniciado'
        )
    ).count()
    
    entidades_total = EntidadeIdentificada.query.count()
    
    # Reagendamentos
    reagendamentos = Visita.query.filter_by(status='remarcada').count()
    
    # Entidades resistentes
    entidades_resistentes = EntidadeIdentificada.query.filter(
        and_(
            EntidadeIdentificada.status_mrs == 'nao_iniciado',
            EntidadeIdentificada.status_map == 'nao_iniciado',
            EntidadeIdentificada.identificado_em < (datetime.now() - timedelta(days=14))
        )
    ).count()
    
    return {
        'visitas_realizadas': visitas_realizadas,
        'visitas_total': visitas_total,
        'taxa_conclusao_visitas': round((visitas_realizadas / visitas_total) * 100, 1) if visitas_total > 0 else 0,
        'taxa_contato': round((entidades_contactadas / entidades_total) * 100, 1) if entidades_total > 0 else 0,
        'reagendamentos': reagendamentos,
        'entidades_resistentes': entidades_resistentes,
        'produtividade_semanal': calcular_produtividade_semanal(),
        'eficiencia_equipe': calcular_eficiencia_equipe()
    }

# Funções auxiliares específicas para PNSB
def calcular_municipios_em_risco(dias_restantes, dias_totais):
    """Identifica municípios em risco de não cumprir o prazo"""
    # Implementar lógica específica
    return 0  # Placeholder

def determinar_fase_atual():
    """Determina a fase atual da pesquisa PNSB"""
    # Implementar lógica baseada no cronograma
    return "Coleta de Dados"

def calcular_proximo_milestone():
    """Calcula o próximo marco importante"""
    # Implementar lógica de milestones
    return "Validação P1 - 30 dias"

def calcular_progresso_municipio(municipio):
    """Calcula progresso específico de um município"""
    # Implementar cálculo baseado em entidades do município
    return 0  # Placeholder

def calcular_distribuicao_regional():
    """Analisa distribuição regional da coleta"""
    # Implementar análise regional
    return {}

def calcular_validacao_metodologica_ibge():
    """Calcula aderência às normas metodológicas IBGE"""
    # Implementar validação específica
    return 85.0  # Placeholder

def calcular_compliance_metodologico():
    """Calcula compliance metodológico específico"""
    return 90.0  # Placeholder

def calcular_entidades_resistentes():
    """Conta entidades que estão resistindo à pesquisa"""
    return 3  # Placeholder

def avaliar_status_instrumento(respondidos, total):
    """Avalia status de um instrumento (MRS/MAP)"""
    if total == 0:
        return "N/A"
    
    percentual = (respondidos / total) * 100
    
    if percentual >= 90:
        return "EXCELENTE"
    elif percentual >= 75:
        return "BOM"
    elif percentual >= 50:
        return "REGULAR"
    else:
        return "CRÍTICO"

def calcular_instrumentos_completos():
    """Calcula entidades com ambos instrumentos completos"""
    # Implementar lógica
    return 0  # Placeholder

def calcular_cobertura_combinada(mrs_validados, mrs_total, map_validados, map_total):
    """Calcula cobertura combinada MRS+MAP"""
    # Implementar lógica
    return 0.0  # Placeholder

def criar_qualidade_vazia():
    """Retorna estrutura vazia para qualidade"""
    return {
        'score_metodologico': 0,
        'geocodificacao': {'total': 0, 'percentual': 0},
        'completude_dados': {'total': 0, 'percentual': 0},
        'validacao_tecnica': {'total': 0, 'percentual': 0},
        'inconsistencias_criticas': 0,
        'criterios_ibge': {}
    }

def calcular_inconsistencias_criticas(entidades):
    """Calcula inconsistências críticas nos dados"""
    # Implementar validação de inconsistências
    return 0  # Placeholder

def calcular_score_metodologico_ibge(entidades):
    """Calcula score metodológico específico para IBGE"""
    # Implementar cálculo específico
    return 87.5  # Placeholder

def avaliar_criterios_ibge(entidades):
    """Avalia critérios específicos do IBGE"""
    # Implementar avaliação
    return {}  # Placeholder

def calcular_produtividade_semanal():
    """Calcula produtividade semanal da equipe"""
    # Implementar cálculo
    return 0.0  # Placeholder

def calcular_eficiencia_equipe():
    """Calcula eficiência geral da equipe"""
    # Implementar cálculo
    return 0.0  # Placeholder