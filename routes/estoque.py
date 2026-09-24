from flask import Blueprint, render_template, request, session, redirect, url_for
from database import conectar_banco, TABELA_PRODUTO, registrar_backup

estoque_bp = Blueprint('estoque', __name__)

@estoque_bp.route('/estoque/entrada', methods=['GET', 'POST'])
def entrada_estoque():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    usuario = session['usuario']
    msg = None

    if request.method == 'POST':
        identificador = request.form.get('identificador', '').strip()
        qtd = int(request.form.get('quantidade', 0))

        if identificador and qtd != 0:
            try:
                conn = conectar_banco()
                cur = conn.cursor()

                if identificador.isdigit():
                    cur.execute(f"SELECT id, nome, preco, estoque FROM {TABELA_PRODUTO} WHERE id = %s OR codigo_barras = %s", (int(identificador), identificador))
                else:
                    cur.execute(f"SELECT id, nome, preco, estoque FROM {TABELA_PRODUTO} WHERE codigo_barras = %s", (identificador,))

                prod = cur.fetchone()

                if prod:
                    prod_id, nome, preco, estoque_atual = prod
                    novo_estoque = estoque_atual + qtd

                    cur.execute(f"UPDATE {TABELA_PRODUTO} SET estoque = %s WHERE id = %s", (novo_estoque, prod_id))
                    registrar_backup(cur, prod_id, nome, preco, novo_estoque, f"AJUSTE ESTOQUE ({qtd})", usuario)

                    conn.commit()
                    msg = f"Estoque do produto '{nome}' atualizado de {estoque_atual} para {novo_estoque}."
                else:
                    msg = "Produto não encontrado para atualização."

                cur.close()
                conn.close()
            except Exception as e:
                msg = f"Erro ao atualizar estoque: {e}"

    return render_template('estoque.html', usuario=usuario, msg=msg)