from vikro.service import BaseService

class HelloService(BaseService):

    def start(self):
        super(HelloService, self).start()
        print "HelloService start"

    def stop(self):
        pass

    def reload(self):
        pass