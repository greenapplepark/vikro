from .fsm import StateMachine
from gevent.pywsgi import WSGIServer

class BaseServiceType(type):
    def __init__(cls, name, bases, attrs):
        for key, val in attrs.iteritems():
            properties = getattr(val, 'route_pattern', None)
            if properties is not None:
                cls.route_table[properties] = key

class BaseService(object):
    __metaclass__ = BaseServiceType
    route_table = {}
    
    def __init__(self):
        self._state_machine = StateMachine(None)
        self._components = []

    def add_component(self, component):
        pass

    def start(self):
        for c in self._components:
            c.initialize()

        print "BaseService start\n"
        print('Serving on 8088...\n')
        WSGIServer(('', 8088), self.dispatcher).serve_forever()

    def stop(self):
        pass

    def reload(self):
        pass

    @classmethod
    def route(cls, pattern):
        def decorator(f):
            f.route_pattern = pattern
            return f
        return decorator

    def dispatcher(self, env, start_response):
        if env['PATH_INFO'] in self.route_table:
            func = getattr(self, self.route_table[env['PATH_INFO']])
            return func(start_response)
        else:
            start_response('404 Not Found', [('Content-Type', 'text/html')])
            return [b'<h1>Not Found</h1>']