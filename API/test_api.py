import unittest
from flask import Flask, request, jsonify
from flask_testing import TestCase
import json
import os

# Import the app and methods from the provided script.
from dttsa import app, runQoSTest, runBackupQoSTest

class MyTest(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app

    def test_eval_route(self):
        response = self.client.get('/eval')
        self.assertEqual(response.status_code, 200)
        self.assertIn('status', response.json)

    def test_testbackupservices_route(self):
        response = self.client.get('/testbackupservices?testcount=1')
        self.assertEqual(response.status_code, 200)
        self.assertIn('status', response.json)
        self.assertEqual(response.json['status'], 'QoS Test Started')

    def test_testqos_route(self):
        response = self.client.get('/testqos?testcount=1&c=10&l=5')
        self.assertEqual(response.status_code, 200)
        self.assertIn('status', response.json)
        self.assertEqual(response.json['status'], 'QoS Test Started')

    def test_setconfigs_route(self):
        response = self.client.get('/setconfigs?astra=http://example.com&db=127.0.0.1')
        self.assertEqual(response.status_code, 200)
        self.assertIn('http://example.com', response.data.decode())

    def test_restart_service_route(self):
        with self.assertRaises(SystemExit):
            self.client.get('/restart')

    def test_dttsa_details_route(self):
        response = self.client.get('/dttsa_details')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('version', data)
        self.assertIn('astra', data)
        self.assertIn('db', data)

    def test_dttsa_start_route(self):
        response = self.client.get('/dttsa_start')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode(), 'Success')

if __name__ == '__main__':
    unittest.main()
