/**
 * Dashboard Preditivo PNSB 2024
 * Sistema de análise preditiva com IA para controle total do progresso
 */

class DashboardPreditivo {
    constructor() {
        this.dados = {};
        this.charts = {};
        this.alertasAtivos = [];
        this.intervalUpdate = null;
        this.init();
    }

    async init() {
        console.log('🔮 Inicializando Dashboard Preditivo PNSB 2024...');
        
        try {
            // Carregar dados iniciais
            await this.carregarDados();
            
            // Renderizar dashboard
            this.renderizarDashboard();
            
            // Configurar atualizações automáticas
            this.configurarAtualizacoes();
            
            console.log('✅ Dashboard Preditivo inicializado com sucesso!');
            
        } catch (error) {
            console.error('❌ Erro ao inicializar dashboard preditivo:', error);
            this.mostrarErro('Erro ao inicializar dashboard preditivo');
        }
    }

    async carregarDados() {
        console.log('📊 Carregando dados do dashboard preditivo...');
        
        try {
            // Carregar dashboard completo
            const response = await fetch('/api/dashboard-preditivo/completo');
            const result = await response.json();
            
            if (result.success) {
                this.dados = result.data;
                console.log('✅ Dados carregados:', this.dados);
            } else {
                throw new Error(result.error || 'Erro ao carregar dados');
            }
            
        } catch (error) {
            console.error('❌ Erro ao carregar dados:', error);
            throw error;
        }
    }

    renderizarDashboard() {
        console.log('🎨 Renderizando dashboard preditivo...');
        
        // Renderizar cada seção
        this.renderizarScoreSaude();
        this.renderizarAnalisePrazos();
        this.renderizarAlertasCriticos();
        this.renderizarProjecoes();
        this.renderizarRiscos();
        this.renderizarAnaliseVelocidade();
        this.renderizarMunicipios();
        this.renderizarRecomendacoes();
        
        // Inicializar gráficos
        this.inicializarGraficos();
    }

    renderizarScoreSaude() {
        const scoreElement = document.getElementById('score-saude-projeto');
        if (!scoreElement) return;

        const score = this.dados.score_saude;
        const progressoWidth = Math.min(score.score_final, 100);
        
        scoreElement.innerHTML = `
            <div class="score-saude-container">
                <div class="score-header">
                    <h3>Score de Saúde do Projeto</h3>
                    <div class="score-valor ${score.cor}">
                        ${score.score_final}%
                    </div>
                </div>
                
                <div class="score-progress">
                    <div class="progress-bar">
                        <div class="progress-fill ${score.cor}" style="width: ${progressoWidth}%"></div>
                    </div>
                    <div class="score-classificacao ${score.cor}">
                        ${score.classificacao}
                    </div>
                </div>
                
                <div class="score-componentes">
                    <div class="componente">
                        <span class="label">Velocidade:</span>
                        <span class="valor">${score.componentes.velocidade}%</span>
                    </div>
                    <div class="componente">
                        <span class="label">Riscos:</span>
                        <span class="valor">${score.componentes.riscos}%</span>
                    </div>
                    <div class="componente">
                        <span class="label">Alertas:</span>
                        <span class="valor">${score.componentes.alertas}%</span>
                    </div>
                    <div class="componente">
                        <span class="label">Progresso:</span>
                        <span class="valor">${score.componentes.progresso}%</span>
                    </div>
                </div>
                
                <div class="score-interpretacao">
                    <p>${score.interpretacao}</p>
                </div>
            </div>
        `;
    }

    renderizarAnalisePrazos() {
        const prazosElement = document.getElementById('analise-prazos');
        if (!prazosElement) return;

        const prazos = this.dados.analise_prazos;
        
        prazosElement.innerHTML = `
            <div class="analise-prazos-container">
                <h3>Análise de Prazos e Projeções</h3>
                
                <div class="prazos-grid">
                    <div class="prazo-card ${prazos.prazos.p1_p2.status}">
                        <div class="prazo-header">
                            <h4>Prazo P1/P2</h4>
                            <div class="prazo-data">${prazos.prazos.p1_p2.data}</div>
                        </div>
                        <div class="prazo-info">
                            <div class="dias-restantes">
                                <span class="numero">${prazos.prazos.p1_p2.dias_restantes}</span>
                                <span class="label">dias restantes</span>
                            </div>
                            <div class="progresso-atual">
                                <span class="numero">${prazos.prazos.p1_p2.progresso_atual}%</span>
                                <span class="label">progresso atual</span>
                            </div>
                        </div>
                        <div class="prazo-projecao">
                            <div class="status-icon ${prazos.prazos.p1_p2.status}">
                                ${prazos.prazos.p1_p2.projecao_cumprimento ? '✅' : '⚠️'}
                            </div>
                            <div class="projecao-info">
                                <div>Dias necessários: ${prazos.prazos.p1_p2.dias_necessarios}</div>
                                <div>Status: ${prazos.prazos.p1_p2.projecao_cumprimento ? 'No prazo' : 'Em risco'}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="prazo-card ${prazos.prazos.questionarios.status}">
                        <div class="prazo-header">
                            <h4>Questionários</h4>
                            <div class="prazo-data">${prazos.prazos.questionarios.data}</div>
                        </div>
                        <div class="prazo-info">
                            <div class="dias-restantes">
                                <span class="numero">${prazos.prazos.questionarios.dias_restantes}</span>
                                <span class="label">dias restantes</span>
                            </div>
                            <div class="progresso-atual">
                                <span class="numero">${prazos.prazos.questionarios.progresso_atual}%</span>
                                <span class="label">progresso atual</span>
                            </div>
                        </div>
                        <div class="prazo-projecao">
                            <div class="status-icon ${prazos.prazos.questionarios.status}">
                                ${prazos.prazos.questionarios.projecao_cumprimento ? '✅' : '⚠️'}
                            </div>
                            <div class="projecao-info">
                                <div>Dias necessários: ${prazos.prazos.questionarios.dias_necessarios}</div>
                                <div>Status: ${prazos.prazos.questionarios.projecao_cumprimento ? 'No prazo' : 'Em risco'}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="prazo-card ${prazos.prazos.final_pnsb.status}">
                        <div class="prazo-header">
                            <h4>Final PNSB</h4>
                            <div class="prazo-data">${prazos.prazos.final_pnsb.data}</div>
                        </div>
                        <div class="prazo-info">
                            <div class="dias-restantes">
                                <span class="numero">${prazos.prazos.final_pnsb.dias_restantes}</span>
                                <span class="label">dias restantes</span>
                            </div>
                            <div class="status-prazo">
                                <span class="status-badge ${prazos.prazos.final_pnsb.status}">
                                    ${prazos.prazos.final_pnsb.status}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="resumo-progresso">
                    <h4>Resumo do Progresso</h4>
                    <div class="progresso-barras">
                        <div class="barra-progresso">
                            <label>Visitas: ${prazos.progresso_geral.visitas}%</label>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${prazos.progresso_geral.visitas}%"></div>
                            </div>
                        </div>
                        <div class="barra-progresso">
                            <label>P1/P2: ${prazos.progresso_geral.p1_p2}%</label>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${prazos.progresso_geral.p1_p2}%"></div>
                            </div>
                        </div>
                        <div class="barra-progresso">
                            <label>Questionários: ${prazos.progresso_geral.questionarios}%</label>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${prazos.progresso_geral.questionarios}%"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderizarAlertasCriticos() {
        const alertasElement = document.getElementById('alertas-criticos');
        if (!alertasElement) return;

        const alertas = this.dados.alertas_criticos;
        this.alertasAtivos = alertas;
        
        if (alertas.length === 0) {
            alertasElement.innerHTML = `
                <div class="alertas-container">
                    <h3>Alertas Críticos</h3>
                    <div class="sem-alertas">
                        <div class="status-ok">✅</div>
                        <p>Nenhum alerta crítico no momento</p>
                    </div>
                </div>
            `;
            return;
        }

        const alertasHTML = alertas.map(alerta => `
            <div class="alerta-card ${alerta.nivel}">
                <div class="alerta-header">
                    <div class="alerta-nivel ${alerta.nivel}">
                        ${alerta.nivel.toUpperCase()}
                    </div>
                    <div class="alerta-tipo">${alerta.tipo}</div>
                </div>
                <div class="alerta-content">
                    <h4>${alerta.titulo}</h4>
                    <p class="alerta-mensagem">${alerta.mensagem}</p>
                    <div class="alerta-acao">
                        <strong>Ação necessária:</strong> ${alerta.acao_necessaria}
                    </div>
                </div>
                <div class="alerta-footer">
                    <span class="alerta-timestamp">${new Date(alerta.timestamp).toLocaleString()}</span>
                    <button class="btn-alerta-acao" onclick="dashboardPreditivo.executarAcaoAlerta('${alerta.id}')">
                        Ação
                    </button>
                </div>
            </div>
        `).join('');

        alertasElement.innerHTML = `
            <div class="alertas-container">
                <h3>Alertas Críticos (${alertas.length})</h3>
                <div class="alertas-lista">
                    ${alertasHTML}
                </div>
            </div>
        `;
    }

    renderizarProjecoes() {
        const projecoesElement = document.getElementById('projecoes-progresso');
        if (!projecoesElement) return;

        const projecoes = this.dados.projecoes_progresso;
        
        // Preparar dados para gráfico
        const historicoData = projecoes.historico_semanas.map(s => ({
            x: s.semana,
            y: s.visitas,
            label: `${s.inicio} - ${s.fim}`
        }));

        const projecaoData = projecoes.projecao_futuro.map((p, i) => ({
            x: i + 5,
            y: p.visitas_projetadas,
            label: p.semana
        }));

        projecoesElement.innerHTML = `
            <div class="projecoes-container">
                <h3>Projeções de Progresso</h3>
                
                <div class="tendencia-info">
                    <div class="tendencia-card">
                        <div class="tendencia-valor ${projecoes.tendencia.interpretacao}">
                            ${projecoes.tendencia.valor > 0 ? '+' : ''}${projecoes.tendencia.valor}
                        </div>
                        <div class="tendencia-label">
                            Tendência: ${projecoes.tendencia.interpretacao}
                        </div>
                    </div>
                    <div class="media-semanal">
                        <div class="media-valor">${projecoes.tendencia.visitas_por_semana_media}</div>
                        <div class="media-label">Visitas/semana (média)</div>
                    </div>
                </div>
                
                <div class="grafico-projecoes">
                    <canvas id="chart-projecoes-progresso"></canvas>
                </div>
                
                <div class="conclusao-prevista">
                    <h4>Previsão de Conclusão</h4>
                    <div class="conclusao-info">
                        <div class="conclusao-data">
                            <strong>Data prevista:</strong> ${projecoes.conclusao_prevista.data}
                        </div>
                        <div class="conclusao-semanas">
                            <strong>Semanas necessárias:</strong> ${projecoes.conclusao_prevista.semanas_necessarias}
                        </div>
                        <div class="conclusao-status ${projecoes.conclusao_prevista.dentro_do_prazo ? 'ok' : 'risco'}">
                            <strong>Status:</strong> ${projecoes.conclusao_prevista.dentro_do_prazo ? 'Dentro do prazo' : 'Fora do prazo'}
                        </div>
                    </div>
                </div>
                
                <div class="projecao-futuro">
                    <h4>Próximas 4 Semanas</h4>
                    <div class="semanas-futuras">
                        ${projecoes.projecao_futuro.map(p => `
                            <div class="semana-card">
                                <div class="semana-nome">${p.semana}</div>
                                <div class="semana-data">${p.data_inicio}</div>
                                <div class="semana-visitas">${p.visitas_projetadas} visitas</div>
                                <div class="semana-acumulado">Acumulado: ${p.acumulado_projetado}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    renderizarRiscos() {
        const riscosElement = document.getElementById('riscos-identificados');
        if (!riscosElement) return;

        const riscos = this.dados.riscos_identificados;
        
        if (riscos.length === 0) {
            riscosElement.innerHTML = `
                <div class="riscos-container">
                    <h3>Riscos Identificados</h3>
                    <div class="sem-riscos">
                        <div class="status-ok">✅</div>
                        <p>Nenhum risco identificado no momento</p>
                    </div>
                </div>
            `;
            return;
        }

        const riscosHTML = riscos.map(risco => `
            <div class="risco-card ${risco.nivel}">
                <div class="risco-header">
                    <div class="risco-nivel ${risco.nivel}">
                        ${risco.nivel.toUpperCase()}
                    </div>
                    <div class="risco-tipo">${risco.tipo}</div>
                    <div class="risco-probabilidade">${risco.probabilidade}%</div>
                </div>
                <div class="risco-content">
                    <h4>${risco.titulo}</h4>
                    <p class="risco-descricao">${risco.descricao}</p>
                    <div class="risco-impacto">
                        <strong>Impacto:</strong> ${risco.impacto}
                    </div>
                    <div class="risco-acao">
                        <strong>Ação recomendada:</strong> ${risco.acao_recomendada}
                    </div>
                </div>
                <div class="risco-footer">
                    <button class="btn-risco-mitigar" onclick="dashboardPreditivo.mitigarRisco('${risco.id}')">
                        Mitigar Risco
                    </button>
                </div>
            </div>
        `).join('');

        riscosElement.innerHTML = `
            <div class="riscos-container">
                <h3>Riscos Identificados (${riscos.length})</h3>
                <div class="riscos-lista">
                    ${riscosHTML}
                </div>
            </div>
        `;
    }

    renderizarAnaliseVelocidade() {
        const velocidadeElement = document.getElementById('analise-velocidade');
        if (!velocidadeElement) return;

        const velocidade = this.dados.velocidade_atual;
        
        velocidadeElement.innerHTML = `
            <div class="velocidade-container">
                <h3>Análise de Velocidade</h3>
                
                <div class="velocidade-principal">
                    <div class="velocidade-valor ${this.getVelocidadeClass(velocidade.geral)}">
                        ${velocidade.geral}%
                    </div>
                    <div class="velocidade-label">Por dia</div>
                    <div class="velocidade-interpretacao">
                        ${velocidade.interpretacao}
                    </div>
                </div>
                
                <div class="velocidade-detalhes">
                    <div class="velocidade-item">
                        <span class="label">Geral:</span>
                        <span class="valor">${velocidade.geral}%/dia</span>
                    </div>
                    <div class="velocidade-item">
                        <span class="label">P1/P2:</span>
                        <span class="valor">${velocidade.p1_p2}%/dia</span>
                    </div>
                    <div class="velocidade-item">
                        <span class="label">Questionários:</span>
                        <span class="valor">${velocidade.questionarios}%/dia</span>
                    </div>
                    <div class="velocidade-item">
                        <span class="label">Semanal:</span>
                        <span class="valor">${velocidade.semanal}%/sem</span>
                    </div>
                </div>
                
                <div class="velocidade-grafico">
                    <canvas id="chart-velocidade"></canvas>
                </div>
            </div>
        `;
    }

    renderizarMunicipios() {
        const municipiosElement = document.getElementById('analise-municipios');
        if (!municipiosElement) return;

        const municipios = this.dados.analise_municipios;
        
        const municipiosHTML = municipios.map(m => `
            <div class="municipio-card ${m.status}">
                <div class="municipio-header">
                    <h4>${m.municipio}</h4>
                    <div class="municipio-status ${m.status}">
                        ${m.status}
                    </div>
                </div>
                <div class="municipio-metricas">
                    <div class="metrica">
                        <span class="label">Visitas:</span>
                        <span class="valor">${m.metricas.visitas_concluidas}/${m.metricas.visitas_total}</span>
                    </div>
                    <div class="metrica">
                        <span class="label">Entidades:</span>
                        <span class="valor">${m.metricas.entidades_concluidas}/${m.metricas.total_entidades}</span>
                    </div>
                    <div class="metrica">
                        <span class="label">P1:</span>
                        <span class="valor">${m.metricas.entidades_p1}</span>
                    </div>
                    <div class="metrica">
                        <span class="label">Progresso:</span>
                        <span class="valor">${m.metricas.progresso_entidades}%</span>
                    </div>
                </div>
                <div class="municipio-progresso">
                    <div class="progress-bar">
                        <div class="progress-fill ${m.cor}" style="width: ${m.metricas.progresso_entidades}%"></div>
                    </div>
                </div>
                <div class="municipio-prioridade">
                    <span class="prioridade-label">Prioridade:</span>
                    <span class="prioridade-valor">${m.score_prioridade}</span>
                </div>
                <div class="municipio-acao">
                    <strong>Ação:</strong> ${m.acao_recomendada}
                </div>
            </div>
        `).join('');

        municipiosElement.innerHTML = `
            <div class="municipios-container">
                <h3>Análise por Município</h3>
                <div class="municipios-grid">
                    ${municipiosHTML}
                </div>
            </div>
        `;
    }

    renderizarRecomendacoes() {
        const recomendacoesElement = document.getElementById('recomendacoes-ia');
        if (!recomendacoesElement) return;

        const recomendacoes = this.dados.recomendacoes;
        
        const recomendacoesHTML = recomendacoes.map((rec, i) => `
            <div class="recomendacao-item">
                <div class="recomendacao-numero">${i + 1}</div>
                <div class="recomendacao-texto">${rec}</div>
            </div>
        `).join('');

        recomendacoesElement.innerHTML = `
            <div class="recomendacoes-container">
                <h3>Recomendações da IA</h3>
                <div class="recomendacoes-lista">
                    ${recomendacoesHTML}
                </div>
            </div>
        `;
    }

    inicializarGraficos() {
        // Gráfico de projeções
        this.criarGraficoProjecoes();
        
        // Gráfico de velocidade
        this.criarGraficoVelocidade();
        
        // Gráfico de municípios
        this.criarGraficoMunicipios();
    }

    criarGraficoProjecoes() {
        const ctx = document.getElementById('chart-projecoes-progresso');
        if (!ctx) return;

        const projecoes = this.dados.projecoes_progresso;
        
        // Combinar dados históricos e projeções
        const labels = [
            ...projecoes.historico_semanas.map(s => `Sem ${s.semana}`),
            ...projecoes.projecao_futuro.map(p => p.semana)
        ];
        
        const dadosReais = [
            ...projecoes.historico_semanas.map(s => s.visitas),
            ...new Array(projecoes.projecao_futuro.length).fill(null)
        ];
        
        const dadosProjetados = [
            ...new Array(projecoes.historico_semanas.length).fill(null),
            ...projecoes.projecao_futuro.map(p => p.visitas_projetadas)
        ];

        this.charts.projecoes = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Histórico',
                    data: dadosReais,
                    borderColor: '#2E86AB',
                    backgroundColor: 'rgba(46, 134, 171, 0.1)',
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'Projeção',
                    data: dadosProjetados,
                    borderColor: '#F18F01',
                    backgroundColor: 'rgba(241, 143, 1, 0.1)',
                    fill: true,
                    tension: 0.4,
                    borderDash: [5, 5]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Histórico e Projeção de Visitas'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Visitas'
                        }
                    }
                }
            }
        });
    }

    criarGraficoVelocidade() {
        const ctx = document.getElementById('chart-velocidade');
        if (!ctx) return;

        const velocidade = this.dados.velocidade_atual;
        
        this.charts.velocidade = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Geral', 'P1/P2', 'Questionários', 'Semanal'],
                datasets: [{
                    label: 'Velocidade Atual',
                    data: [velocidade.geral, velocidade.p1_p2, velocidade.questionarios, velocidade.semanal],
                    borderColor: '#2E86AB',
                    backgroundColor: 'rgba(46, 134, 171, 0.2)',
                    pointBackgroundColor: '#2E86AB',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#2E86AB'
                }, {
                    label: 'Meta Ideal',
                    data: [1.5, 1.5, 1.5, 10],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    pointBackgroundColor: '#28a745',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#28a745'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Análise de Velocidade'
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 2
                    }
                }
            }
        });
    }

    criarGraficoMunicipios() {
        const ctx = document.getElementById('chart-municipios-progresso');
        if (!ctx) return;

        const municipios = this.dados.analise_municipios;
        
        const labels = municipios.map(m => m.municipio);
        const dados = municipios.map(m => m.metricas.progresso_entidades);
        const cores = municipios.map(m => this.getCorPorStatus(m.status));

        this.charts.municipios = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Progresso (%)',
                    data: dados,
                    backgroundColor: cores,
                    borderColor: cores,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Progresso por Município'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Progresso (%)'
                        }
                    }
                }
            }
        });
    }

    // Métodos auxiliares
    getVelocidadeClass(velocidade) {
        if (velocidade >= 1.5) return 'excelente';
        if (velocidade >= 1.0) return 'boa';
        if (velocidade >= 0.5) return 'regular';
        return 'critica';
    }

    getCorPorStatus(status) {
        const cores = {
            'concluido': '#28a745',
            'andamento': '#ffc107',
            'iniciado': '#17a2b8',
            'pendente': '#dc3545'
        };
        return cores[status] || '#6c757d';
    }

    // Ações interativas
    async executarAcaoAlerta(alertaId) {
        const alerta = this.alertasAtivos.find(a => a.id === alertaId);
        if (!alerta) return;

        // Mostrar modal ou executar ação específica
        if (confirm(`Executar ação: ${alerta.acao_necessaria}?`)) {
            // Implementar ação específica
            console.log('Executando ação para alerta:', alertaId);
        }
    }

    async mitigarRisco(riscoId) {
        const risco = this.dados.riscos_identificados.find(r => r.id === riscoId);
        if (!risco) return;

        if (confirm(`Implementar mitigação: ${risco.acao_recomendada}?`)) {
            // Implementar mitigação
            console.log('Mitigando risco:', riscoId);
        }
    }

    // Atualizações automáticas
    configurarAtualizacoes() {
        // Atualizar a cada 5 minutos
        this.intervalUpdate = setInterval(() => {
            this.atualizarDados();
        }, 5 * 60 * 1000);
    }

    async atualizarDados() {
        try {
            await this.carregarDados();
            this.renderizarDashboard();
            console.log('✅ Dados atualizados automaticamente');
        } catch (error) {
            console.error('❌ Erro ao atualizar dados:', error);
        }
    }

    // Utilitários
    mostrarErro(mensagem) {
        // Implementar notificação de erro
        console.error(mensagem);
    }

    destruir() {
        if (this.intervalUpdate) {
            clearInterval(this.intervalUpdate);
        }
        
        // Destruir gráficos
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
    }
}

// Inicialização global
let dashboardPreditivo = null;

document.addEventListener('DOMContentLoaded', function() {
    // Verificar se estamos na página do dashboard preditivo
    if (document.getElementById('dashboard-preditivo')) {
        dashboardPreditivo = new DashboardPreditivo();
    }
});