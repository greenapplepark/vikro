"""
vikro.runner
~~~~~~~~~~~~

This module provides command line support for vikro.
"""

import sys
import os
import os.path
import argparse
import runpy
import logging
import vikro
from vikro.util import Config2Dict

logger = logging.getLogger(__name__)

sys.path.insert(0, os.getcwd())

def run_vikro():
    """Use vikro to run vikro."""
    parser = argparse.ArgumentParser(prog='vikro')
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s {}'.format(vikro.__version__))
    parser.add_argument('service', nargs='?', help="""
        service class path to run (modulename.ServiceClass)
        """.strip())
    parser.add_argument('-c', '--config', help="""
        config file to specify amqp server, name server and more
        """.strip())
    args = parser.parse_args()
    if args.service:
        try:
            module_name, class_name = parse_module_class(args.service)
            service_config = parse_config(args.config, module_name)
            service_class = get_service_class(module_name, class_name)
            start_service(service_class, service_config)
        except RuntimeError, ex:
            parser.error(ex)
    else:
        parser.print_usage()

def run_vikromgr():
    """Run vikro manager."""
    logger.info('run_vikromgr.')

def parse_module_class(service_path):
    """Get module name and class name from command line."""
    if '.' not in service_path:
        raise RuntimeError('Invalid class path')
    return service_path.rsplit('.', 1)

def parse_config(config, module_name):
    """Parse configuration file."""
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
            logger.warning('Cannot find config file. Your service will run alone.')
    return service_config

def get_service_class(module_name, class_name):
    """Rum module and get service class."""
    try:
        try:
            module = runpy.run_module(module_name)
        except ImportError:
            module = runpy.run_module(module_name + '.__init__')
    except ImportError, ex:
        raise RuntimeError(
            'Unable to load class path: {}.{}:\n{}'.format(module_name, class_name, ex))
    try:
        return module[class_name]
    except KeyError:
        raise RuntimeError(
            'Unable to find service class in module: {}.'.format(module_name))

def start_service(service_class, service_config):
    """Start vikro service."""
    service = service_class(service_config)
    if not isinstance(service, vikro.service.BaseService):
        raise RuntimeError('{} is not Service type\n'.format(service_class))
    try:
        service.start()
    except KeyboardInterrupt:
        logger.info('Service stopping.')
        service.stop()
