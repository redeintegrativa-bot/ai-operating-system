/**
 * AIOS Dashboard - Tasks Page (Task Center)
 */
const Pages = window.Pages || {};
Pages.Tasks = {
  _el: null, _unsubs: [],
  _filters: {search:'',status:'all',priority:'all'},

  render() {
    const el = document.createElement('div');
    el.className = 'tasks-page animate-fade-in';
    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Task Center</h1>
          <p class="page-subtitle">Gerencie todas as tarefas do AIOS</p>
        </div>
        <div class="header-actions">
          <button class="btn btn-primary btn-sm" onclick="Pages.Tasks._create()"><span class="material-icons">add</span> Nova Tarefa</button>
        </div>
      </div>
      <div class="search-bar">
        <span class="search-bar-icon material-icons">search</span>
        <input type="text" class="search-bar-input" id="tasks-search" placeholder="Filtrar tarefas..." oninput="Pages.Tasks._filter({search:this.value})">
        <div class="search-bar-filters">
          <select class="form-select filter-select" id="tasks-status" onchange="Pages.Tasks._filter({status:this.value})">
            <option value="all">Todos status</option>
            <option value="pending">Pendente</option>
            <option value="in_progress">Em Progresso</option>
            <option value="done">Concluído</option>
            <option value="failed">Falhou</option>
          </select>
          <select class="form-select filter-select" id="tasks-priority" onchange="Pages.Tasks._filter({priority:this.value})">
            <option value="all">Todas prioridades</option>
            <option value="high">Alta</option>
            <option value="medium">Média</option>
            <option value="low">Baixa</option>
          </select>
        </div>
      </div>
      <div class="table-wrapper">
        <table class="data-table" id="tasks-table">
          <thead><tr><th>ID</th><th>Título</th><th>Status</th><th>Prioridade</th><th>Responsável</th><th>Missão</th><th>Ações</th></tr></thead>
          <tbody id="tasks-body"><tr><td colspan="7"><div class="loading-spinner"></div></td></tr></tbody>
        </table>
      </div>
    `;
    this._el = el;
    return el;
  },
  mount() {
    Store.fetchTasks();
    this._unsubs.push(Store.subscribe('tasks', data => this._renderTable(data)));
    this._unsubs.push(Store.subscribe('loading', () => {
      if (Store.loading.tasks && document.getElementById('tasks-body'))
        document.getElementById('tasks-body').innerHTML = '<tr><td colspan="7"><div class="loading-spinner"></div></td></tr>';
    }));
  },
  unmount() { this._unsubs.forEach(u => u()); },

  _renderTable(tasks) {
    const tbody = document.getElementById('tasks-body');
    if (!tbody) return;
    if (!tasks || tasks.length === 0) { tbody.innerHTML = '<tr><td colspan="7" class="empty-cell"><div class="empty-state"><span class="empty-icon material-icons">task_alt</span><p class="empty-text">Nenhuma tarefa</p></div></td></tr>'; return; }
    tbody.innerHTML = tasks.map(t => `
      <tr data-task-id="${t.id}" data-task-status="${t.status}" data-task-priority="${t.priority}">
        <td class="task-id-cell">${t.id}</td>
        <td class="task-title-cell">${t.title}</td>
        <td><span class="task-status task-status-${t.status||'pending'}">${t.status||'pending'}</span></td>
        <td><span class="task-priority task-priority-${t.priority||'medium'}">${t.priority||'medium'}</span></td>
        <td>${t.assignee||'—'}</td>
        <td>${t.mission||'—'}</td>
        <td class="task-actions-cell">
          <button class="btn-icon" onclick="Pages.Tasks._edit('${t.id}')" title="Editar"><span class="material-icons">edit</span></button>
          <button class="btn-icon btn-icon-danger" onclick="Pages.Tasks._delete('${t.id}')" title="Excluir"><span class="material-icons">delete</span></button>
          <button class="btn-icon" onclick="Pages.Tasks._detail('${t.id}')" title="Detalhes"><span class="material-icons">info</span></button>
        </td>
      </tr>
    `).join('');
  },

  _filter(changes) {
    Object.assign(this._filters, changes);
    const {search, status, priority} = this._filters;
    const q = search.toLowerCase();
    document.querySelectorAll('#tasks-body tr').forEach(row => {
      if (row.dataset.taskStatus === undefined) return;
      const text = row.textContent.toLowerCase();
      const rs = row.dataset.taskStatus;
      const rp = row.dataset.taskPriority;
      const matchSearch = !q || text.includes(q);
      const matchStatus = status === 'all' || rs === status;
      const matchPriority = priority === 'all' || rp === priority;
      row.classList.toggle('hidden', !(matchSearch && matchStatus && matchPriority));
    });
  },

  _create() {
    Components.Modal.open({
      title: 'Nova Tarefa',
      body: `
        <form id="task-form" onsubmit="Pages.Tasks._submitCreate(event)">
          <div class="form-group"><label class="form-label">Título</label><input type="text" class="form-input" id="task-title" required></div>
          <div class="form-group"><label class="form-label">Descrição</label><textarea class="form-input form-textarea" id="task-desc" rows="2"></textarea></div>
          <div class="form-row"><div class="form-group half"><label class="form-label">Prioridade</label><select class="form-select" id="task-priority"><option value="medium">Média</option><option value="high">Alta</option><option value="low">Baixa</option></select></div><div class="form-group half"><label class="form-label">Responsável</label><select class="form-select" id="task-assignee"><option value="">Atribuir</option></select></div></div>
          <button type="submit" class="btn btn-primary btn-block">Criar Tarefa</button>
        </form>
      `,
      theme: 'modal-narrow'
    });
  },
  _submitCreate(e) {
    e.preventDefault();
    const title = document.getElementById('task-title').value;
    Store.addItem('tasks', {title, description:document.getElementById('task-desc').value, priority:document.getElementById('task-priority').value, status:'pending'});
    this._renderTable(Store.state.tasks);
    Components.Modal.close();
    Components.Toast.success('Tarefa criada');
  },
  _edit(id) {
    Components.Modal.open({
      title: 'Editar Tarefa',
      body: `<p>Edição da tarefa ${id} — em breve...</p>`
    });
  },
  _delete(id) {
    if (!confirm(`Excluir tarefa ${id}?`)) return;
    Store.removeItem('tasks', id);
    this._renderTable(Store.state.tasks);
    Components.Toast.success('Tarefa excluída');
  },
  _detail(id) {
    const t = Store.findById('tasks', id);
    if (!t) return Components.Toast.error('Tarefa não encontrada');
    Components.Modal.open({
      title: `Tarefa ${id}`,
      body: `<div class="task-detail"><div class="detail-section"><h4>${t.title}</h4><p>${t.description||'Sem descrição'}</p></div><div class="detail-grid"><div><strong>Status:</strong> ${t.status}</div><div><strong>Prioridade:</strong> ${t.priority}</div><div><strong>Responsável:</strong> ${t.assignee||'—'}</div><div><strong>Missão:</strong> ${t.mission||'—'}</div></div></div>`
    });
  }
};
