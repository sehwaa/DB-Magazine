from flask import Flask, render_template, request, redirect, session, flash
from flaskext.mysql import MySQL 
import os
import pymysql
from bs4 import BeautifulSoup
import requests
import operator
import datetime
import json

mysql = MySQL(cursorclass=pymysql.cursors.DictCursor)
app = Flask(__name__)

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '1234'
app.config['MYSQL_DATABASE_DB'] = 'dbmagazine'
app.config['MYSQL_DATABASE_HOST'] = '192.168.113.166'

app.config.from_object(__name__)
app.secret_key = os.urandom(12)
mysql.init_app(app)

lol_api_key = "RGAPI-33b0f2d2-8d59-4279-b6fc-28e9906cef07"
headers = {
    "Origin": "https://developer.riotgames.com",
    "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Riot-Token": "RGAPI-33b0f2d2-8d59-4279-b6fc-28e9906cef07",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
}

@app.route('/')
def index():
    getlolSummonerId()
    result = tetrisrank()
    earlybird = early_bird()
    top3 = loltop3()
    if not session.get('user_info'):
        return render_template('index.html', gameranking=result , early_bird=earlybird, top3=top3)
    else:
        return render_template('after_login_index.html', user_info=session.get('user_info'), gameranking=result, early_bird=earlybird, top3=top3)

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
    if session.get('user_info'):
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
            return render_template('game.html', user_info=session.get('user_info'))
    else:
        return render_template('loginview.html')

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
        lol=getlollist()
        for i in lol['solo']:
            i['win_rate'] = round(i['win_rate'])

        for i in lol['team']:
            i['win_rate'] = round(i['win_rate'])
        return render_template('lol_ranking.html', lol=lol, user_info=session.get('user_info'))


@app.route('/attendance') #메인
def attendance():
    if session.get('user_info'):
        return render_template('attendance.html', user_info=session.get('user_info'))
    else:
        return render_template('loginview.html')

@app.route('/present', methods=['GET','POST']) #출석입력
def present():
    if session.get('user_info'):
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
            return render_template('/plist')
        else:
            return render_template('presentform.html', user_info=session.get('user_info'))
    else:
        return render_template('loginview.html')

@app.route('/plist') #출석리스트
def plist():
    if session.get('user_info'):
        # SELECT 해와서 정보를 list.html 에 넘긴다
        conn = mysql.connect()
        cur = conn.cursor()
        sql = "select name 이름, date_format(p_day, '%y-%m-%d') 날짜 from attendance where date_format(p_day, '%T') <='09:10:55' and date_format(p_day, '%y-%m-%d')=date_format(now(),'%y-%m-%d');"
        cur.execute(sql)
        lists = cur.fetchall()
        print('lists===', lists)
        conn.close()
        return render_template('plist.html', lists=lists, user_info=session.get('user_info'))
    else:
        return render_template('loginview.html')

@app.route('/late', methods=['GET','POST']) #지각입력
def late():
    if session.get('user_info'):
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
            return render_template('lateform.html', user_info=session.get('user_info'))
    else:
        return render_template('loginview.html', user_info=session.get('user_info'))

@app.route('/llist') #지각리스트
def llist():
    if session.get('user_info'):
        # SELECT 해와서 정보를 list.html 에 넘긴다
        sql = "select name 이름, date_format(p_day, '%y-%m-%d') 날짜 from attendance where date_format(p_day, '%y-%m-%d')=date_format(now(),'%y-%m-%d') and date_format(p_day, '%T')>='09:11:00' and date_format(p_day, '%T')<='14:00:00';"
        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute(sql)
        late_lists = cur.fetchall()
        print('late_lists===', late_lists)
        conn.close()
        return render_template('llist.html', late_lists=late_lists, user_info=session.get('user_info'))
    else:
        return render_template('loginview.html')

@app.route('/select_l_count') #지각수 조회
def s_llist():
    if session.get('user_info'):
        # SELECT 해와서 정보를 list.html 에 넘긴다
        sql="select name 이름, count(*) as 지각수  from attendance where date_format(p_day, '%T') >='09:11:00' and date_format(p_day, '%T')<='14:00:00' and date_format(p_day, '%M')=date_format(now(), '%M') and date_format(p_day, '%y-%m-%d')<=date_format(now(),'%y-%m-%d') group by name;"
        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute(sql)
        slate_lists = cur.fetchall()
        print('late_lists===', slate_lists)
        conn.close()
        return render_template('select_l_count.html', slate_lists=slate_lists, user_info=session.get('user_info'))
    else:
        return render_template('loginview.html')

@app.route('/absent', methods=['GET','POST']) #결석입력
def absent():
    if session.get('user_info'):
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
            return render_template('absentform.html', user_info=session.get('user_info'))
    else:
        return render_template('loginview.html', user_info=session.get('user_info'))

@app.route('/alist') #결석리스트
def alist():
    if session.get('user_info'):
        # SELECT 해와서 정보를 list.html 에 넘긴다
        sql = "select name 이름, date_format(p_day, '%y-%m-%d') 날짜 from attendance where date_format(p_day, '%y-%m-%d')=date_format(now(),'%y-%m-%d') and date_format(p_day, '%T')>='14:00:01';"
        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute(sql)
        absent_lists = cur.fetchall()
        print('absent_lists===', absent_lists)
        conn.close()
        return render_template('alist.html', absent_lists=absent_lists, user_info=session.get('user_info'))
    else:
        return render_template('loginview.html')

@app.route('/select_a_count') #결석수 조회
def s_alist():
    if session.get('user_info'):
        # SELECT 해와서 정보를 list.html 에 넘긴다
        sql = "select name 이름, count(*) as 결석수  from attendance where date_format(p_day, '%T') >='14:00:01' and date_format(p_day, '%M')=date_format(now(), '%M') and date_format(p_day, '%y-%m-%d')<=date_format(now(),'%y-%m-%d') group by name;"
        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute(sql)
        alate_lists = cur.fetchall()
        print('absent_lists===', alate_lists)
        conn.close()
        return render_template('select_a_count.html', alate_lists=alate_lists, user_info=session.get('user_info'))
    else:
        return render_template('loginview.html')

@app.route('/calendar')
def calendar():
    if session.get('user_info'):
        return render_template('calendar.html', user_info=session.get('user_info'))
    else:
        return render_template('loginview.html')

@app.route('/tedupload', methods=['GET', 'POST'])
def tedupload():
    if request.method == 'POST':
        ted_url = request.form['ted_url']
        sql = "INSERT INTO ted(ted_url,tdate) VALUES(%s,now())"
        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute(sql, ted_url)
        conn.commit()
        conn.close()
        return render_template('ted_upload.html', user_info=session.get('user_info'))
    else:
        if session.get('user_info'):
            return render_template('ted_upload.html', user_info=session.get('user_info'))
        else:
            return render_template('loginview.html')

@app.route('/ted', methods=['GET', 'POST'])
def ted():
    if session.get('user_info'):
        sql = "SELECT * FROM ted ORDER BY tdate DESC"
        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute(sql)
        url = cur.fetchall()
        return render_template('ted.html', url=url, user_info=session.get('user_info'))
    else:
        return render_template('loginview.html')

@app.route('/board')
def board():
    if session.get('user_info'):
        conn = mysql.connect()
        cur = conn.cursor()
        sql = "select * from board order by num desc"
        cur.execute(sql)
        lists = cur.fetchall()
        return render_template('board.html', lists=lists, user_info=session.get('user_info'))
    else:
        return render_template('loginview.html')
    
@app.route('/write', methods=['GET','POST'])
def write():
    if request.method == 'POST':
        # 넘어온 값을 받아서 insert
        title = request.form['title']
        content = request.form['content']
        writer = request.form['writer']
        pwd = request.form['pwd']
        sql = "insert into board(title, content, writer, pwd) values(%s, %s, %s, %s)"
        data = (title, content, writer, pwd)
        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute(sql, data)
        conn.commit()
        conn.close()
        return redirect('/board')

@app.route('/like/<int:num>')
def like(num):
    #조아요 증가코드
    sql_update = "UPDATE board SET likes=likes+1 where num=%s"
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute(sql_update, num)
    conn.commit()
    sql = "SELECT * FROM board WHERE num=%s"
    cur.execute(sql, num)
    b = cur.fetchone()
    conn.close()
    return redirect('/board#'+str(num+1))

@app.route('/unlike/<int:num>')
def unlike(num):
    #시러요 증가코드
    sql_update = "UPDATE board SET unlikes=unlikes+1 where num=%s"
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute(sql_update, num)
    conn.commit()
    sql = "SELECT * FROM board WHERE num=%s"
    cur.execute(sql, num)
    b = cur.fetchone()
    conn.close()
    return redirect('/board#'+str(num+1))

@app.route('/delete', methods=['POST'])
def delete():
    # 글번호와 비밀번호를 받아서 삭제(DELETE) 후 리스트로 간다
    pwd = request.form['pwd']
    sql = "DELETE FROM board WHERE pwd=%s"
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute(sql, pwd)
    
    conn.commit()
    conn.close()
    return redirect('/board#1')

@app.route('/read/<title>')
def read(title):
    if session.get('user_info'):
        #조회수 증가 코드
        conn = mysql.connect()
        cur = conn.cursor()
        sql_update = "UPDATE nayoung SET hit=hit+1 WHERE title=%s"
        cur.execute(sql_update, title)
        conn.commit()
        #글 하나를 SELECT 해서 read.html에 넘겨준다
        conn = mysql.connect()
        cur = conn.cursor()
        sql = "SELECT * FROM nayoung WHERE title=%s"
        cur.execute(sql, title)
        conn.commit()
        nb = cur.fetchone()
        print(nb)  #nb=nayoung_board
        return render_template('read.html', nb=nb, user_info=session.get('user_info'))
        #return 'read OK'
    else:
        return render_template('loginview.html')

@app.route('/column')
def column():
    return render_template('nyindex.html', user_info=session.get('user_info'))

@app.route('/cboard', methods=['GET', 'POST'])
def cboard():
    if request.method == "POST":
        title = request.form['title']
        content = request.form['editor1'].replace('<p>','').replace('</p>','').replace('&nbsp','').replace(';', ' ')
        preview = request.form['preview']
        conn = mysql.connect()
        cur = conn.cursor()
        sql = "INSERT into nayoung (title,content,preview,hit) values (%s,%s,%s, 0)"
        cur.execute(sql,(title,content,preview))
        conn.commit()
        conn.close()
        return redirect('/list')
    else:
        return render_template('cboard.html')

@app.route('/list')
def listaaa():
    if session.get('user_info'):
        conn = mysql.connect()
        cur = conn.cursor()
        sql = "SELECT * from nayoung"
        cur.execute(sql)
        result = cur.fetchall()
        conn.close()
        return render_template('list.html', lists=result, user_info=session.get('user_info'))
    else:
        return render_template('loginview.html')

@app.route('/story1/')
def story1():
    return render_template('story1.html')


@app.route('/story2/')
def story2():
    return render_template('story2.html')


@app.route('/story3/')
def story3():
    return render_template('story3.html')

@app.route('/update/<title>')
def updateform(title):
    #업데이트 할 글을 SELECT해서 updateform.html 에 넘긴다
    sql = "SELECT * FROM nayoung WHERE title=%s"
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute(sql, title)
    nb = cur.fetchone()
    conn.close()
    return render_template('updateform.html', nb=nb)


@app.route('/update', methods=['POST'])
# methods에 get생략 가능 기본값이라서
def update():
    #넘어온 값들로 UPDATE한 후 리스트로 이동
    otitle = request.form['old_title']     
    title = request.form['title']    
    preview = request.form['preview']
    content = request.form['content']
    print(otitle)
    sql = '''
    UPDATE nayoung
    SET title = %s, preview=%s, content=%s WHERE title=%s
    '''
    datas = (title, preview, content, otitle)
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute(sql, datas)
    conn.commit()
    conn.close()
    return redirect('/list')
    # return 'update ok'

@app.route('/deletecolumn/<int:num>')
def deleteform(num):
    return render_template('deleteform.html', num=num)

@app.route('/deletecolumn', methods=['POST'])
def deletecolumn():
    num = request.form['num']
    sql = 'DELETE FROM nayoung WHERE num=%s'
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute(sql, num)
    conn.commit()
    conn.close()
    return redirect('/list')

@app.route('/lunch')
def lunch():
    if session.get('user_info'):
        return render_template('mainview.html')
    else:
        return render_template('loginview.html')

@app.route('/menu1')
def menu1():
    conn = mysql.connect()
    cur = conn.cursor()
    sql = "SELECT * FROM foodreview"
    cur.execute(sql)
    result = cur.fetchall()
    conn.close()
    return render_template('menu1.html', foodreview=result)

@app.route('/process', methods=['GET', 'POST'])
def process():
    if request.method == 'POST':
        writer = request.form['writer']
        review = request.form['review']
        conn = mysql.connect()
        cur = conn.cursor()
        sql="INSERT INTO foodreview (writer, review) VALUES(%s,%s)"
        cur.execute(sql, (writer, review))
        conn.commit()
        conn.close()
        return redirect('/menu1')
    else:
        return redirect('/menu1')

#API에 사용하기 위한 summonerid 불러오기
def getlolSummonerId():
    sql = "SELECT lol.lol_id, student.name, student.phone FROM lol INNER JOIN student ON lol.phone=student.phone"
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute(sql)
    lol_id = cur.fetchall()
    
    url = "https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/"
    
    response_list = []
    for id in lol_id:
        response = requests.get(url+id['lol_id']+"?api_key="+lol_api_key, headers=headers)
        rep = response.content.decode('utf-8').replace("'", '"')
        data = json.loads(rep)
        response_list.append(data)
        sql2 = "UPDATE lol SET puuid=%s, summonerLevel=%s, revisionDate=%s, id=%s, accountId=%s WHERE phone = " + str(id['phone'])
        cur.execute(sql2, (data['puuid'], data['summonerLevel'], data['revisionDate'], data['id'], data['accountId']))
        conn.commit()
    conn.close()
    return response_list

# 랭크 티어, 승률 정보 가져오기
def getlolInfo():
    sql = "SELECT id FROM lol"
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute(sql)
    record = cur.fetchall()

    url = "https://kr.api.riotgames.com/lol/league/v4/positions/by-summoner/"

    response_list = []
    for info in record:
        response = requests.get(url+info['id']+"?api_key="+lol_api_key, headers=headers)
        rep = response.content.decode('utf-8')
        data = json.loads(rep)
        response_list.append(data)
    conn.close()
    return response_list

#솔랭/자랭 결과 가져오기
def getlollist():
    info = getlolInfo()

    conn = mysql.connect()
    cur = conn.cursor()

    sql = "SELECT name FROM student WHERE phone=(SELECT phone FROM lol WHERE lol_id=%s)"

    solo = []
    team = []

    #솔랭 / 자랭 분리
    for i in info:
        for j in i:
            if j['queueType'] == 'RANKED_SOLO_5x5':
                solo.append(j)
            else:
                team.append(j)

    #솔랭 승률계산, 토탈 판 수 계산, 이름 가져오기
    for i in solo:
        i['win_rate'] = i['wins'] / (i['wins']+i['losses']) * 100
        i['total'] = i['wins'] + i['losses']
        i['status'] = 'no'
        cur.execute(sql, i['summonerName'])
        result = cur.fetchall()
        i['name'] = result[0]['name']


    #솔랭 승률에 따라 정렬
    temp = []
    for i in solo:
        temp.append(i['win_rate'])
    temp.sort(reverse=True)

    #솔랭 점수에 따른 정렬 결과
    soloresult = []
    for j in temp:
        for i in solo:
            if i['win_rate'] == j and i['status'] == 'no':
                soloresult.append(i)
                i['status'] = 'ok'
                break

    #자랭 승률계산, 토탈 판 수 계산
    for i in team:
        i['win_rate'] = i['wins'] / (i['wins']+i['losses']) * 100
        i['total'] = i['wins'] + i['losses']
        i['status'] = 'no'
        cur.execute(sql, i['summonerName'])
        result = cur.fetchall()
        i['name'] = result[0]['name']

    conn.close()

    temp2 = []
    for i in team:
        temp2.append(i['win_rate'])
    temp2.sort(reverse=True)

    #자랭 점수에 따른 정렬 결과
    teamresult = []
    for j in temp2:
        for i in team:
            if i['win_rate'] == j and i['status'] == 'no':
                teamresult.append(i)
                i['status'] = 'ok'
                break

    result = dict()
    result['solo'] = soloresult
    result['team'] = teamresult
    return result

#솔랭 승률로 top3 추출
def loltop3():
    lollist = getlollist()
    lollist2 = lollist['solo']
    
    #top3 nickname list
    top_list = []
    top_list.append(lollist2[0]['summonerName'])
    top_list.append(lollist2[1]['summonerName'])
    top_list.append(lollist2[2]['summonerName'])

    conn = mysql.connect()
    cur = conn.cursor()

    sql = "SELECT name FROM student WHERE phone=(SELECT phone FROM lol WHERE lol_id=%s)"
    
    top3_list = []
    for idx in top_list:
        cur.execute(sql, idx)
        result = cur.fetchall()
        top3_list.append(result)
    conn.close()

    #top3 승률
    top3_winrate = []
    top3_winrate.append(round(lollist2[0]['win_rate']))
    top3_winrate.append(round(lollist2[1]['win_rate']))
    top3_winrate.append(round(lollist2[2]['win_rate']))

    top3_list.append(top3_winrate)

    return top3_list

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
        info['status'] = 'no'
        lol.append(info)
    temp = []
    for i in lol:
        temp.append(int(i['played'].replace('%','')))
    temp.sort(reverse=True)

    result = []
    for j in temp:
        for i in lol:
            if i['played'] == str(j)+'%' and i['status'] == 'no':
                result.append(i)
                i['status'] = 'ok'
                break
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
    conn = mysql.connect()
    cur = conn.cursor()
    now = datetime.datetime.now().strftime('%Y-%m-%d')
    sql = "SELECT * FROM attendance WHERE DATE(p_day) = " + "'" +now+ "'" + " ORDER BY p_day ASC"
    cur.execute(sql)
    result = cur.fetchall()
    conn.close()

    if len(result) >= 3:
        return result
    elif len(result) == 1 :
        result.append({'name':'없음'})
        result.append({'name':'없음'})
        return result
    elif len(result) == 2 :
        result.append({'name':'없음'})
        return result
    else:
        result = [{'name':'없음'}, {'name':'없음'}, {'name':'없음'}]
        return result


if __name__=='__main__':
    app.run(debug=True, host= '192.168.113.166')