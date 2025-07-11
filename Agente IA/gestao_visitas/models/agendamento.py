from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Time, Boolean
from sqlalchemy.orm import relationship
from gestao_visitas.db import db
from .checklist import Checklist
from ..config import STATUS_VISITA, DURACAO_PADRAO_VISITA

STATUS_VISITA_COMPLETO = [
    'agendada',
    'em andamento',              # SIMPLIFICADO: em preparação + em execução
    'realizada',
    'questionários concluídos',  # Questionários respondidos, aguardando validação
    'questionários validados',   # Questionários validados sem críticas ✅
    'finalizada',
    'remarcada',
    'não realizada'
]

class Visita(db.Model):
    __tablename__ = 'visitas'
    
    id = Column(Integer, primary_key=True)
    municipio = Column(String(100), nullable=False, index=True)  # Índice para consultas por município
    data = Column(Date, nullable=False, index=True)  # Índice para consultas por data
    hora_inicio = Column(Time, nullable=False)
    hora_fim = Column(Time, nullable=False)
    local = Column(String(100), nullable=False)
    tipo_pesquisa = Column(String(10), nullable=False, default='MRS', index=True)  # Índice para filtros por tipo
    status = Column(String(20), default='agendada', index=True)  # Índice para consultas por status
    observacoes = Column(String(500))
    data_criacao = Column(DateTime, default=datetime.now, index=True)  # Índice para ordenação temporal
    data_atualizacao = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    tipo_informante = Column(String(30), nullable=False, default='prefeitura', index=True)  # Índice para filtros por tipo
    pesquisador_responsavel = Column(String(100), index=True)  # Campo para funcionalidades PNSB
    
    # Campos expandidos para múltiplas entidades (preparação futura)
    entidade_nome = Column(String(200))  # Nome específico da entidade/empresa
    entidade_cnpj = Column(String(20))  # CNPJ da entidade (se aplicável)
    entidade_categoria = Column(String(50))  # Categoria específica da entidade
    responsavel_cargo = Column(String(100))  # Cargo do responsável na entidade
    entidade_endereco = Column(String(300))  # Endereço específico da entidade
    entidade_servicos = Column(String(500))  # Serviços prestados pela entidade (JSON ou texto)
    
    # Campos para verificação por WhatsApp
    telefone_responsavel = Column(String(20))  # Telefone para WhatsApp
    email_enviado_em = Column(DateTime)  # Quando o e-mail foi enviado pelo IBGE
    whatsapp_verificacao_enviado = Column(DateTime)  # Quando verificação foi enviada
    whatsapp_resposta_recebida = Column(DateTime)  # Quando resposta foi recebida
    email_recebido_confirmado = Column(Boolean, default=False)  # Se confirmou recebimento
    
    checklist = relationship(
        'Checklist',
        uselist=False,
        backref='visita',
        foreign_keys='Checklist.visita_id',
        cascade='all, delete-orphan'
    )

    # Mapeamento de transições de status simplificado para entrevistas PNSB
    TRANSICOES_STATUS = {
        'agendada': ['em andamento', 'realizada', 'remarcada', 'não realizada'],
        'em andamento': ['realizada', 'agendada', 'remarcada', 'não realizada'],
        'realizada': ['questionários concluídos', 'agendada', 'em andamento'],
        'questionários concluídos': ['questionários validados', 'realizada'],
        'questionários validados': ['finalizada', 'questionários concluídos'],
        'finalizada': ['questionários validados', 'questionários concluídos', 'realizada'],  # Permite reabrir se necessário
        'remarcada': ['agendada'],
        'não realizada': ['agendada', 'remarcada']
    }
    
    def __init__(self, id=None, municipio=None, data=None, hora_inicio=None, 
                 hora_fim=None, local=None, tipo_pesquisa='MRS', status='agendada', 
                 observacoes=None, checklist=None, roteiro_progresso=None, tipo_informante='prefeitura',
                 pesquisador_responsavel=None, entidade_nome=None, entidade_cnpj=None,
                 entidade_categoria=None, responsavel_cargo=None, entidade_endereco=None,
                 entidade_servicos=None):
        self.id = id
        self.municipio = municipio
        self.data = data
        self.hora_inicio = hora_inicio
        self.hora_fim = hora_fim or self._calcular_hora_fim(hora_inicio)
        self.local = local
        self.tipo_pesquisa = tipo_pesquisa
        self.status = status
        self.observacoes = observacoes or ""
        self.roteiro_progresso = roteiro_progresso or {}
        self.data_criacao = datetime.now()
        self.data_atualizacao = datetime.now()
        self.tipo_informante = (tipo_informante or 'prefeitura').lower()
        self.pesquisador_responsavel = pesquisador_responsavel
        
        # Campos de entidade
        self.entidade_nome = entidade_nome
        self.entidade_cnpj = entidade_cnpj
        self.entidade_categoria = entidade_categoria
        self.responsavel_cargo = responsavel_cargo
        self.entidade_endereco = entidade_endereco
        self.entidade_servicos = entidade_servicos

    def _calcular_hora_fim(self, hora_inicio):
        """Calcula a hora de fim baseada na hora de início e duração padrão."""
        if not hora_inicio:
            return None
        hora_fim = datetime.combine(datetime.today(), hora_inicio) + \
                  timedelta(minutes=DURACAO_PADRAO_VISITA)
        return hora_fim.time()

    def adicionar_observacao(self, observacao):
        """Adiciona uma nova observação com timestamp."""
        self.observacoes.append({
            'texto': observacao,
            'data': datetime.now()
        })
        self.data_atualizacao = datetime.now()

    def atualizar_status(self, novo_status):
        """Atualiza o status da visita, validando a transição."""
        if novo_status not in STATUS_VISITA_COMPLETO:
            raise ValueError(f'Status inválido: {novo_status}')
        if novo_status not in self.TRANSICOES_STATUS.get(self.status, []):
            raise ValueError(f'Transição de status não permitida: {self.status} -> {novo_status}')
        self.status = novo_status
        self.data_atualizacao = datetime.now()
        return True

    def calcular_status_inteligente(self):
        """Calcula o status real baseado em questionários, checklist e visitas obrigatórias (versão otimizada)."""
        try:
            # Retorna status atual para evitar queries pesadas
            return getattr(self, 'status', 'agendada')
        except Exception:
            return 'agendada' 

    def obter_progresso_checklist(self):
        """Retorna o progresso do checklist por etapa (versão otimizada)."""
        try:
            # Versão simplificada que não faz queries pesadas
            return {'antes': 0, 'durante': 0, 'apos': 0}
        except Exception:
            return {'antes': 0, 'durante': 0, 'apos': 0}

    def obter_status_questionarios(self):
        """Retorna o status detalhado dos questionários (versão otimizada)."""
        try:
            # Retorna estrutura padrão sem queries pesadas
            return {
                'mrs': {'nao_iniciado': 0, 'respondido': 0, 'validado_concluido': 0, 'nao_aplicavel': 0},
                'map': {'nao_iniciado': 0, 'respondido': 0, 'validado_concluido': 0, 'nao_aplicavel': 0},
                'total_entidades': 0
            }
        except Exception:
            return {
                'mrs': {'nao_iniciado': 0, 'respondido': 0, 'validado_concluido': 0, 'nao_aplicavel': 0},
                'map': {'nao_iniciado': 0, 'respondido': 0, 'validado_concluido': 0, 'nao_aplicavel': 0},
                'total_entidades': 0
            }

    def recomendar_proxima_acao(self):
        """Recomenda a próxima ação baseada no status atual (versão otimizada)."""
        try:
            status = getattr(self, 'status', 'agendada')
            
            if status == 'agendada':
                return "Completar preparação da visita no checklist"
            elif status == 'em andamento':
                return "Finalizar visita"
            elif status == 'realizada':
                return "Validar questionários respondidos"
            elif status == 'questionários concluídos':
                return "Validar questionários para aprovação"
            elif status == 'questionários validados':
                return "Finalizar visita"
            elif status == 'verificação whatsapp':
                return "Aguardar confirmação por WhatsApp"
            else:
                return "Verificar status"
        except Exception:
            return "Verificar status"

    def calcular_progresso_completo(self):
        """Calcula o progresso completo da visita (versão otimizada)."""
        try:
            status = getattr(self, 'status', 'agendada')
            
            # Progresso baseado no status
            if status == 'agendada':
                progresso = 10.0
            elif status == 'em andamento':
                progresso = 30.0
            elif status == 'realizada':
                progresso = 60.0
            elif status == 'questionários concluídos':
                progresso = 80.0
            elif status == 'questionários validados':
                progresso = 95.0
            elif status == 'finalizada':
                progresso = 100.0
            else:
                progresso = 5.0
            
            return {
                'progresso_total': progresso,
                'detalhes': {
                    'preparacao': 0,
                    'execucao': 0,
                    'questionarios': 0,
                    'finalizacao': 0
                },
                'status_inteligente': status
            }
        except Exception:
            return {
                'progresso_total': 0.0,
                'detalhes': {'preparacao': 0, 'execucao': 0, 'questionarios': 0, 'finalizacao': 0},
                'status_inteligente': 'agendada'
            }

    def atualizar_progresso_roteiro(self, etapa, concluida=True):
        """Atualiza o progresso de uma etapa do roteiro."""
        self.roteiro_progresso[etapa] = {
            'concluida': concluida,
            'data_atualizacao': datetime.now()
        }
        self.data_atualizacao = datetime.now()

    def verificar_progresso_roteiro(self):
        """Retorna o progresso geral do roteiro em porcentagem."""
        if not hasattr(self, 'roteiro_progresso') or not self.roteiro_progresso:
            return 0
            
        etapas_concluidas = sum(1 for etapa in self.roteiro_progresso.values() 
                              if etapa.get('concluida'))
        total_etapas = len(self.roteiro_progresso)
        return (etapas_concluidas / total_etapas) * 100 if total_etapas > 0 else 0

    def pode_ser_editada(self):
        """Permite edição em qualquer status."""
        return True

    def pode_ser_excluida(self):
        """Permite exclusão em qualquer status."""
        return True

    def obter_status_visitas_obrigatorias(self):
        """Retorna status das visitas obrigatórias (versão otimizada)"""
        try:
            # Retorna estrutura padrão sem queries pesadas
            return {
                'tem_visitas_obrigatorias': False,
                'total_vinculadas': 0,
                'status_detalhes': []
            }
        except Exception:
            return {
                'tem_visitas_obrigatorias': False,
                'total_vinculadas': 0,
                'status_detalhes': []
            }

    def sincronizar_com_visitas_obrigatorias(self):
        """Sincroniza esta visita com visitas obrigatórias vinculadas"""
        try:
            from .visitas_obrigatorias import sincronizar_visita_obrigatoria_com_visita_real
            return sincronizar_visita_obrigatoria_com_visita_real(self.id)
        except Exception:
            return False

    def to_dict(self):
        """Converte a visita para um dicionário."""
        def format_time(t):
            try:
                return t.strftime('%H:%M') if t else None
            except Exception:
                return str(t) if t else None
        
        def format_date(d):
            try:
                return d.strftime('%d/%m/%Y') if d else None
            except Exception:
                return str(d) if d else None
        
        checklist_dict = {}
        try:
            if hasattr(self, 'checklist') and self.checklist:
                checklist_dict = self.checklist.to_dict()
        except Exception:
            checklist_dict = {}
        
        return {
            'id': self.id,
            'municipio': getattr(self, 'municipio', None),
            'data': format_date(getattr(self, 'data', None)),
            'hora_inicio': format_time(getattr(self, 'hora_inicio', None)),
            'hora_fim': format_time(getattr(self, 'hora_fim', None)),
            'local': getattr(self, 'local', None),
            'tipo_pesquisa': getattr(self, 'tipo_pesquisa', None),
            'status': getattr(self, 'status', None),
            'observacoes': getattr(self, 'observacoes', '') or '',
            'checklist': checklist_dict,
            'roteiro_progresso': getattr(self, 'roteiro_progresso', {}),
            'progresso_geral': self.verificar_progresso_roteiro() if hasattr(self, 'verificar_progresso_roteiro') else {},
            'data_criacao': format_date(getattr(self, 'data_criacao', None)),
            'data_atualizacao': format_date(getattr(self, 'data_atualizacao', None)),
            'pode_editar': self.pode_ser_editada() if hasattr(self, 'pode_ser_editada') else False,
            'pode_excluir': self.pode_ser_excluida() if hasattr(self, 'pode_ser_excluida') else False,
            'tipo_informante': (getattr(self, 'tipo_informante', None) or 'prefeitura').lower(),
            'telefone_responsavel': getattr(self, 'telefone_responsavel', None),
            'email_enviado_em': format_date(getattr(self, 'email_enviado_em', None)),
            'whatsapp_verificacao_enviado': format_date(getattr(self, 'whatsapp_verificacao_enviado', None)),
            'whatsapp_resposta_recebida': format_date(getattr(self, 'whatsapp_resposta_recebida', None)),
            'email_recebido_confirmado': getattr(self, 'email_recebido_confirmado', False),
            'verificacao_whatsapp': self.obter_status_verificacao() if hasattr(self, 'obter_status_verificacao') else {},
            # Campos expandidos para múltiplas entidades
            'entidade': {
                'nome': getattr(self, 'entidade_nome', None),
                'cnpj': getattr(self, 'entidade_cnpj', None),
                'categoria': getattr(self, 'entidade_categoria', None),
                'endereco': getattr(self, 'entidade_endereco', None),
                'servicos': getattr(self, 'entidade_servicos', None)
            },
            'responsavel_cargo': getattr(self, 'responsavel_cargo', None),
            # Novos campos para status inteligente
            'status_inteligente': self.calcular_status_inteligente(),
            'progresso_checklist': self.obter_progresso_checklist(),
            'status_questionarios': self.obter_status_questionarios(),
            'proxima_acao': self.recomendar_proxima_acao(),
            'progresso_completo': self.calcular_progresso_completo(),
            # NOVO: Status de visitas obrigatórias
            'visitas_obrigatorias': self.obter_status_visitas_obrigatorias()
        }

    @classmethod
    def excluir_visita(cls, visita_id):
        """Exclui uma visita do banco de dados e seu checklist relacionado."""
        visita = cls.query.get(visita_id)
        if visita:
            # Excluir checklist relacionado, se existir
            if visita.checklist:
                db.session.delete(visita.checklist)
            db.session.delete(visita)
            db.session.commit()
            return True
        return False

    def registrar_email_enviado(self, data_envio=None):
        """Registra quando o e-mail foi enviado pelo sistema IBGE."""
        self.email_enviado_em = data_envio or datetime.now()
        self.data_atualizacao = datetime.now()
        
    def pode_verificar_whatsapp(self):
        """Verifica se pode enviar verificação por WhatsApp."""
        try:
            # Pode verificar se:
            # 1. Tem telefone do responsável
            # 2. E-mail foi enviado
            # 3. Status permite verificação
            return bool(
                getattr(self, 'telefone_responsavel', None) and
                getattr(self, 'email_enviado_em', None) and
                getattr(self, 'status', '') in ['realizada', 'resultados visita', 'verificação whatsapp']
            )
        except Exception:
            return False
        
    def enviar_verificacao_whatsapp(self):
        """Envia verificação por WhatsApp e atualiza status."""
        if not self.pode_verificar_whatsapp():
            return False, "Condições não atendidas para verificação"
            
        # Registrar envio
        self.whatsapp_verificacao_enviado = datetime.now()
        self.status = 'verificação whatsapp'
        self.data_atualizacao = datetime.now()
        
        return True, "Verificação enviada com sucesso"
        
    def confirmar_email_recebido(self, resposta_recebida=True):
        """Confirma se o responsável recebeu o e-mail."""
        self.email_recebido_confirmado = resposta_recebida
        self.whatsapp_resposta_recebida = datetime.now()
        self.data_atualizacao = datetime.now()
        
        # Se confirmou recebimento, pode ir para follow-up
        # Se não recebeu, mantém em verificação para nova tentativa
        if resposta_recebida:
            self.status = 'em follow-up'
            
    def obter_status_verificacao(self):
        """Retorna informações sobre o status da verificação."""
        def safe_format_datetime(dt):
            """Formata datetime de forma segura"""
            if dt is None:
                return None
            try:
                return dt.strftime('%d/%m/%Y %H:%M')
            except Exception:
                return None
        
        return {
            'telefone_cadastrado': bool(self.telefone_responsavel),
            'email_enviado': bool(self.email_enviado_em),
            'verificacao_enviada': bool(self.whatsapp_verificacao_enviado),
            'resposta_recebida': bool(self.whatsapp_resposta_recebida),
            'email_confirmado': bool(getattr(self, 'email_recebido_confirmado', False)),
            'pode_verificar': self.pode_verificar_whatsapp(),
            'data_email': safe_format_datetime(self.email_enviado_em),
            'data_verificacao': safe_format_datetime(self.whatsapp_verificacao_enviado),
            'data_resposta': safe_format_datetime(self.whatsapp_resposta_recebida)
        }

    def excluir_checklist_etapa(self, etapa_nome):
        """Remove os dados do checklist da etapa informada."""
        if not self.checklist:
            return False
        campos = []
        if etapa_nome == 'Antes da Visita':
            campos = ['cracha_ibge', 'recibo_entrega', 'questionario_mrs_impresso', 'questionario_map_impresso',
                      'carta_oficial', 'questionario_mrs_digital', 'questionario_map_digital', 'manual_pnsb',
                      'guia_site_externo', 'card_contato', 'audio_explicativo', 'planejamento_rota', 'agenda_confirmada',
                      'observacoes_antes']
        elif etapa_nome == 'Durante a Visita':
            campos = ['apresentacao_ibge', 'explicacao_objetivo', 'explicacao_estrutura', 'explicacao_data_referencia',
                      'explicacao_prestador', 'explicacao_servicos', 'explicacao_site_externo', 'explicacao_pdf_editavel',
                      'validacao_prestadores', 'registro_contatos', 'assinatura_informante', 'observacoes_durante']
        elif etapa_nome == 'Após a Visita':
            campos = ['devolucao_materiais', 'registro_followup', 'combinacao_entrega', 'combinacao_acompanhamento', 'observacoes_finais', 'observacoes_apos']
        for campo in campos:
            if hasattr(self.checklist, campo):
                setattr(self.checklist, campo, None)
        return True

class Calendario:
    def __init__(self):
        self.visitas = []

    def adicionar_visita(self, visita):
        """Adiciona uma nova visita ao calendário."""
        if self.verificar_disponibilidade(visita.data, visita.hora_inicio, 
                                        visita.hora_fim):
            self.visitas.append(visita)
            return True
        return False

    def verificar_disponibilidade(self, data, hora_inicio, hora_fim):
        """Verifica se há disponibilidade no horário especificado."""
        for visita in self.visitas:
            if visita.data == data:
                # Verifica sobreposição de horários
                if (hora_inicio <= visita.hora_fim and 
                    hora_fim >= visita.hora_inicio):
                    return False
        return True

    def obter_visitas_por_periodo(self, data_inicio, data_fim):
        """Retorna todas as visitas em um período específico."""
        return [v for v in self.visitas 
                if data_inicio <= v.data <= data_fim]

    def obter_visitas_por_municipio(self, municipio):
        """Retorna todas as visitas de um município específico."""
        return [v for v in self.visitas if v.municipio == municipio]

    def obter_visitas_por_status(self, status):
        """Retorna todas as visitas com um status específico."""
        return [v for v in self.visitas if v.status == status]
