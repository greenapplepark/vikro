import sys
import os
import argparse
import runpy
import vikro

sys.path.insert(0, os.getcwd())

def run_vikro():
    parser = argparse.ArgumentParser(prog="vikro")
    parser.add_argument("-v", "--version",
        action="version", version="%(prog)s {}".format(vikro.__version__))
    parser.add_argument("service", nargs='?', help="""
        service class path to run (modulename.ServiceClass)
        """.strip())
    args = parser.parse_args()
    if args.service:
        try:
            service_class = load_service_class(args.service)
            print service_class
            start_service(service_class)
        except RuntimeError, e:
            parser.error(e)
    else:
        parser.print_usage()


def run_vikromgr():
    print "run_vikromgr"


def load_service_class(service_path):
    print "load_service_class"
    if '.' not in service_path:
        raise RuntimeError("Invalid class path")
    module_name, class_name = service_path.rsplit('.', 1)
    try:
        try:
            module = runpy.run_module(module_name)
        except ImportError:
            module = runpy.run_module(module_name + ".__init__")
    except ImportError, e:
            raise RuntimeError("Unable to load class path: {}:\n{}".format(
                service_path, e))
    try:
        return module[class_name]
    except KeyError, e:
        raise RuntimeError("Unable to find class in module: {}".format(
            service_path))

def start_service(service_class):
    service = service_class()
    if not isinstance(service, vikro.service.BaseService):
        raise RuntimeError("{} is not Service type\n".format(service_class))
    service.start()