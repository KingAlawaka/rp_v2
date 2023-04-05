from flask import Flask,jsonify
import os

app = Flask(__name__)

@app.get("/")
def index():
    return "hello world"

@app.get("/hello")
def say_hello():
    return jsonify({"message": "hello jason"})

def start_server():
    app.run(host='0.0.0.0',port=9000)

def main():
    start_server()

if __name__ == '__main__':
    main()