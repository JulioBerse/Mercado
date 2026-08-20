from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'segredo_grupo_yamasaki'

def get_db_connection():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

HTML_CAIXA = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>PDV - Grupo Yamasaki</title>
    <style>
        body { background: #0f172a; color: white; font-family: sans-serif; padding: 20px; }
        .container { max-width: 600px; margin: auto; background: #1e293b; padding: 25px; border-radius: 10px; }
        input, select { width: 100%; padding: 12px; margin: 8px 0; border-radius: 5px; border: 1px solid #334; background: #0f172a; color: white; }
        .total-box { font-size: 28px; color: #10b981; font-weight: bold; margin: 15px 0; text-align: center; }
        #info_produto { color: #fbbf24; font-size: 14px; margin-bottom: 10px; min-height: 20px; }
        #qr_box { display: none; text-align: center; border: 1px dashed #3b82f6; padding: 15px; margin-top: 10px; }
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
                        document.getElementById('info_produto').innerText = data.nome + " | R$ " + data.preco.toFixed(2);
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
    <div class="container">
        <h1>PDV - Grupo Yamasaki</h1>
        <form method="POST">
            <input type="text" id="identificador" name="identificador" placeholder="Código ou ID" onblur="buscarProduto()" required>
            <div id="info_produto"></div>
            <input type="number" id="quantidade" name="quantidade" value="1" min="1" oninput="calcularTotal()" required>
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
            <button type="submit" style="width: 100%; padding: 15px; background: #10b981; border: none; color: white; border-radius: 5px; cursor: pointer;">FINALIZAR</button>
        </form>
    </div>
</body>
</html>
"""

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
            cur.execute("INSERT INTO vendas (produto_id, quantidade, valor_total, forma_pagamento, operador, data_venda) VALUES (%s, %s, %s, %s, 'admin', %s)",
                        (prod[0], qtd, total, forma, datetime.now()))
            conn.commit()
        cur.close(); conn.close()
    return render_template_string(HTML_CAIXA)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
