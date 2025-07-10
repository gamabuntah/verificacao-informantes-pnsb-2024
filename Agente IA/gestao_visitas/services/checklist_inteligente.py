from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from ..models.agendamento import Visita
from ..models.checklist import Checklist
from ..models.contatos import Contato
from ..db import db
import json

class ChecklistInteligente:
    """Sistema inteligente de checklist adaptativo"""
    
    def __init__(self):
        self.templates_base = self._carregar_templates_base()
        self.regras_adaptacao = self._carregar_regras_adaptacao()
    
    def gerar_checklist_personalizado(self, visita: Visita) -> Dict:
        """Gera checklist personalizado baseado no contexto da visita"""
        
        # Base do template
        template_base = self.templates_base.get(
            (visita.tipo_pesquisa, visita.tipo_informante),
            self.templates_base[('DEFAULT', 'DEFAULT')]
        )
        
        # Adaptações baseadas no contexto
        adaptacoes = self._analisar_contexto_visita(visita)
        
        # Aplicar adaptações
        checklist_personalizado = self._aplicar_adaptacoes(template_base, adaptacoes)
        
        # Adicionar itens baseados no histórico
        itens_historico = self._sugerir_baseado_historico(visita.municipio, visita.tipo_pesquisa)
        
        # Adicionar verificações sazonais
        itens_sazonais = self._adicionar_verificacoes_sazonais(visita.data)
        
        return {
            'checklist_base': checklist_personalizado,
            'itens_historico': itens_historico,
            'itens_sazonais': itens_sazonais,
            'prioridades': self._calcular_prioridades(checklist_personalizado),
            'tempo_estimado': self._estimar_tempo_checklist(checklist_personalizado),
            'alertas': self._gerar_alertas_contextuais(visita, adaptacoes)
        }
    
    def validar_completude_inteligente(self, checklist: Checklist, visita: Visita) -> Dict:
        """Valida completude do checklist com inteligência contextual"""
        
        campos_obrigatorios = self._obter_campos_obrigatorios(visita)
        campos_recomendados = self._obter_campos_recomendados(visita)
        campos_opcionais = self._obter_campos_opcionais(visita)
        
        validacao = {
            'obrigatorios': {'total': len(campos_obrigatorios), 'completos': 0, 'faltantes': []},
            'recomendados': {'total': len(campos_recomendados), 'completos': 0, 'faltantes': []},
            'opcionais': {'total': len(campos_opcionais), 'completos': 0, 'faltantes': []},
            'score_completude': 0,
            'bloqueadores': [],
            'recomendacoes': []
        }
        
        # Verificar campos obrigatórios
        for campo in campos_obrigatorios:
            if getattr(checklist, campo, False):
                validacao['obrigatorios']['completos'] += 1
            else:
                validacao['obrigatorios']['faltantes'].append(campo)
        
        # Verificar campos recomendados
        for campo in campos_recomendados:
            if getattr(checklist, campo, False):
                validacao['recomendados']['completos'] += 1
            else:
                validacao['recomendados']['faltantes'].append(campo)
        
        # Verificar campos opcionais
        for campo in campos_opcionais:
            if getattr(checklist, campo, False):
                validacao['opcionais']['completos'] += 1
            else:
                validacao['opcionais']['faltantes'].append(campo)
        
        # Calcular score
        score_obrigatorio = (validacao['obrigatorios']['completos'] / max(validacao['obrigatorios']['total'], 1)) * 60
        score_recomendado = (validacao['recomendados']['completos'] / max(validacao['recomendados']['total'], 1)) * 30
        score_opcional = (validacao['opcionais']['completos'] / max(validacao['opcionais']['total'], 1)) * 10
        
        validacao['score_completude'] = round(score_obrigatorio + score_recomendado + score_opcional, 1)
        
        # Gerar bloqueadores e recomendações
        validacao['bloqueadores'] = self._identificar_bloqueadores(validacao, visita)
        validacao['recomendacoes'] = self._gerar_recomendacoes_completude(validacao, visita)
        
        return validacao
    
    def sugerir_proximo_passo(self, checklist: Checklist, visita: Visita) -> Dict:
        """Sugere próximo passo baseado no estado atual"""
        
        etapa_atual = self._identificar_etapa_atual(visita)
        progresso_etapa = self._calcular_progresso_etapa(checklist, etapa_atual)
        
        sugestoes = []
        
        if etapa_atual == 'antes_visita':
            if not checklist.cracha_ibge:
                sugestoes.append({
                    'acao': 'Verificar crachá IBGE',
                    'prioridade': 'alta',
                    'categoria': 'identificacao',
                    'tempo_estimado': '2 min'
                })
            
            if not checklist.planejamento_rota:
                sugestoes.append({
                    'acao': 'Planejar rota de viagem',
                    'prioridade': 'alta',
                    'categoria': 'logistica',
                    'tempo_estimado': '10 min'
                })
        
        elif etapa_atual == 'durante_visita':
            if not checklist.apresentacao_ibge:
                sugestoes.append({
                    'acao': 'Realizar apresentação do IBGE',
                    'prioridade': 'critica',
                    'categoria': 'apresentacao',
                    'tempo_estimado': '5 min'
                })
            
            if visita.tipo_pesquisa == 'MRS' and not checklist.validacao_prestadores:
                sugestoes.append({
                    'acao': 'Validar prestadores de serviço',
                    'prioridade': 'alta',
                    'categoria': 'validacao',
                    'tempo_estimado': '15 min'
                })
        
        elif etapa_atual == 'apos_visita':
            if not checklist.registro_followup:
                sugestoes.append({
                    'acao': 'Registrar necessidade de follow-up',
                    'prioridade': 'media',
                    'categoria': 'followup',
                    'tempo_estimado': '5 min'
                })
        
        return {
            'etapa_atual': etapa_atual,
            'progresso_etapa': progresso_etapa,
            'sugestoes': sugestoes,
            'proxima_etapa': self._calcular_proxima_etapa(etapa_atual, progresso_etapa),
            'tempo_total_estimado': sum(int(s['tempo_estimado'].split()[0]) for s in sugestoes)
        }
    
    def gerar_relatorio_qualidade(self, checklist: Checklist, visita: Visita) -> Dict:
        """Gera relatório de qualidade da execução do checklist"""
        
        validacao = self.validar_completude_inteligente(checklist, visita)
        historico_municipio = self._analisar_historico_municipio(visita.municipio)
        
        # Comparar com média do município
        score_medio_municipio = historico_municipio.get('score_medio', 80)
        desempenho_relativo = validacao['score_completude'] - score_medio_municipio
        
        # Identificar pontos fortes e fracos
        pontos_fortes = self._identificar_pontos_fortes(checklist, visita)
        pontos_melhoria = self._identificar_pontos_melhoria(checklist, visita)
        
        # Sugestões de melhoria
        sugestoes_melhoria = self._gerar_sugestoes_melhoria(checklist, visita, historico_municipio)
        
        return {
            'score_qualidade': validacao['score_completude'],
            'classificacao': self._classificar_qualidade(validacao['score_completude']),
            'desempenho_relativo': {
                'valor': round(desempenho_relativo, 1),
                'status': 'acima' if desempenho_relativo > 0 else 'abaixo' if desempenho_relativo < 0 else 'igual',
                'referencia': score_medio_municipio
            },
            'pontos_fortes': pontos_fortes,
            'pontos_melhoria': pontos_melhoria,
            'sugestoes_melhoria': sugestoes_melhoria,
            'comparacao_historica': historico_municipio
        }
    
    def detectar_anomalias(self, checklist: Checklist, visita: Visita) -> List[Dict]:
        """Detecta anomalias no preenchimento do checklist"""
        
        anomalias = []
        
        # Tempo de preenchimento anômalo
        if checklist.data_atualizacao and checklist.data_criacao:
            tempo_preenchimento = (checklist.data_atualizacao - checklist.data_criacao).total_seconds() / 60
            if tempo_preenchimento < 5:  # Muito rápido
                anomalias.append({
                    'tipo': 'tempo_preenchimento',
                    'severidade': 'media',
                    'descricao': f'Checklist preenchido muito rapidamente ({tempo_preenchimento:.1f} min)',
                    'recomendacao': 'Verificar se todos os itens foram adequadamente validados'
                })
            elif tempo_preenchimento > 180:  # Muito lento
                anomalias.append({
                    'tipo': 'tempo_preenchimento',
                    'severidade': 'baixa',
                    'descricao': f'Checklist levou muito tempo para ser preenchido ({tempo_preenchimento/60:.1f} horas)',
                    'recomendacao': 'Considerar melhorias no processo de checklist'
                })
        
        # Padrões inconsistentes
        if visita.tipo_pesquisa == 'MRS':
            if checklist.questionario_mrs_digital and not checklist.questionario_mrs_impresso:
                anomalias.append({
                    'tipo': 'inconsistencia_material',
                    'severidade': 'alta',
                    'descricao': 'Questionário MRS digital marcado mas não o impresso',
                    'recomendacao': 'Verificar se ambas as versões foram levadas'
                })
        
        # Observações vazias em etapas críticas
        if not checklist.observacoes_durante and visita.status in ['em execução', 'realizada']:
            anomalias.append({
                'tipo': 'observacoes_faltantes',
                'severidade': 'media',
                'descricao': 'Observações da etapa "Durante a Visita" estão vazias',
                'recomendacao': 'Adicionar observações sobre o andamento da visita'
            })
        
        return anomalias
    
    def _carregar_templates_base(self) -> Dict:
        """Carrega templates base de checklist"""
        return {
            ('MRS', 'prefeitura'): {
                'antes_visita': [
                    'cracha_ibge', 'recibo_entrega', 'questionario_mrs_impresso',
                    'questionario_mrs_digital', 'carta_oficial', 'manual_pnsb',
                    'guia_site_externo', 'card_contato', 'audio_explicativo',
                    'planejamento_rota', 'agenda_confirmada'
                ],
                'durante_visita': [
                    'apresentacao_ibge', 'explicacao_objetivo', 'explicacao_estrutura',
                    'explicacao_data_referencia', 'explicacao_prestador', 'explicacao_servicos',
                    'explicacao_site_externo', 'explicacao_pdf_editavel', 'validacao_prestadores',
                    'registro_contatos', 'assinatura_informante'
                ],
                'apos_visita': [
                    'devolucao_materiais', 'registro_followup', 'combinacao_entrega',
                    'combinacao_acompanhamento', 'observacoes_finais'
                ]
            },
            ('MAP', 'prefeitura'): {
                'antes_visita': [
                    'cracha_ibge', 'recibo_entrega', 'questionario_map_impresso',
                    'questionario_map_digital', 'carta_oficial', 'manual_pnsb',
                    'planejamento_rota', 'agenda_confirmada'
                ],
                'durante_visita': [
                    'apresentacao_ibge', 'explicacao_objetivo', 'explicacao_estrutura',
                    'explicacao_data_referencia', 'registro_contatos', 'assinatura_informante'
                ],
                'apos_visita': [
                    'devolucao_materiais', 'registro_followup', 'combinacao_entrega',
                    'observacoes_finais'
                ]
            },
            ('DEFAULT', 'DEFAULT'): {
                'antes_visita': ['cracha_ibge', 'recibo_entrega', 'carta_oficial'],
                'durante_visita': ['apresentacao_ibge', 'registro_contatos'],
                'apos_visita': ['observacoes_finais']
            }
        }
    
    def _carregar_regras_adaptacao(self) -> Dict:
        """Carrega regras de adaptação do checklist"""
        return {
            'primeira_visita_municipio': {
                'adicionar': ['validacao_dados_contato', 'mapeamento_estrutura_organizacional'],
                'enfatizar': ['apresentacao_ibge', 'explicacao_objetivo']
            },
            'visita_followup': {
                'adicionar': ['verificacao_pendencias_anteriores', 'validacao_dados_atualizados'],
                'remover': ['apresentacao_ibge']
            },
            'municipio_pequeno': {
                'adaptar': {'tempo_estimado': -15, 'complexidade': 'baixa'}
            },
            'municipio_grande': {
                'adaptar': {'tempo_estimado': +30, 'complexidade': 'alta'},
                'adicionar': ['mapeamento_departamentos', 'validacao_multiplos_contatos']
            }
        }
    
    def _analisar_contexto_visita(self, visita: Visita) -> Dict:
        """Analisa contexto específico da visita"""
        contexto = {
            'primeira_visita_municipio': self._eh_primeira_visita_municipio(visita),
            'visita_followup': 'follow-up' in visita.observacoes.lower() if visita.observacoes else False,
            'municipio_porte': self._classificar_porte_municipio(visita.municipio),
            'historico_municipio': self._obter_historico_municipio(visita.municipio)
        }
        
        return contexto
    
    def _aplicar_adaptacoes(self, template_base: Dict, adaptacoes: Dict) -> Dict:
        """Aplica adaptações ao template base"""
        checklist_adaptado = template_base.copy()
        
        for contexto, regra in self.regras_adaptacao.items():
            if adaptacoes.get(contexto):
                # Adicionar itens
                if 'adicionar' in regra:
                    for etapa in checklist_adaptado:
                        if etapa in ['antes_visita', 'durante_visita', 'apos_visita']:
                            checklist_adaptado[etapa].extend(regra['adicionar'])
                
                # Remover itens
                if 'remover' in regra:
                    for etapa in checklist_adaptado:
                        if etapa in ['antes_visita', 'durante_visita', 'apos_visita']:
                            for item in regra['remover']:
                                if item in checklist_adaptado[etapa]:
                                    checklist_adaptado[etapa].remove(item)
        
        return checklist_adaptado
    
    def _sugerir_baseado_historico(self, municipio: str, tipo_pesquisa: str) -> List[Dict]:
        """Sugere itens baseado no histórico do município"""
        
        # Buscar visitas anteriores
        visitas_anteriores = Visita.query.filter_by(
            municipio=municipio,
            tipo_pesquisa=tipo_pesquisa,
            status='realizada'
        ).limit(5).all()
        
        sugestoes = []
        
        if visitas_anteriores:
            # Analisar observações anteriores para sugerir verificações
            observacoes_historicas = [v.observacoes for v in visitas_anteriores if v.observacoes]
            
            palavras_chave = {
                'prestador': 'Verificar mudanças nos prestadores de serviço',
                'contrato': 'Validar situação atual dos contratos',
                'terceirizado': 'Confirmar empresas terceirizadas ativas',
                'catador': 'Mapear entidades de catadores atualizadas'
            }
            
            for palavra, sugestao in palavras_chave.items():
                if any(palavra in obs.lower() for obs in observacoes_historicas):
                    sugestoes.append({
                        'item': sugestao,
                        'baseado_em': 'histórico_municipio',
                        'prioridade': 'alta'
                    })
        
        return sugestoes
    
    def _adicionar_verificacoes_sazonais(self, data_visita) -> List[Dict]:
        """Adiciona verificações baseadas na época do ano"""
        sazonais = []
        
        mes = data_visita.month
        
        # Verificações de final/início de ano
        if mes in [11, 12, 1]:
            sazonais.append({
                'item': 'Verificar planejamento orçamentário para próximo ano',
                'motivo': 'Período de planejamento orçamentário',
                'categoria': 'sazonal'
            })
        
        # Verificações de período chuvoso (verão)
        if mes in [12, 1, 2, 3]:
            sazonais.append({
                'item': 'Verificar funcionamento sistema drenagem período chuvoso',
                'motivo': 'Período de chuvas intensas',
                'categoria': 'sazonal'
            })
        
        return sazonais
    
    # Métodos auxiliares continuam...
    
    def _eh_primeira_visita_municipio(self, visita: Visita) -> bool:
        """Verifica se é a primeira visita ao município"""
        visitas_anteriores = Visita.query.filter(
            Visita.municipio == visita.municipio,
            Visita.id != visita.id,
            Visita.status.in_(['realizada', 'finalizada'])
        ).count()
        
        return visitas_anteriores == 0
    
    def _classificar_porte_municipio(self, municipio: str) -> str:
        """Classifica porte do município (simplificado)"""
        municipios_grandes = ['Itajaí', 'Balneário Camboriú']
        municipios_pequenos = ['Luiz Alves', 'Porto Belo', 'Ilhota']
        
        if municipio in municipios_grandes:
            return 'grande'
        elif municipio in municipios_pequenos:
            return 'pequeno'
        return 'medio'
    
    def _obter_historico_municipio(self, municipio: str) -> Dict:
        """Obtém histórico de visitas do município"""
        visitas = Visita.query.filter_by(municipio=municipio, status='realizada').all()
        
        if not visitas:
            return {'visitas_realizadas': 0, 'score_medio': 80}
        
        return {
            'visitas_realizadas': len(visitas),
            'ultima_visita': max(v.data for v in visitas).strftime('%d/%m/%Y'),
            'score_medio': 85  # Simplificado
        }
    
    def _calcular_prioridades(self, checklist: Dict) -> Dict:
        """Calcula prioridades dos itens do checklist"""
        prioridades = {
            'critica': ['cracha_ibge', 'apresentacao_ibge', 'assinatura_informante'],
            'alta': ['carta_oficial', 'explicacao_objetivo', 'registro_contatos'],
            'media': ['manual_pnsb', 'planejamento_rota', 'observacoes_finais'],
            'baixa': ['audio_explicativo', 'card_contato']
        }
        
        return prioridades
    
    def _estimar_tempo_checklist(self, checklist: Dict) -> Dict:
        """Estima tempo necessário para completar checklist"""
        tempos_por_etapa = {
            'antes_visita': 30,
            'durante_visita': 45,
            'apos_visita': 15
        }
        
        tempo_total = sum(tempos_por_etapa.get(etapa, 0) for etapa in checklist.keys())
        
        return {
            'tempo_total_min': tempo_total,
            'tempos_por_etapa': tempos_por_etapa,
            'estimativa': 'baseada_em_historico'
        }
    
    def _gerar_alertas_contextuais(self, visita: Visita, adaptacoes: Dict) -> List[str]:
        """Gera alertas baseados no contexto"""
        alertas = []
        
        if adaptacoes.get('primeira_visita_municipio'):
            alertas.append("🆕 Primeira visita ao município - dedicar tempo extra para apresentação")
        
        if adaptacoes.get('municipio_porte') == 'grande':
            alertas.append("🏢 Município grande - pode haver múltiplos departamentos envolvidos")
        
        return alertas
    
    def _obter_campos_obrigatorios(self, visita: Visita) -> List[str]:
        """Obtém campos obrigatórios baseado no tipo de visita"""
        base = ['cracha_ibge', 'apresentacao_ibge', 'registro_contatos']
        
        if visita.tipo_pesquisa == 'MRS':
            base.extend(['questionario_mrs_impresso', 'validacao_prestadores'])
        elif visita.tipo_pesquisa == 'MAP':
            base.extend(['questionario_map_impresso'])
        
        return base
    
    def _obter_campos_recomendados(self, visita: Visita) -> List[str]:
        """Obtém campos recomendados"""
        return ['carta_oficial', 'manual_pnsb', 'explicacao_objetivo', 'observacoes_finais']
    
    def _obter_campos_opcionais(self, visita: Visita) -> List[str]:
        """Obtém campos opcionais"""
        return ['audio_explicativo', 'card_contato', 'guia_site_externo']
    
    def _identificar_bloqueadores(self, validacao: Dict, visita: Visita) -> List[str]:
        """Identifica bloqueadores críticos"""
        bloqueadores = []
        
        if 'cracha_ibge' in validacao['obrigatorios']['faltantes']:
            bloqueadores.append("❌ Crachá IBGE obrigatório para identificação")
        
        if 'assinatura_informante' in validacao['obrigatorios']['faltantes'] and visita.status == 'realizada':
            bloqueadores.append("❌ Assinatura do informante obrigatória para visita realizada")
        
        return bloqueadores
    
    def _gerar_recomendacoes_completude(self, validacao: Dict, visita: Visita) -> List[str]:
        """Gera recomendações para melhorar completude"""
        recomendacoes = []
        
        if validacao['score_completude'] < 70:
            recomendacoes.append("📈 Score baixo - revisar itens obrigatórios não completados")
        
        if len(validacao['recomendados']['faltantes']) > 2:
            recomendacoes.append("💡 Considerar completar itens recomendados para melhor qualidade")
        
        return recomendacoes
    
    def _identificar_etapa_atual(self, visita: Visita) -> str:
        """Identifica etapa atual da visita"""
        if visita.status in ['agendada', 'em preparação']:
            return 'antes_visita'
        elif visita.status in ['em execução']:
            return 'durante_visita'
        else:
            return 'apos_visita'
    
    def _calcular_progresso_etapa(self, checklist: Checklist, etapa: str) -> float:
        """Calcula progresso da etapa atual"""
        # Simplificado - seria mais elaborado na implementação real
        return 0.0
    
    def _calcular_proxima_etapa(self, etapa_atual: str, progresso: float) -> Optional[str]:
        """Calcula próxima etapa baseada no progresso"""
        if progresso >= 0.8:
            etapas = ['antes_visita', 'durante_visita', 'apos_visita']
            idx_atual = etapas.index(etapa_atual)
            if idx_atual < len(etapas) - 1:
                return etapas[idx_atual + 1]
        return None
    
    def _analisar_historico_municipio(self, municipio: str) -> Dict:
        """Analisa histórico completo do município"""
        return self._obter_historico_municipio(municipio)
    
    def _identificar_pontos_fortes(self, checklist: Checklist, visita: Visita) -> List[str]:
        """Identifica pontos fortes da execução"""
        pontos_fortes = []
        
        if checklist.cracha_ibge and checklist.carta_oficial:
            pontos_fortes.append("✅ Identificação e documentação oficial completas")
        
        if checklist.observacoes_durante and len(checklist.observacoes_durante) > 50:
            pontos_fortes.append("✅ Observações detalhadas durante a visita")
        
        return pontos_fortes
    
    def _identificar_pontos_melhoria(self, checklist: Checklist, visita: Visita) -> List[str]:
        """Identifica pontos de melhoria"""
        pontos_melhoria = []
        
        if not checklist.planejamento_rota:
            pontos_melhoria.append("⚠️ Planejamento de rota não documentado")
        
        if not checklist.observacoes_apos:
            pontos_melhoria.append("⚠️ Observações pós-visita ausentes")
        
        return pontos_melhoria
    
    def _gerar_sugestoes_melhoria(self, checklist: Checklist, visita: Visita, historico: Dict) -> List[str]:
        """Gera sugestões específicas de melhoria"""
        sugestoes = []
        
        if historico['visitas_realizadas'] > 0:
            sugestoes.append("💡 Revisar observações de visitas anteriores para este município")
        
        sugestoes.append("📋 Considerar criar template específico para este tipo de visita")
        
        return sugestoes
    
    def _classificar_qualidade(self, score: float) -> str:
        """Classifica qualidade baseada no score"""
        if score >= 90:
            return "Excelente"
        elif score >= 80:
            return "Boa"
        elif score >= 70:
            return "Regular"
        elif score >= 60:
            return "Ruim"
        else:
            return "Crítica"