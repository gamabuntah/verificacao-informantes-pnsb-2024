# 📱 Configuração WhatsApp Business API - PNSB 2024

## Visão Geral

A integração com WhatsApp Business permite envio automático de:
- **Agendamentos de visitas**
- **Lembretes 24h antes**
- **Confirmações de reagendamento**
- **Follow-ups pós-visita**
- **Mensagens em lote**

## 🔧 Configuração Inicial

### 1. Criar App no Facebook Developers

1. Acesse: https://developers.facebook.com/
2. Crie uma nova aplicação
3. Adicione o produto "WhatsApp Business"
4. Configure o webhook apontando para: `https://seu-dominio.com/api/whatsapp/webhook`

### 2. Variáveis de Ambiente Obrigatórias

Adicione no arquivo `.env` ou configure no sistema:

```bash
# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=seu_access_token_aqui
WHATSAPP_PHONE_NUMBER_ID=seu_phone_number_id_aqui
WHATSAPP_BUSINESS_ACCOUNT_ID=seu_business_account_id_aqui
WHATSAPP_WEBHOOK_VERIFY_TOKEN=token_secreto_para_webhook
```

### 3. Como Obter as Credenciais

#### Access Token:
- Vá em: App Dashboard → WhatsApp → API Setup
- Copie o "Temporary access token"
- Para produção, gere um token permanente

#### Phone Number ID:
- Na mesma tela de API Setup
- Copie o "Phone number ID" do número WhatsApp Business

#### Business Account ID:
- Em WhatsApp → Getting Started
- Copie o "WhatsApp Business Account ID"

#### Webhook Verify Token:
- Crie um token secreto qualquer (ex: `pnsb_webhook_2024_secret`)
- Use este mesmo token na configuração do webhook no Facebook

## 📋 Templates de Mensagem

### Templates Pré-configurados:

1. **agendamento_inicial** - Primeira mensagem de agendamento
2. **confirmacao_agendamento** - Confirmação após aceite
3. **lembrete_visita** - Lembrete 24h antes
4. **followup_pos_visita** - Acompanhamento após visita
5. **reagendamento** - Nova data de agendamento

### Aprovação de Templates:

⚠️ **Importante**: Templates precisam ser aprovados pelo Facebook antes do uso em produção.

Para aprovar templates:
1. Acesse Meta Business Manager
2. Vá em WhatsApp Manager → Message Templates
3. Submeta cada template para aprovação
4. Aguarde aprovação (pode levar até 24h)

## 🚀 Como Usar

### 1. Interface Web

Acesse `/whatsapp` no sistema para:
- ✅ Verificar status da configuração
- 📤 Enviar mensagens individuais
- 📦 Envio em lote para múltiplas visitas
- 📊 Ver estatísticas de uso
- 🧪 Testar conexão

### 2. Automático

O sistema envia automaticamente quando:
- ✅ Nova visita é agendada (se telefone fornecido)
- ⏰ 24h antes da visita (agendamento automático)
- 🔄 Status da visita é atualizado

### 3. Via API

Endpoints disponíveis:

```bash
# Verificar configuração
GET /api/whatsapp/config/status

# Enviar template específico
POST /api/whatsapp/send/template
{
  "telefone": "+5511999999999",
  "template": "agendamento_inicial",
  "variaveis": {...},
  "visita_id": 123
}

# Enviar agendamento para visita
POST /api/whatsapp/send/agendamento/123
{
  "telefone": "+5511999999999"
}

# Enviar em lote
POST /api/whatsapp/send/bulk/agendamentos
{
  "visita_ids": [1, 2, 3],
  "telefones": {"1": "+5511111111", "2": "+5511222222"}
}
```

## 🔒 Segurança

### Boas Práticas:

1. **Nunca commitee credenciais** no código
2. **Use HTTPS** para webhooks
3. **Valide tokens** de webhook
4. **Rate limiting** para envios
5. **Log de auditoria** para todas as mensagens

### Validações Implementadas:

- ✅ Formato de telefone brasileiro
- ✅ Validação de templates
- ✅ Verificação de variáveis obrigatórias
- ✅ Fallback gracioso se API indisponível
- ✅ Log de todas as tentativas de envio

## 📊 Monitoramento

### Métricas Disponíveis:

- **Taxa de entrega**: % de mensagens entregues
- **Taxa de leitura**: % de mensagens visualizadas
- **Taxa de resposta**: % que responderam
- **Horários de maior engajamento**
- **Templates mais eficazes**

### Logs e Auditoria:

Todas as mensagens são registradas com:
- Timestamp do envio
- ID da mensagem no WhatsApp
- Status de entrega/leitura
- Visita associada
- Template utilizado

## 🚨 Troubleshooting

### Problemas Comuns:

#### "Invalid API key provided"
- ✅ Verifique se `WHATSAPP_ACCESS_TOKEN` está correto
- ✅ Token não expirou
- ✅ App tem permissões de WhatsApp Business

#### "Template not found"
- ✅ Template foi aprovado pelo Facebook
- ✅ Nome do template está correto
- ✅ Idioma configurado como `pt_BR`

#### "Invalid phone number"
- ✅ Formato: +5511999999999
- ✅ Número registrado no WhatsApp
- ✅ Não está em lista de bloqueio

#### Webhook não funciona
- ✅ URL pública acessível via HTTPS
- ✅ Token de verificação correto
- ✅ Endpoint `/api/whatsapp/webhook` respondendo

### Debug Mode:

Para debug, verifique logs:
```bash
# Ver status detalhado
curl http://localhost:8080/api/whatsapp/config/status

# Testar conexão
curl -X POST http://localhost:8080/api/whatsapp/test/connection \
  -H "Content-Type: application/json" \
  -d '{"telefone_teste": "+5511999999999"}'
```

## 📈 Roadmap Futuro

### Funcionalidades Planejadas:

- 🤖 **Chatbot básico** para respostas automáticas
- 📅 **Integração com calendário** para reagendamentos
- 📊 **Analytics avançado** de engajamento
- 🔔 **Notificações push** para equipe
- 📋 **Templates dinâmicos** baseados no perfil
- 🎯 **Segmentação automática** de mensagens

## 💡 Dicas de Uso

### Para Melhores Resultados:

1. **Personalize mensagens** com nome do informante
2. **Envie em horários comerciais** (9h-17h)
3. **Use linguagem formal** mas amigável
4. **Inclua informações de contato** do pesquisador
5. **Mantenha mensagens concisas** e objetivas
6. **Teste templates** antes de usar em produção

### Compliance LGPD:

- ✅ Obtenha consentimento para uso de WhatsApp
- ✅ Informe sobre coleta de dados
- ✅ Permita opt-out a qualquer momento
- ✅ Mantenha logs por período limitado
- ✅ Não compartilhe dados com terceiros

---

**🔗 Links Úteis:**
- [WhatsApp Business API Docs](https://developers.facebook.com/docs/whatsapp)
- [Message Templates Guide](https://developers.facebook.com/docs/whatsapp/message-templates)
- [Webhook Setup](https://developers.facebook.com/docs/whatsapp/webhooks)

**📞 Suporte:**
- Para dúvidas técnicas, consulte a documentação do Facebook Developers
- Para problemas no sistema PNSB, verifique logs em `/api/whatsapp/config/status`