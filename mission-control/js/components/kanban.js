/**
 * AIOS Mission Control - Kanban Board Component
 * Drag-and-drop Kanban board with columns and task cards.
 */
const Components = window.Components || {};

Components.KanbanBoard = {
  /**
   * Create a Kanban board.
   * @param {Object} options
   * @param {Array} options.columns - Column configs [{ id, name }]
   * @param {Array} options.tasks - Task items
   * @param {Function} [options.onTaskMove] - (taskId, fromColumn, toColumn)
   * @param {Function} [options.onTaskClick] - (task)
   * @param {Function} [options.onAddTask] - (columnId)
   * @returns {HTMLElement}
   */
  create(options) {
    const el = document.createElement('div');
    el.className = 'kanban-board';

    const columns = options.columns || [
      { id: 'backlog', name: 'Backlog' },
      { id: 'todo', name: 'To Do' },
      { id: 'in_progress', name: 'In Progress' },
      { id: 'review', name: 'Review' },
      { id: 'done', name: 'Done' }
    ];

    columns.forEach(col => {
      const tasks = options.tasks.filter(t => t.column === col.id);
      const colEl = document.createElement('div');
      colEl.className = 'kanban-column';
      colEl.dataset.column = col.id;

      colEl.innerHTML = `
        <div class="kanban-column-header">
          <span class="kanban-column-title">${col.name}</span>
          <span class="kanban-column-count">${tasks.length}</span>
        </div>
        <div class="kanban-column-body" data-column="${col.id}">
          ${tasks.map(t => this._buildCard(t)).join('')}
        </div>
        <button class="kanban-add-btn" data-column="${col.id}">+ Add Task</button>
      `;

      el.appendChild(colEl);
    });

    this._bindDragDrop(el, options);
    this._bindAddButtons(el, options);

    return el;
  },

  /**
   * Build a task card HTML.
   * @param {Object} task
   * @returns {string}
   * @private
   */
  _buildCard(task) {
    const agent = Store.findById('agents', task.assignee);
    const priorityColors = { high: 'var(--accent-red)', medium: 'var(--accent-orange)', low: 'var(--accent-blue)' };
    const tags = (task.tags || []).slice(0, 2).map(t =>
      `<span class="badge badge-tag">${t}</span>`
    ).join('');

    return `
      <div class="kanban-card" draggable="true" data-task-id="${task.id}">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
          <span class="badge badge-${task.priority}">${task.priority}</span>
          ${agent ? `<div class="kanban-card-assignee">${agent.avatar}</div>` : ''}
        </div>
        <div class="kanban-card-title">${task.title}</div>
        <div class="kanban-card-footer">
          <div class="kanban-card-tags">${tags}</div>
        </div>
      </div>
    `;
  },

  /**
   * Bind drag and drop events.
   * @param {HTMLElement} board
   * @param {Object} options
   * @private
   */
  _bindDragDrop(board, options) {
    let draggedTask = null;
    let fromColumn = null;

    board.addEventListener('dragstart', (e) => {
      const card = e.target.closest('.kanban-card');
      if (!card) return;

      draggedTask = card;
      fromColumn = card.closest('.kanban-column-body').dataset.column;
      card.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', card.dataset.taskId);
    });

    board.addEventListener('dragend', (e) => {
      const card = e.target.closest('.kanban-card');
      if (card) card.classList.remove('dragging');
      board.querySelectorAll('.kanban-column-body').forEach(col => {
        col.classList.remove('drag-over');
      });
      draggedTask = null;
      fromColumn = null;
    });

    board.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      const colBody = e.target.closest('.kanban-column-body');
      if (colBody) {
        board.querySelectorAll('.kanban-column-body').forEach(c => c.classList.remove('drag-over'));
        colBody.classList.add('drag-over');
      }
    });

    board.addEventListener('dragleave', (e) => {
      const colBody = e.target.closest('.kanban-column-body');
      if (colBody && !colBody.contains(e.relatedTarget)) {
        colBody.classList.remove('drag-over');
      }
    });

    board.addEventListener('drop', (e) => {
      e.preventDefault();
      const colBody = e.target.closest('.kanban-column-body');
      if (!colBody || !draggedTask) return;

      const toColumn = colBody.dataset.column;
      const taskId = parseInt(draggedTask.dataset.taskId);

      // Move the card
      colBody.appendChild(draggedTask);
      colBody.classList.remove('drag-over');

      // Update counts
      this._updateCounts(board);

      // Callback
      if (options.onTaskMove) {
        options.onTaskMove(taskId, fromColumn, toColumn);
      }
    });

    // Click on cards
    board.addEventListener('click', (e) => {
      const card = e.target.closest('.kanban-card');
      if (card && options.onTaskClick) {
        const taskId = parseInt(card.dataset.taskId);
        const task = Store.findById('tasks', taskId);
        if (task) options.onTaskClick(task);
      }
    });
  },

  /**
   * Bind add task buttons.
   * @param {HTMLElement} board
   * @param {Object} options
   * @private
   */
  _bindAddButtons(board, options) {
    board.querySelectorAll('.kanban-add-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const column = btn.dataset.column;
        if (options.onAddTask) options.onAddTask(column);
      });
    });
  },

  /**
   * Update column task counts.
   * @param {HTMLElement} board
   * @private
   */
  _updateCounts(board) {
    board.querySelectorAll('.kanban-column').forEach(col => {
      const body = col.querySelector('.kanban-column-body');
      const count = col.querySelector('.kanban-column-count');
      if (body && count) {
        count.textContent = body.querySelectorAll('.kanban-card').length;
      }
    });
  }
};
