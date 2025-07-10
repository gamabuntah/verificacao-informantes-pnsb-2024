/*
===========================================
PNSB Components - Componentes Reutilizáveis
===========================================
*/

// ===== GERENCIADOR DE SIDEBAR =====
class SidebarManager {
  constructor() {
    this.sidebar = null;
    this.overlay = null;
    this.toggle = null;
    this.mainLayout = null;
    this.navbar = null;
    this.isOpen = false;
    this.isMobile = window.innerWidth <= 768;
    
    this.init();
  }
  
  init() {
    this.createElements();
    this.bindEvents();
    
    // Auto-abrir em desktop
    if (!this.isMobile) {
      this.open();
    }
  }
  
  createElements() {
    // Criar overlay
    this.overlay = document.createElement('div');
    this.overlay.className = 'sidebar-overlay';
    document.body.appendChild(this.overlay);
    
    // Referenciar elementos existentes
    this.sidebar = document.querySelector('.sidebar');
    this.toggle = document.querySelector('.sidebar-toggle');
    this.mainLayout = document.querySelector('.main-layout');
    this.navbar = document.querySelector('.navbar-custom');
  }
  
  bindEvents() {
    // Toggle button
    if (this.toggle) {
      this.toggle.addEventListener('click', () => this.toggleSidebar());
    }
    
    // Overlay click
    this.overlay.addEventListener('click', () => this.close());
    
    // Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) {
        this.close();
      }
    });
    
    // Resize handler
    window.addEventListener('resize', () => {
      const wasMobile = this.isMobile;
      this.isMobile = window.innerWidth <= 768;
      
      // Se mudou de mobile para desktop, abrir sidebar
      if (wasMobile && !this.isMobile && !this.isOpen) {
        this.open();
      }
      // Se mudou de desktop para mobile, fechar sidebar
      else if (!wasMobile && this.isMobile && this.isOpen) {
        this.close();
      }
    });
    
    // Links da sidebar
    document.querySelectorAll('.nav-link-custom').forEach(link => {
      link.addEventListener('click', () => {
        if (this.isMobile) {
          this.close();
        }
      });
    });
  }
  
  toggleSidebar() {
    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  }
  
  open() {
    this.isOpen = true;
    
    if (this.sidebar) this.sidebar.classList.add('active');
    if (this.overlay) this.overlay.classList.add('active');
    if (this.mainLayout && !this.isMobile) this.mainLayout.classList.add('sidebar-open');
    if (this.navbar && !this.isMobile) this.navbar.classList.add('sidebar-open');
    
    document.body.style.overflow = this.isMobile ? 'hidden' : 'auto';
  }
  
  close() {
    this.isOpen = false;
    
    if (this.sidebar) this.sidebar.classList.remove('active');
    if (this.overlay) this.overlay.classList.remove('active');
    if (this.mainLayout) this.mainLayout.classList.remove('sidebar-open');
    if (this.navbar) this.navbar.classList.remove('sidebar-open');
    
    document.body.style.overflow = 'auto';
  }
}

// ===== GERENCIADOR DE LOADING =====
class LoadingManager {
  static show(container, message = 'Carregando...') {
    // Remove loading existente
    this.hide(container);
    
    const loader = document.createElement('div');
    loader.className = 'loading-overlay';
    loader.innerHTML = `
      <div class="loading-spinner">
        <div class="spinner-ring"></div>
        <span>${message}</span>
      </div>
    `;
    
    // Garantir que o container seja posicionado relativamente
    const position = window.getComputedStyle(container).position;
    if (position === 'static') {
      container.style.position = 'relative';
    }
    
    container.appendChild(loader);
  }
  
  static hide(container) {
    const overlay = container.querySelector('.loading-overlay');
    if (overlay) {
      overlay.remove();
    }
  }
  
  static showGlobal(message = 'Carregando...') {
    this.show(document.body, message);
  }
  
  static hideGlobal() {
    this.hide(document.body);
  }
}

// ===== GERENCIADOR DE NOTIFICAÇÕES =====
class NotificationManager {
  static show(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    const icon = this.getIconByType(type);
    
    notification.innerHTML = `
      <div class="notification-content">
        <i class="fas fa-${icon}"></i>
        <span>${message}</span>
        <button class="notification-close" aria-label="Fechar">&times;</button>
      </div>
    `;
    
    // Adicionar ao DOM
    document.body.appendChild(notification);
    
    // Event listener para fechar
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => this.remove(notification));
    
    // Auto-remover após duração
    if (duration > 0) {
      setTimeout(() => this.remove(notification), duration);
    }
    
    // Animate in
    requestAnimationFrame(() => {
      notification.style.opacity = '1';
      notification.style.transform = 'translateX(0)';
    });
    
    return notification;
  }
  
  static remove(notification) {
    notification.style.opacity = '0';
    notification.style.transform = 'translateX(100%)';
    
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 300);
  }
  
  static success(message, duration = 5000) {
    return this.show(message, 'success', duration);
  }
  
  static error(message, duration = 7000) {
    return this.show(message, 'error', duration);
  }
  
  static warning(message, duration = 6000) {
    return this.show(message, 'warning', duration);
  }
  
  static info(message, duration = 5000) {
    return this.show(message, 'info', duration);
  }
  
  static getIconByType(type) {
    const icons = {
      success: 'check-circle',
      error: 'times-circle',
      warning: 'exclamation-triangle',
      info: 'info-circle'
    };
    return icons[type] || 'info-circle';
  }
}

// ===== GERENCIADOR DE BREADCRUMBS =====
class BreadcrumbManager {
  static create(items) {
    const breadcrumb = document.createElement('nav');
    breadcrumb.setAttribute('aria-label', 'breadcrumb');
    
    const ol = document.createElement('ol');
    ol.className = 'breadcrumb-custom';
    
    items.forEach((item, index) => {
      const li = document.createElement('li');
      li.className = 'breadcrumb-item';
      
      if (index === items.length - 1) {
        // Último item (ativo)
        li.classList.add('active');
        li.textContent = item.text;
        li.setAttribute('aria-current', 'page');
      } else {
        // Item com link
        const a = document.createElement('a');
        a.href = item.href;
        a.textContent = item.text;
        li.appendChild(a);
      }
      
      ol.appendChild(li);
    });
    
    breadcrumb.appendChild(ol);
    return breadcrumb;
  }
  
  static update(items, containerId = 'breadcrumb-container') {
    const container = document.getElementById(containerId);
    if (container) {
      container.innerHTML = '';
      container.appendChild(this.create(items));
    }
  }
}

// ===== GERENCIADOR DE TABELAS RESPONSIVAS =====
class ResponsiveTableManager {
  static init(selector = '.table-responsive-stack') {
    document.querySelectorAll(selector).forEach(table => {
      this.setupTable(table);
    });
  }
  
  static setupTable(tableContainer) {
    const table = tableContainer.querySelector('table');
    if (!table) return;
    
    const headers = table.querySelectorAll('th');
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
      const cells = row.querySelectorAll('td');
      cells.forEach((cell, index) => {
        if (headers[index]) {
          cell.setAttribute('data-label', headers[index].textContent);
        }
      });
    });
  }
}

// ===== GERENCIADOR DE FORMULÁRIOS =====
class FormManager {
  static init() {
    // Validação em tempo real
    document.querySelectorAll('.input-custom, .select-custom').forEach(input => {
      input.addEventListener('blur', () => this.validateField(input));
      input.addEventListener('input', () => this.clearFieldError(input));
    });
    
    // Submit handlers
    document.querySelectorAll('form').forEach(form => {
      form.addEventListener('submit', (e) => this.handleSubmit(e));
    });
  }
  
  static validateField(field) {
    const value = field.value.trim();
    const isRequired = field.hasAttribute('required');
    const type = field.type;
    
    let isValid = true;
    let message = '';
    
    // Validação de campo obrigatório
    if (isRequired && !value) {
      isValid = false;
      message = 'Este campo é obrigatório';
    }
    
    // Validação de email
    if (type === 'email' && value && !this.isValidEmail(value)) {
      isValid = false;
      message = 'Email inválido';
    }
    
    // Validação de telefone
    if (field.classList.contains('phone-input') && value && !this.isValidPhone(value)) {
      isValid = false;
      message = 'Telefone inválido';
    }
    
    if (!isValid) {
      this.showFieldError(field, message);
    } else {
      this.clearFieldError(field);
    }
    
    return isValid;
  }
  
  static showFieldError(field, message) {
    this.clearFieldError(field);
    
    field.classList.add('is-invalid');
    
    const error = document.createElement('div');
    error.className = 'field-error';
    error.style.color = 'var(--error-color)';
    error.style.fontSize = '0.75rem';
    error.style.marginTop = 'var(--spacing-xs)';
    error.textContent = message;
    
    field.parentNode.appendChild(error);
  }
  
  static clearFieldError(field) {
    field.classList.remove('is-invalid');
    
    const error = field.parentNode.querySelector('.field-error');
    if (error) {
      error.remove();
    }
  }
  
  static handleSubmit(e) {
    const form = e.target;
    const fields = form.querySelectorAll('.input-custom, .select-custom');
    
    let isValid = true;
    
    fields.forEach(field => {
      if (!this.validateField(field)) {
        isValid = false;
      }
    });
    
    if (!isValid) {
      e.preventDefault();
      NotificationManager.error('Por favor, corrija os erros no formulário');
    }
  }
  
  static isValidEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
  }
  
  static isValidPhone(phone) {
    const cleaned = phone.replace(/\D/g, '');
    return cleaned.length >= 10 && cleaned.length <= 11;
  }
}

// ===== UTILITÁRIOS =====
class Utils {
  static formatDate(date, format = 'dd/mm/yyyy') {
    if (!date) return '';
    
    const d = new Date(date);
    if (isNaN(d.getTime())) return '';
    
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    
    switch (format) {
      case 'dd/mm/yyyy':
        return `${day}/${month}/${year}`;
      case 'yyyy-mm-dd':
        return `${year}-${month}-${day}`;
      default:
        return d.toLocaleDateString('pt-BR');
    }
  }
  
  static formatPhone(phone) {
    if (!phone) return '';
    
    const cleaned = phone.replace(/\D/g, '');
    
    if (cleaned.length === 11) {
      return cleaned.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
    } else if (cleaned.length === 10) {
      return cleaned.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
    }
    
    return phone;
  }
  
  static debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }
  
  static throttle(func, limit) {
    let inThrottle;
    return function() {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }
}

// ===== INICIALIZAÇÃO GLOBAL =====
class App {
  static init() {
    // Inicializar componentes
    new SidebarManager();
    ResponsiveTableManager.init();
    FormManager.init();
    
    // Event listeners globais
    this.setupGlobalEventListeners();
    
    console.log('🚀 PNSB Components initialized');
  }
  
  static setupGlobalEventListeners() {
    // Smooth scroll para âncoras
    document.querySelectorAll('a[href^="#"]').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const target = document.querySelector(link.getAttribute('href'));
        if (target) {
          target.scrollIntoView({ behavior: 'smooth' });
        }
      });
    });
    
    // Auto-hide notifications after click outside
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.notification')) {
        document.querySelectorAll('.notification').forEach(notification => {
          if (!notification.dataset.persistent) {
            NotificationManager.remove(notification);
          }
        });
      }
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      // Ctrl/Cmd + K para buscar (se implementado)
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('.search-input');
        if (searchInput) {
          searchInput.focus();
        }
      }
    });
  }
}

// ===== AUTO-INICIALIZAÇÃO =====
document.addEventListener('DOMContentLoaded', () => {
  App.init();
});

// Exportar para uso global
window.LoadingManager = LoadingManager;
window.NotificationManager = NotificationManager;
window.BreadcrumbManager = BreadcrumbManager;
window.ResponsiveTableManager = ResponsiveTableManager;
window.FormManager = FormManager;
window.Utils = Utils;