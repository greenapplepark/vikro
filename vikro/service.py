import runpy
import types
import functools
import logging
import gevent
from gevent.pywsgi import WSGIServer
from vikro.fsm import StateMachine
from vikro.route import parse_route_rule
from vikro.proxy import Proxy
from vikro.components import BaseComponent, COMPONENT_TYPE_AMQP
from vikro.protocol import AMQPRequest, AMQPResponse

LOG = logging.getLogger(__name__)

def greenlet(func):
    """
    Spawn a greenlet instead calling function directly
    """
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        gevent.spawn(func, self, *args, **kwargs)
    return wrapped

class BaseServiceType(type):
    """
    Meta class of BaseService
    It is used to record route url to route_table
    """
    def __init__(cls, name, bases, attrs):
        for key, val in attrs.iteritems():
            rule = getattr(val, 'route_rule', None)
            if rule is not None:
                re_rule = parse_route_rule(rule)
                cls.route_table[re_rule] = key

class BaseService(object):
    """
    Base class of Service.
    This BaseService class provides functionalities like
    * RESTful style route decorator
    * AMQP/RESTful based RPC
    which are easy for drived class to use.
    """
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
        """
        Read config file and spawn components
        """
        for module_name in service_config:
            modules = runpy.run_module('vikro.components.' + module_name)
            for module in modules:
                if (type(modules[module]) == types.TypeType and
                        modules[module] != BaseComponent and
                        issubclass(modules[module], BaseComponent)):
                    instance = modules[module](**service_config[module_name])
                    self._components[instance.component_type] = instance

    def start(self):
        """
        Start service
        """
        self._state_machine.start()
        self._do_start()
        self._state_machine.wait_in('starting')
        self._state_machine.wait_in('running')

    @greenlet
    def _do_start(self):
        """
        Do actual starting work in greenlet.
        Starting WSGI Server, spawn components,
        start amqp listener if has
        """
        LOG.info('Serving on 8088...')
        WSGIServer(('', 8088), self.dispatcher).start()
        gevent.joinall(
            [gevent.spawn(c.initialize) for c in self._components.itervalues()])
        if COMPONENT_TYPE_AMQP in self._components:
            self._start_amqp_event_listener()
        self._state_machine.started()

    def stop(self):
        """
        Stop service
        """
        self._state_machine.stop()
        self._do_stop()
        self._state_machine.wait_in('stopping')

    @greenlet
    def _do_stop(self):
        """
        Do actual stopping working in greenlet
        """
        for component in self._components.itervalues():
            component.finalize()
        self._state_machine.stopped()

    def reload(self):
        """
        Reload service
        """
        pass

    def get_proxy(self, dest_service_name):
        """
        Get proxy object to call RPC
        """
        amqp = self._components.get(COMPONENT_TYPE_AMQP)
        return Proxy(None, amqp, dest_service_name, type(self).__name__)

    @property
    def is_running(self):
        """
        Check if service is in running state
        """
        return self._state_machine.current_state == 'running'

    @staticmethod
    def route(rule):
        """
        Route decorator to define routing url pattern
        """
        def decorator(func):
            func.route_rule = rule
            return func
        return decorator

    @greenlet
    def _start_amqp_event_listener(self):
        """
        Start to listen rpc message from amqp server
        """
        amqp = self._components[COMPONENT_TYPE_AMQP]
        service_name = type(self).__name__
        queue_name = 'service_{0}_queue'.format(service_name)
        amqp.listen_to_queue(service_name, queue_name, self._on_amqp_request)

    def dispatcher(self, env, start_response):
        """
        Dispatcher RESTful based http request to handlers
        """
        if self._state_machine.current_state != 'running':
            start_response('503 Service Unavailable',
                           [('Content-Type', 'text/html')])
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
    def _on_amqp_request(self, request, message):
        """
        Handle amqp rpc request in greenlet
        """
        LOG.info('Got message: %s', message.payload)
        if isinstance(message.payload, AMQPRequest):
            req = message.payload
            func = getattr(self, req.func_name, None)
            LOG.info('_on_request got request %s', message.payload)
            if func is not None:
                try:
                    response = func(*req.func_args, **req.func_kwargs)
                except Exception, e:
                    response = e
            else:
                response = Exception('MethodNotFound')
            self._components[COMPONENT_TYPE_AMQP].publish_message(
                AMQPResponse(response),
                req.reply_to,
                req.reply_key)

route = BaseService.route
