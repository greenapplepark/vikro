import sys
import os
import os.path
import argparse
import runpy
import vikro
import inspect
from util import Config2Dict
from service import BaseService

sys.path.insert(0, os.getcwd())

def run_vikro():
    parser = argparse.ArgumentParser(prog='vikro')
    parser.add_argument('-v', '--version',
        action='version', version='%(prog)s {}'.format(vikro.__version__))
    parser.add_argument('service', nargs='?', help='''
        service class path to run (modulename.ServiceClass)
        '''.strip())
    parser.add_argument("-c", "--config", help="""
        config file to specify amqp server, name server and more
        """.strip())
    args = parser.parse_args()
    if args.service:
        try:
            module_name, class_name = parse_module_class(args.service)
            service_config = parse_config(args.config, module_name)
            service_class = get_service_class(module_name, class_name)
            start_service(service_class, service_config)
        except RuntimeError, e:
            parser.error(e)
    else:
        parser.print_usage()

def run_vikromgr():
    print 'run_vikromgr'

def parse_module_class(service_path):
    if '.' not in service_path:
        raise RuntimeError('Invalid class path')
    return service_path.rsplit('.', 1)

def parse_config(config, module_name):
    config_file_path = None
    service_config = None
    if config is not None:
        if os.path.isfile(config):
            config_file_path = config
        elif os.path.isfile(os.path.join(os.getcwd(), config)):
            config_file_path = os.path.join(os.getcwd(), config)
    
    if config_file_path is None:
        if os.path.isfile(os.path.join(os.getcwd(), module_name + '.ini')):
            config_file_path = os.path.join(os.getcwd(), module_name + '.ini')
            config_parser = Config2Dict()
            config_parser.read(config_file_path)
            service_config = config_parser.as_dict()
        else:
            print 'Warning: cannot find config file. Your service will run alone'
    return service_config

def get_service_class(module_name, class_name):
    try:
        try:
            module = runpy.run_module(module_name)
        except ImportError:
            module = runpy.run_module(module_name + '.__init__')
    except ImportError, e:
            raise RuntimeError('Unable to load class path: {}:\n{}'.format(
                service_path, e))
    try:
        return module[class_name]
    except KeyError, e:
        raise RuntimeError('Unable to find class in module: {}'.format(
            service_path))

def start_service(service_class, service_config):
    service = service_class(service_config)
    if not isinstance(service, vikro.service.BaseService):
        raise RuntimeError('{} is not Service type\n'.format(service_class))
    try:
        service.start()
    except KeyboardInterrupt:
        print 'Service stopping'
        service.stop()