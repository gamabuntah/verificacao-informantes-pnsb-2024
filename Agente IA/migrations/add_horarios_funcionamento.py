"""
Migração para adicionar tabela de horários de funcionamento
"""

from flask import current_app
from gestao_visitas.db import db
from gestao_visitas.models.horarios_funcionamento import HorariosFuncionamento
import logging

logger = logging.getLogger(__name__)

def migrate_horarios_funcionamento():
    """
    Cria a tabela de horários de funcionamento se não existir
    """
    try:
        # Verificar se a tabela já existe usando a API correta
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if inspector.has_table('horarios_funcionamento'):
            logger.info("Tabela 'horarios_funcionamento' já existe")
            return True
        
        # Criar tabela
        db.create_all()
        logger.info("Tabela 'horarios_funcionamento' criada com sucesso")
        
        # Adicionar dados iniciais se necessário
        populate_initial_data()
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao criar tabela de horários: {str(e)}")
        return False

def populate_initial_data():
    """
    Popula dados iniciais na tabela de horários
    """
    try:
        # Municípios PNSB Santa Catarina
        municipios = [
            'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas', 
            'Camboriú', 'Itajaí', 'Itapema', 'Luiz Alves', 
            'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
        ]
        
        tipos_estabelecimento = ['prefeitura', 'saae', 'secretaria']
        
        # Verificar se já existem registros
        existing_count = HorariosFuncionamento.query.count()
        if existing_count > 0:
            logger.info(f"Tabela já possui {existing_count} registros")
            return
        
        # Criar registros iniciais (sem horários para forçar busca na API)
        for municipio in municipios:
            for tipo in tipos_estabelecimento:
                nome = f"{tipo.title()} de {municipio}"
                
                record = HorariosFuncionamento(
                    municipio=municipio,
                    tipo_estabelecimento=tipo,
                    nome_estabelecimento=nome,
                    fonte='A ser preenchido via API'
                )
                
                db.session.add(record)
        
        db.session.commit()
        logger.info(f"Criados {len(municipios) * len(tipos_estabelecimento)} registros iniciais")
        
    except Exception as e:
        logger.error(f"Erro ao popular dados iniciais: {str(e)}")
        db.session.rollback()

if __name__ == '__main__':
    # Executar migração
    migrate_horarios_funcionamento()