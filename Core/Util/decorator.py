import os
import sys
import time
import cStringIO

from formatter import Formatter

class method_tracer:
    def __init__(self, name_only = False, silent = False):
        self.name_only = name_only
        self.silent = silent

    def __call__(self, func):
        if not self.silent:
            def _trace(_self, *args, **kwargs):
                start_time = time.clock()

                print Formatter.methodized(_self, func.__name__, *args, **kwargs),

                if not self.name_only:
                    stdout_cache, sys.stdout = sys.stdout, cStringIO.StringIO()
                else:
                    stdout_cache, sys.stdout = sys.stdout, open(os.devnull, 'wb')

                try:
                    result = func(_self, *args, **kwargs)
                    return result
                except:
                    result = 'ERROR'
                    raise
                finally:
                    stdout_cache, sys.stdout = sys.stdout, stdout_cache

                    print result, '...', time.clock() - start_time
                    if not self.name_only and len(stdout_cache.getvalue()) > 0:
                        print Formatter.tablized(stdout_cache.getvalue()),
                    stdout_cache.close()
        else:
            def _trace(_self, *args, **kwargs):
                stdout_cache, sys.stdout = sys.stdout, open(os.devnull, 'wb')

                try:
                    result = func(_self, *args, **kwargs)
                    return result
                finally:
                    stdout_cache, sys.stdout = sys.stdout, stdout_cache
                    stdout_cache.close()
        return _trace
