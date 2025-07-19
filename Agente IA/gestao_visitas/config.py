from datetime import time

# Configurações de Horários
HORARIO_INICIO_DIA = time(8, 0)  # 08:00
HORARIO_FIM_DIA = time(18, 0)    # 18:00
DURACAO_PADRAO_VISITA = 60       # 60 minutos

# Configurações de Municípios
MUNICIPIOS = [
    'Balneário Camboriú',
    'Balneário Piçarras',
    'Bombinhas',
    'Camboriú',
    'Itajaí',
    'Itapema',
    'Luiz Alves',
    'Navegantes',
    'Penha',
    'Porto Belo',
    'Ilhota'
]

# Configurações de Status de Visita (integrado com sistema livre)
STATUS_VISITA = {
    'agendada': 'Agendada',
    'em preparação': 'Em Preparação',
    'em andamento': 'Em Andamento',
    'em execução': 'Em Execução',
    'em follow-up': 'Em Follow-up',
    'verificação whatsapp': 'Verificação WhatsApp',
    'realizada': 'Realizada',
    'questionários concluídos': 'Questionários Concluídos',
    'questionários validados': 'Questionários Validados',
    'finalizada': 'Finalizada',
    'remarcada': 'Remarcada',
    'não realizada': 'Não Realizada',
    'cancelada': 'Cancelada',
    'aguardando': 'Aguardando',
    'pendente': 'Pendente',
    'confirmada': 'Confirmada'
}

# Configurações de Checklist
CHECKLIST_MATERIAIS = {
    'questionario': 'Questionário PNSB 2024',
    'oficio_presidente': 'Ofício do Presidente do IBGE',
    'conteudo_simplificado': 'Conteúdo Simplificado MRS',
    'dicas_preenchimento': 'Dicas de Preenchimento'
}

CHECKLIST_DOCUMENTOS = {
    'identificacao': 'Identificação',
    'credencial_ibge': 'Credencial IBGE',
    'autorizacao_visita': 'Autorização de Visita'
}

CHECKLIST_EQUIPAMENTOS = {
    'tablet': 'Tablet',
    'carregador': 'Carregador',
    'fone_ouvido': 'Fone de Ouvido',
    'camera': 'Câmera'
}

# Configurações de Roteiro
ROTEIRO_ABORDAGEM = [
    'Apresentação Inicial',
    'Objetivo da Visita',
    'Orientação sobre o Questionário',
    'Entrega de Materiais de Apoio',
    'Pontos-Chave Antes do Preenchimento',
    'Explicação da Estrutura do Questionário',
    'Dicas e Atenção',
    'Validação de Prestadores',
    'Apoio e Contato',
    'Próximos Passos',
    'Encerramento'
]

# Configurações de Tipos de Pesquisa
TIPOS_PESQUISA = {
    'MRS': 'Manejo de Resíduos Sólidos',
    'MAP': 'Manejo de Águas Pluviais'
}

# Configurações de Tipos de Entidades (expandido para múltiplas entidades)
TIPOS_ENTIDADE = {
    'prefeitura': {
        'nome': 'Prefeitura Municipal',
        'descricao': 'Órgão público municipal responsável pelo saneamento',
        'cores': {'primary': '#007bff', 'secondary': '#6c757d'},
        'icone': 'fas fa-university',
        'campos_obrigatorios': ['local', 'responsavel_cargo']
    },
    'empresa_terceirizada': {
        'nome': 'Empresa Terceirizada',
        'descricao': 'Empresa contratada para serviços de saneamento',
        'cores': {'primary': '#28a745', 'secondary': '#6f42c1'},
        'icone': 'fas fa-building',
        'campos_obrigatorios': ['entidade_nome', 'entidade_cnpj', 'entidade_servicos']
    },
    'entidade_catadores': {
        'nome': 'Entidade de Catadores',
        'descricao': 'Cooperativas, associações ou organizações de catadores',
        'cores': {'primary': '#fd7e14', 'secondary': '#20c997'},
        'icone': 'fas fa-recycle',
        'campos_obrigatorios': ['entidade_nome', 'entidade_categoria', 'entidade_servicos']
    },
    'empresa_nao_vinculada': {
        'nome': 'Empresa Não Vinculada',
        'descricao': 'Empresas que prestam serviços sem vínculo direto com a prefeitura',
        'cores': {'primary': '#6f42c1', 'secondary': '#fd7e14'},
        'icone': 'fas fa-industry',
        'campos_obrigatorios': ['entidade_nome', 'entidade_cnpj', 'entidade_servicos']
    }
}

# Subcategorias de Entidades (para detalhamento)
CATEGORIAS_ENTIDADE = {
    'empresa_terceirizada': [
        'Coleta de Resíduos Sólidos',
        'Limpeza Urbana',
        'Tratamento de Resíduos',
        'Gestão de Aterros',
        'Coleta Seletiva',
        'Compostagem',
        'Outros Serviços'
    ],
    'entidade_catadores': [
        'Cooperativa de Catadores',
        'Associação de Catadores',
        'Organização de Catadores',
        'Grupo Informal de Catadores',
        'Central de Cooperativas'
    ],
    'empresa_nao_vinculada': [
        'Geradora de Resíduos',
        'Transportadora de Resíduos',
        'Recicladora',
        'Beneficiadora de Materiais',
        'Outros'
    ]
}

# Mapeamento para compatibilidade com código existente
TIPOS_INFORMANTE = {key: value['nome'] for key, value in TIPOS_ENTIDADE.items()}

# Configurações de Relatórios
RELATORIO_PERIODOS = {
    'hoje': 'Hoje',
    'semana': 'Esta Semana',
    'mes': 'Este Mês',
    'personalizado': 'Personalizado'
} 