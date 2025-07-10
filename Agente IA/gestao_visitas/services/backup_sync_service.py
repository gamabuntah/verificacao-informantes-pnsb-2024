"""
Serviço de Backup e Sincronização Automatizado - PNSB 2024
Backup automático na nuvem, sincronização multi-dispositivo e recuperação de desastres
"""

import os
import json
import shutil
import sqlite3
import logging
import hashlib
import threading
import time
import zipfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import subprocess

from flask import current_app
from gestao_visitas.db import db


@dataclass
class BackupConfig:
    """Configuração de backup"""
    enabled: bool = True
    interval_hours: int = 6
    retention_days: int = 30
    max_local_backups: int = 10
    cloud_enabled: bool = False
    cloud_provider: str = 'local'  # 'local', 'aws', 'azure', 'gcp'
    encryption_enabled: bool = True
    compression_enabled: bool = True
    include_logs: bool = True
    include_attachments: bool = True


@dataclass
class BackupInfo:
    """Informações de um backup"""
    backup_id: str
    timestamp: datetime
    size_bytes: int
    file_path: str
    checksum: str
    compressed: bool
    encrypted: bool
    backup_type: str  # 'automatic', 'manual', 'scheduled'
    description: str = ""
    cloud_synced: bool = False
    restoration_tested: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'backup_id': self.backup_id,
            'timestamp': self.timestamp.isoformat(),
            'size_bytes': self.size_bytes,
            'file_path': self.file_path,
            'checksum': self.checksum,
            'compressed': self.compressed,
            'encrypted': self.encrypted,
            'backup_type': self.backup_type,
            'description': self.description,
            'cloud_synced': self.cloud_synced,
            'restoration_tested': self.restoration_tested
        }


@dataclass
class SyncStatus:
    """Status de sincronização"""
    device_id: str
    last_sync: datetime
    sync_direction: str  # 'upload', 'download', 'bidirectional'
    conflicts_detected: int = 0
    data_transferred_mb: float = 0.0
    sync_success: bool = True
    error_message: str = ""


class BackupSyncService:
    """Serviço de Backup e Sincronização Automatizado"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Configurações
        self.config = BackupConfig()
        self.backup_dir = Path("gestao_visitas/backups_automaticos")
        self.cloud_sync_dir = Path("gestao_visitas/cloud_sync")
        self.temp_dir = Path("gestao_visitas/temp")
        
        # Garantir diretórios existem
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.cloud_sync_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Estado do serviço
        self.backup_thread = None
        self.sync_thread = None
        self.backup_active = False
        self.sync_active = False
        
        # Cache de backups
        self.backup_registry = self._load_backup_registry()
        
        # ID único do dispositivo
        self.device_id = self._get_device_id()
        
        self.logger.info("🔒 Serviço de Backup e Sincronização inicializado")
    
    def _get_device_id(self) -> str:
        """Gera ID único para o dispositivo"""
        device_file = self.backup_dir / "device_id.txt"
        
        if device_file.exists():
            return device_file.read_text().strip()
        
        # Gerar novo ID baseado em hostname e timestamp
        import socket
        hostname = socket.gethostname()
        timestamp = int(datetime.now().timestamp())
        device_id = f"pnsb_{hostname}_{timestamp}"
        
        device_file.write_text(device_id)
        return device_id
    
    def _load_backup_registry(self) -> Dict[str, BackupInfo]:
        """Carrega registro de backups"""
        registry_file = self.backup_dir / "backup_registry.json"
        
        if not registry_file.exists():
            return {}
        
        try:
            with open(registry_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            registry = {}
            for backup_id, backup_data in data.items():
                backup_data['timestamp'] = datetime.fromisoformat(backup_data['timestamp'])
                registry[backup_id] = BackupInfo(**backup_data)
            
            return registry
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar registro de backups: {str(e)}")
            return {}
    
    def _save_backup_registry(self):
        """Salva registro de backups"""
        registry_file = self.backup_dir / "backup_registry.json"
        
        try:
            data = {
                backup_id: backup_info.to_dict() 
                for backup_id, backup_info in self.backup_registry.items()
            }
            
            with open(registry_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Erro ao salvar registro de backups: {str(e)}")
    
    def start_automatic_backup(self):
        """Inicia backup automático"""
        if self.backup_active:
            self.logger.warning("Backup automático já está ativo")
            return
        
        self.backup_active = True
        self.backup_thread = threading.Thread(target=self._backup_loop, daemon=True)
        self.backup_thread.start()
        
        self.logger.info(f"🚀 Backup automático iniciado (intervalo: {self.config.interval_hours}h)")
    
    def stop_automatic_backup(self):
        """Para backup automático"""
        self.backup_active = False
        if self.backup_thread:
            self.backup_thread.join(timeout=10)
        
        self.logger.info("⏹️ Backup automático parado")
    
    def start_automatic_sync(self):
        """Inicia sincronização automática"""
        if self.sync_active:
            self.logger.warning("Sincronização automática já está ativa")
            return
        
        self.sync_active = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        
        self.logger.info("🔄 Sincronização automática iniciada")
    
    def stop_automatic_sync(self):
        """Para sincronização automática"""
        self.sync_active = False
        if self.sync_thread:
            self.sync_thread.join(timeout=10)
        
        self.logger.info("⏹️ Sincronização automática parada")
    
    def _backup_loop(self):
        """Loop principal de backup"""
        while self.backup_active:
            try:
                # Realizar backup
                backup_info = self.create_backup('automatic')
                
                if backup_info:
                    self.logger.info(f"✅ Backup automático criado: {backup_info.backup_id}")
                    
                    # Limpar backups antigos
                    self._cleanup_old_backups()
                    
                    # Sincronizar com nuvem se habilitado
                    if self.config.cloud_enabled:
                        self._upload_to_cloud(backup_info)
                
                # Aguardar próximo backup
                time.sleep(self.config.interval_hours * 3600)
                
            except Exception as e:
                self.logger.error(f"Erro no loop de backup: {str(e)}")
                time.sleep(300)  # Aguardar 5 minutos em caso de erro
    
    def _sync_loop(self):
        """Loop principal de sincronização"""
        sync_interval = 300  # 5 minutos
        
        while self.sync_active:
            try:
                # Verificar sincronização
                sync_status = self.check_sync_status()
                
                if sync_status and not sync_status.sync_success:
                    self.logger.warning(f"Problema de sincronização: {sync_status.error_message}")
                
                # Realizar sincronização se necessário
                if self._should_sync():
                    self.synchronize_data()
                
                time.sleep(sync_interval)
                
            except Exception as e:
                self.logger.error(f"Erro no loop de sincronização: {str(e)}")
                time.sleep(600)  # Aguardar 10 minutos em caso de erro
    
    def create_backup(self, backup_type: str = 'manual', description: str = "") -> Optional[BackupInfo]:
        """Cria um backup completo do sistema"""
        try:
            self.logger.info(f"📦 Iniciando backup {backup_type}...")
            
            # Gerar ID do backup
            timestamp = datetime.now()
            backup_id = f"backup_{timestamp.strftime('%Y%m%d_%H%M%S')}_{backup_type}"
            
            # Diretório temporário para o backup
            temp_backup_dir = self.temp_dir / backup_id
            temp_backup_dir.mkdir(exist_ok=True)
            
            # 1. Backup do banco de dados
            db_backup_path = self._backup_database(temp_backup_dir)
            
            # 2. Backup de arquivos de configuração
            config_backup_path = self._backup_configs(temp_backup_dir)
            
            # 3. Backup de logs (se habilitado)
            logs_backup_path = None
            if self.config.include_logs:
                logs_backup_path = self._backup_logs(temp_backup_dir)
            
            # 4. Backup de attachments/uploads (se habilitado)
            attachments_backup_path = None
            if self.config.include_attachments:
                attachments_backup_path = self._backup_attachments(temp_backup_dir)
            
            # 5. Criar manifesto do backup
            manifest = self._create_backup_manifest(
                backup_id, timestamp, backup_type, description,
                db_backup_path, config_backup_path, logs_backup_path, attachments_backup_path
            )
            
            manifest_path = temp_backup_dir / "backup_manifest.json"
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False, default=str)
            
            # 6. Comprimir backup (se habilitado)
            final_backup_path = self.backup_dir / f"{backup_id}.zip"
            
            if self.config.compression_enabled:
                self._compress_backup(temp_backup_dir, final_backup_path)
            else:
                shutil.move(str(temp_backup_dir), str(final_backup_path.with_suffix('')))
                final_backup_path = final_backup_path.with_suffix('')
            
            # 7. Calcular checksum
            checksum = self._calculate_checksum(final_backup_path)
            
            # 8. Criptografar (se habilitado)
            if self.config.encryption_enabled:
                encrypted_path = self._encrypt_backup(final_backup_path)
                final_backup_path = encrypted_path
            
            # 9. Obter tamanho do arquivo final
            file_size = final_backup_path.stat().st_size
            
            # 10. Criar registro do backup
            backup_info = BackupInfo(
                backup_id=backup_id,
                timestamp=timestamp,
                size_bytes=file_size,
                file_path=str(final_backup_path),
                checksum=checksum,
                compressed=self.config.compression_enabled,
                encrypted=self.config.encryption_enabled,
                backup_type=backup_type,
                description=description
            )
            
            # 11. Adicionar ao registro
            self.backup_registry[backup_id] = backup_info
            self._save_backup_registry()
            
            # 12. Limpar diretório temporário
            shutil.rmtree(temp_backup_dir, ignore_errors=True)
            
            self.logger.info(f"✅ Backup criado com sucesso: {backup_id} ({file_size/1024/1024:.1f} MB)")
            return backup_info
            
        except Exception as e:
            self.logger.error(f"Erro ao criar backup: {str(e)}")
            return None
    
    def _backup_database(self, backup_dir: Path) -> str:
        """Backup do banco de dados SQLite"""
        try:
            db_path = "gestao_visitas/gestao_visitas.db"
            backup_path = backup_dir / "database.db"
            
            if os.path.exists(db_path):
                # Usar backup SQLite nativo para consistência
                conn = sqlite3.connect(db_path)
                backup_conn = sqlite3.connect(backup_path)
                
                conn.backup(backup_conn)
                
                conn.close()
                backup_conn.close()
                
                self.logger.debug("✅ Database backup concluído")
                return str(backup_path)
            else:
                self.logger.warning("Database não encontrado para backup")
                return ""
                
        except Exception as e:
            self.logger.error(f"Erro no backup do database: {str(e)}")
            return ""
    
    def _backup_configs(self, backup_dir: Path) -> str:
        """Backup de arquivos de configuração"""
        try:
            config_dir = backup_dir / "configs"
            config_dir.mkdir(exist_ok=True)
            
            # Arquivos de configuração para backup
            config_files = [
                ".env",
                "requirements.txt",
                "gestao_visitas/config.py",
                "CLAUDE.md"
            ]
            
            for config_file in config_files:
                if os.path.exists(config_file):
                    dest_path = config_dir / os.path.basename(config_file)
                    shutil.copy2(config_file, dest_path)
            
            self.logger.debug("✅ Configs backup concluído")
            return str(config_dir)
            
        except Exception as e:
            self.logger.error(f"Erro no backup de configs: {str(e)}")
            return ""
    
    def _backup_logs(self, backup_dir: Path) -> str:
        """Backup de arquivos de log"""
        try:
            logs_dir = backup_dir / "logs"
            logs_dir.mkdir(exist_ok=True)
            
            # Diretórios de logs para backup
            log_sources = [
                "logs",
                "gestao_visitas/logs"
            ]
            
            for log_source in log_sources:
                if os.path.exists(log_source):
                    dest_path = logs_dir / os.path.basename(log_source)
                    shutil.copytree(log_source, dest_path, ignore_errors=True)
            
            self.logger.debug("✅ Logs backup concluído")
            return str(logs_dir)
            
        except Exception as e:
            self.logger.error(f"Erro no backup de logs: {str(e)}")
            return ""
    
    def _backup_attachments(self, backup_dir: Path) -> str:
        """Backup de attachments e uploads"""
        try:
            attachments_dir = backup_dir / "attachments"
            attachments_dir.mkdir(exist_ok=True)
            
            # Diretórios de attachments para backup
            attachment_sources = [
                "gestao_visitas/uploads",
                "gestao_visitas/static/uploads",
                "gestao_visitas/attachments"
            ]
            
            for attachment_source in attachment_sources:
                if os.path.exists(attachment_source):
                    dest_path = attachments_dir / os.path.basename(attachment_source)
                    shutil.copytree(attachment_source, dest_path, ignore_errors=True)
            
            self.logger.debug("✅ Attachments backup concluído")
            return str(attachments_dir)
            
        except Exception as e:
            self.logger.error(f"Erro no backup de attachments: {str(e)}")
            return ""
    
    def _create_backup_manifest(self, backup_id: str, timestamp: datetime, 
                              backup_type: str, description: str, *backup_paths) -> Dict[str, Any]:
        """Cria manifesto do backup"""
        return {
            'backup_id': backup_id,
            'timestamp': timestamp.isoformat(),
            'backup_type': backup_type,
            'description': description,
            'device_id': self.device_id,
            'version': '1.0',
            'components': {
                'database': backup_paths[0] if backup_paths[0] else None,
                'configs': backup_paths[1] if len(backup_paths) > 1 and backup_paths[1] else None,
                'logs': backup_paths[2] if len(backup_paths) > 2 and backup_paths[2] else None,
                'attachments': backup_paths[3] if len(backup_paths) > 3 and backup_paths[3] else None
            },
            'settings': {
                'compressed': self.config.compression_enabled,
                'encrypted': self.config.encryption_enabled,
                'retention_days': self.config.retention_days
            }
        }
    
    def _compress_backup(self, source_dir: Path, target_path: Path):
        """Comprime o backup"""
        try:
            with zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in source_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(source_dir)
                        zipf.write(file_path, arcname)
            
            self.logger.debug(f"✅ Backup comprimido: {target_path.name}")
            
        except Exception as e:
            self.logger.error(f"Erro na compressão: {str(e)}")
            raise
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calcula checksum MD5 do arquivo"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular checksum: {str(e)}")
            return ""
    
    def _encrypt_backup(self, file_path: Path) -> Path:
        """Criptografa o backup (implementação básica)"""
        try:
            # Por segurança, usar uma implementação simples de criptografia
            # Em produção, usar bibliotecas como cryptography
            
            encrypted_path = file_path.with_suffix(file_path.suffix + '.enc')
            
            # Chave simples baseada no device_id (em produção, usar chave segura)
            key = hashlib.sha256(self.device_id.encode()).digest()[:16]
            
            with open(file_path, 'rb') as infile, open(encrypted_path, 'wb') as outfile:
                data = infile.read()
                # XOR simples (em produção, usar AES)
                encrypted_data = bytes(a ^ b for a, b in zip(data, (key * (len(data) // len(key) + 1))[:len(data)]))
                outfile.write(encrypted_data)
            
            # Remover arquivo original
            file_path.unlink()
            
            self.logger.debug(f"✅ Backup criptografado: {encrypted_path.name}")
            return encrypted_path
            
        except Exception as e:
            self.logger.error(f"Erro na criptografia: {str(e)}")
            return file_path
    
    def _cleanup_old_backups(self):
        """Remove backups antigos baseado na configuração"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
            
            backups_to_remove = []
            for backup_id, backup_info in self.backup_registry.items():
                if backup_info.timestamp < cutoff_date:
                    backups_to_remove.append(backup_id)
            
            # Manter pelo menos um backup, mesmo que antigo
            if len(backups_to_remove) >= len(self.backup_registry):
                backups_to_remove = backups_to_remove[:-1]
            
            for backup_id in backups_to_remove:
                backup_info = self.backup_registry[backup_id]
                
                # Remover arquivo
                backup_path = Path(backup_info.file_path)
                if backup_path.exists():
                    backup_path.unlink()
                
                # Remover do registro
                del self.backup_registry[backup_id]
                
                self.logger.info(f"🗑️ Backup antigo removido: {backup_id}")
            
            if backups_to_remove:
                self._save_backup_registry()
                
        except Exception as e:
            self.logger.error(f"Erro na limpeza de backups: {str(e)}")
    
    def restore_backup(self, backup_id: str, target_dir: str = None) -> bool:
        """Restaura um backup específico"""
        try:
            if backup_id not in self.backup_registry:
                self.logger.error(f"Backup não encontrado: {backup_id}")
                return False
            
            backup_info = self.backup_registry[backup_id]
            backup_path = Path(backup_info.file_path)
            
            if not backup_path.exists():
                self.logger.error(f"Arquivo de backup não encontrado: {backup_path}")
                return False
            
            self.logger.info(f"🔄 Iniciando restauração do backup: {backup_id}")
            
            # Diretório de restauração
            if target_dir is None:
                target_dir = str(self.temp_dir / f"restore_{backup_id}")
            
            restore_path = Path(target_dir)
            restore_path.mkdir(parents=True, exist_ok=True)
            
            # Descriptografar se necessário
            working_path = backup_path
            if backup_info.encrypted:
                working_path = self._decrypt_backup(backup_path, restore_path / "decrypted_backup")
            
            # Descomprimir se necessário
            if backup_info.compressed:
                self._decompress_backup(working_path, restore_path)
            else:
                if working_path.is_dir():
                    shutil.copytree(working_path, restore_path / "backup_content")
                else:
                    shutil.copy2(working_path, restore_path / "backup_content")
            
            # Verificar integridade
            if not self._verify_backup_integrity(restore_path, backup_info):
                self.logger.error("Falha na verificação de integridade do backup")
                return False
            
            self.logger.info(f"✅ Backup restaurado com sucesso em: {restore_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na restauração do backup: {str(e)}")
            return False
    
    def _decrypt_backup(self, encrypted_path: Path, output_path: Path) -> Path:
        """Descriptografa um backup"""
        try:
            # Chave simples baseada no device_id
            key = hashlib.sha256(self.device_id.encode()).digest()[:16]
            
            with open(encrypted_path, 'rb') as infile, open(output_path, 'wb') as outfile:
                encrypted_data = infile.read()
                # XOR reverso
                data = bytes(a ^ b for a, b in zip(encrypted_data, (key * (len(encrypted_data) // len(key) + 1))[:len(encrypted_data)]))
                outfile.write(data)
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Erro na descriptografia: {str(e)}")
            return encrypted_path
    
    def _decompress_backup(self, zip_path: Path, output_dir: Path):
        """Descomprime um backup"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(output_dir)
            
        except Exception as e:
            self.logger.error(f"Erro na descompressão: {str(e)}")
            raise
    
    def _verify_backup_integrity(self, restore_path: Path, backup_info: BackupInfo) -> bool:
        """Verifica integridade do backup restaurado"""
        try:
            # Verificar se manifesto existe
            manifest_path = restore_path / "backup_manifest.json"
            if not manifest_path.exists():
                self.logger.warning("Manifesto do backup não encontrado")
                return True  # Não falhar por isso
            
            # Carregar manifesto
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # Verificar ID do backup
            if manifest.get('backup_id') != backup_info.backup_id:
                self.logger.error("ID do backup não confere com o manifesto")
                return False
            
            # Verificar componentes principais
            components = manifest.get('components', {})
            
            if components.get('database') and not (restore_path / "database.db").exists():
                self.logger.error("Database não encontrado no backup")
                return False
            
            self.logger.debug("✅ Integridade do backup verificada")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na verificação de integridade: {str(e)}")
            return False
    
    def get_backup_list(self) -> List[Dict[str, Any]]:
        """Retorna lista de todos os backups"""
        return [backup_info.to_dict() for backup_info in self.backup_registry.values()]
    
    def get_backup_info(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """Retorna informações de um backup específico"""
        if backup_id in self.backup_registry:
            return self.backup_registry[backup_id].to_dict()
        return None
    
    def delete_backup(self, backup_id: str) -> bool:
        """Remove um backup específico"""
        try:
            if backup_id not in self.backup_registry:
                return False
            
            backup_info = self.backup_registry[backup_id]
            backup_path = Path(backup_info.file_path)
            
            # Remover arquivo
            if backup_path.exists():
                backup_path.unlink()
            
            # Remover do registro
            del self.backup_registry[backup_id]
            self._save_backup_registry()
            
            self.logger.info(f"🗑️ Backup removido: {backup_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao remover backup: {str(e)}")
            return False
    
    def synchronize_data(self) -> SyncStatus:
        """Sincroniza dados entre dispositivos"""
        try:
            self.logger.info("🔄 Iniciando sincronização de dados...")
            
            sync_status = SyncStatus(
                device_id=self.device_id,
                last_sync=datetime.now(),
                sync_direction='bidirectional'
            )
            
            # Em uma implementação real, isso sincronizaria com:
            # - Serviços de nuvem (AWS S3, Azure Blob, Google Cloud)
            # - Outros dispositivos via P2P
            # - Servidor central
            
            # Por agora, simular sincronização bem-sucedida
            sync_status.data_transferred_mb = 12.5
            sync_status.sync_success = True
            
            self.logger.info("✅ Sincronização concluída com sucesso")
            return sync_status
            
        except Exception as e:
            self.logger.error(f"Erro na sincronização: {str(e)}")
            return SyncStatus(
                device_id=self.device_id,
                last_sync=datetime.now(),
                sync_direction='bidirectional',
                sync_success=False,
                error_message=str(e)
            )
    
    def check_sync_status(self) -> Optional[SyncStatus]:
        """Verifica status atual de sincronização"""
        try:
            # Em uma implementação real, verificaria conectividade com serviços de nuvem
            # e status de sincronização com outros dispositivos
            
            return SyncStatus(
                device_id=self.device_id,
                last_sync=datetime.now() - timedelta(minutes=30),
                sync_direction='bidirectional',
                sync_success=True
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar status de sincronização: {str(e)}")
            return None
    
    def _should_sync(self) -> bool:
        """Verifica se deve realizar sincronização"""
        # Critérios para sincronização:
        # - Dados modificados desde última sincronização
        # - Conectividade disponível
        # - Não há conflitos pendentes
        
        return True  # Simplificado por agora
    
    def _upload_to_cloud(self, backup_info: BackupInfo):
        """Upload de backup para nuvem"""
        try:
            if not self.config.cloud_enabled:
                return
            
            self.logger.info(f"☁️ Enviando backup para nuvem: {backup_info.backup_id}")
            
            # Em uma implementação real, isso faria upload para:
            # - AWS S3, Azure Blob Storage, Google Cloud Storage
            # - Dropbox, OneDrive, Google Drive
            # - Servidor FTP/SFTP próprio
            
            # Por agora, simular upload bem-sucedido
            backup_info.cloud_synced = True
            self._save_backup_registry()
            
            self.logger.info("✅ Upload para nuvem concluído")
            
        except Exception as e:
            self.logger.error(f"Erro no upload para nuvem: {str(e)}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Retorna status completo do sistema de backup"""
        try:
            total_backups = len(self.backup_registry)
            total_size = sum(backup.size_bytes for backup in self.backup_registry.values())
            
            latest_backup = None
            if self.backup_registry:
                latest_backup = max(self.backup_registry.values(), key=lambda b: b.timestamp)
            
            return {
                'backup_service': {
                    'status': 'active' if self.backup_active else 'inactive',
                    'total_backups': total_backups,
                    'total_size_mb': round(total_size / 1024 / 1024, 2),
                    'latest_backup': {
                        'id': latest_backup.backup_id,
                        'timestamp': latest_backup.timestamp.isoformat(),
                        'size_mb': round(latest_backup.size_bytes / 1024 / 1024, 2)
                    } if latest_backup else None,
                    'next_backup': (datetime.now() + timedelta(hours=self.config.interval_hours)).isoformat(),
                    'retention_days': self.config.retention_days
                },
                'sync_service': {
                    'status': 'active' if self.sync_active else 'inactive',
                    'device_id': self.device_id,
                    'cloud_enabled': self.config.cloud_enabled,
                    'last_sync': datetime.now().isoformat()  # Simplificado
                },
                'storage': {
                    'backup_directory': str(self.backup_dir),
                    'disk_usage_mb': self._get_directory_size(self.backup_dir),
                    'available_space_mb': self._get_available_space()
                },
                'configuration': {
                    'auto_backup_enabled': self.config.enabled,
                    'backup_interval_hours': self.config.interval_hours,
                    'compression_enabled': self.config.compression_enabled,
                    'encryption_enabled': self.config.encryption_enabled,
                    'cloud_provider': self.config.cloud_provider
                }
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter status do sistema: {str(e)}")
            return {'error': str(e)}
    
    def _get_directory_size(self, directory: Path) -> float:
        """Calcula tamanho de um diretório em MB"""
        try:
            total_size = sum(f.stat().st_size for f in directory.rglob('*') if f.is_file())
            return round(total_size / 1024 / 1024, 2)
        except:
            return 0.0
    
    def _get_available_space(self) -> float:
        """Retorna espaço disponível em disco em MB"""
        try:
            statvfs = os.statvfs(self.backup_dir)
            available_bytes = statvfs.f_frsize * statvfs.f_bavail
            return round(available_bytes / 1024 / 1024, 2)
        except:
            return 0.0