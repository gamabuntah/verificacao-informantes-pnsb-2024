"""
API Routes para integração WhatsApp Business
"""

from flask import Blueprint, request, jsonify, current_app
from gestao_visitas.services.whatsapp_business import whatsapp_service
from gestao_visitas.models.agendamento import Visita
from gestao_visitas.db import db
import json

whatsapp_bp = Blueprint('whatsapp', __name__, url_prefix='/api/whatsapp')

@whatsapp_bp.route('/config/status', methods=['GET'])
def verificar_configuracao():
    """Verifica status da configuração WhatsApp"""
    try:
        status = whatsapp_service.verificar_configuracao()
        return jsonify(status)
    except Exception as e:
        return jsonify({
            'error': f'Erro ao verificar configuração: {str(e)}'
        }), 500

@whatsapp_bp.route('/send/template', methods=['POST'])
def enviar_template():
    """Envia mensagem usando template"""
    try:
        data = request.get_json()
        
        telefone = data.get('telefone')
        template_nome = data.get('template')
        variaveis = data.get('variaveis', {})
        visita_id = data.get('visita_id')
        
        if not telefone or not template_nome:
            return jsonify({
                'error': 'Telefone e template são obrigatórios'
            }), 400
        
        resultado = whatsapp_service.enviar_mensagem_template(
            telefone=telefone,
            template_nome=template_nome,
            variaveis=variaveis,
            visita_id=visita_id
        )
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({
            'error': f'Erro ao enviar mensagem: {str(e)}'
        }), 500

@whatsapp_bp.route('/send/agendamento/<int:visita_id>', methods=['POST'])
def enviar_agendamento(visita_id):
    """Envia mensagem automática de agendamento para uma visita"""
    try:
        visita = Visita.query.get(visita_id)
        if not visita:
            return jsonify({'error': 'Visita não encontrada'}), 404
        
        # Converter visita para dict
        visita_dict = visita.to_dict()
        
        # Adicionar dados extras necessários
        visita_dict.update({
            'pesquisador_responsavel': visita_dict.get('pesquisador_responsavel', 'Pesquisador IBGE'),
            'telefone': request.json.get('telefone') if request.json else None
        })
        
        resultado = whatsapp_service.enviar_agendamento_automatico(visita_dict)
        
        # Se sucesso, marcar que WhatsApp foi enviado
        if resultado.get('sucesso'):
            # Adicionar na observações que WhatsApp foi enviado
            obs_atual = visita.observacoes or ''
            nova_obs = f"{obs_atual}\n[WhatsApp] Agendamento enviado em {resultado.get('timestamp', '')}"
            visita.observacoes = nova_obs.strip()
            db.session.commit()
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({
            'error': f'Erro ao enviar agendamento: {str(e)}'
        }), 500

@whatsapp_bp.route('/send/lembrete/<int:visita_id>', methods=['POST'])
def enviar_lembrete(visita_id):
    """Envia lembrete automático para uma visita"""
    try:
        visita = Visita.query.get(visita_id)
        if not visita:
            return jsonify({'error': 'Visita não encontrada'}), 404
        
        visita_dict = visita.to_dict()
        visita_dict.update({
            'pesquisador_responsavel': visita_dict.get('pesquisador_responsavel', 'Pesquisador IBGE'),
            'telefone': request.json.get('telefone') if request.json else None
        })
        
        resultado = whatsapp_service.enviar_lembrete_automatico(visita_dict)
        
        if resultado.get('sucesso'):
            obs_atual = visita.observacoes or ''
            nova_obs = f"{obs_atual}\n[WhatsApp] Lembrete enviado em {resultado.get('timestamp', '')}"
            visita.observacoes = nova_obs.strip()
            db.session.commit()
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({
            'error': f'Erro ao enviar lembrete: {str(e)}'
        }), 500

@whatsapp_bp.route('/send/bulk/agendamentos', methods=['POST'])
def enviar_agendamentos_bulk():
    """Envia agendamentos em lote para múltiplas visitas"""
    try:
        data = request.get_json()
        visita_ids = data.get('visita_ids', [])
        telefones = data.get('telefones', {})  # {visita_id: telefone}
        
        if not visita_ids:
            return jsonify({'error': 'Lista de visitas é obrigatória'}), 400
        
        resultados = []
        
        for visita_id in visita_ids:
            try:
                visita = Visita.query.get(visita_id)
                if not visita:
                    resultados.append({
                        'visita_id': visita_id,
                        'sucesso': False,
                        'erro': 'Visita não encontrada'
                    })
                    continue
                
                visita_dict = visita.to_dict()
                visita_dict['telefone'] = telefones.get(str(visita_id))
                
                if not visita_dict['telefone']:
                    resultados.append({
                        'visita_id': visita_id,
                        'sucesso': False,
                        'erro': 'Telefone não fornecido'
                    })
                    continue
                
                resultado = whatsapp_service.enviar_agendamento_automatico(visita_dict)
                resultado['visita_id'] = visita_id
                
                # Atualizar observações se sucesso
                if resultado.get('sucesso'):
                    obs_atual = visita.observacoes or ''
                    nova_obs = f"{obs_atual}\n[WhatsApp] Agendamento em lote enviado em {resultado.get('timestamp', '')}"
                    visita.observacoes = nova_obs.strip()
                
                resultados.append(resultado)
                
            except Exception as e:
                resultados.append({
                    'visita_id': visita_id,
                    'sucesso': False,
                    'erro': str(e)
                })
        
        # Commit todas as mudanças
        db.session.commit()
        
        # Estatísticas
        sucessos = sum(1 for r in resultados if r.get('sucesso'))
        falhas = len(resultados) - sucessos
        
        return jsonify({
            'resultados': resultados,
            'estatisticas': {
                'total': len(resultados),
                'sucessos': sucessos,
                'falhas': falhas,
                'taxa_sucesso': round((sucessos / len(resultados)) * 100, 2) if resultados else 0
            }
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Erro no envio em lote: {str(e)}'
        }), 500

@whatsapp_bp.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Webhook para receber notificações do WhatsApp"""
    
    if request.method == 'GET':
        # Verificação do webhook (primeiro setup)
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if verify_token == whatsapp_service.webhook_verify_token:
            return challenge
        else:
            return 'Token de verificação inválido', 403
    
    elif request.method == 'POST':
        # Processar notificação recebida
        try:
            webhook_data = request.get_json()
            
            if not webhook_data:
                return jsonify({'error': 'Dados do webhook inválidos'}), 400
            
            resultado = whatsapp_service.processar_webhook(webhook_data)
            
            return jsonify(resultado)
            
        except Exception as e:
            current_app.logger.error(f'Erro no webhook WhatsApp: {str(e)}')
            return jsonify({'error': 'Erro interno'}), 500

@whatsapp_bp.route('/templates', methods=['GET'])
def listar_templates():
    """Lista templates disponíveis"""
    try:
        templates_info = {}
        
        for nome, template in whatsapp_service.templates.items():
            templates_info[nome] = {
                'nome': template.nome,
                'tipo': template.tipo.value,
                'categoria': template.categoria,
                'variaveis': template.variaveis,
                'corpo': template.corpo,
                'botoes': template.botoes
            }
        
        return jsonify({
            'templates': templates_info,
            'total': len(templates_info)
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Erro ao listar templates: {str(e)}'
        }), 500

@whatsapp_bp.route('/test/connection', methods=['POST'])
def testar_conexao():
    """Testa conexão com WhatsApp Business API"""
    try:
        data = request.get_json()
        telefone_teste = data.get('telefone_teste')
        
        if not telefone_teste:
            return jsonify({'error': 'Telefone de teste é obrigatório'}), 400
        
        # Enviar mensagem de teste simples
        variaveis = {
            'nome_informante': 'Teste',
            'nome_pesquisador': 'Sistema PNSB',
            'municipio': 'Teste',
            'tipo_pesquisa': 'Teste de Configuração',
            'data_visita': 'Data de Teste',
            'horario_visita': '10:00',
            'local_visita': 'Local de Teste'
        }
        
        resultado = whatsapp_service.enviar_mensagem_template(
            telefone=telefone_teste,
            template_nome='agendamento_inicial',
            variaveis=variaveis
        )
        
        return jsonify({
            'teste_realizado': True,
            'resultado': resultado,
            'configuracao': whatsapp_service.verificar_configuracao()
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Erro no teste: {str(e)}'
        }), 500

@whatsapp_bp.route('/stats', methods=['GET'])
def estatisticas_whatsapp():
    """Estatísticas de uso do WhatsApp"""
    try:
        # Aqui você pode implementar consultas ao banco de dados
        # para obter estatísticas reais de uso
        
        # Por enquanto, retorna dados simulados
        stats = {
            'mensagens_enviadas_hoje': 0,
            'mensagens_enviadas_semana': 0,
            'mensagens_enviadas_mes': 0,
            'taxa_entrega': 0.0,
            'taxa_leitura': 0.0,
            'taxa_resposta': 0.0,
            'templates_mais_usados': {},
            'horarios_melhor_engajamento': [],
            'municipios_mais_ativos': {}
        }
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({
            'error': f'Erro ao obter estatísticas: {str(e)}'
        }), 500