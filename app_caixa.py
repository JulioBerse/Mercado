import os
import psycopg2
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# CONFIGURAÇÕES DO BANCO DE DADOS
HOST = "localhost"
PORTA = "5432"
BANCO = "Mercado"
USUARIO = "postgres"
SENHA = "j"

# NOME DA TABELA NO POSTGRESQL (Ajustado para 'produtos')
TABELA_PRODUTOS = "produto"

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
        input { width: 100%; padding: 12px; margin-top: 6px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 15px; }
        input:focus { border-color: #007bff; outline: none; }
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
    </style>
</head>
<body>
    <div class="card">
        <a class="nav-link" href="/estoque/entrada">📦 Ir para Entrada de Estoque →</a>
        <h1>🛒 Frente de Caixa (PDV)</h1>

        <form id="formVenda" method="POST" action="/registrar_venda">
            <label for="identificador">ID ou Código de Barras do Produto:</label>
            <input type="text" id="identificador" name="identificador" placeholder="Digite o ID/Código e pressione TAB ou ENTER" required autofocus onblur="buscarProduto()" onkeydown="tratarTeclaIdentificador(event)">
            <select name="forma_pagamento">
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
            <div class="msg msg-sucesso">{{ msg }}</div>
        {% endif %}
        {% if erro %}
            <div class="msg msg-erro">{{ erro }}</div>
        {% endif %}
    </div>

    <script>
        let precoUnitarioAtual = 0;

        async function buscarProduto() {
            const identificador = document.getElementById('identificador').value.trim();
            if (!identificador) {
                resetarCampos();
                return false;
            }

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
                    document.getElementById('valor_unitario').innerText = 'R$ 0,00';
                    precoUnitarioAtual = 0;
                    calcularTotal();
                    return false;
                }
            } catch (e) {
                resetarCampos();
                return false;
            }
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

        function tratarTeclaQuantidade(e) {
            if (e.key === 'Enter') {
                calcularTotal();
            }
        }

        function calcularTotal() {
            const qtd = parseInt(document.getElementById('quantidade').value) || 0;
            const total = precoUnitarioAtual * qtd;
            document.getElementById('valor_total').innerText = 'R$ ' + total.toFixed(2).replace('.', ',');
        }

        function resetarCampos() {
            document.getElementById('nome_produto').innerText = 'Aguardando busca...';
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
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Entrada de Estoque - Berse Supermercados</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 40px; background-color: #f0f2f5; display: flex; justify-content: center; }
        .card { background: #ffffff; width: 100%; max-width: 500px; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        h1 { color: #1a1a1a; margin-top: 0; font-size: 24px; border-bottom: 2px solid #28a745; padding-bottom: 10px; }
        label { display: block; margin-top: 15px; font-weight: 600; color: #444; }
        input { width: 100%; padding: 12px; margin-top: 6px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 15px; }
        input:focus { border-color: #28a745; outline: none; }
        button { margin-top: 25px; width: 100%; padding: 12px; background-color: #28a745; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background 0.2s; }
        button:hover { background-color: #218838; }
        .msg { margin-top: 20px; padding: 12px; background: #e8f5e9; color: #2e7d32; border-radius: 6px; font-weight: bold; text-align: center; }
        .btn-voltar { display: inline-block; margin-top: 20px; color: #007bff; text-decoration: none; font-weight: 600; }
        .btn-voltar:hover { text-decoration: underline; }
        .hint { font-size: 12px; color: #666; margin-top: 4px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>📦 Entrada de Estoque</h1>
        <form method="POST">
            <label for="identificador">Código de Barras ou ID do Produto:</label>
            <input type="text" id="identificador" name="identificador" placeholder="Digite o ID (ex: 5) ou Código (ex: 789123...)" required autofocus>
            <div class="hint">* Digite apenas o ID numérico ou o Código de Barras completo.</div>

            <label for="quantidade">Quantidade a Adicionar:</label>
            <input type="number" id="quantidade" name="quantidade" placeholder="Ex: 10" required min="1">

            <button type="submit">Atualizar Estoque</button>
        </form>

        {% if msg %}
            <div class="msg">{{ msg }}</div>
        {% endif %}

        <a class="btn-voltar" href="/">← Voltar para o PDV (Frente de Caixa)</a>
    </div>
</body>
</html>
"""

@app.route('/registrar_venda', methods=['POST'])
def registrar_venda():
    # Pega os dados que vieram do formulário da sua página HTML
    identificador = request.form.get('identificador', '').strip()
    quantidade = int(request.form.get('quantidade', 1))
    forma_pgto = request.form.get('forma_pagamento', 'Dinheiro') # Pega do formulário

    # Conecta no seu banco Neon
    db_url = os.environ.get('DATABASE_URL') 
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    try:
        # Chama a procedure que você acabou de criar no SQL Editor do Neon
        cur.execute(
            "CALL registrar_venda_completa(%s, %s, %s);", 
            (identificador, quantidade, forma_pgto)
        )
        conn.commit()
        mensagem = "Venda realizada com sucesso!"
    except Exception as e:
        conn.rollback()
        mensagem = f"Erro: {e}"
    finally:
        cur.close()
        conn.close()

    return render_template_string(HTML_CAIXA, msg=mensagem)
