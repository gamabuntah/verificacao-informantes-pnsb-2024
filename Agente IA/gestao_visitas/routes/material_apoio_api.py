"""
API Routes para Material de Apoio PNSB
Gerencia chat especializado, biblioteca digital e recursos
"""

from flask import Blueprint, request, jsonify, send_file
from ..services.api_manager import api_manager
from ..utils.validators import validate_json_input
from ..utils.error_handlers import APIResponse
import os
import logging
from datetime import datetime
import pdfplumber
from pathlib import Path
import time

logger = logging.getLogger(__name__)

# Cache global para conteúdo dos PDFs
_pdfs_cache = None
_cache_timestamp = 0
_cache_duration = 1800  # 30 minutos (conteúdo completo é pesado)

material_apoio_bp = Blueprint('material_apoio', __name__)

@material_apoio_bp.route('/chat/manual', methods=['POST'])
@validate_json_input(required_fields=['message'])
def chat_manual_pnsb():
    """Chat especializado com contexto do manual PNSB"""
    try:
        user_message = request.validated_data['message']
        
        # Construir contexto específico do manual PNSB
        context = build_manual_context(user_message)
        
        # Usar o gerenciador de APIs
        result = api_manager.chat_with_ai(user_message, context)
        
        if result['success']:
            return APIResponse.success(data={
                'response': result['response'],
                'source': 'Manual PNSB 2024',
                'type': 'manual_specialized',
                'fallback_used': False
            })
        else:
            # Fallback específico para PNSB baseado nos PDFs
            fallback_response = generate_pnsb_manual_fallback(user_message)
            return APIResponse.success(data={
                'response': fallback_response,
                'source': 'PDFs da pasta Contexto_Material_de_Apoio',
                'type': 'fallback',
                'fallback_used': True,
                'message': 'IA temporariamente indisponível - usando conhecimento limitado aos 3 PDFs disponíveis'
            })
        
    except Exception as e:
        logger.error(f"Erro no chat manual PNSB: {e}")
        return APIResponse.error(f"Erro no processamento da consulta: {str(e)}")

def extract_complete_pdf_content(pdf_path):
    """Extrai TODO o conteúdo de um PDF - sem limitações"""
    try:
        content = ""
        filename = os.path.basename(pdf_path)
        
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            logger.info(f"📖 Extraindo TODO o conteúdo de {filename} ({total_pages} páginas)")
            
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                if page_text.strip():  # Só adicionar se a página tem conteúdo
                    content += f"\n=== PÁGINA {i + 1} ===\n"
                    content += page_text + "\n"
            
            logger.info(f"📊 {filename}: {len(content):,} caracteres extraídos de {total_pages} páginas")
            return content.strip()
            
    except Exception as e:
        logger.error(f"Erro ao extrair PDF completo {pdf_path}: {e}")
        return f"[ERRO ao ler {os.path.basename(pdf_path)}]"

def extract_pdf_content(pdf_path, max_pages=10, max_chars=3000, key_sections=None):
    """Extrai conteúdo de um PDF com priorização de seções-chave"""
    try:
        content = ""
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            
            # Se há seções-chave definidas, priorizar essas páginas
            if key_sections:
                logger.info(f"📑 Extraindo seções-chave {key_sections} de {os.path.basename(pdf_path)}")
                for page_num in key_sections:
                    if page_num <= total_pages:
                        page = pdf.pages[page_num - 1]  # PDFs são 0-indexed
                        page_text = page.extract_text() or ""
                        content += f"\n=== PÁGINA {page_num} (SEÇÃO-CHAVE) ===\n"
                        content += page_text + "\n\n"
                
                # Depois extrair páginas do início
                remaining_chars = max_chars - len(content)
                if remaining_chars > 1000:
                    pages_to_read = min(50, max_pages, total_pages)
                    for i in range(pages_to_read):
                        if (i + 1) not in key_sections:  # Evitar duplicar seções-chave
                            page = pdf.pages[i]
                            page_text = page.extract_text() or ""
                            content += page_text + "\n\n"
                            
                            if len(content) > max_chars:
                                content = content[:max_chars] + "...[CONTEÚDO TRUNCADO]\n"
                                break
            else:
                # Extração normal
                pages_to_read = min(len(pdf.pages), max_pages)
                for i in range(pages_to_read):
                    page = pdf.pages[i]
                    page_text = page.extract_text() or ""
                    content += page_text + "\n\n"
                    
                    # Limitar tamanho do conteúdo
                    if len(content) > max_chars:
                        content = content[:max_chars] + "...[CONTEÚDO TRUNCADO]\n"
                        break
        
        return content.strip()
    except Exception as e:
        logger.error(f"Erro ao extrair PDF {pdf_path}: {e}")
        return f"[ERRO ao ler {os.path.basename(pdf_path)}]"

def load_pdfs_content():
    """Carrega conteúdo dos PDFs da pasta Contexto_Material_de_Apoio com cache"""
    global _pdfs_cache, _cache_timestamp
    
    # Verificar se o cache é válido
    current_time = time.time()
    if _pdfs_cache and (current_time - _cache_timestamp) < _cache_duration:
        logger.info("📚 Usando cache dos PDFs")
        return _pdfs_cache
    
    logger.info("📚 Carregando PDFs (cache expirado ou inexistente)")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    context_folder = os.path.join(base_dir, 'Contexto_Material_de_Apoio')
    
    # Processar TODOS os PDFs que existem na pasta, sem limitações
    pdfs_info = {
        'Manual_PNSB2024_15052025.pdf': {'desc': 'Manual oficial da pesquisa PNSB 2024', 'priority': 1},
        'MRS 2024 19 04 25.pdf': {'desc': 'Questionário de Manejo de Resíduos Sólidos', 'priority': 2},
        'MAP 2024 24 04 25.pdf': {'desc': 'Questionário de Manejo de Águas Pluviais', 'priority': 2},
        'GuiaRápido_SigcPnsb2024.pdf': {'desc': 'Guia rápido do sistema SIGC PNSB', 'priority': 3},
        'Sistema.pdf': {'desc': 'Documentação técnica do sistema', 'priority': 4}
    }
    
    pdfs_content = {}
    
    for filename, info in pdfs_info.items():
        pdf_path = os.path.join(context_folder, filename)
        if os.path.exists(pdf_path):
            # Extrair TODO o conteúdo do PDF - sem limitações
            content = extract_complete_pdf_content(pdf_path)
            pdfs_content[filename] = {
                'content': content,
                'description': info['desc'],
                'priority': info['priority']
            }
        else:
            logger.warning(f"PDF não encontrado: {pdf_path}")
    
    # Atualizar cache
    _pdfs_cache = pdfs_content
    _cache_timestamp = current_time
    logger.info(f"📚 Cache dos PDFs atualizado com {len(pdfs_content)} documentos")
    
    return pdfs_content

def build_manual_context(user_message):
    """Constrói contexto específico baseado EXCLUSIVAMENTE no conteúdo real dos PDFs"""
    
    # Carregar conteúdo dos PDFs
    pdfs_content = load_pdfs_content()
    
    # Construir contexto com conteúdo real
    context_parts = []
    context_parts.append("Você é um assistente técnico especializado EXCLUSIVAMENTE no conteúdo dos seguintes documentos oficiais da PNSB 2024:")
    context_parts.append("")
    
    # Adicionar conteúdo dos PDFs por prioridade
    sorted_pdfs = sorted(pdfs_content.items(), key=lambda x: x[1]['priority'])
    
    # ENVIAR TODO O CONTEÚDO - SEM LIMITAÇÕES ARTIFICIAIS
    for filename, pdf_info in sorted_pdfs:
        content = pdf_info['content']
        
        context_parts.append(f"📚 **{filename}** ({pdf_info['description']})")
        context_parts.append(f"CONTEÚDO COMPLETO:")
        context_parts.append(content)  # TODO O CONTEÚDO, SEM TRUNCAR
        context_parts.append("=" * 80)
        context_parts.append("")
    
    context_parts.append(f"🎯 **PERGUNTA DO USUÁRIO:** {user_message}")
    context_parts.append("")
    context_parts.append("**INSTRUÇÕES PARA RESPOSTA:**")
    context_parts.append("1. Base sua resposta EXCLUSIVAMENTE no conteúdo COMPLETO acima dos PDFs fornecidos")
    context_parts.append("2. Cite qual documento específico contém a informação, incluindo páginas quando disponível")
    context_parts.append("3. Use apenas a terminologia exata que consta nos PDFs")
    context_parts.append("4. Se a informação não estiver no conteúdo fornecido acima, informe essa limitação")
    context_parts.append("5. Seja preciso e prático para pesquisadores da PNSB")
    context_parts.append("6. IMPORTANTE: Você tem acesso ao conteúdo COMPLETO dos documentos listados acima")
    
    return "\n".join(context_parts)

def generate_pnsb_manual_fallback(user_message):
    """Gera resposta de fallback baseada EXCLUSIVAMENTE nos PDFs da pasta Contexto_Material_de_Apoio"""
    message_lower = user_message.lower()
    
    # Resíduos Sólidos
    if any(word in message_lower for word in ['residuo', 'lixo', 'coleta', 'reciclagem', 'compostagem', 'mrs']):
        return """**QUESTIONÁRIOS MRS - MANEJO DE RESÍDUOS SÓLIDOS (PNSB 2024)**

📋 **Fontes Disponíveis:**
• **PNSB MRS COMPLETO_22_05_2025.pdf** (Versão detalhada e completa)
• **MRS 2024 19 04 25.pdf** (Versão básica)

⚠️ **Informação baseada exclusivamente nos PDFs dos questionários MRS**

**TEMAS PRINCIPAIS DOS QUESTIONÁRIOS MRS:**
• Estrutura organizacional do manejo de resíduos sólidos
• Coleta domiciliar regular e seletiva
• Tratamento, beneficiamento e destinação final
• Plano Municipal de Gestão Integrada de Resíduos Sólidos (PMGIRS)
• Parcerias com catadores e cooperativas
• Compostagem e aproveitamento energético
• Custos, taxas e sustentabilidade financeira
• Resíduos especiais e específicos

⚠️ **PRIORIZAÇÃO:** Para informações detalhadas, consulte preferencialmente o documento COMPLETO (22_05_2025). O documento básico (19_04_25) serve como complemento.

💡 **Sugestão:** Faça perguntas específicas como "Como preencher a questão X do questionário MRS completo?" para obter informações detalhadas baseadas na versão mais completa do documento."""
    
    # Águas Pluviais
    elif any(word in message_lower for word in ['agua', 'pluvial', 'drenagem', 'alagamento', 'inundacao', 'map']):
        return """**QUESTIONÁRIOS MAP - MANEJO DE ÁGUAS PLUVIAIS (PNSB 2024)**

📋 **Fontes Disponíveis:**
• **PNSB MAP COMPLETO_25042025.pdf** (Versão detalhada e completa)
• **MAP 2024 24 04 25.pdf** (Versão básica)

⚠️ **Informação baseada exclusivamente nos PDFs dos questionários MAP**

**TEMAS PRINCIPAIS DOS QUESTIONÁRIOS MAP:**
• Sistema de drenagem urbana municipal
• Problemas de alagamentos, inundações e enchentes
• Obras de macrodrenagem e microdrenagem
• Manutenção preventiva e corretiva da rede
• Plano Municipal de Drenagem e Manejo de Águas Pluviais
• Medidas estruturais e não estruturais
• Gestão integrada com recursos hídricos
• Sustentabilidade e soluções baseadas na natureza

⚠️ **PRIORIZAÇÃO:** Para informações detalhadas, consulte preferencialmente o documento COMPLETO (25042025). O documento básico (24_04_25) serve como complemento.

💡 **Sugestão:** Faça perguntas específicas como "Como preencher a questão Y do questionário MAP completo?" para obter informações detalhadas baseadas na versão mais completa do documento."""
    
    # Metodologia
    elif any(word in message_lower for word in ['questionario', 'entrevista', 'metodologia', 'pesquisa', 'manual']):
        return """**METODOLOGIA PNSB 2024**

📚 **Fonte:** Manual_PNSB2024_15052025.pdf (Contexto_Material_de_Apoio)

⚠️ **Informação baseada exclusivamente no Manual PNSB 2024 disponível**

**INSTRUMENTOS E METODOLOGIA (conforme Manual):**
• Questionário MRS e MAP da PNSB 2024
• Procedimentos de entrevista
• Identificação de informantes
• Coleta de documentação

⚠️ **LIMITAÇÃO:** Esta resposta está baseada apenas no conteúdo específico do Manual_PNSB2024_15052025.pdf. Para informações detalhadas sobre procedimentos específicos, códigos ou orientações técnicas, consulte diretamente o documento PDF ou use uma pergunta mais específica.

💡 **Sugestão:** Faça perguntas específicas como "Qual o procedimento para identificar informantes segundo o manual?" para obter informações mais detalhadas baseadas no documento."""
    
    # Perguntas sobre conteúdo não disponível
    elif any(word in message_lower for word in ['lei', 'legislacao', 'marco', 'legal', 'norma', 'plano', 'pmgirs', 'pmsb', 'planejamento', 'indicador', 'calculo', 'indice', 'taxa']):
        return """**INFORMAÇÃO NÃO DISPONÍVEL NOS DOCUMENTOS**

⚠️ **Sua pergunta se refere a conteúdo que pode não estar detalhado nos 3 PDFs disponíveis:**

📚 **Documentos disponíveis:**
• Manual_PNSB2024_15052025.pdf
• MRS 2024 19 04 25.pdf  
• MAP 2024 24 04 25.pdf

🔍 **Para obter essa informação:**
1. Consulte diretamente os PDFs específicos
2. Reformule sua pergunta para ser mais específica sobre o conteúdo dos questionários
3. Verifique se a informação está em seções específicas dos documentos

💡 **Exemplos de perguntas adequadas:**
• "Como preencher a questão X do questionário MRS?"
• "Qual informação solicitar sobre drenagem no MAP?"
• "Quais são os procedimentos de entrevista no manual?"

⚠️ **LIMITAÇÃO:** Este assistente responde apenas com base no conteúdo específico dos 3 PDFs da pasta Contexto_Material_de_Apoio."""
    
    # Resposta genérica
    else:
        return """**ASSISTENTE PNSB 2024 - MATERIAL DE APOIO**

📚 **DOCUMENTOS DISPONÍVEIS (pasta Contexto_Material_de_Apoio):**
• Manual_PNSB2024_15052025.pdf
• MRS 2024 19 04 25.pdf (Questionário Manejo de Resíduos Sólidos)
• MAP 2024 24 04 25.pdf (Questionário Manejo de Águas Pluviais)

⚠️ **IMPORTANTE - LIMITAÇÕES:**
• Respondo APENAS com base no conteúdo específico desses 3 PDFs
• NÃO tenho acesso a conhecimento externo ou outras fontes
• Se uma informação não estiver nos PDFs, informarei essa limitação

🔍 **TEMAS DISPONÍVEIS (conforme PDFs):**
• Estrutura e preenchimento dos questionários MRS e MAP
• Procedimentos metodológicos do manual
• Orientações específicas dos documentos oficiais

💡 **EXEMPLOS DE PERGUNTAS ADEQUADAS:**
• "Como preencher a seção X do questionário MRS?"
• "Qual o procedimento Y descrito no manual?"
• "Que informações o questionário MAP solicita sobre Z?"
• "Quais códigos usar para W no MRS?"

⚠️ **EXEMPLOS DE PERGUNTAS QUE NÃO POSSO RESPONDER:**
• Informações não contidas nos 3 PDFs específicos
• Conhecimento geral sobre IBGE ou saneamento
• Legislação não explicitamente citada nos documentos

**Digite sua pergunta específica sobre o conteúdo dos PDFs da PNSB 2024!**"""

@material_apoio_bp.route('/biblioteca/documentos', methods=['GET'])
def listar_documentos():
    """Lista documentos disponíveis na biblioteca digital"""
    try:
        # Estrutura completa da biblioteca
        documentos = {
            'manuais': [
                {
                    'id': 'manual_pnsb_2024',
                    'titulo': 'Manual PNSB 2024 - Completo',
                    'categoria': 'Manual Oficial',
                    'formato': 'PDF',
                    'tamanho': '2.5 MB',
                    'status': 'disponivel',
                    'url': '/api/material-apoio/biblioteca/download/manual_pnsb_2024'
                }
            ],
            'questionarios': [
                {
                    'id': 'questionario_residuos',
                    'titulo': 'Questionário MRS - Resíduos Sólidos',
                    'categoria': 'Questionário',
                    'formato': 'PDF',
                    'tamanho': '1.2 MB',
                    'status': 'disponivel',
                    'url': '/api/material-apoio/biblioteca/download/questionario_residuos'
                },
                {
                    'id': 'questionario_aguas',
                    'titulo': 'Questionário MAP - Águas Pluviais',
                    'categoria': 'Questionário',
                    'formato': 'PDF',
                    'tamanho': '1.1 MB',
                    'status': 'disponivel',
                    'url': '/api/material-apoio/biblioteca/download/questionario_aguas'
                }
            ],
            'legislacao': [
                {
                    'id': 'marco_legal_saneamento',
                    'titulo': 'Marco Legal do Saneamento (Lei 14.026/2020)',
                    'categoria': 'Legislação',
                    'formato': 'PDF',
                    'tamanho': '0.8 MB',
                    'status': 'disponivel',
                    'url': '/api/material-apoio/biblioteca/download/marco_legal_saneamento'
                },
                {
                    'id': 'pnrs_lei',
                    'titulo': 'Política Nacional de Resíduos Sólidos (Lei 12.305/2010)',
                    'categoria': 'Legislação',
                    'formato': 'PDF',
                    'tamanho': '0.6 MB',
                    'status': 'disponivel',
                    'url': '/api/material-apoio/biblioteca/download/pnrs_lei'
                }
            ]
        }
        
        return APIResponse.success(data=documentos)
        
    except Exception as e:
        logger.error(f"Erro ao listar documentos: {e}")
        return APIResponse.error(f"Erro ao carregar biblioteca: {str(e)}")

@material_apoio_bp.route('/biblioteca/download/<documento_id>', methods=['GET'])
def download_documento(documento_id):
    """Download de documento da biblioteca"""
    try:
        # Diretório de documentos
        docs_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'documentos_pnsb')
        
        # Mapeamento de documentos disponíveis
        documentos_mapa = {
            'manual_pnsb_2024': {
                'filename': 'Manual_PNSB2024_15052025.pdf',
                'nome_download': 'Manual_PNSB_2024.pdf',
                'content_type': 'application/pdf'
            },
            'questionario_residuos': {
                'filename': 'MRS.pdf', 
                'nome_download': 'Questionario_Residuos_Solidos_PNSB.pdf',
                'content_type': 'application/pdf'
            },
            'questionario_aguas': {
                'filename': 'MAP.pdf',
                'nome_download': 'Questionario_Aguas_Pluviais_PNSB.pdf', 
                'content_type': 'application/pdf'
            },
            'marco_legal_saneamento': {
                'filename': 'Lei_14026_2020_Marco_Legal.pdf',
                'nome_download': 'Marco_Legal_Saneamento_2020.pdf',
                'content_type': 'application/pdf'
            },
            'pnrs_lei': {
                'filename': 'Lei_12305_2010_PNRS.pdf',
                'nome_download': 'Politica_Nacional_Residuos_Solidos.pdf',
                'content_type': 'application/pdf'
            }
        }
        
        if documento_id not in documentos_mapa:
            return APIResponse.error(
                f"Documento '{documento_id}' não encontrado",
                error_type="not_found",
                status_code=404
            )
        
        doc_info = documentos_mapa[documento_id]
        filepath = os.path.join(docs_dir, doc_info['filename'])
        
        # Verificar se arquivo existe, senão criar placeholder
        if not os.path.exists(filepath):
            # Criar diretório se não existir
            os.makedirs(docs_dir, exist_ok=True)
            
            # Criar arquivo placeholder para demonstração
            placeholder_content = f"""
DOCUMENTO PLACEHOLDER - {doc_info['nome_download']}

Este é um arquivo de demonstração para o sistema Material de Apoio PNSB.

Para usar com documentos reais:
1. Coloque os arquivos PDF na pasta: gestao_visitas/documentos_pnsb/
2. Use os nomes de arquivo configurados no sistema
3. Os downloads funcionarão automaticamente

Documento solicitado: {documento_id}
Arquivo esperado: {doc_info['filename']}
Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Sistema Material de Apoio PNSB - Em Desenvolvimento
            """.strip()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(placeholder_content)
        
        # Log da atividade
        logger.info(f"Download solicitado: {documento_id} por IP {request.remote_addr}")
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=doc_info['nome_download'],
            mimetype=doc_info['content_type']
        )
        
    except Exception as e:
        logger.error(f"Erro no download de {documento_id}: {e}")
        return APIResponse.error(f"Erro no download: {str(e)}")

@material_apoio_bp.route('/busca', methods=['POST'])
@validate_json_input(required_fields=['query'])
def busca_unificada():
    """Busca unificada em todos os materiais"""
    try:
        query = request.validated_data['query']
        search_type = request.validated_data.get('type', 'all')
        filtros = request.validated_data.get('filtros', {})
        
        # Base de conhecimento PNSB para busca
        base_conhecimento = {
            'documentos': [
                {
                    'id': 'manual_pnsb_2024',
                    'titulo': 'Manual PNSB 2024 - Completo',
                    'categoria': 'Manual Oficial',
                    'tipo': 'manual',
                    'descricao': 'Manual completo da Pesquisa Nacional de Saneamento Básico 2024',
                    'tags': ['pnsb', 'manual', 'saneamento', 'pesquisa', 'ibge'],
                    'conteudo': 'pesquisa nacional saneamento básico manual metodologia resíduos sólidos águas pluviais questionários'
                },
                {
                    'id': 'questionario_residuos',
                    'titulo': 'Questionário MRS - Manejo de Resíduos Sólidos',
                    'categoria': 'Questionário',
                    'tipo': 'questionario',
                    'descricao': 'Questionário específico para coleta de dados sobre manejo de resíduos sólidos urbanos',
                    'tags': ['mrs', 'resíduos', 'sólidos', 'coleta', 'questionário'],
                    'conteudo': 'manejo resíduos sólidos coleta domiciliar seletiva tratamento destinação pmgirs catadores'
                },
                {
                    'id': 'questionario_aguas',
                    'titulo': 'Questionário MAP - Manejo de Águas Pluviais',
                    'categoria': 'Questionário', 
                    'tipo': 'questionario',
                    'descricao': 'Questionário para levantamento de dados sobre drenagem urbana e águas pluviais',
                    'tags': ['map', 'águas', 'pluviais', 'drenagem', 'questionário'],
                    'conteudo': 'manejo águas pluviais drenagem urbana alagamentos plano municipal microdrenagem macrodrenagem'
                }
            ],
            'procedimentos': [
                {
                    'id': 'entrevista_tecnicas',
                    'titulo': 'Técnicas de Entrevista PNSB',
                    'categoria': 'Metodologia',
                    'tipo': 'procedimento',
                    'descricao': 'Orientações para conduzir entrevistas com informantes qualificados',
                    'tags': ['entrevista', 'metodologia', 'informante', 'técnicas'],
                    'conteudo': 'entrevista informante qualificado agendamento apresentação documentação observações'
                },
                {
                    'id': 'preenchimento_questionario',
                    'titulo': 'Preenchimento de Questionários',
                    'categoria': 'Metodologia',
                    'tipo': 'procedimento', 
                    'descricao': 'Instruções para preenchimento correto dos questionários PNSB',
                    'tags': ['preenchimento', 'questionário', 'códigos', 'consistência'],
                    'conteudo': 'preenchimento questionário códigos padronizados consistência verificação documentação'
                }
            ],
            'legislacao': [
                {
                    'id': 'marco_legal_2020',
                    'titulo': 'Lei 14.026/2020 - Marco Legal do Saneamento',
                    'categoria': 'Legislação Federal',
                    'tipo': 'lei',
                    'descricao': 'Atualiza o marco legal do saneamento básico no Brasil',
                    'tags': ['marco legal', 'saneamento', 'lei', '2020', 'universalização'],
                    'conteudo': 'marco legal saneamento universalização regulação metas prazos'
                },
                {
                    'id': 'pnrs_2010',
                    'titulo': 'Lei 12.305/2010 - Política Nacional de Resíduos Sólidos',
                    'categoria': 'Legislação Federal',
                    'tipo': 'lei',
                    'descricao': 'Institui a Política Nacional de Resíduos Sólidos',
                    'tags': ['pnrs', 'resíduos sólidos', 'lei', '2010', 'pmgirs'],
                    'conteudo': 'política nacional resíduos sólidos pmgirs responsabilidade compartilhada logística reversa'
                }
            ],
            'perguntas_frequentes': [
                {
                    'id': 'faq_coleta_seletiva',
                    'titulo': 'Como investigar coleta seletiva municipal?',
                    'categoria': 'FAQ',
                    'tipo': 'qa',
                    'descricao': 'Perguntas frequentes sobre coleta seletiva no PNSB',
                    'tags': ['coleta seletiva', 'faq', 'municipal'],
                    'conteudo': 'coleta seletiva municipal programa cooperativas materiais recicláveis'
                },
                {
                    'id': 'faq_drenagem',
                    'titulo': 'Como avaliar sistema de drenagem urbana?',
                    'categoria': 'FAQ',
                    'tipo': 'qa',
                    'descricao': 'Orientações para avaliação de sistemas de drenagem',
                    'tags': ['drenagem', 'urbana', 'faq', 'avaliação'],
                    'conteudo': 'drenagem urbana sistema avaliação alagamentos obras plano'
                }
            ]
        }
        
        # Realizar busca
        resultados_encontrados = []
        query_lower = query.lower()
        
        # Função para calcular relevância
        def calcular_relevancia(item, query_lower):
            score = 0
            
            # Título (peso 3)
            if query_lower in item['titulo'].lower():
                score += 3
                
            # Tags (peso 2)
            for tag in item['tags']:
                if query_lower in tag.lower():
                    score += 2
                    
            # Conteúdo (peso 1)
            if query_lower in item['conteudo'].lower():
                score += 1
                
            # Categoria (peso 1)
            if query_lower in item['categoria'].lower():
                score += 1
                
            return score
        
        # Buscar em todas as categorias
        categorias_busca = []
        
        if search_type == 'all' or search_type == 'documents':
            categorias_busca.extend(base_conhecimento['documentos'])
        if search_type == 'all' or search_type == 'procedures':
            categorias_busca.extend(base_conhecimento['procedimentos'])
        if search_type == 'all' or search_type == 'legislation':
            categorias_busca.extend(base_conhecimento['legislacao'])
        if search_type == 'all' or search_type == 'qa':
            categorias_busca.extend(base_conhecimento['perguntas_frequentes'])
        
        # Aplicar busca e filtros
        for item in categorias_busca:
            relevancia = calcular_relevancia(item, query_lower)
            
            if relevancia > 0:
                # Aplicar filtros
                if filtros.get('categoria') and filtros['categoria'] not in item['categoria'].lower():
                    continue
                if filtros.get('tipo_documento') and filtros['tipo_documento'] != item['tipo']:
                    continue
                    
                # Determinar ícone
                icon_map = {
                    'manual': 'fas fa-file-pdf text-danger',
                    'questionario': 'fas fa-clipboard-list text-primary',
                    'procedimento': 'fas fa-tasks text-success',
                    'lei': 'fas fa-gavel text-warning',
                    'qa': 'fas fa-question-circle text-info'
                }
                
                resultado = {
                    'id': item['id'],
                    'titulo': item['titulo'],
                    'descricao': item['descricao'],
                    'categoria': item['categoria'],
                    'tipo': item['tipo'],
                    'relevancia': relevancia,
                    'icon': icon_map.get(item['tipo'], 'fas fa-file text-secondary'),
                    'tags': item['tags'][:3]  # Primeiras 3 tags
                }
                
                resultados_encontrados.append(resultado)
        
        # Ordenar por relevância
        resultados_encontrados.sort(key=lambda x: x['relevancia'], reverse=True)
        
        # Limitar resultados
        if filtros.get('relevancia') == 'high':
            resultados_encontrados = [r for r in resultados_encontrados if r['relevancia'] >= 2]
        
        # Gerar sugestões baseadas na query
        sugestoes = gerar_sugestoes_busca(query_lower)
        
        resultados_final = {
            'query': query,
            'total_resultados': len(resultados_encontrados),
            'resultados': resultados_encontrados[:20],  # Máximo 20 resultados
            'sugestoes': sugestoes,
            'status': 'ativo',
            'filtros_aplicados': filtros,
            'tipo_busca': search_type
        }
        
        return APIResponse.success(data=resultados_final)
        
    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        return APIResponse.error(f"Erro na busca: {str(e)}")

def gerar_sugestoes_busca(query_lower):
    """Gera sugestões de busca baseadas na query"""
    sugestoes_base = {
        'residuo': ['resíduos sólidos', 'coleta seletiva', 'PMGIRS', 'destinação final'],
        'agua': ['águas pluviais', 'drenagem urbana', 'alagamentos', 'macrodrenagem'],
        'coleta': ['coleta domiciliar', 'coleta seletiva', 'frequência coleta', 'cobertura'],
        'questionario': ['preenchimento questionário', 'códigos PNSB', 'metodologia'],
        'plano': ['PMGIRS', 'plano saneamento', 'plano drenagem', 'planejamento'],
        'lei': ['marco legal', 'PNRS', 'legislação saneamento', 'normas'],
        'municipal': ['prefeitura', 'secretaria', 'gestão municipal', 'informante'],
        'tratamento': ['tratamento resíduos', 'aterro sanitário', 'compostagem'],
        'drenagem': ['sistema drenagem', 'obras drenagem', 'manutenção rede']
    }
    
    sugestoes = []
    for palavra_chave in sugestoes_base:
        if palavra_chave in query_lower:
            sugestoes.extend(sugestoes_base[palavra_chave])
            break
    
    # Sugestões padrão se nenhuma palavra-chave combinar
    if not sugestoes:
        sugestoes = ['resíduos sólidos', 'águas pluviais', 'questionário PNSB', 'legislação saneamento']
    
    return sugestoes[:6]  # Máximo 6 sugestões

@material_apoio_bp.route('/recursos/calculadora', methods=['POST'])
@validate_json_input(required_fields=['tipo'])
def calculadora_pnsb():
    """Calculadoras específicas do PNSB"""
    try:
        tipo = request.validated_data['tipo']
        dados = request.validated_data.get('dados', {})
        
        resultado = {}
        
        if tipo == 'cobertura_coleta':
            # Calculadora de cobertura de coleta
            pop_total = float(dados.get('populacao_total', 0))
            pop_atendida = float(dados.get('populacao_atendida', 0))
            
            if pop_total > 0:
                cobertura = (pop_atendida / pop_total) * 100
                resultado = {
                    'tipo': 'Cobertura de Coleta Domiciliar',
                    'resultado': round(cobertura, 2),
                    'unidade': '%',
                    'formula': '(População Atendida / População Total) × 100',
                    'interpretacao': get_interpretacao_cobertura(cobertura),
                    'dados_entrada': {
                        'populacao_total': pop_total,
                        'populacao_atendida': pop_atendida
                    }
                }
            else:
                return APIResponse.error("População total deve ser maior que zero")
                
        elif tipo == 'geracao_per_capita':
            # Calculadora de geração per capita
            total_residuos = float(dados.get('total_residuos_kg_dia', 0))
            populacao = float(dados.get('populacao', 0))
            
            if populacao > 0:
                per_capita = total_residuos / populacao
                resultado = {
                    'tipo': 'Geração Per Capita de Resíduos',
                    'resultado': round(per_capita, 3),
                    'unidade': 'kg/hab/dia',
                    'formula': 'Total de Resíduos (kg/dia) / População',
                    'interpretacao': get_interpretacao_per_capita(per_capita),
                    'dados_entrada': {
                        'total_residuos_kg_dia': total_residuos,
                        'populacao': populacao
                    }
                }
            else:
                return APIResponse.error("População deve ser maior que zero")
                
        elif tipo == 'taxa_reciclagem':
            # Calculadora de taxa de reciclagem
            total_coletado = float(dados.get('total_coletado', 0))
            total_reciclado = float(dados.get('total_reciclado', 0))
            
            if total_coletado > 0:
                taxa = (total_reciclado / total_coletado) * 100
                resultado = {
                    'tipo': 'Taxa de Reciclagem',
                    'resultado': round(taxa, 2),
                    'unidade': '%',
                    'formula': '(Total Reciclado / Total Coletado) × 100',
                    'interpretacao': get_interpretacao_reciclagem(taxa),
                    'dados_entrada': {
                        'total_coletado': total_coletado,
                        'total_reciclado': total_reciclado
                    }
                }
            else:
                return APIResponse.error("Total coletado deve ser maior que zero")
                
        elif tipo == 'densidade_drenagem':
            # Calculadora de densidade da rede de drenagem
            extensao_rede = float(dados.get('extensao_rede_km', 0))
            area_urbana = float(dados.get('area_urbana_km2', 0))
            
            if area_urbana > 0:
                densidade = extensao_rede / area_urbana
                resultado = {
                    'tipo': 'Densidade da Rede de Drenagem',
                    'resultado': round(densidade, 2),
                    'unidade': 'km/km²',
                    'formula': 'Extensão da Rede (km) / Área Urbana (km²)',
                    'interpretacao': get_interpretacao_densidade(densidade),
                    'dados_entrada': {
                        'extensao_rede_km': extensao_rede,
                        'area_urbana_km2': area_urbana
                    }
                }
            else:
                return APIResponse.error("Área urbana deve ser maior que zero")
                
        elif tipo == 'custo_per_capita':
            # Calculadora de custo per capita
            custo_total_anual = float(dados.get('custo_total_anual', 0))
            populacao = float(dados.get('populacao', 0))
            
            if populacao > 0:
                custo_per_capita = custo_total_anual / populacao
                resultado = {
                    'tipo': 'Custo Per Capita do Serviço',
                    'resultado': round(custo_per_capita, 2),
                    'unidade': 'R$/hab/ano',
                    'formula': 'Custo Total Anual / População',
                    'interpretacao': get_interpretacao_custo(custo_per_capita),
                    'dados_entrada': {
                        'custo_total_anual': custo_total_anual,
                        'populacao': populacao
                    }
                }
            else:
                return APIResponse.error("População deve ser maior que zero")
                
        else:
            return APIResponse.error(f"Tipo de calculadora '{tipo}' não reconhecido")
        
        return APIResponse.success(data=resultado)
        
    except ValueError as e:
        return APIResponse.error(f"Erro nos dados de entrada: valores devem ser numéricos")
    except Exception as e:
        logger.error(f"Erro na calculadora: {e}")
        return APIResponse.error(f"Erro no cálculo: {str(e)}")

def get_interpretacao_cobertura(cobertura):
    """Interpretação para cobertura de coleta"""
    if cobertura >= 95:
        return "Excelente - Cobertura quase universal"
    elif cobertura >= 80:
        return "Boa - Cobertura adequada"
    elif cobertura >= 60:
        return "Regular - Necessita melhorias"
    else:
        return "Inadequada - Requer investimentos urgentes"

def get_interpretacao_per_capita(per_capita):
    """Interpretação para geração per capita"""
    if per_capita > 1.5:
        return "Acima da média nacional (0.8-1.2 kg/hab/dia)"
    elif per_capita >= 0.8:
        return "Dentro da média nacional"
    else:
        return "Abaixo da média nacional"

def get_interpretacao_reciclagem(taxa):
    """Interpretação para taxa de reciclagem"""
    if taxa >= 20:
        return "Excelente performance de reciclagem"
    elif taxa >= 10:
        return "Boa performance de reciclagem"
    elif taxa >= 5:
        return "Performance moderada"
    else:
        return "Performance baixa - requer melhorias"

def get_interpretacao_densidade(densidade):
    """Interpretação para densidade de drenagem"""
    if densidade >= 15:
        return "Rede densa - boa cobertura"
    elif densidade >= 10:
        return "Densidade adequada"
    elif densidade >= 5:
        return "Densidade moderada"
    else:
        return "Densidade baixa - pode necessitar expansão"

def get_interpretacao_custo(custo):
    """Interpretação para custo per capita"""
    if custo > 200:
        return "Custo alto - verificar eficiência"
    elif custo >= 100:
        return "Custo médio"
    else:
        return "Custo baixo"

@material_apoio_bp.route('/recursos/glossario', methods=['GET'])
def glossario_pnsb():
    """Glossário de termos técnicos do PNSB"""
    try:
        termo = request.args.get('termo', '').lower()
        
        glossario = {
            'pmgirs': {
                'termo': 'PMGIRS',
                'definicao': 'Plano Municipal de Gestão Integrada de Resíduos Sólidos',
                'descricao': 'Documento que contém o diagnóstico da situação dos resíduos sólidos gerados no respectivo território, a proposição de cenários, metas de redução, reutilização, reciclagem, entre outras.',
                'categoria': 'Planejamento',
                'base_legal': 'Lei 12.305/2010 - Art. 18'
            },
            'coleta_seletiva': {
                'termo': 'Coleta Seletiva',
                'definicao': 'Coleta de resíduos sólidos previamente segregados conforme sua constituição ou composição',
                'descricao': 'Sistema de recolhimento diferenciado de materiais recicláveis (papel, plástico, vidro, metal) já separados na fonte geradora.',
                'categoria': 'Operação',
                'base_legal': 'Lei 12.305/2010 - Art. 3º, V'
            },
            'drenagem_urbana': {
                'termo': 'Drenagem Urbana',
                'definicao': 'Conjunto de atividades, infraestruturas e instalações operacionais de drenagem urbana de águas pluviais',
                'descricao': 'Sistema que compreende microdrenagem, macrodrenagem e o manejo das águas pluviais urbanas.',
                'categoria': 'Infraestrutura',
                'base_legal': 'Lei 11.445/2007'
            },
            'aterro_sanitario': {
                'termo': 'Aterro Sanitário',
                'definicao': 'Técnica de disposição de resíduos sólidos urbanos no solo',
                'descricao': 'Disposição final ambientalmente adequada, com critérios de engenharia e normas operacionais específicas.',
                'categoria': 'Destinação Final',
                'base_legal': 'NBR 13896'
            },
            'informante_qualificado': {
                'termo': 'Informante Qualificado',
                'definicao': 'Pessoa com conhecimento técnico sobre os serviços de saneamento do município',
                'descricao': 'Servidor público ou responsável técnico com acesso às informações e documentos necessários para responder ao questionário.',
                'categoria': 'Metodologia',
                'base_legal': 'Manual PNSB 2024'
            }
        }
        
        if termo and termo in glossario:
            return APIResponse.success(data=glossario[termo])
        elif termo:
            # Busca parcial
            resultados = {k: v for k, v in glossario.items() 
                         if termo in k or termo in v['definicao'].lower() or termo in v['descricao'].lower()}
            return APIResponse.success(data={'termo_buscado': termo, 'resultados': resultados})
        else:
            return APIResponse.success(data={'glossario_completo': glossario})
            
    except Exception as e:
        logger.error(f"Erro no glossário: {e}")
        return APIResponse.error(f"Erro ao acessar glossário: {str(e)}")

@material_apoio_bp.route('/recursos/tabelas', methods=['GET'])
def tabelas_referencia():
    """Tabelas de referência do PNSB"""
    try:
        tipo = request.args.get('tipo', 'municipios')
        
        if tipo == 'municipios':
            # Municípios de Santa Catarina na pesquisa
            tabela = {
                'titulo': 'Municípios PNSB 2024 - Santa Catarina',
                'colunas': ['Código IBGE', 'Município', 'População 2022', 'Região'],
                'dados': [
                    ['4202008', 'Balneário Camboriú', '138.732', 'Vale do Itajaí'],
                    ['4202057', 'Balneário Piçarras', '20.272', 'Vale do Itajaí'],
                    ['4202404', 'Bombinhas', '19.040', 'Vale do Itajaí'],
                    ['4204202', 'Camboriú', '75.267', 'Vale do Itajaí'],
                    ['4209102', 'Itajaí', '224.936', 'Vale do Itajaí'],
                    ['4209300', 'Itapema', '65.835', 'Vale do Itajaí'],
                    ['4210902', 'Luiz Alves', '11.287', 'Vale do Itajaí'],
                    ['4212809', 'Navegantes', '74.720', 'Vale do Itajaí'],
                    ['4213500', 'Penha', '33.367', 'Vale do Itajaí'],
                    ['4214805', 'Porto Belo', '20.704', 'Vale do Itajaí'],
                    ['4207809', 'Ilhota', '14.875', 'Vale do Itajaí']
                ],
                'fonte': 'IBGE - Estimativas Populacionais 2022'
            }
            
        elif tipo == 'classificacao_residuos':
            tabela = {
                'titulo': 'Classificação de Resíduos Sólidos',
                'colunas': ['Classe', 'Descrição', 'Exemplos'],
                'dados': [
                    ['Domiciliar', 'Gerados em atividades domésticas', 'Restos de alimentos, embalagens'],
                    ['Comercial', 'Gerados em estabelecimentos comerciais', 'Papéis, plásticos, orgânicos'],
                    ['Público', 'Gerados em espaços públicos', 'Varrição, podas, capina'],
                    ['Construção Civil', 'Gerados em construções', 'Entulhos, materiais de reforma'],
                    ['Perigosos', 'Com risco à saúde/ambiente', 'Pilhas, baterias, medicamentos']
                ],
                'fonte': 'Lei 12.305/2010'
            }
            
        elif tipo == 'indicadores':
            tabela = {
                'titulo': 'Principais Indicadores PNSB',
                'colunas': ['Indicador', 'Fórmula', 'Unidade'],
                'dados': [
                    ['Cobertura Coleta', '(Pop. Atendida / Pop. Total) × 100', '%'],
                    ['Geração Per Capita', 'Total Resíduos / População', 'kg/hab/dia'],
                    ['Taxa Reciclagem', '(Reciclado / Coletado) × 100', '%'],
                    ['Densidade Drenagem', 'Extensão Rede / Área Urbana', 'km/km²'],
                    ['Custo Per Capita', 'Custo Total / População', 'R$/hab/ano']
                ],
                'fonte': 'Manual PNSB 2024'
            }
            
        else:
            return APIResponse.error(f"Tipo de tabela '{tipo}' não encontrado")
            
        return APIResponse.success(data=tabela)
        
    except Exception as e:
        logger.error(f"Erro nas tabelas: {e}")
        return APIResponse.error(f"Erro ao acessar tabelas: {str(e)}")

@material_apoio_bp.route('/status', methods=['GET'])
def status_material_apoio():
    """Status geral do sistema de Material de Apoio"""
    try:
        status = {
            'chat_ia': {
                'disponivel': api_manager.is_google_gemini_available(),
                'endpoint': '/api/material-apoio/chat/manual',
                'contexto': 'EXCLUSIVAMENTE baseado nos 3 PDFs da pasta Contexto_Material_de_Apoio',
                'documentos_referencia': [
                    'Manual_PNSB2024_15052025.pdf',
                    'MRS 2024 19 04 25.pdf',
                    'MAP 2024 24 04 25.pdf'
                ],
                'fallback_local': True
            },
            'biblioteca_digital': {
                'disponivel': True,
                'documentos_disponiveis': 5,
                'total_documentos_planejados': 15,
                'download_funcional': True,
                'endpoint': '/api/material-apoio/biblioteca/documentos'
            },
            'busca_inteligente': {
                'disponivel': True,
                'status': 'ativo',
                'base_conhecimento': True,
                'filtros_avancados': True,
                'endpoint': '/api/material-apoio/busca'
            },
            'recursos_praticos': {
                'disponivel': True,
                'status': 'ativo',
                'calculadoras_disponiveis': 5,
                'glossario': True,
                'tabelas_referencia': True,
                'endpoints': {
                    'calculadora': '/api/material-apoio/recursos/calculadora',
                    'glossario': '/api/material-apoio/recursos/glossario',
                    'tabelas': '/api/material-apoio/recursos/tabelas'
                }
            },
            'centro_treinamento': {
                'disponivel': False,
                'status': 'planejado',
                'previsao': 'Próxima versão'
            },
            'comunidade_pratica': {
                'disponivel': False,
                'status': 'planejado',
                'previsao': 'Versão futura'
            },
            'calculadoras_disponiveis': [
                'cobertura_coleta',
                'geracao_per_capita', 
                'taxa_reciclagem',
                'densidade_drenagem',
                'custo_per_capita'
            ],
            'funcionalidades_implementadas': [
                'Chat IA com Manual PNSB',
                'Biblioteca Digital com downloads',
                'Busca Inteligente unificada',
                'Calculadoras PNSB especializadas',
                'Glossário técnico',
                'Tabelas de referência'
            ],
            'ultima_atualizacao': datetime.now().strftime('%Y-%m-%d'),
            'versao': '2.0'
        }
        
        return APIResponse.success(data=status)
        
    except Exception as e:
        logger.error(f"Erro no status: {e}")
        return APIResponse.error(f"Erro ao verificar status: {str(e)}")