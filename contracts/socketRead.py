from websocket import create_connection
import json
import requests

oracle_url = "http://127.0.0.1:9100"
ws = create_connection("ws://localhost:5000/ws?namespace=default&ephemeral&autoack&filter.events=blockchain_event_received")
while(True):
    result =  ws.recv()
    print ("Received '%s'" % result)
    json_obj = json.loads(result)
    print(json_obj['blockchainEvent']['output'])
    
    url = oracle_url +"/return?dt="+str(json_obj['blockchainEvent']['output']['dt'])+"&con_dt="+str(json_obj['blockchainEvent']['output']['condt'])+"&reply="+str(json_obj['blockchainEvent']['output']['verdict'])
    res = requests.get(url)

