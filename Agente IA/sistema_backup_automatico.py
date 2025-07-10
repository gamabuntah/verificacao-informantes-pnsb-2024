#!/usr/bin/env python3
"""
SISTEMA DE BACKUP AUTOMÁTICO - NUNCA PERDER VISITAS
==================================================

Sistema robusto para garantir que as visitas nunca sejam perdidas.
"""

import os
import sqlite3
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import threading
import time

class BackupAutomatico:
    def __init__(self, db_path='gestao_visitas/gestao_visitas.db'):
        self.db_path = db_path
        self.backup_dir = Path('gestao_visitas/backups_automaticos')
        self.backup_dir.mkdir(exist_ok=True)
        self.running = False
        self.thread = None
        
        # Configurações
        self.intervalo_backup = 300  # 5 minutos
        self.max_backups = 50  # Manter 50 backups
        
    def iniciar_backup_automatico(self):
        """Inicia o sistema de backup automático."""
        if self.running:
            print("⚠️ Backup automático já está rodando")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._executar_backup_loop, daemon=True)
        self.thread.start()
        print("🔄 Sistema de backup automático iniciado")
        print(f"   Intervalo: {self.intervalo_backup} segundos")
        print(f"   Diretório: {self.backup_dir}")
        
    def parar_backup_automatico(self):
        """Para o sistema de backup automático."""
        self.running = False
        if self.thread:
            self.thread.join()
        print("🛑 Sistema de backup automático parado")
        
    def _executar_backup_loop(self):
        """Loop principal do backup automático."""
        while self.running:
            try:
                self.criar_backup()
                self.limpar_backups_antigos()
            except Exception as e:
                print(f"❌ Erro no backup automático: {e}")
            
            # Aguardar próximo backup
            for _ in range(self.intervalo_backup):
                if not self.running:
                    break
                time.sleep(1)
                
    def criar_backup(self):
        """Cria um backup completo do banco de dados."""
        if not os.path.exists(self.db_path):
            print("⚠️ Banco de dados não encontrado para backup")
            return False
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Backup do arquivo DB
        backup_db = self.backup_dir / f"backup_db_{timestamp}.db"
        shutil.copy2(self.db_path, backup_db)
        
        # Backup em JSON (mais legível)
        backup_json = self.backup_dir / f"backup_json_{timestamp}.json"
        self._exportar_para_json(backup_json)
        
        print(f"✅ Backup criado: {timestamp}")
        return True
        
    def _exportar_para_json(self, json_path):
        """Exporta dados do banco para JSON."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'tabelas': {}
        }
        
        # Exportar tabela visitas
        try:
            cursor.execute('SELECT * FROM visitas')
            visitas = cursor.fetchall()
            
            cursor.execute('PRAGMA table_info(visitas)')
            colunas = [col[1] for col in cursor.fetchall()]
            
            backup_data['tabelas']['visitas'] = {
                'colunas': colunas,
                'dados': [dict(zip(colunas, row)) for row in visitas],
                'count': len(visitas)
            }
            
        except Exception as e:
            print(f"⚠️ Erro ao exportar visitas: {e}")
            
        # Exportar tabela checklists
        try:
            cursor.execute('SELECT * FROM checklists')
            checklists = cursor.fetchall()
            
            cursor.execute('PRAGMA table_info(checklists)')
            colunas = [col[1] for col in cursor.fetchall()]
            
            backup_data['tabelas']['checklists'] = {
                'colunas': colunas,
                'dados': [dict(zip(colunas, row)) for row in checklists],
                'count': len(checklists)
            }
            
        except Exception as e:
            print(f"⚠️ Erro ao exportar checklists: {e}")
            
        conn.close()
        
        # Salvar JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, default=str, ensure_ascii=False)
            
    def limpar_backups_antigos(self):
        """Remove backups antigos mantendo apenas os mais recentes."""
        backups_db = sorted(self.backup_dir.glob("backup_db_*.db"))
        backups_json = sorted(self.backup_dir.glob("backup_json_*.json"))
        
        # Remover backups DB antigos
        if len(backups_db) > self.max_backups:
            for backup in backups_db[:-self.max_backups]:
                backup.unlink()
                
        # Remover backups JSON antigos
        if len(backups_json) > self.max_backups:
            for backup in backups_json[:-self.max_backups]:
                backup.unlink()
                
    def listar_backups(self):
        """Lista todos os backups disponíveis."""
        backups_db = sorted(self.backup_dir.glob("backup_db_*.db"))
        backups_json = sorted(self.backup_dir.glob("backup_json_*.json"))
        
        print(f"📦 BACKUPS DISPONÍVEIS ({len(backups_db)} DB, {len(backups_json)} JSON):")
        
        for backup in backups_db[-10:]:  # Últimos 10
            stat = backup.stat()
            size = stat.st_size / 1024  # KB
            modified = datetime.fromtimestamp(stat.st_mtime)
            print(f"   DB:   {backup.name} ({size:.1f}KB) - {modified.strftime('%d/%m/%Y %H:%M')}")
            
        for backup in backups_json[-10:]:  # Últimos 10
            stat = backup.stat()
            size = stat.st_size / 1024  # KB
            modified = datetime.fromtimestamp(stat.st_mtime)
            print(f"   JSON: {backup.name} ({size:.1f}KB) - {modified.strftime('%d/%m/%Y %H:%M')}")
            
    def restaurar_backup(self, backup_file):
        """Restaura um backup específico."""
        backup_path = self.backup_dir / backup_file
        
        if not backup_path.exists():
            print(f"❌ Backup não encontrado: {backup_file}")
            return False
            
        if backup_file.endswith('.db'):
            return self._restaurar_db(backup_path)
        elif backup_file.endswith('.json'):
            return self._restaurar_json(backup_path)
        else:
            print(f"❌ Formato de backup não suportado: {backup_file}")
            return False
            
    def _restaurar_db(self, backup_path):
        """Restaura backup do arquivo DB."""
        try:
            # Fazer backup do atual antes de restaurar
            if os.path.exists(self.db_path):
                backup_atual = f"{self.db_path}.backup_antes_restauracao_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(self.db_path, backup_atual)
                print(f"📦 Backup do banco atual salvo: {backup_atual}")
            
            # Restaurar backup
            shutil.copy2(backup_path, self.db_path)
            print(f"✅ Banco restaurado de: {backup_path.name}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao restaurar DB: {e}")
            return False
            
    def _restaurar_json(self, backup_path):
        """Restaura backup do arquivo JSON."""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
                
            print(f"📄 Restaurando de JSON: {backup_path.name}")
            print(f"   Timestamp: {backup_data.get('timestamp')}")
            
            # Conectar ao banco
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Restaurar visitas
            if 'visitas' in backup_data['tabelas']:
                visitas_data = backup_data['tabelas']['visitas']
                print(f"   Restaurando {visitas_data['count']} visitas...")
                
                # Limpar tabela atual
                cursor.execute('DELETE FROM visitas')
                
                # Inserir dados do backup
                for visita in visitas_data['dados']:
                    colunas = list(visita.keys())
                    valores = list(visita.values())
                    placeholders = ', '.join(['?' for _ in valores])
                    cols_str = ', '.join(colunas)
                    
                    query = f'INSERT INTO visitas ({cols_str}) VALUES ({placeholders})'
                    cursor.execute(query, valores)
                    
            # Restaurar checklists
            if 'checklists' in backup_data['tabelas']:
                checklists_data = backup_data['tabelas']['checklists']
                print(f"   Restaurando {checklists_data['count']} checklists...")
                
                # Limpar tabela atual
                cursor.execute('DELETE FROM checklists')
                
                # Inserir dados do backup
                for checklist in checklists_data['dados']:
                    colunas = list(checklist.keys())
                    valores = list(checklist.values())
                    placeholders = ', '.join(['?' for _ in valores])
                    cols_str = ', '.join(colunas)
                    
                    query = f'INSERT INTO checklists ({cols_str}) VALUES ({placeholders})'
                    cursor.execute(query, valores)
            
            conn.commit()
            conn.close()
            
            print(f"✅ Dados restaurados com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao restaurar JSON: {e}")
            return False
            
    def verificar_integridade(self):
        """Verifica a integridade dos dados."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar visitas
            cursor.execute('SELECT COUNT(*) FROM visitas')
            count_visitas = cursor.fetchone()[0]
            
            # Verificar checklists
            cursor.execute('SELECT COUNT(*) FROM checklists')
            count_checklists = cursor.fetchone()[0]
            
            # Verificar visitas sem checklist
            cursor.execute('''
                SELECT COUNT(*) FROM visitas v 
                LEFT JOIN checklists c ON v.id = c.visita_id 
                WHERE c.id IS NULL
            ''')
            visitas_sem_checklist = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"🔍 VERIFICAÇÃO DE INTEGRIDADE:")
            print(f"   Visitas: {count_visitas}")
            print(f"   Checklists: {count_checklists}")
            print(f"   Visitas sem checklist: {visitas_sem_checklist}")
            
            if visitas_sem_checklist > 0:
                print(f"⚠️ {visitas_sem_checklist} visitas sem checklist - pode precisar de correção")
                
            return {
                'visitas': count_visitas,
                'checklists': count_checklists,
                'visitas_sem_checklist': visitas_sem_checklist
            }
            
        except Exception as e:
            print(f"❌ Erro na verificação: {e}")
            return None

def main():
    print("=" * 60)
    print("🔒 SISTEMA DE BACKUP AUTOMÁTICO - NUNCA PERDER VISITAS")
    print("=" * 60)
    
    backup_system = BackupAutomatico()
    
    while True:
        print("\n📋 OPÇÕES:")
        print("1. Iniciar backup automático")
        print("2. Criar backup manual")
        print("3. Listar backups")
        print("4. Restaurar backup")
        print("5. Verificar integridade")
        print("6. Parar backup automático")
        print("0. Sair")
        
        try:
            opcao = input("\nEscolha uma opção: ").strip()
            
            if opcao == '1':
                backup_system.iniciar_backup_automatico()
                
            elif opcao == '2':
                if backup_system.criar_backup():
                    print("✅ Backup manual criado com sucesso")
                    
            elif opcao == '3':
                backup_system.listar_backups()
                
            elif opcao == '4':
                backup_system.listar_backups()
                backup_file = input("\nNome do arquivo de backup: ").strip()
                if backup_file:
                    backup_system.restaurar_backup(backup_file)
                    
            elif opcao == '5':
                backup_system.verificar_integridade()
                
            elif opcao == '6':
                backup_system.parar_backup_automatico()
                
            elif opcao == '0':
                backup_system.parar_backup_automatico()
                print("👋 Sistema de backup finalizado")
                break
                
            else:
                print("❌ Opção inválida")
                
        except KeyboardInterrupt:
            backup_system.parar_backup_automatico()
            print("\n👋 Sistema de backup finalizado")
            break
        except EOFError:
            backup_system.parar_backup_automatico()
            print("\n👋 Sistema de backup finalizado")
            break

if __name__ == "__main__":
    main()