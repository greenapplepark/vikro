import gevent
import requests
import uuid
import functools
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
        return functools.partial(self.rpc_handler, attr)
        # if self._amqp is not None:
        #     # use amqp to do rpc call if we have
        #     self._uuid = str(uuid.uuid4())
        #     self._exchange_name = 'client_{0}_exchange_{1}'.format(type(self._parent_service).__name__, self._uuid)
        #     self._queue_name = 'client_{0}_queue_{1}'.format(type(self._parent_service).__name__, self._uuid)
        # else:
        #     # go through restful api
        #     pass

    def rpc_handler(self, func_name, *func_args, **func_kwargs):
        logger.debug('proxy try to call {} with param {} and {}'.format(func_name, func_args, func_kwargs))
        # uuid = str(uuid.uuid4())
        exchange_name = 'service_{0}_exchange'.format(self._dest_service_name)
        exchange = self._amqp.make_exchange(exchange_name)
        request = AMQPRequest(func_name, func_args, func_kwargs, None)
        self._amqp.publish_message(request, exchange)