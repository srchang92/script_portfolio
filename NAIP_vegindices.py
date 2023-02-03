# Script for Calculating Spectral Indices from NAIP imagery
# Stephen Chang
# April 15, 2017

import os
import sys
import numpy
import arcpy
import timeit
import time
from arcpy import env
from arcpy.sa import *

timeBegin = timeit.default_timer()             	            # timer start for processing time
timeSt = time.localtime()
print('Start time: '+ time.strftime('%a %b %d %H:%M:%S %Y',timeSt)+'\n')

#root = 'C:\\Users\\whills\\Dropbox\\2.Research\\SRC_capstone\\NAIP' # Beckett's PC
#root = 'B:\\2.Research\\SRC_capstone\\NAIP'
root = 'Y:\\NAIP'  # Stephen's PC
ws = os.path.join(root,'aligned') #made new change here for aligned segments
#wso = 'D:\Workspace_Beckett\NAIPproc' #Beckett's
wso = 'Y:\\NAIP\\aligned\\Indices' #changed location for aligned images
outDir = os.path.join(wso,'2015')
#outDir = os.path.join(root,ws,'Out')
temp = os.path.join(root,'temp')

#imgpath = 'P:\\NAIPimgs\\2015' # Beckett's PC
imgPath = 'Y:\\NAIP\\aligned' # AUK server change made
#imgPath = 'C:\\NAIPimgs\\2015' # Stephen's PC
imgName = 'm_4608961_sw_16_1_20150708-w_snapped' #added new image name
maskPath = os.path.join(ws,'Watermasks 4608961')
maskName = 'watermask.tif'

arcpy.CheckOutExtension('spatial')
env.overwriteOutput = True
arcpy.ClearEnvironment("mask")

os.chdir(root)
arcpy.env.workspace = root
env.scratchWorkspace = temp
env.nodata = 0

mask = Raster(os.path.join(maskPath,maskName))
img = Raster(os.path.join(imgPath,imgName+'.tif'))

BL =  Raster(os.path.join(imgPath,imgName+'.tif','Band_1'))
GR =  Raster(os.path.join(imgPath,imgName+'.tif','Band_2'))
RED =  Raster(os.path.join(imgPath,imgName+'.tif','Band_3'))
NIR =  Raster(os.path.join(imgPath,imgName+'.tif','Band_4'))

# Seg =  Raster('Y:\\NAIP\\workflow4608961sw\\segments\\4608961s2.tif')


compositeList = []
indProcList = []

indProcList.append('BL')
indProcList.append('GR')
indProcList.append('RED')
indProcList.append('NIR')
#indProcList.append('Seg')


compositeList.append(BL)
compositeList.append(GR)
compositeList.append(RED)
compositeList.append(NIR)
#compositeList.append(Seg)


#------------------------------------------------------------#
# NDVI
#------------------------------------------------------------#
# ((NIR - Red) / (NIR + Red))
def NDVI(mask):
    timeStart = timeit.default_timer()
    print('Calculating NDVI...')
    ndvi_out = os.path.join(outDir,imgName+'_NDVI.tif')
    arcpy.env.mask = mask   
    ndviNum = arcpy.sa.Float(NIR - RED)
    ndviDenom = arcpy.sa.Float(NIR + RED)
    NDVI_eq = arcpy.sa.Divide(ndviNum, ndviDenom)
    print('Saving...')
    NDVI_eq.save(ndvi_out)
    print('NDVI saved.')
    indProcList.append('NDVI')
    compositeList.append(NDVI_eq)
    timeEnd = timeit.default_timer()
    print('Layer Processing Time: '+ "{0:.2f}".format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print('\n'+'---------------------------------------------'+'\n')
 
 
#------------------------------------------------------------#
# NDWI
#------------------------------------------------------------#
# ((GR - NIR) / (GR + NIR))
def NDWI(mask):
    timeStart = timeit.default_timer()
    print('Calculating NDWI...')
    ndwi_out = os.path.join(outDir,imgName+'_NDWI.tif')
    arcpy.env.mask = mask   
    ndwiNum = arcpy.sa.Float(GR - NIR)
    ndwiDenom = arcpy.sa.Float(GR + NIR)
    NDWI_eq = arcpy.sa.Divide(ndwiNum, ndwiDenom)
    print('Saving...')
    NDWI_eq.save(ndwi_out)
    print('NDWI saved.')
    indProcList.append('NDWI')
    compositeList.append(NDWI_eq)
    timeEnd = timeit.default_timer()
    print('Layer Processing Time: '+ "{0:.2f}".format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print('\n'+'---------------------------------------------'+'\n')
 

#------------------------------------------------------------#
# GARI GR Atmospherically Resistant Vegetation Index
#------------------------------------------------------------#
# (NIR - ( GREEN - ( BLUE - RED ))) / (NIR - ( GREEN + ( BLUE - RED )))

def GARI(mask):
    timeStart = timeit.default_timer()
    print('Calculating GARI...')
    arcpy.env.mask = mask
    gari_out = os.path.join(outDir,imgName+'_GARI.tif')
    gariNum = arcpy.sa.Float((NIR - (GR - (BL - RED))))
    gariDenom = arcpy.sa.Float((NIR - (GR + (BL - RED))))
    GARI_eq = arcpy.sa.Divide(gariNum, gariDenom)
    print('Saving...')
    GARI_eq.save(gari_out)
    print('GARI saved.')
    indProcList.append('GARI')
    compositeList.append(GARI_eq)
    timeEnd = timeit.default_timer()
    print('Layer Processing Time: '+ "{0:.2f}".format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print('\n'+'---------------------------------------------'+'\n')


#------------------------------------------------------------#
# SAVI Soil Adjusted Vegetation Index
#------------------------------------------------------------#
#(1+ 0.5)*(NIR – RED) / (NIR + RED + 0.5)

def SAVI(mask):
    timeStart = timeit.default_timer()
    print('Calculating SAVI...')
    arcpy.env.mask = mask   
    savi_out = os.path.join(outDir,imgName+'_SAVI.tif')
    savi_prod = arcpy.sa.Float(NIR - RED)
    saviNum = arcpy.sa.Float((Times(savi_prod,1.5)))
    saviDenom = arcpy.sa.Float(NIR + RED +.5)
    SAVI_eq = arcpy.sa.Divide(saviNum,saviDenom)
    print('Saving...')
    SAVI_eq.save(savi_out)
    print('SAVI saved.')
    indProcList.append('SAVI')
    compositeList.append(SAVI_eq)
    timeEnd = timeit.default_timer()
    print('Layer Processing Time: '+ "{0:.2f}".format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print('\n'+'---------------------------------------------'+'\n')  

#------------------------------------------------------------#
# MSAVI Modified Soil Adjusted Vegetation Index
#------------------------------------------------------------#
#((2 * NIR + 1) - Sqrt(((2 * NIR + 1 )^2) - (8 ⁢* ( NIR - RED )))) / 2

def MSAVI(mask):
    timeStart = timeit.default_timer()
    print('Calculating MSAVI...')
    arcpy.env.mask = mask   
    msavi_out = os.path.join(outDir,imgName+'_MSAVI.tif')
    msavi_prod = arcpy.sa.Float(Times(NIR,2) + 1)
    msaviNum = arcpy.sa.Float((Times(NIR,2) + 1) - SquareRoot((Power(msavi_prod,2) - Times(8,(NIR - RED)))))
    MSAVI_eq = arcpy.sa.Divide(msaviNum, 2)
    print('Saving...')
    MSAVI_eq.save(msavi_out)
    print('MSAVI saved.')
    indProcList.append('MSAVI')
    compositeList.append(MSAVI_eq)
    timeEnd = timeit.default_timer()
    print('Layer Processing Time: '+ "{0:.2f}".format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print('\n'+'---------------------------------------------'+'\n')
    

#------------------------------------------------------------#
# GNDVI Green Normalized Difference Vegetation Index
#------------------------------------------------------------#
# (NIR - GR ) / (NIR + GR )

def GNDVI(mask):
    timeStart = timeit.default_timer()
    print('Calculating GNDVI...')
    arcpy.env.mask = mask   
    gndvi_out = os.path.join(outDir,imgName+'_GNDVI.tif')
    gndviNum = arcpy.sa.Float(NIR - GR)
    gndviDenom = arcpy.sa.Float(NIR + GR)
    GNDVI_eq = arcpy.sa.Divide(gndviNum, gndviDenom)
    print('Saving...')
    GNDVI_eq.save(gndvi_out)
    print('GNDVI saved.')
    indProcList.append('GNDVI')
    compositeList.append(GNDVI_eq)
    timeEnd = timeit.default_timer()
    print('Layer Processing Time: '+ "{0:.2f}".format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print('\n'+'---------------------------------------------'+'\n')
    
#------------------------------------------------------------#
# GRVI GR Ratio Vegetation Index
#------------------------------------------------------------#
# NIR / GR

def GRVI(mask):
    timeStart = timeit.default_timer()
    print('Calculating GRVI...')
    arcpy.env.mask = mask   
    grvi_out = os.path.join(outDir,imgName+'_GRVI.tif')
    GRVI_eq = arcpy.sa.Divide(NIR, GR)
    print('Saving...')
    GRVI_eq.save(grvi_out)
    print('GRVI saved.')
    indProcList.append('GRVI')
    compositeList.append(GRVI_eq)
    timeEnd = timeit.default_timer()
    print('Layer Processing Time: '+ "{0:.2f}".format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print('\n'+'---------------------------------------------'+'\n')
    
#------------------------------------------------------------#
# IPVIs Infrared Percentage Vegetation Index (short version)
#------------------------------------------------------------#
# (NIR / ( NIR + RED ))

def IPVIs(mask):
    timeStart = timeit.default_timer()
    print('Calculating IPVIs...')
    arcpy.env.mask = mask   
    ipvis_out = os.path.join(outDir,imgName+'_IPVIs.tif')
    ipvisDenom = arcpy.sa.Float(NIR + RED)
    IPVIs_eq = arcpy.sa.Divide(NIR,ipvisDenom)
    print('Saving...')
    IPVIs_eq.save(ipvis_out)
    print('IPVIs saved.')
    indProcList.append('IPVIs')
    compositeList.append(IPVIs_eq)
    timeEnd = timeit.default_timer()
    compositeList.append(IPVIs_eq)
    timeEnd = timeit.default_timer()
    print('Layer Processing Time: '+ "{0:.2f}".format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print('\n'+'---------------------------------------------'+'\n')


#------------------------------------------------------------#
# IPVI Infrared Percentage Vegetation Index (long version)
#------------------------------------------------------------#
# ((NIR / ( NIR + RED ))/2)*(((NIR - RED)/(NIR + RED))+1)

def IPVI(mask):
    timeStart = timeit.default_timer()
    print('Calculating IPVI...')
    arcpy.env.mask = mask   
    ipvi_out = os.path.join(outDir,imgName+'_IPVI.tif')
    ipvi_denom1 = arcpy.sa.Float(NIR + RED)
    ipvi_num1 = arcpy.sa.Divide(NIR,ipvi_denom1)
    ipvi_prod1 = arcpy.sa.Divide(ipvi_num1,2)
    ipviNum = arcpy.sa.Float(RED - GR)
    ipviDenom = arcpy.sa.Float(RED + GR)
    ipvi_prod2a = arcpy.sa.Divide(ipviNum, ipviDenom)
    ipvi_prod2 = arcpy.sa.Float(ipvi_prod2a + 1)
    IPVI_eq = arcpy.sa.Times(ipvi_prod1,ipvi_prod2)
    print('Saving...')
    IPVI_eq.save(ipvi_out)
    print('IPVI saved.')
    indProcList.append('IPVI')
    compositeList.append(IPVI_eq)
    timeEnd = timeit.default_timer()
    print('Layer Processing Time: '+ "{0:.2f}".format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print('\n'+'---------------------------------------------'+'\n')

    
#------------------------------------------------------------#
# EVI Enhanced Vegetation Index
#------------------------------------------------------------#
#2.5 * (NIR - RED) /( NIR + 6*RED - 7.5*BL  + 1)

def EVI(mask):
    timeStart = timeit.default_timer()
    print('Calculating EVI...')
    arcpy.env.mask = mask   
    evi_out = os.path.join(outDir,imgName+'_EVI.tif')
    EVI_eq = arcpy.sa.Float(2.5 * (NIR - RED) / (NIR + 6 * RED - 7.5 * BL + 1))
    print('Saving...')
    EVI_eq.save(evi_out)
    print('EVI saved.')
    indProcList.append('EVI')
    compositeList.append(EVI_eq)
    timeEnd = timeit.default_timer()
    print('Layer Processing Time: '+ "{0:.2f}".format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print('\n'+'---------------------------------------------'+'\n')


#------------------------------------------------------------#
# MSR Modified Simple Ratio
#------------------------------------------------------------#
# (( NIR / RED ) - 1) / ((Sqrt(NIR/RED) + 1 ))

def MSR(mask):
    timeStart = timeit.default_timer()
    print('Calculating MSR...')
    arcpy.env.mask = mask   
    msr_out = os.path.join(outDir,imgName+'_MSR.tif')
    msr_prod = arcpy.sa.Divide(NIR,RED)
    msrNum = arcpy.sa.Float(msr_prod - 1)
    msr_root = arcpy.sa.SquareRoot(msr_prod)
    msrDenom = arcpy.sa.Float(msr_root + 1)
    MSR_eq = arcpy.sa.Divide(msrNum,msrDenom)
    print('Saving...')
    MSR_eq.save(msr_out)
    print('MSR saved.')
    indProcList.append('MSR')
    compositeList.append(MSR_eq)
    timeEnd = timeit.default_timer()
    print('Layer Processing Time: '+ "{0:.2f}".format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print('\n'+'---------------------------------------------'+'\n')

#------------------------------------------------------------#
# SR Simple Ratio
#------------------------------------------------------------#
# NIR / RED
def SR(mask):
    timeStart = timeit.default_timer()
    print('Calculating SR...')
    arcpy.env.mask = mask   
    srto_out = os.path.join(outDir,imgName+'_SR.tif')
    SRTO_eq = arcpy.sa.Float(arcpy.sa.Divide(NIR, RED))
    print('Saving...')
    SRTO_eq.save(srto_out)
    print('Simple Ratio saved.')
    indProcList.append('SR')
    compositeList.append(SRTO_eq)
    timeEnd = timeit.default_timer()
    print('Layer Processing Time: '+ "{0:.2f}".format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print('\n'+'---------------------------------------------'+'\n')


    
#------------------------------------------------------------#
# Main LOOP
#------------------------------------------------------------#

NDVI(mask)
NDWI(mask)
GARI(mask)
SAVI(mask)
MSAVI(mask)
GNDVI(mask)
GRVI(mask)
IPVIs(mask)
IPVI(mask)
EVI(mask)
MSR(mask)
SR(mask)

 
# Build composite
#------------------------------------------------------------#
print('Building Composite...')
timeCompSt = time.localtime()
print('Composite started: '+ time.strftime('%a %b %d %H:%M:%S %Y',timeCompSt)+'\n')
timeStart = timeit.default_timer()
compositeOut = os.path.join(ws,outDir,imgName+'_indices.tif')
arcpy.CompositeBands_management(compositeList,compositeOut)
for ind in compositeList:
    print ind
print('Composite done.')
timeEnd = timeit.default_timer()
print('Composite Raster Time: '+ "{0:.2f}".format(((timeEnd - timeStart)/60))+' minutes'+'\n')
print('---------------------------------------------'+'\n')

# Rename bands
#------------------------------------------------------------#

print("Renaming bands...")
arcpy.env.workspace = compositeOut
lyrs = arcpy.ListRasters()
for lyr in lyrs:
    band = os.path.basename(str(indProcList[lyrs.index(lyr)]))
    arcpy.Rename_management(lyr, band)
    print lyr,band
arcpy.env.workspace = ws
print('Renaming done.')
print('---------------------------------------------'+'\n\n')

print('Processing Finished.')

timeDone = timeit.default_timer()
print('Total Processing Time: '+ "{0:.2f}".format(((timeDone - timeBegin)/60))+' minutes'+'\n')
timeEd = time.localtime()
print('End Time: '+ time.strftime('%a %b %d %H:%M:%S %Y',timeEd)+'\n')



print('Layer Processing Time: '+ "{0:.2f}".format(((timeEnd - timeStart)/60))+' minutes'+'\n')
print('\n'+'---------------------------------------------'+'\n')


#------------------------------------------------------------#
# IPVI Infrared Percentage Vegetation Index (long version)
#------------------------------------------------------------#
# ((NIR / ( NIR + RED ))/2)*(((NIR - RED)/(NIR + RED))+1)

def IPVI(mask):
    timeStart = timeit.default_timer()
    print('Calculating IPVI...')
    arcpy.env.mask = mask   
    ipvi_out = os.path.join(outDir,imgName+'_IPVI.tif')
    ipvi_denom1 = arcpy.sa.Float(NIR + RED)
    ipvi_num1 = arcpy.sa.Divide(NIR,ipvi_denom1)
    ipvi_prod1 = arcpy.sa.Divide(ipvi_num1,2)
    ipviNum = arcpy.sa.Float(RED - GR)
    ipviDenom = arcpy.sa.Float(RED + GR)
    ipvi_prod2a = arcpy.sa.Divide(ipviNum, ipviDenom)
    ipvi_prod2 = arcpy.sa.Float(ipvi_prod2a + 1)
    IPVI_eq = arcpy.sa.Times(ipvi_prod1,ipvi_prod2)
    print('Saving...')
    IPVI_eq.save(ipvi_out)
    print('IPVI saved.')
    indProcList.append('IPVI')
    compositeList.append(IPVI_eq)
    timeEnd = timeit.default_timer()
    print('Layer Processing Time: '+ "{0:.2f}".format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print('\n'+'---------------------------------------------'+'\n')

    
#------------------------------------------------------------#
# EVI Enhanced Vegetation Index
#------------------------------------------------------------#
#2.5 * (NIR - RED) /( NIR + 6*RED - 7.5*BL  + 1)

def EVI(mask):
    timeStart = timeit.default_timer()
    print('Calculating EVI...')
    arcpy.env.mask = mask   
    evi_out = os.path.join(outDir,imgName+'_EVI.tif')
    EVI_eq = arcpy.sa.Float(2.5 * (NIR - RED) / (NIR + 6 * RED - 7.5 * BL + 1))
    print('Saving...')
    EVI_eq.save(evi_out)
    print('EVI saved.')
    indProcList.append('EVI')
    compositeList.append(EVI_eq)
    timeEnd = timeit.default_timer()
    print('Layer Processing Time: '+ "{0:.2f}".format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print('\n'+'---------------------------------------------'+'\n')


#------------------------------------------------------------#
# MSR Modified Simple Ratio
#------------------------------------------------------------#
# (( NIR / RED ) - 1) / ((Sqrt(NIR/RED) + 1 ))

def MSR(mask):
    timeStart = timeit.default_timer()
    print('Calculating MSR...')
    arcpy.env.mask = mask   
    msr_out = os.path.join(outDir,imgName+'_MSR.tif')
    msr_prod = arcpy.sa.Divide(NIR,RED)
    msrNum = arcpy.sa.Float(msr_prod - 1)
    msr_root = arcpy.sa.SquareRoot(msr_prod)
    msrDenom = arcpy.sa.Float(msr_root + 1)
    MSR_eq = arcpy.sa.Divide(msrNum,msrDenom)
    print('Saving...')
    MSR_eq.save(msr_out)
    print('MSR saved.')
    indProcList.append('MSR')
    compositeList.append(MSR_eq)
    timeEnd = timeit.default_timer()
    print('Layer Processing Time: '+ "{0:.2f}".format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print('\n'+'---------------------------------------------'+'\n')

#------------------------------------------------------------#
# SR Simple Ratio
#------------------------------------------------------------#
# NIR / RED
def SR(mask):
    timeStart = timeit.default_timer()
    print('Calculating SR...')
    arcpy.env.mask = mask   
    srto_out = os.path.join(outDir,imgName+'_SR.tif')
    SRTO_eq = arcpy.sa.Float(arcpy.sa.Divide(NIR, RED))
    print('Saving...')
    SRTO_eq.save(srto_out)
    print('Simple Ratio saved.')
    indProcList.append('SR')
    compositeList.append(SRTO_eq)
    timeEnd = timeit.default_timer()
    print('Layer Processing Time: '+ "{0:.2f}".format(((timeEnd - timeStart)/60))+' minutes'+'\n')
    print('\n'+'---------------------------------------------'+'\n')


    
#------------------------------------------------------------#
# Main LOOP
#------------------------------------------------------------#

NDVI(mask)
NDWI(mask)
GARI(mask)
SAVI(mask)
MSAVI(mask)
GNDVI(mask)
GRVI(mask)
IPVIs(mask)
IPVI(mask)
EVI(mask)
MSR(mask)
SR(mask)

 
# Build composite
#------------------------------------------------------------#
print('Building Composite from ' + str(len(indProcList)) + ' layers')
timeCompSt = time.localtime()
print('Composite started: '+ time.strftime('%a %b %d %H:%M:%S %Y',timeCompSt)+'\n')
timeStart = timeit.default_timer()
compositeOut = os.path.join(ws,outDir,imgName+'_indices.tif')
arcpy.CompositeBands_management(compositeList,compositeOut)
for ind in compositeList:
    print ind
print('Composite done.')
timeEnd = timeit.default_timer()
print('Composite Raster Time: '+ "{0:.2f}".format(((timeEnd - timeStart)/60))+' minutes'+'\n')
print('---------------------------------------------'+'\n')

# Rename bands
#------------------------------------------------------------#
arcpy.env.workspace = compositeOut
lyrs = arcpy.ListRasters()
print('Renaming ' + str(len(lyrs)) + ' bands')
for lyr in lyrs:
    band = os.path.basename(str(indProcList[lyrs.index(lyr)]))
    arcpy.Rename_management(lyr, band)
    print lyr,band
arcpy.env.workspace = ws
print('Renaming done.')
print('---------------------------------------------'+'\n\n')

print('Processing Finished.')

timeDone = timeit.default_timer()
print('Total Processing Time: '+ "{0:.2f}".format(((timeDone - timeBegin)/60))+' minutes'+'\n')
timeEd = time.localtime()
print('End Time: '+ time.strftime('%a %b %d %H:%M:%S %Y',timeEd)+'\n')



