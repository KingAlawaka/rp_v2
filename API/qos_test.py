#QoS test to check reliability of the APIs
from time import sleep
import time
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import requests
import json
import os
import pdb
import ast
import inspect
import random

# import asyncio
import sys
import threading
from threading import Thread, Event, Timer
import queue

if sys.version_info < (3, 7):
    raise Exception("Requires Python 3.7 or above.")

# Change log level to error to improve client performance.
LOG_LEVEL = logging.DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Assume project structure as below:
# Scripts - python scripts
# Logs - logs
# run.bat - batch script to run

# root_path is parent folder of Scripts folder (one level up)
root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# %(levelname)7s to align 7 bytes to right, %(levelname)-7s to left.
# common_formatter = logging.Formatter('%(asctime)s [%(levelname)-7s][ln-%(lineno)-3d]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
common_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)-7s][ln-%(lineno)-3d]: %(message)s"
)

#urlToTest = "http://127.0.0.1:9100/getvalue"
urlToTest = "http://127.0.0.1:9100/send/"

# Note: To create multiple log files, must use different logger name.
def setup_logger(log_file, level=logging.INFO, name="", formatter=common_formatter):
    """Function setup as many loggers as you want."""
    handler = logging.FileHandler(log_file, mode="w")  # default mode is append
    # Or use a rotating file handler
    # handler = RotatingFileHandler(log_file,maxBytes=1024, backupCount=5)
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger


# default debug logger
debug_log_filename = root_path + os.sep + "Logs" + os.sep + "debug.log"
log = setup_logger(debug_log_filename, LOG_LEVEL, "log")

# logger for API outputs
# api_formatter = logging.Formatter('%(asctime)s: %(message)s', datefmt='%Y-%m-%d %I:%M:%S')
api_formatter = logging.Formatter("%(asctime)s: %(message)s")
api_outputs_filename = root_path + os.sep + "Logs" + os.sep + "api_outputs.log"
log_api = setup_logger(
    api_outputs_filename, LOG_LEVEL, "log_api", formatter=api_formatter
)

# pretty print Restful request to API log
# argument is request object
def pretty_print_request(request):
    """
    Pay attention at the formatting used in this function because it is programmed to be pretty printed and may differ from the actual request.
    """
    log_api.info(
        "{}\n{}\n\n{}\n\n{}\n".format(
            "-----------Request----------->",
            request.method + " " + request.url,
            "\n".join("{}: {}".format(k, v) for k, v in request.headers.items()),
            request.body,
        )
    )


# pretty print Restful request to API log
# argument is response object
def pretty_print_response(response):
    log_api.info(
        "{}\n{}\n\n{}\n\n{}\n".format(
            "<-----------Response-----------",
            "Status code:" + str(response.status_code),
            "\n".join("{}: {}".format(k, v) for k, v in response.headers.items()),
            response.text,
        )
    )


# argument is request object
# display body in json format explicitly with expected indent. Actually most of the time it is not very necessary because body is formatted in pretty print way.
def pretty_print_request_json(request):
    log_api.info(
        "{}\n{}\n\n{}\n\n{}\n".format(
            "-----------Request----------->",
            request.method + " " + request.url,
            "\n".join("{}: {}".format(k, v) for k, v in request.headers.items()),
            json.dumps(ast.literal_eval(request.body), indent=4),
        )
    )


# argument is response object
# display body in json format explicitly with expected indent. Actually most of the time it is not very necessary because body is formatted in pretty print way.
def pretty_print_response_json(response):
    log_api.info(
        "{}\n{}\n\n{}\n\n{}\n".format(
            "<-----------Response-----------",
            "Status code:" + str(response.status_code),
            "\n".join("{}: {}".format(k, v) for k, v in response.headers.items()),
            json.dumps(response.json(), indent=4),
        )
    )


class TestAPI:
    """
    Performance Test Restful HTTP API examples.
    """

    def __init__(self):
        log.debug("To load test data.")
        self.queue_results = queue.Queue()

        # test start and end time
        self.start_time = 0
        self.end_time = 0

        # request per second
        # self.rps_min = 0
        self.rps_mean = 0
        # self.rps_max = 0
        self.total_tested_requests = 0
        self.total_tested_time = 0
        self.total_pass_requests = 0

        # time per request
        self.tpr_min = 999
        self.tpr_mean = 0
        self.tpr_max = 0
        self.sum_response_time = 0

        # failures
        self.total_fail_requests = 0
        self.total_exception_requests = 0

        # event flag to set and check test time is up.
        self.event_time_up = Event()
        # event flag to indicate test is done, either normally or by interruption
        self.event_test_done = Event()

        self.timer = None

    # post with headers, json body
    def test_post_headers_body_json(self,url,sample_json):
        #payload = {"key1": 1, "key2": "value2"}
        #payload = {"msg":"test","sender":"sender"}
        payload = sample_json
        # No need to specify common headers as it is taken cared of by common self.post() function.
        # headers = {'Content-Type': 'application/json' }

        # convert dict to json by json.dumps() for body data. It is risky to use str(payload) to convert because json format must use double quotes ("")
        #url = "https://httpbin.org/post"
        #url = "http://172.17.0.1:9100/send/"
        #url = urlToTest
        resp = self.post(url, data=json.dumps(payload, indent=4))
        # assert resp != None
        if resp == None:
            log.error("Test %s failed with exception." % inspect.stack()[0][3])
            return "exception", None
        elif resp.status_code != 200:
            log.error(
                "Test %s failed with response status code %s."
                % (inspect.stack()[0][3], resp.status_code)
            )
            return "fail", resp.elapsed.total_seconds()
        # elif resp.json()["url"] != url:
        #     log.error(
        #         "Test %s failed with url %s != %s."
        #         % (inspect.stack()[0][3], resp.json()["url"], url)
        #     )
        #     return "fail", resp.elapsed.total_seconds()
        else:
            log.info("Test %s passed." % inspect.stack()[0][3])
            return "pass", resp.elapsed.total_seconds()
        """ Request HTTP body:
        {   "key1": 1, 
            "key2": "value2"
        }
        """

    # To run this test using Flask mocking service,
    # start mock service first: python flask_mock_service.py
    # Then run the tests.
    def test_mock_service(self,url):
        log.info("Calling %s." % inspect.stack()[0][3])
        #url = r"http://10.138.0.2:9100/getvalues"
        #url = urlToTest
        resp = self.get(url)

        # Convert assert for functional tests to validate for performance tests so it won't stop on a test failure.
        # assert resp != None
        # assert resp.json()["code"] == 1
        if resp == None:
            log.error("Test %s failed with exception." % inspect.stack()[0][3])
            return "exception", None
        elif resp.status_code != 200:
            log.error(
                "Test %s failed with response status code %s."
                % (inspect.stack()[0][3], resp.status_code)
            )
            return "fail", resp.elapsed.total_seconds()
        else:
            log.info("Test %s passed." % inspect.stack()[0][3])
            return "pass", resp.elapsed.total_seconds()

        """ json response
        {
        "code": 1,
        "message": "Hello, World!"
        }
        """

    def loop_test(self,request_type,url,sample_json, loop_wait=0, loop_times=sys.maxsize):
        """
        loop test of some APIs for performance test purpose.

        Parameters:
        loop_wait   wait time between two loops.
        loop_times  number of loops, default indefinite
        """
        try:
            looped_times = 0

            while (
                looped_times < loop_times
                and not self.event_time_up.is_set()
                and not self.event_test_done.is_set()
            ):
                # APIs to test

                # API - test_mock_service:
                
                if request_type =="GET":
                    test_result, elapsed_time = self.test_mock_service(url)
                    self.queue_results.put(["test_mock_service", test_result, elapsed_time])
                else:
                    #TODO temp post requests are not checked
                    ii = 0
                    #test_result, elapsed_time = self.test_post_headers_body_json(url,sample_json)
                
                # put results into a queue for statistics
                # self.queue_results.put(["test_mock_service", test_result, elapsed_time])

                # # API - test_post_headers_body_json:
                # test_result, elapsed_time = self.test_post_headers_body_json()
                # self.queue_results.put(['test_post_headers_body_json', test_result, elapsed_time])

                looped_times += 1
                sleep(loop_wait)
        except Exception as e:
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values (%s,%s,%s,%s,1);',(req_type,DT_ID,API_ID,value)
            #v = 'insert into data_tbl (req_type,DT_ID,API_ID,value,used) values ('+ req_type +','+ str(DT_ID)+','+str(API_ID)+','+str(value)+',0);'
            print("except: loop_test ", request_type, url, str(e))
    
    def getResults(self):
        results = []
        results.append(time.asctime(time.localtime(self.start_time)))
        results.append(time.asctime(time.localtime(self.end_time)))
        results.append(self.end_time - self.start_time) #duration
        results.append("%.2f" % self.rps_mean)
        results.append(self.total_tested_requests)
        results.append(self.total_tested_time)
        results.append(self.total_pass_requests)
        results.append("%.6f" % self.tpr_min)
        results.append("%.6f" % self.tpr_mean)
        results.append("%.6f" % self.tpr_max)
        results.append("%.6f" % self.sum_response_time)
        results.append(self.total_fail_requests)
        results.append(self.total_exception_requests)
        return results

    def stats(self):
        """calculate statistics"""
        end_time = time.time()
        # get the approximate queue size
        qsize = self.queue_results.qsize()
        loop = 0
        for i in range(qsize):
            try:
                result = self.queue_results.get_nowait()
                loop += 1
            except Empty:
                break
            # calc stats
            if result[1] == "exception":
                self.total_exception_requests += 1
            elif result[1] == "fail":
                self.total_fail_requests += 1
            elif result[1] == "pass":
                self.total_pass_requests += 1
                self.sum_response_time += result[2]
                if result[2] < self.tpr_min:
                    self.tpr_min = result[2]
                if result[2] > self.tpr_max:
                    self.tpr_max = result[2]

        self.total_tested_requests += loop
        # time per requests mean (avg)
        if self.total_pass_requests != 0:
            self.tpr_mean = self.sum_response_time / self.total_pass_requests
        # requests per second
        if self.start_time == 0:
            log.error("stats: self.start_time is not set, skipping rps stats.")
        else:
            # calc the tested time so far.
            tested_time = end_time - self.start_time
            self.rps_mean = self.total_pass_requests / tested_time

        # # print stats
        # print("\n-----------------Test Statistics---------------")
        # print(time.asctime())
        # print(
        #     "Total requests: %s, pass: %s, fail: %s, exception: %s"
        #     % (
        #         self.total_tested_requests,
        #         self.total_pass_requests,
        #         self.total_fail_requests,
        #         self.total_exception_requests,
        #     )
        # )
        # if self.total_pass_requests > 0:
        #     print("For pass requests:")
        #     print("Request per Second - mean: %.2f" % self.rps_mean)
        #     print(
        #         "Time per Request   - mean: %.6f, min: %.6f, max: %.6f"
        #         % (self.tpr_mean, self.tpr_min, self.tpr_max)
        #     )
        # print('\n')
        #return self.total_tested_requests,self.total_pass_requests,self.total_fail_requests,self.total_exception_requests,self.rps_mean,

    def loop_stats(self, interval=60):
        """print stats in an interval(secs) continunously

        Run this as a separate thread so it won't block the main thread.
        """
        # while True:
        while not self.event_time_up.is_set() and not self.event_test_done.is_set():
            sleep(interval)
            self.stats()

    def set_event_time_up(self):
        """set the time up flag"""
        if not self.event_time_up.is_set():
            self.event_time_up.set()
            self.event_test_done.set()

    def set_event_test_done(self):
        """set the test done flag either normally or by interruption"""
        if not self.event_test_done.is_set():
            self.event_test_done.set()

    def start_timer(self, timeout):
        """set a timer to stop testing"""
        self.timer = Timer(timeout, self.set_event_time_up)
        self.timer.start()

    def cancel_timer(self):
        """cancel the timer if test loop_times is reached first."""
        if self.timer != None and not self.event_time_up.is_set():
            self.timer.cancel()

    def post(self, url, data, headers={}, verify=True, amend_headers=True):
        """
        common request post function with below features, which you only need to take care of url and body data:
            - append common headers
            - print request and response in API log file
            - Take care of request exception and non-200 response codes and return None, so you only need to care normal json response.
            - arguments are the same as requests.post, except amend_headers.

        verify: False - Disable SSL certificate verification

        Return: None for exception
        """

        # append common headers if none
        headers_new = headers
        if amend_headers == True:
            if "Content-Type" not in headers_new:
                headers_new["Content-Type"] = r"application/json"
            if "User-Agent" not in headers_new:
                headers_new["User-Agent"] = "Python Requests"

        # send post request
        try:
            resp = requests.post(url, data=data, headers=headers_new, verify=verify)
        except Exception as ex:
            log.error("requests.post() failed with exception:", str(ex))
            return None

        # pretty request and response into API log file
        # Note: request print is common instead of checking if it is JSON body. So pass pretty formatted json string as argument to the request for pretty logging.
        pretty_print_request(resp.request)
        pretty_print_response_json(resp)
        log_api.debug(
            "response time in seconds: " + str(resp.elapsed.total_seconds()) + "\n"
        )

        # This return caller function's name, not this function post.
        # caller_func_name = inspect.stack()[1][3]
        # if resp.status_code != 200:
        #     log.error('%s failed with response code %s.' %(caller_func_name,resp.status_code))
        #     return None
        # return resp.json()
        return resp

    def get(self, url, auth=None, verify=False):
        """
        common request get function with below features, which you only need to take care of url:
            - print request and response in API log file
            - Take care of request exception and non-200 response codes and return None, so you only need to care normal json response.
            - arguments are the same as requests.get

        verify: False - Disable SSL certificate verification

        Return: None for exception
        """
        try:
            if auth == None:
                resp = requests.get(url, verify=verify)
            else:
                resp = requests.get(url, auth=auth, verify=verify)
        except Exception as ex:
            log.error("requests.get() failed with exception:", str(ex))
            return None

        # pretty request and response into API log file
        pretty_print_request(resp.request)
        pretty_print_response_json(resp)
        log_api.debug(
            "response time in seconds: " + str(resp.elapsed.total_seconds()) + "\n"
        )

        # This return caller function's name, not this function post.
        # caller_func_name = inspect.stack()[1][3]
        # if resp.status_code != 200:
        #     log.error('%s failed with response code %s.' %(caller_func_name,resp.status_code))
        #     return None
        # return resp.json()
        return resp

class QoSTest:
    def __init__(self,concurrent_users=5,loop_times=5,test_time=3600,stats_interval=5,ramp_up=0):
        self.concurrent_users=concurrent_users
        self.loop_times=loop_times
        self.test_time=test_time
        self.stats_interval=stats_interval
        self.ramp_up=ramp_up
        
    def startTest(self,request_type,url,sample_json):
        ### Test Settings ###
        concurrent_users = self.concurrent_users
        # test stops whenever loop_times or test_time is met first.
        loop_times = self.loop_times # number of iterations
        test_time = self.test_time  # time in seconds, e.g. 36000 after this time test will be terminated. This will prevent the infinite loops
        stats_interval = self.stats_interval #print to console about the current test results
        ramp_up = self.ramp_up  # total time in secs to ramp up. default 0, no wait

        perf_test = TestAPI()
        workers = []
        start_time = time.time()
        perf_test.start_time = start_time
        print("Tests started at %s." % time.asctime())

        # start stats thread
        stats_thread = Thread(
            target=perf_test.loop_stats, args=[stats_interval], daemon=True
        )
        stats_thread.start()

        # start concurrent user threads
        for i in range(concurrent_users):
            thread = Thread(
                target=perf_test.loop_test, kwargs={"request_type": request_type, "url" : url, "sample_json" : sample_json,"loop_times": loop_times}, daemon=True
            )
            thread.start()
            workers.append(thread)
            # ramp up wait
            sleep(ramp_up / concurrent_users)

        # start timer
        perf_test.start_timer(test_time)

        # Block until all threads finish.
        for w in workers:
            w.join()

        # clean up
        # stop timer if loop_times is reached first.
        perf_test.cancel_timer()

        end_time = time.time()
        perf_test.end_time = end_time

        # Ensure to execute the last statistics:
        perf_test.stats()
        results = perf_test.getResults()

        # print(
        #     "\nTests ended at %s.\nTotal test time: %s seconds."
        #     % (time.asctime(), end_time - start_time)
        # )
        return results