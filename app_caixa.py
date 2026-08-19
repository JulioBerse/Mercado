from flask import Flask, render_template_string, request, jsonify
import os
import psycopg2

app = Flask(__name__)

# Configurações do Banco de Dados Neon
def conectar_banco():
    return psycopg2.connect(
        os.environ.get("DATABASE_URL", "sua_url_do_neon_aqui")
    )

TABELA_PRODUTO = "produto" # ou o nome da sua tabela de produtos

# --- TEMPLATE DA TELA DE ESTOQUE (HTML_ESTOQUE) ---
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

# --- TEMPLATE DA TELA DE CAIXA (HTML_CAIXA) ---
HTML_CAIXA = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Caixa - Berse Supermercados</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f4f9; padding: 20px; }
        .container { max-width: 600px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); margin: auto; }
        h2 { color: #333; }
        label { display: block; margin-top: 10px; font-weight: bold; }
        input, select, button { width: 100%; padding: 10px; margin-top: 5px; box-sizing: border-box; }
        button { background: #007bff; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; margin-top: 15px; }
        button:hover { background: #0056b3; }
        .msg { margin-top: 15px; padding: 10px; background: #d1ecf1; color: #0c5460; border-radius: 4px; text-align: center; }
        a { display: block; text-align: center; margin-top: 15px; text-decoration: none; color: #28a745; }
        .info-produto { margin-top: 10px; font-size: 14px; color: #555; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Frente de Caixa</h2>
        {% if msg %}
            <div class="msg">{{ msg }}</div>
        {% endif %}
        <form method="POST">
            <label for="identificador">Código de Barras ou ID:</label>
            <input type="text" id="identificador" name="identificador" required autofocus onblur="buscarProduto()">
            
            <div id="info_produto" class="info-produto"></div>

            <label for="quantidade">Quantidade:</label>
            <input type="number" id="quantidade" name="quantidade" value="1" min="1" required>
            
            <label for="forma_pagamento">Forma de Pagamento:</label>
            <select name="forma_pagamento" id="forma_pagamento">
                <option value="Dinheiro">Dinheiro</option>
                <option value="Cartao">Cartão</option>
                <option value="Pix">Pix</option>
            </select>
            
            <button type="submit">Finalizar Venda</button>
        </form>
        <a href="/estoque/entrada">Ir para Entrada de Estoque</a>
    </div>

    <script>
        function buscarProduto() {
            let id = document.getElementById('identificador').value.trim();
            if(!id) return;
            fetch('/api/produto/' + id)
                .then(res => res.json())
                .then(data => {
                    let div = document.getElementById('info_produto');
                    if(data.encontrado) {
                        div.innerHTML = "Produto: <b>" + data.nome + "</b>";
                    } else {
                        div.innerHTML = "<span style='color:red;'>Produto não encontrado!</span>";
                    }
                });
        }
    </script>
</body>
</html>
"""

# --- ROTA DO CAIXA (Com o INSERT correto na tabela vendas) ---
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
            # 1. Busca nome e preço do produto
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
            
            # 3. Insere o registro na tabela de vendas com o nome do produto
            cur.execute(
                "INSERT INTO vendas (data_venda, total, forma_pagamento, produto, quantidade) VALUES (NOW(), %s, %s, %s, %s);",
                (total_venda, forma_pagamento, nome_produto, quantidade)
            )
            
            conn.commit()
            mensagem = f"Venda registrada com sucesso! ({quantidade}x {nome_produto} - R$ {total_venda:.2f})"
        except Exception as e:
            conn.rollback()
            mensagem = f"Erro ao registrar venda: {e}"
        finally:
            cur.close()
            conn.close()

    return render_template_string(HTML_CAIXA, msg=mensagem)

# --- ROTAS DE API E ESTOQUE ---
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
