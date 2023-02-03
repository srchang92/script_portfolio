####### Cluster Analysis  #########
#PLJV script in 2018
#By Stephen Chang

import os
import sys
import arcpy
from arcpy import env
from arcpy.sa import *
import timeit
import time
import datetime
arcpy.env.overwriteOutput = True

#timer for processing time start
timeBegin = timeit.default_timer()
timest = time.localtime()
print ('Start time: '+time.strftime('%a %b %d %H:%M:%S %Y', timest)+'\n')


##--------------------assign variables--------------------------##

#directories for workspace and output
root = 'C:\\Users\\srcha\\Desktop'
ws = os.path.join(root, 'Cluster_Analysis')
outDir = os.path.join('r',ws, 'output')

#directory to playa cluster layer
playapath = 'C:\\Users\\srcha\\Desktop\\Cluster_Analysis'
playaname = 'PPv4DisbyID_andRWB'
playalyr = os.path.join('r',playapath, playaname+'.shp')



# Check a list of field names for 'AREA', and add an empty field if it is not found
print ('finding the area of all playas...')
field_names = [f.name for f in arcpy.ListFields(playalyr)]
counter = 0
for field in field_names:
    field_names[counter] = str(field_names[counter])
    counter +=1
if 'AREA' not in field_names:
    arcpy.AddField_management(playalyr,"AREA","FLOAT","9","6","#","#","NON_NULLABLE","NON_REQUIRED","#")
    expression1 = "{0}".format("!SHAPE.area@SQUAREKILOMETERS!")
    arcpy.CalculateField_management(playalyr, "AREA", expression1, "PYTHON",)
print ('area field created and populated')

# Creating playa centroids
print ('creating playa centroids layer...')
centrout = os.path.join(outDir,playaname+'_centroids.shp')
arcpy.FeatureToPoint_management(playalyr, centrout, point_location="CENTROID")
print ('done with centroids')



### pt. 1 - number of playas per unit area as selector   line 54

#Add Spatial analyst extension, persists for rest of script
arcpy.CheckOutExtension("Spatial")
#Creating point density raster layer
print ('creating playa density layer...')
densityout = os.path.join(outDir, playaname+'_pt_density.tif')
arcpy.gp.PointDensity_sa(centrout, "NONE", densityout, "30", "Circle 2000 MAP", "SQUARE_KILOMETERS")
print ('density layer complete')

#extract density values back to centroids
print ('creating extracted density layer...')
extractout = os.path.join(outDir, playaname+'_extracted.shp')
arcpy.gp.ExtractValuesToPoints_sa(centrout, densityout, extractout, "INTERPOLATE", "VALUE_ONLY")
print ('extracted values complete')

#add new adjusted density field
print ('adjusting density for same playa...')
arcpy.AddField_management(extractout, field_name="AREA_ADJ", field_type="FLOAT", field_precision="9", field_scale="6", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
arcpy.CalculateField_management(extractout, field="AREA_ADJ", expression="[RASTERVALU] -0.079577", expression_type="VB", code_block="")
print ('density adjusted')

#Delete 'RASTERVALU' field, you don't need it anymore since you have adjusted density
print ('deleting "RASTERVALU" field...')
arcpy.DeleteField_management(extractout, drop_field="RASTERVALU")
print ('field deleted')



### pt. 2 - surface area per unit area as a selector

#create SA density TIF line 84
print ('creating playa surface area density layer...')
saout = os.path.join(outDir, playaname+'_sa_density.tif')
arcpy.gp.PointDensity_sa(centrout, "AREA", saout, "30", "Circle 2000 MAP", "SQUARE_KILOMETERS")
print ('density by surface area now complete... ')

#extract those values to new layer - use "extractout"
print ('extracting surface area density values...')
extract1out = os.path.join(outDir, playaname+'_extracted1.shp')
arcpy.gp.ExtractValuesToPoints_sa(extractout, saout, extract1out, "INTERPOLATE", "VALUE_ONLY")
print ('new extractions complete')

#adjust SA values for own playa
print ('adjusting SA density for own playa...')
arcpy.AddField_management(extract1out, field_name="SA_ADJ", field_type="FLOAT", field_precision="9", field_scale="9", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
arcpy.CalculateField_management(extract1out, field="SA_ADJ", expression="(([RASTERVALU] *12.566370614) - [AREA]) /12.566370614", expression_type="VB", code_block="")
print ('SA density adjusted')

#Delete 'RASTERVALU' field again from extract1out, not needed, and you'll have to extract again... line 102
print ('deleting "RASTERVALU" field...')
arcpy.DeleteField_management(extract1out, drop_field="RASTERVALU")
print ('field deleted')


### pt. 3  -   Making selections from previous centroids, making new layers,

#select centroids based on high numbers of playas
print ('Creating 2 selected centroid layers from high density criteria...')

#makes a feature layer of the doubly extracted "extract1out" to make selections
extractfeature = os.path.join(outDir, playaname+'_ftrlyr')
arcpy.MakeFeatureLayer_management(extract1out, extractfeature)

#Makes selection to the feature and coopies the "promised" centroids to two new layers line 117
arcpy.SelectLayerByAttribute_management(extractfeature, selection_type="NEW_SELECTION", where_clause='"AREA_ADJ" >0.74')
centroids1 = os.path.join(outDir, playaname+'_sel_centr_1.shp')
arcpy.CopyFeatures_management(extractfeature,centroids1, config_keyword="", spatial_grid_1="0", spatial_grid_2="0", spatial_grid_3="0")

arcpy.SelectLayerByAttribute_management(extractfeature, selection_type="NEW_SELECTION", where_clause='"SA_ADJ" >0.0074')
centroids2 = os.path.join(outDir, playaname+'_sel_centr_2.shp')
arcpy.CopyFeatures_management(extractfeature,centroids2, config_keyword="", spatial_grid_1="0", spatial_grid_2="0", spatial_grid_3="0")
print ('Features copied...')

### pt. 4 -   kernel density of playa centroids

#create Playa kernel density TIF
print ('creating playa centroid kernel density TIF...')
kernel1out = os.path.join(outDir, playaname+'_K_pt_density.tif')
arcpy.gp.KernelDensity_sa(centrout, "NONE", kernel1out, "30", "2000", "SQUARE_KILOMETERS", "DENSITIES", "PLANAR")
print ('Kernel playa density complete')

#create Playa SA density TIF
print ('creating playa surface area density TIF...')
kernel2out = os.path.join(outDir,playaname+'_K_sa_density.tif')
arcpy.gp.KernelDensity_sa(centrout, "AREA", kernel2out, "30", "2000", "SQUARE_KILOMETERS", "DENSITIES", "PLANAR")
print ('Kernel playa surface area density')


### pt. 5 - extract values of kernel density rasters to new selected centroids
print ('extracting kernel density...')

# create extracted Kernel centroids for playa density
kernelextracted1 = os.path.join(outDir, playaname+'_kernel_extract_1.shp')
arcpy.gp.ExtractValuesToPoints_sa(centroids1, kernel1out, kernelextracted1, "INTERPOLATE", "VALUE_ONLY")

# create extracted Kernel centroids for playa surface area density
kernelextracted2 = os.path.join(outDir, playaname+'_kernel_extract_2.shp')
arcpy.gp.ExtractValuesToPoints_sa(centroids1, kernel2out, kernelextracted2, "INTERPOLATE", "VALUE_ONLY")
print ('kernel density extracted')

### pt. 6 - finds the FID Values necessary to then extract the cutoff AREA and SA values from a sorted centroid layer

#create a count and 95th percentile FID Value for each
print ('finding 95th percentile threshold...')
result1=arcpy.GetCount_management(kernelextracted1)
result1 = str(result1)
index1 = int(int(result1)*.05)

result2=arcpy.GetCount_management(kernelextracted2)
result2 = str(result2)
index2= int(int(result2)*0.05)

#sort the two centroid layers by ascending AREA_ADJ, SA_ADJ, respectively
sortout1 = os.path.join(outDir,playaname+'_centr_sort1.shp')
arcpy.Sort_management(kernelextracted1, sortout1, sort_field="AREA_ADJ ASCENDING", spatial_sort_method="UR")

sortout2 = os.path.join(outDir,playaname+'_centr_sort2.shp')
arcpy.Sort_management(kernelextracted2, sortout2, sort_field="SA_ADJ ASCENDING", spatial_sort_method="UR")

#defines fields for searchcursor, then uses fields to output threshold value
fields1 = ["AREA_ADJ","FID"]
with arcpy.da.SearchCursor(sortout1,fields1) as cursor:
    for row in cursor:
        if row[1]==index1:
            threshold1=str(row[0])
            threshold1=threshold1[0:7]

fields2 = ["SA_ADJ","FID"]
with arcpy.da.SearchCursor(sortout2,fields2) as cursor:
    for row in cursor:
        if row[1]==index2:
            threshold2=str(row[0])
            threshold2=threshold2[0:7]
print ('Thresholds assigned')


### pt. 7 use threshold to select 95% of playas from the respective sortout puts and copy those to a new layer

print ('sorting layers and selecting top 95%...')
#make feature layers of each in order to select FEATURE LAYERS SAVED TO MEMORY ONLY
sortedftr1 = 'sortedftr1_lyr'
arcpy.MakeFeatureLayer_management(sortout1,sortedftr1)
sortedftr2 = 'sortedftr2_lyr'
arcpy.MakeFeatureLayer_management(sortout2,sortedftr2)

#make selections from each based on thresholds, copy them to new layers
arcpy.SelectLayerByAttribute_management(sortedftr1, selection_type="NEW_SELECTION", where_clause='"AREA_ADJ" >='+threshold1)
centr95_1=os.path.join(outDir,playaname+'_centr_95_1.shp')
arcpy.CopyFeatures_management(sortedftr1,centr95_1, config_keyword="", spatial_grid_1="0", spatial_grid_2="0", spatial_grid_3="0")

arcpy.SelectLayerByAttribute_management(sortedftr2, selection_type="NEW_SELECTION", where_clause='"SA_ADJ" >='+threshold2)
centr95_2=os.path.join(outDir,playaname+'_centr_95_2.shp')
arcpy.CopyFeatures_management(sortedftr2,centr95_2, config_keyword="", spatial_grid_1="0", spatial_grid_2="0", spatial_grid_3="0")
print ('top 95% copied to new layer')


### pt. 8 sorts copied features again, and assigns a minvalue to the lowest Kdensity value

print ('finding minimum corresponding Kernel values...')
#create new sorted layers, again.... lesigh... There is definitely an easier way to get the minimum value...
sort95out1= os.path.join(outDir,playaname+'_95_sort1.shp')
arcpy.Sort_management(centr95_1, sort95out1, sort_field="RASTERVALU ASCENDING", spatial_sort_method="UR")
sort95out2= os.path.join(outDir,playaname+'_95_sort2.shp')
arcpy.Sort_management(centr95_2, sort95out2, sort_field="RASTERVALU ASCENDING", spatial_sort_method="UR")

#searchcursor assigns two new minvalues for use in reclassification of rasters
fieldsboth = ["FID","RASTERVALU"]
with arcpy.da.SearchCursor(sort95out1,fieldsboth) as cursor:
    for row in cursor:
        if row[0]==0:
            minvalue1=row[1]
with arcpy.da.SearchCursor(sort95out2,fieldsboth) as cursor:
    for row in cursor:
        if row[0]==0:
            minvalue2=row[1]
print ('Kernel Values assigned')


### pt. 9 reclassifying Kernel Density rasters to zeroes and 1s

# reclassify, and save the rasters to new files
print ('reclassifying rasters...')
reclassified1 = os.path.join(outDir,playaname+'_Kernel1_reclassified.tif')
reclassified2 = os.path.join(outDir,playaname+'_Kernel2_reclassified.tif')
reclass1 = Reclassify(kernel1out, "VALUE", "0 "+str(minvalue1)+" 0;"+str(minvalue1)+" 20 1", "DATA")
reclass2 = Reclassify(kernel2out, "VALUE", "0 "+str(minvalue2)+" 0;"+str(minvalue2)+" 5 1", "DATA")
reclass1.save(reclassified1)
reclass2.save(reclassified2)
print ('reclassified rasters have been saved')


### pt. 10 merge reclassified rasters, then convert to polygons, AKA clusters

print ('creating playa clusters layer.............')
# Use Math Algebra to create 1 and 2 values for reclassification
kernelmath = os.path.join(outDir,playaname+'_kernel12_algebra.tif')
outplus = Plus(reclassified1,reclassified2)
outplus.save(kernelmath)

# Reclassify result
mathreclass = os.path.join(outDir,playaname+'_kernel12_merged.tif')
mergereclass = Reclassify(kernelmath, "VALUE", "0 0;1 1;2 1","DATA")
mergereclass.save(mathreclass)

#extract the 1s!!!!!
mergedkernelnull = os.path.join(outDir,playaname+'_kernel12_null.tif')
mergednull = ExtractByAttributes(mathreclass, '"Value" = 1')
mergednull.save(mergedkernelnull)

# Convert mergedkernel raster to polygons
clusters = os.path.join(outDir,playaname+'_clusters.shp')
arcpy.RasterToPolygon_conversion(mergedkernelnull, clusters, simplify="SIMPLIFY", raster_field="Value")

timeDone = timeit.default_timer()
print('Total Processing Time: '+ "{0:.2f}".format(((timeDone - timeBegin)/60))+' minutes'+'\n')
timeEd = time.localtime()
print('End Time: '+ time.strftime('%a %b %d %H:%M:%S %Y',timeEd)+'\n')

print ("Finshed!")
