"""
APIs para geocodificação de entidades usando Google Maps API
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from gestao_visitas.db import db
from gestao_visitas.services.geocodificacao_service import GeocodificacaoService, processar_geocodificacao_pendentes
from gestao_visitas.models.questionarios_obrigatorios import EntidadeIdentificada, EntidadePrioritariaUF

geocodificacao_bp = Blueprint('geocodificacao', __name__)


@geocodificacao_bp.route('/geocodificacao/status', methods=['GET'])
def obter_status_geocodificacao():
    """Retorna estatísticas sobre o status da geocodificação"""
    try:
        service = GeocodificacaoService()
        estatisticas = service.obter_estatisticas_geocodificacao()
        
        return jsonify({
            'success': True,
            'data': estatisticas
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter status de geocodificação: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@geocodificacao_bp.route('/geocodificacao/processar-todas', methods=['POST'])
def processar_todas_entidades():
    """Geocodifica todas as entidades pendentes"""
    try:
        data = request.get_json() or {}
        limite = data.get('limite', 100)  # Limite padrão para evitar sobrecarga
        forcar_atualizacao = data.get('forcar_atualizacao', False)
        
        service = GeocodificacaoService()
        
        # Se forçar atualização, resetar status de todas as entidades
        if forcar_atualizacao:
            current_app.logger.info("🔄 Resetando status de geocodificação para reprocessar todas as entidades")
            
            # Reset EntidadeIdentificada
            EntidadeIdentificada.query.update({
                'geocodificacao_status': 'pendente',
                'geocodificado_em': None
            })
            
            # Reset EntidadePrioritariaUF
            EntidadePrioritariaUF.query.update({
                'geocodificacao_status': 'pendente',
                'geocodificado_em': None
            })
            
            db.session.commit()
        
        # Processar geocodificação
        estatisticas = service.geocodificar_todas_entidades(limite=limite)
        
        return jsonify({
            'success': True,
            'message': 'Geocodificação concluída com sucesso',
            'data': estatisticas
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao processar geocodificação: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@geocodificacao_bp.route('/geocodificacao/processar-pendentes', methods=['POST'])
def processar_pendentes():
    """Processa apenas entidades com status pendente"""
    try:
        data = request.get_json() or {}
        limite = data.get('limite', 50)
        
        estatisticas = processar_geocodificacao_pendentes(limite=limite)
        
        return jsonify({
            'success': True,
            'message': f'Processadas até {limite} entidades pendentes',
            'data': estatisticas
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao processar entidades pendentes: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@geocodificacao_bp.route('/geocodificacao/entidade/<int:entidade_id>', methods=['POST'])
def geocodificar_entidade_especifica():
    """Geocodifica uma entidade específica"""
    try:
        entidade_id = request.view_args['entidade_id']
        data = request.get_json() or {}
        tipo_entidade = data.get('tipo', 'identificada')  # 'identificada' ou 'prioritaria'
        forcar = data.get('forcar', False)
        
        service = GeocodificacaoService()
        
        if tipo_entidade == 'prioritaria':
            entidade = EntidadePrioritariaUF.query.get_or_404(entidade_id)
            sucesso = service.geocodificar_entidade_prioritaria_uf(entidade, forcar_atualizacao=forcar)
        else:
            entidade = EntidadeIdentificada.query.get_or_404(entidade_id)
            sucesso = service.geocodificar_entidade_identificada(entidade, forcar_atualizacao=forcar)
        
        if sucesso:
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'Entidade {entidade.nome_entidade} geocodificada com sucesso',
                'data': entidade.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Falha ao geocodificar entidade {entidade.nome_entidade}',
                'data': entidade.to_dict()
            })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao geocodificar entidade específica: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@geocodificacao_bp.route('/geocodificacao/teste-endereco', methods=['POST'])
def testar_geocodificacao():
    """Testa geocodificação de um endereço sem salvar no banco"""
    try:
        data = request.get_json()
        
        if not data or not data.get('endereco'):
            return jsonify({'success': False, 'error': 'Endereço é obrigatório'}), 400
        
        endereco = data['endereco']
        municipio = data.get('municipio')
        
        service = GeocodificacaoService()
        resultado = service.geocodificar_endereco(endereco, municipio)
        
        return jsonify({
            'success': resultado['status'] == 'sucesso',
            'data': resultado
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro no teste de geocodificação: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@geocodificacao_bp.route('/geocodificacao/backup-enderecos', methods=['POST'])
def criar_backup_enderecos():
    """Cria backup dos endereços originais antes de modificações"""
    try:
        # Backup EntidadeIdentificada
        entidades_sem_backup = EntidadeIdentificada.query.filter(
            EntidadeIdentificada.endereco_original.is_(None),
            EntidadeIdentificada.endereco.isnot(None)
        ).all()
        
        backup_count = 0
        for entidade in entidades_sem_backup:
            entidade.endereco_original = entidade.endereco
            backup_count += 1
        
        # Backup EntidadePrioritariaUF
        entidades_prioritarias_sem_backup = EntidadePrioritariaUF.query.filter(
            EntidadePrioritariaUF.endereco_original.is_(None),
            EntidadePrioritariaUF.endereco_completo.isnot(None)
        ).all()
        
        for entidade in entidades_prioritarias_sem_backup:
            entidade.endereco_original = entidade.endereco_completo
            backup_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Backup criado para {backup_count} endereços',
            'data': {
                'entidades_identificadas': len(entidades_sem_backup),
                'entidades_prioritarias': len(entidades_prioritarias_sem_backup),
                'total_backup': backup_count
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao criar backup de endereços: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@geocodificacao_bp.route('/geocodificacao/restaurar-enderecos', methods=['POST'])
def restaurar_enderecos_originais():
    """Restaura endereços originais (desfaz geocodificação)"""
    try:
        data = request.get_json() or {}
        confirmar = data.get('confirmar', False)
        
        if not confirmar:
            return jsonify({
                'success': False,
                'error': 'Confirmação necessária - adicione "confirmar": true'
            }), 400
        
        # Restaurar EntidadeIdentificada
        entidades_restaurar = EntidadeIdentificada.query.filter(
            EntidadeIdentificada.endereco_original.isnot(None)
        ).all()
        
        restaurado_count = 0
        for entidade in entidades_restaurar:
            entidade.endereco = entidade.endereco_original
            entidade.endereco_formatado = None
            entidade.latitude = None
            entidade.longitude = None
            entidade.place_id = None
            entidade.plus_code = None
            entidade.geocodificacao_status = 'pendente'
            entidade.geocodificacao_confianca = None
            entidade.geocodificado_em = None
            restaurado_count += 1
        
        # Restaurar EntidadePrioritariaUF
        entidades_prioritarias_restaurar = EntidadePrioritariaUF.query.filter(
            EntidadePrioritariaUF.endereco_original.isnot(None)
        ).all()
        
        for entidade in entidades_prioritarias_restaurar:
            entidade.endereco_completo = entidade.endereco_original
            entidade.endereco_formatado = None
            entidade.latitude = None
            entidade.longitude = None
            entidade.place_id = None
            entidade.plus_code = None
            entidade.geocodificacao_status = 'pendente'
            entidade.geocodificacao_confianca = None
            entidade.geocodificado_em = None
            restaurado_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Endereços originais restaurados para {restaurado_count} entidades',
            'data': {
                'entidades_identificadas': len(entidades_restaurar),
                'entidades_prioritarias': len(entidades_prioritarias_restaurar),
                'total_restaurado': restaurado_count
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao restaurar endereços originais: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@geocodificacao_bp.route('/geocodificacao/relatorio', methods=['GET'])
def relatorio_geocodificacao():
    """Gera relatório detalhado sobre geocodificação"""
    try:
        # Estatísticas por município
        municipios_stats = {}
        
        from gestao_visitas.config import MUNICIPIOS
        for municipio in MUNICIPIOS:
            # EntidadeIdentificada
            total_identificadas = EntidadeIdentificada.query.filter_by(municipio=municipio).count()
            geocodificadas_identificadas = EntidadeIdentificada.query.filter_by(
                municipio=municipio, 
                geocodificacao_status='sucesso'
            ).count()
            
            # EntidadePrioritariaUF
            total_prioritarias = EntidadePrioritariaUF.query.filter_by(municipio=municipio).count()
            geocodificadas_prioritarias = EntidadePrioritariaUF.query.filter_by(
                municipio=municipio, 
                geocodificacao_status='sucesso'
            ).count()
            
            municipios_stats[municipio] = {
                'entidades_identificadas': {
                    'total': total_identificadas,
                    'geocodificadas': geocodificadas_identificadas,
                    'percentual': round((geocodificadas_identificadas / total_identificadas * 100), 2) if total_identificadas > 0 else 0
                },
                'entidades_prioritarias': {
                    'total': total_prioritarias,
                    'geocodificadas': geocodificadas_prioritarias,
                    'percentual': round((geocodificadas_prioritarias / total_prioritarias * 100), 2) if total_prioritarias > 0 else 0
                },
                'total_geral': {
                    'total': total_identificadas + total_prioritarias,
                    'geocodificadas': geocodificadas_identificadas + geocodificadas_prioritarias
                }
            }
        
        # Estatísticas por nível de confiança
        confianca_stats = {}
        niveis_confianca = ['ROOFTOP', 'RANGE_INTERPOLATED', 'GEOMETRIC_CENTER', 'APPROXIMATE']
        
        for nivel in niveis_confianca:
            count_identificadas = EntidadeIdentificada.query.filter_by(geocodificacao_confianca=nivel).count()
            count_prioritarias = EntidadePrioritariaUF.query.filter_by(geocodificacao_confianca=nivel).count()
            
            confianca_stats[nivel] = {
                'entidades_identificadas': count_identificadas,
                'entidades_prioritarias': count_prioritarias,
                'total': count_identificadas + count_prioritarias
            }
        
        return jsonify({
            'success': True,
            'data': {
                'por_municipio': municipios_stats,
                'por_confianca': confianca_stats,
                'gerado_em': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao gerar relatório de geocodificação: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500