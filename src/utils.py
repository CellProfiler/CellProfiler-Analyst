
class Observable:
    '''Mixin for objects that need to be observed by other objects.'''
    _observers = None
    def addobserver(self, observer):
        if not self._observers:
            self._observers = []
        self._observers.append(observer)

    def removeobserver(self, observer):
        self._observers.remove(observer)

    def notify(self, event):
        for o in self._observers or ():
            o(event)


class ObservableDict(dict, Observable):
    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.notify((key, value))

