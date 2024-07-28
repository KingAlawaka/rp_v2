#https://github.com/schemathesis/schemathesis/blob/master/example/openapi.json
import unittest
import requests
import json

class TestLiveFlaskService(unittest.TestCase):
    BASE_URL = 'http://localhost:9000'  # Update this URL to your live service URL if different

    def test_eval_route(self):
        response = requests.get(f'{self.BASE_URL}/eval')
        self.assertEqual(response.status_code, 200)
        self.assertIn('status', response.json())

    def test_testbackupservices_route(self):
        response = requests.get(f'{self.BASE_URL}/testbackupservices', params={'testcount': 1})
        self.assertEqual(response.status_code, 200)
        self.assertIn('status', response.json())
        self.assertEqual(response.json()['status'], 'QoS Test Started')

    def test_testqos_route(self):
        response = requests.get(f'{self.BASE_URL}/testqos', params={'testcount': 1, 'c': 10, 'l': 5})
        self.assertEqual(response.status_code, 200)
        self.assertIn('status', response.json())
        self.assertEqual(response.json()['status'], 'QoS Test Started')

    def test_setconfigs_route(self):
        response = requests.get(f'{self.BASE_URL}/setconfigs', params={'astra': 'http://example.com', 'db': '127.0.0.1'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('http://example.com', response.text)

    def test_dttsa_details_route(self):
        response = requests.get(f'{self.BASE_URL}/dttsa_details')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('version', data)
        self.assertIn('astra', data)
        self.assertIn('db', data)

    def test_dttsa_start_route(self):
        response = requests.get(f'{self.BASE_URL}/dttsa_start')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, 'Success')

    # def test_restart_service_route(self):
    #     response = requests.get(f'{self.BASE_URL}/restart')
    #     # Since the server restarts, we can't assert the response, 
    #     # but we can check if the response is received or if a connection error is raised
    #     try:
    #         self.assertEqual(response.status_code, 200)
    #     except requests.exceptions.ConnectionError:
    #         # ConnectionError is expected because the server restarts
    #         pass

if __name__ == '__main__':
    unittest.main()
