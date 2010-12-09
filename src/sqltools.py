from dbconnect import *
from properties import Properties

p = Properties.getInstance()


class QueryBuilder(object):
    '''
    A class for building query strings.
    This class will auto-generate your from clause and link tables in the
    where clause.
    q = Query()
    q.set_select_clause([Column(p.image_table, p.image_id), 
                         Column('per_well', 'gene'), 
                         Column('per_object', 'intensity', 'AVG')])
    q.add_where_condition(('asdf', 'x'), '<', '100')
    q.add_where_condition(('asdf', 'y'), '<', '10', 'OR')
    q.set_group_columns([('per_well', 'gene')])
    '''
    def __init__(self):
        self.select_clause = []
        self.where_clause = WhereClause()
        self.group_cols = []
        self.other_tables = []
        
    def __str__(self):
        select_clause = self.get_select_clause_string()
        from_clause = self.get_from_clause()
        where_clause = self.get_where_clause()
        if where_clause:
            where_clause = '\n\tWHERE '+where_clause
        group_clause = ''
        if self.group_cols != []:
            group_clause = '\n\tGROUP BY ' + ', '.join([str(col) for col in self.group_cols])
            
        return 'SELECT %s \n\tFROM %s %s %s'%(select_clause, from_clause, 
                                          where_clause, group_clause)
        
    def set_select_clause(self, sel_list):
        '''sel_list - a list of Expressions and/or Columns.        
        eg: 
        >>> col = Column('t','a','AVG')
        >>> qb.set_select_clause([col, Expression([col, '/', col])
        >>> qb.get_select_clause_string()
        "AVG(t.a), AVG(t.a)/AVG(t.a)"
        '''
        self.select_clause = sel_list
        
    def get_select_clause_string(self):
        '''returns the select clause as a string
        '''
        return ', '.join([str(t) for t in self.select_clause])
            
    def add_table_dependencies(self, tables):
        '''tables - a list of table names to add to the from clause
        '''
        self.other_tables = tables
        
    def add_where_condition(self, column, comparator, value, conjunction='AND'):
        '''
        column - a tuple of the form (table, col) or (table, col, agg)
        comparator - an SQL comparator string
        value - a string or a column tuple
        '''
        self.where_clause.add_condition(column, comparator, value, conjunction)
        
    def filter_imkeys(self, imkeys):
        '''imkeys - a list of image keys
        computes a where clause to include only the specified images
        '''
        imkeys.sort()
        if not p.table_id:
            self.where_clause.add_condition((p.image_table, p.image_id), 'IN', 
                                '(%s)'%(','.join([str(k[0]) for k in imkeys])))
        else:
            wc = WhereClause()
            imkeys = np.array(imkeys)
            count = 0
            tnum = 0
            wheres = []
            while count < len(imkeys):
                imnums = imkeys[(imkeys[:,0]==tnum), 1]
                count += len(imnums)
                if len(imnums)>0:
                    wc.add_condition((p.image_table, p.table_id),'=', tnum, 'OR')
                    wc.add_condition((p.image_table, p.image_id), 'IN', 
                                     ','.join([str(k) for k in imnums]))
                tnum += 1
            self.where_clause.add_where_clause(wc)

    def set_group_columns(self, cols):
        '''cols - a list of either Columns or column tuples: (table, col, [agg])
        '''
        self.group_cols = []
        for col in cols:
            if isinstance(col, Column):
                self.group_cols += [col]
            elif isinstance(col, tuple):
                self.group_cols += [Column(*col)]
            else:
                raise 'Invalid parameter type'
        
    def get_queried_tables(self):
        '''returns all tables referenced in the "select", "where", and 
        "group by" clauses.
        '''
        tables = self.other_tables
        # add the tables from the select clause
        for exp in self.select_clause:
            tables += exp.get_tables()
        # add the tables from the where clause
        tables += self.where_clause.get_tables()
        # add the tables from the group columns
        tables += [col.table for col in self.group_cols]
        return list(set(tables))
        
    def get_tables(self):
        '''returns all tables required in the from clause for this query.
        '''
        tables = self.get_queried_tables()
        # add the tables required to link the above tables together
        db = DBConnect.getInstance()
        conditions = db.get_linking_conditions(tables)
        for c in conditions:
            tables += c.get_tables()
        return list(set(tables))
    
    def get_from_clause(self):
        return ', '.join(self.get_tables())
    
    def get_where_clause(self):
        '''Build the where clause from conditions given by the user and 
        conditions that link all the tables together.
        '''
        db = DBConnect.getInstance()
        conditions = []
        if self.where_clause.is_not_empty():
            conditions += [str(self.where_clause)]
        queried_tables = self.get_queried_tables()
        if len(queried_tables) > 1:
            link_conditions = db.get_linking_conditions(queried_tables)
            if link_conditions:
                conditions += [' AND '.join([str(c) for c in link_conditions])]
        return ' AND '.join(conditions)


class Column:
    def __init__(self, table, col, agg=None):
        '''table - the table name
        col - the column name
        agg - (optional) SQL aggregation function to use (eg: "AVG", "STD", etc)
        '''
        self.table = table
        self.col = col
        self.agg = agg
        
    def __str__(self):
        if self.agg:
            return '%s(%s.%s)'%(self.agg.upper(), self.table, self.col)
        else:
            return '%s.%s'%(self.table, self.col)
        
    def __hash__(self):
        return hash(str(self))
    
    def __eq__(self, col):
        return (self.table == col.table and 
                self.col == col.col and 
                self.agg == col.agg)
            
    def __ne__(self, col):
        return not self.__eq__(col)
    
    def get_tables(self):
        return [self.table]

    
## {{{ http://code.activestate.com/recipes/511480/ (r1)
def interleave(*args):
    for idx in range(0, max(len(arg) for arg in args)):
        for arg in args:
            try:
                yield arg[idx]
            except IndexError:
                continue
## end of http://code.activestate.com/recipes/511480/ }}}


class Expression(object):
    def __init__(exp_list):
        '''exp_list -- a list of string tokens and columns comprising a valid 
                       SQL expression when joined into a single string.
           eg:
           >>>col1 = Column('imtbl', 'PosCount', 'AVG')
           >>>col2 = Column('imtbl', 'NegCount', 'AVG')
           >>>exp = Expression([col1, '/ (', col1, '+', col2, ')'
           >>>str(exp)
           "AVG(imtbl.PosCount)/ (AVG(imtbl.PosCount) + AVG(imtbl.NegCount))"
        '''
        self.exp = exp_list
        
    def __str__(self):
        return ''.join([str(token) for token in self.exp])

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, exp):
        return isinstance(exp, Expression) and (str(self) == str(exp))
            
    def __ne__(self, exp):
        return not self.__eq__(exp)

    def get_tables(self):
        return [token.table for token in self.exp if isinstance(token, Column)]

    
class WhereClause(object):
    '''
    A WhereClause is a list of WhereConditions strung together by conjunctions
    "AND" or "OR"
    '''
    def __init__(self, column=None, comparator=None, value=None):
        '''
        column - Column or (table, column) tuple
        comparator - SQL comparator string
        value - Column or (table, column) tuple
        '''
        self.conditions = []
        self.conjunctions = []
        if None not in [column, comparator, value]:
            self.conditions = [WhereCondition(column, comparator, value)]
        elif not column == comparator == value == None:
            raise Exception, 'All Filter fields are required.'
    
    def __str__(self):
        return ' '.join(map(str, interleave(self.conditions, self.conjunctions)))
    
    def is_empty(self):
        return self.conditions == []
    def is_not_empty(self):
        return not self.is_empty()

    def get_tables(self):
        tables = []
        for c in self.conditions:
            tables += c.get_tables()
        return list(set(tables))
    
    def add_condition(self, column, comparator, value, conjunction='AND'):
        if not self.is_empty():
            self.conjunctions += [conjunction]
        self.conditions += [WhereCondition(column, comparator, value)]
        assert len(self.conjunctions) == len(self.conditions) - 1
        
    def add_where_clause(self, where, conjunction='AND'):
        if not (self.is_empty() or where.is_empty()):
            self.conjunctions += [conjunction]
        self.conditions += where.conditions
        self.conjunctions += where.conjunctions
        assert len(self.conjunctions) == len(self.conditions) - 1
        
    def add_filter(self, filter, conjunction='AND'):
        if not (self.is_empty() or filter.is_empty()):
            self.conjunctions += [conjunction]
        self.conditions += filter.conditions
        self.conjunctions += filter.conjunctions
        assert len(self.conjunctions) == len(self.conditions) - 1

        
class Filter(WhereClause):
    '''
    A Filter is basically a WhereClause with a different string representation
    '''
    def __str__(self):
        if self.is_empty():
            raise 'Filter has no where clause'
        tables = super(Filter, self).get_tables()
        where = super(Filter, self).__str__()
        # currently expect table to be the per image table
        return 'SELECT %s FROM %s WHERE %s'%(UniqueImageClause(p.image_table), 
                                             ', '.join(tables), where)

    
class WhereCondition:
    '''
    Conditional statement in the form of "Column <comparator> value/Column"
    '''
    def __init__(self, column, comparator, value):
        '''
        column - Column or (table, column) tuple
        value - Column or (table, col) tuple
        '''
        if type(column) == tuple:
            self.column = Column(*column)
        elif isinstance(column, Column):
            self.column = column
        else:
            raise 'invalid type (%s) for "column"'%(type(column))
        self.comparator = comparator
        if type(value) == tuple:
            self.value = Column(*value)
        else:
            self.value = value
    
    def __eq__(self, wc):
        return (self.column==wc.column and
                self.comparator==wc.comparator and
                self.value==wc.value)
        
    def __ne__(self, wc):
        return not self.__eq__(wc)
    
    def __str__(self):
        return '%s %s %s'%(self.column, self.comparator, self.value)

    def __hash__(self):
        return hash(str(self))
    
    def get_tables(self):
        tables = [self.column.table]
        if isinstance(self.value, Column):
            tables += [self.value.table]
        return list(set(tables))                
    
    
if __name__ == "__main__":
    import wx
    app = wx.PySimpleApp()
    p.LoadFile('/Users/afraser/cpa_example/example.properties')

    q = QueryBuilder()
    q.set_select_clause([Column('per_image', 'ImageNumber'), 
                         Column('per_well', 'gene'), 
                         Column('per_object', 'intensity', 'AVG')])
    q.add_where_condition(('asdf', 'x'), '<', '100')
    q.add_where_condition(('asdf', 'y'), '<', '10', 'OR')
    q.set_group_columns([('per_well', 'gene')])
    print q

    
    f = Filter(('A', 'a'), '=', '1')
    print f
    f.add_condition(('C', 'c'), '=', '1')
    print f
    f.add_condition(('C', 'cc'), '=', '3')
    print f
    
    f.add_filter(Filter(('A','a'),'=','1'), 'OR')
    f.add_filter(Filter(('B','b'),'=','1'), 'OR')
    print f
     
    assert str(WhereCondition(('T', 'a'), '<=', ('TT', 'b'))) == 'T.a <= TT.b'
    assert WhereCondition(('a','a'),'=','1') == WhereCondition(('a','a'),'=','1') 
    assert not(WhereCondition(('a','a'),'=','1') != WhereCondition(('a','a'),'=','1')) 
    assert not(WhereCondition(('a','a'),'=','1') == WhereCondition(('b','a'),'=','1')) 
    assert WhereCondition(('a','a'),'=','1') != WhereCondition(('b','a'),'=','1') 
     
    app.MainLoop()