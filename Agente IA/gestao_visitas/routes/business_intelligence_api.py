"""
APIs para Business Intelligence Automatizado - PNSB 2024
Dashboards em tempo real, alertas preditivos e relatórios automáticos
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import json
from typing import Dict, Any

from gestao_visitas.services.business_intelligence import BusinessIntelligence

business_intelligence_bp = Blueprint('business_intelligence', __name__)

# Instância global do serviço BI
bi_service = None

def get_bi_service():
    """Obtém instância do serviço BI (singleton)"""
    global bi_service
    if bi_service is None:
        bi_service = BusinessIntelligence()
        # Iniciar monitoramento automaticamente
        bi_service.start_monitoring()
    return bi_service


@business_intelligence_bp.route('/dashboard/realtime', methods=['GET'])
def get_realtime_dashboard():
    """
    Retorna dashboard completo em tempo real
    """
    try:
        bi = get_bi_service()
        dashboard_data = bi.get_realtime_dashboard()
        
        return jsonify({
            'success': True,
            'data': dashboard_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro no dashboard tempo real: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro no dashboard: {str(e)}'
        }), 500


@business_intelligence_bp.route('/kpis/current', methods=['GET'])
def get_current_kpis():
    """
    Retorna KPIs atuais do sistema
    """
    try:
        bi = get_bi_service()
        dashboard_data = bi.get_realtime_dashboard()
        
        return jsonify({
            'success': True,
            'data': {
                'kpis': dashboard_data.get('main_kpis', []),
                'timestamp': dashboard_data.get('timestamp'),
                'next_refresh': dashboard_data.get('next_refresh')
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter KPIs: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao obter KPIs: {str(e)}'
        }), 500


@business_intelligence_bp.route('/kpis/<metric_name>/history', methods=['GET'])
def get_kpi_history(metric_name):
    """
    Retorna histórico de um KPI específico
    """
    try:
        days = int(request.args.get('days', 30))
        
        bi = get_bi_service()
        history = bi.get_kpi_history(metric_name, days)
        
        return jsonify({
            'success': True,
            'data': {
                'metric_name': metric_name,
                'history': history,
                'period_days': days
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter histórico de {metric_name}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao obter histórico: {str(e)}'
        }), 500


@business_intelligence_bp.route('/alerts/active', methods=['GET'])
def get_active_alerts():
    """
    Retorna alertas ativos do sistema
    """
    try:
        bi = get_bi_service()
        dashboard_data = bi.get_realtime_dashboard()
        
        alerts = dashboard_data.get('active_alerts', [])
        
        # Filtrar por severidade se especificado
        severity_filter = request.args.get('severity')
        if severity_filter:
            alerts = [alert for alert in alerts if alert['severity'] == severity_filter]
        
        return jsonify({
            'success': True,
            'data': {
                'alerts': alerts,
                'total_count': len(alerts),
                'timestamp': dashboard_data.get('timestamp')
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter alertas: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao obter alertas: {str(e)}'
        }), 500


@business_intelligence_bp.route('/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """
    Marca um alerta como reconhecido
    """
    try:
        # Em uma implementação real, isso atualizaria o status no banco
        current_app.logger.info(f"Alerta {alert_id} reconhecido pelo usuário")
        
        return jsonify({
            'success': True,
            'message': f'Alerta {alert_id} reconhecido com sucesso'
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao reconhecer alerta: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao reconhecer alerta: {str(e)}'
        }), 500


@business_intelligence_bp.route('/reports/executive', methods=['POST'])
def generate_executive_report():
    """
    Gera relatório executivo automatizado
    """
    try:
        data = request.get_json() or {}
        period = data.get('period', 'monthly')
        
        bi = get_bi_service()
        report = bi.generate_executive_report(period)
        
        # Converter para formato serializável
        report_data = {
            'report_id': report.report_id,
            'generated_at': report.generated_at.isoformat(),
            'period': report.period,
            'summary': report.summary,
            'key_metrics': [
                {
                    'name': kpi.name,
                    'value': kpi.value,
                    'unit': kpi.unit,
                    'trend': kpi.trend,
                    'status': kpi.status,
                    'target_value': kpi.target_value,
                    'last_updated': kpi.last_updated.isoformat()
                }
                for kpi in report.key_metrics
            ],
            'alerts': [
                {
                    'id': alert.id,
                    'metric_name': alert.metric_name,
                    'message': alert.message,
                    'severity': alert.severity,
                    'timestamp': alert.timestamp.isoformat(),
                    'current_value': alert.current_value,
                    'threshold_value': alert.threshold_value
                }
                for alert in report.alerts
            ],
            'recommendations': report.recommendations,
            'trends': report.trends
        }
        
        return jsonify({
            'success': True,
            'data': report_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao gerar relatório executivo: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao gerar relatório: {str(e)}'
        }), 500


@business_intelligence_bp.route('/monitoring/status', methods=['GET'])
def get_monitoring_status():
    """
    Retorna status do monitoramento contínuo
    """
    try:
        bi = get_bi_service()
        
        return jsonify({
            'success': True,
            'data': {
                'monitoring_active': bi.monitoring_active,
                'refresh_interval': bi.refresh_interval,
                'alert_check_interval': bi.alert_check_interval,
                'last_refresh': bi.last_refresh.isoformat() if bi.last_refresh else None,
                'total_alert_configs': len(bi.alert_configs),
                'enabled_alerts': len([c for c in bi.alert_configs if c.enabled])
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter status do monitoramento: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao obter status: {str(e)}'
        }), 500


@business_intelligence_bp.route('/monitoring/start', methods=['POST'])
def start_monitoring():
    """
    Inicia monitoramento contínuo
    """
    try:
        bi = get_bi_service()
        
        if bi.monitoring_active:
            return jsonify({
                'success': True,
                'message': 'Monitoramento já está ativo'
            })
        
        bi.start_monitoring()
        
        return jsonify({
            'success': True,
            'message': 'Monitoramento iniciado com sucesso'
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao iniciar monitoramento: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao iniciar monitoramento: {str(e)}'
        }), 500


@business_intelligence_bp.route('/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """
    Para monitoramento contínuo
    """
    try:
        bi = get_bi_service()
        bi.stop_monitoring()
        
        return jsonify({
            'success': True,
            'message': 'Monitoramento parado com sucesso'
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao parar monitoramento: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao parar monitoramento: {str(e)}'
        }), 500


@business_intelligence_bp.route('/monitoring/refresh', methods=['POST'])
def force_refresh():
    """
    Força atualização imediata dos dados
    """
    try:
        bi = get_bi_service()
        bi._refresh_all_kpis()
        bi._check_all_alerts()
        
        return jsonify({
            'success': True,
            'message': 'Dados atualizados com sucesso',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao forçar atualização: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao atualizar dados: {str(e)}'
        }), 500


@business_intelligence_bp.route('/predictions/completion', methods=['GET'])
def get_completion_predictions():
    """
    Retorna previsões de conclusão do projeto
    """
    try:
        bi = get_bi_service()
        dashboard_data = bi.get_realtime_dashboard()
        
        predictions = dashboard_data.get('predictions', {})
        
        return jsonify({
            'success': True,
            'data': predictions
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter previsões: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao obter previsões: {str(e)}'
        }), 500


@business_intelligence_bp.route('/statistics/realtime', methods=['GET'])
def get_realtime_statistics():
    """
    Retorna estatísticas do sistema em tempo real
    """
    try:
        bi = get_bi_service()
        dashboard_data = bi.get_realtime_dashboard()
        
        stats = dashboard_data.get('realtime_stats', {})
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter estatísticas: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao obter estatísticas: {str(e)}'
        }), 500


@business_intelligence_bp.route('/trends/analysis', methods=['GET'])
def get_trends_analysis():
    """
    Retorna análise de tendências
    """
    try:
        period = request.args.get('period', '30d')  # 7d, 30d, 90d
        
        bi = get_bi_service()
        dashboard_data = bi.get_realtime_dashboard()
        
        trends = dashboard_data.get('trends', {})
        
        return jsonify({
            'success': True,
            'data': {
                'period': period,
                'trends': trends,
                'analysis_timestamp': dashboard_data.get('timestamp')
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro na análise de tendências: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro na análise: {str(e)}'
        }), 500


@business_intelligence_bp.route('/health', methods=['GET'])
def health_check():
    """
    Verifica saúde do sistema BI
    """
    try:
        bi = get_bi_service()
        
        health_status = {
            'status': 'healthy',
            'monitoring_active': bi.monitoring_active,
            'last_refresh': bi.last_refresh.isoformat() if bi.last_refresh else None,
            'cache_size': len(bi.kpi_cache),
            'alert_configs': len(bi.alert_configs),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': health_status
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro no health check: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Sistema BI com problemas: {str(e)}',
            'status': 'unhealthy'
        }), 500


@business_intelligence_bp.route('/export/dashboard', methods=['POST'])
def export_dashboard_data():
    """
    Exporta dados do dashboard para diferentes formatos
    """
    try:
        data = request.get_json() or {}
        export_format = data.get('format', 'json')  # json, csv, excel
        
        bi = get_bi_service()
        dashboard_data = bi.get_realtime_dashboard()
        
        if export_format == 'json':
            return jsonify({
                'success': True,
                'data': dashboard_data,
                'export_format': 'json',
                'exported_at': datetime.now().isoformat()
            })
        else:
            # Para CSV/Excel, seria necessário implementar conversão específica
            return jsonify({
                'success': False,
                'error': f'Formato {export_format} não implementado ainda'
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"Erro ao exportar dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro na exportação: {str(e)}'
        }), 500


# Cleanup quando a aplicação for encerrada
@business_intelligence_bp.teardown_app_request
def cleanup_bi_service(exception):
    """Cleanup do serviço BI"""
    global bi_service
    if bi_service and bi_service.monitoring_active:
        # Não parar o monitoramento aqui, pois pode ser uma requisição temporária
        pass