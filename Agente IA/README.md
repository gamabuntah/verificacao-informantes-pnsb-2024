# Agente IA - Gestão de Visitas PNSB 2024

Sistema de gestão de visitas para a Pesquisa Nacional de Saneamento Básico (PNSB) 2024, focado em urban cleaning e gestão de resíduos sólidos em 11 municípios de Santa Catarina.

## Estrutura do Projeto

```
Agente IA/
├── gestao_visitas/
│   ├── models/
│   │   ├── agendamento.py
│   │   └── checklist.py
│   ├── services/
│   │   ├── informantes.py
│   │   ├── maps.py
│   │   ├── prestadores.py
│   │   ├── questionarios.py
│   │   ├── relatorios.py
│   │   ├── roteiro.py
│   │   └── rotas.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── calendario.html
│   │   ├── checklist.html
│   │   └── relatorios.html
│   ├── config.py
│   └── __init__.py
├── requirements.txt
└── README.md
```

## Funcionalidades

### Gestão de Visitas
- Agendamento de visitas
- Calendário de visitas
- Checklist de materiais e documentos
- Roteiro de abordagem
- Validação de prestadores de serviço

### Gestão de Informantes
- Cadastro de informantes
- Contatos e áreas de atuação
- Status de disponibilidade

### Gestão de Prestadores
- Cadastro de prestadores
- Validação de serviços
- Contratos e áreas de atuação

### Questionários
- Estrutura do questionário PNSB 2024
- Preenchimento e validação
- Observações e anexos

### Relatórios
- Relatórios de visitas
- Relatórios consolidados
- Estatísticas e indicadores

### Rotas
- Cálculo de rotas otimizadas
- Verificação de viabilidade
- Tempos de deslocamento

## Requisitos

- Python 3.8+
- Flask
- SQLAlchemy
- Google Maps API
- Outras dependências listadas em `requirements.txt`

## Instalação

1. Clone o repositório
2. Crie um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure as variáveis de ambiente:
   - GOOGLE_MAPS_API_KEY
   - DATABASE_URL
   - FLASK_ENV
   - FLASK_APP

## Uso

1. Inicie o servidor:
   ```bash
   flask run
   ```
2. Acesse a aplicação em `http://localhost:5000`

## Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Crie um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes. 