
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'segredo_grupo_yamasaki'

def get_db_connection():
    # Certifique-se que sua DATABASE_URL está configurada corretamente no Render
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

# --- TEMPLATES HTML ---

HTML_LOGIN = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Login - Grupo Yamasaki</title>
    <style>
        body { background: #0f172a; color: white; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #1e293b; padding: 30px; border-radius: 10px; width: 300px; }
        input { width: 100%; padding: 10px; margin: 10px 0; border-radius: 5px; border: none; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background: #3b82f6; color: white; border: none; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Login</h2>
        <form method="POST">
            <input type="text" name="usuario" placeholder="Usuário" required>
            <input type="password" name="senha" placeholder="Senha" required>
            <button type="submit">Entrar</button>
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
    <title>PDV - Grupo Yamasaki</title>
    <style>
        body { background: #0f172a; color: white; font-family: sans-serif; padding: 20px; }
        .container { max-width: 800px; margin: auto; background: #1e293b; padding: 20px; border-radius: 10px; }
        input, select { width: 100%; padding: 10px; margin: 10px 0; border-radius: 5px; border: 1px solid #334; background: #0f172a; color: white; }
        .total-box { font-size: 24px; color: #10b981; font-weight: bold; margin: 10px 0; }
        #qr_box { display: none; margin-top: 20px; text-align: center; border: 1px dashed #3b82f6; padding: 10px; }
    </style>
    <script>
        function buscarProduto() {
            let val = document.getElementById('identificador').value;
            fetch('/buscar_produto?q=' + encodeURIComponent(val))
                .then(r => r.json())
                .then(data => {
                    if (data.sucesso) {
                        document.getElementById('info_prod').innerText = data.nome + " | R$ " + data.preco.toFixed(2);
                        window.precoAtual = data.preco;
                        calcularTotal();
                    } else {
                        document.getElementById('info_prod').innerText = "Produto não encontrado";
                    }
                });
        }
        function calcularTotal() {
            let qtd = document.getElementById('quantidade').value || 1;
            document.getElementById('total_display').innerText = "R$ " + (window.precoAtual * qtd).toFixed(2);
        }
        function checkPix(val) {
            document.getElementById('qr_box').style.display = (val === 'Pix') ? 'block' : 'none';
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>PDV - Grupo Yamasaki</h1>
        <form method="POST">
            <input type="text" id="identificador" name="identificador" placeholder="Código ou ID" onblur="buscarProduto()" required>
            <div id="info_prod" style="color: #fbbf24;"></div>
            <input type="number" id="quantidade" name="quantidade" value="1" oninput="calcularTotal()">
            <div class="total-box" id="total_display">R$ 0,00</div>
            <select name="forma_pagamento" onchange="checkPix(this.value)">
                <option value="Dinheiro">Dinheiro</option>
                <option value="Pix">Pix</option>
                <option value="Cartão">Cartão</option>
            </select>
            <div id="qr_box">
                <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=py9dm.mt@gmail.com" width="150">
                <p>Chave: py9dm.mt@gmail.com</p>
            </div>
            <button type="submit" style="width: 100%; padding: 15px; background: #10b981; border: none; color: white; margin-top: 10px;">FINALIZAR</button>
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
    <title>Estoque - Grupo Yamasaki</title>
    <style>
        body { background: #0f172a; color: white; font-family: sans-serif; padding: 20px; }
        .container { max-width: 600px; margin: auto; background: #1e293b; padding: 20px; border-radius: 10px; }
        input { width: 100%; padding: 10px; margin: 10px 0; border-radius: 5px; }
        button { width: 100%; padding: 10px; background: #3b82f6; border: none; color: white; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Entrada de Estoque</h1>
        <form method="POST">
            <input type="text" name="identificador" placeholder="ID ou Código do Produto" required>
            <input type="number" name="quantidade" placeholder="Quantidade" required>
            <button type="submit">Adicionar</button>
        </form>
    </div>
</body>
</html>
"""

# --- ROTAS ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['usuario'] = request.form['usuario']
        return redirect(url_for('caixa'))
    return render_template_string(HTML_LOGIN)

@app.route('/buscar_produto')
def buscar_produto():
    q = request.args.get('q')
    conn = get_db_connection()
    cur = conn.cursor()
    # Busca tanto por ID (numérico) quanto por código de barras (string)
    cur.execute("SELECT nome, preco FROM produtos WHERE CAST(id AS TEXT) = %s OR codigo_barras = %s", (q, q))
    res = cur.fetchone()
    cur.close(); conn.close()
    if res:
        return jsonify({"sucesso": True, "nome": res[0], "preco": float(res[1])})
    return jsonify({"sucesso": False})

@app.route('/', methods=['GET', 'POST'])
def caixa():
    if 'usuario' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        id_prod = request.form['identificador']
        qtd = int(request.form['quantidade'])
        conn = get_db_connection()
        cur = conn.cursor()
        # Atualiza estoque e registra venda
        cur.execute("UPDATE produtos SET estoque = estoque - %s WHERE CAST(id AS TEXT) = %s OR codigo_barras = %s", (qtd, id_prod, id_prod))
        cur.execute("INSERT INTO vendas (produto_id, quantidade, valor_total, forma_pagamento, operador, data_venda) VALUES ((SELECT id FROM produtos WHERE CAST(id AS TEXT) = %s OR codigo_barras = %s), %s, 0, %s, %s, %s)",
                    (id_prod, id_prod, qtd, request.form['forma_pagamento'], session['usuario'], datetime.now()))
        conn.commit()
        cur.close(); conn.close()
    return render_template_string(HTML_CAIXA)

@app.route('/estoque/entrada', methods=['GET', 'POST'])
def entrada_estoque():
    if request.method == 'POST':
        id_prod = request.form['identificador']
        qtd = int(request.form['quantidade'])
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE produtos SET estoque = estoque + %s WHERE CAST(id AS TEXT) = %s OR codigo_barras = %s", (qtd, id_prod, id_prod))
        conn.commit()
        cur.close(); conn.close()
    return render_template_string(HTML_ESTOQUE)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
