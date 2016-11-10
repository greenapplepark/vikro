import runpy
import gevent
import types
import functools
from fsm import StateMachine
from gevent.pywsgi import WSGIServer
from route import parse_route_rule
from proxy import Proxy
from components import BaseComponent, COMPONENT_TYPE_AMQP
from gevent import monkey
from protocol import AMQPRequest, AMQPResponse
monkey.patch_all
import socket
import logging

logger = logging.getLogger(__name__)

def greenlet(func):
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        gevent.spawn(func, self, *args, **kwargs)
    return wrapped

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
    
    def __init__(self, service_config):
        self._state_machine = StateMachine(self.state_machine_config)
        self._components = {}
        self.add_component_from_config(service_config)

    def add_component_from_config(self, service_config):
        for module_name in service_config:
            module = runpy.run_module('vikro.components.' + module_name)
            for m in module:
                if type(module[m]) == types.TypeType and module[m] != BaseComponent and issubclass(module[m], BaseComponent):
                    instance = module[m](**service_config[module_name])
                    self._components[instance.component_type] = instance

    def start(self):
        self._state_machine.start()
        self._do_start()
        self._state_machine.wait_in('starting')
        # for c in self._components.itervalues():
        #     c.run()
        # Now the service started
        self._state_machine.wait_in('running')

    @greenlet
    def _do_start(self):
        logger.info('Serving on 8088...')
        WSGIServer(('', 8088), self.dispatcher).start()
        gevent.joinall([gevent.spawn(c.initialize) for c in self._components.itervalues()])
        if COMPONENT_TYPE_AMQP in self._components:
            self._start_amqp_event_listener()
        self._state_machine.started()
        
    def stop(self):
        self._state_machine.stop()
        self._do_stop()
        self._state_machine.wait_in('stopping')

    @greenlet
    def _do_stop(self):
        for c in self._components.itervalues():
            c.finalize()
        self._state_machine.stopped()

    def reload(self):
        pass

    def get_proxy(self, dest_service_name):
        amqp = self._components[COMPONENT_TYPE_AMQP] if COMPONENT_TYPE_AMQP in self._components else None
        return Proxy(None, amqp, dest_service_name, type(self).__name__)

    @property
    def is_running(self):
        return self._state_machine.current_state == 'running'

    @staticmethod
    def route(rule):
        def decorator(f):
            f.route_rule = rule
            return f
        return decorator

    @greenlet
    def _start_amqp_event_listener(self):
        amqp = self._components[COMPONENT_TYPE_AMQP]
        service_name = type(self).__name__
        queue_name = 'service_{0}_queue'.format(service_name)
        amqp.listen_to_queue(service_name, queue_name, self._on_request)

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

    @greenlet
    def _on_request(self, request, message):
        logger.info('Got message: {}'.format(message.payload))
        if isinstance(message.payload, AMQPRequest):
            req = message.payload
            func = getattr(self, req.func_name, None)
            logger.info('_on_request got request {}'.format(message.payload))
            if func is not None:
                try:
                    response = func(*req.func_args, **req.func_kwargs)
                except Exception, e:
                    response = e
            else:
                response = Exception('MethodNotFound')
            self._components[COMPONENT_TYPE_AMQP].publish_message(AMQPResponse(response), req.reply_to, req.reply_key)
            

route = BaseService.route