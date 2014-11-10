#! /usr/bin/python
# -*- coding: latin1 -*-

"""
Converts and reprojects a GDAL readable dataset to the data model.

Module for reading a GDAL compatible raster file and exporting it to the data model that is
consisting of the following files: numpy data array, coordinate metadata xml file
and NCML NetCDF XML file.
Data is considered as grid, therefore the shape of the output numpy array is:
(variable, time, z, lat, lon). Find more information in the documentation.

Modified for data: TIBET_LAI_Products_2008-2010_BNU
"""

__author__= "Nicolai Holzer"
__author_email__ = "first-name dot last-name @ mailbox.tu-dresden.de"
__date__ ="2011-04-18"
__version__ = "v0.1.4" #MajorVersion(backward_incompatible).MinorVersion(backward_compatible).Patch(Bug_fixes)


#Changelog
#-------------------------------------------------------------------------------
#2001-04-18: v0.1.4 little changes for new data conversions: LAI, and little changes for NcML attributes
#2011-01-14: v0.1.3 logging implemented, functionalities changed
#2010-12-14: v0.1.2 parser added, functionalities changed
#2010-11-22: v0.1.1 comments and docstrings added
#2010-11-10: v0.1.0 first version


#Imported libraries
#-------------------------------------------------------------------------------
#standard libraries
from decimal import * #Needed for data conversion from sting to float list
import sys
import struct
from optparse import OptionParser #Parser
import logging

#related libraries
import numpy

try: #Import GDAL
    from osgeo import gdal
    from osgeo.gdalconst import *
    gdal.TermProgress = gdal.TermProgress_nocb
except ImportError:
    import gdal
    from gdalconst import *

#local applications / library specific import
from interface_Settings import *
from interface_ProcessingTools import *
from etc.progressBar import * #needs empty '__init__.py' file in directory

#===============================================================================

#Module constants (Parser)
#-------------------------------------------------------------------------------
USAGE = "%prog [options] operation data\
    \n[options]:\
    \n    type '--help' for more information\
    \n\
    \noperation:\
    \n    - reproject       Reproject image to defined projection and extend\
    \n    - gdal2Model      Convert GDAL raster image file to data model\
    \n    - printGdal       Read GDAL file and print it on screen\
    \n\
    \ndata:\
    \n    Raster data file that is readable by the GDAL library"

DESCRIPTION= "Conversion tool of CEOP-AEGIS data model for GDAL readable raster data"
EPILOG = "Author: "+__author__+" (E-mail: "+__author_email__+")"

VERSION = "%prog version "+__version__+" from "+__date__


#Module default values / constants, may be overwritten by OptionParser
#-------------------------------------------------------------------------------
NUMPYDATA_DTYPE = '' #'float32' #Default data type of output numpy array, if set to ''
    #use datatype of GDAL dataset instead
NODATA = '' #0 #Default nodata value of output numpy array, if set to ''
    #use nodata value of GDAL dataset instead


DECLARATION_GDAL_REPROJECTION = '_repr.' #String to set in filename of reprojected file

#XDim = 2516 YDim = 1752 UpperLeftPointMtrs = (-1698240.9147396, 1341366.2807033)
#Layer spatial reference: +proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs
#Projected Coordinate System: 'Asia_North_Albers_Equal_Area_Conic Projection: Albers False_Easting: 0,0 False_Northing: 0,0 Central_Meridian: 95,0
#Standard_Parallel_1: 15,0 Standard_Parallel_2: 65,0 Latitude_Of_Origin: 30,0 Linear Unit: Meter Geographic Coordinate System: GCS_WGS_1984
#Datum: D_WGS_1984 Prime Meridian: Greenwich Angular Unit: Degree'
INGEOTRANS = [73, 0.15, 0, 39.0, 0, -0.13]#[-1698240.9147396, 1, 0, 1341366.2807033, 0, 1] #[lonMin, pixelSizeX, 0, latMax, 0, pixelSizeY]
PROJECTION_INPUT=  'PROJCS[" Projection Name = Albers Conical Equal Area Units = meters,\
GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.2572235629972,AUTHORITY["EPSG","7030"]],\
AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]],\
PROJECTION["Albers_Conic_Equal_Area"],PARAMETER["standard_parallel_1",15],PARAMETER["standard_parallel_2",65],\
PARAMETER["latitude_of_center",30],PARAMETER["longitude_of_center",100],PARAMETER["false_easting",4000000],\
PARAMETER["false_northing",1000000],UNIT["metre",1,AUTHORITY["EPSG","9001"]]]'


PROJECTION_DATAMODEL = 'GEOGCS["WGS 84", DATUM["WGS_1984", \
    SPHEROID["WGS 84",6378137,298.2572235629972, AUTHORITY["EPSG","7030"]], AUTHORITY["EPSG","6326"]], \
    PRIMEM["Greenwich",0], UNIT["degree",0.0174532925199433], AUTHORITY["EPSG","4326"]]' #Data model projection

LAT_MIN = 26.52
LAT_MAX = 39.60
LON_MIN = 73.46
LON_MAX = 104.37
EXTEND = [LAT_MIN, LAT_MAX, LON_MIN, LON_MAX]

RASTER_XSIZE = 2516
RASTER_YSIZE = 1752


MODULE_LOGGER_ROOT = 'gdal' #Logger root name



#_______________________________________________________________________________

class ControlModelGdal:
    """Control class for model 'ModelGdal'. This class is providing all available functions for reading data"""

    def __init__(self, infile_, option_):
        """
        Constructor for new control instance of specific file.

        INPUT_PARAMETERS:
        infile      - name of data file including filename extension (string)
        option      - Parser.options arguments

        COMMENTS:
        Suffixes will be automatically assigned and must respect the declarations
        in the module 'interface_Settings'.
        """

        infile = str(infile_).rsplit('__',1)
        self.inputFile = infile[0]

        self.pModelGdalRead = ModelGdalRead(self.inputFile)

        self.pParserOptions = option_

        self.pParserOptions = option_
        self.pLogger = logging.getLogger(MODULE_LOGGER_ROOT+"."+__name__+"."+self.__class__.__name__)
        self.pLogger.info("Open project '" + self.inputFile + "':")


    #def __del__(self):
        #"""Desctructor"""
        

    def reprojectImage(self):
        """Reproject image bands to defined projection PROJECTION_DATAMODEL and extend"""
        self.pModelGdalRead.gdalFileReprojection(self.pParserOptions.extendList, self.pParserOptions.rasterSizeList, \
            self.pParserOptions.bandNumber, self.pParserOptions.nodataValue)

        return


    def writeGdalNumpyData(self):
        """Read GDAL file and save data as numpy data array according to the specifications
        of the data interface"""

        #Make a copy of the GDAL-file as numpy file
        pGdalData = self.pModelGdalRead.readGdalFile(self.pParserOptions.bandDim, \
            self.pParserOptions.bandNumber, self.pParserOptions.dataType)

        #Export data as new numpy file
        self.pModelGdalRead.writeNumpyData(pGdalData)

        return


    def writeGdalMetadata(self):
        """Get metadata from a GDAL readable file and write metadata to coordinate metadata file and
        NCML XML file according to the specifications of the data interface"""

        self.pModelGdalRead.writeMetadataNcml()
        self.pModelGdalRead.writeMetadataNumpymeta()
        return


    #optional
    def completeDataModelManually(self):
        """Complete missing data and metadata manually"""

        self.pModelGdalRead.completeDataVariables()
        self.pModelGdalRead.completeMetadataNcml()
        self.pModelGdalRead.completeMetadataNumpymeta()
        return


    #optional
    def printGdalMetadata(self):
        """Read GDAL readable file and print metadata on screen"""

        self.pModelGdalRead.printGdalMetadata(self.pParserOptions.bandNumber, self.pParserOptions.noPrintData)
        return


#_______________________________________________________________________________

class ModelGdalRead:
    """This class contains functions to handle read operations on GDAL data and is controlled by
    the class 'ControlModelGdal'"""


    def __init__(self, infile_):
        """
        Constructor.

        INPUT_PARAMETERS:
        infile        - name of GDAL file name with filename extension (string)
        """
        self.pDefaultSettings = DefaultSettings()

        self.gdalFileName = infile_ #With file name extension
        
        infile = self.gdalFileName.rsplit('.',1) #without file name extension

        #Hack to remove additional point characters from filename
        #infile = infile[0].replace('.','')

        self.numpyDataName = infile[0]+FILENAME_SUFFIX_NUMPYDATA
        self.ncmlName = infile[0]+FILENAME_SUFFIX_NCML
        self.numpymetaName = infile[0]+FILENAME_SUFFIX_NUMPYXML

        #Use Processing Tools
        self.pProcessingTool = ProcessingTool()
        self.pProcessNcml = ProcessNcml(self.ncmlName)
        self.pProcessNumpymeta = ProcessNumpymeta(self.numpymetaName)

        self.pLogger = logging.getLogger(MODULE_LOGGER_ROOT+"."+__name__+"."+self.__class__.__name__)

        #Loading GDAL
        gdal.AllRegister() #Register all drivers
        #Not only physical files, but almost anything can be opened (e.g. URL, ...)
        self.pDataset = gdal.Open(self.gdalFileName, GA_ReadOnly )
        if self.pDataset is None: #gdal.Open returns None when open failed
            raise Exception ("Opening of file '" + str(self.gdalFileName) + "' failed. Check if it exists and if filename suffix is set.")
            

    def __del__(self):
        """Destructor"""
        self.pDataset = None


    def gdalFileReprojection(self, extend_, rasterSize_, bandNumber_, nodata_):
        """
        Reproject image file to defined projection PROJECTION_DATAMODEL

        Reproject image file (or defined image bands from 1 to 'bandNumber') to the defined
        extend and to the defined projection PROJECTION_DATAMODEL at the defined raster size.

        INPUT_PARAMETERS:
        extend          - Extend for 'reprojection': LatMin, LatMax, LonMin, LonMax (float)
        rasterSize      - Rastersize for 'reprojection': Y-Rastersize, X-Rastersize (integer)
        bandNumber      - Output image file will contain input band numbers from 1 to 'bandNumber';
            if bandNumber is 'None', all bands will be reprojected (integer)
        noData          - Set nodata value (default = NODATA, if default = '' then Dataset nodata value)" (number)

        RETURN_VALUE:
        Reprojected image file
        """
       
        #Get input dataset settings
        #-------------------------------------------------------------------------------
        pDriver = gdal.GetDriverByName(self.pDataset.GetDriver().ShortName)

        infile = self.gdalFileName.rsplit('.',1) #Get filename without file extension (e.g. '.tif')

        #Define what bands should be used (from 1 to bandNumber, or all bands if bandNumber is None)
        bands = self.__getBandNumber(bandNumber_)
        if bands == self.pDataset.RasterCount: #Reproject all bands = complete file
            outFileName = infile[0]+'_all'+DECLARATION_GDAL_REPROJECTION+infile[1]
        else: #Reproject bands from 1 to 'bandNumber'
            outFileName = infile[0]+'_b1to'+str(bands)+DECLARATION_GDAL_REPROJECTION+infile[1]

        #Get extend and RasterSize (size of image) from arguments
        latMin = extend_[0]
        latMax = extend_[1]
        lonMin = extend_[2]
        lonMax = extend_[3]

        rasterYSize = rasterSize_[0]
        rasterXSize = rasterSize_[1]

        #Positiv pixelSizeX and negative PixelSizeY since origin is upper left corner
        pixelSizeY = float((float(latMax - latMin)/float(rasterYSize))*-1.0)
        pixelSizeX = float(float(lonMax - lonMin)/float(rasterXSize))
        
        #inGeoTrans = self.pDataset.GetGeoTransform() #Wrong since pixel size is in unit of input data file projection (e.g meter instead of degree)
        #pixelSizeY = inGeoTrans[5]
        #pixelSizeX = inGeoTrans[1]

        #!!! Weird order for GetGeoTransform: Order for [4] and [5] are swapped!
        outGeoTrans = [lonMin, pixelSizeX, 0, latMax, 0, pixelSizeY]

        #Datatype of output file = Datatype of first band of input file, Dataset.AddBand() does not work for all drivers
        firstBand = self.pDataset.GetRasterBand(1)
        inputDataType = gdal.GetDataTypeName(firstBand.DataType)
        outputDataType = self.pProcessingTool.dataType_2Gdal(inputDataType)


        #Create ouput file with defined settings, partly derived from input data
        #-------------------------------------------------------------------------------
        #Not usefull here: driver.CreateCopy( dst_filename, src_ds, 0, [ 'TILED=YES', 'COMPRESS=PACKBITS' ] )

        #Due to keyword argument for type, no string in argument can be delivered to function
        if outputDataType == 'GDT_Byte':
            pOutDataset = pDriver.Create(outFileName, rasterXSize, rasterYSize, bands, GDT_Byte)
        elif outputDataType == 'GDT_UInt16':
            pOutDataset = pDriver.Create(outFileName, rasterXSize, rasterYSize, bands, GDT_UInt16)
        elif outputDataType == 'GDT_Int16':
            pOutDataset = pDriver.Create(outFileName, rasterXSize, rasterYSize, bands, GDT_Int16)
        elif outputDataType == 'GDT_UInt32':
            pOutDataset = pDriver.Create(outFileName, rasterXSize, rasterYSize, bands, GDT_UInt32)
        elif outputDataType == 'GDT_Int32':
            pOutDataset = pDriver.Create(outFileName, rasterXSize, rasterYSize, bands, GDT_Int32)
        elif outputDataType == 'GDT_Float32':
            pOutDataset = pDriver.Create(outFileName, rasterXSize, rasterYSize, bands, GDT_Float32)
        elif outputDataType == 'GDT_Float64':
            pOutDataset = pDriver.Create(outFileName, rasterXSize, rasterYSize, bands, GDT_Float64)
        else:
            raise Exception("Error data type conversion input/output before reprojection. GDAL data type not know. Valid data types are: " + str(GDAL_DTYPES) + "'.")
        
        pOutDataset.SetGeoTransform(outGeoTrans) # #pOutDataset.SetGeoTransform(self.pDataset.GetGeoTransform())
        pOutDataset.SetProjection(PROJECTION_DATAMODEL) # #pOutDataset.SetProjection(self.pDataset.GetProjection())


        self.pLogger.debug("Settings for created output data file '" + str(outFileName) + "' from band 1 to band '" + str(bands) + "':")

        #Set nodata value for each band
        #-------------------------------------------------------------------------------
        for cnBand in range(1, pOutDataset.RasterCount + 1, 1): #For all bands
            pOutBand = pOutDataset.GetRasterBand(cnBand) #GetRasterBand is 1-based index
            pInBand = self.pDataset.GetRasterBand(cnBand) #GetRasterBand is 1-based index
            if not nodata_ == '': #if Parser.nodataValue is set or if default NODATA != '' then use this value
                if outputDataType in ALL_INTS: #Type conversion vor nodata value necessary
                    pOutBand.SetNoDataValue(int(Decimal(nodata_)))# Hack to convert negativ values to ints
                else:
                    pOutBand.SetNoDataValue(float(nodata_))
            elif not pInBand.GetNoDataValue() is None: #use Dataset nodata value if there is a value
                pOutBand.SetNoDataValue(pInBand.GetNoDataValue())
            else:
                self.pLogger.warning("No valid nodata value can be set. Got input value: '" + str(nodata_) + "'. Chose nodata value with -n option")

            self.pLogger.debug("Set nodata value for band # '" + str(cnBand) + "' to value '" + str(pOutBand.GetNoDataValue()) + "'")

        self.pLogger.debug("Driver: '" + str(pDriver.ShortName) + "'")
        self.pLogger.debug("Pixel size (x/y): '" + str(pixelSizeX) + "' / '" + str(pixelSizeY) + "'")
        self.pLogger.debug("GDAL Geo-transformation output parameter: '" + str(outGeoTrans) + "'")
        self.pLogger.debug("Raster size (x/y): '" + str(rasterXSize) + "' / '" + str(rasterYSize) + "'")
        self.pLogger.debug("Projection: '" + str(PROJECTION_DATAMODEL) + "'")


        #Set parameters of LAI input dataset manually
        #-------------------------------------------------------------------------------
        self.pDataset.SetGeoTransform(INGEOTRANS)
        self.pLogger.debug("Transformation parameters for input dataset manually set to: '" + str(self.pDataset.GetGeoTransform()) + "'")

        if self.pDataset.GetProjection() == '':
            self.pDataset.SetProjection(PROJECTION_INPUT)
            self.pLogger.debug("No projection available for input dataset. Set to: '" + str(self.pDataset.GetProjection()) + "'")



        #Reproject input dataset to output dataset
        #-------------------------------------------------------------------------------
        self.pLogger.info("Start to reproject image '" + str(self.gdalFileName) + "' to '" + str(outFileName) + "', please wait...")

        #ReprojectImage(g_in, f_out, src_wkt, dst_wkt)
        gdal.ReprojectImage(self.pDataset, pOutDataset)

        #Does not yet work in this version of GDAL!
        #gdal.CreateAndReprojectImage(self.pDataset, outFileName, self.pDataset.GetProjection(), PROJECTION_DATAMODEL, pDriver,)

        pOutDataset = None

        self.pLogger.info("Done. Reprojected file save with file name: '" + str(outFileName) + "'")
        
        return


    def readGdalFile(self, bandDim_, bandNumber_, dataType_):
        """
        Reads a GDAL file and returns data as numpy array

        A GDAL dataset contains a list of raster bands all having the same area
        and resolution. Furthermore the dataset contains metadata, a georeferencing
        transform as well as a coordinate system, the size of the raster and other 
        information.

        INPUT_PARAMETERS:
        bandDim         - Define which NetCDF dimension should be represented by GDAL bands (string)
        bandNumber      - Output image file will contain input band numbers from 1 to 'bandNumber';
            if bandNumber is 'None', all bands will be reprojected (integer)
        dataType        - Define output data type of numpy array (string)

        RETURN_VALUE:
        numpy data array with data from GDAL input dataset
        """
        
        #Get GDAL input dataset and define settings
        #-------------------------------------------------------------------------------
        
        #Set data type for output numpy array
        firstBand = self.pDataset.GetRasterBand(1)
        if not dataType_ == '': #if Parser.dataType is set or if default NUMPY_DATATYPE != '' then use this value
            pDataType = self.pProcessingTool.dataType_2Numpy(dataType_) #Convert to numpy dtype
        elif not gdal.GetDataTypeName(firstBand.DataType) is None: #use Dataset type value if there is a type available
            pDataType = self.pProcessingTool.dataType_2Numpy(gdal.GetDataTypeName(firstBand.DataType)) #Convert to numpy dtype
        else:
            raise Exception("Error: No valid data type can be set. Input value is: '" + str(dataType_) + "'")

        #Define what bands should be used (from 1 to bandNumber, or all bands if bandNumber is None)
        bands = self.__getBandNumber(bandNumber_)

        #Define what numpy (NetCDF) dimension should correspond to input bands (self.pDataset.RasterCount)
        dimY = int(self.pDataset.RasterYSize) #Last but one axis top to bottom: lat -> row
        dimX = int(self.pDataset.RasterXSize)  #Last axis left to right: lon -> col
       
        if bandDim_ == 'var':
            pDocGradsNumpy = numpy.zeros([int(bands), int(1), int(1), dimY, dimX], dtype = pDataType)
        elif bandDim_ == 'time':
            pDocGradsNumpy = numpy.zeros([int(1), int(bands), int(1), dimY, dimX], dtype = pDataType)
        elif bandDim_ ==  'height':
            pDocGradsNumpy = numpy.zeros([int(1), int(1), int(bands), dimY, dimX], dtype = pDataType)
        else:
            raise Exception("Error: Value of bandDim argument not allowed. Valid values are 'var', 'time' or 'height'" )
               

        #Read input dataset and save it to numpy file
        #-------------------------------------------------------------------------------
        #Easiest and best technique for data reading is line per line. Better would be block size reading.
        #Reading one pixel at a time is inefficient. Reading the entire image at once is most efficient, but can cause
        #problems if RAM is not sufficient.

        for cnBand in range(1, bands + 1, 1): #For all bands defined
            pInBand = self.pDataset.GetRasterBand(cnBand) #GetRasterBand is 1-based index

            for cnRow in range(pInBand.YSize -1, -1, -1): #Each row in file, Y origin is on upper left in GDAL!

                #DimRowCount must run in inverse order as cnRow (from lower left to upper left) because of Y origin
                dimRowCn = pInBand.YSize - 1 - cnRow

                #scanline = pInBand.ReadAsArray(0, cnRow, pInBand.XSize, 1, \
                #                    pInBand.XSize, 1, GDT_Float32 )
                #data = GdalRasterBand.ReadRaster(int nXOffset, int nYOffset, int nXSize, int nYSize, \
                    #int nBuffXSize, int nBuffYSize, GdalDataType eBufType, int nPixelSpace, int nLineSpace)
                scanline = pInBand.ReadRaster( 0, cnRow, pInBand.XSize, 1, \
                                     pInBand.XSize, 1, GDT_Float32 )

                #Convert data and cast to numpy data array

                #To unpack use IEEE 754 binary32 (for 'f') or binary 64 (for 'd') format
                scanline_tupleOfFloats = struct.unpack('f' * pInBand.XSize, scanline)# convert data to Python values

                scanline_numpy = numpy.asarray(scanline_tupleOfFloats)

                if bandDim_ == 'var':
                    pDocGradsNumpy[cnBand-1,0,0,dimRowCn,:] = scanline_numpy.astype(pDataType) #cnBand - 1 because of 1-based index
                elif bandDim_ == 'time':
                    pDocGradsNumpy[0,cnBand-1,0,dimRowCn,:] = scanline_numpy.astype(pDataType) #cnBand - 1 because of 1-based index
                elif bandDim_ ==  'height':
                    pDocGradsNumpy[0,0,cnBand-1,dimRowCn,:] = scanline_numpy.astype(pDataType) #cnBand - 1 because of 1-based index
                else:
                    raise Exception("Error: Value of bandDim argument ('" + str(bandDim_) + "') not allowed. Valid values are 'var', 'time' or 'height'")

                #gdal.TermProgress(float(pInBand.YSize-cnRow) / pInBand.YSize)
              
            gdal.TermProgress(1-(float(self.pDataset.RasterCount - cnBand) / self.pDataset.RasterCount))

        return pDocGradsNumpy


    def writeNumpyData(self, pNumpyData_):
        """Export numpy data array to file"""

        self.pLogger.info("Numpy output will be file saved as '"+ str(self.numpyDataName) + "'...")
        numpy.save(str(self.numpyDataName), pNumpyData_) #Better as 'tofile'. Also possible: 'dump'
        self.pLogger.info("Done. Shape of resulting numpy file: '" + str(pNumpyData_.shape) + "'; Data type: '" + str(pNumpyData_.dtype) + "'.")
        
        return


    def writeMetadataNcml(self):
        """Create new NCML XML file according to the specifications of the data model and
        complete this file by the metadata that can be extracted out of input metadata"""
    
        #Get metadata information from file
        #-------------------------------------------------------------------------------
        pNumpyData = numpy.load(self.numpyDataName)
        dimVar = pNumpyData.shape[0] #Number of variables in array

        #Define progress bar settings
        widgetsBar = ['Creating Ncml metadata file: ', Percentage(), ' ', Bar(marker=RotatingMarker()),
                   ' ', ETA(), ' ', FileTransferSpeed()]
        progressBar = ProgressBar(widgets=widgetsBar, maxval=dimVar).start()

        #Write metadata NCML file
        #-------------------------------------------------------------------------------
        self.pProcessNcml.createMacroNcmlFile()
        self.pProcessNcml.fillNcmlMacroWithNumpy(pNumpyData)

        #Correct and complete entries
        for i_var in range(0,dimVar,1): # otherwise returns list of ints from >= start and < end: 0 .. 10
            pInBand = self.pDataset.GetRasterBand(i_var+1) #GetRasterBand is 1-based index
            varName = 'variable #'+str(i_var)
            
            if not pInBand.GetNoDataValue() is None: #use Dataset nodata value if there is a value
                self.pProcessNcml.changeLocalAttribute(varName, '_FillValue', 'value', str(pInBand.GetNoDataValue()))
            else:
                self.pProcessNcml.changeLocalAttribute(varName, '_FillValue', 'value', str(None))

            progressBar.update(i_var+1)# Progress bar

        return


    def writeMetadataNumpymeta(self):
        """Create new metadata coordinate XML file according to the specifications of the data model and
        complete this file by the metadata that can be extracted out of the grib file"""

        geoTransform = self.pDataset.GetGeoTransform()
        if not geoTransform is None: #Coordinates are top left corners of pixels (unlike Imagine which uses centers)
            if (geoTransform[2] == 0 and geoTransform[2] == 0): #Rotation x, y (0 if image is "north-up")
                latMin = geoTransform[3]+ (self.pDataset.RasterYSize * geoTransform[5]) #latMax + (nrLatPixels * pixelSizeLat)
                latMax = geoTransform[3] #Origin y upper left corner!
                lonMin = geoTransform[0] #Origin x upper left corner!
                lonMax = geoTransform[0]+ (self.pDataset.RasterXSize * geoTransform[1]) #lonMin + (nrLonPixels * pixelSizeLon)
            else:
                raise Exception("Error: Image is rotated and not 'north-up'. No rotation is allowed.")
        
            #Write coordinate metadata file
            #-------------------------------------------------------------------------------
            self.pProcessNumpymeta.createMacroNumpymetaFile()

            self.pProcessNumpymeta.setAttribute('numpymeta', 'latitude', 'min', str(latMin))
            self.pProcessNumpymeta.setAttribute('numpymeta', 'latitude', 'max', str(latMax))
            self.pProcessNumpymeta.setAttribute('numpymeta', 'longitude', 'min', str(lonMin))
            self.pProcessNumpymeta.setAttribute('numpymeta', 'longitude', 'max', str(lonMax))

        else:
            self.pLogger.warning("No coordinate information can be written to coordinate metadata file since no coordinate information is available GDAL dataset!")

        return


    #Other functions
    #-------------------------------------------------------------------------------

    def printGdalMetadata(self, bandNumber_, noPrintData_):
        """Read GDAL file and print metadata on screen. Program code derived and adapted from
        GDAL tutorial: http://www.gdal.org/gdal_tutorial.html"""

        #Getting pDataset information
        #-------------------------------------------------------------------------------
        self.pLogger.info("Driver: '" + str(self.pDataset.GetDriver().ShortName) + "'/'" + str(self.pDataset.GetDriver().LongName) + "'")
        self.pLogger.info("Size (x*y*z): '" + str(self.pDataset.RasterXSize) + "'*'" + str(self.pDataset.RasterYSize) + \
            "'*'" + str(self.pDataset.RasterCount) + "'")
        self.pLogger.info("Projection: " + str(self.pDataset.GetProjection()) + "'")


        geoTransform = self.pDataset.GetGeoTransform()
        if not geoTransform is None: #Coordinates are top left corners of pixels (unlike Imagine which uses centers)
            self.pLogger.info("Origin x, y = ('" + str(geoTransform[0]) + "','" + str(geoTransform[3]) + "')")
            self.pLogger.info("Pixel Size = ('" + str(geoTransform[1]) + "','" + str(geoTransform[5]) + "')")
            self.pLogger.info("Rotation x, y (0 if image is 'north-up') = ('" + str(geoTransform[2]) + "','" + str(geoTransform[4]) + "')")

        #GeoTransform[0] /* top left x */
        #GeoTransform[1] /* w-e pixel resolution */
        #GeoTransform[2] /* rotation, 0 if image is "north up" */
        #GeoTransform[3] /* top left y */
        #!!!GeoTransform[4] /* rotation, 0 if image is "north up" */
        #!!!GeoTransform[5] /* n-s pixel resolution */


        #Fetching a raster band. Access is done one band at a time from 1 through Dataset.RasterCount
        #-------------------------------------------------------------------------------
        bands = self.__getBandNumber(bandNumber_)
        for cnBand in range(1, bands + 1, 1): #For all bands defined
            band = self.pDataset.GetRasterBand(cnBand)
            self.pLogger.info("-  -  -")
            self.pLogger.info("Band Number = '" + str(cnBand) + "'")
            self.pLogger.info("Band Type = '" + str(gdal.GetDataTypeName(band.DataType)) + "'")

            minValue = band.GetMinimum()
            maxValue = band.GetMaximum()
            if minValue is None or maxValue is None: #use 'is' statement only for None, 'is' is identity (memory), not equality
                (minValue, maxValue) = band.ComputeRasterMinMax(1)
            self.pLogger.info("Minimum value = '" + str(minValue) + "', Maximum value = '" + str(maxValue) + "'")

            if band.GetOverviewCount() > 0:
                self.pLogger.info("Band has '" + str(band.GetOverviewCount()) + "' overviews.")

            if not band.GetRasterColorTable() is None: #use 'is' statement only for None, 'is' is identity (memory), not equality
                self.pLogger.info("Band has a color table with '" + str(band.GetRasterColorTable().GetCount()) + "' entries.")

            #Reading raster data
            #-------------------------------------------------------------------------------
            if noPrintData_ is False:
                #GdalRasterBand.ReadRaster(int nXOffset, int nYOffset, int nXSize, int nYSize, \
                    #int nBuffXSize, int nBuffYSize, GdalDataType eBufType, int nPixelSpace, int nLineSpace)

                #Returned data of type string contains xsize*4bytes of raw binary floating point data
                scanLine = band.ReadRaster( 0, 0, band.XSize, 1, band.XSize, 1, GDT_Float32 )
                tupleOfFloats = struct.unpack('f' * band.XSize, scanLine)# convert data to Python values
                self.pLogger.info("Data: ")
                self.pLogger.info(tupleOfFloats)

        return


    def __getBandNumber(self, bandNumber_):
        """Define what bands should be used (from 1 to bandNumber, or all bands if bandNumber is None)"""

        if bandNumber_ is None: #All bands = complete file
            return int(self.pDataset.RasterCount)
        else: #Bands from 1 to 'bandNumber'
            if bandNumber_ > self.pDataset.RasterCount:
                raise Exception("Band number must be lower as '" + str(self.pDataset.RasterCount) + "' (is: '" + str(bandNumber_) + "')")
            else:
                return bandNumber_


    #Data specific functions
    #-------------------------------------------------------------------------------

    def completeDataVariables(self):
        """Complete missing data variable value modification manually

        Example: Scale data values in case that units prefix have to be changed
        (e.g. from hPa to Pa) due to defined unit in standard_name entry."""

        #pGdalData = numpy.load(self.numpyDataName)
        #--> Nothing to complete at the moment
        #numpy.save(self.numpyDataName, pGdalData) #Better then 'tofile'. Also possible: 'dump'

        return

   
    def completeMetadataNcml(self):
        "Complete missing data in NCML XML file manually"
        
        self.pProcessNcml.changeGlobalAttribute('title', 'value', 'Tibet LAI')
        self.pProcessNcml.changeGlobalAttribute('source', 'value', 'No information available')
        self.pProcessNcml.changeGlobalAttribute('references', 'value', 'No information available')
        self.pProcessNcml.changeGlobalAttribute('comment', 'value', 'No information available')
        
        self.pProcessNcml.changeLocalAttribute(str(self.pDefaultSettings.axisHeightName), 'units', 'value', '1') #'Level' is not conform to udunits!
        self.pProcessNcml.changeLocalAttribute(str(self.pDefaultSettings.axisHeightName), 'long_name', 'value', 'level')
###############Define Standard Name!
        #self.pProcessNcml.changeLocalAttribute(str(self.pDefaultSettings.axisHeightName), 'standard_name', 'value', '???')
        self.pProcessNcml.removeLocalAttribute(str(self.pDefaultSettings.axisHeightName), 'standard_name')

        self.pProcessNcml.changeVariable('variable #0', 'name', 'LAI_1km')
        self.pProcessNcml.changeLocalAttribute('LAI_1km', 'units', 'value', '1')
        self.pProcessNcml.changeLocalAttribute('LAI_1km', 'long_name', 'value', 'Tibet LAI')
        self.pProcessNcml.changeLocalAttribute('LAI_1km', '_FillValue', 'value', '255')
        #self.pProcessNcml.addLocalAttribute('LAI_1km', 'comment', '0 = no data, 1 = not flooded, 2 = wet, 3 = flooded', "","")
###############Define Standard Name!
        #self.pProcessNcml.changeLocalAttribute('LAI_1km', 'standard_name', 'value', '???')
        self.pProcessNcml.removeLocalAttribute('LAI_1km', 'standard_name')
        self.pProcessNcml.addLocalAttribute('LAI_1km', 'scale_factor', '0.1', 'float32', '')
        #self.pProcessNcml.addLocalAttribute('LAI_1km', 'valid_range', '0,100', 'float32', ',')
        self.pProcessNcml.addLocalAttribute('LAI_1km', 'valid_min', '0', 'float32', '')
        self.pProcessNcml.addLocalAttribute('LAI_1km', 'valid_max', '100', 'float32', '')
    
        return


    def completeMetadataNumpymeta(self):
        "Complete missing data in metadata coordinate XML file manually"

        #-------------------------------------------------------------------------------
        #Hack to obtain a conformal time value from the file name that is present in the form 'TIBET_LAI.A2008001.hdf'
        #This hack converts from the file name the year value and the day of year value to a conformal date (day/month/year)
        #Example: Input file name: 'TIBET_LAI.A2008001.hdf'; Ouput date in the form as it is needed: '2008-01-01 00:00:0.0'
        infile = self.gdalFileName.rsplit('_all_repr.',1) #without file name extension '.hdf'
        infile1 = infile[0].split('.A',1) #Delete prefix string 'TIBET_LAI.A'
        infileDate = infile1[1]
        yearFileName = int(infileDate[:4]) #Year
        doiFileName = int(infileDate[4:]) #Day of Year

        from datetime import datetime, timedelta #Needed for date conversion
        dateConformal = datetime(yearFileName,1,1) + timedelta(doiFileName - 1) #output e.g. '2008-01-01 00:00:0.0'
        #-------------------------------------------------------------------------------

        #Reference time of data in NetCDF metadata format, calculate time values
        pTimes = self.pProcessingTool.createTimeValuesNumpy('hours since '+ str(dateConformal), self.pDataset.RasterCount, 24)
        self.pProcessNumpymeta.writeNumpyMetadataValues(pTimes, 'time')  #Either time values or min/max

        self.pProcessNumpymeta.setAttribute('numpymeta', 'height', 'values', str(1))
        self.pProcessNumpymeta.setAttribute('numpymeta', 'height', 'separator', str(','))

        self.pProcessNumpymeta.setAttribute('numpymeta', 'latitude', 'min', str(25.0))
        self.pProcessNumpymeta.setAttribute('numpymeta', 'latitude', 'max', str(43.0))
        self.pProcessNumpymeta.setAttribute('numpymeta', 'longitude', 'min', str(70.0))
        self.pProcessNumpymeta.setAttribute('numpymeta', 'longitude', 'max', str(110.0))

        return


    

#_______________________________________________________________________________

def main():
    """
    Main function.

    This function represents the user interface and is called when the
    program is executed. Start the program by executing it with the following
    statement in your shell to get more information: gdal_2Interface.py --help
    """
    
    startTime = time.time()
    pDefaultSettings = DefaultSettings()

    #Parser definition
    #-------------------------------------------------------------------------------
    pParser = OptionParser(usage=USAGE, version = VERSION, description = DESCRIPTION, epilog = EPILOG)

    pParser.set_defaults(bandNumber = None)
    pParser.set_defaults(completeModel = False)
    pParser.set_defaults(isDoc = False)
    pParser.set_defaults(extendList = EXTEND)
    pParser.set_defaults(logLevel = pDefaultSettings.loggerLevelConsole)
    pParser.set_defaults(nodataValue = NODATA)
    pParser.set_defaults(dataPath = pDefaultSettings.dataDirectory) 
    pParser.set_defaults(rasterSizeList = [RASTER_YSIZE, RASTER_XSIZE])
    pParser.set_defaults(dataType = NUMPYDATA_DTYPE)
    pParser.set_defaults(noPrintData = True)
    pParser.set_defaults(bandDim = 'time')
    

    pParser.add_option('-b', '--band', action = 'store', type = 'int', dest='bandNumber', nargs = 1, help="Bands from 1 to 'input' on that the operation is to be employed (default = %default)")
    pParser.add_option("-c", "--complModel", action="store_true",  dest='completeModel', help="Complete data model by functions particularly written for specific data (default = %default)")
    pParser.add_option("-d", "--doc", action="store_true",  dest='isDoc', help="Give more information by printing docstrings (default = %default)")
    pParser.add_option('-e', '--extend', action = 'store', type ='float', dest='extendList', nargs = 4, help="Extend for 'reprojection': LatMin, LatMax, LonMin, LonMax (default = %default)")
    pParser.add_option('-l', '--log', action = 'store', dest='logLevel', choices = ['debug','info','warning','error','critical'], nargs = 1, help="Minimum level for printing information to the console (default = %default)")
    pParser.add_option('-n', '--nodata', action = 'store', dest='nodataValue', nargs = 1, help="Set nodata value (default = %default, if default = '' then Dataset nodata value)")
    pParser.add_option('-p', '--path', action = 'store', type ='string', dest='dataPath', nargs = 1, help="Directory for input / output files (default = %default)")
    pParser.add_option('-r', '--rastersize', action = 'store', type ='int', dest='rasterSizeList', nargs = 2, help="Rastersize for 'reprojection': Y-Rastersize, X-Rastersize (default = %default)")
    pParser.add_option('-t', '--dtype', action = 'store', dest='dataType', choices = [''] + NUMPY_DTYPES, nargs = 1, help="Define output data type of numpy array (default = %default)")
    pParser.add_option("-v", "--nopvars", action="store_false",  dest='noPrintData', help="Beside metadata print also data variable values on screen (default = %default)")
    pParser.add_option('-z', '--zdim', action = 'store', dest='bandDim', choices = ['var','time','height'], nargs = 1, help="Define which NetCDF dimension should represent the vertical band of the GDAL file (default = %default)")
   
    (options, args) = pParser.parse_args()
    
    
    #Initialize logger
    #-------------------------------------------------------------------------------
    pLog = LoggingInterface(MODULE_LOGGER_ROOT, options.logLevel, pDefaultSettings.loggerLevelFile) #Instance is necessary although if not used.
    pLogger = logging.getLogger(MODULE_LOGGER_ROOT+"."+__name__)
    pLogger.info("_____________________________________________________________________________________________")
    pLogger.info("Starting program 'GDAL2INTERFACE' version '" + str(__version__) + "' from '" + str(__date__) + "':")


    try:

        #Parse command line arguments and options
        #-------------------------------------------------------------------------------
        if len(args) != 2:
            pLogger.error("Parser error occured. See error messages on the screen.")
            pParser.error("Incorrect number of arguments. Two arguments 'operation' and 'data' are nedded. " \
            +str(len(args))+" arguments are given. Execute '%prog --help' for more information")
        else:
            #args = sys.argv[1:]#sys.argv[0] is name of program being executed
            operation_ = args[0]
            infile_ = args[1]


        #Process parser options
        #-------------------------------------------------------------------------------
        if options.isDoc:
            pLogger.info(__doc__)
            sys.exit(0)

        dataPath = options.dataPath
        if not dataPath.endswith('/') and dataPath != '': #Adds '/' to path in case that this is not the case
            dataPath = dataPath+'/'
        infileName = dataPath+infile_ #Add path of data directory to filename


        #Run program
        #-------------------------------------------------------------------------------
        pControlModelGdal = ControlModelGdal(infileName, options)

        if operation_ == 'reproject':
            pLogger.info("Operation: Reproject GDAL file")
            pControlModelGdal.reprojectImage()

        elif operation_ == 'gdal2Model':
            pLogger.info("Operation: Convert GDAL to data model")
            pControlModelGdal.writeGdalNumpyData() #Write numpy data array
            pControlModelGdal.writeGdalMetadata() #Write metadata

            if options.completeModel:
                pControlModelGdal.completeDataModelManually() #Complete data model manually

        elif operation_ == 'printGdal':
            pLogger.info("Operation: Print GDAL data on the screen")
            pControlModelGdal.printGdalMetadata()

        else:
            pLogger.error("Parser error: Operation '" + str(operation_) + "' is unknown.")
            pParser.error("Operation '" + str(operation_) + "' is unknown.") #System exit code 2

            
    except Exception: #If Exceptiation occured in this module or all connected sub-modules
        pLogger.exception('Exception Error occured: ')
        raise

    finally:
        pLogger.info("Finished. Total processing time [s]: '" + str(time.time() - startTime) + "'.")
        pLogger.info("_____________________________________________________________________________________________")
        pLog.__del__()

        #pControlModelGdal.__del__()


if __name__ == "__main__":
      main()