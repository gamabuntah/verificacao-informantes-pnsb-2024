"""Adiciona campos PNSB aos modelos

Revision ID: 001_add_pnsb_fields
Revises: 45b8c4200dbc
Create Date: 2025-06-30 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '001_add_pnsb_fields'
down_revision = '45b8c4200dbc'
branch_labels = None
depends_on = None


def upgrade():
    # ### Adicionar campos PNSB ao modelo Contato ###
    with op.batch_alter_table('contatos', schema=None) as batch_op:
        # Campos principais do informante
        batch_op.add_column(sa.Column('nome', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('telefone', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('email', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('cargo', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('orgao', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('endereco', sa.String(length=500), nullable=True))
        
        # Campos para funcionalidades avançadas (JSON)
        batch_op.add_column(sa.Column('historico_abordagens', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('historico_comunicacao', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('data_ultima_tentativa', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('status_ultimo_contato', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('preferencias_contato', sa.Text(), nullable=True))
        
        # Campos de auditoria
        batch_op.add_column(sa.Column('data_criacao', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('data_atualizacao', sa.DateTime(), nullable=True))
        
        # Criar índices para campos importantes
        batch_op.create_index('idx_contatos_nome', ['nome'])
    
    # ### Adicionar campo pesquisador_responsavel ao modelo Visita ###
    with op.batch_alter_table('visitas', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pesquisador_responsavel', sa.String(length=100), nullable=True))
        batch_op.create_index('idx_visitas_pesquisador', ['pesquisador_responsavel'])


def downgrade():
    # ### Remover campos PNSB do modelo Contato ###
    with op.batch_alter_table('contatos', schema=None) as batch_op:
        batch_op.drop_index('idx_contatos_nome')
        batch_op.drop_column('data_atualizacao')
        batch_op.drop_column('data_criacao')
        batch_op.drop_column('preferencias_contato')
        batch_op.drop_column('status_ultimo_contato')
        batch_op.drop_column('data_ultima_tentativa')
        batch_op.drop_column('historico_comunicacao')
        batch_op.drop_column('historico_abordagens')
        batch_op.drop_column('endereco')
        batch_op.drop_column('orgao')
        batch_op.drop_column('cargo')
        batch_op.drop_column('email')
        batch_op.drop_column('telefone')
        batch_op.drop_column('nome')
    
    # ### Remover campo pesquisador_responsavel do modelo Visita ###
    with op.batch_alter_table('visitas', schema=None) as batch_op:
        batch_op.drop_index('idx_visitas_pesquisador')
        batch_op.drop_column('pesquisador_responsavel')