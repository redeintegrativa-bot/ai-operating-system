/**
 * AIOS Dashboard - Card Component
 */
const Components = window.Components || {};

Components.Card = {
  create(config = {}) {
    const card = document.createElement('div');
    card.className = config.className || 'card';
    if (config.onClick) card.onclick = config.onClick;

    const header = config.title || config.icon ? `
      <div class="card-header">
        ${config.icon ? `<span class="card-icon material-icons">${config.icon}</span>` : ''}
        ${config.title ? `<h3 class="card-title">${config.title}</h3>` : ''}
        ${config.actions || ''}
      </div>
    ` : '';

    card.innerHTML = header + (config.body || '');
    return card;
  }
};
