from vikro.service import BaseService, route
import gevent

class HelloService(BaseService):

    def __init__(self, service_config):
        super(HelloService, self).__init__(service_config)

    def start(self):
        super(HelloService, self).start()

    def stop(self):
        super(HelloService, self).stop()

    def reload(self):
        pass
    
    @route('/hello')
    def test_hello(self, start_response):
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [b'<b>hello world from hello module</b>']

    @route('/keke')
    def test_keke(self, start_response):
        self.get_proxy('HelloService').test(1, 2)
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [b'<i>kekekekeke</i>']

    @route('/route_test/<int:test_int>/content/<string:test_string>')
    def test_route(self, start_response, test_int, test_string):
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [b'<i>int: %s, string: %s</i>' % (test_int, test_string)]

    def test(self, a, b):
        # gevent.sleep(3)
        return a + b