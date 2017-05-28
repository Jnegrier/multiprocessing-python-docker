''' Distributed load among several Docker containers using Python multiprocessing capabilities '''

import random
import time
import subprocess
import queue
from multiprocessing import Pool, Queue, Lock

LOCK = Lock()
TEST_QUEUE = Queue()


class TestWorker(object):
    ''' This Class is executed by each container '''

    @staticmethod
    def run_test(container_id, value):
        ''' Operation to be executed for each container '''

        cmd = ['docker exec -it {0} echo "I am container {0}!, this is message: {1}"' \
                .format(container_id, value)]
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        for line in process.stdout:
            print(line.decode('utf-8')[:-2])
        process.wait()

    @staticmethod
    def container(container_id):
        ''' Here we get a value from the shared queue '''

        while not TEST_QUEUE.empty():
            LOCK.acquire()
            try:
                value = TEST_QUEUE.get(block=False)
                time.sleep(0.5)
            except queue.Empty:
                print("Queue empty ):")
                return
            print("\nProcessing: {0}\n".format(value))
            LOCK.release()
            TestWorker.run_test(container_id, value)

def master():
    ''' Main controller to set containers and test values '''

    qty = input("How many containers you want to deploy: ")
    msg_val = input("How many random values you want to send among this containers: ")

    print("\nGenerating test messages...\n")
    for _ in range(int(msg_val)):
        item = random.randint(1000, 9999)
        TEST_QUEUE.put(item)
    ids = []
    for _ in range(int(qty)):
        container_id = subprocess.run(["docker", "run", "-it", "-d", "centos:7"], \
                stdout=subprocess.PIPE)
        container_id = container_id.stdout.decode('utf-8')[:-1]
        ids.append(container_id)
    pool = Pool(int(qty))
    pool.map(TestWorker.container, ids)
    pool.close()

master()
