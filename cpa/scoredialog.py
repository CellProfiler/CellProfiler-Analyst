
import wx

class ScoreDialog(wx.Dialog):
    """
    A dialog that prompts the user for group and filter, and whether or not
    to calculate/report enrichment values.
    """
    def __init__(self, parent, groups, filters, enrichments=True):
        """Groups and filters are lists.  Each item in the list is
        either a (key, value) pair or a non-tuple value (e.g., a
        string).  In the latter case, str(value) is used as the key."""
        wx.Dialog.__init__(self, parent, -1, "Score all cells")

        def key_value(item):
            if isinstance(item, tuple):
                return item
            else:
                return (item, str(item))
        
        self.groups = list(map(key_value, groups))
        self.filters = list(map(key_value, filters))

        self.groups_lb = wx.ListBox(self, choices=[v for k,v in self.groups])
        self.groups_lb.SetSelection(0)
        self.filters_lb = wx.ListBox(self, choices=[v for k,v in self.filters])
        self.filters_lb.SetSelection(0)
        self._wants_enrichments = wx.CheckBox(self, -1, 'Report enrichments?')
        self._wants_enrichments.SetValue(enrichments)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(wx.StaticText(self, -1, 'Grouping method:'), 0)
        vbox.Add(self.groups_lb, 1, wx.EXPAND)
        vbox.Add(wx.StaticText(self, -1, 'Filter:'), 0, wx.TOP, 5)
        vbox.Add(self.filters_lb, 1, wx.EXPAND)
        vbox.Add(self._wants_enrichments)
        vbox.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL), 0,
                 wx.TOP | wx.ALIGN_CENTER, 5)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(vbox, 1, wx.EXPAND | wx.ALL, 10)
        self.SetSizer(hbox)
        self.Centre()

    @property
    def group(self):
        """Return the key of the selected group."""
        return self.groups[self.groups_lb.GetSelections()[0]][0]

    @property
    def filter(self):
        """Return the key of the selected filter."""
        return self.filters[self.filters_lb.GetSelections()[0]][0]
    
    @property
    def wants_enrichments(self):
        """Return whether the user checked the "Report enrichments?" box."""
        return self._wants_enrichments.Value


if __name__ == "__main__":
    app = wx.App()
    d = ScoreDialog(None, [str(a) for a in range(15)],
                    [(None, 'None'), 'Untreated', 'HRG'])
    if d.ShowModal() == wx.ID_OK:
        print('a')
        print(("Group:", repr(d.group)))
        print(("Filter:", repr(d.filter)))
        print(((d.wants_enrichments and 'Wants' or 'Does not want') + ' enrichments'))
    d.Destroy()
