f# Implementação da Gestão de Visitas - PNSB 2024

## Caso de Uso: Bombinhas e Porto Belo

### Informações dos Municípios
```json
{
  "municipios": [
    {
      "nome": "Bombinhas",
      "codigo_ibge": "4202453",
      "prefeitura": {
        "nome": "FAMAB",
        "endereco": "Av. Leopoldo Zarling, 2752 - Bombas",
        "horario_funcionamento": "12:00",
        "contato_principal": "Flávio Steigleder Martins",
        "area": "Gestão ambiental e resíduos sólidos"
      }
    },
    {
      "nome": "Porto Belo",
      "codigo_ibge": "4213500",
      "prefeitura": {
        "nome": "FAMAP",
        "endereco": "Rua Aderbal de Souza, 150, Balneário Perequê",
        "horario_funcionamento": "8:00",
        "area": "Gestão ambiental e resíduos sólidos"
      }
    }
  ]
}
```

### Cronograma de Visitas
```json
{
  "cronograma": {
    "data": "2024-03-XX",
    "visitas": [
      {
        "municipio": "Porto Belo",
        "horario": "10:00-11:00",
        "local": "FAMAP",
        "tipo": "Apresentação PNSB"
      },
      {
        "municipio": "Bombinhas",
        "horario": "13:00-14:00",
        "local": "FAMAB",
        "tipo": "Apresentação PNSB"
      }
    ],
    "deslocamentos": [
      {
        "origem": "Itajaí",
        "destino": "Porto Belo",
        "horario": "9:00-10:00"
      },
      {
        "origem": "Porto Belo",
        "destino": "Bombinhas",
        "horario": "12:00-13:00"
      }
    ]
  }
}
```

## Implementação das Funcionalidades

### 1. Interface Básica
```python
# app.py
from flask import Flask, render_template, jsonify
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/calendario')
def calendario():
    return render_template('calendario.html')

@app.route('/checklist')
def checklist():
    return render_template('checklist.html')

@app.route('/relatorios')
def relatorios():
    return render_template('relatorios.html')
```

### 2. Sistema de Agendamento
```python
# models/agendamento.py
class Visita:
    def __init__(self, municipio, data, hora_inicio, hora_fim, informante):
        self.municipio = municipio
        self.data = data
        self.hora_inicio = hora_inicio
        self.hora_fim = hora_fim
        self.informante = informante
        self.status = "agendada"
        self.checklist = Checklist()

class Calendario:
    def __init__(self):
        self.visitas = []
    
    def adicionar_visita(self, visita):
        if self.verificar_disponibilidade(visita):
            self.visitas.append(visita)
            return True
        return False
    
    def verificar_disponibilidade(self, visita):
        # Lógica de verificação de conflitos
        pass
```

### 3. Checklist de Visitas
```python
# models/checklist.py
class Checklist:
    def __init__(self):
        self.materiais = [
            "Ofício do Presidente do IBGE",
            "Conteúdo_Simplificado_MRS.pdf",
            "DICAS LIMPEZA URBANA E MANEJO DE RESÍDUOS SÓLIDOS 2.pdf"
        ]
        self.documentos = [
            "Identificação IBGE",
            "Autorização de Visita"
        ]
        self.equipamentos = [
            "Notebook",
            "Carregador",
            "Material de Escrita"
        ]
        self.status = {item: "pendente" for item in self.materiais + self.documentos + self.equipamentos}
```

### 4. Integração com Mapas
```python
# services/maps.py
from googlemaps import Client

class MapaService:
    def __init__(self, api_key):
        self.client = Client(api_key)
    
    def calcular_rota(self, origem, destino):
        return self.client.directions(origem, destino)
    
    def estimar_tempo(self, origem, destino):
        return self.client.distance_matrix(origem, destino)
```

### 5. Sistema de Relatórios
```python
# services/relatorios.py
class RelatorioService:
    def gerar_relatorio_visita(self, visita):
        return {
            "municipio": visita.municipio,
            "data": visita.data,
            "status": visita.status,
            "checklist": visita.checklist.status,
            "observacoes": visita.observacoes
        }
    
    def gerar_relatorio_periodo(self, data_inicio, data_fim):
        # Lógica para gerar relatório do período
        pass
```

## Templates HTML

### 1. Dashboard
```html
<!-- templates/dashboard.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - Gestão de Visitas PNSB</title>
</head>
<body>
    <div class="container">
        <h1>Dashboard</h1>
        <div class="proximas-visitas">
            <h2>Próximas Visitas</h2>
            <!-- Lista de visitas -->
        </div>
        <div class="metricas">
            <h2>Métricas</h2>
            <!-- Gráficos e estatísticas -->
        </div>
    </div>
</body>
</html>
```

### 2. Calendário
```html
<!-- templates/calendario.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Calendário - Gestão de Visitas PNSB</title>
</head>
<body>
    <div class="container">
        <h1>Calendário de Visitas</h1>
        <div id="calendario">
            <!-- Implementação do calendário -->
        </div>
    </div>
</body>
</html>
```

## Próximos Passos Imediatos

1. **Configuração do Ambiente**
   - Instalar dependências
   - Configurar banco de dados
   - Configurar chaves de API (Google Maps)

2. **Desenvolvimento da Interface**
   - Implementar templates básicos
   - Adicionar estilos CSS
   - Implementar interatividade com JavaScript

3. **Implementação do Backend**
   - Configurar rotas
   - Implementar lógica de negócios
   - Integrar com serviços externos

4. **Testes**
   - Testes unitários
   - Testes de integração
   - Testes de interface

5. **Documentação**
   - Documentar código
   - Criar manual do usuário
   - Documentar APIs

## Requisitos Técnicos

- Python 3.8+
- Flask
- SQLAlchemy
- Google Maps API
- Bootstrap
- jQuery

## Instalação

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# Iniciar aplicação
python app.py
``` 