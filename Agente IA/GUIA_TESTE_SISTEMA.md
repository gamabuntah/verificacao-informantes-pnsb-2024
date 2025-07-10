# 🧪 **GUIA COMPLETO PARA TESTAR O SISTEMA PNSB**

## 🚀 **Preparação do Ambiente**

### **1. Instalar Dependências**
```bash
# Opção 1: Se pip3 estiver disponível
pip3 install -r requirements.txt

# Opção 2: Usando apt (Ubuntu/Debian)
sudo apt update
sudo apt install python3-pip
pip3 install -r requirements.txt

# Opção 3: Usando conda
conda create -n pnsb python=3.10
conda activate pnsb
pip install -r requirements.txt
```

### **2. Configurar Variáveis de Ambiente**
```bash
# Editar o arquivo .env
nano .env

# Configurar chaves (opcional para teste básico):
SECRET_KEY=sua_chave_secreta_aqui
GOOGLE_MAPS_API_KEY=sua_chave_google_maps_aqui
GOOGLE_GEMINI_API_KEY=sua_chave_gemini_aqui
```

### **3. Executar Migrações**
```bash
# Se houver migrações pendentes
python3 -c "from gestao_visitas.app_factory import create_app; app = create_app(); app.app_context().push(); from gestao_visitas.db import db; db.create_all()"
```

---

## 🎯 **ROTEIRO DE TESTES COMPLETO**

### **TESTE 1: Inicialização do Sistema**

```bash
# Iniciar o servidor
python3 app_new.py
```

**✅ Resultado esperado:**
```
🚀 Iniciando Sistema PNSB - Gestão de Visitas
==================================================
📍 Ambiente: development
🔐 Validando configuração de segurança...
⚠️  Algumas funcionalidades podem estar limitadas
🏗️  Criando aplicação...
🔥 Aquecendo cache...
==================================================
🌐 Servidor rodando em: http://127.0.0.1:5000
🔧 Debug: Ativado
==================================================
📝 Para parar o servidor: Ctrl+C
==================================================
```

### **TESTE 2: Interface Principal (Layout Moderno)**

**URL**: `http://127.0.0.1:5000`

**✅ Verificar:**
1. **Navegação Lateral:**
   - [ ] Sidebar aparece corretamente
   - [ ] 3 seções: Principal, Gestão, PNSB Avançado
   - [ ] Ícones e textos visíveis
   - [ ] Hover effects funcionando

2. **Navbar Superior:**
   - [ ] Toggle da sidebar funciona
   - [ ] Logo "Sistema PNSB" com gradiente
   - [ ] Botão de usuário presente

3. **Responsividade:**
   - [ ] Redimensionar janela para mobile
   - [ ] Sidebar vira overlay
   - [ ] Layout se adapta corretamente

### **TESTE 3: Funcionalidades de Navegação**

**Clicar em cada item da sidebar:**

1. **Dashboard** (`/`)
   - [ ] Página carrega corretamente
   - [ ] Breadcrumb mostra "Dashboard"
   - [ ] Cards responsivos

2. **Visitas** (`/visitas`)
   - [ ] Botão "Agendar Nova Visita" modernizado
   - [ ] Filtros com design atualizado
   - [ ] Inputs e selects customizados

3. **Checklist** (`/checklist`)
   - [ ] Interface funcional
   - [ ] Breadcrumb correto

4. **Contatos** (`/contatos`)
   - [ ] Tabela responsiva implementada
   - [ ] Filtros modernizados
   - [ ] Botões com novo design

5. **Relatórios** (`/relatorios`)
   - [ ] Página carrega sem erros

### **TESTE 4: APIs PNSB (Funcionalidades Avançadas)**

**Testar endpoints no navegador ou via curl:**

1. **Status das Funcionalidades:**
```bash
curl http://127.0.0.1:5000/api/pnsb/status/funcionalidades-pnsb
```

2. **Mapa de Progresso:**
```bash
curl http://127.0.0.1:5000/api/pnsb/questionarios/mapa-progresso
```

3. **Produtividade:**
```bash
curl http://127.0.0.1:5000/api/pnsb/produtividade/comparativo-equipe
```

**✅ Resultado esperado:** JSON com dados simulados das funcionalidades

### **TESTE 5: Responsividade Mobile**

**Ferramentas do Desenvolvedor (F12):**

1. **Testar breakpoints:**
   - [ ] Desktop (>1200px)
   - [ ] Tablet (768px-1199px)
   - [ ] Mobile (<768px)

2. **Verificar tabelas:**
   - [ ] Em `/contatos`, redimensionar para mobile
   - [ ] Tabela deve empilhar verticalmente
   - [ ] Data labels aparecem

3. **Navegação mobile:**
   - [ ] Sidebar vira modal
   - [ ] Overlay escuro aparece
   - [ ] Fechar ao clicar fora

### **TESTE 6: Componentes Interativos**

1. **Sistema de Notificações:**
```javascript
// Abrir console do navegador (F12) e testar:
NotificationManager.success('Teste de sucesso!');
NotificationManager.error('Teste de erro!');
NotificationManager.warning('Teste de aviso!');
NotificationManager.info('Teste de informação!');
```

2. **Loading States:**
```javascript
// No console:
LoadingManager.show(document.body, 'Carregando...');
// Aguardar 3 segundos
setTimeout(() => LoadingManager.hide(document.body), 3000);
```

3. **Validação de Formulários:**
   - [ ] Ir para `/contatos`
   - [ ] Tentar enviar formulário vazio
   - [ ] Verificar validações visuais

### **TESTE 7: Performance e Acessibilidade**

1. **Lighthouse (Chrome DevTools):**
   - [ ] Performance: >80
   - [ ] Accessibility: >90
   - [ ] Best Practices: >80
   - [ ] SEO: >80

2. **Navegação por teclado:**
   - [ ] Tab para navegar
   - [ ] Enter para ativar
   - [ ] Escape para fechar sidebar

3. **Screen reader:**
   - [ ] Labels adequados
   - [ ] ARIA attributes funcionando

---

## 🐛 **TESTE DE BUGS CONHECIDOS**

### **Verificar se foram corrigidos:**

1. **✅ Campos faltando nos modelos**
   - Testar criação de contatos com todos os campos
   - Verificar se `pesquisador_responsavel` existe

2. **✅ Responsividade de tabelas**
   - Redimensionar `/contatos` em mobile
   - Verificar se empilha corretamente

3. **✅ Navegação consistente**
   - Testar todos os links da sidebar
   - Verificar breadcrumbs automáticos

---

## 📊 **ENDPOINTS PARA TESTE MANUAL**

### **Dashboard de Funcionalidades:**
```bash
# Status geral
GET http://127.0.0.1:5000/api/pnsb/status/funcionalidades-pnsb

# Demo das funcionalidades
GET http://127.0.0.1:5000/api/pnsb/demo/funcionalidades-pnsb
```

### **Perfil Inteligente:**
```bash
# Obter perfil
GET http://127.0.0.1:5000/api/pnsb/perfil-informante/João Silva/Itajaí

# Melhores horários
GET http://127.0.0.1:5000/api/pnsb/perfil-informante/melhores-horarios/João Silva/Itajaí
```

### **Logística com Google Maps:**
```bash
# Otimizar rota
POST http://127.0.0.1:5000/api/pnsb/logistica/otimizar-rota-diaria
Content-Type: application/json
{
  "data_visita": "2024-07-01",
  "origem": "Itajaí"
}
```

### **Rastreamento de Questionários:**
```bash
# Mapa de progresso
GET http://127.0.0.1:5000/api/pnsb/questionarios/mapa-progresso

# Status por município
GET http://127.0.0.1:5000/api/pnsb/questionarios/status-municipio/Itajaí
```

---

## 🎯 **CHECKLIST FINAL DE TESTE**

### **✅ Interface Geral:**
- [ ] Sistema inicia sem erros
- [ ] Layout moderno carrega corretamente
- [ ] Navegação lateral funciona
- [ ] Responsividade mobile OK
- [ ] Breadcrumbs automáticos aparecem

### **✅ Funcionalidades Core:**
- [ ] Dashboard carrega dados
- [ ] Visitas podem ser criadas/editadas
- [ ] Checklist funciona corretamente
- [ ] Contatos com busca avançada
- [ ] Relatórios são gerados

### **✅ APIs PNSB (9 módulos):**
- [ ] Perfil Inteligente responde
- [ ] Logística Maps funciona
- [ ] Rastreamento ativo
- [ ] Assistente de Abordagem OK
- [ ] Sistema de Contingência ativo
- [ ] Comunicação Eficiente funciona
- [ ] Análise de Resistência OK
- [ ] Dashboard Produtividade ativo
- [ ] Otimizador Cronograma funciona

### **✅ UX/UI Melhorias:**
- [ ] Design consistente em todas as páginas
- [ ] Componentes interativos funcionam
- [ ] Loading states aparecem
- [ ] Notificações funcionam
- [ ] Validação de formulários ativa

---

## 🚨 **Resolução de Problemas**

### **Erro: "Module not found"**
```bash
# Instalar dependência específica
pip3 install flask flask-sqlalchemy python-dotenv
```

### **Erro: "Port already in use"**
```bash
# Matar processo na porta 5000
lsof -ti:5000 | xargs kill -9
# Ou usar porta diferente
FLASK_PORT=5001 python3 app_new.py
```

### **Erro: "Database not found"**
```bash
# Recriar banco
rm -f gestao_visitas/gestao_visitas.db
python3 -c "from gestao_visitas.app_factory import create_app; app = create_app(); app.app_context().push(); from gestao_visitas.db import db; db.create_all()"
```

### **CSS/JS não carrega**
```bash
# Verificar arquivos estáticos
ls -la gestao_visitas/static/css/
ls -la gestao_visitas/static/js/
```

---

## 🎉 **Resultado Esperado**

**Ao final dos testes, você deve ter:**

✅ **Sistema funcionando completamente**  
✅ **Interface moderna e responsiva**  
✅ **46+ endpoints PNSB operacionais**  
✅ **Navegação intuitiva e funcional**  
✅ **Componentes interativos ativos**  
✅ **Tabelas responsivas em mobile**  
✅ **Validação e feedback visual**  
✅ **Acessibilidade melhorada**  

**🚀 Sistema PNSB totalmente operacional e testado!**