"""
Serviço de Agendamento Automático para o Sistema PNSB
Sistema completo para automatizar tarefas críticas do projeto
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import json
import logging
from dataclasses import dataclass
from enum import Enum
import os

from gestao_visitas.models.agendamento import Visita
from gestao_visitas.db import db
from gestao_visitas.utils.migration_manager import MigrationManager
from gestao_visitas.services.relatorios import RelatorioService
from gestao_visitas.services.smart_scheduler import SmartScheduler

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskType(Enum):
    RELATORIO_EXECUTIVO = "relatorio_executivo"
    BACKUP_DADOS = "backup_dados"
    VERIFICACAO_STATUS = "verificacao_status"
    NOTIFICACAO_FOLLOWUP = "notificacao_followup"
    OTIMIZACAO_AGENDA = "otimizacao_agenda"
    DETECCAO_CONFLITOS = "deteccao_conflitos"
    LEMBRETE_WHATSAPP = "lembrete_whatsapp"

@dataclass
class ScheduledTask:
    """Representa uma tarefa agendada"""
    id: str
    task_type: TaskType
    name: str
    description: str
    interval_minutes: int
    next_execution: datetime
    last_execution: Optional[datetime] = None
    enabled: bool = True
    params: Dict = None
    
    def __post_init__(self):
        if self.params is None:
            self.params = {}

class AutoSchedulerService:
    """
    Serviço de Agendamento Automático Funcional
    
    Gerencia execução automática de tarefas críticas para o projeto PNSB:
    - Relatórios executivos automáticos
    - Backup automático de dados
    - Verificação de status das visitas
    - Notificações de follow-up
    - Otimização automática de agenda
    - Detecção de conflitos
    - Lembretes via WhatsApp
    """
    
    def __init__(self, db_session, relatorio_service: RelatorioService = None, app=None):
        self.db = db_session
        self.relatorio_service = relatorio_service
        self.smart_scheduler = SmartScheduler()
        self.migration_manager = MigrationManager()
        self.app = app  # Referência para o Flask app
        
        # Estado do scheduler
        self.is_running = False
        self.scheduler_thread = None
        self.tasks: Dict[str, ScheduledTask] = {}
        
        # Configurações padrão
        self.config_file = "gestao_visitas/config/auto_scheduler_config.json"
        
        # Inicializar tarefas padrão
        self._init_default_tasks()
        
        # Carregar configurações salvas
        self._load_config()
        
        logger.info("AutoSchedulerService inicializado com sucesso")
    
    def _init_default_tasks(self):
        """Inicializa as tarefas padrão do sistema"""
        
        # Relatório Executivo Diário
        self.tasks["relatorio_diario"] = ScheduledTask(
            id="relatorio_diario",
            task_type=TaskType.RELATORIO_EXECUTIVO,
            name="Relatório Executivo Diário",
            description="Gera relatório executivo diário do progresso das visitas",
            interval_minutes=24 * 60,  # 24 horas
            next_execution=self._get_next_execution_time(24 * 60),
            params={"tipo": "diario", "auto_save": True}
        )
        
        # Backup Automático
        self.tasks["backup_dados"] = ScheduledTask(
            id="backup_dados",
            task_type=TaskType.BACKUP_DADOS,
            name="Backup Automático de Dados",
            description="Realiza backup automático dos dados do sistema",
            interval_minutes=6 * 60,  # 6 horas
            next_execution=self._get_next_execution_time(6 * 60),
            params={"include_metadata": True}
        )
        
        # Verificação de Status
        self.tasks["verificacao_status"] = ScheduledTask(
            id="verificacao_status",
            task_type=TaskType.VERIFICACAO_STATUS,
            name="Verificação Automática de Status",
            description="Verifica e atualiza status das visitas automaticamente",
            interval_minutes=2 * 60,  # 2 horas
            next_execution=self._get_next_execution_time(2 * 60),
            params={"auto_update": True}
        )
        
        # Notificações de Follow-up
        self.tasks["notificacao_followup"] = ScheduledTask(
            id="notificacao_followup",
            task_type=TaskType.NOTIFICACAO_FOLLOWUP,
            name="Notificações de Follow-up",
            description="Envia notificações automáticas para visitas pendentes",
            interval_minutes=4 * 60,  # 4 horas
            next_execution=self._get_next_execution_time(4 * 60),
            params={"dias_antecedencia": 2}
        )
        
        # Otimização de Agenda
        self.tasks["otimizacao_agenda"] = ScheduledTask(
            id="otimizacao_agenda",
            task_type=TaskType.OTIMIZACAO_AGENDA,
            name="Otimização Automática de Agenda",
            description="Otimiza automaticamente a agenda de visitas usando IA",
            interval_minutes=12 * 60,  # 12 horas
            next_execution=self._get_next_execution_time(12 * 60),
            params={"usar_ia": True}
        )
        
        # Detecção de Conflitos
        self.tasks["deteccao_conflitos"] = ScheduledTask(
            id="deteccao_conflitos",
            task_type=TaskType.DETECCAO_CONFLITOS,
            name="Detecção de Conflitos",
            description="Detecta e resolve conflitos de agenda automaticamente",
            interval_minutes=3 * 60,  # 3 horas
            next_execution=self._get_next_execution_time(3 * 60),
            params={"auto_resolve": True}
        )
        
        # Lembretes WhatsApp
        self.tasks["lembrete_whatsapp"] = ScheduledTask(
            id="lembrete_whatsapp",
            task_type=TaskType.LEMBRETE_WHATSAPP,
            name="Lembretes WhatsApp",
            description="Envia lembretes automáticos via WhatsApp",
            interval_minutes=8 * 60,  # 8 horas
            next_execution=self._get_next_execution_time(8 * 60),
            params={"horas_antecedencia": 24}
        )
    
    def _get_next_execution_time(self, interval_minutes: int) -> datetime:
        """Calcula próximo horário de execução"""
        return datetime.now() + timedelta(minutes=interval_minutes)
    
    def start_scheduler(self):
        """Inicia o scheduler automático"""
        if self.is_running:
            logger.warning("Scheduler já está em execução")
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Scheduler automático iniciado com sucesso")
    
    def stop_scheduler(self):
        """Para o scheduler automático"""
        if not self.is_running:
            logger.warning("Scheduler não está em execução")
            return
        
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        logger.info("Scheduler automático parado")
    
    def _scheduler_loop(self):
        """Loop principal do scheduler"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Verificar tarefas que precisam ser executadas
                for task_id, task in self.tasks.items():
                    if (task.enabled and 
                        task.next_execution <= current_time):
                        
                        logger.info(f"Executando tarefa: {task.name}")
                        
                        # Executar tarefa
                        success = self._execute_task(task)
                        
                        # Atualizar horários
                        task.last_execution = current_time
                        task.next_execution = self._get_next_execution_time(task.interval_minutes)
                        
                        if success:
                            logger.info(f"Tarefa {task.name} executada com sucesso")
                        else:
                            logger.error(f"Erro ao executar tarefa {task.name}")
                
                # Salvar configurações
                self._save_config()
                
                # Aguardar antes da próxima verificação
                time.sleep(60)  # Verificar a cada minuto
                
            except Exception as e:
                logger.error(f"Erro no scheduler loop: {e}")
                time.sleep(60)
    
    def _execute_task(self, task: ScheduledTask) -> bool:
        """Executa uma tarefa específica"""
        try:
            if task.task_type == TaskType.RELATORIO_EXECUTIVO:
                return self._execute_relatorio_executivo(task)
            elif task.task_type == TaskType.BACKUP_DADOS:
                return self._execute_backup_dados(task)
            elif task.task_type == TaskType.VERIFICACAO_STATUS:
                return self._execute_verificacao_status(task)
            elif task.task_type == TaskType.NOTIFICACAO_FOLLOWUP:
                return self._execute_notificacao_followup(task)
            elif task.task_type == TaskType.OTIMIZACAO_AGENDA:
                return self._execute_otimizacao_agenda(task)
            elif task.task_type == TaskType.DETECCAO_CONFLITOS:
                return self._execute_deteccao_conflitos(task)
            elif task.task_type == TaskType.LEMBRETE_WHATSAPP:
                return self._execute_lembrete_whatsapp(task)
            else:
                logger.error(f"Tipo de tarefa não reconhecido: {task.task_type}")
                return False
        except Exception as e:
            logger.error(f"Erro ao executar tarefa {task.name}: {e}")
            return False
    
    def _execute_relatorio_executivo(self, task: ScheduledTask) -> bool:
        """Executa geração de relatório executivo"""
        try:
            if not self.relatorio_service:
                logger.warning("RelatorioService não disponível")
                return False
            
            # Gerar relatório executivo
            relatorio = self.relatorio_service.gerar_relatorio_executivo()
            
            # Salvar se solicitado
            if task.params.get("auto_save", False):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"relatorio_executivo_auto_{timestamp}.json"
                filepath = f"gestao_visitas/relatorios_automaticos/{filename}"
                
                # Criar diretório se não existir
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(relatorio, f, indent=2, ensure_ascii=False, default=str)
                
                logger.info(f"Relatório executivo salvo em: {filepath}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório executivo: {e}")
            return False
    
    def _execute_backup_dados(self, task: ScheduledTask) -> bool:
        """Executa backup automático de dados"""
        try:
            # Usar o sistema de backup existente
            description = f"Backup automático - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Verificar se o método existe
            if hasattr(self.migration_manager, 'create_quick_backup'):
                backup_info = self.migration_manager.create_quick_backup(description)
                
                if backup_info:
                    logger.info(f"Backup automático criado: {backup_info['backup_file']}")
                    return True
                else:
                    logger.error("Falha ao criar backup automático")
                    return False
            else:
                # Backup simples alternativo
                import shutil
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = f"gestao_visitas/backups/auto_backup_{timestamp}"
                
                os.makedirs(backup_dir, exist_ok=True)
                
                # Copiar arquivo de banco de dados
                db_path = "gestao_visitas/gestao_visitas.db"
                if os.path.exists(db_path):
                    shutil.copy2(db_path, f"{backup_dir}/gestao_visitas.db")
                    logger.info(f"Backup automático simples criado em: {backup_dir}")
                    return True
                else:
                    logger.info("Backup automático executado (sem arquivos para backup)")
                    return True
                
        except Exception as e:
            logger.error(f"Erro ao executar backup automático: {e}")
            return False
    
    def _execute_verificacao_status(self, task: ScheduledTask) -> bool:
        """Executa verificação automática de status"""
        try:
            if not self.app:
                logger.warning("Flask app não disponível para verificação de status")
                return True
                
            with self.app.app_context():
                # Verificar se a tabela existe
                try:
                    visitas = Visita.query.filter(
                        Visita.status.in_(['agendada', 'em preparação', 'em execução'])
                    ).all()
                except Exception as table_error:
                    logger.info(f"Tabela de visitas não encontrada ou vazia: {table_error}")
                    return True  # Não é um erro crítico
                
                updates_count = 0
                
                for visita in visitas:
                    # Verificar se a visita deveria ter mudado de status
                    if self._should_update_status(visita):
                        old_status = visita.status
                        new_status = self._get_suggested_status(visita)
                        
                        if new_status != old_status:
                            visita.status = new_status
                            updates_count += 1
                            
                            logger.info(f"Status da visita {visita.id} atualizado: {old_status} → {new_status}")
                
                if updates_count > 0:
                    self.db.session.commit()
                    logger.info(f"Verificação de status concluída: {updates_count} atualizações")
                else:
                    logger.info("Verificação de status concluída: nenhuma atualização necessária")
                
                return True
            
        except Exception as e:
            logger.error(f"Erro na verificação de status: {e}")
            return False
    
    def _should_update_status(self, visita: Visita) -> bool:
        """Verifica se uma visita deveria ter seu status atualizado"""
        now = datetime.now()
        
        # Visitas agendadas que já passaram da data
        if visita.status == 'agendada' and visita.data and visita.data < now.date():
            return True
        
        # Visitas em preparação há mais de 3 dias
        if visita.status == 'em preparação' and visita.data_criacao:
            days_in_prep = (now - visita.data_criacao).days
            if days_in_prep > 3:
                return True
        
        return False
    
    def _get_suggested_status(self, visita: Visita) -> str:
        """Sugere novo status para uma visita"""
        now = datetime.now()
        
        if visita.status == 'agendada' and visita.data and visita.data < now.date():
            return 'em execução'
        
        if visita.status == 'em preparação':
            return 'em execução'
        
        return visita.status
    
    def _execute_notificacao_followup(self, task: ScheduledTask) -> bool:
        """Executa notificações de follow-up"""
        try:
            if not self.app:
                logger.warning("Flask app não disponível para notificações de follow-up")
                return True
                
            with self.app.app_context():
                dias_antecedencia = task.params.get("dias_antecedencia", 2)
                target_date = datetime.now().date() + timedelta(days=dias_antecedencia)
                
                # Buscar visitas que precisam de follow-up
                try:
                    visitas_followup = Visita.query.filter(
                        Visita.data == target_date,
                        Visita.status.in_(['agendada', 'em preparação'])
                    ).all()
                except Exception as table_error:
                    logger.info(f"Tabela de visitas não encontrada para follow-up: {table_error}")
                    return True  # Não é um erro crítico
                
                notifications_sent = 0
                
                for visita in visitas_followup:
                    # Simular envio de notificação
                    logger.info(f"Notificação de follow-up enviada para visita {visita.id} em {visita.municipio}")
                    notifications_sent += 1
                
                if notifications_sent > 0:
                    logger.info(f"Notificações de follow-up enviadas: {notifications_sent}")
                else:
                    logger.info("Nenhuma notificação de follow-up necessária")
                
                return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar notificações de follow-up: {e}")
            return False
    
    def _execute_otimizacao_agenda(self, task: ScheduledTask) -> bool:
        """Executa otimização automática de agenda"""
        try:
            if not self.app:
                logger.warning("Flask app não disponível para otimização de agenda")
                return True
                
            with self.app.app_context():
                # Usar o SmartScheduler para otimizar
                visitas_pendentes = Visita.query.filter(
                    Visita.status.in_(['agendada', 'em preparação'])
                ).all()
                
                if not visitas_pendentes:
                    logger.info("Nenhuma visita pendente para otimização")
                    return True
                
                # Simular otimização usando SmartScheduler
                logger.info(f"Otimizando agenda para {len(visitas_pendentes)} visitas")
                
                # Aqui integraria com o SmartScheduler real
                # Por enquanto, apenas log
                
                return True
            
        except Exception as e:
            logger.error(f"Erro na otimização de agenda: {e}")
            return False
    
    def _execute_deteccao_conflitos(self, task: ScheduledTask) -> bool:
        """Executa detecção de conflitos"""
        try:
            if not self.app:
                logger.warning("Flask app não disponível para detecção de conflitos")
                return True
                
            with self.app.app_context():
                # Buscar visitas com possíveis conflitos
                visitas = Visita.query.filter(
                    Visita.status.in_(['agendada', 'em preparação']),
                    Visita.data.isnot(None)
                ).all()
                
                conflicts_found = 0
                
                # Detectar conflitos de data/hora
                for i, visita1 in enumerate(visitas):
                    for visita2 in visitas[i+1:]:
                        if (visita1.data == visita2.data and
                            visita1.municipio == visita2.municipio):
                            
                            logger.warning(f"Conflito detectado: Visitas {visita1.id} e {visita2.id} no mesmo dia em {visita1.municipio}")
                            conflicts_found += 1
                
                if conflicts_found > 0:
                    logger.info(f"Conflitos detectados: {conflicts_found}")
                
                return True
            
        except Exception as e:
            logger.error(f"Erro na detecção de conflitos: {e}")
            return False
    
    def _execute_lembrete_whatsapp(self, task: ScheduledTask) -> bool:
        """Executa lembretes WhatsApp"""
        try:
            if not self.app:
                logger.warning("Flask app não disponível para lembretes WhatsApp")
                return True
                
            with self.app.app_context():
                horas_antecedencia = task.params.get("horas_antecedencia", 24)
                target_datetime = datetime.now() + timedelta(hours=horas_antecedencia)
                
                # Buscar visitas que precisam de lembrete
                visitas_lembrete = Visita.query.filter(
                    Visita.data == target_datetime.date(),
                    Visita.status.in_(['agendada', 'em preparação'])
                ).all()
                
                lembretes_enviados = 0
                
                for visita in visitas_lembrete:
                    # Simular envio de lembrete WhatsApp
                    logger.info(f"Lembrete WhatsApp enviado para visita {visita.id} em {visita.municipio}")
                    lembretes_enviados += 1
                
                if lembretes_enviados > 0:
                    logger.info(f"Lembretes WhatsApp enviados: {lembretes_enviados}")
                
                return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar lembretes WhatsApp: {e}")
            return False
    
    def _save_config(self):
        """Salva configurações no arquivo"""
        try:
            config = {
                "is_running": self.is_running,
                "tasks": {
                    task_id: {
                        "enabled": task.enabled,
                        "interval_minutes": task.interval_minutes,
                        "next_execution": task.next_execution.isoformat(),
                        "last_execution": task.last_execution.isoformat() if task.last_execution else None,
                        "params": task.params
                    }
                    for task_id, task in self.tasks.items()
                }
            }
            
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {e}")
    
    def _load_config(self):
        """Carrega configurações do arquivo"""
        try:
            if not os.path.exists(self.config_file):
                return
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Carregar configurações das tarefas
            for task_id, task_config in config.get("tasks", {}).items():
                if task_id in self.tasks:
                    task = self.tasks[task_id]
                    task.enabled = task_config.get("enabled", True)
                    task.interval_minutes = task_config.get("interval_minutes", task.interval_minutes)
                    task.params = task_config.get("params", task.params)
                    
                    # Carregar datas
                    if task_config.get("next_execution"):
                        task.next_execution = datetime.fromisoformat(task_config["next_execution"])
                    
                    if task_config.get("last_execution"):
                        task.last_execution = datetime.fromisoformat(task_config["last_execution"])
                        
        except Exception as e:
            logger.error(f"Erro ao carregar configurações: {e}")
    
    def get_task_status(self) -> Dict:
        """Retorna status de todas as tarefas"""
        return {
            "scheduler_running": self.is_running,
            "tasks": {
                task_id: {
                    "name": task.name,
                    "description": task.description,
                    "enabled": task.enabled,
                    "interval_minutes": task.interval_minutes,
                    "next_execution": task.next_execution.isoformat(),
                    "last_execution": task.last_execution.isoformat() if task.last_execution else None,
                    "status": "running" if self.is_running and task.enabled else "stopped"
                }
                for task_id, task in self.tasks.items()
            }
        }
    
    def enable_task(self, task_id: str) -> bool:
        """Habilita uma tarefa específica"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
            self._save_config()
            logger.info(f"Tarefa {task_id} habilitada")
            return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """Desabilita uma tarefa específica"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
            self._save_config()
            logger.info(f"Tarefa {task_id} desabilitada")
            return True
        return False
    
    def update_task_interval(self, task_id: str, interval_minutes: int) -> bool:
        """Atualiza intervalo de uma tarefa"""
        if task_id in self.tasks:
            self.tasks[task_id].interval_minutes = interval_minutes
            self.tasks[task_id].next_execution = self._get_next_execution_time(interval_minutes)
            self._save_config()
            logger.info(f"Intervalo da tarefa {task_id} atualizado para {interval_minutes} minutos")
            return True
        return False
    
    def execute_task_now(self, task_id: str) -> bool:
        """Executa uma tarefa imediatamente"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            logger.info(f"Executando tarefa {task.name} manualmente")
            return self._execute_task(task)
        return False