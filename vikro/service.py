from fsm import StateMachine
from gevent.pywsgi import WSGIServer
from route import parse_route_rule
import gevent

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
    state_machine_config = {
        'initial': 'init',
        'transitions': [
            {'name': 'start', 'src': 'init', 'dst': 'starting'},
            {'name': 'started', 'src': 'starting', 'dst': 'running'},
            {'name': 'stop', 'src': 'running', 'dst': 'stopping'},
            {'name': 'stopped', 'src': 'stopping', 'dst': 'init'},
        ]
    }
    
    def __init__(self):
        self._state_machine = StateMachine(self.state_machine_config)
        self._components = {}

    def add_component(self, component_cls):
        instance = component_cls(None)
        type = instance.component_type
        self._components[type] = instance

    def start(self):
        self._state_machine.start()
        print 'BaseService start\n'
        print('Serving on 8088...\n')
        WSGIServer(('', 8088), self.dispatcher).start()
        gevent.joinall([gevent.spawn(c.initialize) for c in self._components.itervalues()])
        self._state_machine.started()

    def stop(self):
        self._state_machine.stop()
        for c in self._components.itervalues():
            c.finalize()
        self._state_machine.stopped()

    def reload(self):
        pass

    @staticmethod
    def route(rule):
        def decorator(f):
            f.route_rule = rule
            return f
        return decorator

    def dispatcher(self, env, start_response):
        if self._state_machine.current_state != 'running':
            start_response('503 Service Unavailable', [('Content-Type', 'text/html')])
            return [b'<h1>Service Unavailable</h1>']
        for route_pattern, view_func_name in self.route_table.iteritems():
            match_obj = route_pattern.match(env['PATH_INFO'])
            if match_obj is not None:
                match_group = match_obj.groupdict()
                view_func = getattr(self, view_func_name)
                return view_func(start_response, **match_group)
        else:
            start_response('404 Not Found', [('Content-Type', 'text/html')])
            return [b'<h1>Not Found</h1>']