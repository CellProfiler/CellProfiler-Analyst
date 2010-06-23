from dbconnect import *
from properties import Properties

p = Properties.getInstance() 

def merge_filters(filters):
    ''' Takes a list of filters, returns a single filter with all the where 
    clauses combined'''
    wc = []
    for filter in filters:
        wc += filter.get_where_clauses()
    return Filter()

class Filter:
    '''
    Represents a method for filtering results from the database.
    Filters are comprised of one or more WhereClause classes.
    '''
    def __init__(self, table=None, column=None, comparator=None, value=None):
        self.where_clauses = set([])
        if None not in [table, column, comparator, value]:
            self.where_clauses = [WhereClause(table, column, comparator, value)]
        elif not table==column==comparator==value==None:
            raise Exception, 'All Filter fields are required.'
    
    def __str__(self):
        tables = set([cl.table for cl in self.where_clauses])
        # currently expect table to be the per image table
        return ('SELECT %s FROM %s WHERE %s'%(UniqueImageClause(p.image_table), 
                ', '.join(tables),
                ' AND '.join(map(str, self.where_clauses))))
    
    def get_where_clauses(self):
        return self.where_clauses
    
    def add_column(self, table, column, comparator, value):
        self.where_clauses += [WhereClause(table, column, comparator, value)]
        
    def add_where_clause(self, wc):
        self.where_clauses.add(wc)
        
    def add_filter(self, filter):
        self.where_clauses.add(filter.get_where_clauses())
        
    def __add__(self, filter):
        if isinstance(filter, Filter):
            copy = Filter()
            copy.where_clauses = set(self.where_clauses).union(filter.get_where_clauses())
            return copy
        else:
            raise Exception, 'Cannot add type %s to a Filter'%(type(filter))


class WhereClause:
    def __init__(self, table, column, comparator, value):
        self.table = table
        self.column = column
        self.comparator = comparator
        self.value = value
    
    def __eq__(self, wc):
        return (self.table==wc.table and 
                self.column==wc.column and
                self.comparator==wc.comparator and
                self.value==wc.value)
        
    def __ne__(self, wc):
        return not self.__eq__(wc)
    
    def __hash__(self):
        return str(self).__hash__()
        
    def __str__(self):
        return '%s.%s %s "%s"'%(self.table, self.column, self.comparator, self.value)
    
    
    
if __name__ == "__main__":
    p.image_table = 'imtbl'
    p.image_id = 'imnum'
    
    f = Filter('A','a','=','1')
    f.add_column('C', 'c', '=', '1')
    print f
    f.add_column('C', 'cc', '=', '3')
    print f
    
    f2 = Filter('A','a','=','1')
    f3 = Filter('B','b','=','1')
    
    g = f + f2
    g = g + f3
    print g
     
    assert WhereClause('a','a','=','1') == WhereClause('a','a','=','1') 
    assert not(WhereClause('a','a','=','1') != WhereClause('a','a','=','1')) 
    assert not(WhereClause('a','a','=','1') == WhereClause('b','a','=','1')) 
    assert WhereClause('a','a','=','1') != WhereClause('b','a','=','1') 
     