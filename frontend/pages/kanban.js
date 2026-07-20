/**
 * AIOS Dashboard - Kanban Board Page
 */
const Pages = window.Pages || {};
Pages.Kanban = {
  _el: null,
  _columns: [
    {key:'pending',label:'Pendente'},
    {key:'in_progress',label:'Em progresso'},
    {key:'done',label:'Concluído'},
    {key:'backlog',label:'Backlog'},
  ],

  render() {
    const el = document.createElement('div');
    el.className = 'kanban-page animate-fade-in';
    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Kanban</h1>
          <p class="page-subtitle">Quadro Kanban para gerenciamento visual de tarefas</p>
        </div>
        <div class="header-actions">
          <button class="btn btn-primary btn-sm" onclick="Pages.Kanban._addTaskColumn()"><span class="material-icons">add</span> Adicionar</button>
        </div>
      </div>
      <div class="kanban-board" id="kanban-board"></div>
    `;
    this._el = el;
    return el;
  },
  mount() {
    Store.fetchTasks();
    Store.subscribe('tasks', d => this._render(d));
    this._render(Store.state.tasks);
  },
  _render(t) {
    const board = document.getElementById('kanban-board');
    if (!board) return;
    const tasks = t || [];
    board.innerHTML = this._columns.map(col => {
      const colTasks = tasks.filter(t => (t.status||'pending') === col.key);
      return `<div class="kanban-column">
        <div class="kanban-column-head">
          <span class="kanban-column-label">${col.label}</span>
          <span class="kanban-badge">${colTasks.length}</span>
        </div>
        <div class="kanban-column-body" data-status="${col.key}">
          ${colTasks.length === 0 ? '<div class="kanban-empty">Sem tarefas</div>' :
          colTasks.map(t => `
            <div class="card task-card" onclick="Pages.Kanban._detail('${t.id}')">
              <div class="card-body">
                <div class="task-card-header">
                  <span class="task-priority task-priority-${t.priority||'medium'}"></span>
                  <span class="task-id">${t.id}</span>
                </div>
                <span class="task-card-title">${t.title}</span>
                <div class="task-card-footer">
                  <span class="task-card-assignee">${t.assignee||'—'}</span>
                </div>
              </div>
            </div>`
          ).join('')}
        </div>
      </div>`
    }).join('');
  },
  _addTaskColumn() {
    const cols = ['Pendente','Em Progresso','Concluído'];
    const m = Components.Modal.open({
      title: 'Nova Tarefa',
      theme: 'modal-narrow',
      body: `<form id="new-task" onsubmit="Pages.Kanban._submitAdd(event)">
        <div class="form-group"><label class="form-label">Título</label><input class="form-input" id="new-task-title" required></div>
        <div class="form-group"><label class="form-label">Prioridade</label><select class="form-select" id="new-task-priority">${['high','medium','low'].map(v => `<option value="${v}" ${v==='medium'?'selected':''}>${v}</option>`).join('')}</select></div>
        <div class="form-group"><label class="form-label">Status</label><select class="form-select" id="new-task-status">${cols.map(c => `<option value="${c}" ${c==='Pendente'?'selected':''}>${c}</option>`).join('')}</select></div>
        <button type="submit" class="btn btn-primary btn-block">Criar</button>
      </form>`
    });
  },
  _submitAdd(e) {
    e.preventDefault();
    const title = document.getElementById('new-task-title').value;
    const priority = document.getElementById('new-task-priority').value;
    const statusMap = {Pendente:'pending','Em Progresso':'in_progress',Concluído:'done'};
    const status = statusMap[document.getElementById('new-task-status').value] || 'pending';
    if (!title) return;
    Store.addItem('tasks', {title, priority, status});
    this._render(Store.state.tasks);
    Components.Modal.close();
  },
  _detail(id) {
    Components.Modal.open({title: `Tarefa ${id}`, body: `<p>Detalhes da tarefa ${id}</p>`});
  }
};
