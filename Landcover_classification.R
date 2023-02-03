#################################################
######   Landcover Classification     ########### 
###########     Summer 22      ##################
###########    Stephen Chang   ##################
#################################################

##### Dear passengers, this sript reads in a folder containing subfolder landsat scenes. 
##### This represents a muli-scene classification where all scenes for a given goal year
##### are stacked automatically and classified. The user provides the folder directory,
##### the training point shapefile, and a few other logistical lines for the output, 
##### and this script takes care of the rest. 


###### Load Packages ######
library(raster)           #for raster covariate data; version 2.6-7 used
library(randomForest)     #for random forest SDMs; version 4.6-14 used
library(rgdal)
library(dplyr)
library(rgeos)
library(stringr)
library(caret)            #accuracy assessment/matrix
library(whitebox)

rm(list = ls())            #this clears environment history, use when necessary



###### Provide directories and inputs ######
### Input training shapefile ###
training_dataset <- readOGR('C:/Users/srcha/Documents/Grad_school/research/vectors/sampling_points/all_merged/MM_2000_training_pts.shp')

### Input of analysis extent ###
finalmask <- readOGR("C:/Users/srcha/Documents/Grad_school/research/vectors/analysis_extents/MM_finalmask.shp") #read in analysis extent remember_nocloud for AA
fm_extent<- extent(finalmask)

### Input Landsat directory for analysis
wd<-"C:/Users/srcha/Documents/Grad_school/research/landsat/MM/2000"

#SRTM Elevation (CHANGES DEPENDING ON site)
srtm<- raster('C:/Users/srcha/Documents/Grad_school/research/elevation/MM_srtm.tif')


### Output directory for predicted raster
outdir<-'C:/Users/srcha/Documents/Grad_school/research/landcover/RF_output'
output_name<-"MM_rf_2000_test.tif"

### Output directory for filtered raster
outdirfil<-'C:/Users/srcha/Documents/Grad_school/research/landcover/processed_lc'
outfil_name<- "MM_rf_2000_filtered.tif"



##### Functions vault  #####
#find the scene name
find_scene_name <- function(folderpath){
  scene_name<-str_sub(folderpath, -23, -16)
  return(scene_name)
}

# return EVI : conditional on position of the layers in the stack
evi_finder <- function(lyrstack){
  b4<-raster::subset(lyrstack, grep('B4', names(lyrstack), value = T))
  b3<-raster::subset(lyrstack, grep('B3', names(lyrstack), value = T))
  b1<-raster::subset(lyrstack, grep('B1', names(lyrstack), value = T))
  evi<- ((b4-b3)/(b4+(6*b3)-(7.5*b1)+1))
  return(evi)
}

# return NDMI
NDMI_finder <- function(lyrstack){
  b4<-raster::subset(lyrstack, grep('B4', names(lyrstack), value = T))
  b5<-raster::subset(lyrstack, grep('B5', names(lyrstack), value = T))
  ndmi<-(b4 - b5) / (b4 + b5)
  return(ndmi)
}


# return ndvi 
NDVI_finder<-function(lyrstack){
  b4<-raster::subset(lyrstack, grep('B4', names(lyrstack), value = T))
  b3<-raster::subset(lyrstack, grep('B3', names(lyrstack), value = T))
  ndvi<-(b4-b3)/(b4+b3)
  return(ndvi)
}



##### Processing pt 1: Reading bands and calculating spectral indices #####
wd_subdirs<-list.dirs(wd)[-1]     #create list of the sub directories minus the mother

#appends cropped band bricks to individual scene in list of scenes. List of scenes accessed as strings using get()
scene_list_string<-list()
for (dir in wd_subdirs){
  bands<- list.files(dir,pattern = glob2rx("*B*.TIF$"), full.names = TRUE)
  bands<- subset(bands, !grepl('B8',bands))   #drop band 8, panchromatic
  bands<- subset(bands, !grepl("VCID_2",bands)) #drop high band 6, only want low band 6
  scene_name<-find_scene_name(dir)
  band_stack<- stack(bands)
  band_crop<-crop(band_stack,fm_extent)
  dir_evi<- evi_finder(band_crop)
  dir_ndmi<-NDMI_finder(band_crop)
  dir_ndvi<- NDVI_finder(band_crop)
  dir_spectral<-list(dir_evi,dir_ndmi,dir_ndvi)
  spectral_stack<-stack(dir_spectral)
  final_stack<-stack(list(band_crop, spectral_stack))
  names(final_stack)[8]<-paste('ndvi',scene_name, sep = '')
  names(final_stack)[9]<-paste('evi',scene_name, sep = '')
  names(final_stack)[10]<-paste('ndmi',scene_name, sep = '')
  assign(scene_name,final_stack)
  scene_list_string<-append(scene_list_string, scene_name)
}

scene_list_string
get(scene_list_string[[1]])                         # variable accessed from strings using get()


#srtm processing
dummystack<-get(scene_list_string[[1]])
dummyraster<- dummystack[[1]]
srtm<-resample(srtm,dummyraster)
srtm
dummyraster

#Calculate slope from srtm
slope<-terrain(x=srtm, opt="slope", unit="degrees", neighbors=8)
slope


#Loop through string list and stack all bands 10 bands each scene
stack_all_scenes<-list()
for (item in scene_list_string){
  stack_all_scenes<-append(stack_all_scenes, get(item))
}
stack_all_scenes<-append(stack_all_scenes,srtm)
stack_all_scenes<-append(stack_all_scenes, slope)
stack_analyze<-stack(stack_all_scenes)
stack_analyze                                       # It seems the naming convention defaults to B1.1, B1.1, evi.1, evi.2
stack_analyze<-mask(x=stack_analyze, mask=finalmask) #Remove line if you want to run the whole extent


# Random sampling from training dataset,
head(training_dataset)
training_df<-as.data.frame(training_dataset)
head(training_df)
training_df_sub<-training_df[,c("LC","coords.x1","coords.x2")]
head(training_df_sub)
dummy_rows<-sample(nrow(training_df_sub))
training_df_shuffled<-training_df_sub[dummy_rows,]
head(training_df_shuffled)
numtraining<-round(nrow(training_df_shuffled)*0.7)    #70/30
numvalidation<- nrow(training_df_sub)-numtraining
validation_df_final<-training_df_shuffled[1:numvalidation,]
training_df_final <- training_df_shuffled[numvalidation+1:nrow(training_df_shuffled),]

#extract spectral data
head(training_df_final)
training_xy <- as.matrix(training_df_final[,c('coords.x1','coords.x2')])
training_cov <-extract(stack_analyze, training_xy)
training_extracted <-data.frame(training_df_final, training_cov)

#drop the location information and ID
training_only <-subset(training_extracted, select = -c(coords.x1,coords.x2))

# drop nodata rows just in case
training_only <- training_only[complete.cases(training_only),]
nrow(training_only)
head(training_only)

#Random Forest -
var_matrix<-as.matrix(names(training_only))
var_matrix<-var_matrix[-1]  #Drops LC from matrix, which is always first. 
randfor<- randomForest(as.factor(LC)~ ., ntree = 1000, na.action = na.omit, data=training_only)
varImpPlot(randfor)
summary(randfor)
memory.limit(100000)  #needed for larger stacks
randfor.map<- predict(stack_analyze, randfor, type="class", index=1, na.rm=TRUE, inf.rm=TRUE) # Long

#write output raster (quick because all integers)
writeRaster(randfor.map, filename = file.path(outdir, output_name), format="GTiff", overwrite=TRUE)



###### Pt2 Accuracy Assessment of a single classification ######
names(validation_df_final)<-c('LC_truth', 'coords.x1','coords.x2')
validation_coords<-validation_df_final[,c('coords.x1','coords.x2')]
validation_extract <-extract(randfor.map, validation_coords)
accuracy_df <-data.frame(validation_df_final, validation_extract)
accuracy_df<- accuracy_df[,c('LC_truth','validation_extract')]

val_total<-nrow(accuracy_df)
val_correct<-nrow(accuracy_df[accuracy_df$LC_truth==accuracy_df$validation_extract,])
overall_accuracy<- (val_correct/val_total)*100
print(paste0("Overall Accuracy:",overall_accuracy, "%"))

#Individual accuracies
truth_vec<-factor(accuracy_df$LC_truth)
classified_vec<-factor(accuracy_df$validation_extract)
accuracy_matrix<-confusionMatrix(data = classified_vec, reference = truth_vec)
table(classified_vec,truth_vec)



