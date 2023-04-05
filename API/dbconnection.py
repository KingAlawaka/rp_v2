from distutils.log import error
import os
from pymongo import MongoClient
import psycopg2
#from pymongo import ServerSelectionTimeoutError
import configparser

class DBConnection:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('environment_config.ini')
        #print(config['database']['DB_IP'])
        self.DB_IP = config['database']['DB_IP']
        self.DB_name = config['database']['DB_NAME']
        self.DB_user = config['database']['DB_USER']
        self.DB_password = config['database']['DB_PASSWORD']

    def get_db_connection(self):
        conn = psycopg2.connect(host=self.DB_IP,database=self.DB_name,user=self.DB_user,password=self.DB_password)
        return conn

    def db_connect(self):
        maxSevSelDelay = 1
        try:
            mongo_host = 'localhost'
            mongo_port = 27017

            if 'MONGO_PORT_27017_TCP_ADDR' in os.environ:
                mongo_host = os.environ['MONGO_PORT_27017_TCP_ADDR']
            
            if 'MONGO_PORT_27017_TCP_PORT' in os.environ:
                mongo_port = int(os.environ['MONGO_PORT_27017_TCP_PORT'])
            
            client = MongoClient(mongo_host,mongo_port,ServerSelectionTimeoutMS=maxSevSelDelay)
            client.server_info()
            return client
        except error as err:
            exit("Failed to connect to Mongo DB")