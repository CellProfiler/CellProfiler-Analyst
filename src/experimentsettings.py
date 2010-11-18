from singleton import Singleton

class ExperimentSettings(Singleton):
    def __init__(self):
        self.global_settings = {}
        self.timeline = None
        
    def set_field(self, tag, value):
        self.global_settings[tag] = value

    def get_field(self, tag, default=None):
        return self.global_settings.get(tag, default)
    
    def remove_field(self, tag):
        if self.get_field(tag) is not None:
            self.global_settings.pop(tag)
    
    def get_field_instances(self, tag_prefix):
        '''returns a list of unique instance ids for each tag beginning with 
        tag_prefix'''
        ids = set([tag.rsplit('|', 1)[-1] for tag in self.global_settings
                   if tag.startswith(tag_prefix)])
        return list(ids)

    def get_field_tags(self, tag_prefix, instance=''):
        '''returns a list of all tags beginning with tag_prefix. If instance
        is passed in, only tags of the given instance will be returned'''
        return [tag for tag in self.global_settings 
                if tag.startswith(tag_prefix) and tag.endswith(instance)]
    
    def clear(self):
        self.global_settings = {}
        self.timeline = None        

    def save_to_file(self, file):
        f = open(file, 'w')
        for field, value in self.global_settings.items():
            f.write('%s = %s\n'%(field, repr(value)))
        f.close()

    def load_from_file(self, file):
        self.clear()
        f = open(file, 'r')
        for line in f:
            field, value = line.split('=')
            field = field.strip()
            self.set_field(field, eval(value))
        f.close()