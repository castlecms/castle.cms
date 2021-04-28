from multiprocessing import Process

import logging
logger = logging.getLogger('castle.cms')


class Worker(Process):
    def __init__(self, queue):
        super(Worker, self).__init__()
        self.queue = queue

    def run(self):
        logger.info('Worker started')
        for process_data in iter(self.queue.get, None):
            process = Process(
                target=process_data['target'],
                args=process_data['args'],
                kwargs=process_data['kwargs']
            )
            process.start()
            process.join()
