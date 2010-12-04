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

    def add_event(self, timepoint, action, well_ids):
        '''Creates and inserts an event into the timeline.
        '''
        evt = Event(timepoint, action, well_ids)
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

    def delete_event(self, timepoint, action):
        for i, e in enumerate(self.events):
            if (e.get_timepoint() == timepoint and e.get_action() == action):
                self.events = self.events[:i] + self.events[i+1:]
                break
            
    def get_unique_timepoints(self):
        '''returns an ascending ordered list of UNIQUE timepoints on this timeline
        '''
        return sorted(set([e.get_timepoint() for e in self.events]))

    def get_event_list(self):
        '''returns a list of events in chronological order
        '''
        # return a copy of the event list
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
            if d.get(event.timepoint, None) is None:
                d[event.timepoint] = [event]
            else:
                d[event.timepoint] += [event]
        return d
        

    def get_event(self, action, timepoint):
        '''returns a specific event that occurred for a specific tag instance
        at the given timepoint
        '''
        for e in self.events:
            if (e.get_timepoint() == timepoint and e.get_action() == action):
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
        from experimentsettings import PlateDesign
        d = {}
        for event in self.get_events_at_timepoint(timepoint):
            # build a hash, mapping well_ids to lists of events that occurred
            for well in PlateDesign.get_well_ids(PlateDesign.get_plate_format(event.get_plate_id())):
                if well in event.get_well_ids():
                    if d.get(well, None) is None:
                        d[well] = [event]
                    else:
                        d[well] += [event]
        return set([tuple(set(d[k])) for k in d.keys()])

    def get_well_permutations(self, timepoint):
        '''returns a list of well-permutations
        Each permutation is a tuple of wells that have a common state.
        d = {(e1,)   :  ((p1 A01), (p1, A03)),
             (e1,e2) :  ((p1, A02), (p1, B03)),
             (e2, )  :  ((p1, B02))
             (noop)  :  ((p1, B01)) }
        '''
        # TODO: improve performance (tree building explodes with larger plates)
        from experimentsettings import PlateDesign
        d = {}
        for wellid in PlateDesign.get_all_platewell_ids():
            events_in_well = self.get_events_in_well(wellid, timepoint)
            if d.get(events_in_well, None) is None:
                d[events_in_well] = [wellid]
            else:
                d[events_in_well] += [wellid]
        return set([tuple(set(d[k])) for k in d.keys()])

    def get_lineage_tree(self):
        '''Returns a tree that traces the lineage of unique well states through 
        all timepoints in the timeline. The root of this tree will be the timeline
        stock.
        '''
        timepoints = self.get_unique_timepoints()
        well_permutations_per_timepoint = {}
        for t in timepoints:
            well_permutations_per_timepoint[t] = self.get_well_permutations(t)
        
        def attach_child_nodes(parent, tp_idx):
            '''For a particular timepoint index and parent node, this function will
            calculate the subsets of wells that will represent each child node. It
            then creates the children and links them into the parent.
            parent -- the parent node to add children to
            tp_idx -- the index of the current timepoint in the timeline
                      (== the depth of the current node in the tree)
            '''
            timepoint = timepoints[tp_idx]
            subwells = []
            for wells in well_permutations_per_timepoint[timepoint]:
                wellset = sorted(set(parent.get_well_ids()).intersection(wells))
                if len(wellset) > 0:
                    subwells += [wellset]
            for childnum, wells in enumerate(subwells):
                parent.add_child(id = '%s:%s'%(parent.id, childnum),
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

        root = LineageNode(None, self.stock, self.get_well_ids(), -1)
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
    def __init__(self, timepoint, action, well_ids):
        '''timepoint : the timepoint that this event occurred at
        action : the action that took place
        wells_ids : the list of well_ids that this event effects
        '''
        self.action = action
        self.wells = well_ids
        self.timepoint = timepoint

    def get_timepoint(self):
        return self.timepoint

    def get_well_ids(self):
        return self.wells

    def get_action(self):
        return self.action

    def set_well_ids(self, well_ids):
        self.wells = well_ids

    def __str__(self):
        return '%s event'%(self.action)


class LineageNode(object):
    '''A lineage node represents a unique state in a subset of wells at a given
    timepoint. For example: the set of wells that were seeded at density X at t0,
    treated with reagent Y at t1, and imaged at t2.
    '''
    def __init__(self, parent, id, wells, timepoint):
        self.parent = parent
        self.id = id
        self.wells = wells
        self.timepoint = timepoint
        self.children = []

    def get_parent(self):
        return self.parent

    def get_children(self):
        return self.children

    def get_well_ids(self):
        return self.wells

    def get_timepoint(self):
        return self.timepoint

    def __eq__(self, node):
        return self is node

    def __neq__(self, node):
        return node is not self

    def add_child(self, id, wells, timepoint):
        '''create a child node and link child -> parent and parent -> child
        '''
        self.children += [LineageNode(self, id, wells, timepoint)]

    def __str__(self):
        if self.parent:
            return 'p:%s; id:%s; wells:%s'%(self.parent.id, self.id, sorted(self.wells))
        else:
            return 'ROOT; id:%s; wells:%s'%(self.id, sorted(self.wells))


#
# Test code here
#
if __name__ == '__main__':
    t = Timeline('U2OS')
    PlateDesign.add_plate('plate1', P6)
    PlateDesign.add_plate('plate2', P6)
    all_wells = PlateDesign.get_well_ids(PlateDesign.get_plate_format('plate1'))

    t.add_event(1, 'seed', [('plate1', well) for well in all_wells]+[('plate2', well) for well in all_wells])

    t.add_event(2, 'treatment1', [('plate1', 'A01'), ('plate1', 'A02'), ('plate1', 'A03'), 
                                  ('plate1', 'B03')])
    t.add_event(2, 'treatment2', [                   ('plate1', 'A02'), 
                                                     ('plate1', 'B02'), ('plate1', 'B03'), 
                                                     ('plate2', 'A01')])
    #untreated_wells = set(all_wells) - set(t.get_well_ids(2))
    #t.add_event(2, NO_EVENT,     'plate1', untreated_wells)  

    t.add_event(3, 'treat', [('plate1', 'A01'),                         ('plate1', 'A03'), 
                             ('plate1', 'B02')])
    t.add_event(3, 'wash', [                       ('plate1', 'B02'), ('plate1', 'B03')])
    #untreated_wells = set(all_wells) - set(t.get_well_ids(3))
    #t.add_event(3, NO_EVENT, 'plate1', untreated_wells)

    t.add_event(4, 'spin', [('plate1', 'A01'), ('plate1', 'A02'), ('plate1', 'A03')])
    #untreated_wells = set(all_wells) - set(t.get_well_ids(4))
    #t.add_event(4, NO_EVENT, 'plate1', untreated_wells)

    d = t.get_nodes_by_timepoint()

    for time in d.keys():
        print str(time)+"\t"+str([node.id for node in d[time]])

    for p in t.get_well_permutations(2):
        print [x for x in p]

    tree = t.get_lineage_tree()

    import wx
    app = wx.PySimpleApp()
    f = wx.Frame(None)
    tc = wx.TreeCtrl(f)
    tcroot = tc.AddRoot("ROOT")
    def populate_wx_tree(wxparent, tnode):
        for child in tnode.children:    
            subtree = tc.AppendItem(wxparent, ', '.join([str(id) for id in child.get_well_ids()]))
            populate_wx_tree(subtree, child)
            tc.Expand(subtree)
    populate_wx_tree(tcroot, tree)    
    tc.Expand(tcroot)

    f.Show()
    app.MainLoop()
