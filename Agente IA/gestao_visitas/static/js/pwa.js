// PWA JavaScript - Sistema PNSB 2024
class PWAManager {
    constructor() {
        this.deferredPrompt = null;
        this.isInstalled = false;
        this.isOnline = navigator.onLine;
        this.swRegistration = null;
        
        this.init();
    }

    async init() {
        // 🔧 MODO DESENVOLVIMENTO - PWA desabilitado para evitar erros
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            console.log('🔧 PWA Manager: Modo desenvolvimento detectado - funcionalidades PWA desabilitadas');
            console.log('💡 Para produção, altere esta verificação em pwa.js');
            this.simulatePWAFeatures();
            return;
        }
        
        // Verificar se PWA já está instalada
        this.checkInstallStatus();
        
        // Registrar Service Worker
        await this.registerServiceWorker();
        
        // Configurar eventos PWA
        this.setupPWAEvents();
        
        // Configurar detecção de conectividade
        this.setupConnectivityDetection();
        
        // Configurar background sync
        this.setupBackgroundSync();
        
        // Configurar push notifications
        await this.setupPushNotifications();
        
        console.log('PWA Manager initialized successfully');
    }

    checkInstallStatus() {
        // Verificar se já está instalado
        if (window.matchMedia('(display-mode: standalone)').matches ||
            window.navigator.standalone === true) {
            this.isInstalled = true;
            console.log('PWA is installed and running in standalone mode');
        }
    }

    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                // Primeiro, tentar desregistrar service workers antigos
                const registrations = await navigator.serviceWorker.getRegistrations();
                for (const registration of registrations) {
                    if (registration.scope.includes('/static/') || 
                        registration.active?.scriptURL.includes('/static/sw.js')) {
                        console.log('Removing old service worker:', registration.scope);
                        await registration.unregister();
                    }
                }
                
                // Registrar o novo service worker com retry
                let attempts = 0;
                const maxAttempts = 3;
                
                while (attempts < maxAttempts) {
                    try {
                        this.swRegistration = await navigator.serviceWorker.register('/sw.js', {
                            scope: '/',
                            updateViaCache: 'none'  // Forçar atualização
                        });
                        
                        console.log('Service Worker registered successfully:', this.swRegistration);
                        break;
                        
                    } catch (registerError) {
                        attempts++;
                        console.warn(`Service Worker registration attempt ${attempts} failed:`, registerError);
                        
                        if (attempts >= maxAttempts) {
                            throw registerError;
                        }
                        
                        // Aguardar antes de tentar novamente
                        await new Promise(resolve => setTimeout(resolve, 1000));
                    }
                }
                
                // Escutar atualizações do Service Worker
                this.swRegistration.addEventListener('updatefound', () => {
                    this.handleServiceWorkerUpdate();
                });
                
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }
    }

    setupPWAEvents() {
        // Evento de instalação
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallBanner();
        });

        // Evento pós-instalação
        window.addEventListener('appinstalled', () => {
            this.isInstalled = true;
            this.hideInstallBanner();
            this.showToast('App instalado com sucesso!', 'success');
            
            // Analytics
            this.trackEvent('pwa_installed');
        });

        // Detectar mudança de orientação
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.adjustLayoutForOrientation();
            }, 100);
        });
    }

    setupConnectivityDetection() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.handleOnlineStatus();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.handleOfflineStatus();
        });
    }

    setupBackgroundSync() {
        if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
            console.log('Background Sync is supported');
            
            // Registrar sync quando voltar online
            window.addEventListener('online', () => {
                this.registerBackgroundSync('background-sync-visitas');
                this.registerBackgroundSync('background-sync-checklist');
            });
        }
    }

    async setupPushNotifications() {
        if ('Notification' in window && 'serviceWorker' in navigator) {
            // Verificar permissão existente
            if (Notification.permission === 'default') {
                // Mostrar prompt de permissão após 10 segundos
                setTimeout(() => {
                    this.requestNotificationPermission();
                }, 10000);
            }
        }
    }

    showInstallBanner() {
        // Verificar se já não está instalado
        if (this.isInstalled) return;

        const banner = document.createElement('div');
        banner.id = 'pwa-install-banner';
        banner.className = 'pwa-install-banner';
        banner.innerHTML = `
            <div class="banner-content">
                <div class="banner-info">
                    <i class="fas fa-mobile-alt"></i>
                    <div>
                        <h6>Instalar App PNSB</h6>
                        <p>Acesse rapidamente mesmo offline</p>
                    </div>
                </div>
                <div class="banner-actions">
                    <button class="btn btn-sm btn-outline-light" onclick="pwaManager.dismissInstallBanner()">
                        Agora não
                    </button>
                    <button class="btn btn-sm btn-primary" onclick="pwaManager.installApp()">
                        Instalar
                    </button>
                </div>
            </div>
        `;

        // Adicionar estilos
        if (!document.getElementById('pwa-styles')) {
            const styles = document.createElement('style');
            styles.id = 'pwa-styles';
            styles.textContent = `
                .pwa-install-banner {
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    background: linear-gradient(90deg, #5F5CFF 0%, #6EE7B7 100%);
                    color: white;
                    padding: 15px 20px;
                    box-shadow: 0 -2px 10px rgba(0,0,0,0.2);
                    z-index: 10000;
                    animation: slideUp 0.3s ease-out;
                }
                
                .banner-content {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    max-width: 1200px;
                    margin: 0 auto;
                }
                
                .banner-info {
                    display: flex;
                    align-items: center;
                    gap: 15px;
                }
                
                .banner-info i {
                    font-size: 24px;
                }
                
                .banner-info h6 {
                    margin: 0;
                    font-weight: 600;
                }
                
                .banner-info p {
                    margin: 0;
                    font-size: 12px;
                    opacity: 0.9;
                }
                
                .banner-actions {
                    display: flex;
                    gap: 10px;
                }
                
                @keyframes slideUp {
                    from { transform: translateY(100%); }
                    to { transform: translateY(0); }
                }
                
                .pwa-offline-indicator {
                    position: fixed;
                    top: 10px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: #dc3545;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-size: 12px;
                    z-index: 10001;
                    animation: fadeIn 0.3s ease-out;
                }
                
                .pwa-update-banner {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #28a745;
                    color: white;
                    padding: 12px 16px;
                    border-radius: 8px;
                    font-size: 14px;
                    z-index: 10001;
                    cursor: pointer;
                    animation: fadeIn 0.3s ease-out;
                }
                
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(-10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                
                @media (max-width: 768px) {
                    .banner-content {
                        flex-direction: column;
                        gap: 10px;
                        text-align: center;
                    }
                    
                    .banner-actions {
                        justify-content: center;
                    }
                }
            `;
            document.head.appendChild(styles);
        }

        document.body.appendChild(banner);
        
        // Auto-dismiss após 30 segundos
        setTimeout(() => {
            this.dismissInstallBanner();
        }, 30000);
    }

    async installApp() {
        if (this.deferredPrompt) {
            this.deferredPrompt.prompt();
            const { outcome } = await this.deferredPrompt.userChoice;
            
            if (outcome === 'accepted') {
                console.log('User accepted the install prompt');
                this.trackEvent('pwa_install_accepted');
            } else {
                console.log('User dismissed the install prompt');
                this.trackEvent('pwa_install_dismissed');
            }
            
            this.deferredPrompt = null;
            this.dismissInstallBanner();
        }
    }

    dismissInstallBanner() {
        const banner = document.getElementById('pwa-install-banner');
        if (banner) {
            banner.style.animation = 'slideDown 0.3s ease-out forwards';
            setTimeout(() => {
                banner.remove();
            }, 300);
        }
    }
    
    simulatePWAFeatures() {
        // Simular funcionalidades PWA para ambiente de desenvolvimento
        console.log('📱 PWA Features simuladas para desenvolvimento:');
        console.log('  ✅ Cache offline: Simulado');
        console.log('  ✅ Sincronização: Simulada');
        console.log('  ✅ Notificações: Simuladas');
        console.log('  ✅ Instalação: Simulada');
        
        // Simular status online/offline
        this.isOnline = true;
        
        // Configurar apenas detecção de conectividade (sem service worker)
        this.setupConnectivityDetection();
        
        console.log('🔧 Ambiente de desenvolvimento: Service Worker desabilitado');
    }

    hideInstallBanner() {
        this.dismissInstallBanner();
    }

    handleServiceWorkerUpdate() {
        const updateBanner = document.createElement('div');
        updateBanner.className = 'pwa-update-banner';
        updateBanner.innerHTML = `
            <i class="fas fa-download"></i>
            Nova versão disponível - Clique para atualizar
        `;
        
        updateBanner.addEventListener('click', () => {
            if (this.swRegistration && this.swRegistration.waiting) {
                this.swRegistration.waiting.postMessage({ type: 'SKIP_WAITING' });
                window.location.reload();
            }
        });
        
        document.body.appendChild(updateBanner);
    }

    handleOnlineStatus() {
        this.hideOfflineIndicator();
        this.showToast('Conexão restaurada', 'success');
        
        // Tentar sincronizar dados offline
        this.syncOfflineData();
    }

    handleOfflineStatus() {
        this.showOfflineIndicator();
        this.showToast('Você está offline - Algumas funcionalidades podem ser limitadas', 'warning');
    }

    showOfflineIndicator() {
        if (document.getElementById('pwa-offline-indicator')) return;
        
        const indicator = document.createElement('div');
        indicator.id = 'pwa-offline-indicator';
        indicator.className = 'pwa-offline-indicator';
        indicator.innerHTML = '<i class="fas fa-wifi"></i> Modo Offline';
        
        document.body.appendChild(indicator);
    }

    hideOfflineIndicator() {
        const indicator = document.getElementById('pwa-offline-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    async requestNotificationPermission() {
        try {
            const permission = await Notification.requestPermission();
            
            if (permission === 'granted') {
                this.showToast('Notificações ativadas com sucesso!', 'success');
                this.trackEvent('notifications_enabled');
                
                // Mostrar notificação de boas-vindas
                this.showWelcomeNotification();
            } else {
                console.log('Notification permission denied');
                this.trackEvent('notifications_denied');
            }
        } catch (error) {
            console.error('Error requesting notification permission:', error);
        }
    }

    showWelcomeNotification() {
        if (Notification.permission === 'granted') {
            new Notification('Sistema PNSB 2024', {
                body: 'Notificações ativadas! Você receberá lembretes importantes.',
                icon: '/static/icons/icon-192x192.png',
                badge: '/static/icons/badge-72x72.png'
            });
        }
    }

    async registerBackgroundSync(tag) {
        if (this.swRegistration && 'sync' in this.swRegistration) {
            try {
                await this.swRegistration.sync.register(tag);
                console.log(`Background sync registered: ${tag}`);
            } catch (error) {
                console.error(`Background sync failed: ${tag}`, error);
            }
        }
    }

    async syncOfflineData() {
        // Sincronizar dados salvos offline
        this.registerBackgroundSync('background-sync-visitas');
        this.registerBackgroundSync('background-sync-checklist');
    }

    adjustLayoutForOrientation() {
        const isLandscape = window.orientation === 90 || window.orientation === -90;
        document.body.classList.toggle('landscape-mode', isLandscape);
    }

    // Salvar dados offline
    async saveOfflineData(type, data) {
        try {
            const offlineData = JSON.parse(localStorage.getItem(`offline_${type}`) || '[]');
            offlineData.push({
                ...data,
                timestamp: Date.now(),
                synced: false
            });
            localStorage.setItem(`offline_${type}`, JSON.stringify(offlineData));
            
            // Registrar sync quando voltar online
            if (this.isOnline) {
                this.registerBackgroundSync(`background-sync-${type}`);
            }
            
            console.log(`Data saved offline: ${type}`);
        } catch (error) {
            console.error('Failed to save offline data:', error);
        }
    }

    // Obter dados offline
    getOfflineData(type) {
        try {
            return JSON.parse(localStorage.getItem(`offline_${type}`) || '[]');
        } catch (error) {
            console.error('Failed to get offline data:', error);
            return [];
        }
    }

    // Analytics simplificado
    trackEvent(eventName, data = {}) {
        console.log(`PWA Event: ${eventName}`, data);
        
        // Enviar para analytics quando online
        if (this.isOnline) {
            // Implementar envio para Google Analytics ou similar
        }
    }

    // Utilitário para mostrar toast
    showToast(message, type = 'info') {
        // Usar função global se disponível
        if (typeof showToast === 'function') {
            showToast(message, type);
            return;
        }
        
        // Fallback simples
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// Inicializar PWA Manager com error handling
let pwaManager;

function initializePWA() {
    try {
        pwaManager = new PWAManager();
        window.pwaManager = pwaManager;
        console.log('PWA Manager initialized successfully');
        
        // Adicionar funções de debugging global
        window.clearPWACache = async () => {
            try {
                const cacheNames = await caches.keys();
                await Promise.all(cacheNames.map(name => caches.delete(name)));
                
                const registrations = await navigator.serviceWorker.getRegistrations();
                await Promise.all(registrations.map(reg => reg.unregister()));
                
                console.log('PWA cache and service workers cleared');
                window.location.reload();
            } catch (error) {
                console.error('Error clearing PWA cache:', error);
            }
        };
        
        window.debugPWA = () => {
            console.log('=== PWA DEBUG INFO ===');
            console.log('PWA Manager:', pwaManager);
            console.log('Service Worker Support:', 'serviceWorker' in navigator);
            console.log('Current URL:', window.location.href);
            console.log('Run clearPWACache() to reset everything');
        };
        
    } catch (error) {
        console.error('Failed to initialize PWA Manager:', error);
        // Fallback: criar objeto vazio para evitar erros
        window.pwaManager = {
            installApp: () => console.log('PWA Manager not available'),
            dismissInstallBanner: () => console.log('PWA Manager not available')
        };
        
        window.clearPWACache = () => console.log('PWA Manager not available');
        window.debugPWA = () => console.log('PWA Manager not available');
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializePWA);
} else {
    initializePWA();
}