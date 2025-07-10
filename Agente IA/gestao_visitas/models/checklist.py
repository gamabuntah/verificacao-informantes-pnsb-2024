from datetime import datetime
from ..config import (CHECKLIST_MATERIAIS, CHECKLIST_DOCUMENTOS, 
                     CHECKLIST_EQUIPAMENTOS)
from gestao_visitas.db import db

class Checklist(db.Model):
    __tablename__ = 'checklists'
    id = db.Column(db.Integer, primary_key=True)
    visita_id = db.Column(db.Integer, db.ForeignKey('visitas.id'), nullable=False)
    # Adicione outros campos conforme necessário
    observacoes_antes = db.Column(db.String(1000))
    observacoes_durante = db.Column(db.String(1000))
    observacoes_apos = db.Column(db.String(1000))
    itens_marcados = db.Column(db.JSON)  # Campo para salvar os itens marcados de cada checklist
    # Campos de checkboxes para cada etapa
    cracha_ibge = db.Column(db.Boolean, default=False)
    recibo_entrega = db.Column(db.Boolean, default=False)
    questionario_mrs_impresso = db.Column(db.Boolean, default=False)
    questionario_map_impresso = db.Column(db.Boolean, default=False)
    carta_oficial = db.Column(db.Boolean, default=False)
    questionario_mrs_digital = db.Column(db.Boolean, default=False)
    questionario_map_digital = db.Column(db.Boolean, default=False)
    manual_pnsb = db.Column(db.Boolean, default=False)
    guia_site_externo = db.Column(db.Boolean, default=False)
    card_contato = db.Column(db.Boolean, default=False)
    audio_explicativo = db.Column(db.Boolean, default=False)
    planejamento_rota = db.Column(db.Boolean, default=False)
    agenda_confirmada = db.Column(db.Boolean, default=False)
    apresentacao_ibge = db.Column(db.Boolean, default=False)
    explicacao_objetivo = db.Column(db.Boolean, default=False)
    explicacao_estrutura = db.Column(db.Boolean, default=False)
    explicacao_data_referencia = db.Column(db.Boolean, default=False)
    explicacao_prestador = db.Column(db.Boolean, default=False)
    explicacao_servicos = db.Column(db.Boolean, default=False)
    explicacao_site_externo = db.Column(db.Boolean, default=False)
    explicacao_pdf_editavel = db.Column(db.Boolean, default=False)
    validacao_prestadores = db.Column(db.Boolean, default=False)
    registro_contatos = db.Column(db.Boolean, default=False)
    assinatura_informante = db.Column(db.Boolean, default=False)
    devolucao_materiais = db.Column(db.Boolean, default=False)
    registro_followup = db.Column(db.Boolean, default=False)
    combinacao_entrega = db.Column(db.Boolean, default=False)
    combinacao_acompanhamento = db.Column(db.Boolean, default=False)
    observacoes_finais = db.Column(db.Boolean, default=False)

    def __init__(self, visita_id, **kwargs):
        super().__init__(**kwargs)
        self.visita_id = visita_id
        self.materiais = self._inicializar_itens(CHECKLIST_MATERIAIS)
        self.documentos = self._inicializar_itens(CHECKLIST_DOCUMENTOS)
        self.equipamentos = self._inicializar_itens(CHECKLIST_EQUIPAMENTOS)
        self.data_criacao = datetime.now()
        self.data_atualizacao = datetime.now()
        self.observacoes_antes = ""
        self.observacoes_durante = ""
        self.observacoes_apos = ""
        self.itens_marcados = {}  # Inicializa o campo de itens marcados

    def _inicializar_itens(self, itens_config):
        """Inicializa os itens do checklist com status pendente."""
        return {chave: {
            'nome': valor,
            'status': 'pendente',
            'data_atualizacao': None,
            'observacoes': None
        } for chave, valor in itens_config.items()}

    def atualizar_status(self, categoria, item, status, observacoes=None):
        """Atualiza o status de um item específico."""
        if categoria not in ['materiais', 'documentos', 'equipamentos']:
            return False

        itens = getattr(self, categoria)
        if item not in itens:
            return False

        itens[item].update({
            'status': status,
            'data_atualizacao': datetime.now(),
            'observacoes': observacoes
        })
        self.data_atualizacao = datetime.now()
        return True

    def verificar_completo(self):
        """Verifica se todos os itens estão concluídos."""
        categorias = [self.materiais, self.documentos, self.equipamentos]
        return all(
            item['status'] == 'concluido'
            for categoria in categorias
            for item in categoria.values()
        )

    def obter_itens_pendentes(self):
        """Retorna todos os itens pendentes organizados por categoria."""
        return {
            'materiais': self._filtrar_itens_por_status(self.materiais, 'pendente'),
            'documentos': self._filtrar_itens_por_status(self.documentos, 'pendente'),
            'equipamentos': self._filtrar_itens_por_status(self.equipamentos, 'pendente')
        }

    def _filtrar_itens_por_status(self, itens, status):
        """Filtra itens por status específico."""
        return {
            chave: valor
            for chave, valor in itens.items()
            if valor['status'] == status
        }

    def obter_progresso(self):
        """Retorna o progresso geral do checklist em porcentagem."""
        total_itens = (
            len(self.materiais) +
            len(self.documentos) +
            len(self.equipamentos)
        )
        itens_concluidos = sum(
            1 for categoria in [self.materiais, self.documentos, self.equipamentos]
            for item in categoria.values()
            if item['status'] == 'concluido'
        )
        return (itens_concluidos / total_itens) * 100 if total_itens > 0 else 0

    def to_dict(self):
        """Converte o checklist para um dicionário."""
        # Inicializa atributos se não existirem (caso o objeto venha do banco)
        if not hasattr(self, 'materiais'):
            self.materiais = self._inicializar_itens(CHECKLIST_MATERIAIS)
        if not hasattr(self, 'documentos'):
            self.documentos = self._inicializar_itens(CHECKLIST_DOCUMENTOS)
        if not hasattr(self, 'equipamentos'):
            self.equipamentos = self._inicializar_itens(CHECKLIST_EQUIPAMENTOS)
        
        # Campos de checkboxes para cada etapa
        campos_antes = ['cracha_ibge', 'recibo_entrega', 'questionario_mrs_impresso', 'questionario_map_impresso',
                        'carta_oficial', 'questionario_mrs_digital', 'questionario_map_digital', 'manual_pnsb',
                        'guia_site_externo', 'card_contato', 'audio_explicativo', 'planejamento_rota', 'agenda_confirmada']
        campos_durante = ['apresentacao_ibge', 'explicacao_objetivo', 'explicacao_estrutura', 'explicacao_data_referencia',
                          'explicacao_prestador', 'explicacao_servicos', 'explicacao_site_externo', 'explicacao_pdf_editavel',
                          'validacao_prestadores', 'registro_contatos', 'assinatura_informante', 'observacoes_durante']
        campos_apos = ['devolucao_materiais', 'registro_followup', 'combinacao_entrega', 'combinacao_acompanhamento', 'observacoes_finais']
        
        # Incluir campos de checkboxes no dicionário
        result = {
            'materiais': self.materiais,
            'documentos': self.documentos,
            'equipamentos': self.equipamentos,
            'progresso': self.obter_progresso(),
            'completo': self.verificar_completo(),
            'data_criacao': self.data_criacao.isoformat() if hasattr(self, 'data_criacao') else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if hasattr(self, 'data_atualizacao') else None,
            'observacoes_antes': self.observacoes_antes,
            'observacoes_durante': self.observacoes_durante,
            'observacoes_apos': self.observacoes_apos,
            'itens_marcados': self.itens_marcados
        }
        
        # Adicionar campos de checkboxes de cada etapa
        for campo in campos_antes:
            result[campo] = getattr(self, campo, False)
        for campo in campos_durante:
            result[campo] = getattr(self, campo, False)
        for campo in campos_apos:
            result[campo] = getattr(self, campo, False)
        
        return result

    def adicionar_item(self, categoria, chave, nome):
        """Adiciona um novo item ao checklist."""
        if categoria not in ['materiais', 'documentos', 'equipamentos']:
            return False

        itens = getattr(self, categoria)
        if chave in itens:
            return False

        itens[chave] = {
            'nome': nome,
            'status': 'pendente',
            'data_atualizacao': None,
            'observacoes': None
        }
        self.data_atualizacao = datetime.now()
        return True

    def remover_item(self, categoria, chave):
        """Remove um item do checklist."""
        if categoria not in ['materiais', 'documentos', 'equipamentos']:
            return False

        itens = getattr(self, categoria)
        if chave not in itens:
            return False

        del itens[chave]
        self.data_atualizacao = datetime.now()
        return True

    def calcular_progresso_preparacao(self):
        """Calcula o progresso da etapa de preparação (antes da visita)."""
        campos_preparacao = [
            'cracha_ibge', 'recibo_entrega', 'questionario_mrs_impresso', 'questionario_map_impresso',
            'carta_oficial', 'questionario_mrs_digital', 'questionario_map_digital', 'manual_pnsb',
            'guia_site_externo', 'card_contato', 'audio_explicativo', 'planejamento_rota', 'agenda_confirmada'
        ]
        
        total_campos = len(campos_preparacao)
        campos_concluidos = sum(1 for campo in campos_preparacao if getattr(self, campo, False))
        
        return (campos_concluidos / total_campos) * 100 if total_campos > 0 else 0

    def calcular_progresso_execucao(self):
        """Calcula o progresso da etapa de execução (durante a visita)."""
        campos_execucao = [
            'apresentacao_ibge', 'explicacao_objetivo', 'explicacao_estrutura', 'explicacao_data_referencia',
            'explicacao_prestador', 'explicacao_servicos', 'explicacao_site_externo', 'explicacao_pdf_editavel',
            'validacao_prestadores', 'registro_contatos', 'assinatura_informante'
        ]
        
        total_campos = len(campos_execucao)
        campos_concluidos = sum(1 for campo in campos_execucao if getattr(self, campo, False))
        
        return (campos_concluidos / total_campos) * 100 if total_campos > 0 else 0

    def calcular_progresso_resultados(self):
        """Calcula o progresso da etapa de resultados (após a visita)."""
        campos_resultados = [
            'devolucao_materiais', 'registro_followup', 'combinacao_entrega', 
            'combinacao_acompanhamento', 'observacoes_finais'
        ]
        
        total_campos = len(campos_resultados)
        campos_concluidos = sum(1 for campo in campos_resultados if getattr(self, campo, False))
        
        return (campos_concluidos / total_campos) * 100 if total_campos > 0 else 0 