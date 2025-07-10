# 🗺️ CONFIGURAÇÃO GOOGLE MAPS API - GUIA COMPLETO

## PASSO 1: Criar Conta Google Cloud Console

### 1.1 Acessar Google Cloud Console
- Vá para: https://console.cloud.google.com/
- Faça login com sua conta Google
- Se for primeira vez, aceite os termos de serviço

### 1.2 Criar Novo Projeto
1. Clique no dropdown do projeto (canto superior esquerdo)
2. Clique em "NOVO PROJETO"
3. Nome do projeto: `PNSB-2024-Gestao-Visitas`
4. Clique em "CRIAR"
5. Aguarde alguns segundos e selecione o projeto criado

## PASSO 2: Ativar APIs Necessárias

### 2.1 Navegar para APIs & Serviços
1. No menu lateral, clique em "APIs e serviços"
2. Clique em "Biblioteca"

### 2.2 Ativar APIs Específicas (IMPORTANTE)
Ative TODAS essas APIs (uma por vez):

**APIs OBRIGATÓRIAS:**
1. **Maps JavaScript API** - Para mapas interativos
2. **Geocoding API** - Para converter endereços em coordenadas
3. **Directions API** - Para calcular rotas
4. **Distance Matrix API** - Para calcular distâncias
5. **Places API** - Para buscar locais (opcional)

**Como ativar cada API:**
1. Digite o nome da API na busca
2. Clique na API
3. Clique em "ATIVAR"
4. Repita para todas as 4-5 APIs listadas acima

## PASSO 3: Criar Chave de API

### 3.1 Criar Credencial
1. Vá em "APIs e serviços" > "Credenciais"
2. Clique em "+ CRIAR CREDENCIAIS"
3. Selecione "Chave de API"
4. Uma chave será gerada (algo como: `AIzaSyC7Xx...`)
5. **COPIE ESTA CHAVE IMEDIATAMENTE**

### 3.2 Configurar Restrições de Segurança
1. Clique na chave criada para editá-la
2. Em "Restrições da aplicação":
   - Selecione "Referenciadores HTTP (sites)"
   - Adicione: `http://localhost:8080/*`
   - Adicione: `http://127.0.0.1:8080/*`
   - Se tiver domínio: `https://seudominio.com/*`

3. Em "Restrições de API":
   - Selecione "Restringir chave"
   - Marque TODAS as APIs que ativou:
     ✅ Maps JavaScript API
     ✅ Geocoding API  
     ✅ Directions API
     ✅ Distance Matrix API
     ✅ Places API (se ativou)

4. Clique em "SALVAR"

## PASSO 4: Configurar Faturamento

### 4.1 Ativar Faturamento (OBRIGATÓRIO)
⚠️ **IMPORTANTE**: Google Maps API requer cartão de crédito, mas tem cota gratuita generosa

1. No menu lateral, clique em "Faturamento"
2. Clique em "VINCULAR CONTA DE FATURAMENTO"
3. Criar nova conta de faturamento:
   - Nome: `PNSB-Faturamento`
   - País: Brasil
   - Moeda: Real (BRL)
4. Adicione cartão de crédito (necessário mesmo com cota gratuita)
5. Vincule ao projeto

### 4.2 Configurar Alertas de Cota
1. Vá em "APIs e serviços" > "Cotas"
2. Para cada API, configure limite diário baixo:
   - Maps JavaScript API: 1.000 carregamentos/dia
   - Geocoding API: 100 consultas/dia
   - Directions API: 100 consultas/dia
   - Distance Matrix API: 100 consultas/dia

## PASSO 5: Testar a Chave

### 5.1 Teste Básico no Navegador
Abra esta URL no navegador (substitua SUA_CHAVE):
```
https://maps.googleapis.com/maps/api/geocode/json?address=Itajaí,SC,Brasil&key=SUA_CHAVE_AQUI
```

**Resposta esperada:**
```json
{
  "results": [...],
  "status": "OK"
}
```

## COTA GRATUITA MENSAL (2024)

| API | Cota Gratuita | Valor Após Cota |
|-----|---------------|-----------------|
| Maps JavaScript | 28.500 carregamentos | $7,00/1000 |
| Geocoding | 40.000 consultas | $5,00/1000 |
| Directions | 40.000 consultas | $5,00/1000 |
| Distance Matrix | 40.000 consultas | $5,00/1000 |

**Para o projeto PNSB**: A cota gratuita é mais que suficiente para desenvolvimento e uso normal.

## PRÓXIMOS PASSOS

Após obter sua chave de API:
1. ✅ Configure no arquivo .env do projeto
2. ✅ Reinicie o Flask
3. ✅ Teste as funcionalidades de mapa
4. ✅ Configure monitoramento de uso

---

**🚨 SEGURANÇA**: Nunca compartilhe sua chave de API publicamente!
**💡 DICA**: Use sempre restrições de domínio em produção!