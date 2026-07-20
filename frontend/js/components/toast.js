/**
 * AIOS Dashboard - Toast Notification Component
 */
const Components = window.Components || {};
Components.Toast = {
  _container: document.getElementById('toast-container'),
  show(message, type = 'info', duration = 4000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icons = {success:'✅',error:'❌',warning:'⚠️',info:'ℹ️',processing:'⏳'};
    toast.innerHTML = `<span class="toast-icon">${icons[type]||'ℹ️'}</span><span class="toast-text">${message}</span>`;
    this._container.appendChild(toast);
    setTimeout(() => { toast.classList.add('visible'); }, 10);
    setTimeout(() => {
      toast.classList.remove('visible');
      setTimeout(() => toast.remove(), 300);
    }, duration);
    return toast;
  },
  success(m) { return this.show(m,'success'); },
  error(m) { return this.show(m,'error',6000); },
  warning(m) { return this.show(m,'warning',5000); },
  info(m) { return this.show(m,'info'); },
  processing(m) { return this.show(m,'processing', 60000); },
};
