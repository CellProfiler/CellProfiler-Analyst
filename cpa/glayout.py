'''glayout - a module to perform a layer layout of a NetworkX directed graph

'''

import numpy as np
import networkx as nx

def layer_layout(g, level_attribute = "t"):
    '''Lay out a directed graph by layer
    
    g - a NetworkX directed graph with the layer defined as the node's "t"
        attribute. The graph must be acyclic - a restriction that's guaranteed
        by TrackObjects since edges are always going forward in time.
        
    level_attribute - the attribute in the node attribute dictionary that
        specifies the level of the node
        
    on exit, each node will have a y attribute that can be used to place
    the node vertically on a display. "t" can be used for the horizontal
    display.
    
    The algorithm is a partial implementation of 
    Sugiyama, Kozo, Tagawa, Shojiro; Toda, Mitsuhiko (1981), 
    "Methods for visual understanding of hierarchical system structures", 
    IEEE Transactions on Systems, Man, and Cybernetics SMC-11 (2):109-125,
    doi:10.1109/TSMC.1981.4308636
	
    as described by sydney.edu.au/engineering/it/~visual/comp4048/slides03.ppt
    '''
    
    subgraphs = nx.weakly_connected_component_subgraphs(g)
    y = 0
    for subgraph in subgraphs:
        y = layer_layout_subgraph(g, subgraph, y, level_attribute)
        
def layer_layout_subgraph(g, sg, y0, level_attribute):
    '''Lay out a connected subgraph
    
    g - the graph
    
    sg - the subgraph
    
    y0 - the y offset for each node
    
    level_attribute - the attribute in the node dictionary that gives the level
    
    returns the height of the graph
    '''
    nodes = sg.nodes(data=True)
    t = np.array([float(x[1][level_attribute]) for x in nodes])
    idx = np.array([x[0] for x in nodes])
    #
    # The format for edges is an N x 2 array
    # with index 0 being the source and 1 the destination
    #
    edges = np.array(sg.out_edges())
    if len(edges) == 0:
        # Can happen if there is only 1 node
        for node, data in nodes:
            g.add_node(node, y = y0)
        return y0 + 1
    #
    # Map the values in idx to the range from 0 to len(idx)
    #
    real_vertex_end = len(idx)
    mapping = np.zeros(np.max(idx)+1, int)
    mapping[idx] = np.arange(real_vertex_end)
    #
    # Map the t values to an ordering.
    #
    t_unique, t_order = np.unique(t, return_inverse=True)
    #
    # Convert the edge coordinates to the mapping
    #
    edges = mapping[edges]
    #
    # Make dummy vertices
    #
    edges, t_order = make_dummies(edges, t_order)
    #
    # Sort the edges so that we can index them by destination vertex
    #
    order = np.lexsort([edges[:, 0], edges[:, 1]])
    edges = edges[order]
    bin_edge_counts = np.bincount(edges[:, 1])
    edge_counts = np.zeros(t_order.shape[0], int)
    edge_counts[:len(bin_edge_counts)] = bin_edge_counts
    first_edges = np.hstack([[0], np.cumsum(edge_counts)])
    #
    # Process the vertices in increasing t_order
    #
    v_order = np.lexsort([t_order])
    #
    # Find the first index in v_order for each value of t_order
    #
    v_count = np.bincount(t_order)
    v_first = np.hstack(([0], np.cumsum(v_count)))
    #
    # height holds the heights of the vertices - the units are arbitrary.
    #
    height = np.zeros(len(v_order), float)
    #
    # ave_height holds the mean of the source node heights. This acts
    # as the first tiebreaker if the medians are the same.
    #
    ave_height = np.zeros(len(v_order), float)
    #
    # We space the leftmost ones evenly. Pragmatically, we're dealing with
    # a time series of dividing cells, so this is likely to be a tree and
    # there is likely only a single node on the left
    #
    height[v_order[:v_count[0]]] = np.arange(v_count[0])
    #
    # We maintain "eps" = a distance that is less than 1/2 of that between
    # the closest neighbors at the current level.
    #
    max_height = v_count[0] - 1
    for i in range(1, len(v_count)):
        last_heights = height[v_order[v_first[i-1]:v_first[i]]]
        last_heights.sort()
        if len(last_heights) > 1:
            eps = np.min(last_heights[1:] - last_heights[:-1]) / 3.0
        else:
            eps = 1
        v_level = v_order[v_first[i]:v_first[i+1]]
        for v in v_level:
            # The source edges for this vertex
            v_src = edges[first_edges[v]:first_edges[v+1], 0]
            if len(v_src) == 0:
                height[v] = max_height = max_height+1
            else:
                height[v] = np.median(height[v_src])
                ave_height[v] = np.mean(height[v_src])
        #
        # Here, we have to find and separate any vertices at the same height.
        #
        level_order = np.lexsort((v_level, ave_height[v_level], height[v_level]))
        v_level = v_level[level_order]
        u_height, v_level_first = np.unique(height[v_level], return_index = True)
        v_level_first = np.hstack([v_level_first, [len(v_level)]])
        #
        # v_level_count is the # of vertices with height = u_height
        #
        v_level_count = v_level_first[1: ] - v_level_first[:-1]
        #
        # only disambiguate if more than one at same height
        #
        if np.any(v_level_count > 1):
            v_level = np.delete(v_level, v_level_first[v_level_count == 1])
            #
            # Use "unique" to get new indexes to firsts and reverse
            #
            u_height, v_level_first, v_level_reverse = \
                np.unique(height[v_level], 
                          return_index = True,
                          return_inverse = True)
            v_level_first = np.hstack([v_level_first, [len(v_level)]])
            v_level_count = v_level_first[1: ] - v_level_first[:-1]
            #
            # The within-group index is the # of steps we are from the
            # first. That's arange - our first's arange #
            #
            v_level_idx = np.arange(len(v_level)) -\
                v_level_first[v_level_reverse]
            #
            # our delta is (2 * eps / count) - eps which spreads things between
            # -eps and eps
            #
            delta = (2 * eps * v_level_idx / 
                     (v_level_count[v_level_reverse] - 1)) - eps
            height[v_level] = height[v_level] + delta
    #
    # Now convert the heights into integral values
    #
    u_height, i_height = np.unique(height, return_inverse=True)
    #
    # Remember to add the offsets
    #
    i_height = i_height + y0
    y_max = np.max(i_height) + 1
    #
    # Plaster the heights back into the good vertices
    #
    for (node_num, d), node_height in zip(nodes, i_height[:real_vertex_end]):
        g.add_node(node_num, y = node_height)
    return y_max
    
def make_dummies(edges, t_order):
    '''Create edges to dummy vertices for all edges > 1 apart
    
    edges - an Nx2 matrix of edges
    
    t_order - the level metric for each vertex
    
    returns an augmented edge matrix and t_order augmented with the ordering 
            metric of each dummy vertex
            
    Note that this calculation is much simpler than Sugiyama because we
    are given the layering and don't have to optimize for it.
    '''
    real_vertex_end = len(t_order)
    #
    # Make the dummy vertices. We need one dummy vertex for each distance > 1
    #
    distances = t_order[edges[:, 1]] - t_order[edges[:, 0]]
    assert np.all(distances >= 0), "Edges must always connect forward"
    n_dummies = distances - 1
    edges_needing_dummies = edges[n_dummies > 0]
    n_dummies = n_dummies[n_dummies > 0]
    n_dummy_vertices = np.sum(n_dummies)
    if n_dummy_vertices == 0:
        return edges, t_order
    
    dummy_vertices = np.arange(real_vertex_end, 
                               real_vertex_end + n_dummy_vertices)
    #
    # We need an edge from the real start to the first dummy, an edge
    # between dummies for distances > 2 and an edge between the last dummy
    # and the real end. That's n_dummies + 1 edges
    #
    n_dummy_edges = n_dummy_vertices + len(n_dummies)
    dummy_edges = -np.ones((n_dummy_edges, 2), int)
    #
    # "first" is the index of the edge from the real vertex to the first dummy
    #
    first = np.hstack([[0], np.cumsum(n_dummies+1)])
    #
    # "last" is the index of the edge from the last dummy to the first real
    # vertex.
    #
    last = first[1:] - 1
    first = first[:-1]
    #
    # Fill in the source edges
    #
    dummy_edges[first, 0] = edges_needing_dummies[:, 0]
    #
    # Fill in the destination edges
    #
    dummy_edges[last, 1] = edges_needing_dummies[:, 1]
    #
    # There should be as many blank dummy edges as there are dummy vertices
    #
    for i in (0, 1):
        dummy_edges[dummy_edges[:, i] == -1, i] = dummy_vertices
    #
    # find the t_order for each of the dummy vertices
    # 
    t_order_augmented = np.ones(n_dummy_vertices, int)
    if len(n_dummies) > 1:
        #
        # get the increment to add to the t_order of the start
        #
        increment = np.ones(len(dummy_vertices), int)
        first = np.hstack([[0], np.cumsum(n_dummies[:-1])])
        increment[first[1:]] = first[:-1] - first[1:] + 1
        increment = np.cumsum(increment)
        #
        # Get a pointer to edges_needing_dummies for each dummy_vertex
        #
        reverse_index = np.zeros(len(dummy_vertices), int)
        reverse_index[first[1:]] = 1
        reverse_index = np.cumsum(reverse_index)
        #
        # The augmented order is the increment plus t_order of the leading edge
        #
        t_order_augmented = increment + \
            t_order[edges_needing_dummies[reverse_index, 0]]
    return np.vstack((edges, dummy_edges)), \
           np.hstack((t_order, t_order_augmented))
           
if __name__=="__main__":
    #
    # Read a CellProfiler relationships .csv and display using matplotlib.
    #
    import csv
    import sys
    import wx
    
    import matplotlib
    matplotlib.use("WXAgg")
    from matplotlib.backends.backend_wxagg import FigureFrameWxAgg
    
    K_ALL = \
        [ "Module", "Module Number", "Relationship",
          "First Object Name", "First Image Number", "First Object Number",
          "Second Object Name", "Second Image Number", "Second Object Number" ]
    
    K_MODULE, K_MODULE_NUMBER, K_RELATIONSHIP, \
        K_FIRST_OBJECT_NAME, K_FIRST_IMAGE_NUMBER, K_FIRST_OBJECT_NUMBER, \
        K_SECOND_OBJECT_NAME, K_SECOND_IMAGE_NUMBER, K_SECOND_OBJECT_NUMBER = \
        K_ALL 
    
    g = nx.DiGraph()
    
    vertex_idx = 0
    vertex_dict = {}
    def vertex(image_number, object_number):
        global vertex_idx, vertex_dict, g
        k = (image_number, object_number)
        node_num = vertex_dict.get(k, vertex_idx)
        if node_num == vertex_idx:
            d = dict(image_number = image_number, 
                     object_number = object_number)
            g.add_node(node_num, d)
            vertex_dict[k] = node_num
            vertex_idx += 1
        return node_num
    
    if len(sys.argv) > 1:
        fd = open(sys.argv[1], "rb")
        rdr = csv.reader(fd)
        header = rdr.next()
        i_image_number1 = i_image_number2 = i_object_number1 = i_object_number2 = None
        for i, key in enumerate(header):
            if key == K_FIRST_IMAGE_NUMBER:
                i_image_number1 = i
            elif key == K_SECOND_IMAGE_NUMBER:
                i_image_number2 = i
            elif key == K_FIRST_OBJECT_NUMBER:
                i_object_number1 = i
            elif key == K_SECOND_OBJECT_NUMBER:
                i_object_number2 = i
        for row in rdr:
            image_number1 = row[i_image_number1]
            object_number1 = row[i_object_number1]
            image_number2 = row[i_image_number2]
            object_number2 = row[i_object_number2]
            v1 = vertex(image_number1, object_number1)
            v2 = vertex(image_number2, object_number2)
            g.add_edge(v1, v2)
    else:
        np.random.seed(1)
        def objnum(image_number, object_numbers = {}):
            result = object_numbers.get(image_number, 1)
            object_numbers[image_number] = result + 1
            return result
        
        # bug # 1 test - detached vertex
        vertex(50, objnum(50))
        
        cells = [ (1, objnum(1)) for _ in range(4)]
        while len(cells) > 0:
            image_number1, object_number1 = cells.pop(0)
            v1 = vertex(image_number1, object_number1)
            fate = np.random.uniform()
            if fate < .2 and image_number1 > 1:
                pass #death
            elif fate < .7:
                # split
                for i in range(2):
                    if image_number1 >= 95:
                        image_number2 = 100
                    else:
                        image_number2 = np.random.randint(image_number1 + 5, 100)
                    object_number2 = objnum(image_number2)
                    image_number1a = image_number1 + 1
                    object_number1a = objnum(image_number1a)
                    v1a = vertex(image_number1a, object_number1a)
                    g.add_edge(v1, v1a)
                    v2 = vertex(image_number2, object_number2)
                    g.add_edge(v1a, v2)
                    if image_number2 < 93:
                        cells.append((image_number2, object_number2))
                    elif image_number2 < 100:
                        v3 = vertex(100, objnum(100))
                        g.add_edge(v2, v3)
            else:
                # merge
                if image_number1 >= 93:
                    image_number2 = 100
                else:
                    image_number2 = np.random.randint(image_number1 + 7, 100)
                object_number3 = objnum(image_number2)
                v3 = vertex(image_number2, object_number3)
                image_number1a = image_number1 + 1
                image_number2a = image_number2-1
                for i in range(2):
                    object_number2 = objnum(image_number2a)
                    object_number1a = objnum(image_number1a)
                    v1a = vertex(image_number1a, object_number1a)
                    g.add_edge(v1, v1a)
                    v2 = vertex(image_number2a, object_number2)
                    g.add_edge(v1a, v2)
                    g.add_edge(v2, v3)
                if image_number2 < 93:
                    cells.append((image_number2, object_number3))
                elif image_number2 < 100:
                    g.add_edge(v3, vertex(100, objnum(100)))
                
    layer_layout(g, level_attribute = "image_number")

    app = wx.PySimpleApp(True)
    figure = matplotlib.figure.Figure()
    frame = FigureFrameWxAgg(1, figure)
    ax = figure.add_subplot(1,1,1)
    assert isinstance(ax, matplotlib.axes.Axes)

    x = np.zeros(vertex_idx)
    y = np.zeros(vertex_idx)
    for node, d in g.nodes_iter(data=True):
        x[node] = d["image_number"]
        y[node] = d["y"]
        
    ax.plot(x, y, linestyle="None", marker="o")
    ax.set_xlim(np.min(x) - 1, np.max(x)+1)
    ax.set_ylim(np.min(y) - 1, np.max(y)+1)
    
    for u, v in g.edges_iter():
        uv = np.array([u, v])
        ax.plot(x[uv], y[uv], color="black", linestyle="-", marker="None")
    def on_close(event):
        app.ExitMainLoop()
    frame.Bind(wx.EVT_CLOSE, on_close)
    frame.Show()
    app.MainLoop()
    