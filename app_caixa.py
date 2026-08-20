from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'segredo_grupo_yamasaki'

def get_db_connection():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

# --- TEMPLATES HTML ---

HTML_LOGIN = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Grupo Yamasaki - Login</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-card { background: #1e293b; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); width: 100%; max-width: 400px; border-top: 4px solid #3b82f6; }
        h2 { color: #60a5fa; text-align: center; margin-top: 0; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #94a3b8; }
        input { width: 100%; padding: 12px; border-radius: 6px; border: 1px solid #334155; background: #0f172a; color: #fff; box-sizing: border-box; font-size: 16px; }
        button { background: #3b82f6; color: white; border: none; padding: 14px; width: 100%; font-size: 16px; font-weight: bold; border-radius: 6px; cursor: pointer; transition: background 0.2s; }
        button:hover { background: #2563eb; }
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
                <label>Usuário / Operador</label>
                <input type="text" name="usuario" required autofocus>
            </div>
            <div class="form-group">
                <label>Senha</label>
                <input type="password" name="senha" required>
            </div>
            <button type="submit">Entrar no Sistema</button>
        </form>
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
        .container { max-width: 900px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); display: flex; gap: 30px; }
        .form-section { flex: 1; }
        .qr-section { width: 260px; background: #0f172a; padding: 20px; border-radius: 8px; text-align: center; display: none; border: 1px dashed #3b82f6; align-self: flex-start; }
        .qr-section img { width: 100%; max-height: 200px; object-fit: contain; border-radius: 4px; margin-top: 10px; background: #fff; padding: 8px; }
        h1 { color: #60a5fa; margin-top: 0; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #94a3b8; }
        input, select { width: 100%; padding: 12px; border-radius: 6px; border: 1px solid #334155; background: #0f172a; color: #fff; box-sizing: border-box; font-size: 16px; }
        button { background: #10b981; color: white; border: none; padding: 14px; width: 100%; font-size: 16px; font-weight: bold; border-radius: 6px; cursor: pointer; transition: background 0.2s; }
        button:hover { background: #059669; }
        .msg { padding: 12px; background: #065f46; color: #d1fae5; border-radius: 6px; margin-bottom: 20px; text-align: center; font-weight: bold; }
        #info_produto { color: #fbbf24; font-size: 14px; margin-top: 5px; }
        .total-box { background: #0f172a; padding: 15px; border-radius: 6px; border: 1px solid #334155; margin-bottom: 20px; text-align: center; }
        .total-box span { font-size: 24px; font-weight: bold; color: #34d399; }
    </style>
    <script>
        let precoUnitarioGlobal = 0;

        function buscarProduto() {
            let id = document.getElementById('identificador').value.trim();
            let infoDiv = document.getElementById('info_produto');
            if (id.length > 0) {
                fetch('/buscar_produto?q=' + encodeURIComponent(id))
                    .then(response => response.json())
                    .then(data => {
                        if (data.sucesso) {
                            precoUnitarioGlobal = data.preco;
                            infoDiv.innerHTML = "<strong>Produto:</strong> " + data.nome + " | <strong>Preço Unit.:</strong> R$ " + data.preco.toFixed(2) + " | <strong>Estoque:</strong> " + data.estoque;
                            calcularTotal();
                        } else {
                            precoUnitarioGlobal = 0;
                            infoDiv.innerText = "Aguardando busca / Produto não encontrado";
                            document.getElementById('valor_total_visor').innerText = "R$ 0,00";
                        }
                    });
            } else {
                precoUnitarioGlobal = 0;
                infoDiv.innerText = "";
                document.getElementById('valor_total_visor').innerText = "R$ 0,00";
            }
        }

        function calcularTotal() {
            let quantidade = parseInt(document.getElementById('quantidade').value) || 1;
            let total = precoUnitarioGlobal * quantidade;
            document.getElementById('valor_total_visor').innerText = "R$ " + total.toFixed(2);
        }

        function verificarPagamento() {
            let forma = document.getElementById('forma_pagamento').value;
            let qrBox = document.getElementById('qr_box');
            if (forma === 'Pix') {
                qrBox.style.display = 'block';
            } else {
                qrBox.style.display = 'none';
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
        <div class="form-section">
            <h1>Frente de Caixa - PDV</h1>
            {% if msg %}
                <div class="msg">{{ msg }}</div>
            {% endif %}
            <form method="POST">
                <div class="form-group">
                    <label>Código de Barras ou ID do Produto</label>
                    <input type="text" id="identificador" name="identificador" oninput="buscarProduto()" onblur="buscarProduto()" required autofocus>
                    <div id="info_produto"></div>
                </div>
                <div class="form-group">
                    <label>Quantidade</label>
                    <input type="number" id="quantidade" name="quantidade" value="1" min="1" oninput="calcularTotal()" required>
                </div>
                <div class="total-box">
                    <label style="margin-bottom: 5px; color: #94a3b8;">Valor Total da Venda</label>
                    <span id="valor_total_visor">R$ 0,00</span>
                </div>
                <div class="form-group">
                    <label>Forma de Pagamento</label>
                    <select name="forma_pagamento" id="forma_pagamento" onchange="verificarPagamento()">
                        <option value="Dinheiro">Dinheiro</option>
                        <option value="Pix">Pix</option>
                        <option value="Cartão de Crédito">Cartão de Crédito</option>
                        <option value="Cartão de Débito">Cartão de Débito</option>
                    </select>
                </div>
                <button type="submit">Finalizar Venda</button>
            </form>
        </div>

        <div class="qr-section" id="qr_box">
            <h3 style="color: #60a5fa; margin-top: 0; font-size: 16px;">Pagamento via Pix</h3>
            <p style="font-size: 13px; color: #94a3b8;">Escaneie a chave:</p>
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
                <input type="text" id="identificador_estoque" name="identificador" oninput="buscarEstoque()" onblur="buscarEstoque()" required autofocus>
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

# --- ROTAS DO FLASK ---

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
def caixa():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    msg = None
    if request.method == 'POST':
        identificador = request.form.get('identificador')
        quantidade = int(request.form.get('quantidade', 1))
        forma_pagamento = request.form.get('forma_pagamento')
        
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            if identificador.isdigit():
                cur.execute("SELECT id, nome, preco, estoque FROM produtos WHERE id = %s OR codigo_barras = %s", (int(identificador), identificador))
            else:
                cur.execute("SELECT id, nome, preco, estoque FROM produtos WHERE codigo_barras = %s", (identificador,))
            
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
                msg = "Produto não encontrado!"
        except Exception as e:
            conn.rollback()
            msg = f"Erro ao realizar venda: {e}"
        finally:
            cur.close()
            conn.close()

    return render_template_string(HTML_CAIXA, usuario=session['usuario'], msg=msg)

@app.route('/estoque/entrada', methods=['GET', 'POST'])
def entrada_estoque():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    msg = None
    if request.method == 'POST':
        identificador = request.form.get('identificador')
        quantidade = int(request.form.get('quantidade', 1))
        
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            if identificador.isdigit():
                cur.execute("SELECT id, estoque FROM produtos WHERE id = %s OR codigo_barras = %s", (int(identificador), identificador))
            else:
                cur.execute("SELECT id, estoque FROM produtos WHERE codigo_barras = %s", (identificador,))
            
            prod = cur.fetchone()
            if prod:
                prod_id, estoque_atual = prod
                novo_estoque = estoque_atual + quantidade
                cur.execute("UPDATE produtos SET estoque = %s WHERE id = %s", (novo_estoque, prod_id))
                conn.commit()
                msg = f"Estoque atualizado com sucesso! Novo estoque: {novo_estoque}"
            else:
                msg = "Produto não encontrado!"
        except Exception as e:
            conn.rollback()
            msg = f"Erro ao atualizar estoque: {e}"
        finally:
            cur.close()
            conn.close()

    return render_template_string(HTML_ESTOQUE, usuario=session['usuario'], msg=msg)

@app.route('/relatorio/fechamento')
def fechamento():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT forma_pagamento, SUM(valor_total) FROM vendas GROUP BY forma_pagamento")
        totais = cur.fetchall()
        
        cur.execute("SELECT SUM(valor_total) FROM vendas")
        res_geral = cur.fetchone()
        total_geral = res_geral[0] if res_geral and res_geral[0] else 0.0
    finally:
        cur.close()
        conn.close()

    return render_template_string(HTML_FECHAMENTO, usuario=session['usuario'], totais=totais, total_geral=total_geral)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
