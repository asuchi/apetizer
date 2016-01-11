'''
Created on 22 sept. 2015

@author: biodigitals
'''
from multiprocessing import Pool, Lock
import multiprocessing, logging
from multiprocessing.pool import ThreadPool
from multiprocessing.process import Process
import time

from django.conf import settings


# thinking about threading/multiprocessing ...
# http://stackoverflow.com/questions/8068945/django-long-running-asynchronous-tasks-with-threads-processing
logger = multiprocessing.log_to_stderr()
logger.setLevel(logging.INFO)


class AsyncDispatcher(Process):

    istart = 0
    iclock = 0
    icycle = 1

    pool_size = 4

    cron_settings = []
    cron_execution = {}

    results = []
    _instance = None
    _instance_lock = Lock()
    _stop = False

    @classmethod
    def get_instance(cls):
        if cls._instance:
            return cls._instance
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = AsyncDispatcher()
                if not settings.DEBUG:
                    cls._instance.start()
            return cls._instance

    def __init__(self, *args, **kwargs):
        """
        
        """
        # start multiprocessing pool 
        self.pool = ThreadPool(processes=self.pool_size)
        super(AsyncDispatcher, self).__init__(*args, **kwargs)

    def run(self):
        while self._stop is False:
            time.sleep(self.icycle)
            execution = self.get_execution()
            if execution:
                self.spawn(execution[0], execution[1], execution[2])
            self.iclock += 1
        print "Stopped dispatcher"

    def add_cron(self, function, args, kwargs, cycle, start=None, end=None, count=None):
        """
        Adds a cron to manage
        Cycle represents the duration 
        at witch the task has to execute
        123 -> every 123 seconds
        12s -> every 12 seconds
        1h  -> every hour
        2d  -> every day
        3m  -> every month
        4y  -> every year
        etc ...
        to be defined much more like the cron settings on unix systems
        if start is not provided, the current date time is used
        start can be a past date and change. 
        unlike other systems based on persistent cron data,
        the task execution is planned "in memory" and recalculated each execution
        """
        # TODO
        # create a deep copy of args and params 
        # to avoid dict or other changes occurs
        settings = {'callable':[function, args, kwargs],
                    'settings':[cycle, start, end, count],}
        self.set_execution(settings)

    def set_execution(self, dict):
        # well ... requires some work to have correct time planning
        next_exec_time = self.istart+self.icycle+dict['settings'][0]
        self.cron_execution[next_exec_time] = dict['callable']

    def get_execution(self):
        """
        Returns first occurence of past time execution pile
        """
        time_keys = self.cron_execution.keys()
        time_keys.sort()
        for time_key in time_keys:
            # if timekey passed, then trigger execution
            execution = self.cron_execution[time_key]
            return execution

    def spawn(self, function, fargs, fkwargs):
        print 'Executing '
        print function
        result = self.pool.apply_async(function, fargs, fkwargs, self.finished_task)
        #result_q.get(timeout=1)
        self.results.append(result)
        print result
        return result

    def delay(self, timeout, function, fargs, fkwargs):
        # well ... requires some work to have correct time planning
        next_exec_time = self.istart+self.icycle+timeout
        self.cron_execution[next_exec_time] = [function, fargs, fkwargs]

    def finished_task(self, result):
        # the result is the return value from the function
        return

    def join(self, timeout=None):
        self._stop = True
        self.pool.join(timeout)
        super(AsyncDispatcher, self).join(timeout=timeout)

