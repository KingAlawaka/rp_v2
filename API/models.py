from flask import Flask
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50), nullable = False)
    age = db.Column(db.Integer, nullable = True)

    def __init__(self,name,age):
        self.name = name
        self.age = age

    def __repr__(self):
        return {"id": self.id, "name": self.name,"age" : self.age}
    
    @property
    def serialize(self):
        return {
            'id' : self.id,
            'name' : self.name,
            'age' : self.age
        }

class DT(db.Model):
    __tablename__ = 'test_tbl'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50), nullable = False)
    age = db.Column(db.Integer, nullable = True)

    def __init__(self,name,age):
        self.name = name
        self.age = age

    def __repr__(self):
        return {"id": self.id, "name": self.name,"age" : self.age}
    
    @property
    def serialize(self):
        return {
            'id' : self.id,
            'name' : self.name,
            'age' : self.age
        }