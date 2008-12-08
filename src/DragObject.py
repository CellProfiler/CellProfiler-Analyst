from Singleton import Singleton

class DragObject(Singleton):
    def __init__(self):
        self.data = None
        self.source = None
    
    def IsEmpty(self):
        return self.data == None
    
    def Empty(self):
        self.data = None