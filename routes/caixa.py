@caixa_bp.route('/buscar_produto')
def buscar_produto():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'sucesso': False})

    conn = get_db_connection()
    cur = conn.cursor()

    # Procura por ID (se for número) OU por Código de Barras (texto/string)
    if query.isdigit():
        sql = """
            SELECT id, nome, preco, estoque 
            FROM produtos 
            WHERE id = %s OR codigo_barras = %s OR codigo_barras LIKE %s
            LIMIT 1
        """
        cur.execute(sql, (int(query), query, f"%{query}%"))
    else:
        sql = """
            SELECT id, nome, preco, estoque 
            FROM produtos 
            WHERE codigo_barras = %s OR LOWER(nome) LIKE LOWER(%s)
            LIMIT 1
        """
        cur.execute(sql, (query, f"%{query}%"))

    produto = cur.fetchone()
    cur.close()
    conn.close()

    if produto:
        return jsonify({
            'sucesso': True,
            'id': produto[0],
            'nome': produto[1],
            'preco': float(produto[2]),
            'estoque': produto[3]
        })
    
    return jsonify({'sucesso': False})