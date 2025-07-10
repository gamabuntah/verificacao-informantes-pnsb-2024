# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask-based web application for managing field research visits for the PNSB (Pesquisa Nacional de Saneamento Básico) 2024 survey. The system manages visits to 11 municipalities in Santa Catarina, Brazil, focusing on urban cleaning and solid waste management data collection.

## Commands

### Development Setup
```bash
# Install dependencies (Windows)
instalar_dependencias.bat

# Run the application (Windows)
executar_projeto.bat

# Manual setup for non-Windows environments
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
cd "Agente IA"
python app.py
```

### Database Operations
```bash
# Initialize database migrations
flask db init

# Create new migration
flask db migrate -m "description"

# Apply migrations
flask db upgrade
```

## Architecture

### Core Structure
- **Main App**: `Agente IA/app.py` - Flask application with all routes and API endpoints
- **Models**: `gestao_visitas/models/` - SQLAlchemy models for visits, checklists, and contacts
- **Services**: `gestao_visitas/services/` - Business logic separated into service classes
- **Templates**: `gestao_visitas/templates/` - HTML templates for web interface

### Key Models
- **Visita** (`models/agendamento.py`): Core visit entity with status workflow (agendada → em preparação → em execução → resultados visita → realizada → finalizada)
  - **IMPORTANT**: Uses 'local' field instead of 'informante' (migrated 2025-06-30)
- **Checklist** (`models/checklist.py`): Task tracking for three visit phases with boolean fields for each step
- **Contato** (`models/contatos.py`): Contact information from multiple AI sources (ChatGPT, Gemini, Grok)

### Service Layer Architecture
- **RelatorioService**: Visit reports and analytics
- **MapaService**: Google Maps integration for routes
- **InformanteService**: Informant management
- **RotaService**: Route optimization
- All services initialized in app.py with proper dependency injection

### Database Configuration
- SQLite database at `gestao_visitas/gestao_visitas.db`
- Flask-Migrate for schema management
- Auto-creation on startup via `db.create_all()`

## API Endpoints

### Main APIs
- `GET/POST /api/visitas` - Visit CRUD operations
- `GET/PUT /api/visitas/<id>` - Individual visit management
- `POST /api/visitas/<id>/status` - Status updates
- `GET/POST /api/checklist/<visita_id>` - Checklist management
- `GET /api/contatos` - Contact information
- `POST /api/contatos/importar` - CSV import for contacts
- `POST /api/chat` - AI chat integration with Google Gemini

### Important Validation Rules
- Visit dates cannot be in the past
- Municipality must be from the predefined list in `config.py`
- Status transitions follow strict workflow
- Checklist is automatically created for each visit

## External Dependencies

### Required API Keys
- `GOOGLE_MAPS_API_KEY` - For route calculations (optional, falls back gracefully)
- Gemini API key hardcoded in app.py for chat functionality

### Key Libraries
- Flask 3.0.2 with SQLAlchemy 3.1.1
- Flask-Migrate 4.0.5 for database migrations
- pandas 2.3.0 for CSV processing
- requests 2.31.0 for external API calls

## Development Notes

### Municipality Coverage
The system covers 11 specific municipalities in Santa Catarina: Balneário Camboriú, Balneário Piçarras, Bombinhas, Camboriú, Itajaí, Itapema, Luiz Alves, Navegantes, Penha, Porto Belo, and Ilhota.

### Data Collection Types
- **MRS**: Manejo de Resíduos Sólidos (Solid Waste Management)
- **MAP**: Manejo de Águas Pluviais (Stormwater Management)

### File Organization
- Batch scripts for Windows automation in root directory
- Research materials and documentation in various folders
- Contact research data in CSV format within `gestao_visitas/pesquisa_contatos_prefeituras/`

### Status Workflow
Visits follow a strict status progression that cannot be bypassed. The system validates status transitions and prevents invalid state changes.

## Data Protection & Migration System

### Backup & Migration Tools
- **Migration Manager**: `gestao_visitas/utils/migration_manager.py` - Complete backup/restore system
- **Migration Scripts**: Scripts for safe schema changes without data loss
- **Backup Directory**: `gestao_visitas/backups/` - Automated backups with metadata

### Critical Guidelines for Schema Changes
1. **ALWAYS create backup before changes**: Use `create_quick_backup('description')`
2. **Test changes locally first**
3. **Follow migration guide**: See `MIGRATION_GUIDE.md`
4. **Use migration scripts for field renames/type changes**

### Recent Migrations
- **2025-06-30**: Changed 'informante' field to 'local' in Visit model
- **2025-06-30**: Implemented autocomplete for 'local' field using AI data from CSV files