# 🔧 CORREÇÃO DAS CHAVES DE API

## ❌ PROBLEMAS ENCONTRADOS:

### 1. Google Maps API
**Erro**: `API keys with referer restrictions cannot be used with this API`
**Causa**: Restrições de referenciador muito específicas

### 2. Google Gemini API  
**Erro**: `models/gemini-pro is not found`
**Causa**: API não ativada ou modelo incorreto

## ✅ SOLUÇÕES:

### PASSO 1: Corrigir Google Maps
1. **Vá para**: https://console.cloud.google.com/apis/credentials
2. **Clique** na sua chave do Google Maps
3. **Em "Restrições da aplicação"**:
   - Selecione **"Nenhum"** (temporariamente)
   - OU mantenha "Referenciadores HTTP" e adicione: `*`
4. **Clique** "SALVAR"
5. **Aguarde** 2-3 minutos

### PASSO 2: Corrigir Google Gemini
1. **Vá para**: https://console.cloud.google.com/apis/library
2. **Busque**: "Generative Language API"
3. **Clique** na API e clique "ATIVAR"
4. **Aguarde** alguns minutos

### PASSO 3: Testar Novamente
```bash
python test_api_keys.py
```

## 🎯 RESULTADO ESPERADO:
```
🗺️ Google Maps API: ✅ OK
🤖 Google Gemini API: ✅ OK  
🐍 Integração Flask: ✅ OK

🎉 TODAS AS CHAVES FUNCIONANDO!
```

## 🔒 REATIVAR SEGURANÇA DEPOIS:
Após confirmar que funciona, reative as restrições:
1. Volte nas configurações da chave do Google Maps
2. Reative "Referenciadores HTTP" 
3. Use: `http://localhost:8080/*` e `http://127.0.0.1:8080/*`