from datetime import datetime, timedelta
from ..models.agendamento import Visita
from ..models.questionarios_obrigatorios import EntidadeIdentificada, ProgressoQuestionarios, QuestionarioObrigatorio
from ..config import RELATORIO_PERIODOS, MUNICIPIOS
import json

class RelatorioService:
    def __init__(self):
        self.relatorios = {}
    
    def _format_datetime_for_json(self, obj):
        """Converte objetos datetime, date e time para strings JSON-compatíveis."""
        if hasattr(obj, 'strftime'):
            if hasattr(obj, 'date'):  # datetime object
                return obj.strftime('%Y-%m-%d %H:%M:%S')
            elif hasattr(obj, 'year'):  # date object
                return obj.strftime('%Y-%m-%d')
            else:  # time object
                return obj.strftime('%H:%M:%S')
        return obj

    def gerar_relatorio_visita(self, visita):
        """Gera um relatório detalhado de uma visita específica."""
        if not visita:
            return None

        relatorio = {
            'id': f"rel_visita_{visita.id}",
            'tipo': 'visita',
            'data_geracao': self._format_datetime_for_json(datetime.now()),
            'dados_visita': {
                'municipio': visita.municipio,
                'data': self._format_datetime_for_json(visita.data),
                'hora_inicio': self._format_datetime_for_json(visita.hora_inicio),
                'hora_fim': self._format_datetime_for_json(visita.hora_fim),
                'status': visita.status,
                'informante': getattr(visita, 'tipo_informante', 'prefeitura'),
                'checklist': visita.checklist.to_dict() if visita.checklist else {},
                'observacoes': visita.observacoes
            },
            'progresso': {
                'checklist': visita.checklist.obter_progresso() if visita.checklist and hasattr(visita.checklist, 'obter_progresso') else {},
                'roteiro': visita.verificar_progresso_roteiro() if hasattr(visita, 'verificar_progresso_roteiro') else {}
            }
        }

        self.relatorios[relatorio['id']] = relatorio
        return relatorio

    def gerar_relatorio_periodo(self, visitas, data_inicio, data_fim):
        """Gera um relatório consolidado de um período específico integrado com PNSB."""
        # Obter dados PNSB atuais
        dados_pnsb = self._obter_dados_pnsb()
        
        relatorio = {
            'id': f"rel_periodo_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'tipo': 'periodo',
            'data_geracao': self._format_datetime_for_json(datetime.now()),
            'periodo': {
                'inicio': self._format_datetime_for_json(data_inicio),
                'fim': self._format_datetime_for_json(data_fim)
            },
            'resumo': {
                # Dados básicos de visitas
                'total_visitas': len(visitas),
                'por_status': self._contar_por_status(visitas),
                'por_municipio': self._contar_por_municipio(visitas),
                
                # Dados PNSB integrados
                'questionarios_obrigatorios': dados_pnsb['questionarios'],
                'entidades_identificadas': dados_pnsb['entidades'],
                'progresso_pnsb': dados_pnsb['progresso'],
                'prioridades': dados_pnsb['prioridades'],
                'compliance_pnsb': self._calcular_compliance_pnsb(dados_pnsb),
                'metricas_avancadas': self._calcular_metricas_avancadas(visitas, dados_pnsb)
            },
            'detalhes': [self.gerar_relatorio_visita(v) for v in visitas if v],
            'pnsb_detalhado': self._gerar_detalhes_pnsb(dados_pnsb)
        }

        self.relatorios[relatorio['id']] = relatorio
        return relatorio

    def _obter_dados_pnsb(self):
        """Obtém dados completos do sistema PNSB atual."""
        try:
            # Entidades identificadas
            entidades = EntidadeIdentificada.query.all()
            
            # Questionários obrigatórios
            questionarios = QuestionarioObrigatorio.query.filter_by(ativo=True).all()
            
            # Progresso por município
            progressos = ProgressoQuestionarios.query.all()
            
            return {
                'entidades': {
                    'total': len(entidades),
                    'prefeituras': len([e for e in entidades if e.tipo_entidade == 'prefeitura']),
                    'empresas': len([e for e in entidades if e.tipo_entidade == 'empresa_terceirizada']),
                    'por_municipio': self._agrupar_entidades_por_municipio(entidades),
                    'por_status': self._agrupar_entidades_por_status(entidades)
                },
                'questionarios': {
                    'total': len(questionarios),
                    'mrs_obrigatorio': len([q for q in questionarios if q.mrs_obrigatorio]),
                    'map_obrigatorio': len([q for q in questionarios if q.map_obrigatorio]),
                    'por_municipio': self._agrupar_questionarios_por_municipio(questionarios)
                },
                'progresso': {
                    'municipios_com_progresso': len(progressos),
                    'total_mrs_obrigatorios': sum(p.total_mrs_obrigatorios for p in progressos),
                    'total_map_obrigatorios': sum(p.total_map_obrigatorios for p in progressos),
                    'detalhes_por_municipio': {p.municipio: {
                        'mrs_obrigatorios': p.total_mrs_obrigatorios,
                        'map_obrigatorios': p.total_map_obrigatorios,
                        'mrs_respondidos': p.mrs_respondidos,
                        'map_respondidos': p.map_respondidos,
                        'mrs_validados': p.mrs_validados,
                        'map_validados': p.map_validados
                    } for p in progressos}
                },
                'prioridades': {
                    'p1_critica': len([e for e in entidades if e.prioridade == 1]),
                    'p2_importante': len([e for e in entidades if e.prioridade == 2]),
                    'p3_opcional': len([e for e in entidades if e.prioridade == 3]),
                    'detalhes_p1': [self._entidade_to_dict(e) for e in entidades if e.prioridade == 1],
                    'detalhes_p2': [self._entidade_to_dict(e) for e in entidades if e.prioridade == 2],
                    'detalhes_p3': [self._entidade_to_dict(e) for e in entidades if e.prioridade == 3]
                }
            }
        except Exception as e:
            # Fallback em caso de erro
            return {
                'entidades': {'total': 0, 'prefeituras': 0, 'empresas': 0, 'por_municipio': {}, 'por_status': {}},
                'questionarios': {'total': 0, 'mrs_obrigatorio': 0, 'map_obrigatorio': 0, 'por_municipio': {}},
                'progresso': {'municipios_com_progresso': 0, 'total_mrs_obrigatorios': 0, 'total_map_obrigatorios': 0, 'detalhes_por_municipio': {}},
                'prioridades': {'p1_critica': 0, 'p2_importante': 0, 'p3_opcional': 0, 'detalhes_p1': [], 'detalhes_p2': [], 'detalhes_p3': []},
                'erro': str(e)
            }

    def gerar_relatorio_mensal(self, visitas, mes, ano):
        """Gera um relatório consolidado mensal."""
        data_inicio = datetime(ano, mes, 1)
        if mes == 12:
            data_fim = datetime(ano + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim = datetime(ano, mes + 1, 1) - timedelta(days=1)

        return self.gerar_relatorio_periodo(visitas, data_inicio, data_fim)

    def _contar_por_status(self, visitas):
        """Conta o número de visitas por status."""
        contagem = {}
        for visita in visitas:
            status = visita.status
            contagem[status] = contagem.get(status, 0) + 1
        return contagem

    def _contar_por_municipio(self, visitas):
        """Conta o número de visitas por município."""
        contagem = {}
        for visita in visitas:
            municipio = visita.municipio
            contagem[municipio] = contagem.get(municipio, 0) + 1
        return contagem

    def _agrupar_entidades_por_municipio(self, entidades):
        """Agrupa entidades por município."""
        agrupamento = {}
        for entidade in entidades:
            municipio = entidade.municipio
            if municipio not in agrupamento:
                agrupamento[municipio] = {
                    'total': 0,
                    'prefeituras': 0,
                    'empresas': 0,
                    'p1': 0,
                    'p2': 0,
                    'p3': 0,
                    'mrs_obrigatorio': 0,
                    'map_obrigatorio': 0
                }
            
            agrupamento[municipio]['total'] += 1
            
            if entidade.tipo_entidade == 'prefeitura':
                agrupamento[municipio]['prefeituras'] += 1
            elif entidade.tipo_entidade == 'empresa_terceirizada':
                agrupamento[municipio]['empresas'] += 1
            
            if entidade.prioridade == 1:
                agrupamento[municipio]['p1'] += 1
            elif entidade.prioridade == 2:
                agrupamento[municipio]['p2'] += 1
            elif entidade.prioridade == 3:
                agrupamento[municipio]['p3'] += 1
            
            if getattr(entidade, 'mrs_obrigatorio', False):
                agrupamento[municipio]['mrs_obrigatorio'] += 1
            if getattr(entidade, 'map_obrigatorio', False):
                agrupamento[municipio]['map_obrigatorio'] += 1
        
        return agrupamento

    def _agrupar_entidades_por_status(self, entidades):
        """Agrupa entidades por status do questionário."""
        agrupamento = {}
        for entidade in entidades:
            status = getattr(entidade, 'status_questionario', 'nao_iniciado')
            agrupamento[status] = agrupamento.get(status, 0) + 1
        return agrupamento

    def _agrupar_questionarios_por_municipio(self, questionarios):
        """Agrupa questionários obrigatórios por município."""
        agrupamento = {}
        for questionario in questionarios:
            municipio = questionario.municipio
            if municipio not in agrupamento:
                agrupamento[municipio] = {
                    'total': 0,
                    'mrs': 0,
                    'map': 0
                }
            
            agrupamento[municipio]['total'] += 1
            if questionario.mrs_obrigatorio:
                agrupamento[municipio]['mrs'] += 1
            if questionario.map_obrigatorio:
                agrupamento[municipio]['map'] += 1
        
        return agrupamento

    def _entidade_to_dict(self, entidade):
        """Converte entidade para dicionário."""
        return {
            'id': entidade.id,
            'nome': entidade.nome_entidade,
            'municipio': entidade.municipio,
            'tipo': entidade.tipo_entidade,
            'prioridade': entidade.prioridade,
            'mrs_obrigatorio': getattr(entidade, 'mrs_obrigatorio', False),
            'map_obrigatorio': getattr(entidade, 'map_obrigatorio', False),
            'status': getattr(entidade, 'status_questionario', 'nao_iniciado'),
            'visitada': bool(getattr(entidade, 'visita_id', None))
        }

    def _calcular_compliance_pnsb(self, dados_pnsb):
        """Calcula métricas de compliance com PNSB."""
        entidades = dados_pnsb['entidades']
        progresso = dados_pnsb['progresso']
        prioridades = dados_pnsb['prioridades']
        
        # Taxa de entidades P1 (críticas) com questionários obrigatórios
        total_p1 = prioridades['p1_critica']
        p1_com_questionarios = len([e for e in prioridades['detalhes_p1'] if e['mrs_obrigatorio'] or e['map_obrigatorio']])
        
        # Taxa de questionários respondidos vs obrigatórios
        total_mrs_obrigatorios = progresso['total_mrs_obrigatorios']
        total_map_obrigatorios = progresso['total_map_obrigatorios']
        
        mrs_respondidos = sum(p['mrs_respondidos'] for p in progresso['detalhes_por_municipio'].values())
        map_respondidos = sum(p['map_respondidos'] for p in progresso['detalhes_por_municipio'].values())
        
        return {
            'taxa_p1_compliance': (p1_com_questionarios / total_p1 * 100) if total_p1 > 0 else 0,
            'taxa_mrs_respondidos': (mrs_respondidos / total_mrs_obrigatorios * 100) if total_mrs_obrigatorios > 0 else 0,
            'taxa_map_respondidos': (map_respondidos / total_map_obrigatorios * 100) if total_map_obrigatorios > 0 else 0,
            'municipios_11_objetivo': len(MUNICIPIOS),
            'municipios_com_progresso': progresso['municipios_com_progresso'],
            'cobertura_municipios': (progresso['municipios_com_progresso'] / len(MUNICIPIOS) * 100),
            'status_geral': 'Em Andamento' if progresso['municipios_com_progresso'] > 0 else 'Não Iniciado'
        }

    def _calcular_metricas_avancadas(self, visitas, dados_pnsb):
        """Calcula métricas avançadas cruzando visitas com dados PNSB."""
        # Visitas que geraram questionários obrigatórios
        visitas_com_questionarios = len([v for v in visitas if getattr(v, 'tipo_informante', None)])
        
        # Visitas por tipo de entidade PNSB
        visitas_prefeitura = len([v for v in visitas if getattr(v, 'tipo_informante', '') == 'prefeitura'])
        visitas_empresa = len([v for v in visitas if getattr(v, 'tipo_informante', '') == 'empresa_terceirizada'])
        
        return {
            'visitas_geraram_questionarios': visitas_com_questionarios,
            'visitas_prefeitura': visitas_prefeitura,
            'visitas_empresa': visitas_empresa,
            'taxa_visitas_vs_entidades': (len(visitas) / dados_pnsb['entidades']['total'] * 100) if dados_pnsb['entidades']['total'] > 0 else 0,
            'eficiencia_coleta': {
                'visitas_realizadas': len([v for v in visitas if v.status in ['realizada', 'finalizada', 'questionários validados']]),
                'questionarios_gerados': visitas_com_questionarios,
                'entidades_cobertas': len(set(v.municipio for v in visitas))
            }
        }

    def _gerar_detalhes_pnsb(self, dados_pnsb):
        """Gera seção detalhada específica do PNSB."""
        return {
            'estrutura_prioridades': {
                'p1_critica': {
                    'descricao': 'Prefeituras + Lista UF (Obrigatórias para metas PNSB)',
                    'total': dados_pnsb['prioridades']['p1_critica'],
                    'entidades': dados_pnsb['prioridades']['detalhes_p1']
                },
                'p2_importante': {
                    'descricao': 'Identificadas em campo (Se incluídas, tornam-se obrigatórias)',
                    'total': dados_pnsb['prioridades']['p2_importante'],
                    'entidades': dados_pnsb['prioridades']['detalhes_p2']
                },
                'p3_opcional': {
                    'descricao': 'Referência (Recursos disponíveis, não contam para metas)',
                    'total': dados_pnsb['prioridades']['p3_opcional'],
                    'entidades': dados_pnsb['prioridades']['detalhes_p3']
                }
            },
            'resumo_municipal': dados_pnsb['entidades']['por_municipio'],
            'progresso_detalhado': dados_pnsb['progresso']['detalhes_por_municipio']
        }

    def obter_relatorio(self, relatorio_id):
        """Retorna um relatório específico."""
        return self.relatorios.get(relatorio_id)

    def obter_relatorios_por_tipo(self, tipo):
        """Retorna todos os relatórios de um tipo específico."""
        return [
            relatorio
            for relatorio in self.relatorios.values()
            if relatorio['tipo'] == tipo
        ]

    def obter_relatorios_por_periodo(self, data_inicio, data_fim):
        """Retorna todos os relatórios gerados em um período específico."""
        return [
            relatorio
            for relatorio in self.relatorios.values()
            if data_inicio <= relatorio['data_geracao'] <= data_fim
        ]

    def gerar_relatorio_consolidado(self, visitas, informantes, prestadores, questionarios):
        """Gera um relatório consolidado com todos os dados."""
        relatorio = {
            'id': f"rel_consolidado_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'tipo': 'consolidado',
            'data_geracao': datetime.now(),
            'resumo': {
                'visitas': {
                    'total': len(visitas),
                    'por_status': self._contar_por_status(visitas),
                    'por_municipio': self._contar_por_municipio(visitas)
                },
                'informantes': {
                    'total': len(informantes),
                    'ativos': sum(1 for i in informantes if i['status'] == 'ativo')
                },
                'prestadores': {
                    'total': len(prestadores),
                    'validados': sum(1 for p in prestadores 
                                   if p['validacao']['status'] == 'aprovado')
                },
                'questionarios': {
                    'total': len(questionarios),
                    'concluidos': sum(1 for q in questionarios 
                                    if q['status'] == 'concluido')
                }
            },
            'detalhes': {
                'visitas': [self.gerar_relatorio_visita(v) for v in visitas if v],
                'informantes': informantes,
                'prestadores': prestadores,
                'questionarios': questionarios
            }
        }

        self.relatorios[relatorio['id']] = relatorio
        return relatorio

    def exportar_relatorio(self, relatorio_id, formato='json'):
        """Exporta um relatório em um formato específico."""
        relatorio = self.obter_relatorio(relatorio_id)
        if not relatorio:
            return None

        if formato == 'json':
            return relatorio
        elif formato == 'csv':
            return self._converter_para_csv(relatorio)
        elif formato == 'pdf':
            return self._converter_para_pdf(relatorio)
        else:
            return None

    def _converter_para_csv(self, relatorio):
        """Converte um relatório para formato CSV."""
        # Implementar conversão para CSV
        pass

    def _converter_para_pdf(self, relatorio):
        """Converte um relatório para formato PDF."""
        # Implementar conversão para PDF
        pass 