import gevent
import requests
import uuid
from protocol import RpcRequest

class Proxy(object):
    
    def __init__(self, server_map, amqp, service_name, parent_service):
        self._server_map = server_map
        self._amqp = amqp
        self._service_name = service_name
        self._parent_service = parent_service
    
    def __getattr__(self, name):
        if self._amqp is not None:
            # use amqp to do rpc call if we have
            self._uuid = str(uuid.uuid4())
            self._exchange_name = 'client_{0}_exchange_{1}'.format(type(self._parent_service).__name__, self._uuid)
            self._queue_name = 'client_{0}_queue_{1}'.format(type(self._parent_service).__name__, self._uuid)
        else:
            # go through restful api
            pass