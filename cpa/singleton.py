'''
This Singleton metaclass ensures that only one instance of a
class can be created. Subsequent calls to make that class will
return the original instance. In Python 3, specify metaclass=Singleton
to use this functionality.

If you absolutely must re-create a singleton, use the forget() method
to delete the original instance. A new instance will then be created
on the next class call.

This version was put together to replace a more complex Python 2 singleton
class that no longer works in Python 3. Good luck!
'''

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

    def forget(cls):
        if cls in cls._instances:
            del cls._instances[cls]

