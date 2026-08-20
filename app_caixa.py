import os
import psycopg2
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "chave_secreta_super_segura_berse"

TABELA_PRODUTO = "produto"
TABELA_USUARIO = "usuario"

def conectar_banco():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url)

HTML_LOGIN = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Login - Grupo Yamasaki PDV</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; min-height: 100vh; background-color: #f0f2f5; display: flex; justify-content: center; align-items: center; }
        .login-card { background: #ffffff; width: 100%; max-width: 400px; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        h2 { color: #007bff; text-align: center; margin-top: 0; }
        label { display: block; margin-top: 15px; font-weight: 600; color: #444; }
        input { width: 100%; padding: 12px; margin-top: 6px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 15px; }
        button { margin-top: 25px; width: 100%; padding: 12px; background-color: #007bff; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        .msg { margin-top: 15px; padding: 10px; border-radius: 6px; font-weight: bold; text-align: center; background: #ffebee; color: #c62828; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>🏪 GRUPO YAMASAKI</h2>
        <p style="text-align: center; color: #666; font-size: 14px;">Faça login para acessar o PDV</p>
        
        <form method="POST">
            <label for="username">Usuário:</label>
            <input type="text" id="username" name="username" required autofocus>
            
            <label for="password">Senha:</label>
            <input type="password" id="password" name="password" required>
            
            <button type="submit">Entrar</button>
        </form>

        {% if msg %}
            <div class="msg">{{ msg }}</div>
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
    <title>Berse Supermercados - PDV</title>
    <style>

        body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 0;
    min-height: 100vh;
    background-color: #f0f2f5;
    
    /* Textura de fundo moderna (padrão sutil em grid) */
    background-image: 
        linear-gradient(rgba(0, 0, 0, 0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 0, 0, 0.02) 1px, transparent 1px);
    background-size: 20px 20px;
    
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
    box-sizing: border-box;
}
        
        /* Container principal que segura o Pix e o Card lado a lado */
        .main-container { display: flex; gap: 20px; align-items: flex-start; max-width: 1000px; width: 100%; justify-content: center; }
        
        /* Estilo do Card do Pix à esquerda */
        .pix-card { background: #ffffff; width: 100%; max-width: 350px; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); display: none; text-align: center; }
        .pix-card h3 { color: #007bff; margin-top: 0; font-size: 18px; border-bottom: 2px solid #007bff; padding-bottom: 8px; }
        .qr-placeholder { width: 200px; height: 200px; background: #f8f9fa; border: 2px dashed #ccc; border-radius: 8px; margin: 15px auto; display: flex; align-items: center; justify-content: center; color: #666; font-size: 14px; }
        .btn-pix-link { display: inline-block; margin-top: 10px; padding: 10px 15px; background-color: #28a745; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 14px; }
        .btn-pix-link:hover { background-color: #218838; }

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
        .brand-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #e9ecef; padding-bottom: 10px; }
        .brand-header h2 { color: #007bff; margin: 0; font-size: 20px; font-weight: bold; }
        .user-info { font-size: 13px; color: #555; text-align: right; }
        .user-info a { color: #dc3545; text-decoration: none; margin-left: 8px; font-weight: bold; }
        .footer-system { text-align: center; margin-top: 30px; font-size: 12px; color: #888; border-top: 1px solid #e9ecef; padding-top: 15px; }
    </style>
</head>
<body>

   <!-- PAINEL PIX REAL -->
    <div id="painel-pix" class="pix-card">
        <h3 style="color: #28a745; margin-top: 0;">Pagamento via Pix</h3>
        <p style="font-size: 13px; color: #666; margin-bottom: 10px;">Escaneie o QR Code abaixo:</p>
        
        <!-- Imagem gerada dinamicamente com o seu Payload do Pix -->
        <img src="https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=00020126400014br.gov.bcb.pix0118py9dm.mt@gmail.com5204000053039865802BR5915BERSEJULIOCESAR6009Sao Paulo610901227-20062230519daqr2112582259416686304F335" alt="QR Code Pix" style="width: 200px; height: 200px; border-radius: 8px; border: 1px solid #ddd; padding: 5px; background: #fff;">
        
        <p style="font-size: 12px; color: #666; margin-top: 10px;">Ou copie o código Copia e Cola:</p>
        <textarea readonly style="width: 100%; height: 50px; font-size: 10px; border: 1px solid #ccc; padding: 5px; resize: none; background: #f9f9f9;">00020126400014br.gov.bcb.pix0118py9dm.mt@gmail.com5204000053039865802BR5915BERSEJULIOCESAR6009Sao Paulo610901227-20062230519daqr2112582259416686304F335</textarea>
    </div>

        <!-- CARD PRINCIPAL DE VENDAS -->
        <div class="card">
            <div style="text-align: center; margin-bottom: 15px;">
                <div style="display: inline-block; width: 40px; height: 40px; background-color: #bc002d; border-radius: 50%; line-height: 40px; color: white; font-weight: bold; font-size: 18px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 4px;">山</div>
                <h2 style="color: #1a1a1a; font-size: 18px; font-weight: 700; letter-spacing: 2px; margin: 0;">GRUPO YAMASAKI</h2>
                <span style="color: #666; font-size: 10px; letter-spacing: 3px; text-transform: uppercase;">山崎グループ</span>
            </div>
            <hr style="border: none; height: 1px; background: #e0e0e0; margin-bottom: 15px;">

            <div class="brand-header">
                <h2>🏪 Frente de Caixa</h2>
                <div class="user-info">
                    Operador: <strong>{{ usuario }}</strong> <a href="/logout">[Sair]</a>
                </div>
            </div>
            <a class="nav-link" href="/estoque/entrada">📦 Ir para Entrada de Estoque →</a>

            <form id="formVenda" method="POST" action="/">
                <label for="identificador">ID ou Código de Barras do Produto:</label>
                <input type="text" id="identificador" name="identificador" placeholder="Digite o ID/Código e pressione TAB ou ENTER" required autofocus onblur="buscarProduto()" onkeydown="tratarTeclaIdentificador(event)">
                
                <label for="forma_pagamento">Forma de Pagamento:</label>
                <select name="forma_pagamento" id="forma_pagamento" onchange="verificarPix()">
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
    </div>

    <script>
        let precoUnitarioAtual = 0;

        // Função que controla a exibição do painel Pix ao lado
        function verificarPix() {
            const formaPagto = document.getElementById('forma_pagamento').value;
            const painelPix = document.getElementById('painel-pix');
            
            if (formaPagto === 'Pix') {
                painelPix.style.display = 'block'; // Mostra o QR Code/Link à esquerda
            } else {
                painelPix.style.display = 'none';  // Oculta se for Dinheiro ou Cartão
            }
        }

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
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Entrada de Estoque - Grupo Yamasaki</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; min-height: 100vh; background-color: #f0f2f5; display: flex; justify-content: center; align-items: center; }
        .card { background: #ffffff; width: 100%; max-width: 600px; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin: auto; }
        h1 { color: #1a1a1a; margin-top: 0; font-size: 24px; border-bottom: 2px solid #28a745; padding-bottom: 10px; }
        label { display: block; margin-top: 15px; font-weight: 600; color: #444; }
        input { width: 100%; padding: 12px; margin-top: 6px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 15px; background-color: #fff; }
        input:focus { border-color: #28a745; outline: none; }
        button { margin-top: 25px; width: 100%; padding: 12px; background-color: #28a745; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background 0.2s; }
        button:hover { background-color: #218838; }
        .info-box { background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 15px; margin-top: 15px; }
        .info-row { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 16px; }
        .info-row strong { color: #333; }
        .msg { margin-top: 20px; padding: 12px; border-radius: 6px; font-weight: bold; text-align: center; }
        .msg-sucesso { background: #e8f5e9; color: #2e7d32; }
        .msg-erro { background: #ffebee; color: #c62828; }
        .nav-link { display: inline-block; margin-bottom: 15px; color: #007bff; text-decoration: none; font-weight: bold; }
        .brand-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #e9ecef; padding-bottom: 10px; }
        .brand-header h2 { color: #007bff; margin: 0; font-size: 20px; font-weight: bold; }
        .user-info { font-size: 13px; color: #555; text-align: right; }
        .user-info a { color: #dc3545; text-decoration: none; margin-left: 8px; font-weight: bold; }
        .footer-system { text-align: center; margin-top: 30px; font-size: 12px; color: #888; border-top: 1px solid #e9ecef; padding-top: 15px; }
    </style>
</head>
<body>
  <div class="card">
        <div style="text-align: center; margin-bottom: 15px;">
            <div style="display: inline-block; width: 40px; height: 40px; background-color: #bc002d; border-radius: 50%; line-height: 40px; color: white; font-weight: bold; font-size: 18px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 4px;">山</div>
            <h2 style="color: #1a1a1a; font-size: 18px; font-weight: 700; letter-spacing: 2px; margin: 0;">GRUPO YAMASAKI</h2>
            <span style="color: #666; font-size: 10px; letter-spacing: 3px; text-transform: uppercase;">山崎グループ</span>
        </div>
        <hr style="border: none; height: 1px; background: #e0e0e0; margin-bottom: 15px;">

        <div class="brand-header">
            <h2>📦 Gerenciamento de Estoque</h2>
            <div class="user-info">
                Operador: <strong>{{ usuario }}</strong> <a href="/logout">[Sair]</a>
            </div>
        </div>
        <a class="nav-link" href="/">← Voltar para o Caixa</a>

        <form method="POST">
            <label for="identificador">Código de Barras ou ID:</label>
            <input type="text" id="identificador" name="identificador" placeholder="Digite o ID/Código e pressione TAB ou ENTER" required autofocus onblur="buscarProdutoEstoque()" onkeydown="tratarTeclaIdentificadorEstoque(event)">
            
            <div class="info-box">
                <div class="info-row">
                    <span>Produto:</span>
                    <strong id="nome_produto">Aguardando busca...</strong>
                </div>
                <div class="info-row">
                    <span>Estoque Atual:</span>
                    <strong id="estoque_atual">-</strong>
                </div>
            </div>

            <label for="quantidade">Quantidade a Adicionar / Retirar (ex: 10 ou -10):</label>
            <input type="number" id="quantidade" name="quantidade" value="1" required>

            <button type="submit">Atualizar Estoque</button>
        </form>

        {% if msg %}
            <div class="msg {{ 'msg-sucesso' if 'sucesso' in msg.lower() else 'msg-erro' }}">{{ msg }}</div>
        {% endif %}

        <div class="footer-system">
            Powered by <strong>Yamasaki Technology Solution</strong> 🚀
        </div>
    </div>

    <script>
        async function buscarProdutoEstoque() {
            const identificador = document.getElementById('identificador').value.trim();
            if (!identificador) { resetarCampos(); return false; }
            try {
                const response = await fetch('/buscar_produto?q=' + encodeURIComponent(identificador));
                const data = await response.json();
                if (data.sucesso) {
                    document.getElementById('nome_produto').innerText = data.nome;
                    document.getElementById('estoque_atual').innerText = data.estoque;
                    return true;
                } else {
                    document.getElementById('nome_produto').innerText = 'Produto não encontrado';
                    document.getElementById('estoque_atual').innerText = '-';
                    return false;
                }
            } catch (e) { resetarCampos(); return false; }
        }

        async function tratarTeclaIdentificadorEstoque(e) {
            if (e.key === 'Enter' || e.key === 'Tab') {
                e.preventDefault();
                const achou = await buscarProdutoEstoque();
                if (achou) {
                    const campoQtd = document.getElementById('quantidade');
                    campoQtd.focus();
                    campoQtd.select();
                }
            }
        }
        function resetarCampos() {
            document.getElementById('nome_produto').innerText = 'Aguardando busca...';
            document.getElementById('estoque_atual').innerText = '-';
        }
    </script>
</body>
</html>
"""

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
            
            cur.execute(
                "INSERT INTO vendas (data_venda, total, forma_pagamento, produto, quantidade) VALUES (NOW(), %s, %s, %s, %s);",
                (total_venda, forma_pagamento, nome_produto, quantidade)
            )
            
            # ATUALIZADO: Adicionado 'VENDA' no bkp
            cur.execute(
                "INSERT INTO produtobkp (produto_id, codigo_barra, nome, preco_praticado, quantidade_vendida, data_movimento, tipo_operacao) VALUES (%s, %s, %s, %s, %s, NOW(), 'VENDA');",
                (prod_id, codigo_barra, nome_produto, preco_unitario, quantidade)
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
            
            # ATUALIZADO: Adicionado 'ENTRADA' no bkp
            cur.execute(
                "INSERT INTO produtobkp (produto_id, codigo_barra, nome, preco_praticado, quantidade_vendida, data_movimento, tipo_operacao) VALUES (%s, %s, %s, %s, %s, NOW(), 'ENTRADA');",
                (prod_id, codigo_barra, nome_produto, preco_unitario, quantidade)
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

if __name__ == '__main__':
    app.run(debug=True)
