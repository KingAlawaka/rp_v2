from flask import Flask,jsonify,Blueprint

auth = Blueprint("auth",__name__,url_prefix="/api/v1/auth/")

@auth.get("/")
def index():
    return "hello world"

@auth.get("/hello")
def say_hello():
    return jsonify({"message": "hello jason"})
