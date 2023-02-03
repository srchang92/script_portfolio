#################################################
######   Landcover area calculator   ############ 
###########     Summer 22      ##################
###########    Stephen Chang   ##################
#################################################



#####
# Dear passenger, this script is quick and will calculate the area of landcovers from 
# a classified raster for different polygon regions of interest. For my research, I 
# I am calculating areas for each landcover type for protected areas and surrounding 
# communities
#####

###### Load Packages ######
library(raster)           
library(rgdal)
library(dplyr)
library(rgeos)
library(stringr)
library(leaflet)

rm(list = ls())            #this clears environment history, use when necessary

###### Provide directories and inputs ######
# raster input
landcover<-raster('C:/Users/srcha/Documents/Grad_school/research/landcover/RF_output/AS_rf_1990_.tif')

##### Directories for vectors #####
# National park
natpark<-readOGR('C:/Users/srcha/Documents/Grad_school/research/vectors/nat_parks/Zahamena_proj.shp')

# Analysis extent
analysis_extent<-readOGR('C:/Users/srcha/Documents/Grad_school/research/vectors/analysis_extents/AS_finalmask.shp')

# village extent(s)
village_dir<- 'C:/Users/srcha/Documents/Grad_school/research/vectors/village_boundaries/'
village1_name<-'Anosivola_proj.shp'
village2_name<-'Sahamalaza_proj.shp'
village1<-readOGR(file.path(village_dir,village1_name))
village2<-readOGR(file.path(village_dir,village2_name))

#Village-park intersects
inter_dir<- 'C:/Users/srcha/Documents/Grad_school/research/vectors/intersects/'
inter1_name<- 'ZAH_anosivola.shp'
inter2_name<- 'ZAH_sahamalaza.shp'
inter1<-readOGR(file.path(inter_dir,inter1_name))
inter2<-readOGR(file.path(inter_dir,inter2_name))  # Just use one of these for the Andohahela area, it doesn't matter if that portion of the script fails.

# WHole buffer LC - 1 per scene. Not doing the Special reserve ANkarana
buff<-readOGR('C:/Users/srcha/Documents/Grad_school/research/vectors/buffers/Zahamena_buffer.shp')


#CSV output folder, if necessary
outdir<- 'C:/Users/srcha/Documents/Grad_school/research/tables'


##### Processing #####
## mask the rasters
lc_ae<-mask(x=landcover, mask=analysis_extent)
lc_village1<-mask(x=landcover, mask=village1)
lc_village2<-mask(x=landcover, mask=village2)
lc_natpark<-mask(x=landcover, mask = natpark)
lc_inter1<-mask(x=landcover, mask=inter1)
lc_inter2<-mask(x=landcover, mask=inter2)
lc_buffer<-mask(x=landcover, mask=buff)

# vector of landcover types
lc_types<-unique(lc_ae)
lc_types<-as.vector(lc_types)
lc_types

# LC areas analysis extent
lc_df_ae<-as.data.frame(freq(lc_ae))
lc_df_ae<-lc_df_ae[!is.na(lc_df_ae$value),]
lc_df_ae$m2<-lc_df_ae$count*900
lc_df_ae$km2<-lc_df_ae$m2/1000000
tot_area_ae<-sum(lc_df_ae[lc_df_ae$value!=0,]['km2'])
lc_df_ae<-lc_df_ae[lc_df_ae$value!=0,]
lc_df_ae$percov<-(lc_df_ae$km2/tot_area_ae)*100
lc_df_ae
tot_area_ae


#LC areas natpark
lc_df_natpark<-as.data.frame(freq(lc_natpark))
lc_df_natpark<-lc_df_natpark[!is.na(lc_df_natpark$value),]
lc_df_natpark$m2<-lc_df_natpark$count*900
lc_df_natpark$km2<-lc_df_natpark$m2/1000000
tot_area_natpark<-sum(lc_df_natpark['km2'])
lc_df_natpark$percov<-round((lc_df_natpark$km2/tot_area_natpark)*100,3)
lc_df_natpark
tot_area_natpark

# LC areas village1
lc_df_village1<-as.data.frame(freq(lc_village1))
lc_df_village1<-lc_df_village1[!is.na(lc_df_village1$value),]
lc_df_village1$m2<-lc_df_village1$count*900
lc_df_village1$km2<-lc_df_village1$m2/1000000
tot_area_village1<-sum(lc_df_village1['km2'])
lc_df_village1$percov<-round((lc_df_village1$km2/tot_area_village1)*100,3)
lc_df_village1
tot_area_village1


# LC areas village2
lc_df_village2<-as.data.frame(freq(lc_village2))
lc_df_village2<-lc_df_village2[!is.na(lc_df_village2$value),]
lc_df_village2$m2<-lc_df_village2$count*900
lc_df_village2$km2<-lc_df_village2$m2/1000000
tot_area_village2<-sum(lc_df_village2['km2'])
lc_df_village2$percov<-round((lc_df_village2$km2/tot_area_village2)*100,3)
lc_df_village2
tot_area_village2

#LC areas inter1
lc_df_inter1<-as.data.frame(freq(lc_inter1))
lc_df_inter1<-lc_df_inter1[!is.na(lc_df_inter1$value),]
lc_df_inter1$m2<-lc_df_inter1$count*900
lc_df_inter1$km2<-lc_df_inter1$m2/1000000
tot_area_inter1<-sum(lc_df_inter1['km2'])
lc_df_inter1$percov<-round((lc_df_inter1$km2/tot_area_inter1)*100,3)
lc_df_inter1
tot_area_inter1


#LC areas inter2  #THIS CAN FAIL, DOESN'T HURT REST OF SCRIPT if you only use one intersect (Andohahela)
lc_df_inter2<-as.data.frame(freq(lc_inter2))
lc_df_inter2<-lc_df_inter2[!is.na(lc_df_inter2$value),]
lc_df_inter2$m2<-lc_df_inter2$count*900
lc_df_inter2$km2<-lc_df_inter2$m2/1000000
tot_area_inter2<-sum(lc_df_inter2['km2'])
lc_df_inter2$percov<-round((lc_df_inter2$km2/tot_area_inter2)*100,3)
lc_df_inter2
tot_area_inter2


#LC areas buffer
lc_df_buffer<-as.data.frame(freq(lc_buffer))
lc_df_buffer<-lc_df_buffer[!is.na(lc_df_buffer$value),]
lc_df_buffer$m2<-lc_df_buffer$count*900
lc_df_buffer$km2<-lc_df_buffer$m2/1000000
tot_area_buffer<-sum(lc_df_buffer['km2'])
lc_df_buffer$percov<-round((lc_df_buffer$km2/tot_area_buffer)*100,3)
lc_df_buffer
tot_area_buffer

#present area tables
lc_df_ae
tot_area_ae
lc_df_natpark
tot_area_natpark
lc_df_village1
tot_area_village1
lc_df_village2
tot_area_village2
lc_df_inter1
tot_area_inter1
lc_df_inter2
tot_area_inter2
lc_df_buffer
tot_area_buffer

