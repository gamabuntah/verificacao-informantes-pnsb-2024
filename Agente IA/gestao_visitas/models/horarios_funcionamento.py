"""
Modelo para cache de horários de funcionamento
"""

from gestao_visitas.db import db
from datetime import datetime, timedelta
import json

class HorariosFuncionamento(db.Model):
    """Modelo para armazenar horários de funcionamento em cache"""
    
    __tablename__ = 'horarios_funcionamento'
    
    id = db.Column(db.Integer, primary_key=True)
    municipio = db.Column(db.String(100), nullable=False)
    tipo_estabelecimento = db.Column(db.String(50), nullable=False)
    nome_estabelecimento = db.Column(db.String(200), nullable=False)
    
    # Dados do Google Places
    place_id = db.Column(db.String(200), nullable=True)
    endereco = db.Column(db.String(300), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    website = db.Column(db.String(200), nullable=True)
    
    # Horários em JSON
    horarios_json = db.Column(db.Text, nullable=True)
    
    # Status
    is_open_now = db.Column(db.Boolean, default=False)
    business_status = db.Column(db.String(50), nullable=True)
    
    # Metadados
    fonte = db.Column(db.String(50), default='Google Places API')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Índices compostos
    __table_args__ = (
        db.Index('idx_municipio_tipo', 'municipio', 'tipo_estabelecimento'),
        db.Index('idx_updated_at', 'updated_at'),
    )
    
    def __repr__(self):
        return f'<HorariosFuncionamento {self.municipio} - {self.tipo_estabelecimento}>'
    
    @property
    def horarios(self):
        """Retorna horários como dict"""
        if self.horarios_json:
            try:
                return json.loads(self.horarios_json)
            except json.JSONDecodeError:
                return {}
        return {}
    
    @horarios.setter
    def horarios(self, value):
        """Define horários como JSON"""
        if isinstance(value, dict):
            self.horarios_json = json.dumps(value, ensure_ascii=False)
        else:
            self.horarios_json = None
    
    def is_cache_valid(self, max_age_hours=24):
        """Verifica se o cache ainda é válido"""
        if not self.updated_at:
            return False
        
        age = datetime.utcnow() - self.updated_at
        return age.total_seconds() < (max_age_hours * 3600)
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            'id': self.id,
            'municipio': self.municipio,
            'tipo_estabelecimento': self.tipo_estabelecimento,
            'nome_estabelecimento': self.nome_estabelecimento,
            'place_id': self.place_id,
            'endereco': self.endereco,
            'telefone': self.telefone,
            'website': self.website,
            'horarios': self.horarios,
            'is_open_now': self.is_open_now,
            'business_status': self.business_status,
            'fonte': self.fonte,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'cache_valid': self.is_cache_valid()
        }
    
    @classmethod
    def get_or_create(cls, municipio, tipo_estabelecimento, nome_estabelecimento):
        """Obtém ou cria um registro de horários"""
        existing = cls.query.filter_by(
            municipio=municipio,
            tipo_estabelecimento=tipo_estabelecimento
        ).first()
        
        if existing:
            return existing, False
        
        new_record = cls(
            municipio=municipio,
            tipo_estabelecimento=tipo_estabelecimento,
            nome_estabelecimento=nome_estabelecimento
        )
        
        db.session.add(new_record)
        db.session.commit()
        
        return new_record, True
    
    @classmethod
    def get_cached_horarios(cls, municipio, tipo_estabelecimento):
        """Obtém horários do cache se válidos"""
        record = cls.query.filter_by(
            municipio=municipio,
            tipo_estabelecimento=tipo_estabelecimento
        ).first()
        
        if record and record.is_cache_valid():
            return record.to_dict()
        
        return None
    
    @classmethod
    def update_horarios(cls, municipio, tipo_estabelecimento, dados_google):
        """Atualiza horários com dados do Google Places"""
        record, created = cls.get_or_create(
            municipio=municipio,
            tipo_estabelecimento=tipo_estabelecimento,
            nome_estabelecimento=dados_google.get('name', f'{tipo_estabelecimento} {municipio}')
        )
        
        # Atualizar dados
        record.place_id = dados_google.get('place_id')
        record.endereco = dados_google.get('formatted_address')
        record.telefone = dados_google.get('formatted_phone_number')
        record.website = dados_google.get('website')
        
        # Horários de funcionamento
        opening_hours = dados_google.get('opening_hours', {})
        record.horarios = opening_hours
        record.is_open_now = opening_hours.get('open_now', False)
        record.business_status = dados_google.get('business_status', 'OPERATIONAL')
        
        record.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return record.to_dict()
    
    @classmethod
    def cleanup_old_cache(cls, max_age_days=7):
        """Remove cache antigo"""
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        
        old_records = cls.query.filter(
            cls.updated_at < cutoff_date
        ).all()
        
        count = len(old_records)
        
        for record in old_records:
            db.session.delete(record)
        
        db.session.commit()
        
        return count
    
    @classmethod
    def get_all_municipios_tipos(cls):
        """Retorna todos os municípios e tipos cadastrados"""
        result = db.session.query(
            cls.municipio,
            cls.tipo_estabelecimento
        ).distinct().all()
        
        return [
            {'municipio': r.municipio, 'tipo_estabelecimento': r.tipo_estabelecimento}
            for r in result
        ]