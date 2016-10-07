import gevent
import requests

class Proxy(object):
    
    def __init__(self, server_map, amqp, service_name):
        self._server_map = server_map
        self._amqp = amqp
        self._service_name = service_name
    
    def __getattr__(self, name):
        if self._amqp is not None:
            # use amqp to do rpc call if we have
        else:
            # go through restful api
            pass