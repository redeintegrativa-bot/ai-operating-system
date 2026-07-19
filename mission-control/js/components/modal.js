/**
 * AIOS Mission Control - Modal Component
 * Reusable modal dialog with animations and accessibility.
 */
const Components = window.Components || {};

Components.Modal = {
  /** @type {Array} Stack of active modals */
  _stack: [],

  /**
   * Create and show a modal.
   * @param {Object} options
   * @param {string} options.title - Modal title
   * @param {string|HTMLElement} options.content - HTML string or DOM element
   * @param {string} [options.size='md'] - Size: 'sm', 'md', 'lg', 'xl'
   * @param {Function} [options.onClose] - Called when modal closes
   * @param {string} [options.footer] - HTML for footer buttons
   * @returns {Object} { show, hide, el }
   */
  create(options) {
    const size = options.size || 'md';
    const id = 'modal-' + Date.now();

    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.id = id;
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', options.title || 'Dialog');

    const content = typeof options.content === 'string'
      ? options.content
      : (options.content ? options.content.outerHTML : '');

    overlay.innerHTML = `
      <div class="modal modal-${size}">
        <div class="modal-header">
          <h3 class="modal-title">${options.title || ''}</h3>
          <button class="modal-close" aria-label="Close modal">&times;</button>
        </div>
        <div class="modal-body">${content}</div>
        ${options.footer ? `<div class="modal-footer">${options.footer}</div>` : ''}
      </div>
    `;

    const modal = {
      el: overlay,
      show() {
        document.getElementById('modal-container').appendChild(overlay);
        Components.Modal._stack.push(modal);
        // Focus first focusable
        requestAnimationFrame(() => {
          const focusable = overlay.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
          if (focusable) focusable.focus();
        });
      },
      hide() {
        Components.Modal._remove(modal);
        if (options.onClose) options.onClose();
      }
    };

    // Close button
    overlay.querySelector('.modal-close').addEventListener('click', () => modal.hide());

    // Backdrop click
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) modal.hide();
    });

    return modal;
  },

  /**
   * Show a simple confirmation dialog.
   * @param {string} title
   * @param {string} message
   * @returns {Promise<boolean>}
   */
  confirm(title, message) {
    return new Promise((resolve) => {
      const modal = this.create({
        title,
        content: `<p style="color: var(--text-secondary);">${message}</p>`,
        size: 'sm',
        footer: `
          <button class="btn btn-secondary" id="confirm-cancel">Cancel</button>
          <button class="btn btn-primary" id="confirm-ok">Confirm</button>
        `,
        onClose: () => resolve(false)
      });

      modal.show();

      const okBtn = modal.el.querySelector('#confirm-ok');
      const cancelBtn = modal.el.querySelector('#confirm-cancel');

      okBtn.addEventListener('click', () => { modal.hide(); resolve(true); });
      cancelBtn.addEventListener('click', () => { modal.hide(); resolve(false); });
    });
  },

  /**
   * Remove a modal from the DOM and stack.
   * @param {Object} modal
   * @private
   */
  _remove(modal) {
    if (modal.el && modal.el.parentNode) {
      modal.el.style.animation = 'fadeOut 150ms ease forwards';
      setTimeout(() => {
        if (modal.el.parentNode) modal.el.parentNode.removeChild(modal.el);
      }, 150);
    }
    this._stack = this._stack.filter(m => m !== modal);
  },

  /**
   * Close the topmost modal.
   */
  closeTop() {
    if (this._stack.length > 0) {
      const top = this._stack[this._stack.length - 1];
      top.hide();
    }
  }
};

// ESC key closes top modal
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && Components.Modal._stack.length > 0) {
    Components.Modal.closeTop();
  }
});
