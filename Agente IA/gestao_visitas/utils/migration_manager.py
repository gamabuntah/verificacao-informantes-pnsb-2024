"""
Sistema de Migração e Backup para o PNSB
Garante que não haja perda de dados durante mudanças de schema
"""

import os
import json
import shutil
from datetime import datetime
from sqlalchemy import create_engine, text, inspect
from typing import Dict, List, Any, Optional

class MigrationManager:
    """Gerenciador de migrações e backups do banco de dados"""
    
    def __init__(self, db_path: str = 'gestao_visitas/gestao_visitas.db'):
        self.db_path = db_path
        self.backup_dir = 'gestao_visitas/backups'
        self.migrations_dir = 'gestao_visitas/migrations'
        self.engine = create_engine(f'sqlite:///{db_path}')
        
        # Criar diretórios se não existirem
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.migrations_dir, exist_ok=True)
    
    def create_backup(self, description: str = "") -> str:
        """Cria um backup completo do banco de dados"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.db"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            # Copiar arquivo do banco
            shutil.copy2(self.db_path, backup_path)
            
            # Criar arquivo de metadados
            metadata = {
                'created_at': datetime.now().isoformat(),
                'original_path': self.db_path,
                'description': description,
                'schema_info': self._get_schema_info(),
                'data_counts': self._get_data_counts()
            }
            
            metadata_path = os.path.join(self.backup_dir, f"backup_{timestamp}.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Backup criado: {backup_filename}")
            print(f"📊 Dados salvos: {metadata['data_counts']}")
            
            return backup_path
            
        except Exception as e:
            print(f"❌ Erro ao criar backup: {e}")
            return ""
    
    def export_data_to_json(self) -> str:
        """Exporta todos os dados para JSON (backup lógico)"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_filename = f"data_export_{timestamp}.json"
        export_path = os.path.join(self.backup_dir, export_filename)
        
        try:
            data_export = {
                'export_info': {
                    'created_at': datetime.now().isoformat(),
                    'schema_version': self._get_schema_version(),
                    'tables': []
                },
                'data': {}
            }
            
            with self.engine.connect() as conn:
                inspector = inspect(self.engine)
                tables = inspector.get_table_names()
                
                for table_name in tables:
                    if table_name == 'sqlite_sequence':
                        continue
                        
                    # Exportar dados da tabela
                    result = conn.execute(text(f"SELECT * FROM {table_name}"))
                    columns = result.keys()
                    rows = []
                    
                    for row in result:
                        row_dict = {}
                        for i, col in enumerate(columns):
                            value = row[i]
                            # Converter tipos especiais para JSON
                            if hasattr(value, 'isoformat'):  # datetime
                                value = value.isoformat()
                            elif hasattr(value, 'strftime'):  # time
                                value = value.strftime('%H:%M:%S')
                            row_dict[col] = value
                        rows.append(row_dict)
                    
                    data_export['data'][table_name] = {
                        'columns': list(columns),
                        'rows': rows,
                        'count': len(rows)
                    }
                    
                    data_export['export_info']['tables'].append({
                        'name': table_name,
                        'columns': list(columns),
                        'row_count': len(rows)
                    })
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data_export, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Dados exportados para: {export_filename}")
            return export_path
            
        except Exception as e:
            print(f"❌ Erro ao exportar dados: {e}")
            return ""
    
    def import_data_from_json(self, json_path: str) -> bool:
        """Importa dados de um arquivo JSON"""
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data_export = json.load(f)
            
            print(f"📥 Importando dados de: {os.path.basename(json_path)}")
            print(f"📅 Exportado em: {data_export['export_info']['created_at']}")
            
            with self.engine.connect() as conn:
                trans = conn.begin()
                
                try:
                    # Limpar tabelas existentes
                    for table_info in data_export['export_info']['tables']:
                        table_name = table_info['name']
                        conn.execute(text(f"DELETE FROM {table_name}"))
                    
                    # Importar dados
                    for table_name, table_data in data_export['data'].items():
                        if table_data['count'] == 0:
                            continue
                            
                        columns = table_data['columns']
                        placeholders = ', '.join(['?' for _ in columns])
                        
                        insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                        
                        for row in table_data['rows']:
                            values = [row[col] for col in columns]
                            conn.execute(text(insert_sql), values)
                    
                    trans.commit()
                    print("✅ Dados importados com sucesso")
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    print(f"❌ Erro na importação: {e}")
                    return False
                    
        except Exception as e:
            print(f"❌ Erro ao ler arquivo JSON: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """Lista todos os backups disponíveis"""
        
        backups = []
        
        try:
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.json') and filename.startswith('backup_'):
                    metadata_path = os.path.join(self.backup_dir, filename)
                    
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    backup_filename = filename.replace('.json', '.db')
                    backup_path = os.path.join(self.backup_dir, backup_filename)
                    
                    if os.path.exists(backup_path):
                        backups.append({
                            'metadata_file': filename,
                            'backup_file': backup_filename,
                            'created_at': metadata['created_at'],
                            'description': metadata.get('description', ''),
                            'data_counts': metadata.get('data_counts', {}),
                            'size_mb': round(os.path.getsize(backup_path) / 1024 / 1024, 2)
                        })
            
            # Ordenar por data de criação (mais recente primeiro)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            print(f"❌ Erro ao listar backups: {e}")
        
        return backups
    
    def restore_backup(self, backup_filename: str) -> bool:
        """Restaura um backup específico"""
        
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        if not os.path.exists(backup_path):
            print(f"❌ Backup não encontrado: {backup_filename}")
            return False
        
        try:
            # Criar backup do estado atual antes de restaurar
            current_backup = self.create_backup("Backup antes de restauração")
            
            # Restaurar backup
            shutil.copy2(backup_path, self.db_path)
            
            print(f"✅ Backup restaurado: {backup_filename}")
            print(f"💾 Estado atual salvo em: {os.path.basename(current_backup)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao restaurar backup: {e}")
            return False
    
    def _get_schema_info(self) -> Dict[str, Any]:
        """Obtém informações sobre o schema atual"""
        
        schema_info = {}
        
        try:
            with self.engine.connect() as conn:
                inspector = inspect(self.engine)
                
                for table_name in inspector.get_table_names():
                    if table_name == 'sqlite_sequence':
                        continue
                        
                    columns = inspector.get_columns(table_name)
                    schema_info[table_name] = [
                        {
                            'name': col['name'],
                            'type': str(col['type']),
                            'nullable': col['nullable'],
                            'default': col['default']
                        }
                        for col in columns
                    ]
        
        except Exception as e:
            print(f"⚠️ Erro ao obter schema: {e}")
        
        return schema_info
    
    def _get_data_counts(self) -> Dict[str, int]:
        """Obtém contagem de registros por tabela"""
        
        counts = {}
        
        try:
            with self.engine.connect() as conn:
                inspector = inspect(self.engine)
                
                for table_name in inspector.get_table_names():
                    if table_name == 'sqlite_sequence':
                        continue
                        
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    counts[table_name] = result.fetchone()[0]
        
        except Exception as e:
            print(f"⚠️ Erro ao contar registros: {e}")
        
        return counts
    
    def _get_schema_version(self) -> str:
        """Gera uma versão do schema baseada na estrutura"""
        
        schema_info = self._get_schema_info()
        schema_str = json.dumps(schema_info, sort_keys=True)
        
        # Usar hash simples como versão
        import hashlib
        return hashlib.md5(schema_str.encode()).hexdigest()[:8]

# Função de conveniência para criar backup rápido
def create_quick_backup(description: str = "") -> str:
    """Cria um backup rápido do estado atual"""
    manager = MigrationManager()
    return manager.create_backup(description)

# Função para listar backups disponíveis
def list_available_backups():
    """Lista todos os backups disponíveis"""
    manager = MigrationManager()
    backups = manager.list_backups()
    
    if not backups:
        print("📂 Nenhum backup encontrado")
        return
    
    print("📂 BACKUPS DISPONÍVEIS")
    print("=" * 50)
    
    for i, backup in enumerate(backups, 1):
        print(f"{i}. {backup['backup_file']}")
        print(f"   📅 Criado: {backup['created_at']}")
        print(f"   📝 Descrição: {backup['description'] or 'Sem descrição'}")
        print(f"   📊 Dados: {backup['data_counts']}")
        print(f"   💾 Tamanho: {backup['size_mb']} MB")
        print()

if __name__ == "__main__":
    # Teste do sistema de migração
    print("🔧 SISTEMA DE MIGRAÇÃO PNSB")
    print("=" * 30)
    
    manager = MigrationManager()
    
    # Criar backup do estado atual
    backup_path = manager.create_backup("Backup inicial - sistema de migração implementado")
    
    # Exportar dados para JSON
    json_path = manager.export_data_to_json()
    
    # Listar backups
    list_available_backups()
    
    print("🎉 Sistema de migração configurado!")
    print("💡 Use as funções do MigrationManager para futuras alterações")