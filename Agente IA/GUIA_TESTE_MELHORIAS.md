# 🧪 Guia de Teste das Melhorias Funcionais - Sistema PNSB

## 🚀 Como Testar Todas as Funcionalidades Implementadas

### 📋 **Pré-requisitos**

1. **Instale as dependências atualizadas:**
```bash
pip install -r requirements.txt
```

2. **Configure as variáveis de ambiente:**
```bash
# Configure suas chaves no arquivo .env
SECRET_KEY=sua_chave_secreta_aqui
GOOGLE_MAPS_API_KEY=sua_chave_google_maps
GOOGLE_GEMINI_API_KEY=sua_chave_google_gemini
```

3. **Execute a aplicação:**
```bash
# Versão nova com todas as melhorias
python app_new.py

# OU versão original (compatibilidade)
python app.py
```

---

## 🎯 **Teste 1: Dashboard Avançado**

### **Endpoint Principal:**
```http
GET /api/melhorias/dashboard/principal
```

### **Teste via cURL:**
```bash
curl -X GET "http://127.0.0.1:5000/api/melhorias/dashboard/principal" \
  -H "Content-Type: application/json"
```

### **O que esperar:**
```json
{
  "success": true,
  "data": {
    "kpis_principais": {
      "total_visitas_mes": {"valor": 15, "variacao": 25.0},
      "taxa_sucesso": {"valor": 87.5, "status": "acima"},
      "cobertura_municipios": {"valor": 72.7, "municipios_visitados": 8}
    },
    "status_tempo_real": {
      "visitas_agendadas_hoje": 2,
      "em_andamento": 1,
      "concluidas_hoje": 3
    },
    "insights_automaticos": [
      {
        "tipo": "positivo",
        "titulo": "Excelente Taxa de Sucesso",
        "descricao": "Taxa de sucesso de 87.5% está acima da meta"
      }
    ]
  }
}
```

---

## 🎯 **Teste 2: Agendamento Inteligente**

### **Sugerir Horários Disponíveis:**
```http
POST /api/melhorias/agendamento/sugerir-horarios
```

### **Teste via cURL:**
```bash
curl -X POST "http://127.0.0.1:5000/api/melhorias/agendamento/sugerir-horarios" \
  -H "Content-Type: application/json" \
  -d '{
    "municipio": "Itajaí",
    "data": "2024-02-15",
    "duracao_minutos": 90
  }'
```

### **Otimizar Rota Diária:**
```bash
curl -X POST "http://127.0.0.1:5000/api/melhorias/agendamento/otimizar-rota" \
  -H "Content-Type: application/json" \
  -d '{
    "data": "2024-02-15",
    "origem": "Itajaí"
  }'
```

### **Detectar Conflitos:**
```bash
curl -X POST "http://127.0.0.1:5000/api/melhorias/agendamento/detectar-conflitos" \
  -H "Content-Type: application/json" \
  -d '{
    "municipio": "Itajaí",
    "data": "2024-02-15",
    "hora_inicio": "09:00",
    "hora_fim": "10:00"
  }'
```

---

## 🎯 **Teste 3: Checklist Inteligente**

### **Criar Visita de Teste:**
```bash
# Primeiro, crie uma visita para testar
curl -X POST "http://127.0.0.1:5000/api/visitas" \
  -H "Content-Type: application/json" \
  -d '{
    "municipio": "Navegantes",
    "data": "2024-02-20",
    "hora_inicio": "14:00",
    "hora_fim": "15:00",
    "informante": "João Silva",
    "tipo_pesquisa": "MRS",
    "observacoes": "Teste de checklist inteligente"
  }'
```

### **Obter Checklist Personalizado:**
```bash
# Use o ID da visita criada (ex: 1)
curl -X GET "http://127.0.0.1:5000/api/melhorias/checklist/personalizado/1"
```

### **Validar Completude:**
```bash
curl -X GET "http://127.0.0.1:5000/api/melhorias/checklist/validar-completude/1"
```

### **Sugerir Próximo Passo:**
```bash
curl -X GET "http://127.0.0.1:5000/api/melhorias/checklist/proximo-passo/1"
```

---

## 🎯 **Teste 4: Contatos Inteligente**

### **Enriquecer Contato:**
```bash
curl -X POST "http://127.0.0.1:5000/api/melhorias/contatos/enriquecer" \
  -H "Content-Type: application/json" \
  -d '{
    "municipio": "Bombinhas",
    "tipo_pesquisa": "MRS"
  }'
```

### **Detectar Duplicados:**
```bash
curl -X GET "http://127.0.0.1:5000/api/melhorias/contatos/detectar-duplicados?municipio=Itajaí"
```

### **Relatório de Qualidade:**
```bash
curl -X GET "http://127.0.0.1:5000/api/melhorias/contatos/relatorio-qualidade"
```

---

## 🎯 **Teste 5: Relatórios Avançados**

### **Relatório Executivo:**
```bash
curl -X POST "http://127.0.0.1:5000/api/melhorias/relatorios/executivo" \
  -H "Content-Type: application/json" \
  -d '{
    "periodo_inicio": "2024-01-01",
    "periodo_fim": "2024-01-31"
  }'
```

### **Relatório de Qualidade:**
```bash
curl -X POST "http://127.0.0.1:5000/api/melhorias/relatorios/qualidade" \
  -H "Content-Type: application/json" \
  -d '{
    "periodo_inicio": "2024-01-01",
    "periodo_fim": "2024-01-31"
  }'
```

### **Análise de Tendências:**
```bash
curl -X GET "http://127.0.0.1:5000/api/melhorias/relatorios/tendencias?meses=3"
```

---

## 🎯 **Teste 6: Notificações e Alertas**

### **Configurar Notificações:**
```bash
curl -X POST "http://127.0.0.1:5000/api/melhorias/notificacoes/configurar" \
  -H "Content-Type: application/json" \
  -d '{
    "usuario_id": "teste123",
    "configuracoes": {
      "canais_preferidos": ["email", "sistema"],
      "horario_nao_perturbar": {"inicio": "22:00", "fim": "06:00"},
      "email": "teste@email.com"
    }
  }'
```

### **Verificar Alertas:**
```bash
curl -X GET "http://127.0.0.1:5000/api/melhorias/notificacoes/verificar-alertas"
```

### **Gerar Lembretes:**
```bash
curl -X GET "http://127.0.0.1:5000/api/melhorias/notificacoes/lembretes"
```

### **Resumo Diário:**
```bash
curl -X GET "http://127.0.0.1:5000/api/melhorias/notificacoes/resumo-diario?data=2024-02-15"
```

---

## 🎯 **Teste 7: Status das Melhorias**

### **Verificar Status Geral:**
```bash
curl -X GET "http://127.0.0.1:5000/api/melhorias/status/melhorias"
```

### **Demonstração de Funcionalidades:**
```bash
curl -X GET "http://127.0.0.1:5000/api/melhorias/demo/funcionalidades"
```

---

## 🧪 **Testando via Interface Web**

### **1. Acesse o sistema:**
```
http://127.0.0.1:5000
```

### **2. Use o Console do Navegador:**
```javascript
// Teste do Dashboard
fetch('/api/melhorias/dashboard/principal')
  .then(response => response.json())
  .then(data => console.log('Dashboard:', data));

// Teste de Sugestão de Horários
fetch('/api/melhorias/agendamento/sugerir-horarios', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    municipio: 'Itajaí',
    data: '2024-02-20',
    duracao_minutos: 60
  })
}).then(response => response.json())
  .then(data => console.log('Horários:', data));

// Teste de Alertas
fetch('/api/melhorias/notificacoes/verificar-alertas')
  .then(response => response.json())
  .then(data => console.log('Alertas:', data));
```

---

## 📊 **Teste com Dados Reais**

### **1. Crie dados de teste:**
```bash
# Criar múltiplas visitas para testar
for i in {1..5}; do
  curl -X POST "http://127.0.0.1:5000/api/visitas" \
    -H "Content-Type: application/json" \
    -d "{
      \"municipio\": \"Municipio$i\",
      \"data\": \"2024-02-$(printf %02d $((15+i)))\",
      \"hora_inicio\": \"$(printf %02d $((9+i))):00\",
      \"hora_fim\": \"$(printf %02d $((10+i))):00\",
      \"informante\": \"Informante $i\",
      \"tipo_pesquisa\": \"MRS\",
      \"observacoes\": \"Visita teste $i\"
    }"
done
```

### **2. Teste funcionalidades com dados:**
```bash
# Depois de criar as visitas, teste:
curl -X GET "http://127.0.0.1:5000/api/melhorias/dashboard/principal"
curl -X GET "http://127.0.0.1:5000/api/melhorias/relatorios/tendencias"
curl -X GET "http://127.0.0.1:5000/api/melhorias/notificacoes/verificar-alertas"
```

---

## 🔍 **Verificação de Resultados**

### **Indicadores de Sucesso:**

1. **Dashboard carrega com métricas reais ✅**
2. **Sugestões de horário são inteligentes ✅**
3. **Checklists se adaptam ao contexto ✅**
4. **Contatos são enriquecidos automaticamente ✅**
5. **Relatórios mostram insights úteis ✅**
6. **Alertas detectam problemas reais ✅**

### **Performance Esperada:**
- ⚡ Respostas < 2 segundos
- 🎯 Dados precisos e atualizados
- 💡 Insights relevantes e acionáveis
- 🔔 Alertas oportunos e úteis

---

## 🐛 **Troubleshooting**

### **Problemas Comuns:**

**1. Erro de API Keys:**
```bash
# Verifique se as chaves estão configuradas
grep -E "(GOOGLE_MAPS|GOOGLE_GEMINI)" .env
```

**2. Erro de Dependências:**
```bash
# Reinstale dependências
pip install --upgrade -r requirements.txt
```

**3. Erro de Banco:**
```bash
# Recrie o banco se necessário
rm gestao_visitas/gestao_visitas.db
python app_new.py  # Recria automaticamente
```

**4. Teste de Conectividade:**
```bash
# Verifique se a aplicação está rodando
curl -X GET "http://127.0.0.1:5000/api/melhorias/status/melhorias"
```

---

## 📈 **Métricas de Teste**

### **Após completar todos os testes, você deve ver:**

1. **Dashboard funcional** com métricas em tempo real
2. **Sugestões inteligentes** de agendamento
3. **Alertas automáticos** para problemas detectados
4. **Relatórios ricos** com insights
5. **Qualidade melhorada** dos dados

### **Logs de Sucesso:**
```
✅ Dashboard principal carregado
✅ Agendamento inteligente ativo
✅ Checklist personalizado gerado
✅ Contatos enriquecidos
✅ Relatórios executivos criados
✅ Sistema de alertas funcionando
```

---

## 🎉 **Próximos Passos**

Após validar que todas as funcionalidades estão funcionando:

1. **Configure usuários reais** com suas preferências
2. **Importe dados históricos** para análises mais ricas
3. **Configure alertas específicos** para sua operação
4. **Treine a equipe** nas novas funcionalidades
5. **Monitore métricas** de adoção e eficiência

---

**🚀 Status:** Todas as funcionalidades prontas para uso!
**📞 Suporte:** Documentação completa nos arquivos de código