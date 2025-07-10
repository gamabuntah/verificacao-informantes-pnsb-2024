# -*- coding: utf-8 -*-
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

# Configurações de Status de Visita
STATUS_VISITA = {
    'agendada': 'Agendada',
    'em_andamento': 'Em Andamento',
    'concluida': 'Concluida',
    'cancelada': 'Cancelada',
    'reagendada': 'Reagendada'
}

# Configurações de Checklist
CHECKLIST_MATERIAIS = {
    'questionario': 'Questionario PNSB 2024',
    'oficio_presidente': 'Oficio do Presidente do IBGE',
    'conteudo_simplificado': 'Conteudo Simplificado MRS',
    'dicas_preenchimento': 'Dicas de Preenchimento'
}

CHECKLIST_DOCUMENTOS = {
    'identificacao': 'Identificacao',
    'credencial_ibge': 'Credencial IBGE',
    'autorizacao_visita': 'Autorizacao de Visita'
}

CHECKLIST_EQUIPAMENTOS = {
    'tablet': 'Tablet',
    'carregador': 'Carregador',
    'fone_ouvido': 'Fone de Ouvido',
    'camera': 'Camera'
}

# Configurações de Roteiro
ROTEIRO_ABORDAGEM = [
    'Apresentacao Inicial',
    'Objetivo da Visita',
    'Orientacao sobre o Questionario',
    'Entrega de Materiais de Apoio',
    'Pontos-Chave Antes do Preenchimento',
    'Explicacao da Estrutura do Questionario',
    'Dicas e Atencao',
    'Validacao de Prestadores',
    'Apoio e Contato',
    'Proximos Passos',
    'Encerramento'
]

# Configurações de Tipos de Pesquisa
TIPOS_PESQUISA = {
    'MRS': 'Manejo de Residuos Solidos',
    'MAP': 'Manejo de Aguas Pluviais'
}

# Configurações de Tipos de Informante
TIPOS_INFORMANTE = {
    'prefeitura': 'Prefeitura',
    'empresa_terceirizada': 'Contratada',
    'entidade_catadores': 'Entidade de Catadores',
    'outros': 'Outros'
}

# Configurações de Relatórios
RELATORIO_PERIODOS = {
    'hoje': 'Hoje',
    'semana': 'Esta Semana',
    'mes': 'Este Mes',
    'personalizado': 'Personalizado'
}