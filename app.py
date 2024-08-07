from flask import Flask, render_template, request, flash, redirect, url_for, session

import sqlite3
import random
import numpy as np
import csv
import pickle
import json
from flask_ngrok import run_with_ngrok
import nltk
from keras.models import load_model
from nltk.stem import WordNetLemmatizer



lemmatizer = WordNetLemmatizer()

model = load_model("chatbot_mode2.h5")
intents = json.loads(open("intents1.json").read())
words = pickle.load(open("words.pkl", "rb"))
classes = pickle.load(open("classes.pkl", "rb"))

app = Flask(__name__)
app.secret_key = "123"

database='new1.db'
conn=sqlite3.connect(database)
cursor=conn.cursor()
cursor.execute("create table if not exists register(id integer primary key autoincrement,name text,mail text,password text)")
conn.commit()
conn.close()
values = []


@app.route('/')
def register1():
    return render_template('register.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        mail = request.form['mail']
        password = request.form['password']
        con = sqlite3.connect(database)
        con.row_factory = sqlite3.Row
        cursor = con.cursor()
        cursor.execute("select * from register where mail=? AND password=?",(mail,password))
        data=cursor.fetchone()
        if data is None:
            return render_template('register.html', show_alert3=True)
        else:
            conn=sqlite3.connect(database)
            cursor=conn.cursor()
            cursor.execute("select * from register where mail=?",(mail,))
            results=cursor.fetchone()
            conn.commit()
            return render_template('chatbot.html')

    return redirect(url_for("index"))





@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        name=request.form['name']
        mail=request.form['mail']
        password=request.form['password']
        con=sqlite3.connect(database)
        cursor=con.cursor()
        cursor.execute(" SELECT mail FROM register WHERE mail=?",(mail,))
        registered=cursor.fetchall()
        if registered:
            return render_template('register.html',show_alert1=True)

        else:
            cursor.execute("insert into register(name,mail,password)values(?,?,?)",(name,mail,password))
            con.commit()
            return render_template('register.html', show_alert2=True)


    return render_template('register.html')

@app.route('/logout')
def logout():
       session.clear()
       return redirect(url_for("index"))
    
@app.route('/')
@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route("/get", methods=["POST"])
def get_bot_response():
    msg = request.form["msg"]
    return chatbot_response(msg)


def chatbot_response(msg):
    messg = msg.lower()
    print(msg)
    
    ints = predict_class(msg, model)
    res = getResponse(ints, intents)
    return res


    
    # chat functionalities
def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words


# return bag of words array: 0 or 1 for each word in the bag that exists in the sentence
def bow(sentence, words, show_details=True):
    # tokenize the pattern
    sentence_words = clean_up_sentence(sentence)
    # bag of words - matrix of N words, vocabulary matrix
    bag = [0] * len(words)
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:
                # assign 1 if current word is in the vocabulary position
                bag[i] = 1
                if show_details:
                    print("found in bag: %s" % w)
    return np.array(bag)


def predict_class(sentence, model):
    # filter out predictions below a threshold
    p = bow(sentence, words, show_details=False)
    res = model.predict(np.array([p]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    # sort by strength of probability
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
    return return_list


def getResponse(ints, intents_json):
    tag = ints[0]["intent"]
    list_of_intents = intents_json["intents"]
    result = "Sorry, I don't understand that."

    for i in list_of_intents:
        if i["tag"] == tag:
            result = random.choice(i["responses"])
            break

    return result



if __name__ == '__main__':
    app.run(port=800)


###

