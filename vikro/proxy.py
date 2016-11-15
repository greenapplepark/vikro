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

PROXY_TIMEOUT = 2


def _id_generator(size=6, chars=string.ascii_letters + string.digits):
    """Generate random string."""
    return ''.join(random.choice(chars) for _ in range(size))

class Proxy(object):
    """Proxy to call RPC, using AMQP or RESTful way.
    """
    def __init__(self, server_map, amqp, dest_service_name, src_service_name):
        self._server_map = server_map
        self._amqp = amqp
        self._dest_service_name = dest_service_name
        self._src_service_name = src_service_name

    def __getattr__(self, attr):
        return functools.partial(self._rpc_handler, attr)

    def _rpc_handler(self, func_name, *func_args, **func_kwargs):
        """Handle AMQP rpc call.
        Send request to AMQP broker and wait for response with timeout.
        """
        logger.info(
            'proxy try to call %s with param %s and %s.',
            func_name, func_args, func_kwargs)
        exchange_name = 'service_{0}_exchange'.format(self._dest_service_name)
        reply_to = 'service_{}_exchange'.format(self._src_service_name)
        reply_key = _id_generator()
        request = AMQPRequest(func_name, func_args, func_kwargs, reply_to, reply_key)
        listen_queue = 'service_{}_queue_{}'.format(self._src_service_name, reply_key)
        self._amqp.publish_message(request, exchange_name)
        got_response = {'value' : False}

        def _on_response(request, message):
            got_response['value'] = True
            logger.info('Get response %s.', message.payload)

        exchange = self._amqp.make_exchange(exchange_name)
        queue = self._amqp.make_queue(listen_queue, exchange, reply_key)
        conn = self._amqp.get_connection()
        start_time = time.time()
        # Here I tried to get message using raw api from kombu rather than
        # using methods in AMQPComponent because it looks kombu doesn't
        # support get only one message. It will try to drain event till
        # timeout even if it already got one message.
        with conn.Consumer(queues=queue, callbacks=[_on_response], accept=['pickle']):
            while not got_response['value']:
                try:
                    conn.drain_events(timeout=0.1)
                except socket.timeout:
                    if time.time() - start_time > PROXY_TIMEOUT:
                        raise exc.VikroTimeoutException('timeout')
                except KeyboardInterrupt:
                    return
                except Exception, ex:
                    logger.error(ex)
                    break
                gevent.sleep(0.1)
