# 🗺️ CONFIGURAÇÃO GOOGLE MAPS - PASSOS PRÁTICOS

## 🚀 EXECUTE ESTES PASSOS NA ORDEM:

### **PASSO 1: Criar Projeto Google Cloud**
1. **Abra**: https://console.cloud.google.com/
2. **Faça login** com sua conta Google
3. **Clique** no dropdown do projeto (canto superior esquerdo)
4. **Clique** em "NOVO PROJETO"
5. **Nome**: `PNSB-2024-Gestao-Visitas`
6. **Clique** em "CRIAR"
7. **Aguarde** e selecione o projeto criado

### **PASSO 2: Ativar APIs (MUITO IMPORTANTE)**
1. **Vá** em "APIs e serviços" > "Biblioteca"
2. **Ative UMA POR VEZ** estas APIs:

   **a) Maps JavaScript API**
   - Digite "Maps JavaScript API" na busca
   - Clique na API
   - Clique "ATIVAR"
   
   **b) Geocoding API**
   - Digite "Geocoding API" na busca
   - Clique na API
   - Clique "ATIVAR"
   
   **c) Directions API**
   - Digite "Directions API" na busca
   - Clique na API
   - Clique "ATIVAR"
   
   **d) Distance Matrix API**
   - Digite "Distance Matrix API" na busca
   - Clique na API
   - Clique "ATIVAR"

### **PASSO 3: Configurar Faturamento**
⚠️ **OBRIGATÓRIO mesmo sendo gratuito até certa cota**

1. **Vá** em "Faturamento" no menu lateral
2. **Clique** "VINCULAR CONTA DE FATURAMENTO"
3. **Crie** nova conta:
   - Nome: `PNSB-Faturamento`
   - País: Brasil
   - Moeda: Real (BRL)
4. **Adicione** cartão de crédito (necessário)
5. **Vincule** ao projeto

### **PASSO 4: Criar Chave de API**
1. **Vá** em "APIs e serviços" > "Credenciais"
2. **Clique** "+ CRIAR CREDENCIAIS"
3. **Selecione** "Chave de API"
4. **COPIE** a chave gerada (ex: AIzaSyC7Xx...)
5. **Guarde** esta chave em local seguro!

### **PASSO 5: Configurar Restrições**
1. **Clique** na chave criada para editá-la
2. **Em "Restrições da aplicação"**:
   - Selecione "Referenciadores HTTP (sites)"
   - Adicione: `http://localhost:8080/*`
   - Adicione: `http://127.0.0.1:8080/*`

3. **Em "Restrições de API"**:
   - Selecione "Restringir chave"
   - Marque TODAS as APIs que ativou:
     ✅ Maps JavaScript API
     ✅ Geocoding API  
     ✅ Directions API
     ✅ Distance Matrix API

4. **Clique** "SALVAR"

### **PASSO 6: Testar a Chave**
Abra esta URL no navegador (substitua SUA_CHAVE):
```
https://maps.googleapis.com/maps/api/geocode/json?address=Itajaí,SC,Brasil&key=SUA_CHAVE_AQUI
```

**Se funcionar**, você verá algo como:
```json
{
  "results": [...],
  "status": "OK"
}
```

## 🔧 CONFIGURAR NO PROJETO

### **MÉTODO 1: Manual**
1. Abra o arquivo `.env`
2. Substitua esta linha:
   ```
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
   ```
   Por:
   ```
   GOOGLE_MAPS_API_KEY=SUA_CHAVE_AQUI
   ```
3. Salve o arquivo
4. Reinicie o Flask

### **MÉTODO 2: Script Automático (Windows)**
```powershell
# No PowerShell
python configure_google_maps.py
# Cole sua chave quando solicitado
```

## ✅ VERIFICAR SE FUNCIONOU

1. **Reinicie** o Flask: `Ctrl+C` e `python app.py`
2. **Verifique** os logs - não deve mais aparecer:
   ```
   ⚠️ ATENÇÃO: Google Maps API Key não configurada!
   ```
3. **Teste** em: http://localhost:8080/mapa-progresso
4. **Teste rotas** em: http://localhost:8080/visitas

## 💰 CUSTOS (Tranquilo!)

**COTA GRATUITA MENSAL:**
- Maps JavaScript: 28.500 carregamentos
- Geocoding: 40.000 consultas  
- Directions: 40.000 consultas
- Distance Matrix: 40.000 consultas

**Para este projeto**: A cota gratuita é MAIS que suficiente!

## 🚨 SEGURANÇA

✅ **SEMPRE configure restrições de domínio**
❌ **NUNCA compartilhe sua chave publicamente**  
📊 **Configure alertas de cota no Google Cloud**

---

## 🆘 PRECISA DE AJUDA?

Se encontrar problemas, execute:
```bash
python configure_google_maps.py
```

O script vai detectar e ajudar a resolver!