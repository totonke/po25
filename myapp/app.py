from flask import Flask,request,render_template
import mariadb

from datetime import date, datetime
import json

app = Flask(__name__)

#IP_add = "192.168.52.204"
#IP_add = "192.168.52.210"
#IP_add = "192.168.52.212"
#IP_add = "192.168.52.239"
IP_add = "192.168.52.215"
tableName = "kadai_Table"

def connect_mariadb():
    conn = mariadb.connect(
        host = IP_add,
        port = 3306,
        user = "052user",
        password = "password",
        database = "db_kadai")
    return conn

@app.route("/")
def form():
    return render_template('form.html')

@app.route("/makeTable")
def connect_db():
    try:
        conn=connect_mariadb()
        cour=conn.cursor()
        sql=f'create table {tableName} ('
        sql+="id int auto_increment primary key,device varchar(32) ,temp varchar(5), ill varchar(5), date varchar(20))"
        cour.execute(sql)
        conn.commit()
        conn.close()
        return 'Executed successfully'

    except mariadb.Error as e:
        conn.close()
        return f'DBError : {e}'
    
@app.route('/datajson',methods=['POST'])
def select_json():
    try:
        # -- select関数で記述したDB接続/SELECT文/executeの処理を記述---
        conn = connect_mariadb()
        cour = conn.cursor()
        param=[]  #request.paramData
        sdatekey = ['sdate1','sdate2']
        for key in sdatekey:
            data = request.form.get(key)
            if data =='':
                param.append(None)
            else:
                param.append(data)
                
        devno = request.form.getlist('devno')
        for dev in devno:
            param.append(dev)
        
        sql = "select * FROM kadai_Table"
        sql +=" WHERE date BETWEEN IFNULL(%s,'1000-01-01') AND IFNULL(%s,'9999-12-31')"
        flg =True
        for dev in devno:
            sql +=" AND ( "if flg else " OR "   #3項演算子　y=a if 条件　else b　→　（条件が成立したらy=a,成立しなければy=b）
            sql +="device = %s"
            flg = False
        sql +=" "if flg else " )"
        print(sql)
        cour.execute(sql,tuple(param))
        
        rows = cour.fetchall()
        keys = ['id','device','temp','ill','date']
        lists = []
        for row in rows:
            values = []
            print(row)
            for i in row:
                if isinstance(i,(datetime,date)):
                    values.append(str(i))
                else:
                    values.append(i)
                    
                    
            items = dict(zip(keys,values))
            lists.append(items)
            
        conn.close()
        kadaidata = {'kadaiData':lists}
        return render_template('table.html',collist=keys,datas=rows )
    
    except mariadb.Error as e:
        conn.close()
        return f'DBError : {e}'

@app.route("/gn/receive", methods=["POST"])
def receive():
    device = request.form.get("device")
    temp_str = request.form.get("temp")
    light_str = request.form.get("light")
    time_str = request.form.get("time")
    # dataNo_str = request.form.get("dataNo")

    if device is None or device.strip() == "":
        return "Missing device", 400

    temp_val = float(temp_str)
    light_val = int(light_str)
    # dataNo_val = safe_to_int(dataNo_str)

    conn = None
    try:
        conn = connect_mariadb()
        cur = conn.cursor()

        # mariadb-python prefers ? placeholders
        sql = f"""
        INSERT INTO {tableName} (device, temp, ill, date)
        VALUES (?, ?, ?, ?)
        """
        cur.execute(sql, (device, temp_val, light_val, time_str))
        conn.commit()

        return "OK", 200
    except mariadb.Error as e:
        if conn is not None:
            conn.rollback()
        return f"DBError: {e}", 500
    finally:
        if conn is not None:
            conn.close()
