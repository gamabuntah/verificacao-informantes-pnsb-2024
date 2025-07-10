"""
Serviço de Backup Automático Integrado ao Flask
==============================================

Garante que as visitas nunca sejam perdidas.
"""

import os
import sqlite3
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import threading
import time
import atexit

class BackupService:
    """Serviço de backup automático para proteger os dados das visitas."""
    
    def __init__(self, db_path='gestao_visitas/gestao_visitas.db'):
        self.db_path = db_path
        self.backup_dir = Path('gestao_visitas/backups_automaticos')
        self.backup_dir.mkdir(exist_ok=True)
        self.running = False
        self.thread = None
        
        # Configurações de backup
        self.intervalo_backup = 300  # 5 minutos
        self.max_backups = 50
        
        # Registrar para parar no shutdown
        atexit.register(self.parar)
        
    def iniciar(self):
        """Inicia o serviço de backup automático."""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._loop_backup, daemon=True)
        self.thread.start()
        
        # Criar backup inicial
        self.criar_backup_agora()
        
        print("🔒 Sistema de backup automático iniciado")
        print(f"   📁 Diretório: {self.backup_dir}")
        print(f"   ⏰ Intervalo: {self.intervalo_backup} segundos")
        
    def parar(self):
        """Para o serviço de backup."""
        if not self.running:
            return
            
        self.running = False
        if self.thread and self.thread.is_alive():
            try:
                self.thread.join(timeout=5)
            except KeyboardInterrupt:
                # Ignorar interrupções durante o encerramento
                pass
        print("🛑 Sistema de backup automático parado")
        
    def _loop_backup(self):
        """Loop principal do backup."""
        while self.running:
            try:
                time.sleep(self.intervalo_backup)
                if self.running:
                    self.criar_backup_agora()
                    self.limpar_backups_antigos()
            except Exception as e:
                print(f"❌ Erro no backup automático: {e}")
                
    def criar_backup_agora(self):
        """Cria um backup imediato."""
        if not os.path.exists(self.db_path):
            return False
            
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Backup do arquivo DB (cópia completa)
            backup_db = self.backup_dir / f"auto_backup_{timestamp}.db"
            shutil.copy2(self.db_path, backup_db)
            
            # Backup em JSON (dados estruturados)
            backup_json = self.backup_dir / f"auto_backup_{timestamp}.json"
            self._exportar_dados_criticos(backup_json)
            
            print(f"💾 Backup automático criado: {timestamp}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar backup: {e}")
            return False
            
    def _exportar_dados_criticos(self, json_path):
        """Exporta apenas os dados críticos (visitas e checklists)."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            backup_data = {
                'backup_info': {
                    'timestamp': datetime.now().isoformat(),
                    'tipo': 'backup_automatico_criticos',
                    'sistema': 'PNSB_Gestao_Visitas'
                },
                'dados': {}
            }
            
            # Exportar visitas (CRÍTICO)
            try:
                cursor.execute('SELECT * FROM visitas ORDER BY id')
                visitas = cursor.fetchall()
                
                cursor.execute('PRAGMA table_info(visitas)')
                colunas = [col[1] for col in cursor.fetchall()]
                
                backup_data['dados']['visitas'] = {
                    'estrutura': colunas,
                    'registros': [dict(zip(colunas, row)) for row in visitas],
                    'total': len(visitas)
                }
                
            except Exception as e:
                print(f"⚠️ Erro ao exportar visitas: {e}")
                backup_data['dados']['visitas'] = {'erro': str(e)}
                
            # Exportar checklists (CRÍTICO)
            try:
                cursor.execute('SELECT * FROM checklists ORDER BY id')
                checklists = cursor.fetchall()
                
                cursor.execute('PRAGMA table_info(checklists)')
                colunas = [col[1] for col in cursor.fetchall()]
                
                backup_data['dados']['checklists'] = {
                    'estrutura': colunas,
                    'registros': [dict(zip(colunas, row)) for row in checklists],
                    'total': len(checklists)
                }
                
            except Exception as e:
                print(f"⚠️ Erro ao exportar checklists: {e}")
                backup_data['dados']['checklists'] = {'erro': str(e)}
                
            conn.close()
            
            # Salvar JSON com encoding UTF-8
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, default=str, ensure_ascii=False)
                
        except Exception as e:
            print(f"❌ Erro na exportação JSON: {e}")
            
    def limpar_backups_antigos(self):
        """Remove backups antigos mantendo os mais recentes."""
        try:
            backups_db = sorted(self.backup_dir.glob("auto_backup_*.db"))
            backups_json = sorted(self.backup_dir.glob("auto_backup_*.json"))
            
            # Manter apenas os últimos N backups
            if len(backups_db) > self.max_backups:
                for backup in backups_db[:-self.max_backups]:
                    backup.unlink()
                    
            if len(backups_json) > self.max_backups:
                for backup in backups_json[:-self.max_backups]:
                    backup.unlink()
                    
        except Exception as e:
            print(f"⚠️ Erro na limpeza de backups: {e}")
            
    def obter_estatisticas(self):
        """Retorna estatísticas dos backups."""
        try:
            backups_db = list(self.backup_dir.glob("auto_backup_*.db"))
            backups_json = list(self.backup_dir.glob("auto_backup_*.json"))
            
            if backups_db:
                ultimo_backup = max(backups_db, key=lambda p: p.stat().st_mtime)
                ultimo_backup_time = datetime.fromtimestamp(ultimo_backup.stat().st_mtime)
            else:
                ultimo_backup_time = None
                
            return {
                'total_backups_db': len(backups_db),
                'total_backups_json': len(backups_json),
                'ultimo_backup': ultimo_backup_time.isoformat() if ultimo_backup_time else None,
                'ultimo_backup_formatado': ultimo_backup_time.strftime('%d/%m/%Y %H:%M') if ultimo_backup_time else 'Nunca',
                'diretorio': str(self.backup_dir),
                'ativo': self.running
            }
            
        except Exception as e:
            return {'erro': str(e)}
            
    def backup_emergencial(self):
        """Cria um backup de emergência com timestamp especial."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Backup de emergência
            backup_emergencial = self.backup_dir / f"EMERGENCIA_backup_{timestamp}.db"
            shutil.copy2(self.db_path, backup_emergencial)
            
            # JSON de emergência
            json_emergencial = self.backup_dir / f"EMERGENCIA_backup_{timestamp}.json"
            self._exportar_dados_criticos(json_emergencial)
            
            print(f"🚨 BACKUP DE EMERGÊNCIA CRIADO: {timestamp}")
            return True
            
        except Exception as e:
            print(f"❌ Erro no backup de emergência: {e}")
            return False
            
    def restaurar_ultimo_backup(self):
        """Restaura o último backup disponível."""
        try:
            backups_db = sorted(self.backup_dir.glob("auto_backup_*.db"))
            
            if not backups_db:
                print("❌ Nenhum backup disponível para restauração")
                return False
                
            ultimo_backup = backups_db[-1]
            
            # Fazer backup do estado atual antes de restaurar
            backup_antes = f"{self.db_path}.antes_restauracao_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, backup_antes)
                
            # Restaurar
            shutil.copy2(ultimo_backup, self.db_path)
            
            print(f"✅ Banco restaurado do backup: {ultimo_backup.name}")
            print(f"📦 Estado anterior salvo em: {backup_antes}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na restauração: {e}")
            return False

# Instância global do serviço
backup_service = BackupService()

def inicializar_backup_service():
    """Inicializa o serviço de backup (chamado pelo app.py)."""
    backup_service.iniciar()
    
def obter_backup_service():
    """Retorna a instância do serviço de backup."""
    return backup_service