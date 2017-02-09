"""
vikro.service
~~~~~~~~~~~~~

This module contains BaseSevice, base class of all services.
"""

try:
    import simplejson as json
except ImportError:
    import json
import runpy
import types
import functools
import logging
import gevent
from gevent.pywsgi import WSGIServer
from vikro.fsm import StateMachine
from vikro.route import RouteData
from vikro.proxy import Proxy
from vikro.components import BaseComponent, COMPONENT_TYPE_AMQP
from vikro.models import AMQPRequest, AMQPResponse
import vikro.exceptions as exc
from haigha.message import Message

logger = logging.getLogger(__name__)

def greenlet(func):
    """Spawn a greenlet instead calling function directly."""

    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        gevent.spawn(func, self, *args, **kwargs)
    return wrapped

class BaseServiceType(type):
    """Meta class of BaseService.
    It is used to record route url to route_table.
    """

    def __init__(cls, name, bases, attrs):
        for key, val in attrs.iteritems():
            rule = getattr(val, 'route_rule', None)
            verb = getattr(val, 'verb', None)
            if rule is not None:
                route_obj = RouteData(verb, rule, key)
                cls.route_table[route_obj] = key

class BaseService(object):
    """Base class of Service.
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
        self._service_name = type(self).__name__
        self._components = {}
        self.add_component_from_config(service_config)
        self._port = int(service_config['service']['port'])

    def add_component_from_config(self, service_config):
        """Read config file and spawn components."""
        for module_name in service_config:
            try:
                modules = runpy.run_module('vikro.components.' + module_name)
            except ImportError:
                continue
            for module in modules:
                if (type(modules[module]) == types.TypeType
                        and modules[module] != BaseComponent
                        and issubclass(modules[module], BaseComponent)):
                    instance = modules[module](self._service_name, **service_config[module_name])
                    self._components[instance.component_type] = instance

    def start(self):
        """Start service."""
        self._state_machine.start()
        self._do_start()
        self._state_machine.wait_in('starting')
        self._state_machine.wait_in('running')

    @greenlet
    def _do_start(self):
        """Do actual starting work in greenlet.
        Starting WSGI Server, spawn components,
        start amqp listener if has.
        """
        logger.info('Serving on %s...', self._port)
        WSGIServer(('', self._port), self.dispatcher).start()
        gevent.joinall(
            [gevent.spawn(c.initialize) for c in self._components.itervalues()])
        if COMPONENT_TYPE_AMQP in self._components:
            self._start_amqp_event_listener()
        self._state_machine.started()

    def stop(self):
        """Stop service."""
        self._state_machine.stop()
        self._do_stop()
        self._state_machine.wait_in('stopping')

    @greenlet
    def _do_stop(self):
        """Do actual stopping working in greenlet.
        """
        for component in self._components.itervalues():
            component.finalize()
        self._state_machine.stopped()

    def reload(self):
        """Reload service."""
        pass

    def get_proxy(self, dest_service_name, rpc_timeout=None):
        """Get proxy object to call RPC."""
        amqp = self._components.get(COMPONENT_TYPE_AMQP)
        return Proxy(None, amqp, dest_service_name, type(self).__name__, rpc_timeout)

    @property
    def is_running(self):
        """Check if service is in running state."""
        return self._state_machine.current_state == 'running'

    @staticmethod
    def route(rule, verb='get'):
        """Route decorator to define routing url pattern."""
        def decorator(func):
            func.route_rule = rule
            func.verb = verb
            return func
        return decorator

    @greenlet
    def _start_amqp_event_listener(self):
        """Start to listen rpc message from amqp server."""
        amqp = self._components[COMPONENT_TYPE_AMQP]
        amqp.listen_to_queue(self._on_amqp_request)

    def dispatcher(self, env, start_response):
        """Dispatcher RESTful based http request to handlers."""
        if self._state_machine.current_state != 'running':
            start_response('503', [('Content-Type', 'application/json')])
            return []
        for route_obj, view_func_name in self.route_table.iteritems():
            if route_obj.route_verb != env['REQUEST_METHOD'].lower():
                continue
            match_obj = route_obj.re_rule.match(env['PATH_INFO'])
            if match_obj is not None:
                match_group = match_obj.groupdict()
                view_func = getattr(self, view_func_name)
                try:
                    ret = json.dumps(view_func(**match_group))
                    start_response('200', [('Content-Type', 'application/json')])
                    return [ret]
                except exc.VikroException, vex:
                    logger.error(vex)
                    ret_code = exc.EXCEPTION_CODE_MAPPING.get(vex.__class__, '500')
                    start_response(ret_code, [('Content-Type', 'application/json')])
                    return []
                except Exception, ex:
                    logger.error(ex)
                    start_response('500', [('Content-Type', 'application/json')])
                    return []
        else:
            start_response('404', [('Content-Type', 'application/json')])
            return []

    @greenlet
    def _on_amqp_request(self, message):
        """Handle amqp rpc request in greenlet."""
        logger.debug('[_on_amqp_request] got raw request %s.', message)
        req = AMQPRequest.from_json(message.body)
        if isinstance(req, AMQPRequest):
            func = getattr(self, req.func_name, None)
            if func is not None:
                try:
                    response = func(*req.func_args, **req.func_kwargs)
                except Exception, ex:
                    response = ex
            else:
                response = exc.VikroMethodNotFound('MethodNotFound')
            response = AMQPResponse(response)
            msg = Message(response.to_json(), correlation_id=req.reply_key)
            self._components[COMPONENT_TYPE_AMQP].send_response(
                msg,
                req.reply_to,
                req.response_id)

route = BaseService.route
