from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import psycopg2
import os

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

def conectar_banco():
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

TABELA_USUARIO = "usuario"
TABELA_PRODUTO = "produto"

# --- TEMPLATES HTML ---

HTML_LOGIN = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
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
        button:hover { background: #2563eb; }
        .error { color: #f87171; font-size: 14px; text-align: center; margin-top: 12px; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>Grupo Yamasaki</h2>
        <form method="POST">
            <div class="form-group">
                <label>Usuário</label>
                <input type="text" name="username" required autofocus>
            </div>
            <div class="form-group">
                <label>Senha</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit">Entrar no Sistema</button>
        </form>
        {% if msg %}
            <div class="error">{{ msg }}</div>
        {% endif %}
    </div>
</body>
</html>
"""

HTML_CAIXA = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Grupo Yamasaki - PDV Caixa</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #1e293b; padding: 15px 25px; border-radius: 8px; margin-bottom: 20px; border-bottom: 3px solid #3b82f6; }
        .nav-links a { color: #60a5fa; text-decoration: none; margin-left: 15px; font-weight: 600; }
        .nav-links a:hover { text-decoration: underline; }
        .container { max-width: 800px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        h1 { color: #60a5fa; margin-top: 0; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #94a3b8; }
        input, select { width: 100%; padding: 12px; border-radius: 6px; border: 1px solid #334155; background: #0f172a; color: #fff; box-sizing: border-box; font-size: 16px; }
        button { background: #10b981; color: white; border: none; padding: 14px; width: 100%; font-size: 16px; font-weight: bold; border-radius: 6px; cursor: pointer; transition: background 0.2s; }
        button:hover { background: #059669; }
        .msg { padding: 12px; background: #065f46; color: #d1fae5; border-radius: 6px; margin-bottom: 20px; text-align: center; font-weight: bold; }
        #info_produto { color: #fbbf24; font-size: 14px; margin-top: 5px; }
    </style>
  <script>
        function buscarProduto() {
            let id = document.getElementById('identificador').value.trim();
            let infoDiv = document.getElementById('info_produto');
            if (id.length > 0) {
                fetch('/buscar_produto?q=' + encodeURIComponent(id))
                    .then(response => response.json())
                    .then(data => {
                        if (data.sucesso) {
                            infoDiv.innerHTML = "<strong>Produto:</strong> " + data.nome + " | <strong>Preço:</strong> R$ " + data.preco.toFixed(2) + " | <strong>Estoque:</strong> " + data.estoque;
                        } else {
                            infoDiv.innerText = "Aguardando busca / Produto não encontrado";
                        }
                    });
            } else {
                infoDiv.innerText = "";
            }
        }
    </script>
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
        <h1>Frente de Caixa - PDV</h1>
        {% if msg %}
            <div class="msg">{{ msg }}</div>
        {% endif %}
        <form method="POST">
            <div class="form-group">
                <label>Código de Barras ou ID do Produto</label>
                <input type="text" id="identificador" name="identificador" onkeyup="buscarProduto()" required autofocus>
                <div id="info_produto"></div>
            </div>
            <div class="form-group">
                <label>Quantidade</label>
                <input type="number" name="quantidade" value="1" min="1" required>
            </div>
            <div class="form-group">
                <label>Forma de Pagamento</label>
                <select name="forma_pagamento">
                    <option value="Dinheiro">Dinheiro</option>
                    <option value="Pix">Pix</option>
                    <option value="Cartão de Crédito">Cartão de Crédito</option>
                    <option value="Cartão de Débito">Cartão de Débito</option>
                </select>
            </div>
            <button type="submit">Finalizar Venda</button>
        </form>
    </div>
</body>
</html>
"""

HTML_ESTOQUE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Grupo Yamasaki - Entrada de Estoque</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #1e293b; padding: 15px 25px; border-radius: 8px; margin-bottom: 20px; border-bottom: 3px solid #3b82f6; }
        .nav-links a { color: #60a5fa; text-decoration: none; margin-left: 15px; font-weight: 600; }
        .container { max-width: 800px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        h1 { color: #60a5fa; margin-top: 0; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #94a3b8; }
        input { width: 100%; padding: 12px; border-radius: 6px; border: 1px solid #334155; background: #0f172a; color: #fff; box-sizing: border-box; font-size: 16px; }
        button { background: #3b82f6; color: white; border: none; padding: 14px; width: 100%; font-size: 16px; font-weight: bold; border-radius: 6px; cursor: pointer; }
        button:hover { background: #2563eb; }
        .msg { padding: 12px; background: #1e3a8a; color: #bfdbfe; border-radius: 6px; margin-bottom: 20px; text-align: center; font-weight: bold; }
        #info_produto { color: #fbbf24; font-size: 14px; margin-top: 5px; }
    </style>
    <script>
        function buscarEstoque() {
            let id = document.getElementById('identificador_estoque').value.trim();
            let infoDiv = document.getElementById('info_produto');
            if (id.length > 0) {
                fetch('/buscar_produto?q=' + encodeURIComponent(id))
                    .then(response => response.json())
                    .then(data => {
                        if (data.sucesso) {
                            infoDiv.innerHTML = "<strong>Produto:</strong> " + data.nome + " | <strong>Estoque Atual:</strong> " + data.estoque;
                        } else {
                            infoDiv.innerText = "Aguardando busca / Produto não encontrado";
                        }
                    });
            } else {
                infoDiv.innerText = "";
            }
        }
    </script>
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
        <h1>Entrada de Estoque</h1>
        {% if msg %}
            <div class="msg">{{ msg }}</div>
        {% endif %}
        <form method="POST">
            <div class="form-group">
                <label>Código de Barras ou ID do Produto</label>
                <input type="text" id="identificador_estoque" name="identificador" onkeyup="buscarEstoque()" required autofocus>
                <div id="info_produto"></div>
            </div>
            <div class="form-group">
                <label>Quantidade a Adicionar</label>
                <input type="number" name="quantidade" value="1" min="1" required>
            </div>
            <button type="submit">Confirmar Entrada</button>
        </form>
    </div>
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

    return render_template_string(HTML_LOGIN, msg=mensagem)

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    mensagem = None
    if request.method == 'POST':
        identificador = request.form.get('identificador', '').strip()
        quantidade = int(request.form.get('quantidade', 1))
        forma_pagamento = request.form.get('forma_pagamento', 'Dinheiro')
        operador_atual = session.get('usuario', 'Desconhecido')

        conn = conectar_banco()
        cur = conn.cursor()
        try:
            if identificador.isdigit():
                cur.execute(f"SELECT id, codigo_barra, nome, preco FROM {TABELA_PRODUTO} WHERE id = %s;", (int(identificador),))
            else:
                cur.execute(f"SELECT id, codigo_barra, nome, preco FROM {TABELA_PRODUTO} WHERE codigo_barra = %s;", (identificador,))
            
            produto = cur.fetchone()
            if not produto:
                raise Exception("Produto não encontrado no cadastro!")
            
            prod_id = produto[0]
            codigo_barra = produto[1]
            nome_produto = produto[2]
            preco_unitario = float(produto[3])
            total_venda = preco_unitario * quantidade

            if identificador.isdigit():
                cur.execute(f"UPDATE {TABELA_PRODUTO} SET estoque = estoque - %s WHERE id = %s;", (quantidade, int(identificador)))
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
        except Exception as e:
            conn.rollback()
            mensagem = f"Erro ao registrar venda: {e}"
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

@app.route('/estoque/entrada', methods=['GET', 'POST'])
def entrada_estoque():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    mensagem = None
    if request.method == 'POST':
        identificador = request.form.get('identificador', '').strip()
        quantidade = int(request.form.get('quantidade', 0))
        operador_atual = session.get('usuario', 'Desconhecido')

        conn = conectar_banco()
        cur = conn.cursor()
        try:
            if identificador.isdigit():
                cur.execute(f"SELECT id, codigo_barra, nome, preco FROM {TABELA_PRODUTO} WHERE id = %s;", (int(identificador),))
            else:
                cur.execute(f"SELECT id, codigo_barra, nome, preco FROM {TABELA_PRODUTO} WHERE codigo_barra = %s;", (identificador,))
            
            produto = cur.fetchone()
            if not produto:
                raise Exception("Produto não encontrado no cadastro!")
            
            prod_id = produto[0]
            codigo_barra = produto[1]
            nome_produto = produto[2]
            preco_unitario = float(produto[3])

            if identificador.isdigit():
                cur.execute(f"UPDATE {TABELA_PRODUTO} SET estoque = estoque + %s WHERE id = %s;", (quantidade, int(identificador)))
            else:
                cur.execute(f"UPDATE {TABELA_PRODUTO} SET estoque = estoque + %s WHERE codigo_barra = %s;", (quantidade, identificador))
            
            cur.execute(
                "INSERT INTO produtobkp (produto_id, codigo_barra, nome, preco_praticado, quantidade_vendida, data_movimento, tipo_operacao, operador) VALUES (%s, %s, %s, %s, %s, NOW(), 'ENTRADA', %s);",
                (prod_id, codigo_barra, nome_produto, preco_unitario, quantidade, operador_atual)
            )

            conn.commit()
            mensagem = f"Estoque atualizado com sucesso! ({quantidade:+d} unidades de {nome_produto})"
        except Exception as e:
            conn.rollback()
            mensagem = f"Erro ao atualizar estoque: {e}"
        finally:
            cur.close()
            conn.close()
    return render_template_string(HTML_ESTOQUE, msg=mensagem, usuario=session['usuario'])

@app.route('/relatorio/fechamento')
def fechamento_caixa():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conn = conectar_banco()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COALESCE(SUM(total), 0), COUNT(*) FROM vendas WHERE DATE(data_venda) = CURRENT_DATE;")
        res_geral = cur.fetchone()
        total_faturado = res_geral[0]
        total_vendas = res_geral[1]

        cur.execute("SELECT forma_pagamento, COALESCE(SUM(total), 0) FROM vendas WHERE DATE(data_venda) = CURRENT_DATE GROUP BY forma_pagamento;")
        por_pagamento = cur.fetchall()

        cur.execute("SELECT operador, COALESCE(SUM(total), 0), COUNT(*) FROM vendas WHERE DATE(data_venda) = CURRENT_DATE GROUP BY operador;")
        por_operador = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    return render_template_string(HTML_FECHAMENTO, 
                                 faturado=total_faturado, 
                                 vendas=total_vendas, 
                                 pagamentos=por_pagamento, 
                                 operadores=por_operador,
                                 usuario=session['usuario'])

if __name__ == '__main__':
    app.run(debug=True)
