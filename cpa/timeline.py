import experimentsettings as exp

class Timeline(object):
    '''Represents a timeline.
    '''
    def __init__(self, stock):
        self.stock = stock
        # events : a chronologically ordered list of events
        self.events = []
        # plate_ids : a list of plate ids included in the experiment
        #             (all events will take place on these plates)
        self.plate_ids = set([])

    def add_event(self, welltag, well_ids):
        '''Creates and inserts an event into the timeline.
        '''
        evt = Event(welltag, well_ids)
        self.plate_ids.update(set([well_id[0] for well_id in well_ids]))
        if len(self.events) == 0:
            self.events = [evt]
        else:
            # search from the end of the list since most insertions will occur there
            for i in range(len(self.events)-1, -1, -1): 
                if evt.get_timepoint() > self.events[i].get_timepoint() or i==0:
                    self.events.insert(i+1,evt)
                    break
        return evt

    def delete_event(self, welltag):
        for i, e in enumerate(self.events):
            if (e.get_welltag() == welltag):
                self.events = self.events[:i] + self.events[i+1:]
                break
            
    def get_unique_timepoints(self):
        '''returns an ascending ordered list of UNIQUE timepoints on this timeline
        '''
        return sorted(set([e.get_timepoint() for e in self.events]))
    
    def get_max_timepoint(self):
        '''returns the last timepoint in the timeline
        '''
        #TODO: make this fast
        return self.get_unique_timepoints()[-1]

    def get_event_list(self):
        '''returns a list of events in chronological order
        '''
        # return a copy
        return list(self.events)

    def get_events_at_timepoint(self, timepoint):
        '''returns each event that occurred at the exact timepoint specified
        '''
        return [evn for evn in self.events if evn.get_timepoint() == timepoint]
    
    def get_events_by_timepoint(self):
        '''return a dictionary of event lists keyed by timepoint
        '''
        d = {}
        for event in self.events:
            if d.get(event.get_timepoint(), None) is None:
                d[event.get_timepoint()] = [event]
            else:
                d[event.get_timepoint()] += [event]
        return d

    def get_event(self, welltag):
        '''returns a specific event that occurred for a specific tag instance
        at the given timepoint
        '''
        for e in self.events:
            if (e.get_welltag() == welltag):
                return e
        return None

    def get_events_in_well(self, wellid, timepoint):
        '''returns a tuple of events that occurred in the given well at timepoint
        '''
        return tuple([evt for evt in self.get_events_at_timepoint(timepoint) 
                      if wellid in evt.get_well_ids()])

    def get_well_ids(self, timepoint=None):
        well_ids = []
        for evt in self.get_event_list():
            if evt.get_timepoint() == timepoint or timepoint == None:
                well_ids += evt.get_well_ids()
        return list(set(well_ids))

    # CURRENTLY UNUSED
    def get_event_permutations(self, timepoint):
        '''returns a list of unique permutations of events at a given timepoint.
        Each permutation is a tuple of events that occurred.
        '''
        d = {}
        for event in self.get_events_at_timepoint(timepoint):
            # build a hash, mapping well_ids to lists of events that occurred
            for well in exp.PlateDesign.get_well_ids(
                           exp.PlateDesign.get_plate_format(event.get_plate_id())):
                if well in event.get_well_ids():
                    if d.get(well, None) is None:
                        d[well] = [event]
                    else:
                        d[well] += [event]
        return set([tuple(set(d[k])) for k in d.keys()])

    def get_well_permutations(self, timepoint):
        '''returns a dict mapping unique sets of events to well lists
        d = {(e1,)   : [(p1 A01), (p1, A03)],
             (e1,e2) : [(p1, A02), (p1, B03)],
             (e2, )  : [(p1, B02)]
             ()      : [(p1, B01)]            # no event
             }
        '''
        # TODO: improve performance (tree building explodes with larger plates)
        d = {}
        for pwid in exp.PlateDesign.get_all_platewell_ids():
            events_in_well = self.get_events_in_well(pwid, timepoint)
            d[events_in_well] = d.get(events_in_well, []) + [pwid]
        return d

    def get_lineage_tree(self):
        '''Returns a tree that traces the lineage of unique well states through 
        all timepoints in the timeline. The root of this tree will be the timeline
        stock.
        '''
        timepoints = self.get_unique_timepoints()
        permutations_per_timepoint = {}
        for t in timepoints:
            permutations_per_timepoint[t] = self.get_well_permutations(t)
        
        def attach_child_nodes(parent, tp_idx):
            '''For a particular timepoint index and parent node, this function 
            will calculate the subsets of wells that will represent each child 
            node. It then creates the children and links them into the parent.
            parent -- the parent node to add children to
            tp_idx -- the index of the current timepoint in the timeline
                      (== the depth of the current node in the tree)
            '''
            timepoint = timepoints[tp_idx]
            node_data = []
            for events, wells in permutations_per_timepoint[timepoint].items():
                wellset = set(parent.get_well_ids()).intersection(wells)
                if len(wellset) > 0:
                    node_data += [(events, wellset)]
            for childnum, (events, wells) in enumerate(node_data):
                parent.add_child(id = '%s:%s'%(parent.id, childnum),
                                 tags = [e.get_welltag() for e in events],
                                 wells = wells,
                                 timepoint = timepoint)

        def build_tree(parent, tp_idx=0):
            '''Creates a lineage tree by calling the attach_child_nodes to compute
            the children for a given node and attaches them. The function then 
            recurses into each childnode.
            parent -- the current root node for this branch of the tree.
            tp_idx -- the index of the current timepoint in the timeline
                      (== the depth of the current node in the tree)
            '''
            if tp_idx < len(timepoints):
                attach_child_nodes(parent, tp_idx)
                for child in parent.get_children():
                    build_tree(child, tp_idx+1)
            return parent

        root = LineageNode(None, self.stock, [], self.get_well_ids(), -1)
        return build_tree(root)

    def get_nodes_by_timepoint(self):
        '''returns a dict mapping timepoints to LineageNodes
        '''
        def get_dict(node, d):
            if not node.children:
                return d
            d.setdefault(node.children[0].timepoint, []).extend(node.children)
            for child in node.children:
                d.update(get_dict(child, d))
            return d
        tree = self.get_lineage_tree()
        return get_dict(tree, {tree.timepoint:[tree]})

    def save(self, filename):
        '''Saves the timeline to filename
        '''
        raise NotImplemented

    def load(self, filename):
        '''Loads a timeline from filename
        '''
        raise NotImplemented


class Event(object):
    '''An Event is an action that was taken at some timepoint that is associated
    with a list of well_ids.
    '''
    def __init__(self, welltag, well_ids):
        '''welltag : the well tag from the experiement metadata
        wells_ids : the list of well_ids that this event effects
        '''
        self.welltag = welltag
        self.wells = well_ids

    def get_timepoint(self):
        return exp.get_tag_timepoint(self.welltag)

    def get_well_ids(self):
        return self.wells

    def get_welltag(self):
        return self.welltag

    def set_well_ids(self, well_ids):
        self.wells = well_ids

    def __str__(self):
        return '%s event'%(self.welltag)


def reverse_iter_tree(node):
    '''a generator that returns parents of the given node.
    '''
    while node is not None:
        yield node.parent
        node = node.parent
        
def get_progeny(node):
    for child in node.get_children():
        yield child
        for grandchild in get_progeny(child):
            yield grandchild        

class LineageNode(object):
    '''A lineage node represents a unique state in a subset of wells at a given
    timepoint. For example: the set of wells that were seeded at density X at t0,
    treated with reagent Y at t1, and imaged at t2.
    '''
    def __init__(self, parent, id, tags, wells, timepoint):
        self.parent = parent
        self.id = id
        self.tags = tags
        self.wells = wells
        self.timepoint = timepoint
        self.children = []

    def get_parent(self):
        return self.parent

    def get_children(self):
        return self.children

    def get_tags(self):
        return self.tags
    
    def get_well_ids(self):
        return self.wells

    def get_timepoint(self):
        return self.timepoint

    def __eq__(self, node):
        return self is node

    def __neq__(self, node):
        return node is not self

    def add_child(self, id, tags, wells, timepoint):
        '''create a child node and link child -> parent and parent -> child
        '''
        self.children += [LineageNode(self, id, tags, wells, timepoint)]

    def __str__(self):
        return ', '.join(self.tags)
        #if self.parent:
            #return 'p:%s; id:%s; wells:%s'%(self.parent.id, self.id, sorted(self.wells))
        #else:
            #return 'ROOT; id:%s; wells:%s'%(self.id, sorted(self.wells))


#
# Test code here
#
#if __name__ == '__main__':
    ##import numpy as np
    
    #N_FURCATIONS = 2
    #N_TIMEPOINTS = 5
    #MAX_TIMEPOINT = 10
    #PLATE_TYPE = exp.P6

    #def generate_random_data():
        #meta = exp.ExperimentSettings.getInstance()
        #exp.PlateDesign.add_plate('test', PLATE_TYPE)
        #allwells = exp.PlateDesign.get_well_ids(exp.PlateDesign.get_plate_format('test'))
        #event_types = ['AddProcess|Stain|Wells|0|',
                       #'AddProcess|Wash|Wells|0|',
                       #'AddProcess|Dry|Wells|0|',
                       #'AddProcess|Spin|Wells|0|',
                       #'Perturbation|Chem|Wells|0|',
                       #'Perturbation|Bio|Wells|0|',
                       #'DataAcquis|TLM|Wells|0|',
                       #'DataAcquis|FCS|Wells|0|',
                       #'DataAcquis|HCS|Wells|0|',
                       #'CellTransfer|Seed|Wells|0|',
                       #'CellTransfer|Harvest|Wells|0|']
        ## GENERATE RANDOM EVENTS ON RANDOM WELLS
        #for t in list(np.random.random_integers(0, MAX_TIMEPOINT, N_TIMEPOINTS)):
            #for j in range(np.random.randint(1, N_FURCATIONS)):
                #np.random.shuffle(allwells)
                #well_ids = [('test', well) for well in allwells[:np.random.randint(1, len(allwells)+1)]]
                ##timeline.add_event(t, 'event%d'%(t), well_ids)
                #etype = event_types[np.random.randint(0,len(event_types))]
                #meta.set_field('%s%s'%(etype, t), well_ids)

    #generate_random_data()
    #meta = exp.ExperimentSettings.getInstance()
    #t = meta.get_timeline()
    #tree = t.get_lineage_tree()
    