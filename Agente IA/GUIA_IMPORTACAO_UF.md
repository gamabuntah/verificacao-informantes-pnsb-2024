# 📋 Guia de Importação da Lista UF - Entidades Prioritárias

## 🎯 **Visão Geral**

Este guia explica como importar a lista oficial da UF contendo as entidades/empresas **mais obrigatórias de todas** (Prioridade 1) para o sistema PNSB 2024.

---

## 📊 **Formato do Arquivo CSV**

### **Colunas Obrigatórias:**
- `codigo_uf` - Código único da entidade na lista da UF
- `municipio` - Município (deve ser um dos 11 municípios PNSB)
- `nome_entidade` - Nome completo da empresa/entidade
- `tipo_entidade` - Tipo: `empresa_terceirizada`, `entidade_catadores`, ou `empresa_nao_vinculada`

### **Colunas Opcionais:**
- `mrs_obrigatorio` - true/false (padrão: false)
- `map_obrigatorio` - true/false (padrão: false)
- `cnpj` - CNPJ da entidade
- `endereco_completo` - Endereço completo
- `categoria_uf` - Categoria na classificação da UF
- `motivo_mrs` - Por que MRS é obrigatório
- `motivo_map` - Por que MAP é obrigatório
- `telefone_uf` - Telefone da entidade
- `email_uf` - E-mail da entidade
- `responsavel_uf` - Nome do responsável
- `observacoes_uf` - Observações adicionais

### **Municípios Válidos:**
```
- Balneário Camboriú    - Itajaí        - Penha
- Balneário Piçarras    - Itapema       - Porto Belo
- Bombinhas             - Luiz Alves    - Ilhota
- Camboriú              - Navegantes
```

---

## 🚀 **Método 1: Interface Web (Recomendado)**

### **Passo a Passo:**

1. **Inicie o sistema:**
   ```bash
   cd "Agente IA"
   python app.py
   ```

2. **Acesse a interface:**
   ```
   http://localhost:5000/questionarios-obrigatorios
   ```

3. **Vá para a aba "Entidades Prioritárias UF"**

4. **Clique em "Importar Lista UF"**

5. **Selecione seu arquivo CSV**

6. **Clique em "Importar"**

7. **Após a importação, clique em "Processar Todas"** para ativar as entidades

---

## 🔧 **Método 2: Script Python (Para Grandes Volumes)**

### **Preparação:**
```bash
# Instalar dependências (se necessário)
pip install pandas requests

# Validar e importar
python script_importar_lista_uf.py exemplo_lista_uf.csv
```

### **Exemplo de Uso:**
```bash
# 1. Validar arquivo
python script_importar_lista_uf.py minha_lista_uf.csv

# 2. Após validação bem-sucedida, confirmar importação
# O script perguntará: "Deseja prosseguir com a importação? (s/N):"
# Digite 's' e pressione Enter
```

---

## 📋 **Exemplo de Arquivo CSV**

Arquivo já criado: `exemplo_lista_uf.csv`

```csv
codigo_uf,municipio,nome_entidade,tipo_entidade,mrs_obrigatorio,map_obrigatorio,cnpj,categoria_uf,motivo_mrs
UF001,Balneário Camboriú,Empresa de Limpeza Urbana BC Ltda,empresa_terceirizada,true,false,12.345.678/0001-90,Limpeza Urbana,Responsável pela coleta
UF002,Itajaí,Cooperativa de Catadores Vale Verde,entidade_catadores,true,true,98.765.432/0001-10,Cooperativa,Coleta seletiva
```

---

## ⚡ **Workflow Após Importação**

### **1. Verificar Importação:**
- Acesse a aba "Entidades Prioritárias UF"
- Verifique se todas as entidades aparecem com **badge vermelho "PRIORIDADE 1"**
- Confira se os dados estão corretos

### **2. Processar Entidades:**
```
Opção A: Processar individualmente
- Clique no botão "Processar" de cada entidade

Opção B: Processar todas de uma vez
- Clique no botão "Processar Todas" no topo da aba
```

### **3. Verificar Ativação:**
- Vá para a aba "Entidades Identificadas"
- As entidades processadas aparecerão lá como **ativas**
- Status mudará de "PENDENTE" para "PROCESSADA"

### **4. Acompanhar no Mapa:**
- Acesse `/mapa-progresso`
- Clique no botão "Modo Questionários"
- Municipios com entidades prioritárias terão alertas especiais

---

## 🎯 **Sistema de Prioridades**

### **Prioridade 1 (Vermelho):**
- 🔥 Entidades da lista oficial da UF
- **Mais obrigatórias de todas**
- Processamento imediato recomendado

### **Prioridade 2 (Amarelo):**
- 📋 Entidades identificadas durante visitas de campo
- Obrigatórias de segunda instância
- Processamento conforme identificação

---

## 🔍 **Validações Automáticas**

O sistema automaticamente valida:
- ✅ Códigos UF únicos
- ✅ Municípios válidos do PNSB
- ✅ Tipos de entidade corretos
- ✅ Formato de dados
- ✅ Campos obrigatórios

---

## 📞 **Suporte**

### **Em caso de erro:**
1. Verifique se o arquivo CSV está no formato correto
2. Confirme se todos os municípios estão escritos exatamente como na lista
3. Verifique se não há códigos UF duplicados
4. Certifique-se de que o servidor Flask está rodando

### **Logs de erro:**
- Verificar console do servidor Flask
- Logs são salvos automaticamente
- Detalhes de erro são exibidos na interface

---

## 🎉 **Após Importação Bem-Sucedida**

Você terá:
- ✅ Lista UF completamente importada
- ✅ Entidades marcadas como Prioridade 1
- ✅ Sistema pronto para acompanhamento
- ✅ Alertas automáticos no mapa de progresso
- ✅ Workflow de processamento ativo

**Próximos passos:**
1. Processar todas as entidades importadas
2. Definir obrigatoriedade MRS/MAP para cada uma
3. Iniciar acompanhamento via mapa de progresso
4. Usar sistema de alertas para follow-up