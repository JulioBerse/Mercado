from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database import conectar_banco, TABELA_PRODUTO

caixa_bp = Blueprint('caixa', __name__)

@caixa_bp.route('/', methods=['GET', 'POST'])
@caixa_bp.route('/caixa', methods=['GET', 'POST'])
def index():
    if not session.get('usuario'):
        return redirect(url_for('auth.login'))
    
    # Inicializa o carrinho e total na sessão caso não existam
    if 'carrinho' not in session:
        session['carrinho'] = []
    if 'total_compra_atual' not in session:
        session['total_compra_atual'] = 0.0

    # Trata a submissão de formulário tradicional
    if request.method == 'POST':
        produto_id = request.form.get('produto_id') or request.form.get('id')
        nome = request.form.get('nome') or request.form.get('produto_nome')
        preco = float(request.form.get('preco', 0))
        quantidade = int(request.form.get('quantidade', 1))

        if nome and preco > 0:
            subtotal = preco * quantidade
            carrinho = session.get('carrinho', [])
            carrinho.append({
                'id': produto_id,
                'nome': nome,
                'quantidade': quantidade,
                'preco': preco,
                'subtotal': subtotal
            })
            session['carrinho'] = carrinho
            session['total_compra_atual'] = sum(item['subtotal'] for item in carrinho)
            session.modified = True

        return redirect(url_for('caixa.index'))

    total_compra = session.get('total_compra_atual', 0.0)
    carrinho = session.get('carrinho', [])
    
    return render_template('caixa.html', total_compra_atual=total_compra, carrinho=carrinho)


@caixa_bp.route('/buscar_produto')
def buscar_produto():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'sucesso': False, 'mensagem': 'Termo de busca vazio'})

    try:
        conn = conectar_banco()
        cur = conn.cursor()
        produto = None

        if query.isdigit():
            cur.execute(f"SELECT id, nome, preco, estoque FROM {TABELA_PRODUTO} WHERE id = %s LIMIT 1", (int(query),))
            produto = cur.fetchone()

        if not produto:
            sql = f"""
                SELECT id, nome, preco, estoque 
                FROM {TABELA_PRODUTO} 
                WHERE codigo_barras = %s OR LOWER(nome) LIKE LOWER(%s)
                LIMIT 1
            """
            cur.execute(sql, (query, f"%{query}%"))
            produto = cur.fetchone()

        cur.close()
        conn.close()

        if produto:
            dados_prod = {
                'id': produto[0],
                'nome': produto[1],
                'preco': float(produto[2]),
                'estoque': produto[3]
            }
            return jsonify({
                'sucesso': True,
                'id': produto[0],
                'nome': produto[1],
                'preco': float(produto[2]),
                'estoque': produto[3],
                'produto': dados_prod
            })
        
        return jsonify({'sucesso': False, 'mensagem': 'Produto não encontrado'})

    except Exception as e:
        print(f"Erro na busca: {e}")
        return jsonify({'sucesso': False, 'mensagem': str(e)}), 200


@caixa_bp.route('/adicionar_item', methods=['POST'])
def adicionar_item():
    dados = request.get_json() or request.form
    nome = dados.get('nome') or dados.get('produto_nome')
    preco = float(dados.get('preco', 0))
    quantidade = int(dados.get('quantidade', 1))
    produto_id = dados.get('id') or dados.get('produto_id')

    if not nome or preco <= 0:
        return jsonify({'sucesso': False, 'mensagem': 'Dados do produto inválidos'})

    carrinho = session.get('carrinho', [])
    subtotal = preco * quantidade

    carrinho.append({
        'id': produto_id,
        'nome': nome,
        'quantidade': quantidade,
        'preco': preco,
        'subtotal': subtotal
    })

    session['carrinho'] = carrinho
    session['total_compra_atual'] = sum(item['subtotal'] for item in carrinho)
    session.modified = True

    return jsonify({
        'sucesso': True,
        'carrinho': session['carrinho'],
        'total': session['total_compra_atual']
    })


@caixa_bp.route('/limpar_carrinho', methods=['POST'])
def limpar_carrinho():
    session['carrinho'] = []
    session['total_compra_atual'] = 0.0
    session.modified = True
    return jsonify({'sucesso': True})