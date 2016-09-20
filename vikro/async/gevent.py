class AsyncManager(AbstractAsyncManager):

    def __init__(self):
        self._greenlets = gevent.pool.Group()

    def init(self):
        gevent.reinit()

    def spawn(self, func, *args, **kwargs):
        """Spawn a greenlet under this service"""
        return self._greenlets.spawn(func, *args, **kwargs)

    def sleep(self, seconds):
        return gevent.sleep(seconds)

    def event(self, *args, **kwargs):
        return gevent.event.Event(*args, **kwargs)