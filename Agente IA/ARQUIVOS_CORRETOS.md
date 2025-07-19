# 🎯 ARQUIVOS CORRETOS DO SISTEMA - REFERÊNCIA OBRIGATÓRIA

## ⚠️ IMPORTANTE: SEMPRE CONSULTAR ESTE ARQUIVO ANTES DE QUALQUER MODIFICAÇÃO

### 📁 ARQUIVOS ATIVOS (OS ÚNICOS QUE DEVEM SER EDITADOS)

#### 1. TEMPLATE PRINCIPAL
```
/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA/gestao_visitas/templates/mapa_progresso_renovado.html
```
- **Tamanho:** ~21KB (arquivo pequeno)
- **Rota:** /mapa-progresso, /dashboard-executivo, /mapa-progresso-novo
- **Status:** ✅ ATIVO

#### 2. JAVASCRIPT PRINCIPAL
```
/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA/gestao_visitas/static/js/mapa_progresso.js
```
- **Contém:** Classe MapaProgressoPNSB, calcularEficienciaDinamica()
- **Status:** ✅ ATIVO

#### 3. JAVASCRIPT CHARTS
```
/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA/gestao_visitas/static/js/mapa_progresso_charts.js
```
- **Contém:** ChartsAnalytics, gráficos Chart.js
- **Status:** ✅ ATIVO

#### 4. JAVASCRIPT WORKFLOW
```
/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA/gestao_visitas/static/js/mapa_progresso_workflow.js
```
- **Contém:** Funcionalidades de workflow
- **Status:** ✅ ATIVO

#### 5. CSS PRINCIPAL
```
/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA/gestao_visitas/static/css/mapa_progresso.css
```
- **Contém:** Estilos do dashboard
- **Status:** ✅ ATIVO

---

## ❌ ARQUIVOS INATIVOS (NUNCA EDITAR)

### Template Antigo (732KB - IGNORAR SEMPRE)
```
❌ /mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA/gestao_visitas/templates/mapa_progresso.html
```

### Backups (IGNORAR SEMPRE)
```
❌ mapa_progresso_backup_*.html
❌ mapa_progresso_BACKUP_*.html
❌ mapa_progresso_ORIGINAL.html
```

### Arquivos Otimizados (Auto-gerados)
```
⚠️ gestao_visitas/static/optimized/js/*.js
⚠️ gestao_visitas/static/optimized/css/*.css
```

---

## 🔍 COMO VERIFICAR SE ESTÁ NO ARQUIVO CORRETO

### Para Template:
```bash
# CORRETO: Arquivo deve ter ~21KB
ls -la gestao_visitas/templates/mapa_progresso_renovado.html

# ERRADO: Arquivo tem 732KB
ls -la gestao_visitas/templates/mapa_progresso.html
```

### Para JavaScript:
```bash
# Verificar se contém a função
grep -c "calcularEficienciaDinamica" gestao_visitas/static/js/mapa_progresso.js
# Deve retornar: 3 (se contém a função)
```

---

## 📋 CHECKLIST ANTES DE QUALQUER MODIFICAÇÃO

- [ ] ✅ Confirmar que estou editando `mapa_progresso_renovado.html` (NÃO o mapa_progresso.html)
- [ ] ✅ Confirmar que estou editando arquivos em `/static/js/` (NÃO em `/static/optimized/`)
- [ ] ✅ Verificar tamanho do arquivo HTML (~21KB = correto, 732KB = errado)
- [ ] ✅ Consultar este arquivo antes de qualquer edição

---

## 🚨 COMANDOS DE EMERGÊNCIA

### Se editei o arquivo errado:
```bash
# Verificar qual template está sendo usado
grep -n "mapa_progresso" /mnt/c/users/ggmob/Cursor\ AI/Verificação\ Informantes\ PNSB/Agente\ IA/app.py
```

### Sincronizar arquivos otimizados (se necessário):
```bash
cp gestao_visitas/static/js/mapa_progresso.js gestao_visitas/static/optimized/js/
cp gestao_visitas/static/css/mapa_progresso.css gestao_visitas/static/optimized/css/
```

---

## 🎯 RESUMO EXECUTIVO

**REGRA DE OURO:** 
- Template = `mapa_progresso_renovado.html` (21KB)
- JavaScript = `/static/js/` (NÃO /static/optimized/)
- SEMPRE verificar este arquivo antes de editar

**EM CASO DE DÚVIDA:**
1. Consultar este arquivo
2. Verificar tamanho do HTML (21KB = correto)
3. Confirmar rota em app.py (deve apontar para _renovado.html)