// Service Worker para PWA Sistema PNSB 2024
const CACHE_NAME = 'pnsb-v1.0.0';
const OFFLINE_URL = '/offline';

// Recursos essenciais para cache
const ESSENTIAL_RESOURCES = [
    '/',
    '/visitas',
    '/configuracoes',
    '/relatorios',
    '/static/css/design-system.css',
    '/static/js/components.js',
    '/static/manifest.json',
    // Bootstrap e FontAwesome
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js'
];

// API endpoints críticos
const API_CACHE_PATTERNS = [
    '/api/visitas',
    '/api/contatos',
    '/api/checklist',
    '/api/relatorios'
];

// Instalar Service Worker
self.addEventListener('install', event => {
    console.log('[SW] Installing Service Worker...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[SW] Caching essential resources');
                return cache.addAll(ESSENTIAL_RESOURCES);
            })
            .then(() => {
                console.log('[SW] Installation complete');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('[SW] Installation failed:', error);
            })
    );
});

// Ativar Service Worker
self.addEventListener('activate', event => {
    console.log('[SW] Activating Service Worker...');
    
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== CACHE_NAME) {
                            console.log('[SW] Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('[SW] Activation complete');
                return self.clients.claim();
            })
    );
});

// Interceptar requisições (Fetch)
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);

    // Ignorar extensões do browser e requisições non-GET
    if (request.method !== 'GET' || 
        url.protocol !== 'http:' && url.protocol !== 'https:') {
        return;
    }

    // Cache First para recursos estáticos
    if (isStaticResource(url)) {
        event.respondWith(cacheFirst(request));
        return;
    }

    // Network First para APIs
    if (isApiRequest(url)) {
        event.respondWith(networkFirst(request));
        return;
    }

    // Stale While Revalidate para páginas
    if (isPageRequest(url)) {
        event.respondWith(staleWhileRevalidate(request));
        return;
    }
});

// Estratégia Cache First (para recursos estáticos)
async function cacheFirst(request) {
    try {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }

        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.error('[SW] Cache First failed:', error);
        return await caches.match('/offline') || new Response('Offline', { status: 503 });
    }
}

// Estratégia Network First (para APIs)
async function networkFirst(request) {
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.log('[SW] Network failed, trying cache for:', request.url);
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Retornar dados offline para APIs críticas
        if (isOfflineCompatibleAPI(request.url)) {
            return new Response(JSON.stringify({
                error: 'Offline',
                message: 'Dados salvos localmente não disponíveis',
                offline: true
            }), {
                headers: { 'Content-Type': 'application/json' },
                status: 503
            });
        }
        
        throw error;
    }
}

// Estratégia Stale While Revalidate (para páginas)
async function staleWhileRevalidate(request) {
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    const fetchPromise = fetch(request).then(networkResponse => {
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    }).catch(() => cachedResponse);
    
    return cachedResponse || fetchPromise;
}

// Helpers para identificar tipos de requisição
function isStaticResource(url) {
    return url.pathname.includes('/static/') ||
           url.hostname !== self.location.hostname ||
           /\.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf)$/i.test(url.pathname);
}

function isApiRequest(url) {
    return url.pathname.startsWith('/api/');
}

function isPageRequest(url) {
    return url.hostname === self.location.hostname && 
           !url.pathname.startsWith('/api/') && 
           !url.pathname.includes('/static/');
}

function isOfflineCompatibleAPI(url) {
    return API_CACHE_PATTERNS.some(pattern => url.includes(pattern));
}

// Escutar mensagens do cliente
self.addEventListener('message', event => {
    const { type, data } = event.data;
    
    switch (type) {
        case 'SKIP_WAITING':
            self.skipWaiting();
            break;
            
        case 'GET_VERSION':
            event.ports[0].postMessage({ version: CACHE_NAME });
            break;
            
        case 'CACHE_URLS':
            cacheUrls(data.urls);
            break;
            
        case 'CLEAR_CACHE':
            clearCache();
            break;
    }
});

// Função para cache manual de URLs
async function cacheUrls(urls) {
    try {
        const cache = await caches.open(CACHE_NAME);
        await cache.addAll(urls);
        console.log('[SW] URLs cached successfully:', urls);
    } catch (error) {
        console.error('[SW] Failed to cache URLs:', error);
    }
}

// Função para limpar cache
async function clearCache() {
    try {
        const cacheNames = await caches.keys();
        await Promise.all(cacheNames.map(name => caches.delete(name)));
        console.log('[SW] All caches cleared');
    } catch (error) {
        console.error('[SW] Failed to clear cache:', error);
    }
}

// Background Sync para operações offline
self.addEventListener('sync', event => {
    console.log('[SW] Background sync triggered:', event.tag);
    
    if (event.tag === 'background-sync-visitas') {
        event.waitUntil(syncVisitas());
    }
    
    if (event.tag === 'background-sync-checklist') {
        event.waitUntil(syncChecklist());
    }
});

// Sincronizar visitas offline
async function syncVisitas() {
    try {
        // Recuperar dados salvos offline
        const offlineData = await getOfflineData('visitas');
        
        if (offlineData && offlineData.length > 0) {
            for (const item of offlineData) {
                try {
                    await fetch('/api/visitas', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(item)
                    });
                } catch (error) {
                    console.error('[SW] Failed to sync visit:', error);
                }
            }
            
            // Limpar dados offline após sincronização
            await clearOfflineData('visitas');
            console.log('[SW] Visitas synchronized successfully');
        }
    } catch (error) {
        console.error('[SW] Sync visitas failed:', error);
    }
}

// Sincronizar checklist offline
async function syncChecklist() {
    try {
        const offlineData = await getOfflineData('checklist');
        
        if (offlineData && offlineData.length > 0) {
            for (const item of offlineData) {
                try {
                    await fetch(`/api/checklist/${item.visita_id}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(item.data)
                    });
                } catch (error) {
                    console.error('[SW] Failed to sync checklist:', error);
                }
            }
            
            await clearOfflineData('checklist');
            console.log('[SW] Checklist synchronized successfully');
        }
    } catch (error) {
        console.error('[SW] Sync checklist failed:', error);
    }
}

// Helpers para dados offline
async function getOfflineData(type) {
    // Implementar recuperação de dados do IndexedDB
    return [];
}

async function clearOfflineData(type) {
    // Implementar limpeza de dados do IndexedDB
}

// Push Notifications
self.addEventListener('push', event => {
    const options = {
        body: event.data ? event.data.text() : 'Nova notificação do Sistema PNSB',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/badge-72x72.png',
        vibrate: [200, 100, 200],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'explore',
                title: 'Abrir Sistema',
                icon: '/static/icons/checkmark.png'
            },
            {
                action: 'close',
                title: 'Fechar',
                icon: '/static/icons/xmark.png'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification('Sistema PNSB 2024', options)
    );
});

// Notification Click
self.addEventListener('notificationclick', event => {
    event.notification.close();

    if (event.action === 'explore') {
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

console.log('[SW] Service Worker loaded successfully');