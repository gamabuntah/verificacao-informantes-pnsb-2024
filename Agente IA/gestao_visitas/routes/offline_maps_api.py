"""
APIs para sistema de mapas offline
Cache de tiles, rotas pré-calculadas e funcionalidades offline
"""

from flask import Blueprint, request, jsonify, current_app, send_file
from datetime import datetime
import io
import base64

from gestao_visitas.services.offline_maps_service import OfflineMapsService, cache_santa_catarina_maps, precalculate_all_routes

offline_maps_bp = Blueprint('offline_maps', __name__)


@offline_maps_bp.route('/offline/status', methods=['GET'])
def get_offline_status():
    """Retorna status do sistema offline"""
    try:
        service = OfflineMapsService()
        stats = service.get_cache_statistics()
        
        return jsonify({
            'success': True,
            'data': {
                'cache_statistics': stats,
                'offline_ready': stats.get('valid_tiles', 0) > 0 and stats.get('valid_routes', 0) > 0,
                'last_check': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter status offline: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@offline_maps_bp.route('/offline/cache-maps', methods=['POST'])
def cache_maps_for_region():
    """Faz cache de mapas para uma região específica"""
    try:
        data = request.get_json() or {}
        
        # Parâmetros da região
        center_lat = data.get('center_lat')
        center_lng = data.get('center_lng') 
        radius_km = data.get('radius_km', 10)
        zoom_levels = data.get('zoom_levels', [12, 14, 16])
        
        if not center_lat or not center_lng:
            return jsonify({
                'success': False, 
                'error': 'center_lat e center_lng são obrigatórios'
            }), 400
        
        service = OfflineMapsService()
        result = service.cache_map_tiles_for_region(
            center_lat, center_lng, radius_km, zoom_levels
        )
        
        return jsonify({
            'success': True,
            'message': f'Cache de mapas concluído para região ({center_lat}, {center_lng})',
            'data': result
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro no cache de mapas: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@offline_maps_bp.route('/offline/cache-santa-catarina', methods=['POST'])
def cache_santa_catarina():
    """Faz cache completo de mapas para região PNSB de Santa Catarina"""
    try:
        current_app.logger.info("🗺️ Iniciando cache completo de Santa Catarina...")
        
        result = cache_santa_catarina_maps()
        
        return jsonify({
            'success': True,
            'message': 'Cache de Santa Catarina concluído com sucesso',
            'data': result
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro no cache de SC: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@offline_maps_bp.route('/offline/precalculate-routes', methods=['POST'])
def precalculate_routes():
    """Pré-calcula rotas entre entidades"""
    try:
        data = request.get_json() or {}
        municipio = data.get('municipio')  # None = todos os municípios
        
        service = OfflineMapsService()
        result = service.precalculate_entity_routes(municipio)
        
        return jsonify({
            'success': True,
            'message': f'Rotas pré-calculadas para {municipio or "todos os municípios"}',
            'data': result
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro no pré-cálculo de rotas: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@offline_maps_bp.route('/offline/precalculate-all-routes', methods=['POST'])
def precalculate_all_routes_endpoint():
    """Pré-calcula todas as rotas entre todas as entidades"""
    try:
        current_app.logger.info("🗺️ Iniciando pré-cálculo de todas as rotas...")
        
        result = precalculate_all_routes()
        
        return jsonify({
            'success': True,
            'message': 'Todas as rotas pré-calculadas com sucesso',
            'data': result
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro no pré-cálculo geral: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@offline_maps_bp.route('/offline/route', methods=['GET'])
def get_offline_route():
    """Recupera rota do cache offline"""
    try:
        # Parâmetros da rota
        origin_lat = float(request.args.get('origin_lat'))
        origin_lng = float(request.args.get('origin_lng'))
        dest_lat = float(request.args.get('dest_lat'))
        dest_lng = float(request.args.get('dest_lng'))
        
        service = OfflineMapsService()
        route_data = service.get_cached_route(
            (origin_lat, origin_lng),
            (dest_lat, dest_lng)
        )
        
        if route_data:
            return jsonify({
                'success': True,
                'data': route_data,
                'source': 'offline_cache'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Rota não encontrada no cache offline',
                'suggestion': 'Execute pré-cálculo de rotas ou verifique conexão online'
            }), 404
        
    except ValueError:
        return jsonify({
            'success': False, 
            'error': 'Coordenadas inválidas'
        }), 400
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar rota offline: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@offline_maps_bp.route('/offline/cleanup', methods=['POST'])
def cleanup_cache():
    """Remove itens expirados do cache"""
    try:
        service = OfflineMapsService()
        result = service.cleanup_expired_cache()
        
        return jsonify({
            'success': True,
            'message': 'Cache limpo com sucesso',
            'data': result
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro na limpeza do cache: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@offline_maps_bp.route('/offline/entities-for-municipality/<municipio>', methods=['GET'])
def get_entities_for_offline(municipio):
    """Retorna entidades de um município com dados para modo offline"""
    try:
        from gestao_visitas.models.questionarios_obrigatorios import EntidadeIdentificada, EntidadePrioritariaUF
        
        # Buscar entidades geocodificadas do município
        identificadas = EntidadeIdentificada.query.filter_by(
            municipio=municipio,
            geocodificacao_status='sucesso'
        ).all()
        
        prioritarias = EntidadePrioritariaUF.query.filter_by(
            municipio=municipio,
            geocodificacao_status='sucesso'
        ).all()
        
        # Preparar dados offline
        entities_data = []
        
        for ent in identificadas:
            entities_data.append({
                'id': f'identificada_{ent.id}',
                'type': 'identificada',
                'name': ent.nome_entidade,
                'municipality': ent.municipio,
                'coordinates': {
                    'lat': ent.latitude,
                    'lng': ent.longitude
                },
                'address': ent.endereco_formatado,
                'place_id': ent.place_id,
                'plus_code': ent.plus_code,
                'priority': ent.prioridade,
                'mrs_required': ent.mrs_obrigatorio,
                'map_required': ent.map_obrigatorio,
                'contact': {
                    'phone': ent.telefone,
                    'email': ent.email,
                    'responsible': ent.responsavel
                }
            })
        
        for ent in prioritarias:
            entities_data.append({
                'id': f'prioritaria_{ent.id}',
                'type': 'prioritaria',
                'name': ent.nome_entidade,
                'municipality': ent.municipio,
                'coordinates': {
                    'lat': ent.latitude,
                    'lng': ent.longitude
                },
                'address': ent.endereco_formatado,
                'place_id': ent.place_id,
                'plus_code': ent.plus_code,
                'priority': 1,  # P1
                'mrs_required': ent.mrs_obrigatorio,
                'map_required': ent.map_obrigatorio,
                'uf_code': ent.codigo_uf
            })
        
        return jsonify({
            'success': True,
            'data': {
                'municipality': municipio,
                'entities': entities_data,
                'total_entities': len(entities_data),
                'total_identified': len(identificadas),
                'total_priority': len(prioritarias),
                'offline_ready': True,
                'generated_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar entidades offline: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@offline_maps_bp.route('/offline/sync-status', methods=['GET'])
def get_sync_status():
    """Retorna status de sincronização de dados offline"""
    try:
        service = OfflineMapsService()
        
        # Verificar dados que precisam ser sincronizados
        import sqlite3
        with sqlite3.connect(service.routes_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT COUNT(*) as pending_uploads 
                FROM offline_entities 
                WHERE needs_upload = 1
            ''')
            pending_uploads = cursor.fetchone()['pending_uploads']
        
        # Status geral de conectividade
        import requests
        try:
            response = requests.get('https://www.google.com', timeout=5)
            online = response.status_code == 200
        except:
            online = False
        
        return jsonify({
            'success': True,
            'data': {
                'online': online,
                'pending_uploads': pending_uploads,
                'last_sync': datetime.now().isoformat(),
                'sync_needed': pending_uploads > 0
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao verificar status de sync: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@offline_maps_bp.route('/offline/download-package/<municipio>', methods=['GET'])
def download_offline_package(municipio):
    """Gera e retorna pacote offline para um município"""
    try:
        import zipfile
        import tempfile
        import json
        
        service = OfflineMapsService()
        
        # Buscar dados do município
        from gestao_visitas.models.questionarios_obrigatorios import EntidadeIdentificada, EntidadePrioritariaUF
        
        identificadas = EntidadeIdentificada.query.filter_by(
            municipio=municipio,
            geocodificacao_status='sucesso'
        ).all()
        
        prioritarias = EntidadePrioritariaUF.query.filter_by(
            municipio=municipio,
            geocodificacao_status='sucesso'
        ).all()
        
        # Criar pacote offline
        with tempfile.NamedTemporaryFile(mode='w+b', suffix='.zip', delete=False) as tmp_file:
            with zipfile.ZipFile(tmp_file, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Adicionar dados das entidades
                entities_data = {
                    'municipality': municipio,
                    'entities': [ent.to_dict() for ent in identificadas + prioritarias],
                    'generated_at': datetime.now().isoformat(),
                    'version': '1.0'
                }
                
                zip_file.writestr(
                    f'{municipio}_entities.json',
                    json.dumps(entities_data, ensure_ascii=False, indent=2)
                )
                
                # Adicionar rotas pré-calculadas
                routes_data = []
                with sqlite3.connect(service.routes_db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute('''
                        SELECT * FROM cached_routes 
                        WHERE route_data LIKE ? AND expires_at > datetime('now')
                    ''', (f'%{municipio}%',))
                    
                    for row in cursor.fetchall():
                        routes_data.append(dict(row))
                
                zip_file.writestr(
                    f'{municipio}_routes.json',
                    json.dumps(routes_data, ensure_ascii=False, indent=2)
                )
        
        return send_file(
            tmp_file.name,
            as_attachment=True,
            download_name=f'pnsb_offline_{municipio}.zip',
            mimetype='application/zip'
        )
        
    except Exception as e:
        current_app.logger.error(f"Erro ao gerar pacote offline: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@offline_maps_bp.route('/offline/prepare-full-system', methods=['POST'])
def prepare_full_offline_system():
    """Prepara sistema completo para modo offline"""
    try:
        current_app.logger.info("🚀 Preparando sistema completo offline...")
        
        service = OfflineMapsService()
        results = {}
        
        # 1. Cache de mapas de Santa Catarina
        current_app.logger.info("📍 Fazendo cache de mapas...")
        results['maps_cache'] = cache_santa_catarina_maps()
        
        # 2. Pré-cálculo de todas as rotas
        current_app.logger.info("🗺️ Pré-calculando rotas...")
        results['routes_precalc'] = precalculate_all_routes()
        
        # 3. Estatísticas finais
        results['final_stats'] = service.get_cache_statistics()
        
        # 4. Verificar se sistema está pronto
        stats = results['final_stats']
        offline_ready = (
            stats.get('valid_tiles', 0) > 100 and  # Pelo menos 100 tiles
            stats.get('valid_routes', 0) > 10      # Pelo menos 10 rotas
        )
        
        return jsonify({
            'success': True,
            'message': 'Sistema offline preparado com sucesso',
            'data': {
                'offline_ready': offline_ready,
                'preparation_results': results,
                'prepared_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro na preparação offline: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500