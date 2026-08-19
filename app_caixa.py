import os
from flask import Flask, render_template_string, request, jsonify, render_template
import psycopg2

app = Flask(__name__)

# CONFIGURAÇÕES DO BANCO DE DADOS
HOST = "localhost"
PORTA = "5432"
BANCO = "Mercado"
USUARIO = "postgres"
SENHA = "j"  # COLOQUE SUA SENHA DO POSTGRESQL AQUI

HTML_CAIXA = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Frente de Caixa - Mercado</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #1e1e2e; color: #cdd6f4; padding: 30px; margin: 0; }
        h1 { color: #a6e3a1; text-align: center; margin-bottom: 25px; }
        .container { max-width: 480px; margin: 0 auto; background: #313244; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.4); }
        label { display: block; margin-top: 15px; font-weight: bold; color: #89b4fa; }
        input { width: 100%; padding: 12px; margin-top: 5px; border-radius: 6px; border: 1px solid #45475a; background: #181825; color: #fff; box-sizing: border-box; font-size: 15px; }
        input:focus { border-color: #89b4fa; outline: none; }
        input[readonly] { background-color: #2a2a3c; color: #a6e3a1; font-weight: bold; cursor: not-allowed; }
        button { width: 100%; background-color: #a6e3a1; color: #11111b; font-weight: bold; padding: 14px; border: none; border-radius: 6px; margin-top: 25px; cursor: pointer; font-size: 16px; transition: 0.2s; }
        button:hover { background-color: #94e2d5; }
        .mensagem { background-color: #a6e3a1; color: #11111b; padding: 12px; border-radius: 6px; margin-bottom: 20px; text-align: center; font-weight: bold; }
        .erro { background-color: #f38ba8; color: #11111b; padding: 12px; border-radius: 6px; margin-bottom: 20px; text-align: center; font-weight: bold; }
        .info-produto { font-size: 13px; color: #fab387; margin-top: 4px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛒 Frente de Caixa (PDV)</h1>
        
        {% if msg %}
            <div class="mensagem">{{ msg }}</div>
        {% endif %}
        {% if erro %}
            <div class="erro">{{ erro }}</div>
        {% endif %}

        <form action="/registrar" method="POST">
            <label for="cod_funcionario">Código do Funcionário (Caixa):</label>
            <input type="number" id="cod_funcionario" name="cod_funcionario" required placeholder="Ex: 1" autofocus>

            <label for="cod_produto">Código do Produto (cod_produto):</label>
            <input type="number" id="cod_produto" name="cod_produto" required placeholder="Ex: 101" oninput="buscarProduto()">
            <div id="nome_produto" class="info-produto"></div>

            <label for="quantidade">Quantidade:</label>
            <input type="number" id="quantidade" name="quantidade" value="1" min="1" required oninput="calcularTotal()">

            <label for="preco_unitario">Preço Unitário (R$):</label>
            <input type="number" step="0.01" id="preco_unitario" name="preco_unitario" readonly placeholder="Busca automática...">

            <label for="valor_total_display">Total da Venda (R$):</label>
            <input type="text" id="valor_total_display" readonly placeholder="R$ 0.00">

            <button type="submit">Confirmar e Registrar Venda</button>
        </form>
    </div>

    <script>
        async function buscarProduto() {
            const cod = document.getElementById('cod_produto').value;
            const campoPreco = document.getElementById('preco_unitario');
            const campoNome = document.getElementById('nome_produto');

            if (!cod) {
                campoPreco.value = '';
                campoNome.innerText = '';
                calcularTotal();
                return;
            }

            try {
                const res = await fetch(`/api/produto/${cod}`);
                const data = await res.json();

                if (data.sucesso) {
                    campoPreco.value = data.preco.toFixed(2);
                    campoNome.innerText = `📦 ${data.nome} | Estoque: ${data.estoque}`;
                } else {
                    campoPreco.value = '';
                    campoNome.innerText = '❌ Produto não encontrado';
                }
            } catch (err) {
                campoPreco.value = '';
                campoNome.innerText = '';
            }
            calcularTotal();
        }

        function calcularTotal() {
            const qtd = parseFloat(document.getElementById('quantidade').value) || 0;
            const preco = parseFloat(document.getElementById('preco_unitario').value) || 0;
            const total = qtd * preco;
            document.getElementById('valor_total_display').value = 'R$ ' + total.toFixed(2);
        }
    </script>
</body>
</html>
"""

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
    return render_template_string(HTML_CAIXA, msg=mensagem)