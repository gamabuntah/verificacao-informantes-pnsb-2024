"""
Models para gestão de questionários obrigatórios do PNSB 2024
Define quais questionários (MRS/MAP) são obrigatórios para cada município e tipo de entidade
"""

from gestao_visitas.db import db
from datetime import datetime
from sqlalchemy import Index, event

class QuestionarioObrigatorio(db.Model):
    """
    Define questionários obrigatórios por município e tipo de entidade
    """
    __tablename__ = 'questionarios_obrigatorios'
    
    id = db.Column(db.Integer, primary_key=True)
    municipio = db.Column(db.String(100), nullable=False, index=True)
    tipo_entidade = db.Column(db.String(50), nullable=False, index=True)  # prefeitura, empresa_terceirizada, entidade_catadores, empresa_nao_vinculada
    
    # Questionários obrigatórios
    mrs_obrigatorio = db.Column(db.Boolean, default=False, nullable=False)
    map_obrigatorio = db.Column(db.Boolean, default=False, nullable=False)
    
    # Metadados
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    # Observações sobre a obrigatoriedade
    observacoes = db.Column(db.Text)
    
    # Índices compostos para performance
    __table_args__ = (
        Index('idx_municipio_entidade', 'municipio', 'tipo_entidade'),
        Index('idx_questionarios_ativos', 'ativo', 'municipio'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'municipio': self.municipio,
            'tipo_entidade': self.tipo_entidade,
            'mrs_obrigatorio': self.mrs_obrigatorio,
            'map_obrigatorio': self.map_obrigatorio,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None,
            'ativo': self.ativo,
            'observacoes': self.observacoes
        }
    
    @staticmethod
    def get_questionarios_municipio(municipio):
        """Retorna todos os questionários obrigatórios para um município"""
        return QuestionarioObrigatorio.query.filter_by(
            municipio=municipio, 
            ativo=True
        ).all()
    
    @staticmethod
    def get_questionarios_entidade(municipio, tipo_entidade):
        """Retorna questionários obrigatórios para uma entidade específica"""
        return QuestionarioObrigatorio.query.filter_by(
            municipio=municipio,
            tipo_entidade=tipo_entidade,
            ativo=True
        ).first()

class EntidadeIdentificada(db.Model):
    """
    Registry de entidades identificadas que precisam responder questionários
    """
    __tablename__ = 'entidades_identificadas'
    
    id = db.Column(db.Integer, primary_key=True)
    municipio = db.Column(db.String(100), nullable=False, index=True)
    tipo_entidade = db.Column(db.String(50), nullable=False)  # empresa_terceirizada, entidade_catadores, empresa_nao_vinculada
    
    # Sistema de prioridades PNSB (P1, P2, P3)
    prioridade = db.Column(db.Integer, default=2, nullable=False)  # 1 = P1 (Prefeituras + Lista UF), 2 = P2 (Identificadas em campo), 3 = P3 (Adicionais)
    categoria_prioridade = db.Column(db.String(20), default='p2', nullable=False)  # p1, p2, p3
    origem_lista_uf = db.Column(db.Boolean, default=False, nullable=False)  # Se veio da lista oficial da UF
    origem_prefeitura = db.Column(db.Boolean, default=False, nullable=False)  # Se é questionário da prefeitura
    codigo_uf = db.Column(db.String(20))  # Código de referência na lista da UF
    
    # Dados da entidade
    nome_entidade = db.Column(db.String(200), nullable=False)
    cnpj = db.Column(db.String(18), index=True)  # XX.XXX.XXX/XXXX-XX
    endereco = db.Column(db.Text)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    responsavel = db.Column(db.String(100))
    
    # Dados geográficos - Google Maps API
    endereco_original = db.Column(db.Text)  # Backup do endereço original antes da geocodificação
    endereco_formatado = db.Column(db.Text)  # Endereço formatado pelo Google Maps
    latitude = db.Column(db.Float)  # Coordenada latitude
    longitude = db.Column(db.Float)  # Coordenada longitude
    place_id = db.Column(db.String(200))  # Google Places ID único
    plus_code = db.Column(db.String(50))  # Plus Code para áreas rurais
    geocodificado_em = db.Column(db.DateTime)  # Quando foi geocodificado
    geocodificacao_confianca = db.Column(db.String(20))  # ROOFTOP, RANGE_INTERPOLATED, GEOMETRIC_CENTER, APPROXIMATE
    geocodificacao_fonte = db.Column(db.String(50), default='google_maps_api')  # Fonte da geocodificação
    geocodificacao_status = db.Column(db.String(20), default='pendente')  # pendente, sucesso, erro, ignorado
    
    # Obrigatoriedade específica de questionários
    mrs_obrigatorio = db.Column(db.Boolean, default=False, nullable=False)
    map_obrigatorio = db.Column(db.Boolean, default=False, nullable=False)
    
    # Status do questionário - APENAS CONTROLE DE STATUS (SEM PREENCHIMENTO)
    status_mrs = db.Column(db.String(20), default='nao_iniciado')  # nao_iniciado, respondido, validado_concluido, nao_aplicavel
    status_map = db.Column(db.String(20), default='nao_iniciado')  # nao_iniciado, respondido, validado_concluido, nao_aplicavel
    
    # Metadados
    identificado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    fonte_identificacao = db.Column(db.String(100))  # Como foi identificada (lista_uf, visita_prefeitura, pesquisa_web, etc.)
    
    # Relacionamento com visitas
    visita_id = db.Column(db.Integer, db.ForeignKey('visitas.id'))
    
    # Observações e validação
    observacoes = db.Column(db.Text)
    validado_em = db.Column(db.DateTime)  # Quando foi validada a obrigatoriedade dos questionários
    validado_por = db.Column(db.String(100))  # Quem validou
    
    def to_dict(self):
        return {
            'id': self.id,
            'municipio': self.municipio,
            'tipo_entidade': self.tipo_entidade,
            'prioridade': self.prioridade,
            'categoria_prioridade': self.categoria_prioridade,
            'origem_lista_uf': self.origem_lista_uf,
            'origem_prefeitura': self.origem_prefeitura,
            'codigo_uf': self.codigo_uf,
            'nome_entidade': self.nome_entidade,
            'cnpj': self.cnpj,
            'endereco': self.endereco,
            'telefone': self.telefone,
            'email': self.email,
            'responsavel': self.responsavel,
            'mrs_obrigatorio': self.mrs_obrigatorio,
            'map_obrigatorio': self.map_obrigatorio,
            'status_mrs': self.status_mrs,
            'status_map': self.status_map,
            'identificado_em': self.identificado_em.isoformat() if self.identificado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None,
            'fonte_identificacao': self.fonte_identificacao,
            'visita_id': self.visita_id,
            'observacoes': self.observacoes,
            'validado_em': self.validado_em.isoformat() if self.validado_em else None,
            'validado_por': self.validado_por,
            # Dados geográficos
            'endereco_original': self.endereco_original,
            'endereco_formatado': self.endereco_formatado,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'place_id': self.place_id,
            'plus_code': self.plus_code,
            'geocodificacao_status': self.geocodificacao_status,
            'geocodificacao_confianca': self.geocodificacao_confianca,
            'geocodificado_em': self.geocodificado_em.isoformat() if self.geocodificado_em else None,
            'geocodificacao_fonte': self.geocodificacao_fonte
        }
    
    def definir_prioridade_automatica(self):
        """Auto-classifica a prioridade baseada nas origens e tipo de entidade"""
        if self.origem_prefeitura or self.tipo_entidade == 'prefeitura':
            # P1: Questionários de prefeituras (sempre obrigatórios)
            self.prioridade = 1
            self.categoria_prioridade = 'p1'
            self.origem_prefeitura = True
        elif self.origem_lista_uf:
            # P1: Entidades da lista oficial da UF (também obrigatórias)
            self.prioridade = 1
            self.categoria_prioridade = 'p1'
        elif self.fonte_identificacao in ['visita_prefeitura', 'indicacao_informante', 'pesquisa_campo']:
            # P2: Entidades identificadas em campo (se tornam obrigatórias quando incluídas)
            self.prioridade = 2
            self.categoria_prioridade = 'p2'
        else:
            # P3: Entidades adicionais para trabalho completo (apenas referência, não obrigatórias)
            self.prioridade = 3
            self.categoria_prioridade = 'p3'
    
    @staticmethod
    def get_entidades_por_prioridade(municipio=None, prioridade=None):
        """Retorna entidades filtradas por município e/ou prioridade"""
        query = EntidadeIdentificada.query
        
        if municipio:
            query = query.filter_by(municipio=municipio)
        
        if prioridade:
            query = query.filter_by(prioridade=prioridade)
        
        return query.order_by(EntidadeIdentificada.prioridade, EntidadeIdentificada.nome_entidade).all()
    
    @staticmethod
    def get_entidades_obrigatorias(municipio=None):
        """Retorna apenas entidades obrigatórias (P1 + P2) para metas PNSB"""
        query = EntidadeIdentificada.query.filter(EntidadeIdentificada.prioridade.in_([1, 2]))
        
        if municipio:
            query = query.filter_by(municipio=municipio)
        
        return query.order_by(EntidadeIdentificada.prioridade, EntidadeIdentificada.nome_entidade).all()
    
    def sincronizar_com_visita(self):
        """Sincroniza status dos questionários com status da visita vinculada"""
        if not self.visita_id:
            return
        
        from .agendamento import Visita
        visita = Visita.query.get(self.visita_id)
        if not visita:
            return
        
        # MAPEAMENTO SIMPLIFICADO: STATUS VISITA → STATUS QUESTIONÁRIOS
        if visita.status == 'questionários validados':
            # Questionários foram validados sem críticas (APROVADOS PARA METAS PNSB)
            if self.mrs_obrigatorio:
                self.status_mrs = 'validado_concluido'
            if self.map_obrigatorio:
                self.status_map = 'validado_concluido'
        elif visita.status == 'questionários concluídos':
            # Questionários foram respondidos, aguardando validação
            if self.mrs_obrigatorio:
                self.status_mrs = 'respondido'
            if self.map_obrigatorio:
                self.status_map = 'respondido'
        elif visita.status == 'finalizada':
            # Visita finalizada = questionários validados (compatibilidade)
            if self.mrs_obrigatorio:
                self.status_mrs = 'validado_concluido'
            if self.map_obrigatorio:
                self.status_map = 'validado_concluido'
        elif visita.status == 'realizada':
            # Entrevista realizada = questionários respondidos (aguardando validação)
            if self.mrs_obrigatorio:
                self.status_mrs = 'respondido'
            if self.map_obrigatorio:
                self.status_map = 'respondido'
        elif visita.status == 'não realizada':
            # Entrevista não realizada = questionários não aplicáveis
            if self.mrs_obrigatorio:
                self.status_mrs = 'nao_aplicavel'
            if self.map_obrigatorio:
                self.status_map = 'nao_aplicavel'
        elif visita.status in ['agendada', 'em andamento', 'remarcada']:
            # Status iniciais = questionários não iniciados
            if self.mrs_obrigatorio:
                self.status_mrs = 'nao_iniciado'
            if self.map_obrigatorio:
                self.status_map = 'nao_iniciado'
    
    @staticmethod
    def sincronizar_entidades_por_visita(visita_id):
        """Sincroniza todas as entidades vinculadas a uma visita"""
        entidades = EntidadeIdentificada.query.filter_by(visita_id=visita_id).all()
        for entidade in entidades:
            entidade.sincronizar_com_visita()
        db.session.commit()
        return len(entidades)
    
    @staticmethod
    def criar_questionarios_para_visita(visita_id, municipio, tipo_pesquisa, local_nome):
        """Cria automaticamente questionários obrigatórios para uma visita"""
        from .agendamento import Visita
        
        # Verificar se já existem questionários para esta visita
        entidades_existentes = EntidadeIdentificada.query.filter_by(visita_id=visita_id).count()
        if entidades_existentes > 0:
            return entidades_existentes
        
        visita = Visita.query.get(visita_id)
        if not visita:
            return 0
        
        # Determinar obrigatoriedade baseada no tipo de pesquisa
        mrs_obrigatorio = tipo_pesquisa in ['MRS', 'ambos']
        map_obrigatorio = tipo_pesquisa in ['MAP', 'ambos']
        
        # Criar entidade baseada na visita
        entidade = EntidadeIdentificada(
            municipio=municipio,
            tipo_entidade='prefeitura',  # Default para visitas
            nome_entidade=local_nome or f'Visita {municipio}',
            mrs_obrigatorio=mrs_obrigatorio,
            map_obrigatorio=map_obrigatorio,
            status_mrs='nao_iniciado',
            status_map='nao_iniciado',
            fonte_identificacao='visita_agendada',
            visita_id=visita_id,
            prioridade=1,  # P1 para visitas agendadas
            categoria_prioridade='p1',
            origem_prefeitura=True,
            observacoes=f'Questionários gerados automaticamente para visita em {local_nome}'
        )
        
        db.session.add(entidade)
        db.session.commit()
        
        # Sincronizar status inicial
        entidade.sincronizar_com_visita()
        db.session.commit()
        
        return 1
    
    @staticmethod
    def get_entidades_informativas(municipio=None):
        """Retorna apenas entidades informativas (P3) para trabalho completo"""
        query = EntidadeIdentificada.query.filter_by(prioridade=3)
        
        if municipio:
            query = query.filter_by(municipio=municipio)
        
        return query.order_by(EntidadeIdentificada.nome_entidade).all()
    
    @staticmethod
    def get_estatisticas_prioridades(municipio=None):
        """Retorna estatísticas de questionários por prioridade"""
        query = EntidadeIdentificada.query
        
        if municipio:
            query = query.filter_by(municipio=municipio)
        
        entidades = query.all()
        
        stats = {
            'p1': {'total': 0, 'mrs_concluido': 0, 'map_concluido': 0, 'ambos_concluidos': 0},
            'p2': {'total': 0, 'mrs_concluido': 0, 'map_concluido': 0, 'ambos_concluidos': 0},
            'p3': {'total': 0, 'mrs_concluido': 0, 'map_concluido': 0, 'ambos_concluidos': 0}
        }
        
        for entidade in entidades:
            prioridade_key = f'p{entidade.prioridade}'
            stats[prioridade_key]['total'] += 1
            
            if entidade.status_mrs == 'concluido':
                stats[prioridade_key]['mrs_concluido'] += 1
            
            if entidade.status_map == 'concluido':
                stats[prioridade_key]['map_concluido'] += 1
                
            if entidade.status_mrs == 'concluido' and entidade.status_map == 'concluido':
                stats[prioridade_key]['ambos_concluidos'] += 1
        
        return stats

class ProgressoQuestionarios(db.Model):
    """
    View consolidada do progresso dos questionários obrigatórios por município
    Agora inclui tracking por prioridade (P1, P2, P3)
    """
    __tablename__ = 'progresso_questionarios'
    
    id = db.Column(db.Integer, primary_key=True)
    municipio = db.Column(db.String(100), nullable=False, index=True)
    
    # Contadores gerais de questionários obrigatórios
    total_mrs_obrigatorios = db.Column(db.Integer, default=0)
    total_map_obrigatorios = db.Column(db.Integer, default=0)
    
    # SEPARAÇÃO: Questionários Concluídos vs Validados
    mrs_concluidos = db.Column(db.Integer, default=0)      # Questionários respondidos (aguardando validação)
    map_concluidos = db.Column(db.Integer, default=0)      # Questionários respondidos (aguardando validação)
    mrs_validados = db.Column(db.Integer, default=0)       # Questionários validados sem críticas (aprovados para metas)
    map_validados = db.Column(db.Integer, default=0)       # Questionários validados sem críticas (aprovados para metas)
    
    # Percentuais de conclusão gerais
    percentual_mrs = db.Column(db.Float, default=0.0)
    percentual_map = db.Column(db.Float, default=0.0)
    percentual_geral = db.Column(db.Float, default=0.0)
    
    # === MÉTRICAS POR PRIORIDADE ===
    # P1 - Crítica (Prefeituras + Lista UF)
    p1_total_entidades = db.Column(db.Integer, default=0)
    p1_mrs_concluidos = db.Column(db.Integer, default=0)     # Respondidos
    p1_map_concluidos = db.Column(db.Integer, default=0)     # Respondidos
    p1_mrs_validados = db.Column(db.Integer, default=0)      # Validados
    p1_map_validados = db.Column(db.Integer, default=0)      # Validados
    p1_percentual_conclusao = db.Column(db.Float, default=0.0)
    
    # P2 - Importante (Identificadas em campo)
    p2_total_entidades = db.Column(db.Integer, default=0)
    p2_mrs_concluidos = db.Column(db.Integer, default=0)     # Respondidos
    p2_map_concluidos = db.Column(db.Integer, default=0)     # Respondidos
    p2_mrs_validados = db.Column(db.Integer, default=0)      # Validados
    p2_map_validados = db.Column(db.Integer, default=0)      # Validados
    p2_percentual_conclusao = db.Column(db.Float, default=0.0)
    
    # P3 - Opcional (Adicionais)
    p3_total_entidades = db.Column(db.Integer, default=0)
    p3_mrs_concluidos = db.Column(db.Integer, default=0)     # Respondidos
    p3_map_concluidos = db.Column(db.Integer, default=0)     # Respondidos
    p3_mrs_validados = db.Column(db.Integer, default=0)      # Validados
    p3_map_validados = db.Column(db.Integer, default=0)      # Validados
    p3_percentual_conclusao = db.Column(db.Float, default=0.0)
    
    # Status geral do município
    status_geral = db.Column(db.String(20), default='nao_iniciado')  # nao_iniciado, em_andamento, concluido
    status_p1 = db.Column(db.String(20), default='nao_iniciado')     # Status específico das prioridades críticas
    
    # Última atualização
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'municipio': self.municipio,
            'total_mrs_obrigatorios': self.total_mrs_obrigatorios,
            'total_map_obrigatorios': self.total_map_obrigatorios,
            'mrs_concluidos': self.mrs_concluidos,
            'map_concluidos': self.map_concluidos,
            'percentual_mrs': round(self.percentual_mrs, 1),
            'percentual_map': round(self.percentual_map, 1),
            'percentual_geral': round(self.percentual_geral, 1),
            'status_geral': self.status_geral,
            'status_p1': self.status_p1,
            # Separação clara: Obrigatórios vs Informativos
            'obrigatorios': {
                'total_mrs': self.p1_mrs_concluidos + self.p2_mrs_concluidos + (self.p1_total_entidades - self.p1_mrs_concluidos) + (self.p2_total_entidades - self.p2_mrs_concluidos),
                'total_map': self.p1_map_concluidos + self.p2_map_concluidos + (self.p1_total_entidades - self.p1_map_concluidos) + (self.p2_total_entidades - self.p2_map_concluidos),
                'mrs_concluidos': self.p1_mrs_concluidos + self.p2_mrs_concluidos,
                'map_concluidos': self.p1_map_concluidos + self.p2_map_concluidos,
                'percentual_conclusao': round(self.percentual_geral, 1),
                'descricao': 'P1 (Crítica) + P2 (Importante) - Base para metas PNSB'
            },
            'informativos': {
                'total_entidades': self.p3_total_entidades,
                'mrs_concluidos': self.p3_mrs_concluidos,
                'map_concluidos': self.p3_map_concluidos,
                'percentual_conclusao': round(self.p3_percentual_conclusao, 1),
                'descricao': 'P3 (Opcional) - Trabalho completo se houver tempo'
            },
            # Métricas por prioridade
            'prioridades': {
                'p1': {
                    'total_entidades': self.p1_total_entidades,
                    'mrs_concluidos': self.p1_mrs_concluidos,
                    'map_concluidos': self.p1_map_concluidos,
                    'percentual_conclusao': round(self.p1_percentual_conclusao, 1),
                    'descricao': 'Crítica (Prefeituras + Lista UF)'
                },
                'p2': {
                    'total_entidades': self.p2_total_entidades,
                    'mrs_concluidos': self.p2_mrs_concluidos,
                    'map_concluidos': self.p2_map_concluidos,
                    'percentual_conclusao': round(self.p2_percentual_conclusao, 1),
                    'descricao': 'Importante (Identificadas em campo)'
                },
                'p3': {
                    'total_entidades': self.p3_total_entidades,
                    'mrs_concluidos': self.p3_mrs_concluidos,
                    'map_concluidos': self.p3_map_concluidos,
                    'percentual_conclusao': round(self.p3_percentual_conclusao, 1),
                    'descricao': 'Opcional (Recursos disponíveis)'
                }
            },
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }
    
    @staticmethod
    def garantir_prefeitura_completa(municipio):
        """
        Garante que existe uma prefeitura P1 completa (MRS=True, MAP=True) para o município
        """
        MUNICIPIOS_PNSB = [
            'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas', 'Camboriú',
            'Itajaí', 'Itapema', 'Luiz Alves', 'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
        ]
        
        if municipio not in MUNICIPIOS_PNSB:
            return None
        
        # Verificar se já existe prefeitura completa
        prefeitura_existente = EntidadeIdentificada.query.filter_by(
            municipio=municipio,
            tipo_entidade='prefeitura',
            prioridade=1,
            origem_prefeitura=True,
            mrs_obrigatorio=True,
            map_obrigatorio=True
        ).first()
        
        if prefeitura_existente:
            return prefeitura_existente
        
        # CORREÇÃO: Não remover prefeituras existentes indiscriminadamente
        # Apenas verificar se existe alguma prefeitura funcional
        prefeituras_existentes = EntidadeIdentificada.query.filter_by(
            municipio=municipio,
            tipo_entidade='prefeitura'
        ).all()
        
        # Se já existe qualquer prefeitura, não fazer nada
        if prefeituras_existentes:
            print(f"⚠️ Prefeitura já existe para {municipio} - mantendo existente")
            return prefeituras_existentes[0]
        
        # Criar prefeitura completa obrigatória
        nova_prefeitura = EntidadeIdentificada(
            municipio=municipio,
            tipo_entidade='prefeitura',
            nome_entidade=f'Prefeitura de {municipio}',
            mrs_obrigatorio=True,  # FIXO: Sempre obrigatório
            map_obrigatorio=True,  # FIXO: Sempre obrigatório
            status_mrs='nao_iniciado',
            status_map='nao_iniciado',
            prioridade=1,
            categoria_prioridade='p1',
            origem_prefeitura=True,
            origem_lista_uf=False,
            fonte_identificacao='prefeitura_automatica',
            observacoes=f'Prefeitura obrigatória criada automaticamente - MRS e MAP sempre obrigatórios'
        )
        
        db.session.add(nova_prefeitura)
        db.session.commit()
        
        return nova_prefeitura

    @staticmethod
    def calcular_totais_esperados_dinamicos(municipio=None):
        """
        Calcula totais esperados de questionários de forma dinâmica baseado em:
        - 11 prefeituras (fixo, sempre MRS=1 + MAP=1 obrigatórias)
        - Entidades P1 da lista UF (obrigatórias, podem mudar)
        - Entidades P2 identificadas (obrigatórias quando incluídas, podem mudar)
        """
        # 1. Base fixa: 11 prefeituras sempre obrigatórias (MRS=1, MAP=1 cada)
        MUNICIPIOS_PNSB = [
            'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas', 'Camboriú',
            'Itajaí', 'Itapema', 'Luiz Alves', 'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
        ]
        
        if municipio:
            # Para um município específico
            if municipio in MUNICIPIOS_PNSB:
                # GARANTIR que prefeitura existe e está completa
                ProgressoQuestionarios.garantir_prefeitura_completa(municipio)
                base_prefeituras_mrs = 1  # FIXO: Sempre 1 MRS por prefeitura
                base_prefeituras_map = 1  # FIXO: Sempre 1 MAP por prefeitura
            else:
                base_prefeituras_mrs = 0
                base_prefeituras_map = 0
            
            # Entidades P1 do município
            p1_uf = EntidadePrioritariaUF.query.filter_by(municipio=municipio).all()
            p1_mrs = sum(1 for e in p1_uf if e.mrs_obrigatorio)
            p1_map = sum(1 for e in p1_uf if e.map_obrigatorio)
            
            # Entidades P2 do município
            p2_entidades = EntidadeIdentificada.query.filter(
                EntidadeIdentificada.municipio == municipio,
                EntidadeIdentificada.prioridade == 2
            ).all()
            p2_mrs = sum(1 for e in p2_entidades if e.mrs_obrigatorio)
            p2_map = sum(1 for e in p2_entidades if e.map_obrigatorio)
            
            return {
                'municipio': municipio,
                'mrs_esperados': base_prefeituras_mrs + p1_mrs + p2_mrs,
                'map_esperados': base_prefeituras_map + p1_map + p2_map,
                'detalhamento': {
                    'prefeitura': {'mrs': base_prefeituras_mrs, 'map': base_prefeituras_map},
                    'p1_uf': {'mrs': p1_mrs, 'map': p1_map, 'total': len(p1_uf)},
                    'p2_identificadas': {'mrs': p2_mrs, 'map': p2_map, 'total': len(p2_entidades)}
                }
            }
        else:
            # Para todos os municípios
            total_mrs_esperados = len(MUNICIPIOS_PNSB)  # 11 prefeituras
            total_map_esperados = len(MUNICIPIOS_PNSB)  # 11 prefeituras
            
            # Somar todas as entidades P1
            p1_todas = EntidadePrioritariaUF.query.all()
            total_mrs_esperados += sum(1 for e in p1_todas if e.mrs_obrigatorio)
            total_map_esperados += sum(1 for e in p1_todas if e.map_obrigatorio)
            
            # Somar todas as entidades P2
            p2_todas = EntidadeIdentificada.query.filter_by(prioridade=2).all()
            total_mrs_esperados += sum(1 for e in p2_todas if e.mrs_obrigatorio)
            total_map_esperados += sum(1 for e in p2_todas if e.map_obrigatorio)
            
            return {
                'total_mrs_esperados': total_mrs_esperados,
                'total_map_esperados': total_map_esperados,
                'detalhamento': {
                    'prefeituras': len(MUNICIPIOS_PNSB),
                    'p1_uf': len(p1_todas),
                    'p2_identificadas': len(p2_todas)
                }
            }

    @staticmethod
    def calcular_progresso_municipio(municipio):
        """
        Recalcula o progresso de questionários para um município usando TOTAIS ESPERADOS DINÂMICOS
        LÓGICA CORRETA: Base nas entidades obrigatórias (Prefeituras + P1 + P2), não apenas nas visitas
        """
        # 1. CALCULAR TOTAIS ESPERADOS DINÂMICOS (incluindo entidades não visitadas ainda)
        totais_esperados = ProgressoQuestionarios.calcular_totais_esperados_dinamicos(municipio)
        total_mrs_esperados = totais_esperados['mrs_esperados']
        total_map_esperados = totais_esperados['map_esperados']
        
        # 2. CONTAR QUESTIONÁRIOS RESPONDIDOS/VALIDADOS (apenas das visitas realizadas)
        entidades_visitadas = EntidadeIdentificada.query.filter_by(municipio=municipio).all()
        
        # CONTAR QUESTIONÁRIOS POR STATUS (SEPARAR CONCLUÍDOS DOS VALIDADOS)
        mrs_concluidos = sum(1 for e in entidades_visitadas if e.mrs_obrigatorio and e.status_mrs == 'respondido')
        map_concluidos = sum(1 for e in entidades_visitadas if e.map_obrigatorio and e.status_map == 'respondido')
        mrs_validados = sum(1 for e in entidades_visitadas if e.mrs_obrigatorio and e.status_mrs == 'validado_concluido')
        map_validados = sum(1 for e in entidades_visitadas if e.map_obrigatorio and e.status_map == 'validado_concluido')
        
        # 3. CALCULAR PERCENTUAIS CORRETOS (baseado nos totais esperados dinâmicos)
        percentual_mrs = (mrs_validados / total_mrs_esperados * 100) if total_mrs_esperados > 0 else 0
        percentual_map = (map_validados / total_map_esperados * 100) if total_map_esperados > 0 else 0
        total_questionarios_esperados = total_mrs_esperados + total_map_esperados
        total_validados = mrs_validados + map_validados
        percentual_geral = (total_validados / total_questionarios_esperados * 100) if total_questionarios_esperados > 0 else 0
        
        # 4. DETERMINAR STATUS
        if percentual_geral == 100:
            status_geral = 'concluido'
        elif percentual_geral > 0:
            status_geral = 'em_andamento'
        else:
            status_geral = 'nao_iniciado'
        
        # 5. ATUALIZAR OU CRIAR REGISTRO DE PROGRESSO
        progresso = ProgressoQuestionarios.query.filter_by(municipio=municipio).first()
        if not progresso:
            progresso = ProgressoQuestionarios(municipio=municipio)
            db.session.add(progresso)
        
        # 6. SALVAR MÉTRICAS CORRIGIDAS (baseadas nos totais esperados dinâmicos)
        progresso.total_mrs_obrigatorios = total_mrs_esperados
        progresso.total_map_obrigatorios = total_map_esperados
        progresso.mrs_concluidos = mrs_concluidos
        progresso.map_concluidos = map_concluidos
        progresso.mrs_validados = mrs_validados
        progresso.map_validados = map_validados
        progresso.percentual_mrs = percentual_mrs
        progresso.percentual_map = percentual_map
        progresso.percentual_geral = percentual_geral
        progresso.status_geral = status_geral
        progresso.atualizado_em = datetime.utcnow()
        
        # 7. CALCULAR MÉTRICAS POR PRIORIDADE (das entidades visitadas)
        entidades_p1 = [e for e in entidades_visitadas if e.prioridade == 1]
        entidades_p2 = [e for e in entidades_visitadas if e.prioridade == 2]
        entidades_p3 = [e for e in entidades_visitadas if e.prioridade == 3]
        
        # P1 metrics
        p1_mrs_validados = sum(1 for e in entidades_p1 if e.mrs_obrigatorio and e.status_mrs == 'validado_concluido')
        p1_map_validados = sum(1 for e in entidades_p1 if e.map_obrigatorio and e.status_map == 'validado_concluido')
        p1_total = len(entidades_p1)
        
        # P2 metrics  
        p2_mrs_validados = sum(1 for e in entidades_p2 if e.mrs_obrigatorio and e.status_mrs == 'validado_concluido')
        p2_map_validados = sum(1 for e in entidades_p2 if e.map_obrigatorio and e.status_map == 'validado_concluido')
        p2_total = len(entidades_p2)
        
        # P3 metrics
        p3_mrs_validados = sum(1 for e in entidades_p3 if e.mrs_obrigatorio and e.status_mrs == 'validado_concluido')
        p3_map_validados = sum(1 for e in entidades_p3 if e.map_obrigatorio and e.status_map == 'validado_concluido')
        p3_total = len(entidades_p3)
        
        # Salvar métricas por prioridade
        progresso.p1_total_entidades = p1_total
        progresso.p1_mrs_validados = p1_mrs_validados
        progresso.p1_map_validados = p1_map_validados
        progresso.p2_total_entidades = p2_total
        progresso.p2_mrs_validados = p2_mrs_validados
        progresso.p2_map_validados = p2_map_validados
        progresso.p3_total_entidades = p3_total
        progresso.p3_mrs_validados = p3_mrs_validados
        progresso.p3_map_validados = p3_map_validados
        
        db.session.commit()
        return progresso
        

class EntidadePrioritariaUF(db.Model):
    """
    Lista oficial de entidades prioritárias fornecida pela UF
    Estas são as entidades mais obrigatórias de todas
    """
    __tablename__ = 'entidades_prioritarias_uf'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo_uf = db.Column(db.String(20), unique=True, nullable=False, index=True)  # Código único da UF
    
    # Localização
    municipio = db.Column(db.String(100), nullable=False, index=True)
    regiao = db.Column(db.String(50))  # Região dentro do município se aplicável
    
    # Dados da entidade
    nome_entidade = db.Column(db.String(200), nullable=False)
    tipo_entidade = db.Column(db.String(50), nullable=False)  # empresa_terceirizada, entidade_catadores, empresa_nao_vinculada
    cnpj = db.Column(db.String(18), index=True)
    endereco_completo = db.Column(db.Text)
    
    # Dados geográficos - Google Maps API
    endereco_original = db.Column(db.Text)  # Backup do endereço original
    endereco_formatado = db.Column(db.Text)  # Endereço formatado pelo Google Maps
    latitude = db.Column(db.Float)  # Coordenada latitude
    longitude = db.Column(db.Float)  # Coordenada longitude
    place_id = db.Column(db.String(200))  # Google Places ID único
    plus_code = db.Column(db.String(50))  # Plus Code para áreas rurais
    geocodificado_em = db.Column(db.DateTime)  # Quando foi geocodificado
    geocodificacao_confianca = db.Column(db.String(20))  # ROOFTOP, RANGE_INTERPOLATED, GEOMETRIC_CENTER, APPROXIMATE
    geocodificacao_fonte = db.Column(db.String(50), default='google_maps_api')  # Fonte da geocodificação
    geocodificacao_status = db.Column(db.String(20), default='pendente')  # pendente, sucesso, erro, ignorado
    
    # Questionários obrigatórios específicos
    mrs_obrigatorio = db.Column(db.Boolean, default=False, nullable=False)
    map_obrigatorio = db.Column(db.Boolean, default=False, nullable=False)
    
    # Motivo da obrigatoriedade
    motivo_mrs = db.Column(db.Text)  # Por que MRS é obrigatório
    motivo_map = db.Column(db.Text)  # Por que MAP é obrigatório
    
    # Status de processamento
    processado = db.Column(db.Boolean, default=False, nullable=False)  # Se já foi convertido em EntidadeIdentificada
    data_processamento = db.Column(db.DateTime)
    
    # Metadados da lista UF
    categoria_uf = db.Column(db.String(100))  # Categoria na lista da UF
    subcategoria_uf = db.Column(db.String(100))  # Subcategoria se aplicável
    prioridade_uf = db.Column(db.Integer, default=1)  # Prioridade dentro da lista UF
    
    # Dados de contato da lista
    telefone_uf = db.Column(db.String(20))
    email_uf = db.Column(db.String(100))
    responsavel_uf = db.Column(db.String(100))
    
    # Observações da UF
    observacoes_uf = db.Column(db.Text)
    
    # Controle de importação
    importado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    arquivo_origem = db.Column(db.String(200))  # Nome do arquivo de importação
    linha_origem = db.Column(db.Integer)  # Linha no arquivo original
    
    def to_dict(self):
        return {
            'id': self.id,
            'codigo_uf': self.codigo_uf,
            'municipio': self.municipio,
            'regiao': self.regiao,
            'nome_entidade': self.nome_entidade,
            'tipo_entidade': self.tipo_entidade,
            'cnpj': self.cnpj,
            'endereco_completo': self.endereco_completo,
            'mrs_obrigatorio': self.mrs_obrigatorio,
            'map_obrigatorio': self.map_obrigatorio,
            'motivo_mrs': self.motivo_mrs,
            'motivo_map': self.motivo_map,
            'processado': self.processado,
            'data_processamento': self.data_processamento.isoformat() if self.data_processamento else None,
            'categoria_uf': self.categoria_uf,
            'subcategoria_uf': self.subcategoria_uf,
            'prioridade_uf': self.prioridade_uf,
            'telefone_uf': self.telefone_uf,
            'email_uf': self.email_uf,
            'responsavel_uf': self.responsavel_uf,
            'observacoes_uf': self.observacoes_uf,
            'importado_em': self.importado_em.isoformat() if self.importado_em else None,
            'arquivo_origem': self.arquivo_origem,
            'linha_origem': self.linha_origem
        }
    
    @staticmethod
    def processar_entidade_prioritaria(entidade_id):
        """
        Converte uma entidade prioritária da UF em EntidadeIdentificada
        GARANTE: Vínculo correto ENTIDADE + MUNICÍPIO + TIPO_QUESTIONÁRIO
        """
        entidade_uf = EntidadePrioritariaUF.query.get(entidade_id)
        if not entidade_uf or entidade_uf.processado:
            return None
        
        # VALIDAÇÃO 1: Município deve estar na lista oficial PNSB
        from gestao_visitas.config import MUNICIPIOS
        if entidade_uf.municipio not in MUNICIPIOS:
            raise ValueError(f"Município '{entidade_uf.municipio}' não está na lista oficial do PNSB 2024")
        
        # VALIDAÇÃO 2: Pelo menos um questionário deve ser obrigatório
        if not (entidade_uf.mrs_obrigatorio or entidade_uf.map_obrigatorio):
            raise ValueError(f"Entidade '{entidade_uf.nome_entidade}' deve ter pelo menos um questionário obrigatório (MRS ou MAP)")
        
        # BUSCA DE ENTIDADE EXISTENTE - Critério: CNPJ + MUNICÍPIO (vínculo obrigatório)
        entidade_existente = None
        
        # 1º - Buscar por codigo_uf (mais confiável)
        if entidade_uf.codigo_uf:
            entidade_existente = EntidadeIdentificada.query.filter_by(
                codigo_uf=entidade_uf.codigo_uf,
                municipio=entidade_uf.municipio  # SEMPRE validar município junto
            ).first()
        
        # 2º - Buscar por CNPJ + MUNICÍPIO (vínculo obrigatório)
        if not entidade_existente and entidade_uf.cnpj:
            entidade_existente = EntidadeIdentificada.query.filter_by(
                cnpj=entidade_uf.cnpj,
                municipio=entidade_uf.municipio  # NUNCA permitir entidade em município errado
            ).first()
        
        # 3º - Buscar por NOME + MUNICÍPIO (último recurso)
        if not entidade_existente:
            entidade_existente = EntidadeIdentificada.query.filter_by(
                nome_entidade=entidade_uf.nome_entidade,
                municipio=entidade_uf.municipio
            ).first()
        
        if entidade_existente:
            # ATUALIZAR ENTIDADE EXISTENTE - garantir configuração correta
            entidade_existente.origem_lista_uf = True
            entidade_existente.prioridade = 1
            entidade_existente.categoria_prioridade = 'p1'
            entidade_existente.codigo_uf = entidade_uf.codigo_uf
            
            # IMPORTANTE: Aplicar questionários obrigatórios da Lista UF
            entidade_existente.mrs_obrigatorio = entidade_uf.mrs_obrigatorio
            entidade_existente.map_obrigatorio = entidade_uf.map_obrigatorio
            
            # Atualizar dados se necessário
            if entidade_uf.cnpj and not entidade_existente.cnpj:
                entidade_existente.cnpj = entidade_uf.cnpj
            if entidade_uf.endereco_completo and not entidade_existente.endereco:
                entidade_existente.endereco = entidade_uf.endereco_completo
            if entidade_uf.telefone_uf and not entidade_existente.telefone:
                entidade_existente.telefone = entidade_uf.telefone_uf
            if entidade_uf.email_uf and not entidade_existente.email:
                entidade_existente.email = entidade_uf.email_uf
            
            entidade_existente.definir_prioridade_automatica()
            entidade = entidade_existente
        else:
            # CRIAR NOVA ENTIDADE IDENTIFICADA
            # Verificar tipo_entidade
            tipo_entidade = entidade_uf.tipo_entidade or 'empresa_terceirizada'
            
            # Validar tipo_entidade
            from gestao_visitas.config import TIPOS_ENTIDADE
            if tipo_entidade not in TIPOS_ENTIDADE:
                tipo_entidade = 'empresa_terceirizada'  # Fallback seguro
            
            # Criar entidade vinculada OBRIGATORIAMENTE ao município correto
            entidade = EntidadeIdentificada(
                municipio=entidade_uf.municipio,  # VÍNCULO OBRIGATÓRIO
                tipo_entidade=tipo_entidade,
                prioridade=1,
                categoria_prioridade='p1',
                origem_lista_uf=True,
                origem_prefeitura=False,
                codigo_uf=entidade_uf.codigo_uf,
                nome_entidade=entidade_uf.nome_entidade,
                cnpj=entidade_uf.cnpj or '',
                endereco=entidade_uf.endereco_completo or '',
                telefone=entidade_uf.telefone_uf or '',
                email=entidade_uf.email_uf or '',
                responsavel=entidade_uf.responsavel_uf or '',
                mrs_obrigatorio=entidade_uf.mrs_obrigatorio,  # OBRIGATORIEDADE ESPECÍFICA
                map_obrigatorio=entidade_uf.map_obrigatorio,  # OBRIGATORIEDADE ESPECÍFICA
                fonte_identificacao='lista_uf',
                observacoes=EntidadePrioritariaUF._gerar_observacoes_processamento(entidade_uf)
            )
            entidade.definir_prioridade_automatica()
            db.session.add(entidade)
        
        # CRIAR/ATUALIZAR QUESTIONÁRIOS OBRIGATÓRIOS POR TIPO
        EntidadePrioritariaUF._garantir_questionarios_obrigatorios(entidade_uf.municipio, tipo_entidade, entidade_uf)
        
        # Marcar como processado
        entidade_uf.processado = True
        entidade_uf.data_processamento = datetime.utcnow()
        
        db.session.commit()
        return entidade
    
    @staticmethod
    def _gerar_observacoes_processamento(entidade_uf):
        """Gera observações detalhadas do processamento da Lista UF"""
        observacoes = f"📋 Lista Oficial UF - {entidade_uf.categoria_uf or 'Sem categoria'}"
        
        if entidade_uf.subcategoria_uf:
            observacoes += f" / {entidade_uf.subcategoria_uf}"
        
        observacoes += f"\n🏛️ Município: {entidade_uf.municipio}"
        
        if entidade_uf.mrs_obrigatorio:
            observacoes += f"\n♻️ MRS OBRIGATÓRIO"
            if entidade_uf.motivo_mrs:
                observacoes += f": {entidade_uf.motivo_mrs}"
        
        if entidade_uf.map_obrigatorio:
            observacoes += f"\n💧 MAP OBRIGATÓRIO"
            if entidade_uf.motivo_map:
                observacoes += f": {entidade_uf.motivo_map}"
        
        if entidade_uf.observacoes_uf:
            observacoes += f"\n📝 Obs UF: {entidade_uf.observacoes_uf}"
        
        return observacoes
    
    @staticmethod 
    def _garantir_questionarios_obrigatorios(municipio, tipo_entidade, entidade_uf):
        """Garante que questionários obrigatórios sejam criados por tipo de entidade"""
        # Buscar questionário obrigatório existente
        questionario = QuestionarioObrigatorio.query.filter_by(
            municipio=municipio,
            tipo_entidade=tipo_entidade
        ).first()
        
        if not questionario:
            # Criar novo questionário obrigatório
            questionario = QuestionarioObrigatorio(
                municipio=municipio,
                tipo_entidade=tipo_entidade,
                mrs_obrigatorio=entidade_uf.mrs_obrigatorio,
                map_obrigatorio=entidade_uf.map_obrigatorio,
                observacoes=f"Criado via Lista UF - {entidade_uf.nome_entidade}"
            )
            db.session.add(questionario)
        else:
            # Atualizar questionário existente (OR lógico - se qualquer entidade precisar, fica obrigatório)
            if entidade_uf.mrs_obrigatorio:
                questionario.mrs_obrigatorio = True
            if entidade_uf.map_obrigatorio:
                questionario.map_obrigatorio = True
    
    @staticmethod
    def processar_todas_prioritarias():
        """Processa todas as entidades prioritárias não processadas"""
        entidades_nao_processadas = EntidadePrioritariaUF.query.filter_by(processado=False).all()
        
        entidades_processadas = []
        for entidade_uf in entidades_nao_processadas:
            entidade = EntidadePrioritariaUF.processar_entidade_prioritaria(entidade_uf.id)
            if entidade:
                entidades_processadas.append(entidade)
        
        return entidades_processadas
    
    @staticmethod
    def inicializar_questionarios_prefeituras():
        """Inicializa questionários obrigatórios para todas as 11 prefeituras (MRS + MAP cada)"""
        from gestao_visitas.config import MUNICIPIOS
        
        # Lista para tracking
        questionarios_criados = []
        entidades_criadas = []
        
        for municipio in MUNICIPIOS:
            # 1. CRIAR QUESTIONÁRIOS OBRIGATÓRIOS PARA PREFEITURA
            # Buscar ou criar questionário obrigatório para prefeitura no município
            questionario_prefeitura = QuestionarioObrigatorio.query.filter_by(
                municipio=municipio,
                tipo_entidade='prefeitura'
            ).first()
            
            if not questionario_prefeitura:
                questionario_prefeitura = QuestionarioObrigatorio(
                    municipio=municipio,
                    tipo_entidade='prefeitura',
                    mrs_obrigatorio=True,  # SEMPRE obrigatório para prefeituras
                    map_obrigatorio=True,  # SEMPRE obrigatório para prefeituras  
                    observacoes=f"Questionários obrigatórios base para Prefeitura de {municipio} - PNSB 2024"
                )
                db.session.add(questionario_prefeitura)
                questionarios_criados.append(questionario_prefeitura)
            else:
                # Garantir que prefeituras sempre tenham ambos obrigatórios
                questionario_prefeitura.mrs_obrigatorio = True
                questionario_prefeitura.map_obrigatorio = True
                questionario_prefeitura.ativo = True
            
            # 2. CRIAR ENTIDADES IDENTIFICADAS PARA PREFEITURA
            # Buscar ou criar entidade identificada para a prefeitura
            entidade_prefeitura = EntidadeIdentificada.query.filter_by(
                municipio=municipio,
                tipo_entidade='prefeitura',
                origem_prefeitura=True
            ).first()
            
            if not entidade_prefeitura:
                entidade_prefeitura = EntidadeIdentificada(
                    municipio=municipio,
                    tipo_entidade='prefeitura',
                    prioridade=1,
                    categoria_prioridade='p1',
                    origem_lista_uf=False,
                    origem_prefeitura=True,
                    nome_entidade=f"Prefeitura Municipal de {municipio}",
                    mrs_obrigatorio=True,
                    map_obrigatorio=True,
                    fonte_identificacao='sistema_base_pnsb',
                    observacoes=f"Entidade base obrigatória - Prefeitura de {municipio}"
                )
                entidade_prefeitura.definir_prioridade_automatica()
                db.session.add(entidade_prefeitura)
                entidades_criadas.append(entidade_prefeitura)
            else:
                # Garantir configuração correta da prefeitura existente
                entidade_prefeitura.prioridade = 1
                entidade_prefeitura.categoria_prioridade = 'p1'
                entidade_prefeitura.origem_prefeitura = True
                entidade_prefeitura.mrs_obrigatorio = True
                entidade_prefeitura.map_obrigatorio = True
        
        # Commit das mudanças
        db.session.commit()
        
        return {
            'questionarios_criados': len(questionarios_criados),
            'entidades_criadas': len(entidades_criadas),
            'municipios_processados': len(MUNICIPIOS),
            'detalhes': {
                'questionarios': [q.to_dict() for q in questionarios_criados],
                'entidades': [e.to_dict() for e in entidades_criadas]
            }
        }


# ===== HOOKS AUTOMÁTICOS PARA GEOCODIFICAÇÃO =====

def _geocodificar_entidade_automatica(mapper, connection, target):
    """Hook automático para geocodificar entidades quando inseridas/atualizadas"""
    try:
        # Só geocodificar se há endereço e ainda não foi processado
        endereco = None
        if hasattr(target, 'endereco') and target.endereco:
            endereco = target.endereco
        elif hasattr(target, 'endereco_completo') and target.endereco_completo:
            endereco = target.endereco_completo
        
        if endereco and target.geocodificacao_status == 'pendente':
            # Usar thread para não bloquear a transação principal
            from threading import Thread
            from flask import current_app
            
            def geocodificar_async():
                try:
                    with current_app.app_context():
                        from gestao_visitas.services.geocodificacao_service import geocodificar_nova_entidade
                        geocodificar_nova_entidade(target)
                        db.session.commit()
                except Exception as e:
                    current_app.logger.warning(f"⚠️ Erro na geocodificação automática: {str(e)}")
            
            # Executar geocodificação em background
            thread = Thread(target=geocodificar_async)
            thread.daemon = True
            thread.start()
            
    except Exception as e:
        # Não falhar a inserção se geocodificação der erro
        pass


# Registrar hooks para geocodificação automática
event.listen(EntidadeIdentificada, 'after_insert', _geocodificar_entidade_automatica)
event.listen(EntidadeIdentificada, 'after_update', _geocodificar_entidade_automatica)
event.listen(EntidadePrioritariaUF, 'after_insert', _geocodificar_entidade_automatica)
event.listen(EntidadePrioritariaUF, 'after_update', _geocodificar_entidade_automatica)