import os
import psycopg2

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
"postgresql://neondb_owner:npg_BDSw8HQc4ETC@ep-noisy-wildflower-acwatwjg-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

TABELA_PRODUTO = "produto"
TABELA_USUARIO = "usuario"
TABELA_VENDAS = "vendas"
TABELA_PRODUTOBKP = "produtobkp"

def conectar_banco():
    db_url = DATABASE_URL  # Usa a variável definida no topo!
    
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    return psycopg2.connect(db_url)

def registrar_backup(cur, prod_id, nome, preco, estoque, operacao, responsavel):
    query = f"""
        INSERT INTO {TABELA_PRODUTOBKP} (produto_id, nome, preco, estoque, operacao, responsavel)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cur.execute(query, (prod_id, nome, preco, estoque, operacao, responsavel))