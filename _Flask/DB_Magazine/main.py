from flask import Flask, render_template, request, redirect, session, flash
from flaskext.mysql import MySQL 
import os
import pymysql
from bs4 import BeautifulSoup
import requests
import operator
import datetime

mysql = MySQL(cursorclass=pymysql.cursors.DictCursor)
app = Flask(__name__)

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '1234'
app.config['MYSQL_DATABASE_DB'] = 'dbmagazine'
app.config['MYSQL_DATABASE_HOST'] = '192.168.22.103'

app.config.from_object(__name__)
app.secret_key = os.urandom(12)

mysql.init_app(app)

@app.route('/')
def index():
    result = tetrisrank()
    lol=lol_opgg()
    earlybird = early_bird()
    if not session.get('user_info'):
        return render_template('index.html', gameranking=result , lol=lol, early_bird=earlybird)
    else:
        if session.get('user_info')[0]['name'] == "김나영":
            return render_template('nayoung_index.html', user_info=session.get('user_info'), gameranking=result, lol=lol, early_bird=earlybird)
        else:
            return render_template('after_login_index.html', user_info=session.get('user_info'), gameranking=result, lol=lol, early_bird=earlybird)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        pw = request.form['password']
        conn = mysql.connect()
        cur = conn.cursor()
        sql = "SELECT * FROM student WHERE phone=%s"
        cur.execute(sql, phone)
        try:
            result = cur.fetchall()
            if result[0]['password'] == pw:
                session['user_info'] = result
                return redirect('/')
            else:
                return render_template('loginview.html')
        except:
            return render_template('loginview.html')
        return render_template('index.html')
    else:
        return render_template('loginview.html')

@app.route('/logout')
def logout():
    session.pop('user_info')
    return redirect('/')

@app.route('/deleteuser', methods=['GET', 'POST'])
def deleteuser():
    if request.method == 'GET':
        conn = mysql.connect()
        cur = conn.cursor()
        sql = "DELETE FROM student WHERE phone=%s"
        cur.execute(sql, session.get('user_info')[0]['phone'])
        conn.commit()
        conn.close()
        if session.get('user_info'):
            session.pop('user_info')
        return redirect('/')
    else:
        return redirect('/')

@app.route('/game', methods=['GET', 'POST'])
def game():
    if request.method == 'POST':
        if session.get('user_info'):
            name = session.get('user_info')[0]['name']
            score = request.form['score']
            game_name = '테트리스'
            phone = session.get('user_info')[0]['phone']
            sql = "INSERT INTO game (name, score, game_name, phone, score_date) VALUES (%s,%s,%s, %s, now())"
            conn = mysql.connect()
            cur = conn.cursor()
            data = (name, score, game_name, phone)
            cur.execute(sql, data)
            conn.commit()
            conn.close()
        return redirect('/')
    else:
        return render_template('game.html')

@app.route('/tetris_ranking')
def tetris_ranking():
    if not session.get('user_info'):
        return render_template('loginview.html')
    else:
        ranking = tetrisrank()
        return render_template('tetris_ranking.html', ranking=ranking, user_info=session.get('user_info'))

@app.route('/lol_ranking')
def lol_ranking():
    if not session.get('user_info'):
        return render_template('loginview.html')
    else:
        lol=lol_opgg()
        return render_template('lol_ranking.html', lol=lol, user_info=session.get('user_info'))


@app.route('/attendance') #메인
def attendance():
    if session.get('user_info'):
        return render_template('attendance.html', user_info=session.get('user_info'))
    else:
        return render_template('loginview.html')

@app.route('/present', methods=['GET','POST']) #출석입력
def present():
    if request.method == 'POST':
        #출석정보를 입력
        name = request.form['name']
        conn = mysql.connect()
        cur = conn.cursor()
        sql = "INSERT INTO attendance (name) values(%s)"
        cur.execute(sql, name)
        conn.commit()
        conn.close()
        print("출석 뿅!")
        return redirect('/plist')
    else:
        return render_template('presentform.html')

@app.route('/plist') #출석리스트
def plist():
    # SELECT 해와서 정보를 list.html 에 넘긴다
    conn = mysql.connect()
    cur = conn.cursor()
    sql = "select name 이름, date_format(p_day, '%y-%m-%d') 날짜 from attendance where date_format(p_day, '%T') <='09:10:55' and date_format(p_day, '%y-%m-%d')=date_format(now(),'%y-%m-%d');"
    cur.execute(sql)
    lists = cur.fetchall()
    print('lists===', lists)
    conn.close()
    return render_template('plist.html', lists=lists)

@app.route('/late', methods=['GET','POST']) #지각입력
def late():
    if request.method == 'POST':
        #지각정보를 입력
        name = request.form['name']
        sql = "insert into attendance (name) values(%s)"
        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute(sql, name)
        conn.commit()
        conn.close()
        print("오긴왔네?!")
        return redirect('/llist')
    else:
        return render_template('lateform.html')

@app.route('/llist') #지각리스트
def llist():
    # SELECT 해와서 정보를 list.html 에 넘긴다
    sql = "select name 이름, date_format(p_day, '%y-%m-%d') 날짜 from attendance where date_format(p_day, '%y-%m-%d')=date_format(now(),'%y-%m-%d') and date_format(p_day, '%T')>='09:11:00' and date_format(p_day, '%T')<='14:00:00';"
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute(sql)
    late_lists = cur.fetchall()
    print('late_lists===', late_lists)
    conn.close()
    return render_template('llist.html', late_lists=late_lists)

@app.route('/select_l_count') #지각수 조회
def s_llist():
    # SELECT 해와서 정보를 list.html 에 넘긴다
    sql="select name 이름, count(*) as 지각수  from attendance where date_format(p_day, '%T') >='09:11:00' and date_format(p_day, '%T')<='14:00:00' and date_format(p_day, '%M')=date_format(now(), '%M') and date_format(p_day, '%y-%m-%d')<=date_format(now(),'%y-%m-%d') group by name;"
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute(sql)
    slate_lists = cur.fetchall()
    print('late_lists===', slate_lists)
    conn.close()
    return render_template('select_l_count.html', slate_lists=slate_lists)

@app.route('/absent', methods=['GET','POST']) #결석입력
def absent():
    if request.method == 'POST':
        #결석정보를 입력
        name = request.form['name']
        sql = "insert into attendance (name) values(%s)"
        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute(sql, name)
        conn.commit()
        conn.close()
        print("결석 ㅜ!")
        return redirect('/alist')
    else:
        return render_template('absentform.html')

@app.route('/alist') #결석리스트
def alist():
    # SELECT 해와서 정보를 list.html 에 넘긴다
    sql = "select name 이름, date_format(p_day, '%y-%m-%d') 날짜 from attendance where date_format(p_day, '%y-%m-%d')=date_format(now(),'%y-%m-%d') and date_format(p_day, '%T')>='14:00:01';"
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute(sql)
    absent_lists = cur.fetchall()
    print('absent_lists===', absent_lists)
    conn.close()
    return render_template('alist.html', absent_lists=absent_lists)

@app.route('/select_a_count') #결석수 조회
def s_alist():
    # SELECT 해와서 정보를 list.html 에 넘긴다
    sql = "select name 이름, count(*) as 결석수  from attendance where date_format(p_day, '%T') >='14:00:01' and date_format(p_day, '%M')=date_format(now(), '%M') and date_format(p_day, '%y-%m-%d')<=date_format(now(),'%y-%m-%d') group by name;"
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute(sql)
    alate_lists = cur.fetchall()
    print('absent_lists===', alate_lists)
    conn.close()
    return render_template('select_a_count.html', alate_lists=alate_lists)

@app.route('/calendar')
def calendar():
    if session.get('user_info'):
        return render_template('calendar.html', user_info=session.get('user_info'))
    else:
        return render_template('loginview.html')

def lol_opgg():
    sql = "SELECT lol.lol_id, student.name FROM lol INNER JOIN student ON lol.phone=student.phone"
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute(sql)
    lol_id = cur.fetchall()
    conn.close()
    
    lol = []
    for id in lol_id:
        info = {}
        url = "http://www.op.gg/summoner/userName="+id['lol_id']
        html_doc = requests.get(url).text
        soup = BeautifulSoup(html_doc, 'html.parser')
        result = soup.find("div", {"class" : "ChampionBox Ranked"})
        most_champion = result.find("div", {"class" : "ChampionName"}).get_text()
        kda = result.find("div", {"class" : "PersonalKDA"}).get_text()
        played = result.find("div", {"class" : "Played"}).get_text()
        info['lol_id'] = id['lol_id']
        info['name'] = id['name']
        info['most_champion'] = most_champion.replace('\n', '').replace('\t', '')
        info['kda'] = kda.replace('\n', '').replace('\t', '').replace('KDA', ' ')
        info['played'] = played.replace('\n', '').replace('\t', '')[:3].replace('%', '') + '%'
        lol.append(info)
    temp = []
    for i in lol:
        temp.append(int(i['played'].replace('%','')))
    temp.sort(reverse=True)

    result = []
    for j in temp:
        for i in lol:                
            if i['played'] == str(j)+'%':
                result.append(i)
    return result

def tetrisrank():
    conn = mysql.connect()
    cur = conn.cursor()
    sql = "SELECT * FROM game WHERE game_name='테트리스' ORDER BY score DESC"
    cur.execute(sql)
    result = cur.fetchall()
    conn.close()
    return result

def early_bird():
    try:
        conn = mysql.connect()
        cur = conn.cursor()
        now = datetime.datetime.now().strftime('%Y-%m-%d')
        print(now)
        sql = "SELECT * FROM attendance WHERE DATE(p_day) = " + "'" +now+ "'" + " ORDER BY p_day ASC"
        cur.execute(sql)
        result = cur.fetchall()
        conn.close()
    except:
        result = ['없음', '없음', '없음']
    return result

if __name__=='__main__':
    app.run(debug=True)