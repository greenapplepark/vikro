"""
HelloService example.
"""

import vikro.exceptions as exc
from vikro.service import BaseService, route

class HelloService(BaseService):
    """Test service."""

    def __init__(self, service_config):
        super(HelloService, self).__init__(service_config)

    def start(self):
        super(HelloService, self).start()

    def stop(self):
        super(HelloService, self).stop()

    def reload(self):
        pass

    @route('/hello')
    def test_hello(self):
        return 'Hello vikro!'

    @route('/rpc')
    def test_rpc(self):
        ret = self.get_proxy('MathService').subtract(10, 2)
        return ret

    @route('/route_test/<int:test_int>/content/<string:test_string>')
    def test_route(self, test_int, test_string):
        return 'int: {0}, string: {1}'.format(test_int, test_string)

    def add(self, a, b):
        return a + b

    def multi(self, a, b):
        return a * b

    @route('/exception')
    def test_exception(self):
        raise exc.VikroTooManyRequests()
