# 1. Configurações e Imports lá no topo
import os
from flask import Flask, render_template_string, request, jsonify, render_template
import psycopg2

app = Flask(__name__)

# 2. Dados do Banco
HOST = "localhost"
...

# 3. HTML do Caixa
HTML_CAIXA = """
... (todo o HTML do caixa aqui) ...
"""

# 4. HTML do Estoque (COLE AQUI!)
HTML_ESTOQUE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Entrada de Estoque - Berse Supermercados</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f9; }
        .container { max-width: 500px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        h1 { color: #333; }
        label { display: block; margin-top: 10px; font-weight: bold; }
        input { width: 100%; padding: 8px; margin-top: 5px; box-sizing: border-box; }
        button { margin-top: 15px; width: 100%; padding: 10px; background-color: #28a745; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; }
        button:hover { background-color: #218838; }
        .msg { margin-top: 15px; padding: 10px; background: #e2e3e5; border-radius: 4px; }
        .voltar { display: inline-block; margin-top: 15px; color: #007bff; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Entrada de Estoque</h1>
        <form method="POST">
            <label for="codigo_barra">Código de Barras do Produto:</label>
            <input type="text" id="codigo_barra" name="codigo_barra" required>

            <label for="quantidade">Quantidade a Adicionar:</label>
            <input type="number" id="quantidade" name="quantidade" required min="1">

            <button type="submit">Adicionar ao Estoque</button>
        </form>

        {% if msg %}
            <div class="msg">{{ msg }}</div>
        {% endif %}

        <a class="voltar" href="/">← Voltar para o PDV (Frente de Caixa)</a>
    </div>
</body>
</html>
"""

# 5. Rotas do Flask (registrar_venda, entrada_estoque, etc.)
@app.route('/')
def index():
    return render_template_string(HTML_CAIXA)

@app.route('/api/produto/<int:cod_produto>')
def consultar_produto(cod_produto):
    try:
        conexao = psycopg2.connect(host=HOST, port=PORTA, dbname=BANCO, user=USUARIO, password=SENHA)
        cursor = conexao.cursor()
        
        cursor.execute("SELECT nome, preco, qtde_estoque FROM produto WHERE cod_produto = %s;", (cod_produto,))
        resultado = cursor.fetchone()

        cursor.close()
        conexao.close()

        if resultado:
            return jsonify({
                "sucesso": True, 
                "nome": resultado[0], 
                "preco": float(resultado[1]),
                "estoque": resultado[2]
            })
        else:
            return jsonify({"sucesso": False, "mensagem": "Produto não encontrado"})
    except Exception as e:
        return jsonify({"sucesso": False, "erro": str(e)})

@app.route('/registrar', methods=['POST'])
def registrar_venda():
    conexao = None
    try:
        cod_funcionario = int(request.form['cod_funcionario'])
        cod_produto = int(request.form['cod_produto'])
        quantidade = int(request.form['quantidade'])

        conexao = psycopg2.connect(host=HOST, port=PORTA, dbname=BANCO, user=USUARIO, password=SENHA)
        cursor = conexao.cursor()

        # 1. Valida se o funcionário existe e se o cargo é autorizada para vendas
        cursor.execute("""
            SELECT f.nome, c.nome 
            FROM funcionario f
            JOIN cargo c ON c.cod_cargo = f.cod_cargo
            WHERE f.cod_funcionario = %s;
        """, (cod_funcionario,))
        func = cursor.fetchone()

        if not func:
            return render_template_string(HTML_CAIXA, erro="Funcionário não encontrado no sistema!")

        nome_func, nome_cargo = func[0], func[1]

        # Verifica se o termo 'venda' ou 'caixa' está presente no nome do cargo (independente de maiúsculas)
        cargo_valido = any(termo in nome_cargo.lower() for termo in ['venda', 'vendas', 'caixa', 'operador'])

        if not cargo_valido:
            return render_template_string(
                HTML_CAIXA, 
                erro=f"Acesso negado: {nome_func} ({nome_cargo}) não possui permissão para operar o caixa!"
            )

        # 2. Busca preço real e estoque diretamente no banco
        cursor.execute("SELECT preco, qtde_estoque FROM produto WHERE cod_produto = %s;", (cod_produto,))
        prod = cursor.fetchone()

        if not prod:
            return render_template_string(HTML_CAIXA, erro="Produto não encontrado!")

        preco_unitario = float(prod[0])
        estoque_atual = prod[1]

        if estoque_atual < quantidade:
            return render_template_string(HTML_CAIXA, erro=f"Estoque insuficiente! Disponível: {estoque_atual}")

        valor_total = quantidade * preco_unitario

        # 3. Registra a Venda
        cursor.execute(
            "INSERT INTO venda (cod_funcionario, valor_total) VALUES (%s, %s) RETURNING cod_venda;",
            (cod_funcionario, valor_total)
        )
        cod_venda = cursor.fetchone()[0]

        # 4. Registra o Item da Venda
        cursor.execute(
            "INSERT INTO item_venda (cod_produto, cod_venda, preco_unitario, quantidade) VALUES (%s, %s, %s, %s);",
            (cod_produto, cod_venda, preco_unitario, quantidade)
        )

        # 5. Atualiza o Estoque do Produto
        cursor.execute(
            "UPDATE produto SET qtde_estoque = qtde_estoque - %s WHERE cod_produto = %s;",
            (quantidade, cod_produto)
        )

        conexao.commit()
        cursor.close()
        conexao.close()

        msg = f"✓ Venda #{cod_venda} registrada por {nome_func} ({nome_cargo})! Total: R$ {valor_total:.2f}"
        return render_template_string(HTML_CAIXA, msg=msg)

    except Exception as e:
        if conexao:
            conexao.rollback()
            conexao.close()
        return render_template_string(HTML_CAIXA, erro=f"Erro ao salvar venda: {e}")

@app.route('/estoque/entrada', methods=['GET', 'POST'])
def entrada_estoque():
    mensagem = None

    if request.method == 'POST':
        codigo_barra = request.form.get('codigo_barra')
        quantidade = int(request.form.get('quantidade'))

        db_url = os.environ.get('DATABASE_URL', f"postgresql://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{BANCO}")
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        cur.execute(
            "UPDATE produto SET estoque = estoque + %s WHERE codigo_barra = %s",
            (quantidade, codigo_barra)
        )
        conn.commit()

        if cur.rowcount > 0:
            mensagem = f"Sucesso! Adicionadas {quantidade} unidades ao produto."
        else:
            mensagem = "Erro: Produto não encontrado com esse código!"

        cur.close()
        conn.close()

    # Este retorno PRECISA ficar fora do 'if' para responder ao acesso via navegador (GET)
    # Se você tiver uma variável HTML_ESTOQUE, use ela aqui:
    return render_template_string(HTML_ESTOQUE, msg=mensagem)