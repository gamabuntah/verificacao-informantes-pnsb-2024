/**
 * CHARTS E ANALYTICS - MAPA DE PROGRESSO PNSB 2024
 * Implementação dos gráficos e análises para o dashboard
 */

class ChartsAnalytics {
    constructor(mapaProgresso) {
        this.mapaProgresso = mapaProgresso;
        this.charts = {};
        this.cores = {
            primary: '#2E86AB',
            secondary: '#A23B72', 
            success: '#F18F01',
            warning: '#C73E1D',
            info: '#6c757d',
            mrs: ['#FF6B6B', '#FF8E53'],
            map: ['#4ECDC4', '#44A08D'],
            p1: ['#2E86AB', '#A23B72']
        };
    }

    /**
     * Criar gráfico de progresso por município
     */
    criarChartProgressoMunicipios() {
        const canvas = document.getElementById('chart-progresso-municipios');
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');
        const municipios = this.obterDadosProcessados();
        
        const dados = {
            labels: municipios.map(m => m.nome),
            datasets: [
                {
                    label: 'MRS (%)',
                    data: municipios.map(m => m.progressoMRS),
                    backgroundColor: this.criarGradiente(ctx, this.cores.mrs),
                    borderColor: this.cores.mrs[0],
                    borderWidth: 2
                },
                {
                    label: 'MAP (%)',
                    data: municipios.map(m => m.progressoMAP),
                    backgroundColor: this.criarGradiente(ctx, this.cores.map),
                    borderColor: this.cores.map[0],
                    borderWidth: 2
                }
            ]
        };

        return new Chart(ctx, {
            type: 'bar',
            data: dados,
            options: {
                responsive: false,
                maintainAspectRatio: false,
                resizeDelay: 0,
                plugins: {
                    title: {
                        display: true,
                        text: 'Progresso de Coleta por Município'
                    },
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            afterBody: function(context) {
                                const municipio = municipios[context[0].dataIndex];
                                return `P1 Contactadas: ${municipio.p1Contactadas}/${municipio.totalP1}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 45,
                            minRotation: 0
                        }
                    }
                },
                animation: {
                    duration: 1500,
                    easing: 'easeInOutQuart'
                }
            }
        });
    }

    /**
     * Criar gráfico de distribuição de status
     */
    criarChartDistribuicaoStatus() {
        const canvas = document.getElementById('chart-distribuicao-status');
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');
        
        // Usar dados processados dos municípios
        const municipios = this.obterDadosProcessados();
        
        // Contar municípios por status
        const statusCount = {
            'sem_visita': 0,
            'agendado': 0,
            'em_followup': 0,
            'executado': 0,
            'finalizado': 0
        };

        municipios.forEach(m => {
            if (statusCount.hasOwnProperty(m.status)) {
                statusCount[m.status]++;
            }
        });
        
        // Se temos dados de entidades, também processar
        const entidades = this.mapaProgresso.dados.entidades || [];
        const entidadeStatusCount = {
            'nao_iniciado': 0,
            'respondido': 0,
            'validado_concluido': 0,
            'nao_aplicavel': 0
        };

        entidades.forEach(e => {
            if (e.status_mrs) entidadeStatusCount[e.status_mrs] = (entidadeStatusCount[e.status_mrs] || 0) + 1;
            if (e.status_map) entidadeStatusCount[e.status_map] = (entidadeStatusCount[e.status_map] || 0) + 1;
        });

        // Definir dados baseado no que temos disponível
        const usarDadosMunicipios = Object.values(statusCount).some(v => v > 0);
        
        const dados = usarDadosMunicipios ? {
            labels: ['Sem Visita', 'Agendado', 'Em Follow-up', 'Executado', 'Finalizado'],
            datasets: [{
                data: [
                    statusCount.sem_visita,
                    statusCount.agendado,
                    statusCount.em_followup,
                    statusCount.executado,
                    statusCount.finalizado
                ],
                backgroundColor: [
                    '#dc3545', // Sem visita - vermelho
                    '#6c757d', // Agendado - cinza
                    '#ffc107', // Em follow-up - amarelo
                    '#17a2b8', // Executado - azul
                    '#28a745'  // Finalizado - verde
                ],
                borderWidth: 0,
                hoverOffset: 4
            }]
        } : {
            labels: ['Não Iniciado', 'Respondido', 'Validado/Concluído', 'Não Aplicável'],
            datasets: [{
                data: [
                    entidadeStatusCount.nao_iniciado,
                    entidadeStatusCount.respondido,
                    entidadeStatusCount.validado_concluido,
                    entidadeStatusCount.nao_aplicavel
                ],
                backgroundColor: [
                    '#dc3545', // Não iniciado - vermelho
                    '#ffc107', // Respondido - amarelo
                    '#28a745', // Validado - verde
                    '#6c757d'  // Não aplicável - cinza
                ],
                borderWidth: 0,
                hoverOffset: 4
            }]
        };

        return new Chart(ctx, {
            type: 'doughnut',
            data: dados,
            options: {
                responsive: false,
                maintainAspectRatio: false,
                resizeDelay: 0,
                plugins: {
                    title: {
                        display: true,
                        text: usarDadosMunicipios ? 'Distribuição de Status dos Municípios' : 'Distribuição de Status das Entidades'
                    },
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    duration: 2000
                }
            }
        });
    }

    /**
     * Criar gráfico de timeline de visitas
     */
    criarChartTimelineVisitas() {
        const canvas = document.getElementById('chart-timeline-visitas');
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');
        const visitas = this.mapaProgresso.dados.visitas;
        
        // Agrupar visitas por semana
        const visitasPorSemana = this.agruparVisitasPorPeriodo(visitas, 'semana');
        
        const dados = {
            labels: visitasPorSemana.labels,
            datasets: [{
                label: 'Visitas Realizadas',
                data: visitasPorSemana.dados,
                fill: true,
                backgroundColor: this.criarGradiente(ctx, [this.cores.primary, this.cores.secondary], true),
                borderColor: this.cores.primary,
                borderWidth: 3,
                tension: 0.4,
                pointBackgroundColor: this.cores.primary,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5
            }]
        };

        return new Chart(ctx, {
            type: 'line',
            data: dados,
            options: {
                responsive: false,
                maintainAspectRatio: false,
                resizeDelay: 0,
                plugins: {
                    title: {
                        display: true,
                        text: 'Timeline de Visitas por Semana'
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                elements: {
                    point: {
                        hoverRadius: 8
                    }
                },
                animation: {
                    duration: 2000,
                    easing: 'easeInOutCubic'
                }
            }
        });
    }

    /**
     * Criar gráfico de qualidade dos dados
     */
    criarChartQualidadeDados() {
        const canvas = document.getElementById('chart-qualidade-dados');
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');
        const qualidade = this.calcularMetricasQualidade();
        
        const dados = {
            labels: ['Geocodificação', 'Completude', 'Validação', 'Atualização'],
            datasets: [{
                label: 'Score de Qualidade',
                data: [
                    qualidade.geocodificacao,
                    qualidade.completude,
                    qualidade.validacao,
                    qualidade.atualizacao
                ],
                backgroundColor: this.cores.primary + '20',
                borderColor: this.cores.primary,
                borderWidth: 3,
                pointBackgroundColor: this.cores.primary,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                fill: true
            }]
        };

        return new Chart(ctx, {
            type: 'radar',
            data: dados,
            options: {
                responsive: false,
                maintainAspectRatio: false,
                resizeDelay: 0,
                plugins: {
                    title: {
                        display: true,
                        text: 'Radar de Qualidade dos Dados'
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                },
                animation: {
                    duration: 1500,
                    easing: 'easeInOutBack'
                }
            }
        });
    }

    /**
     * Criar gráfico de eficácia por canal de comunicação
     */

    /**
     * Atualizar todos os gráficos com dados reais
     */
    atualizarTodosCharts() {
        // Implementar throttling seguro para evitar atualizações excessivas
        if (this._updateThrottle) {
            clearTimeout(this._updateThrottle);
        }
        
        this._updateThrottle = setTimeout(() => {
            console.log('📊 Atualizando todos os gráficos com dados reais...');
            
            // Destruir gráficos existentes antes de recriar
            this.destruirCharts();
            
            // Recriar gráficos com dados atualizados
            this.inicializarTodosCharts();
            
            console.log('✅ Gráficos atualizados com sucesso');
        }, 500); // Throttle de 500ms para evitar múltiplas atualizações
    }

    /**
     * Destruir todos os gráficos
     */
    destruirCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts = {};
    }
    
    /**
     * Inicializar todos os gráficos
     */
    inicializarTodosCharts() {
        console.log('📊 Inicializando todos os gráficos...');
        
        // Limpar gráficos existentes
        this.destruirCharts();
        
        // Criar novos gráficos
        this.charts.progressoMunicipios = this.criarChartProgressoMunicipios();
        this.charts.distribuicaoStatus = this.criarChartDistribuicaoStatus();
        this.charts.timelineVisitas = this.criarChartTimelineVisitas();
        this.charts.qualidadeDados = this.criarChartQualidadeDados();
        
        // Forçar dimensões fixas em todos os gráficos
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.canvas) {
                chart.canvas.style.width = '400px';
                chart.canvas.style.height = '280px';
                chart.canvas.style.maxWidth = '400px';
                chart.canvas.style.maxHeight = '280px';
                chart.canvas.width = 400;
                chart.canvas.height = 280;
            }
        });
        
        console.log('✅ Todos os gráficos inicializados com sucesso');
    }
    
    /**
     * Atualizar gráficos com dados filtrados
     */
    atualizarComFiltros(dadosFiltrados) {
        console.log('📊 Atualizando gráficos com dados filtrados...');
        
        // Salvar dados filtrados temporariamente
        this.dadosFiltrados = dadosFiltrados;
        
        // Recriar gráficos com dados filtrados
        this.destruirCharts();
        this.inicializarTodosCharts();
        
        // Restaurar dados originais
        this.dadosFiltrados = null;
        
        console.log('✅ Gráficos atualizados com filtros');
    }
    
    /**
     * Obter dados processados (considerando filtros se aplicado)
     */
    obterDadosProcessados() {
        if (this.dadosFiltrados) {
            // Converter dados filtrados para formato esperado
            return Object.entries(this.dadosFiltrados).map(([municipio, dados]) => ({
                nome: municipio,
                status: dados.status || 'sem_visita',
                progressoMRS: dados.questionarios?.percentual_mrs || 0,
                progressoMAP: dados.questionarios?.percentual_map || 0,
                progressoP1: dados.resumo?.percentual_conclusao || 0,
                totalP1: dados.questionarios?.total_mrs_obrigatorios + dados.questionarios?.total_map_obrigatorios || 0,
                p1Contactadas: dados.questionarios?.mrs_validados + dados.questionarios?.map_validados || 0,
                geocodificacao: dados.resumo?.percentual_conclusao || 0,
                ultimaAtividade: dados.timing?.ultima_atividade || 'Nenhuma',
                alertas: dados.alertas || []
            }));
        }
        
        // Usar dados completos se não há filtros
        return this.mapaProgresso.processarDadosMunicipios();
    }

    /**
     * Criar gradiente para gráficos
     */
    criarGradiente(ctx, cores, vertical = false) {
        const gradient = vertical ? 
            ctx.createLinearGradient(0, 0, 0, 400) :
            ctx.createLinearGradient(0, 0, 400, 0);
        
        gradient.addColorStop(0, cores[0]);
        gradient.addColorStop(1, cores[1]);
        
        return gradient;
    }

    /**
     * Agrupar visitas por período
     */
    agruparVisitasPorPeriodo(visitas, periodo = 'semana') {
        const agrupamento = new Map();
        const hoje = new Date();
        
        // Criar últimas 12 semanas
        for (let i = 11; i >= 0; i--) {
            const data = new Date(hoje);
            data.setDate(data.getDate() - (i * 7));
            const semana = this.obterSemana(data);
            agrupamento.set(semana, 0);
        }
        
        // Contar visitas por semana
        visitas.forEach(visita => {
            if (visita.data) {
                const dataVisita = new Date(visita.data);
                const semana = this.obterSemana(dataVisita);
                if (agrupamento.has(semana)) {
                    agrupamento.set(semana, agrupamento.get(semana) + 1);
                }
            }
        });
        
        return {
            labels: Array.from(agrupamento.keys()),
            dados: Array.from(agrupamento.values())
        };
    }

    /**
     * Obter identificador da semana
     */
    obterSemana(data) {
        const inicioSemana = new Date(data);
        inicioSemana.setDate(data.getDate() - data.getDay());
        return inicioSemana.toLocaleDateString('pt-BR', { 
            day: '2-digit', 
            month: '2-digit' 
        });
    }

    /**
     * Calcular métricas de qualidade
     */
    calcularMetricasQualidade() {
        const entidades = this.mapaProgresso.dados.entidades || [];
        const municipios = this.mapaProgresso.processarDadosMunicipios();
        
        // Se não temos dados de entidades, usar dados dos municípios
        if (!entidades.length && municipios.length > 0) {
            // Calcular métricas baseadas nos municípios
            const totalMunicipios = municipios.length;
            const comVisitas = municipios.filter(m => m.status !== 'sem_visita').length;
            const emFollowup = municipios.filter(m => m.status === 'em_followup' || m.status === 'executado').length;
            const finalizados = municipios.filter(m => m.status === 'finalizado').length;
            
            // Calcular médias de progresso
            const mediaProgressoMRS = municipios.reduce((sum, m) => sum + m.progressoMRS, 0) / totalMunicipios;
            const mediaProgressoMAP = municipios.reduce((sum, m) => sum + m.progressoMAP, 0) / totalMunicipios;
            const mediaProgressoGeral = (mediaProgressoMRS + mediaProgressoMAP) / 2;
            
            return {
                geocodificacao: Math.round((comVisitas / totalMunicipios) * 100),
                completude: Math.round(mediaProgressoGeral),
                validacao: Math.round((finalizados / totalMunicipios) * 100),
                atualizacao: Math.round((emFollowup / totalMunicipios) * 100)
            };
        }
        
        if (!entidades.length) {
            return {
                geocodificacao: 0,
                completude: 0,
                validacao: 0,
                atualizacao: 0
            };
        }
        
        // Geocodificação
        const geocodificadas = entidades.filter(e => e.latitude && e.longitude).length;
        const geocodificacao = (geocodificadas / entidades.length) * 100;
        
        // Completude dos dados
        const completas = entidades.filter(e => 
            e.nome_entidade && e.endereco && e.telefone
        ).length;
        const completude = (completas / entidades.length) * 100;
        
        // Validação
        const validadas = entidades.filter(e => 
            e.status_mrs === 'validado_concluido' || 
            e.status_map === 'validado_concluido'
        ).length;
        const validacao = (validadas / entidades.length) * 100;
        
        // Atualização (baseado em data de modificação)
        const hoje = new Date();
        const atualizadasRecente = entidades.filter(e => {
            if (!e.data_atualizacao) return false;
            const dataAtualizacao = new Date(e.data_atualizacao);
            const diasAtraso = (hoje - dataAtualizacao) / (1000 * 60 * 60 * 24);
            return diasAtraso <= 30; // Atualizadas nos últimos 30 dias
        }).length;
        const atualizacao = (atualizadasRecente / entidades.length) * 100;
        
        return {
            geocodificacao: Math.round(geocodificacao),
            completude: Math.round(completude),
            validacao: Math.round(validacao),
            atualizacao: Math.round(atualizacao)
        };
    }

    /**
     * Gerar insights automáticos baseados nos dados
     */
    gerarInsights() {
        const insights = [];
        const municipios = this.mapaProgresso.processarDadosMunicipios();
        const qualidade = this.calcularMetricasQualidade();
        
        // Insight 1: Município com melhor performance
        const melhorMunicipio = municipios.reduce((melhor, atual) => 
            atual.progressoP1 > melhor.progressoP1 ? atual : melhor
        );
        
        insights.push({
            tipo: 'sucesso',
            titulo: 'Melhor Performance',
            descricao: `${melhorMunicipio.nome} lidera com ${melhorMunicipio.progressoP1}% de P1 finalizadas`,
            acao: 'replicar_estrategia'
        });
        
        // Insight 2: Oportunidade de melhoria
        const piorMunicipio = municipios.reduce((pior, atual) => 
            atual.progressoP1 < pior.progressoP1 ? atual : pior
        );
        
        insights.push({
            tipo: 'oportunidade',
            titulo: 'Oportunidade de Melhoria',
            descricao: `${piorMunicipio.nome} precisa de atenção: apenas ${piorMunicipio.progressoP1}% de P1 finalizadas`,
            acao: 'priorizar_municipio'
        });
        
        // Insight 3: Qualidade dos dados
        if (qualidade.geocodificacao > 90) {
            insights.push({
                tipo: 'info',
                titulo: 'Geocodificação Excelente',
                descricao: `${qualidade.geocodificacao}% das entidades estão geocodificadas`,
                acao: null
            });
        }
        
        // Insight 4: Tendência temporal
        const visitas = this.mapaProgresso.dados.visitas;
        const visitasUltimaSemana = visitas.filter(v => {
            if (!v.data) return false;
            const dataVisita = new Date(v.data);
            const hoje = new Date();
            const diasAtraso = (hoje - dataVisita) / (1000 * 60 * 60 * 24);
            return diasAtraso <= 7;
        }).length;
        
        if (visitasUltimaSemana >= 5) {
            insights.push({
                tipo: 'tendencia',
                titulo: 'Ritmo Acelerado',
                descricao: `${visitasUltimaSemana} visitas na última semana - mantendo bom ritmo`,
                acao: 'manter_ritmo'
            });
        }
        
        return insights;
    }
}

// Export para uso global
if (typeof window !== 'undefined') {
    window.ChartsAnalytics = ChartsAnalytics;
}