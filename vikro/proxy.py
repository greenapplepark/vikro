import gevent
import requests
import uuid
import functools
import string
import random
from protocol import AMQPRequest, AMQPResponse
import logging

logger = logging.getLogger(__name__)


class Proxy(object):
    
    def __init__(self, server_map, amqp, dest_service_name, src_service_name):
        self._server_map = server_map
        self._amqp = amqp
        self._dest_service_name = dest_service_name
        self._src_service_name = src_service_name
    
    def __getattr__(self, attr):
        logger.debug('Proxy calling {}'.format(attr))
        return functools.partial(self._rpc_handler, attr)

    def _rpc_handler(self, func_name, *func_args, **func_kwargs):
        logger.debug('proxy try to call {} with param {} and {}'.format(func_name, func_args, func_kwargs))
        exchange_name = 'service_{0}_exchange'.format(self._dest_service_name)
        reply_to = 'service_{}_exchange'.format(self._src_service_name)
        reply_key = self._id_generator()
        request = AMQPRequest(func_name, func_args, func_kwargs, reply_to, reply_key)
        listen_queue = 'service_{}_queue_{}'.format(self._src_service_name, reply_key)
        self._amqp.publish_message(request, exchange_name)

        def _on_response(request, message):
            logger.debug('Get response {}'.format(message.payload))
        self._amqp.listen_to_queue(self._src_service_name, listen_queue, _on_response, routing_key=reply_key, timeout=3)


    def _id_generator(self, size=6, chars=string.ascii_letters + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))