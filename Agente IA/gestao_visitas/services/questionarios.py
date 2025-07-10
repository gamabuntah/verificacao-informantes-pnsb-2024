from datetime import datetime

class QuestionarioService:
    def __init__(self):
        self.questionarios = {}
        self.respostas = {}
        self.secoes = {
            'identificacao': {
                'titulo': 'Identificação do Município',
                'campos': [
                    'nome_municipio',
                    'codigo_ibge',
                    'populacao_estimada',
                    'area_territorial'
                ]
            },
            'gestao': {
                'titulo': 'Gestão de Resíduos Sólidos',
                'campos': [
                    'plano_municipal',
                    'plano_regional',
                    'plano_intermunicipal',
                    'plano_estadual',
                    'plano_nacional'
                ]
            },
            'servicos': {
                'titulo': 'Serviços de Limpeza Urbana',
                'campos': [
                    'varricao_manual',
                    'varricao_mecanica',
                    'coleta_regular',
                    'coleta_seletiva',
                    'transporte',
                    'tratamento',
                    'disposicao_final'
                ]
            },
            'prestadores': {
                'titulo': 'Prestadores de Serviço',
                'campos': [
                    'tipo_prestacao',
                    'modalidade_contratacao',
                    'vigencia_contrato',
                    'valor_contrato',
                    'areas_atuacao'
                ]
            },
            'indicadores': {
                'titulo': 'Indicadores de Desempenho',
                'campos': [
                    'cobertura_coleta',
                    'taxa_geracao',
                    'taxa_recuperacao',
                    'custos_servicos'
                ]
            }
        }

    def criar_questionario(self, municipio, informante_id):
        """Cria um novo questionário para um município."""
        questionario_id = f"{municipio}_{len(self.questionarios) + 1}"
        self.questionarios[questionario_id] = {
            'id': questionario_id,
            'municipio': municipio,
            'informante_id': informante_id,
            'data_criacao': datetime.now(),
            'status': 'pendente',
            'secoes': self._inicializar_secoes(),
            'observacoes': []
        }
        return questionario_id

    def _inicializar_secoes(self):
        """Inicializa as seções do questionário com status pendente."""
        return {
            secao: {
                'titulo': dados['titulo'],
                'campos': {
                    campo: {
                        'valor': None,
                        'status': 'pendente',
                        'data_preenchimento': None,
                        'observacoes': None
                    }
                    for campo in dados['campos']
                }
            }
            for secao, dados in self.secoes.items()
        }

    def preencher_campo(self, questionario_id, secao, campo, valor, observacoes=None):
        """Preenche um campo específico do questionário."""
        if questionario_id not in self.questionarios:
            return False

        questionario = self.questionarios[questionario_id]
        if secao not in questionario['secoes']:
            return False

        if campo not in questionario['secoes'][secao]['campos']:
            return False

        questionario['secoes'][secao]['campos'][campo].update({
            'valor': valor,
            'status': 'preenchido',
            'data_preenchimento': datetime.now(),
            'observacoes': observacoes
        })
        questionario['data_atualizacao'] = datetime.now()
        return True

    def adicionar_observacao(self, questionario_id, observacao):
        """Adiciona uma observação ao questionário."""
        if questionario_id not in self.questionarios:
            return False

        self.questionarios[questionario_id]['observacoes'].append({
            'texto': observacao,
            'data': datetime.now()
        })
        return True

    def finalizar_questionario(self, questionario_id):
        """Finaliza o preenchimento do questionário."""
        if questionario_id not in self.questionarios:
            return False

        questionario = self.questionarios[questionario_id]
        if not self._verificar_completo(questionario):
            return False

        questionario.update({
            'status': 'concluido',
            'data_conclusao': datetime.now()
        })
        return True

    def _verificar_completo(self, questionario):
        """Verifica se todas as seções do questionário foram preenchidas."""
        for secao in questionario['secoes'].values():
            for campo in secao['campos'].values():
                if campo['status'] != 'preenchido':
                    return False
        return True

    def obter_questionario(self, questionario_id):
        """Retorna os dados de um questionário específico."""
        if questionario_id not in self.questionarios:
            return None

        return self.questionarios[questionario_id]

    def obter_questionarios_por_municipio(self, municipio):
        """Retorna todos os questionários de um município."""
        return [
            questionario
            for questionario in self.questionarios.values()
            if questionario['municipio'] == municipio
        ]

    def obter_questionarios_por_status(self, status):
        """Retorna todos os questionários com um status específico."""
        return [
            questionario
            for questionario in self.questionarios.values()
            if questionario['status'] == status
        ]

    def obter_estatisticas(self):
        """Retorna estatísticas sobre os questionários."""
        total = len(self.questionarios)
        concluidos = sum(1 for q in self.questionarios.values() 
                        if q['status'] == 'concluido')
        por_municipio = {}
        por_status = {}

        for questionario in self.questionarios.values():
            municipio = questionario['municipio']
            status = questionario['status']

            por_municipio[municipio] = por_municipio.get(municipio, 0) + 1
            por_status[status] = por_status.get(status, 0) + 1

        return {
            'total': total,
            'concluidos': concluidos,
            'pendentes': total - concluidos,
            'por_municipio': por_municipio,
            'por_status': por_status
        }

    def obter_secoes(self):
        """Retorna todas as seções do questionário."""
        return self.secoes 