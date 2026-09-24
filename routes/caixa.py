from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database import conectar_banco, TABELA_PRODUTO

caixa_bp = Blueprint('caixa', __name__)

@caixa_bp.route('/')
@caixa_bp.route('/caixa')
def index():
    if not session.get('usuario'):
        return redirect(url_for('auth.login'))
    
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

        # 1. Se for numérico, tenta buscar primeiro por ID
        if query.isdigit():
            cur.execute(f"SELECT id, nome, preco, estoque FROM {TABELA_PRODUTO} WHERE id = %s LIMIT 1", (int(query),))
            produto = cur.fetchone()

        # 2. Se não encontrou por ID, tenta por Código de Barras ou Nome
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