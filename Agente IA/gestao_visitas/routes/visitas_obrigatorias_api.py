"""
API para Controle de Visitas Obrigatórias - PNSB 2024
===================================================

Endpoints para gerenciar e monitorar visitas obrigatórias:
- Listar visitas obrigatórias por município
- Status consolidado de visitas obrigatórias
- Atualizar status de visitas
- Dashboard integrado com questionários
"""

from flask import Blueprint, request, jsonify
from gestao_visitas.db import db
from gestao_visitas.models.visitas_obrigatorias import (
    VisitaObrigatoria,
    StatusVisitasObrigatorias,
    inicializar_visitas_obrigatorias,
    sincronizar_visita_obrigatoria_com_visita_real
)
from gestao_visitas.models.agendamento import Visita
from gestao_visitas.models.questionarios_obrigatorios import EntidadeIdentificada
from gestao_visitas.config import MUNICIPIOS as MUNICIPIOS_PNSB
from datetime import datetime
import logging

visitas_obrigatorias_bp = Blueprint('visitas_obrigatorias', __name__)

@visitas_obrigatorias_bp.route('/visitas-obrigatorias', methods=['GET'])
def listar_visitas_obrigatorias():
    """Lista todas as visitas obrigatórias com filtros"""
    try:
        municipio = request.args.get('municipio')
        status = request.args.get('status')
        prioridade = request.args.get('prioridade')
        
        query = VisitaObrigatoria.query.filter_by(ativo=True)
        
        if municipio:
            query = query.filter_by(municipio=municipio)
        
        if status:
            query = query.filter_by(status_visita=status)
        
        if prioridade:
            query = query.filter_by(prioridade=int(prioridade))
        
        visitas_obrigatorias = query.order_by(
            VisitaObrigatoria.prioridade.asc(),
            VisitaObrigatoria.municipio.asc(),
            VisitaObrigatoria.nome_entidade.asc()
        ).all()
        
        return jsonify({
            'success': True,
            'total': len(visitas_obrigatorias),
            'visitas_obrigatorias': [v.to_dict() for v in visitas_obrigatorias],
            'filtros_aplicados': {
                'municipio': municipio,
                'status': status,
                'prioridade': prioridade
            }
        })
        
    except Exception as e:
        logging.error(f"Erro ao listar visitas obrigatórias: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor',
            'details': str(e)
        }), 500

@visitas_obrigatorias_bp.route('/visitas-obrigatorias/municipio/<municipio>', methods=['GET'])
def obter_visitas_obrigatorias_municipio(municipio):
    """Obtém todas as visitas obrigatórias de um município específico"""
    try:
        if municipio not in MUNICIPIOS_PNSB:
            return jsonify({
                'success': False,
                'error': f'Município {municipio} não faz parte do PNSB 2024'
            }), 400
        
        # Buscar visitas obrigatórias
        visitas_obrigatorias = VisitaObrigatoria.query.filter_by(
            municipio=municipio,
            ativo=True
        ).order_by(
            VisitaObrigatoria.prioridade.asc(),
            VisitaObrigatoria.nome_entidade.asc()
        ).all()
        
        # Buscar status consolidado
        status_consolidado = StatusVisitasObrigatorias.query.filter_by(
            municipio=municipio
        ).first()
        
        if not status_consolidado:
            # Calcular se não existir
            status_consolidado = StatusVisitasObrigatorias.recalcular_status_municipio(municipio)
        
        return jsonify({
            'success': True,
            'municipio': municipio,
            'status_consolidado': status_consolidado.to_dict() if status_consolidado else None,
            'visitas_obrigatorias': [v.to_dict() for v in visitas_obrigatorias],
            'resumo': {
                'total': len(visitas_obrigatorias),
                'por_status': {
                    'nao_agendadas': sum(1 for v in visitas_obrigatorias if v.status_visita == 'nao_agendada'),
                    'agendadas': sum(1 for v in visitas_obrigatorias if v.status_visita == 'agendada'),
                    'concluidas': sum(1 for v in visitas_obrigatorias if v.status_visita == 'concluida'),
                    'reagendadas': sum(1 for v in visitas_obrigatorias if v.status_visita == 'reagendada'),
                    'canceladas': sum(1 for v in visitas_obrigatorias if v.status_visita == 'cancelada')
                },
                'por_prioridade': {
                    'p1': len([v for v in visitas_obrigatorias if v.prioridade == 1]),
                    'p2': len([v for v in visitas_obrigatorias if v.prioridade == 2])
                }
            }
        })
        
    except Exception as e:
        logging.error(f"Erro ao obter visitas obrigatórias do município {municipio}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor',
            'details': str(e)
        }), 500

@visitas_obrigatorias_bp.route('/visitas-obrigatorias/<int:visita_obrigatoria_id>/status', methods=['PUT'])
def atualizar_status_visita_obrigatoria(visita_obrigatoria_id):
    """Atualiza o status de uma visita obrigatória"""
    try:
        data = request.get_json()
        novo_status = data.get('status')
        justificativa = data.get('justificativa', '')
        
        if not novo_status:
            return jsonify({
                'success': False,
                'error': 'Status é obrigatório'
            }), 400
        
        visita_obrigatoria = VisitaObrigatoria.query.get(visita_obrigatoria_id)
        if not visita_obrigatoria:
            return jsonify({
                'success': False,
                'error': 'Visita obrigatória não encontrada'
            }), 404
        
        # Atualizar status
        try:
            sucesso = visita_obrigatoria.atualizar_status(novo_status, justificativa)
            if not sucesso:
                return jsonify({
                    'success': False,
                    'error': 'Falha ao atualizar status'
                }), 400
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
        
        db.session.commit()
        
        # Recalcular status do município
        StatusVisitasObrigatorias.recalcular_status_municipio(visita_obrigatoria.municipio)
        
        return jsonify({
            'success': True,
            'message': f'Status atualizado para {novo_status}',
            'visita_obrigatoria': visita_obrigatoria.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao atualizar status da visita obrigatória {visita_obrigatoria_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor',
            'details': str(e)
        }), 500

@visitas_obrigatorias_bp.route('/visitas-obrigatorias/<int:visita_obrigatoria_id>/vincular-visita', methods=['POST'])
def vincular_visita_real(visita_obrigatoria_id):
    """Vincula uma visita real a uma visita obrigatória"""
    try:
        data = request.get_json()
        visita_id = data.get('visita_id')
        
        if not visita_id:
            return jsonify({
                'success': False,
                'error': 'ID da visita é obrigatório'
            }), 400
        
        visita_obrigatoria = VisitaObrigatoria.query.get(visita_obrigatoria_id)
        if not visita_obrigatoria:
            return jsonify({
                'success': False,
                'error': 'Visita obrigatória não encontrada'
            }), 404
        
        # Vincular visita
        try:
            sucesso = visita_obrigatoria.vincular_visita(visita_id)
            if not sucesso:
                return jsonify({
                    'success': False,
                    'error': 'Falha ao vincular visita'
                }), 400
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
        
        db.session.commit()
        
        # Recalcular status do município
        StatusVisitasObrigatorias.recalcular_status_municipio(visita_obrigatoria.municipio)
        
        return jsonify({
            'success': True,
            'message': f'Visita {visita_id} vinculada com sucesso',
            'visita_obrigatoria': visita_obrigatoria.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao vincular visita à visita obrigatória {visita_obrigatoria_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor',
            'details': str(e)
        }), 500

@visitas_obrigatorias_bp.route('/status-visitas-obrigatorias', methods=['GET'])
def obter_status_consolidado_todos_municipios():
    """Obtém status consolidado de visitas obrigatórias para todos os municípios"""
    try:
        municipio_filtro = request.args.get('municipio')
        
        query = StatusVisitasObrigatorias.query
        
        if municipio_filtro:
            if municipio_filtro not in MUNICIPIOS_PNSB:
                return jsonify({
                    'success': False,
                    'error': f'Município {municipio_filtro} não faz parte do PNSB 2024'
                }), 400
            query = query.filter_by(municipio=municipio_filtro)
        
        status_municipios = query.order_by(StatusVisitasObrigatorias.municipio.asc()).all()
        
        # Calcular estatísticas gerais
        total_municipios = len(MUNICIPIOS_PNSB) if not municipio_filtro else 1
        municipios_com_dados = len(status_municipios)
        
        total_visitas_obrigatorias = sum(s.total_obrigatorias for s in status_municipios)
        total_concluidas = sum(s.concluidas for s in status_municipios)
        total_agendadas = sum(s.agendadas for s in status_municipios)
        total_pendentes = sum(s.nao_agendadas for s in status_municipios)
        total_urgentes = sum(s.visitas_urgentes for s in status_municipios)
        
        percentual_geral = (total_concluidas / total_visitas_obrigatorias * 100) if total_visitas_obrigatorias > 0 else 0
        
        # Status por município
        municipios_completos = sum(1 for s in status_municipios if s.percentual_p1 == 100.0)
        municipios_finalizados = sum(1 for s in status_municipios if s.percentual_conclusao == 100.0)
        
        return jsonify({
            'success': True,
            'estatisticas_gerais': {
                'total_municipios': total_municipios,
                'municipios_com_dados': municipios_com_dados,
                'total_visitas_obrigatorias': total_visitas_obrigatorias,
                'total_concluidas': total_concluidas,
                'total_agendadas': total_agendadas,
                'total_pendentes': total_pendentes,
                'total_urgentes': total_urgentes,
                'percentual_geral': round(percentual_geral, 1),
                'municipios_completos': municipios_completos,
                'municipios_finalizados': municipios_finalizados
            },
            'status_por_municipio': [s.to_dict() for s in status_municipios],
            'alertas': {
                'municipios_com_urgencias': len([s for s in status_municipios if s.visitas_urgentes > 0]),
                'total_visitas_urgentes': total_urgentes,
                'municipios_em_atraso': len([s for s in status_municipios if s.visitas_em_atraso > 0])
            }
        })
        
    except Exception as e:
        logging.error(f"Erro ao obter status consolidado: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor',
            'details': str(e)
        }), 500

@visitas_obrigatorias_bp.route('/dashboard-integrado/<municipio>', methods=['GET'])
def obter_dashboard_integrado(municipio):
    """
    Dashboard integrado mostrando questionários + visitas obrigatórias
    
    Exemplo de resposta:
    {
        "municipio": "Itajaí",
        "questionarios": {"8 respondidos, 5 validados"},
        "visitas_obrigatorias": {"3 de 5 concluídas"},
        "status_integrado": "Questionários validados, visitas pendentes"
    }
    """
    try:
        if municipio not in MUNICIPIOS_PNSB:
            return jsonify({
                'success': False,
                'error': f'Município {municipio} não faz parte do PNSB 2024'
            }), 400
        
        # 1. STATUS DOS QUESTIONÁRIOS
        from gestao_visitas.models.questionarios_obrigatorios import ProgressoQuestionarios
        
        progresso_questionarios = ProgressoQuestionarios.query.filter_by(municipio=municipio).first()
        if not progresso_questionarios:
            progresso_questionarios = ProgressoQuestionarios.calcular_progresso_municipio(municipio)
        
        # 2. STATUS DAS VISITAS OBRIGATÓRIAS
        status_visitas = StatusVisitasObrigatorias.query.filter_by(municipio=municipio).first()
        if not status_visitas:
            status_visitas = StatusVisitasObrigatorias.recalcular_status_municipio(municipio)
        
        # 3. CALCULAR STATUS INTEGRADO
        def calcular_status_integrado():
            if not progresso_questionarios or not status_visitas:
                return "Dados insuficientes"
            
            q_pct = progresso_questionarios.percentual_geral
            v_pct = status_visitas.percentual_conclusao
            
            if q_pct == 100 and v_pct == 100:
                return "✅ Município completo"
            elif q_pct == 100 and v_pct < 100:
                return f"✅ Questionários completos, {status_visitas.nao_agendadas + status_visitas.agendadas} visitas pendentes"
            elif q_pct < 100 and v_pct == 100:
                return f"✅ Visitas completas, questionários {q_pct:.0f}% validados"
            elif q_pct > 0 and v_pct > 0:
                return f"🔄 Em andamento: Q={q_pct:.0f}%, V={v_pct:.0f}%"
            elif v_pct > 0:
                return f"📅 {status_visitas.concluidas} visitas concluídas, questionários pendentes"
            elif q_pct > 0:
                return f"📋 {progresso_questionarios.mrs_validados + progresso_questionarios.map_validados} questionários validados, visitas pendentes"
            else:
                return "🚀 Município não iniciado"
        
        # 4. PRÓXIMAS AÇÕES RECOMENDADAS
        def recomendar_proximas_acoes():
            acoes = []
            
            if status_visitas.visitas_urgentes > 0:
                acoes.append(f"⚠️ URGENTE: {status_visitas.visitas_urgentes} visitas P1 em atraso")
            
            if status_visitas.nao_agendadas > 0:
                acoes.append(f"📅 Agendar {status_visitas.nao_agendadas} visitas obrigatórias")
            
            if progresso_questionarios and progresso_questionarios.mrs_concluidos > progresso_questionarios.mrs_validados:
                pendentes = progresso_questionarios.mrs_concluidos - progresso_questionarios.mrs_validados
                acoes.append(f"📋 Validar {pendentes} questionários MRS respondidos")
            
            if progresso_questionarios and progresso_questionarios.map_concluidos > progresso_questionarios.map_validados:
                pendentes = progresso_questionarios.map_concluidos - progresso_questionarios.map_validados
                acoes.append(f"📋 Validar {pendentes} questionários MAP respondidos")
            
            if not acoes:
                if status_visitas.percentual_conclusao == 100 and progresso_questionarios and progresso_questionarios.percentual_geral == 100:
                    acoes.append("🎉 Município finalizado!")
                else:
                    acoes.append("✅ Continuar trabalho em andamento")
            
            return acoes
        
        return jsonify({
            'success': True,
            'municipio': municipio,
            'timestamp': datetime.utcnow().isoformat(),
            
            # Dados detalhados
            'questionarios': progresso_questionarios.to_dict() if progresso_questionarios else None,
            'visitas_obrigatorias': status_visitas.to_dict() if status_visitas else None,
            
            # Status integrado
            'status_integrado': calcular_status_integrado(),
            'proximas_acoes': recomendar_proximas_acoes(),
            
            # Resumo executivo
            'resumo': {
                'questionarios_validados': f"{progresso_questionarios.mrs_validados + progresso_questionarios.map_validados}" if progresso_questionarios else "0",
                'questionarios_respondidos': f"{progresso_questionarios.mrs_concluidos + progresso_questionarios.map_concluidos}" if progresso_questionarios else "0",
                'visitas_concluidas': f"{status_visitas.concluidas}" if status_visitas else "0",
                'visitas_obrigatorias': f"{status_visitas.total_obrigatorias}" if status_visitas else "0",
                'percentual_questionarios': f"{progresso_questionarios.percentual_geral:.0f}%" if progresso_questionarios else "0%",
                'percentual_visitas': f"{status_visitas.percentual_conclusao:.0f}%" if status_visitas else "0%"
            },
            
            # Alertas
            'alertas': {
                'tem_urgencias': status_visitas and status_visitas.visitas_urgentes > 0,
                'visitas_urgentes': status_visitas.visitas_urgentes if status_visitas else 0,
                'visitas_em_atraso': status_visitas.visitas_em_atraso if status_visitas else 0,
                'precisa_atencao': status_visitas and status_visitas.precisa_atencao
            }
        })
        
    except Exception as e:
        logging.error(f"Erro ao obter dashboard integrado para {municipio}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor',
            'details': str(e)
        }), 500

@visitas_obrigatorias_bp.route('/inicializar-visitas-obrigatorias', methods=['POST'])
def inicializar_sistema():
    """Inicializa o sistema de visitas obrigatórias"""
    try:
        resultado = inicializar_visitas_obrigatorias()
        
        return jsonify({
            'success': True,
            'message': 'Sistema de visitas obrigatórias inicializado com sucesso',
            'resultado': resultado
        })
        
    except Exception as e:
        logging.error(f"Erro ao inicializar visitas obrigatórias: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor',
            'details': str(e)
        }), 500

@visitas_obrigatorias_bp.route('/recalcular-status', methods=['POST'])
def recalcular_status_todos_municipios():
    """Recalcula status de visitas obrigatórias para todos os municípios"""
    try:
        municipio = request.get_json().get('municipio') if request.is_json else None
        
        if municipio:
            if municipio not in MUNICIPIOS_PNSB:
                return jsonify({
                    'success': False,
                    'error': f'Município {municipio} não faz parte do PNSB 2024'
                }), 400
            
            municipios_para_processar = [municipio]
        else:
            municipios_para_processar = MUNICIPIOS_PNSB
        
        resultados = []
        for mun in municipios_para_processar:
            try:
                status = StatusVisitasObrigatorias.recalcular_status_municipio(mun)
                resultados.append({
                    'municipio': mun,
                    'success': True,
                    'status': status.to_dict() if status else None
                })
            except Exception as e:
                resultados.append({
                    'municipio': mun,
                    'success': False,
                    'error': str(e)
                })
        
        total_sucesso = sum(1 for r in resultados if r['success'])
        
        return jsonify({
            'success': True,
            'message': f'Status recalculado para {total_sucesso}/{len(municipios_para_processar)} municípios',
            'resultados': resultados
        })
        
    except Exception as e:
        logging.error(f"Erro ao recalcular status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor',
            'details': str(e)
        }), 500