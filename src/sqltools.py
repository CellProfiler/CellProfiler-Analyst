from dbconnect import *
from properties import Properties
from utils import Observable
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
    q.add_where_condition(Expression(Column('asdf', 'x'), '<', '100'))
    q.add_where_condition(Expression(Column('asdf', 'y'), '<', '10'), 'OR')
    q.set_group_columns([('per_well', 'gene')])
    '''
    def __init__(self):
        self.select_clause = []
        self.where_clause = Expression()
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
        
    def filter_imkeys(self, imkeys):
        '''imkeys - a list of image keys
        computes a where clause to include only the specified images
        '''
        imkeys.sort()
        if not p.table_id:
            exp_list = [(p.image_table, p.image_id), 'IN', 
                        '(%s)'%(','.join([str(k[0]) for k in imkeys]))]
            if self.where_clause.is_empty:
                self.where_clause.append_expression(*exp_list)
            else:
                self.where_clause.append_expression('AND', *exp_list)                
        else:
            wc = Expression()
            imkeys = np.array(imkeys)
            count = 0
            tnum = 0
            wheres = []
            while count < len(imkeys):
                imnums = imkeys[(imkeys[:,0]==tnum), 1]
                count += len(imnums)
                if len(imnums)>0:
                    exp_list = ['(', (p.image_table, p.table_id), '=', tnum, 
                                'AND', (p.image_table, p.image_id), 'IN', ','.join([str(k) for k in imnums]), ')']
                    if wc.is_empty:
                        wc.append_expression(*exp_list)
                    else:
                        wc.append_expression('OR', *exp_list)
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
        exps = db.get_linking_expressions(tables)
        for exp in exps:
            tables += exp.get_tables()
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
            link_exps = db.get_linking_expressions(queried_tables)
            if link_exps:
                conditions += [' AND '.join([str(exp) for exp in link_exps])]
        return ' AND '.join(conditions)
    
    def add_filter(self, fltr):
        '''Adds a filter to the where clause
        filter -- a Filter or OldFilter object
        '''
        exp_list = []
        if self.where_clause.is_not_empty():
            exp_list += ['AND']
        if isinstance(fltr, Filter):
            exp_list += fltr.get_token_list()
        elif isinstance(fltr, OldFilter):
            exp_list += [str(fltr)]
        else:
            raise 'add_filter requires a Filter or OldFilter object as input'
        self.where_clause.append_expression(*exp_list)


class Column(object):
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
        return (isinstance(col, Column) and 
                self.table == col.table and 
                self.col == col.col and 
                self.agg == col.agg)

    def __ne__(self, col):
        return not self.__eq__(col)
    
    def copy(self):
        return Column(self.table, self.col, self.agg)

    def get_tables(self):
        return [self.table]

            
class Gate1D(object, Observable):
    '''
    A 1D gate associates a particular column with a value range.
    '''
    def __init__(self, column, value_range):
        '''
        column - Column or (table, column) tuple
        value_range - tuple containing (min,max) values for the column
        '''
        if type(column) == tuple:
            self.column = Column(*column)
        elif isinstance(column, Column):
            self.column = column
        else:
            raise 'invalid type (%s) for "column"'%(type(column))
        self.min, self.max = value_range
    
    def __eq__(self, wc):
        return (isinstance(wc, Gate1D) and 
                self.column == wc.column and
                self.min == wc.min and
                self.max == wc.max)
        
    def __ne__(self, wc):
        return not self.__eq__(wc)
    
    def __str__(self):
        return '%s BETWEEN "%s" AND "%s"'%(self.column, self.min, self.max)

    def __hash__(self):
        return hash(str(self))
    
    def copy(self):
        return Gate1D(self.get_column, (self,min, self.max))
    
    def get_table(self):
        return self.column.table
    
    def get_tables(self):
        return [self.column.table]
        
    def get_column(self):
        return self.column.copy()
        
    def get_min(self):
        return self.min
    
    def set_min(self, min):
        self.min = min
        self.notify(None)

    def get_max(self):
        return self.max
    
    def set_max(self, max):
        self.max = max
        self.notify(None)
        
    def get_range(self):
        return (self.min, self.max)

    def set_range(self, min, max):
        self.min = min
        self.max = max
        self.notify(None)
    
    def as_filter(self):
        return Filter(self.column.copy(), '>="%s" AND '%(self.min),
                      self.column.copy(), '<="%s"'%(self.max))
    
    def get_init_params(self):
        '''This is used for encoding and decoding Gate objects.
        Returns a tuple of parameters which can be used to construct this Gate1D
        if passed to __init__.
        eg: g = Gate1D(...)
        Gate1D( g.get_init_params() ) #creates an identical gate to g.
        '''
        return (self.column.table, self.column.col), (self.min, self.max)


class Gate(object, Observable):
    '''
    A list of 1D gates to be ANDed together
    '''
    def __init__(self, gate_list=None):
        '''
        gate_list - a list of Gate1D objects.
        '''
        self._gate_list = gate_list or []
        for subgate in self._gate_list:
            subgate.addobserver(self.notify)
        
    def __str__(self):
        return ' AND '.join(map(str, self._gate_list))
    
    def __hash__(self):
        return hash(str(self))
    
    def get_tables(self):
        return [g.get_table() for g in self._gate_list]
            
    def get_columns(self):
        return [g.get_column() for g in self._gate_list]
    
    def get_subgates(self):
        return self._gate_list
    
    def add_subgate(self, subgate):
        '''subgate -- a Gate1D object'''
        self._gate_list += [subgate]
        # forward notifications from subgates
        subgate.addobserver(self.notify)
        
    def is_empty(self):
        return self._gate_list == []
    
    def as_filter(self):
        if len(self._gate_list) == 0:
            import sqltools
            return sqltools.Filter()
        fltr = self._gate_list[0].as_filter()
        for g in self._gate_list[1:]:
            fltr.and_filter(g.as_filter())
        return fltr
            
    def encode(self):
        '''returns string representation of this gate.
        call Gate.decode with this string representation to get the gate back.
        '''
        return repr([g.get_init_params() for g in self.get_subgates()])
    
    @classmethod
    def decode(cls, gate_encoding):
        '''returns a Gate object from a gate string encoding.
        gate_encoding -- a string generated by gate.encode()
        '''
        init_param_list = eval(gate_encoding)
        return Gate([Gate1D(*params) for params in init_param_list])

class Expression(object):
    def __init__(self, *exp_list):
        '''takes a sequence of string tokens and columns comprising a valid SQL 
        expression when joined into a single string.
        eg:
        >>>col1 = Column('imtbl', 'PosCount', 'AVG')
        >>>col2 = Column('imtbl', 'NegCount', 'AVG')
        >>>exp = Expression([col1, '/ (', col1, '+', col2, ')'
        >>>str(exp)
        "AVG(imtbl.PosCount)/ (AVG(imtbl.PosCount) + AVG(imtbl.NegCount))"
        '''
        self.exp = []
        for exp in exp_list:
            if type(exp) == tuple:
                self.exp += [Column(*exp)]
            else:
                self.exp += [exp]
        
    def __str__(self):
        return ' '.join([str(token) for token in self.exp])

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, exp):
        return isinstance(exp, Expression) and (str(self) == str(exp))
            
    def __ne__(self, exp):
        return not self.__eq__(exp)
        
    def is_empty(self):
        return self.exp == []
    def is_not_empty(self):
        return self.exp != []

    def get_tables(self):
        return [token.table for token in self.exp if isinstance(token, Column)]
    
    def get_columns(self):
        return [token for token in self.exp if isinstance(token, Column)]
    
    def get_token_list(self, columns_as_tuples=False):
        if not columns_as_tuples:
            return list(self.exp)
        else:
            l = []
            for token in self.exp:
                if isinstance(token, Column):
                    l += [(token.table, token.col, token.agg)]
                else:
                    l += [token]
            return l
    
    def append_expression(self, *exp_list):
        self.exp += list(exp_list)


class Filter(Expression):
    '''A Filter is an Expression
    '''
    def and_filter(self, fltr):
        '''appends fltr to this filter with AND
        fltr - a Filter object
        '''
        self.append_filter('AND', fltr)
        
    def or_filter(self, fltr):
        '''appends fltr to this filter with OR
        fltr - a Filter object
        '''
        self.append_filter('OR', fltr)
        
    def append_filter(self, conjunction, fltr):
        '''appends fltr to this filter with the given conjunction
        fltr - a Filter object
        '''
        self.exp += [conjunction] + fltr.get_token_list()
        
##    def get_sub_expressions(self):
##        ''' This is a bit hokey: break this expression up into a list of 
##        expressions of the form: [Expression(col, comparator, value), ...]
##        each of these expressions must be separated by conjunctions (ie: "AND" 
##        or "OR") in this Expression.
##        Note: this will break if value is a conjunction 
##        returns None if the expression can't be broken down this way.
##        '''
##        l = [[]]
##        for exp in self.get_token_list():
##            if type(l) == str and l.strip().upper() in ['AND', 'OR']:
##                l += [[]]
##                if len(l[-1]) != 3:
##                    return None
##            else:
##                l[-1] += [exp]
##        if len(l[-1]) != 3:
##            return None
##        return [Expression(*ll) for ll in l]
##    
##    def get_conjunctions(self):
##        ''' Return a list of the conjunctions that are used in this expression
##        '''
##        return [t.strip() for t in self.get_token_list() 
##                if type(t)==str and t.strip().upper() in ['AND', 'OR']]
    
    def encode(self):
        '''returns string representation of this filter.
        call Filter.decode with this string representation to get the filter back.
        '''
        return repr(self.get_token_list(columns_as_tuples=True))
    
    @classmethod
    def decode(cls, filter_encoding):
        '''returns a Filter object from a filter string encoding.
        filter_encoding -- a string generated by filter.encode()
        '''
        init_param_list = eval(filter_encoding)
        return Filter(*init_param_list)


class OldFilter(object):
    '''Wrapper class for backwards compatibility with the old style of defining
    filters. 
    '''
    def __init__(self, filter_name, filter_query):
        fq = filter_query
        self.query = filter_query
        parseable = re.match('^SELECT\s+(?P<select>.+)\s+'
                             'FROM\s+(?P<from>.+)\s+'
                             '(WHERE\s+(?P<where>.+)\s+)?'
                             '(GROUP BY\s+(?P<group>.+))?', 
                             fq, re.IGNORECASE) is not None
        self.where_clause = re.search('\sWHERE\s(?P<wc>.*)', fq, re.IGNORECASE).groups()[0]
        self.from_clause = re.search('\sFROM\s(?P<wc>.*)\sWHERE', fq, re.IGNORECASE).groups()[0]    
        self.tables = [t.strip() for t in self.from_clause.split(',')]
        for t in self.tables:
            if ' ' in t:
                import wx
                wx.MessageBox('Unable to parse properties filter "%s" because '
                              'it appears to use table aliases. Please remove '
                              'aliases and try again.\n\tQuery was: "%s".'%(filter_name, fq), 'Error')
        if not parseable:
            import wx
            wx.MessageBox('Unable to parse properties filter query.\n\t"%s".'%(fq), 'Error')
    
    def __str__(self):
        return self.where_clause
    
    def get_tables(self):
        return self.tables
    
    def get_columns(self):
        raise Exception('OldFilter does not support get_columns interface.')

    
def parse_old_group_query(group_query):
    '''
    '''
    gq = group_query
    match = re.match('^SELECT\s+(?P<select>.+)\s+FROM\s+(?P<from>.+)\s*$', 
                     gq, re.IGNORECASE)
    if match == None:
        import wx
        wx.MessageBox('Unable to parse properties group query:\n\t"%s".'%(gq), 'Error')
    col_strings = [t.strip() for t in match.groupdict('select').split(',')]
    tables = set([t.strip() for t in match.groupdict('from').split(',')])

    columns = []
    for col_string in col_strings:
        tablecol = col_string.split('.')
        if len(tablecol) == 1 and len(tables) == 1:
            columns += [Column(tables[0], tablecol[0])]
        elif len(tablecol) == 2 and tablecol[0] in tables:
            columns += [Column(tablecol[0], tablecol[1])]
        else:
            import wx
            wx.MessageBox('Unable to parse properties group query:\n\t"%s".'%(gq), 'Error')
            


if __name__ == "__main__":
    import wx
    app = wx.PySimpleApp()
    p.LoadFile('/Users/afraser/cpa_example/example.properties')

    app.MainLoop()