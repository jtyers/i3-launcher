import os
import sys
from threading import Thread, Event

# FIXME currently unused!


# https://stackoverflow.com/a/12435256/1432488
# https://stackoverflow.com/a/49007649/1432488
class Watcher(Thread):
    """
    Watcher that polls the save_tree_file and calls a function when it changes.
    """

    def __init__(self, call_func_on_change=None, *args, **kwargs):
        Thread.__init__(self)
        self.stopFlag = Event()

        self._cached_stamp = 0
        self.filename = save_file
        self.call_func_on_change = call_func_on_change
        self.args = args
        self.kwargs = kwargs

    # Look for changes
    def look(self):
        stamp = os.stat(self.filename).st_mtime
        if stamp != self._cached_stamp:
            self._cached_stamp = stamp
            # File has changed, so do something...
            if self.call_func_on_change is not None:
                self.call_func_on_change(*self.args, **self.kwargs)

    def run(self):
        while not self.stopFlag.wait(2.0):
            # call a function
            try:
                self.look()
            except KeyboardInterrupt:
                self.stopFlag.set()
                break

            except FileNotFoundError:
                # Action on file not found
                pass
            except:
                print("Unhandled error: %s" % sys.exc_info()[0])

    def stop(self):
        self.stopFlag.set()
