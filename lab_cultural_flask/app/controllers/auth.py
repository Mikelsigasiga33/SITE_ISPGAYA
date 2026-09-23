from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models.utilizador import Utilizador
from app.utils.security import sanitize
import pyotp

auth_bp = Blueprint('auth', __name__)


def login_required(f):
    """Decorator que verifica se o utilizador está autenticado."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logado'):
            flash('Por favor, faça login para aceder ao backoffice.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    """Decorator que verifica se o utilizador tem um dos roles permitidos."""
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('admin_logado'):
                flash('Por favor, faça login para aceder ao backoffice.', 'warning')
                return redirect(url_for('auth.login'))
            user_role = session.get('admin_role', '')
            # O admin global tem acesso a tudo
            if user_role == 'admin':
                return f(*args, **kwargs)
            if user_role not in roles:
                flash('Não tem permissão para aceder a esta secção.', 'error')
                return redirect(url_for('backoffice.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def efetuar_login_sessao(utilizador):
    """Auxiliar para registar os dados do administrador na sessão do Flask."""
    session['admin_logado'] = True
    session['admin_id'] = utilizador['id']
    session['admin_nome'] = utilizador['nome']
    session['admin_username'] = utilizador['username']
    session['admin_role'] = utilizador.get('role', 'admin')
    session['admin_clube_id'] = utilizador.get('clube_id')
    # Limpar variáveis de 2FA temporárias
    session.pop('mfa_pending_user_id', None)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login do backoffice."""
    if session.get('admin_logado'):
        return redirect(url_for('backoffice.dashboard'))

    erro = None
    if request.method == 'POST':
        username = sanitize(request.form.get('username', ''))
        password = request.form.get('password', '')

        # Validar campos
        if not username or not password:
            erro = 'Por favor, preencha todos os campos.'
        else:
            utilizador = Utilizador.get_by_username(username)
            if utilizador and Utilizador.verificar_password(password, utilizador['password']):
                # Se o utilizador tiver MFA ativo, redirecionar para verificação do código
                if utilizador.get('mfa_ativo') and utilizador.get('mfa_secret'):
                    session['mfa_pending_user_id'] = utilizador['id']
                    return redirect(url_for('auth.verify_2fa'))
                
                # Caso contrário, login completo direto
                efetuar_login_sessao(utilizador)
                return redirect(url_for('backoffice.dashboard'))
            else:
                erro = 'Credenciais incorretas. Tente novamente.'

    return render_template('backoffice/login.html', erro=erro)


@auth_bp.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    """Página de introdução do código 2FA (TOTP) gerado pela aplicação autenticadora."""
    if not session.get('mfa_pending_user_id'):
        flash('Sessão expirada. Por favor, faça login novamente.', 'warning')
        return redirect(url_for('auth.login'))

    erro = None
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        if not code:
            erro = 'Introduza o código de 6 dígitos.'
        else:
            utilizador = Utilizador.get_by_id(session['mfa_pending_user_id'])
            if not utilizador or not utilizador.get('mfa_secret'):
                erro = 'Configuração do 2FA corrompida. Faça login novamente.'
            else:
                totp = pyotp.TOTP(utilizador['mfa_secret'])
                # Validação com tolerância de desvio temporal (valid_window=1)
                if totp.verify(code, valid_window=1):
                    efetuar_login_sessao(utilizador)
                    flash('Autenticação multifator efetuada com sucesso.', 'success')
                    return redirect(url_for('backoffice.dashboard'))
                else:
                    erro = 'Código incorreto ou expirado. Tente novamente.'

    return render_template('backoffice/verify_mfa.html', erro=erro)


@auth_bp.route('/logout')
def logout():
    """Terminar sessão."""
    session.clear()
    flash('Sessão terminada com sucesso.', 'info')
    return redirect(url_for('auth.login'))
