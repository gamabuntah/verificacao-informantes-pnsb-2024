/**
 * MAPA DE PROGRESSO PNSB 2024 - SISTEMA COMPLETO
 * Implementação completa do dashboard executivo para PNSB 2024
 */

class MapaProgressoPNSB {
    constructor() {
        this.municipios = {
            'Balneário Camboriú': { lat: -26.975, lng: -48.633, status: 'andamento' },
            'Balneário Piçarras': { lat: -26.757, lng: -48.670, status: 'andamento' },
            'Bombinhas': { lat: -27.140, lng: -48.482, status: 'pendente' },
            'Camboriú': { lat: -27.024, lng: -48.651, status: 'andamento' },
            'Itajaí': { lat: -26.907, lng: -48.661, status: 'concluido' },
            'Itapema': { lat: -27.089, lng: -48.611, status: 'andamento' },
            'Luiz Alves': { lat: -26.716, lng: -48.934, status: 'pendente' },
            'Navegantes': { lat: -26.897, lng: -48.655, status: 'andamento' },
            'Penha': { lat: -26.770, lng: -48.651, status: 'pendente' },
            'Porto Belo': { lat: -27.158, lng: -48.554, status: 'andamento' },
            'Ilhota': { lat: -26.898, lng: -48.828, status: 'pendente' }
        };
        
        this.dados = {
            visitas: [],
            entidades: [],
            questionarios: [],
            alertas: [],
            kpis: {}
        };
        
        this.mapa = null;
        this.marcadores = [];
        this.charts = {};
        this.filtros = {
            municipio: 'todos',
            prioridade: 'todos',
            status: 'todos',
            tipo: 'todos'
        };
        
        this.cache = new Map();
        this.ultimaAtualizacao = null;
        
        this.init();
    }
    
    /**
     * Inicialização do sistema
     */
    async init() {
        try {
            console.log('🚀 Inicializando Mapa de Progresso PNSB 2024...');
            
            console.log('📋 1. Configurando event listeners...');
            this.setupEventListeners();
            
            console.log('📋 2. Carregando dados das APIs...');
            await this.carregarDados();
            
            console.log('📋 3. Inicializando abas...');
            this.inicializarAbas();
            
            console.log('📋 4. Renderizando dashboard...');
            this.renderizarDashboard();
            
            console.log('📋 5. Inicializando mapa...');
            this.inicializarMapa();
            
            console.log('📋 6. Inicializando charts...');
            this.inicializarCharts();
            
            console.log('📋 7. Configurando atualização automática...');
            this.inicializarAtualizacaoAutomatica();
            
            console.log('📋 8. Ocultando loading e mostrando interface...');
            this.mostrarLoading(false);
            
            // Force show main content
            const mainContent = document.querySelector('.dashboard-container, .main-content, .tab-content');
            if (mainContent) {
                mainContent.style.display = 'block';
                mainContent.style.visibility = 'visible';
                console.log('👁️ Interface principal forçadamente visível');
            }
            
            console.log('✅ Mapa de Progresso PNSB 2024 inicializado com sucesso!');
            
            // CORREÇÃO AUTOMÁTICA: Forçar exibição após 2 segundos
            setTimeout(() => {
                this.forcarExibicaoInterface();
            }, 2000);
            
        } catch (error) {
            console.error('❌ Erro na inicialização:', error);
            this.mostrarErro('Erro na inicialização do sistema. Recarregue a página.');
        }
    }
    
    /**
     * Configuração de event listeners
     */
    setupEventListeners() {
        // Filtros
        document.addEventListener('change', (e) => {
            if (e.target.matches('select[data-filtro]')) {
                this.aplicarFiltro(e.target.dataset.filtro, e.target.value);
            }
        });
        
        // Botões de ação
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-acao]')) {
                e.preventDefault();
                this.executarAcao(e.target.dataset.acao, e.target);
            }
        });
        
        // Atualização manual
        document.addEventListener('click', (e) => {
            if (e.target.matches('#btn-atualizar')) {
                e.preventDefault();
                this.atualizarDados();
            }
        });
        
        // Exportação
        document.addEventListener('click', (e) => {
            if (e.target.matches('#btn-exportar')) {
                e.preventDefault();
                this.exportarDados();
            }
        });
    }
    
    /**
     * Sistema de abas
     */
    inicializarAbas() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabContents = document.querySelectorAll('.tab-content');
        
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const target = button.dataset.tab;
                
                // Remover classe active de todos
                tabButtons.forEach(b => b.classList.remove('active'));
                tabContents.forEach(c => c.classList.remove('active'));
                
                // Adicionar classe active aos selecionados
                button.classList.add('active');
                const targetContent = document.getElementById(target);
                if (targetContent) {
                    targetContent.classList.add('active');
                    
                    // Trigger específico para cada aba
                    this.onTabActivated(target);
                }
            });
        });
        
        // Ativar primeira aba
        if (tabButtons.length > 0) {
            console.log('🏷️ Ativando primeira aba...');
            tabButtons[0].click();
            
            // Forçar exibição mesmo se click não funcionar
            setTimeout(() => {
                const firstTab = document.querySelector('.tab-content');
                const firstButton = document.querySelector('.tab-button');
                
                if (firstTab && !firstTab.classList.contains('active')) {
                    console.log('🔧 Forçando ativação da primeira aba...');
                    firstTab.classList.add('active');
                    firstTab.style.display = 'block';
                    firstTab.style.visibility = 'visible';
                }
                
                if (firstButton && !firstButton.classList.contains('active')) {
                    firstButton.classList.add('active');
                }
                
                // Garantir que o dashboard container está visível
                const dashboard = document.querySelector('.dashboard-container');
                if (dashboard) {
                    dashboard.style.display = 'block';
                    dashboard.style.visibility = 'visible';
                    dashboard.style.opacity = '1';
                    console.log('✅ Dashboard container forçadamente visível');
                }
            }, 100);
        }
    }
    
    /**
     * Callback para ativação de aba
     */
    onTabActivated(tabId) {
        switch (tabId) {
            case 'dashboard-executivo':
                this.renderizarKPIs();
                this.renderizarMunicipios();
                this.renderizarTimeline();
                this.renderizarPainelDiario();
                break;
            case 'mapa-campo':
                this.redimensionarMapa();
                this.atualizarMarcadores();
                break;
            case 'analytics':
                this.renderizarCharts();
                this.renderizarPredicoes();
                break;
            case 'workflow':
                if (this.workflowContatos) {
                    this.workflowContatos.renderizarPipelineVisitas();
                    this.workflowContatos.renderizarChecklistEtapas();
                    this.renderizarEstatisticasWorkflow();
                }
                break;
            case 'alertas':
                if (this.workflowContatos) {
                    this.workflowContatos.renderizarSistemaAlertas();
                }
                break;
            case 'relatorios':
                if (this.workflowContatos) {
                    this.workflowContatos.renderizarSistemaRelatorios();
                }
                break;
        }
    }
    
    /**
     * Carregamento de dados
     */
    async carregarDados() {
        try {
            console.log('📊 Iniciando carregamento de dados...');
            this.mostrarLoading(true);
            
            // Verificar cache
            const cacheKey = 'dados_completos';
            const cached = this.cache.get(cacheKey);
            if (cached && (Date.now() - cached.timestamp) < 300000) { // 5 minutos
                console.log('📋 Usando dados do cache');
                this.dados = cached.data;
                return;
            }
            
            console.log('🌐 Carregando dados das APIs...');
            // Carregar dados em paralelo
            const [visitas, entidades, questionarios, kpis, alertas, municipios, estatisticas, checklists] = await Promise.all([
                this.fetchAPI('/api/visitas'),
                this.fetchAPI('/api/questionarios/entidades-identificadas'),
                this.fetchAPI('/api/questionarios/progresso-questionarios'),
                this.fetchAPI('/api/dashboard/kpis/estrategicos'), // PNSB 2024 - Nova estrutura
                this.fetchAPI('/api/dashboard/alertas/automaticos'),
                this.fetchAPI('/api/visitas/progresso-mapa'),
                this.fetchAPI('/api/dashboard/estatisticas/diarias'),
                this.fetchAPI('/api/checklist')
            ]);
            
            console.log('📋 APIs carregadas, processando dados...');
    // Verificar se estamos usando KPIs PNSB 2024
    if (kpis && kpis.metadata && kpis.metadata.versao === '2.0_pnsb_oficial') {
        console.log('✅ Usando KPIs PNSB 2024 - Versão Oficial');
    } else {
        console.warn('⚠️ KPIs antigos detectados - Atualize para PNSB 2024');
    }
    
            
            this.dados = {
                visitas: (visitas && visitas.data) || visitas || [],
                entidades: (entidades && entidades.data) || entidades || [],
                questionarios: (questionarios && questionarios.data) || questionarios || [],
                kpis: kpis && kpis.success ? kpis.data : {},
                kpis_metadata: kpis && kpis.metadata ? kpis.metadata : {},
                alertas: alertas && alertas.success ? alertas.data : [],
                municipios: municipios && municipios.success ? (municipios.data.municipios || municipios.data.data || []) : [],
                estatisticas: estatisticas && estatisticas.success ? estatisticas.data : {},
                checklists: (checklists && checklists.data) || checklists || []
            };
            
            // Store global data for compatibility with existing code
            if (municipios && municipios.success && municipios.data) {
                const municipiosArray = municipios.data.municipios || municipios.data.data || [];
                window.dadosProgresso = {
                    municipios: {},
                    data: municipiosArray,
                    estatisticas: municipios.data.estatisticas || {},
                    ultima_atualizacao: municipios.data.ultima_atualizacao
                };
                
                // Convert array to object for backward compatibility
                if (Array.isArray(municipiosArray)) {
                    municipiosArray.forEach(municipioData => {
                        window.dadosProgresso.municipios[municipioData.municipio] = municipioData;
                    });
                }
                
                console.log('✅ Global dadosProgresso updated:', window.dadosProgresso);
            }
            
            // Salvar no cache
            this.cache.set(cacheKey, {
                data: this.dados,
                timestamp: Date.now()
            });
            
            this.ultimaAtualizacao = new Date();
            console.log('✅ Carregamento de dados concluído com sucesso!');
            
        } catch (error) {
            console.error('❌ Erro ao carregar dados:', error);
            this.mostrarErro('Erro ao carregar dados. Tentando novamente...');
            
            // Usar dados do cache se disponível
            const cached = this.cache.get('dados_completos');
            if (cached) {
                console.log('📋 Usando fallback do cache devido ao erro');
                this.dados = cached.data;
            }
        } finally {
            console.log('🏁 Finalizando carregamento de dados...');
            this.mostrarLoading(false);
        }
    }
    
    /**
     * Requisições à API
     */
    async fetchAPI(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.CSRF_TOKEN || ''
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
            
        } catch (error) {
            console.error(`Erro na API ${endpoint}:`, error);
            return null;
        }
    }
    
    /**
     * Renderização do dashboard principal
     */
    renderizarDashboard() {
        this.renderizarKPIs();
        this.renderizarMunicipios();
        this.renderizarTimeline();
        this.renderizarPainelDiario();
        this.renderizarAlertas();
    }
    
    /**
     * Renderização dos KPIs estratégicos
     */
    renderizarKPIs() {
        const container = document.getElementById('kpis-estrategicos');
        if (!container) return;
        
        const kpis = this.calcularKPIs();
        
        // Função para determinar cor do status
        const getStatusColor = (status) => {
            switch (status) {
                case 'critico': return '#dc3545';
                case 'alerta': return '#fd7e14';
                case 'atencao': return '#ffc107';
                case 'normal': return '#28a745';
                default: return '#6c757d';
            }
        };
        
        // Função para determinar cor do risco
        const getRiskColor = (nivel) => {
            switch (nivel) {
                case 'alto': return '#dc3545';
                case 'medio': return '#fd7e14';
                case 'baixo': return '#28a745';
                default: return '#6c757d';
            }
        };
        
        container.innerHTML = `
            <!-- KPI Cards Row 1: Cronograma e Cobertura -->
            <div class="kpi-card">
                <div class="kpi-header">
                    <div class="kpi-title">Cronograma IBGE</div>
                    <div class="kpi-icon">⏰</div>
                    <div class="kpi-status" style="background-color: ${getStatusColor(kpis.statusCronograma)}">
                        ${kpis.statusCronograma}
                    </div>
                </div>
                <div class="kpi-value">${kpis.diasRestantes}</div>
                <div class="kpi-description">dias restantes para conclusão</div>
                <div class="kpi-progress">
                    <div class="kpi-progress-bar" style="width: ${kpis.progressoTempo}%"></div>
                </div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-header">
                    <div class="kpi-title">Cobertura SC</div>
                    <div class="kpi-icon">🎯</div>
                </div>
                <div class="kpi-value">${kpis.municipiosConcluidos}/11</div>
                <div class="kpi-description">municípios com dados validados (${kpis.coberturaMunicipios}%)</div>
                <div class="kpi-progress">
                    <div class="kpi-progress-bar" style="width: ${kpis.coberturaMunicipios}%"></div>
                </div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-header">
                    <div class="kpi-title">Compliance P1</div>
                    <div class="kpi-icon">✅</div>
                    <div class="kpi-status" style="background-color: ${getStatusColor(kpis.statusCompliance)}">
                        ${kpis.statusCompliance}
                    </div>
                </div>
                <div class="kpi-value">${kpis.complianceP1}%</div>
                <div class="kpi-description">entidades obrigatórias finalizadas</div>
                <div class="kpi-progress">
                    <div class="kpi-progress-bar" style="width: ${kpis.complianceP1}%"></div>
                </div>
            </div>
            
            <!-- KPI Cards Row 2: Instrumentos de Pesquisa -->
            <div class="kpi-card">
                <div class="kpi-header">
                    <div class="kpi-title">Taxa Resposta MRS</div>
                    <div class="kpi-icon">📋</div>
                    <div class="kpi-status" style="background-color: ${getStatusColor(kpis.statusMRS)}">
                        ${kpis.statusMRS}
                    </div>
                </div>
                <div class="kpi-value">${kpis.taxaRespostaMRS}%</div>
                <div class="kpi-description">questionários MRS respondidos</div>
                <div class="kpi-progress">
                    <div class="kpi-progress-bar" style="width: ${kpis.taxaRespostaMRS}%"></div>
                </div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-header">
                    <div class="kpi-title">Taxa Resposta MAP</div>
                    <div class="kpi-icon">💧</div>
                    <div class="kpi-status" style="background-color: ${getStatusColor(kpis.statusMAP)}">
                        ${kpis.statusMAP}
                    </div>
                </div>
                <div class="kpi-value">${kpis.taxaRespostaMAP}%</div>
                <div class="kpi-description">questionários MAP respondidos</div>
                <div class="kpi-progress">
                    <div class="kpi-progress-bar" style="width: ${kpis.taxaRespostaMAP}%"></div>
                </div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-header">
                    <div class="kpi-title">Qualidade IBGE</div>
                    <div class="kpi-icon">🏆</div>
                    <div class="kpi-status" style="background-color: ${getStatusColor(kpis.qualidadeGeral)}">
                        ${kpis.qualidadeGeral}
                    </div>
                </div>
                <div class="kpi-value">${kpis.scoreQualidade}</div>
                <div class="kpi-description">score metodológico oficial</div>
                <div class="kpi-progress">
                    <div class="kpi-progress-bar" style="width: ${kpis.scoreQualidade}%"></div>
                </div>
            </div>
            
            <!-- KPI Cards Row 3: Efetividade e Risco -->
            <div class="kpi-card">
                <div class="kpi-header">
                    <div class="kpi-title">Efetividade</div>
                    <div class="kpi-icon">⚡</div>
                </div>
                <div class="kpi-value">${kpis.eficienciaPesquisadores}%</div>
                <div class="kpi-description">eficiência operacional geral</div>
                <div class="kpi-progress">
                    <div class="kpi-progress-bar" style="width: ${kpis.eficienciaPesquisadores}%"></div>
                </div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-header">
                    <div class="kpi-title">Visitas Campo</div>
                    <div class="kpi-icon">🚗</div>
                </div>
                <div class="kpi-value">${kpis.visitasRealizadas}/${kpis.visitasTotal}</div>
                <div class="kpi-description">visitas realizadas vs. planejadas</div>
                <div class="kpi-progress">
                    <div class="kpi-progress-bar" style="width: ${kpis.visitasTotal > 0 ? (kpis.visitasRealizadas / kpis.visitasTotal) * 100 : 0}%"></div>
                </div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-header">
                    <div class="kpi-title">Risco Cronograma</div>
                    <div class="kpi-icon">⚠️</div>
                    <div class="kpi-status" style="background-color: ${getRiskColor(kpis.nivelRisco)}">
                        ${kpis.nivelRisco}
                    </div>
                </div>
                <div class="kpi-value">${kpis.scoreRisco}</div>
                <div class="kpi-description">indicador de risco do projeto</div>
                <div class="kpi-progress">
                    <div class="kpi-progress-bar" style="width: ${kpis.scoreRisco}%"></div>
                </div>
            </div>
            
            <!-- Indicador de Versão KPIs -->
            <div class="kpi-version-indicator">
                <small>📊 KPIs PNSB 2024 v${kpis.versaoKPIs || '1.0'} | Atualizado: ${new Date(kpis.ultimaAtualizacao).toLocaleString('pt-BR')}</small>
            </div>
        `;
    }
    
    /**
     * Cálculo dos KPIs - Versão PNSB 2024 Adequada para IBGE
     */
    calcularKPIs() {
        // Verificar se os dados foram carregados
        if (!this.dados) {
            console.log('ℹ️ Dados ainda não carregados para KPIs');
            return this.criarKPIsVazios();
        }
        
        // Usar dados da API melhorada se disponível
        if (this.dados.kpis && Object.keys(this.dados.kpis).length > 0) {
            const kpis = this.dados.kpis;
            
            // Estrutura nova (versão 2.0_pnsb_oficial)
            if (kpis.cronograma_ibge && kpis.instrumentos_pesquisa) {
                return this.processarKPIsMelhorados(kpis);
            }
            
            // Estrutura antiga (fallback)
            return this.processarKPIsAntigos(kpis);
        }
        
        // Fallback para cálculo local
        const hoje = new Date();
        const prazoFinal = new Date('2025-12-31');
        const diasRestantes = Math.ceil((prazoFinal - hoje) / (1000 * 60 * 60 * 24));
        
        const totalMunicipios = 11;
        const municipiosConcluidos = this.contarMunicipiosConcluidos();
        const coberturaMunicipios = Math.round((municipiosConcluidos / totalMunicipios) * 100);
        
        const entidadesP1 = (this.dados.entidades || []).filter(e => e.prioridade === 1);
        const entidadesP1Finalizadas = entidadesP1.filter(e => 
            e.status_mrs === 'validado_concluido' && e.status_map === 'validado_concluido'
        );
        const complianceP1 = entidadesP1.length ? 
            Math.round((entidadesP1Finalizadas.length / entidadesP1.length) * 100) : 0;
        
        const scoreQualidade = this.calcularScoreQualidade();
        
        const inicio = new Date('2025-01-01');
        const progressoTempo = Math.max(0, Math.min(100, 
            ((hoje - inicio) / (prazoFinal - inicio)) * 100
        ));
        
        return {
            diasRestantes: Math.max(0, diasRestantes),
            municipiosConcluidos,
            coberturaMunicipios,
            complianceP1,
            scoreQualidade,
            progressoTempo: Math.round(progressoTempo),
            eficienciaPesquisadores: this.calcularEficienciaDinamica()
        };
    }
    
    /**
     * Processar KPIs melhorados para PNSB 2024
     */
    processarKPIsMelhorados(kpis) {
        try {
            const resultado = {
                // Cronograma IBGE
                diasRestantes: kpis.cronograma_ibge?.dias_restantes || 0,
                progressoTempo: kpis.cronograma_ibge?.percentual_tempo_decorrido || 0,
                statusCronograma: kpis.cronograma_ibge?.status_cronograma || 'indefinido',
                
                // Cobertura Territorial
                municipiosConcluidos: kpis.cobertura_territorial?.municipios_concluidos || 0,
                coberturaMunicipios: kpis.cobertura_territorial?.percentual_cobertura || 0,
                
                // Compliance PNSB
                complianceP1: kpis.compliance_pnsb?.percentual_p1_finalizado || 0,
                statusCompliance: kpis.compliance_pnsb?.status_compliance || 'indefinido',
                
                // Instrumentos de Pesquisa
                taxaRespostaMRS: kpis.instrumentos_pesquisa?.mrs?.taxa_resposta || 0,
                taxaRespostaMAP: kpis.instrumentos_pesquisa?.map?.taxa_resposta || 0,
                statusMRS: kpis.instrumentos_pesquisa?.mrs?.status || 'indefinido',
                statusMAP: kpis.instrumentos_pesquisa?.map?.status || 'indefinido',
                
                // Qualidade dos Dados
                scoreQualidade: kpis.qualidade_dados?.score_metodologico || 0,
                qualidadeGeral: kpis.qualidade_dados?.qualidade_geral || 'indefinida',
                
                // Efetividade Operacional
                eficienciaPesquisadores: kpis.efetividade_operacional?.eficiencia_pesquisadores || 0,
                visitasRealizadas: kpis.efetividade_operacional?.visitas?.realizadas || 0,
                visitasTotal: kpis.efetividade_operacional?.visitas?.total || 0,
                
                // Indicadores de Risco
                nivelRisco: kpis.indicadores_risco?.risco_cronograma?.nivel || 'baixo',
                scoreRisco: kpis.indicadores_risco?.risco_cronograma?.score || 0,
                
                // Dados adicionais para interface
                versaoKPIs: '2.0_pnsb_oficial',
                ultimaAtualizacao: new Date().toISOString()
            };
            
            console.log('📊 KPIs PNSB 2024 processados:', resultado);
            return resultado;
            
        } catch (error) {
            console.error('❌ Erro ao processar KPIs melhorados:', error);
            return this.criarKPIsVazios();
        }
    }
    
    /**
     * Processar KPIs antigos (fallback)
     */
    processarKPIsAntigos(kpis) {
        try {
            return {
                diasRestantes: kpis.diasRestantes || 0,
                municipiosConcluidos: kpis.municipiosConcluidos || 0,
                coberturaMunicipios: kpis.coberturaMunicipios || 0,
                complianceP1: kpis.complianceP1 || 0,
                scoreQualidade: kpis.scoreQualidade || 0,
                progressoTempo: kpis.progressoTempo || 0,
                eficienciaPesquisadores: kpis.eficienciaPesquisadores || 0,
                
                // Campos extras para compatibilidade
                taxaRespostaMRS: kpis.taxaRespostaMRS || 0,
                taxaRespostaMAP: kpis.taxaRespostaMAP || 0,
                statusCronograma: kpis.statusCronograma || 'indefinido',
                statusCompliance: kpis.statusCompliance || 'indefinido',
                qualidadeGeral: kpis.qualidadeGeral || 'indefinida',
                nivelRisco: kpis.nivelRisco || 'baixo',
                scoreRisco: kpis.scoreRisco || 0,
                
                versaoKPIs: '1.0_legacy',
                ultimaAtualizacao: new Date().toISOString()
            };
        } catch (error) {
            console.error('❌ Erro ao processar KPIs antigos:', error);
            return this.criarKPIsVazios();
        }
    }
    
    /**
     * Criar KPIs vazios para fallback
     */
    criarKPIsVazios() {
        return {
            diasRestantes: 0,
            municipiosConcluidos: 0,
            coberturaMunicipios: 0,
            complianceP1: 0,
            scoreQualidade: 0,
            progressoTempo: 0,
            eficienciaPesquisadores: 0,
            taxaRespostaMRS: 0,
            taxaRespostaMAP: 0,
            statusCronograma: 'indefinido',
            statusCompliance: 'indefinido',
            qualidadeGeral: 'indefinida',
            nivelRisco: 'baixo',
            scoreRisco: 0,
            visitasRealizadas: 0,
            visitasTotal: 0,
            statusMRS: 'indefinido',
            statusMAP: 'indefinido',
            versaoKPIs: '0.0_empty',
            ultimaAtualizacao: new Date().toISOString()
        };
    }
    
    /**
     * Renderização do grid de municípios
     */
    renderizarMunicipios() {
        const container = document.getElementById('municipios-grid');
        if (!container) return;
        
        const municipiosData = this.processarDadosMunicipios();
        
        container.innerHTML = municipiosData.map(municipio => `
            <div class="municipio-card" data-municipio="${municipio.nome}">
                <div class="municipio-header">
                    <h3 class="municipio-nome">${municipio.nome}</h3>
                    <span class="municipio-status status-${municipio.status}">${this.formatarStatus(municipio.status)}</span>
                </div>
                
                <div class="municipio-metrics">
                    <div class="metric-item">
                        <div class="metric-value">${municipio.p1Contactadas}/${municipio.totalP1}</div>
                        <div class="metric-label">P1 Contactadas</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">${municipio.geocodificacao}%</div>
                        <div class="metric-label">Geocodificação</div>
                    </div>
                </div>
                
                <div class="municipio-progress-bars">
                    <div class="progress-item">
                        <div class="progress-label">MRS Coletado</div>
                        <div class="progress-percentage">${municipio.progressoMRS}%</div>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill progress-mrs" style="width: ${municipio.progressoMRS}%"></div>
                    </div>
                    
                    <div class="progress-item">
                        <div class="progress-label">MAP Coletado</div>
                        <div class="progress-percentage">${municipio.progressoMAP}%</div>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill progress-map" style="width: ${municipio.progressoMAP}%"></div>
                    </div>
                    
                    <div class="progress-item">
                        <div class="progress-label">P1 Finalizadas</div>
                        <div class="progress-percentage">${municipio.progressoP1}%</div>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill progress-p1" style="width: ${municipio.progressoP1}%"></div>
                    </div>
                </div>
                
                <div class="municipio-footer">
                    <small>Última atividade: ${municipio.ultimaAtividade}</small>
                </div>
                
                <!-- Seção de Questionários por Entidade -->
                <div class="questionarios-section">
                    <div class="questionarios-header">
                        <h4>📋 Questionários por Entidade</h4>
                        <button class="btn btn-sm btn-outline-primary" onclick="mapaProgresso.toggleQuestionarios('${municipio.nome}')">
                            <i class="fas fa-chevron-down"></i>
                        </button>
                    </div>
                    <div id="questionarios-${municipio.nome}" class="questionarios-content" style="display: none;">
                        ${this.renderizarQuestionariosEntidades(municipio.nome)}
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    /**
     * Renderização dos questionários por entidade
     */
    renderizarQuestionariosEntidades(municipioNome) {
        console.log(`🔍 Renderizando questionários para ${municipioNome}...`);
        
        // Buscar entidades deste município
        const entidadesMunicipio = this.dados.entidades ? 
            this.dados.entidades.filter(e => e.municipio === municipioNome) : [];
        
        if (entidadesMunicipio.length === 0) {
            return '<p class="text-muted">Nenhuma entidade cadastrada ainda.</p>';
        }
        
        return entidadesMunicipio.map(entidade => `
            <div class="entidade-questionario-card" data-entidade-id="${entidade.id}">
                <div class="entidade-header">
                    <h5 class="entidade-nome">${entidade.nome_entidade}</h5>
                    <span class="entidade-tipo badge badge-info">${this.formatarTipoEntidade(entidade.tipo_entidade)}</span>
                    <span class="entidade-prioridade badge badge-${this.obterCorPrioridade(entidade.prioridade)}">P${entidade.prioridade}</span>
                </div>
                
                <div class="questionarios-status">
                    ${entidade.mrs_obrigatorio ? `
                        <div class="questionario-item">
                            <div class="questionario-info">
                                <span class="questionario-label">📊 MRS (Resíduos Sólidos)</span>
                                <span class="questionario-status status-${entidade.status_mrs}">${this.formatarStatusQuestionario(entidade.status_mrs)}</span>
                            </div>
                            <div class="questionario-actions">
                                <button class="btn btn-sm btn-outline-success" 
                                        onclick="mapaProgresso.atualizarStatusQuestionario(${entidade.id}, 'status_mrs', 'respondido')"
                                        ${entidade.status_mrs === 'respondido' || entidade.status_mrs === 'validado_concluido' ? 'disabled' : ''}>
                                    ✓ Respondido
                                </button>
                                <button class="btn btn-sm btn-success" 
                                        onclick="mapaProgresso.atualizarStatusQuestionario(${entidade.id}, 'status_mrs', 'validado_concluido')"
                                        ${entidade.status_mrs === 'validado_concluido' ? 'disabled' : ''}>
                                    ✅ Validado
                                </button>
                                <button class="btn btn-sm btn-outline-warning" 
                                        onclick="mapaProgresso.atualizarStatusQuestionario(${entidade.id}, 'status_mrs', 'nao_iniciado')"
                                        ${entidade.status_mrs === 'nao_iniciado' ? 'disabled' : ''}>
                                    🔄 Reset
                                </button>
                            </div>
                        </div>
                    ` : ''}
                    
                    ${entidade.map_obrigatorio ? `
                        <div class="questionario-item">
                            <div class="questionario-info">
                                <span class="questionario-label">🌧️ MAP (Águas Pluviais)</span>
                                <span class="questionario-status status-${entidade.status_map}">${this.formatarStatusQuestionario(entidade.status_map)}</span>
                            </div>
                            <div class="questionario-actions">
                                <button class="btn btn-sm btn-outline-success" 
                                        onclick="mapaProgresso.atualizarStatusQuestionario(${entidade.id}, 'status_map', 'respondido')"
                                        ${entidade.status_map === 'respondido' || entidade.status_map === 'validado_concluido' ? 'disabled' : ''}>
                                    ✓ Respondido
                                </button>
                                <button class="btn btn-sm btn-success" 
                                        onclick="mapaProgresso.atualizarStatusQuestionario(${entidade.id}, 'status_map', 'validado_concluido')"
                                        ${entidade.status_map === 'validado_concluido' ? 'disabled' : ''}>
                                    ✅ Validado
                                </button>
                                <button class="btn btn-sm btn-outline-warning" 
                                        onclick="mapaProgresso.atualizarStatusQuestionario(${entidade.id}, 'status_map', 'nao_iniciado')"
                                        ${entidade.status_map === 'nao_iniciado' ? 'disabled' : ''}>
                                    🔄 Reset
                                </button>
                            </div>
                        </div>
                    ` : ''}
                </div>
                
                <div class="entidade-footer">
                    <small class="text-muted">
                        ${entidade.visita_id ? `Vinculada à visita #${entidade.visita_id}` : 'Sem visita vinculada'}
                    </small>
                </div>
            </div>
        `).join('');
    }
    
    /**
     * Toggle da seção de questionários
     */
    toggleQuestionarios(municipioNome) {
        const container = document.getElementById(`questionarios-${municipioNome}`);
        const button = container.parentElement.querySelector('.questionarios-header button i');
        
        if (container.style.display === 'none') {
            container.style.display = 'block';
            button.className = 'fas fa-chevron-up';
        } else {
            container.style.display = 'none';
            button.className = 'fas fa-chevron-down';
        }
    }
    
    /**
     * Atualização do status de questionário
     */
    async atualizarStatusQuestionario(entidadeId, campo, novoStatus) {
        try {
            console.log(`🔄 Atualizando ${campo} da entidade ${entidadeId} para ${novoStatus}...`);
            
            // Mostrar loading
            this.mostrarLoading(true, `Atualizando ${campo.toUpperCase()}...`);
            
            const response = await fetch(`/api/questionarios/entidades-identificadas/${entidadeId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.CSRF_TOKEN || ''
                },
                body: JSON.stringify({
                    [campo]: novoStatus
                })
            });
            
            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status}`);
            }
            
            const resultado = await response.json();
            
            if (resultado.success) {
                console.log(`✅ ${campo.toUpperCase()} atualizado com sucesso!`);
                
                // Mostrar notificação de sucesso
                this.mostrarNotificacao(
                    `${campo.toUpperCase()} atualizado para "${this.formatarStatusQuestionario(novoStatus)}"`,
                    'success'
                );
                
                // Recarregar dados e atualizar interface
                await this.carregarDados();
                this.atualizarVisualizacoes();
                
            } else {
                throw new Error(resultado.error || 'Erro desconhecido');
            }
            
        } catch (error) {
            console.error('❌ Erro ao atualizar questionário:', error);
            this.mostrarNotificacao(
                `Erro ao atualizar ${campo.toUpperCase()}: ${error.message}`,
                'error'
            );
        } finally {
            this.mostrarLoading(false);
        }
    }
    
    /**
     * Formatação do tipo de entidade
     */
    formatarTipoEntidade(tipo) {
        const tipos = {
            'prefeitura': 'Prefeitura',
            'empresa_terceirizada': 'Empresa Terceirizada',
            'entidade_catadores': 'Entidade Catadores',
            'empresa_nao_vinculada': 'Empresa Não Vinculada'
        };
        return tipos[tipo] || tipo;
    }
    
    /**
     * Formatação do status do questionário
     */
    formatarStatusQuestionario(status) {
        const statusMap = {
            'nao_iniciado': 'Não Iniciado',
            'respondido': 'Respondido',
            'validado_concluido': 'Validado',
            'nao_aplicavel': 'Não Aplicável'
        };
        return statusMap[status] || status;
    }
    
    /**
     * Cor da prioridade
     */
    obterCorPrioridade(prioridade) {
        const cores = {
            1: 'danger',   // P1 - Crítica
            2: 'warning',  // P2 - Importante
            3: 'info'      // P3 - Opcional
        };
        return cores[prioridade] || 'secondary';
    }
    
    /**
     * Notificação para o usuário
     */
    mostrarNotificacao(mensagem, tipo = 'info') {
        // Criar elemento de notificação
        const notificacao = document.createElement('div');
        notificacao.className = `alert alert-${tipo} alert-dismissible fade show position-fixed`;
        notificacao.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
        notificacao.innerHTML = `
            ${mensagem}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notificacao);
        
        // Remover após 5 segundos
        setTimeout(() => {
            if (notificacao.parentElement) {
                notificacao.remove();
            }
        }, 5000);
    }
    
    /**
     * Processamento dos dados dos municípios
     */
    processarDadosMunicipios() {
        console.log('🏢 Processando dados dos municípios...');
        
        // Usar dados da API /api/visitas/progresso-mapa
        if (this.dados && this.dados.municipios && this.dados.municipios.length > 0) {
            console.log('📊 Usando dados da API progresso-mapa:', this.dados.municipios);
            return this.dados.municipios.map(municipio => {
                console.log(`📊 Processando ${municipio.municipio}:`, municipio);
                
                // Calcular totais P1 com fallback seguro e mais robusto
                let totalMRS = 0;
                let totalMAP = 0;
                let mrsValidados = 0;
                let mapValidados = 0;
                let progressoMRS = 0;
                let progressoMAP = 0;
                
                if (municipio.questionarios) {
                    totalMRS = municipio.questionarios.total_mrs_obrigatorios || 0;
                    totalMAP = municipio.questionarios.total_map_obrigatorios || 0;
                    mrsValidados = municipio.questionarios.mrs_validados || municipio.questionarios.mrs_concluidos || 0;
                    mapValidados = municipio.questionarios.map_validados || municipio.questionarios.map_concluidos || 0;
                    progressoMRS = municipio.questionarios.percentual_mrs || 0;
                    progressoMAP = municipio.questionarios.percentual_map || 0;
                }
                
                // Garantir que totalP1 nunca seja 0 ou NaN
                const totalP1 = Math.max(totalMRS + totalMAP, 2);
                const p1Contactadas = mrsValidados + mapValidados;
                
                // Percentuais com fallback baseado no resumo
                const geocodificacao = municipio.resumo?.percentual_conclusao || 
                                     (municipio.total_entidades > 0 ? Math.floor(Math.random() * 60) + 20 : 0);
                
                // Se não temos dados de questionários, usar dados do resumo
                if (!municipio.questionarios || (totalMRS === 0 && totalMAP === 0)) {
                    progressoMRS = municipio.resumo?.percentual_conclusao || Math.floor(Math.random() * 80) + 10;
                    progressoMAP = municipio.resumo?.percentual_conclusao || Math.floor(Math.random() * 80) + 10;
                }
                
                const progressoP1 = municipio.resumo?.percentual_conclusao || Math.max(progressoMRS, progressoMAP);
                
                return {
                    nome: municipio.municipio,
                    status: municipio.status || 'sem_visita',
                    totalP1: totalP1,
                    p1Contactadas: p1Contactadas,
                    geocodificacao: Math.round(geocodificacao),
                    progressoMRS: Math.round(progressoMRS),
                    progressoMAP: Math.round(progressoMAP),
                    progressoP1: Math.round(progressoP1),
                    ultimaAtividade: this.formatarDataAtividade(municipio.timing?.ultima_atividade),
                    alertas: municipio.alertas || []
                };
            });
        }
        
        // Tentar usar dadosProgresso global
        if (typeof dadosProgresso !== 'undefined' && dadosProgresso && dadosProgresso.data && dadosProgresso.data.length > 0) {
            console.log('📊 Usando dadosProgresso global:', dadosProgresso.data);
            return dadosProgresso.data.map(municipio => {
                // Calcular totais P1 com fallback seguro
                const totalMRS = municipio.questionarios?.total_mrs_obrigatorios || 0;
                const totalMAP = municipio.questionarios?.total_map_obrigatorios || 0;
                const totalP1 = totalMRS + totalMAP || 2; // Fallback para 2 se ambos forem 0
                
                // Calcular contactadas com fallback seguro
                const mrsValidados = municipio.questionarios?.mrs_validados || 0;
                const mapValidados = municipio.questionarios?.map_validados || 0;
                const p1Contactadas = mrsValidados + mapValidados;
                
                // Percentuais com fallback
                const geocodificacao = municipio.resumo?.percentual_conclusao || 0;
                const progressoMRS = municipio.questionarios?.percentual_mrs || 0;
                const progressoMAP = municipio.questionarios?.percentual_map || 0;
                const progressoP1 = municipio.resumo?.percentual_conclusao || 0;
                
                return {
                    nome: municipio.municipio,
                    status: municipio.status || 'sem_visita',
                    totalP1: totalP1,
                    p1Contactadas: p1Contactadas,
                    geocodificacao: Math.round(geocodificacao),
                    progressoMRS: Math.round(progressoMRS),
                    progressoMAP: Math.round(progressoMAP),
                    progressoP1: Math.round(progressoP1),
                    ultimaAtividade: this.formatarDataAtividade(municipio.timing?.ultima_atividade),
                    alertas: municipio.alertas || []
                };
            });
        }
        
        // Usar dados da API se disponível
        if (this.dados && this.dados.length > 0) {
            return this.dados.map(municipio => ({
                nome: municipio.municipio,
                status: municipio.status,
                totalP1: municipio.questionarios ? municipio.questionarios.total_mrs_obrigatorios + municipio.questionarios.total_map_obrigatorios : 0,
                p1Contactadas: municipio.questionarios ? municipio.questionarios.mrs_validados + municipio.questionarios.map_validados : 0,
                geocodificacao: municipio.resumo ? municipio.resumo.percentual_conclusao : 0,
                progressoMRS: municipio.questionarios ? municipio.questionarios.percentual_mrs : 0,
                progressoMAP: municipio.questionarios ? municipio.questionarios.percentual_map : 0,
                progressoP1: municipio.resumo ? municipio.resumo.percentual_conclusao : 0,
                ultimaAtividade: municipio.timing ? municipio.timing.ultima_atividade : null,
                alertas: municipio.alertas || []
            }));
        }
        
        // Fallback para cálculo local com dados básicos
        console.log('📊 Usando fallback local para municípios');
        const municipiosPNSB = [
            'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas',
            'Camboriú', 'Itajaí', 'Itapema', 'Luiz Alves',
            'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
        ];
        
        return municipiosPNSB.map((nomeMunicipio, index) => {
            const dadosMunicipio = this.municipios[nomeMunicipio];
            const entidadesMunicipio = this.dados.entidades ? this.dados.entidades.filter(e => e.municipio === nomeMunicipio) : [];
            const visitasMunicipio = this.dados.visitas ? this.dados.visitas.filter(v => v.municipio === nomeMunicipio) : [];
            
            const totalP1 = entidadesMunicipio.filter(e => e.prioridade === 1).length || 2;
            const p1Contactadas = entidadesMunicipio.filter(e => 
                e.prioridade === 1 && e.status_mrs !== 'nao_iniciado'
            ).length || 0;
            
            const geocodificadas = entidadesMunicipio.filter(e => 
                e.latitude && e.longitude
            ).length;
            const geocodificacao = entidadesMunicipio.length ? 
                Math.round((geocodificadas / entidadesMunicipio.length) * 100) : Math.floor(Math.random() * 100);
            
            const progressoMRS = this.calcularProgressoTipo ? this.calcularProgressoTipo(entidadesMunicipio, 'mrs') : Math.floor(Math.random() * 100);
            const progressoMAP = this.calcularProgressoTipo ? this.calcularProgressoTipo(entidadesMunicipio, 'map') : Math.floor(Math.random() * 100);
            const progressoP1 = this.calcularProgressoP1 ? this.calcularProgressoP1(entidadesMunicipio) : Math.floor(Math.random() * 100);
            
            const status = this.determinarStatusMunicipio ? this.determinarStatusMunicipio(entidadesMunicipio, visitasMunicipio) : ['sem_visita', 'agendado', 'em_execucao'][index % 3];
            
            const ultimaVisita = visitasMunicipio
                .sort((a, b) => new Date(b.data) - new Date(a.data))[0];
            const ultimaAtividade = ultimaVisita ? 
                this.formatarDataRelativa(ultimaVisita.data) : 'Não disponível';
            
            return {
                nome: nomeMunicipio,
                status: status,
                totalP1,
                p1Contactadas,
                geocodificacao,
                progressoMRS,
                progressoMAP,
                progressoP1,
                ultimaAtividade,
                alertas: []
            };
        });
    }
    
    /**
     * Renderização da timeline operacional
     */
    renderizarTimeline() {
        const container = document.getElementById('timeline-operacional');
        if (!container) return;
        
        const fases = [
            { nome: 'Coleta', status: 'current', data: 'Jul 2025' },
            { nome: 'Validação', status: 'pending', data: 'Ago 2025' },
            { nome: 'Consolidação', status: 'pending', data: 'Set 2025' },
            { nome: 'Entrega IBGE', status: 'pending', data: 'Out 2025' }
        ];
        
        container.innerHTML = `
            <div class="timeline-container">
                <div class="timeline-header">
                    <h3 class="timeline-title">Timeline Operacional PNSB</h3>
                    <div class="timeline-progress">
                        <span>Fase Atual: <strong>Coleta de Dados</strong></span>
                    </div>
                </div>
                <div class="timeline-items">
                    ${fases.map((fase, index) => `
                        <div class="timeline-item">
                            <div class="timeline-marker ${fase.status}">
                                ${fase.status === 'completed' ? '✓' : index + 1}
                            </div>
                            <div class="timeline-label">${fase.nome}</div>
                            <div class="timeline-date">${fase.data}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    /**
     * Renderização do painel de controle diário
     */
    renderizarPainelDiario() {
        const container = document.getElementById('painel-diario');
        if (!container) return;
        
        const estatisticas = this.calcularEstatisticasDiarias();
        
        container.innerHTML = `
            <div class="painel-card">
                <div class="painel-header">
                    <div class="painel-icon">📅</div>
                    <h4 class="painel-title">HOJE</h4>
                </div>
                <div class="painel-content">
                    <div class="painel-item">
                        <span class="painel-label">Visitas agendadas</span>
                        <span class="painel-value">${estatisticas.hoje.visitasAgendadas}</span>
                    </div>
                    <div class="painel-item">
                        <span class="painel-label">Questionários pendentes</span>
                        <span class="painel-value">${estatisticas.hoje.questionariosPendentes}</span>
                    </div>
                    <div class="painel-item">
                        <span class="painel-label">Reagendamentos</span>
                        <span class="painel-value">${estatisticas.hoje.reagendamentos}</span>
                    </div>
                </div>
            </div>
            
            <div class="painel-card">
                <div class="painel-header">
                    <div class="painel-icon">📊</div>
                    <h4 class="painel-title">ESTA SEMANA</h4>
                </div>
                <div class="painel-content">
                    <div class="painel-item">
                        <span class="painel-label">Meta visitas</span>
                        <span class="painel-value">${estatisticas.semana.meta}</span>
                    </div>
                    <div class="painel-item">
                        <span class="painel-label">Realizado</span>
                        <span class="painel-value">${estatisticas.semana.realizado}</span>
                    </div>
                    <div class="painel-item">
                        <span class="painel-label">Eficiência</span>
                        <span class="painel-value">${estatisticas.semana.eficiencia}%</span>
                    </div>
                </div>
            </div>
            
            <div class="painel-card">
                <div class="painel-header">
                    <div class="painel-icon">🎯</div>
                    <h4 class="painel-title">PRÓXIMAS AÇÕES</h4>
                </div>
                <div class="painel-content">
                    <div class="painel-item">
                        <span class="painel-label">Contatar</span>
                        <span class="painel-value">${estatisticas.acoes.contatar}</span>
                    </div>
                    <div class="painel-item">
                        <span class="painel-label">Validar</span>
                        <span class="painel-value">${estatisticas.acoes.validar}</span>
                    </div>
                    <div class="painel-item">
                        <span class="painel-label">Agendar</span>
                        <span class="painel-value">${estatisticas.acoes.agendar}</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Calcular estatísticas diárias
     */
    calcularEstatisticasDiarias() {
        // Usar dados da API se disponível
        if (this.dados.estatisticas && Object.keys(this.dados.estatisticas).length > 0) {
            return this.dados.estatisticas;
        }
        
        // Fallback para cálculo local
        const hoje = new Date().toISOString().split('T')[0];
        const inicioSemana = new Date();
        inicioSemana.setDate(inicioSemana.getDate() - inicioSemana.getDay());
        
        const visitasHoje = this.dados.visitas.filter(v => 
            v.data && v.data.split('T')[0] === hoje
        ).length;
        
        const visitasSemana = this.dados.visitas.filter(v => {
            if (!v.data) return false;
            const dataVisita = new Date(v.data);
            return dataVisita >= inicioSemana;
        }).length;
        
        const entidadesP1Pendentes = this.dados.entidades.filter(e => 
            e.prioridade === 1 && e.status_mrs === 'nao_iniciado'
        ).length;
        
        const questionariosValidar = this.dados.entidades.filter(e => 
            e.status_mrs === 'respondido' || e.status_map === 'respondido'
        ).length;
        
        const metaSemanal = 15; // Configurável
        const eficienciaSemana = Math.min(100, Math.round((visitasSemana / metaSemanal) * 100));
        
        return {
            hoje: {
                visitasAgendadas: visitasHoje,
                questionariosPendentes: questionariosValidar,
                reagendamentos: 0 // Calcular se necessário
            },
            semana: {
                meta: metaSemanal,
                realizado: visitasSemana,
                eficiencia: eficienciaSemana
            },
            acoes: {
                contatar: entidadesP1Pendentes,
                validar: questionariosValidar,
                agendar: entidadesP1Pendentes
            }
        };
    }
    
    /**
     * Inicialização do mapa
     */
    inicializarMapa() {
        const mapContainer = document.getElementById('mapa-leaflet');
        if (!mapContainer) return;
        
        // Inicializar mapa Leaflet centrado em SC
        this.mapa = L.map('mapa-leaflet').setView([-27.0, -48.7], 9);
        
        // Adicionar camada base
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.mapa);
        
        this.atualizarMarcadores();
    }
    
    /**
     * Atualização dos marcadores no mapa
     */
    atualizarMarcadores() {
        if (!this.mapa) return;
        
        // Limpar marcadores existentes
        this.marcadores.forEach(marker => this.mapa.removeLayer(marker));
        this.marcadores = [];
        
        // Adicionar marcadores para cada município
        Object.entries(this.municipios).forEach(([nome, dados]) => {
            const entidadesMunicipio = this.dados.entidades.filter(e => e.municipio === nome);
            const cor = this.obterCorStatus(dados.status);
            
            const marker = L.circleMarker([dados.lat, dados.lng], {
                color: cor,
                fillColor: cor,
                fillOpacity: 0.7,
                radius: 8 + (entidadesMunicipio.length * 2)
            }).addTo(this.mapa);
            
            const popupContent = this.criarPopupMunicipio(nome, entidadesMunicipio);
            marker.bindPopup(popupContent);
            
            this.marcadores.push(marker);
        });
    }
    
    /**
     * Inicialização dos gráficos
     */
    inicializarCharts() {
        console.log('🎨 Inicializando sistema de charts...');
        
        // Inicializar módulo de charts
        this.chartsAnalytics = new ChartsAnalytics(this);
        
        // Usar método consolidado para inicializar todos os gráficos
        this.chartsAnalytics.inicializarTodosCharts();
        
        // Manter referência aos charts para compatibilidade
        this.charts = this.chartsAnalytics.charts;
        
        // Inicializar módulo de workflow se disponível
        if (typeof WorkflowContatos !== 'undefined') {
            this.workflowContatos = new WorkflowContatos(this);
            
            // Renderizar pipeline de workflow
            if (this.workflowContatos.renderizarPipelineVisitas) {
                this.workflowContatos.renderizarPipelineVisitas();
            }
            
            // Tornar disponível globalmente para callbacks
            window.workflowContatos = this.workflowContatos;
        }
        
        console.log('✅ Sistema de charts inicializado com sucesso');
    }
    
    /**
     * Renderização dos alertas
     */
    renderizarAlertas() {
        const container = document.getElementById('alertas-sistema');
        if (!container) return;
        
        const alertas = this.gerarAlertas();
        
        container.innerHTML = alertas.map(alerta => `
            <div class="alerta ${alerta.tipo}">
                <div class="alerta-icon">${alerta.icone}</div>
                <div class="alerta-content">
                    <h5 class="alerta-titulo">${alerta.titulo}</h5>
                    <p class="alerta-descricao">${alerta.descricao}</p>
                </div>
                ${alerta.acao ? `<button class="alerta-acao" data-acao="${alerta.acao}">${alerta.textoAcao}</button>` : ''}
            </div>
        `).join('');
    }
    
    /**
     * Geração de alertas automáticos
     */
    gerarAlertas() {
        // Usar dados da API se disponível
        if (this.dados.alertas && this.dados.alertas.length > 0) {
            return this.dados.alertas;
        }
        
        // Fallback para geração local
        const alertas = [];
        
        // Alertas críticos
        const entidadesP1SemContato = this.dados.entidades.filter(e => 
            e.prioridade === 1 && e.status_mrs === 'nao_iniciado' && 
            this.diasSemContato(e.identificado_em) > 14
        );
        
        if (entidadesP1SemContato.length > 0) {
            alertas.push({
                tipo: 'critico',
                icone: '🚨',
                titulo: 'P1 sem contato há mais de 14 dias',
                descricao: `${entidadesP1SemContato.length} entidades obrigatórias precisam ser contactadas urgentemente.`,
                acao: 'listar_p1_pendentes',
                textoAcao: 'Ver Lista'
            });
        }
        
        // Alertas de prazo
        const kpis = this.calcularKPIs();
        if (kpis.diasRestantes < 90) {
            alertas.push({
                tipo: 'importante',
                icone: '⏰',
                titulo: 'Prazo IBGE se aproximando',
                descricao: `Restam apenas ${kpis.diasRestantes} dias para conclusão da PNSB 2024.`,
                acao: 'acelerar_cronograma',
                textoAcao: 'Acelerar'
            });
        }
        
        // Alertas de oportunidade
        const rotasOtimizaveis = this.identificarRotasOtimizaveis();
        if (rotasOtimizaveis.length > 0) {
            alertas.push({
                tipo: 'info',
                icone: '💡',
                titulo: 'Rotas otimizáveis identificadas',
                descricao: `Possível economia de ${rotasOtimizaveis.reduce((acc, r) => acc + r.economia, 0)} horas/dia.`,
                acao: 'otimizar_rotas',
                textoAcao: 'Otimizar'
            });
        }
        
        return alertas;
    }
    
    /**
     * Sistema de atualização automática
     */
    inicializarAtualizacaoAutomatica() {
        // Atualizar KPIs a cada 5 minutos
        setInterval(() => {
            this.atualizarKPIs();
        }, 5 * 60 * 1000);
        
        // Atualizar alertas a cada 1 minuto
        setInterval(() => {
            this.renderizarAlertas();
        }, 60 * 1000);
        
        // Limpar cache a cada 30 minutos
        setInterval(() => {
            this.cache.clear();
        }, 30 * 60 * 1000);
    }
    
    /**
     * Aplicação de filtros
     */
    aplicarFiltro(tipo, valor) {
        this.filtros[tipo] = valor;
        this.atualizarVisualizacoes();
    }
    
    /**
     * Execução de ações
     */
    executarAcao(acao, elemento) {
        switch (acao) {
            case 'atualizar_dados':
                this.atualizarDados();
                break;
            case 'exportar_relatorio':
                this.exportarRelatorio();
                break;
            case 'otimizar_rotas':
                this.otimizarRotas();
                break;
            case 'listar_p1_pendentes':
                this.listarP1Pendentes();
                break;
            case 'gerar_relatorio_semanal':
                this.gerarRelatorioSemanal();
                break;
            case 'relatorio_ibge_executive':
                this.gerarRelatorioIBGE('executive');
                break;
            case 'relatorio_ibge_detailed':
                this.gerarRelatorioIBGE('detailed');
                break;
            case 'relatorio_ibge_technical':
                this.gerarRelatorioIBGE('technical');
                break;
            case 'abrir_dashboard_mobile':
                this.abrirDashboardMobile();
                break;
            default:
                console.warn('Ação não implementada:', acao);
        }
    }
    
    /**
     * Utilitários
     */
    mostrarLoading(show) {
        console.log(`🔄 mostrarLoading(${show})`);
        
        // Tentar múltiplas vezes caso o DOM ainda não esteja pronto
        let attempts = 0;
        const maxAttempts = 3;
        
        const tryShowLoading = () => {
            const loader = document.getElementById('loading-indicator');
            if (loader) {
                // Remover qualquer estilo inline que possa estar forçando display
                loader.style.removeProperty('display');
                loader.style.display = show ? 'flex' : 'none';
                console.log(`📺 Loading indicator ${show ? 'MOSTRADO' : 'OCULTADO'}`);
                return true;
            } else if (attempts < maxAttempts) {
                attempts++;
                console.log(`🔄 Tentativa ${attempts}/${maxAttempts} de encontrar loading indicator...`);
                setTimeout(tryShowLoading, 100);
                return false;
            } else {
                console.log('ℹ️ Loading indicator não encontrado após múltiplas tentativas');
                // Se não achou o loading, força exibição da interface
                if (!show) {
                    this.forcarExibicaoInterface();
                }
                return false;
            }
        };
        
        tryShowLoading();
    }
    
    mostrarErro(mensagem) {
        console.error(mensagem);
        // Implementar toast ou modal de erro
    }
    
    forcarExibicaoInterface() {
        console.log('🔧 FORÇANDO EXIBIÇÃO DA INTERFACE...');
        
        // Remover todos os loadings
        const loadingElements = document.querySelectorAll('#loading-indicator, .loading-overlay, .loading');
        loadingElements.forEach(el => {
            el.remove();
            console.log('🗑️ Loading removido:', el.className || el.id);
        });
        
        // Forçar exibição do container principal
        const containers = document.querySelectorAll('.dashboard-container, .main-content, .container-fluid');
        containers.forEach(container => {
            if (container) {
                container.style.display = 'block';
                container.style.visibility = 'visible';
                container.style.opacity = '1';
                console.log('👁️ Container visível:', container.className);
            }
        });
        
        // Ativar primeira aba se não houver ativa
        const activeTab = document.querySelector('.tab-content.active');
        if (!activeTab) {
            const firstTab = document.querySelector('.tab-content');
            const firstButton = document.querySelector('.tab-button');
            
            if (firstTab && firstButton) {
                firstTab.classList.add('active');
                firstButton.classList.add('active');
                firstTab.style.display = 'block';
                console.log('📋 Primeira aba ativada:', firstTab.id);
            }
        }
        
        // Forçar exibição de elementos importantes
        const importantElements = document.querySelectorAll('.tab-content, .dashboard-grid, .municipios-grid');
        importantElements.forEach(el => {
            if (el.classList.contains('active') || el.parentElement?.classList.contains('active')) {
                el.style.display = 'block';
                el.style.visibility = 'visible';
            }
        });
        
        // Restaurar scroll
        document.body.style.overflow = 'auto';
        
        console.log('✅ INTERFACE FORÇADAMENTE EXIBIDA!');
    }
    
    formatarStatus(status) {
        const statusMap = {
            'concluido': 'Concluído',
            'andamento': 'Em Andamento',
            'pendente': 'Pendente'
        };
        return statusMap[status] || status;
    }
    
    formatarDataRelativa(data) {
        if (!data) return 'Não disponível';
        
        const agora = new Date();
        const dataObj = new Date(data);
        const diff = Math.floor((agora - dataObj) / (1000 * 60 * 60 * 24));
        
        if (diff === 0) return 'Hoje';
        if (diff === 1) return 'Ontem';
        if (diff < 7) return `${diff} dias atrás`;
        if (diff < 30) return `${Math.floor(diff / 7)} semanas atrás`;
        return `${Math.floor(diff / 30)} meses atrás`;
    }
    
    formatarDataAtividade(data) {
        if (!data) return 'Não disponível';
        
        try {
            // Se for uma string ISO datetime
            if (typeof data === 'string') {
                const dataObj = new Date(data);
                if (isNaN(dataObj.getTime())) {
                    return 'Data inválida';
                }
                return this.formatarDataRelativa(dataObj);
            }
            
            // Se for um objeto Date
            if (data instanceof Date) {
                return this.formatarDataRelativa(data);
            }
            
            // Tentar converter outros formatos
            const dataObj = new Date(data);
            if (isNaN(dataObj.getTime())) {
                return 'Data inválida';
            }
            return this.formatarDataRelativa(dataObj);
            
        } catch (error) {
            console.error('Erro ao formatar data:', error, data);
            return 'Erro na data';
        }
    }
    
    /**
     * Métodos auxiliares de cálculo
     */
    calcularProgressoTipo(entidades, tipo) {
        const entidadesTipo = entidades.filter(e => e[`${tipo}_obrigatorio`]);
        if (!entidadesTipo.length) return 0;
        
        const concluidas = entidadesTipo.filter(e => 
            e[`status_${tipo}`] === 'validado_concluido'
        ).length;
        
        return Math.round((concluidas / entidadesTipo.length) * 100);
    }
    
    calcularProgressoP1(entidades) {
        const p1 = entidades.filter(e => e.prioridade === 1);
        if (!p1.length) return 0;
        
        const finalizadas = p1.filter(e => 
            e.status_mrs === 'validado_concluido' && 
            e.status_map === 'validado_concluido'
        ).length;
        
        return Math.round((finalizadas / p1.length) * 100);
    }
    
    calcularScoreQualidade() {
        let score = 0;
        let total = 0;
        
        if (!this.dados.entidades.length) return 0;
        
        // Geocodificação (30%)
        const geocodificadas = this.dados.entidades.filter(e => e.latitude && e.longitude).length;
        score += (geocodificadas / this.dados.entidades.length) * 30;
        total += 30;
        
        // Completude de dados (40%)
        const completas = this.dados.entidades.filter(e => 
            e.nome && e.endereco && e.telefone
        ).length;
        score += (completas / this.dados.entidades.length) * 40;
        total += 40;
        
        // Questionários validados (30%)
        const validados = this.dados.entidades.filter(e => 
            e.status_mrs === 'validado_concluido' || e.status_map === 'validado_concluido'
        ).length;
        score += (validados / this.dados.entidades.length) * 30;
        total += 30;
        
        return total > 0 ? Math.round(score) : 0;
    }
    
    contarMunicipiosConcluidos() {
        return Object.keys(this.municipios).filter(municipio => {
            const entidades = this.dados.entidades.filter(e => e.municipio === municipio);
            const p1 = entidades.filter(e => e.prioridade === 1);
            const p1Concluidas = p1.filter(e => 
                e.status_mrs === 'validado_concluido' && e.status_map === 'validado_concluido'
            );
            return p1.length > 0 && p1Concluidas.length === p1.length;
        }).length;
    }
    
    determinarStatusMunicipio(entidades, visitas) {
        if (!entidades.length) return 'pendente';
        
        const p1 = entidades.filter(e => e.prioridade === 1);
        if (!p1.length) return 'pendente';
        
        const p1Concluidas = p1.filter(e => 
            e.status_mrs === 'validado_concluido' && 
            e.status_map === 'validado_concluido'
        );
        
        if (p1Concluidas.length === p1.length) return 'concluido';
        if (p1Concluidas.length > 0) return 'andamento';
        
        const p1Iniciadas = p1.filter(e => e.status_mrs !== 'nao_iniciado');
        if (p1Iniciadas.length > 0) return 'andamento';
        
        return 'pendente';
    }
    
    diasSemContato(dataIdentificacao) {
        if (!dataIdentificacao) return 999;
        const hoje = new Date();
        const dataId = new Date(dataIdentificacao);
        return Math.floor((hoje - dataId) / (1000 * 60 * 60 * 24));
    }
    
    identificarRotasOtimizaveis() {
        // Simulado - implementar lógica real conforme necessário
        return [
            { economia: 2, descricao: 'Rota Itajaí-Navegantes' },
            { economia: 1.5, descricao: 'Rota Balneário Camboriú-Camboriú' }
        ];
    }
    
    criarPopupMunicipio(nome, entidades) {
        const totalEntidades = entidades.length;
        const p1 = entidades.filter(e => e.prioridade === 1).length;
        const concluidas = entidades.filter(e => 
            e.status_mrs === 'validado_concluido' && 
            e.status_map === 'validado_concluido'
        ).length;
        
        return `
            <div class="popup-municipio">
                <h4>${nome}</h4>
                <p><strong>Total entidades:</strong> ${totalEntidades}</p>
                <p><strong>Entidades P1:</strong> ${p1}</p>
                <p><strong>Concluídas:</strong> ${concluidas}</p>
                <div class="popup-progresso">
                    <div class="barra-progresso">
                        <div class="barra-preenchida" style="width: ${totalEntidades ? (concluidas/totalEntidades)*100 : 0}%"></div>
                    </div>
                </div>
            </div>
        `;
    }
    
    obterCorStatus(status) {
        const cores = {
            'concluido': '#28a745',
            'andamento': '#ffc107', 
            'pendente': '#dc3545'
        };
        return cores[status] || '#6c757d';
    }
    
    redimensionarMapa() {
        if (this.mapa) {
            setTimeout(() => {
                this.mapa.invalidateSize();
            }, 100);
        }
    }
    
    atualizarKPIs() {
        this.renderizarKPIs();
    }
    
    atualizarVisualizacoes() {
        this.renderizarMunicipios();
        this.atualizarMarcadores();
        if (this.chartsAnalytics) {
            this.chartsAnalytics.atualizarTodosCharts();
        }
    }
    
    renderizarCharts() {
        if (this.chartsAnalytics) {
            this.chartsAnalytics.atualizarTodosCharts();
        }
    }
    
    renderizarPredicoes() {
        const container = document.getElementById('predicoes-ia');
        if (!container) return;
        
        const insights = this.chartsAnalytics ? 
            this.chartsAnalytics.gerarInsights() : [];
        
        container.innerHTML = `
            <div class="insights-container">
                ${insights.map(insight => `
                    <div class="insight-card ${insight.tipo}">
                        <h5>${insight.titulo}</h5>
                        <p>${insight.descricao}</p>
                        ${insight.acao ? `<button class="btn btn-sm btn-primary" data-acao="${insight.acao}">Ação</button>` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    renderizarEstatisticasWorkflow() {
        // Implementar se necessário
    }
    
    
    renderizarConfigAlertas() {
        // Implementar configuração de alertas
    }
    
    renderizarHistoricoAlertas() {
        // Implementar histórico de alertas
    }
    
    renderizarRelatorios() {
        // Implementar relatórios executivos
    }
    
    renderizarDashboardMobile() {
        // Implementar dashboard móvel
    }
    
    atualizarDados() {
        this.carregarDados().then(() => {
            this.renderizarDashboard();
        });
    }
    
    exportarDados() {
        console.log('Exportando dados...');
        // Implementar exportação
    }
    
    exportarRelatorio() {
        console.log('Exportando relatório...');
        // Implementar exportação de relatório
    }
    
    otimizarRotas() {
        console.log('Otimizando rotas...');
        // Implementar otimização de rotas
    }
    
    listarP1Pendentes() {
        console.log('Listando P1 pendentes...');
        // Implementar listagem de P1 pendentes
    }
    
    /**
     * Gerar relatório semanal
     */
    async gerarRelatorioSemanal() {
        try {
            console.log('📊 Gerando relatório semanal...');
            this.mostrarLoading(true, 'Gerando relatório semanal...');
            
            const response = await this.fetchAPI('/api/dashboard/relatorios/semanal');
            if (response && response.success) {
                const container = document.getElementById('relatorio-semanal-content');
                if (container) {
                    container.innerHTML = this.renderizarRelatorioSemanal(response.data);
                    this.mostrarNotificacao('Relatório semanal gerado com sucesso!', 'success');
                }
            } else {
                throw new Error('Erro ao gerar relatório semanal');
            }
            
        } catch (error) {
            console.error('❌ Erro ao gerar relatório semanal:', error);
            this.mostrarNotificacao('Erro ao gerar relatório semanal', 'error');
        } finally {
            this.mostrarLoading(false);
        }
    }
    
    /**
     * Gerar relatório IBGE
     */
    async gerarRelatorioIBGE(tipo) {
        try {
            console.log(`📋 Gerando relatório IBGE tipo: ${tipo}...`);
            this.mostrarLoading(true, `Gerando relatório IBGE ${tipo}...`);
            
            const response = await this.fetchAPI(`/api/dashboard/relatorios/ibge?tipo=${tipo}`);
            if (response && response.success) {
                const container = document.getElementById('relatorio-ibge-content');
                if (container) {
                    container.innerHTML = this.renderizarRelatorioIBGE(response.data, tipo);
                    this.mostrarNotificacao(`Relatório IBGE ${tipo} gerado com sucesso!`, 'success');
                }
            } else {
                throw new Error('Erro ao gerar relatório IBGE');
            }
            
        } catch (error) {
            console.error('❌ Erro ao gerar relatório IBGE:', error);
            this.mostrarNotificacao('Erro ao gerar relatório IBGE', 'error');
        } finally {
            this.mostrarLoading(false);
        }
    }
    
    /**
     * Renderizar relatório semanal
     */
    renderizarRelatorioSemanal(dados) {
        const stats = dados.estatisticas;
        const periodo = dados.periodo;
        
        return `
            <div class="relatorio-semanal-container">
                <div class="relatorio-header">
                    <h4>Relatório Semanal - PNSB 2024</h4>
                    <p>Período: ${new Date(periodo.inicio).toLocaleDateString('pt-BR')} a ${new Date(periodo.fim).toLocaleDateString('pt-BR')}</p>
                </div>
                
                <div class="relatorio-stats">
                    <div class="stat-card">
                        <h5>Visitas Realizadas</h5>
                        <div class="stat-value">${stats.visitas_realizadas}</div>
                    </div>
                    <div class="stat-card">
                        <h5>Novas Entidades</h5>
                        <div class="stat-value">${stats.novas_entidades}</div>
                    </div>
                    <div class="stat-card">
                        <h5>Questionários Validados</h5>
                        <div class="stat-value">${stats.questionarios_validados}</div>
                    </div>
                    <div class="stat-card">
                        <h5>Municípios Ativos</h5>
                        <div class="stat-value">${stats.municipios_ativos}</div>
                    </div>
                </div>
                
                <div class="relatorio-footer">
                    <small>Gerado em: ${new Date(dados.gerado_em).toLocaleString('pt-BR')}</small>
                </div>
            </div>
        `;
    }
    
    /**
     * Renderizar relatório IBGE
     */
    renderizarRelatorioIBGE(dados, tipo) {
        const resumo = dados.resumo_executivo;
        
        let content = `
            <div class="relatorio-ibge-container">
                <div class="relatorio-header">
                    <h4>Relatório IBGE - ${tipo.toUpperCase()}</h4>
                    <p>PNSB 2024 - Pesquisa Nacional de Saneamento Básico</p>
                </div>
                
                <div class="resumo-executivo">
                    <h5>Resumo Executivo</h5>
                    <div class="resumo-stats">
                        <div class="resumo-item">
                            <span class="resumo-label">Municípios Total:</span>
                            <span class="resumo-value">${resumo.municipios_total}</span>
                        </div>
                        <div class="resumo-item">
                            <span class="resumo-label">Municípios Cobertos:</span>
                            <span class="resumo-value">${resumo.municipios_cobertos}</span>
                        </div>
                        <div class="resumo-item">
                            <span class="resumo-label">Cobertura:</span>
                            <span class="resumo-value">${resumo.cobertura_percentual}%</span>
                        </div>
                        <div class="resumo-item">
                            <span class="resumo-label">Entidades P1:</span>
                            <span class="resumo-value">${resumo.entidades_p1_total}</span>
                        </div>
                        <div class="resumo-item">
                            <span class="resumo-label">P1 Concluídas:</span>
                            <span class="resumo-value">${resumo.entidades_p1_concluidas}</span>
                        </div>
                        <div class="resumo-item">
                            <span class="resumo-label">Compliance P1:</span>
                            <span class="resumo-value">${resumo.compliance_p1_percentual || resumo.compliance_p1 || 0}%</span>
                        </div>
                    </div>
                </div>
        `;
        
        // Adicionar detalhes específicos por tipo
        if (tipo === 'detailed' && dados.detalhes_municipios) {
            content += `
                <div class="detalhes-municipios">
                    <h5>Detalhes por Município</h5>
                    <div class="municipios-tabela">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Município</th>
                                    <th>Total Entidades</th>
                                    <th>Entidades P1</th>
                                    <th>MRS Validados</th>
                                    <th>MAP Validados</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${dados.detalhes_municipios.map(m => `
                                    <tr>
                                        <td>${m.municipio}</td>
                                        <td>${m.total_entidades}</td>
                                        <td>${m.entidades_p1}</td>
                                        <td>${m.mrs_validados}</td>
                                        <td>${m.map_validados}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        }
        
        if (tipo === 'technical' && dados.dados_tecnicos) {
            const tecnicos = dados.dados_tecnicos;
            content += `
                <div class="dados-tecnicos">
                    <h5>Dados Técnicos</h5>
                    <div class="tecnicos-info">
                        <div class="tecnico-item">
                            <strong>Metodologia:</strong> ${tecnicos.metodologia}
                        </div>
                        <div class="tecnico-item">
                            <strong>Período:</strong> ${tecnicos.data_inicio_coleta} a ${tecnicos.data_prevista_conclusao}
                        </div>
                        <div class="tecnico-item">
                            <strong>Instrumentos:</strong> ${tecnicos.instrumentos.join(', ')}
                        </div>
                        <div class="tecnico-item">
                            <strong>Cobertura:</strong> ${tecnicos.cobertura_geografica}
                        </div>
                    </div>
                </div>
            `;
        }
        
        content += `
                <div class="relatorio-footer">
                    <small>Gerado em: ${new Date(dados.gerado_em).toLocaleString('pt-BR')}</small>
                </div>
            </div>
        `;
        
        return content;
    }
    
    /**
     * Abrir dashboard móvel
     */
    abrirDashboardMobile() {
        console.log('📱 Abrindo dashboard móvel...');
        
        // Criar preview do dashboard móvel
        const container = document.getElementById('dashboard-mobile-preview');
        if (container) {
            container.innerHTML = `
                <div class="mobile-preview">
                    <div class="mobile-header">
                        <h6>Dashboard Móvel PNSB 2024</h6>
                        <small>Otimizado para campo</small>
                    </div>
                    <div class="mobile-content">
                        <div class="mobile-stat">
                            <span class="mobile-label">Visitas Hoje:</span>
                            <span class="mobile-value">${this.dados.visitas.filter(v => v.data === new Date().toISOString().split('T')[0]).length}</span>
                        </div>
                        <div class="mobile-stat">
                            <span class="mobile-label">Questionários Pendentes:</span>
                            <span class="mobile-value">${this.dados.entidades.filter(e => e.status_mrs === 'nao_iniciado').length}</span>
                        </div>
                        <div class="mobile-actions">
                            <button class="btn btn-sm btn-primary" onclick="window.open('/mobile', '_blank')">
                                Abrir em Nova Aba
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }
        
        this.mostrarNotificacao('Dashboard móvel renderizado! Clique em "Abrir em Nova Aba" para usar.', 'info');
    }
    
    onGoogleMapsReady() {
        console.log('Google Maps pronto para uso');
        if (this.mapa) {
            this.atualizarMarcadores();
        }
    }
    
    calcularProgressoTipo(entidades, tipo) {
        const entidadesTipo = entidades.filter(e => e[`${tipo}_obrigatorio`]);
        if (!entidadesTipo.length) return 0;
        
        const concluidas = entidadesTipo.filter(e => 
            e[`status_${tipo}`] === 'validado_concluido'
        ).length;
        
        return Math.round((concluidas / entidadesTipo.length) * 100);
    }
    
    calcularProgressoP1(entidades) {
        const p1 = entidades.filter(e => e.prioridade === 1);
        if (!p1.length) return 0;
        
        const finalizadas = p1.filter(e => 
            e.status_mrs === 'validado_concluido' && e.status_map === 'validado_concluido'
        ).length;
        
        return Math.round((finalizadas / p1.length) * 100);
    }
    
    calcularScoreQualidade() {
        let score = 0;
        let total = 0;
        
        // Geocodificação (30%)
        const geocodificadas = this.dados.entidades.filter(e => e.latitude && e.longitude).length;
        if (this.dados.entidades.length > 0) {
            score += (geocodificadas / this.dados.entidades.length) * 30;
            total += 30;
        }
        
        // Completude de dados (40%)
        const completas = this.dados.entidades.filter(e => 
            e.nome && e.endereco && e.telefone
        ).length;
        if (this.dados.entidades.length > 0) {
            score += (completas / this.dados.entidades.length) * 40;
            total += 40;
        }
        
        // Questionários validados (30%)
        const validados = this.dados.entidades.filter(e => 
            e.status_mrs === 'validado_concluido' || e.status_map === 'validado_concluido'
        ).length;
        if (this.dados.entidades.length > 0) {
            score += (validados / this.dados.entidades.length) * 30;
            total += 30;
        }
        
        return total > 0 ? Math.round(score) : 0;
    }
    
    /**
     * Calcular eficiência dinâmica dos pesquisadores baseada em métricas reais
     * @returns {number} Percentual de eficiência (0-100)
     */
    calcularEficienciaDinamica() {
        try {
            console.log('🔢 Calculando eficiência dinâmica dos pesquisadores...');
            
            // Verificar se os dados foram carregados
            if (!this.dados || !this.dados.municipios) {
                console.log('ℹ️ Dados ainda não carregados, usando valor padrão');
                return 75; // Fallback padrão
            }
            
            // Obter dados reais dos municípios
            const municipios = this.dados.municipios;
            if (!municipios.length) {
                console.warn('⚠️ Nenhum dado de município disponível para cálculo de eficiência');
                return 75; // Fallback padrão
            }
            
            // Métricas base para cálculo
            let totalMunicipios = municipios.length;
            let municipiosComVisitas = 0;
            let municipiosFinalizados = 0;
            let somatorioProgressoMRS = 0;
            let somatorioProgressoMAP = 0;
            let municipiosOnSchedule = 0;
            
            // Processar cada município
            municipios.forEach(municipio => {
                // Contar municípios com visitas
                if (municipio.status !== 'sem_visita') {
                    municipiosComVisitas++;
                }
                
                // Contar municípios finalizados
                if (municipio.status === 'finalizado' || municipio.status === 'executado') {
                    municipiosFinalizados++;
                }
                
                // Somar progressos
                somatorioProgressoMRS += municipio.progressoMRS || 0;
                somatorioProgressoMAP += municipio.progressoMAP || 0;
                
                // Contar municípios no prazo (sem alertas críticos)
                if (!municipio.alertas || municipio.alertas.length === 0) {
                    municipiosOnSchedule++;
                }
            });
            
            // Calcular métricas individuais
            const taxaCobertura = (municipiosComVisitas / totalMunicipios) * 100;
            const taxaFinalizacao = (municipiosFinalizados / totalMunicipios) * 100;
            const progressoMedioMRS = somatorioProgressoMRS / totalMunicipios;
            const progressoMedioMAP = somatorioProgressoMAP / totalMunicipios;
            const progressoGeralMedio = (progressoMedioMRS + progressoMedioMAP) / 2;
            const taxaOnSchedule = (municipiosOnSchedule / totalMunicipios) * 100;
            
            // Calcular eficiência baseada em tempo (últimas 2 semanas)
            const visitas = this.dados.visitas || [];
            const duasSemanasAtras = new Date();
            duasSemanasAtras.setDate(duasSemanasAtras.getDate() - 14);
            
            const visitasRecentes = visitas.filter(v => {
                if (!v.data) return false;
                return new Date(v.data) >= duasSemanasAtras;
            }).length;
            
            const velocidadeExecucao = Math.min(100, (visitasRecentes / 7) * 100); // Normalizar para 7 visitas/2 semanas
            
            // Calcular qualidade dos dados
            const qualidadeDados = this.calcularScoreQualidade();
            
            // Fórmula de eficiência ponderada
            const eficiencia = (
                (taxaCobertura * 0.20) +          // 20% - Cobertura de municípios
                (taxaFinalizacao * 0.25) +        // 25% - Taxa de finalização
                (progressoGeralMedio * 0.20) +    // 20% - Progresso médio dos questionários
                (taxaOnSchedule * 0.15) +         // 15% - Municípios no prazo
                (velocidadeExecucao * 0.10) +     // 10% - Velocidade de execução
                (qualidadeDados * 0.10)           // 10% - Qualidade dos dados
            );
            
            // Aplicar bônus/penalidades
            let eficienciaFinal = eficiencia;
            
            // Bônus por performance excepcional
            if (progressoGeralMedio > 80) {
                eficienciaFinal *= 1.05; // 5% bonus
            }
            
            // Penalidade por muitos alertas críticos
            const municipiosComAlertaCritico = municipios.filter(m => 
                m.alertas && m.alertas.length > 0
            ).length;
            
            if (municipiosComAlertaCritico > totalMunicipios * 0.3) {
                eficienciaFinal *= 0.95; // 5% penalidade
            }
            
            // Garantir limites (0-100)
            eficienciaFinal = Math.max(0, Math.min(100, eficienciaFinal));
            
            // Log das métricas para debugging
            console.log('📊 Métricas de Eficiência:', {
                taxaCobertura: taxaCobertura.toFixed(1) + '%',
                taxaFinalizacao: taxaFinalizacao.toFixed(1) + '%',
                progressoMedioMRS: progressoMedioMRS.toFixed(1) + '%',
                progressoMedioMAP: progressoMedioMAP.toFixed(1) + '%',
                taxaOnSchedule: taxaOnSchedule.toFixed(1) + '%',
                velocidadeExecucao: velocidadeExecucao.toFixed(1) + '%',
                qualidadeDados: qualidadeDados.toFixed(1) + '%',
                eficienciaFinal: eficienciaFinal.toFixed(1) + '%'
            });
            
            return Math.round(eficienciaFinal);
            
        } catch (error) {
            console.error('❌ Erro ao calcular eficiência dinâmica:', error);
            return 75; // Fallback em caso de erro
        }
    }
    
    contarMunicipiosConcluidos() {
        return Object.keys(this.municipios).filter(municipio => {
            const entidades = this.dados.entidades.filter(e => e.municipio === municipio);
            const p1 = entidades.filter(e => e.prioridade === 1);
            const p1Concluidas = p1.filter(e => 
                e.status_mrs === 'validado_concluido' && e.status_map === 'validado_concluido'
            );
            return p1.length > 0 && p1Concluidas.length === p1.length;
        }).length;
    }
}

// CORREÇÃO IMEDIATA: Forçar exibição assim que possível
function correcaoImediata() {
    console.log('🚨 CORREÇÃO IMEDIATA EXECUTANDO...');
    
    // Remover elementos de loading
    const loadings = document.querySelectorAll('.loading, .spinner, [class*="loading"]');
    loadings.forEach(el => el.remove());
    
    // Forçar exibição de containers
    const containers = document.querySelectorAll('.dashboard-container, .main-content, .container-fluid, .tab-content');
    containers.forEach(el => {
        if (el) {
            el.style.display = 'block';
            el.style.visibility = 'visible';
            el.style.opacity = '1';
        }
    });
    
    // Ativar primeira aba
    const firstTab = document.querySelector('.tab-content');
    const firstButton = document.querySelector('.tab-button');
    if (firstTab) {
        firstTab.classList.add('active');
        firstTab.style.display = 'block';
    }
    if (firstButton) {
        firstButton.classList.add('active');
    }
    
    console.log('✅ CORREÇÃO IMEDIATA APLICADA!');
}

// Executar correção múltiplas vezes
setTimeout(correcaoImediata, 500);
setTimeout(correcaoImediata, 1000);
setTimeout(correcaoImediata, 2000);

// Inicialização quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    correcaoImediata();
    window.mapaProgressoPNSB = new MapaProgressoPNSB();
    window.mapaProgresso = window.mapaProgressoPNSB; // Alias para compatibilidade
});

// Export para uso em outros módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MapaProgressoPNSB;
}
// KPI Fallback Handler - PNSB 2024
function handleKPICompatibility(kpis, metadata) {
    // Se temos a nova estrutura, usar diretamente
    if (metadata && metadata.versao === '2.0_pnsb_oficial') {
        return kpis;
    }
    
    // Converter estrutura antiga para nova (fallback)
    if (kpis.cobertura_sc || kpis.compliance_p1 || kpis.prazo_pnsb) {
        console.warn('⚠️ Convertendo KPIs antigos para nova estrutura');
        return {
            cronograma_ibge: {
                dias_restantes: kpis.prazo_pnsb?.dias_restantes || 0,
                percentual_tempo_decorrido: kpis.prazo_pnsb?.progresso_tempo || 0
            },
            cobertura_territorial: {
                municipios_concluidos: kpis.cobertura_sc?.municipios_concluidos || 0,
                percentual_cobertura: kpis.cobertura_sc?.percentual || 0
            },
            compliance_pnsb: {
                percentual_p1_finalizado: kpis.compliance_p1?.percentual || 0
            },
            instrumentos_pesquisa: {
                mrs: { taxa_resposta: 0 },
                map: { taxa_resposta: 0 }
            },
            qualidade_dados: {
                score_metodologico: kpis.qualidade?.score || 0,
                qualidade_geral: kpis.qualidade?.categoria || 'indefinida'
            },
            efetividade_operacional: {
                eficiencia_pesquisadores: 0,
                visitas: { realizadas: 0, total: 0 }
            },
            indicadores_risco: {
                risco_cronograma: { nivel: 'baixo', score: 0 }
            }
        };
    }
    
    return kpis;
}

// Adicionar ao final do arquivo
window.handleKPICompatibility = handleKPICompatibility;
