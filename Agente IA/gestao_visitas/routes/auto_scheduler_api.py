"""
APIs para controlar o Sistema de Agendamento Automático
Integração entre frontend e backend do auto scheduler
"""

from flask import Blueprint, request, jsonify
from gestao_visitas.services.auto_scheduler import AutoSchedulerService
from gestao_visitas.db import db
from gestao_visitas.services.relatorios import RelatorioService
import logging

logger = logging.getLogger(__name__)

auto_scheduler_bp = Blueprint('auto_scheduler', __name__)

# Instância global do serviço (será inicializada na aplicação)
auto_scheduler_service = None

def init_auto_scheduler_service(app):
    """Inicializa o serviço de agendamento automático"""
    global auto_scheduler_service
    
    with app.app_context():
        relatorio_service = RelatorioService()
        auto_scheduler_service = AutoSchedulerService(db, relatorio_service, app)
        
        # Iniciar o scheduler automaticamente
        auto_scheduler_service.start_scheduler()
        
        logger.info("AutoSchedulerService inicializado e iniciado")

@auto_scheduler_bp.route('/api/agendamento-automatico/status', methods=['GET'])
def get_scheduler_status():
    """Retorna status do agendamento automático"""
    try:
        if not auto_scheduler_service:
            return jsonify({
                'error': 'Serviço de agendamento não inicializado',
                'scheduler_running': False,
                'tasks': {}
            }), 503
        
        status = auto_scheduler_service.get_task_status()
        
        return jsonify({
            'success': True,
            'scheduler_running': status['scheduler_running'],
            'tasks': status['tasks']
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter status do scheduler: {e}")
        return jsonify({
            'error': 'Erro interno do servidor',
            'scheduler_running': False,
            'tasks': {}
        }), 500

@auto_scheduler_bp.route('/api/agendamento-automatico/toggle', methods=['POST'])
def toggle_scheduler():
    """Ativa/desativa o agendamento automático"""
    try:
        if not auto_scheduler_service:
            return jsonify({
                'error': 'Serviço de agendamento não inicializado',
                'success': False
            }), 503
        
        data = request.get_json() or {}
        action = data.get('action', 'toggle')
        
        if action == 'start' or (action == 'toggle' and not auto_scheduler_service.is_running):
            auto_scheduler_service.start_scheduler()
            message = 'Agendamento automático ativado com sucesso'
            status = True
        else:
            auto_scheduler_service.stop_scheduler()
            message = 'Agendamento automático desativado'
            status = False
        
        return jsonify({
            'success': True,
            'message': message,
            'scheduler_running': status,
            'tasks': auto_scheduler_service.get_task_status()['tasks']
        })
        
    except Exception as e:
        logger.error(f"Erro ao alternar scheduler: {e}")
        return jsonify({
            'error': 'Erro interno do servidor',
            'success': False
        }), 500

@auto_scheduler_bp.route('/api/agendamento-automatico/task/<task_id>/toggle', methods=['POST'])
def toggle_task(task_id):
    """Habilita/desabilita uma tarefa específica"""
    try:
        if not auto_scheduler_service:
            return jsonify({
                'error': 'Serviço de agendamento não inicializado',
                'success': False
            }), 503
        
        data = request.get_json() or {}
        enable = data.get('enable', True)
        
        if enable:
            success = auto_scheduler_service.enable_task(task_id)
            action = 'habilitada'
        else:
            success = auto_scheduler_service.disable_task(task_id)
            action = 'desabilitada'
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Tarefa {task_id} {action} com sucesso',
                'task_status': auto_scheduler_service.get_task_status()['tasks'].get(task_id, {})
            })
        else:
            return jsonify({
                'error': f'Tarefa {task_id} não encontrada',
                'success': False
            }), 404
            
    except Exception as e:
        logger.error(f"Erro ao alternar tarefa {task_id}: {e}")
        return jsonify({
            'error': 'Erro interno do servidor',
            'success': False
        }), 500

@auto_scheduler_bp.route('/api/agendamento-automatico/task/<task_id>/interval', methods=['PUT'])
def update_task_interval(task_id):
    """Atualiza intervalo de uma tarefa"""
    try:
        if not auto_scheduler_service:
            return jsonify({
                'error': 'Serviço de agendamento não inicializado',
                'success': False
            }), 503
        
        data = request.get_json()
        if not data or 'interval_minutes' not in data:
            return jsonify({
                'error': 'Parâmetro interval_minutes é obrigatório',
                'success': False
            }), 400
        
        interval_minutes = data['interval_minutes']
        
        if not isinstance(interval_minutes, int) or interval_minutes < 1:
            return jsonify({
                'error': 'Intervalo deve ser um número inteiro positivo',
                'success': False
            }), 400
        
        success = auto_scheduler_service.update_task_interval(task_id, interval_minutes)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Intervalo da tarefa {task_id} atualizado para {interval_minutes} minutos',
                'task_status': auto_scheduler_service.get_task_status()['tasks'].get(task_id, {})
            })
        else:
            return jsonify({
                'error': f'Tarefa {task_id} não encontrada',
                'success': False
            }), 404
            
    except Exception as e:
        logger.error(f"Erro ao atualizar intervalo da tarefa {task_id}: {e}")
        return jsonify({
            'error': 'Erro interno do servidor',
            'success': False
        }), 500

@auto_scheduler_bp.route('/api/agendamento-automatico/task/<task_id>/execute', methods=['POST'])
def execute_task_now(task_id):
    """Executa uma tarefa imediatamente"""
    try:
        if not auto_scheduler_service:
            return jsonify({
                'error': 'Serviço de agendamento não inicializado',
                'success': False
            }), 503
        
        success = auto_scheduler_service.execute_task_now(task_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Tarefa {task_id} executada com sucesso',
                'task_status': auto_scheduler_service.get_task_status()['tasks'].get(task_id, {})
            })
        else:
            return jsonify({
                'error': f'Falha ao executar tarefa {task_id}',
                'success': False
            }), 500
            
    except Exception as e:
        logger.error(f"Erro ao executar tarefa {task_id}: {e}")
        return jsonify({
            'error': 'Erro interno do servidor',
            'success': False
        }), 500

@auto_scheduler_bp.route('/api/agendamento-automatico/relatorio-config', methods=['GET', 'POST'])
def manage_relatorio_config():
    """Gerencia configurações de relatórios automáticos"""
    try:
        if not auto_scheduler_service:
            return jsonify({
                'error': 'Serviço de agendamento não inicializado',
                'success': False
            }), 503
        
        if request.method == 'GET':
            # Retornar configurações atuais dos relatórios
            tasks = auto_scheduler_service.get_task_status()['tasks']
            relatorio_tasks = {
                'daily': tasks.get('relatorio_diario', {}),
                'weekly': tasks.get('relatorio_semanal', {}),
                'monthly': tasks.get('relatorio_mensal', {})
            }
            
            return jsonify({
                'success': True,
                'relatorio_config': relatorio_tasks,
                'scheduler_running': auto_scheduler_service.is_running
            })
        
        elif request.method == 'POST':
            # Atualizar configurações dos relatórios
            data = request.get_json()
            if not data:
                return jsonify({
                    'error': 'Dados de configuração são obrigatórios',
                    'success': False
                }), 400
            
            updated_tasks = []
            
            # Relatório diário
            if 'daily' in data:
                config = data['daily']
                if 'enabled' in config:
                    task_id = 'relatorio_diario'
                    if config['enabled']:
                        auto_scheduler_service.enable_task(task_id)
                    else:
                        auto_scheduler_service.disable_task(task_id)
                    updated_tasks.append('daily')
            
            # Relatório semanal
            if 'weekly' in data:
                config = data['weekly']
                if 'enabled' in config:
                    task_id = 'relatorio_semanal'
                    if config['enabled']:
                        auto_scheduler_service.enable_task(task_id)
                    else:
                        auto_scheduler_service.disable_task(task_id)
                    updated_tasks.append('weekly')
            
            # Relatório mensal
            if 'monthly' in data:
                config = data['monthly']
                if 'enabled' in config:
                    task_id = 'relatorio_mensal'
                    if config['enabled']:
                        auto_scheduler_service.enable_task(task_id)
                    else:
                        auto_scheduler_service.disable_task(task_id)
                    updated_tasks.append('monthly')
            
            return jsonify({
                'success': True,
                'message': f'Configurações dos relatórios atualizadas: {", ".join(updated_tasks)}',
                'updated_tasks': updated_tasks
            })
            
    except Exception as e:
        logger.error(f"Erro ao gerenciar configurações de relatório: {e}")
        return jsonify({
            'error': 'Erro interno do servidor',
            'success': False
        }), 500

@auto_scheduler_bp.route('/api/agendamento-automatico/logs', methods=['GET'])
def get_scheduler_logs():
    """Retorna logs do agendamento automático"""
    try:
        if not auto_scheduler_service:
            return jsonify({
                'error': 'Serviço de agendamento não inicializado',
                'success': False
            }), 503
        
        # Simular logs do sistema
        logs = [
            {
                'timestamp': '2024-01-15 08:00:00',
                'level': 'INFO',
                'message': 'Relatório diário gerado com sucesso',
                'task': 'relatorio_diario'
            },
            {
                'timestamp': '2024-01-15 06:00:00',
                'level': 'INFO',
                'message': 'Backup automático realizado',
                'task': 'backup_dados'
            },
            {
                'timestamp': '2024-01-15 04:00:00',
                'level': 'INFO',
                'message': 'Verificação de status concluída: 3 atualizações',
                'task': 'verificacao_status'
            }
        ]
        
        return jsonify({
            'success': True,
            'logs': logs,
            'total_logs': len(logs)
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter logs: {e}")
        return jsonify({
            'error': 'Erro interno do servidor',
            'success': False
        }), 500

@auto_scheduler_bp.route('/api/agendamento-automatico/stats', methods=['GET'])
def get_scheduler_stats():
    """Retorna estatísticas do agendamento automático"""
    try:
        if not auto_scheduler_service:
            return jsonify({
                'error': 'Serviço de agendamento não inicializado',
                'success': False
            }), 503
        
        tasks = auto_scheduler_service.get_task_status()['tasks']
        
        stats = {
            'total_tasks': len(tasks),
            'active_tasks': sum(1 for task in tasks.values() if task.get('enabled', False)),
            'scheduler_uptime': 'Calculando...',
            'last_executions': {
                task_id: task.get('last_execution', 'Nunca executado')
                for task_id, task in tasks.items()
            },
            'next_executions': {
                task_id: task.get('next_execution', 'Não agendado')
                for task_id, task in tasks.items()
            }
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({
            'error': 'Erro interno do servidor',
            'success': False
        }), 500