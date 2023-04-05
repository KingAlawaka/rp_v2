import os
from flask import Flask,jsonify,request,Response,render_template,make_response

app = Flask(__name__)

@app.get("/test")
def testService():
    return "Ok"

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=8080)