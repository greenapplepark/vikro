from fsm import StateMachine
from gevent.pywsgi import WSGIServer
from route import parse_route_rule
from proxy import Proxy
from components import COMPONENT_TYPE_AMQP
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
        instance = component_cls(None, self)
        type = instance.component_type
        self._components[type] = instance

    def start(self):
        self._state_machine.start()
        gevent.spawn(self._do_start)
        self._state_machine.wait_in('starting')
        for c in self._components.itervalues():
            c.run()
        # Now the service started
        self._state_machine.wait_in('running')

    def _do_start(self):
        print 'Serving on 8088...'
        WSGIServer(('', 8088), self.dispatcher).start()
        gevent.joinall([gevent.spawn(c.initialize) for c in self._components.itervalues()])
        self._state_machine.started()
        
    def stop(self):
        self._state_machine.stop()
        gevent.spawn(self._do_stop)
        self._state_machine.wait_in('stopping')

    def _do_stop(self):
        for c in self._components.itervalues():
            c.finalize()
        self._state_machine.stopped()

    def reload(self):
        pass

    def get_proxy(self, service_name):
        amqp = self._components[COMPONENT_TYPE_AMQP] if COMPONENT_TYPE_AMQP in self._components else None
        return Proxy(None, amqp, service_name)

    @property
    def is_running(self):
        return self._state_machine.current_state == 'running'

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

    def remote_service_call_handler(self, func, *args, **kwargs):
        print 'received remote server call %s' % func