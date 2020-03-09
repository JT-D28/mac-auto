import psycopg2 as pg2
 
# 返回数据库PostgreSQL连接
def get_db_conn():
    # 创建连接
    return pg2.connect(database='luna_test', user='luna_test', password='luna_test1bbbb', host='10.60.44.229', port=5432)
 
 
# 操作数据库PostgreSQL，返回一条结果
def db_fetchone(sql):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchone()  # 返回一条结果，返回多条结果使用rows = cur.fetchall()
 
        return rows[0]
    except pg2.DatabaseError as e:
        print('Error $s' % e)
 
    finally:
        conn.commit()
        cur.close()
        conn.close()

print(db_fetchone('select 1'))