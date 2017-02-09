"""
HelloService example.
"""

import logging
from random import randint
import vikro.exceptions as exc
from vikro.service import BaseService, route

logger = logging.getLogger(__name__)

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
        """Hello vikro."""
        return 'Hello vikro!'

    @route('/hello', verb='post')
    def test_post_hello(self):
        """Hello post vikro."""
        return 'Hello post vikro!'

    @route('/rpc')
    def test_rpc(self):
        """Test RPC call to another service."""
        add1 = randint(0, 100)
        add2 = randint(0, 100)
        try:
            ret = self.get_proxy('MathService').add(add1, add2)
        except Exception, ex:
            ret = None
            logger.error(ex)
        logger.info('Got response: %s + %s = %s', add1, add2, ret)
        return ret

    @route('/route_test/<int:test_int>/content/<string:test_string>')
    def test_route(self, test_int, test_string):
        """Test route format."""
        return 'int: {0}, string: {1}'.format(test_int, test_string)

    @route('/exception')
    def test_exception(self):
        """Test exception."""
        raise exc.VikroTooManyRequests()
