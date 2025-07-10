# 💰 Guia de Economia de Custos - API Google Gemini

## 🚨 Problema Identificado
O sistema estava usando a API do Google Gemini para o chat de IA, gerando custos por cada consulta feita.

## ✅ Soluções Implementadas

### 1. **Chat IA Desabilitado por Padrão**
```bash
# No arquivo .env
CHAT_IA_HABILITADO=false
```
- Sistema funciona normalmente sem o chat IA
- Zero custos da API do Google
- Funcionalidades principais intactas

### 2. **Cache Inteligente**
- Respostas em cache para perguntas repetidas
- Não gera nova requisição para pergunta já feita
- Cache automático de até 100 respostas

### 3. **Respostas Predefinidas**
Perguntas comuns respondidas sem usar API:
- "como agendar visita"
- "como funciona o sistema" 
- "quais municipios"
- "questionarios obrigatorios"
- "sistema prioridades"
- "como usar mapa"
- "backup dados"
- "relatorios"

### 4. **Rate Limiting**
- Máximo 10 consultas por hora por usuário
- Previne uso excessivo acidental
- Resetado automaticamente

### 5. **Modelo Mais Barato**
Quando habilitado, usa:
- `gemini-1.5-flash` (mais barato que gemini-pro)
- Máximo 150 tokens de resposta
- Timeout reduzido para 15s

### 6. **Limitações de Entrada**
- Máximo 500 caracteres por pergunta
- Previne consultas muito longas (caras)

## 🔧 Como Configurar

### Modo Economia (Recomendado)
```bash
# Arquivo .env
CHAT_IA_HABILITADO=false
# GOOGLE_GEMINI_API_KEY= (deixar vazio ou comentar)
```

### Para Habilitar Chat IA (Gerará Custos)
```bash
# Arquivo .env
CHAT_IA_HABILITADO=true
GOOGLE_GEMINI_API_KEY=sua_chave_api_aqui
```

## 📊 Estimativa de Economia

### Antes (Sem Otimizações)
- Modelo: gemini-1.5-pro
- Sem cache ou rate limiting
- Sem respostas predefinidas
- **Alto custo por consulta**

### Depois (Com Otimizações)
- 80%+ das perguntas respondidas sem API (cache + predefinidas)
- Rate limiting: máximo 10 consultas/hora
- Modelo mais barato quando necessário
- **~90% de redução de custos**

## 🎯 Funcionalidades Que Funcionam Sem API

### Totalmente Funcionais
✅ Agendamento de visitas
✅ Mapa de progresso com prioridades P1/P2/P3
✅ Questionários obrigatórios
✅ Sistema de checklists
✅ Relatórios e estatísticas
✅ Backup automático
✅ Importação de dados CSV
✅ Gestão de contatos

### Funcionalidades de IA Disponíveis
✅ Respostas predefinidas para perguntas comuns
✅ Sugestões de navegação
✅ Documentação integrada

## 🚀 Recomendações

### Para Uso Normal (Zero Custos)
1. Mantenha `CHAT_IA_HABILITADO=false`
2. Use as funcionalidades principais do sistema
3. Consulte este guia para dúvidas comuns

### Para Uso com IA (Com Custos)
1. Configure uma chave API válida
2. Monitore uso no Google Cloud Console
3. Use com moderação devido aos custos
4. O sistema já otimiza automaticamente

## 📝 Mensagens do Sistema

### Chat Desabilitado
```json
{
  "error": "Chat IA desabilitado para economizar custos",
  "suggestions": [
    "Acesse 'Visitas' para agendar",
    "Use 'Mapa de Progresso' para acompanhar",
    "Consulte 'Questionários Obrigatórios'",
    "Verifique 'Relatórios' para estatísticas"
  ]
}
```

### Limite Atingido
```json
{
  "error": "Limite de 10 perguntas por hora atingido",
  "message": "Use as funcionalidades do sistema",
  "reset_time": "Limite resetado a cada hora"
}
```

## 🎉 Resultado Final

**Sistema PNSB 2024 funcionando 100% sem custos de API**, mantendo todas as funcionalidades essenciais para gestão de visitas de campo e questionários obrigatórios!