# Estrutura Multi-Entidades - Sistema PNSB

## 📋 Visão Geral

O sistema foi preparado para suportar múltiplas entidades por município além da prefeitura, incluindo empresas terceirizadas, entidades de catadores e empresas não vinculadas.

## 🏗️ Estrutura Implementada

### Modelo de Dados Expandido

**Campos Adicionados ao Modelo `Visita`:**
```python
# Campos expandidos para múltiplas entidades
entidade_nome = Column(String(200))         # Nome específico da entidade/empresa
entidade_cnpj = Column(String(20))          # CNPJ da entidade (se aplicável)
entidade_categoria = Column(String(50))     # Categoria específica da entidade
responsavel_cargo = Column(String(100))     # Cargo do responsável na entidade
entidade_endereco = Column(String(300))     # Endereço específico da entidade
entidade_servicos = Column(String(500))     # Serviços prestados pela entidade
```

### Tipos de Entidades Suportadas

#### 1. **Prefeitura Municipal** (atual)
- **Identificador**: `prefeitura`
- **Descrição**: Órgão público municipal responsável pelo saneamento
- **Campos obrigatórios**: `local`, `responsavel_cargo`
- **Cor primária**: #007bff (azul)
- **Ícone**: `fas fa-university`

#### 2. **Empresa Terceirizada** (preparado)
- **Identificador**: `empresa_terceirizada`
- **Descrição**: Empresa contratada para serviços de saneamento
- **Campos obrigatórios**: `entidade_nome`, `entidade_cnpj`, `entidade_servicos`
- **Cor primária**: #28a745 (verde)
- **Ícone**: `fas fa-building`
- **Subcategorias**:
  - Coleta de Resíduos Sólidos
  - Limpeza Urbana
  - Tratamento de Resíduos
  - Gestão de Aterros
  - Coleta Seletiva
  - Compostagem
  - Outros Serviços

#### 3. **Entidade de Catadores** (preparado)
- **Identificador**: `entidade_catadores`
- **Descrição**: Cooperativas, associações ou organizações de catadores
- **Campos obrigatórios**: `entidade_nome`, `entidade_categoria`, `entidade_servicos`
- **Cor primária**: #fd7e14 (laranja)
- **Ícone**: `fas fa-recycle`
- **Subcategorias**:
  - Cooperativa de Catadores
  - Associação de Catadores
  - Organização de Catadores
  - Grupo Informal de Catadores
  - Central de Cooperativas

#### 4. **Empresa Não Vinculada** (preparado)
- **Identificador**: `empresa_nao_vinculada`
- **Descrição**: Empresas que prestam serviços sem vínculo direto com a prefeitura
- **Campos obrigatórios**: `entidade_nome`, `entidade_cnpj`, `entidade_servicos`
- **Cor primária**: #6f42c1 (roxo)
- **Ícone**: `fas fa-industry`
- **Subcategorias**:
  - Geradora de Resíduos
  - Transportadora de Resíduos
  - Recicladora
  - Beneficiadora de Materiais
  - Outros

## 🔌 APIs Disponíveis

### 1. Tipos de Entidades
```http
GET /api/entidades/tipos
```
Retorna todas as configurações de tipos de entidades disponíveis.

### 2. Entidades por Município
```http
GET /api/entidades/municipio/{municipio}
```
Retorna todas as entidades de um município específico, agrupadas com suas visitas e progresso.

### 3. Progresso Multi-Entidades
```http
GET /api/visitas/progresso-mapa
```
API atualizada para incluir informações de múltiplas entidades por município.

## 📊 Estrutura de Dados de Resposta

### Entidade Individual
```json
{
  "tipo": "empresa_terceirizada",
  "nome": "Empresa Limpeza SC Ltda",
  "cnpj": "12.345.678/0001-90",
  "categoria": "Coleta de Resíduos Sólidos",
  "endereco": "Rua dos Coletores, 123",
  "servicos": "Coleta domiciliar, comercial e seletiva",
  "responsavel_cargo": "Gerente Operacional",
  "telefone": "(47) 99999-9999",
  "visitas": [...],
  "progresso": {
    "total": 3,
    "agendadas": 1,
    "executadas": 2,
    "em_followup": 1,
    "finalizadas": 0
  }
}
```

### Progresso por Município
```json
{
  "municipio": "Itajaí",
  "entidades": {
    "prefeitura_principal": {...},
    "empresa_terceirizada_Limpeza SC": {...},
    "entidade_catadores_Cooperativa Verde": {...}
  },
  "total_entidades": 3,
  "resumo": {...}
}
```

## 🎯 Quando Adicionar as Informações

### Pré-requisitos
1. **Dados das empresas terceirizadas**:
   - Nome da empresa
   - CNPJ
   - Tipo de serviço prestado
   - Contato do responsável

2. **Informações das entidades de catadores**:
   - Nome da cooperativa/associação
   - Tipo de organização
   - Área de atuação
   - Responsável

3. **Empresas não vinculadas**:
   - Identificação da empresa
   - Tipo de atividade
   - Relação com o saneamento municipal

### Processo de Migração
1. **Criar visitas para novas entidades** usando os novos campos
2. **Atualizar frontend** para mostrar múltiplas entidades por município
3. **Configurar filtros** por tipo de entidade
4. **Ajustar relatórios** para considerar múltiplas entidades

## 🔧 Implementação Futura

### Frontend Preparado
- Formulários com campos condicionais por tipo de entidade
- Visualização em cards por entidade no mapa de progresso
- Filtros por tipo de entidade
- Cores diferenciadas por tipo

### Validações
- Campos obrigatórios específicos por tipo
- Validação de CNPJ para empresas
- Categorização automática

### Relatórios
- Progresso por tipo de entidade
- Comparativo entre entidades do mesmo município
- Análise de eficiência por categoria

## 🚀 Status Atual

✅ **Estrutura de dados preparada**
✅ **APIs implementadas**
✅ **Configurações definidas**
✅ **Compatibilidade mantida**
⏳ **Frontend aguardando dados**
⏳ **Formulários aguardando configuração**

O sistema está completamente preparado para receber as informações das múltiplas entidades quando disponíveis.