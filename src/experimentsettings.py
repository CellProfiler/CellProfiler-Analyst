from singleton import Singleton

class ExperimentSettings(Singleton):
    def __init__(self):
        self.global_settings = {}
        self.timeline = None
        
    def set_field(self, field, value):
        self.global_settings[field] = value

    def get_field(self, field, default=None):
        return self.global_settings.get(field, default)
    
    def clear(self):
        self.global_settings = {}
        self.timeline = None        

    def save_to_file(self, file):
        f = open(file, 'w')
        for field, value in self.global_settings.items():
            f.write('%s = %s\n'%(field, repr(value)))
        #self.timeline.save_to_file(f)
        f.close()

    def load_from_file(self, file):
        self.clear()
        f = open(file, 'r')
        for line in f:
            field, value = line.split('=')
            field = field.strip()
            self.set_field(field, eval(value))
        f.close()
        
        
        
if __name__ == "__main__":
    settings = ExperimentSettings.getInstance()
    settings.set_field('test_string', 'test_value')
    settings.set_field('test_list',   ['data', 3])
    settings.set_field('test_int',    2)
    settings.set_field('test_float',  234.3)
    
    settings.save_to_file('/Users/afraser/Desktop/test.txt')
    print settings.global_settings.items()
    before = settings.global_settings.items()
    
    settings.load_from_file('/Users/afraser/Desktop/test.txt')    
    print settings.global_settings.items()
    after = settings.global_settings.items()
    
    for a, b in zip(sorted(before), sorted(after)):
        assert a == b, 'loaded data is not the same as the saved data.'