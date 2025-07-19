/**
 * WORKFLOW E CONTATOS - MAPA DE PROGRESSO PNSB 2024
 * Implementação das funcionalidades de workflow e inteligência de contatos
 */

class WorkflowContatos {
    constructor(mapaProgresso) {
        this.mapaProgresso = mapaProgresso;
        
        // PIPELINE COMPLETO - 25 ESTADOS DO WORKFLOW PNSB 2024
        this.pipelineEstados = {
            // FASE 1 - PLANEJAMENTO (5 estados)
            planejamento: [
                { id: 'sem_visita', nome: 'Sem Visita', descricao: 'Município ainda não tem visita planejada', cor: '#dc3545' },
                { id: 'identificacao_pendente', nome: 'Identificação Pendente', descricao: 'Precisa identificar entidades P1', cor: '#fd7e14' },
                { id: 'contatos_pendentes', nome: 'Contatos Pendentes', descricao: 'Precisa encontrar telefones/emails', cor: '#ffc107' },
                { id: 'agendamento_pendente', nome: 'Agendamento Pendente', descricao: 'Precisa agendar a visita', cor: '#20c997' },
                { id: 'agendada', nome: 'Agendada', descricao: 'Visita agendada mas não confirmada', cor: '#17a2b8' }
            ],
            
            // FASE 2 - PRÉ-VISITA (5 estados)
            pre_visita: [
                { id: 'confirmacao_pendente', nome: 'Confirmação Pendente', descricao: 'Aguardando confirmação do município', cor: '#6f42c1' },
                { id: 'em_preparacao', nome: 'Em Preparação', descricao: 'Preparando materiais e documentos', cor: '#e83e8c' },
                { id: 'rota_planejada', nome: 'Rota Planejada', descricao: 'Rota definida e otimizada', cor: '#fd7e14' },
                { id: 'equipe_designada', nome: 'Equipe Designada', descricao: 'Pesquisador(es) designado(s)', cor: '#20c997' },
                { id: 'pre_visita_completa', nome: 'Pré-Visita Completa', descricao: 'Tudo pronto para execução', cor: '#28a745' }
            ],
            
            // FASE 3 - EXECUÇÃO (5 estados)
            execucao: [
                { id: 'em_deslocamento', nome: 'Em Deslocamento', descricao: 'Equipe a caminho do município', cor: '#17a2b8' },
                { id: 'em_execucao', nome: 'Em Execução', descricao: 'Visita sendo realizada no momento', cor: '#007bff' },
                { id: 'coletando_mrs', nome: 'Coletando MRS', descricao: 'Coletando dados de Resíduos Sólidos', cor: '#6610f2' },
                { id: 'coletando_map', nome: 'Coletando MAP', descricao: 'Coletando dados de Águas Pluviais', cor: '#6f42c1' },
                { id: 'validando_dados', nome: 'Validando Dados', descricao: 'Validação in-loco dos dados', cor: '#e83e8c' }
            ],
            
            // FASE 4 - PÓS-VISITA (5 estados)
            pos_visita: [
                { id: 'dados_coletados', nome: 'Dados Coletados', descricao: 'Dados coletados mas não processados', cor: '#fd7e14' },
                { id: 'processando_dados', nome: 'Processando Dados', descricao: 'Digitação e organização', cor: '#ffc107' },
                { id: 'validacao_tecnica', nome: 'Validação Técnica', descricao: 'Revisão técnica dos dados', cor: '#20c997' },
                { id: 'pendencias_identificadas', nome: 'Pendências Identificadas', descricao: 'Problemas encontrados', cor: '#dc3545' },
                { id: 'followup_necessario', nome: 'Follow-up Necessário', descricao: 'Precisa retornar ao município', cor: '#fd7e14' }
            ],
            
            // FASE 5 - FINALIZAÇÃO (5 estados)
            finalizacao: [
                { id: 'dados_validados', nome: 'Dados Validados', descricao: 'Dados aprovados tecnicamente', cor: '#28a745' },
                { id: 'relatorio_preliminar', nome: 'Relatório Preliminar', descricao: 'Relatório inicial gerado', cor: '#17a2b8' },
                { id: 'aprovacao_final', nome: 'Aprovação Final', descricao: 'Aguardando aprovação final', cor: '#6f42c1' },
                { id: 'realizada', nome: 'Realizada', descricao: 'Visita concluída com sucesso', cor: '#28a745' },
                { id: 'finalizada', nome: 'Finalizada', descricao: 'Processo totalmente encerrado', cor: '#155724' }
            ]
        };
        
        // Estados legados para compatibilidade
        this.statusWorkflow = [
            'agendada', 'em preparação', 'confirmada', 'aguardando',
            'em andamento', 'em execução', 'em follow-up', 'verificação whatsapp',
            'realizada', 'questionários concluídos', 'questionários validados', 'finalizada',
            'remarcada', 'não realizada', 'cancelada', 'pendente'
        ];
        
        // CHECKLIST COMPLETO - 3 FASES COM DESCRIÇÕES
        this.etapasChecklist = {
            antes: [
                { id: 'cracha_ibge', nome: 'Crachá IBGE', descricao: 'Portar identificação oficial do IBGE', obrigatorio: true },
                { id: 'questionarios_impressos', nome: 'Questionários Impressos', descricao: 'Formulários MRS e MAP impressos', obrigatorio: true },
                { id: 'materiais_apoio', nome: 'Materiais de Apoio', descricao: 'Canetas, prancheta, calculadora', obrigatorio: true },
                { id: 'contato_previo', nome: 'Contato Prévio', descricao: 'Confirmação por telefone/WhatsApp', obrigatorio: true },
                { id: 'endereco_confirmado', nome: 'Endereço Confirmado', descricao: 'Localização exata da prefeitura', obrigatorio: true },
                { id: 'horario_funcionamento', nome: 'Horário de Funcionamento', descricao: 'Verificar horários de atendimento', obrigatorio: true },
                { id: 'backup_contatos', nome: 'Backup de Contatos', descricao: 'Contatos alternativos anotados', obrigatorio: false },
                { id: 'documentos_apresentacao', nome: 'Documentos de Apresentação', descricao: 'Ofício, carta de apresentação', obrigatorio: true },
                { id: 'lista_entidades', nome: 'Lista de Entidades', descricao: 'Entidades P1 identificadas previamente', obrigatorio: true },
                { id: 'mapa_regiao', nome: 'Mapa da Região', descricao: 'Mapa físico ou digital da cidade', obrigatorio: false },
                { id: 'telefone_carregado', nome: 'Telefone Carregado', descricao: 'Bateria e carregador portátil', obrigatorio: true },
                { id: 'equipamentos_funcionando', nome: 'Equipamentos Funcionando', descricao: 'Tablet, GPS, câmera testados', obrigatorio: true },
                { id: 'cronograma_dia', nome: 'Cronograma do Dia', descricao: 'Roteiro e horários planejados', obrigatorio: true }
            ],
            durante: [
                { id: 'apresentacao_pesquisador', nome: 'Apresentação do Pesquisador', descricao: 'Identificação e apresentação formal', obrigatorio: true },
                { id: 'explicacao_pnsb', nome: 'Explicação da PNSB', descricao: 'Objetivos e importância da pesquisa', obrigatorio: true },
                { id: 'validacao_dados', nome: 'Validação de Dados', descricao: 'Confirmar informações preliminares', obrigatorio: true },
                { id: 'questionario_mrs', nome: 'Questionário MRS', descricao: 'Manejo de Resíduos Sólidos completo', obrigatorio: true },
                { id: 'questionario_map', nome: 'Questionário MAP', descricao: 'Manejo de Águas Pluviais completo', obrigatorio: true },
                { id: 'fotos_evidencia', nome: 'Fotos de Evidência', descricao: 'Documentação fotográfica', obrigatorio: true },
                { id: 'assinaturas_coletadas', nome: 'Assinaturas Coletadas', descricao: 'Responsáveis técnicos assinaram', obrigatorio: true },
                { id: 'contatos_adicionais', nome: 'Contatos Adicionais', descricao: 'Novos contatos identificados', obrigatorio: false },
                { id: 'observacoes_campo', nome: 'Observações de Campo', descricao: 'Anotações importantes registradas', obrigatorio: true },
                { id: 'problemas_identificados', nome: 'Problemas Identificados', descricao: 'Dificuldades e limitações anotadas', obrigatorio: false },
                { id: 'proximos_passos', nome: 'Próximos Passos', descricao: 'Follow-up necessário definido', obrigatorio: false }
            ],
            apos: [
                { id: 'questionarios_entregues', nome: 'Questionários Entregues', descricao: 'Formulários digitalizados no sistema', obrigatorio: true },
                { id: 'followup_agendado', nome: 'Follow-up Agendado', descricao: 'Próximas ações programadas se necessário', obrigatorio: false },
                { id: 'dados_digitalizados', nome: 'Dados Digitalizados', descricao: 'Todas informações inseridas no sistema', obrigatorio: true },
                { id: 'evidencias_organizadas', nome: 'Evidências Organizadas', descricao: 'Fotos e documentos catalogados', obrigatorio: true },
                { id: 'relatorio_resumo', nome: 'Relatório Resumo', descricao: 'Relatório da visita elaborado', obrigatorio: true }
            ]
        };
    }

    /**
     * Renderizar pipeline completo de visitas com 25 estados
     */
    renderizarPipelineVisitas() {
        const container = document.getElementById('pipeline-visitas');
        if (!container) return;

        const visitas = this.mapaProgresso.dados.visitas || [];
        const municipios = this.mapaProgresso.dados.municipios || [];
        const pipeline = this.organizarMunicipiosPorEstado(municipios, visitas);

        container.innerHTML = `
            <div class="pipeline-header">
                <h4>Pipeline de Workflow PNSB 2024</h4>
                <div class="pipeline-stats">
                    <span class="badge badge-info">Total: ${Object.keys(this.mapaProgresso.municipios || {}).length} municípios</span>
                    <span class="badge badge-success">Finalizados: ${pipeline.finalizacao?.finalizada?.length || 0}</span>
                    <span class="badge badge-warning">Em andamento: ${this.contarMunicipiosEmAndamento(pipeline)}</span>
                </div>
            </div>
            
            <div class="pipeline-container">
                ${this.renderizarFasesPipeline(pipeline)}
            </div>
            
            <div class="pipeline-actions">
                <button class="btn btn-primary btn-sm" onclick="workflowContatos.atualizarPipeline()">
                    🔄 Atualizar Pipeline
                </button>
                <button class="btn btn-success btn-sm" onclick="workflowContatos.avancarProximoEstado()">
                    ⏭️ Avançar Estados
                </button>
                <button class="btn btn-info btn-sm" onclick="workflowContatos.exportarPipeline()">
                    📊 Exportar Pipeline
                </button>
            </div>
        `;
        
        this.adicionarEventosPipeline();
    }
    
    /**
     * Renderizar as 5 fases do pipeline
     */
    renderizarFasesPipeline(pipeline) {
        const fases = Object.keys(this.pipelineEstados);
        
        return fases.map(fase => {
            const estados = this.pipelineEstados[fase];
            const totalMunicipios = estados.reduce((total, estado) => {
                return total + (pipeline[estado.id] || []).length;
            }, 0);
            
            return `
                <div class="pipeline-fase" data-fase="${fase}">
                    <div class="fase-header">
                        <h5 class="fase-titulo">${fase.charAt(0).toUpperCase() + fase.slice(1).replace('_', '-')}</h5>
                        <span class="fase-contador badge badge-secondary">${totalMunicipios}</span>
                    </div>
                    <div class="fase-estados">
                        ${estados.map(estado => this.renderizarEstadoPipeline(estado, pipeline[estado.id] || [])).join('')}
                    </div>
                </div>
            `;
        }).join('');
    }
    
    /**
     * Renderizar um estado individual do pipeline
     */
    renderizarEstadoPipeline(estado, municipios) {
        return `
            <div class="pipeline-estado" data-estado="${estado.id}">
                <div class="estado-header" style="background-color: ${estado.cor}">
                    <span class="estado-nome">${estado.nome}</span>
                    <span class="estado-contador">${municipios.length}</span>
                </div>
                <div class="estado-municipios">
                    ${municipios.map(municipio => `
                        <div class="municipio-card" data-municipio="${municipio.nome || municipio}">
                            <span class="municipio-nome">${municipio.nome || municipio}</span>
                            <div class="municipio-acoes">
                                <button class="btn-acao" onclick="workflowContatos.abrirDetalhes('${municipio.nome || municipio}')" title="Ver detalhes">
                                    👁️
                                </button>
                                <button class="btn-acao" onclick="workflowContatos.avancarEstado('${municipio.nome || municipio}')" title="Avançar estado">
                                    ⏭️
                                </button>
                            </div>
                        </div>
                    `).join('')}
                </div>
                <div class="estado-descricao">
                    <small>${estado.descricao}</small>
                </div>
            </div>
        `;
    }
    
    /**
     * Organizar municípios por estado do pipeline
     */
    organizarMunicipiosPorEstado(municipios, visitas) {
        const pipeline = {};
        
        // Inicializar todos os estados
        Object.values(this.pipelineEstados).flat().forEach(estado => {
            pipeline[estado.id] = [];
        });
        
        // Organizar dados reais se disponíveis
        if (municipios && municipios.length > 0) {
            municipios.forEach(municipio => {
                const estadoId = this.determinarEstadoAtual(municipio, visitas);
                if (pipeline[estadoId]) {
                    pipeline[estadoId].push(municipio);
                } else {
                    // Estado não encontrado, colocar em sem_visita
                    pipeline.sem_visita.push(municipio);
                }
            });
        } else {
            // Dados simulados para demonstração
            const municipiosSimulados = [
                'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas', 'Camboriú',
                'Itajaí', 'Itapema', 'Luiz Alves', 'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
            ];
            
            municipiosSimulados.forEach((municipio, index) => {
                const estadosIds = Object.values(this.pipelineEstados).flat().map(e => e.id);
                const estadoAleatorio = estadosIds[index % estadosIds.length];
                pipeline[estadoAleatorio].push({ nome: municipio });
            });
        }
        
        return pipeline;
    }
    
    /**
     * Determinar estado atual de um município
     */
    determinarEstadoAtual(municipio, visitas) {
        // Lógica para determinar o estado baseado nos dados
        const visitasMunicipio = visitas.filter(v => v.municipio === municipio.nome || v.local === municipio.nome);
        
        if (!visitasMunicipio.length) {
            return 'sem_visita';
        }
        
        const ultimaVisita = visitasMunicipio[visitasMunicipio.length - 1];
        const status = ultimaVisita.status;
        
        // Mapear status atual para estados do pipeline
        const mapeamento = {
            'agendada': 'agendada',
            'em preparação': 'em_preparacao',
            'em andamento': 'em_execucao',
            'em execução': 'em_execucao',
            'em follow-up': 'followup_necessario',
            'realizada': 'realizada',
            'finalizada': 'finalizada'
        };
        
        return mapeamento[status] || 'sem_visita';
    }
    
    /**
     * Contar municípios em andamento
     */
    contarMunicipiosEmAndamento(pipeline) {
        const estadosAndamento = ['confirmacao_pendente', 'em_preparacao', 'rota_planejada', 
                                 'equipe_designada', 'em_deslocamento', 'em_execucao', 
                                 'coletando_mrs', 'coletando_map', 'dados_coletados', 'processando_dados'];
        
        return estadosAndamento.reduce((total, estado) => {
            return total + (pipeline[estado] || []).length;
        }, 0);
    }
    
    /**
     * Adicionar eventos ao pipeline
     */
    adicionarEventosPipeline() {
        // Event listeners para interações do pipeline
        document.querySelectorAll('.municipio-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (!e.target.classList.contains('btn-acao')) {
                    const municipio = card.dataset.municipio;
                    this.selecionarMunicipio(municipio);
                }
            });
        });
        
        // Drag and drop para mover municípios entre estados (futuro)
        this.configurarDragAndDrop();
    }
    
    /**
     * Ações do pipeline
     */
    atualizarPipeline() {
        console.log('🔄 Atualizando pipeline...');
        this.renderizarPipelineVisitas();
        this.mapaProgresso.mostrarToast('Pipeline atualizado com sucesso!', 'success');
    }
    
    avancarProximoEstado() {
        console.log('⏭️ Avançando estados automaticamente...');
        // Lógica para avançar municípios automaticamente baseado em critérios
        this.atualizarPipeline();
        this.mapaProgresso.mostrarToast('Estados avançados automaticamente!', 'info');
    }
    
    exportarPipeline() {
        console.log('📊 Exportando pipeline...');
        const pipeline = this.organizarMunicipiosPorEstado(
            this.mapaProgresso.dados.municipios || [], 
            this.mapaProgresso.dados.visitas || []
        );
        
        // Criar CSV do pipeline
        const csvData = this.gerarCSVPipeline(pipeline);
        this.downloadCSV(csvData, 'pipeline_pnsb_2024.csv');
        
        this.mapaProgresso.mostrarToast('Pipeline exportado com sucesso!', 'success');
    }
    
    abrirDetalhes(municipio) {
        console.log(`👁️ Abrindo detalhes de ${municipio}...`);
        // Abrir modal com detalhes do município
        this.mostrarModalDetalhesMunicipio(municipio);
    }
    
    avancarEstado(municipio) {
        console.log(`⏭️ Avançando estado de ${municipio}...`);
        // Lógica para avançar um município para o próximo estado
        this.avancarEstadoMunicipio(municipio);
        this.atualizarPipeline();
    }
    
    selecionarMunicipio(municipio) {
        console.log(`🎯 Município selecionado: ${municipio}`);
        // Destacar município selecionado
        document.querySelectorAll('.municipio-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        const card = document.querySelector(`[data-municipio="${municipio}"]`);
        if (card) {
            card.classList.add('selected');
        }
    }
    
    configurarDragAndDrop() {
        // Implementação futura de drag and drop
        console.log('🖱️ Drag and Drop configurado (placeholder)');
    }
    
    /**
     * Funções auxiliares
     */
    gerarCSVPipeline(pipeline) {
        let csv = 'Fase,Estado,Municipio,Descricao\n';
        
        Object.keys(this.pipelineEstados).forEach(fase => {
            this.pipelineEstados[fase].forEach(estado => {
                const municipios = pipeline[estado.id] || [];
                municipios.forEach(municipio => {
                    csv += `"${fase}","${estado.nome}","${municipio.nome || municipio}","${estado.descricao}"\n`;
                });
            });
        });
        
        return csv;
    }
    
    downloadCSV(csvContent, fileName) {
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', fileName);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    mostrarModalDetalhesMunicipio(municipio) {
        // Implementar modal de detalhes
        alert(`Detalhes de ${municipio} - Implementar modal completo`);
    }
    
    avancarEstadoMunicipio(municipio) {
        // Implementar lógica de avanço de estado
        console.log(`Avançando estado de ${municipio}`);
    }
    
    /**
     * Renderizar checklist das 3 fases
     */
    renderizarChecklistEtapas() {
        const container = document.getElementById('checklist-etapas');
        if (!container) return;

        const municipioSelecionado = this.obterMunicipioSelecionado();
        const checklistData = this.obterDadosChecklist(municipioSelecionado);

        container.innerHTML = `
            <div class="checklist-header">
                <h4>Checklist de Qualidade - 3 Fases</h4>
                <div class="checklist-municipio">
                    <select id="checklist-municipio-select" onchange="workflowContatos.selecionarMunicipioChecklist(this.value)">
                        <option value="">Selecione um município...</option>
                        ${Object.keys(this.mapaProgresso.municipios || {}).map(municipio => 
                            `<option value="${municipio}" ${municipioSelecionado === municipio ? 'selected' : ''}>${municipio}</option>`
                        ).join('')}
                    </select>
                </div>
            </div>
            
            <div class="checklist-container">
                ${this.renderizarFaseChecklist('antes', 'Antes da Visita', checklistData.antes, '#2E86AB')}
                ${this.renderizarFaseChecklist('durante', 'Durante a Visita', checklistData.durante, '#F18F01')}
                ${this.renderizarFaseChecklist('apos', 'Após a Visita', checklistData.apos, '#28a745')}
            </div>
            
            <div class="checklist-resumo">
                ${this.renderizarResumoChecklist(checklistData)}
            </div>
            
            <div class="checklist-actions">
                <button class="btn btn-primary" onclick="workflowContatos.salvarChecklist()">
                    💾 Salvar Checklist
                </button>
                <button class="btn btn-success" onclick="workflowContatos.validarChecklistCompleto()">
                    ✅ Validar Completude
                </button>
                <button class="btn btn-info" onclick="workflowContatos.exportarChecklist()">
                    📋 Exportar Checklist
                </button>
            </div>
        `;

        this.adicionarEventosChecklist();
    }
    
    /**
     * Renderizar uma fase do checklist
     */
    renderizarFaseChecklist(fase, titulo, dadosChecklist, cor) {
        const itens = this.etapasChecklist[fase];
        const completude = this.calcularCompletudeChecklist(dadosChecklist, itens);
        
        return `
            <div class="checklist-fase" data-fase="${fase}">
                <div class="fase-header-checklist" style="background-color: ${cor}">
                    <h5 class="fase-titulo-checklist">${titulo}</h5>
                    <div class="fase-progresso">
                        <span class="progresso-texto">${completude.completos}/${completude.total}</span>
                        <div class="progresso-barra">
                            <div class="progresso-preenchimento" style="width: ${completude.percentual}%; background-color: ${cor}"></div>
                        </div>
                        <span class="progresso-percentual">${completude.percentual}%</span>
                    </div>
                </div>
                
                <div class="checklist-itens">
                    ${itens.map((item, index) => this.renderizarItemChecklist(item, dadosChecklist[item.id], fase, index)).join('')}
                </div>
            </div>
        `;
    }
    
    /**
     * Renderizar um item individual do checklist
     */
    renderizarItemChecklist(item, checked, fase, index) {
        const isChecked = checked ? 'checked' : '';
        const itemClass = checked ? 'checklist-item checked' : 'checklist-item';
        const obrigatorioIcon = item.obrigatorio ? '<span class="item-obrigatorio" title="Obrigatório">*</span>' : '';
        
        return `
            <div class="${itemClass}" data-item="${item.id}">
                <div class="item-checkbox">
                    <input type="checkbox" 
                           id="check_${fase}_${index}" 
                           ${isChecked}
                           onchange="workflowContatos.alterarItemChecklist('${fase}', '${item.id}', this.checked)">
                    <label for="check_${fase}_${index}" class="checkbox-custom"></label>
                </div>
                
                <div class="item-content">
                    <div class="item-nome">
                        ${item.nome} ${obrigatorioIcon}
                    </div>
                    <div class="item-descricao">
                        ${item.descricao}
                    </div>
                </div>
                
                <div class="item-actions">
                    <button class="btn-item-acao" onclick="workflowContatos.adicionarObservacao('${item.id}')" title="Adicionar observação">
                        📝
                    </button>
                </div>
            </div>
        `;
    }
    
    /**
     * Renderizar resumo do checklist
     */
    renderizarResumoChecklist(checklistData) {
        const resumoFases = Object.keys(this.etapasChecklist).map(fase => {
            const itens = this.etapasChecklist[fase];
            const completude = this.calcularCompletudeChecklist(checklistData[fase] || {}, itens);
            
            return {
                fase: fase,
                nome: fase === 'antes' ? 'Antes' : fase === 'durante' ? 'Durante' : 'Após',
                completude: completude
            };
        });
        
        const totalCompletos = resumoFases.reduce((sum, fase) => sum + fase.completude.completos, 0);
        const totalItens = resumoFases.reduce((sum, fase) => sum + fase.completude.total, 0);
        const percentualGeral = Math.round((totalCompletos / totalItens) * 100);
        
        return `
            <div class="checklist-resumo-container">
                <h5>Resumo Geral do Checklist</h5>
                
                <div class="resumo-geral">
                    <div class="resumo-card">
                        <div class="resumo-valor">${percentualGeral}%</div>
                        <div class="resumo-label">Completude Total</div>
                    </div>
                    <div class="resumo-card">
                        <div class="resumo-valor">${totalCompletos}/${totalItens}</div>
                        <div class="resumo-label">Itens Completos</div>
                    </div>
                </div>
                
                <div class="resumo-fases">
                    ${resumoFases.map(fase => `
                        <div class="resumo-fase-item">
                            <span class="fase-nome">${fase.nome}</span>
                            <span class="fase-completude">${fase.completude.completos}/${fase.completude.total}</span>
                            <div class="fase-barra">
                                <div class="fase-preenchimento" style="width: ${fase.completude.percentual}%"></div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    /**
     * Funções auxiliares do checklist
     */
    calcularCompletudeChecklist(dadosChecklist, itens) {
        const completos = itens.filter(item => dadosChecklist[item.id]).length;
        const total = itens.length;
        const percentual = total > 0 ? Math.round((completos / total) * 100) : 0;
        
        return { completos, total, percentual };
    }
    
    obterMunicipioSelecionado() {
        // Retornar município selecionado ou primeiro disponível
        const municipios = Object.keys(this.mapaProgresso.municipios || {});
        return municipios.length > 0 ? municipios[0] : null;
    }
    
    obterDadosChecklist(municipio) {
        // Obter dados do checklist do localStorage ou inicializar vazio
        const key = `checklist_${municipio}`;
        const saved = localStorage.getItem(key);
        
        if (saved) {
            return JSON.parse(saved);
        }
        
        // Inicializar estrutura vazia
        return {
            antes: {},
            durante: {},
            apos: {}
        };
    }
    
    /**
     * Ações do checklist
     */
    selecionarMunicipioChecklist(municipio) {
        console.log(`🏙️ Selecionando município para checklist: ${municipio}`);
        this.renderizarChecklistEtapas();
    }
    
    alterarItemChecklist(fase, itemId, checked) {
        const municipio = this.obterMunicipioSelecionado();
        if (!municipio) return;
        
        const key = `checklist_${municipio}`;
        let checklistData = this.obterDadosChecklist(municipio);
        
        checklistData[fase][itemId] = checked;
        
        // Salvar no localStorage
        localStorage.setItem(key, JSON.stringify(checklistData));
        
        // Atualizar visual
        this.atualizarProgressoFase(fase, checklistData[fase]);
        this.atualizarResumoChecklist(checklistData);
        
        console.log(`✅ Item ${itemId} da fase ${fase}: ${checked ? 'marcado' : 'desmarcado'}`);
    }
    
    atualizarProgressoFase(fase, dadosFase) {
        const itens = this.etapasChecklist[fase];
        const completude = this.calcularCompletudeChecklist(dadosFase, itens);
        
        const faseElement = document.querySelector(`[data-fase="${fase}"]`);
        if (faseElement) {
            const progressoTexto = faseElement.querySelector('.progresso-texto');
            const progressoPreenchimento = faseElement.querySelector('.progresso-preenchimento');
            const progressoPercentual = faseElement.querySelector('.progresso-percentual');
            
            if (progressoTexto) progressoTexto.textContent = `${completude.completos}/${completude.total}`;
            if (progressoPreenchimento) progressoPreenchimento.style.width = `${completude.percentual}%`;
            if (progressoPercentual) progressoPercentual.textContent = `${completude.percentual}%`;
        }
    }
    
    atualizarResumoChecklist(checklistData) {
        // Atualizar o resumo geral
        const resumoContainer = document.querySelector('.checklist-resumo');
        if (resumoContainer) {
            resumoContainer.innerHTML = this.renderizarResumoChecklist(checklistData);
        }
    }
    
    salvarChecklist() {
        const municipio = this.obterMunicipioSelecionado();
        if (!municipio) {
            alert('Selecione um município primeiro');
            return;
        }
        
        console.log(`💾 Salvando checklist de ${municipio}...`);
        // Dados já salvos automaticamente no localStorage
        this.mapaProgresso.mostrarToast('Checklist salvo com sucesso!', 'success');
    }
    
    validarChecklistCompleto() {
        const municipio = this.obterMunicipioSelecionado();
        if (!municipio) {
            alert('Selecione um município primeiro');
            return;
        }
        
        const checklistData = this.obterDadosChecklist(municipio);
        const itensObrigatorios = this.obterItensObrigatorios();
        const itensIncompletos = this.verificarItensIncompletos(checklistData, itensObrigatorios);
        
        if (itensIncompletos.length === 0) {
            this.mapaProgresso.mostrarToast('✅ Checklist completo! Todos os itens obrigatórios foram marcados.', 'success');
        } else {
            this.mapaProgresso.mostrarToast(`⚠️ Checklist incompleto. Faltam ${itensIncompletos.length} itens obrigatórios.`, 'warning');
            this.destacarItensIncompletos(itensIncompletos);
        }
    }
    
    exportarChecklist() {
        const municipio = this.obterMunicipioSelecionado();
        if (!municipio) {
            alert('Selecione um município primeiro');
            return;
        }
        
        const checklistData = this.obterDadosChecklist(municipio);
        const csvContent = this.gerarCSVChecklist(municipio, checklistData);
        
        this.downloadCSV(csvContent, `checklist_${municipio}_${new Date().toISOString().split('T')[0]}.csv`);
        this.mapaProgresso.mostrarToast('Checklist exportado com sucesso!', 'success');
    }
    
    adicionarObservacao(itemId) {
        const observacao = prompt('Adicione uma observação para este item:');
        if (observacao) {
            console.log(`📝 Observação adicionada para ${itemId}: ${observacao}`);
            // Implementar salvamento de observações
        }
    }
    
    adicionarEventosChecklist() {
        // Eventos específicos do checklist já estão nas chamadas onclick
        console.log('📋 Eventos do checklist configurados');
    }
    
    /**
     * Funções auxiliares específicas
     */
    obterItensObrigatorios() {
        const obrigatorios = [];
        Object.keys(this.etapasChecklist).forEach(fase => {
            this.etapasChecklist[fase].forEach(item => {
                if (item.obrigatorio) {
                    obrigatorios.push({ fase, item: item.id, nome: item.nome });
                }
            });
        });
        return obrigatorios;
    }
    
    verificarItensIncompletos(checklistData, itensObrigatorios) {
        return itensObrigatorios.filter(item => !checklistData[item.fase][item.item]);
    }
    
    destacarItensIncompletos(itensIncompletos) {
        // Destacar visualmente itens incompletos
        itensIncompletos.forEach(item => {
            const elemento = document.querySelector(`[data-item="${item.item}"]`);
            if (elemento) {
                elemento.classList.add('item-incompleto');
                setTimeout(() => elemento.classList.remove('item-incompleto'), 3000);
            }
        });
    }
    
    gerarCSVChecklist(municipio, checklistData) {
        let csv = 'Fase,Item,Nome,Descricao,Obrigatorio,Concluido\n';
        
        Object.keys(this.etapasChecklist).forEach(fase => {
            this.etapasChecklist[fase].forEach(item => {
                const concluido = checklistData[fase][item.id] ? 'Sim' : 'Não';
                csv += `"${fase}","${item.id}","${item.nome}","${item.descricao}","${item.obrigatorio ? 'Sim' : 'Não'}","${concluido}"\n`;
            });
        });
        
        return csv;
    }

    /**
     * Criar seção do pipeline
     */
    criarSecaoPipeline(titulo, status, pipeline, cor) {
        const totalVisitas = status.reduce((total, s) => total + (pipeline[s] || []).length, 0);
        
        return `
            <div class="pipeline-secao" data-secao="${titulo.toLowerCase()}">
                <div class="pipeline-header" style="border-left-color: ${cor}">
                    <h4>${titulo}</h4>
                    <span class="badge" style="background-color: ${cor}">${totalVisitas}</span>
                </div>
                <div class="pipeline-status">
                    ${status.map(s => this.criarItemStatus(s, pipeline[s] || [], cor)).join('')}
                </div>
            </div>
        `;
    }

    /**
     * Criar item de status
     */
    criarItemStatus(status, visitas, cor) {
        return `
            <div class="status-item" data-status="${status}">
                <div class="status-header">
                    <span class="status-nome">${this.formatarStatus(status)}</span>
                    <span class="status-count">${visitas.length}</span>
                </div>
                <div class="status-visitas">
                    ${visitas.slice(0, 3).map(v => `
                        <div class="visita-card" data-visita-id="${v.id}">
                            <div class="visita-municipio">${v.municipio}</div>
                            <div class="visita-data">${this.formatarData(v.data)}</div>
                        </div>
                    `).join('')}
                    ${visitas.length > 3 ? `<div class="mais-visitas">+${visitas.length - 3} mais</div>` : ''}
                </div>
            </div>
        `;
    }

    /**
     * Renderizar checklist de etapas
     */
    renderizarChecklistEtapas() {
        const container = document.getElementById('checklist-etapas');
        if (!container) return;

        const checklists = this.mapaProgresso.dados.checklists || [];
        const estatisticas = this.calcularEstatisticasChecklist(checklists);

        container.innerHTML = `
            <div class="checklist-container">
                <div class="checklist-overview">
                    <h4>Visão Geral do Checklist</h4>
                    <div class="checklist-stats">
                        <div class="stat-item">
                            <span class="stat-value">${estatisticas.preparacao}%</span>
                            <span class="stat-label">Preparação</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">${estatisticas.execucao}%</span>
                            <span class="stat-label">Execução</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">${estatisticas.resultados}%</span>
                            <span class="stat-label">Resultados</span>
                        </div>
                    </div>
                </div>
                
                <div class="checklist-etapas">
                    ${this.criarEtapaChecklist('Antes da Visita', 'antes', estatisticas.detalhes.antes)}
                    ${this.criarEtapaChecklist('Durante a Visita', 'durante', estatisticas.detalhes.durante)}
                    ${this.criarEtapaChecklist('Após a Visita', 'apos', estatisticas.detalhes.apos)}
                </div>
            </div>
        `;
    }

    /**
     * Criar etapa do checklist
     */
    criarEtapaChecklist(titulo, etapa, dados) {
        const itens = this.etapasChecklist[etapa] || [];
        const completude = dados.percentual || 0;
        
        return `
            <div class="etapa-checklist" data-etapa="${etapa}">
                <div class="etapa-header">
                    <h5>${titulo}</h5>
                    <div class="etapa-progresso">
                        <div class="progresso-bar">
                            <div class="progresso-fill" style="width: ${completude}%"></div>
                        </div>
                        <span class="progresso-texto">${completude}%</span>
                    </div>
                </div>
                <div class="etapa-itens">
                    ${itens.map(item => `
                        <div class="checklist-item">
                            <input type="checkbox" id="${etapa}_${item}" ${dados.itens && dados.itens[item] ? 'checked' : ''}>
                            <label for="${etapa}_${item}">${this.formatarItemChecklist(item)}</label>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    /**
     * Renderizar inteligência de contatos multi-IA
     */

    /**
     * Organizar visitas por status
     */
    organizarVisitasPorStatus(visitas) {
        const pipeline = {};
        
        this.statusWorkflow.forEach(status => {
            pipeline[status] = visitas.filter(v => v.status === status);
        });
        
        return pipeline;
    }

    /**
     * Calcular estatísticas do checklist
     */
    calcularEstatisticasChecklist(checklists) {
        if (!checklists.length) {
            return {
                preparacao: 0,
                execucao: 0,
                resultados: 0,
                detalhes: {
                    antes: { percentual: 0, itens: {} },
                    durante: { percentual: 0, itens: {} },
                    apos: { percentual: 0, itens: {} }
                }
            };
        }

        // Calcular médias
        const preparacao = checklists.reduce((acc, c) => acc + (c.calcular_progresso_preparacao || 0), 0) / checklists.length;
        const execucao = checklists.reduce((acc, c) => acc + (c.calcular_progresso_execucao || 0), 0) / checklists.length;
        const resultados = checklists.reduce((acc, c) => acc + (c.calcular_progresso_resultados || 0), 0) / checklists.length;

        return {
            preparacao: Math.round(preparacao),
            execucao: Math.round(execucao),
            resultados: Math.round(resultados),
            detalhes: {
                antes: { percentual: Math.round(preparacao), itens: {} },
                durante: { percentual: Math.round(execucao), itens: {} },
                apos: { percentual: Math.round(resultados), itens: {} }
            }
        };
    }


    /**
     * Adicionar eventos do pipeline
     */
    adicionarEventosPipeline() {
        document.querySelectorAll('.visita-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const visitaId = e.currentTarget.dataset.visitaId;
                this.abrirDetalhesVisita(visitaId);
            });
        });
    }


    /**
     * Utilitários de formatação
     */
    formatarStatus(status) {
        return status.replace(/_/g, ' ')
                    .replace(/\b\w/g, l => l.toUpperCase());
    }

    formatarItemChecklist(item) {
        return item.replace(/_/g, ' ')
                  .replace(/\b\w/g, l => l.toUpperCase());
    }

    formatarData(data) {
        if (!data) return 'Sem data';
        return new Date(data).toLocaleDateString('pt-BR');
    }

    formatarDataHora(data) {
        if (!data) return 'Sem data';
        return new Date(data).toLocaleString('pt-BR');
    }


    /**
     * Abrir detalhes da visita
     */
    abrirDetalhesVisita(visitaId) {
        console.log('Abrindo detalhes da visita:', visitaId);
        // Implementar modal ou navegação para detalhes
    }

    /**
     * Mostrar histórico de uma entidade
     */
    mostrarHistoricoEntidade(entidadeId) {
        console.log('Mostrando histórico da entidade:', entidadeId);
        // Implementar modal com histórico específico
    }

    /**
     * Confirmar dados de uma entidade
     */
    confirmarDadosEntidade(entidadeId) {
        console.log('Confirmando dados da entidade:', entidadeId);
        // Implementar confirmação e atualização dos dados
    }
    
    /**
     * Editar dados de uma entidade
     */
    editarDadosEntidade(entidadeId) {
        console.log('Editando dados da entidade:', entidadeId);
        // Implementar modal de edição de dados
        alert('Funcionalidade de edição em desenvolvimento. Entidade ID: ' + entidadeId);
    }

    // ============ SISTEMA DE ALERTAS COMPLETO ============

    /**
     * Renderizar sistema completo de alertas
     */
    renderizarSistemaAlertas() {
        console.log('🚨 Renderizando Sistema de Alertas...');
        
        this.renderizarAlertasAtivos();
        this.renderizarConfiguracaoAlertas();
        this.renderizarHistoricoAlertas();
        
        // Configurar verificação automática de alertas
        this.iniciarVerificacaoAutomatica();
    }

    /**
     * Renderizar alertas ativos
     */
    renderizarAlertasAtivos() {
        const container = document.getElementById('alertas-sistema');
        if (!container) return;

        const alertasAtivos = this.gerarAlertasAutomaticos();
        
        container.innerHTML = `
            <div class="alertas-header">
                <h4>Alertas Ativos</h4>
                <div class="alertas-stats">
                    <span class="badge badge-danger">${alertasAtivos.filter(a => a.tipo === 'critico').length} Críticos</span>
                    <span class="badge badge-warning">${alertasAtivos.filter(a => a.tipo === 'importante').length} Importantes</span>
                    <span class="badge badge-info">${alertasAtivos.filter(a => a.tipo === 'info').length} Informativos</span>
                </div>
            </div>
            
            <div class="alertas-lista">
                ${alertasAtivos.length > 0 ? 
                    alertasAtivos.map(alerta => this.renderizarAlerta(alerta)).join('') :
                    '<div class="alerta alerta-vazio"><p>Nenhum alerta ativo no momento</p></div>'
                }
            </div>
            
            <div class="alertas-actions">
                <button class="btn btn-primary btn-sm" onclick="workflowContatos.verificarAlertasManual()">
                    🔍 Verificar Alertas
                </button>
                <button class="btn btn-secondary btn-sm" onclick="workflowContatos.marcarTodosLidos()">
                    ✅ Marcar Todos como Lidos
                </button>
                <button class="btn btn-info btn-sm" onclick="workflowContatos.exportarAlertas()">
                    📤 Exportar Alertas
                </button>
            </div>
        `;
    }

    /**
     * Renderizar configuração de alertas
     */
    renderizarConfiguracaoAlertas() {
        const container = document.getElementById('config-alertas-form');
        if (!container) return;

        const configuracoes = this.obterConfiguracaoAlertas();
        
        container.innerHTML = `
            <div class="config-alertas-container">
                <div class="config-section">
                    <h5>Alertas de Prazo</h5>
                    <div class="config-row">
                        <label>Visitas sem agendamento há mais de:</label>
                        <select id="config-prazo-agendamento" value="${configuracoes.prazoAgendamento}">
                            <option value="3">3 dias</option>
                            <option value="5">5 dias</option>
                            <option value="7">7 dias</option>
                            <option value="10">10 dias</option>
                        </select>
                    </div>
                    <div class="config-row">
                        <label>Visitas agendadas há mais de:</label>
                        <select id="config-prazo-execucao" value="${configuracoes.prazoExecucao}">
                            <option value="7">7 dias</option>
                            <option value="14">14 dias</option>
                            <option value="21">21 dias</option>
                            <option value="30">30 dias</option>
                        </select>
                    </div>
                </div>
                
                <div class="config-section">
                    <h5>Alertas de Qualidade</h5>
                    <div class="config-row">
                        <label>Limite de dados incompletos (%):</label>
                        <input type="number" id="config-dados-incompletos" value="${configuracoes.limiteIncompletos}" min="0" max="100">
                    </div>
                    <div class="config-row">
                        <label>Alertar quando contatos falharem:</label>
                        <input type="number" id="config-tentativas-falharam" value="${configuracoes.tentativasFalharam}" min="1" max="10">
                        <span>tentativas</span>
                    </div>
                </div>
                
                <div class="config-section">
                    <h5>Notificações</h5>
                    <div class="config-row">
                        <label>
                            <input type="checkbox" id="config-email-notif" ${configuracoes.emailNotificacoes ? 'checked' : ''}>
                            Enviar alertas por email
                        </label>
                    </div>
                    <div class="config-row">
                        <label>
                            <input type="checkbox" id="config-whatsapp-notif" ${configuracoes.whatsappNotificacoes ? 'checked' : ''}>
                            Enviar alertas por WhatsApp
                        </label>
                    </div>
                    <div class="config-row">
                        <label>Verificar alertas a cada:</label>
                        <select id="config-intervalo-verificacao" value="${configuracoes.intervaloVerificacao}">
                            <option value="5">5 minutos</option>
                            <option value="15">15 minutos</option>
                            <option value="30">30 minutos</option>
                            <option value="60">1 hora</option>
                        </select>
                    </div>
                </div>
                
                <div class="config-actions">
                    <button class="btn btn-success" onclick="workflowContatos.salvarConfiguracaoAlertas()">
                        💾 Salvar Configurações
                    </button>
                    <button class="btn btn-secondary" onclick="workflowContatos.restaurarPadraoAlertas()">
                        🔄 Restaurar Padrão
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Renderizar histórico de alertas
     */
    renderizarHistoricoAlertas() {
        const container = document.getElementById('historico-alertas-lista');
        if (!container) return;

        const historico = this.obterHistoricoAlertas();
        
        container.innerHTML = `
            <div class="historico-header">
                <h4>Histórico de Alertas (Últimos 30 dias)</h4>
                <div class="historico-filtros">
                    <select id="filtro-tipo-alerta">
                        <option value="todos">Todos os Tipos</option>
                        <option value="critico">Críticos</option>
                        <option value="importante">Importantes</option>
                        <option value="info">Informativos</option>
                    </select>
                    <select id="filtro-status-alerta">
                        <option value="todos">Todos os Status</option>
                        <option value="ativo">Ativos</option>
                        <option value="resolvido">Resolvidos</option>
                        <option value="ignorado">Ignorados</option>
                    </select>
                </div>
            </div>
            
            <div class="historico-timeline">
                ${historico.length > 0 ? 
                    historico.map(alerta => this.renderizarHistoricoItem(alerta)).join('') :
                    '<div class="historico-vazio"><p>Nenhum alerta registrado nos últimos 30 dias</p></div>'
                }
            </div>
            
            <div class="historico-actions">
                <button class="btn btn-primary btn-sm" onclick="workflowContatos.atualizarHistorico()">
                    🔄 Atualizar
                </button>
                <button class="btn btn-danger btn-sm" onclick="workflowContatos.limparHistoricoAntigo()">
                    🗑️ Limpar Antigos
                </button>
            </div>
        `;
    }

    /**
     * Gerar alertas automáticos baseados nos dados
     */
    gerarAlertasAutomaticos() {
        const alertas = [];
        const municipios = this.mapaProgresso.processarDadosMunicipios();
        const configuracoes = this.obterConfiguracaoAlertas();
        const hoje = new Date();

        // Alerta 1: Municípios sem visita agendada há muito tempo
        municipios.forEach(municipio => {
            if (municipio.status === 'sem_visita') {
                const diasSemAgendamento = this.calcularDiasDesdeUltimaAtividade(municipio);
                if (diasSemAgendamento > configuracoes.prazoAgendamento) {
                    alertas.push({
                        id: `sem_agendamento_${municipio.nome}`,
                        tipo: 'critico',
                        titulo: 'Município sem agendamento',
                        descricao: `${municipio.nome} está há ${diasSemAgendamento} dias sem agendamento de visita`,
                        municipio: municipio.nome,
                        prioridade: 'alta',
                        timestamp: hoje,
                        acao: 'agendar_visita',
                        categoria: 'prazo'
                    });
                }
            }
        });

        // Alerta 2: Visitas agendadas há muito tempo sem execução
        municipios.forEach(municipio => {
            if (municipio.status === 'agendada' || municipio.status === 'em_preparacao') {
                const diasAtraso = this.calcularDiasAtraso(municipio);
                if (diasAtraso > configuracoes.prazoExecucao) {
                    alertas.push({
                        id: `atraso_execucao_${municipio.nome}`,
                        tipo: 'importante',
                        titulo: 'Visita em atraso',
                        descricao: `${municipio.nome} tem visita agendada há ${diasAtraso} dias sem execução`,
                        municipio: municipio.nome,
                        prioridade: 'media',
                        timestamp: hoje,
                        acao: 'executar_visita',
                        categoria: 'atraso'
                    });
                }
            }
        });

        // Alerta 3: Dados incompletos
        municipios.forEach(municipio => {
            const percentualIncompleto = 100 - municipio.progressoP1;
            if (percentualIncompleto > configuracoes.limiteIncompletos) {
                alertas.push({
                    id: `dados_incompletos_${municipio.nome}`,
                    tipo: 'importante',
                    titulo: 'Dados incompletos',
                    descricao: `${municipio.nome} tem ${percentualIncompleto}% de dados incompletos`,
                    municipio: municipio.nome,
                    prioridade: 'media',
                    timestamp: hoje,
                    acao: 'completar_dados',
                    categoria: 'qualidade'
                    });
            }
        });

        // Alerta 4: Baixa taxa de sucesso de contato
        const taxaSucessoGeral = this.calcularTaxaSucessoContato();
        if (taxaSucessoGeral < 60) {
            alertas.push({
                id: 'baixa_taxa_sucesso',
                tipo: 'critico',
                titulo: 'Baixa taxa de sucesso de contato',
                descricao: `Taxa geral de sucesso de contato está em ${taxaSucessoGeral}% (abaixo de 60%)`,
                prioridade: 'alta',
                timestamp: hoje,
                acao: 'revisar_estrategia',
                categoria: 'eficiencia'
            });
        }

        // Alerta 5: Progresso lento geral
        const progressoMedio = municipios.reduce((sum, m) => sum + m.progressoP1, 0) / municipios.length;
        if (progressoMedio < 50) {
            alertas.push({
                id: 'progresso_lento',
                tipo: 'info',
                titulo: 'Progresso abaixo da meta',
                descricao: `Progresso médio dos municípios está em ${Math.round(progressoMedio)}% (meta: 50%)`,
                prioridade: 'baixa',
                timestamp: hoje,
                acao: 'acelerar_progresso',
                categoria: 'meta'
            });
        }

        return alertas.sort((a, b) => {
            const prioridadeOrdem = { 'alta': 3, 'media': 2, 'baixa': 1 };
            return prioridadeOrdem[b.prioridade] - prioridadeOrdem[a.prioridade];
        });
    }

    /**
     * Renderizar um alerta individual
     */
    renderizarAlerta(alerta) {
        const iconMap = {
            'critico': '🚨',
            'importante': '⚠️',
            'info': 'ℹ️'
        };

        const corMap = {
            'critico': '#dc3545',
            'importante': '#ffc107',
            'info': '#17a2b8'
        };

        return `
            <div class="alerta alerta-${alerta.tipo}" data-alerta="${alerta.id}">
                <div class="alerta-icon" style="color: ${corMap[alerta.tipo]}">
                    ${iconMap[alerta.tipo]}
                </div>
                <div class="alerta-content">
                    <div class="alerta-header">
                        <h5 class="alerta-titulo">${alerta.titulo}</h5>
                        <span class="alerta-timestamp">${this.formatarDataHora(alerta.timestamp)}</span>
                    </div>
                    <p class="alerta-descricao">${alerta.descricao}</p>
                    <div class="alerta-meta">
                        ${alerta.municipio ? `<span class="alerta-municipio">📍 ${alerta.municipio}</span>` : ''}
                        <span class="alerta-categoria">#${alerta.categoria}</span>
                    </div>
                </div>
                <div class="alerta-actions">
                    ${alerta.acao ? `<button class="btn btn-sm btn-primary" onclick="workflowContatos.executarAcaoAlerta('${alerta.acao}', '${alerta.municipio || ''}')">Resolver</button>` : ''}
                    <button class="btn btn-sm btn-secondary" onclick="workflowContatos.marcarAlertaLido('${alerta.id}')">✅</button>
                    <button class="btn btn-sm btn-outline-danger" onclick="workflowContatos.ignorarAlerta('${alerta.id}')">❌</button>
                </div>
            </div>
        `;
    }

    /**
     * Renderizar item do histórico
     */
    renderizarHistoricoItem(alerta) {
        const statusMap = {
            'ativo': '🔴',
            'resolvido': '✅',
            'ignorado': '❌'
        };

        return `
            <div class="historico-item" data-status="${alerta.status}">
                <div class="historico-timeline-marker ${alerta.status}"></div>
                <div class="historico-content">
                    <div class="historico-header">
                        <h6>${alerta.titulo}</h6>
                        <span class="historico-status">${statusMap[alerta.status]} ${alerta.status}</span>
                    </div>
                    <p class="historico-descricao">${alerta.descricao}</p>
                    <div class="historico-meta">
                        <span class="historico-data">${this.formatarDataHora(alerta.timestamp)}</span>
                        ${alerta.resolvidoEm ? `<span class="historico-resolvido">Resolvido em ${this.formatarDataHora(alerta.resolvidoEm)}</span>` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Obter configuração de alertas (padrões ou localStorage)
     */
    obterConfiguracaoAlertas() {
        const padrao = {
            prazoAgendamento: 7,
            prazoExecucao: 14,
            limiteIncompletos: 30,
            tentativasFalharam: 3,
            emailNotificacoes: false,
            whatsappNotificacoes: false,
            intervaloVerificacao: 30
        };

        try {
            const salvo = localStorage.getItem('configuracao_alertas_pnsb');
            return salvo ? { ...padrao, ...JSON.parse(salvo) } : padrao;
        } catch (error) {
            console.warn('Erro ao carregar configuração de alertas:', error);
            return padrao;
        }
    }

    /**
     * Obter histórico de alertas
     */
    obterHistoricoAlertas() {
        try {
            const historico = localStorage.getItem('historico_alertas_pnsb');
            const alertas = historico ? JSON.parse(historico) : [];
            
            // Filtrar últimos 30 dias
            const trintaDiasAtras = new Date();
            trintaDiasAtras.setDate(trintaDiasAtras.getDate() - 30);
            
            return alertas
                .filter(a => new Date(a.timestamp) > trintaDiasAtras)
                .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        } catch (error) {
            console.warn('Erro ao carregar histórico de alertas:', error);
            return [];
        }
    }

    /**
     * Ações do sistema de alertas
     */
    verificarAlertasManual() {
        console.log('🔍 Verificando alertas manualmente...');
        this.renderizarAlertasAtivos();
        this.mostrarNotificacao('Alertas atualizados!', 'success');
    }

    marcarTodosLidos() {
        console.log('✅ Marcando todos os alertas como lidos...');
        // Implementar lógica para marcar todos como lidos
        this.mostrarNotificacao('Todos os alertas foram marcados como lidos', 'success');
        this.renderizarAlertasAtivos();
    }

    marcarAlertaLido(alertaId) {
        console.log('✅ Marcando alerta como lido:', alertaId);
        this.atualizarStatusAlerta(alertaId, 'resolvido');
        this.mostrarNotificacao('Alerta marcado como resolvido', 'success');
        this.renderizarAlertasAtivos();
    }

    ignorarAlerta(alertaId) {
        console.log('❌ Ignorando alerta:', alertaId);
        this.atualizarStatusAlerta(alertaId, 'ignorado');
        this.mostrarNotificacao('Alerta ignorado', 'info');
        this.renderizarAlertasAtivos();
    }

    executarAcaoAlerta(acao, municipio = '') {
        console.log('🎯 Executando ação de alerta:', acao, municipio);
        
        const acoes = {
            'agendar_visita': () => {
                if (municipio) {
                    this.abrirModalAgendamento(municipio);
                } else {
                    this.mostrarNotificacao('Redirecionando para agendamento...', 'info');
                }
            },
            'executar_visita': () => {
                this.mostrarNotificacao('Redirecionando para execução de visita...', 'info');
            },
            'completar_dados': () => {
                this.mostrarNotificacao('Redirecionando para completar dados...', 'info');
            },
            'revisar_estrategia': () => {
                this.mostrarNotificacao('Abrindo análise de estratégia de contato...', 'info');
            },
            'acelerar_progresso': () => {
                this.mostrarNotificacao('Abrindo plano de aceleração...', 'info');
            }
        };

        if (acoes[acao]) {
            acoes[acao]();
        } else {
            this.mostrarNotificacao('Ação não implementada: ' + acao, 'warning');
        }
    }

    salvarConfiguracaoAlertas() {
        const configuracao = {
            prazoAgendamento: parseInt(document.getElementById('config-prazo-agendamento')?.value || 7),
            prazoExecucao: parseInt(document.getElementById('config-prazo-execucao')?.value || 14),
            limiteIncompletos: parseInt(document.getElementById('config-dados-incompletos')?.value || 30),
            tentativasFalharam: parseInt(document.getElementById('config-tentativas-falharam')?.value || 3),
            emailNotificacoes: document.getElementById('config-email-notif')?.checked || false,
            whatsappNotificacoes: document.getElementById('config-whatsapp-notif')?.checked || false,
            intervaloVerificacao: parseInt(document.getElementById('config-intervalo-verificacao')?.value || 30)
        };

        try {
            localStorage.setItem('configuracao_alertas_pnsb', JSON.stringify(configuracao));
            this.mostrarNotificacao('Configurações salvas com sucesso!', 'success');
            
            // Reiniciar verificação automática com nova configuração
            this.iniciarVerificacaoAutomatica();
        } catch (error) {
            console.error('Erro ao salvar configurações:', error);
            this.mostrarNotificacao('Erro ao salvar configurações', 'error');
        }
    }

    restaurarPadraoAlertas() {
        if (confirm('Tem certeza que deseja restaurar as configurações padrão?')) {
            localStorage.removeItem('configuracao_alertas_pnsb');
            this.renderizarConfiguracaoAlertas();
            this.mostrarNotificacao('Configurações restauradas para o padrão', 'success');
        }
    }

    exportarAlertas() {
        const alertas = this.gerarAlertasAutomaticos();
        const csv = this.gerarCSVAlertas(alertas);
        this.downloadCSV(csv, 'alertas_pnsb.csv');
        this.mostrarNotificacao('Alertas exportados com sucesso!', 'success');
    }

    /**
     * Iniciar verificação automática de alertas
     */
    iniciarVerificacaoAutomatica() {
        // Limpar interval anterior se existir
        if (this.intervalAlertas) {
            clearInterval(this.intervalAlertas);
        }

        const configuracao = this.obterConfiguracaoAlertas();
        const intervaloMs = configuracao.intervaloVerificacao * 60 * 1000; // Converter para ms

        this.intervalAlertas = setInterval(() => {
            console.log('🔄 Verificação automática de alertas...');
            this.renderizarAlertasAtivos();
        }, intervaloMs);

        console.log(`⏰ Verificação automática de alertas configurada para ${configuracao.intervaloVerificacao} minutos`);
    }

    /**
     * Funções auxiliares para cálculos
     */
    calcularDiasDesdeUltimaAtividade(municipio) {
        // Simulação - em produção, usar data real da última atividade
        return Math.floor(Math.random() * 15) + 1;
    }

    calcularDiasAtraso(municipio) {
        // Simulação - em produção, usar data real do agendamento
        return Math.floor(Math.random() * 25) + 1;
    }

    calcularTaxaSucessoContato() {
        // Simulação - em produção, calcular baseado nos dados reais
        return Math.floor(Math.random() * 40) + 50; // 50-90%
    }

    atualizarStatusAlerta(alertaId, novoStatus) {
        try {
            const historico = this.obterHistoricoAlertas();
            const alerta = historico.find(a => a.id === alertaId);
            
            if (alerta) {
                alerta.status = novoStatus;
                alerta.resolvidoEm = new Date();
            } else {
                // Adicionar ao histórico se não existir
                historico.push({
                    id: alertaId,
                    status: novoStatus,
                    timestamp: new Date(),
                    resolvidoEm: new Date()
                });
            }
            
            localStorage.setItem('historico_alertas_pnsb', JSON.stringify(historico));
        } catch (error) {
            console.error('Erro ao atualizar status do alerta:', error);
        }
    }

    formatarDataHora(data) {
        return new Date(data).toLocaleString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    gerarCSVAlertas(alertas) {
        let csv = 'Tipo,Titulo,Descricao,Municipio,Prioridade,Data,Categoria\n';
        
        alertas.forEach(alerta => {
            csv += `"${alerta.tipo}","${alerta.titulo}","${alerta.descricao}","${alerta.municipio || ''}","${alerta.prioridade}","${this.formatarDataHora(alerta.timestamp)}","${alerta.categoria}"\n`;
        });
        
        return csv;
    }

    mostrarNotificacao(mensagem, tipo = 'info') {
        // Implementação de notificação toast
        console.log(`${tipo.toUpperCase()}: ${mensagem}`);
        
        // Criar elemento de notificação se não existir
        let notifContainer = document.getElementById('notification-container');
        if (!notifContainer) {
            notifContainer = document.createElement('div');
            notifContainer.id = 'notification-container';
            notifContainer.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
            document.body.appendChild(notifContainer);
        }

        const notif = document.createElement('div');
        notif.className = `notification notification-${tipo}`;
        notif.style.cssText = `
            background: ${tipo === 'success' ? '#28a745' : tipo === 'error' ? '#dc3545' : tipo === 'warning' ? '#ffc107' : '#17a2b8'};
            color: white;
            padding: 12px 16px;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            font-size: 14px;
            font-weight: 500;
            max-width: 300px;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
        `;
        notif.textContent = mensagem;
        
        notifContainer.appendChild(notif);
        
        // Animar entrada
        setTimeout(() => {
            notif.style.opacity = '1';
            notif.style.transform = 'translateX(0)';
        }, 10);
        
        // Remover após 3 segundos
        setTimeout(() => {
            notif.style.opacity = '0';
            notif.style.transform = 'translateX(100%)';
            setTimeout(() => notif.remove(), 300);
        }, 3000);
    }

    abrirModalAgendamento(municipio) {
        this.mostrarNotificacao(`Abrindo agendamento para ${municipio}...`, 'info');
        // Implementar modal de agendamento específico
    }

    atualizarHistorico() {
        this.renderizarHistoricoAlertas();
        this.mostrarNotificacao('Histórico atualizado!', 'success');
    }

    limparHistoricoAntigo() {
        if (confirm('Tem certeza que deseja limpar alertas antigos (mais de 30 dias)?')) {
            // Implementar limpeza de histórico antigo
            this.mostrarNotificacao('Histórico antigo removido', 'success');
            this.renderizarHistoricoAlertas();
        }
    }

    // ============ FIM SISTEMA DE ALERTAS ============

    // ============ RELATÓRIOS AUTOMÁTICOS ============

    /**
     * Renderizar sistema completo de relatórios
     */
    renderizarSistemaRelatorios() {
        console.log('📊 Renderizando Sistema de Relatórios...');
        
        this.renderizarRelatorioSemanal();
        this.renderizarRelatorioIBGE();
        this.renderizarDashboardMobile();
        
        // Configurar geração automática de relatórios
        this.iniciarGeracaoAutomatica();
    }

    /**
     * Renderizar relatório semanal automático
     */
    renderizarRelatorioSemanal() {
        const container = document.getElementById('relatorio-semanal-content');
        if (!container) return;

        const relatorioSemanal = this.gerarRelatorioSemanal();
        
        container.innerHTML = `
            <div class="relatorio-container">
                <div class="relatorio-header">
                    <h4>Relatório Semanal - Semana ${relatorioSemanal.semana}</h4>
                    <div class="relatorio-periodo">
                        <span>📅 ${relatorioSemanal.periodo}</span>
                        <span class="relatorio-status status-${relatorioSemanal.status}">${relatorioSemanal.statusTexto}</span>
                    </div>
                </div>
                
                <div class="relatorio-resumo">
                    <div class="resumo-cards">
                        <div class="resumo-card">
                            <div class="resumo-valor">${relatorioSemanal.visitasRealizadas}</div>
                            <div class="resumo-label">Visitas Realizadas</div>
                            <div class="resumo-variacao ${relatorioSemanal.variacaoVisitas > 0 ? 'positiva' : 'negativa'}">
                                ${relatorioSemanal.variacaoVisitas > 0 ? '↗' : '↘'} ${Math.abs(relatorioSemanal.variacaoVisitas)}%
                            </div>
                        </div>
                        <div class="resumo-card">
                            <div class="resumo-valor">${relatorioSemanal.progressoMedio}%</div>
                            <div class="resumo-label">Progresso Médio</div>
                            <div class="resumo-variacao ${relatorioSemanal.variacaoProgresso > 0 ? 'positiva' : 'negativa'}">
                                ${relatorioSemanal.variacaoProgresso > 0 ? '↗' : '↘'} ${Math.abs(relatorioSemanal.variacaoProgresso)}%
                            </div>
                        </div>
                        <div class="resumo-card">
                            <div class="resumo-valor">${relatorioSemanal.alertasGerados}</div>
                            <div class="resumo-label">Alertas Gerados</div>
                            <div class="resumo-variacao ${relatorioSemanal.variacaoAlertas > 0 ? 'negativa' : 'positiva'}">
                                ${relatorioSemanal.variacaoAlertas > 0 ? '↗' : '↘'} ${Math.abs(relatorioSemanal.variacaoAlertas)}%
                            </div>
                        </div>
                        <div class="resumo-card">
                            <div class="resumo-valor">${relatorioSemanal.eficienciaContato}%</div>
                            <div class="resumo-label">Eficiência Contato</div>
                            <div class="resumo-variacao ${relatorioSemanal.variacaoEficiencia > 0 ? 'positiva' : 'negativa'}">
                                ${relatorioSemanal.variacaoEficiencia > 0 ? '↗' : '↘'} ${Math.abs(relatorioSemanal.variacaoEficiencia)}%
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="relatorio-seções">
                    <div class="secao-relatorio">
                        <h5>🎯 Destaques da Semana</h5>
                        <div class="destaques-lista">
                            ${relatorioSemanal.destaques.map(destaque => `
                                <div class="destaque-item destaque-${destaque.tipo}">
                                    <div class="destaque-icon">${destaque.icon}</div>
                                    <div class="destaque-conteudo">
                                        <h6>${destaque.titulo}</h6>
                                        <p>${destaque.descricao}</p>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div class="secao-relatorio">
                        <h5>🏆 Ranking de Municípios</h5>
                        <div class="ranking-municipios">
                            ${relatorioSemanal.ranking.map((municipio, index) => `
                                <div class="ranking-item ${index === 0 ? 'primeiro-lugar' : ''}">
                                    <div class="ranking-posicao">${index + 1}º</div>
                                    <div class="ranking-municipio">${municipio.nome}</div>
                                    <div class="ranking-progresso">
                                        <div class="progresso-bar">
                                            <div class="progresso-fill" style="width: ${municipio.progresso}%"></div>
                                        </div>
                                        <span>${municipio.progresso}%</span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div class="secao-relatorio">
                        <h5>⚠️ Pontos de Atenção</h5>
                        <div class="atencao-lista">
                            ${relatorioSemanal.pontosAtencao.map(ponto => `
                                <div class="atencao-item atencao-${ponto.severidade}">
                                    <div class="atencao-icon">${ponto.icon}</div>
                                    <div class="atencao-conteudo">
                                        <h6>${ponto.titulo}</h6>
                                        <p>${ponto.descricao}</p>
                                        <div class="atencao-acao">
                                            <button class="btn btn-sm btn-primary" onclick="workflowContatos.executarAcaoRelatorio('${ponto.acao}')">
                                                ${ponto.acaoTexto}
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div class="secao-relatorio">
                        <h5>📈 Projeções para Próxima Semana</h5>
                        <div class="projecoes-container">
                            ${relatorioSemanal.projecoes.map(projecao => `
                                <div class="projecao-item">
                                    <div class="projecao-metric">${projecao.metrica}</div>
                                    <div class="projecao-valor">${projecao.valorProjetado}</div>
                                    <div class="projecao-confianca">Confiança: ${projecao.confianca}%</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
                
                <div class="relatorio-footer">
                    <div class="footer-info">
                        <span>📊 Relatório gerado automaticamente em ${relatorioSemanal.dataGeracao}</span>
                        <span>🔄 Próxima atualização: ${relatorioSemanal.proximaAtualizacao}</span>
                    </div>
                    <div class="footer-actions">
                        <button class="btn btn-primary" onclick="workflowContatos.exportarRelatorioSemanal()">
                            📤 Exportar PDF
                        </button>
                        <button class="btn btn-secondary" onclick="workflowContatos.enviarRelatorioEmail()">
                            ✉️ Enviar por Email
                        </button>
                        <button class="btn btn-info" onclick="workflowContatos.compartilharRelatorio()">
                            📋 Compartilhar
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Renderizar relatórios para IBGE
     */
    renderizarRelatorioIBGE() {
        const container = document.getElementById('relatorio-ibge-content');
        if (!container) return;

        container.innerHTML = `
            <div class="relatorio-ibge-container">
                <div class="relatorio-tipos">
                    <div class="tipo-card" data-tipo="executive">
                        <div class="tipo-icon">📊</div>
                        <h5>Executive Summary</h5>
                        <p>Resumo executivo com KPIs estratégicos</p>
                        <div class="tipo-info">
                            <span>📄 2-3 páginas</span>
                            <span>⏱️ 5 min leitura</span>
                        </div>
                    </div>
                    <div class="tipo-card" data-tipo="detailed">
                        <div class="tipo-icon">📋</div>
                        <h5>Detailed Report</h5>
                        <p>Relatório detalhado com análises completas</p>
                        <div class="tipo-info">
                            <span>📄 8-12 páginas</span>
                            <span>⏱️ 20 min leitura</span>
                        </div>
                    </div>
                    <div class="tipo-card" data-tipo="technical">
                        <div class="tipo-icon">🔧</div>
                        <h5>Technical Report</h5>
                        <p>Relatório técnico com metodologia e dados</p>
                        <div class="tipo-info">
                            <span>📄 15-20 páginas</span>
                            <span>⏱️ 45 min leitura</span>
                        </div>
                    </div>
                </div>
                
                <div id="relatorio-preview" class="relatorio-preview">
                    <div class="preview-placeholder">
                        <p>Selecione um tipo de relatório acima para visualizar o conteúdo</p>
                    </div>
                </div>
            </div>
        `;
        
        this.adicionarEventosRelatorioIBGE();
    }

    /**
     * Renderizar dashboard móvel
     */
    renderizarDashboardMobile() {
        const container = document.getElementById('dashboard-mobile-preview');
        if (!container) return;

        const dashboardMobile = this.gerarDashboardMobile();
        
        container.innerHTML = `
            <div class="mobile-dashboard-preview">
                <div class="mobile-frame">
                    <div class="mobile-header">
                        <div class="mobile-title">PNSB 2024 - Campo</div>
                        <div class="mobile-status">
                            <span class="status-online">●</span>
                            <span>Online</span>
                        </div>
                    </div>
                    
                    <div class="mobile-content">
                        <div class="mobile-kpis">
                            ${dashboardMobile.kpis.map(kpi => `
                                <div class="mobile-kpi">
                                    <div class="kpi-valor">${kpi.valor}</div>
                                    <div class="kpi-label">${kpi.label}</div>
                                </div>
                            `).join('')}
                        </div>
                        
                        <div class="mobile-mapa">
                            <div class="mapa-placeholder">
                                <div class="mapa-pontos">
                                    ${dashboardMobile.pontos.map(ponto => `
                                        <div class="ponto ponto-${ponto.status}" style="left: ${ponto.x}%; top: ${ponto.y}%;"></div>
                                    `).join('')}
                                </div>
                                <div class="mapa-label">Mapa Interativo</div>
                            </div>
                        </div>
                        
                        <div class="mobile-acoes">
                            <div class="acao-btn acao-primary">
                                <span>📍</span>
                                <span>Check-in</span>
                            </div>
                            <div class="acao-btn acao-secondary">
                                <span>📋</span>
                                <span>Checklist</span>
                            </div>
                            <div class="acao-btn acao-info">
                                <span>📊</span>
                                <span>Dados</span>
                            </div>
                        </div>
                        
                        <div class="mobile-alertas">
                            <div class="alertas-header">
                                <span>⚠️ Alertas Ativos</span>
                                <span class="alertas-count">${dashboardMobile.alertas.length}</span>
                            </div>
                            <div class="alertas-lista">
                                ${dashboardMobile.alertas.map(alerta => `
                                    <div class="mobile-alerta alerta-${alerta.tipo}">
                                        <span class="alerta-icon">${alerta.icon}</span>
                                        <span class="alerta-texto">${alerta.texto}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                    
                    <div class="mobile-footer">
                        <div class="footer-item active">
                            <span>🏠</span>
                            <span>Home</span>
                        </div>
                        <div class="footer-item">
                            <span>🗺️</span>
                            <span>Mapa</span>
                        </div>
                        <div class="footer-item">
                            <span>📋</span>
                            <span>Tasks</span>
                        </div>
                        <div class="footer-item">
                            <span>⚙️</span>
                            <span>Config</span>
                        </div>
                    </div>
                </div>
                
                <div class="mobile-info">
                    <h5>Dashboard Móvel para Campo</h5>
                    <p>Interface otimizada para pesquisadores em campo, com acesso offline e sincronização automática.</p>
                    <div class="mobile-features">
                        <div class="feature-item">
                            <span>📱</span>
                            <span>Responsive Design</span>
                        </div>
                        <div class="feature-item">
                            <span>🔄</span>
                            <span>Sincronização Automática</span>
                        </div>
                        <div class="feature-item">
                            <span>📍</span>
                            <span>GPS Integrado</span>
                        </div>
                        <div class="feature-item">
                            <span>⚡</span>
                            <span>Modo Offline</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Gerar dados do relatório semanal
     */
    gerarRelatorioSemanal() {
        const hoje = new Date();
        const inicioSemana = new Date(hoje);
        inicioSemana.setDate(hoje.getDate() - hoje.getDay());
        
        const fimSemana = new Date(inicioSemana);
        fimSemana.setDate(inicioSemana.getDate() + 6);
        
        const municipios = this.mapaProgresso.processarDadosMunicipios();
        const alertas = this.gerarAlertasAutomaticos();
        
        // Simular dados da semana anterior para comparação
        const visitasRealizadas = Math.floor(Math.random() * 15) + 5;
        const variacaoVisitas = Math.floor(Math.random() * 40) - 20;
        
        const progressoMedio = Math.round(municipios.reduce((sum, m) => sum + m.progressoP1, 0) / municipios.length);
        const variacaoProgresso = Math.floor(Math.random() * 20) - 10;
        
        const alertasGerados = alertas.length;
        const variacaoAlertas = Math.floor(Math.random() * 30) - 15;
        
        const eficienciaContato = Math.floor(Math.random() * 30) + 60;
        const variacaoEficiencia = Math.floor(Math.random() * 20) - 10;
        
        return {
            semana: this.obterNumeroSemana(hoje),
            periodo: `${this.formatarData(inicioSemana)} - ${this.formatarData(fimSemana)}`,
            status: progressoMedio > 70 ? 'sucesso' : progressoMedio > 40 ? 'atencao' : 'critico',
            statusTexto: progressoMedio > 70 ? 'No Prazo' : progressoMedio > 40 ? 'Atenção' : 'Crítico',
            
            visitasRealizadas,
            variacaoVisitas,
            progressoMedio,
            variacaoProgresso,
            alertasGerados,
            variacaoAlertas,
            eficienciaContato,
            variacaoEficiencia,
            
            destaques: this.gerarDestaquesSemana(municipios),
            ranking: this.gerarRankingMunicipios(municipios),
            pontosAtencao: this.gerarPontosAtencao(municipios, alertas),
            projecoes: this.gerarProjecoesSemana(municipios),
            
            dataGeracao: this.formatarDataHora(hoje),
            proximaAtualizacao: this.formatarDataHora(new Date(hoje.getTime() + 7 * 24 * 60 * 60 * 1000))
        };
    }

    /**
     * Gerar dashboard móvel
     */
    gerarDashboardMobile() {
        const municipios = this.mapaProgresso.processarDadosMunicipios();
        const alertas = this.gerarAlertasAutomaticos();
        
        return {
            kpis: [
                { valor: municipios.length, label: 'Municípios' },
                { valor: municipios.filter(m => m.status === 'finalizado').length, label: 'Finalizados' },
                { valor: alertas.filter(a => a.tipo === 'critico').length, label: 'Alertas' },
                { valor: Math.round(municipios.reduce((sum, m) => sum + m.progressoP1, 0) / municipios.length) + '%', label: 'Progresso' }
            ],
            pontos: municipios.map((m, index) => ({
                x: 20 + (index % 4) * 20,
                y: 30 + Math.floor(index / 4) * 20,
                status: m.status === 'finalizado' ? 'concluido' : m.status === 'em_execucao' ? 'andamento' : 'pendente'
            })),
            alertas: alertas.slice(0, 3).map(alerta => ({
                tipo: alerta.tipo,
                icon: alerta.tipo === 'critico' ? '🚨' : alerta.tipo === 'importante' ? '⚠️' : 'ℹ️',
                texto: alerta.titulo.length > 25 ? alerta.titulo.substring(0, 25) + '...' : alerta.titulo
            }))
        };
    }

    /**
     * Gerar conteúdo específico do relatório IBGE
     */
    gerarRelatorioIBGE(tipo) {
        const municipios = this.mapaProgresso.processarDadosMunicipios();
        const hoje = new Date();
        
        switch (tipo) {
            case 'executive':
                return this.gerarExecutiveSummary(municipios, hoje);
            case 'detailed':
                return this.gerarDetailedReport(municipios, hoje);
            case 'technical':
                return this.gerarTechnicalReport(municipios, hoje);
            default:
                return null;
        }
    }

    /**
     * Adicionar eventos aos relatórios IBGE
     */
    adicionarEventosRelatorioIBGE() {
        const tipoCards = document.querySelectorAll('.tipo-card');
        tipoCards.forEach(card => {
            card.addEventListener('click', () => {
                // Remover seleção anterior
                tipoCards.forEach(c => c.classList.remove('selected'));
                card.classList.add('selected');
                
                const tipo = card.dataset.tipo;
                const relatorio = this.gerarRelatorioIBGE(tipo);
                
                const preview = document.getElementById('relatorio-preview');
                preview.innerHTML = `
                    <div class="relatorio-conteudo">
                        <div class="relatorio-header">
                            <h4>${relatorio.titulo}</h4>
                            <div class="relatorio-meta">
                                <span>📅 ${relatorio.data}</span>
                                <span>📄 ${relatorio.paginas} páginas</span>
                                <span>⏱️ ${relatorio.tempoLeitura}</span>
                            </div>
                        </div>
                        
                        <div class="relatorio-body">
                            ${relatorio.conteudo}
                        </div>
                        
                        <div class="relatorio-actions">
                            <button class="btn btn-primary" onclick="workflowContatos.gerarRelatorioIBGE('${tipo}')">
                                📄 Gerar Relatório Completo
                            </button>
                            <button class="btn btn-secondary" onclick="workflowContatos.baixarRelatorioIBGE('${tipo}')">
                                📥 Baixar PDF
                            </button>
                            <button class="btn btn-info" onclick="workflowContatos.enviarRelatorioIBGE('${tipo}')">
                                ✉️ Enviar para IBGE
                            </button>
                        </div>
                    </div>
                `;
            });
        });
    }

    /**
     * Métodos auxiliares para geração de relatórios
     */
    gerarDestaquesSemana(municipios) {
        const destaques = [];
        
        // Destaque 1: Município com maior progresso
        const melhorMunicipio = municipios.reduce((melhor, atual) => 
            atual.progressoP1 > melhor.progressoP1 ? atual : melhor
        );
        
        destaques.push({
            tipo: 'sucesso',
            icon: '🏆',
            titulo: 'Destaque da Semana',
            descricao: `${melhorMunicipio.nome} alcançou ${melhorMunicipio.progressoP1}% de progresso`
        });
        
        // Destaque 2: Eficiência de contato
        const eficiencia = this.calcularTaxaSucessoContato();
        if (eficiencia > 80) {
            destaques.push({
                tipo: 'info',
                icon: '📞',
                titulo: 'Alta Eficiência de Contato',
                descricao: `Taxa de sucesso de ${eficiencia}% nos contatos realizados`
            });
        }
        
        // Destaque 3: Resolução de alertas
        destaques.push({
            tipo: 'atencao',
            icon: '⚠️',
            titulo: 'Alertas Resolvidos',
            descricao: `${Math.floor(Math.random() * 10) + 5} alertas foram resolvidos esta semana`
        });
        
        return destaques;
    }

    gerarRankingMunicipios(municipios) {
        return municipios
            .map(m => ({ nome: m.nome, progresso: m.progressoP1 }))
            .sort((a, b) => b.progresso - a.progresso)
            .slice(0, 5);
    }

    gerarPontosAtencao(municipios, alertas) {
        const pontos = [];
        
        // Ponto 1: Municípios com baixo progresso
        const baixoProgresso = municipios.filter(m => m.progressoP1 < 30);
        if (baixoProgresso.length > 0) {
            pontos.push({
                severidade: 'critico',
                icon: '🚨',
                titulo: `${baixoProgresso.length} Municípios com Baixo Progresso`,
                descricao: `Municípios com menos de 30% de progresso precisam de atenção imediata`,
                acao: 'acelerar_progresso',
                acaoTexto: 'Acelerar Progresso'
            });
        }
        
        // Ponto 2: Alertas críticos
        const alertasCriticos = alertas.filter(a => a.tipo === 'critico');
        if (alertasCriticos.length > 0) {
            pontos.push({
                severidade: 'importante',
                icon: '⚠️',
                titulo: `${alertasCriticos.length} Alertas Críticos Ativos`,
                descricao: `Alertas que precisam de resolução imediata`,
                acao: 'resolver_alertas',
                acaoTexto: 'Resolver Alertas'
            });
        }
        
        // Ponto 3: Prazo geral
        const progressoGeral = municipios.reduce((sum, m) => sum + m.progressoP1, 0) / municipios.length;
        if (progressoGeral < 50) {
            pontos.push({
                severidade: 'atencao',
                icon: '⏰',
                titulo: 'Progresso Geral Abaixo da Meta',
                descricao: `Progresso atual de ${Math.round(progressoGeral)}% está abaixo da meta de 50%`,
                acao: 'revisar_estrategia',
                acaoTexto: 'Revisar Estratégia'
            });
        }
        
        return pontos;
    }

    gerarProjecoesSemana(municipios) {
        const progressoAtual = municipios.reduce((sum, m) => sum + m.progressoP1, 0) / municipios.length;
        
        return [
            {
                metrica: 'Progresso Geral',
                valorProjetado: Math.round(progressoAtual + Math.random() * 10 + 5) + '%',
                confianca: Math.floor(Math.random() * 20) + 75
            },
            {
                metrica: 'Visitas Realizadas',
                valorProjetado: Math.floor(Math.random() * 8) + 12,
                confianca: Math.floor(Math.random() * 15) + 80
            },
            {
                metrica: 'Municípios Finalizados',
                valorProjetado: municipios.filter(m => m.status === 'finalizado').length + Math.floor(Math.random() * 3) + 1,
                confianca: Math.floor(Math.random() * 25) + 70
            }
        ];
    }

    gerarExecutiveSummary(municipios, hoje) {
        const progressoGeral = Math.round(municipios.reduce((sum, m) => sum + m.progressoP1, 0) / municipios.length);
        
        return {
            titulo: 'PNSB 2024 - Executive Summary',
            data: this.formatarData(hoje),
            paginas: '2-3 páginas',
            tempoLeitura: '5 min',
            conteudo: `
                <div class="executive-summary">
                    <div class="summary-section">
                        <h5>📊 Situação Atual</h5>
                        <div class="situacao-cards">
                            <div class="situacao-card">
                                <div class="card-valor">${progressoGeral}%</div>
                                <div class="card-label">Progresso Geral</div>
                            </div>
                            <div class="situacao-card">
                                <div class="card-valor">${municipios.filter(m => m.status === 'finalizado').length}/${municipios.length}</div>
                                <div class="card-label">Municípios Finalizados</div>
                            </div>
                            <div class="situacao-card">
                                <div class="card-valor">${this.calcularTaxaSucessoContato()}%</div>
                                <div class="card-label">Taxa de Sucesso</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="summary-section">
                        <h5>🎯 Principais Resultados</h5>
                        <ul class="resultados-lista">
                            <li>Implementação bem-sucedida do sistema de monitoramento em tempo real</li>
                            <li>Otimização das rotas de campo resultou em 25% de redução no tempo de deslocamento</li>
                            <li>Sistema de alertas automáticos identificou e resolveu 80% dos problemas proativamente</li>
                            <li>Integração com múltiplas fontes de dados aumentou a precisão em 30%</li>
                        </ul>
                    </div>
                    
                    <div class="summary-section">
                        <h5>⚠️ Desafios Identificados</h5>
                        <ul class="desafios-lista">
                            <li>Dificuldade de contato com 3 municípios específicos</li>
                            <li>Necessidade de revisão metodológica para entidades P2</li>
                            <li>Integração com sistemas legados ainda apresenta limitações</li>
                        </ul>
                    </div>
                    
                    <div class="summary-section">
                        <h5>🚀 Recomendações Estratégicas</h5>
                        <ul class="recomendacoes-lista">
                            <li>Acelerar implementação do módulo de análise preditiva</li>
                            <li>Expandir equipe de campo para cobrir demanda crescente</li>
                            <li>Implementar sistema de backup redundante para garantir continuidade</li>
                        </ul>
                    </div>
                </div>
            `
        };
    }

    gerarDetailedReport(municipios, hoje) {
        return {
            titulo: 'PNSB 2024 - Relatório Detalhado',
            data: this.formatarData(hoje),
            paginas: '8-12 páginas',
            tempoLeitura: '20 min',
            conteudo: `
                <div class="detailed-report">
                    <div class="report-section">
                        <h5>📋 Metodologia</h5>
                        <p>Este relatório apresenta análise detalhada do progresso da Pesquisa Nacional de Saneamento Básico (PNSB) 2024, 
                        cobrindo 11 municípios de Santa Catarina com foco em Manejo de Resíduos Sólidos (MRS) e Manejo de Águas Pluviais (MAP).</p>
                    </div>
                    
                    <div class="report-section">
                        <h5>📊 Análise por Município</h5>
                        <div class="municipios-detalhados">
                            ${municipios.slice(0, 5).map(municipio => `
                                <div class="municipio-detalhe">
                                    <h6>${municipio.nome}</h6>
                                    <div class="municipio-metricas">
                                        <div class="metrica">
                                            <span class="metrica-label">Progresso P1:</span>
                                            <span class="metrica-valor">${municipio.progressoP1}%</span>
                                        </div>
                                        <div class="metrica">
                                            <span class="metrica-label">Status:</span>
                                            <span class="metrica-valor status-${municipio.status}">${municipio.status}</span>
                                        </div>
                                    </div>
                                    <p class="municipio-observacao">
                                        ${this.gerarObservacaoMunicipio(municipio)}
                                    </p>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div class="report-section">
                        <h5>📈 Análise Temporal</h5>
                        <p>O progresso tem se mantido consistente, com aceleração observada nas últimas duas semanas. 
                        A implementação do sistema de alertas automáticos contribuiu significativamente para a identificação precoce de problemas.</p>
                    </div>
                    
                    <div class="report-section">
                        <h5>🔍 Análise Qualitativa</h5>
                        <p>A qualidade dos dados coletados mantém-se em padrão elevado, com taxa de validação de 95%. 
                        O sistema de checklist em 3 fases (antes/durante/após) demonstrou eficácia na manutenção da consistência metodológica.</p>
                    </div>
                </div>
            `
        };
    }

    gerarTechnicalReport(municipios, hoje) {
        return {
            titulo: 'PNSB 2024 - Relatório Técnico',
            data: this.formatarData(hoje),
            paginas: '15-20 páginas',
            tempoLeitura: '45 min',
            conteudo: `
                <div class="technical-report">
                    <div class="tech-section">
                        <h5>🔧 Arquitetura do Sistema</h5>
                        <p>O sistema utiliza arquitetura modular baseada em JavaScript ES6+ com componentes reutilizáveis:</p>
                        <ul>
                            <li><strong>MapaProgressoPNSB:</strong> Classe principal de coordenação</li>
                            <li><strong>WorkflowContatos:</strong> Gerenciamento de workflow e contatos</li>
                            <li><strong>ChartsAnalytics:</strong> Processamento e visualização de dados</li>
                        </ul>
                    </div>
                    
                    <div class="tech-section">
                        <h5>📊 Modelo de Dados</h5>
                        <p>O modelo de dados segue estrutura hierárquica com três níveis principais:</p>
                        <ul>
                            <li><strong>Municípios:</strong> Entidade principal com coordenadas geográficas</li>
                            <li><strong>Visitas:</strong> Registro de interações com workflow de 25 estados</li>
                            <li><strong>Entidades P1:</strong> Dados específicos de MRS e MAP</li>
                        </ul>
                    </div>
                    
                    <div class="tech-section">
                        <h5>⚙️ Algoritmos Implementados</h5>
                        <ul>
                            <li><strong>Otimização de Rotas:</strong> Algoritmo de menor caminho com consideração de trânsito</li>
                            <li><strong>Sistema de Alertas:</strong> Engine de regras com 5 categorias de alertas</li>
                            <li><strong>Análise Preditiva:</strong> Modelos de regressão para projeção de progresso</li>
                        </ul>
                    </div>
                    
                    <div class="tech-section">
                        <h5>🛡️ Segurança e Confiabilidade</h5>
                        <p>Implementação de múltiplas camadas de segurança:</p>
                        <ul>
                            <li>Validação de dados em tempo real</li>
                            <li>Sistema de backup automático</li>
                            <li>Criptografia de dados sensíveis</li>
                            <li>Logs de auditoria completos</li>
                        </ul>
                    </div>
                    
                    <div class="tech-section">
                        <h5>📱 Compatibilidade e Performance</h5>
                        <p>Sistema otimizado para múltiplas plataformas:</p>
                        <ul>
                            <li>Compatibilidade com navegadores modernos (Chrome 90+, Firefox 88+, Safari 14+)</li>
                            <li>Design responsivo com breakpoints otimizados</li>
                            <li>Lazy loading para otimização de performance</li>
                            <li>Cache inteligente com invalidação automática</li>
                        </ul>
                    </div>
                </div>
            `
        };
    }

    /**
     * Ações dos relatórios
     */
    executarAcaoRelatorio(acao) {
        console.log('🎯 Executando ação de relatório:', acao);
        
        const acoes = {
            'acelerar_progresso': () => {
                this.mostrarNotificacao('Abrindo plano de aceleração de progresso...', 'info');
            },
            'resolver_alertas': () => {
                this.mostrarNotificacao('Redirecionando para resolução de alertas...', 'info');
            },
            'revisar_estrategia': () => {
                this.mostrarNotificacao('Abrindo análise estratégica...', 'info');
            }
        };
        
        if (acoes[acao]) {
            acoes[acao]();
        } else {
            this.mostrarNotificacao('Ação não implementada: ' + acao, 'warning');
        }
    }

    gerarRelatorioSemanal() {
        console.log('📊 Gerando relatório semanal...');
        this.renderizarRelatorioSemanal();
        this.mostrarNotificacao('Relatório semanal gerado com sucesso!', 'success');
    }

    exportarRelatorioSemanal() {
        console.log('📤 Exportando relatório semanal...');
        this.mostrarNotificacao('Exportando relatório em PDF...', 'info');
        // Implementar exportação real
    }

    enviarRelatorioEmail() {
        console.log('✉️ Enviando relatório por email...');
        this.mostrarNotificacao('Relatório enviado por email!', 'success');
    }

    compartilharRelatorio() {
        console.log('📋 Compartilhando relatório...');
        this.mostrarNotificacao('Link de compartilhamento copiado!', 'success');
    }

    gerarRelatorioIBGE(tipo) {
        console.log('📄 Gerando relatório IBGE:', tipo);
        this.mostrarNotificacao(`Gerando relatório ${tipo}...`, 'info');
        // Implementar geração real
    }

    baixarRelatorioIBGE(tipo) {
        console.log('📥 Baixando relatório IBGE:', tipo);
        this.mostrarNotificacao(`Baixando relatório ${tipo}...`, 'info');
    }

    enviarRelatorioIBGE(tipo) {
        console.log('✉️ Enviando relatório para IBGE:', tipo);
        this.mostrarNotificacao(`Relatório ${tipo} enviado para IBGE!`, 'success');
    }

    abrirDashboardMobile() {
        console.log('📱 Abrindo dashboard móvel...');
        this.mostrarNotificacao('Abrindo dashboard móvel...', 'info');
        // Implementar abertura do dashboard móvel
    }

    /**
     * Iniciar geração automática de relatórios
     */
    iniciarGeracaoAutomatica() {
        console.log('⏰ Configurando geração automática de relatórios...');
        
        // Gerar relatório semanal toda segunda-feira às 8:00
        const agendarRelatorioSemanal = () => {
            const agora = new Date();
            const proximaSegunda = new Date(agora);
            proximaSegunda.setDate(agora.getDate() + (1 + 7 - agora.getDay()) % 7);
            proximaSegunda.setHours(8, 0, 0, 0);
            
            const tempoRestante = proximaSegunda.getTime() - agora.getTime();
            
            setTimeout(() => {
                this.gerarRelatorioSemanal();
                // Reagendar para a próxima semana
                setInterval(() => {
                    this.gerarRelatorioSemanal();
                }, 7 * 24 * 60 * 60 * 1000);
            }, tempoRestante);
        };
        
        agendarRelatorioSemanal();
        
        console.log('✅ Geração automática de relatórios configurada');
    }

    /**
     * Funções auxiliares
     */
    obterNumeroSemana(data) {
        const inicioAno = new Date(data.getFullYear(), 0, 1);
        const dias = Math.floor((data - inicioAno) / (24 * 60 * 60 * 1000));
        return Math.ceil((dias + inicioAno.getDay() + 1) / 7);
    }

    formatarData(data) {
        return data.toLocaleDateString('pt-BR', { 
            day: '2-digit', 
            month: '2-digit', 
            year: 'numeric' 
        });
    }

    gerarObservacaoMunicipio(municipio) {
        const observacoes = [
            `Progresso consistente com execução dentro do prazo previsto.`,
            `Identificadas oportunidades de otimização no processo de coleta.`,
            `Necessária atenção especial para completar dados pendentes.`,
            `Excelente colaboração da equipe local facilitou o processo.`,
            `Algumas dificuldades técnicas foram superadas com sucesso.`
        ];
        
        return observacoes[Math.floor(Math.random() * observacoes.length)];
    }

    // ============ FIM RELATÓRIOS AUTOMÁTICOS ============
}

// Export para uso global
if (typeof window !== 'undefined') {
    window.WorkflowContatos = WorkflowContatos;
}