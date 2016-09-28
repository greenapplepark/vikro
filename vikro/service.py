from .fsm import StateMachine
from gevent.pywsgi import WSGIServer
from route import parse_route_rule

class BaseServiceType(type):
    def __init__(cls, name, bases, attrs):
        for key, val in attrs.iteritems():
            rule = getattr(val, 'route_rule', None)
            if rule is not None:
                re_rule = parse_route_rule(rule)
                cls.route_table[re_rule] = key

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

    @staticmethod
    def route(rule):
        def decorator(f):
            f.route_rule = rule
            return f
        return decorator

    def dispatcher(self, env, start_response):
        for route_pattern, view_func_name in self.route_table.iteritems():
            match_obj = route_pattern.match(env['PATH_INFO'])
            if match_obj is not None:
                match_group = match_obj.groupdict()
                view_func = getattr(self, view_func_name)
                return view_func(start_response, **match_group)
        else:
            start_response('404 Not Found', [('Content-Type', 'text/html')])
            return [b'<h1>Not Found</h1>']