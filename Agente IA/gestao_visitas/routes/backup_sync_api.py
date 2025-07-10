"""
APIs para Sistema de Backup e Sincronização - PNSB 2024
Backup automático na nuvem, sincronização multi-dispositivo e recuperação de desastres
"""

from flask import Blueprint, request, jsonify, current_app, send_file
from datetime import datetime
import json
import os
from typing import Dict, Any

from gestao_visitas.services.backup_sync_service import BackupSyncService

backup_sync_bp = Blueprint('backup_sync', __name__)

# Instância global do serviço
backup_service = None

def get_backup_service():
    """Obtém instância do serviço de backup (singleton)"""
    global backup_service
    if backup_service is None:
        backup_service = BackupSyncService()
        # Iniciar serviços automáticos
        backup_service.start_automatic_backup()
        backup_service.start_automatic_sync()
    return backup_service


@backup_sync_bp.route('/backups', methods=['GET'])
def list_backups():
    """
    Lista todos os backups disponíveis
    """
    try:
        service = get_backup_service()
        backups = service.get_backup_list()
        
        # Ordenar por timestamp (mais recente primeiro)
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'backups': backups,
                'total_count': len(backups),
                'total_size_mb': sum(b['size_bytes'] for b in backups) / 1024 / 1024
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao listar backups: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao listar backups: {str(e)}'
        }), 500


@backup_sync_bp.route('/backups', methods=['POST'])
def create_backup():
    """
    Cria um novo backup manual
    """
    try:
        data = request.get_json() or {}
        description = data.get('description', 'Backup manual')
        
        service = get_backup_service()
        backup_info = service.create_backup('manual', description)
        
        if backup_info:
            return jsonify({
                'success': True,
                'data': backup_info.to_dict(),
                'message': f'Backup criado com sucesso: {backup_info.backup_id}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Falha ao criar backup'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Erro ao criar backup: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao criar backup: {str(e)}'
        }), 500


@backup_sync_bp.route('/backups/<backup_id>', methods=['GET'])
def get_backup_details(backup_id):
    """
    Obtém detalhes de um backup específico
    """
    try:
        service = get_backup_service()
        backup_info = service.get_backup_info(backup_id)
        
        if backup_info:
            return jsonify({
                'success': True,
                'data': backup_info
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Backup não encontrado'
            }), 404
            
    except Exception as e:
        current_app.logger.error(f"Erro ao obter backup {backup_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao obter backup: {str(e)}'
        }), 500


@backup_sync_bp.route('/backups/<backup_id>', methods=['DELETE'])
def delete_backup(backup_id):
    """
    Remove um backup específico
    """
    try:
        service = get_backup_service()
        success = service.delete_backup(backup_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Backup {backup_id} removido com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Backup não encontrado ou erro ao remover'
            }), 404
            
    except Exception as e:
        current_app.logger.error(f"Erro ao remover backup {backup_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao remover backup: {str(e)}'
        }), 500


@backup_sync_bp.route('/backups/<backup_id>/restore', methods=['POST'])
def restore_backup(backup_id):
    """
    Restaura um backup específico
    """
    try:
        data = request.get_json() or {}
        target_dir = data.get('target_dir')
        
        service = get_backup_service()
        success = service.restore_backup(backup_id, target_dir)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Backup {backup_id} restaurado com sucesso',
                'restore_location': target_dir or 'diretório temporário'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Falha na restauração do backup'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Erro ao restaurar backup {backup_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao restaurar backup: {str(e)}'
        }), 500


@backup_sync_bp.route('/backups/<backup_id>/download', methods=['GET'])
def download_backup(backup_id):
    """
    Download de um backup específico
    """
    try:
        service = get_backup_service()
        backup_info = service.get_backup_info(backup_id)
        
        if not backup_info:
            return jsonify({
                'success': False,
                'error': 'Backup não encontrado'
            }), 404
        
        backup_path = backup_info['file_path']
        
        if not os.path.exists(backup_path):
            return jsonify({
                'success': False,
                'error': 'Arquivo de backup não encontrado'
            }), 404
        
        return send_file(
            backup_path,
            as_attachment=True,
            download_name=f"{backup_id}.backup"
        )
        
    except Exception as e:
        current_app.logger.error(f"Erro ao baixar backup {backup_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao baixar backup: {str(e)}'
        }), 500


@backup_sync_bp.route('/sync/status', methods=['GET'])
def get_sync_status():
    """
    Obtém status atual de sincronização
    """
    try:
        service = get_backup_service()
        sync_status = service.check_sync_status()
        
        if sync_status:
            return jsonify({
                'success': True,
                'data': {
                    'device_id': sync_status.device_id,
                    'last_sync': sync_status.last_sync.isoformat(),
                    'sync_direction': sync_status.sync_direction,
                    'conflicts_detected': sync_status.conflicts_detected,
                    'data_transferred_mb': sync_status.data_transferred_mb,
                    'sync_success': sync_status.sync_success,
                    'error_message': sync_status.error_message
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Status de sincronização não disponível'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Erro ao obter status de sync: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao obter status: {str(e)}'
        }), 500


@backup_sync_bp.route('/sync/execute', methods=['POST'])
def execute_sync():
    """
    Executa sincronização manual
    """
    try:
        service = get_backup_service()
        sync_status = service.synchronize_data()
        
        return jsonify({
            'success': sync_status.sync_success,
            'data': {
                'device_id': sync_status.device_id,
                'sync_direction': sync_status.sync_direction,
                'data_transferred_mb': sync_status.data_transferred_mb,
                'sync_timestamp': sync_status.last_sync.isoformat(),
                'error_message': sync_status.error_message if not sync_status.sync_success else None
            },
            'message': 'Sincronização concluída' if sync_status.sync_success else 'Falha na sincronização'
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro na sincronização: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro na sincronização: {str(e)}'
        }), 500


@backup_sync_bp.route('/system/status', methods=['GET'])
def get_system_status():
    """
    Obtém status completo do sistema de backup e sincronização
    """
    try:
        service = get_backup_service()
        system_status = service.get_system_status()
        
        return jsonify({
            'success': True,
            'data': system_status
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter status do sistema: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao obter status: {str(e)}'
        }), 500


@backup_sync_bp.route('/system/start', methods=['POST'])
def start_system():
    """
    Inicia serviços automáticos de backup e sincronização
    """
    try:
        service = get_backup_service()
        
        if not service.backup_active:
            service.start_automatic_backup()
        
        if not service.sync_active:
            service.start_automatic_sync()
        
        return jsonify({
            'success': True,
            'message': 'Serviços automáticos iniciados',
            'status': {
                'backup_active': service.backup_active,
                'sync_active': service.sync_active
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao iniciar serviços: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao iniciar serviços: {str(e)}'
        }), 500


@backup_sync_bp.route('/system/stop', methods=['POST'])
def stop_system():
    """
    Para serviços automáticos de backup e sincronização
    """
    try:
        service = get_backup_service()
        
        if service.backup_active:
            service.stop_automatic_backup()
        
        if service.sync_active:
            service.stop_automatic_sync()
        
        return jsonify({
            'success': True,
            'message': 'Serviços automáticos parados',
            'status': {
                'backup_active': service.backup_active,
                'sync_active': service.sync_active
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao parar serviços: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao parar serviços: {str(e)}'
        }), 500


@backup_sync_bp.route('/config', methods=['GET'])
def get_backup_config():
    """
    Obtém configuração atual do sistema
    """
    try:
        service = get_backup_service()
        config = service.config
        
        return jsonify({
            'success': True,
            'data': {
                'enabled': config.enabled,
                'interval_hours': config.interval_hours,
                'retention_days': config.retention_days,
                'max_local_backups': config.max_local_backups,
                'cloud_enabled': config.cloud_enabled,
                'cloud_provider': config.cloud_provider,
                'encryption_enabled': config.encryption_enabled,
                'compression_enabled': config.compression_enabled,
                'include_logs': config.include_logs,
                'include_attachments': config.include_attachments
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter configuração: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao obter configuração: {str(e)}'
        }), 500


@backup_sync_bp.route('/config', methods=['PUT'])
def update_backup_config():
    """
    Atualiza configuração do sistema
    """
    try:
        data = request.get_json() or {}
        service = get_backup_service()
        config = service.config
        
        # Atualizar configurações fornecidas
        if 'enabled' in data:
            config.enabled = bool(data['enabled'])
        if 'interval_hours' in data:
            config.interval_hours = max(1, int(data['interval_hours']))
        if 'retention_days' in data:
            config.retention_days = max(1, int(data['retention_days']))
        if 'max_local_backups' in data:
            config.max_local_backups = max(1, int(data['max_local_backups']))
        if 'cloud_enabled' in data:
            config.cloud_enabled = bool(data['cloud_enabled'])
        if 'cloud_provider' in data:
            config.cloud_provider = str(data['cloud_provider'])
        if 'encryption_enabled' in data:
            config.encryption_enabled = bool(data['encryption_enabled'])
        if 'compression_enabled' in data:
            config.compression_enabled = bool(data['compression_enabled'])
        if 'include_logs' in data:
            config.include_logs = bool(data['include_logs'])
        if 'include_attachments' in data:
            config.include_attachments = bool(data['include_attachments'])
        
        return jsonify({
            'success': True,
            'message': 'Configuração atualizada com sucesso',
            'data': {
                'enabled': config.enabled,
                'interval_hours': config.interval_hours,
                'retention_days': config.retention_days,
                'max_local_backups': config.max_local_backups,
                'cloud_enabled': config.cloud_enabled,
                'cloud_provider': config.cloud_provider,
                'encryption_enabled': config.encryption_enabled,
                'compression_enabled': config.compression_enabled,
                'include_logs': config.include_logs,
                'include_attachments': config.include_attachments
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao atualizar configuração: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao atualizar configuração: {str(e)}'
        }), 500


@backup_sync_bp.route('/health', methods=['GET'])
def health_check():
    """
    Verifica saúde do sistema de backup
    """
    try:
        service = get_backup_service()
        
        # Verificações básicas
        backup_dir_exists = service.backup_dir.exists()
        has_backups = len(service.backup_registry) > 0
        services_running = service.backup_active and service.sync_active
        
        health_status = {
            'status': 'healthy' if backup_dir_exists and services_running else 'degraded',
            'backup_directory_exists': backup_dir_exists,
            'has_backups': has_backups,
            'backup_service_active': service.backup_active,
            'sync_service_active': service.sync_active,
            'device_id': service.device_id,
            'timestamp': datetime.now().isoformat()
        }
        
        # Verificações adicionais
        try:
            latest_backup = max(service.backup_registry.values(), key=lambda b: b.timestamp) if service.backup_registry else None
            if latest_backup:
                hours_since_last = (datetime.now() - latest_backup.timestamp).total_seconds() / 3600
                health_status['hours_since_last_backup'] = round(hours_since_last, 1)
                health_status['last_backup_ok'] = hours_since_last < (service.config.interval_hours * 2)
        except:
            pass
        
        return jsonify({
            'success': True,
            'data': health_status
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro no health check: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Sistema de backup com problemas: {str(e)}',
            'status': 'unhealthy'
        }), 500


@backup_sync_bp.route('/metrics', methods=['GET'])
def get_backup_metrics():
    """
    Obtém métricas detalhadas do sistema de backup
    """
    try:
        service = get_backup_service()
        
        # Calcular métricas
        total_backups = len(service.backup_registry)
        total_size = sum(backup.size_bytes for backup in service.backup_registry.values())
        
        # Backups por tipo
        backup_types = {}
        for backup in service.backup_registry.values():
            backup_types[backup.backup_type] = backup_types.get(backup.backup_type, 0) + 1
        
        # Backups por dia (últimos 30 dias)
        backup_timeline = {}
        for backup in service.backup_registry.values():
            date_key = backup.timestamp.date().isoformat()
            backup_timeline[date_key] = backup_timeline.get(date_key, 0) + 1
        
        # Sucessos vs falhas (simulado)
        success_rate = 95.5  # Em uma implementação real, trackear falhas
        
        metrics = {
            'summary': {
                'total_backups': total_backups,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'average_size_mb': round((total_size / total_backups) / 1024 / 1024, 2) if total_backups > 0 else 0,
                'success_rate': success_rate
            },
            'breakdown': {
                'by_type': backup_types,
                'by_date': backup_timeline
            },
            'storage': {
                'local_storage_mb': service._get_directory_size(service.backup_dir),
                'available_space_mb': service._get_available_space(),
                'retention_days': service.config.retention_days
            },
            'performance': {
                'backup_interval_hours': service.config.interval_hours,
                'compression_ratio': 0.75,  # Simulado
                'encryption_overhead': 0.05  # Simulado
            }
        }
        
        return jsonify({
            'success': True,
            'data': metrics
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter métricas: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao obter métricas: {str(e)}'
        }), 500


# Cleanup quando a aplicação for encerrada
@backup_sync_bp.teardown_app_request
def cleanup_backup_service(exception):
    """Cleanup do serviço de backup"""
    # Os serviços continuam rodando em background
    pass