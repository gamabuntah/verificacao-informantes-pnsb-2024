from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import requests
import pandas as pd
import csv

from ..db import db
from ..models.agendamento import Visita
from ..models.checklist import Checklist
from ..models.contatos import Contato, TipoEntidade, FonteInformacao
from ..services.relatorios import RelatorioService
from ..services.rotas import RotaService
from ..services.maps import MapaService
from ..services.checklist import get_campos_etapa
from ..services.api_manager import api_manager
from ..utils.validators import validate_json_input, VisitaValidator, ValidationError
from ..utils.error_handlers import APIResponse
from ..config.security import SecurityConfig

api_bp = Blueprint('api', __name__)

# Inicializar services
google_maps_key = SecurityConfig.get_google_maps_key()
google_gemini_key = SecurityConfig.get_google_gemini_key()

mapa_service = MapaService(google_maps_key) if google_maps_key else None
relatorio_service = RelatorioService()
rota_service = RotaService(mapa_service)

# === ROTAS DE VISITAS ===

@api_bp.route('/visitas', methods=['GET'])
def get_visitas():
    """Retorna a lista de visitas ordenada por data e hora_inicio"""
    try:
        visitas = Visita.query.order_by(Visita.data.asc(), Visita.hora_inicio.asc()).all()
        visitas_dict = [v.to_dict() for v in visitas]
        return APIResponse.success(data=visitas_dict)
    except Exception as e:
        return APIResponse.error(f"Erro ao buscar visitas: {str(e)}")

# === ROTAS DE QUESTIONÁRIOS ===

@api_bp.route('/visitas/<int:visita_id>/questionarios', methods=['GET'])
def get_questionarios_visita(visita_id):
    """Retorna questionários e entidades vinculadas a uma visita"""
    try:
        visita = Visita.query.get(visita_id)
        if not visita:
            return APIResponse.not_found("Visita")
        
        from ..models.questionarios_obrigatorios import EntidadeIdentificada
        entidades = EntidadeIdentificada.query.filter_by(visita_id=visita_id).all()
        
        status_questionarios = visita.obter_status_questionarios()
        
        return APIResponse.success({
            'visita_id': visita_id,
            'status_visita': visita.status,
            'status_questionarios': status_questionarios,
            'entidades': [e.to_dict() for e in entidades],
            'resumo': {
                'total_entidades': len(entidades),
                'mrs_obrigatorios': sum(1 for e in entidades if e.mrs_obrigatorio),
                'map_obrigatorios': sum(1 for e in entidades if e.map_obrigatorio),
                'mrs_respondidos': sum(1 for e in entidades if e.mrs_obrigatorio and e.status_mrs == 'respondido'),
                'map_respondidos': sum(1 for e in entidades if e.map_obrigatorio and e.status_map == 'respondido'),
                'mrs_validados': sum(1 for e in entidades if e.mrs_obrigatorio and e.status_mrs == 'validado_concluido'),
                'map_validados': sum(1 for e in entidades if e.map_obrigatorio and e.status_map == 'validado_concluido')
            }
        })
        
    except Exception as e:
        return APIResponse.error(f"Erro ao buscar questionários: {str(e)}")

@api_bp.route('/visitas/<int:visita_id>/questionarios/status', methods=['PUT'])
@validate_json_input(required_fields=['entidade_id', 'tipo', 'status'])
def atualizar_status_questionario_visita(visita_id):
    """Atualiza status específico de questionário de uma visita"""
    try:
        data = request.validated_data
        entidade_id = data.get('entidade_id')
        tipo_questionario = data.get('tipo')  # 'mrs' ou 'map'
        novo_status = data.get('status')  # 'respondido' ou 'validado_concluido'
        
        # Validar parâmetros
        if tipo_questionario not in ['mrs', 'map']:
            return APIResponse.validation_error("Tipo deve ser 'mrs' ou 'map'")
        
        if novo_status not in ['nao_iniciado', 'respondido', 'validado_concluido', 'nao_aplicavel']:
            return APIResponse.validation_error("Status inválido")
        
        from ..models.questionarios_obrigatorios import EntidadeIdentificada
        entidade = EntidadeIdentificada.query.filter_by(
            id=entidade_id,
            visita_id=visita_id
        ).first()
        
        if not entidade:
            return APIResponse.not_found("Entidade")
        
        # Atualizar status específico
        if tipo_questionario == 'mrs':
            if not entidade.mrs_obrigatorio:
                return APIResponse.validation_error("MRS não é obrigatório para esta entidade")
            entidade.status_mrs = novo_status
        elif tipo_questionario == 'map':
            if not entidade.map_obrigatorio:
                return APIResponse.validation_error("MAP não é obrigatório para esta entidade")
            entidade.status_map = novo_status
        
        entidade.atualizado_em = datetime.utcnow()
        db.session.commit()
        
        # Obter visita e recalcular status inteligente
        visita = Visita.query.get(visita_id)
        novo_status_visita = visita.calcular_status_inteligente()
        
        return APIResponse.success({
            'entidade_atualizada': entidade.to_dict(),
            'status_visita': novo_status_visita,
            'questionarios_status': visita.obter_status_questionarios(),
            'message': f'Status {tipo_questionario.upper()} atualizado para {novo_status}'
        })
        
    except ValidationError as e:
        db.session.rollback()
        return APIResponse.validation_error(str(e))
    except Exception as e:
        db.session.rollback()
        return APIResponse.error(f"Erro ao atualizar status: {str(e)}")

@api_bp.route('/visitas/<int:visita_id>/questionarios/sincronizar', methods=['POST'])
def sincronizar_questionarios_visita(visita_id):
    """Força sincronização dos questionários com o status da visita"""
    try:
        visita = Visita.query.get(visita_id)
        if not visita:
            return APIResponse.not_found("Visita")
        
        # Forçar sincronização
        visita._sincronizar_questionarios()
        
        # Retornar status atualizado
        status_questionarios = visita.obter_status_questionarios()
        
        return APIResponse.success({
            'visita_id': visita_id,
            'status_visita': visita.status,
            'questionarios_sincronizados': status_questionarios,
            'message': 'Questionários sincronizados com sucesso'
        })
        
    except Exception as e:
        return APIResponse.error(f"Erro ao sincronizar questionários: {str(e)}")

@api_bp.route('/visitas/<int:visita_id>/entidades', methods=['POST'])
@validate_json_input(required_fields=['nome_entidade', 'tipo_entidade'])
def adicionar_entidade_visita(visita_id):
    """Adiciona nova entidade a uma visita existente"""
    try:
        data = request.validated_data
        
        visita = Visita.query.get(visita_id)
        if not visita:
            return APIResponse.not_found("Visita")
        
        from ..models.questionarios_obrigatorios import EntidadeIdentificada
        
        # Criar nova entidade
        entidade = EntidadeIdentificada(
            municipio=visita.municipio,
            tipo_entidade=data.get('tipo_entidade'),
            nome_entidade=data.get('nome_entidade'),
            cnpj=data.get('cnpj', ''),
            endereco=data.get('endereco', ''),
            telefone=data.get('telefone', ''),
            email=data.get('email', ''),
            responsavel=data.get('responsavel', ''),
            mrs_obrigatorio=data.get('mrs_obrigatorio', False),
            map_obrigatorio=data.get('map_obrigatorio', False),
            status_mrs='nao_iniciado',
            status_map='nao_iniciado',
            fonte_identificacao='adicionada_manualmente',
            visita_id=visita_id,
            prioridade=data.get('prioridade', 2),
            categoria_prioridade=data.get('categoria_prioridade', 'p2'),
            observacoes=data.get('observacoes', f'Entidade adicionada manualmente à visita {visita_id}')
        )
        
        entidade.definir_prioridade_automatica()
        db.session.add(entidade)
        
        # Sincronizar com status da visita
        entidade.sincronizar_com_visita()
        
        db.session.commit()
        
        return APIResponse.success({
            'entidade_criada': entidade.to_dict(),
            'questionarios_status': visita.obter_status_questionarios(),
            'message': 'Entidade adicionada com sucesso'
        }, status_code=201)
        
    except ValidationError as e:
        db.session.rollback()
        return APIResponse.validation_error(str(e))
    except Exception as e:
        db.session.rollback()
        return APIResponse.error(f"Erro ao adicionar entidade: {str(e)}")

@api_bp.route('/visitas/progresso-mapa', methods=['GET'])
def get_progresso_mapa():
    """Retorna dados consolidados para o mapa de progresso"""
    try:
        from ..models.questionarios_obrigatorios import EntidadeIdentificada, ProgressoQuestionarios
        from ..config import MUNICIPIOS
        
        municipios_data = []
        
        for municipio in MUNICIPIOS:
            # Buscar visitas do município
            visitas = Visita.query.filter_by(municipio=municipio).all()
            
            # Buscar entidades identificadas do município
            entidades = EntidadeIdentificada.query.filter_by(municipio=municipio).all()
            
            # CORREÇÃO: Sincronizar status dos questionários com visitas
            for entidade in entidades:
                try:
                    entidade.sincronizar_com_visita()
                except Exception as e:
                    print(f"Erro ao sincronizar entidade {entidade.id}: {e}")
            
            # Commit das alterações
            db.session.commit()
            
            # Calcular estatísticas de questionários reais
            total_mrs_obrigatorios = sum(1 for e in entidades if e.mrs_obrigatorio)
            total_map_obrigatorios = sum(1 for e in entidades if e.map_obrigatorio)
            
            mrs_respondidos = sum(1 for e in entidades if e.mrs_obrigatorio and e.status_mrs == 'respondido')
            map_respondidos = sum(1 for e in entidades if e.map_obrigatorio and e.status_map == 'respondido')
            
            mrs_validados = sum(1 for e in entidades if e.mrs_obrigatorio and e.status_mrs == 'validado_concluido')
            map_validados = sum(1 for e in entidades if e.map_obrigatorio and e.status_map == 'validado_concluido')
            
            # Fallback: Se não há dados sincronizados, usar status das visitas
            if mrs_validados == 0 and map_validados == 0 and visitas:
                visitas_finalizadas = len([v for v in visitas if v.status in ['finalizada', 'questionários validados']])
                total_visitas = len(visitas)
                
                if total_visitas > 0:
                    percentual_base = (visitas_finalizadas / total_visitas) * 100
                    mrs_validados = int((percentual_base / 100) * total_mrs_obrigatorios)
                    map_validados = int((percentual_base / 100) * total_map_obrigatorios)
                    mrs_respondidos = mrs_validados
                    map_respondidos = map_validados
            
            # Calcular percentuais
            percentual_mrs = (mrs_validados / total_mrs_obrigatorios * 100) if total_mrs_obrigatorios > 0 else 0
            percentual_map = (map_validados / total_map_obrigatorios * 100) if total_map_obrigatorios > 0 else 0
            percentual_geral = ((mrs_validados + map_validados) / (total_mrs_obrigatorios + total_map_obrigatorios) * 100) if (total_mrs_obrigatorios + total_map_obrigatorios) > 0 else 0
            
            # Determinar status do município
            if percentual_geral >= 90:
                status = 'concluido'
            elif percentual_geral >= 30:
                status = 'andamento'
            else:
                status = 'pendente'
            
            # Dados do resumo
            visitas_concluidas = len([v for v in visitas if v.status in ['finalizada', 'questionários validados']])
            total_visitas = len(visitas)
            
            municipio_data = {
                'municipio': municipio,
                'status': status,
                'total_entidades': len(entidades),
                'questionarios': {
                    'total_mrs_obrigatorios': total_mrs_obrigatorios,
                    'total_map_obrigatorios': total_map_obrigatorios,
                    'mrs_respondidos': mrs_respondidos,
                    'map_respondidos': map_respondidos,
                    'mrs_validados': mrs_validados,
                    'map_validados': map_validados,
                    'mrs_concluidos': mrs_respondidos,  # Alias para compatibilidade
                    'map_concluidos': map_respondidos,  # Alias para compatibilidade
                    'percentual_mrs': round(percentual_mrs, 1),
                    'percentual_map': round(percentual_map, 1),
                    'percentual_geral': round(percentual_geral, 1)
                },
                'resumo': {
                    'total_visitas': total_visitas,
                    'visitas_concluidas': visitas_concluidas,
                    'percentual_conclusao': round(percentual_geral, 1),
                    'finalizadas': visitas_concluidas
                },
                'coords': [municipio, 0, 0],  # Placeholder
                'ultima_atividade': datetime.now().strftime('%d/%m/%Y %H:%M')
            }
            
            municipios_data.append(municipio_data)
        
        # Estatísticas gerais
        total_mrs_sistema = sum(m['questionarios']['total_mrs_obrigatorios'] for m in municipios_data)
        total_map_sistema = sum(m['questionarios']['total_map_obrigatorios'] for m in municipios_data)
        total_mrs_validados = sum(m['questionarios']['mrs_validados'] for m in municipios_data)
        total_map_validados = sum(m['questionarios']['map_validados'] for m in municipios_data)
        
        estatisticas_gerais = {
            'municipios_total': len(MUNICIPIOS),
            'municipios_concluidos': len([m for m in municipios_data if m['status'] == 'concluido']),
            'questionarios_mrs_total': total_mrs_sistema,
            'questionarios_map_total': total_map_sistema,
            'questionarios_mrs_validados': total_mrs_validados,
            'questionarios_map_validados': total_map_validados,
            'progresso_geral': round(((total_mrs_validados + total_map_validados) / (total_mrs_sistema + total_map_sistema) * 100) if (total_mrs_sistema + total_map_sistema) > 0 else 0, 1)
        }
        
        return APIResponse.success({
            'municipios': municipios_data,
            'estatisticas': estatisticas_gerais,
            'ultima_atualizacao': datetime.now().isoformat(),
            'data': municipios_data  # Alias para compatibilidade
        })
        
    except Exception as e:
        return APIResponse.error(f"Erro ao buscar progresso do mapa: {str(e)}")

@api_bp.route('/visitas', methods=['POST'])
@validate_json_input(required_fields=['municipio', 'data', 'hora_inicio', 'informante', 'tipo_pesquisa'])
def criar_visita():
    """Cria uma nova visita"""
    try:
        data = request.validated_data
        
        # Validar dados específicos de visita
        validated_data = VisitaValidator.validate_visita_data(data)
        
        # Criar visita
        visita = Visita(
            municipio=validated_data['municipio'],
            data=validated_data['data'],
            hora_inicio=validated_data['hora_inicio'],
            hora_fim=validated_data['hora_fim'],
            informante=validated_data['informante'],
            tipo_pesquisa=validated_data['tipo_pesquisa'],
            tipo_informante=validated_data['tipo_informante'],
            observacoes=validated_data['observacoes'],
            status='agendada'
        )
        
        db.session.add(visita)
        db.session.commit()
        
        # Criar checklist automaticamente
        checklist = Checklist(visita_id=visita.id)
        db.session.add(checklist)
        db.session.commit()
        
        # Associar checklist à visita
        visita.checklist_id = checklist.id
        db.session.commit()
        
        return APIResponse.success(
            data=visita.to_dict(),
            message="Visita criada com sucesso",
            status_code=201
        )
        
    except ValidationError as e:
        db.session.rollback()
        return APIResponse.validation_error(str(e))
    except Exception as e:
        db.session.rollback()
        return APIResponse.error(f"Erro ao criar visita: {str(e)}")

@api_bp.route('/visitas/<int:visita_id>', methods=['GET'])
def get_visita(visita_id):
    """Obtém uma visita específica"""
    try:
        visita = Visita.query.get(visita_id)
        if not visita:
            return APIResponse.not_found("Visita")
        
        return APIResponse.success(data=visita.to_dict())
    except Exception as e:
        return APIResponse.error(f"Erro ao buscar visita: {str(e)}")

@api_bp.route('/visitas/<int:visita_id>', methods=['PUT'])
@validate_json_input(required_fields=['municipio', 'data', 'hora_inicio', 'informante', 'tipo_pesquisa'])
def atualizar_visita(visita_id):
    """Atualiza uma visita existente"""
    try:
        visita = Visita.query.get(visita_id)
        if not visita:
            return APIResponse.not_found("Visita")
        
        if not visita.pode_ser_editada():
            return APIResponse.error(
                "Esta visita não pode ser editada no status atual",
                error_type="business_rule_violation",
                status_code=400
            )
        
        data = request.validated_data
        validated_data = VisitaValidator.validate_visita_data(data)
        
        # Atualizar campos
        visita.municipio = validated_data['municipio']
        visita.data = validated_data['data']
        visita.hora_inicio = validated_data['hora_inicio']
        visita.hora_fim = validated_data['hora_fim']
        visita.local = validated_data.get('local', validated_data.get('informante', 'Local não especificado'))
        visita.tipo_pesquisa = validated_data['tipo_pesquisa']
        visita.tipo_informante = validated_data['tipo_informante']
        visita.observacoes = validated_data['observacoes']
        visita.data_atualizacao = datetime.now()
        
        db.session.commit()
        
        return APIResponse.success(
            data=visita.to_dict(),
            message="Visita atualizada com sucesso"
        )
        
    except ValidationError as e:
        db.session.rollback()
        return APIResponse.validation_error(str(e))
    except Exception as e:
        db.session.rollback()
        return APIResponse.error(f"Erro ao atualizar visita: {str(e)}")

@api_bp.route('/visitas/<int:visita_id>', methods=['DELETE'])
def excluir_visita(visita_id):
    """Exclui uma visita específica"""
    try:
        # Verificar se a visita existe
        visita = Visita.query.get(visita_id)
        if not visita:
            return APIResponse.not_found("Visita", data={'visita_id': visita_id})
        
        # Verificar se pode ser excluída
        if not visita.pode_ser_excluida():
            return APIResponse.error(
                "Esta visita não pode ser excluída no status atual",
                error_type="business_rule_violation",
                status_code=400,
                data={
                    'visita_id': visita_id,
                    'status_atual': visita.status
                }
            )
        
        # Tentar excluir
        success = Visita.excluir_visita(visita_id)
        if success:
            return APIResponse.success(
                message="Visita excluída com sucesso",
                data={'visita_id': visita_id}
            )
        else:
            return APIResponse.error(
                "Erro interno ao excluir visita",
                error_type="delete_failed", 
                data={'visita_id': visita_id}
            )
            
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao excluir visita {visita_id}: {str(e)}")
        return APIResponse.error(f"Erro ao excluir visita: {str(e)}")

@api_bp.route('/test-delete', methods=['GET'])
def test_delete_endpoint():
    """Endpoint de teste para verificar se blueprint está funcionando"""
    return APIResponse.success(message="CÓDIGO ATUALIZADO - v2.0 - DELETE funcionando!", data={
        'blueprint': 'api_bp',
        'url_prefix': '/api',
        'delete_route': '/api/visitas/<int:visita_id>',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0-UPDATED'
    })

@api_bp.route('/test-status', methods=['POST'])
def test_status_endpoint():
    """Endpoint de teste para verificar POST status"""
    try:
        data = request.get_json()
        return jsonify({
            'success': True,
            'message': 'POST status está funcionando!',
            'received_data': data
        })
    except Exception as e:
        return jsonify({'error': f'Erro no teste: {str(e)}'}), 500

@api_bp.route('/visitas/<int:visita_id>/status', methods=['POST'])
def atualizar_status_visita(visita_id):
    """Atualiza status de uma visita"""
    try:
        # Validação básica
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({'error': 'Campo status é obrigatório'}), 400
        
        novo_status = data['status']
        if not novo_status:
            return jsonify({'error': 'Status não pode estar vazio'}), 400
        
        # Buscar visita
        visita = Visita.query.get(visita_id)
        if not visita:
            return jsonify({'error': 'Visita não encontrada'}), 404
        
        # Atualizar status
        visita.status = novo_status.strip()
        visita.data_atualizacao = datetime.now()
        
        db.session.commit()
        
        # SINCRONIZAR E RECALCULAR TODAS AS MÉTRICAS
        entidades_sincronizadas = 0
        metricas_atualizadas = False
        
        try:
            # 1. Sincronizar questionários com status da visita
            from gestao_visitas.models.questionarios_obrigatorios import EntidadeIdentificada, ProgressoQuestionarios
            entidades_sincronizadas = EntidadeIdentificada.sincronizar_entidades_por_visita(visita_id)
            
            # 2. Sempre recalcular progresso do município (independente de entidades)
            ProgressoQuestionarios.calcular_progresso_municipio(visita.municipio)
            
            # 3. Atualizar caches relacionados
            try:
                from gestao_visitas.services.redis_cache import redis_cache
                # Limpar cache específico do município
                redis_cache.clear_pattern(f"dashboard:*{visita.municipio}*")
                redis_cache.clear_pattern(f"progresso:*{visita.municipio}*")
                redis_cache.clear_pattern("mapa_progresso:*")
                print(f"🗑️ Cache limpo para dashboards do município {visita.municipio}")
            except Exception as cache_error:
                print(f"⚠️ Erro ao limpar cache: {str(cache_error)}")
            
            metricas_atualizadas = True
            print(f"📊 Métricas atualizadas para município {visita.municipio} após mudança de status para '{novo_status}'")
            
        except Exception as sync_error:
            print(f"⚠️ Erro na sincronização de métricas: {str(sync_error)}")
            # Continue mesmo se a sincronização falhar
        
        return jsonify({
            'success': True,
            'message': 'Status atualizado com sucesso',
            'data': {
                'visita_id': visita_id,
                'status': visita.status,
                'municipio': visita.municipio,
                'data_atualizacao': visita.data_atualizacao.strftime('%d/%m/%Y %H:%M'),
                'entidades_sincronizadas': entidades_sincronizadas,
                'metricas_atualizadas': metricas_atualizadas
            }
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        error_msg = str(e)
        tb = traceback.format_exc()
        print(f"❌ Erro ao atualizar status da visita {visita_id}: {error_msg}")
        print(f"❌ Traceback completo:\n{tb}")
        
        # Log to file
        import logging
        logger = logging.getLogger('pnsb_errors')
        logger.error(f"Status update error for visit {visita_id}: {error_msg}\n{tb}")
        
        # Return more detailed error in development
        return jsonify({
            'error': 'Erro ao atualizar status',
            'details': error_msg,
            'visita_id': visita_id
        }), 500

# === ROTAS DE CHECKLIST ===

@api_bp.route('/checklist/<int:visita_id>', methods=['GET'])
def get_checklist_por_visita(visita_id):
    """Obtém checklist de uma visita"""
    try:
        checklist = Checklist.query.filter_by(visita_id=visita_id).first()
        if not checklist:
            # Criar checklist se não existir
            checklist = Checklist(visita_id=visita_id)
            db.session.add(checklist)
            db.session.commit()
        
        return APIResponse.success(data=checklist.to_dict())
    except Exception as e:
        return APIResponse.error(f"Erro ao buscar checklist: {str(e)}")

@api_bp.route('/checklist/<int:visita_id>', methods=['POST'])
@validate_json_input(required_fields=['etapa'])
def salvar_checklist(visita_id):
    """Salva dados do checklist"""
    try:
        visita = Visita.query.get(visita_id)
        if not visita:
            return APIResponse.not_found("Visita")
        
        data = request.validated_data
        dados = data.get('dados', {})
        etapa = data.get('etapa')
        
        checklist = visita.checklist or Checklist(visita_id=visita_id)
        campos_etapa = get_campos_etapa(etapa)
        
        # Atualizar campos da etapa
        for campo in campos_etapa:
            if campo in dados:
                setattr(checklist, campo, dados[campo])
        
        # Salvar observações por etapa
        if etapa == 'Antes da Visita' and 'observacoes_0' in dados:
            checklist.observacoes_antes = dados['observacoes_0']
        elif etapa == 'Durante a Visita' and 'observacoes_1' in dados:
            checklist.observacoes_durante = dados['observacoes_1']
        elif etapa == 'Após a Visita' and 'observacoes_2' in dados:
            checklist.observacoes_apos = dados['observacoes_2']
        
        # Salvar itens marcados
        if 'itens_marcados' in dados:
            checklist.itens_marcados = dados['itens_marcados']
        
        if not visita.checklist:
            db.session.add(checklist)
            visita.checklist = checklist
        
        db.session.commit()
        
        return APIResponse.success(message="Checklist salvo com sucesso")
        
    except Exception as e:
        db.session.rollback()
        return APIResponse.error(f"Erro ao salvar checklist: {str(e)}")

# === ROTAS DE CONTATOS ===

@api_bp.route('/contatos', methods=['GET'])
def listar_contatos():
    """Lista todos os contatos"""
    try:
        contatos = Contato.query.all()
        return APIResponse.success(data=[contato.to_dict() for contato in contatos])
    except Exception as e:
        return APIResponse.error(f"Erro ao listar contatos: {str(e)}")

@api_bp.route('/contatos/importar', methods=['POST'])
def importar_contatos():
    """Importa contatos de arquivo CSV"""
    try:
        if 'arquivo' not in request.files:
            return APIResponse.validation_error("Nenhum arquivo enviado")
        
        arquivo = request.files['arquivo']
        if arquivo.filename == '':
            return APIResponse.validation_error("Nenhum arquivo selecionado")
        
        if not arquivo.filename.endswith('.csv'):
            return APIResponse.validation_error("Arquivo deve ser CSV")
        
        # Processar CSV
        df = pd.read_csv(arquivo)
        
        for _, row in df.iterrows():
            municipio = row['Município']
            campo = row['Campo']
            
            contato = Contato.query.filter_by(
                municipio=municipio,
                tipo_pesquisa='MRS' if 'MRS' in arquivo.filename else 'MAP'
            ).first()
            
            if not contato:
                contato = Contato(
                    municipio=municipio,
                    tipo_pesquisa='MRS' if 'MRS' in arquivo.filename else 'MAP',
                    tipo_entidade=TipoEntidade.PREFEITURA.value
                )
            
            # Atualizar campos baseado no tipo
            if campo == 'Local':
                contato.local = row['Mais provável']
                contato.fonte_local = FonteInformacao.MAIS_PROVAVEL.value
            elif campo == 'Responsavel':
                contato.responsavel = row['Mais provável']
                contato.fonte_responsavel = FonteInformacao.MAIS_PROVAVEL.value
            elif campo == 'Endereco':
                contato.endereco = row['Mais provável']
                contato.fonte_endereco = FonteInformacao.MAIS_PROVAVEL.value
            elif campo == 'Contato':
                contato.contato = row['Mais provável']
                contato.fonte_contato = FonteInformacao.MAIS_PROVAVEL.value
            elif campo == 'Horario':
                contato.horario = row['Mais provável']
                contato.fonte_horario = FonteInformacao.MAIS_PROVAVEL.value
            
            db.session.add(contato)
        
        db.session.commit()
        return APIResponse.success(message="Contatos importados com sucesso")
        
    except Exception as e:
        db.session.rollback()
        return APIResponse.error(f"Erro ao importar contatos: {str(e)}")

@api_bp.route('/contatos_csv')
def contatos_csv():
    """Retorna dados dos arquivos CSV de contatos"""
    try:
        arquivos = [
            ('MAP', os.path.join(os.path.dirname(__file__), '..', 'pesquisa_contatos_prefeituras', 'Comparacao_MAP.csv')),
            ('MRS', os.path.join(os.path.dirname(__file__), '..', 'pesquisa_contatos_prefeituras', 'Comparacao_MRS.csv'))
        ]
        
        linhas = []
        for tipo, caminho in arquivos:
            if os.path.exists(caminho):
                with open(caminho, encoding='latin1') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        linhas.append({
                            'municipio': row.get('Município', '').strip(),
                            'campo': row.get('Campo', '').strip(),
                            'chatgpt': row.get('ChatGPT', '').strip(),
                            'gemini': row.get('Gemini', '').strip(),
                            'grok': row.get('Grok', '').strip(),
                            'mais_provavel': row.get('Mais provável', '').strip(),
                            'tipo_pesquisa': tipo,
                            'tipo_informante': 'prefeitura'
                        })
        
        return APIResponse.success(data=linhas)
    except Exception as e:
        return APIResponse.error(f"Erro ao ler dados CSV: {str(e)}")

# === ROTAS DE RELATÓRIOS ===

@api_bp.route('/relatorios/<periodo>', methods=['GET'])
def get_relatorio(periodo):
    """Gera relatório por período"""
    try:
        from datetime import timedelta
        
        if periodo == 'hoje':
            data_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            data_fim = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        elif periodo == 'semana':
            data_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            data_fim = data_inicio + timedelta(days=7)
        elif periodo == 'mes':
            data_inicio = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if data_inicio.month == 12:
                data_fim = datetime(data_inicio.year + 1, 1, 1) - timedelta(days=1)
            else:
                data_fim = datetime(data_inicio.year, data_inicio.month + 1, 1) - timedelta(days=1)
        else:
            data_inicio = datetime.strptime(request.args.get('inicio'), '%Y-%m-%d')
            data_fim = datetime.strptime(request.args.get('fim'), '%Y-%m-%d')
        
        relatorio = relatorio_service.gerar_relatorio_periodo(data_inicio, data_fim)
        return APIResponse.success(data=relatorio)
        
    except Exception as e:
        return APIResponse.error(f"Erro ao gerar relatório: {str(e)}")

@api_bp.route('/relatorios/custom', methods=['GET'])
def get_relatorio_custom():
    """Gera relatório personalizado com período customizado"""
    try:
        # Obter parâmetros da query string
        inicio_str = request.args.get('inicio')
        fim_str = request.args.get('fim')
        
        if not inicio_str or not fim_str:
            return APIResponse.validation_error("Parâmetros 'inicio' e 'fim' são obrigatórios")
        
        try:
            data_inicio = datetime.strptime(inicio_str, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
            data_fim = datetime.strptime(fim_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
        except ValueError:
            return APIResponse.validation_error("Formato de data inválido. Use YYYY-MM-DD")
        
        if data_inicio > data_fim:
            return APIResponse.validation_error("Data de início deve ser anterior à data de fim")
        
        # Gerar relatório personalizado
        relatorio = relatorio_service.gerar_relatorio_periodo(data_inicio, data_fim)
        
        # Adicionar informações do período customizado
        relatorio['periodo_personalizado'] = {
            'inicio': inicio_str,
            'fim': fim_str,
            'dias': (data_fim - data_inicio).days + 1
        }
        
        return APIResponse.success(data=relatorio)
        
    except Exception as e:
        return APIResponse.error(f"Erro ao gerar relatório personalizado: {str(e)}")

# === ROTAS DE CHAT IA ===

@api_bp.route('/chat', methods=['POST'])
@validate_json_input(required_fields=['message'])
def chat_ia():
    """Chat com IA Gemini (com fallback inteligente)"""
    try:
        user_message = request.validated_data['message']
        context = request.validated_data.get('context', None)
        
        # Usar o gerenciador de APIs com fallback
        result = api_manager.chat_with_ai(user_message, context)
        
        if result['success']:
            return APIResponse.success(data={
                'response': result['response'],
                'source': result.get('source', 'ai'),
                'fallback_used': False
            })
        else:
            # Retornar resposta de fallback como sucesso
            return APIResponse.success(data={
                'response': result['response'],
                'source': 'fallback',
                'fallback_used': True,
                'message': result.get('message', 'IA temporariamente indisponível')
            })
        
    except Exception as e:
        # Fallback final em caso de erro inesperado
        return APIResponse.success(data={
            'response': 'Desculpe, estou com dificuldades técnicas. Por favor, tente novamente ou use as funcionalidades do sistema diretamente.',
            'source': 'error_fallback',
            'fallback_used': True,
            'error': str(e)
        })

# === ROTAS DE ROTA/MAPAS ===

@api_bp.route('/rota', methods=['POST'])
@validate_json_input(required_fields=['origem', 'destino'])
def calcular_rota():
    """Calcula rota entre dois pontos (com fallback)"""
    try:
        data = request.validated_data
        origem = data['origem']
        destino = data['destino']
        
        # Usar o gerenciador de APIs com fallback
        resultado = api_manager.calculate_route(origem, destino)
        
        if resultado.get('success'):
            return APIResponse.success(data=resultado)
        elif resultado.get('fallback'):
            # Retornar informação de fallback
            return APIResponse.success(data={
                'fallback_used': True,
                'message': resultado['message'],
                'recommendation': 'Configure a API do Google Maps para cálculos precisos',
                'origin': origem,
                'destination': destino
            })
        else:
            return APIResponse.error(resultado.get('erro', 'Erro desconhecido no cálculo da rota'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao calcular rota: {str(e)}")

# === ROTAS DE ALERTAS CRÍTICOS ===

@api_bp.route('/alertas/criticos', methods=['GET'])
def get_alertas_criticos():
    """Retorna alertas críticos de prazos PNSB 2024"""
    try:
        from ..services.alertas_prazos_criticos import sistema_alertas
        
        # Verificar todos os alertas
        alertas = sistema_alertas.verificar_todos_alertas()
        resumo = sistema_alertas.get_resumo_alertas()
        
        # Converter para formato JSON
        alertas_json = []
        for alerta in alertas:
            alerta_dict = {
                'id': alerta.id,
                'tipo': alerta.tipo.value,
                'nivel': alerta.nivel.value,
                'titulo': alerta.titulo,
                'descricao': alerta.descricao,
                'municipio': alerta.municipio,
                'entidade': alerta.entidade,
                'dias_restantes': alerta.dias_restantes,
                'data_limite': alerta.data_limite.isoformat() if alerta.data_limite else None,
                'acao_recomendada': alerta.acao_recomendada,
                'metadata': alerta.metadata,
                'criado_em': alerta.criado_em.isoformat() if alerta.criado_em else None
            }
            alertas_json.append(alerta_dict)
        
        return APIResponse.success(data={
            'alertas': alertas_json,
            'resumo': resumo,
            'gerado_em': datetime.now().isoformat()
        })
        
    except Exception as e:
        return APIResponse.error(f"Erro ao buscar alertas críticos: {str(e)}")

@api_bp.route('/alertas/municipio/<municipio>', methods=['GET'])
def get_alertas_municipio(municipio):
    """Retorna alertas específicos de um município"""
    try:
        from ..services.alertas_prazos_criticos import sistema_alertas
        
        sistema_alertas.verificar_todos_alertas()
        alertas_municipio = sistema_alertas.get_alertas_por_municipio(municipio)
        
        alertas_json = []
        for alerta in alertas_municipio:
            alerta_dict = {
                'id': alerta.id,
                'tipo': alerta.tipo.value,
                'nivel': alerta.nivel.value,
                'titulo': alerta.titulo,
                'descricao': alerta.descricao,
                'entidade': alerta.entidade,
                'dias_restantes': alerta.dias_restantes,
                'acao_recomendada': alerta.acao_recomendada,
                'metadata': alerta.metadata
            }
            alertas_json.append(alerta_dict)
        
        return APIResponse.success(data={
            'municipio': municipio,
            'alertas': alertas_json,
            'total': len(alertas_json)
        })
        
    except Exception as e:
        return APIResponse.error(f"Erro ao buscar alertas do município: {str(e)}")

# === ROTAS DE STATUS DAS APIs ===

@api_bp.route('/status/apis', methods=['GET'])
def get_apis_status():
    """Retorna status das APIs externas configuradas"""
    try:
        status = api_manager.get_system_status()
        return APIResponse.success(data=status)
    except Exception as e:
        return APIResponse.error(f"Erro ao verificar status das APIs: {str(e)}")

# === ROTAS DE ACOMPANHAMENTO AUTOMÁTICO ===

@api_bp.route('/rastreamento/dashboard', methods=['GET'])
def get_dashboard_rastreamento():
    """Dashboard completo de rastreamento de questionários"""
    try:
        from ..services.rastreamento_questionarios import rastreamento_questionarios
        
        dashboard = rastreamento_questionarios.obter_dashboard_completo()
        
        return APIResponse.success(data=dashboard)
        
    except Exception as e:
        return APIResponse.error(f"Erro ao gerar dashboard de rastreamento: {str(e)}")

@api_bp.route('/rastreamento/questionario/<municipio>/<tipo_pesquisa>', methods=['GET'])
def get_status_questionario(municipio, tipo_pesquisa):
    """Status detalhado de um questionário específico"""
    try:
        from ..services.rastreamento_questionarios import rastreamento_questionarios
        
        status = rastreamento_questionarios.obter_status_detalhado_questionario(municipio, tipo_pesquisa)
        
        return APIResponse.success(data=status)
        
    except Exception as e:
        return APIResponse.error(f"Erro ao obter status do questionário: {str(e)}")

@api_bp.route('/rastreamento/questionario/<municipio>/<tipo_pesquisa>', methods=['PUT'])
@validate_json_input(required_fields=['novo_status'])
def atualizar_status_questionario(municipio, tipo_pesquisa):
    """Atualiza status de um questionário com validações"""
    try:
        from ..services.rastreamento_questionarios import rastreamento_questionarios
        
        data = request.validated_data
        novo_status = data['novo_status']
        dados_atualizacao = data.get('dados_atualizacao', {})
        
        resultado = rastreamento_questionarios.atualizar_status_questionario_avancado(
            municipio, tipo_pesquisa, novo_status, dados_atualizacao
        )
        
        if resultado.get('sucesso'):
            return APIResponse.success(data=resultado)
        else:
            return APIResponse.error(resultado.get('erro', 'Erro desconhecido'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao atualizar status do questionário: {str(e)}")

@api_bp.route('/rastreamento/plano-coleta', methods=['POST'])
def gerar_plano_coleta():
    """Gera plano de coleta otimizado"""
    try:
        from ..services.rastreamento_questionarios import rastreamento_questionarios
        
        data = request.get_json() or {}
        parametros = data.get('parametros', {})
        
        plano = rastreamento_questionarios.gerar_plano_coleta_otimizado(parametros)
        
        return APIResponse.success(data=plano)
        
    except Exception as e:
        return APIResponse.error(f"Erro ao gerar plano de coleta: {str(e)}")

@api_bp.route('/rastreamento/qualidade', methods=['GET'])
def monitorar_qualidade_dados():
    """Monitora qualidade dos dados coletados"""
    try:
        from ..services.rastreamento_questionarios import rastreamento_questionarios
        
        qualidade = rastreamento_questionarios.monitorar_qualidade_dados()
        
        return APIResponse.success(data=qualidade)
        
    except Exception as e:
        return APIResponse.error(f"Erro ao monitorar qualidade: {str(e)}")

@api_bp.route('/rastreamento/insights', methods=['GET'])
def gerar_insights_preditivos():
    """Gera insights preditivos sobre coleta"""
    try:
        from ..services.rastreamento_questionarios import rastreamento_questionarios
        
        insights = rastreamento_questionarios.gerar_insights_preditivos_coleta()
        
        return APIResponse.success(data=insights)
        
    except Exception as e:
        return APIResponse.error(f"Erro ao gerar insights preditivos: {str(e)}")

# === ROTAS DE ORGANIZAÇÃO PESSOAL ===

@api_bp.route('/organizacao/dashboard', methods=['GET'])
def get_dashboard_pessoal():
    """Dashboard pessoal completo"""
    try:
        from ..services.organizacao_pessoal import organizacao_pessoal
        
        dashboard = organizacao_pessoal.obter_dashboard_pessoal()
        
        return APIResponse.success(data=dashboard)
        
    except Exception as e:
        return APIResponse.error(f"Erro ao gerar dashboard pessoal: {str(e)}")

@api_bp.route('/organizacao/tarefas', methods=['POST'])
@validate_json_input(required_fields=['titulo', 'tipo', 'prioridade'])
def criar_tarefa_pessoal():
    """Cria nova tarefa pessoal"""
    try:
        from ..services.organizacao_pessoal import organizacao_pessoal
        
        dados_tarefa = request.validated_data
        resultado = organizacao_pessoal.criar_tarefa(dados_tarefa)
        
        if resultado.get('sucesso'):
            return APIResponse.success(data=resultado)
        else:
            return APIResponse.error(resultado.get('erro', 'Erro desconhecido'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao criar tarefa: {str(e)}")

@api_bp.route('/organizacao/tarefas/<id_tarefa>', methods=['PUT'])
def atualizar_tarefa_pessoal(id_tarefa):
    """Atualiza tarefa pessoal existente"""
    try:
        from ..services.organizacao_pessoal import organizacao_pessoal
        
        dados_atualizacao = request.get_json() or {}
        resultado = organizacao_pessoal.atualizar_tarefa(id_tarefa, dados_atualizacao)
        
        if resultado.get('sucesso'):
            return APIResponse.success(data=resultado)
        else:
            return APIResponse.error(resultado.get('erro', 'Erro desconhecido'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao atualizar tarefa: {str(e)}")

@api_bp.route('/organizacao/notas', methods=['POST'])
@validate_json_input(required_fields=['titulo', 'conteudo'])
def criar_nota_pessoal():
    """Cria nova nota pessoal"""
    try:
        from ..services.organizacao_pessoal import organizacao_pessoal
        
        dados_nota = request.validated_data
        resultado = organizacao_pessoal.criar_nota(dados_nota)
        
        if resultado.get('sucesso'):
            return APIResponse.success(data=resultado)
        else:
            return APIResponse.error(resultado.get('erro', 'Erro desconhecido'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao criar nota: {str(e)}")

@api_bp.route('/organizacao/calendario', methods=['POST'])
@validate_json_input(required_fields=['titulo', 'data_inicio', 'data_fim'])
def criar_evento_calendario():
    """Cria novo evento no calendário"""
    try:
        from ..services.organizacao_pessoal import organizacao_pessoal
        
        dados_evento = request.validated_data
        resultado = organizacao_pessoal.criar_evento_calendario(dados_evento)
        
        if resultado.get('sucesso'):
            return APIResponse.success(data=resultado)
        else:
            return APIResponse.error(resultado.get('erro', 'Erro desconhecido'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao criar evento: {str(e)}")

@api_bp.route('/organizacao/produtividade', methods=['GET'])
def gerar_relatorio_produtividade():
    """Gera relatório de produtividade"""
    try:
        from ..services.organizacao_pessoal import organizacao_pessoal
        
        periodo = request.args.get('periodo', 'semana')
        relatorio = organizacao_pessoal.gerar_relatorio_produtividade(periodo)
        
        return APIResponse.success(data=relatorio)
        
    except Exception as e:
        return APIResponse.error(f"Erro ao gerar relatório de produtividade: {str(e)}")

@api_bp.route('/organizacao/agenda', methods=['GET'])
def obter_agenda_inteligente():
    """Obtém agenda inteligente com sugestões"""
    try:
        from ..services.organizacao_pessoal import organizacao_pessoal
        from datetime import date, datetime
        
        data_str = request.args.get('data')
        data_agenda = datetime.strptime(data_str, '%Y-%m-%d').date() if data_str else date.today()
        
        agenda = organizacao_pessoal.obter_agenda_inteligente(data_agenda)
        
        return APIResponse.success(data=agenda)
        
    except Exception as e:
        return APIResponse.error(f"Erro ao obter agenda inteligente: {str(e)}")

# === ROTAS DO WHATSAPP BUSINESS ===

@api_bp.route('/whatsapp/configurar', methods=['POST'])
@validate_json_input(required_fields=['phone_number_id', 'access_token', 'verify_token'])
def configurar_whatsapp_api():
    """Configura credenciais do WhatsApp Business API"""
    try:
        from ..services.whatsapp_business import whatsapp_business
        
        data = request.validated_data
        resultado = whatsapp_business.configurar_api(
            data['phone_number_id'],
            data['access_token'],
            data['verify_token']
        )
        
        if resultado.get('sucesso'):
            return APIResponse.success(data=resultado)
        else:
            return APIResponse.error(resultado.get('erro', 'Erro na configuração'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao configurar WhatsApp API: {str(e)}")

@api_bp.route('/whatsapp/agendamento/<int:visita_id>', methods=['POST'])
def enviar_mensagem_agendamento(visita_id):
    """Envia mensagem de agendamento via WhatsApp"""
    try:
        from ..services.whatsapp_business import whatsapp_business
        
        dados_personalizacao = request.get_json() or {}
        resultado = whatsapp_business.enviar_mensagem_agendamento(visita_id, dados_personalizacao)
        
        if resultado.get('sucesso'):
            return APIResponse.success(data=resultado)
        else:
            return APIResponse.error(resultado.get('erro', 'Erro no envio'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao enviar mensagem de agendamento: {str(e)}")

@api_bp.route('/whatsapp/follow-up/<int:visita_id>', methods=['POST'])
def enviar_follow_up_questionario(visita_id):
    """Envia follow-up de questionário via WhatsApp"""
    try:
        from ..services.whatsapp_business import whatsapp_business
        
        data = request.get_json() or {}
        tipo_follow_up = data.get('tipo_follow_up', 'primeira_tentativa')
        
        resultado = whatsapp_business.enviar_follow_up_questionario(visita_id, tipo_follow_up)
        
        if resultado.get('sucesso'):
            return APIResponse.success(data=resultado)
        else:
            return APIResponse.error(resultado.get('erro', 'Erro no envio'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao enviar follow-up: {str(e)}")

@api_bp.route('/whatsapp/dashboard', methods=['GET'])
def get_dashboard_whatsapp():
    """Dashboard do WhatsApp Business"""
    try:
        from ..services.whatsapp_business import whatsapp_business
        
        dashboard = whatsapp_business.obter_dashboard_whatsapp()
        
        return APIResponse.success(data=dashboard)
        
    except Exception as e:
        return APIResponse.error(f"Erro ao gerar dashboard WhatsApp: {str(e)}")

@api_bp.route('/whatsapp/webhook', methods=['GET', 'POST'])
def whatsapp_webhook():
    """Webhook do WhatsApp Business"""
    try:
        from ..services.whatsapp_business import whatsapp_business
        
        if request.method == 'GET':
            # Verificação do webhook
            verify_token = request.args.get('hub.verify_token')
            challenge = request.args.get('hub.challenge')
            
            if verify_token == whatsapp_business.verify_token:
                return challenge
            else:
                return APIResponse.error("Token de verificação inválido", status_code=403)
        
        elif request.method == 'POST':
            # Processar webhook
            dados_webhook = request.get_json()
            resultado = whatsapp_business.processar_webhook(dados_webhook)
            
            return APIResponse.success(data=resultado)
        
    except Exception as e:
        return APIResponse.error(f"Erro no webhook WhatsApp: {str(e)}")

# === ROTAS DE OTIMIZAÇÃO ML DE ROTAS ===

@api_bp.route('/rotas-ml/treinar-modelo', methods=['POST'])
def treinar_modelo_rotas():
    """Treina modelo ML para otimização de rotas"""
    try:
        from ..services.otimizacao_rotas_ml import otimizacao_rotas_ml
        
        resultado = otimizacao_rotas_ml.treinar_modelo_historico()
        
        if resultado.get('sucesso'):
            return APIResponse.success(data=resultado)
        else:
            return APIResponse.error(resultado.get('erro', 'Erro no treinamento'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao treinar modelo de rotas: {str(e)}")

@api_bp.route('/rotas-ml/otimizar', methods=['POST'])
@validate_json_input(required_fields=['visitas'])
def otimizar_rota_inteligente():
    """Otimização inteligente de rota com ML"""
    try:
        from ..services.otimizacao_rotas_ml import otimizacao_rotas_ml
        
        data = request.validated_data
        visitas = data['visitas']
        parametros = data.get('parametros', {})
        
        resultado = otimizacao_rotas_ml.otimizar_rota_inteligente(visitas, parametros)
        
        if resultado.get('erro'):
            return APIResponse.error(resultado['erro'])
        else:
            return APIResponse.success(data=resultado)
        
    except Exception as e:
        return APIResponse.error(f"Erro na otimização de rota: {str(e)}")

@api_bp.route('/rotas-ml/prever-tempo', methods=['POST'])
@validate_json_input(required_fields=['origem', 'destino', 'data_hora'])
def prever_tempo_viagem():
    """Previsão inteligente de tempo de viagem"""
    try:
        from ..services.otimizacao_rotas_ml import otimizacao_rotas_ml
        from datetime import datetime
        
        data = request.validated_data
        origem = data['origem']
        destino = data['destino']
        data_hora = datetime.fromisoformat(data['data_hora'])
        
        resultado = otimizacao_rotas_ml.prever_tempo_viagem(origem, destino, data_hora)
        
        if resultado.get('erro'):
            return APIResponse.error(resultado['erro'])
        else:
            return APIResponse.success(data=resultado)
        
    except Exception as e:
        return APIResponse.error(f"Erro na previsão de tempo: {str(e)}")

@api_bp.route('/rotas-ml/padroes-sazonais', methods=['GET'])
def analisar_padroes_sazonais():
    """Análise de padrões sazonais"""
    try:
        from ..services.otimizacao_rotas_ml import otimizacao_rotas_ml
        
        resultado = otimizacao_rotas_ml.analisar_padroes_sazonais()
        
        if resultado.get('erro'):
            return APIResponse.error(resultado['erro'])
        else:
            return APIResponse.success(data=resultado)
        
    except Exception as e:
        return APIResponse.error(f"Erro na análise sazonal: {str(e)}")

@api_bp.route('/rotas-ml/cronograma-semanal', methods=['POST'])
@validate_json_input(required_fields=['visitas_semana'])
def otimizar_cronograma_semanal():
    """Otimização de cronograma semanal"""
    try:
        from ..services.otimizacao_rotas_ml import otimizacao_rotas_ml
        
        data = request.validated_data
        visitas_semana = data['visitas_semana']
        
        resultado = otimizacao_rotas_ml.otimizar_cronograma_semanal(visitas_semana)
        
        if resultado.get('erro'):
            return APIResponse.error(resultado['erro'])
        else:
            return APIResponse.success(data=resultado)
        
    except Exception as e:
        return APIResponse.error(f"Erro na otimização semanal: {str(e)}")

@api_bp.route('/rotas-ml/feedback/<rota_id>', methods=['POST'])
@validate_json_input(required_fields=['dados_execucao'])
def registrar_feedback_rota(rota_id):
    """Registra feedback de execução de rota"""
    try:
        from ..services.otimizacao_rotas_ml import otimizacao_rotas_ml
        
        data = request.validated_data
        dados_execucao = data['dados_execucao']
        
        resultado = otimizacao_rotas_ml.feedback_rota_executada(rota_id, dados_execucao)
        
        if resultado.get('erro'):
            return APIResponse.error(resultado['erro'])
        else:
            return APIResponse.success(data=resultado)
        
    except Exception as e:
        return APIResponse.error(f"Erro ao registrar feedback: {str(e)}")

# === ROTAS DE CHAT E COLABORAÇÃO ===

@api_bp.route('/chat/enviar-mensagem', methods=['POST'])
@validate_json_input(required_fields=['canal_id', 'autor_id', 'conteudo'])
def enviar_mensagem_chat():
    """Envia mensagem no chat"""
    try:
        from ..services.chat_colaboracao import chat_colaboracao, TipoMensagem
        
        data = request.validated_data
        tipo_msg = TipoMensagem(data.get('tipo', 'texto'))
        
        resultado = chat_colaboracao.enviar_mensagem(
            canal_id=data['canal_id'],
            autor_id=data['autor_id'],
            conteudo=data['conteudo'],
            tipo=tipo_msg,
            metadata=data.get('metadata')
        )
        
        if resultado.get('sucesso'):
            return APIResponse.success(data=resultado)
        else:
            return APIResponse.error(resultado.get('erro', 'Erro no envio'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao enviar mensagem: {str(e)}")

@api_bp.route('/chat/criar-canal', methods=['POST'])
@validate_json_input(required_fields=['nome', 'tipo', 'criado_por'])
def criar_canal_chat():
    """Cria novo canal de chat"""
    try:
        from ..services.chat_colaboracao import chat_colaboracao, TipoCanal
        
        data = request.validated_data
        tipo_canal = TipoCanal(data['tipo'])
        
        resultado = chat_colaboracao.criar_canal(
            nome=data['nome'],
            tipo=tipo_canal,
            criado_por=data['criado_por'],
            configuracao=data.get('configuracao')
        )
        
        if resultado.get('sucesso'):
            return APIResponse.success(data=resultado)
        else:
            return APIResponse.error(resultado.get('erro', 'Erro na criação'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao criar canal: {str(e)}")

@api_bp.route('/chat/mensagens/<canal_id>', methods=['GET'])
def obter_mensagens_canal(canal_id):
    """Obtém mensagens de um canal"""
    try:
        from ..services.chat_colaboracao import chat_colaboracao
        
        usuario_id = request.args.get('usuario_id')
        limite = int(request.args.get('limite', 50))
        antes_de = request.args.get('antes_de')
        
        if not usuario_id:
            return APIResponse.validation_error("usuario_id é obrigatório")
        
        resultado = chat_colaboracao.obter_mensagens_canal(
            canal_id=canal_id,
            usuario_id=usuario_id,
            limite=limite,
            antes_de=antes_de
        )
        
        if resultado.get('erro'):
            return APIResponse.error(resultado['erro'])
        else:
            return APIResponse.success(data=resultado)
        
    except Exception as e:
        return APIResponse.error(f"Erro ao obter mensagens: {str(e)}")

@api_bp.route('/chat/compartilhar-visita', methods=['POST'])
@validate_json_input(required_fields=['visita_id', 'canal_id', 'usuario_id'])
def compartilhar_visita_chat():
    """Compartilha visita no chat"""
    try:
        from ..services.chat_colaboracao import chat_colaboracao
        
        data = request.validated_data
        
        resultado = chat_colaboracao.compartilhar_visita(
            visita_id=data['visita_id'],
            canal_id=data['canal_id'],
            usuario_id=data['usuario_id'],
            comentario=data.get('comentario', '')
        )
        
        if resultado.get('sucesso'):
            return APIResponse.success(data=resultado)
        else:
            return APIResponse.error(resultado.get('erro', 'Erro no compartilhamento'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao compartilhar visita: {str(e)}")

@api_bp.route('/chat/dashboard/<usuario_id>', methods=['GET'])
def obter_dashboard_colaboracao(usuario_id):
    """Dashboard de colaboração do usuário"""
    try:
        from ..services.chat_colaboracao import chat_colaboracao
        
        resultado = chat_colaboracao.obter_dashboard_colaboracao(usuario_id)
        
        if resultado.get('erro'):
            return APIResponse.error(resultado['erro'])
        else:
            return APIResponse.success(data=resultado)
        
    except Exception as e:
        return APIResponse.error(f"Erro ao obter dashboard: {str(e)}")

@api_bp.route('/chat/buscar', methods=['POST'])
@validate_json_input(required_fields=['usuario_id', 'termo_busca'])
def buscar_mensagens_chat():
    """Busca mensagens no chat"""
    try:
        from ..services.chat_colaboracao import chat_colaboracao
        
        data = request.validated_data
        
        resultado = chat_colaboracao.buscar_mensagens(
            usuario_id=data['usuario_id'],
            termo_busca=data['termo_busca'],
            filtros=data.get('filtros')
        )
        
        if resultado.get('erro'):
            return APIResponse.error(resultado['erro'])
        else:
            return APIResponse.success(data=resultado)
        
    except Exception as e:
        return APIResponse.error(f"Erro na busca: {str(e)}")

@api_bp.route('/chat/configurar-notificacoes', methods=['POST'])
@validate_json_input(required_fields=['usuario_id', 'configuracoes'])
def configurar_notificacoes_chat():
    """Configura notificações do chat"""
    try:
        from ..services.chat_colaboracao import chat_colaboracao
        
        data = request.validated_data
        
        resultado = chat_colaboracao.configurar_notificacoes(
            usuario_id=data['usuario_id'],
            configuracoes=data['configuracoes']
        )
        
        if resultado.get('sucesso'):
            return APIResponse.success(data=resultado)
        else:
            return APIResponse.error(resultado.get('erro', 'Erro na configuração'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao configurar notificações: {str(e)}")

@api_bp.route('/chat/relatorio-colaboracao', methods=['GET'])
def gerar_relatorio_colaboracao():
    """Gera relatório de colaboração"""
    try:
        from ..services.chat_colaboracao import chat_colaboracao
        
        periodo = request.args.get('periodo', 'semana')
        
        resultado = chat_colaboracao.gerar_relatorio_colaboracao(periodo)
        
        if resultado.get('erro'):
            return APIResponse.error(resultado['erro'])
        else:
            return APIResponse.success(data=resultado)
        
    except Exception as e:
        return APIResponse.error(f"Erro ao gerar relatório: {str(e)}")

# === ROTAS DE APIS GOVERNAMENTAIS ===

@api_bp.route('/apis-gov/snis/<municipio>', methods=['GET'])
def obter_dados_snis(municipio):
    """Obtém dados SNIS para município"""
    try:
        from ..services.apis_governamentais import apis_governamentais
        
        ano = request.args.get('ano', 2022, type=int)
        
        resultado = apis_governamentais.obter_dados_snis_municipio(municipio, ano)
        
        if resultado.get('sucesso'):
            return APIResponse.success(data=resultado)
        else:
            return APIResponse.error(resultado.get('erro', 'Erro na consulta SNIS'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao consultar SNIS: {str(e)}")

@api_bp.route('/apis-gov/cnpj/<cnpj>', methods=['GET'])
def validar_cnpj_prefeitura(cnpj):
    """Valida CNPJ via Receita Federal"""
    try:
        from ..services.apis_governamentais import apis_governamentais
        
        resultado = apis_governamentais.validar_cnpj_prefeitura(cnpj)
        
        if resultado.get('sucesso'):
            return APIResponse.success(data=resultado)
        else:
            return APIResponse.error(resultado.get('erro', 'Erro na validação CNPJ'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao validar CNPJ: {str(e)}")

@api_bp.route('/apis-gov/siconv/<municipio>', methods=['GET'])
def buscar_convenios_siconv(municipio):
    """Busca convênios no SICONV"""
    try:
        from ..services.apis_governamentais import apis_governamentais
        
        area = request.args.get('area', 'saneamento')
        
        resultado = apis_governamentais.buscar_convenios_siconv(municipio, area)
        
        if resultado.get('sucesso'):
            return APIResponse.success(data=resultado)
        else:
            return APIResponse.error(resultado.get('erro', 'Erro na consulta SICONV'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao consultar SICONV: {str(e)}")

@api_bp.route('/apis-gov/transparencia/<municipio>', methods=['GET'])
def obter_dados_transparencia(municipio):
    """Obtém dados do Portal da Transparência"""
    try:
        from ..services.apis_governamentais import apis_governamentais
        
        resultado = apis_governamentais.obter_dados_transparencia_municipio(municipio)
        
        if resultado.get('sucesso'):
            return APIResponse.success(data=resultado)
        else:
            return APIResponse.error(resultado.get('erro', 'Erro na consulta Transparência'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao consultar Transparência: {str(e)}")

@api_bp.route('/apis-gov/cep/<cep>', methods=['GET'])
def validar_endereco_cep(cep):
    """Valida endereço via CEP"""
    try:
        from ..services.apis_governamentais import apis_governamentais
        
        resultado = apis_governamentais.validar_endereco_correios(cep)
        
        if resultado.get('sucesso'):
            return APIResponse.success(data=resultado)
        else:
            return APIResponse.error(resultado.get('erro', 'Erro na validação CEP'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao validar CEP: {str(e)}")

@api_bp.route('/apis-gov/consolidar/<municipio>', methods=['GET'])
def consolidar_dados_municipio(municipio):
    """Consolida dados de todas as APIs para um município"""
    try:
        from ..services.apis_governamentais import apis_governamentais
        
        resultado = apis_governamentais.consolidar_dados_municipio(municipio)
        
        if resultado.get('sucesso'):
            return APIResponse.success(data=resultado)
        else:
            return APIResponse.error(resultado.get('erro', 'Erro na consolidação'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao consolidar dados: {str(e)}")

@api_bp.route('/apis-gov/relatorio', methods=['GET'])
def gerar_relatorio_apis():
    """Gera relatório de uso das APIs governamentais"""
    try:
        from ..services.apis_governamentais import apis_governamentais
        
        resultado = apis_governamentais.gerar_relatorio_apis()
        
        if resultado.get('erro'):
            return APIResponse.error(resultado['erro'])
        else:
            return APIResponse.success(data=resultado)
        
    except Exception as e:
        return APIResponse.error(f"Erro ao gerar relatório APIs: {str(e)}")

# === ROTAS DE COMPLIANCE LGPD ===

@api_bp.route('/lgpd/log-auditoria', methods=['POST'])
@validate_json_input(required_fields=['operacao', 'recurso', 'dados_alterados', 'usuario_id'])
def registrar_log_auditoria():
    """Registra log de auditoria LGPD"""
    try:
        from ..services.compliance_lgpd import compliance_lgpd, TipoOperacao
        
        data = request.validated_data
        operacao = TipoOperacao(data['operacao'])
        
        # Obter informações da requisição
        request_info = {
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'metadata': data.get('metadata', {})
        }
        
        log_id = compliance_lgpd.registrar_log_auditoria(
            operacao=operacao,
            recurso=data['recurso'],
            dados_alterados=data['dados_alterados'],
            usuario_id=data['usuario_id'],
            request_info=request_info
        )
        
        return APIResponse.success(data={'log_id': log_id})
        
    except Exception as e:
        return APIResponse.error(f"Erro ao registrar log: {str(e)}")

@api_bp.route('/lgpd/consentimento', methods=['POST'])
@validate_json_input(required_fields=['titular_id', 'titular_nome', 'finalidade', 'dados_coletados', 'canal_coleta', 'evidencia'])
def criar_consentimento():
    """Cria novo consentimento LGPD"""
    try:
        from ..services.compliance_lgpd import compliance_lgpd
        
        data = request.validated_data
        
        request_info = {
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        }
        
        resultado = compliance_lgpd.criar_consentimento(
            titular_id=data['titular_id'],
            titular_nome=data['titular_nome'],
            finalidade=data['finalidade'],
            dados_coletados=data['dados_coletados'],
            canal_coleta=data['canal_coleta'],
            evidencia=data['evidencia'],
            request_info=request_info
        )
        
        if resultado.get('sucesso'):
            return APIResponse.success(data=resultado)
        else:
            return APIResponse.error(resultado.get('erro', 'Erro na criação'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao criar consentimento: {str(e)}")

@api_bp.route('/lgpd/consentimento/<consentimento_id>/revogar', methods=['POST'])
@validate_json_input(required_fields=['titular_id', 'motivo'])
def revogar_consentimento(consentimento_id):
    """Revoga consentimento LGPD"""
    try:
        from ..services.compliance_lgpd import compliance_lgpd
        
        data = request.validated_data
        
        request_info = {
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        }
        
        resultado = compliance_lgpd.revogar_consentimento(
            consentimento_id=consentimento_id,
            titular_id=data['titular_id'],
            motivo=data['motivo'],
            request_info=request_info
        )
        
        if resultado.get('sucesso'):
            return APIResponse.success(data=resultado)
        else:
            return APIResponse.error(resultado.get('erro', 'Erro na revogação'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao revogar consentimento: {str(e)}")

@api_bp.route('/lgpd/solicitacao-titular', methods=['POST'])
@validate_json_input(required_fields=['tipo_solicitacao', 'titular_id', 'dados_solicitacao'])
def processar_solicitacao_titular():
    """Processa solicitação de direitos do titular"""
    try:
        from ..services.compliance_lgpd import compliance_lgpd
        
        data = request.validated_data
        
        request_info = {
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        }
        
        resultado = compliance_lgpd.processar_solicitacao_titular(
            tipo_solicitacao=data['tipo_solicitacao'],
            titular_id=data['titular_id'],
            dados_solicitacao=data['dados_solicitacao'],
            request_info=request_info
        )
        
        if resultado.get('sucesso'):
            return APIResponse.success(data=resultado)
        else:
            return APIResponse.error(resultado.get('erro', 'Erro no processamento'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao processar solicitação: {str(e)}")

@api_bp.route('/lgpd/incidente-seguranca', methods=['POST'])
@validate_json_input(required_fields=['tipo_incidente', 'descricao', 'dados_afetados', 'nivel_risco', 'responsavel'])
def reportar_incidente_seguranca():
    """Reporta incidente de segurança"""
    try:
        from ..services.compliance_lgpd import compliance_lgpd, NivelRisco
        
        data = request.validated_data
        nivel_risco = NivelRisco(data['nivel_risco'])
        
        resultado = compliance_lgpd.reportar_incidente_seguranca(
            tipo_incidente=data['tipo_incidente'],
            descricao=data['descricao'],
            dados_afetados=data['dados_afetados'],
            nivel_risco=nivel_risco,
            responsavel=data['responsavel']
        )
        
        if resultado.get('sucesso'):
            return APIResponse.success(data=resultado)
        else:
            return APIResponse.error(resultado.get('erro', 'Erro no reporte'))
        
    except Exception as e:
        return APIResponse.error(f"Erro ao reportar incidente: {str(e)}")

@api_bp.route('/lgpd/relatorio-compliance', methods=['GET'])
def gerar_relatorio_compliance():
    """Gera relatório de compliance LGPD"""
    try:
        from ..services.compliance_lgpd import compliance_lgpd
        
        periodo = request.args.get('periodo', 'mes')
        
        resultado = compliance_lgpd.gerar_relatorio_compliance(periodo)
        
        if resultado.get('erro'):
            return APIResponse.error(resultado['erro'])
        else:
            return APIResponse.success(data=resultado)
        
    except Exception as e:
        return APIResponse.error(f"Erro ao gerar relatório: {str(e)}")

@api_bp.route('/lgpd/verificacao-tempo-real', methods=['GET'])
def verificar_compliance_tempo_real():
    """Verificação de compliance em tempo real"""
    try:
        from ..services.compliance_lgpd import compliance_lgpd
        
        resultado = compliance_lgpd.verificar_compliance_tempo_real()
        
        if resultado.get('erro'):
            return APIResponse.error(resultado['erro'])
        else:
            return APIResponse.success(data=resultado)
        
    except Exception as e:
        return APIResponse.error(f"Erro na verificação: {str(e)}")

# === ROTAS DE EXPORTAÇÃO ===

@api_bp.route('/relatorios/exportar-pdf', methods=['POST'])
@validate_json_input(required_fields=['template', 'dados'])
def exportar_relatorio_pdf():
    """Exporta relatório em formato PDF"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from io import BytesIO
        from flask import send_file
        
        data = request.validated_data
        template = data['template']
        dados = data['dados']
        filtros = data.get('filtros', {})
        
        # Criar buffer em memória
        buffer = BytesIO()
        
        # Criar documento PDF
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Estilos customizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.HexColor('#2D3142')
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#5F5CFF')
        )
        
        # Título do relatório
        titulo = f"Relatório PNSB 2024 - {template.title()}"
        story.append(Paragraph(titulo, title_style))
        story.append(Spacer(1, 12))
        
        # Informações do filtro
        filtro_info = []
        if filtros.get('periodo'):
            filtro_info.append(f"Período: {filtros['periodo']}")
        if filtros.get('municipio'):
            filtro_info.append(f"Município: {filtros['municipio']}")
        if filtros.get('dataInicio') and filtros.get('dataFim'):
            filtro_info.append(f"Data: {filtros['dataInicio']} a {filtros['dataFim']}")
        
        if filtro_info:
            story.append(Paragraph(f"Filtros aplicados: {' | '.join(filtro_info)}", styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Resumo executivo
        story.append(Paragraph("Resumo Executivo", subtitle_style))
        resumo_data = [
            ['Métrica', 'Valor'],
            ['Total de Visitas', str(dados.get('total', 0))],
            ['Visitas Realizadas', str(dados.get('realizadas', 0))],
            ['Visitas Pendentes', str(dados.get('pendentes', 0))],
            ['Taxa de Sucesso', f"{round((dados.get('realizadas', 0) / dados.get('total', 1)) * 100, 1)}%"]
        ]
        
        resumo_table = Table(resumo_data)
        resumo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5F5CFF')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(resumo_table)
        story.append(Spacer(1, 20))
        
        # Detalhamento por template
        if template == 'detalhado' and dados.get('visitas'):
            story.append(Paragraph("Detalhamento de Visitas", subtitle_style))
            
            visitas_data = [['Município', 'Data', 'Status', 'Informante']]
            for visita in dados['visitas'][:50]:  # Limitar a 50 para não sobrecarregar
                visitas_data.append([
                    visita.get('municipio', '-'),
                    visita.get('data', '-'),
                    visita.get('status', '-'),
                    visita.get('informante', '-')[:30] + '...' if len(visita.get('informante', '')) > 30 else visita.get('informante', '-')
                ])
            
            visitas_table = Table(visitas_data)
            visitas_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6EE7B7')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(visitas_table)
        
        # Rodapé
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        story.append(Paragraph("Sistema PNSB 2024 - IBGE", styles['Normal']))
        
        # Construir PDF
        doc.build(story)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'relatorio_pnsb_{template}_{datetime.now().strftime("%Y%m%d")}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao gerar PDF: {str(e)}")

@api_bp.route('/relatorios/exportar-excel', methods=['POST'])
@validate_json_input(required_fields=['template', 'dados'])
def exportar_relatorio_excel():
    """Exporta relatório em formato Excel"""
    try:
        import pandas as pd
        from io import BytesIO
        from flask import send_file
        
        data = request.validated_data
        template = data['template']
        dados = data['dados']
        filtros = data.get('filtros', {})
        
        # Criar buffer em memória
        buffer = BytesIO()
        
        # Criar writer do Excel
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Aba de resumo
            resumo_df = pd.DataFrame({
                'Métrica': ['Total de Visitas', 'Visitas Realizadas', 'Visitas Pendentes', 'Taxa de Sucesso (%)'],
                'Valor': [
                    dados.get('total', 0),
                    dados.get('realizadas', 0),
                    dados.get('pendentes', 0),
                    round((dados.get('realizadas', 0) / dados.get('total', 1)) * 100, 1) if dados.get('total', 0) > 0 else 0
                ]
            })
            resumo_df.to_excel(writer, sheet_name='Resumo', index=False)
            
            # Aba de distribuição por município
            if dados.get('municipios') and dados.get('porMunicipio'):
                municipio_df = pd.DataFrame({
                    'Município': dados['municipios'],
                    'Quantidade de Visitas': dados['porMunicipio']
                })
                municipio_df.to_excel(writer, sheet_name='Por Município', index=False)
            
            # Aba detalhada (se template for detalhado)
            if template == 'detalhado' and dados.get('visitas'):
                visitas_df = pd.DataFrame(dados['visitas'])
                # Reordenar colunas para melhor apresentação
                colunas_ordem = ['municipio', 'data', 'hora_inicio', 'status', 'informante', 'tipo_pesquisa', 'observacoes']
                colunas_existentes = [col for col in colunas_ordem if col in visitas_df.columns]
                if colunas_existentes:
                    visitas_df = visitas_df[colunas_existentes]
                
                visitas_df.to_excel(writer, sheet_name='Visitas Detalhadas', index=False)
            
            # Aba de metadados
            metadata_df = pd.DataFrame({
                'Propriedade': ['Template', 'Data de Geração', 'Período', 'Município', 'Sistema'],
                'Valor': [
                    template,
                    datetime.now().strftime('%d/%m/%Y %H:%M'),
                    filtros.get('periodo', 'Não especificado'),
                    filtros.get('municipio', 'Todos'),
                    'Sistema PNSB 2024 - IBGE'
                ]
            })
            metadata_df.to_excel(writer, sheet_name='Metadados', index=False)
        
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'relatorio_pnsb_{template}_{datetime.now().strftime("%Y%m%d")}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao gerar Excel: {str(e)}")

@api_bp.route('/relatorios/compartilhar', methods=['POST'])
@validate_json_input(required_fields=['template', 'dados'])
def compartilhar_relatorio():
    """Gera link para compartilhamento de relatório"""
    try:
        import uuid
        import json
        import os
        
        data = request.validated_data
        template = data['template']
        dados = data['dados']
        filtros = data.get('filtros', {})
        
        # Gerar ID único para o relatório
        relatorio_id = str(uuid.uuid4())
        
        # Criar estrutura de dados para salvar
        relatorio_dados = {
            'id': relatorio_id,
            'template': template,
            'dados': dados,
            'filtros': filtros,
            'criado_em': datetime.now().isoformat(),
            'expires_em': (datetime.now() + timedelta(days=7)).isoformat()  # Expira em 7 dias
        }
        
        # Diretório para armazenar relatórios compartilhados
        relatorios_dir = os.path.join(os.path.dirname(__file__), '..', 'shared_reports')
        os.makedirs(relatorios_dir, exist_ok=True)
        
        # Salvar dados do relatório
        arquivo_relatorio = os.path.join(relatorios_dir, f'{relatorio_id}.json')
        with open(arquivo_relatorio, 'w', encoding='utf-8') as f:
            json.dump(relatorio_dados, f, ensure_ascii=False, indent=2)
        
        # Gerar link de compartilhamento
        from flask import request as flask_request
        base_url = flask_request.host_url.rstrip('/')
        link_compartilhamento = f"{base_url}/relatorio-compartilhado/{relatorio_id}"
        
        return APIResponse.success(
            data={
                'link': link_compartilhamento,
                'expires_em': relatorio_dados['expires_em'],
                'relatorio_id': relatorio_id
            },
            message="Link de compartilhamento gerado com sucesso"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao gerar link de compartilhamento: {str(e)}")

# === TESTE DE MÉTRICAS ===

@api_bp.route('/test/metricas/<municipio>', methods=['GET'])
def test_metricas_municipio(municipio):
    """Endpoint de teste para verificar métricas de um município"""
    try:
        from gestao_visitas.models.questionarios_obrigatorios import ProgressoQuestionarios
        
        # Obter progresso atual
        progresso = ProgressoQuestionarios.query.filter_by(municipio=municipio).first()
        
        # Obter visitas do município
        visitas = Visita.query.filter_by(municipio=municipio).all()
        
        # Estatísticas básicas
        stats = {
            'municipio': municipio,
            'total_visitas': len(visitas),
            'status_counts': {},
            'progresso_questionarios': None,
            'timestamp': datetime.now().isoformat()
        }
        
        # Contar por status
        for visita in visitas:
            status = visita.status
            stats['status_counts'][status] = stats['status_counts'].get(status, 0) + 1
        
        # Adicionar dados de progresso se existir
        if progresso:
            stats['progresso_questionarios'] = {
                'total_mrs_obrigatorios': progresso.total_mrs_obrigatorios,
                'total_map_obrigatorios': progresso.total_map_obrigatorios,
                'mrs_concluidos': progresso.mrs_concluidos,
                'map_concluidos': progresso.map_concluidos,
                'percentual_mrs': progresso.percentual_mrs,
                'percentual_map': progresso.percentual_map,
                'percentual_geral': progresso.percentual_geral,
                'atualizado_em': progresso.atualizado_em.isoformat() if progresso.atualizado_em else None
            }
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc().split('\n')[-3:-1]
        }), 500