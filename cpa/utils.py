
class Observable:
    '''Mixin for objects that need to be observed by other objects.'''
    _observers = None
    def addobserver(self, observer):
        if not self._observers:
            self._observers = []
        self._observers.append(observer)

    def removeobserver(self, observer):
        if self._observers and observer in self._observers:
            self._observers.remove(observer)

    def notify(self, event):
        for o in self._observers or ():
            o(event)


class ObservableDict(dict, Observable):
    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.notify((key, value))

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self.notify((key, None))
        
    def pop(self, key):
        v = dict.pop(self, key)
        self.notify((key, None))
        return v
    
    def clear(self):
        dict.clear(self)
        self.notify(None)


# AutoSave
import threading
from functools import wraps

def delay(delay=0.):
    """
    Decorator delaying the execution of a function for a while.
    """
    def wrap(f):
        @wraps(f)
        def delayed(*args, **kwargs):
            timer = threading.Timer(delay, f, args=args, kwargs=kwargs)
            timer.start()
        return delayed
    return wrap