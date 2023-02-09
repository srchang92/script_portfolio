###########################################
######         Lab 9 Code         #########
######        Stephen Chang        ########
###########################################


###### Load Packages ######
library(raster)           #for raster covariate data; version 2.6-7 used
library(reshape2)         #for re-formatting data; version 1.4.3 used
library(mgcv)             #for gams; version 1.8-24 used
library(dismo)            #for SDMs; version 1.1-4 used
library(randomForest)     #for random forest SDMs; version 4.6-14 used
library(maxnet)           #maxent with maxnet; version 0.1.2 used
library(glmnet)           #needed for maxnet; version 2.0-16 used
library(MuMIn)            #for model selection; version 1.42.1 used
library(PresenceAbsence)  #for model evaluation; version 1.1.9 used
library(ecospat)         #for model evaluation; version 3.0 used
library(cowplot)
library(ggplot2)
library(viridis)
library(data.table)
library(rgdal)
library(dplyr)

#clear environment
rm(list = ls())

#set working directory where data were downloaded
setwd("C:/Users/srcha/Documents/Grad_school/classes/ecol620_landscape/labs/lab9/lab9_data")

#### Read in Datasets####

###  Read CSV eBird
clnu <- read.csv(file="zero_fill_data_Nucifraga_columbiana.csv", header=TRUE) #CO observations between a certain date range.

### Read in Rasters
elev<- raster('elevation.tif')
slope<-terrain(x=elev, opt="slope", unit="degrees", neighbors=8)
nlcd_low<- raster('nlcd2011_low.tif')
impervious_low<-raster('percent_impervious_surface_2011_low.tif')
precip_annual <- raster('precip_annual_mean.tif')
precip_june <- raster('precip_june_mean.tif')
temp_annual <- raster('temp_annual_mean.tif')
temp_max_june <-raster('temp_max_june.tif')
temp_mean_june <- raster('temp_mean_june.tif')
temp_min_june <- raster('temp_min_june.tif')
canopy_low <- raster('tree_canopy_percent_2011_low.tif')
ndvi<- raster('CO_NDVI_proj.tif') #The projection is right, but we will fix the resolution and extent next - only ndvi res is different, only ndvi extent is different


#### Filtering/formatting datasets ####

### eBird pt 1 ###
#desired columns
clnu_sub<-clnu[,c("latitude", "longitude", "duration_minutes", "effort_distance_km", "number_observers", "species_observed")]


#how many pres-abs
summary(clnu_sub$species_observed) #This shows 33923 absence and 1040 presence files
head(clnu_sub)

#omit na values
nrow(clnu_sub)
clnu_sub<-na.omit(clnu_sub)
nrow(clnu_sub) #19585
summary(clnu_sub$species_observed) # now 19,071 absence and 514 presence
#could have more observations, but removal of NA probably dropped
#"incomplete" or "incidental" checklist types from number of minutes column 

#separate presence and absence data to randomly select some of them
clnu_pres<-clnu_sub[clnu_sub$species_observed==TRUE,]
clnu_abs<-clnu_sub[clnu_sub$species_observed==FALSE,]

#split into training/truth randomly
presence_rows<-sample(nrow(clnu_pres)) #creates a matrix/array of values by which clnu_pres will be shuffled next step
clnu_pres<-clnu_pres[presence_rows,] #These two steps shuffle the df
clnu_pres_train<- clnu_pres[1:round((nrow(clnu_pres)*.8)),] # the first 80%
clnu_pres_validate<-clnu_pres[412:514,] # the last 20% , I only know the integers from printing

absence_rows<- sample(nrow(clnu_abs))
clnu_abs<-clnu_abs[absence_rows,] #shuffle absence values
clnu_abs_train<- clnu_abs[1:round((nrow(clnu_abs)*.8)),] # the first 80%
clnu_abs_validate<-clnu_abs[15258:nrow(clnu_abs),] # the last 20% , I only know the integers from printing

#combine training and validation points for presence/absence
all_training <- rbind(clnu_pres_train, clnu_abs_train) #binds training presences with training absences
nrow(clnu_abs_train)+nrow(clnu_pres_train) #15668
nrow(all_training) #15668)

all_validation<-rbind(clnu_pres_validate, clnu_abs_validate) #binds validation presences with validation absences
nrow(clnu_abs_validate)+nrow(clnu_pres_validate) #3917
nrow(all_validation) #3917

nrow(clnu_sub) #19585
nrow(all_validation)+nrow(all_training) #19585 Just a verification step

#change TRUE to 1 and FALSE to 0 for both training and validation
head(all_training) #quick check
all_training$pres_abs<-0 #create new variable column, set to 0
head(all_training) #quick check
all_training$pres_abs[all_training$species_observed==FALSE]<-0 #subset new column based on boolean
all_training$pres_abs[all_training$species_observed==TRUE]<-1 #subset new column based on boolean
head(all_training) # quick check
all_training_final<-all_training[,c("latitude", "longitude", "duration_minutes", "effort_distance_km", "number_observers", "pres_abs")]#drop species_observed column
head(all_training_final)

all_validation$pres_abs<-0
head(all_validation)
all_validation$pres_abs[all_validation$species_observed==FALSE]<-0
all_validation$pres_abs[all_validation$species_observed==TRUE]<-1
head(all_validation)
all_validation_final<-all_validation[,c("latitude", "longitude", "duration_minutes", "effort_distance_km", "number_observers", "pres_abs")]
head(all_validation_final)
all_validation_final$pres_abs


### end of eBird pt 1 ###




### formatting rasters ### - only NDVI, since other data was pre-formatted for this exercise
#resample ndvi
ndvi <- resample(x=ndvi, y=elev, "bilinear")  #bilinear fine for continuous NDVI

#crop ndvi
ndvi <- mask(ndvi, elev)


#mean of each, a very simplistic way to translate eBird table effort values to raster surface, not something I would predict on outside of school laboratory setting.
duration_value <-mean(clnu_sub$duration_minutes, na.rm=TRUE)
distance_value <-mean(clnu_sub$effort_distance_km, na.rm=TRUE)
observers_value <-mean(clnu_sub$number_observers, na.rm=TRUE)

#empty raster
#nrow and ncol of stack
nrow(elev) #481
ncol(elev) #842

duration_r<-raster(nrows=nrow(elev), ncols=ncol(elev), ext=extent(elev), crs=proj4string(elev)) #dummy duration raster
values(duration_r)<-duration_value

distance_r<-raster(nrows=nrow(elev), ncols=ncol(elev), ext=extent(elev), crs=proj4string(elev)) #dummy distance raster
values(distance_r)<-distance_value

observers_r <- raster(nrows=nrow(elev), ncols=ncol(elev), ext=extent(elev), crs=proj4string(elev))
values(observers_r)<- observers_value

#prep nlcd better
int_vec<-unique(nlcd_low$nlcd2011_low) #NLCD integers vector
class_vec<- c('water', 'ice_now', 'devel_open', 'devel_low','devel_med', 'devel_high',
              'barren', 'deciduous', 'evergreen', 'mixed_forest', 'shrub_scrub',
              'grassland', 'pasture', 'crops', 'woody_wetland', 'herby_wetland')
#ABOVE: order-sensitive, nlcd LC names based on integers
class_matrix <- data.frame(int_vec, class_vec)      
head(class_matrix) #correct

##Reclassify: create rasters to predict based on forest cover types
#evergreen
reclass_to_evergreen <- c(0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0)
reclass.mat_evergreen <- cbind(int_vec,reclass_to_evergreen)
reclass.mat_evergreen#first col: orginal; second: change to
nlcd_low_evergreen <- reclassify(nlcd_low,reclass.mat_evergreen)

#mixed
reclass_to_mixed<-c(0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0)
reclass.mat_mixed<-cbind(int_vec, reclass_to_mixed)
reclass.mat_mixed
nlcd_low_mixed <-reclassify(nlcd_low, reclass.mat_mixed)

#Prepare the stack
layers_rf <-stack(elev, slope, nlcd_low_evergreen, nlcd_low_mixed, impervious_low, precip_annual, precip_june, temp_annual,
                  temp_max_june, temp_mean_june, temp_min_june, canopy_low, ndvi)
layers_predict <- stack(elev, slope, nlcd_low_evergreen, nlcd_low_mixed, impervious_low, precip_annual, precip_june, temp_annual,
                temp_max_june, temp_mean_june, temp_min_june, canopy_low, ndvi, duration_r, distance_r, observers_r)
names(layers_rf)
names(layers_predict) #view current names layer.1=duration_r layer.2=distance_r, layer.3=observers_r, otherwise obvious

# Changing names of layers for easier interpretation
names(layers_predict)<- c('Elevation', "Slope", "Evergreen", "Mixed", "Impervious","Precip_Annual_Mean", "Precip_June_Mean",
                          "Temp_Annual_Mean", "Temp_June_Max", "Temp_June_Mean", "Temp_June_Min", "Canopy",
                          "NDVI", "Duration", "Distance", "Observers")

### end of formatting rasters ###




### extract GIS data to table for RF ### ####CHECK HERE FOR SLOPE
head(all_training_final)
clnu_xy_training <- as.matrix(all_training_final[,c("longitude","latitude")]) #table of only latlong values
clnu_cov_training <- extract(layers_rf, clnu_xy_training) #extract raster values at each xy coordinate
clnu_presabs_training <- data.frame(all_training_final, clnu_cov_training) # bind the values above to the training data which has latlong, and eBird effort vals
names(clnu_presabs_training) #current names default from variable/layer names 
colnames(clnu_presabs_training) <- c("Latitude", "Longitude", "Duration", "Distance", "Observers",
                                     "CLNU", "Elevation","Slope","Evergreen", "Mixed", "Impervious",
                                     "Precip_Annual_Mean", "Precip_June_Mean", "Temp_Annual_Mean",
                                     "Temp_June_Max", "Temp_June_Mean", "Temp_June_Min", "Canopy",
                                     "NDVI")
colnames(clnu_presabs_training) #check 
clnu_presabs_training_pred<-clnu_presabs_training[,3:18] #drop latitude and longitude from training
head(clnu_presabs_training_pred)

# DO the same extraction for validation data
clnu_xy_validation <- as.matrix(all_validation_final[,c("longitude","latitude")])
clnu_cov_validation <- extract(layers_rf, clnu_xy_validation)
clnu_presabs_validation <- data.frame(all_validation_final, clnu_cov_validation)
names(clnu_presabs_validation)
colnames(clnu_presabs_validation) <- c("Latitude", "Longitude", "Duration", "Distance", "Observers",
                                     "CLNU", "Elevation", "Slope","Evergreen", "Mixed", "Impervious",
                                     "Precip_Annual_Mean", "Precip_June_Mean", "Temp_Annual_Mean",
                                     "Temp_June_Max", "Temp_June_Mean", "Temp_June_Min", "Canopy",
                                     "NDVI")
head(clnu_presabs_validation) #check
clnu_presabs_validation_pred<-clnu_presabs_validation[,3:18] #drop latitude and longitude from training
head(clnu_presabs_validation_pred) #check


#I'M NOW READY WITH clnu_presabs_training_pred as my training data and my two layers: layers_rf, layers_predict

### end of extract GIS data ###


head(clnu_presabs_training)

### Random Forest model and prediction surface ###
#random forest model (default) # as.factor makes it a classification (discrete) rather than regressions (continuous)
rf.clnu<-randomForest(as.factor(CLNU) ~ ., na.action=na.omit, ntree=500, data=clnu_presabs_training_pred)
varImpPlot(rf.clnu)
rf.map <- predict(layers_predict, rf.clnu, type="prob",index=2) #creates raster surface across entire state for CLark's Nutcracker


### End Random Forest Model ###




### Display ###
#read in CO state outline
states_map <- map_data("state")
co_map <- states_map[states_map$region=='colorado',]
co_map

class(states_map)
p1<-ggplot()+
  geom_polygon(data=co_map, aes(x=long, y=lat), fill=NA, color='black')+
  geom_point(data=all_training_final, aes(x=longitude, y=latitude), color='black')+
  ggtitle("Clark's Nutcracker Training")+
  theme(plot.title = element_text(hjust = 0.5))+
  theme_classic()
p1
p2<-ggplot()+
  geom_polygon(data=co_map, aes(x=long, y=lat), fill=NA, color='black')+
  geom_point(data=all_validation_final, aes(x=longitude, y=latitude), color='black')+
  ggtitle("Clarks Nutcracker Validation")+
  theme(plot.title = element_text(hjust = 0.5))+
  theme_classic()
p2
plot_grid(p1,p2,nrow=1)

rf.map.df<-as.data.frame(rf.map, xy=T)
rf.map.df_nonull<-na.omit(rf.map.df)
names(rf.map.df_nonull)<-c('x', 'y', 'Occurrence')
p3<- ggplot()+
  geom_tile(data=rf.map.df_nonull, aes(x=x, y=y, fill=Occurrence))+
  scale_fill_viridis(option='magma', direction=-1)+
  ggtitle("Clark's Nutcracker Occurrence")+
  theme_classic()
p3
writeRaster(rf.map, "occurrence_surface_rf", format="GTiff")
