from scipy.ndimage import median_filter
import numpy as np
import properties
# Grouping options
from normalizationtool import G_EXPERIMENT, G_PLATE, G_QUADRANT, G_WELL_NEIGHBORS, G_CONSTANT
# Aggregation options
from normalizationtool import  M_MEDIAN, M_MEAN, M_MODE

# Parameter names for do_normalization_step
P_GROUPING = 'grouping'
P_AGG_TYPE = 'aggregate_type'
P_WIN_SIZE = 'win_size'
P_WIN_TYPE = 'win_type'
P_CONSTANT = 'constant'

# Spatial neighbor options (window_type)
W_SQUARE = "Square"
W_LINEAR = "Linear"

p = properties.Properties.getInstance()

def do_normalization_step(input_data, grouping, aggregate_type, win_size, win_type, constant):
    '''Aply a single normalization step
    input_data -- a numpy array of raw data to normalize. This array MUST be in the same
                  shape as your plate data if you are applying a spacially dependent
                  grouping.
    returns a 2-tuple containing an array of normalized values and an array of
       the normalization factors
    '''
    assert input_data.ndim==2 or grouping in (G_CONSTANT, G_EXPERIMENT)
    
    if grouping == G_EXPERIMENT:
        output_data = do_normalization(input_data, aggregate_type)
        
    elif grouping == G_PLATE:
        output_data = do_normalization(input_data, aggregate_type)
    
    elif grouping == G_QUADRANT:
        all_quadrants = [
            # upper left
            (np.arange(input_data.shape[0]) % 2 == 0, np.arange(input_data.shape[1]) % 2 == 0),
            # upper right
            (np.arange(input_data.shape[0]) % 2 == 0, np.arange(input_data.shape[1]) % 2 != 0),
            # lower left
            (np.arange(input_data.shape[0]) % 2 != 0, np.arange(input_data.shape[1]) % 2 == 0),
            # lower right
            (np.arange(input_data.shape[0]) % 2 != 0, np.arange(input_data.shape[1]) % 2 != 0) ]
        output_data = input_data.copy()
        for quad in all_quadrants:
            output_data[quad[0],:][:,quad[1]] = do_normalization(input_data[quad[0],:][:,quad[1]], aggregate_type)
            
    elif grouping == G_WELL_NEIGHBORS:
        if neighbor_type == W_SQUARE:
            output_data = square_filter_normalization(input_data, aggregate_type, win_size)
        elif neighbor_type == W_LINEAR:
            output_data = linear_filter_normalization(input_data, aggregate_type, win_size)
            
    elif grouping == G_CONSTANT:
        output_data = do_normalization(input_data, constant)
    else:
        raise 'Programming Error: Unknown normalization type supplied.'
        
    return output_data, input_data / output_data

def square_filter_normalization(data, aggregate_type, win_size):
    '''
    '''
    # Filter locally, for staining variation
    if aggregate_type  == M_MEDIAN:
        normalization_values = median_filter(data, (win_size, win_size))
    elif aggregate_type  == M_MEAN:
        normalization_values = uniform_filter(data, (win_size, win_size))
    else:
        raise
    
    return data / normalization_values

def linear_filter_normalization(data, aggregate_type, win_size):
    '''
    '''
    # Filter linearly (assumes meandering pattern)
    if aggregate_type  == M_MEDIAN:
        normalization_values = median_filter(data.flatten(), win_size).reshape(data.shape)
    elif aggregate_type  == M_MEAN:
        normalization_values = uniform_filter(data.flatten(), win_size).reshape(data.shape)
    else:
        raise
    
    return data / normalization_values

def do_normalization(data, aggregate_type_or_const):
    '''
    data -- meat and potatoes
    aggregate_type_or_const -- specify an aggregation type or a numeric constant
       to divide by
    '''
    if aggregate_type_or_const == M_MEDIAN:
        val = np.median(data)
    elif aggregate_type_or_const == M_MEAN:
        val = np.mean(data)
    elif aggregate_type_or_const == M_MODE:
        import scipy.ndimage
        # Use histogram function with values a bit removed from saturation
        robust_min = 0.02 * (np.max(data) - np.min(data)) + np.min(data)
        robust_max = 0.98 * (np.max(data) - np.min(data)) + np.min(data)
        nbins = 256
        h = scipy.ndimage.histogram(data.flatten(), robust_min, robust_max, nbins)
        index = np.argmax(h)
        val = np.min(data) + float(index)/float(nbins-1)*(np.max(data) - np.min(data))
    elif type(aggregate_type_or_const) in (float, int, long):
        val = aggregate_type_or_const
    return data/val
