import os
# بالای فایل، بعد از importها این خط رو اضافه کن
from flask import Flask, request, jsonify, Response, session, send_from_directory, url_for
""" from utils import 
from config import  """
import uuid
import threading


app = Flask(__name__,)
app.secret_key = 'my_secret_key' 


@app.route('/')
def index():

    return send_from_directory('static/html', 'index.html')





if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4002)  