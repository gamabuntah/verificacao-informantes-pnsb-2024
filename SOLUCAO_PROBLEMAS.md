# 🔧 SOLUÇÃO DE PROBLEMAS - SISTEMA PNSB 2024

## ❌ Erro: `ModuleNotFoundError: No module named 'pdfplumber'`

### 🎯 **Solução Rápida:**
Execute o instalador completo:
```bash
instalar_dependencias_completas.bat
```

### 🔍 **Diagnóstico:**
O sistema está tentando importar a biblioteca `pdfplumber` que não está instalada.

### 🛠️ **Soluções:**

#### **Opção 1: Instalar manualmente**
```bash
# Ativar ambiente virtual
.venv\Scripts\activate

# Instalar pdfplumber
pip install pdfplumber==0.9.0
```

#### **Opção 2: Atualizar requirements.txt**
O arquivo `requirements.txt` já foi atualizado com todas as dependências necessárias:
```bash
pip install -r requirements.txt
```

#### **Opção 3: Desabilitar funcionalidades de PDF**
Se não conseguir instalar o `pdfplumber`, o sistema funcionará normalmente com funcionalidades de PDF limitadas.

---

## ❌ Erro: `ModuleNotFoundError: No module named 'flask_compress'`

### 🛠️ **Solução:**
```bash
pip install flask-compress==1.14
```

**OU** o sistema funcionará sem compressão (performance ligeiramente reduzida).

---

## ❌ Erro: `ModuleNotFoundError: No module named 'geopy'`

### 🛠️ **Solução:**
```bash
pip install geopy==2.4.1
```

**OU** o sistema usará cálculos de distância aproximados.

---

## ❌ Erro: `Redis não disponível`

### 🛠️ **Solução:**
```bash
pip install redis==5.0.1
```

**OU** o sistema usará o simulador de cache Redis (funcional).

---

## 🚀 **Instalação Completa Garantida**

### **Execute este comando para instalar TUDO:**

```bash
instalar_dependencias_completas.bat
```

Este script:
- ✅ Cria/ativa ambiente virtual
- ✅ Instala todas as dependências obrigatórias
- ✅ Instala dependências opcionais (com fallback)
- ✅ Verifica a instalação
- ✅ Mostra o status de cada biblioteca

---

## 📋 **Dependências do Sistema:**

### **Obrigatórias (Sistema não funciona sem):**
- `flask==3.0.2`
- `flask-sqlalchemy==3.1.1`
- `pandas==2.3.0`
- `requests==2.31.0`

### **Opcionais (Sistema funciona com funcionalidades reduzidas):**
- `pdfplumber==0.9.0` - Processamento de PDFs
- `flask-compress==1.14` - Compressão HTTP
- `geopy==2.4.1` - Cálculos de distância precisos
- `redis==5.0.1` - Cache avançado

---

## 🔍 **Verificar Instalação:**

Execute este código Python para verificar:

```python
# Verificar dependências principais
try:
    import flask, flask_sqlalchemy, pandas, requests
    print("✅ Dependências principais: OK")
except ImportError as e:
    print(f"❌ Erro: {e}")

# Verificar dependências opcionais
libs = ['pdfplumber', 'flask_compress', 'geopy', 'redis']
for lib in libs:
    try:
        __import__(lib)
        print(f"✅ {lib}: OK")
    except ImportError:
        print(f"⚠️ {lib}: NÃO INSTALADO (opcional)")
```

---

## 📞 **Se o problema persistir:**

1. **Excluir ambiente virtual e recriar:**
   ```bash
   rmdir /s .venv
   instalar_dependencias_completas.bat
   ```

2. **Verificar versão do Python:**
   ```bash
   python --version
   # Deve ser Python 3.8+ 
   ```

3. **Executar modo de diagnóstico:**
   ```bash
   python -c "import sys; print(sys.path)"
   ```

---

## ✅ **Status das Funcionalidades:**

| Biblioteca | Status | Funcionalidade Afetada |
|------------|--------|-------------------------|
| pdfplumber | ⚠️ Opcional | Processamento de documentos PDF |
| flask-compress | ⚠️ Opcional | Compressão de páginas web |
| geopy | ⚠️ Opcional | Cálculos de distância precisos |
| redis | ⚠️ Opcional | Cache de alta performance |

**IMPORTANTE:** O sistema PNSB 2024 funcionará perfeitamente mesmo sem as bibliotecas opcionais!