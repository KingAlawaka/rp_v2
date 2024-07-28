from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

@app.route('/eval')
def evaluation():
    # Example implementation
    return jsonify({'status': 'success'}), 200

@app.route('/testbackupservices')
def testBackupServices():
    test_count = request.args.get('testcount')
    # Mock function to simulate behavior
    def runBackupQoSTest(test_count):
        pass
    runBackupQoSTest(test_count)
    return jsonify({"status": "QoS Test Started"}), 200

@app.route('/testqos')
def testqos():
    test_count = request.args.get('testcount')
    c_users = int(request.args.get('c'))
    loop = int(request.args.get('l'))
    # Mock function to simulate behavior
    def runQoSTest(iteration_count, concurrent_users, loop_times):
        pass
    runQoSTest(iteration_count=test_count, concurrent_users=c_users, loop_times=loop)
    return jsonify({"status": "QoS Test Started"}), 200

@app.route('/setconfigs')
def setConfigs():
    if 'astra' in request.args:
        app.config['API_VULNERBILITY_SERVICE_URL'] = request.args.get('astra')
    if 'db' in request.args:
        app.config['db_ip'] = request.args.get('db')
    return app.config.get('API_VULNERBILITY_SERVICE_URL', ''), 200

@app.route('/restart')
def restartService():
    os._exit(0)

@app.route('/dttsa_details')
def DTTSAStatus():
    return json.dumps({
        'version': "v7",
        'astra': app.config.get('API_VULNERBILITY_SERVICE_URL', ''),
        'db': app.config.get('db_ip', '')
    })

@app.route('/dttsa_start')
def startDTTSA():
    # Mock function to simulate behavior
    def runSchedulerJobs():
        pass
    runSchedulerJobs()
    return "Success"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)
