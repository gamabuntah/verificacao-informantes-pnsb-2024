"""
Modelo para Controle de Visitas Obrigatórias - PNSB 2024
======================================================

Controla e rastreia visitas obrigatórias para:
- Todas as prefeituras (obrigatórias)
- Entidades P1 com questionários obrigatórios
- Entidades P2 com questionários obrigatórios

Status: Não agendada → Agendada → Concluída
"""

from gestao_visitas.db import db
from datetime import datetime
from sqlalchemy import Index

class VisitaObrigatoria(db.Model):
    """
    Controle de visitas obrigatórias por entidade
    
    Lógica:
    - Toda prefeitura precisa de visita
    - Toda entidade P1/P2 com questionário obrigatório precisa de visita
    - Tracking: não agendada → agendada → concluída
    """
    __tablename__ = 'visitas_obrigatorias'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificação da entidade obrigatória
    municipio = db.Column(db.String(100), nullable=False, index=True)
    entidade_id = db.Column(db.Integer, db.ForeignKey('entidades_identificadas.id'), nullable=True, index=True)
    tipo_entidade = db.Column(db.String(50), nullable=False)  # prefeitura, empresa_terceirizada, etc.
    nome_entidade = db.Column(db.String(200), nullable=False)
    
    # Motivo da obrigatoriedade
    prioridade = db.Column(db.Integer, nullable=False)  # 1=P1, 2=P2
    categoria_prioridade = db.Column(db.String(10), nullable=False)  # p1, p2
    motivo_obrigatoriedade = db.Column(db.Text)  # Por que é obrigatória
    
    # Questionários obrigatórios relacionados
    requer_mrs = db.Column(db.Boolean, default=False, nullable=False)
    requer_map = db.Column(db.Boolean, default=False, nullable=False)
    
    # ===== STATUS DA VISITA OBRIGATÓRIA =====
    status_visita = db.Column(db.String(20), default='nao_agendada', nullable=False)
    # nao_agendada: Visita ainda não foi agendada
    # agendada: Visita foi agendada mas não realizada
    # concluida: Visita foi realizada com sucesso
    # reagendada: Visita precisou ser reagendada
    # cancelada: Visita foi cancelada (entidade não aplicável)
    
    # Relacionamento com visita real
    visita_id = db.Column(db.Integer, db.ForeignKey('visitas.id'), nullable=True, index=True)
    
    # Datas de controle
    data_identificacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_agendamento = db.Column(db.DateTime, nullable=True)
    data_conclusao = db.Column(db.DateTime, nullable=True)
    
    # Observações e justificativas
    observacoes = db.Column(db.Text)
    justificativa_status = db.Column(db.Text)  # Por que está neste status
    
    # Metadados
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relacionamentos
    entidade = db.relationship('EntidadeIdentificada', backref='visitas_obrigatorias_relacionadas')
    visita = db.relationship('Visita', backref='visitas_obrigatorias_vinculadas')
    
    # Índices compostos para performance
    __table_args__ = (
        Index('idx_municipio_status', 'municipio', 'status_visita'),
        Index('idx_prioridade_status', 'prioridade', 'status_visita'),
        Index('idx_ativo_municipio', 'ativo', 'municipio'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'municipio': self.municipio,
            'entidade_id': self.entidade_id,
            'tipo_entidade': self.tipo_entidade,
            'nome_entidade': self.nome_entidade,
            'prioridade': self.prioridade,
            'categoria_prioridade': self.categoria_prioridade,
            'motivo_obrigatoriedade': self.motivo_obrigatoriedade,
            'requer_mrs': self.requer_mrs,
            'requer_map': self.requer_map,
            'status_visita': self.status_visita,
            'visita_id': self.visita_id,
            'data_identificacao': self.data_identificacao.isoformat() if self.data_identificacao else None,
            'data_agendamento': self.data_agendamento.isoformat() if self.data_agendamento else None,
            'data_conclusao': self.data_conclusao.isoformat() if self.data_conclusao else None,
            'observacoes': self.observacoes,
            'justificativa_status': self.justificativa_status,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None,
            'ativo': self.ativo,
            # Dados da visita vinculada (se existir)
            'visita_info': self.visita.to_dict() if self.visita else None,
            # Status calculado
            'dias_desde_identificacao': (datetime.utcnow() - self.data_identificacao).days if self.data_identificacao else None,
            'prazo_vencido': self._verificar_prazo_vencido(),
            'proxima_acao': self._recomendar_proxima_acao()
        }
    
    def atualizar_status(self, novo_status, justificativa=None):
        """Atualiza status da visita obrigatória com validação"""
        status_validos = ['nao_agendada', 'agendada', 'concluida', 'reagendada', 'cancelada']
        
        if novo_status not in status_validos:
            raise ValueError(f'Status inválido: {novo_status}')
        
        # Validar transições
        transicoes_validas = {
            'nao_agendada': ['agendada', 'cancelada'],
            'agendada': ['concluida', 'reagendada', 'nao_agendada'],
            'concluida': ['reagendada'],  # Pode reabrir se necessário
            'reagendada': ['agendada', 'cancelada'],
            'cancelada': ['nao_agendada']  # Pode reativar
        }
        
        if novo_status not in transicoes_validas.get(self.status_visita, []):
            raise ValueError(f'Transição não permitida: {self.status_visita} → {novo_status}')
        
        status_anterior = self.status_visita
        self.status_visita = novo_status
        self.justificativa_status = justificativa or f'Status alterado de {status_anterior} para {novo_status}'
        
        # Atualizar datas
        if novo_status == 'agendada':
            self.data_agendamento = datetime.utcnow()
        elif novo_status == 'concluida':
            self.data_conclusao = datetime.utcnow()
        
        self.atualizado_em = datetime.utcnow()
        return True
    
    def vincular_visita(self, visita_id, auto_atualizar_status=True):
        """Vincula uma visita real à visita obrigatória"""
        from .agendamento import Visita
        
        visita = Visita.query.get(visita_id)
        if not visita:
            raise ValueError('Visita não encontrada')
        
        if visita.municipio != self.municipio:
            raise ValueError('Visita deve ser do mesmo município')
        
        self.visita_id = visita_id
        
        if auto_atualizar_status:
            # Sincronizar status baseado na visita
            if visita.status in ['agendada', 'em andamento']:
                if self.status_visita == 'nao_agendada':
                    self.atualizar_status('agendada', f'Visita agendada: {visita.data}')
            elif visita.status in ['realizada', 'finalizada', 'questionários validados']:
                if self.status_visita in ['nao_agendada', 'agendada']:
                    self.atualizar_status('concluida', f'Visita concluída: {visita.status}')
        
        self.atualizado_em = datetime.utcnow()
        return True
    
    def desvincular_visita(self, motivo=None):
        """Remove vínculo com visita (ex: visita cancelada)"""
        if self.visita_id:
            visita_anterior = self.visita_id
            self.visita_id = None
            
            # Retroceder status se necessário
            if self.status_visita == 'concluida':
                self.atualizar_status('nao_agendada', motivo or f'Visita {visita_anterior} desvinculada')
            elif self.status_visita == 'agendada':
                self.atualizar_status('nao_agendada', motivo or f'Visita {visita_anterior} cancelada')
        
        return True
    
    def _verificar_prazo_vencido(self):
        """Verifica se a visita está em atraso (lógica customizável)"""
        if self.status_visita == 'concluida':
            return False
        
        dias_desde_identificacao = (datetime.utcnow() - self.data_identificacao).days
        
        # Critérios de prazo por prioridade
        if self.prioridade == 1:  # P1 - mais urgente
            return dias_desde_identificacao > 30  # 30 dias para P1
        elif self.prioridade == 2:  # P2 
            return dias_desde_identificacao > 45  # 45 dias para P2
        else:
            return dias_desde_identificacao > 60  # 60 dias para P3
    
    def _recomendar_proxima_acao(self):
        """Recomenda a próxima ação baseada no status"""
        if self.status_visita == 'nao_agendada':
            if self._verificar_prazo_vencido():
                return f"⚠️ URGENTE: Agendar visita (P{self.prioridade} em atraso)"
            return f"📅 Agendar visita para {self.nome_entidade}"
        
        elif self.status_visita == 'agendada':
            if self.visita and self.visita.data:
                return f"✅ Visita agendada para {self.visita.data.strftime('%d/%m/%Y')}"
            return "✅ Visita agendada - verificar data"
        
        elif self.status_visita == 'concluida':
            return "✅ Visita concluída"
        
        elif self.status_visita == 'reagendada':
            return "🔄 Reagendar visita"
        
        elif self.status_visita == 'cancelada':
            return "❌ Visita cancelada"
        
        return "Verificar status"

class StatusVisitasObrigatorias(db.Model):
    """
    Consolidação do status de visitas obrigatórias por município
    """
    __tablename__ = 'status_visitas_obrigatorias'
    
    id = db.Column(db.Integer, primary_key=True)
    municipio = db.Column(db.String(100), nullable=False, unique=True, index=True)
    
    # Contadores gerais
    total_obrigatorias = db.Column(db.Integer, default=0)
    nao_agendadas = db.Column(db.Integer, default=0)
    agendadas = db.Column(db.Integer, default=0)
    concluidas = db.Column(db.Integer, default=0)
    reagendadas = db.Column(db.Integer, default=0)
    canceladas = db.Column(db.Integer, default=0)
    
    # Métricas por prioridade
    p1_total = db.Column(db.Integer, default=0)
    p1_concluidas = db.Column(db.Integer, default=0)
    p2_total = db.Column(db.Integer, default=0)
    p2_concluidas = db.Column(db.Integer, default=0)
    
    # Percentuais
    percentual_conclusao = db.Column(db.Float, default=0.0)
    percentual_p1 = db.Column(db.Float, default=0.0)
    percentual_p2 = db.Column(db.Float, default=0.0)
    
    # Status geral
    status_geral = db.Column(db.String(20), default='nao_iniciado')
    # nao_iniciado: Nenhuma visita agendada
    # em_andamento: Algumas agendadas/concluídas
    # completo: Todas P1 concluídas
    # finalizado: Todas obrigatórias concluídas
    
    # Alertas
    visitas_em_atraso = db.Column(db.Integer, default=0)
    visitas_urgentes = db.Column(db.Integer, default=0)
    
    # Metadados
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'municipio': self.municipio,
            'total_obrigatorias': self.total_obrigatorias,
            'nao_agendadas': self.nao_agendadas,
            'agendadas': self.agendadas,
            'concluidas': self.concluidas,
            'reagendadas': self.reagendadas,
            'canceladas': self.canceladas,
            'p1_total': self.p1_total,
            'p1_concluidas': self.p1_concluidas,
            'p2_total': self.p2_total,
            'p2_concluidas': self.p2_concluidas,
            'percentual_conclusao': round(self.percentual_conclusao, 1),
            'percentual_p1': round(self.percentual_p1, 1),
            'percentual_p2': round(self.percentual_p2, 1),
            'status_geral': self.status_geral,
            'visitas_em_atraso': self.visitas_em_atraso,
            'visitas_urgentes': self.visitas_urgentes,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None,
            # Status calculados
            'municipio_completo': self.percentual_p1 == 100.0,
            'precisa_atencao': self.visitas_em_atraso > 0 or self.visitas_urgentes > 0,
            'resumo_status': self._gerar_resumo_status()
        }
    
    def _gerar_resumo_status(self):
        """Gera resumo textual do status"""
        if self.percentual_conclusao == 100:
            return "✅ Todas as visitas obrigatórias concluídas"
        elif self.percentual_p1 == 100:
            return f"✅ P1 completo - {self.p2_concluidas}/{self.p2_total} P2 concluídas"
        elif self.visitas_urgentes > 0:
            return f"⚠️ {self.visitas_urgentes} visitas urgentes pendentes"
        elif self.visitas_em_atraso > 0:
            return f"🔔 {self.visitas_em_atraso} visitas em atraso"
        elif self.concluidas > 0:
            return f"🔄 {self.concluidas}/{self.total_obrigatorias} visitas concluídas"
        else:
            return f"📅 {self.total_obrigatorias} visitas para agendar"
    
    @staticmethod
    def recalcular_status_municipio(municipio):
        """Recalcula status de visitas obrigatórias para um município"""
        
        # Buscar todas as visitas obrigatórias do município
        visitas_obrigatorias = VisitaObrigatoria.query.filter_by(
            municipio=municipio,
            ativo=True
        ).all()
        
        if not visitas_obrigatorias:
            return None
        
        # Contar por status
        total = len(visitas_obrigatorias)
        nao_agendadas = sum(1 for v in visitas_obrigatorias if v.status_visita == 'nao_agendada')
        agendadas = sum(1 for v in visitas_obrigatorias if v.status_visita == 'agendada')
        concluidas = sum(1 for v in visitas_obrigatorias if v.status_visita == 'concluida')
        reagendadas = sum(1 for v in visitas_obrigatorias if v.status_visita == 'reagendada')
        canceladas = sum(1 for v in visitas_obrigatorias if v.status_visita == 'cancelada')
        
        # Contar por prioridade
        p1_visitas = [v for v in visitas_obrigatorias if v.prioridade == 1]
        p2_visitas = [v for v in visitas_obrigatorias if v.prioridade == 2]
        
        p1_total = len(p1_visitas)
        p1_concluidas = sum(1 for v in p1_visitas if v.status_visita == 'concluida')
        p2_total = len(p2_visitas)
        p2_concluidas = sum(1 for v in p2_visitas if v.status_visita == 'concluida')
        
        # Calcular percentuais
        percentual_conclusao = (concluidas / total * 100) if total > 0 else 0
        percentual_p1 = (p1_concluidas / p1_total * 100) if p1_total > 0 else 100
        percentual_p2 = (p2_concluidas / p2_total * 100) if p2_total > 0 else 100
        
        # Determinar status geral
        if percentual_conclusao == 100:
            status_geral = 'finalizado'
        elif percentual_p1 == 100:
            status_geral = 'completo'
        elif concluidas > 0 or agendadas > 0:
            status_geral = 'em_andamento'
        else:
            status_geral = 'nao_iniciado'
        
        # Contar alertas
        visitas_em_atraso = sum(1 for v in visitas_obrigatorias if v._verificar_prazo_vencido())
        visitas_urgentes = sum(1 for v in visitas_obrigatorias 
                              if v._verificar_prazo_vencido() and v.prioridade == 1)
        
        # Atualizar ou criar registro
        status = StatusVisitasObrigatorias.query.filter_by(municipio=municipio).first()
        if not status:
            status = StatusVisitasObrigatorias(municipio=municipio)
            db.session.add(status)
        
        # Atualizar dados
        status.total_obrigatorias = total
        status.nao_agendadas = nao_agendadas
        status.agendadas = agendadas
        status.concluidas = concluidas
        status.reagendadas = reagendadas
        status.canceladas = canceladas
        status.p1_total = p1_total
        status.p1_concluidas = p1_concluidas
        status.p2_total = p2_total
        status.p2_concluidas = p2_concluidas
        status.percentual_conclusao = percentual_conclusao
        status.percentual_p1 = percentual_p1
        status.percentual_p2 = percentual_p2
        status.status_geral = status_geral
        status.visitas_em_atraso = visitas_em_atraso
        status.visitas_urgentes = visitas_urgentes
        status.atualizado_em = datetime.utcnow()
        
        db.session.commit()
        return status

# ===== FUNÇÕES UTILITÁRIAS =====

def inicializar_visitas_obrigatorias():
    """
    Inicializa visitas obrigatórias para todas as entidades que precisam
    
    Lógica:
    1. Todas as prefeituras precisam de visita
    2. Todas as entidades P1 com questionários obrigatórios
    3. Todas as entidades P2 com questionários obrigatórios
    """
    from .questionarios_obrigatorios import EntidadeIdentificada
    from gestao_visitas.config import MUNICIPIOS as MUNICIPIOS_PNSB
    
    visitas_criadas = []
    
    # 1. CRIAR VISITAS OBRIGATÓRIAS PARA PREFEITURAS
    for municipio in MUNICIPIOS_PNSB:
        
        # Verificar se já existe visita obrigatória para prefeitura
        visita_existente = VisitaObrigatoria.query.filter_by(
            municipio=municipio,
            tipo_entidade='prefeitura',
            ativo=True
        ).first()
        
        if not visita_existente:
            # Buscar entidade prefeitura
            entidade_prefeitura = EntidadeIdentificada.query.filter_by(
                municipio=municipio,
                tipo_entidade='prefeitura',
                origem_prefeitura=True
            ).first()
            
            visita_obrigatoria = VisitaObrigatoria(
                municipio=municipio,
                entidade_id=entidade_prefeitura.id if entidade_prefeitura else None,
                tipo_entidade='prefeitura',
                nome_entidade=f'Prefeitura de {municipio}',
                prioridade=1,
                categoria_prioridade='p1',
                motivo_obrigatoriedade='Prefeitura - sempre obrigatória para PNSB',
                requer_mrs=True,
                requer_map=True,
                status_visita='nao_agendada',
                observacoes=f'Visita obrigatória para prefeitura de {municipio} - gerada automaticamente'
            )
            
            db.session.add(visita_obrigatoria)
            visitas_criadas.append(visita_obrigatoria)
    
    # 2. CRIAR VISITAS OBRIGATÓRIAS PARA ENTIDADES P1/P2 COM QUESTIONÁRIOS
    entidades_obrigatorias = EntidadeIdentificada.query.filter(
        EntidadeIdentificada.prioridade.in_([1, 2]),
        db.or_(
            EntidadeIdentificada.mrs_obrigatorio == True,
            EntidadeIdentificada.map_obrigatorio == True
        )
    ).all()
    
    for entidade in entidades_obrigatorias:
        # Verificar se já existe visita obrigatória
        visita_existente = VisitaObrigatoria.query.filter_by(
            entidade_id=entidade.id,
            ativo=True
        ).first()
        
        if not visita_existente and entidade.tipo_entidade != 'prefeitura':  # Prefeituras já foram processadas
            visita_obrigatoria = VisitaObrigatoria(
                municipio=entidade.municipio,
                entidade_id=entidade.id,
                tipo_entidade=entidade.tipo_entidade,
                nome_entidade=entidade.nome_entidade,
                prioridade=entidade.prioridade,
                categoria_prioridade=entidade.categoria_prioridade,
                motivo_obrigatoriedade=f'P{entidade.prioridade} com questionários obrigatórios',
                requer_mrs=entidade.mrs_obrigatorio,
                requer_map=entidade.map_obrigatorio,
                status_visita='nao_agendada',
                observacoes=f'Visita obrigatória para {entidade.nome_entidade} - P{entidade.prioridade}'
            )
            
            db.session.add(visita_obrigatoria)
            visitas_criadas.append(visita_obrigatoria)
    
    # 3. VINCULAR VISITAS EXISTENTES
    visitas_existentes = db.session.query(
        VisitaObrigatoria.id,
        VisitaObrigatoria.municipio,
        VisitaObrigatoria.entidade_id
    ).filter_by(visita_id=None, ativo=True).all()
    
    for visita_obrigatoria_id, municipio, entidade_id in visitas_existentes:
        # Buscar visita real correspondente
        from .agendamento import Visita
        
        visita_real = None
        if entidade_id:
            # Buscar por entidade vinculada
            entidade = EntidadeIdentificada.query.get(entidade_id)
            if entidade and entidade.visita_id:
                visita_real = Visita.query.get(entidade.visita_id)
        
        if not visita_real:
            # Buscar visita por município (mais genérico)
            visita_real = Visita.query.filter_by(municipio=municipio).first()
        
        if visita_real:
            visita_obrigatoria = VisitaObrigatoria.query.get(visita_obrigatoria_id)
            try:
                visita_obrigatoria.vincular_visita(visita_real.id, auto_atualizar_status=True)
            except:
                pass  # Ignorar erros de vinculação
    
    db.session.commit()
    
    # 4. RECALCULAR STATUS PARA TODOS OS MUNICÍPIOS
    for municipio in MUNICIPIOS_PNSB:
        StatusVisitasObrigatorias.recalcular_status_municipio(municipio)
    
    return {
        'visitas_criadas': len(visitas_criadas),
        'municipios_processados': len(MUNICIPIOS_PNSB),
        'detalhes': [v.to_dict() for v in visitas_criadas[:10]]  # Primeiras 10 para exemplo
    }

def sincronizar_visita_obrigatoria_com_visita_real(visita_id):
    """Sincroniza visitas obrigatórias quando uma visita real é atualizada"""
    from .agendamento import Visita
    
    visita = Visita.query.get(visita_id)
    if not visita:
        return False
    
    # Buscar visitas obrigatórias vinculadas
    visitas_obrigatorias = VisitaObrigatoria.query.filter_by(
        visita_id=visita_id,
        ativo=True
    ).all()
    
    for visita_obrigatoria in visitas_obrigatorias:
        try:
            # Sincronizar status baseado na visita real
            if visita.status in ['agendada', 'em andamento']:
                if visita_obrigatoria.status_visita == 'nao_agendada':
                    visita_obrigatoria.atualizar_status('agendada', f'Sincronizado com visita: {visita.status}')
            elif visita.status in ['realizada', 'finalizada', 'questionários validados']:
                if visita_obrigatoria.status_visita in ['nao_agendada', 'agendada']:
                    visita_obrigatoria.atualizar_status('concluida', f'Sincronizado com visita: {visita.status}')
            elif visita.status in ['cancelada', 'não realizada']:
                if visita_obrigatoria.status_visita in ['agendada']:
                    visita_obrigatoria.atualizar_status('reagendada', f'Visita cancelada: {visita.status}')
        except:
            pass  # Ignorar erros de sincronização
    
    # Recalcular status do município
    if visitas_obrigatorias:
        StatusVisitasObrigatorias.recalcular_status_municipio(visita.municipio)
    
    db.session.commit()
    return len(visitas_obrigatorias)