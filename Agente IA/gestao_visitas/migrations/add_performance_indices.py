"""
Script para adicionar índices de performance ao banco de dados
"""

from gestao_visitas.db import db
from gestao_visitas.models.agendamento import Visita
from gestao_visitas.models.checklist import Checklist
from gestao_visitas.models.contatos import Contato
from gestao_visitas.models.questionarios_obrigatorios import (
    QuestionarioObrigatorio, 
    EntidadeIdentificada, 
    ProgressoQuestionarios,
    EntidadePrioritariaUF
)
from sqlalchemy import Index
import os
import sys

# Adicionar o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_indices():
    """Cria índices para melhorar performance das queries mais comuns"""
    
    print("🚀 Iniciando criação de índices de performance...")
    
    try:
        # Índices para Visita
        Index('idx_visita_municipio', Visita.municipio).create(bind=db.engine, checkfirst=True)
        Index('idx_visita_data', Visita.data).create(bind=db.engine, checkfirst=True)
        Index('idx_visita_status', Visita.status).create(bind=db.engine, checkfirst=True)
        Index('idx_visita_tipo_informante', Visita.tipo_informante).create(bind=db.engine, checkfirst=True)
        Index('idx_visita_municipio_data', Visita.municipio, Visita.data).create(bind=db.engine, checkfirst=True)
        print("✅ Índices de Visita criados")
        
        # Índices para Checklist
        Index('idx_checklist_visita_id', Checklist.visita_id).create(bind=db.engine, checkfirst=True)
        print("✅ Índices de Checklist criados")
        
        # Índices para Contato
        Index('idx_contato_municipio', Contato.municipio).create(bind=db.engine, checkfirst=True)
        Index('idx_contato_tipo_entidade', Contato.tipo_entidade).create(bind=db.engine, checkfirst=True)
        Index('idx_contato_fonte', Contato.fonte).create(bind=db.engine, checkfirst=True)
        print("✅ Índices de Contato criados")
        
        # Índices para QuestionarioObrigatorio
        Index('idx_questionario_municipio', QuestionarioObrigatorio.municipio).create(bind=db.engine, checkfirst=True)
        Index('idx_questionario_tipo_entidade', QuestionarioObrigatorio.tipo_entidade).create(bind=db.engine, checkfirst=True)
        Index('idx_questionario_ativo', QuestionarioObrigatorio.ativo).create(bind=db.engine, checkfirst=True)
        Index('idx_questionario_municipio_tipo', QuestionarioObrigatorio.municipio, QuestionarioObrigatorio.tipo_entidade).create(bind=db.engine, checkfirst=True)
        print("✅ Índices de QuestionarioObrigatorio criados")
        
        # Índices para EntidadeIdentificada
        Index('idx_entidade_municipio', EntidadeIdentificada.municipio).create(bind=db.engine, checkfirst=True)
        Index('idx_entidade_tipo', EntidadeIdentificada.tipo_entidade).create(bind=db.engine, checkfirst=True)
        Index('idx_entidade_prioridade', EntidadeIdentificada.prioridade).create(bind=db.engine, checkfirst=True)
        Index('idx_entidade_status_mrs', EntidadeIdentificada.status_mrs).create(bind=db.engine, checkfirst=True)
        Index('idx_entidade_status_map', EntidadeIdentificada.status_map).create(bind=db.engine, checkfirst=True)
        Index('idx_entidade_municipio_prioridade', EntidadeIdentificada.municipio, EntidadeIdentificada.prioridade).create(bind=db.engine, checkfirst=True)
        print("✅ Índices de EntidadeIdentificada criados")
        
        # Índices para ProgressoQuestionarios
        Index('idx_progresso_municipio', ProgressoQuestionarios.municipio).create(bind=db.engine, checkfirst=True)
        print("✅ Índices de ProgressoQuestionarios criados")
        
        # Índices para EntidadePrioritariaUF
        Index('idx_uf_municipio', EntidadePrioritariaUF.municipio).create(bind=db.engine, checkfirst=True)
        Index('idx_uf_processado', EntidadePrioritariaUF.processado).create(bind=db.engine, checkfirst=True)
        Index('idx_uf_municipio_processado', EntidadePrioritariaUF.municipio, EntidadePrioritariaUF.processado).create(bind=db.engine, checkfirst=True)
        print("✅ Índices de EntidadePrioritariaUF criados")
        
        print("\n✨ Todos os índices foram criados com sucesso!")
        print("📊 Isso deve melhorar significativamente a performance das queries")
        
    except Exception as e:
        print(f"\n❌ Erro ao criar índices: {str(e)}")
        raise


if __name__ == "__main__":
    # Para executar diretamente
    from app import app
    
    with app.app_context():
        create_indices()