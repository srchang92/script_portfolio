#################################################
######  Landcover Change Detection   ############ 
###########     Summer 22      ##################
###########    Stephen Chang   ##################
#################################################

####
# Dear Passenger, this is a simple script that will detect change using Raster 
# math or other available packages. The script reclassifies a given raster to 
# new values so that there are only unique values after raster math. Yes, a 
# little complex, but it worked for my purposes. Then, the area of each change
# type is calculated.


###### Load Packages ######
library(raster)           #for raster covariate data; version 2.6-7 used
library(rgdal)
library(dplyr)
library(rgeos)
library(stringr)

rm(list = ls())


##### Directories for rasters ######
#dirs
lc_dir<- 'C:/Users/srcha/Documents/Grad_school/research/landcover/RF_output'
outdir<- 'C:/Users/srcha/Documents/Grad_school/research/landcover/change_rasters'

#filenames
lc1_name<-'MM_rf_1990_.tif'
lc2_name<-'MM_rf_2000_.tif'
outname<-paste0(str_sub(lc1_name, 1, 2),'_',str_sub(lc1_name, 7, 10), '_',str_sub(lc2_name, 7, 10))

#read in lcs
lc1<-raster(file.path(lc_dir,lc1_name))
lc2<-raster(file.path(lc_dir,lc2_name))

##### Directories for vectors #####
# National park
analysis_extent<-readOGR('C:/Users/srcha/Documents/Grad_school/research/vectors/analysis_extents/MM_finalmask.shp')

# Analysis extent
natpark<-readOGR('C:/Users/srcha/Documents/Grad_school/research/vectors/nat_parks/Zahamena_proj.shp')

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

#buffer 
buffer_dir<-'C:/Users/srcha/Documents/Grad_school/research/vectors/buffers/'
buffer_name<-'Zahamena_buffer.shp'
buff<-readOGR(file.path(buffer_dir, buffer_name))



#### Reclassify raster values #### so that each value represents unique change
og_vals<-c(2, 3, 4, 5, 6, 9, 10)
ng_vals<-c(12, 15, 19, 24, 32, 48, 15)
reclassdf<-data.frame(ogval=og_vals,ngval=ng_vals)
reclass_matrix<-as.matrix(reclassdf)
reclass_matrix                                             #this matrix can handle all of the change types as unique values

lc1_new<-reclassify(lc1,reclass_matrix)
lc2_new<-reclassify(lc2,reclass_matrix)

### reclassification into lumped categories
#og_vals_lumps<- c(2, 3, 4, 5, 6, 9, 10)


##### Raster subtraction #####
diff_raster<- lc1_new-lc2_new
#plot(diff_raster)

#output raw difference rasters (you could deal with them in another GIS if you want)
writeRaster(diff_raster, filename = file.path(outdir, outname), format="GTiff", overwrite=TRUE)


##### Mask Rasters #####
change_vill1<-mask(diff_raster, village1)
change_vill2<-mask(diff_raster, village2)
change_natpark<-mask(diff_raster, natpark)
change_ae<-mask(diff_raster, analysis_extent)
change_inter1<-mask(diff_raster, inter1)
change_inter2<-mask(diff_raster, inter2)
change_buffer<-mask(diff_raster, buff)

#useful vectors 
fields<-c("change_types","km2","perchange")


#### Areas of change types ####
# vector of landcover types
change_vals<-unique(diff_raster)
change_types<-as.vector(change_vals)
change_types

# change areas whole scene all
#areas_vec<-c()
#counter<-1
#for (val in change_types){
#  change_area<-freq(diff_raster, value=val)*900
#  areas_vec[counter]<-change_area
#  counter<-counter+1
#}
#areas_vec
#change_df_all<-data.frame(change_types)
#change_df_all<-cbind(change_df_all, data.frame(areas_vec))
#change_df_all$km2<-change_df_all$areas_vec/1000000
#change_df_all$hect<-change_df_all$areas_vec/10000
#tot_all<-sum(change_df_all$km2)

# change areas Analysis extent
areas_vec<-c()
counter<-1
for (val in change_types){
  change_area<-freq(change_ae, value=val)*900
  areas_vec[counter]<-change_area
  counter<-counter+1
}
areas_vec
change_df_ae<-data.frame(change_types)
change_df_ae<-cbind(change_df_ae, data.frame(areas_vec))
change_df_ae$km2<-change_df_ae$areas_vec/1000000
tot_area_ae<-sum(change_df_ae$km2)
change_only_ae<-change_df_ae[change_df_ae$change_types!=0, ]
change_tot<-sum(change_only_ae$km2)
change_only_ae$perchange<-100*(change_only_ae$km2/change_tot)
change_only_ae<-change_only_ae[fields]
change_only_ae<-change_only_ae[change_only_ae$perchange>5,]
change_prop_ae<-(change_tot/tot_area_ae)*100


# Change areas village1
areas_vec<-c()
counter<-1
for (val in change_types){
  change_area<-freq(change_vill1, value=val)*900
  areas_vec[counter]<-change_area
  counter<-counter+1
}
areas_vec
change_df_vill1<-data.frame(change_types)
change_df_vill1<-cbind(change_df_vill1, data.frame(areas_vec))
change_df_vill1$km2<-change_df_vill1$areas_vec/1000000
tot_area_vill1<-sum(change_df_vill1$km2)
tot_vill1<-sum(change_df_vill1$km2)
change_only_vill1<-change_df_vill1[change_df_vill1$change_types!=0, ]
change_tot<-sum(change_only_vill1$km2)
change_only_vill1$perchange<-100*(change_only_vill1$km2/change_tot)
change_only_vill1<-change_only_vill1[fields]
change_only_vill1<-change_only_vill1[change_only_vill1$perchange>5,]
change_prop_vill1<-(change_tot/tot_area_vill1)*100

# Change areas village2 ###ADD NAMES FOR THIS AND VILL1
areas_vec<-c()
counter<-1
for (val in change_types){
  change_area<-freq(change_vill2, value=val)*900
  areas_vec[counter]<-change_area
  counter<-counter+1
}
areas_vec
change_df_vill2<-data.frame(change_types)
change_df_vill2<-cbind(change_df_vill2, data.frame(areas_vec))
change_df_vill2$km2<-change_df_vill2$areas_vec/1000000
tot_area_vill2<-sum(change_df_vill2$km2)
change_only_vill2<-change_df_vill2[change_df_vill2$change_types!=0, ]
change_tot<-sum(change_only_vill2$km2)
change_only_vill2$perchange<-100*(change_only_vill2$km2/change_tot)
change_only_vill2<-change_only_vill2[fields]
change_only_vill2<-change_only_vill2[change_only_vill2$perchange>5,]
change_prop_vill2<-(change_tot/tot_area_vill2)*100

# change areas natpark
areas_vec<-c()
counter<-1
for (val in change_types){
  change_area<-freq(change_natpark, value=val)*900
  areas_vec[counter]<-change_area
  counter<-counter+1
}
areas_vec
change_df_natpark<-data.frame(change_types)
change_df_natpark<-cbind(change_df_natpark, data.frame(areas_vec))
change_df_natpark$km2<-change_df_natpark$areas_vec/1000000
tot_area_natpark<-sum(change_df_natpark$km2)
change_only_natpark<-change_df_natpark[change_df_natpark$change_types!=0, ]
change_tot<-sum(change_only_natpark$km2)
change_only_natpark$perchange<-100*(change_only_natpark$km2/change_tot)
change_only_natpark<-change_only_natpark[fields]
change_only_natpark<-change_only_natpark[change_only_natpark$perchange>5,]
change_prop_natpark<-(change_tot/tot_area_natpark)*100

# intersect 1
areas_vec<-c()
counter<-1
for (val in change_types){
  change_area<-freq(change_inter1, value=val)*900
  areas_vec[counter]<-change_area
  counter<-counter+1
}
areas_vec
change_df_inter1<-data.frame(change_types)
change_df_inter1<-cbind(change_df_inter1, data.frame(areas_vec))
change_df_inter1$km2<-change_df_inter1$areas_vec/1000000
tot_area_inter1<-sum(change_df_inter1$km2)
change_only_inter1<-change_df_inter1[change_df_inter1$change_types!=0, ]
change_tot<-sum(change_only_inter1$km2)
change_only_inter1$perchange<-100*(change_only_inter1$km2/change_tot)
change_only_inter1<-change_only_inter1[fields]
change_only_inter1<-change_only_inter1[change_only_inter1$perchange>5,]
change_prop_inter1<-(change_tot/tot_area_inter1)*100

# intersect 2
areas_vec<-c()
counter<-1
for (val in change_types){
  change_area<-freq(change_inter2, value=val)*900
  areas_vec[counter]<-change_area
  counter<-counter+1
}
areas_vec
change_df_inter2<-data.frame(change_types)
change_df_inter2<-cbind(change_df_inter2, data.frame(areas_vec))
change_df_inter2$km2<-change_df_inter2$areas_vec/1000000
tot_area_inter2<-sum(change_df_inter2$km2)
change_only_inter2<-change_df_inter2[change_df_inter2$change_types!=0, ]
change_tot<-sum(change_only_inter2$km2)
change_only_inter2$perchange<-100*(change_only_inter2$km2/change_tot)
change_only_inter2<-change_only_inter2[fields]
change_only_inter2<-change_only_inter2[change_only_inter2$perchange>5,]
change_prop_inter2<-(change_tot/tot_area_inter2)*100

# whole buffer
areas_vec<-c()
counter<-1
for (val in change_types){
  change_area<-freq(change_buffer, value=val)*900
  areas_vec[counter]<-change_area
  counter<-counter+1
}
areas_vec
change_df_buffer<-data.frame(change_types)
change_df_buffer<-cbind(change_df_buffer, data.frame(areas_vec))
change_df_buffer$km2<-change_df_buffer$areas_vec/1000000
tot_area_buffer<-sum(change_df_buffer$km2)
change_only_buffer<-change_df_buffer[change_df_buffer$change_types!=0, ]
change_tot<-sum(change_only_buffer$km2)
change_only_buffer$perchange<-100*(change_only_buffer$km2/change_tot)
change_only_buffer<-change_only_buffer[fields]
change_only_buffer<-change_only_buffer[change_only_buffer$perchange>5,]
change_prop_buffer<-(change_tot/tot_area_buffer)*100

#present area tables
change_only_ae %>% arrange(desc(km2))
change_prop_ae
change_only_natpark %>% arrange(desc(km2))
change_prop_natpark
change_only_vill1 %>% arrange(desc(km2))
change_prop_vill1
change_only_vill2 %>% arrange(desc(km2))
change_prop_vill2
change_only_inter1 %>% arrange(desc(km2))
change_prop_inter1
change_only_inter2 %>% arrange(desc(km2))
change_prop_inter2
change_only_buffer %>% arrange(desc(km2))
change_prop_buffer






