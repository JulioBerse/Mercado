from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import psycopg2
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'
app.secret_key = 'segredo_grupo_yamasaki'

def conectar_banco():
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

TABELA_USUARIO = "usuario"
TABELA_PRODUTO = "produto"
def get_db_connection():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

# --- TEMPLATES HTML ---

@@ -21,34 +19,33 @@ def conectar_banco():
    <title>Grupo Yamasaki - Login</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-card { background: #1e293b; padding: 40px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); width: 100%; max-width: 400px; border-top: 4px solid #3b82f6; }
        h2 { text-align: center; margin-bottom: 24px; color: #60a5fa; }
        .form-group { margin-bottom: 16px; }
        label { display: block; margin-bottom: 8px; font-size: 14px; color: #94a3b8; }
        input { width: 100%; padding: 12px; border-radius: 6px; border: 1px solid #334155; background: #0f172a; color: #fff; box-sizing: border-box; }
        input:focus { border-color: #3b82f6; outline: none; }
        button { width: 100%; padding: 12px; background: #3b82f6; border: none; border-radius: 6px; color: white; font-weight: bold; cursor: pointer; margin-top: 10px; transition: background 0.2s; }
        .login-card { background: #1e293b; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); width: 100%; max-width: 400px; border-top: 4px solid #3b82f6; }
        h2 { color: #60a5fa; text-align: center; margin-top: 0; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #94a3b8; }
        input { width: 100%; padding: 12px; border-radius: 6px; border: 1px solid #334155; background: #0f172a; color: #fff; box-sizing: border-box; font-size: 16px; }
        button { background: #3b82f6; color: white; border: none; padding: 14px; width: 100%; font-size: 16px; font-weight: bold; border-radius: 6px; cursor: pointer; transition: background 0.2s; }
        button:hover { background: #2563eb; }
        .error { color: #f87171; font-size: 14px; text-align: center; margin-top: 12px; }
        .error { color: #f87171; text-align: center; margin-bottom: 15px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>Grupo Yamasaki</h2>
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <div class="form-group">
                <label>Usuário</label>
                <input type="text" name="username" required autofocus>
                <label>Usuário / Operador</label>
                <input type="text" name="usuario" required autofocus>
            </div>
            <div class="form-group">
                <label>Senha</label>
                <input type="password" name="password" required>
                <input type="password" name="senha" required>
            </div>
            <button type="submit">Entrar no Sistema</button>
        </form>
        {% if msg %}
            <div class="error">{{ msg }}</div>
        {% endif %}
    </div>
</body>
</html>
@@ -170,13 +167,14 @@ def conectar_banco():
        <div class="qr-section" id="qr_box">
            <h3 style="color: #60a5fa; margin-top: 0; font-size: 16px;">Pagamento via Pix</h3>
            <p style="font-size: 13px; color: #94a3b8;">Escaneie a chave:</p>
            <!-- QR Code gerado automaticamente com a sua chave Pix -->
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=py9dm.mt@gmail.com" alt="QR Code Pix py9dm.mt@gmail.com">
            <p style="font-size: 12px; color: #fbbf24; margin-top: 10px;">Chave: py9dm.mt@gmail.com<br><b>Grupo Yamasaki</b></p>
        </div>
    </div>
</body>
</html>
"""

HTML_ESTOQUE = """
<!DOCTYPE html>
<html lang="pt-br">
@@ -235,7 +233,7 @@ def conectar_banco():
        <form method="POST">
            <div class="form-group">
                <label>Código de Barras ou ID do Produto</label>
                <input type="text" id="identificador_estoque" name="identificador" onkeyup="buscarEstoque()" required autofocus>
                <input type="text" id="identificador_estoque" name="identificador" oninput="buscarEstoque()" onblur="buscarEstoque()" required autofocus>
                <div id="info_produto"></div>
            </div>
            <div class="form-group">
@@ -248,210 +246,211 @@ def conectar_banco():
</body>
</html>
"""
# --- ROTAS DO SISTEMA ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    mensagem = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
HTML_FECHAMENTO = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Grupo Yamasaki - Fechamento de Caixa</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #1e293b; padding: 15px 25px; border-radius: 8px; margin-bottom: 20px; border-bottom: 3px solid #3b82f6; }
        .nav-links a { color: #60a5fa; text-decoration: none; margin-left: 15px; font-weight: 600; }
        .container { max-width: 900px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        h1 { color: #60a5fa; margin-top: 0; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #334155; }
        th { background: #0f172a; color: #60a5fa; }
        .total-geral { margin-top: 20px; font-size: 20px; font-weight: bold; color: #34d399; text-align: right; }
    </style>
</head>
<body>
    <div class="header">
        <div><strong>Operador:</strong> {{ usuario }}</div>
        <div class="nav-links">
            <a href="/">Caixa (Venda)</a>
            <a href="/estoque/entrada">Entrada de Estoque</a>
            <a href="/relatorio/fechamento">📊 Fechamento de Caixa</a>
            <a href="/logout" style="color: #f87171;">Sair</a>
        </div>
    </div>
    <div class="container">
        <h1>Fechamento de Caixa do Dia</h1>
        <table>
            <thead>
                <tr>
                    <th>Forma de Pagamento</th>
                    <th>Total Arrecadado</th>
                </tr>
            </thead>
            <tbody>
                {% for row in totais %}
                <tr>
                    <td>{{ row[0] }}</td>
                    <td>R$ {{ "%.2f"|format(row[1]) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <div class="total-geral">
            Total Geral: R$ {{ "%.2f"|format(total_geral) }}
        </div>
    </div>
</body>
</html>
"""

        conn = conectar_banco()
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT * FROM {TABELA_USUARIO} WHERE login = %s AND senha = %s;", (username, password))
            usuario = cur.fetchone()
            
            if usuario:
                session['usuario'] = username
                return redirect(url_for('index'))
            else:
                mensagem = "Usuário ou senha inválidos!"
        except Exception as e:
            mensagem = f"Erro no login: {e}"
        finally:
            cur.close()
            conn.close()
# --- ROTAS DO FLASK ---

    return render_template_string(HTML_LOGIN, msg=mensagem)
@app.route('/login', methods=['GET', 'POST5' if False else 'POST'])
def login():
    error = None
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        if usuario and senha:
            session['usuario'] = usuario
            return redirect(url_for('caixa'))
        else:
            error = "Preencha todos os campos."
    return render_template_string(HTML_LOGIN, error=error)

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

@app.route('/buscar_produto')
def buscar_produto():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({"sucesso": False})
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if q.isdigit():
            cur.execute("SELECT id, nome, preco, estoque FROM produtos WHERE id = %s OR codigo_barras = %s", (int(q), q))
        else:
            cur.execute("SELECT id, nome, preco, estoque FROM produtos WHERE codigo_barras = %s", (q,))
        
        produto = cur.fetchone()
        if produto:
            return jsonify({
                "sucesso": True,
                "id": produto[0],
                "nome": produto[1],
                "preco": float(produto[2]),
                "estoque": produto[3]
            })
        else:
            return jsonify({"sucesso": False})
    except Exception as e:
        return jsonify({"sucesso": False, "erro": str(e)})
    finally:
        cur.close()
        conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
def caixa():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    mensagem = None
    
    msg = None
    if request.method == 'POST':
        identificador = request.form.get('identificador', '').strip()
        identificador = request.form.get('identificador')
        quantidade = int(request.form.get('quantidade', 1))
        forma_pagamento = request.form.get('forma_pagamento', 'Dinheiro')
        operador_atual = session.get('usuario', 'Desconhecido')

        conn = conectar_banco()
        forma_pagamento = request.form.get('forma_pagamento')
        
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            if identificador.isdigit():
                cur.execute(f"SELECT id, codigo_barra, nome, preco FROM {TABELA_PRODUTO} WHERE id = %s;", (int(identificador),))
                cur.execute("SELECT id, nome, preco, estoque FROM produtos WHERE id = %s OR codigo_barras = %s", (int(identificador), identificador))
            else:
                cur.execute(f"SELECT id, codigo_barra, nome, preco FROM {TABELA_PRODUTO} WHERE codigo_barra = %s;", (identificador,))
            
            produto = cur.fetchone()
            if not produto:
                raise Exception("Produto não encontrado no cadastro!")
                cur.execute("SELECT id, nome, preco, estoque FROM produtos WHERE codigo_barras = %s", (identificador,))

            prod_id = produto[0]
            codigo_barra = produto[1]
            nome_produto = produto[2]
            preco_unitario = float(produto[3])
            total_venda = preco_unitario * quantidade

            if identificador.isdigit():
                cur.execute(f"UPDATE {TABELA_PRODUTO} SET estoque = estoque - %s WHERE id = %s;", (quantidade, int(identificador)))
            prod = cur.fetchone()
            if prod:
                prod_id, nome, preco, estoque = prod
                if estoque >= quantidade:
                    novo_estoque = estoque - quantidade
                    cur.execute("UPDATE produtos SET estoque = %s WHERE id = %s", (novo_estoque, prod_id))
                    
                    total_venda = preco * quantidade
                    cur.execute("INSERT INTO vendas (produto_id, quantidade, valor_total, forma_pagamento, operador, data_venda) VALUES (%s, %s, %s, %s, %s, %s)",
                                (prod_id, quantidade, total_venda, forma_pagamento, session['usuario'], datetime.now()))
                    conn.commit()
                    msg = f"Venda realizada com sucesso! Total: R$ {total_venda:.2f}"
                else:
                    msg = "Estoque insuficiente para esta venda!"
            else:
                cur.execute(f"UPDATE {TABELA_PRODUTO} SET estoque = estoque - %s WHERE codigo_barra = %s;", (quantidade, identificador))
            
            # Insere na tabela de vendas com operador
            cur.execute(
                "INSERT INTO vendas (data_venda, total, forma_pagamento, produto, quantidade, operador) VALUES (NOW(), %s, %s, %s, %s, %s);",
                (total_venda, forma_pagamento, nome_produto, quantidade, operador_atual)
            )
            
            # Insere no log de auditoria (produtobkp) com operador
            cur.execute(
                "INSERT INTO produtobkp (produto_id, codigo_barra, nome, preco_praticado, quantidade_vendida, data_movimento, tipo_operacao, operador) VALUES (%s, %s, %s, %s, %s, NOW(), 'VENDA', %s);",
                (prod_id, codigo_barra, nome_produto, preco_unitario, quantidade, operador_atual)
            )

            conn.commit()
            mensagem = f"Venda realizada com sucesso! ({quantidade}x {nome_produto} - R$ {total_venda:.2f})"
                msg = "Produto não encontrado!"
        except Exception as e:
            conn.rollback()
            mensagem = f"Erro ao registrar venda: {e}"
            msg = f"Erro ao realizar venda: {e}"
        finally:
            cur.close()
            conn.close()

    return render_template_string(HTML_CAIXA, msg=mensagem, usuario=session['usuario'])

@app.route('/buscar_produto')
def buscar_produto():
    if 'usuario' not in session:
        return jsonify({'sucesso': False})
    q = request.args.get('q', '').strip()
    conn = conectar_banco()
    cur = conn.cursor()
    try:
        if q.isdigit():
            cur.execute(f"SELECT nome, preco, estoque FROM {TABELA_PRODUTO} WHERE id = %s;", (int(q),))
        else:
            cur.execute(f"SELECT nome, preco, estoque FROM {TABELA_PRODUTO} WHERE codigo_barra = %s;", (q,))
        produto = cur.fetchone()
        if produto:
            return jsonify({'sucesso': True, 'nome': produto[0], 'preco': float(produto[1]), 'estoque': produto[2]})
        return jsonify({'sucesso': False})
    finally:
        cur.close()
        conn.close()

@app.route('/api/produto/<identificador>')
def api_produto(identificador):
    if 'usuario' not in session:
        return jsonify({'encontrado': False})
    conn = conectar_banco()
    cur = conn.cursor()
    try:
        if identificador.isdigit():
            cur.execute(f"SELECT nome FROM {TABELA_PRODUTO} WHERE id = %s;", (int(identificador),))
        else:
            cur.execute(f"SELECT nome FROM {TABELA_PRODUTO} WHERE codigo_barra = %s;", (identificador,))
        produto = cur.fetchone()
        return jsonify({'encontrado': bool(produto), 'nome': produto[0] if produto else ""})
    finally:
        cur.close()
        conn.close()
    return render_template_string(HTML_CAIXA, usuario=session['usuario'], msg=msg)

@app.route('/estoque/entrada', methods=['GET', 'POST'])
def entrada_estoque():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    mensagem = None
    
    msg = None
    if request.method == 'POST':
        identificador = request.form.get('identificador', '').strip()
        quantidade = int(request.form.get('quantidade', 0))
        operador_atual = session.get('usuario', 'Desconhecido')

        conn = conectar_banco()
        identificador = request.form.get('identificador')
        quantidade = int(request.form.get('quantidade', 1))
        
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            if identificador.isdigit():
                cur.execute(f"SELECT id, codigo_barra, nome, preco FROM {TABELA_PRODUTO} WHERE id = %s;", (int(identificador),))
                cur.execute("SELECT id, estoque FROM produtos WHERE id = %s OR codigo_barras = %s", (int(identificador), identificador))
            else:
                cur.execute(f"SELECT id, codigo_barra, nome, preco FROM {TABELA_PRODUTO} WHERE codigo_barra = %s;", (identificador,))
                cur.execute("SELECT id, estoque FROM produtos WHERE codigo_barras = %s", (identificador,))

            produto = cur.fetchone()
            if not produto:
                raise Exception("Produto não encontrado no cadastro!")
            
            prod_id = produto[0]
            codigo_barra = produto[1]
            nome_produto = produto[2]
            preco_unitario = float(produto[3])

            if identificador.isdigit():
                cur.execute(f"UPDATE {TABELA_PRODUTO} SET estoque = estoque + %s WHERE id = %s;", (quantidade, int(identificador)))
            prod = cur.fetchone()
            if prod:
                prod_id, estoque_atual = prod
                novo_estoque = estoque_atual + quantidade
                cur.execute("UPDATE produtos SET estoque = %s WHERE id = %s", (novo_estoque, prod_id))
                conn.commit()
                msg = f"Estoque atualizado com sucesso! Novo estoque: {novo_estoque}"
            else:
                cur.execute(f"UPDATE {TABELA_PRODUTO} SET estoque = estoque + %s WHERE codigo_barra = %s;", (quantidade, identificador))
            
            cur.execute(
                "INSERT INTO produtobkp (produto_id, codigo_barra, nome, preco_praticado, quantidade_vendida, data_movimento, tipo_operacao, operador) VALUES (%s, %s, %s, %s, %s, NOW(), 'ENTRADA', %s);",
                (prod_id, codigo_barra, nome_produto, preco_unitario, quantidade, operador_atual)
            )

            conn.commit()
            mensagem = f"Estoque atualizado com sucesso! ({quantidade:+d} unidades de {nome_produto})"
                msg = "Produto não encontrado!"
        except Exception as e:
            conn.rollback()
            mensagem = f"Erro ao atualizar estoque: {e}"
            msg = f"Erro ao atualizar estoque: {e}"
        finally:
            cur.close()
            conn.close()
    return render_template_string(HTML_ESTOQUE, msg=mensagem, usuario=session['usuario'])

    return render_template_string(HTML_ESTOQUE, usuario=session['usuario'], msg=msg)

@app.route('/relatorio/fechamento')
def fechamento_caixa():
def fechamento():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conn = conectar_banco()
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COALESCE(SUM(total), 0), COUNT(*) FROM vendas WHERE DATE(data_venda) = CURRENT_DATE;")
        cur.execute("SELECT forma_pagamento, SUM(valor_total) FROM vendas GROUP BY forma_pagamento")
        totais = cur.fetchall()
        
        cur.execute("SELECT SUM(valor_total) FROM vendas")
        res_geral = cur.fetchone()
        total_faturado = res_geral[0]
        total_vendas = res_geral[1]

        cur.execute("SELECT forma_pagamento, COALESCE(SUM(total), 0) FROM vendas WHERE DATE(data_venda) = CURRENT_DATE GROUP BY forma_pagamento;")
        por_pagamento = cur.fetchall()

        cur.execute("SELECT operador, COALESCE(SUM(total), 0), COUNT(*) FROM vendas WHERE DATE(data_venda) = CURRENT_DATE GROUP BY operador;")
        por_operador = cur.fetchall()
        total_geral = res_geral[0] if res_geral and res_geral[0] else 0.0
    finally:
        cur.close()
        conn.close()

    return render_template_string(HTML_FECHAMENTO, 
                                 faturado=total_faturado, 
                                 vendas=total_vendas, 
                                 pagamentos=por_pagamento, 
                                 operadores=por_operador,
                                 usuario=session['usuario'])
    return render_template_string(HTML_FECHAMENTO, usuario=session['usuario'], totais=totais, total_geral=total_geral)

if __name__ == '__main__':
    app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
