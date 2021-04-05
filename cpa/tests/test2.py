
# Fancy-pants method for getting a where clause that groups adjacent image keys 
# using "BETWEEN X AND Y" ... unfortunately this usually takes far more  
# characters than using "ImageNumber IN (X,Y,Z...)" since we don't run into  
# queries asking for consecutive image numbers very often (except when we do it
# deliberately).  It is also slower than the "IN" method unless the ImageNumbers
# come in a smaller list of consecutive groups.
#
# ...still, this may be very useful since it is notably faster when ImageNumbers
# are consecutive.

def get_where_clause_for_images(keys, is_sorted=False):
    '''
    takes a list of keys and returns a (hopefully) short where clause that
    includes those keys.
    '''
    def in_sequence(k1,k2):
        if len(k1)>1:
            if k1[:-1] != k2[:-1]:
                return False
        return k1[-1]==(k2[-1]-1)
    
    def optimize_for_query(keys, is_sorted=False):
        if not is_sorted:
            keys.sort()
        groups = []
        in_run = False
        for i in range(len(keys)):
            if i == len(keys)-1:
                if in_run:
                    groups[-1] += [keys[i]]
                else:
                    groups += [[keys[i]]]
                break
            if in_run:
                if in_sequence(keys[i], keys[i+1]):
                    continue
                else:
                    groups[-1] += [keys[i]]
                    in_run = False
            else:
                if in_sequence(keys[i], keys[i+1]):
                    in_run = True
                groups += [[keys[i]]]
        return groups

    groups = optimize_for_query(keys)
    wheres = []
    for k in groups:
        if len(k)==1:
            wheres += ['%s=%s'%(col,value) for col, value in zip(object_key_columns(), k[0])]
        else:
            # expect 2 keys: the first and last of a contiguous run
            first, last = k
            if p.table_id:
                wheres += ['(%s=%s AND %s BETWEEN %s and %s)'%
                           (p.table_id, first[0], p.image_id, first[1], last[1])]
            else:
                wheres += ['(%s BETWEEN %s and %s)'%
                           (p.image_id, first[0], last[0])]
    return ' OR '.join(wheres)