import logging
import os.path as op

import paths
from .Python3 import Python3
from .util import ConfigError


class Scripts(object):
    def __init__(self, config):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.scripts = {}
        for name, script in list(config.items()):
            print(f"{name}, {script}")
            self.scripts[name] = []
            if isinstance(script, str):
                path = op.join(paths.CONFIG_DIR, script)
                print(f"The path for this one is {path}")
                self.scripts[name].append(Python3(path))
                continue

            for s in script:
                path = op.join(paths.CONFIG_DIR, s['path'])
                timeout = s.get('timeout', 0)
                logcat_regex = s.get('logcat_regex', None)

                if s['type'] == 'python3':
                    script = Python3(path, timeout, logcat_regex)
                else:
                    raise ConfigError('Unknown script type: {}'.format(s['type']))

                self.scripts[name].append(script)


    def run(self, name, device, *args, **kwargs):
        self.logger.debug('Running hook {} on device {}\nargs: {}\nkwargs: {}'.format(name, device, args, kwargs))
        for script in self.scripts.get(name, []):
            script.run(device, *args, **kwargs)
