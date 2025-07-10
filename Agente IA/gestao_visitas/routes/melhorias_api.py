"""
API endpoints para as novas funcionalidades avançadas do Sistema PNSB
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, date, timedelta
import os

from ..services.agendamento_avancado import AgendamentoAvancado
from ..services.checklist_inteligente import ChecklistInteligente
from ..services.contatos_inteligente import ContatosInteligente
from ..services.relatorios_avancados import RelatoriosAvancados
from ..services.notificacoes_alertas import SistemaNotificacoes
from ..services.dashboard_avancado import DashboardAvancado
from ..services.maps import MapaService
from ..config.security import SecurityConfig
from ..utils.validators import validate_json_input, ValidationError
from ..utils.error_handlers import APIResponse
from ..models.agendamento import Visita
from ..models.checklist import Checklist
from ..models.contatos import Contato
from ..db import db

# Criar blueprint para novas APIs
melhorias_bp = Blueprint('melhorias', __name__)

# Inicializar serviços avançados
google_maps_key = SecurityConfig.get_google_maps_key()
google_gemini_key = SecurityConfig.get_google_gemini_key()

mapa_service = MapaService(google_maps_key) if google_maps_key else None
agendamento_service = AgendamentoAvancado(mapa_service)
checklist_service = ChecklistInteligente()
contatos_service = ContatosInteligente(google_gemini_key)
relatorios_service = RelatoriosAvancados()
notificacoes_service = SistemaNotificacoes()
dashboard_service = DashboardAvancado(mapa_service, google_gemini_key)

# =====================================
# AGENDAMENTO AVANÇADO
# =====================================

@melhorias_bp.route('/agendamento/sugerir-horarios', methods=['POST'])
@validate_json_input(required_fields=['municipio', 'data'])
def sugerir_horarios():
    """Sugere horários disponíveis para agendamento"""
    try:
        data = request.validated_data
        municipio = data['municipio']
        data_visita = datetime.strptime(data['data'], '%Y-%m-%d').date()
        duracao = data.get('duracao_minutos', 60)
        
        horarios_sugeridos = agendamento_service.sugerir_horarios(
            municipio, data_visita, duracao
        )
        
        return APIResponse.success(
            data=horarios_sugeridos,
            message=f"Encontrados {len(horarios_sugeridos)} horários disponíveis"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao sugerir horários: {str(e)}")

@melhorias_bp.route('/agendamento/otimizar-rota', methods=['POST'])
@validate_json_input(required_fields=['data'])
def otimizar_rota_diaria():
    """Otimiza rota para visitas do dia"""
    try:
        data = request.validated_data
        data_visita = datetime.strptime(data['data'], '%Y-%m-%d').date()
        origem = data.get('origem', 'Itajaí')
        
        rota_otimizada = agendamento_service.otimizar_rota_diaria(data_visita, origem)
        
        return APIResponse.success(
            data=rota_otimizada,
            message="Rota otimizada gerada com sucesso"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao otimizar rota: {str(e)}")

@melhorias_bp.route('/agendamento/detectar-conflitos', methods=['POST'])
@validate_json_input(required_fields=['municipio', 'data', 'hora_inicio', 'hora_fim'])
def detectar_conflitos():
    """Detecta conflitos de agendamento"""
    try:
        data = request.validated_data
        
        conflitos = agendamento_service.detectar_conflitos_agendamento(
            municipio=data['municipio'],
            data=datetime.strptime(data['data'], '%Y-%m-%d').date(),
            hora_inicio=datetime.strptime(data['hora_inicio'], '%H:%M').time(),
            hora_fim=datetime.strptime(data['hora_fim'], '%H:%M').time(),
            excluir_visita_id=data.get('visita_id')
        )
        
        return APIResponse.success(
            data=conflitos,
            message="Verificação de conflitos concluída"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao detectar conflitos: {str(e)}")

@melhorias_bp.route('/agendamento/cronograma-semanal', methods=['GET'])
def obter_cronograma_semanal():
    """Obtém cronograma semanal otimizado"""
    try:
        data_inicio = datetime.strptime(
            request.args.get('inicio', date.today().strftime('%Y-%m-%d')), 
            '%Y-%m-%d'
        ).date()
        data_fim = data_inicio + timedelta(days=6)
        
        cronograma = agendamento_service.gerar_cronograma_semanal(data_inicio, data_fim)
        
        return APIResponse.success(
            data=cronograma,
            message="Cronograma semanal gerado"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao gerar cronograma: {str(e)}")

# =====================================
# CHECKLIST INTELIGENTE
# =====================================

@melhorias_bp.route('/checklist/personalizado/<int:visita_id>', methods=['GET'])
def obter_checklist_personalizado(visita_id):
    """Obtém checklist personalizado para uma visita"""
    try:
        visita = Visita.query.get(visita_id)
        if not visita:
            return APIResponse.not_found("Visita")
        
        checklist_personalizado = checklist_service.gerar_checklist_personalizado(visita)
        
        return APIResponse.success(
            data=checklist_personalizado,
            message="Checklist personalizado gerado"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao gerar checklist: {str(e)}")

@melhorias_bp.route('/checklist/validar-completude/<int:visita_id>', methods=['GET'])
def validar_completude_checklist(visita_id):
    """Valida completude inteligente do checklist"""
    try:
        visita = Visita.query.get(visita_id)
        if not visita or not visita.checklist:
            return APIResponse.not_found("Visita ou checklist")
        
        validacao = checklist_service.validar_completude_inteligente(visita.checklist, visita)
        
        return APIResponse.success(
            data=validacao,
            message="Validação de completude realizada"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro na validação: {str(e)}")

@melhorias_bp.route('/checklist/proximo-passo/<int:visita_id>', methods=['GET'])
def sugerir_proximo_passo(visita_id):
    """Sugere próximo passo no checklist"""
    try:
        visita = Visita.query.get(visita_id)
        if not visita or not visita.checklist:
            return APIResponse.not_found("Visita ou checklist")
        
        sugestao = checklist_service.sugerir_proximo_passo(visita.checklist, visita)
        
        return APIResponse.success(
            data=sugestao,
            message="Próximo passo sugerido"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao sugerir próximo passo: {str(e)}")

@melhorias_bp.route('/checklist/relatorio-qualidade/<int:visita_id>', methods=['GET'])
def obter_relatorio_qualidade_checklist(visita_id):
    """Obtém relatório de qualidade do checklist"""
    try:
        visita = Visita.query.get(visita_id)
        if not visita or not visita.checklist:
            return APIResponse.not_found("Visita ou checklist")
        
        relatorio = checklist_service.gerar_relatorio_qualidade(visita.checklist, visita)
        
        return APIResponse.success(
            data=relatorio,
            message="Relatório de qualidade gerado"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao gerar relatório: {str(e)}")

# =====================================
# CONTATOS INTELIGENTE
# =====================================

@melhorias_bp.route('/contatos/enriquecer', methods=['POST'])
@validate_json_input(required_fields=['municipio', 'tipo_pesquisa'])
def enriquecer_contato():
    """Enriquece dados de contato automaticamente"""
    try:
        data = request.validated_data
        
        resultado = contatos_service.enriquecer_contato_automatico(
            data['municipio'], 
            data['tipo_pesquisa']
        )
        
        return APIResponse.success(
            data=resultado,
            message="Enriquecimento de contato realizado"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao enriquecer contato: {str(e)}")

@melhorias_bp.route('/contatos/validar-qualidade/<int:contato_id>', methods=['GET'])
def validar_qualidade_contato(contato_id):
    """Valida qualidade de um contato"""
    try:
        contato = Contato.query.get(contato_id)
        if not contato:
            return APIResponse.not_found("Contato")
        
        validacao = contatos_service.validar_qualidade_contato(contato)
        
        return APIResponse.success(
            data=validacao,
            message="Validação de qualidade realizada"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro na validação: {str(e)}")

@melhorias_bp.route('/contatos/detectar-duplicados', methods=['GET'])
def detectar_contatos_duplicados():
    """Detecta contatos duplicados"""
    try:
        municipio = request.args.get('municipio')
        
        duplicados = contatos_service.detectar_contatos_duplicados(municipio)
        
        return APIResponse.success(
            data=duplicados,
            message=f"Encontrados {len(duplicados)} possíveis duplicados"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao detectar duplicados: {str(e)}")

@melhorias_bp.route('/contatos/relatorio-qualidade', methods=['GET'])
def obter_relatorio_qualidade_contatos():
    """Obtém relatório de qualidade dos contatos"""
    try:
        municipio = request.args.get('municipio')
        
        relatorio = contatos_service.gerar_relatorio_qualidade_contatos(municipio)
        
        return APIResponse.success(
            data=relatorio,
            message="Relatório de qualidade gerado"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao gerar relatório: {str(e)}")

# =====================================
# RELATÓRIOS AVANÇADOS
# =====================================

@melhorias_bp.route('/relatorios/executivo', methods=['POST'])
@validate_json_input(required_fields=['periodo_inicio', 'periodo_fim'])
def gerar_relatorio_executivo():
    """Gera relatório executivo"""
    try:
        data = request.validated_data
        
        periodo_inicio = datetime.strptime(data['periodo_inicio'], '%Y-%m-%d').date()
        periodo_fim = datetime.strptime(data['periodo_fim'], '%Y-%m-%d').date()
        
        relatorio = relatorios_service.gerar_relatorio_executivo(periodo_inicio, periodo_fim)
        
        return APIResponse.success(
            data=relatorio,
            message="Relatório executivo gerado"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao gerar relatório: {str(e)}")

@melhorias_bp.route('/relatorios/qualidade', methods=['POST'])
@validate_json_input(required_fields=['periodo_inicio', 'periodo_fim'])
def gerar_relatorio_qualidade():
    """Gera relatório de qualidade"""
    try:
        data = request.validated_data
        
        periodo_inicio = datetime.strptime(data['periodo_inicio'], '%Y-%m-%d').date()
        periodo_fim = datetime.strptime(data['periodo_fim'], '%Y-%m-%d').date()
        
        relatorio = relatorios_service.gerar_relatorio_qualidade(periodo_inicio, periodo_fim)
        
        return APIResponse.success(
            data=relatorio,
            message="Relatório de qualidade gerado"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao gerar relatório: {str(e)}")

@melhorias_bp.route('/relatorios/tendencias', methods=['GET'])
def gerar_analise_tendencias():
    """Gera análise de tendências"""
    try:
        periodo_meses = int(request.args.get('meses', 6))
        
        analise = relatorios_service.gerar_analise_tendencias(periodo_meses)
        
        return APIResponse.success(
            data=analise,
            message="Análise de tendências gerada"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao gerar análise: {str(e)}")

@melhorias_bp.route('/relatorios/exportar', methods=['POST'])
@validate_json_input(required_fields=['relatorio_data', 'formato'])
def exportar_relatorio():
    """Exporta relatório em formato específico"""
    try:
        data = request.validated_data
        
        resultado = relatorios_service.exportar_relatorio(
            data['relatorio_data'],
            data['formato']
        )
        
        return APIResponse.success(
            data=resultado,
            message=f"Relatório exportado em {data['formato']}"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao exportar relatório: {str(e)}")

# =====================================
# NOTIFICAÇÕES E ALERTAS
# =====================================

@melhorias_bp.route('/notificacoes/configurar', methods=['POST'])
@validate_json_input(required_fields=['configuracoes'])
def configurar_notificacoes_usuario():
    """Configura preferências de notificação do usuário"""
    try:
        data = request.validated_data
        usuario_id = data.get('usuario_id', 'default')
        
        resultado = notificacoes_service.configurar_usuario(
            usuario_id,
            data['configuracoes']
        )
        
        return APIResponse.success(
            data=resultado,
            message="Configurações de notificação aplicadas"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao configurar notificações: {str(e)}")

@melhorias_bp.route('/notificacoes/verificar-alertas', methods=['GET'])
def verificar_alertas_sistema():
    """Verifica alertas do sistema"""
    try:
        alertas = notificacoes_service.verificar_alertas_sistema()
        
        return APIResponse.success(
            data=alertas,
            message="Verificação de alertas concluída"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao verificar alertas: {str(e)}")

@melhorias_bp.route('/notificacoes/lembretes', methods=['GET'])
def gerar_lembretes():
    """Gera lembretes inteligentes"""
    try:
        lembretes = notificacoes_service.gerar_lembretes_inteligentes()
        
        return APIResponse.success(
            data=lembretes,
            message="Lembretes gerados"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao gerar lembretes: {str(e)}")

@melhorias_bp.route('/notificacoes/resumo-diario', methods=['GET'])
def obter_resumo_diario():
    """Obtém resumo diário de atividades"""
    try:
        data_param = request.args.get('data')
        data_resumo = datetime.strptime(data_param, '%Y-%m-%d').date() if data_param else None
        
        resumo = notificacoes_service.gerar_resumo_diario(data_resumo)
        
        return APIResponse.success(
            data=resumo,
            message="Resumo diário gerado"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao gerar resumo: {str(e)}")

@melhorias_bp.route('/notificacoes/historico', methods=['GET'])
def obter_historico_notificacoes():
    """Obtém histórico de notificações"""
    try:
        usuario_id = request.args.get('usuario_id', 'default')
        periodo_dias = int(request.args.get('periodo_dias', 7))
        
        historico = notificacoes_service.obter_historico_notificacoes(usuario_id, periodo_dias)
        
        return APIResponse.success(
            data=historico,
            message="Histórico de notificações obtido"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao obter histórico: {str(e)}")

# =====================================
# DASHBOARD AVANÇADO
# =====================================

@melhorias_bp.route('/dashboard/principal', methods=['GET'])
def obter_dashboard_principal():
    """Obtém dados completos do dashboard principal"""
    try:
        usuario_id = request.args.get('usuario_id', 'default')
        
        dashboard_data = dashboard_service.obter_dashboard_principal(usuario_id)
        
        return APIResponse.success(
            data=dashboard_data,
            message="Dashboard principal carregado"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao carregar dashboard: {str(e)}")

@melhorias_bp.route('/dashboard/kpis', methods=['GET'])
def obter_kpis_dashboard():
    """Obtém apenas os KPIs principais"""
    try:
        dashboard_data = dashboard_service.obter_dashboard_principal()
        kpis = dashboard_data.get('kpis_principais', {})
        
        return APIResponse.success(
            data=kpis,
            message="KPIs obtidos"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao obter KPIs: {str(e)}")

@melhorias_bp.route('/dashboard/status-tempo-real', methods=['GET'])
def obter_status_tempo_real():
    """Obtém status em tempo real"""
    try:
        dashboard_data = dashboard_service.obter_dashboard_principal()
        status = dashboard_data.get('status_tempo_real', {})
        
        return APIResponse.success(
            data=status,
            message="Status em tempo real obtido"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao obter status: {str(e)}")

# =====================================
# ENDPOINTS DE DEMONSTRAÇÃO
# =====================================

@melhorias_bp.route('/demo/funcionalidades', methods=['GET'])
def demonstrar_funcionalidades():
    """Demonstra todas as funcionalidades avançadas"""
    try:
        # Simular dados para demonstração
        hoje = date.today()
        
        demo_data = {
            'agendamento_inteligente': {
                'exemplo': 'Sugestão de horários para Itajaí',
                'funcionalidade': 'Analisa agenda existente e sugere melhores horários'
            },
            'checklist_inteligente': {
                'exemplo': 'Checklist personalizado para visita MRS',
                'funcionalidade': 'Adapta checklist baseado no contexto da visita'
            },
            'contatos_inteligente': {
                'exemplo': 'Enriquecimento automático de dados',
                'funcionalidade': 'Consolida dados de múltiplas fontes com IA'
            },
            'relatorios_avancados': {
                'exemplo': 'Relatório executivo com insights automáticos',
                'funcionalidade': 'Análises inteligentes com previsões'
            },
            'notificacoes_inteligentes': {
                'exemplo': 'Alertas proativos de problemas',
                'funcionalidade': 'Monitoramento 24/7 com notificações contextuais'
            },
            'dashboard_avancado': {
                'exemplo': 'Métricas em tempo real com insights',
                'funcionalidade': 'Visão completa das operações'
            }
        }
        
        return APIResponse.success(
            data=demo_data,
            message="Demonstração das funcionalidades avançadas"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro na demonstração: {str(e)}")

@melhorias_bp.route('/status/melhorias', methods=['GET'])
def verificar_status_melhorias():
    """Verifica status de todas as melhorias implementadas"""
    try:
        status = {
            'timestamp': datetime.now().isoformat(),
            'servicos_ativos': {
                'agendamento_avancado': bool(mapa_service),
                'checklist_inteligente': True,
                'contatos_inteligente': bool(google_gemini_key),
                'relatorios_avancados': True,
                'notificacoes_alertas': True,
                'dashboard_avancado': True
            },
            'apis_externas': {
                'google_maps': bool(google_maps_key),
                'google_gemini': bool(google_gemini_key)
            },
            'funcionalidades_disponíveis': [
                'Sugestão inteligente de horários',
                'Otimização de rotas',
                'Checklist personalizado',
                'Validação de qualidade',
                'Enriquecimento de contatos',
                'Relatórios executivos',
                'Alertas proativos',
                'Dashboard em tempo real'
            ]
        }
        
        return APIResponse.success(
            data=status,
            message="Status das melhorias verificado"
        )
        
    except Exception as e:
        return APIResponse.error(f"Erro ao verificar status: {str(e)}")