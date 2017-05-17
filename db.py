import csv
import sqlite3
import csv
import json


from flask import Flask, render_template, send_file, make_response, request, g

DATABASE = 'videogame.db'

app = Flask(__name__)
app.config.from_object(__name__)

def create_database():
    conn = sqlite3.connect('videogame.db')
    conn.text_factory = str
    cur = conn.cursor()
    cur.execute("""DROP TABLE IF EXISTS videogame""")
    cur.execute("""CREATE TABLE videogame
        (Rank integer, Name text, Platform text, Year integer not null,
        Genre text, Publisher text, NA_Sales float, EU_Sales float,
        JP_Sales float,Other_Sales float, Global_Sales float)""")

    with open('vgsales.csv', 'r') as f:
        reader = csv.reader(f.readlines()[1:1000])  # exclude header line
    cur.executemany("""INSERT INTO videogame VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (row for row in reader))
    conn.commit()
    conn.close()


def connect_to_database():
    create_database()    
    return sqlite3.connect(app.config['DATABASE'])

def get_db():
    db = getattr(g, 'db', None)
    if db is None:
        db = g.db = connect_to_database()
    db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def execute_query(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.route("/view")
def viewdb():
    info = execute_query("""SELECT distinct Publisher, Year, Global_Sales, Name FROM videogame WHERE Year IS NOT \"N/A\" GROUP BY Publisher""")
    label = ['Publisher','Year','Global_Sales','Name']
    json_data = json.dumps([dict(zip(label,row)) for row in info])
    return json_data

@app.route("/publisher")
def sortby():
    publishers = execute_query("SELECT distinct Genre from videogame")
    label = ['name']
    json_data = json.dumps([dict(zip(label,row)) for row in publishers])
    return json_data

@app.route("/chart")
def bubble_chart():
    Genres = execute_query("SELECT distinct Genre from videogame order by Genre asc")
    series = []
    for Genre in Genres:
        data = []
        videogames = execute_query("SELECT * from videogame where Genre = ? and Year IS NOT \"N/A\"", (Genre[0],))
        for videogame in videogames:
            data.append({ 'name': videogame['Name'], 'publisher': videogame['Publisher'], 'y': videogame['Global_Sales'], 'x': videogame['Year'], 'z': videogame['Global_Sales']})
        series.append({ 'name': Genre[0], 'data': data })
    return render_template("bubble.html", series = json.dumps(series))

if __name__ == '__main__':
    app.run()