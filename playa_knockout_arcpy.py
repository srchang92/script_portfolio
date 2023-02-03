####Script that takes a shapefile with wind farm points and
    ###1. defines an affected area
    ###2. Identifies playas within the affected area.
    ### By Stephen Chang

##initial legwork##

#Import Libraries
import os
import sys
import numpy
import arcpy
from arcpy import env
import timeit
import time
import datetime
import errno
import shutil

#If you are sticking with arcpy, this will save you a load of time
arcpy.env.overwriteOutput = True


#Timer for processing time start
timeBegin= timeit.default_timer()
timeSt= time.localtime()
print ('Start time: '+time.strftime('%a %b %d %H:%M:%S %Y', timeSt)+'\n')


## ---------- assign variables -------------##

# directories for workspace and output, with code to create the output directory if necessary
root = 'C:\\Users\\srcha\\Desktop\\playa_knockout\\windsubsets'
ws = os.path.join(root, 'hullssubsets')
outDir = os.path.join(ws, 'hullssubsets')

#don't use if you created this part already
#try:
 #   os.makedirs(outDir)
#except OSError as e:
 #   if e.errno != errno.EEXIST:
  #      raise

#directory for input wind turbine layer
#windpath = 'Y:\\Wind\\faa_products\\wind_turbines_nov_08_2017'

windname = '2016'
windlyr = os.path.join(ws, windname+'.shp')

#directory to playa layer
#playapath = 'Z:\\Stephen_work\\Practice_layers\\Official_Practice_Run'
playaname = 'PPv4DisbyID_and_RWB'
playalyr = 'C:\\Users\\srcha\\Desktop\\playa_knockout\\PPv4DisbyID_and_RWB.shp'

#directory to PLJV boundary
pljvpath = 'Y:\\PLJV'
pljvname = 'PLJV_Boundary'
pljvlyr = os.path.join(pljvpath,pljvname+'.shp')

#directory to hull lyrs (might need this)
hullname = '2016_hulls'
hulllyr = 'C:\\Users\\srcha\\Desktop\\playa_knockout\\windsubsets\\hullssubsets\\pljv_wind_geometry.shp'

datefield = 'knock_date'


##---------------Geoprocessing for new wind layer -----------------##

def pljv_clip(wind, pljv):
    '''
    Takes the wind layer and clips it to the pljv boundary,
    Direct Paths to the lyrs, plz...
    '''
    # Create feature layer of wind turbines for selection outside Arcmap
    print 'converting wind turbines to a feature class...'
    timeStart = timeit.default_timer()
    windfeature = os.path.join(windpath,windname+'_ftr.shp')
    arcpy.MakeFeatureLayer_management(wind,windfeature)
    print 'feature layer complete'
    timeEnd = timeit.default_timer()
    print ('Processing Time: '+ '{0:.2f}'.format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print ('\n'+'-----------------------------------------'+'\n')
    #Select from wind turbines intersecting the PLJV boundary
    print 'making selection of windmills...'
    timeStart = timeit.default_timer()
    selection = arcpy.SelectLayerByLocation_management(windfeature,"INTERSECT",pljv,"#","NEW_SELECTION")
    print 'selection complete'
    timeEnd = timeit.default_timer()
    print ('Processing Time: '+ '{0:.2f}'.format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print ('\n'+'-----------------------------------------'+'\n')
    #Export wind turbines to new layer
    print 'creating "PLJV wind turbines" layer...'
    timeStart = timeit.default_timer()
    pljvwind = os.path.join(outDir,windname+'_pljv.shp')
    arcpy.CopyFeatures_management(selection,pljvwind,"#","0","0","0")
    print 'layer completed'
    timeEnd = timeit.default_timer()
    print ('Processing Time: '+ '{0:.2f}'.format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print ('\n'+'-----------------------------------------'+'\n')
    #New directory to pljvwind with root in output directory
    pljvwindname = 'wind_turbines_nov_08_2017_pljv'
    pljvwindlyr = os.path.join(outDir,pljvwindname+'.shp')
    return pljvwindlyr

def convexhulls(pljvwind):
    '''
    Creates convex hulls by buffering wind turbines, dissolving buffers,
    assigning them unique IDs, and using IDs as a guide for convex hulls.
    Again, direct path to 'pljvwindlyr' plz.
    '''
    #Buffer - 1000m
    print 'buffering wind turbines...'
    timeStart = timeit.default_timer()
    bufferout = os.path.join(outDir,windname+'_buffer.shp')
    arcpy.Buffer_analysis(pljvwind,bufferout,"1000 Meters","FULL","ROUND","NONE","#")
    print 'Buffer Complete'
    timeEnd = timeit.default_timer()
    print ('Processing Time: '+ '{0:.2f}'.format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print ('\n'+'-----------------------------------------'+'\n')
    #Dissolve buffers - 'create multipart features = unchecked; FID = checked; 
    print 'Dissolving buffer...'
    timeStart = timeit.default_timer()
    dissolveout = os.path.join(outDir,windname+'_dissolve.shp')
    arcpy.Dissolve_management(bufferout,dissolveout,"FID","#","SINGLE_PART","DISSOLVE_LINES")
    print "Dissolve complete"
    timeEnd = timeit.default_timer()
    print ('Processing Time: '+ '{0:.2f}'.format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print ('\n'+'-----------------------------------------'+'\n')
    #Identity - join attributes = ONLY_FID ; input is windmill points, identity is dissolved buffers
    print 'identifying unique windfarm ID for each turbine...'
    timeStart = timeit.default_timer()
    IDout = os.path.join(outDir,windname+'_identity.shp')
    arcpy.Identity_analysis(pljvwind,dissolveout,IDout,"ONLY_FID","#","NO_RELATIONSHIPS")
    print 'Identity complete'
    timeEnd = timeit.default_timer()
    print ('Processing Time: '+ '{0:.2f}'.format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print ('\n'+'-----------------------------------------'+'\n')
    #Minimum bounding geometry - Group Option = List; Group Fields = unique farm ID Column; Windmills w/ farm ID for input.
    print 'Creating convex hulls...'
    timeStart = timeit.default_timer()
    geometryout = os.path.join(outDir,windname+'_hulls.shp') #Made change here 5/9/18
    #creates a list of all field names, changes list to str type, then loops through and selects unique farm_ID field and sets it as a variable
    field_names = [f.name for f in arcpy.ListFields(IDout)]
    counter = 0
    for field in field_names:
        field_names[counter] = str(field_names[counter])
        counter +=1
    #This part here is kinda hacky. It seems as though all of the outputs from
    #the last arcpy function meet these two and requirements
    for field in field_names:
        if 'FID' in field and field.endswith('d'):
            farm_id = field
    #print farm_id
    arcpy.MinimumBoundingGeometry_management(IDout,geometryout,"CONVEX_HULL","LIST",farm_id,"NO_MBG_FIELDS")
    print 'Convex hulls complete'
    return geometryout
    timeEnd = timeit.default_timer()
    print ('Processing Time: '+ '{0:.2f}'.format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print ('\n'+'-----------------------------------------'+'\n')


def affected_playas(hulls,playas):
    '''
    finds newly affected playas and updates the date they were affected to
    that of when the new wind layer was released(2month intervals?)
    '''
    #Make Feature Layer - a necessary step to select features outside of Arcmap
    print 'converting LD_playas to a feature class...'
    timeStart = timeit.default_timer()
    playafeature = playalyr+'_ftr.shp'
    arcpy.MakeFeatureLayer_management(playalyr,playafeature)
    print 'feature layer complete'
    timeEnd = timeit.default_timer()
    print ('Processing Time: '+ '{0:.2f}'.format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print ('\n'+'-----------------------------------------'+'\n')
    #Select by location - selecting playas that intersect with convex hulls
    print 'making selection of affected playas...'
    timeStart = timeit.default_timer()
    arcpy.SelectLayerByLocation_management(playafeature,"INTERSECT",hulls,"#","NEW_SELECTION")
    print 'selection complete'
    timeEnd = timeit.default_timer()
    print ('Processing Time: '+ '{0:.2f}'.format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print ('\n'+'-----------------------------------------'+'\n')
    #Update the fields in the selection IF they are currently null
    with arcpy.da.UpdateCursor(playafeature, datefield) as cursor:
        for row in cursor:
            if row[0]=='0':
                row[0]='2017'#hullname[0:4]
                cursor.updateRow(row)
    print 'knockout dates have been updated'
 
def delet_dir(dir):
    '''
    run this if you don't feel like manually deleting all of the created files
    and the directory, copy all needed files first, though...
    '''
    shutil.rmtree(dir)

#####-----------Call functions here--------------#####
#pljv_clip(windlyr,pljvlyr)
#convexhulls(windlyr)
affected_playas(hulllyr,playalyr)
#delet_dir(outDir)
print 'finished!'
