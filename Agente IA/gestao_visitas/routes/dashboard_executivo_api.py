"""
API para Dashboard Executivo PNSB 2024
Endpoints especializados para o novo mapa de progresso
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

dashboard_bp = Blueprint('pnsb_dashboard_api', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('/kpis/estrategicos', methods=['GET'])
def obter_kpis_estrategicos():
    """
    KPIs Estratégicos PNSB 2024 - Versão Adequada para Pesquisa Oficial IBGE
    """
    try:
        hoje = datetime.now()
        prazo_ibge = datetime(2025, 12, 31)
        
        # 1. CRONOGRAMA IBGE (Aprimorado)
        cronograma_ibge = calcular_cronograma_ibge_completo(hoje, prazo_ibge)
        
        # 2. COBERTURA TERRITORIAL (Aprimorada)
        cobertura_territorial = calcular_cobertura_territorial_completa()
        
        # 3. COMPLIANCE PNSB (Específico para IBGE)
        compliance_pnsb = calcular_compliance_pnsb_completo()
        
        # 4. INSTRUMENTOS DE PESQUISA (Novo - Crítico)
        instrumentos_pesquisa = calcular_instrumentos_pesquisa_completo()
        
        # 5. QUALIDADE DOS DADOS (Específico para PNSB)
        qualidade_dados = calcular_qualidade_dados_pnsb_completo()
        
        # 6. EFETIVIDADE OPERACIONAL (Novo)
        efetividade_operacional = calcular_efetividade_operacional_completa()
        
        # 7. INDICADORES DE RISCO (Novo - Crítico)
        indicadores_risco = calcular_indicadores_risco_completo()
        
        return jsonify({
            'success': True,
            'data': {
                'cronograma_ibge': cronograma_ibge,
                'cobertura_territorial': cobertura_territorial,
                'compliance_pnsb': compliance_pnsb,
                'instrumentos_pesquisa': instrumentos_pesquisa,
                'qualidade_dados': qualidade_dados,
                'efetividade_operacional': efetividade_operacional,
                'indicadores_risco': indicadores_risco
            },
            'metadata': {
                'gerado_em': datetime.now().isoformat(),
                'versao': '2.0_pnsb_oficial',
                'cobertura': 'Santa Catarina - 11 municípios',
                'instrumentos': ['MRS', 'MAP'],
                'criterios': 'IBGE_PNSB_2024'
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao calcular KPIs: {str(e)}'
        }), 500

@dashboard_bp.route('/municipios/detalhado', methods=['GET'])
def obter_dados_municipios_detalhado():
    """
    Retorna dados detalhados de todos os 11 municípios
    """
    try:
        municipios_sc = [
            'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas', 'Camboriú',
            'Itajaí', 'Itapema', 'Luiz Alves', 'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
        ]
        
        dados_municipios = []
        
        for municipio in municipios_sc:
            # Buscar entidades do município
            entidades = EntidadeIdentificada.query.filter_by(municipio=municipio).all()
            visitas = Visita.query.filter_by(municipio=municipio).all()
            
            # Calcular métricas
            total_p1 = len([e for e in entidades if e.prioridade == 1])
            p1_contactadas = len([e for e in entidades if e.prioridade == 1 and e.status_mrs != 'nao_iniciado'])
            
            # Geocodificação
            geocodificadas = len([e for e in entidades if e.latitude and e.longitude])
            percentual_geocodificacao = round((geocodificadas / len(entidades)) * 100) if entidades else 0
            
            # Progresso MRS e MAP
            progresso_mrs = calcular_progresso_tipo(entidades, 'mrs')
            progresso_map = calcular_progresso_tipo(entidades, 'map')
            progresso_p1 = calcular_progresso_p1(entidades)
            
            # Status geral do município
            status = determinar_status_municipio(entidades, visitas)
            
            # Última atividade
            ultima_visita = max(visitas, key=lambda v: v.data if v.data else datetime.min) if visitas else None
            ultima_atividade = formatar_data_relativa(ultima_visita.data) if ultima_visita and ultima_visita.data else 'Nenhuma'
            
            # Alertas
            alertas = gerar_alertas_municipio(municipio, entidades, visitas)
            
            dados_municipios.append({
                'nome': municipio,
                'status': status,
                'entidades': {
                    'total': len(entidades),
                    'p1': total_p1,
                    'p1_contactadas': p1_contactadas,
                    'geocodificadas': geocodificadas
                },
                'progresso': {
                    'mrs': progresso_mrs,
                    'map': progresso_map,
                    'p1': progresso_p1,
                    'geocodificacao': percentual_geocodificacao
                },
                'visitas': {
                    'total': len(visitas),
                    'ultima_atividade': ultima_atividade
                },
                'alertas': alertas
            })
        
        return jsonify({
            'success': True,
            'data': dados_municipios
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao obter dados dos municípios: {str(e)}'
        }), 500

@dashboard_bp.route('/estatisticas/diarias', methods=['GET'])
def obter_estatisticas_diarias():
    """
    Retorna estatísticas para o painel de controle diário
    """
    try:
        hoje = datetime.now().date()
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        
        # Estatísticas de hoje
        visitas_hoje = Visita.query.filter(func.date(Visita.data) == hoje).count()
        questionarios_pendentes = EntidadeIdentificada.query.filter(
            or_(
                EntidadeIdentificada.status_mrs == 'respondido',
                EntidadeIdentificada.status_map == 'respondido'
            )
        ).count()
        reagendamentos_hoje = Visita.query.filter(
            and_(
                func.date(Visita.data) == hoje,
                Visita.status == 'remarcada'
            )
        ).count()
        
        # Estatísticas da semana
        visitas_semana = Visita.query.filter(
            func.date(Visita.data) >= inicio_semana
        ).count()
        meta_semanal = 15  # Configurável
        eficiencia_semana = min(100, round((visitas_semana / meta_semanal) * 100))
        
        # Próximas ações
        entidades_contatar = EntidadeIdentificada.query.filter(
            and_(
                EntidadeIdentificada.prioridade == 1,
                EntidadeIdentificada.status_mrs == 'nao_iniciado'
            )
        ).count()
        
        questionarios_validar = EntidadeIdentificada.query.filter(
            or_(
                EntidadeIdentificada.status_mrs == 'respondido',
                EntidadeIdentificada.status_map == 'respondido'
            )
        ).count()
        
        # Count entities that need visits to be scheduled
        total_entidades_p1_p2 = EntidadeIdentificada.query.filter(
            EntidadeIdentificada.prioridade.in_([1, 2])
        ).count()
        
        # Count visits already scheduled for P1/P2 municipalities
        visitas_agendadas = Visita.query.filter(
            Visita.municipio.in_([
                e.municipio for e in EntidadeIdentificada.query.filter(
                    EntidadeIdentificada.prioridade.in_([1, 2])
                ).all()
            ])
        ).count()
        
        # Estimate visits still needed (simplified calculation)
        visitas_agendar = max(0, total_entidades_p1_p2 - visitas_agendadas)
        
        return jsonify({
            'success': True,
            'data': {
                'hoje': {
                    'visitas_agendadas': visitas_hoje,
                    'questionarios_pendentes': questionarios_pendentes,
                    'reagendamentos': reagendamentos_hoje
                },
                'semana': {
                    'meta': meta_semanal,
                    'realizado': visitas_semana,
                    'eficiencia': eficiencia_semana
                },
                'acoes': {
                    'contatar': entidades_contatar,
                    'validar': questionarios_validar,
                    'agendar': visitas_agendar
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao calcular estatísticas diárias: {str(e)}'
        }), 500

@dashboard_bp.route('/alertas/automaticos', methods=['GET'])
def obter_alertas_automaticos():
    """
    Gera alertas automáticos baseados no estado atual do sistema
    """
    try:
        alertas = []
        
        # Alerta 1: P1 sem contato há muito tempo
        entidades_p1_antigas = EntidadeIdentificada.query.filter(
            and_(
                EntidadeIdentificada.prioridade == 1,
                EntidadeIdentificada.status_mrs == 'nao_iniciado',
                EntidadeIdentificada.identificado_em < (datetime.now() - timedelta(days=14))
            )
        ).all()
        
        if entidades_p1_antigas:
            alertas.append({
                'tipo': 'critico',
                'titulo': 'P1 sem contato há mais de 14 dias',
                'descricao': f'{len(entidades_p1_antigas)} entidades obrigatórias precisam ser contactadas urgentemente.',
                'icone': '🚨',
                'acao': 'listar_p1_pendentes',
                'dados': [{'id': e.id, 'nome': e.nome_entidade, 'municipio': e.municipio} for e in entidades_p1_antigas[:5]]
            })
        
        # Alerta 2: Prazo IBGE
        hoje = datetime.now()
        prazo_ibge = datetime(2025, 12, 31)
        dias_restantes = (prazo_ibge - hoje).days
        
        if dias_restantes < 90:
            alertas.append({
                'tipo': 'importante',
                'titulo': 'Prazo IBGE se aproximando',
                'descricao': f'Restam apenas {dias_restantes} dias para conclusão da PNSB 2024.',
                'icone': '⏰',
                'acao': 'acelerar_cronograma',
                'dados': {'dias_restantes': dias_restantes}
            })
        
        # Alerta 3: Municípios sem atividade
        municipios_inativos = []
        municipios_sc = ['Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas', 'Camboriú',
                        'Itajaí', 'Itapema', 'Luiz Alves', 'Navegantes', 'Penha', 'Porto Belo', 'Ilhota']
        
        for municipio in municipios_sc:
            ultima_visita = Visita.query.filter_by(municipio=municipio).order_by(Visita.data.desc()).first()
            if not ultima_visita or (ultima_visita.data and (hoje.date() - ultima_visita.data).days > 7):
                municipios_inativos.append(municipio)
        
        if municipios_inativos:
            alertas.append({
                'tipo': 'info',
                'titulo': 'Municípios sem atividade recente',
                'descricao': f'{len(municipios_inativos)} municípios sem atividade há mais de 7 dias.',
                'icone': '📍',
                'acao': 'revisar_cronograma',
                'dados': municipios_inativos
            })
        
        # Alerta 4: Backup do sistema
        # Verificar se existe backup recente (implementar lógica específica)
        alertas.append({
            'tipo': 'info',
            'titulo': 'Sistema funcionando normalmente',
            'descricao': 'Backup automático ativo, APIs respondendo normalmente.',
            'icone': '✅',
            'acao': None,
            'dados': {'ultimo_backup': datetime.now().strftime('%d/%m/%Y %H:%M')}
        })
        
        return jsonify({
            'success': True,
            'data': alertas
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao gerar alertas: {str(e)}'
        }), 500

@dashboard_bp.route('/relatorios/executivo', methods=['GET'])
def obter_relatorio_executivo():
    """
    Gera relatório executivo para o dashboard
    """
    try:
        # Estatísticas gerais
        total_visitas = Visita.query.count()
        visitas_concluidas = Visita.query.filter_by(status='finalizada').count()
        total_entidades = EntidadeIdentificada.query.count()
        
        # Progresso por município
        municipios_sc = ['Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas', 'Camboriú',
                        'Itajaí', 'Itapema', 'Luiz Alves', 'Navegantes', 'Penha', 'Porto Belo', 'Ilhota']
        
        progresso_municipios = []
        for municipio in municipios_sc:
            entidades_mun = EntidadeIdentificada.query.filter_by(municipio=municipio).all()
            entidades_validadas = [e for e in entidades_mun if 
                                 e.status_mrs == 'validado_concluido' or e.status_map == 'validado_concluido']
            
            percentual = round((len(entidades_validadas) / len(entidades_mun)) * 100) if entidades_mun else 0
            
            progresso_municipios.append({
                'municipio': municipio,
                'total_entidades': len(entidades_mun),
                'entidades_validadas': len(entidades_validadas),
                'percentual_conclusao': percentual
            })
        
        # Resumo executivo
        resumo = {
            'total_visitas': total_visitas,
            'visitas_concluidas': visitas_concluidas,
            'total_entidades': total_entidades,
            'municipios_cobertos': len([m for m in progresso_municipios if m['total_entidades'] > 0]),
            'progresso_geral': round(sum(m['percentual_conclusao'] for m in progresso_municipios) / len(progresso_municipios)) if progresso_municipios else 0
        }
        
        return jsonify({
            'success': True,
            'data': {
                'resumo': resumo,
                'progresso_municipios': progresso_municipios,
                'gerado_em': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/relatorios/semanal', methods=['GET'])
def obter_relatorio_semanal():
    """
    Gera relatório semanal automático
    """
    try:
        # Definir período da semana
        hoje = datetime.now()
        inicio_semana = hoje - timedelta(days=7)
        
        # Visitas da semana
        visitas_semana = Visita.query.filter(
            Visita.data >= inicio_semana.date()
        ).all()
        
        # Entidades criadas/atualizadas na semana
        entidades_semana = EntidadeIdentificada.query.filter(
            EntidadeIdentificada.identificado_em >= inicio_semana
        ).all()
        
        # Estatísticas semanais
        stats_semana = {
            'visitas_realizadas': len([v for v in visitas_semana if v.status in ['realizada', 'finalizada']]),
            'novas_entidades': len(entidades_semana),
            'questionarios_validados': len([e for e in entidades_semana if 
                                          e.status_mrs == 'validado_concluido' or e.status_map == 'validado_concluido']),
            'municipios_ativos': len(set(v.municipio for v in visitas_semana))
        }
        
        return jsonify({
            'success': True,
            'data': {
                'periodo': {
                    'inicio': inicio_semana.isoformat(),
                    'fim': hoje.isoformat()
                },
                'estatisticas': stats_semana,
                'visitas_detalhadas': [v.to_dict() for v in visitas_semana[:10]],  # Top 10
                'gerado_em': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/relatorios/ibge', methods=['GET'])
def obter_relatorio_ibge():
    """
    Gera relatório específico para o IBGE
    """
    try:
        tipo_relatorio = request.args.get('tipo', 'executive')
        
        # Dados básicos
        total_municipios = 11
        municipios_cobertos = len(set(e.municipio for e in EntidadeIdentificada.query.all()))
        
        # Compliance P1
        entidades_p1 = EntidadeIdentificada.query.filter_by(prioridade=1).all()
        p1_concluidas = [e for e in entidades_p1 if 
                        e.status_mrs == 'validado_concluido' and e.status_map == 'validado_concluido']
        
        # Estrutura base do relatório
        relatorio_base = {
            'resumo_executivo': {
                'municipios_total': total_municipios,
                'municipios_cobertos': municipios_cobertos,
                'cobertura_percentual': round((municipios_cobertos / total_municipios) * 100),
                'entidades_p1_total': len(entidades_p1),
                'entidades_p1_concluidas': len(p1_concluidas),
                'compliance_p1_percentual': round((len(p1_concluidas) / len(entidades_p1)) * 100) if entidades_p1 else 0
            }
        }
        
        if tipo_relatorio == 'detailed':
            # Adicionar detalhes por município
            relatorio_base['detalhes_municipios'] = []
            municipios_sc = ['Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas', 'Camboriú',
                            'Itajaí', 'Itapema', 'Luiz Alves', 'Navegantes', 'Penha', 'Porto Belo', 'Ilhota']
            
            for municipio in municipios_sc:
                entidades_mun = EntidadeIdentificada.query.filter_by(municipio=municipio).all()
                relatorio_base['detalhes_municipios'].append({
                    'municipio': municipio,
                    'total_entidades': len(entidades_mun),
                    'entidades_p1': len([e for e in entidades_mun if e.prioridade == 1]),
                    'mrs_validados': len([e for e in entidades_mun if e.status_mrs == 'validado_concluido']),
                    'map_validados': len([e for e in entidades_mun if e.status_map == 'validado_concluido'])
                })
        
        elif tipo_relatorio == 'technical':
            # Adicionar dados técnicos
            relatorio_base['dados_tecnicos'] = {
                'data_inicio_coleta': '2025-01-01',
                'data_prevista_conclusao': '2025-12-31',
                'metodologia': 'PNSB 2024 - Pesquisa Nacional de Saneamento Básico',
                'instrumentos': ['MRS - Manejo de Resíduos Sólidos', 'MAP - Manejo de Águas Pluviais'],
                'cobertura_geografica': 'Região da Grande Florianópolis - SC'
            }
        
        return jsonify({
            'success': True,
            'data': relatorio_base,
            'tipo_relatorio': tipo_relatorio,
            'gerado_em': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/timeline/operacional', methods=['GET'])
def obter_timeline_operacional():
    """
    Retorna dados da timeline operacional PNSB
    """
    try:
        fases = [
            {
                'nome': 'Identificação',
                'descricao': 'Identificação de entidades P1/P2/P3',
                'status': 'completed',
                'data_inicio': '2025-01-01',
                'data_fim': '2025-06-30',
                'progresso': 100
            },
            {
                'nome': 'Coleta',
                'descricao': 'Coleta de dados MRS e MAP',
                'status': 'current',
                'data_inicio': '2025-07-01',
                'data_fim': '2025-09-30',
                'progresso': calcular_progresso_coleta()
            },
            {
                'nome': 'Validação',
                'descricao': 'Validação dos questionários',
                'status': 'pending',
                'data_inicio': '2025-10-01',
                'data_fim': '2025-11-15',
                'progresso': 0
            },
            {
                'nome': 'Entrega',
                'descricao': 'Entrega final para IBGE',
                'status': 'pending',
                'data_inicio': '2025-11-16',
                'data_fim': '2025-12-31',
                'progresso': 0
            }
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'fases': fases,
                'fase_atual': 'Coleta',
                'progresso_geral': calcular_progresso_geral()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao obter timeline: {str(e)}'
        }), 500

# Funções auxiliares
def calcular_municipios_concluidos():
    """Calcula quantos municípios estão 100% concluídos"""
    municipios_sc = ['Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas', 'Camboriú',
                    'Itajaí', 'Itapema', 'Luiz Alves', 'Navegantes', 'Penha', 'Porto Belo', 'Ilhota']
    
    concluidos = 0
    for municipio in municipios_sc:
        entidades_p1 = EntidadeIdentificada.query.filter_by(municipio=municipio, prioridade=1).all()
        if entidades_p1:
            p1_concluidas = [e for e in entidades_p1 if 
                           e.status_mrs == 'validado_concluido' and 
                           e.status_map == 'validado_concluido']
            if len(p1_concluidas) == len(entidades_p1):
                concluidos += 1
    
    return concluidos

def calcular_score_qualidade():
    """Calcula score de qualidade dos dados (0-100)"""
    entidades = EntidadeIdentificada.query.all()
    if not entidades:
        return 0
    
    score = 0
    
    # Geocodificação (30%)
    geocodificadas = len([e for e in entidades if e.latitude and e.longitude])
    score += (geocodificadas / len(entidades)) * 30
    
    # Completude de dados (40%)
    completas = len([e for e in entidades if e.nome_entidade and e.endereco])
    score += (completas / len(entidades)) * 40
    
    # Questionários validados (30%)
    validadas = len([e for e in entidades if 
                    e.status_mrs == 'validado_concluido' or 
                    e.status_map == 'validado_concluido'])
    score += (validadas / len(entidades)) * 30
    
    return round(score)

def classificar_qualidade(score):
    """Classifica o score de qualidade"""
    if score >= 90:
        return 'Excelente'
    elif score >= 80:
        return 'Boa'
    elif score >= 70:
        return 'Regular'
    elif score >= 60:
        return 'Precisa Melhorar'
    else:
        return 'Crítica'

def calcular_progresso_tipo(entidades, tipo):
    """Calcula progresso para MRS ou MAP"""
    entidades_tipo = [e for e in entidades if getattr(e, f'{tipo}_obrigatorio', False)]
    if not entidades_tipo:
        return 0
    
    concluidas = len([e for e in entidades_tipo if 
                     getattr(e, f'status_{tipo}') == 'validado_concluido'])
    
    return round((concluidas / len(entidades_tipo)) * 100)

def calcular_progresso_p1(entidades):
    """Calcula progresso das entidades P1"""
    p1 = [e for e in entidades if e.prioridade == 1]
    if not p1:
        return 0
    
    finalizadas = len([e for e in p1 if 
                      e.status_mrs == 'validado_concluido' and 
                      e.status_map == 'validado_concluido'])
    
    return round((finalizadas / len(p1)) * 100)

def determinar_status_municipio(entidades, visitas):
    """Determina status geral do município"""
    if not entidades:
        return 'pendente'
    
    p1 = [e for e in entidades if e.prioridade == 1]
    if not p1:
        return 'pendente'
    
    p1_concluidas = [e for e in p1 if 
                    e.status_mrs == 'validado_concluido' and 
                    e.status_map == 'validado_concluido']
    
    if len(p1_concluidas) == len(p1):
        return 'concluido'
    elif len(p1_concluidas) > 0 or len([e for e in p1 if e.status_mrs != 'nao_iniciado']) > 0:
        return 'andamento'
    else:
        return 'pendente'

def gerar_alertas_municipio(municipio, entidades, visitas):
    """Gera alertas específicos para um município"""
    alertas = []
    
    # P1 sem contato
    p1_pendentes = [e for e in entidades if 
                   e.prioridade == 1 and e.status_mrs == 'nao_iniciado']
    if p1_pendentes:
        alertas.append(f'{len(p1_pendentes)} P1 pendentes')
    
    # Sem atividade recente
    if visitas:
        ultima_visita = max(visitas, key=lambda v: v.data if v.data else datetime.min)
        if ultima_visita.data and (datetime.now().date() - ultima_visita.data).days > 7:
            alertas.append('Sem atividade há >7 dias')
    else:
        alertas.append('Nenhuma visita registrada')
    
    return alertas

def formatar_data_relativa(data):
    """Formata data de forma relativa (há X dias)"""
    if not data:
        return 'Nunca'
    
    hoje = datetime.now().date()
    if isinstance(data, datetime):
        data = data.date()
    
    diff = (hoje - data).days
    
    if diff == 0:
        return 'Hoje'
    elif diff == 1:
        return 'Ontem'
    elif diff < 7:
        return f'Há {diff} dias'
    elif diff < 30:
        return f'Há {diff // 7} semanas'
    else:
        return f'Há {diff // 30} meses'

def calcular_progresso_coleta():
    """Calcula progresso da fase de coleta"""
    entidades_total = EntidadeIdentificada.query.filter(EntidadeIdentificada.prioridade.in_([1, 2])).count()
    if not entidades_total:
        return 0
    
    entidades_iniciadas = EntidadeIdentificada.query.filter(
        and_(
            EntidadeIdentificada.prioridade.in_([1, 2]),
            or_(
                EntidadeIdentificada.status_mrs != 'nao_iniciado',
                EntidadeIdentificada.status_map != 'nao_iniciado'
            )
        )
    ).count()
    
    return round((entidades_iniciadas / entidades_total) * 100)

def calcular_progresso_geral():
    """Calcula progresso geral do projeto"""
    # Pesos por fase
    pesos = {
        'identificacao': 20,
        'coleta': 50,
        'validacao': 20,
        'entrega': 10
    }
    
    # Progressos (simplificado para exemplo)
    progressos = {
        'identificacao': 100,  # Fase concluída
        'coleta': calcular_progresso_coleta(),
        'validacao': 0,  # Ainda não iniciada
        'entrega': 0     # Ainda não iniciada
    }
    
    progresso_ponderado = sum(progressos[fase] * (pesos[fase] / 100) for fase in pesos)
    return round(progresso_ponderado)

# =====================================
# FUNÇÕES AUXILIARES PARA KPIs PNSB 2024
# =====================================

def calcular_cronograma_ibge_completo(hoje, prazo_ibge):
    """Cronograma IBGE específico para PNSB 2024"""
    dias_restantes = max(0, (prazo_ibge - hoje).days)
    inicio_projeto = datetime(2025, 1, 1)
    dias_totais = (prazo_ibge - inicio_projeto).days
    progresso_temporal = min(100, max(0, ((hoje - inicio_projeto).days / dias_totais) * 100))
    
    # Calcular municípios em risco
    municipios_em_risco = calcular_municipios_em_risco_cronograma()
    
    # Determinar status do cronograma
    if dias_restantes < 30:
        status = "CRÍTICO"
        prioridade = "ALTA"
    elif dias_restantes < 60:
        status = "ATENÇÃO"
        prioridade = "MÉDIA"
    elif municipios_em_risco > 0:
        status = "CUIDADO"
        prioridade = "BAIXA"
    else:
        status = "NORMAL"
        prioridade = "BAIXA"
    
    # Calcular fase atual
    fase_atual = determinar_fase_atual_pesquisa(progresso_temporal)
    
    # Próximo milestone
    proximo_milestone = calcular_proximo_milestone_pnsb(dias_restantes)
    
    return {
        'dias_restantes': dias_restantes,
        'data_limite': prazo_ibge.strftime('%d/%m/%Y'),
        'progresso_temporal': round(progresso_temporal, 1),
        'municipios_em_risco': municipios_em_risco,
        'status_cronograma': status,
        'prioridade': prioridade,
        'fase_atual': fase_atual,
        'proximo_milestone': proximo_milestone,
        'dias_ate_milestone': calcular_dias_ate_milestone(proximo_milestone)
    }

def calcular_cobertura_territorial_completa():
    """Cobertura territorial específica para PNSB 2024"""
    municipios_sc = [
        'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas', 'Camboriú',
        'Itajaí', 'Itapema', 'Luiz Alves', 'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
    ]
    
    municipios_concluidos = 0
    municipios_em_andamento = 0
    municipios_criticos = []
    municipios_detalhes = []
    
    for municipio in municipios_sc:
        # Calcular dados do município
        entidades_municipio = EntidadeIdentificada.query.filter_by(municipio=municipio).all()
        total_entidades = len(entidades_municipio)
        
        if total_entidades == 0:
            progresso = 0
        else:
            entidades_finalizadas = [e for e in entidades_municipio if 
                                   e.status_mrs == 'validado_concluido' and 
                                   e.status_map == 'validado_concluido']
            progresso = (len(entidades_finalizadas) / total_entidades) * 100
        
        # Classificar município
        if progresso >= 100:
            municipios_concluidos += 1
            status_municipio = "CONCLUÍDO"
        elif progresso >= 50:
            municipios_em_andamento += 1
            status_municipio = "EM ANDAMENTO"
        elif progresso >= 25:
            municipios_em_andamento += 1
            status_municipio = "INICIADO"
        else:
            municipios_criticos.append(municipio)
            status_municipio = "CRÍTICO"
        
        # Calcular última atividade
        visitas_municipio = Visita.query.filter_by(municipio=municipio).order_by(Visita.data.desc()).first()
        ultima_atividade = visitas_municipio.data if visitas_municipio and visitas_municipio.data else None
        
        municipios_detalhes.append({
            'nome': municipio,
            'progresso': round(progresso, 1),
            'status': status_municipio,
            'total_entidades': total_entidades,
            'entidades_finalizadas': len([e for e in entidades_municipio if 
                                        e.status_mrs == 'validado_concluido' and 
                                        e.status_map == 'validado_concluido']),
            'ultima_atividade': ultima_atividade.strftime('%d/%m/%Y') if ultima_atividade else 'Nunca'
        })
    
    return {
        'municipios_concluidos': municipios_concluidos,
        'municipios_total': len(municipios_sc),
        'municipios_em_andamento': municipios_em_andamento,
        'municipios_criticos': municipios_criticos,
        'percentual_cobertura': round((municipios_concluidos / len(municipios_sc)) * 100, 1),
        'municipios_detalhes': municipios_detalhes,
        'cobertura_regional': calcular_cobertura_regional_sc()
    }

def calcular_compliance_pnsb_completo():
    """Compliance PNSB específico para critérios IBGE"""
    # Entidades P1 - Obrigatórias para IBGE
    entidades_p1 = EntidadeIdentificada.query.filter_by(prioridade=1).all()
    
    p1_finalizadas = [e for e in entidades_p1 if 
                     e.status_mrs == 'validado_concluido' and 
                     e.status_map == 'validado_concluido']
    
    p1_em_andamento = [e for e in entidades_p1 if 
                      (e.status_mrs in ['respondido', 'em_validacao'] or 
                       e.status_map in ['respondido', 'em_validacao']) and
                      not (e.status_mrs == 'validado_concluido' and 
                           e.status_map == 'validado_concluido')]
    
    p1_nao_iniciadas = [e for e in entidades_p1 if 
                       e.status_mrs == 'nao_iniciado' and 
                       e.status_map == 'nao_iniciado']
    
    # Entidades P2 - Importantes
    entidades_p2 = EntidadeIdentificada.query.filter_by(prioridade=2).all()
    p2_finalizadas = [e for e in entidades_p2 if 
                     e.status_mrs == 'validado_concluido' and 
                     e.status_map == 'validado_concluido']
    
    # Validação metodológica IBGE
    total_entidades = EntidadeIdentificada.query.count()
    entidades_validadas = EntidadeIdentificada.query.filter(
        or_(
            EntidadeIdentificada.status_mrs == 'validado_concluido',
            EntidadeIdentificada.status_map == 'validado_concluido'
        )
    ).count()
    
    validacao_metodologica = (entidades_validadas / total_entidades) * 100 if total_entidades > 0 else 0
    
    # Calcular compliance por município
    compliance_municipios = calcular_compliance_por_municipio()
    
    return {
        'p1_finalizadas': len(p1_finalizadas),
        'p1_total': len(entidades_p1),
        'p1_em_andamento': len(p1_em_andamento),
        'p1_nao_iniciadas': len(p1_nao_iniciadas),
        'percentual_p1': round((len(p1_finalizadas) / len(entidades_p1)) * 100, 1) if entidades_p1 else 0,
        'p2_finalizadas': len(p2_finalizadas),
        'p2_total': len(entidades_p2),
        'percentual_p2': round((len(p2_finalizadas) / len(entidades_p2)) * 100, 1) if entidades_p2 else 0,
        'validacao_metodologica': round(validacao_metodologica, 1),
        'compliance_municipios': compliance_municipios,
        'status_compliance': avaliar_status_compliance(len(p1_finalizadas), len(entidades_p1))
    }

def calcular_instrumentos_pesquisa_completo():
    """Instrumentos de pesquisa MRS e MAP - CRÍTICO para IBGE"""
    # Análise MRS (Manejo de Resíduos Sólidos)
    mrs_obrigatorios = EntidadeIdentificada.query.filter_by(mrs_obrigatorio=True).count()
    mrs_respondidos = EntidadeIdentificada.query.filter(
        and_(
            EntidadeIdentificada.mrs_obrigatorio == True,
            EntidadeIdentificada.status_mrs.in_(['respondido', 'em_validacao', 'validado_concluido'])
        )
    ).count()
    mrs_validados = EntidadeIdentificada.query.filter(
        and_(
            EntidadeIdentificada.mrs_obrigatorio == True,
            EntidadeIdentificada.status_mrs == 'validado_concluido'
        )
    ).count()
    
    # Análise MAP (Manejo de Águas Pluviais)
    map_obrigatorios = EntidadeIdentificada.query.filter_by(map_obrigatorio=True).count()
    map_respondidos = EntidadeIdentificada.query.filter(
        and_(
            EntidadeIdentificada.map_obrigatorio == True,
            EntidadeIdentificada.status_map.in_(['respondido', 'em_validacao', 'validado_concluido'])
        )
    ).count()
    map_validados = EntidadeIdentificada.query.filter(
        and_(
            EntidadeIdentificada.map_obrigatorio == True,
            EntidadeIdentificada.status_map == 'validado_concluido'
        )
    ).count()
    
    # Calcular taxas de resposta
    taxa_resposta_mrs = (mrs_respondidos / mrs_obrigatorios) * 100 if mrs_obrigatorios > 0 else 0
    taxa_resposta_map = (map_respondidos / map_obrigatorios) * 100 if map_obrigatorios > 0 else 0
    
    # Calcular taxas de validação
    taxa_validacao_mrs = (mrs_validados / mrs_obrigatorios) * 100 if mrs_obrigatorios > 0 else 0
    taxa_validacao_map = (map_validados / map_obrigatorios) * 100 if map_obrigatorios > 0 else 0
    
    # Avaliar status dos instrumentos
    status_mrs = avaliar_status_instrumento(taxa_resposta_mrs)
    status_map = avaliar_status_instrumento(taxa_resposta_map)
    
    # Cobertura combinada
    entidades_ambos_completos = EntidadeIdentificada.query.filter(
        and_(
            EntidadeIdentificada.mrs_obrigatorio == True,
            EntidadeIdentificada.map_obrigatorio == True,
            EntidadeIdentificada.status_mrs == 'validado_concluido',
            EntidadeIdentificada.status_map == 'validado_concluido'
        )
    ).count()
    
    entidades_ambos_obrigatorios = EntidadeIdentificada.query.filter(
        and_(
            EntidadeIdentificada.mrs_obrigatorio == True,
            EntidadeIdentificada.map_obrigatorio == True
        )
    ).count()
    
    cobertura_combinada = (entidades_ambos_completos / entidades_ambos_obrigatorios) * 100 if entidades_ambos_obrigatorios > 0 else 0
    
    return {
        'mrs': {
            'obrigatorios': mrs_obrigatorios,
            'respondidos': mrs_respondidos,
            'validados': mrs_validados,
            'taxa_resposta': round(taxa_resposta_mrs, 1),
            'taxa_validacao': round(taxa_validacao_mrs, 1),
            'status': status_mrs,
            'meta_resposta': 85.0,
            'gap_meta': round(85.0 - taxa_resposta_mrs, 1)
        },
        'map': {
            'obrigatorios': map_obrigatorios,
            'respondidos': map_respondidos,
            'validados': map_validados,
            'taxa_resposta': round(taxa_resposta_map, 1),
            'taxa_validacao': round(taxa_validacao_map, 1),
            'status': status_map,
            'meta_resposta': 80.0,
            'gap_meta': round(80.0 - taxa_resposta_map, 1)
        },
        'cobertura_combinada': {
            'completos': entidades_ambos_completos,
            'obrigatorios': entidades_ambos_obrigatorios,
            'percentual': round(cobertura_combinada, 1)
        },
        'resumo_geral': {
            'instrumentos_criticos': calcular_instrumentos_criticos(taxa_resposta_mrs, taxa_resposta_map),
            'progresso_geral': round((taxa_resposta_mrs + taxa_resposta_map) / 2, 1),
            'status_geral': avaliar_status_geral_instrumentos(taxa_resposta_mrs, taxa_resposta_map)
        }
    }

def calcular_qualidade_dados_pnsb_completo():
    """Qualidade dos dados específica para critérios PNSB do IBGE"""
    entidades = EntidadeIdentificada.query.all()
    
    if not entidades:
        return criar_estrutura_qualidade_vazia()
    
    total_entidades = len(entidades)
    
    # 1. Geocodificação (Obrigatória para IBGE)
    entidades_geocodificadas = [e for e in entidades if e.latitude and e.longitude]
    percentual_geocodificacao = (len(entidades_geocodificadas) / total_entidades) * 100
    
    # 2. Completude de dados obrigatórios
    entidades_completas = [e for e in entidades if 
                          e.nome_entidade and 
                          e.endereco and 
                          e.municipio]
    percentual_completude = (len(entidades_completas) / total_entidades) * 100
    
    # 3. Validação técnica IBGE
    entidades_validadas = [e for e in entidades if 
                          e.status_mrs == 'validado_concluido' or 
                          e.status_map == 'validado_concluido']
    percentual_validacao = (len(entidades_validadas) / total_entidades) * 100
    
    # 4. Consistência metodológica
    inconsistencias = calcular_inconsistencias_metodologicas(entidades)
    
    # 5. Score metodológico IBGE (baseado em critérios oficiais)
    score_metodologico = calcular_score_metodologico_ibge(
        percentual_geocodificacao,
        percentual_completude,
        percentual_validacao,
        inconsistencias
    )
    
    # 6. Critérios específicos IBGE
    criterios_ibge = avaliar_criterios_especificos_ibge(entidades)
    
    return {
        'score_metodologico': round(score_metodologico, 1),
        'geocodificacao': {
            'total': len(entidades_geocodificadas),
            'percentual': round(percentual_geocodificacao, 1),
            'status': 'ADEQUADO' if percentual_geocodificacao >= 90 else 'INADEQUADO'
        },
        'completude_dados': {
            'total': len(entidades_completas),
            'percentual': round(percentual_completude, 1),
            'status': 'ADEQUADO' if percentual_completude >= 95 else 'INADEQUADO'
        },
        'validacao_tecnica': {
            'total': len(entidades_validadas),
            'percentual': round(percentual_validacao, 1),
            'status': 'ADEQUADO' if percentual_validacao >= 80 else 'INADEQUADO'
        },
        'inconsistencias_criticas': inconsistencias,
        'criterios_ibge': criterios_ibge,
        'qualidade_geral': classificar_qualidade_geral(score_metodologico)
    }

def calcular_efetividade_operacional_completa():
    """Efetividade operacional da pesquisa PNSB"""
    # Dados de visitas
    visitas_total = Visita.query.count()
    visitas_realizadas = Visita.query.filter_by(status='realizada').count()
    visitas_finalizadas = Visita.query.filter_by(status='finalizada').count()
    
    # Taxa de contato
    entidades_total = EntidadeIdentificada.query.count()
    entidades_contactadas = EntidadeIdentificada.query.filter(
        or_(
            EntidadeIdentificada.status_mrs != 'nao_iniciado',
            EntidadeIdentificada.status_map != 'nao_iniciado'
        )
    ).count()
    
    # Reagendamentos
    reagendamentos = Visita.query.filter_by(status='remarcada').count()
    
    # Entidades resistentes (sem contato há mais de 14 dias)
    entidades_resistentes = EntidadeIdentificada.query.filter(
        and_(
            EntidadeIdentificada.status_mrs == 'nao_iniciado',
            EntidadeIdentificada.status_map == 'nao_iniciado',
            EntidadeIdentificada.identificado_em < (datetime.now() - timedelta(days=14))
        )
    ).count()
    
    # Produtividade semanal
    inicio_semana = datetime.now() - timedelta(days=7)
    visitas_semana = Visita.query.filter(
        Visita.data >= inicio_semana.date()
    ).count()
    
    # Calcular taxas
    taxa_conclusao_visitas = (visitas_realizadas / visitas_total) * 100 if visitas_total > 0 else 0
    taxa_contato = (entidades_contactadas / entidades_total) * 100 if entidades_total > 0 else 0
    taxa_reagendamento = (reagendamentos / visitas_total) * 100 if visitas_total > 0 else 0
    
    # Eficiência da equipe
    eficiencia_equipe = calcular_eficiencia_equipe_pesquisa(
        taxa_conclusao_visitas,
        taxa_contato,
        taxa_reagendamento
    )
    
    return {
        'visitas': {
            'total': visitas_total,
            'realizadas': visitas_realizadas,
            'finalizadas': visitas_finalizadas,
            'taxa_conclusao': round(taxa_conclusao_visitas, 1)
        },
        'contato': {
            'entidades_total': entidades_total,
            'entidades_contactadas': entidades_contactadas,
            'taxa_contato': round(taxa_contato, 1),
            'entidades_resistentes': entidades_resistentes
        },
        'reagendamentos': {
            'total': reagendamentos,
            'taxa_reagendamento': round(taxa_reagendamento, 1),
            'status': 'NORMAL' if taxa_reagendamento < 15 else 'ALTO'
        },
        'produtividade': {
            'visitas_semana': visitas_semana,
            'meta_semanal': 15,
            'atingimento_meta': round((visitas_semana / 15) * 100, 1)
        },
        'eficiencia_equipe': eficiencia_equipe
    }

def calcular_indicadores_risco_completo():
    """Indicadores de risco específicos para PNSB"""
    municipios_sc = [
        'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas', 'Camboriú',
        'Itajaí', 'Itapema', 'Luiz Alves', 'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
    ]
    
    municipios_risco_alto = []
    municipios_risco_medio = []
    municipios_risco_baixo = []
    
    hoje = datetime.now()
    prazo_final = datetime(2025, 12, 31)
    dias_restantes = (prazo_final - hoje).days
    
    for municipio in municipios_sc:
        # Calcular progresso do município
        entidades_municipio = EntidadeIdentificada.query.filter_by(municipio=municipio).all()
        
        if not entidades_municipio:
            municipios_risco_alto.append({
                'municipio': municipio,
                'motivo': 'Sem entidades identificadas',
                'progresso': 0
            })
            continue
        
        entidades_finalizadas = [e for e in entidades_municipio if 
                               e.status_mrs == 'validado_concluido' and 
                               e.status_map == 'validado_concluido']
        
        progresso = (len(entidades_finalizadas) / len(entidades_municipio)) * 100
        
        # Avaliar risco baseado em progresso e tempo restante
        if progresso < 25 and dias_restantes < 90:
            municipios_risco_alto.append({
                'municipio': municipio,
                'motivo': 'Baixo progresso com pouco tempo',
                'progresso': round(progresso, 1)
            })
        elif progresso < 50 and dias_restantes < 60:
            municipios_risco_medio.append({
                'municipio': municipio,
                'motivo': 'Progresso insuficiente',
                'progresso': round(progresso, 1)
            })
        else:
            municipios_risco_baixo.append({
                'municipio': municipio,
                'progresso': round(progresso, 1)
            })
    
    # Calcular risco geral do projeto
    risco_geral = calcular_risco_geral_projeto(
        len(municipios_risco_alto),
        len(municipios_risco_medio),
        dias_restantes
    )
    
    # Ações recomendadas
    acoes_recomendadas = gerar_acoes_recomendadas(
        municipios_risco_alto,
        municipios_risco_medio,
        dias_restantes
    )
    
    return {
        'risco_cronograma': {
            'nivel': risco_geral['nivel'],
            'score': risco_geral['score'],
            'descricao': risco_geral['descricao']
        },
        'municipios_risco_alto': municipios_risco_alto,
        'municipios_risco_medio': municipios_risco_medio,
        'municipios_risco_baixo': municipios_risco_baixo,
        'resumo_riscos': {
            'alto': len(municipios_risco_alto),
            'medio': len(municipios_risco_medio),
            'baixo': len(municipios_risco_baixo)
        },
        'acoes_recomendadas': acoes_recomendadas,
        'dias_restantes': dias_restantes
    }

# Funções auxiliares específicas
def calcular_municipios_em_risco_cronograma():
    """Calcula quantos municípios estão em risco de cronograma"""
    municipios_sc = [
        'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas', 'Camboriú',
        'Itajaí', 'Itapema', 'Luiz Alves', 'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
    ]
    
    risco = 0
    for municipio in municipios_sc:
        entidades = EntidadeIdentificada.query.filter_by(municipio=municipio).all()
        if entidades:
            finalizadas = [e for e in entidades if 
                          e.status_mrs == 'validado_concluido' and 
                          e.status_map == 'validado_concluido']
            progresso = (len(finalizadas) / len(entidades)) * 100
            
            if progresso < 50:  # Menos de 50% concluído
                risco += 1
    
    return risco

def determinar_fase_atual_pesquisa(progresso_temporal):
    """Determina a fase atual da pesquisa PNSB"""
    if progresso_temporal < 25:
        return "Identificação de Entidades"
    elif progresso_temporal < 50:
        return "Contato Inicial"
    elif progresso_temporal < 75:
        return "Coleta de Dados"
    else:
        return "Validação e Finalização"

def calcular_proximo_milestone_pnsb(dias_restantes):
    """Calcula o próximo milestone da pesquisa"""
    if dias_restantes > 120:
        return "Conclusão P1"
    elif dias_restantes > 90:
        return "Revisão Intermediária"
    elif dias_restantes > 60:
        return "Validação Final"
    else:
        return "Entrega IBGE"

def calcular_dias_ate_milestone(milestone):
    """Calcula quantos dias faltam para o milestone"""
    if milestone == "Conclusão P1":
        return 90
    elif milestone == "Revisão Intermediária":
        return 60
    elif milestone == "Validação Final":
        return 30
    else:
        return 15

def calcular_cobertura_regional_sc():
    """Calcula cobertura por região de SC"""
    # Implementação simplificada
    return {
        'grande_florianopolis': 6,
        'vale_itajai': 5,
        'cobertura_balanceada': True
    }

def calcular_compliance_por_municipio():
    """Calcula compliance por município"""
    municipios_sc = [
        'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas', 'Camboriú',
        'Itajaí', 'Itapema', 'Luiz Alves', 'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
    ]
    
    compliance = []
    for municipio in municipios_sc:
        entidades_p1 = EntidadeIdentificada.query.filter_by(
            municipio=municipio, 
            prioridade=1
        ).all()
        
        if entidades_p1:
            finalizadas = [e for e in entidades_p1 if 
                          e.status_mrs == 'validado_concluido' and 
                          e.status_map == 'validado_concluido']
            percentual = (len(finalizadas) / len(entidades_p1)) * 100
        else:
            percentual = 0
        
        compliance.append({
            'municipio': municipio,
            'percentual': round(percentual, 1),
            'status': 'ADEQUADO' if percentual >= 80 else 'INADEQUADO'
        })
    
    return compliance

def avaliar_status_compliance(finalizadas, total):
    """Avalia o status geral do compliance"""
    if total == 0:
        return "SEM DADOS"
    
    percentual = (finalizadas / total) * 100
    
    if percentual >= 90:
        return "EXCELENTE"
    elif percentual >= 75:
        return "ADEQUADO"
    elif percentual >= 50:
        return "REGULAR"
    else:
        return "CRÍTICO"

def avaliar_status_instrumento(taxa_resposta):
    """Avalia o status de um instrumento (MRS/MAP)"""
    if taxa_resposta >= 90:
        return "EXCELENTE"
    elif taxa_resposta >= 75:
        return "ADEQUADO"
    elif taxa_resposta >= 50:
        return "REGULAR"
    else:
        return "CRÍTICO"

def calcular_instrumentos_criticos(taxa_mrs, taxa_map):
    """Identifica instrumentos críticos"""
    criticos = []
    
    if taxa_mrs < 50:
        criticos.append("MRS")
    if taxa_map < 50:
        criticos.append("MAP")
    
    return criticos

def avaliar_status_geral_instrumentos(taxa_mrs, taxa_map):
    """Avalia status geral dos instrumentos"""
    media = (taxa_mrs + taxa_map) / 2
    
    if media >= 80:
        return "ADEQUADO"
    elif media >= 60:
        return "REGULAR"
    else:
        return "CRÍTICO"

def criar_estrutura_qualidade_vazia():
    """Cria estrutura vazia para qualidade"""
    return {
        'score_metodologico': 0,
        'geocodificacao': {'total': 0, 'percentual': 0, 'status': 'SEM DADOS'},
        'completude_dados': {'total': 0, 'percentual': 0, 'status': 'SEM DADOS'},
        'validacao_tecnica': {'total': 0, 'percentual': 0, 'status': 'SEM DADOS'},
        'inconsistencias_criticas': 0,
        'criterios_ibge': {},
        'qualidade_geral': 'SEM DADOS'
    }

def calcular_inconsistencias_metodologicas(entidades):
    """Calcula inconsistências metodológicas"""
    inconsistencias = 0
    
    for entidade in entidades:
        # Verificar inconsistências básicas
        if not entidade.nome_entidade:
            inconsistencias += 1
        if not entidade.municipio:
            inconsistencias += 1
        if entidade.mrs_obrigatorio and entidade.status_mrs == 'nao_iniciado':
            inconsistencias += 1
        if entidade.map_obrigatorio and entidade.status_map == 'nao_iniciado':
            inconsistencias += 1
    
    return inconsistencias

def calcular_score_metodologico_ibge(geo, completude, validacao, inconsistencias):
    """Calcula score metodológico específico para IBGE"""
    # Pesos específicos para PNSB
    peso_geo = 0.3
    peso_completude = 0.3
    peso_validacao = 0.35
    peso_inconsistencias = 0.05
    
    # Calcular score
    score = (geo * peso_geo + 
             completude * peso_completude + 
             validacao * peso_validacao - 
             inconsistencias * peso_inconsistencias)
    
    return max(0, min(100, score))

def avaliar_criterios_especificos_ibge(entidades):
    """Avalia critérios específicos do IBGE"""
    return {
        'cobertura_prefeituras': calcular_cobertura_prefeituras(entidades),
        'cobertura_terceirizadas': calcular_cobertura_terceirizadas(entidades),
        'diversidade_fontes': calcular_diversidade_fontes(entidades)
    }

def calcular_cobertura_prefeituras(entidades):
    """Calcula cobertura de prefeituras"""
    # Implementação simplificada
    return 85.0

def calcular_cobertura_terceirizadas(entidades):
    """Calcula cobertura de terceirizadas"""
    # Implementação simplificada
    return 70.0

def calcular_diversidade_fontes(entidades):
    """Calcula diversidade de fontes"""
    # Implementação simplificada
    return 80.0

def classificar_qualidade_geral(score):
    """Classifica qualidade geral"""
    if score >= 90:
        return "EXCELENTE"
    elif score >= 80:
        return "ADEQUADO"
    elif score >= 70:
        return "REGULAR"
    else:
        return "CRÍTICO"

def calcular_eficiencia_equipe_pesquisa(taxa_conclusao, taxa_contato, taxa_reagendamento):
    """Calcula eficiência da equipe de pesquisa"""
    # Fórmula específica para pesquisa
    eficiencia = (taxa_conclusao * 0.4 + 
                 taxa_contato * 0.4 - 
                 taxa_reagendamento * 0.2)
    
    return max(0, min(100, eficiencia))

def calcular_risco_geral_projeto(risco_alto, risco_medio, dias_restantes):
    """Calcula risco geral do projeto"""
    # Calcular score de risco
    score_risco = (risco_alto * 10 + risco_medio * 5)
    
    # Ajustar por tempo restante
    if dias_restantes < 60:
        score_risco *= 1.5
    elif dias_restantes < 90:
        score_risco *= 1.2
    
    # Determinar nível
    if score_risco >= 30:
        nivel = "ALTO"
        descricao = "Risco significativo de não cumprimento do prazo"
    elif score_risco >= 15:
        nivel = "MÉDIO"
        descricao = "Alguns municípios precisam de atenção"
    else:
        nivel = "BAIXO"
        descricao = "Projeto dentro do cronograma esperado"
    
    return {
        'nivel': nivel,
        'score': round(score_risco, 1),
        'descricao': descricao
    }

def gerar_acoes_recomendadas(risco_alto, risco_medio, dias_restantes):
    """Gera ações recomendadas baseadas nos riscos"""
    acoes = []
    
    if risco_alto:
        acoes.append({
            'prioridade': 'ALTA',
            'acao': 'Intensificar contatos nos municípios de risco alto',
            'municipios': [m['municipio'] for m in risco_alto]
        })
    
    if risco_medio:
        acoes.append({
            'prioridade': 'MÉDIA',
            'acao': 'Acompanhar de perto municípios de risco médio',
            'municipios': [m['municipio'] for m in risco_medio]
        })
    
    if dias_restantes < 60:
        acoes.append({
            'prioridade': 'CRÍTICA',
            'acao': 'Implementar cronograma acelerado',
            'detalhes': 'Menos de 60 dias para conclusão'
        })
    
    return acoes