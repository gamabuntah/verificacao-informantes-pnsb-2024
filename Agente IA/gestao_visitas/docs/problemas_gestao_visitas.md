# Problemas e Soluções - Sistema de Gestão de Visitas PNSB 2024

## 1. Problemas de Configuração

### Problemas Identificados
- Chave da API do Google Maps exposta no código
- Tratamento inadequado quando a chave da API não está disponível
- Falta de configuração centralizada

### Soluções Propostas
```python
# app.py
# Remover chave hardcoded
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    print("AVISO: Google API Key não configurada")
    GOOGLE_API_KEY = None

# Melhor tratamento de erros
@app.route('/api/rota', methods=['POST'])
def calcular_rota():
    if not mapa_service:
        return jsonify({'error': 'Serviço de mapas não disponível'}), 503
    try:
        data = request.json
        resultado = mapa_service.calcular_rota(data['origem'], data['destino'])
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## 2. Problemas de Interface

### Problemas Identificados
- Filtros de município e status hardcoded no HTML
- Falta de validação de formulários no frontend
- Modal de checklist muito grande em telas pequenas
- Falta de responsividade em alguns componentes

### Soluções Propostas
```javascript
// visitas.html
// Carregar municípios dinamicamente
async function carregarMunicipios() {
    try {
        const response = await fetch('/api/municipios');
        const municipios = await response.json();
        const select = document.getElementById('filtro-municipio');
        select.innerHTML = '<option value="">Todos os Municípios</option>';
        municipios.forEach(m => {
            select.innerHTML += `<option value="${m.codigo}">${m.nome}</option>`;
        });
    } catch (error) {
        showToast('Erro ao carregar municípios', 'danger');
    }
}

// Validação de formulários
document.getElementById('form-nova-visita').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = new FormData(e.target);
    const dataVisita = new Date(data.get('data'));
    
    if (dataVisita < new Date()) {
        showToast('Não é possível agendar visitas no passado', 'danger');
        return;
    }
    
    // Resto do código...
});
```

## 3. Problemas de Dados

### Problemas Identificados
- Falta de validação de datas (possibilidade de agendar visitas no passado)
- Ausência de verificação de conflitos de horários
- Sem limite de visitas por dia
- Falta de validação de dados obrigatórios

### Soluções Propostas
```python
# models/agendamento.py
class Visita(db.Model):
    # ... código existente ...
    
    @classmethod
    def verificar_disponibilidade(cls, data, hora_inicio, hora_fim):
        """Verifica se há conflito de horários."""
        visitas_existentes = cls.query.filter_by(data=data).all()
        for visita in visitas_existentes:
            if (hora_inicio <= visita.hora_fim and hora_fim >= visita.hora_inicio):
                return False
        return True
    
    @classmethod
    def verificar_limite_diario(cls, data):
        """Verifica se já atingiu o limite de visitas do dia."""
        return cls.query.filter_by(data=data).count() < 5  # Limite de 5 visitas por dia
```

## 4. Problemas de Performance

### Problemas Identificados
- Carregamento de todas as visitas de uma vez
- Falta de paginação na lista de visitas
- Ausência de cache de dados
- Consultas ineficientes ao banco de dados

### Soluções Propostas
```python
# app.py
@app.route('/api/visitas', methods=['GET'])
def get_visitas():
    """Retorna a lista de visitas com paginação."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        visitas = Visita.query.order_by(
            Visita.data.asc(), 
            Visita.hora_inicio.asc()
        ).paginate(page=page, per_page=per_page)
        
        return jsonify({
            'visitas': [visita.to_dict() for visita in visitas.items],
            'total': visitas.total,
            'pages': visitas.pages,
            'current_page': visitas.page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## 5. Problemas de Segurança

### Problemas Identificados
- Ausência de autenticação de usuários
- Falta de validação de permissões
- Ausência de proteção contra CSRF
- Exposição de dados sensíveis

### Soluções Propostas
```python
# app.py
from flask_login import LoginManager, login_required
from flask_wtf.csrf import CSRFProtect

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
csrf = CSRFProtect(app)
login_manager = LoginManager(app)

@app.route('/api/visitas', methods=['POST'])
@login_required
def criar_visita():
    # ... código existente ...
```

## 6. Problemas de UX (User Experience)

### Problemas Identificados
- Falta de feedback visual durante carregamentos
- Ausência de confirmação para ações importantes
- Mensagens de erro pouco claras
- Falta de indicadores de progresso

### Soluções Propostas
```javascript
// visitas.html
// Feedback visual durante carregamentos
function showLoading() {
    document.getElementById('loading').style.display = 'block';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

// Confirmação para ações importantes
function confirmarExclusao(visitaId) {
    if (confirm('Tem certeza que deseja excluir esta visita?')) {
        excluirVisita(visitaId);
    }
}

// Mensagens de erro mais claras
function handleError(error) {
    let mensagem = 'Ocorreu um erro';
    if (error.response) {
        switch (error.response.status) {
            case 400:
                mensagem = 'Dados inválidos';
                break;
            case 404:
                mensagem = 'Visita não encontrada';
                break;
            case 500:
                mensagem = 'Erro no servidor';
                break;
        }
    }
    showToast(mensagem, 'danger');
}
```

## Próximos Passos

1. **Priorização de Correções**
   - Implementar autenticação e segurança
   - Corrigir problemas de configuração
   - Implementar validações de dados
   - Melhorar a interface do usuário

2. **Plano de Implementação**
   - Criar branch de desenvolvimento
   - Implementar correções em ordem de prioridade
   - Realizar testes após cada correção
   - Documentar mudanças realizadas

3. **Testes**
   - Testes unitários para novas funcionalidades
   - Testes de integração
   - Testes de interface
   - Testes de segurança

4. **Documentação**
   - Atualizar documentação técnica
   - Criar manual do usuário
   - Documentar processos de segurança
   - Manter histórico de alterações 