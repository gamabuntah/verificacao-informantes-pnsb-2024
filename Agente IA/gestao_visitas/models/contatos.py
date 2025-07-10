from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from gestao_visitas.db import db
import json

class TipoEntidade:
    PREFEITURA = "prefeitura"
    EMPRESA_TERCEIRIZADA = "empresa_terceirizada"
    ENTIDADE_CATADORES = "entidade_catadores"

class FonteInformacao:
    CHATGPT = "chatgpt"
    GEMINI = "gemini"
    GROK = "grok"
    MAIS_PROVAVEL = "mais_provavel"

class Contato(db.Model):
    __tablename__ = 'contatos'

    id = Column(Integer, primary_key=True)
    municipio = Column(String(100), nullable=False, index=True)  # Índice para consultas por município
    tipo_entidade = Column(String(50), nullable=False, default=TipoEntidade.PREFEITURA, index=True)  # Índice para filtros por tipo
    tipo_pesquisa = Column(String(10), nullable=False, index=True)  # Índice para MRS ou MAP
    
    # Campos principais - cada IA e o mais provável
    local_chatgpt = Column(String(200))
    local_gemini = Column(String(200))
    local_grok = Column(String(200))
    local_mais_provavel = Column(String(200))

    responsavel_chatgpt = Column(String(200))
    responsavel_gemini = Column(String(200))
    responsavel_grok = Column(String(200))
    responsavel_mais_provavel = Column(String(200))

    endereco_chatgpt = Column(String(500))
    endereco_gemini = Column(String(500))
    endereco_grok = Column(String(500))
    endereco_mais_provavel = Column(String(500))

    contato_chatgpt = Column(String(200))
    contato_gemini = Column(String(200))
    contato_grok = Column(String(200))
    contato_mais_provavel = Column(String(200))

    horario_chatgpt = Column(String(200))
    horario_gemini = Column(String(200))
    horario_grok = Column(String(200))
    horario_mais_provavel = Column(String(200))
    
    # Campos adicionais para funcionalidades PNSB
    nome = Column(String(200), index=True)  # Nome do informante
    telefone = Column(String(50))
    email = Column(String(200))
    cargo = Column(String(200))
    orgao = Column(String(200))
    endereco = Column(String(500))
    
    # Campos para funcionalidades avançadas
    historico_abordagens = Column(Text)  # JSON com histórico de tentativas
    historico_comunicacao = Column(Text)  # JSON com histórico de comunicações
    data_ultima_tentativa = Column(DateTime)
    status_ultimo_contato = Column(String(50))
    preferencias_contato = Column(Text)  # JSON com preferências
    
    # Campos de auditoria
    data_criacao = Column(DateTime, default=datetime.utcnow)
    data_atualizacao = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'municipio': self.municipio,
            'tipo_entidade': self.tipo_entidade,
            'tipo_pesquisa': self.tipo_pesquisa,
            'local_chatgpt': self.local_chatgpt,
            'local_gemini': self.local_gemini,
            'local_grok': self.local_grok,
            'local_mais_provavel': self.local_mais_provavel,
            'responsavel_chatgpt': self.responsavel_chatgpt,
            'responsavel_gemini': self.responsavel_gemini,
            'responsavel_grok': self.responsavel_grok,
            'responsavel_mais_provavel': self.responsavel_mais_provavel,
            'endereco_chatgpt': self.endereco_chatgpt,
            'endereco_gemini': self.endereco_gemini,
            'endereco_grok': self.endereco_grok,
            'endereco_mais_provavel': self.endereco_mais_provavel,
            'contato_chatgpt': self.contato_chatgpt,
            'contato_gemini': self.contato_gemini,
            'contato_grok': self.contato_grok,
            'contato_mais_provavel': self.contato_mais_provavel,
            'horario_chatgpt': self.horario_chatgpt,
            'horario_gemini': self.horario_gemini,
            'horario_grok': self.horario_grok,
            'horario_mais_provavel': self.horario_mais_provavel,
            # Campos PNSB
            'nome': self.nome,
            'telefone': self.telefone,
            'email': self.email,
            'cargo': self.cargo,
            'orgao': self.orgao,
            'endereco': self.endereco,
            'historico_abordagens': self.historico_abordagens,
            'historico_comunicacao': self.historico_comunicacao,
            'data_ultima_tentativa': self.data_ultima_tentativa.isoformat() if self.data_ultima_tentativa else None,
            'status_ultimo_contato': self.status_ultimo_contato,
            'preferencias_contato': self.preferencias_contato,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        } 