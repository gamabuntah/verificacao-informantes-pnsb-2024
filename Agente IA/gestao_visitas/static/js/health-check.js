// Health Check - Sistema PNSB 2024
// Monitora a saúde do sistema e reporta problemas

class HealthMonitor {
    constructor() {
        this.checks = [];
        this.interval = null;
        this.isRunning = false;
        
        this.init();
    }
    
    init() {
        this.setupChecks();
        this.startMonitoring();
    }
    
    setupChecks() {
        this.checks = [
            {
                name: 'PWA Manager',
                check: () => window.pwaManager !== undefined,
                critical: false
            },
            {
                name: 'Service Worker',
                check: () => 'serviceWorker' in navigator,
                critical: false
            },
            {
                name: 'Local Storage',
                check: () => {
                    try {
                        localStorage.setItem('health-test', 'ok');
                        localStorage.removeItem('health-test');
                        return true;
                    } catch {
                        return false;
                    }
                },
                critical: true
            },
            {
                name: 'Session Storage',
                check: () => {
                    try {
                        sessionStorage.setItem('health-test', 'ok');
                        sessionStorage.removeItem('health-test');
                        return true;
                    } catch {
                        return false;
                    }
                },
                critical: true
            },
            {
                name: 'Network',
                check: () => navigator.onLine,
                critical: false
            },
            {
                name: 'JavaScript APIs',
                check: () => {
                    return window.fetch && 
                           window.JSON && 
                           window.Promise &&
                           window.EventTarget;
                },
                critical: true
            }
        ];
    }
    
    runHealthCheck() {
        const results = {
            timestamp: new Date().toISOString(),
            overall: 'healthy',
            checks: {},
            errors: [],
            warnings: []
        };
        
        let hasErrors = false;
        let hasWarnings = false;
        
        for (const check of this.checks) {
            try {
                const passed = check.check();
                results.checks[check.name] = {
                    status: passed ? 'pass' : 'fail',
                    critical: check.critical
                };
                
                if (!passed) {
                    const message = `${check.name} health check failed`;
                    if (check.critical) {
                        results.errors.push(message);
                        hasErrors = true;
                    } else {
                        results.warnings.push(message);
                        hasWarnings = true;
                    }
                }
            } catch (error) {
                results.checks[check.name] = {
                    status: 'error',
                    error: error.message,
                    critical: check.critical
                };
                
                const message = `${check.name} health check error: ${error.message}`;
                if (check.critical) {
                    results.errors.push(message);
                    hasErrors = true;
                } else {
                    results.warnings.push(message);
                    hasWarnings = true;
                }
            }
        }
        
        if (hasErrors) {
            results.overall = 'unhealthy';
        } else if (hasWarnings) {
            results.overall = 'degraded';
        }
        
        return results;
    }
    
    startMonitoring() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        
        // Check inicial
        this.checkHealth();
        
        // Verificar a cada 30 segundos
        this.interval = setInterval(() => {
            this.checkHealth();
        }, 30000);
        
        console.log('Health monitoring started');
    }
    
    stopMonitoring() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
        this.isRunning = false;
        console.log('Health monitoring stopped');
    }
    
    checkHealth() {
        const results = this.runHealthCheck();
        
        // Log apenas se houver problemas
        if (results.overall !== 'healthy') {
            console.warn('System Health Check:', results);
            
            // Reportar problemas críticos
            if (results.errors.length > 0) {
                this.reportCriticalIssues(results.errors);
            }
        }
        
        // Salvar último resultado
        this.lastResults = results;
        
        // Disparar evento customizado
        window.dispatchEvent(new CustomEvent('healthcheck', {
            detail: results
        }));
        
        return results;
    }
    
    reportCriticalIssues(errors) {
        // Mostrar notificação discreta sobre problemas críticos
        if (typeof showToast === 'function') {
            showToast('Sistema com problemas detectados. Verifique o console.', 'warning');
        }
        
        console.error('CRITICAL SYSTEM ISSUES:', errors);
    }
    
    getLastResults() {
        return this.lastResults || { overall: 'unknown' };
    }
    
    getStatus() {
        const results = this.getLastResults();
        return {
            status: results.overall,
            lastCheck: results.timestamp,
            errors: results.errors?.length || 0,
            warnings: results.warnings?.length || 0
        };
    }
}

// Inicializar monitor de saúde
let healthMonitor;

document.addEventListener('DOMContentLoaded', () => {
    try {
        healthMonitor = new HealthMonitor();
        window.healthMonitor = healthMonitor;
        
        // Adicionar comando global para verificação manual
        window.checkSystemHealth = () => {
            return healthMonitor.checkHealth();
        };
        
        console.log('Health monitor initialized. Use checkSystemHealth() for manual check.');
    } catch (error) {
        console.error('Failed to initialize health monitor:', error);
    }
});