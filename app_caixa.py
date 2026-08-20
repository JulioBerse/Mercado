from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'segredo_grupo_yamasaki'

def get_db_connection():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

# --- TEMPLATE COMPLETO COM DESIGN RESTAURADO ---
HTML_CAIXA = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Grupo Yamasaki - PDV Caixa</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #1e293b; padding: 15px 25px; border-radius: 8px; margin-bottom: 20px; border-bottom: 3px solid #3b82f6; }
        .nav-links a { color: #60a5fa; text-decoration: none; margin-left: 15px; font-weight: 600; }
        .container { max-width: 900px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px; display: flex; gap: 30px; }
        .form-section { flex: 1; }
        .qr-section { width: 260px; background: #0f172a; padding: 20px; border-radius: 8px; text-align: center; display: none; border: 1px dashed #3b82f6; }
        .qr-section img { width: 100%; background: #fff; padding: 8px; border-radius: 4px; }
        input, select { width: 100%; padding: 12px; margin: 10px 0; border-radius: 6px; border: 1px solid #334155; background: #0f172a; color: #fff; }
        button { background: #10b981; color: white; border: none; padding: 14px; width: 100%; font-size: 16px; font-weight: bold; border-radius: 6px; cursor: pointer; }
        .total-box { background: #0f172a; padding: 15px; border-radius: 6px; border: 1px solid #334155; text-align: center; }
        .total-box span { font-size: 24px; font-weight: bold; color: #34d399; }
        #info_produto { color: #fbbf24; font-size: 14px; margin-bottom: 10px; }
    </style>
    <script>
        let precoGlobal = 0;
        function buscarProduto() {
            let id = document.getElementById('identificador').value;
            if(!id) return;
            fetch('/buscar_produto?q=' + encodeURIComponent(id))
                .then(r => r.json())
                .then(data => {
                    if (data.sucesso) {
                        precoGlobal = data.preco;
                        document.getElementById('info_produto').innerText = "Produto: " + data.nome + " | Preço: R$ " + data.preco.toFixed(2);
                        calcularTotal();
                    } else {
                        document.getElementById('info_produto').innerText = "Produto não encontrado!";
                    }
                });
        }
        function calcularTotal() {
            let qtd = document.getElementById('quantidade').value || 1;
            document.getElementById('total_display').innerText = "R$ " + (precoGlobal * qtd).toFixed(2);
        }
        function checkPix(val) {
            document.getElementById('qr_box').style.display = (val === 'Pix') ? 'block' : 'none';
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
            <a href="/logout">Sair</a>
        </div>
    </div>
    <div class="container">
        <div class="form-section">
            <h1>Frente de Caixa</h1>
            <form method="POST">
                <input type="text" id="identificador" name="identificador" placeholder="Código ou ID" onblur="buscarProduto()" required autofocus>
                <div id="info_produto"></div>
                <input type="number" id="quantidade" name="quantidade" value="1" min="1" oninput="calcularTotal()" required>
                <div class="total-box"><label>Total:</label> <span id="total_display">R$ 0,00</span></div>
                <select name="forma_pagamento" onchange="checkPix(this.value)">
                    <option value="Dinheiro">Dinheiro</option>
                    <option value="Pix">Pix</option>
                    <option value="Cartão">Cartão</option>
                </select>
                <button type="submit">FINALIZAR VENDA</button>
            </form>
        </div>
        <div class="qr-section" id="qr_box">
            <h3>Pagamento Pix</h3>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=py9dm.mt@gmail.com">
            <p>py9dm.mt@gmail.com</p>
        </div>
    </div>
</body>
</html>
"""

# --- ROTAS ---
@app.route('/buscar_produto')
def buscar_produto():
    q = request.args.get('q', '')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT nome, preco FROM produtos WHERE id::text = %s OR codigo_barras = %s", (q, q))
    res = cur.fetchone()
    cur.close(); conn.close()
    if res:
        return jsonify({"sucesso": True, "nome": res[0], "preco": float(res[1])})
    return jsonify({"sucesso": False})

@app.route('/', methods=['GET', 'POST'])
def caixa():
    usuario = session.get('usuario', 'Visitante')
    if request.method == 'POST':
        id_prod = request.form['identificador']
        qtd = int(request.form['quantidade'])
        forma = request.form['forma_pagamento']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, preco FROM produtos WHERE id::text = %s OR codigo_barras = %s", (id_prod, id_prod))
        prod = cur.fetchone()
        if prod:
            total = float(prod[1]) * qtd
            cur.execute("UPDATE produtos SET estoque = estoque - %s WHERE id = %s", (qtd, prod[0]))
            cur.execute("INSERT INTO vendas (produto_id, quantidade, valor_total, forma_pagamento, operador, data_venda) VALUES (%s, %s, %s, %s, %s, %s)",
                        (prod[0], qtd, total, forma, usuario, datetime.now()))
            conn.commit()
        cur.close(); conn.close()
    return render_template_string(HTML_CAIXA, usuario=usuario)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
