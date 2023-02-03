"""
Playa Knockout Script OS
By Stephen Chang
stephen.chang@pljv.org
"""

import fiona
import shapely
import os
import geopandas as gpd
import errno
import shutil
from osgeo import ogr, osr
import numpy as np
from beatbox import vector

'''
Some of your shapefiles may not be able to be read by geopandas as they contain non-
UTF 8 characters. Quick-fix: save a copy in QGIS as 'UTF-8' encoding,
otherwise, use the converter functions
'''

#allows you to plot and check as you go. very useful in ipython
#interactive(True)

#FunctionBank $$$
def create_dir(dirlocation=None):

    '''
    creates a directory for you to output files to
    '''

    try:
        os.makedirs(dirlocation)
    except OSError as e:
        if e.errno !=errno.EEXIST:
            raise


def point_converter(shapefile=None):

    '''
    writes a converted shapefile that doesn't contain non-UTF characters
    '''
    #open file with ogr and get its layer
    driver =  ogr.GetDriverByName("ESRI Shapefile")
    ds = driver.Open(shapefile, 0)
    layer = ds.GetLayer()

    #Create new shapefile and convert
    ds2 = driver.CreateDataSource(shapefile[0:-4]+'_converted.shp')
    layer2 = ds2.CreateLayer('', None, ogr.wkbPoint)
    for feature in layer:
        layer2.CreateFeature(feature)

    #prepare corresponding projection file
    spatialref = layer.GetSpatialRef()
    spatialref = str(spatialref)
    spatialref = spatialref.replace(" ","")
    spatialref = spatialref.replace("\n","")

    #write to .prj file
    prj = open(shapefile[0:-4]+'_converted.prj','w')
    prj.write(spatialref)
    prj.close()

def poly_converter(shapefile=None):

    '''
    writes a converted shapefile that doesn't contain non-UTF characters
    '''
    #open file with ogr and get its layer
    driver =  ogr.GetDriverByName("ESRI Shapefile")
    ds = driver.Open(shapefile, 0)
    layer = ds.GetLayer()

    #Create new shapefile and convert
    ds2 = driver.CreateDataSource(shapefile[0:-4]+'_converted.shp')
    layer2 = ds2.CreateLayer('', None, ogr.wkbPolygon)
    for feature in layer:
        layer2.CreateFeature(feature)

    #prepare corresponding projection file
    spatialref = layer.GetSpatialRef()
    spatialref = str(spatialref)
    spatialref = spatialref.replace(" ","")
    spatialref = spatialref.replace("\n","")

    #write to .prj file
    prj = open(shapefile[0:-4]+'_converted.prj','w')
    prj.write(spatialref)
    prj.close()

def pljv_clip(windlyr=None,pljvboundlyr=None):

    '''
    returns wind GeoDataFrame clipped to within input pljvboundary
    writes shapefile of subset
    '''

    wind = gpd.read_file(windlyr)
    pljvbound = gpd.read_file(pljvboundlyr)
    wind = wind.to_crs({'init': 'epsg:32614'})
    pljvbound = pljvbound.to_crs({'init': 'epsg:32614'})

    #clip to pljv boundary
    boundary = pljvbound.geometry[0]
    windsubset =wind[wind.within(boundary)]
    windsubset.to_file(windlyr[0:-4]+'_clip.shp')
    return windsubset


def convexhulls(windsubs=None):

    '''
    accepts geopandas gdf as input
    Buffers points, dissolves buffers, assigns unique ids,and...
    Returns convex hull GeoDataFrame
    '''

    #Format for assigning buffers to geometry of a manipulable geodataframe
    windbuff=windsubs
    windbuff['geometry']=windbuff.geometry.buffer(1000,resolution=16)

    #dissolve buffers by explode()
    windbuff.loc[:,"group"] = 1
    dissolved = windbuff.dissolve(by="group")
    gs = dissolved.explode()
    gdf2 = gs.reset_index().rename(columns={0: 'geometry'})
    gdf_out = gdf2.merge(dissolved.drop('geometry', axis=1), left_on='level_0', right_index=True)
    gdf_out = gdf_out.set_index(['level_0', 'level_1']).set_geometry('geometry')
    gdf_out.crs = windbuff.crs
    buff_diss = gdf_out.reset_index()

    #assign unique windfarm ID field to each wind turbine and group them into multi-points based on that

        # 'level_1' is the unique windfarm id in this case
    windsubset_wID = gpd.sjoin(windsubset,buff_diss,how='inner',op='intersects')

    #create convex hulls around the windturbines based on wind farm windsubset, dissolve--> convex hull
    windsubset_farms = windsubset_wID.dissolve(by='level_1')
    hulls = windsubset_farms.convex_hull
    hulls_gdf = gpd.GeoDataFrame(gpd.GeoSeries(hulls))
    hulls_gdf['geometry']=hulls_gdf[0]
    hulls_gdf.crs = {'init': 'epsg:32614'}
    del hulls_gdf[0] #Clean up that weird column in the hulls
    return hulls_gdf


def affected_playas(hulls_lyr=None,playa_lyr=None):

    '''
    accepts geopandas geodataframe (hulls_lyr) and a .shp (playa_lyr) as inputs
    returns GeoDataFrame of playas with field 'knock_date' updated to date of wind dataset
    release, if playa had not been previously affected. Also writes _copy of original layer
    '''

    playas = gpd.read_file(playa_lyr)
    playas = playas.to_crs({'init': 'epsg:32614'})

    #Find playas that intersect with 'hulls_gdf' and update a date column with the dataset's release IF affected
    playas['knock_date']='null' #add knock_date field, populate w 'null'
    polygons = hulls_lyr.geometry
    polygons = hulls_lyr.loc[hulls['geometry'].geom_type=='Polygon'] #this works officially to trim lines and points
    sj_playas = gpd.sjoin(playas,polygons,how='inner',op='intersects')
    aff_playas = playas.geom_almost_equals(sj_playas)
    aff_playas = aff_playas[~aff_playas.index.duplicated()]
    playas['knock_date'][aff_playas]=playa_lyr[-11:-4] #way to selet only affected playas. seems to work.

    #import

    playas.to_file(playa_lyr[0:-4]+'_copy.shp'))
    return playas

#def write_layer(layer):

#    '''
#    writes Geodataframe to shapefile, don't include '.shp' in your input
#    '''
#    layer.to_file(os.path.join(outDir,input('Name your file here: ')+'.shp'))

def delet_dir(dir):
    '''
    deletes a directory you designate
    '''
    shutil.rmtree(dir)


#Point script to where your files are. In this case, same folder 'ws'
root = 'C:\\Users\\srcha\\Desktop' #where folder is located
ws = os.path.join(root,'playa_knockout') #ws folder path
outDir = os.path.join(ws, 'output') #ouput folder path within ws
create_dir(outDir) #try creating outDir if not already created.

#file names, use os.path.join to create full path from (ws, file_name+'.shp')
pljvbound_name = 'PLJV_Boundary'
playas_name = 'PPv4DisbyID_and_RWB'
wind_name = 'wind_turbines_nov_08_2017'

#convert layers to appropriate utf characters
poly_converter(os.path.join(ws,pljvbound_name+'.shp'))
poly_converter(os.path.join(ws,playas_name+'.shp'))
point_converter(os.path.join(ws,wind_name+'.shp'))

#Define variables to be read
pljvbound_shp = os.path.join(ws,pljvbound_name+'_converted.shp')
playas_shp = os.path.join(ws,playas_name+'_converted.shp')
wind_shp = os.path.join(ws,wind_name+'_converted.shp')

###call functions
#pljv_clip(wind_shp,pljvbound_shp)
#convexhulls(os.path.join(outDir,'wind_clip.shp'))
#affected_playas(os.path.join(outDir,'conv_hulls.shp'), os.path.join(ws,playas_name+'.shp'))##DONT need to convert playas layer i guess.


print ('finshed')

####------OTHER USEFUL ipython functions-----####
#variable.plot()                    ----> plot the output
#gpd.GeodataFrame.crs               ----> print current coordinate reference system
#print(type(variable))              ----> see what geopandas data type you are in
#variable.head()                    ----> prints first few entries
#GeodataFrame.to_file               ----> saves to file
#pd.options.display.max_rows = 4000 ----> increases number of rows printed for more data inspection
