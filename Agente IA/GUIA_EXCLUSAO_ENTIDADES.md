# 🗑️ Guia de Exclusão de Entidades - Sistema PNSB 2024

## 🎯 **Visão Geral**

Sistema completo para exclusão de entidades importadas incorretamente, com confirmações de segurança e interface intuitiva.

---

## 🔧 **Funcionalidades de Exclusão**

### **🗑️ Exclusão Individual**
- **Localização**: Botão "Excluir" em cada entidade
- **Ícone**: `🗑️ Excluir` (botão vermelho)
- **Confirmação**: Modal personalizado com detalhes da entidade
- **Segurança**: Confirmação simples

### **💥 Exclusão em Lote**
- **Localização**: Botão "Excluir Todas" no topo da aba
- **Ícone**: `🗑️ Excluir Todas` (botão vermelho outline)
- **Confirmação**: Modal com lista e confirmação dupla
- **Segurança**: Digitação obrigatória de "CONFIRMAR"

---

## 🖱️ **Como Usar - Exclusão Individual**

### **Passo 1: Localizar a Entidade**
```
📍 Navegue até: Questionários Obrigatórios
    → Aba "🔴 Entidades Prioritárias (Prioridade 1)"
    → Encontre a entidade incorreta
```

### **Passo 2: Iniciar Exclusão**
```
🔘 Clique no botão: "🗑️ Excluir" (vermelho)
```

### **Passo 3: Confirmar no Modal**
```
📋 Modal mostra:
    • Nome da entidade
    • Município e tipo
    • CNPJ (se disponível)
    • Alerta de ação irreversível

✅ Clique em "Excluir Entidade" para confirmar
❌ Clique em "Cancelar" para abortar
```

### **Passo 4: Resultado**
```
✅ Sucesso: "Entidade [NOME] excluída com sucesso!"
❌ Erro: Mensagem de erro específica
🔄 Lista atualizada automaticamente
```

---

## 💥 **Como Usar - Exclusão em Lote**

### **Passo 1: Acessar Função**
```
📍 No topo da aba "Entidades Prioritárias"
🔘 Clique em: "🗑️ Excluir Todas" (canto direito)
```

### **Passo 2: Revisar Modal de Confirmação**
```
⚠️ Modal mostra:
    • Alerta crítico em vermelho
    • Quantidade total de entidades
    • Lista das primeiras 10 entidades
    • Consequências da ação
    • Campo para digitação
```

### **Passo 3: Confirmação Dupla**
```
1️⃣ Primeira confirmação: Ler todos os alertas
2️⃣ Segunda confirmação: Digite "CONFIRMAR" no campo
    ⚠️ Deve ser exatamente "CONFIRMAR" (maiúsculo)
3️⃣ Clique em "Excluir Todas"
```

### **Passo 4: Resultado**
```
✅ Sucesso: "X entidades excluídas com sucesso!"
❌ Erro: Mensagem de erro específica
🔄 Lista completamente limpa
```

---

## 🛡️ **Sistema de Segurança**

### **🔒 Validações Implementadas:**

#### **Exclusão Individual:**
- ✅ Verificação de existência da entidade
- ✅ Modal de confirmação visual
- ✅ Detalhes da entidade mostrados
- ✅ Botão de cancelamento sempre visível

#### **Exclusão em Lote:**
- ✅ Verificação se há entidades para excluir
- ✅ Modal com alertas visuais em vermelho
- ✅ Lista prévia das entidades a serem excluídas
- ✅ Campo de confirmação obrigatório
- ✅ Validação exata do texto "CONFIRMAR"
- ✅ Múltiplos avisos sobre irreversibilidade

---

## ⚠️ **Alertas de Segurança**

### **🚨 ATENÇÃO: Ações Irreversíveis**
```
❌ NÃO há como desfazer exclusões
❌ NÃO há lixeira ou backup automático
❌ NÃO há recuperação posterior
```

### **✅ Quando Usar Exclusão:**
- ✅ Importação com dados incorretos
- ✅ Entidades duplicadas por erro
- ✅ Mudança de estratégia de importação
- ✅ Correção de erros de upload

### **❌ Quando NÃO Usar:**
- ❌ Para "limpar" temporariamente
- ❌ Se não tem certeza dos dados
- ❌ Para testar funcionalidades
- ❌ Se outras pessoas dependem dos dados

---

## 🔄 **Workflow Recomendado**

### **Cenário 1: Correção de Upload Errado**
```
1. 📤 Fez upload de arquivo errado
2. 🔍 Identifica entidades incorretas
3. 🗑️ Exclui entidades individuais OU todas
4. 📤 Faz novo upload com dados corretos
5. ✅ Verifica se está tudo certo
```

### **Cenário 2: Troca de Estratégia MRS/MAP**
```
1. 📤 Importou como MRS, mas era MAP
2. 💥 Usa "Excluir Todas" para limpar
3. 📤 Reimporta usando botão MAP correto
4. ✅ Valida questionários obrigatórios
```

### **Cenário 3: Entidade Individual Errada**
```
1. 🔍 Identifica 1 entidade específica errada
2. 🗑️ Usa exclusão individual
3. ➕ Adiciona manualmente entidade correta
4. ✅ Verifica dados atualizados
```

---

## 📊 **Interface Visual**

### **🔴 Botões de Exclusão:**
```
Individual: [🗑️ Excluir]     - Vermelho pequeno
Em Lote:    [🗑️ Excluir Todas] - Vermelho outline
```

### **📋 Modal de Confirmação:**
```
🔴 Cabeçalho: Fundo vermelho com título
⚠️ Corpo: Alertas amarelos e informações
🗑️ Botões: Cancelar (cinza) + Excluir (vermelho)
```

### **💬 Mensagens de Resultado:**
```
✅ Sucesso: Verde com ícone de check
❌ Erro: Vermelho com descrição específica
🔄 Atualização: Lista recarregada automaticamente
```

---

## 🛠️ **Endpoints da API**

### **Exclusão Individual:**
```http
DELETE /api/questionarios/entidade-prioritaria/{id}

Resposta de Sucesso:
{
  "success": true,
  "message": "Entidade excluída com sucesso",
  "entidade_id": 123
}
```

### **Exclusão em Lote:**
```http
DELETE /api/questionarios/excluir-todas-entidades

Resposta de Sucesso:
{
  "success": true,
  "message": "15 entidades excluídas com sucesso",
  "entidades_excluidas": 15
}
```

---

## 🎯 **Casos de Uso Comuns**

### **1. Upload de Arquivo Errado:**
- **Problema**: Subiu CSV com empresas de outro município
- **Solução**: "Excluir Todas" → Reimportar arquivo correto

### **2. Tipo MRS/MAP Trocado:**
- **Problema**: Importou empresas MAP como MRS
- **Solução**: "Excluir Todas" → Usar botão MAP correto

### **3. Entidade Duplicada:**
- **Problema**: Mesma empresa aparece 2x na lista
- **Solução**: Exclusão individual da duplicata

### **4. CNPJ Incorreto:**
- **Problema**: 1 empresa com CNPJ errado
- **Solução**: Exclusão individual → Editar outra ou reimportar

---

## ✅ **Sistema Completo e Seguro**

O sistema de exclusão está **totalmente implementado** com:

- 🛡️ **Máxima Segurança**: Confirmações duplas e alertas
- 🎨 **Interface Intuitiva**: Modais personalizados e visuais
- ⚡ **Performance**: APIs otimizadas para exclusão rápida
- 🔄 **UX Completa**: Atualizações automáticas da interface
- 📝 **Logs**: Registro completo de todas as exclusões

**🎉 Pronto para corrigir qualquer erro de importação!**