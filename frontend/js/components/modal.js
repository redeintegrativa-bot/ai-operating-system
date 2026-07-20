/**
 * AIOS Dashboard - Modal Component
 */
const Components = window.Components || {};
Components.Modal = {
  _container: document.getElementById('modal-container'),
  open(config) {
    const bg = document.createElement('div');
    bg.className = 'modal-backdrop active';
    bg.onclick = (e) => { if (e.target === bg) this.close(); };
    const modal = document.createElement('div');
    modal.className = `modal ${config.theme || ''}`;
    modal.innerHTML = `
      <div class="modal-header">
        <h3 class="modal-title">${config.title || ''}</h3>
        <button class="modal-close material-icons" onclick="Components.Modal.close()">close</button>
      </div>
      <div class="modal-body">${config.body || ''}</div>
      ${config.footer ? `<div class="modal-footer">${config.footer}</div>` : ''}
    `;
    bg.appendChild(modal);
    this._container.appendChild(bg);
    document.body.style.overflow = 'hidden';
    if (config.onOpen) config.onOpen(modal);
    return modal;
  },
  close() {
    const bg = this._container.querySelector('.modal-backdrop');
    if (bg) { bg.remove(); document.body.style.overflow = ''; }
  },
  updateBody(html) {
    const body = this._container.querySelector('.modal-body');
    if (body) body.innerHTML = html;
  }
};
