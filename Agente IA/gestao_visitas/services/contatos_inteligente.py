from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import re
import requests
from sqlalchemy import and_, or_
from ..models.contatos import Contato, TipoEntidade, FonteInformacao
from ..models.agendamento import Visita
from ..db import db
import json

class ContatosInteligente:
    """Sistema inteligente de gestão de contatos"""
    
    def __init__(self, google_gemini_key: Optional[str] = None):
        self.gemini_key = google_gemini_key
        self.padroes_validacao = self._carregar_padroes_validacao()
        self.fontes_dados = self._configurar_fontes_dados()
    
    def enriquecer_contato_automatico(self, municipio: str, tipo_pesquisa: str) -> Dict:
        """Enriquece dados de contato automaticamente usando múltiplas fontes"""
        
        contato_existente = Contato.query.filter_by(
            municipio=municipio,
            tipo_pesquisa=tipo_pesquisa
        ).first()
        
        # Buscar dados atualizados
        dados_atualizados = self._buscar_dados_multiplas_fontes(municipio, tipo_pesquisa)
        
        # Validar e consolidar informações
        dados_validados = self._validar_e_consolidar_dados(dados_atualizados)
        
        # Detectar mudanças se contato já existe
        mudancas = {}
        if contato_existente:
            mudancas = self._detectar_mudancas(contato_existente, dados_validados)
        
        # Calcular score de confiabilidade
        score_confiabilidade = self._calcular_score_confiabilidade(dados_validados)
        
        return {
            'dados_enriquecidos': dados_validados,
            'mudancas_detectadas': mudancas,
            'score_confiabilidade': score_confiabilidade,
            'recomendacoes': self._gerar_recomendacoes_contato(dados_validados, score_confiabilidade),
            'proximas_acoes': self._sugerir_proximas_acoes(municipio, dados_validados, mudancas)
        }
    
    def validar_qualidade_contato(self, contato: Contato) -> Dict:
        """Valida qualidade e completude dos dados de contato"""
        
        validacao = {
            'score_qualidade': 0,
            'classificacao': '',
            'campos_validados': {},
            'inconsistencias': [],
            'sugestoes_melhoria': [],
            'nivel_confianca': ''
        }
        
        # Validar cada campo
        campos_para_validar = [
            'local', 'responsavel', 'endereco', 'contato', 'horario'
        ]
        
        total_pontos = 0
        pontos_obtidos = 0
        
        for campo in campos_para_validar:
            resultado_campo = self._validar_campo_contato(contato, campo)
            validacao['campos_validados'][campo] = resultado_campo
            
            total_pontos += resultado_campo['peso']
            pontos_obtidos += resultado_campo['pontos']
            
            if resultado_campo['inconsistencias']:
                validacao['inconsistencias'].extend(resultado_campo['inconsistencias'])
            
            if resultado_campo['sugestoes']:
                validacao['sugestoes_melhoria'].extend(resultado_campo['sugestoes'])
        
        # Calcular score final
        validacao['score_qualidade'] = round((pontos_obtidos / total_pontos) * 100, 1) if total_pontos > 0 else 0
        validacao['classificacao'] = self._classificar_qualidade_contato(validacao['score_qualidade'])
        validacao['nivel_confianca'] = self._avaliar_nivel_confianca(contato, validacao)
        
        return validacao
    
    def detectar_contatos_duplicados(self, municipio: str = None) -> List[Dict]:
        """Detecta possíveis contatos duplicados"""
        
        query = Contato.query
        if municipio:
            query = query.filter_by(municipio=municipio)
        
        contatos = query.all()
        duplicados = []
        
        for i, contato1 in enumerate(contatos):
            for contato2 in contatos[i+1:]:
                similaridade = self._calcular_similaridade_contatos(contato1, contato2)
                
                if similaridade['score'] > 0.8:  # 80% de similaridade
                    duplicados.append({
                        'contato1': contato1.to_dict(),
                        'contato2': contato2.to_dict(),
                        'similaridade': similaridade,
                        'recomendacao': self._gerar_recomendacao_duplicata(contato1, contato2, similaridade)
                    })
        
        return duplicados
    
    def sugerir_atualizacao_contato(self, contato_id: int) -> Dict:
        """Sugere atualizações para um contato baseado em análise inteligente"""
        
        contato = Contato.query.get(contato_id)
        if not contato:
            return {'erro': 'Contato não encontrado'}
        
        # Analisar histórico de visitas
        visitas_historico = Visita.query.filter_by(
            municipio=contato.municipio,
            tipo_pesquisa=contato.tipo_pesquisa
        ).order_by(Visita.data.desc()).limit(5).all()
        
        # Buscar dados atualizados online
        dados_externos = self._buscar_dados_externos(contato.municipio)
        
        # Analisar inconsistências nos dados atuais
        inconsistencias = self._analisar_inconsistencias_contato(contato)
        
        # Gerar sugestões baseadas em IA
        sugestoes_ia = self._gerar_sugestoes_ia(contato, visitas_historico, dados_externos)
        
        return {
            'contato_atual': contato.to_dict(),
            'historico_visitas': [v.to_dict() for v in visitas_historico],
            'dados_externos_encontrados': dados_externos,
            'inconsistencias_detectadas': inconsistencias,
            'sugestoes_atualizacao': sugestoes_ia,
            'prioridade_atualizacao': self._calcular_prioridade_atualizacao(contato, inconsistencias),
            'campos_prioritarios': self._identificar_campos_prioritarios(contato, inconsistencias)
        }
    
    def gerar_relatorio_qualidade_contatos(self, municipio: str = None) -> Dict:
        """Gera relatório de qualidade dos contatos"""
        
        query = Contato.query
        if municipio:
            query = query.filter_by(municipio=municipio)
        
        contatos = query.all()
        
        if not contatos:
            return {'total_contatos': 0, 'relatorio': 'Nenhum contato encontrado'}
        
        # Analisar qualidade de cada contato
        analises = []
        scores_qualidade = []
        
        for contato in contatos:
            validacao = self.validar_qualidade_contato(contato)
            analises.append({
                'contato_id': contato.id,
                'municipio': contato.municipio,
                'tipo_pesquisa': contato.tipo_pesquisa,
                'score_qualidade': validacao['score_qualidade'],
                'classificacao': validacao['classificacao'],
                'inconsistencias': len(validacao['inconsistencias'])
            })
            scores_qualidade.append(validacao['score_qualidade'])
        
        # Estatísticas gerais
        score_medio = sum(scores_qualidade) / len(scores_qualidade) if scores_qualidade else 0
        
        distribuicao_qualidade = {
            'excelente': len([s for s in scores_qualidade if s >= 90]),
            'boa': len([s for s in scores_qualidade if 70 <= s < 90]),
            'regular': len([s for s in scores_qualidade if 50 <= s < 70]),
            'ruim': len([s for s in scores_qualidade if s < 50])
        }
        
        # Identificar contatos problemáticos
        contatos_problemáticos = [a for a in analises if a['score_qualidade'] < 50]
        contatos_excellentes = [a for a in analises if a['score_qualidade'] >= 90]
        
        return {
            'total_contatos': len(contatos),
            'score_medio': round(score_medio, 1),
            'distribuicao_qualidade': distribuicao_qualidade,
            'contatos_problematicos': contatos_problemáticos,
            'contatos_excelentes': contatos_excellentes,
            'analises_detalhadas': analises,
            'recomendacoes_gerais': self._gerar_recomendacoes_gerais(analises),
            'municipios_com_lacunas': self._identificar_lacunas_cobertura(contatos)
        }
    
    def sincronizar_com_fonte_externa(self, fonte: str, municipio: str = None) -> Dict:
        """Sincroniza contatos com fonte externa de dados"""
        
        sincronizacao = {
            'fonte': fonte,
            'timestamp': datetime.now().isoformat(),
            'contatos_atualizados': 0,
            'novos_contatos': 0,
            'erros': [],
            'relatorio_mudancas': []
        }
        
        try:
            # Buscar dados da fonte externa
            dados_externos = self._conectar_fonte_externa(fonte, municipio)
            
            for municipio_dados in dados_externos:
                resultado_sync = self._sincronizar_municipio(municipio_dados, fonte)
                
                sincronizacao['contatos_atualizados'] += resultado_sync['atualizados']
                sincronizacao['novos_contatos'] += resultado_sync['novos']
                sincronizacao['relatorio_mudancas'].extend(resultado_sync['mudancas'])
                
                if resultado_sync['erros']:
                    sincronizacao['erros'].extend(resultado_sync['erros'])
        
        except Exception as e:
            sincronizacao['erros'].append(f"Erro na sincronização: {str(e)}")
        
        return sincronizacao
    
    def _carregar_padroes_validacao(self) -> Dict:
        """Carrega padrões de validação para diferentes campos"""
        return {
            'telefone': {
                'regex': r'^(?:\+55\s?)?(?:\([1-9]{2}\)\s?)?(?:9?\d{4}[-\s]?\d{4})$',
                'formatos_aceitos': ['(XX) 9XXXX-XXXX', '(XX) XXXX-XXXX', '+55 XX 9XXXX-XXXX']
            },
            'email': {
                'regex': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                'dominios_governo': ['.gov.br', '.sp.gov.br', '.sc.gov.br']
            },
            'horario': {
                'padroes': [
                    r'\d{1,2}h?\s*às?\s*\d{1,2}h?',
                    r'\d{1,2}:\d{2}\s*às?\s*\d{1,2}:\d{2}',
                    r'segunda\s*a\s*sexta',
                    r'seg\s*a\s*sex'
                ]
            },
            'endereco': {
                'componentes_obrigatorios': ['rua', 'numero', 'cidade', 'cep'],
                'formatos_cep': [r'\d{5}-\d{3}', r'\d{8}']
            }
        }
    
    def _configurar_fontes_dados(self) -> Dict:
        """Configura fontes de dados disponíveis"""
        return {
            'ia_pesquisa': {
                'ativa': bool(self.gemini_key),
                'confiabilidade': 0.7,
                'descricao': 'Pesquisa via IA Gemini'
            },
            'dados_publicos': {
                'ativa': True,
                'confiabilidade': 0.9,
                'descricao': 'Dados de portais governamentais'
            },
            'historico_visitas': {
                'ativa': True,
                'confiabilidade': 0.95,
                'descricao': 'Dados de visitas anteriores'
            }
        }
    
    def _buscar_dados_multiplas_fontes(self, municipio: str, tipo_pesquisa: str) -> Dict:
        """Busca dados em múltiplas fontes"""
        
        dados_consolidados = {
            'local': {'fontes': {}, 'consenso': '', 'confiabilidade': 0},
            'responsavel': {'fontes': {}, 'consenso': '', 'confiabilidade': 0},
            'endereco': {'fontes': {}, 'consenso': '', 'confiabilidade': 0},
            'contato': {'fontes': {}, 'consenso': '', 'confiabilidade': 0},
            'horario': {'fontes': {}, 'consenso': '', 'confiabilidade': 0}
        }
        
        # Buscar em histórico de visitas
        dados_historico = self._buscar_dados_historico_visitas(municipio, tipo_pesquisa)
        if dados_historico:
            for campo, valor in dados_historico.items():
                if valor:
                    dados_consolidados[campo]['fontes']['historico_visitas'] = {
                        'valor': valor,
                        'confiabilidade': 0.95,
                        'data_atualizacao': datetime.now().isoformat()
                    }
        
        # Buscar via IA se disponível
        if self.gemini_key:
            dados_ia = self._buscar_dados_via_ia(municipio, tipo_pesquisa)
            if dados_ia:
                for campo, valor in dados_ia.items():
                    if valor:
                        dados_consolidados[campo]['fontes']['ia_pesquisa'] = {
                            'valor': valor,
                            'confiabilidade': 0.7,
                            'data_atualizacao': datetime.now().isoformat()
                        }
        
        # Consolidar consenso para cada campo
        for campo in dados_consolidados:
            dados_consolidados[campo]['consenso'], dados_consolidados[campo]['confiabilidade'] = \
                self._calcular_consenso_campo(dados_consolidados[campo]['fontes'])
        
        return dados_consolidados
    
    def _validar_e_consolidar_dados(self, dados_multiplas_fontes: Dict) -> Dict:
        """Valida e consolida dados de múltiplas fontes"""
        
        dados_validados = {}
        
        for campo, info_campo in dados_multiplas_fontes.items():
            valor_consenso = info_campo['consenso']
            
            if valor_consenso:
                # Aplicar validação específica do campo
                validacao = self._validar_formato_campo(campo, valor_consenso)
                
                dados_validados[campo] = {
                    'valor': valor_consenso,
                    'valido': validacao['valido'],
                    'confiabilidade': info_campo['confiabilidade'],
                    'observacoes_validacao': validacao['observacoes'],
                    'fontes_consultadas': list(info_campo['fontes'].keys())
                }
        
        return dados_validados
    
    def _detectar_mudancas(self, contato_existente: Contato, dados_novos: Dict) -> Dict:
        """Detecta mudanças nos dados de contato"""
        
        mudancas = {}
        
        mapeamento_campos = {
            'local': 'local_mais_provavel',
            'responsavel': 'responsavel_mais_provavel',
            'endereco': 'endereco_mais_provavel',
            'contato': 'contato_mais_provavel',
            'horario': 'horario_mais_provavel'
        }
        
        for campo_novo, campo_bd in mapeamento_campos.items():
            valor_atual = getattr(contato_existente, campo_bd, '')
            valor_novo = dados_novos.get(campo_novo, {}).get('valor', '')
            
            if valor_novo and valor_atual != valor_novo:
                mudancas[campo_novo] = {
                    'valor_anterior': valor_atual,
                    'valor_novo': valor_novo,
                    'confiabilidade_mudanca': dados_novos[campo_novo]['confiabilidade'],
                    'tipo_mudanca': self._classificar_tipo_mudanca(valor_atual, valor_novo),
                    'recomendacao': self._recomendar_acao_mudanca(campo_novo, valor_atual, valor_novo)
                }
        
        return mudancas
    
    def _calcular_score_confiabilidade(self, dados_validados: Dict) -> float:
        """Calcula score de confiabilidade dos dados"""
        
        if not dados_validados:
            return 0.0
        
        scores_individuais = []
        
        for campo, info in dados_validados.items():
            if info['valido']:
                score_campo = info['confiabilidade'] * 0.8  # Base de confiabilidade
                
                # Bonus por múltiplas fontes
                num_fontes = len(info['fontes_consultadas'])
                bonus_fontes = min(num_fontes * 0.1, 0.2)  # Máximo 20% bonus
                
                score_final_campo = min(score_campo + bonus_fontes, 1.0)
                scores_individuais.append(score_final_campo)
            else:
                scores_individuais.append(0.0)
        
        return round(sum(scores_individuais) / len(scores_individuais), 2) if scores_individuais else 0.0
    
    def _gerar_recomendacoes_contato(self, dados_validados: Dict, score_confiabilidade: float) -> List[str]:
        """Gera recomendações baseadas nos dados validados"""
        
        recomendacoes = []
        
        if score_confiabilidade < 0.5:
            recomendacoes.append("⚠️ Dados com baixa confiabilidade - recomenda-se validação manual")
        
        # Verificar campos específicos
        if 'contato' in dados_validados and not dados_validados['contato']['valido']:
            recomendacoes.append("📞 Contato telefônico parece inválido - verificar formato")
        
        campos_faltantes = [campo for campo in ['local', 'responsavel', 'contato'] 
                           if campo not in dados_validados or not dados_validados[campo]['valor']]
        
        if campos_faltantes:
            recomendacoes.append(f"📝 Campos faltantes: {', '.join(campos_faltantes)}")
        
        return recomendacoes
    
    def _sugerir_proximas_acoes(self, municipio: str, dados_validados: Dict, mudancas: Dict) -> List[Dict]:
        """Sugere próximas ações baseadas na análise"""
        
        acoes = []
        
        if mudancas:
            acoes.append({
                'acao': 'Confirmar mudanças detectadas',
                'prioridade': 'alta',
                'detalhes': f"{len(mudancas)} mudança(s) detectada(s)",
                'tempo_estimado': '10 min'
            })
        
        # Verificar última visita
        ultima_visita = Visita.query.filter_by(municipio=municipio).order_by(Visita.data.desc()).first()
        
        if not ultima_visita or (datetime.now().date() - ultima_visita.data).days > 180:
            acoes.append({
                'acao': 'Agendar visita de atualização',
                'prioridade': 'media',
                'detalhes': 'Dados podem estar desatualizados',
                'tempo_estimado': '60 min'
            })
        
        return acoes
    
    def _validar_campo_contato(self, contato: Contato, campo: str) -> Dict:
        """Valida um campo específico do contato"""
        
        resultado = {
            'valido': False,
            'peso': 20,  # Peso padrão
            'pontos': 0,
            'inconsistencias': [],
            'sugestoes': []
        }
        
        # Obter valores do campo de diferentes fontes
        valores_campo = {
            'mais_provavel': getattr(contato, f'{campo}_mais_provavel', ''),
            'chatgpt': getattr(contato, f'{campo}_chatgpt', ''),
            'gemini': getattr(contato, f'{campo}_gemini', ''),
            'grok': getattr(contato, f'{campo}_grok', '')
        }
        
        # Verificar se há pelo menos um valor
        valores_preenchidos = [v for v in valores_campo.values() if v]
        
        if not valores_preenchidos:
            resultado['sugestoes'].append(f"Campo '{campo}' completamente vazio")
            return resultado
        
        # Dar pontos por ter valor
        resultado['pontos'] += 10
        
        # Validar formato se aplicável
        valor_principal = valores_campo['mais_provavel'] or valores_preenchidos[0]
        
        if campo == 'contato':
            if self._validar_telefone(valor_principal):
                resultado['pontos'] += 10
                resultado['valido'] = True
            else:
                resultado['inconsistencias'].append("Formato de telefone inválido")
        
        elif campo == 'horario':
            if self._validar_horario(valor_principal):
                resultado['pontos'] += 10
                resultado['valido'] = True
            else:
                resultado['inconsistencias'].append("Formato de horário não padronizado")
        
        else:
            # Para outros campos, verificar se não está vazio
            if len(valor_principal.strip()) > 0:
                resultado['pontos'] += 10
                resultado['valido'] = True
        
        # Verificar consistência entre fontes
        valores_unicos = set(v for v in valores_preenchidos if v)
        if len(valores_unicos) > 1:
            resultado['inconsistencias'].append(f"Inconsistência entre fontes de dados para '{campo}'")
        else:
            resultado['pontos'] += 5  # Bonus por consistência
        
        return resultado
    
    def _validar_telefone(self, telefone: str) -> bool:
        """Valida formato de telefone"""
        if not telefone:
            return False
        
        padrao = self.padroes_validacao['telefone']['regex']
        return bool(re.match(padrao, telefone))
    
    def _validar_horario(self, horario: str) -> bool:
        """Valida formato de horário"""
        if not horario:
            return False
        
        for padrao in self.padroes_validacao['horario']['padroes']:
            if re.search(padrao, horario.lower()):
                return True
        
        return False
    
    def _classificar_qualidade_contato(self, score: float) -> str:
        """Classifica qualidade do contato baseado no score"""
        if score >= 90:
            return "Excelente"
        elif score >= 75:
            return "Boa"
        elif score >= 60:
            return "Regular"
        elif score >= 40:
            return "Ruim"
        else:
            return "Crítica"
    
    def _avaliar_nivel_confianca(self, contato: Contato, validacao: Dict) -> str:
        """Avalia nível de confiança nos dados"""
        
        # Verificar data de atualização
        dias_desde_atualizacao = (datetime.now() - contato.data_atualizacao).days if contato.data_atualizacao else 365
        
        if validacao['score_qualidade'] >= 80 and dias_desde_atualizacao <= 30:
            return "Alto"
        elif validacao['score_qualidade'] >= 60 and dias_desde_atualizacao <= 90:
            return "Médio"
        else:
            return "Baixo"
    
    # Métodos auxiliares adicionais (simplificados para brevidade)
    
    def _calcular_similaridade_contatos(self, contato1: Contato, contato2: Contato) -> Dict:
        """Calcula similaridade entre dois contatos"""
        # Implementação simplificada
        return {'score': 0.0, 'campos_similares': []}
    
    def _buscar_dados_historico_visitas(self, municipio: str, tipo_pesquisa: str) -> Dict:
        """Busca dados do histórico de visitas"""
        # Implementação simplificada
        return {}
    
    def _buscar_dados_via_ia(self, municipio: str, tipo_pesquisa: str) -> Dict:
        """Busca dados via IA"""
        # Implementação simplificada
        return {}
    
    def _calcular_consenso_campo(self, fontes: Dict) -> Tuple[str, float]:
        """Calcula consenso entre diferentes fontes"""
        if not fontes:
            return '', 0.0
        
        # Implementação simplificada - retorna fonte mais confiável
        fonte_mais_confiavel = max(fontes.items(), key=lambda x: x[1]['confiabilidade'])
        return fonte_mais_confiavel[1]['valor'], fonte_mais_confiavel[1]['confiabilidade']
    
    def _validar_formato_campo(self, campo: str, valor: str) -> Dict:
        """Valida formato específico de um campo"""
        return {'valido': True, 'observacoes': []}
    
    def _classificar_tipo_mudanca(self, valor_anterior: str, valor_novo: str) -> str:
        """Classifica tipo de mudança"""
        if not valor_anterior:
            return "adicao"
        elif not valor_novo:
            return "remocao"
        else:
            return "atualizacao"
    
    def _recomendar_acao_mudanca(self, campo: str, valor_anterior: str, valor_novo: str) -> str:
        """Recomenda ação para mudança detectada"""
        return f"Verificar se mudança em '{campo}' está correta"
    
    def _gerar_recomendacoes_gerais(self, analises: List[Dict]) -> List[str]:
        """Gera recomendações gerais baseadas nas análises"""
        recomendacoes = []
        
        contatos_ruins = [a for a in analises if a['score_qualidade'] < 50]
        if len(contatos_ruins) > len(analises) * 0.3:
            recomendacoes.append("📊 Mais de 30% dos contatos com qualidade ruim - revisar processo de coleta")
        
        return recomendacoes
    
    def _identificar_lacunas_cobertura(self, contatos: List[Contato]) -> List[str]:
        """Identifica lacunas na cobertura de contatos"""
        from ..config import MUNICIPIOS, TIPOS_PESQUISA
        
        lacunas = []
        
        municipios_com_contato = set(c.municipio for c in contatos)
        municipios_sem_contato = set(MUNICIPIOS) - municipios_com_contato
        
        if municipios_sem_contato:
            lacunas.extend([f"Município sem contatos: {m}" for m in municipios_sem_contato])
        
        return lacunas