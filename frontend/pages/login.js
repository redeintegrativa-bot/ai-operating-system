/**
 * AIOS Dashboard - Login Page
 */
const Pages = window.Pages || {};
Pages.Login = {
  _el: null,
  render() {
    const el = document.createElement('div');
    el.innerHTML = `
      <div class="login-page animate-fade-in">
        <div class="login-card">
          <div class="login-header">
            <div class="login-logo">
              <span class="login-logo-icon">🎯</span>
              <span class="login-logo-text">AIOS</span>
            </div>
            <p class="login-subtitle">Sistema Operacional de IA</p>
          </div>
          <form class="login-form" onsubmit="Pages.Login._submit(event)">
            <div class="form-group">
              <label class="form-label" for="login-username">Usuário</label>
              <input type="text" id="login-username" class="form-input" placeholder="admin" required autofocus>
            </div>
            <div class="form-group">
              <label class="form-label" for="login-password">Senha</label>
              <input type="password" id="login-password" class="form-input" placeholder="••••••" required>
            </div>
            <div id="login-error" class="login-error hidden"></div>
            <button type="submit" class="btn btn-primary btn-block login-btn" id="login-btn">
              Entrar
            </button>
            <div class="login-footer">
              <label class="checkbox-wrapper">
                <input type="checkbox" checked>
                <span>Lembrar acesso</span>
              </label>
              <a href="#" class="login-link">Esqueci a senha</a>
            </div>
          </form>
          <div class="login-hint">
            Credenciais padrão: <strong>admin</strong> / <strong>admin</strong>
          </div>
        </div>
      </div>
    `;
    this._el = el;
    return el;
  },
  mount() {},
  unmount() { this._el = null; },
  async _submit(e) {
    e.preventDefault();
    const btn = document.getElementById('login-btn');
    const err = document.getElementById('login-error');
    btn.disabled = true;
    btn.textContent = 'Entrando...';
    err.classList.add('hidden');
    try {
      await new Promise(r => setTimeout(r, 600));
      Router.navigate('/dashboard');
    } catch (ex) {
      err.textContent = 'Falha na autenticação';
      err.classList.remove('hidden');
      btn.disabled = false;
      btn.textContent = 'Entrar';
    }
  }
};
