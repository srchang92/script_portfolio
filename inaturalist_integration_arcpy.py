##### iNaturalist Data downloads
##### Created: Stephen Chang 8/20/2018
##### Updated: 11/9/18, 1/31/2019

'''
This script accepts a csv from the iNaturalist website
and formats it according to the CPW resource stewardship
standard. It puts the new dataset into the appropriate

'''


####--- Libraries ---####
import os
import arcpy
from arcpy import env


####----- Function vault -----####

def csv_shp(csv):
    '''
    This function takes a csv, outputs it to a shapefile
    to the specifications of stew crew's iNaturalist data downloads
    '''
    #Creates a feature view (points) of a .csv with lat/long fields
    feature_class = 'iNat_points'
    x_coords = 'longitude'
    y_coords = 'latitude'
    arcpy.MakeXYEventLayer_management(table=csv, in_x_field="longitude", in_y_field="latitude", out_layer=feature_class, spatial_reference= arcpy.SpatialReference(4326), in_z_field="")

    #Creates a shapefile of the above feature view
    shp = 'iNat_points_practice'
    arcpy.CopyFeatures_management(in_features=feature_class, out_feature_class=os.path.join(outDir,shp+'.shp'), config_keyword="", spatial_grid_1="0", spatial_grid_2="0", spatial_grid_3="0")
    print 'created shapefile from table!'

    #reprojects shapefile to appropriate sr, input sr should be epsg = 4326 to work
    shp1 = 'iNat_points_26913'
    arcpy.Project_management(in_dataset=os.path.join(outDir,shp+'.shp'), out_dataset=os.path.join(outDir,shp1+'.shp'), out_coor_system=arcpy.SpatialReference(26913), transform_method="WGS_1984_(ITRF00)_To_NAD_1983", in_coor_system=arcpy.Describe(os.path.join(outDir,shp+'.shp')).spatialReference, preserve_shape="NO_PRESERVE_SHAPE", max_deviation="", vertical="NO_VERTICAL")
    print 'reprojected shapefile!'

    # Makes a feature layer, selects by location (within 10miles of park), and exports to a new shp
    feature = 'iNat_26913_ftr'
    arcpy.MakeFeatureLayer_management(os.path.join(outDir,shp1+'.shp'), feature)
    arcpy.SelectLayerByLocation_management(in_layer=feature, overlap_type="WITHIN_A_DISTANCE", select_features=SPboundary, search_distance="10 Miles", selection_type="NEW_SELECTION", invert_spatial_relationship="NOT_INVERT")
    shp2 = 'iNat_26913_closetopark'
    arcpy.CopyFeatures_management(in_features=feature, out_feature_class=os.path.join(outDir,shp2+'.shp'), config_keyword="", spatial_grid_1="0", spatial_grid_2="0", spatial_grid_3="0")
    print 'Screened for close-to-park observations!'

    # Make feature class of new obs and add appropriate matching fields
    tableview = 'new_obs_table'
    arcpy.MakeTableView_management(os.path.join(outDir,shp2+'.shp'),tableview)
    arcpy.AddField_management(in_table=tableview, field_name="id_1", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
    arcpy.AddField_management(in_table=tableview, field_name="field_num", field_type="SHORT", field_precision="3", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
    arcpy.AddField_management(in_table=tableview, field_name="num_id_agr", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
    arcpy.AddField_management(in_table=tableview, field_name="num_id_dis", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
    print 'appropriate fields added'

    #populate above fields
    arcpy.CalculateField_management(in_table=tableview, field="id_1", expression="[id]", expression_type="VB", code_block="")
    arcpy.CalculateField_management(in_table=tableview, field="field_num", expression="[field_numb]", expression_type="VB", code_block="")
    arcpy.CalculateField_management(in_table=tableview, field="num_id_agr", expression="[num_identi]", expression_type="VB", code_block="")
    arcpy.CalculateField_management(in_table=tableview, field="num_id_dis", expression="[num_iden_1]", expression_type="VB", code_block="")
    print 'fields populated!'

    #delete a wonky field
    arcpy.DeleteField_management(in_table = tableview, drop_field = 'field_numb')
    print 'deleted a wonky field...'

def delete_dups(shp,fc):
    '''
    This function takes the prepared shapefile ready for loading,
    Joins it to the official iNat feature class, deletes matching
    entries, and then removes the join
    '''
    tableview = 'shp_view'
    #Make a temporary Table view (annoying, i know) of the last version of the shapefile of new inat observations so that it can be joined.
    feature1 = 'inat_obs_points_feature'
    arcpy.MakeTableView_management(shp,tableview)
    arcpy.MakeFeatureLayer_management(fc,feature1) #the workspace is set to the GDB, so you can refer to this file simply by string name
    print 'made a table view/feature for new and old obs!'

    # Join the new shapefile to the geodatabase 'inat_observation_points
    arcpy.AddJoin_management(in_layer_or_view=feature1, in_field="id", join_table=tableview, join_field="id", join_type="KEEP_ALL")#Loads a shp into a feature class
    print 'join worked!'

    # Select by IS NOT NULL to select duplicates
        #where clause references name from original layer, not from name of tableview.... This is not intuitive, but it seems to work out...
    arcpy.SelectLayerByAttribute_management(in_layer_or_view=feature1, selection_type="NEW_SELECTION", where_clause='"iNat_26913_closetopark.id" IS NOT NULL')
    print 'selection perfection!'

    #deletes duplicates
    arcpy.DeleteFeatures_management(feature1)
    print 'Deleted duplicates!'

    #removes join on inat_obsevation_points
    arcpy.RemoveJoin_management(feature1)
    print 'join removed'

#### Notes about the following append function:
#### Adapted from ESRI community member LukeW
#### Edited by Stephen Chang, CPW

    #### It is important to understand how arcGIS handles the field mapping component
    #### of its tools such as 'append', 'merge', 'spatial join' and others...
    #### I attempt to provide a brief summary of such here:

      ## A FieldMappings object must be provided for any call of the above tools.
      ## This object is a collection of individual FieldMap objects for each target
      ## layer field. By default, just like in the GUI, identical names are matched,
      ## which is good because then you don't have to specify tuples for every freaking
      ## fieldjust the ones that don't match. This script repairs/corrects
      ## the fieldmappings object for fields that we would manually change by hand (GUI)
      ## in the previous download protocol by doing the following for each tuple:
      ## 1. finds the index of the target field
      ## 2. Copies the fieldmap object for this target field
      ## 3. Corrects the target fieldmap object's input to the append field in the tuple
      ## 4. Replaces the old fieldmap object for the target field with the new with the correct append field
      ## FINALLY, the script calls the append tool with the FieldMappings_Object

def append(shp,fc):
    '''
    This function prepares the fieldmappings object,
    then appends the prepared shapefile to the iNat feature class
    '''
    # vars
    append_layer = shp
    target_layer = fc

    ###---Field Mapping---###
    
    ## Populates the arcGIS FieldMappings object ##
    # Empty Field Mappings
    fieldmappings = arcpy.FieldMappings() 
    # Add tables from both layers to field mappings. This FieldMappings object will look different than
    # the object for the spatial join, where you add a single field from the join layer rather than
    # the whole table as done here for the append
    fieldmappings.addTable(append_layer)
    fieldmappings.addTable(target_layer)

    ## Prepares a list of tuples that contain the proper fields ##
    mapping_list = [] #empty list
    # add appropriate tuples. as many as you need, add another line here.
    # First item in tuple is append, second is target
    mapping_list.append(('id_1','id'))
    mapping_list.append(('field_num', 'field_numb'))
    mapping_list.append(('num_id_agr','num_identi'))
    mapping_list.append(('num_id_dis','num_iden_1'))

    ## Loop through the mapping_list and do the things ##

    for field_map in mapping_list:
        # do the stuff. brackets refer to index in tuples
        index = fieldmappings.findFieldMapIndex(field_map[1])    #find index of field we need to modify match for
        field_map_object = fieldmappings.getFieldMap(index)      #define the fieldmap object we need to modify
        field_map_object.addInputField(append_layer,field_map[0])#modify the field map object
        fieldmappings.replaceFieldMap(index, field_map_object)   #replace the old fieldmap object with the new in fieldmappings object

    print 'fields mapped, i hope...'

    ### Arcpy tool call ###
    arcpy.Append_management(inputs=append_layer, target=target_layer, schema_type = 'NO_TEST',field_mapping = fieldmappings)
    print 'appended... check results though...'

def populate_parkname(parkslyr, fc):
    '''
    This function joins the parkbndry layer to the feature class,
    populates parkname, and removes joined field
    '''

    #remake iNat feature layer (just in case, this might not be necessary)
    feature2 = 'iNat_points'
    arcpy.MakeFeatureLayer_management(in_features = fc,out_layer = feature2)

    #define target and join layers
    join_layer = parkslyr
    target_layer = fc

    # field maps for spatial join
    fieldmappings = arcpy.FieldMappings()
    fieldmappings.addTable(target_layer)
    fieldmap = arcpy.FieldMap()
    fieldmap.addInputField(parkslyr,'PropName')
    fieldmappings.addFieldMap(fieldmap)

    #All of the joins
    print 'Attempting spatial join...'
    arcpy.SpatialJoin_analysis('iNat_observation_points',SPboundary, r"L:\parks\public\colorado\biology\animals\Biological_Observations.gdb\iNat_Observations\iNat_observation_points_sj","JOIN_ONE_TO_ONE","KEEP_ALL",fieldmappings, "CLOSEST","10 Miles","")
    #calculate field
    arcpy.CalculateField_management('iNat_observation_points_sj',"Park_Name","[PropName]","VB","")
    #delete field
    arcpy.DeleteField_management("iNat_observation_points_sj","PropName")
    print 'joined, calculated, and cleaned up!'

def TnE_swap_rename(sjfc,fc,TnE_join,swap_join):
    '''
    This function populates TnE and swap fields in the feature class
    through table joins. Finally, because I didnt feel like making a small
    function, this deletes the old and renames the new FC
    '''
    #table/feature views
    feature3 = 'iNat_forjoin'
    arcpy.MakeFeatureLayer_management(in_features = sjfc,out_layer = feature3)
    arcpy.MakeTableView_management(in_table = swap_join, out_view = 'swap_forjoin')
    arcpy.MakeTableView_management(in_table = TnE_join, out_view = 'TnE_forjoin')

    #Join, calculate field, and remove joins for swap and TnE
    arcpy.AddJoin_management(in_layer_or_view = 'iNat_forjoin', in_field = 'common_nam', join_table = 'swap_forjoin', join_field = 'Common_Name', join_type = 'KEEP_ALL')
    arcpy.CalculateField_management(in_table = "iNat_forjoin", field = "SWAP", expression="[swap_join.Status]",expression_type="VB", code_block="")
    arcpy.RemoveJoin_management(in_layer_or_view = 'iNat_forjoin')
    arcpy.AddJoin_management(in_layer_or_view = 'iNat_forjoin', in_field = 'common_nam', join_table = 'TnE_forjoin', join_field = 'Common_Name', join_type = 'KEEP_ALL')
    arcpy.CalculateField_management(in_table = "iNat_forjoin", field = "TnE", expression="[TnE_join.Status]",expression_type="VB", code_block="")
    arcpy.RemoveJoin_management(in_layer_or_view = 'iNat_forjoin')
    print 'swap and tne calculated'

    #delete old, rename new to old
    arcpy.Delete_management(fc)
    arcpy.Rename_management(sjfc, 'iNat_observation_points','FeatureClass')
    print 'feature classes renamed!'


####---- Directories and Variables ----####

### --- Overview directories --- ###

#Root and output directories
root = 'L:\\admin\\stewardship\\iNaturalist\\Data_Downloads\\Edited_for_GDB'
outDir = os.path.join(root,'output')

#directory to State Park boundaries. If the schema of the SDE changes, BeWaRe!
CPWAllProperties = 'Database Connections\CDPW.sde\CDPW.DBO.CPWAllProperties' #path to SDE layer added 11/9/18 updated from out of date shapefile THIS MAY BREAK IF the sde changes any features

# iNat feature class directory, as well as directory settings
arcpy.env.overwriteOutput = True #an important line to overwrite shapefiles if running script more than once
arcpy.env.workspace = r"L:\parks\public\colorado\biology\animals\Biological_Observations.gdb"
arcpy.env.qualifiedFieldNames = False #necessary to manage unruly field names after joining tables

### --- Variables for each function --- ###

## -- csv_shp variables -- ##
#path to table csv input - will change depending on where you put your prepared csv, what you name your csv
csvname = 'State_Parks_NatureFinder_20190401' #just the name, THIS CHANGES EACH MONTH
csv_file = os.path.join(root,csvname+'.csv')#path with function combining root and name, plus file extension type. use variable csv_file for call

## -- delete_dups variables -- ##
shp_name = 'iNat_26913_closetopark'
new_obs = os.path.join(outDir, shp_name+'.shp') #call with new_obs
iNat_feature = 'iNat_observation_points' #call with iNat_feature

## -- append variables -- ##
#call with new_obs
#call with iNat_feature

## -- populate_parkname variables -- ##
arcpy.MakeFeatureLayer_management(CPWAllProperties,'SPboundary')
SPboundary = arcpy.SelectLayerByAttribute_management(in_layer_or_view='SPboundary', selection_type="NEW_SELECTION", where_clause="PropType = 'SP' OR PropType = 'Recreation Area' AND PropName <> 'Cameo Shooting and Education Complex RA'")
#call with SPboundary
#call with iNat_feature

## -- TnE_swap_rename variables -- ##
iNat_feature_sj = 'iNat_observation_points_sj' #call with iNat_feature_sj
#call with iNat_feature
swap = 'swap_join' #call with swap
TnE = 'TnE_join' #call with TnE


#### ----- Call functions here ----- ####
csv_shp(csv_file)
delete_dups(new_obs, iNat_feature)
append(new_obs,iNat_feature)
populate_parkname(SPboundary, iNat_feature)
TnE_swap_rename(iNat_feature_sj,iNat_feature,TnE,swap)

print 'finished!'

