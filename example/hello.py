from vikro.service import BaseService

class HelloService(BaseService):

    def start(self):
        print HelloService.route_table
        super(HelloService, self).start()
        print "HelloService start"

    def stop(self):
        pass

    def reload(self):
        pass
    
    @BaseService.route('/hello')
    def test_hello(self, start_response):
        print "test_hello"
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [b"<b>hello world from hello module</b>"]


    @BaseService.route('/keke')
    def test_keke(self, start_response):
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [b"<i>kekekekeke</i>"]
        