class AbstractAsyncManager():
    def init(self):
        pass

    def spawn(self, func, *args, **kwargs):
        raise NotImplementedError()

    def sleep(self, seconds):
        raise NotImplementedError()

    def event(self, *args, **kwargs):
        raise NotImplementedError()