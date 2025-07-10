import logging
from datetime import datetime
from flask import jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from .validators import ValidationError

class ErrorHandler:
    """Classe para tratamento centralizado de erros"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa handlers de erro no app Flask"""
        
        @app.errorhandler(ValidationError)
        def handle_validation_error(error):
            """Trata erros de validação"""
            self.log_error('Validation Error', str(error), request)
            return jsonify({
                'error': str(error),
                'type': 'validation_error',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        @app.errorhandler(SQLAlchemyError)
        def handle_database_error(error):
            """Trata erros de banco de dados"""
            self.log_error('Database Error', str(error), request)
            return jsonify({
                'error': 'Erro interno do banco de dados',
                'type': 'database_error',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        @app.errorhandler(404)
        def handle_not_found(error):
            """Trata erros 404"""
            return jsonify({
                'error': 'Recurso não encontrado',
                'type': 'not_found',
                'timestamp': datetime.now().isoformat()
            }), 404
        
        @app.errorhandler(405)
        def handle_method_not_allowed(error):
            """Trata erros de método não permitido"""
            return jsonify({
                'error': 'Método não permitido',
                'type': 'method_not_allowed',
                'timestamp': datetime.now().isoformat()
            }), 405
        
        @app.errorhandler(500)
        def handle_internal_error(error):
            """Trata erros internos do servidor"""
            self.log_error('Internal Server Error', str(error), request)
            return jsonify({
                'error': 'Erro interno do servidor',
                'type': 'internal_error',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        @app.errorhandler(Exception)
        def handle_generic_error(error):
            """Trata erros genéricos não capturados"""
            self.log_error('Unhandled Exception', str(error), request)
            return jsonify({
                'error': 'Erro interno do servidor',
                'type': 'generic_error',
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @staticmethod
    def log_error(error_type, error_message, request_obj):
        """Registra erro no log"""
        logger = logging.getLogger('pnsb_errors')
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_message': error_message,
            'url': request_obj.url if request_obj else 'N/A',
            'method': request_obj.method if request_obj else 'N/A',
            'ip': request_obj.remote_addr if request_obj else 'N/A',
            'user_agent': request_obj.headers.get('User-Agent', 'N/A') if request_obj else 'N/A'
        }
        
        logger.error(f"Error: {error_type} | {error_message} | {log_data}")
    
    @staticmethod
    def setup_logging(app):
        """Configura sistema de logging"""
        if not app.debug:
            # Configurar handler para arquivo de log
            import os
            log_dir = os.path.join(app.instance_path, 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            file_handler = logging.FileHandler(
                os.path.join(log_dir, 'pnsb_errors.log')
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s'
            ))
            file_handler.setLevel(logging.ERROR)
            
            # Configurar logger específico para erros
            error_logger = logging.getLogger('pnsb_errors')
            error_logger.addHandler(file_handler)
            error_logger.setLevel(logging.ERROR)
            
            # Adicionar ao app logger também
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)

class APIResponse:
    """Classe para padronizar respostas da API"""
    
    @staticmethod
    def success(data=None, message="Operação realizada com sucesso", status_code=200):
        """Resposta de sucesso padronizada"""
        response = {
            'success': True,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        if data is not None:
            response['data'] = data
        
        return jsonify(response), status_code
    
    @staticmethod
    def error(message="Erro interno", error_type="generic_error", status_code=500, details=None):
        """Resposta de erro padronizada"""
        response = {
            'success': False,
            'error': message,
            'type': error_type,
            'timestamp': datetime.now().isoformat()
        }
        
        if details:
            response['details'] = details
        
        return jsonify(response), status_code
    
    @staticmethod
    def validation_error(message, field=None):
        """Resposta específica para erros de validação"""
        response = {
            'success': False,
            'error': message,
            'type': 'validation_error',
            'timestamp': datetime.now().isoformat()
        }
        
        if field:
            response['field'] = field
        
        return jsonify(response), 400
    
    @staticmethod
    def not_found(resource="Recurso"):
        """Resposta específica para recursos não encontrados"""
        return APIResponse.error(
            message=f"{resource} não encontrado",
            error_type="not_found",
            status_code=404
        )