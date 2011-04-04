from scipy.ndimage import median_filter
import numpy as np

# Normalization options
N_EXPERIMENT = "Experiment"
N_PLATE = "Plate"
N_QUADRANT = "Quadrant"
N_WELL_NEIGHBORS = "Well neighbors"
N_CONSTANT = "Constant"

# Spatial neighbor options
W_SQUARE = "Square"
W_LINEAR = "Linear"

# Aggregation options
M_MEDIAN = "Median"
M_MEAN = "Mean"
M_MODE = "Mode"

p = Properties.getInstance()

# Other constants
IMKEY_COLUMN_INDEX = 0 if not p.table_id else 1
PLATE_COLUMN_INDEX = IMKEY_COLUMN_INDEX + 1
WELL_COLUMN_INDEX = PLATE_COLUMN_INDEX + 1
KEY_INDEX_OFFSET = WELL_COLUMN_INDEX + 1

def get_normalization_option(self):
    '''Returns normalization options that the user selected'''
    return normalization_option

def get_aggregate_function(self):
    '''Returns filter settings that the user selected'''
    return aggregate_function

def get_filter_parameters(self):
    '''Returns filter settings that the user selected'''
    return filter_type, filter_size

def get_selected_measurement_columns(self):
    '''Returns the list of measurement columns that the user selected'''
    return selected_columns

def get_all_normalization_steps(self):    
    '''Returns list of selected normalization steps'''
    return all_normalization_steps

def get_measurements_from_columns(self):
    '''Construct query and obtain measurements'''
    query = "SELECT %s,"%("ImageNumber" if not p.table_id else "TableNumber, ImageNumber")
    if p.plate_id:
        query += ", %s, %s "%(p.plate_id, p.well_id)
    query += ",".join([measurement_column for measurement_column in self.get_selected_measurement_columns()])
    query += " FROM %s"%p.image_table
    if p.plate_id:
        query += " ORDER BY %s, %s ASC"%(p.plate_id, p.well_id)
    cursor.execute(query)
    return np.array(cursor.fetchall())

def do_all_normalization_steps(self, measurement_column):
    ''' For each column of measurements, perform all the specified normalization steps'''
    # Get the data from the db
    input_data = self.get_measurements_from_columns()
    # Initialize the normalization values to an array of NaNs, same size as data (minus the keys)
    shape = input_data.shape if p.plate_id else [input_data.shape[0], input_data.shape[1]-KEY_INDEX_OFFSET]
    normalization_values = np.ones(shape)*np.NaN
    
    # Normalize each measurement column
    for index, measurement_column in enumerate(self.get_selected_measurement_columns()):
        # Create an index for the actual data for each column, plus keys (if any)
        if p.plate_id:
            # Reference the cols for the keys ([TableNum,ImageNum], Plate, Well) plus the data col
            idx = list(np.arange(KEY_INDEX_OFFSET)) + [KEY_INDEX_OFFSET + index]
        else:
            # Otherwise, just reference the data column itself
            idx = [index]
        
        # Apply all the requested nornalization steps for each column
        # First, arrange the data appropriately
        if not p.plate_id: # No plate layout: Keep data as-is
            data = input_data[:,np.ix_(idx)]
            norm_values = normalization_values[:,index]
        else:
            from plateviewer import FormatPlateMapData # Plate layour exists: Format accordingly
            # Format the data
            keys_and_vals = [input_data[i,idx][0] for i in range(input_data.shape[0])]
            data, well_keys = FormatPlateMapData(keys_and_vals)
            # Format the normalization vals
            keys_and_vals = [normalization_values[i,idx][0] for i in range(normalization_values.shape[0])]
            norm_values, well_keys = FormatPlateMapData(keys_and_vals)
        
        for normalization_step in self.get_all_normalization_steps():
            normalization_type = self.get_normalization_option()
            data, norm_values = self.do_normalization_step(data, norm_values, normalization_type)
            
        norm_values /= np.min(norm_values)
        # TODO: Re-arrange the data back the way it was for the final normalization
        input_data /= norm_values

def do_normalization_step(self, input_data, normalization_values, normalization_type):
    '''Aply a single normalization step'''
    
    aggregate_type = self.get_aggregate_function()
    if normalization_type == N_EXPERIMENT:
        plate_data, normalization_values = self.do_normalization(plate_data, normalization_values, aggregate_type)
    elif normalization_type == N_PLATE:
        all_plates = set(input_data[:,PLATE_COLUMN_INDEX])
        for plate in all_plates:
            index = plate_data[:,PLATE_COLUMN_INDEX] == plate
            output_data, output_norms = self.do_normalization(plate_data[index],
                                                              normalization_values[index],
                                                              normalization_type,
                                                              aggregate_type)
            plate_data[index] = output_data
            normalization_values[index] = output_norms
        
    elif normalization_type == N_QUADRANT:
        all_quadrants = [
            # upper left
            (np.arange(plate_data.shape[0]) % 2 == 0, np.arange(plate_data.shape[1]) % 2 == 0),
            # upper right
            (np.arange(plate_data.shape[0]) % 2 == 0, np.arange(plate_data.shape[1]) % 2 != 0),
            # lower left
            (np.arange(plate_data.shape[0]) % 2 != 0, np.arange(plate_data.shape[1]) % 2 == 0),
            # lower right
            (np.arange(plate_data.shape[0]) % 2 != 0, np.arange(plate_data.shape[1]) % 2 != 0) ]
        for quadrant in all_quadrants:
            output_data, output_norms = self.do_normalization(plate_data[quadrant[0],:][:,quadrant[1]], 
                                                              normalization_values[quadrant[0],:][:,quadrant[1]], 
                                                              normalization_type, aggregate_type)
            plate_data[quadrant[0],:][:,quadrant[1]] = output_data
            normalization_values[quadrant[0],:][:,quadrant[1]] = output_norms
            
    elif normalization_type == N_WELL_NEIGHBORS:
        if neighbor_type == W_SQUARE:
            plate_data, normalization_values = self.square_filter_normalization(plate_data, normalization_values, 
                                                                                normalization_type, aggregate_type)
        elif neighbor_type == W_LINEAR:
            plate_data, normalization_values = self.linear_filter_normalization(plate_data, normalization_values, 
                                                                                normalization_type, aggregate_type)
    elif normalization_type == N_CONSTANT:
        input_data, normalization_values = self.do_normalization(input_data, normalization_values, 
                                                                normalization_type, aggregate_type)
    if not p.plate_id: # No plate layout: Keep data as-is
        output_data = plate_data
    else:
        output_data # Rearrange plate_data and normalization values
        normalization_values
        
    return output_data, normalization_values

def square_filter_normalization(self, data, normalization_values):
    
    filter_type, filter_size = self.get_filter_parameters()
    
    # Filter locally, for staining variation
    if self.get_aggregate_function()  == M_MEDIAN:
        normalization_values = median_filter(data, filter_size)
    elif self.get_aggregate_function()  == M_MEAN:
        normalization_values = uniform_filter(data, filter_size)
    
    # Return the result
    return ata/normalization_values, normalization_values

def linear_filter_normalization(self, data, normalization_values):
    
    filter_type, filter_size = self.get_filter_parameters()
    
    # Filter linearly (assumes meandering pattern)
    if self.get_aggregate_function()  == M_MEDIAN:
        normalization_values = median_filter(data.flatten(), filter_size).reshape(data.shape)
    elif self.get_aggregate_function()  == M_MEAN:
        normalization_values = uniform_filter(data.flatten(), filter_size).reshape(data.shape)
    
    # Return the result
    return data/normalization_values, normalization_values

def do_normalization(self, data, normalization_values, normalization_type, aggregate_type):
    if aggregate_type == M_MEDIAN:
        val = np.median(data)
    elif aggregate_type == M_MEAN:
        val = np.mean(data)
    elif aggregate_type == M_MODE:
        import scipy.ndimage
        # Use histogram function with values a bit removed from saturation
        robust_min = 0.02 * (np.max(data) - np.min(data)) + np.min(data)
        robust_max = 0.98 * (np.max(data) - np.min(data)) + np.min(data)
        nbins = 256
        h = scipy.ndimage.histogram(data.flatten(), robust_min, robust_max, nbins)
        index = np.argmax(h)
        val = np.min(data) + float(index)*(np.max(data) - np.min(data))
    
    return data/val, normalization_values*val
    