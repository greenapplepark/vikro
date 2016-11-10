import socket
import time
import functools
import string
import random
import logging
import gevent
import vikro.exceptions as exc
from vikro.protocol import AMQPRequest, AMQPResponse

LOG = logging.getLogger(__name__)

PROXY_TIMEOUT = 2

class Proxy(object):

    def __init__(self, server_map, amqp, dest_service_name, src_service_name):
        self._server_map = server_map
        self._amqp = amqp
        self._dest_service_name = dest_service_name
        self._src_service_name = src_service_name

    def __getattr__(self, attr):
        return functools.partial(self._rpc_handler, attr)

    def _rpc_handler(self, func_name, *func_args, **func_kwargs):
        LOG.info('proxy try to call %s with param %s and %s',
                 func_name, func_args, func_kwargs)
        exchange_name = 'service_{0}_exchange'.format(self._dest_service_name)
        reply_to = 'service_{}_exchange'.format(self._src_service_name)
        reply_key = self._id_generator()
        request = AMQPRequest(func_name, func_args, func_kwargs, reply_to, reply_key)
        listen_queue = 'service_{}_queue_{}'.format(self._src_service_name, reply_key)
        self._amqp.publish_message(request, exchange_name)
        got_response = {'value' : False}

        def _on_response(request, message):
            got_response['value'] = True
            LOG.info('Get response %s', message.payload)

        exchange = self._amqp.make_exchange(exchange_name)
        queue = self._amqp.make_queue(listen_queue, exchange, reply_key)
        conn = self._amqp.get_connection()
        start_time = time.time()
        with conn.Consumer(queues=queue, callbacks=[_on_response], accept=['pickle']):
            while not got_response['value']:
                try:
                    conn.drain_events(timeout=0.1)
                except socket.timeout:
                    if time.time() - start_time > PROXY_TIMEOUT:
                        raise exc.VikroTimeoutException('timeout')
                except KeyboardInterrupt:
                    return
                except Exception, e:
                    LOG.error(e)
                    break
                gevent.sleep(0.1)

    def _id_generator(self, size=6, chars=string.ascii_letters + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))
