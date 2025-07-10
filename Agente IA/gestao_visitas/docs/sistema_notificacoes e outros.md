# Sistema de Notificações - PNSB 2024

## Visão Geral
O sistema de notificações foi projetado para manter os usuários informados sobre eventos importantes relacionados às visitas da PNSB 2024, incluindo visitas próximas, checklists pendentes, lembretes e alertas do sistema.

## Modelo de Dados

### Notificacao
```python
class Notificacao(db.Model):
    __tablename__ = 'notificacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)  # visita_proxima, lembrete, alerta, etc
    mensagem = db.Column(db.String(500), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    data_leitura = db.Column(db.DateTime, nullable=True)
    prioridade = db.Column(db.String(20), default='normal')  # baixa, normal, alta
    status = db.Column(db.String(20), default='não lida')  # não lida, lida, arquivada
    visita_id = db.Column(db.Integer, db.ForeignKey('visitas.id'), nullable=True)
```

## Tipos de Notificações

1. **Visitas Próximas**
   - Verificação automática de visitas nas próximas 24h
   - Prioridade: Alta
   - Exemplo: "Visita agendada para Bombinhas em 20/03/2024 às 10:00"

2. **Checklist Pendente**
   - Verificação de itens pendentes no checklist
   - Prioridade: Normal
   - Exemplo: "Checklist pendente para visita em Porto Belo"

3. **Lembretes Manuais**
   - Criados pelo usuário
   - Prioridade: Configurável
   - Exemplo: "Lembre-se de preparar o material para a visita"

4. **Alertas do Sistema**
   - Notificações automáticas do sistema
   - Prioridade: Alta
   - Exemplo: "Alerta: Checklist incompleto para visita em Bombinhas"

## Prioridades

- **Alta**: Visitas próximas, alertas críticos
- **Normal**: Checklists pendentes, lembretes gerais
- **Baixa**: Informações complementares

## Status

- **Não lida**: Notificação nova
- **Lida**: Notificação visualizada
- **Arquivada**: Notificação arquivada

## Serviço de Notificações

### NotificacaoService
```python
class NotificacaoService:
    def __init__(self):
        self.prioridades = {
            'visita_proxima': 'alta',
            'checklist_pendente': 'normal',
            'lembrete': 'normal',
            'alerta': 'alta'
        }
```

### Métodos Principais

1. **verificar_visitas_proximas()**
   - Verifica visitas nas próximas 24h
   - Cria notificações para visitas agendadas

2. **verificar_checklist_pendente()**
   - Verifica checklists pendentes
   - Cria notificações para itens não concluídos

3. **criar_lembrete(mensagem, visita_id, prioridade)**
   - Cria lembretes manuais
   - Permite vinculação a visitas específicas

4. **obter_notificacoes_nao_lidas()**
   - Retorna todas as notificações não lidas
   - Ordenadas por data de criação

5. **marcar_como_lida(notificacao_id)**
   - Marca uma notificação como lida
   - Registra data e hora da leitura

6. **arquivar_notificacao(notificacao_id)**
   - Arquivamento de notificações
   - Mantém histórico organizado

## API Endpoints

1. **GET /api/notificacoes**
   - Retorna todas as notificações não lidas
   - Ordenadas por data de criação

2. **POST /api/notificacoes/{id}/lida**
   - Marca uma notificação como lida
   - Retorna status da operação

3. **POST /api/notificacoes/{id}/arquivar**
   - Arquivamento de notificação
   - Retorna status da operação

4. **POST /api/notificacoes/lembrete**
   - Criação de novo lembrete
   - Requer mensagem e opcionalmente visita_id e prioridade

## Exemplos de Uso

### Verificar Notificações
```python
notificacoes = notificacao_service.obter_notificacoes_nao_lidas()
```

### Criar Lembrete
```python
notificacao_service.criar_lembrete(
    mensagem="Lembre-se de preparar o material para a visita",
    visita_id=123,
    prioridade="alta"
)
```

### Marcar como Lida
```python
notificacao_service.marcar_como_lida(notificacao_id)
```

### Arquivar Notificação
```python
notificacao_service.arquivar_notificacao(notificacao_id)
```

## Próximos Passos

1. **Implementação**
   - Criar modelo de dados
   - Implementar serviço de notificações
   - Adicionar endpoints da API
   - Implementar sistema de prioridades
   - Criar sistema de agendamento de notificações

2. **Integração**
   - Integrar com sistema de visitas
   - Adicionar verificações automáticas
   - Implementar interface de usuário
   - Integrar com sistema de checklist
   - Conectar com sistema de rotas

3. **Testes**
   - Testes unitários
   - Testes de integração
   - Testes de interface
   - Testes de performance
   - Testes de carga

4. **Documentação**
   - Documentar API
   - Criar manual do usuário
   - Documentar casos de uso
   - Criar guia de integração
   - Documentar fluxos de trabalho

5. **Melhorias Futuras**
   - Sistema de notificações por email
   - Notificações push no navegador
   - Sistema de templates de mensagens
   - Personalização de prioridades
   - Relatórios de notificações

6. **Segurança**
   - Implementar controle de acesso
   - Validar permissões
   - Proteger endpoints
   - Logs de atividades
   - Backup de dados

7. **Monitoramento**
   - Dashboard de notificações
   - Métricas de uso
   - Alertas de sistema
   - Monitoramento de performance
   - Logs de erros

8. **Manutenção**
   - Limpeza automática de notificações antigas
   - Otimização de consultas
   - Atualização de dependências
   - Backup regular
   - Documentação de mudanças 