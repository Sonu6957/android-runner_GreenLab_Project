import os.path as op
import importlib
import sys

from .Script import Script

class Python3(Script):
    def __init__(self, path, timeout=0, logcat_regex=None):
        super(Python3, self).__init__(path, timeout, logcat_regex)
        try:
            print(f"Loading module {op.basename(path)} from {path}")
            loader = importlib.machinery.SourceFileLoader(op.basename(path), op.join(path))
            spec = importlib.util.spec_from_file_location(op.basename(path), op.join(path), loader=loader)
            self.module = importlib.util.module_from_spec(spec)
            
            # Cache the module for fast access in the future
            sys.modules[self.module.__name__] = self.module
            loader.exec_module(self.module)

            self.logger.debug('Imported %s' % path)
        except ImportError:
            self.logger.error('Cannot import %s' % path)
            raise ImportError("Cannot import %s" % path)

    def execute_script(self, device, *args, **kwargs):
        super(Python3, self).execute_script(device, *args, **kwargs)
        return self.module.main(device, *args, **kwargs)
