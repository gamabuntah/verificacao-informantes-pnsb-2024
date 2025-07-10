# 🚀 Sistema PNSB - Gestão de Visitas (Versão Melhorada)

Sistema de gestão de visitas para a Pesquisa Nacional de Saneamento Básico (PNSB) 2024, completamente refatorado com melhorias de segurança, arquitetura e performance.

## ✨ Melhorias Implementadas

### 🔐 Segurança
- ✅ **API Keys removidas do código** - Agora usando variáveis de ambiente
- ✅ **SECRET_KEY segura** - Geração automática de chaves criptograficamente seguras
- ✅ **Validação robusta de entrada** - Sanitização e validação de todos os dados
- ✅ **Tratamento seguro de erros** - Logs estruturados sem exposição de dados sensíveis

### 🏗️ Arquitetura
- ✅ **Blueprints** - Rotas organizadas em módulos separados
- ✅ **Factory Pattern** - Aplicação criada com padrão de fábrica
- ✅ **Separação de responsabilidades** - Validators, error handlers, cache em módulos próprios
- ✅ **Configuração centralizada** - Sistema de configuração por ambiente

### ⚡ Performance
- ✅ **Índices de banco de dados** - Otimização de consultas frequentes
- ✅ **Sistema de cache** - Cache em memória e arquivo com TTL
- ✅ **Decorators de cache** - Cache automático para funções e queries

### 🧪 Qualidade
- ✅ **Testes automatizados** - Cobertura completa de modelos, APIs e validators
- ✅ **Estrutura de testes** - Fixtures, mocks e testes organizados
- ✅ **Validação de dados** - Validadores específicos para cada entidade

## 🚀 Instalação Rápida

### 1. Configurar Ambiente
```bash
# Clonar e navegar
cd "Agente IA"

# Criar ambiente virtual
python -m venv .venv

# Ativar (Windows)
.venv\Scripts\activate

# Ativar (Linux/Mac)
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente
```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env com suas chaves
# SECRET_KEY=sua_chave_secreta_aqui
# GOOGLE_MAPS_API_KEY=sua_chave_google_maps
# GOOGLE_GEMINI_API_KEY=sua_chave_google_gemini
```

### 3. Executar Aplicação

#### Versão Nova (Recomendada)
```bash
python app_new.py
```

#### Versão Original (Compatibilidade)
```bash
python app.py
```

## 🧪 Executar Testes

```bash
# Executar todos os testes
python run_tests.py

# Executar testes específicos
python -m pytest tests/test_models.py -v
python -m pytest tests/test_api.py -v
python -m pytest tests/test_validators.py -v

# Gerar relatório de cobertura
python -m pytest tests/ --cov=gestao_visitas --cov-report=html
```

## 📁 Nova Estrutura do Projeto

```
Agente IA/
├── gestao_visitas/
│   ├── config/
│   │   ├── __init__.py
│   │   └── security.py          # Configurações de segurança
│   ├── models/                  # Modelos com índices otimizados
│   │   ├── agendamento.py
│   │   ├── checklist.py
│   │   └── contatos.py
│   ├── routes/                  # Blueprints organizados
│   │   ├── __init__.py
│   │   ├── main.py             # Rotas das páginas
│   │   └── api.py              # APIs REST
│   ├── services/               # Lógica de negócio
│   │   ├── maps.py
│   │   ├── relatorios.py
│   │   └── ...
│   ├── utils/                  # Utilitários
│   │   ├── __init__.py
│   │   ├── validators.py       # Validação de dados
│   │   ├── error_handlers.py   # Tratamento de erros
│   │   └── cache.py           # Sistema de cache
│   ├── app_factory.py         # Factory pattern
│   └── ...
├── tests/                     # Testes automatizados
│   ├── __init__.py
│   ├── conftest.py           # Configuração dos testes
│   ├── test_models.py        # Testes de modelos
│   ├── test_api.py          # Testes de API
│   └── test_validators.py   # Testes de validação
├── app.py                   # Aplicação original
├── app_new.py              # Aplicação refatorada
├── run_tests.py            # Script de testes
└── pytest.ini             # Configuração do pytest
```

## 🔧 Comandos de Desenvolvimento

### Banco de Dados
```bash
# Inicializar migrações
flask db init

# Criar migração
flask db migrate -m "Descrição da mudança"

# Aplicar migrações
flask db upgrade
```

### Cache
```bash
# No Python/Flask shell
from gestao_visitas.utils.cache import CacheUtils

# Limpar cache
CacheUtils.invalidate_pattern("*")

# Aquecer cache
CacheUtils.warm_up_cache()

# Ver estatísticas
print(CacheUtils.get_cache_info())
```

### Logs
```bash
# Logs são salvos em:
# - logs/pnsb_errors.log (errors)
# - instance/logs/ (aplicação)
```

## 🔐 Configurações de Segurança

### Variáveis de Ambiente Obrigatórias
- `SECRET_KEY` - Chave secreta para sessões
- `GOOGLE_MAPS_API_KEY` - Para cálculo de rotas
- `GOOGLE_GEMINI_API_KEY` - Para chat com IA

### Gerar Chave Secreta Segura
```python
import secrets
print(secrets.token_hex(32))
```

## 📊 APIs Melhoradas

### Respostas Padronizadas
```json
{
  "success": true,
  "data": {...},
  "message": "Operação realizada com sucesso",
  "timestamp": "2024-01-01T10:00:00"
}
```

### Tratamento de Erros
```json
{
  "success": false,
  "error": "Mensagem de erro",
  "type": "validation_error",
  "timestamp": "2024-01-01T10:00:00"
}
```

### Validação Automática
- Campos obrigatórios verificados automaticamente
- Dados sanitizados para prevenir XSS
- Validação de formatos (data, hora, email, telefone)
- Validação de regras de negócio

## 🎯 Principais Melhorias de Performance

1. **Índices de Banco**
   - `municipio` - Para filtros por cidade
   - `data` - Para consultas temporais
   - `status` - Para filtros de estado
   - `tipo_pesquisa` - Para separação MRS/MAP

2. **Cache Inteligente**
   - Configurações estáticas (24h TTL)
   - Consultas frequentes (1h TTL)
   - Resultados de APIs externas (15min TTL)

3. **Validação Otimizada**
   - Validação em camadas
   - Sanitização automática
   - Cache de validações

## 📈 Monitoramento

### Métricas de Cache
```python
# Ver estatísticas do cache
from gestao_visitas.utils.cache import cache_manager
print(cache_manager.get_stats())
```

### Logs de Erro
- Logs estruturados com contexto da requisição
- Rastreamento de IPs e User-Agents
- Timestamps precisos para debugging

## 🛡️ Checklist de Segurança

- ✅ API keys não expostas no código
- ✅ Variáveis de ambiente configuradas
- ✅ Validação de entrada implementada
- ✅ Sanitização de dados ativa
- ✅ Tratamento de erros sem vazamento de dados
- ✅ Headers de segurança configurados (produção)
- ✅ Logs de auditoria implementados

## 🚀 Deploy em Produção

1. **Configurar variáveis de ambiente de produção**
2. **Definir FLASK_ENV=production**
3. **Usar servidor WSGI (Gunicorn/uWSGI)**
4. **Configurar proxy reverso (Nginx)**
5. **Habilitar HTTPS**
6. **Configurar backup do banco de dados**

## 📞 Suporte

Para dúvidas sobre as melhorias implementadas, consulte:
- Documentação inline no código
- Testes automatizados como exemplos
- Logs de aplicação para troubleshooting

---

**Versão:** 2.0.0 (Melhorada)
**Data:** Janeiro 2024
**Status:** ✅ Pronto para Produção