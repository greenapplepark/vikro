"""
vikro.proxy
~~~~~~~~~~~

This module provides 2 method to do RPC between services.
1. Through AMQP broker
2. Use RESTful interface
"""

import functools
import logging
import importlib
import vikro.exceptions as exc
from vikro.models import AMQPRequest, AMQPResponse
from vikro.util import id_generator
from gevent.event import Event
from haigha.message import Message

logger = logging.getLogger(__name__)

RPC_TIMEOUT = 2

class Proxy(object):
    """Proxy to call RPC, using AMQP or RESTful way.
    """
    def __init__(self, server_map, amqp, dest_service_name, src_service_name, rpc_timeout):
        self._server_map = server_map
        self._amqp = amqp
        self._dest_service_name = dest_service_name
        self._src_service_name = src_service_name
        self._rpc_timeout = RPC_TIMEOUT if rpc_timeout is None else rpc_timeout
        self._reply_key = id_generator()
        self._wait_event = Event()
        self._response = None

    def __getattr__(self, attr):
        return functools.partial(self._rpc_handler, attr)

    def _rpc_handler(self, func_name, *func_args, **func_kwargs):
        """Handle AMQP rpc call.
        Send request to AMQP broker and wait for response with timeout.
        """
        logger.debug(
            '[_rpc_handler] Proxy try to call %s with param %s and %s.',
            func_name, func_args, func_kwargs)
        dest_exchange_name = 'service_{0}_exchange'.format(self._dest_service_name)
        request = AMQPRequest(
            func_name,
            func_args,
            func_kwargs,
            self._amqp.exchange_name,
            self._amqp.response_id,
            self._reply_key)
        msg = Message(request.to_json(), correlation_id=self._reply_key)
        logger.debug('[_rpc_handler] send rpc raw: %s.', msg)
        self._amqp.register_rpc_callback(self._reply_key, self.on_rpc_response)
        self._amqp.send_request(msg, dest_exchange_name)
        self._wait_event.wait(timeout=self._rpc_timeout)
        self._amqp.remove_rpc_callback(self._reply_key)
        if self._response is None:
            raise exc.VikroRPCTimeout
        if isinstance(self._response, AMQPResponse):
            if self._response.is_exception:
                _module = importlib.import_module(self._response.result['exception_module'])
                _class = getattr(_module, self._response.result['exception_name'])
                raise _class(self._response.result['exception_message'])
            else:
                return self._response.result

    def on_rpc_response(self, message):
        """RPC response handler"""
        logger.debug('[on_rpc_response] receive response: %s.', message)
        self._response = AMQPResponse.from_json(message.body)
        self._wait_event.set()
