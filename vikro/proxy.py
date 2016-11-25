"""
vikro.proxy
~~~~~~~~~~~

This module provides 2 method to do RPC between services.
1. Through AMQP broker
2. Use RESTful interface
"""

import socket
import time
import functools
import string
import random
import logging
import gevent
import vikro.exceptions as exc
from vikro.models import AMQPRequest

logger = logging.getLogger(__name__)

RPC_TIMEOUT = 2


def _id_generator(size=6, chars=string.ascii_letters + string.digits):
    """Generate random string."""
    return ''.join(random.choice(chars) for _ in range(size))

class Proxy(object):
    """Proxy to call RPC, using AMQP or RESTful way.
    """
    def __init__(self, server_map, amqp, dest_service_name, src_service_name, rpc_timeout):
        self._server_map = server_map
        self._amqp = amqp
        self._dest_service_name = dest_service_name
        self._src_service_name = src_service_name
        self._rpc_timeout = RPC_TIMEOUT if rpc_timeout is None else rpc_timeout
        self._reply_key = _id_generator()

        src_exchange_name = 'service_{0}_exchange'.format(self._src_service_name)
        listen_queue_name = 'service_{0}_queue_{1}'.format(self._src_service_name, self._reply_key)
        src_exchange = self._amqp.make_exchange(src_exchange_name)
        self._listen_queue = self._amqp.make_queue(listen_queue_name, src_exchange, self._reply_key)

    def __getattr__(self, attr):
        return functools.partial(self._rpc_handler, attr)

    def _rpc_handler(self, func_name, *func_args, **func_kwargs):
        """Handle AMQP rpc call.
        Send request to AMQP broker and wait for response with timeout.
        """
        logger.info(
            'proxy try to call %s with param %s and %s.',
            func_name, func_args, func_kwargs)
        dest_exchange_name = 'service_{0}_exchange'.format(self._dest_service_name)
        reply_to = 'service_{0}_exchange'.format(self._src_service_name)
        request = AMQPRequest(func_name, func_args, func_kwargs, reply_to, self._reply_key)
        self._amqp.publish_message(request, dest_exchange_name)
        got_response = {'value': False}
        response = {'data': None}

        def _on_response(request, message):
            got_response['value'] = True
            response['data'] = message.payload
            logger.info('Get response %s.', message.payload)
            message.ack()

        conn = self._amqp.get_connection()
        start_time = time.time()
        # Here I tried to get message using raw api from kombu rather than
        # using methods in AMQPComponent because it looks kombu doesn't
        # support get only one message. It will try to drain event till
        # timeout even if it already got one message.
        with conn.Consumer(queues=self._listen_queue, callbacks=[_on_response], accept=['pickle']):
            while not got_response['value']:
                try:
                    conn.drain_events(timeout=0.01)
                except socket.timeout:
                    if time.time() - start_time > self._rpc_timeout:
                        raise exc.VikroRPCTimeout('timeout')
                except KeyboardInterrupt:
                    return
                except Exception, ex:
                    logger.error(ex)
                    break
                gevent.sleep(0)
        if response['data'].is_exception:
            raise response['data'].result
        else:
            return response['data'].result
