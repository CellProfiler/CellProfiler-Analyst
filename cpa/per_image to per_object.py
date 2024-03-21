
from . import dbconnect
from . import properties
import os
from . import imagereader
import re
import wx
import sys

wildcard = "Properties files (*.properties)|*.properties|"     \
           "All files (*.*)|*.*"

def LoadFile():
     path=''
     dlg = wx.FileDialog(app.GetTopWindow(), message="Choose a properties file",
            defaultDir=os.getcwd(), defaultFile="", wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_CHANGE_DIR)
     if dlg.ShowModal() == wx.ID_OK:
          path=dlg.GetPaths()
     else:
          sys.exit('Loading file error.')
     return path[0]

def error(text):
     dlg = wx.MessageDialog(app.GetTopWindow(), 'Error: %s.' %(text),
            'Error', wx.OK | wx.ICON_INFORMATION)
     dlg.ShowModal()
     sys.exit('Unmaching channels dimensions.')
     
def conflict_table(name):
     dlg = wx.MessageDialog(app.GetTopWindow(), 'A table named %s already exists in the database: overwrite?' %(name),
            'Table conflict', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_INFORMATION)
     choice=dlg.ShowModal()
     if choice==wx.ID_NO:
          return False
          #OLD: sys.exit('Table already exists.')
     return True
     
def conflict_file(name):
     dlg = wx.MessageDialog(app.GetTopWindow(), 'A file named %s already exists: overwrite?' %(name),
            'File conflict', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_INFORMATION)
     choice=dlg.ShowModal()
     if choice==wx.ID_NO:
          return False
          #OLD: sys.exit('File already exists.')
     return True

def conflict_resolution(name):
     dlg = wx.TextEntryDialog(app.GetTopWindow(), 'Enter a new name',
            'Conflict resolution', '', wx.OK)
     dlg.SetValue(name)
     dlg.ShowModal()
     new_name=dlg.GetValue()
     return new_name

def run():
    # Get properties file
    p=properties.Properties()
    p.LoadFile(LoadFile())

    # Create the DB according to the instructions in the properties file
    db=dbconnect.DBConnect()
    db.execute('SELECT 1')

    # Create a copy of the per_image table
    fake_obj_table=p.image_table+'_2'
    # Test to check if a table with this name doesn't exist yet
    table_names=db.GetTableNames()
    # OLD: assert(fake_obj_table not in table_names), 'Error: Per_image-based per_object table already exists.'
    while fake_obj_table in table_names:
         if not conflict_table(fake_obj_table):
              temp=conflict_resolution(fake_obj_table)
              if temp == '':
                   print('Error: No name recorded.')
              else:
                   fake_obj_table=temp
         else:
              db.execute('DROP TABLE %s' %(fake_obj_table))
              break
          
    # Remove the columns with files names and paths
    cols_im=db.GetColumnNames(p.image_table)
    cols_types=db.GetColumnTypes(p.image_table)
    cols_names_types=list(zip(cols_im, cols_types))
    db.execute('CREATE TABLE %s AS SELECT %s FROM %s' %(fake_obj_table, ', '.join([x[0] for x in cols_names_types if x[1]!=str]), p.image_table))

    # Add columns to the new per_image table such that it looks like a per_object table
    cols_obj=['ObjectNumber', 'Nuclei_Location_CenterX', 'Nuclei_Location_CenterY']
    # Object number:
    db.execute('ALTER TABLE %s ADD COLUMN %s' %(fake_obj_table, cols_obj[0]))
    # X position:
    db.execute('ALTER TABLE %s ADD COLUMN %s' %(fake_obj_table, cols_obj[1]))
    # Y position:
    db.execute('ALTER TABLE %s ADD COLUMN %s' %(fake_obj_table, cols_obj[2]))
    db.Commit()

    # Fill the object number column with 1's
    db.execute('UPDATE %s SET %s=1' %(fake_obj_table, cols_obj[0]))
    db.Commit()

    # Move to the directory of the properties file in order to be able to find where the images are
    os.chdir(os.path.dirname(p._filename))
    # Get image keys from the DB
    rows=db.execute('SELECT %s FROM %s LIMIT 1' %(dbconnect.UniqueImageClause(), p.image_table))
    image_keys=rows[0]
    fds=db.GetFullChannelPathsForImage(image_keys)
    # Catches image dimensions
    imrdr=imagereader.ImageReader()
    img=imrdr.ReadImages(fds)
    # Test to check if all channels have the same dimensions
    [X,Y]=img[0].shape
    # OLD:
    # for i in range(1, len(img)):
    #     assert(img[i].shape == (X,Y)), 'Error: Different chanels do not have same dimensions.'
    # Update the X and Y columns as width (or height) divided by two (center of the image)
    dim=True
    text='Different chanels do not have same dimensions'
    for i in range(1, len(img)):
         if img[i].shape != (X,Y):
              dim=False
    if not dim:
         error(text)
         
    db.execute('UPDATE %s SET %s=%s' %(fake_obj_table, cols_obj[1], int(X)/2))
    db.execute('UPDATE %s SET %s=%s' %(fake_obj_table, cols_obj[2], int(Y)/2))
    db.Commit()

    # Creates a new properties file with updated field values
    p.object_table=fake_obj_table
    p.image_tile_size=min(int(X),int(Y))
    filename='example_2.properties' # How to generalize? Like get the name of the current .properties and append a _2?
    # Test to check if there is not already a properties file called like that
    files=os.listdir(os.getcwd())

    # OLD:
    # for i in range(0, len(files)):
    #     assert(files[i] != new_name), 'Error: Properties file already exists.'
    # OLD:
    # exist=False
    # for i in range(0, len(files)):
    #     if files[i] == filename:
    #            exist=True
    #     if exist:
    #            conflict_file(filename)

    while filename in files:
         if not conflict_file(filename):
              temp=conflict_resolution(filename)
              if temp == '':
                   print('Error: No name recorded.')
              else:
                   filename=temp
         else:
              break

    p.save_file(filename)
    sys.exit()

if __name__ == "__main__":
    app = wx.App()
    run()
    app.MainLoop()

# Old stuff:
# File names...
#regexp=re.compile('\w*[Ff]ile[Nn]ames\w*') # Actually '[Ff]ile[Nn]ames' is probably enough
#found=filter(regexp.search, header)
# Paths...
#regexp=re.compile('\w*[Pp]ath[Nn]ames\w*') # Actually '[Pp]ath[Nn]ames*' is probably enough
#found.extend(filter(regexp.search, header))
