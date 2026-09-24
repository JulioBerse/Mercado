from flask import Blueprint, render_template, request, redirect, url_for, session
from database import conectar_banco, TABELA_USUARIO

auth_bp = Blueprint('auth', __name__)

# Removida a rota '/' aqui para não conflitar com a rota '/' do caixa.py

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario_input = request.form.get('username', '').strip()
        senha_input = request.form.get('password', '').strip()
        
        try:
            conn = conectar_banco()
            cur = conn.cursor()
            
            cur.execute(
                f"SELECT id, login, senha, perfil FROM {TABELA_USUARIO} WHERE LOWER(login) = LOWER(%s)", 
                (usuario_input,)
            )
            user = cur.fetchone()
            
            cur.close()
            conn.close()
            
            if user:
                db_senha = str(user[2]).strip() if user[2] else ''
                
                if db_senha == senha_input:
                    session['user_id'] = user[0]
                    session['username'] = user[1]
                    session['usuario'] = user[1]
                    session['perfil'] = user[3]
                    
                    return redirect(url_for('caixa.index'))
                else:
                    return render_template('login.html', msg="Senha incorreta!")
            else:
                return render_template('login.html', msg="Usuário não encontrado!")
                
        except Exception as e:
            return render_template('login.html', msg=f"Erro de banco de dados: {e}")
            
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))