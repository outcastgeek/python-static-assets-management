
from os import path
from webassets import Bundle, Environment
from ConfigParser import ConfigParser

import sys
import requests
import logging

# Setup a logger
log = logging.getLogger('static_assets')
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG)

requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.DEBUG)

config = ConfigParser()
config.read('config.ini')

JS_VENDOR = path.join(path.dirname(__file__), 'javascript/src/vendor')
JS_DEPLOY = path.join(path.dirname(__file__), 'javascript')
CSS_DEPLOY = path.join(path.dirname(__file__), 'stylesheets')

def concat_string(coll):
    string = ''.join(coll)
    return string

def resolve_external_deps(name, url, VENDOR):
    full_url = concat_string(['http://', url, '/', name])
    my_config = {'verbose': sys.stderr,
                 'timeout' : 0.01}
    file = requests.get(full_url, config=my_config)
    with open(path.join(VENDOR, name),'w') as output:
        output.writelines(file.content)

def resolve(VENDOR):
    section = 'remotejs'
    for lib in config.options(section):
        root = config.get(section, lib)
        log.info("%s/%s <<== http://%s/%s", VENDOR, lib, root, lib)
        resolve_external_deps(lib, root, VENDOR)

def create_and_register_bundles(section, filter, DEPLOY):
    environment = Environment('.')
    for option in config.options(section):
        deps = [v.strip() for v in config.get(section, option).split(',')]
        log.info("%s.%s has dependencies: %s", option, section, deps)
        bndl = Bundle(*deps, filters=filter,
                      output=concat_string([DEPLOY, '/', option, '.', section]))
        environment.register(option, bndl)
        bndlgz = Bundle(*deps, filters=concat_string([filter, ', gzip']),
                      output=concat_string([DEPLOY, '/', option, '.', section, '.gz']))
        environment.register(concat_string([option, 'gz']), bndlgz)
        bndl.build()
        bndlgz.build()

if __name__ == '__main__':
    resolve(JS_VENDOR)
    create_and_register_bundles('js', 'jsmin', JS_DEPLOY)
    create_and_register_bundles('css', 'cssutils', CSS_DEPLOY)
