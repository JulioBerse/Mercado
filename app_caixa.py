import os
import psycopg2
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# CONFIGURAÇÃO CORRETA: Tabela no singular
TABELA_PRODUTO = "produto"

def conectar_banco():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url)

HTML_CAIXA = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Berse Supermercados - PDV</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 30px; background-color: #f0f2f5; display: flex; justify-content: center; }
        .card { background: #ffffff; width: 100%; max-width: 600px; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        h1 { color: #1a1a1a; margin-top: 0; font-size: 24px; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        label { display: block; margin-top: 15px; font-weight: 600; color: #444; }
        input, select { width: 100%; padding: 12px; margin-top: 6px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 15px; background-color: #fff; }
        input:focus, select:focus { border-color: #007bff; outline: none; }
        button { margin-top: 25px; width: 100%; padding: 12px; background-color: #007bff; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background 0.2s; }
        button:hover { background-color: #0056b3; }
        .info-box { background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 15px; margin-top: 15px; }
        .info-row { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 16px; }
        .info-row strong { color: #333; }
        .total-box { font-size: 20px; color: #28a745; border-top: 2px solid #28a745; padding-top: 10px; margin-top: 10px; }
        .msg { margin-top: 20px; padding: 12px; border-radius: 6px; font-weight: bold; text-align: center; }
        .msg-sucesso { background: #e8f5e9; color: #2e7d32; }
        .msg-erro { background: #ffebee; color: #c62828; }
        .nav-link { display: inline-block; margin-bottom: 15px; color: #28a745; text-decoration: none; font-weight: bold; }
        .brand-header { text-align: center; margin-bottom: 20px; }
        .brand-header h2 { color: #007bff; margin: 0; font-size: 22px; font-weight: bold; letter-spacing: 1px; }
        .footer-system { text-align: center; margin-top: 30px; font-size: 12px; color: #888; border-top: 1px solid #e9ecef; padding-top: 15px; }
    </style>
</head>
<body>
    <div class="card">
        <div class="brand-header">
            <h2>🏪 GRUPO YAMASAKI</h2>
        </div>
        <a class="nav-link" href="/estoque/entrada">📦 Ir para Entrada de Estoque →</a>
        <h1>🛒 Frente de Caixa (PDV)</h1>

        <form id="formVenda" method="POST" action="/">
            <label for="identificador">ID ou Código de Barras do Produto:</label>
            <input type="text" id="identificador" name="identificador" placeholder="Digite o ID/Código e pressione TAB ou ENTER" required autofocus onblur="buscarProduto()" onkeydown="tratarTeclaIdentificador(event)">
            
            <label for="forma_pagamento">Forma de Pagamento:</label>
            <select name="forma_pagamento" id="forma_pagamento">
                <option value="Dinheiro">Dinheiro</option>
                <option value="Cartao">Cartão</option>
                <option value="Pix">Pix</option>
            </select>

            <div class="info-box">
                <div class="info-row">
                    <span>Produto:</span>
                    <strong id="nome_produto">Aguardando busca...</strong>
                </div>
                <div class="info-row">
                    <span>Valor Unitário:</span>
                    <strong id="valor_unitario">R$ 0,00</strong>
                </div>
            </div>

            <label for="quantidade">Quantidade:</label>
            <input type="number" id="quantidade" name="quantidade" value="1" min="1" required oninput="calcularTotal()" onkeydown="tratarTeclaQuantidade(event)">

            <div class="info-box total-box">
                <div class="info-row">
                    <span>VALOR TOTAL:</span>
                    <strong id="valor_total">R$ 0,00</strong>
                </div>
            </div>

            <button type="submit" id="btnFinalizar">Registrar Venda (ENTER)</button>
        </form>

        {% if msg %}
            <div class="msg {{ 'msg-sucesso' if 'sucesso' in msg.lower() else 'msg-erro' }}">{{ msg }}</div>
        {% endif %}

        <div class="footer-system">
            Powered by <strong>Yamasaki Technology Solution</strong> 🚀
        </div>
    </div>

    <script>
        let precoUnitarioAtual = 0;
        async function buscarProduto() {
            const identificador = document.getElementById('identificador').value.trim();
            if (!identificador) { resetarCampos(); return false; }
            try {
                const response = await fetch('/buscar_produto?q=' + encodeURIComponent(identificador));
                const data = await response.json();
                if (data.sucesso) {
                    document.getElementById('nome_produto').innerText = data.nome;
                    precoUnitarioAtual = parseFloat(data.preco);
                    document.getElementById('valor_unitario').innerText = 'R$ ' + precoUnitarioAtual.toFixed(2).replace('.', ',');
                    calcularTotal();
                    return true;
                } else {
                    document.getElementById('nome_produto').innerText = 'Produto não encontrado';
                    resetarCampos();
                    return false;
                }
            } catch (e) { resetarCampos(); return false; }
        }

        async function tratarTeclaIdentificador(e) {
            if (e.key === 'Enter' || e.key === 'Tab') {
                e.preventDefault();
                const achou = await buscarProduto();
                if (achou) {
                    const campoQtd = document.getElementById('quantidade');
                    campoQtd.focus();
                    campoQtd.select();
                }
            }
        }
        function tratarTeclaQuantidade(e) { if (e.key === 'Enter') { calcularTotal(); } }
        function calcularTotal() {
            const qtd = parseInt(document.getElementById('quantidade').value) || 0;
            const total = precoUnitarioAtual * qtd;
            document.getElementById('valor_total').innerText = 'R$ ' + total.toFixed(2).replace('.', ',');
        }
        function resetarCampos() {
            document.getElementById('valor_unitario').innerText = 'R$ 0,00';
            document.getElementById('valor_total').innerText = 'R$ 0,00';
            precoUnitarioAtual = 0;
        }
    </script>
</body>
</html>
"""

HTML_ESTOQUE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Entrada de Estoque</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f4f9; padding: 20px; }
        .container { max-width: 500px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); margin: auto; }
        h2 { color: #333; }
        label { display: block; margin-top: 10px; font-weight: bold; }
        input, button { width: 100%; padding: 10px; margin-top: 5px; box-sizing: border-box; }
        button { background: #28a745; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; margin-top: 15px; }
        button:hover { background: #218838; }
        .msg { margin-top: 15px; padding: 10px; background: #e2f0d9; color: #385723; border-radius: 4px; text-align: center; }
        a { display: block; text-align: center; margin-top: 15px; text-decoration: none; color: #007bff; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Entrada de Estoque</h2>
        {% if msg %}
            <div class="msg">{{ msg }}</div>
        {% endif %}
        <form method="POST">
            <label for="identificador">Código de Barras ou ID:</label>
            <input type="text" id="identificador" name="identificador" required autofocus>
            
            <label for="quantidade">Quantidade a Adicionar:</label>
            <input type="number" id="quantidade" name="quantidade" value="1" min="1" required>
            
            <button type="submit">Adicionar ao Estoque</button>
        </form>
        <a href="/">Voltar para o Caixa</a>
    </div>
</body>
</html>
"""

# --- ROTA DO CAIXA COM REGISTRO DE VENDAS COMPLETO ---
@app.route('/', methods=['GET', 'POST'])
def index():
    mensagem = None
    if request.method == 'POST':
        identificador = request.form.get('identificador', '').strip()
        quantidade = int(request.form.get('quantidade', 1))
        forma_pagamento = request.form.get('forma_pagamento', 'Dinheiro')

        conn = conectar_banco()
        cur = conn.cursor()
        try:
            # 1. Busca nome e preço do produto para o histórico
            if identificador.isdigit():
                cur.execute(f"SELECT nome, preco FROM {TABELA_PRODUTO} WHERE id = %s;", (int(identificador),))
            else:
                cur.execute(f"SELECT nome, preco FROM {TABELA_PRODUTO} WHERE codigo_barra = %s;", (identificador,))
            
            produto = cur.fetchone()
            if not produto:
                raise Exception("Produto não encontrado no cadastro!")
            
            nome_produto = produto[0]
            preco_unitario = float(produto[1])
            total_venda = preco_unitario * quantidade

            # 2. Atualiza (baixa) o estoque
            if identificador.isdigit():
                cur.execute(f"UPDATE {TABELA_PRODUTO} SET estoque = estoque - %s WHERE id = %s;", (quantidade, int(identificador)))
            else:
                cur.execute(f"UPDATE {TABELA_PRODUTO} SET estoque = estoque - %s WHERE codigo_barra = %s;", (quantidade, identificador))
            
            # 3. REGISTRA NA TABELA DE VENDAS
            cur.execute(
                "INSERT INTO vendas (data_venda, total, forma_pagamento, produto, quantidade) VALUES (NOW(), %s, %s, %s, %s);",
                (total_venda, forma_pagamento, nome_produto, quantidade)
            )
            
            # (Opcional caso utilize a tabela de backup/espelho mencionada)
            # cur.execute("INSERT INTO produtobkp ...", (...))

            conn.commit()
            mensagem = f"Venda realizada com sucesso! ({quantidade}x {nome_produto} - R$ {total_venda:.2f})"
        except Exception as e:
            conn.rollback()
            mensagem = f"Erro ao registrar venda: {e}"
        finally:
            cur.close()
            conn.close()

    return render_template_string(HTML_CAIXA, msg=mensagem)

@app.route('/buscar_produto')
def buscar_produto():
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
    mensagem = None
    if request.method == 'POST':
        identificador = request.form.get('identificador', '').strip()
        quantidade = int(request.form.get('quantidade', 1))
        conn = conectar_banco()
        cur = conn.cursor()
        try:
            if identificador.isdigit():
                cur.execute(f"UPDATE {TABELA_PRODUTO} SET estoque = estoque + %s WHERE id = %s;", (quantidade, int(identificador)))
            else:
                cur.execute(f"UPDATE {TABELA_PRODUTO} SET estoque = estoque + %s WHERE codigo_barra = %s;", (quantidade, identificador))
            conn.commit()
            mensagem = "Estoque atualizado com sucesso!"
        except Exception as e:
            conn.rollback()
            mensagem = f"Erro ao atualizar estoque: {e}"
        finally:
            cur.close()
            conn.close()
    return render_template_string(HTML_ESTOQUE, msg=mensagem)

if __name__ == '__main__':
    app.run(debug=True)
