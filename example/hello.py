from vikro.service import BaseService

class HelloService(BaseService):

    def start(self):
        super(HelloService, self).start()

    def stop(self):
        pass

    def reload(self):
        pass
    
    @BaseService.route('/hello')
    def test_hello(self, start_response):
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [b"<b>hello world from hello module</b>"]


    @BaseService.route('/keke')
    def test_keke(self, start_response):
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [b"<i>kekekekeke</i>"]

    @BaseService.route('/route_test/<int:test_int>/content/<string:test_string>')
    def test_route(self, start_response, test_int, test_string):
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [b"<i>int: %s, string: %s</i>" % (test_int, test_string)]