/*
===========================================
PNSB Breadcrumbs Auto-Initialization
===========================================
*/

document.addEventListener('DOMContentLoaded', function() {
    // Mapear rotas para breadcrumbs
    const breadcrumbMap = {
        '/': [
            { text: 'Dashboard', href: '/' }
        ],
        '/visitas': [
            { text: 'Dashboard', href: '/' },
            { text: 'Visitas', href: '/visitas' }
        ],
        '/checklist': [
            { text: 'Dashboard', href: '/' },
            { text: 'Checklist', href: '/checklist' }
        ],
        '/contatos': [
            { text: 'Dashboard', href: '/' },
            { text: 'Contatos', href: '/contatos' }
        ],
        '/relatorios': [
            { text: 'Dashboard', href: '/' },
            { text: 'Relatórios', href: '/relatorios' }
        ],
        '/api/pnsb/status/funcionalidades-pnsb': [
            { text: 'Dashboard', href: '/' },
            { text: 'PNSB', href: '#' },
            { text: 'Funcionalidades', href: '/api/pnsb/status/funcionalidades-pnsb' }
        ],
        '/api/pnsb/questionarios/mapa-progresso': [
            { text: 'Dashboard', href: '/' },
            { text: 'PNSB', href: '#' },
            { text: 'Mapa de Progresso', href: '/api/pnsb/questionarios/mapa-progresso' }
        ],
        '/api/pnsb/produtividade/comparativo-equipe': [
            { text: 'Dashboard', href: '/' },
            { text: 'PNSB', href: '#' },
            { text: 'Produtividade', href: '/api/pnsb/produtividade/comparativo-equipe' }
        ]
    };
    
    // Obter caminho atual
    const currentPath = window.location.pathname;
    
    // Encontrar breadcrumbs correspondentes
    const breadcrumbs = breadcrumbMap[currentPath];
    
    if (breadcrumbs && window.BreadcrumbManager) {
        // Atualizar breadcrumbs
        BreadcrumbManager.update(breadcrumbs);
        
        // Mostrar container de breadcrumbs
        const container = document.getElementById('breadcrumb-container');
        if (container) {
            container.style.display = 'block';
        }
    }
});

// Função para atualizar breadcrumbs dinamicamente
function updatePageBreadcrumbs(breadcrumbs) {
    if (window.BreadcrumbManager) {
        BreadcrumbManager.update(breadcrumbs);
    }
}

// Exportar para uso global
window.updatePageBreadcrumbs = updatePageBreadcrumbs;