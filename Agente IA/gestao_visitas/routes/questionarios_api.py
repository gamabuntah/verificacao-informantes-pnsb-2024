"""
APIs para gestão de questionários obrigatórios do PNSB 2024
"""

from flask import Blueprint, request, jsonify, current_app
from flask_wtf.csrf import CSRFProtect
from gestao_visitas.db import db
from gestao_visitas.models.questionarios_obrigatorios import (
    QuestionarioObrigatorio, 
    EntidadeIdentificada, 
    ProgressoQuestionarios,
    EntidadePrioritariaUF
)
from gestao_visitas.config import MUNICIPIOS
MUNICIPIOS_PNSB = MUNICIPIOS
from datetime import datetime

questionarios_bp = Blueprint('questionarios', __name__)

# Inicializar CSRF
csrf = CSRFProtect()

@questionarios_bp.route('/questionarios-obrigatorios', methods=['GET'])
def listar_questionarios_obrigatorios():
    """Lista todos os questionários obrigatórios por município"""
    try:
        municipio = request.args.get('municipio')
        tipo_entidade = request.args.get('tipo_entidade')
        
        query = QuestionarioObrigatorio.query.filter_by(ativo=True)
        
        if municipio:
            query = query.filter_by(municipio=municipio)
        if tipo_entidade:
            query = query.filter_by(tipo_entidade=tipo_entidade)
        
        questionarios = query.order_by(
            QuestionarioObrigatorio.municipio,
            QuestionarioObrigatorio.tipo_entidade
        ).all()
        
        return jsonify({
            'success': True,
            'data': [q.to_dict() for q in questionarios],
            'total': len(questionarios)
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao listar questionários obrigatórios: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@questionarios_bp.route('/questionarios-obrigatorios', methods=['POST'])
def criar_questionario_obrigatorio():
    """Cria ou atualiza questionário obrigatório para uma entidade"""
    try:
        data = request.get_json()
        
        # Validações
        if not data.get('municipio') or data['municipio'] not in MUNICIPIOS_PNSB:
            return jsonify({'success': False, 'error': 'Município inválido'}), 400
        
        tipos_validos = ['prefeitura', 'empresa_terceirizada', 'entidade_catadores', 'empresa_nao_vinculada']
        if not data.get('tipo_entidade') or data['tipo_entidade'] not in tipos_validos:
            return jsonify({'success': False, 'error': 'Tipo de entidade inválido'}), 400
        
        # Verificar se já existe
        questionario_existente = QuestionarioObrigatorio.query.filter_by(
            municipio=data['municipio'],
            tipo_entidade=data['tipo_entidade']
        ).first()
        
        if questionario_existente:
            # Atualizar
            questionario_existente.mrs_obrigatorio = data.get('mrs_obrigatorio', False)
            questionario_existente.map_obrigatorio = data.get('map_obrigatorio', False)
            questionario_existente.observacoes = data.get('observacoes', '')
            questionario_existente.ativo = data.get('ativo', True)
            
            questionario = questionario_existente
        else:
            # Criar novo
            questionario = QuestionarioObrigatorio(
                municipio=data['municipio'],
                tipo_entidade=data['tipo_entidade'],
                mrs_obrigatorio=data.get('mrs_obrigatorio', False),
                map_obrigatorio=data.get('map_obrigatorio', False),
                observacoes=data.get('observacoes', ''),
                ativo=data.get('ativo', True)
            )
            db.session.add(questionario)
        
        db.session.commit()
        
        # Recalcular progresso do município
        ProgressoQuestionarios.calcular_progresso_municipio(data['municipio'])
        
        return jsonify({
            'success': True,
            'data': questionario.to_dict(),
            'message': 'Questionário obrigatório salvo com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar questionário obrigatório: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@questionarios_bp.route('/entidades-identificadas', methods=['GET'])
def listar_entidades_identificadas():
    """Lista entidades identificadas por município com suporte a filtros de prioridade"""
    try:
        municipio = request.args.get('municipio')
        tipo_entidade = request.args.get('tipo_entidade')
        prioridade = request.args.get('prioridade')  # Novo filtro de prioridade
        categoria_prioridade = request.args.get('categoria_prioridade')  # p1, p2, p3
        
        query = EntidadeIdentificada.query
        
        if municipio:
            query = query.filter_by(municipio=municipio)
        if tipo_entidade:
            query = query.filter_by(tipo_entidade=tipo_entidade)
        if prioridade:
            try:
                prioridade_int = int(prioridade)
                query = query.filter_by(prioridade=prioridade_int)
            except ValueError:
                return jsonify({'success': False, 'error': 'Prioridade deve ser um número (1, 2 ou 3)'}), 400
        if categoria_prioridade:
            if categoria_prioridade not in ['p1', 'p2', 'p3']:
                return jsonify({'success': False, 'error': 'Categoria de prioridade deve ser p1, p2 ou p3'}), 400
            query = query.filter_by(categoria_prioridade=categoria_prioridade)
        
        entidades = query.order_by(
            EntidadeIdentificada.prioridade,  # Ordenar por prioridade primeiro
            EntidadeIdentificada.municipio,
            EntidadeIdentificada.nome_entidade
        ).all()
        
        # Calcular estatísticas por prioridade se solicitado
        incluir_stats = request.args.get('incluir_stats', 'false').lower() == 'true'
        stats = None
        if incluir_stats:
            stats = EntidadeIdentificada.get_estatisticas_prioridades(municipio)
        
        response_data = {
            'success': True,
            'data': [e.to_dict() for e in entidades],
            'total': len(entidades)
        }
        
        if stats:
            response_data['estatisticas_prioridades'] = stats
        
        return jsonify(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Erro ao listar entidades identificadas: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@questionarios_bp.route('/entidades-identificadas', methods=['POST'])
def criar_entidade_identificada():
    """Registra nova entidade identificada"""
    try:
        data = request.get_json()
        
        # VALIDAÇÕES AJUSTADAS PARA NOVA LÓGICA
        # 1. Validar município (OBRIGATÓRIO estar na lista PNSB)
        municipio = data.get('municipio', '').strip()
        if not municipio or municipio not in MUNICIPIOS_PNSB:
            return jsonify({
                'success': False, 
                'error': f'Município inválido. Deve ser um dos 11 municípios do PNSB: {", ".join(MUNICIPIOS_PNSB)}'
            }), 400
        
        # 2. Validar nome da entidade
        nome_entidade = data.get('nome_entidade', '').strip()
        if not nome_entidade:
            return jsonify({'success': False, 'error': 'Nome da entidade é obrigatório'}), 400
        
        # 3. Validar tipo de entidade (incluindo prefeitura para casos especiais)
        tipos_validos = ['prefeitura', 'empresa_terceirizada', 'entidade_catadores', 'empresa_nao_vinculada']
        tipo_entidade = data.get('tipo_entidade', '').strip()
        if not tipo_entidade or tipo_entidade not in tipos_validos:
            return jsonify({
                'success': False, 
                'error': f'Tipo de entidade inválido. Valores válidos: {", ".join(tipos_validos)}'
            }), 400
        
        # 4. Validar se pelo menos um questionário é obrigatório
        mrs_obrigatorio = data.get('mrs_obrigatorio', False)
        map_obrigatorio = data.get('map_obrigatorio', False)
        if not mrs_obrigatorio and not map_obrigatorio:
            return jsonify({
                'success': False, 
                'error': 'Pelo menos um questionário (MRS ou MAP) deve ser obrigatório'
            }), 400
        
        # 5. VERIFICAR DUPLICAÇÃO: ENTIDADE + MUNICÍPIO (vínculo obrigatório)
        # Buscar por CNPJ + município primeiro (mais preciso)
        cnpj = data.get('cnpj', '').strip()
        entidade_existente = None
        
        if cnpj:
            entidade_existente = EntidadeIdentificada.query.filter_by(
                cnpj=cnpj,
                municipio=municipio
            ).first()
            
            if entidade_existente:
                return jsonify({
                    'success': False, 
                    'error': f'Entidade com CNPJ {cnpj} já cadastrada em {municipio}'
                }), 400
        
        # Se não tem CNPJ, verificar por nome + município + tipo
        entidade_existente = EntidadeIdentificada.query.filter_by(
            municipio=municipio,
            nome_entidade=nome_entidade,
            tipo_entidade=tipo_entidade
        ).first()
        
        if entidade_existente:
            return jsonify({
                'success': False, 
                'error': f'Entidade "{nome_entidade}" do tipo "{tipo_entidade}" já cadastrada em {municipio}'
            }), 400
        
        # DETERMINAR PRIORIDADE BASEADA NA FONTE E CONTEXTO
        # P3 é para entidades informativas (trabalho completo)
        fonte_identificacao = data.get('fonte_identificacao', 'inclusao_manual')
        eh_informativa = data.get('informativa', False)  # Campo explícito para P3
        
        if eh_informativa:
            prioridade = 3
            categoria_prioridade = 'p3'
            fonte_identificacao = 'trabalho_completo'
            observacoes_auto = "Entidade P3 - Informativa para trabalho completo (não obrigatória para metas PNSB)"
        elif fonte_identificacao in ['visita_prefeitura', 'indicacao_informante', 'pesquisa_campo', 'inclusao_manual']:
            prioridade = 2
            categoria_prioridade = 'p2'
            observacoes_auto = "Entidade P2 - Importante (obrigatória quando incluída)"
        else:
            prioridade = data.get('prioridade', 2)
            categoria_prioridade = data.get('categoria_prioridade', 'p2')
            observacoes_auto = ""
        
        # Combinar observações
        observacoes_usuario = data.get('observacoes', '').strip()
        observacoes_final = f"{observacoes_auto}\n{observacoes_usuario}".strip() if observacoes_usuario else observacoes_auto

        # CRIAR NOVA ENTIDADE COM VÍNCULO MUNICÍPIO GARANTIDO
        entidade = EntidadeIdentificada(
            municipio=municipio,           # VÍNCULO OBRIGATÓRIO VALIDADO
            tipo_entidade=tipo_entidade,   # TIPO VALIDADO
            nome_entidade=nome_entidade,   # NOME VALIDADO
            cnpj=cnpj or '',
            endereco=data.get('endereco', '').strip(),
            telefone=data.get('telefone', '').strip(),
            email=data.get('email', '').strip(),
            responsavel=data.get('responsavel', '').strip(),
            mrs_obrigatorio=mrs_obrigatorio,  # OBRIGATORIEDADE VALIDADA
            map_obrigatorio=map_obrigatorio,  # OBRIGATORIEDADE VALIDADA
            status_mrs=data.get('status_mrs', 'nao_iniciado'),  # nao_iniciado, respondido, validado_concluido, nao_aplicavel
            status_map=data.get('status_map', 'nao_iniciado'),  # nao_iniciado, respondido, validado_concluido, nao_aplicavel
            fonte_identificacao=fonte_identificacao,
            visita_id=data.get('visita_id'),
            observacoes=observacoes_final,
            # Campos de prioridade determinados automaticamente
            prioridade=prioridade,
            categoria_prioridade=categoria_prioridade,
            origem_lista_uf=data.get('origem_lista_uf', False),
            origem_prefeitura=data.get('origem_prefeitura', False),
            codigo_uf=data.get('codigo_uf', '')
        )
        
        # Aplicar lógica automática de prioridade se não foi especificada manualmente
        if 'prioridade' not in data or 'categoria_prioridade' not in data:
            entidade.definir_prioridade_automatica()
        
        db.session.add(entidade)
        db.session.commit()
        
        # Recalcular progresso do município
        ProgressoQuestionarios.calcular_progresso_municipio(data['municipio'])
        
        return jsonify({
            'success': True,
            'data': entidade.to_dict(),
            'message': 'Entidade cadastrada com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar entidade identificada: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@questionarios_bp.route('/entidades-identificadas/<int:entidade_id>', methods=['PUT'])
@csrf.exempt
def atualizar_entidade_identificada(entidade_id):
    """Atualiza status de questionários de uma entidade"""
    try:
        entidade = EntidadeIdentificada.query.get_or_404(entidade_id)
        data = request.get_json()
        
        # Atualizar campos permitidos
        campos_permitidos = [
            'nome_entidade', 'cnpj', 'endereco', 'telefone', 'email', 
            'responsavel', 'status_mrs', 'status_map', 'observacoes'
        ]
        
        for campo in campos_permitidos:
            if campo in data:
                setattr(entidade, campo, data[campo])
        
        db.session.commit()
        
        # Recalcular progresso do município
        ProgressoQuestionarios.calcular_progresso_municipio(entidade.municipio)
        
        return jsonify({
            'success': True,
            'data': entidade.to_dict(),
            'message': 'Entidade atualizada com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar entidade: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@questionarios_bp.route('/progresso-questionarios', methods=['GET'])
def obter_progresso_questionarios():
    """Obtém progresso de questionários por município"""
    try:
        municipio = request.args.get('municipio')
        
        if municipio:
            # Progresso de um município específico
            progresso = ProgressoQuestionarios.query.filter_by(municipio=municipio).first()
            if not progresso:
                # Calcular se não existir
                progresso = ProgressoQuestionarios.calcular_progresso_municipio(municipio)
            
            # Buscar detalhes dos questionários obrigatórios
            questionarios = QuestionarioObrigatorio.get_questionarios_municipio(municipio)
            entidades = EntidadeIdentificada.query.filter_by(municipio=municipio).all()
            
            return jsonify({
                'success': True,
                'data': {
                    'progresso': progresso.to_dict(),
                    'questionarios_obrigatorios': [q.to_dict() for q in questionarios],
                    'entidades_identificadas': [e.to_dict() for e in entidades]
                }
            })
        else:
            # Progresso de todos os municípios
            progressos = ProgressoQuestionarios.query.order_by(
                ProgressoQuestionarios.municipio
            ).all()
            
            # Se algum município não tem progresso, calcular
            municipios_com_progresso = {p.municipio for p in progressos}
            for municipio in MUNICIPIOS_PNSB:
                if municipio not in municipios_com_progresso:
                    novo_progresso = ProgressoQuestionarios.calcular_progresso_municipio(municipio)
                    progressos.append(novo_progresso)
            
            return jsonify({
                'success': True,
                'data': [p.to_dict() for p in progressos],
                'resumo': {
                    'total_municipios': len(MUNICIPIOS_PNSB),
                    'municipios_concluidos': len([p for p in progressos if p.status_geral == 'concluido']),
                    'municipios_em_andamento': len([p for p in progressos if p.status_geral == 'em_andamento']),
                    'municipios_nao_iniciados': len([p for p in progressos if p.status_geral == 'nao_iniciado'])
                }
            })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter progresso de questionários: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@questionarios_bp.route('/recalcular-progresso', methods=['POST'])
def recalcular_progresso():
    """Recalcula progresso de questionários para todos os municípios"""
    try:
        # Aceitar tanto JSON quanto form data
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.form.to_dict()
        
        municipio = data.get('municipio')
        
        current_app.logger.info(f"🔄 Recalculando progresso - Município: {municipio or 'todos'}")
        
        if municipio:
            # Recalcular apenas um município
            if municipio not in MUNICIPIOS_PNSB:
                return jsonify({'success': False, 'error': 'Município inválido'}), 400
                
            progresso = ProgressoQuestionarios.calcular_progresso_municipio(municipio)
            municipios_processados = 1
            
            return jsonify({
                'success': True,
                'data': progresso.to_dict() if progresso else None,
                'municipios_processados': municipios_processados,
                'message': f'Progresso recalculado para {municipio}'
            })
        else:
            # Recalcular todos os municípios
            progressos = []
            municipios_processados = 0
            
            for municipio_atual in MUNICIPIOS_PNSB:
                try:
                    progresso = ProgressoQuestionarios.calcular_progresso_municipio(municipio_atual)
                    if progresso:
                        progressos.append(progresso)
                    municipios_processados += 1
                except Exception as e:
                    current_app.logger.warning(f"Erro ao processar {municipio_atual}: {str(e)}")
                    continue
            
            return jsonify({
                'success': True,
                'data': [p.to_dict() for p in progressos if p],
                'municipios_processados': municipios_processados,
                'message': f'Progresso recalculado para {municipios_processados} municípios'
            })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao recalcular progresso: {str(e)}")
        return jsonify({
            'success': False, 
            'error': f'Erro ao recalcular progresso: {str(e)}',
            'municipios_processados': 0
        }), 500

@questionarios_bp.route('/entidades-por-municipio', methods=['GET'])
def listar_entidades_por_municipio():
    """API para o mapa de progresso - entidades agrupadas por município"""
    try:
        resultado = {}
        
        for municipio in MUNICIPIOS_PNSB:
            entidades = EntidadeIdentificada.query.filter_by(municipio=municipio).all()
            resultado[municipio] = [e.to_dict() for e in entidades]
        
        return jsonify(resultado)
        
    except Exception as e:
        current_app.logger.error(f"Erro ao listar entidades por município: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@questionarios_bp.route('/entidades-identificadas', methods=['GET']) 
def listar_todas_entidades_identificadas():
    """API para o mapa de progresso - todas as entidades identificadas"""
    try:
        entidades = EntidadeIdentificada.query.order_by(
            EntidadeIdentificada.prioridade,
            EntidadeIdentificada.municipio,
            EntidadeIdentificada.nome_entidade
        ).all()
        
        return jsonify({
            'success': True,
            'entidades': [e.to_dict() for e in entidades],
            'total': len(entidades)
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao listar entidades identificadas: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@questionarios_bp.route('/progresso-municipio/<municipio>', methods=['GET'])
def obter_progresso_municipio(municipio):
    """API para obter progresso de um município específico"""
    try:
        if municipio not in MUNICIPIOS_PNSB:
            return jsonify({'success': False, 'error': 'Município inválido'}), 400
            
        progresso = ProgressoQuestionarios.calcular_progresso_municipio(municipio)
        
        if progresso:
            return jsonify({
                'success': True,
                'municipio': municipio,
                'percentual_geral': progresso.percentual_geral,
                'progresso': progresso.to_dict()
            })
        else:
            return jsonify({
                'success': True,
                'municipio': municipio,
                'percentual_geral': 0,
                'progresso': None
            })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter progresso de {municipio}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@questionarios_bp.route('/entidades-prioritarias-uf', methods=['GET'])
def listar_entidades_prioritarias_uf():
    """Lista entidades prioritárias da UF"""
    try:
        municipio = request.args.get('municipio')
        tipo_entidade = request.args.get('tipo_entidade')
        processado = request.args.get('processado')
        
        query = EntidadePrioritariaUF.query
        
        if municipio:
            query = query.filter_by(municipio=municipio)
        if tipo_entidade:
            query = query.filter_by(tipo_entidade=tipo_entidade)
        if processado is not None:
            query = query.filter_by(processado=processado.lower() == 'true')
        
        entidades = query.order_by(
            EntidadePrioritariaUF.prioridade_uf,
            EntidadePrioritariaUF.municipio,
            EntidadePrioritariaUF.nome_entidade
        ).all()
        
        return jsonify({
            'success': True,
            'data': [e.to_dict() for e in entidades],
            'total': len(entidades),
            'resumo': {
                'total_entidades': len(entidades),
                'processadas': len([e for e in entidades if e.processado]),
                'nao_processadas': len([e for e in entidades if not e.processado]),
                'mrs_obrigatorios': len([e for e in entidades if e.mrs_obrigatorio]),
                'map_obrigatorios': len([e for e in entidades if e.map_obrigatorio])
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao listar entidades prioritárias UF: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@questionarios_bp.route('/entidades-prioritarias-uf', methods=['POST'])
def criar_entidade_prioritaria_uf():
    """Cria nova entidade prioritária da UF"""
    try:
        data = request.get_json()
        
        # Validações
        campos_obrigatorios = ['codigo_uf', 'municipio', 'nome_entidade', 'tipo_entidade']
        for campo in campos_obrigatorios:
            if not data.get(campo):
                return jsonify({'success': False, 'error': f'{campo} é obrigatório'}), 400
        
        if data['municipio'] not in MUNICIPIOS_PNSB:
            return jsonify({'success': False, 'error': 'Município inválido'}), 400
        
        tipos_validos = ['empresa_terceirizada', 'entidade_catadores', 'empresa_nao_vinculada']
        if data['tipo_entidade'] not in tipos_validos:
            return jsonify({'success': False, 'error': 'Tipo de entidade inválido'}), 400
        
        # Verificar se código UF já existe
        if EntidadePrioritariaUF.query.filter_by(codigo_uf=data['codigo_uf']).first():
            return jsonify({'success': False, 'error': 'Código UF já existe'}), 400
        
        # Criar entidade
        entidade = EntidadePrioritariaUF(
            codigo_uf=data['codigo_uf'],
            municipio=data['municipio'],
            regiao=data.get('regiao', ''),
            nome_entidade=data['nome_entidade'],
            tipo_entidade=data['tipo_entidade'],
            cnpj=data.get('cnpj', ''),
            endereco_completo=data.get('endereco_completo', ''),
            mrs_obrigatorio=data.get('mrs_obrigatorio', False),
            map_obrigatorio=data.get('map_obrigatorio', False),
            motivo_mrs=data.get('motivo_mrs', ''),
            motivo_map=data.get('motivo_map', ''),
            categoria_uf=data.get('categoria_uf', ''),
            subcategoria_uf=data.get('subcategoria_uf', ''),
            prioridade_uf=data.get('prioridade_uf', 1),
            telefone_uf=data.get('telefone_uf', ''),
            email_uf=data.get('email_uf', ''),
            responsavel_uf=data.get('responsavel_uf', ''),
            observacoes_uf=data.get('observacoes_uf', ''),
            arquivo_origem=data.get('arquivo_origem', 'manual'),
            linha_origem=data.get('linha_origem')
        )
        
        db.session.add(entidade)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': entidade.to_dict(),
            'message': 'Entidade prioritária criada com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar entidade prioritária UF: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@questionarios_bp.route('/entidades-prioritarias-uf/<int:entidade_id>', methods=['PUT'])
def atualizar_entidade_prioritaria_uf(entidade_id):
    """Atualiza entidade prioritária da UF"""
    try:
        entidade = EntidadePrioritariaUF.query.get_or_404(entidade_id)
        data = request.get_json()
        
        # Atualizar campos permitidos
        campos_permitidos = [
            'municipio', 'regiao', 'nome_entidade', 'tipo_entidade', 'cnpj',
            'endereco_completo', 'mrs_obrigatorio', 'map_obrigatorio',
            'motivo_mrs', 'motivo_map', 'categoria_uf', 'subcategoria_uf',
            'prioridade_uf', 'telefone_uf', 'email_uf', 'responsavel_uf',
            'observacoes_uf'
        ]
        
        for campo in campos_permitidos:
            if campo in data:
                setattr(entidade, campo, data[campo])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': entidade.to_dict(),
            'message': 'Entidade prioritária atualizada com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar entidade prioritária UF: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@questionarios_bp.route('/processar-entidade-prioritaria/<int:entidade_id>', methods=['POST'])
def processar_entidade_prioritaria(entidade_id):
    """Processa uma entidade prioritária (converte para EntidadeIdentificada)"""
    try:
        entidade = EntidadePrioritariaUF.processar_entidade_prioritaria(entidade_id)
        
        if not entidade:
            return jsonify({
                'success': False,
                'error': 'Entidade não encontrada ou já processada'
            }), 400
        
        # Recalcular progresso do município
        ProgressoQuestionarios.calcular_progresso_municipio(entidade.municipio)
        
        return jsonify({
            'success': True,
            'data': entidade.to_dict(),
            'message': 'Entidade processada com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao processar entidade prioritária: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@questionarios_bp.route('/processar-todas-prioritarias', methods=['POST'])
def processar_todas_entidades_prioritarias():
    """Processa todas as entidades prioritárias não processadas"""
    try:
        data = request.get_json() or {}
        municipio = data.get('municipio')
        
        current_app.logger.info(f"Iniciando processamento de entidades prioritárias. Município: {municipio}")
        
        if municipio:
            # Processar apenas um município
            if municipio not in MUNICIPIOS_PNSB:
                return jsonify({'success': False, 'error': 'Município inválido'}), 400
            
            entidades_nao_processadas = EntidadePrioritariaUF.query.filter_by(
                municipio=municipio,
                processado=False
            ).all()
        else:
            # Processar todas
            entidades_nao_processadas = EntidadePrioritariaUF.query.filter_by(
                processado=False
            ).all()
        
        current_app.logger.info(f"Encontradas {len(entidades_nao_processadas)} entidades não processadas")
        
        if len(entidades_nao_processadas) == 0:
            return jsonify({
                'success': True,
                'data': [],
                'total_processadas': 0,
                'municipios_afetados': [],
                'message': 'Nenhuma entidade pendente para processar'
            })
        
        entidades_processadas = []
        erros_processamento = []
        
        for entidade_uf in entidades_nao_processadas:
            try:
                current_app.logger.info(f"Processando entidade {entidade_uf.id}: {entidade_uf.nome_entidade}")
                entidade = EntidadePrioritariaUF.processar_entidade_prioritaria(entidade_uf.id)
                if entidade:
                    entidades_processadas.append(entidade)
                    current_app.logger.info(f"Entidade {entidade_uf.id} processada com sucesso")
                else:
                    erros_processamento.append(f"Entidade {entidade_uf.nome_entidade}: não foi possível processar")
            except Exception as e:
                current_app.logger.error(f"Erro ao processar entidade {entidade_uf.id}: {str(e)}")
                erros_processamento.append(f"Entidade {entidade_uf.nome_entidade}: {str(e)}")
                continue
        
        # Recalcular progresso dos municípios afetados
        municipios_afetados = list(set([e.municipio for e in entidades_processadas]))
        for municipio_afetado in municipios_afetados:
            ProgressoQuestionarios.calcular_progresso_municipio(municipio_afetado)
        
        current_app.logger.info(f"Processamento concluído: {len(entidades_processadas)} entidades processadas")
        
        response_data = {
            'success': True,
            'data': [e.to_dict() for e in entidades_processadas],
            'total_processadas': len(entidades_processadas),
            'municipios_afetados': municipios_afetados,
            'message': f'{len(entidades_processadas)} entidades processadas com sucesso'
        }
        
        if erros_processamento:
            response_data['erros'] = erros_processamento
            response_data['total_erros'] = len(erros_processamento)
        
        return jsonify(response_data)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao processar todas entidades prioritárias: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@questionarios_bp.route('/importar-lista-uf', methods=['POST'])
def importar_lista_uf():
    """Importa lista de entidades prioritárias da UF via CSV"""
    try:
        if 'arquivo' not in request.files:
            return jsonify({'success': False, 'error': 'Arquivo não fornecido'}), 400
        
        arquivo = request.files['arquivo']
        if arquivo.filename == '':
            return jsonify({'success': False, 'error': 'Nenhum arquivo selecionado'}), 400
        
        # Validar extensão
        if not arquivo.filename.lower().endswith('.csv'):
            return jsonify({'success': False, 'error': 'Arquivo deve ser CSV'}), 400
        
        # Ler arquivo CSV
        import csv
        import io
        
        stream = io.StringIO(arquivo.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.DictReader(stream)
        
        entidades_criadas = []
        entidades_atualizadas = []
        erros = []
        
        for linha_num, linha in enumerate(csv_input, start=2):  # Começar da linha 2 (pular header)
            try:
                # Campos obrigatórios
                if not all([linha.get('codigo_uf'), linha.get('municipio'), 
                           linha.get('nome_entidade'), linha.get('tipo_entidade')]):
                    erros.append(f"Linha {linha_num}: Campos obrigatórios faltando")
                    continue
                
                # Verificar se entidade já existe
                entidade_existente = EntidadePrioritariaUF.query.filter_by(
                    codigo_uf=linha['codigo_uf']
                ).first()
                
                if entidade_existente:
                    # Atualizar
                    for campo, valor in linha.items():
                        if hasattr(entidade_existente, campo) and valor:
                            if campo in ['mrs_obrigatorio', 'map_obrigatorio']:
                                setattr(entidade_existente, campo, valor.lower() in ['true', '1', 'sim', 'yes'])
                            elif campo in ['prioridade_uf', 'linha_origem']:
                                setattr(entidade_existente, campo, int(valor) if valor else None)
                            else:
                                setattr(entidade_existente, campo, valor)
                    
                    entidade_existente.arquivo_origem = arquivo.filename
                    entidade_existente.linha_origem = linha_num
                    entidades_atualizadas.append(entidade_existente)
                    
                else:
                    # Criar nova
                    entidade = EntidadePrioritariaUF(
                        codigo_uf=linha['codigo_uf'],
                        municipio=linha['municipio'],
                        regiao=linha.get('regiao', ''),
                        nome_entidade=linha['nome_entidade'],
                        tipo_entidade=linha['tipo_entidade'],
                        cnpj=linha.get('cnpj', ''),
                        endereco_completo=linha.get('endereco_completo', ''),
                        mrs_obrigatorio=linha.get('mrs_obrigatorio', '').lower() in ['true', '1', 'sim', 'yes'],
                        map_obrigatorio=linha.get('map_obrigatorio', '').lower() in ['true', '1', 'sim', 'yes'],
                        motivo_mrs=linha.get('motivo_mrs', ''),
                        motivo_map=linha.get('motivo_map', ''),
                        categoria_uf=linha.get('categoria_uf', ''),
                        subcategoria_uf=linha.get('subcategoria_uf', ''),
                        prioridade_uf=int(linha.get('prioridade_uf', 1)) if linha.get('prioridade_uf') else 1,
                        telefone_uf=linha.get('telefone_uf', ''),
                        email_uf=linha.get('email_uf', ''),
                        responsavel_uf=linha.get('responsavel_uf', ''),
                        observacoes_uf=linha.get('observacoes_uf', ''),
                        arquivo_origem=arquivo.filename,
                        linha_origem=linha_num
                    )
                    
                    db.session.add(entidade)
                    entidades_criadas.append(entidade)
                    
            except Exception as e:
                erros.append(f"Linha {linha_num}: {str(e)}")
                continue
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'entidades_criadas': len(entidades_criadas),
            'entidades_atualizadas': len(entidades_atualizadas),
            'erros': erros,
            'total_erros': len(erros),
            'message': f'Importação concluída: {len(entidades_criadas)} criadas, {len(entidades_atualizadas)} atualizadas'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao importar lista UF: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@questionarios_bp.route('/importar-csv-simples', methods=['POST'])
def importar_csv_simples():
    """Importa CSV simples com apenas Município, CNPJ, Razão Social"""
    try:
        if 'arquivo' not in request.files:
            return jsonify({'success': False, 'error': 'Arquivo não fornecido'}), 400
        
        arquivo = request.files['arquivo']
        if arquivo.filename == '':
            return jsonify({'success': False, 'error': 'Nenhum arquivo selecionado'}), 400
        
        # Validar extensão
        if not arquivo.filename.lower().endswith('.csv'):
            return jsonify({'success': False, 'error': 'Arquivo deve ser CSV'}), 400
        
        # Obter parâmetros do formulário
        tipo_entidade = request.form.get('tipo_entidade') or ''  # Pode ficar vazio
        tipo_importacao = request.form.get('tipo_importacao')  # 'MRS' ou 'MAP'
        
        if not tipo_importacao or tipo_importacao not in ['MRS', 'MAP']:
            return jsonify({'success': False, 'error': 'Tipo de importação deve ser MRS ou MAP'}), 400
        
        # Definir obrigatoriedade baseado no tipo de importação
        mrs_padrao = tipo_importacao == 'MRS'
        map_padrao = tipo_importacao == 'MAP'
        
        # Ler arquivo CSV com detecção automática de encoding
        import csv
        import io
        
        # Ler conteúdo do arquivo como bytes
        arquivo_bytes = arquivo.stream.read()
        
        # Tentar detectar encoding automaticamente
        encoding_detectado = 'utf-8'
        try:
            import chardet
            detection_result = chardet.detect(arquivo_bytes)
            if detection_result and detection_result.get('encoding'):
                encoding_detectado = detection_result['encoding']
        except ImportError:
            # Chardet não disponível, usar lista padrão
            pass
        
        # Lista de encodings para tentar em ordem de prioridade
        encodings_para_tentar = [encoding_detectado, 'utf-8', 'iso-8859-1', 'windows-1252', 'cp1252', 'latin1']
        
        stream = None
        erro_encoding = None
        
        for enc in encodings_para_tentar:
            try:
                # Tentar decodificar com o encoding atual
                conteudo_texto = arquivo_bytes.decode(enc)
                stream = io.StringIO(conteudo_texto, newline=None)
                current_app.logger.info(f"Arquivo CSV decodificado com encoding: {enc}")
                break
            except (UnicodeDecodeError, UnicodeError) as e:
                erro_encoding = str(e)
                continue
        
        if stream is None:
            return jsonify({
                'success': False, 
                'error': f'Erro de codificação do arquivo CSV. O arquivo contém caracteres não suportados. Soluções: 1) Salve o arquivo como UTF-8 (no Excel: Salvar Como > Mais opções > Codificação: UTF-8), 2) Use um editor de texto como Notepad++ para converter o encoding, 3) Verifique se há caracteres especiais nos nomes. Detalhes técnicos: {erro_encoding}'
            }), 400
        
        csv_input = csv.DictReader(stream)
        
        entidades_criadas = []
        entidades_atualizadas = []
        erros = []
        
        # Verificar se cabeçalho está correto
        campos_esperados = ['Município', 'CNPJ', 'Razão Social']
        campos_csv = list(csv_input.fieldnames)
        
        if not all(campo in campos_csv for campo in campos_esperados):
            return jsonify({
                'success': False, 
                'error': f'Cabeçalho incorreto. Esperado: {", ".join(campos_esperados)}. Encontrado: {", ".join(campos_csv)}'
            }), 400
        
        for linha_num, linha in enumerate(csv_input, start=2):  # Começar da linha 2 (pular header)
            try:
                # Campos obrigatórios
                municipio = linha.get('Município', '').strip()
                cnpj = linha.get('CNPJ', '').strip()
                razao_social = linha.get('Razão Social', '').strip()
                
                if not all([municipio, cnpj, razao_social]):
                    erros.append(f"Linha {linha_num}: Município, CNPJ e Razão Social são obrigatórios")
                    continue
                
                # Verificar se município é válido
                if municipio not in MUNICIPIOS_PNSB:
                    erros.append(f"Linha {linha_num}: Município '{municipio}' não é válido para PNSB")
                    continue
                
                # Gerar código UF único baseado no CNPJ
                codigo_uf = f"SIMPLES_{cnpj.replace('.', '').replace('/', '').replace('-', '')}"
                
                # Verificar se entidade já existe
                entidade_existente = EntidadePrioritariaUF.query.filter_by(
                    codigo_uf=codigo_uf
                ).first()
                
                if entidade_existente:
                    # Atualizar dados básicos
                    entidade_existente.municipio = municipio
                    entidade_existente.nome_entidade = razao_social
                    entidade_existente.cnpj = cnpj
                    if tipo_entidade:  # Só atualiza se foi fornecido
                        entidade_existente.tipo_entidade = tipo_entidade
                    entidade_existente.mrs_obrigatorio = mrs_padrao
                    entidade_existente.map_obrigatorio = map_padrao
                    entidade_existente.arquivo_origem = arquivo.filename
                    entidade_existente.linha_origem = linha_num
                    entidade_existente.prioridade_uf = 1  # Prioridade 1 para entidades MRS/MAP
                    entidade_existente.categoria_uf = f'Importação {tipo_importacao}'
                    entidade_existente.subcategoria_uf = f'{tipo_entidade or "A definir"} - {tipo_importacao}'
                    entidade_existente.motivo_mrs = f'Importação {tipo_importacao}' + (f' - {tipo_entidade}' if tipo_entidade else '') if mrs_padrao else ''
                    entidade_existente.motivo_map = f'Importação {tipo_importacao}' + (f' - {tipo_entidade}' if tipo_entidade else '') if map_padrao else ''
                    entidade_existente.observacoes_uf = f'Importado via CSV simples {tipo_importacao} - tipo de entidade e outros dados podem ser editados manualmente'
                    entidade_existente.importado_em = datetime.now()
                    
                    entidades_atualizadas.append(entidade_existente)
                    
                else:
                    # Criar nova entidade
                    entidade = EntidadePrioritariaUF(
                        codigo_uf=codigo_uf,
                        municipio=municipio,
                        regiao='',
                        nome_entidade=razao_social,
                        tipo_entidade=tipo_entidade or '',  # Vazio se não informado
                        cnpj=cnpj,
                        endereco_completo='',
                        mrs_obrigatorio=mrs_padrao,
                        map_obrigatorio=map_padrao,
                        motivo_mrs=f'Importação {tipo_importacao}' + (f' - {tipo_entidade}' if tipo_entidade else '') if mrs_padrao else '',
                        motivo_map=f'Importação {tipo_importacao}' + (f' - {tipo_entidade}' if tipo_entidade else '') if map_padrao else '',
                        categoria_uf=f'Importação {tipo_importacao}',
                        subcategoria_uf=f'{tipo_entidade or "A definir"} - {tipo_importacao}',
                        prioridade_uf=1,  # Prioridade 1 para entidades MRS/MAP
                        telefone_uf='',
                        email_uf='',
                        responsavel_uf='',
                        observacoes_uf=f'Importado via CSV simples {tipo_importacao} - tipo de entidade e outros dados podem ser editados manualmente',
                        arquivo_origem=arquivo.filename,
                        linha_origem=linha_num,
                        importado_em=datetime.now()
                    )
                    
                    db.session.add(entidade)
                    entidades_criadas.append(entidade)
                    
            except Exception as e:
                erros.append(f"Linha {linha_num}: {str(e)}")
                continue
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'entidades_criadas': len(entidades_criadas),
            'entidades_atualizadas': len(entidades_atualizadas),
            'erros': erros,
            'total_erros': len(erros),
            'message': f'Importação simples concluída: {len(entidades_criadas)} criadas, {len(entidades_atualizadas)} atualizadas'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao importar CSV simples: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@questionarios_bp.route('/entidade-prioritaria/<int:entidade_id>', methods=['DELETE'])
def excluir_entidade_prioritaria(entidade_id):
    """Exclui uma entidade prioritária específica"""
    try:
        entidade = EntidadePrioritariaUF.query.get(entidade_id)
        if not entidade:
            return jsonify({'success': False, 'error': 'Entidade não encontrada'}), 404
        
        nome_entidade = entidade.nome_entidade
        
        # Excluir a entidade
        db.session.delete(entidade)
        db.session.commit()
        
        current_app.logger.info(f"Entidade prioritária excluída: {nome_entidade} (ID: {entidade_id})")
        
        return jsonify({
            'success': True,
            'message': f'Entidade "{nome_entidade}" excluída com sucesso',
            'entidade_id': entidade_id
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao excluir entidade prioritária {entidade_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@questionarios_bp.route('/excluir-todas-entidades', methods=['DELETE'])
def excluir_todas_entidades():
    """Exclui todas as entidades prioritárias"""
    try:
        # Contar entidades antes da exclusão
        total_entidades = EntidadePrioritariaUF.query.count()
        
        if total_entidades == 0:
            return jsonify({
                'success': True,
                'message': 'Não há entidades para excluir',
                'entidades_excluidas': 0
            })
        
        # Excluir todas as entidades
        EntidadePrioritariaUF.query.delete()
        db.session.commit()
        
        current_app.logger.info(f"Todas as entidades prioritárias foram excluídas: {total_entidades} entidades")
        
        return jsonify({
            'success': True,
            'message': f'{total_entidades} entidades excluídas com sucesso',
            'entidades_excluidas': total_entidades
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao excluir todas as entidades: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== NOVOS ENDPOINTS PARA SISTEMA DE PRIORIDADES =====

@questionarios_bp.route('/entidades-por-prioridade', methods=['GET'])
def listar_entidades_por_prioridade():
    """Lista entidades agrupadas por prioridade (P1, P2, P3)"""
    try:
        municipio = request.args.get('municipio')
        incluir_detalhes = request.args.get('incluir_detalhes', 'false').lower() == 'true'
        
        # Buscar entidades com filtro opcional de município
        entidades_p1 = EntidadeIdentificada.get_entidades_por_prioridade(municipio, 1)
        entidades_p2 = EntidadeIdentificada.get_entidades_por_prioridade(municipio, 2)
        entidades_p3 = EntidadeIdentificada.get_entidades_por_prioridade(municipio, 3)
        
        # Preparar resposta
        response_data = {
            'success': True,
            'data': {
                'p1': {
                    'descricao': 'Crítica (Prefeituras + Lista UF)',
                    'total': len(entidades_p1),
                    'entidades': [e.to_dict() for e in entidades_p1] if incluir_detalhes else []
                },
                'p2': {
                    'descricao': 'Importante (Identificadas em campo)',
                    'total': len(entidades_p2),
                    'entidades': [e.to_dict() for e in entidades_p2] if incluir_detalhes else []
                },
                'p3': {
                    'descricao': 'Opcional (Recursos disponíveis)',
                    'total': len(entidades_p3),
                    'entidades': [e.to_dict() for e in entidades_p3] if incluir_detalhes else []
                }
            },
            'resumo': {
                'total_geral': len(entidades_p1) + len(entidades_p2) + len(entidades_p3),
                'p1_total': len(entidades_p1),
                'p2_total': len(entidades_p2),
                'p3_total': len(entidades_p3)
            }
        }
        
        # Adicionar estatísticas se solicitado
        if request.args.get('incluir_stats', 'false').lower() == 'true':
            stats = EntidadeIdentificada.get_estatisticas_prioridades(municipio)
            response_data['estatisticas'] = stats
        
        return jsonify(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Erro ao listar entidades por prioridade: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@questionarios_bp.route('/dashboard-prioridades', methods=['GET'])
def dashboard_prioridades():
    """Dashboard consolidado com métricas de todas as prioridades"""
    try:
        municipio = request.args.get('municipio')
        
        if municipio and municipio not in MUNICIPIOS_PNSB:
            return jsonify({'success': False, 'error': 'Município inválido'}), 400
        
        # Se municipio específico, retornar dados daquele município
        if municipio:
            progresso = ProgressoQuestionarios.query.filter_by(municipio=municipio).first()
            if not progresso:
                progresso = ProgressoQuestionarios.calcular_progresso_municipio(municipio)
            
            return jsonify({
                'success': True,
                'municipio': municipio,
                'data': progresso.to_dict()
            })
        else:
            # Dashboard geral - todos os municípios
            dados_municipios = []
            totais_gerais = {
                'municipios_total': len(MUNICIPIOS_PNSB),
                'p1_total_entidades': 0,
                'p1_concluidas': 0,
                'p2_total_entidades': 0,
                'p2_concluidas': 0,
                'p3_total_entidades': 0,
                'p3_concluidas': 0,
                'municipios_p1_concluidos': 0,
                'municipios_em_andamento': 0,
                'municipios_nao_iniciados': 0
            }
            
            for municipio_nome in MUNICIPIOS_PNSB:
                progresso = ProgressoQuestionarios.query.filter_by(municipio=municipio_nome).first()
                if not progresso:
                    progresso = ProgressoQuestionarios.calcular_progresso_municipio(municipio_nome)
                
                dados_municipios.append(progresso.to_dict())
                
                # Acumular totais
                totais_gerais['p1_total_entidades'] += progresso.p1_total_entidades
                totais_gerais['p1_concluidas'] += progresso.p1_mrs_concluidos + progresso.p1_map_concluidos
                totais_gerais['p2_total_entidades'] += progresso.p2_total_entidades
                totais_gerais['p2_concluidas'] += progresso.p2_mrs_concluidos + progresso.p2_map_concluidos
                totais_gerais['p3_total_entidades'] += progresso.p3_total_entidades
                totais_gerais['p3_concluidas'] += progresso.p3_mrs_concluidos + progresso.p3_map_concluidos
                
                # Contar status dos municípios
                if progresso.status_p1 == 'concluido':
                    totais_gerais['municipios_p1_concluidos'] += 1
                elif progresso.status_geral == 'em_andamento':
                    totais_gerais['municipios_em_andamento'] += 1
                else:
                    totais_gerais['municipios_nao_iniciados'] += 1
            
            # Calcular percentuais gerais
            totais_gerais['p1_percentual'] = (totais_gerais['p1_concluidas'] / (totais_gerais['p1_total_entidades'] * 2) * 100) if totais_gerais['p1_total_entidades'] > 0 else 0
            totais_gerais['p2_percentual'] = (totais_gerais['p2_concluidas'] / (totais_gerais['p2_total_entidades'] * 2) * 100) if totais_gerais['p2_total_entidades'] > 0 else 0
            totais_gerais['p3_percentual'] = (totais_gerais['p3_concluidas'] / (totais_gerais['p3_total_entidades'] * 2) * 100) if totais_gerais['p3_total_entidades'] > 0 else 0
            
            return jsonify({
                'success': True,
                'tipo': 'dashboard_geral',
                'data': dados_municipios,
                'totais_gerais': totais_gerais,
                'timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        current_app.logger.error(f"Erro no dashboard de prioridades: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@questionarios_bp.route('/atualizar-prioridade/<int:entidade_id>', methods=['PUT'])
def atualizar_prioridade_entidade(entidade_id):
    """Atualiza a prioridade de uma entidade específica"""
    try:
        entidade = EntidadeIdentificada.query.get_or_404(entidade_id)
        data = request.get_json()
        
        # Validar nova prioridade
        nova_prioridade = data.get('prioridade')
        nova_categoria = data.get('categoria_prioridade')
        
        if nova_prioridade is not None:
            if nova_prioridade not in [1, 2, 3]:
                return jsonify({'success': False, 'error': 'Prioridade deve ser 1, 2 ou 3'}), 400
            entidade.prioridade = nova_prioridade
        
        if nova_categoria is not None:
            if nova_categoria not in ['p1', 'p2', 'p3']:
                return jsonify({'success': False, 'error': 'Categoria deve ser p1, p2 ou p3'}), 400
            entidade.categoria_prioridade = nova_categoria
        
        # Atualizar outros campos de prioridade se fornecidos
        if 'origem_lista_uf' in data:
            entidade.origem_lista_uf = data['origem_lista_uf']
        if 'origem_prefeitura' in data:
            entidade.origem_prefeitura = data['origem_prefeitura']
        if 'mrs_obrigatorio' in data:
            entidade.mrs_obrigatorio = data['mrs_obrigatorio']
        if 'map_obrigatorio' in data:
            entidade.map_obrigatorio = data['map_obrigatorio']
        
        # Se não foi especificada prioridade manualmente, aplicar lógica automática
        if nova_prioridade is None and nova_categoria is None:
            entidade.definir_prioridade_automatica()
        
        db.session.commit()
        
        # Recalcular progresso do município
        ProgressoQuestionarios.calcular_progresso_municipio(entidade.municipio)
        
        return jsonify({
            'success': True,
            'data': entidade.to_dict(),
            'message': f'Prioridade da entidade atualizada para P{entidade.prioridade}'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar prioridade da entidade {entidade_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@questionarios_bp.route('/reclassificar-prioridades', methods=['POST'])
def reclassificar_todas_prioridades():
    """Reclassifica todas as entidades aplicando a lógica automática de prioridades"""
    try:
        data = request.get_json() or {}
        municipio = data.get('municipio')
        force_update = data.get('force_update', False)
        
        # Filtrar por município se especificado
        query = EntidadeIdentificada.query
        if municipio:
            if municipio not in MUNICIPIOS_PNSB:
                return jsonify({'success': False, 'error': 'Município inválido'}), 400
            query = query.filter_by(municipio=municipio)
        
        entidades = query.all()
        
        if not entidades:
            return jsonify({
                'success': True,
                'message': 'Nenhuma entidade encontrada para reclassificar',
                'entidades_atualizadas': 0
            })
        
        entidades_atualizadas = 0
        log_mudancas = []
        
        for entidade in entidades:
            prioridade_anterior = entidade.prioridade
            categoria_anterior = entidade.categoria_prioridade
            
            # Aplicar lógica automática
            entidade.definir_prioridade_automatica()
            
            # Verificar se houve mudança
            if (entidade.prioridade != prioridade_anterior or 
                entidade.categoria_prioridade != categoria_anterior or 
                force_update):
                
                entidades_atualizadas += 1
                log_mudancas.append({
                    'entidade_id': entidade.id,
                    'nome_entidade': entidade.nome_entidade,
                    'municipio': entidade.municipio,
                    'prioridade_anterior': prioridade_anterior,
                    'prioridade_nova': entidade.prioridade,
                    'categoria_anterior': categoria_anterior,
                    'categoria_nova': entidade.categoria_prioridade,
                    'origem_lista_uf': entidade.origem_lista_uf,
                    'origem_prefeitura': entidade.origem_prefeitura
                })
        
        db.session.commit()
        
        # Recalcular progresso dos municípios afetados
        municipios_afetados = list(set([entidade.municipio for entidade in entidades]))
        for municipio_afetado in municipios_afetados:
            ProgressoQuestionarios.calcular_progresso_municipio(municipio_afetado)
        
        current_app.logger.info(f"Reclassificação de prioridades concluída: {entidades_atualizadas} entidades atualizadas")
        
        return jsonify({
            'success': True,
            'entidades_processadas': len(entidades),
            'entidades_atualizadas': entidades_atualizadas,
            'municipios_afetados': municipios_afetados,
            'log_mudancas': log_mudancas,
            'message': f'Reclassificação concluída: {entidades_atualizadas} entidades atualizadas'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao reclassificar prioridades: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Endpoint removido: prefeituras agora são criadas automaticamente

@questionarios_bp.route('/validar-estrutura', methods=['GET'])
def validar_estrutura_questionarios():
    """
    Valida se a estrutura completa de questionários obrigatórios PNSB está correta
    VERIFICA: Prefeituras (P1), Lista UF (P1), Entidades Campo (P2), Referência (P3)
    """
    try:
        current_app.logger.info("🔍 Iniciando validação da estrutura PNSB completa...")
        
        # Contadores globais
        problemas_encontrados = []
        inconsistencias = []
        estrutura_atual = {}
        
        # === 1. VALIDAÇÃO P1: PREFEITURAS ===
        prefeituras_status = {'ok': 0, 'problemas': []}
        
        for municipio in MUNICIPIOS_PNSB:
            try:
                # Garantir que prefeitura existe e está completa
                prefeitura = ProgressoQuestionarios.garantir_prefeitura_completa(municipio)
                if not prefeitura:
                    prefeituras_status['problemas'].append({
                        'municipio': municipio,
                        'tipo': 'prefeitura_p1',
                        'problema': f'Município {municipio} não criou prefeitura P1 automaticamente'
                    })
                    continue
                
                # Verificar se está corretamente configurada
                entidade_prefeitura = EntidadeIdentificada.query.filter_by(
                    municipio=municipio,
                    tipo_entidade='prefeitura',
                    origem_prefeitura=True,
                    prioridade=1,
                    mrs_obrigatorio=True,
                    map_obrigatorio=True
                ).first()
                
                if entidade_prefeitura:
                    prefeituras_status['ok'] += 1
                else:
                    prefeituras_status['problemas'].append({
                        'municipio': municipio,
                        'tipo': 'prefeitura_validacao',
                        'problema': 'Prefeitura P1 não está configurada corretamente',
                        'esperado': 'P1, MRS: True, MAP: True, origem_prefeitura: True'
                    })
                    
            except Exception as e:
                prefeituras_status['problemas'].append({
                    'municipio': municipio,
                    'tipo': 'prefeitura_erro',
                    'problema': f'Erro ao validar prefeitura: {str(e)}'
                })
        
        # === 2. VALIDAÇÃO P1: LISTA UF ===
        entidades_uf = EntidadePrioritariaUF.query.all()
        uf_status = {
            'total_entidades': len(entidades_uf),
            'por_municipio': {},
            'processadas': 0,
            'pendentes': 0,
            'mrs_obrigatorio': 0,
            'map_obrigatorio': 0
        }
        
        for entidade in entidades_uf:
            municipio = entidade.municipio
            if municipio not in uf_status['por_municipio']:
                uf_status['por_municipio'][municipio] = {
                    'total': 0, 'mrs': 0, 'map': 0, 'processadas': 0, 'pendentes': 0
                }
            
            uf_status['por_municipio'][municipio]['total'] += 1
            
            if entidade.mrs_obrigatorio:
                uf_status['por_municipio'][municipio]['mrs'] += 1
                uf_status['mrs_obrigatorio'] += 1
                
            if entidade.map_obrigatorio:
                uf_status['por_municipio'][municipio]['map'] += 1
                uf_status['map_obrigatorio'] += 1
                
            if entidade.processado:
                uf_status['por_municipio'][municipio]['processadas'] += 1
                uf_status['processadas'] += 1
            else:
                uf_status['por_municipio'][municipio]['pendentes'] += 1
                uf_status['pendentes'] += 1
        
        # === 3. VALIDAÇÃO P2: ENTIDADES IDENTIFICADAS EM CAMPO ===
        entidades_p2 = EntidadeIdentificada.query.filter_by(prioridade=2).all()
        p2_status = {
            'total_entidades': len(entidades_p2),
            'por_municipio': {},
            'mrs_obrigatorio': 0,
            'map_obrigatorio': 0,
            'visitadas': 0,
            'nao_visitadas': 0
        }
        
        for entidade in entidades_p2:
            municipio = entidade.municipio
            if municipio not in p2_status['por_municipio']:
                p2_status['por_municipio'][municipio] = {
                    'total': 0, 'mrs': 0, 'map': 0, 'visitadas': 0
                }
            
            p2_status['por_municipio'][municipio]['total'] += 1
            
            if entidade.mrs_obrigatorio:
                p2_status['por_municipio'][municipio]['mrs'] += 1
                p2_status['mrs_obrigatorio'] += 1
                
            if entidade.map_obrigatorio:
                p2_status['por_municipio'][municipio]['map'] += 1
                p2_status['map_obrigatorio'] += 1
                
            if entidade.visita_id:
                p2_status['por_municipio'][municipio]['visitadas'] += 1
                p2_status['visitadas'] += 1
            else:
                p2_status['nao_visitadas'] += 1
        
        # === 4. VALIDAÇÃO P3: ENTIDADES DE REFERÊNCIA ===
        entidades_p3 = EntidadeIdentificada.query.filter_by(prioridade=3).all()
        p3_status = {
            'total_entidades': len(entidades_p3),
            'por_municipio': {},
            'mrs_opcional': 0,
            'map_opcional': 0,
            'visitadas': 0
        }
        
        for entidade in entidades_p3:
            municipio = entidade.municipio
            if municipio not in p3_status['por_municipio']:
                p3_status['por_municipio'][municipio] = {
                    'total': 0, 'mrs': 0, 'map': 0, 'visitadas': 0
                }
            
            p3_status['por_municipio'][municipio]['total'] += 1
            
            if entidade.mrs_obrigatorio:
                p3_status['por_municipio'][municipio]['mrs'] += 1
                p3_status['mrs_opcional'] += 1
                
            if entidade.map_obrigatorio:
                p3_status['por_municipio'][municipio]['map'] += 1
                p3_status['map_opcional'] += 1
                
            if entidade.visita_id:
                p3_status['por_municipio'][municipio]['visitadas'] += 1
                p3_status['visitadas'] += 1
        
        # === 5. RESUMO GERAL E STATUS ===
        total_problemas = len(prefeituras_status['problemas']) + len(inconsistencias)
        status_geral = 'ok' if total_problemas == 0 else 'problemas_encontrados'
        
        # Calcular totais obrigatórios vs opcionais
        total_mrs_obrigatorio = prefeituras_status['ok'] + uf_status['mrs_obrigatorio'] + p2_status['mrs_obrigatorio']
        total_map_obrigatorio = prefeituras_status['ok'] + uf_status['map_obrigatorio'] + p2_status['map_obrigatorio']
        total_mrs_opcional = p3_status['mrs_opcional']
        total_map_opcional = p3_status['map_opcional']
        
        return jsonify({
            'success': True,
            'status_geral': status_geral,
            'timestamp': datetime.now().isoformat(),
            
            # === VALIDAÇÃO GLOBAL ===
            'validacao_global': {
                'municipios_pnsb': len(MUNICIPIOS_PNSB),
                'problemas_encontrados': total_problemas,
                'status': status_geral,
                'cobertura_municipios': {
                    'prefeituras_ok': prefeituras_status['ok'],
                    'prefeituras_problemas': len(prefeituras_status['problemas']),
                    'percentual_prefeituras': round((prefeituras_status['ok'] / len(MUNICIPIOS_PNSB)) * 100, 1)
                }
            },
            
            # === ESTRUTURA POR PRIORIDADE ===
            'estrutura_prioridades': {
                'p1_critica': {
                    'descricao': 'Prefeituras + Lista UF (Obrigatórias para metas PNSB)',
                    'prefeituras': {
                        'total_municipios': len(MUNICIPIOS_PNSB),
                        'prefeituras_ok': prefeituras_status['ok'],
                        'prefeituras_problemas': len(prefeituras_status['problemas']),
                        'mrs_obrigatorio': prefeituras_status['ok'],
                        'map_obrigatorio': prefeituras_status['ok']
                    },
                    'lista_uf': {
                        'total_entidades': uf_status['total_entidades'],
                        'processadas': uf_status['processadas'],
                        'pendentes': uf_status['pendentes'],
                        'mrs_obrigatorio': uf_status['mrs_obrigatorio'],
                        'map_obrigatorio': uf_status['map_obrigatorio'],
                        'por_municipio': uf_status['por_municipio']
                    },
                    'totais_p1': {
                        'entidades_total': prefeituras_status['ok'] + uf_status['total_entidades'],
                        'mrs_obrigatorio': prefeituras_status['ok'] + uf_status['mrs_obrigatorio'],
                        'map_obrigatorio': prefeituras_status['ok'] + uf_status['map_obrigatorio']
                    }
                },
                
                'p2_importante': {
                    'descricao': 'Entidades identificadas em campo (Se incluídas, tornam-se obrigatórias)',
                    'total_entidades': p2_status['total_entidades'],
                    'mrs_obrigatorio': p2_status['mrs_obrigatorio'],
                    'map_obrigatorio': p2_status['map_obrigatorio'],
                    'visitadas': p2_status['visitadas'],
                    'nao_visitadas': p2_status['nao_visitadas'],
                    'por_municipio': p2_status['por_municipio']
                },
                
                'p3_opcional': {
                    'descricao': 'Entidades de referência (Recursos disponíveis, não contam para metas)',
                    'total_entidades': p3_status['total_entidades'],
                    'mrs_opcional': p3_status['mrs_opcional'],
                    'map_opcional': p3_status['map_opcional'],
                    'visitadas': p3_status['visitadas'],
                    'por_municipio': p3_status['por_municipio']
                }
            },
            
            # === MÉTRICAS CONSOLIDADAS ===
            'metricas_consolidadas': {
                'questionarios_obrigatorios': {
                    'mrs_total': total_mrs_obrigatorio,
                    'map_total': total_map_obrigatorio,
                    'total_obrigatorio': total_mrs_obrigatorio + total_map_obrigatorio
                },
                'questionarios_opcionais': {
                    'mrs_total': total_mrs_opcional,
                    'map_total': total_map_opcional,
                    'total_opcional': total_mrs_opcional + total_map_opcional
                },
                'entidades_por_tipo': {
                    'prefeituras': prefeituras_status['ok'],
                    'lista_uf': uf_status['total_entidades'],
                    'lista_uf_nao_processadas': uf_status['pendentes'],
                    'campo_p2': p2_status['total_entidades'],
                    'referencia_p3': p3_status['total_entidades'],
                    'total_sistema': prefeituras_status['ok'] + uf_status['total_entidades'] + p2_status['total_entidades'] + p3_status['total_entidades'],
                    'total_real_identificadas': prefeituras_status['ok'] + uf_status['total_entidades'] + p2_status['total_entidades'] + p3_status['total_entidades']
                }
            },
            
            # === PROBLEMAS DETALHADOS ===
            'problemas_detalhados': {
                'prefeituras': prefeituras_status['problemas'],
                'inconsistencias_sistema': inconsistencias,
                'total_problemas': total_problemas
            },
            
            # === ESTRUTURA ESPERADA PNSB ===
            'estrutura_esperada_pnsb': {
                'metodologia': 'Sistema de prioridades P1 (crítica) + P2 (importante) + P3 (opcional)',
                'obrigatorios_meta_pnsb': 'P1 (Prefeituras + Lista UF) + P2 (Campo incluídas)',
                'opcionais_trabalho_completo': 'P3 (Referência, se recursos disponíveis)',
                'municipios_pnsb': MUNICIPIOS_PNSB,
                'estrutura_minima': {
                    'por_municipio': '1 Prefeitura P1 (MRS + MAP obrigatórios)',
                    'lista_uf': 'Entidades P1 fornecidas pela UF',
                    'campo': 'Entidades P2 identificadas durante visitas',
                    'referencia': 'Entidades P3 para trabalho completo se possível'
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"❌ Erro na validação da estrutura PNSB: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500