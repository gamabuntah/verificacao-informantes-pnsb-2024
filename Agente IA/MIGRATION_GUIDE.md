# 🔧 Guia de Migração e Backup - Sistema PNSB

Este documento explica como proteger os dados durante mudanças de schema e funcionalidades.

## 📋 Visão Geral

O sistema agora possui proteção completa contra perda de dados durante:
- Alterações de campos (renomeação, tipo, etc.)
- Adição/remoção de colunas
- Mudanças na estrutura do banco
- Atualizações de código

## 🛠️ Ferramentas Disponíveis

### 1. Sistema de Migração Automático
```python
from gestao_visitas.utils.migration_manager import MigrationManager

manager = MigrationManager()
```

### 2. Scripts de Migração
- `migrar_banco_v2.py` - Migração de schema com preservação de dados
- `limpar_dados.py` - Limpeza segura de dados
- `migration_manager.py` - Sistema completo de backup/restore

## 📦 Tipos de Backup

### Backup Físico (.db)
- Cópia exata do arquivo do banco
- Restauração instantânea
- Inclui estrutura e dados

### Backup Lógico (.json)
- Exportação de dados em formato legível
- Compatível entre versões diferentes
- Útil para migração de schema

## 🔄 Processo de Mudanças Seguras

### Antes de Fazer Alterações

1. **Criar Backup**
```bash
cd "Agente IA"
python3 -c "
from gestao_visitas.utils.migration_manager import create_quick_backup
create_quick_backup('Antes de alteração X')
"
```

2. **Verificar Estado Atual**
```bash
python3 -c "
from gestao_visitas.utils.migration_manager import list_available_backups
list_available_backups()
"
```

### Durante as Alterações

1. **Modificar Modelos** (models/)
2. **Atualizar API** (app.py)
3. **Ajustar Frontend** (templates/, static/)

### Após as Alterações

1. **Testar Sistema**
2. **Validar Migração**
3. **Criar Backup da Nova Versão**

## 🚨 Recuperação de Emergência

### Se Algo Der Errado

1. **Parar o Servidor**
```bash
pkill -f "python.*app.py"
```

2. **Restaurar Backup**
```python
from gestao_visitas.utils.migration_manager import MigrationManager

manager = MigrationManager()
backups = manager.list_backups()
print("Backups disponíveis:", [b['backup_file'] for b in backups])

# Restaurar o mais recente
manager.restore_backup(backups[0]['backup_file'])
```

3. **Reiniciar Servidor**
```bash
python3 app.py
```

## 📋 Checklist para Mudanças

### ✅ Antes de Alterar Campos/Tabelas

- [ ] Criar backup com descrição clara
- [ ] Documentar a mudança desejada
- [ ] Verificar dependências no código
- [ ] Planejar migração de dados

### ✅ Durante a Alteração

- [ ] Atualizar modelo SQLAlchemy
- [ ] Modificar endpoints da API
- [ ] Ajustar validações
- [ ] Atualizar frontend/formulários

### ✅ Após a Alteração

- [ ] Testar criação de novos registros
- [ ] Verificar exibição de dados
- [ ] Validar APIs
- [ ] Criar backup da nova versão

## 🔧 Comandos Úteis

### Criar Backup Rápido
```bash
python3 -c "
from gestao_visitas.utils.migration_manager import create_quick_backup
create_quick_backup('Descrição da mudança')
"
```

### Listar Backups
```bash
python3 -c "
from gestao_visitas.utils.migration_manager import list_available_backups
list_available_backups()
"
```

### Exportar Dados para JSON
```bash
python3 -c "
from gestao_visitas.utils.migration_manager import MigrationManager
manager = MigrationManager()
manager.export_data_to_json()
"
```

### Verificar Schema Atual
```bash
python3 -c "
from gestao_visitas.utils.migration_manager import MigrationManager
import json
manager = MigrationManager()
schema = manager._get_schema_info()
print(json.dumps(schema, indent=2))
"
```

## 📁 Estrutura de Backups

```
gestao_visitas/backups/
├── backup_YYYYMMDD_HHMMSS.db      # Backup físico
├── backup_YYYYMMDD_HHMMSS.json    # Metadados
├── data_export_YYYYMMDD_HHMMSS.json  # Backup lógico
└── ...
```

## 🎯 Exemplos de Uso

### Exemplo 1: Renomear Campo
```python
# 1. Backup
create_quick_backup("Renomear campo 'local' para 'endereco'")

# 2. Alterar modelo
# Em models/agendamento.py:
# local = Column(...) → endereco = Column(...)

# 3. Atualizar API
# Em app.py:
# data['local'] → data['endereco']

# 4. Migração de dados (se necessário)
# Script personalizado para converter dados existentes
```

### Exemplo 2: Adicionar Nova Coluna
```python
# 1. Backup
create_quick_backup("Adicionar campo 'prioridade'")

# 2. Alterar modelo
# prioridade = Column(String(10), default='normal')

# 3. O SQLAlchemy criará a coluna automaticamente
# 4. Backup da nova versão
create_quick_backup("Campo 'prioridade' adicionado")
```

## ⚠️ Avisos Importantes

1. **Sempre fazer backup antes de mudanças**
2. **Testar em ambiente local primeiro**
3. **Documentar cada alteração**
4. **Manter histórico de backups**
5. **Verificar integridade após migração**

## 🔗 Arquivos Relacionados

- `/gestao_visitas/utils/migration_manager.py` - Sistema principal
- `/migrar_banco_v2.py` - Script de migração
- `/limpar_dados.py` - Script de limpeza
- `/CLAUDE.md` - Instruções do projeto

---

**💡 Lembre-se**: Este sistema garante que nunca percamos dados, mesmo durante grandes reestruturações!