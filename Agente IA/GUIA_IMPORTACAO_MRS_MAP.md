# 📋 Guia de Importação MRS e MAP - Sistema PNSB 2024

## 🎯 **Visão Geral**

Sistema de importação especializado para identificar automaticamente entidades MRS (Manejo de Resíduos Sólidos) e MAP (Manejo de Águas Pluviais) no PNSB 2024.

---

## 🔧 **Novos Botões de Importação**

### **♻️ Importar Entidades MRS (Prioridade 1)**
- **Prioridade**: 🔴 Prioridade 1 (máxima prioridade)
- **Tipo**: Empresas de coleta, tratamento e destinação de resíduos sólidos
- **Questionário**: MRS será automaticamente marcado como obrigatório
- **Exemplos**: 
  - Empresas de limpeza urbana
  - Cooperativas de catadores
  - Empresas de reciclagem
  - Aterros sanitários

### **💧 Importar Entidades MAP (Prioridade 1)**
- **Prioridade**: 🔴 Prioridade 1 (máxima prioridade)
- **Tipo**: Empresas de drenagem urbana e manejo de águas pluviais
- **Questionário**: MAP será automaticamente marcado como obrigatório
- **Exemplos**: 
  - Empresas de saneamento
  - Empresas de drenagem
  - Sistemas de águas pluviais
  - Engenharia hidráulica

---

## 📊 **Formato CSV Simples**

### **Colunas Obrigatórias:**
```csv
Município,CNPJ,Razão Social
```

### **Exemplo para MRS:**
```csv
Município,CNPJ,Razão Social
Balneário Camboriú,03.094.629/0002-17,AMBIENTAL LIMPEZA URBANA E SANEAMENTO LTDA
Itajaí,12.345.678/0001-90,COOPERATIVA DE CATADORES UNIDOS
Bombinhas,23.456.789/0001-01,EMPRESA DE COLETA SELETIVA LTDA
```

### **Exemplo para MAP:**
```csv
Município,CNPJ,Razão Social
Itajaí,34.567.890/0001-12,ITAJAÍ SANEAMENTO E DRENAGEM S.A.
Navegantes,45.678.901/0001-23,PORTO DRENAGEM ESPECIALIZADA LTDA
Bombinhas,56.789.012/0001-34,BOMBINHAS AMBIENTAL DRENAGEM
```

---

## 🚀 **Como Usar**

### **Passo 1: Acesse o Sistema**
```
http://localhost:5000/questionarios-obrigatorios
→ Aba "Entidades Prioritárias UF"
```

### **Passo 2: Escolha o Tipo de Importação**
- **🟢 Importar Entidades MRS** - Para empresas de resíduos sólidos
- **🔵 Importar Entidades MAP** - Para empresas de águas pluviais

### **Passo 3: Configure a Importação**
1. **Selecione o arquivo CSV** (formato simples)
2. **Tipo de entidade (opcional):**
   - Deixar em branco (recomendado) - Preencher individualmente depois
   - Ou definir para todas: Empresa Terceirizada, Entidade de Catadores, Empresa Não Vinculada

### **Passo 4: Execute a Importação**
- Clique em **"Importar Entidades MRS"** ou **"Importar Entidades MAP"**
- O sistema automaticamente marca o questionário correto como obrigatório

---

## 🏷️ **Sistema de Identificação Automática**

### **Para Entidades MRS:**
- ✅ MRS marcado como obrigatório
- ❌ MAP não obrigatório
- 🏷️ Categoria: "Importação MRS"
- 📝 Motivo: "Importação MRS - [tipo_entidade]"
- 🎯 Prioridade: 1 (Vermelho - Máxima Prioridade)

### **Para Entidades MAP:**
- ❌ MRS não obrigatório
- ✅ MAP marcado como obrigatório
- 🏷️ Categoria: "Importação MAP"
- 📝 Motivo: "Importação MAP - [tipo_entidade]"
- 🎯 Prioridade: 1 (Vermelho - Máxima Prioridade)

---

## 📁 **Arquivos de Exemplo**

### **Disponíveis no Sistema:**
- `exemplo_entidades_mrs.csv` - Entidades MRS (Prioridade 1)
- `exemplo_entidades_map.csv` - Entidades MAP (Prioridade 1)

---

## 🎨 **Interface Visual**

### **Botões Diferenciados:**
- **🟢 Verde**: Importação MRS (Resíduos Sólidos) - Prioridade 1
- **🔵 Azul**: Importação MAP (Águas Pluviais) - Prioridade 1

### **Badges de Prioridade:**
- **🔴 Vermelho**: Prioridade 1 (Entidades MRS/MAP + Prefeituras)
- **🟡 Amarelo**: Prioridade 2 (Identificadas em campo durante visitas)

### **Modais Contextuais:**
- Cada tipo de importação tem interface específica
- Exemplos e descrições contextualizados
- Feedback visual sobre questionários obrigatórios

---

## 🔍 **Validações Automáticas**

### **O sistema verifica:**
- ✅ Formato CSV correto (3 colunas exatas)
- ✅ Municípios válidos do PNSB
- ✅ CNPJs únicos (evita duplicação)
- ✅ Tipo de entidade selecionado
- ✅ Tipo de importação (MRS ou MAP)

### **Códigos UF Gerados:**
- `SIMPLES_[CNPJ_LIMPO]` - Para importação simples
- Evita conflitos com códigos oficiais da UF

---

## 🎯 **Workflow Completo**

### **1. Identificação Automática:**
```
MRS: Empresa → mrs_obrigatorio = true, map_obrigatorio = false
MAP: Empresa → mrs_obrigatorio = false, map_obrigatorio = true
```

### **2. Tipo de Entidade:**
- **Flexível**: Pode ser deixado em branco na importação
- **Individual**: Cada entidade pode ter seu tipo definido separadamente
- **Opcional**: Se informado na importação, será aplicado a todas

### **3. Edição Manual Posterior:**
- **Tipo de entidade**: Preencher campo próprio para cada entidade
- **Campos adicionais**: Endereço, telefone, e-mail, responsável
- **Questionários**: Podem ser ajustados conforme necessário

### **4. Processamento:**
- Use "Processar" para ativar entidades individuais
- Use "Processar Todas" para ativação em lote

### **5. Acompanhamento:**
- Visualize no Mapa de Progresso
- Monitore via dashboard de estatísticas
- Receba alertas automáticos

---

## 💡 **Dicas de Uso**

### **Para MRS:**
- Use para empresas de limpeza urbana
- Inclua cooperativas de catadores
- Adicione empresas de reciclagem
- Considere aterros sanitários

### **Para MAP:**
- Use para empresas de saneamento
- Inclua sistemas de drenagem
- Adicione empresas de engenharia hidráulica
- Considere concessionárias de água

### **Edição Posterior:**
- **IMPORTANTE**: Defina o tipo de entidade individualmente
- Complete endereços manualmente
- Adicione telefones e e-mails
- Inclua responsáveis específicos
- Ajuste observações conforme necessário

---

## 🎉 **Benefícios do Sistema**

✅ **Identificação Automática** - Não precisa marcar questionários manualmente  
✅ **Interface Intuitiva** - Botões específicos para cada tipo  
✅ **Validação Robusta** - Evita erros comuns de importação  
✅ **Tipo de Entidade Flexível** - Pode ser definido individualmente após importação  
✅ **Edição Completa** - Todos os campos podem ser preenchidos posteriormente  
✅ **Rastreabilidade** - Histórico completo de importações  
✅ **Integração** - Funciona com sistema de progresso existente  

---

## 📞 **Suporte**

### **Em caso de problemas:**
1. Verifique o formato CSV (exatamente 3 colunas)
2. Confirme se municípios estão corretos
3. Verifique se não há CNPJs duplicados
4. Use arquivos de exemplo como referência

### **Logs e Debug:**
- Console do navegador para erros de interface
- Logs do servidor Flask para erros de backend
- Mensagens detalhadas de erro na interface