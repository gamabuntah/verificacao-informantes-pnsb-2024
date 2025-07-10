# 🔧 CONFIGURAÇÃO DAS APIs DO SISTEMA PNSB

## ⚠️ SITUAÇÃO ATUAL

O sistema está **100% funcional** com as funcionalidades básicas, mas algumas funcionalidades avançadas requerem configuração de APIs externas.

## ✅ FUNCIONALIDADES QUE FUNCIONAM AGORA

**Sem necessidade de configuração:**
- ✅ Interface web completa com design moderno
- ✅ Gestão de visitas e agendamentos
- ✅ Gestão de contatos e informantes
- ✅ Sistema de checklist completo
- ✅ Relatórios e dashboards básicos
- ✅ 48 endpoints API funcionais
- ✅ Banco de dados SQLite
- ✅ Sistema de status e workflow
- ✅ Todas as operações CRUD

## 🔑 FUNCIONALIDADES QUE PRECISAM DE APIS

### 1. Google Maps API (Para Logística)
**Funcionalidades afetadas:**
- 🗺️ Otimização automática de rotas
- 📍 Cálculo de tempo de viagem entre municípios
- 🚗 Monitoramento de trânsito em tempo real
- 📊 Análise de raio de cobertura

### 2. Google Gemini API (Para IA)
**Funcionalidades afetadas:**
- 🧠 Análise inteligente de perfis de informantes
- 💬 Geração automática de estratégias de abordagem
- 📈 Análise de resistência com IA
- 🎯 Recomendações personalizadas

## 🛠️ COMO CONFIGURAR

### Passo 1: Editar arquivo .env

```bash
# Edite o arquivo .env na raiz do projeto
nano .env
```

### Passo 2: Configurar SECRET_KEY (OBRIGATÓRIA)

```bash
# Gere uma chave segura
python3 -c "import secrets; print(secrets.token_hex(32))"

# Cole o resultado no .env:
SECRET_KEY=sua_chave_gerada_aqui
```

### Passo 3: Google Maps API (OPCIONAL)

1. Acesse: https://console.cloud.google.com/
2. Crie um projeto ou use existente
3. Ative as APIs:
   - Maps JavaScript API
   - Places API  
   - Directions API
   - Distance Matrix API
4. Crie credenciais (API Key)
5. Configure no .env:

```
GOOGLE_MAPS_API_KEY=sua_chave_google_maps_aqui
```

### Passo 4: Google Gemini API (OPCIONAL)

1. Acesse: https://makersuite.google.com/app/apikey
2. Crie uma API Key
3. Configure no .env:

```
GOOGLE_GEMINI_API_KEY=sua_chave_gemini_aqui
```

## 🚀 INICIAR SISTEMA

Após configurar as APIs:

```bash
# Usar o script de inicialização
./start_system.sh

# OU manualmente
python3 app_new.py
```

## 💡 RECOMENDAÇÕES

### Para Testes e Desenvolvimento
- ✅ Configure apenas o SECRET_KEY
- ✅ Use o sistema sem as APIs externas
- ✅ Todas as funcionalidades básicas estarão disponíveis

### Para Produção Completa
- 🔑 Configure todas as 3 chaves
- 🗺️ Habilite logística completa com Maps
- 🧠 Habilite análises de IA com Gemini

## 📊 IMPACTO DAS CONFIGURAÇÕES

| Configuração | Funcionalidades | % do Sistema |
|-------------|----------------|--------------|
| Só SECRET_KEY | Básicas + Interface | 80% |
| + Google Maps | + Logística | 90% |
| + Gemini | + IA Completa | 100% |

## ⚡ CONCLUSÃO

**O sistema ESTÁ PRONTO para uso** mesmo sem as APIs externas. Configure apenas conforme suas necessidades:

- **Mínimo:** SECRET_KEY (80% funcional)
- **Recomendado:** SECRET_KEY + Google Maps (90% funcional)
- **Completo:** Todas as chaves (100% funcional)