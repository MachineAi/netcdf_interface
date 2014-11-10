#! /usr/bin/python
# -*- coding: latin1 -*-

"""
Model module for Interface.

This module contains classes to handle operation on data and is controlled by
the class 'ControlModel' of the module 'interface_Control'
"""

__author__= "Nicolai Holzer"
__author_email__ = "first-name dot last-name @ mailbox.tu-dresden.de"
__date__ ="2011-04-15"
__version__ = "v0.1.3"


#Changelog
#-------------------------------------------------------------------------------
#2001-04-15: v0.1.3 little changes for new data conversions
#2011-01-05: v0.1.2 logging implemented
#2010-11-23: v0.1.1 comments and docstrings added
#2010-10-08: v0.1.0 first version


#Imported libraries
#-------------------------------------------------------------------------------
#standard libraries
from decimal import *
import os
import xml.dom.minidom as minidom
import logging

#related libraries
import numpy
from netCDF4 import Dataset, num2date, date2num, MFDataset

#local applications / library specific import
from interface_Data import *
from interface_Settings import *
from interface_ProcessingTools import *

#===============================================================================



class ModelMetadataNcmlRead:
    """Class for reading NCML XML metadata"""

    def __init__(self, infile_):
        """
        Constructor.

        INPUT_PARAMETERS:
        infile        - name of NCML file name without suffix (string)
        """

        ncmlFileName = infile_+FILENAME_SUFFIX_NCML
        self.pDocNcml = minidom.parse(ncmlFileName)
        self.pProcessingTool = ProcessingTool()
     
        self.pLogger = logging.getLogger(INTERFACE_LOGGER_ROOT+"."+__name__+"."+self.__class__.__name__)
        

    def __del__ (self):
        """Destructor"""
        self.pDocNcml.unlink()


    def readDimensions(self):
        """Read dimensions in NCML file and return new dimension list"""

        pDocNcml = self.pDocNcml
        pDimList = list()

        for node_Dim in pDocNcml.getElementsByTagName('dimension'):

            if node_Dim.parentNode.nodeName == 'netcdf':

                dimName = node_Dim.getAttribute('name')
                dimLength = node_Dim.getAttribute('length')
                dimIsUnlimited_text = node_Dim.getAttribute('isUnlimited')

                #convert bool in form of string to Python bool (True or False)
                dimIsUnlimited = self.pProcessingTool.convertBool(dimIsUnlimited_text)

                pDim = Dimension(dimName, dimLength, dimIsUnlimited)
                pDimList.append(pDim)

        return pDimList
    

    def readGlobalAttributes(self):
        """Read global attributes in NCML file and return new attribute list"""

        pDocNcml = self.pDocNcml
        pAttrList = list()

        for node_Attr in pDocNcml.getElementsByTagName('attribute'):

            if node_Attr.parentNode.nodeName == 'netcdf':

                attrName = node_Attr.getAttribute('name')
                attrType = node_Attr.getAttribute('type')
                attrValue = node_Attr.getAttribute('value')
                attrSeparator = node_Attr.getAttribute('separator') 

                pAttr = Attribute(attrName, attrType, attrValue, attrSeparator)
                pAttrList.append(pAttr)

        return pAttrList


    def readVariables(self):
        """Read variables and appendent local attributes in NCML file and return new variable list"""

        pDocNcml = self.pDocNcml
        pVarList = list()

        for node_Var in pDocNcml.getElementsByTagName('variable'):

            if node_Var.parentNode.nodeName == 'netcdf':

                varName = node_Var.getAttribute('name')
                varShape = node_Var.getAttribute('shape')
                varType = node_Var.getAttribute('type')

                pVar = Variable(varName, varShape, varType)

                for node_VarAttr in node_Var.getElementsByTagName('attribute'):

                    attrName = node_VarAttr.getAttribute('name')
                    attrType = node_VarAttr.getAttribute('type')
                    attrValue = node_VarAttr.getAttribute('value')
                    attrSeparator = node_VarAttr.getAttribute('separator')

                    pVar.addAttribute(attrName, attrType, attrValue, attrSeparator)

                pVarList.append(pVar)

        return pVarList



#_______________________________________________________________________________

class ModelDataRead:
    """Superclass for reading numpy data array and coordinate metadata file
    as well as checking operations for internal datamodel"""

    def __init__(self, infile_):
        "Constructor"
        
        xmlFileName = infile_+FILENAME_SUFFIX_NUMPYXML
        
        self.pProcessingTool = ProcessingTool()
        self.pProcessNumpymeta = ProcessNumpymeta(xmlFileName)
        self.pDefaultSettings = DefaultSettings()

        self.pLogger = logging.getLogger(INTERFACE_LOGGER_ROOT+"."+__name__+"."+self.__class__.__name__)

        
    #def __del__(self):
        #"""Destructor"""
       

    def getCoordinateVariables(self, pVarList_, dimVar_, dimTime_, dimZ_, dimLat_, dimLon_, dimId_):
        """
        Obtain coordinate information.
        
        Get coordinate information out of coordinate metadata file and calculate coordinate values
        by the use of this information. Attach coordinate values as numpy array to corresponding
        variable in internal model

        INPUT_PARAMETERS:
        pVarList                                        - variable list of internal model
        dimVar, dimTime, dimZ, dimLat, dimLon, dimId    - number of values to generate

        RETURN_VALUE:
        Actualized variable list with coordinate data arrays attached to corresponding variables

        IMPORTANT:
        In case that separate values instead of minimum and maximum values for cpordinates are
        provided, the number of these values must be the same as the shape of the corresponding
        dimension.
        """

        pVarList = pVarList_
        varNumpyNr = 0

        for pVar in pVarList[:]:
            pDataType = self.pProcessingTool.dataType_2Numpy(pVar.getType())

            if pVar.getName() in TIME:
                pTimeNumpy = self.__readNumpyMetadataValues('time', dimTime_, pDataType)
                pVar.addData(pTimeNumpy)

            elif pVar.getName() in HEIGHT:
                pHeightNumpy = self.__readNumpyMetadataValues('height', dimZ_, pDataType)
                pVar.addData(pHeightNumpy)

            elif pVar.getName() in LATITUDE:
                pLatNumpy = self.__readNumpyMetadataValues('latitude', dimLat_, pDataType)
                pVar.addData(pLatNumpy)

            elif pVar.getName() in LONGITUDE :
                pLonNumpy = self.__readNumpyMetadataValues('longitude', dimLon_, pDataType)
                pVar.addData(pLonNumpy)

            elif pVar.getName() in ID: #should be unique value!
                pIdNumpy = self.__readNumpyMetadataValues('id', dimId_, pDataType)
                pVar.addData(pIdNumpy)

            else:
                varNumpyNr = varNumpyNr+1

        if varNumpyNr != dimVar_:
            raise Exception("Error: Inconsistency in number of data variables. Got: '" + str(dimVar_) + "', but calculated: '" + str(varNumpyNr) + "'.")

        return pVarList


    def checkDataModel(self, pDataList_):
        """
        Check if internal data model is correct.
        
        This function checks dimensions as well as coordinate and data variables of a data model if they
        are correct and consistent to each other as they are declared in the NCML and coordinate
        metadata and numpy data array. If no error is found, the NetCDF creation should be successfull
        out of this data modell.

        INPUT_PARAMETERS:
        pDataList       - internal data model
        
        RETURN_VALUE:
        Boolean: True if no error could be found, False if one or more errors were found

        COMMENT:
        This function only checks the correctness of the data model and its consistency so that the
        NetCDF creation out of this data model will be successfull. It does not check if any NetCDF convention is
        respected.
        """

        #Define settings and flags
        #-------------------------------------------------------------------------------
        pDimList = pDataList_[0]
        pAttrList = pDataList_[1]
        pVarList = pDataList_[2]

        pDimTime =  pDimHeight = pDimLat = pDimLon = None #Flags that none of these dimensions are found yet and considered as correct

        checkTime = checkHeight = checkLat = checkLon = False #Flags that coordinates are not checked yet and considered as correct
        dataOk = True #Flag that no error is found yet


        #Check dimensions
        #-------------------------------------------------------------------------------
        #Dimensions time, height, latitude and longitude are needed for data variables of this model
        #Attach dimensions to corresponding coordinates and check their names
        pPreviousDimNamesList = list() #List with names of already checked dimension names
        for pDim in pDimList[:]:
            #Check that each dimension name exists only one time
            if pDim.getName() in pPreviousDimNamesList[:]:
                self.pLogger.error("Multiple appearance of dimension name '" + str(pDim.getName()) + "' in NCML metadata.")
                dataOk = False
            if pDim.getName() in TIME:
                pDimTime = pDim
            elif pDim.getName() in HEIGHT:
                pDimHeight = pDim
            elif pDim.getName() in LATITUDE:
                pDimLat = pDim
            elif pDim.getName() in LONGITUDE:
                pDimLon = pDim
            else: #Warning: Dimension name could not be allocated.
                self.pLogger.warning("Dimension name '" + str(pDim.getName()) + \
                "' is not a valid coordinate dimension name. Valid coordinate dimension names are '" + str(TIME) + "' for time, '" + str(HEIGHT) + \
                "' for height, '" + str(LATITUDE) + "' for latitude and '" + str(LONGITUDE) + "' for longitude.")
            pPreviousDimNamesList.append(pDim.getName())

        #Error: One or more necessary dimensions is missing since they were not found
        if pDimTime is None or pDimHeight is None or pDimLat is None or pDimLon is None:
            self.pLogger.error("A valid coordinate dimension is missing or the name is not a valid coordinated dimension name.\
            Valid coordinate dimension names are '" + str(TIME) + "' for time, '" + str(HEIGHT) + "' for height, '" + str(LATITUDE) + "' for latitude and '"\
            + str(LONGITUDE) + "' for longitude. No more test of data model is employed.")
            dataOk = False

        #All necessary dimensions are existing --> continue to check
        else:

            #Check global attributes
            #-------------------------------------------------------------------------------
            pPreviousAttrNamesList = list() #List with names of already checked global attribute names
            for pAttribute in pAttrList[:]:

                #Check that each global attribute name is not empty
                if pAttribute.getValue() == '':
                    self.pLogger.warning("Global attribute '" + str(pAttribute.getName()) + "' in NCML metadata is empty.")

                #Check that each global attribute name exists only one time per file
                if pAttribute.getName() in pPreviousAttrNamesList[:]:
                    self.pLogger.error("Multiple appearance of global attribute '" + str(pAttribute.getName()) + "' in NCML metadata.")
                    dataOk = False

                pPreviousAttrNamesList.append(pAttribute.getName()) #Append global attribute name to previous global attribute names list


            #Check consistency of dimensions, variables and local attributes
            #-------------------------------------------------------------------------------
            pPreviousVarNamesList = list() #List with names of already checked variable names
            for pVar in pVarList[:]:

                attrLongName = False #Flag that no attribute 'long_name' was found yet

                #Check that each variable name exists only one time
                if pVar.getName() in pPreviousVarNamesList[:]:
                     self.pLogger.error("Multiple appearance of variable name '" + str(pVar.getName()) + "' in NCML metadata.")
                     dataOk = False

                #Check local attributes
                pPreviousVarAttrNamesList = list() #List with names of already checked local attribute names
                for pVarAttribute in pVar.getAttributes():

                    #Check that each local attribute name is not empty
                    if pVarAttribute.getValue() == '':
                        self.pLogger.warning("Local attribute '" + str(pVarAttribute.getName()) + "' at variable name '" + str(pVar.getName()) + \
                        "' in NCML metadata is empty.")

                    #Local attribute 'long_name' found
                    if pVarAttribute.getName() == 'long_name':
                        attrLongName = True

                    #Check that each local attribute name exists only one time per attribute
                    if pVarAttribute.getName() in pPreviousVarAttrNamesList[:]:
                        self.pLogger.error("Multiple appearance of local attribute '" + str(pVarAttribute.getName()) + "' at variable name '" + \
                        str(pVar.getName()) + "' in NCML metadata.")
                        dataOk = False

                    pPreviousVarAttrNamesList.append(pVarAttribute.getName()) #Append local attribute name to previous local attribute names list

                #Check that each variable has at least the attribute long_name attached
                if attrLongName == False:
                    self.pLogger.warning("No local attribute 'long_name' could be found for variable '" + str(pVar.getName()) + "'. This attribute is stronly recommended.")

                #Each coordinate (dimension and coordinate variable) must be existing, checked and be free of errors
                if pVar.getName() in TIME:
                    for pDim in pDimList[:]:
                        if pDim.getName() in TIME:
                            checkTime = self.__checkDataModelCoordinates(pDim, pVar)
                elif pVar.getName() in HEIGHT:
                    for pDim in pDimList[:]:
                        if pDim.getName() in HEIGHT:
                            checkHeight = self.__checkDataModelCoordinates(pDim, pVar)
                elif pVar.getName() in LATITUDE:
                    for pDim in pDimList[:]:
                        if pDim.getName() in LATITUDE:
                            checkLat = self.__checkDataModelCoordinates(pDim, pVar)
                elif pVar.getName() in LONGITUDE:
                    for pDim in pDimList[:]:
                        if pDim.getName() in LONGITUDE:
                            checkLon = self.__checkDataModelCoordinates(pDim, pVar)

                else: #Variable is no coordinate variable, check if error is in data variable
                    if self.__checkDataModelData(pVar, pDimTime, pDimHeight, pDimLat, pDimLon) == False:
                        dataOk = False

                pPreviousVarNamesList.append(pVar.getName()) #Append variable name to previous variable names list

            #One or more coordinate variables were not checked or an error occured
            if checkTime != True or checkHeight != True or checkLat != True or checkLon != True:
                self.pLogger.error("A valid coordinate variable is missing, an error occured, or the name is not a valid coordinated variable name.\
                Valid coordinate variable names are '" + str(TIME) + "' for time, '" + str(HEIGHT) + "' for height, '" + \
                str(LATITUDE) + "' for latitude and '" + str(LONGITUDE) + "' for longitude.")
                dataOk = False


        #Recapitulate if an error occured in data or coordinates
        #-------------------------------------------------------------------------------
        if checkTime != True or checkHeight != True or checkLat != True or checkLon != True or dataOk != True:
            return False #Error occured
        else:
            return True #No error occured


    def __checkDataModelCoordinates(self, pDim_, pVar_):
        """Check if coordinates of internal data model are correct. Returns True if no error occured,
        False if one or more errors occured"""

        #Settings
        #-------------------------------------------------------------------------------
        pVar = pVar_
        pDim = pDim_

        coordOk = True #Flag that coordinate was checked and that no error occured yet

        #Errors
        #-------------------------------------------------------------------------------

        #Dimensions

        #Name of dimension as declared in NCML metadata must be the same as the shape of the related coordinate variable
        if pVar.getShape() != pDim.getName():
            self.pLogger.error("Dimension name '" + str(pDim.getName()) + "' is not the same as its corresponding shape '" + \
            str(pVar.getShape()) + "' of the coordinate variable '" + str(pVar.getName()) + "'.")
            coordOk = False

        #Dimension length as declared in NCML metadata must be the same as shape of the related numpy coordinate variable
        if pDim.getLength() != pVar.getData().shape[0]:
            self.pLogger.error("Dimension length '" + str(pDim.getLength()) + "' for dimension '" + str(pDim.getName()) + \
            "' as declared in NCML metadata is not the same as the variable dimension length '" + str(pVar.getData().shape[0]) + \
            "' of the corresponding numpy array thats dimension information is based on the related coordinate metadata file.")
            coordOk = False

        #Only time dimension can be of unlimited size for NetCDF3 in this model
        if (pDim.getIsUnlimited() != False and pDim.getName() not in TIME):
            self.pLogger.error("Dimension attribute 'isUnlimited' must must be false for this dimension (dimension can't be unlimited). Got value '" + \
            str(pDim.getIsUnlimited()) + "' for dimension '" + str(pDim.getName()) + "'.")
            coordOk = False


        #Coordinate Variables

        #Coordinate variable type as declared in NCML metadata must be the same as the type of the related numpy coordinate variable
        varTypeNcmlConv = self.pProcessingTool.dataType_2Numpy(pVar.getType())
        if varTypeNcmlConv != pVar.getData().dtype:
            self.pLogger.error("Numpy coordinate variable type '" + str(pVar.getData().dtype) + "' for variable '" + str(pVar.getName()) + \
            "' is not the same as declared in NCML metadata: '" + str(pVar.getType()) + "' (equals to '" + str(varTypeNcmlConv) + "' for numpy).")
            coordOk = False

        #Numpy coordinate variable is only allowed to have one dimension
        #Number of dimensions as declared in NCML metadata must be the same as the number of dimensions of related numpy data array
        pListVarShapeConv = self.pProcessingTool.string2List(pVar.getShape(), ' ')
        if (pVar.getData().ndim != 1 or len(pListVarShapeConv) != pVar.getData().ndim):
            self.pLogger.error("Numpy array for coordinate variable is only allowed to have one dimension. Got value '" + \
            str(pVar.getData().ndim) + "' for variable '" + str(pVar.getName()) + \
            "'. It must have the same number of dimensions as declared in NCML metadata: '" + \
            str(pVar.getShape()) + "' ( #'" + str(len(pListVarShapeConv)) + "').")
            coordOk = False


        #Check if mandatory attributes are set
        #-------------------------------------------------------------------------------
        #Coordinate variable attributes 'units' and 'axis' must be correctly set for all coordinate variables
        #Coordinate variable attribute 'calendar' must be correctly set for coordinate variable 'time'
        #Coordinate variable attribute 'positive' must be correctly set for coordinate variable 'height'

        unitExists = axisExists = False #Flag = No attribute 'units' and 'axis' found yet
        calendarExists = positiveExists = False #Flag = No attribute 'calendar' and 'positve' found yet

        for pVarAttr in pVar.getAttributes(): #Find attributes and attached values

            #Check if units is set correctly for all variables (default values and udunits)
            if pVarAttr.getName() == 'units':
                unitExists = True #Attribute 'units' is existing
                unit = pVarAttr.getValue()
                if unit != '': #if string is not empty, check if units is conform to default entries
                    if (pVar.getName() in TIME and unit not in MODEL_REFERENCE_TIME_UNITS) or \
                    (pVar.getName() in HEIGHT and unit not in HEIGHT_UNITS) or \
                    (pVar.getName() in LATITUDE and unit not in LATITUDE_UNITS) or \
                    (pVar.getName() in LONGITUDE and unit not in LONGITUDE_UNITS):
                        self.pLogger.error("Coordinate variable attribute 'units' with value '" + str(pVarAttr.getValue()) + \
                        "' for variable '" + str(pVar.getName()) + "' is not a valid entry. Valid entries are '" + str(MODEL_REFERENCE_TIME_UNITS) + \
                        "' for time, '" + str(HEIGHT_UNITS) + "' for height, '" + str(LATITUDE_UNITS) + "' for latitude and '" + str(LONGITUDE_UNITS) + "' for longitude.")
                        coordOk = False
                    isUdunits = self.pProcessingTool.checkUdunitsUnit(unit)
                    if isUdunits is False: #Unit is not conform to Udunits2
                        self.pLogger.error("Coordinate variable attribute 'units' with value '" + str(pVarAttr.getValue()) + \
                        "' for variable '" + str(pVar.getName()) + "' is not conform to Udunits2 units library. Please check variable unit\
                        and/or find correct corresponding Udunits2 unit in table 'udunits2.xml').")
                        coordOk = False
                else: #empty string
                    self.pLogger.warning("Coordinate variable attribute 'units' for variable '" + str(pVar.getName()) + "' is empty.")

            #Check if axis is set correctly for all variables
            if pVarAttr.getName() == 'axis':
                axisExists = True #Attribute 'axis' is existing
                axis = pVarAttr.getValue()
                if axis != '': #if string is not empty, check if unit is conform
                    if (pVar.getName() in TIME and axis !='T') or (pVar.getName() in HEIGHT and axis !='Z') or \
                    (pVar.getName() in LATITUDE and axis !='Y') or (pVar.getName() in LONGITUDE and axis !='X'):
                         self.pLogger.error("Coordinate variable attribute 'axis' with value '" + str(pVarAttr.getValue()) + \
                         "' for variable '" + str(pVar.getName()) + "' is not a valid entry. Valid entries are 'T', 'Z', 'Y' and 'X'.")
                         coordOk = False
                else: #empty string
                    self.pLogger.error("Coordinate variable attribute 'axis' for variable '" + str(pVar.getName()) + "' is empty.")
                    coordOk = False

            #Check if calendar is set correctly for time
            if (pVar.getName() in TIME) and pVarAttr.getName() == 'calendar':
                calendarExists = True #Attribute 'calendar' is existing
                calendar = pVarAttr.getValue()
                if calendar != '': #if string is not empty, check if unit is conform
                    if (calendar != str(self.pDefaultSettings.varTimeAttrCalendar)):
                         self.pLogger.error("Coordinate variable attribute 'calendar' with value '" + str(pVarAttr.getValue()) + \
                         "' for variable '" + str(pVar.getName()) + "' is not a valid entry. Valid entries are '" + str(self.pDefaultSettings.varTimeAttrCalendar) + "'.")
                         coordOk = False
                else: #empty string
                    self.pLogger.error("Coordinate variable attribute 'calendar' for variable '" + str(pVar.getName()) + "' is empty.")
                    coordOk = False

            #Check if positive is set correctly for height
            if (pVar.getName() in HEIGHT) and pVarAttr.getName() == 'positive':
                positiveExists = True #Attribute 'positiv' is existing
                positive = pVarAttr.getValue()
                if positive != '': #if string is not empty, check if unit is conform
                    if (positive != 'up') and (positive != 'down') :
                         self.pLogger.error("Coordinate variable attribute 'positive' with value '" + str(pVarAttr.getValue()) + \
                         "' for variable '" + str(pVar.getName()) + "' is not a valid entry. Valid entries are 'up' and 'down'.")
                         coordOk = False
                else: #empty string
                    self.pLogger.error("Coordinate variable attribute 'positive' for variable '" + str(pVar.getName()) + "' is empty.")
                    coordOk = False


        #Check if attributes are existing for variables
        if unitExists != True: #No attribute 'units' found
            self.pLogger.error("No attribute 'units' found for variable '" + str(pVar.getName()) + "'. This attribute is mandatory.")
            coordOk = False
        if axisExists != True: #No attribute 'axis' found
            self.pLogger.error("No attribute 'axis' found for variable '" + str(pVar.getName()) + "'. This attribute is mandatory.")
            coordOk = False
        if (calendarExists != True) and (pVar.getName() in TIME): #No attribute 'calendar' found
            self.pLogger.error("No attribute 'calendar' found for variable '" + str(pVar.getName()) + "'. This attribute is mandatory.")
            coordOk = False
        if (positiveExists != True) and (pVar.getName() in HEIGHT): #No attribute 'positive' found
            self.pLogger.error("No attribute 'positive' found for variable '" + str(pVar.getName()) + "'. This attribute is mandatory.")
            coordOk = False


        #Warnings
        #-------------------------------------------------------------------------------

        #Coordinate variable should have the same name as its shape (what is the dimensions name)
        if pVar.getName() != pVar.getShape():
            self.pLogger.warning("Coordinate variable name '" + str(pVar.getName()) + \
            "' is not the same as its corresponding shape '" + str(pVar.getShape()) + "' in NCML metadata.")
        
        return coordOk


    def __checkDataModelData(self, pVar_, pDimTime_, pDimHeight_, pDimLat_, pDimLon_):
        """Check if data of internal data model is correct. Returns True if no error occured,
        False if one or more errors occured"""

        #Settings
        #-------------------------------------------------------------------------------

        pVar = pVar_
        pDimTime = pDimTime_
        pDimHeight = pDimHeight_
        pDimLat = pDimLat_
        pDimLon = pDimLon_

        dataOk = True #Flag that data was checked and that no error occured yet


        #Errors
        #-------------------------------------------------------------------------------

        #Coordinate Variables
           
        #Number of dimensions as declared in NCML metadata must be the same as the number of dimensions of related numpy data array
        pListVarShapeConv = self.pProcessingTool.string2List(pVar.getShape(), ' ')
        if len(pListVarShapeConv) != pVar.getData().ndim:
            if not (len(pListVarShapeConv) == 0 and pVar.getData().ndim ==1): #In case of dimensionless scalar variables like ID
                self.pLogger.error("Data variable number of dimensions '" + str(pVar.getData().ndim) + "' for variable '" + str(pVar.getName()) + \
                "' is not the same as declared in NCML metadata: '" + str(pVar.getShape()) + "' ( #'" + str(len(pListVarShapeConv)) + "').")
                dataOk = False
            
        #Names of data variable dimensions must be "time height latitude longitude" with a length of '4' in this case
        if len(pListVarShapeConv) == 4 and (pListVarShapeConv[0] != pDimTime.getName() or pListVarShapeConv[1] != pDimHeight.getName() \
        or pListVarShapeConv[2] != pDimLat.getName() or pListVarShapeConv[3] != pDimLon.getName()):
            self.pLogger.error("One or more declared dimension names and/or order and/or number of dimension names of data variable '" + str(pVar.getName()) + \
            "' are not valid as declared in NCML metadata. The necessary order with valid names is: time ('" + \
            str(TIME) + "', got shape '" + str(pListVarShapeConv[0]) + "' for dimension '" + str(pDimTime.getName()) + "'), height ('" + \
            str(HEIGHT) + "', got shape '" + str(pListVarShapeConv[1]) + "' for dimension '" + str(pDimHeight.getName()) + "'), latitude ('" + \
            str(LATITUDE) + "', got shape '" + str(pListVarShapeConv[2]) + "' for dimension '" + str(pDimLat.getName()) + "') and longitude ('" + \
            str(LONGITUDE) + "', got shape '" + str(pListVarShapeConv[3]) + "' for dimension '" + str(pDimLon.getName()) + "').")
            dataOk = False 

        #Dimension lengths as declared in NCML metadata must be the same as shape of the related numpy data variable
        if len(pListVarShapeConv) == 4 and (pVar.getData().shape[0] != pDimTime.getLength() or pVar.getData().shape[1] != pDimHeight.getLength() \
        or pVar.getData().shape[2] != pDimLat.getLength() or pVar.getData().shape[3] != pDimLon.getLength()):
            self.pLogger.error("One or more declared dimension lengths of data variable '" + str(pVar.getName()) + \
            "' are not the same as the corresponding numpy data array. Got the following values: time (NCML: '" + \
            str(pDimTime.getLength()) + "', Numpy: '" + str(pVar.getData().shape[0]) + "'); height (NCML: '" + \
            str(pDimHeight.getLength()) + "', Numpy: '" + str(pVar.getData().shape[1]) + "'); latitude (NCML: '" + \
            str(pDimLat.getLength()) + "', Numpy: '" + str(pVar.getData().shape[2]) + "'); longitude (NCML: '" + \
            str(pDimLon.getLength()) + "', Numpy: '" + str(pVar.getData().shape[3]) + "').")
            dataOk = False
       
        #Data variable type as declared in NCML metadata must be the same as type of the related numpy data variable
        varTypeNcmlConv = self.pProcessingTool.dataType_2Numpy(pVar.getType())
        if varTypeNcmlConv != pVar.getData().dtype:
            self.pLogger.error("Data variable type '" + str(pVar.getData().dtype) + "' for variable '" + str(pVar.getName()) + \
            "' is not the same as declared in NCML metadata: '" + str(pVar.getType()) + "' ('" + str(varTypeNcmlConv) + "' for numpy).")
            dataOk = False


        #Check if mandatory attributes are set
        #-------------------------------------------------------------------------------

        #Data variable attribute 'units' must be set and must be conform to Udunits2 library
        unitExists = False #Flag = No attribute 'units' found yet
        for pVarAttr in pVar.getAttributes(): #Find 'units' attribute and attached value
            if pVarAttr.getName() == 'units':
                unitExists = True #Attribute 'units' is existing
                unit = pVarAttr.getValue()
                if unit != '': #if string is not empty check if unit is udunits conform
                    isUdunits = self.pProcessingTool.checkUdunitsUnit(unit)
                    if isUdunits is False: #Unit is not conform to Udunits2
                        self.pLogger.error("Data variable attribute 'units' with value '" + str(pVarAttr.getValue()) + \
                        "' for variable '" + str(pVar.getName()) + "' is not conform to Udunits2 units library. Please check variable unit\
                        and/or find correct corresponding Udunits2 unit in table 'udunits2.xml').")
                        dataOk = False
                else: #empty string
                    self.pLogger.warning("Data variable attribute 'units' for variable '" + str(pVar.getName()) + "' is empty.")
        if unitExists != True and pVar.getName() not in ID: #No attribute 'units' found, is not mandatory (for ID for example)
            self.pLogger.warning("No attribute 'units' is found for variable '" + str(pVar.getName()) + "'. This attribute should be set.")
            

        #Warnings
        #-------------------------------------------------------------------------------

        #Number of dimensions of data variable should be '4' (or '1' for ID)
        if (not (len(pListVarShapeConv) == 4 or len(pListVarShapeConv) == 0)): #and pVar.getName() not in ID:
            self.pLogger.warning("Number of dimensions for data variables should be '4' (time height longitude latitude) or dimensionless. Got dimension number '" + \
            str(len(pListVarShapeConv)) + "' for variable '" + str(pVar.getName()) + "' in NCML metadata instead.")

        return dataOk


    def __readNumpyMetadataValues(self, tag_, dim_, pDataType_):
        """Private function for reading values of coordinate metadata file and
        returning calculated coordinates out of these values"""

        nodeMin = self.pProcessNumpymeta.readAttribute('numpymeta', tag_, 'min')
        nodeMax = self.pProcessNumpymeta.readAttribute('numpymeta', tag_, 'max')
        nodeValues = self.pProcessNumpymeta.readAttribute('numpymeta', tag_, 'values')
        nodeSeparator = self.pProcessNumpymeta.readAttribute('numpymeta', tag_, 'separator')
        
        #calculate evenly spaced values in case that minimum and maximum value is given
        if (nodeMin != '' and nodeMax != ''):
            pNumpyMeta = self.pProcessingTool.createEvenlySpacedNumpy(nodeMin, nodeMax, dim_, pDataType_)

        #else if values are provided (e.g. if they are not evenly spaced) use these values as coordinates
        elif nodeValues != '':
            try:
                if nodeSeparator == '':
                    nodeSeparator = ','
                nodeListValues = nodeValues.split(nodeSeparator)
                pNumpyMeta = numpy.array(nodeListValues, dtype=pDataType_)
            except:
                raise Exception("Error: Values '" + str(nodeListValues) + "' at tag '" + str(tag_) + \
                "' of coordinate metadata could not be imported. Check Values and their related datatype '" + str(pDataType_) + "' as well as separator.")
        else:
            raise Exception("Error: No coordinate values found in coordinate metadata for tag '" + str(tag_) + "'.")

        return pNumpyMeta


#-------------------------------------------------------------------------------

class ModelDataGridRead(ModelDataRead):
    """Class for reading coordinate metadata file and numpy data array of shape
    (variable, time, z, lat, lon). This class inherits from 'ModelDataRead'"""


    def __init__(self, infile_):
        """
        Constructor.

        INPUT_PARAMETERS:
        infile        - file name without suffix (string). Both the numpy data array
            and the coordinate metadata file must have the same name (expect of suffix)
        """

        numpyFileName = infile_+FILENAME_SUFFIX_NUMPYDATA
        self.pNumpy = numpy.load(str(numpyFileName)) 

        ModelDataRead.__init__(self, infile_) #call superclass


    #def __del__(self):
        #"""Destructor"""
        #ModelDataRead.__del__(self)


    def getCoordinateVariables(self, pVarList_):
        """Reading coordinate information in coordinate metadata file and attaching
        calculated coordinates to coordinate variables in internal model"""

        self.dimVar = self.pNumpy.shape[0] #Number of variables in array
        self.dimTime = self.pNumpy.shape[1] #Time Dimension
        self.dimZ = self.pNumpy.shape[2] #Height Dimensions
        self.dimLat = self.pNumpy.shape[3] #Last but one axis top to bottom: lat -> row
        self.dimLon = self.pNumpy.shape[4] #Last axis left to right: lon -> col

        pVarList = ModelDataRead.getCoordinateVariables(self, pVarList_, self.dimVar, self.dimTime, self.dimZ, self.dimLat, self.dimLon, 0)

        return pVarList


    def getDataVariables(self, pVarList_):
        """
        Reading data in numpy data array and attaching these data as separate numpy arrays
        to data variables in internal model. The shape of the separate numpy arrays will
        be transformed to (time, z, lat, lon) for the internal model.

        IMPORTANT:
        The variable order and the number of variables in the numpy array must be coherent
        with the variable order and the number of variables in the internal model!
        """

        varNumpyNr = 0
        pVarList = pVarList_

        for pVar in pVarList[:]:
            if pVar.getName() not in COORD_KEYWORDS: #if not a coordinate variable
                self.pLogger.info("Reading numpy data variable array ID '" + str(varNumpyNr) + "' with name '" + str(pVar.getName()) + "' according to metadata...")
                pVar.addData(self.pNumpy[varNumpyNr,:,:,:,:])
                varNumpyNr = varNumpyNr+1
                
        return pVarList


    def checkDataModel(self, pDataList_):
        """Check if complete data model is correct and consistent"""

        return ModelDataRead.checkDataModel(self, pDataList_)



#-------------------------------------------------------------------------------

class ModelDataStationRead(ModelDataRead):
    """Class for reading coordinate metadata file and numpy data array of shape
    (time, variable). This class inherits from 'ModelDataRead'"""


    def __init__(self, infile_):
        """
        Constructor.

        INPUT_PARAMETERS:
        infile        - file name without suffix (string). Both the numpy data array
            and the coordinate metadata file must have the same name (expect of suffix)
        """

        numpyFileName = infile_+FILENAME_SUFFIX_NUMPYDATA
        self.pNumpy = numpy.load(str(numpyFileName)) 

        ModelDataRead.__init__(self, infile_) #call superclass


    #def __del__(self):
        #"""Destructor"""
        #ModelDataRead.__del__(self)


    def getCoordinateVariables(self, pVarList_):
        """Reading coordinate information in coordinate metadata file and attaching
        calculated coordinates to coordinate variables in internal model"""

        self.dimTime = self.pNumpy.shape[0] #Last but one axis top to bottom: Time Dimension
        self.dimVar = self.pNumpy.shape[1] #Last axis left to right: Number of variables in array
        self.dimZ = int(1) #Single Height dimension for station
        self.dimLat = int(1) #Single Latitude dimension for station
        self.dimLon = int(1) #Single Longitude dimension for station
        self.dimID = int(1) #Single ID needed by Dapper/DChart

        pVarList = ModelDataRead.getCoordinateVariables(self, pVarList_, self.dimVar, self.dimTime, self.dimZ, self.dimLat, self.dimLon, self.dimID)

        return pVarList


    def getDataVariables(self, pVarList_):
        """
        Reading data in numpy data array and attaching these data as separate numpy arrays
        to data variables in internal model. The shape of the separate numpy arrays will
        be transformed to (time, z, lat, lon) for the internal model.

        IMPORTANT:
        The variable order and the number of variables in the numpy array must be coherent
        with the variable order and the number of variables in the internal model!
        """
       
        varNumpyNr = 0
        pVarList = pVarList_

        #The input shape (time, variable) will be transformed to (variable, time, z, lat, lon)
        pNumpyConv = numpy.empty([self.dimVar, self.dimTime, self.dimZ, self.dimLat, self.dimLon], dtype = self.pNumpy.dtype)

        for pVar in pVarList[:]:
            if pVar.getName() not in COORD_KEYWORDS: #if not a coordinate variable
                self.pLogger.info("Reading numpy data variable array ID '" + str(varNumpyNr) + "' with name '" + str(pVar.getName()) + "' according to metadata.")
                pNumpyConv[varNumpyNr,:,0,0,0] = self.pNumpy[:,varNumpyNr]
                pVar.addData(pNumpyConv[varNumpyNr,:,:,:,:])
                varNumpyNr = varNumpyNr+1

        return pVarList


    def checkDataModel(self, pDataList_):
        """Check if complete data model is correct and consistent"""

        #elev = lat = lon = id = 1 --> Must not be checked since internal data model is transformed to this shape
        return ModelDataRead.checkDataModel(self, pDataList_)



#_______________________________________________________________________________

class ModelNetCdfRead:
    """Class for reading one or multiple NetCDF files"""


    def __init__(self,infile_):
        """
        Constructor.

        INPUT_PARAMETERS:
        infile        - NetCDF file name without suffix (string) or that part of the
            NetCDF file name that is shared by all files (for reading multiple files),
            followed by a wildcard (*).

        COMMENTS:
        For reading and aggregating multiple NetCDF files all files need to be similiar
        expect of the time coordinate values (but need to share the same time unit).
        """

        if not infile_.endswith(FILENAME_SUFFIX_NETCDF): #Add filename suffix '.nc' if this is missing
            netCdfFileNames = infile_ + FILENAME_SUFFIX_NETCDF
        else:
            netCdfFileNames = infile_

        #Reading one NetCDF file to internal model, and if does not exist,
        #reading all files infile_+'*.nc' to data model in case that wildcard is in argument
        try:
            self.pMFNetCdf = MFDataset(netCdfFileNames)#, check = True) #Desactivate "check", causes trouble!!!
        except:
            if not os.path.exists(netCdfFileNames):
                raise Exception("Error: NetCDF file '" + str(netCdfFileNames) + "' does not exist in current directory '" + str(os.getcwd()) + \
                "'. Check filename, directory, or use wildcards (*) to read mulitple NetCDF files.")
            else:
                raise Exception("Error: Problems while reading NetCDF file '" + str(netCdfFileNames) + "' in current directory '" + str(os.getcwd()) + \
                "'. Check filename, directory, or use wildcards (*) to read mulitple NetCDF files.")

        self.pProcessingTool = ProcessingTool()

        self.pLogger = logging.getLogger(INTERFACE_LOGGER_ROOT+"."+__name__+"."+self.__class__.__name__)

       
    def __del__(self):
        """Destructor"""
        self.pMFNetCdf.close()
        #self.pLogFile.close()


    def readDimensions(self):
        """Reading dimensions of NetCDF file and saving them to internal model"""

        pDimList = list()

        for dimName, dimObj in self.pMFNetCdf.dimensions.iteritems():
            #print 'Dimension: ', dimName, '; Length:', len(dimObj),'; Is Unlimited:', dimObj.isunlimited()
            dimLength = len(dimObj)
            dimIsUnlimited = dimObj.isunlimited()

            pDim = Dimension(dimName, dimLength, dimIsUnlimited)
            pDimList.append(pDim)

        return pDimList


    def readGlobalAttributes(self):
        """"Reading global attributes of NetCDF file and saving them to internal model"""

        pAttrList = list()

        for attrName in self.pMFNetCdf.ncattrs():
            #print 'Attribute: ', attrName + ' ; Value: ', getattr(self.pMFNetCdf, attrName)
            attrType = "" #not needed for global attributes
            attrSeparator = "" #can not be extracted via this Python NetCDF API
            attrValue = getattr(self.pMFNetCdf, attrName)

            pAttr = Attribute(attrName, attrType, attrValue, attrSeparator)
            pAttrList.append(pAttr)

        return pAttrList


    def readVariables(self):
        """
        Reading variables and associated local attributes of NetCDF file and saving
        them to internal model

        IMPORTANT:
        Activate function '.__correctVariableInputData' for manual bug fix of 'issue 34'
        (slicing MFDataset variables with dimensions of length 1) if API NetCDF4 is older then version 0.9
        """

        pVarList = list()

        for varName, varObj in self.pMFNetCdf.variables.iteritems():

            pMFNetCdfVariable = self.pMFNetCdf.variables[varName] #specific variable
            #print pMFNetCdfVariable.__dict__


            #Create Variable in internal model and get variable metadata
            #-------------------------------------------------------------------------------
            #convert list of variable dimensions to single string
            varDims = self.pProcessingTool.list2String(pMFNetCdfVariable.dimensions, ',', ' ')
            varType = pMFNetCdfVariable.dtype
            #varNrDim = pMFNetCdfVariable.ndim #information not needed
            pVar = Variable(varName, varDims, varType)


            #Attach numpy array data to variable and get data
            #-------------------------------------------------------------------------------
            varNumpyShape = pMFNetCdfVariable.shape
            numpyVarType = self.pProcessingTool.dataType_2Numpy(varType)# convert to numpy dtype

            pVarDataNumpy = numpy.empty(varNumpyShape, dtype = numpyVarType)
            pVarDataNumpy = pMFNetCdfVariable [:]

#!!!Activate manual bug fix for issue 34 if API Netcdf4 older as version 0.9
            #pVarDataNumpy = self.__correctVariableInputData(pVarDataNumpy, varNumpyShape, varName)
                   
            pVar.addData(pVarDataNumpy)


            #Attach local attributes and get variable attribute information and convert type if necessary
            #-------------------------------------------------------------------------------
            for attrName in pMFNetCdfVariable.ncattrs():
                #print 'Attribute: ', attrName + ' ; Value: ', getattr(pMFNetCdfVariable, attrName)
                attrValue = getattr(pMFNetCdfVariable, attrName)

                #Test if attribute value consists of multiple values --> keywords
                if attrName in ['valid_range']:
                    attrSeparator = "," # Attribute also set as key indicator that multiple values are present
                    attrValueElement = attrValue[0] #For type determination
                    attrValueString = str(attrValue[0]) + attrSeparator + str(attrValue[1]) #Change from list to string
                    attrValue = attrValueString

                #Attribute consist of single scalar value
                else:
                    attrSeparator = "" #Key indicator that value is scalar
                    attrValueElement = attrValue #For type determination

                #Test if attribute is numeric
                if type(attrValueElement) is numpy.int8:
                    attrType = "int8"
                #elif type(attrValueElement) is numpy.uint8:
                #    attrType = "uint8"
                elif type(attrValueElement) is numpy.int16:
                    attrType = "int16"
                elif type(attrValueElement) is numpy.uint16:
                    attrType = "uint16"
                elif type(attrValueElement) is numpy.int32:
                    attrType = "int32"
                elif type(attrValueElement) is numpy.uint32:
                    attrType = "uint32"
                elif type(attrValueElement) is numpy.int64:
                    attrType = "int64"
                elif type(attrValueElement) is numpy.uint64:
                    attrType = "uint64"
                elif type(attrValueElement) is numpy.float32:
                    attrType = "float32"
                elif type(attrValueElement) is numpy.float64:
                    attrType = "float64"
                else:
                    attrType = "" #String value, not numeric, attribute also set as key indicator that value is string
                
                self.pLogger.debug("Read local attribute from variable '" + str(varName) + "' of NetCDF file: Name: '" + str(attrName) + \
                 "'; Value: '" + str(attrValue) + "'; Type: '" + str(attrType) + "' (" + str(type(attrValueElement)) + "); Separator: '" + str(attrSeparator) + "')")

                pVar.addAttribute(attrName, attrType, attrValue, attrSeparator)

            pVarList.append(pVar)

        return pVarList


    def __correctVariableInputData(self, pVarDataNumpy_, varNumpyShape_, varName_):
        """ Function for manual bug fix of 'issue 34' when slicing MFDataset variables with dimensions
        of length 1 (command 'pVarDataNumpy = pMFNetCdfVariable [:]) if API NetCDF4 is older then version 0.9"""

        #Manual bug fix (issue 34) when slicing MFDataset variables with dimensions of length 1
        #Bug fixed since NetCDF v0.9
        if varNumpyShape_ != pVarDataNumpy_.shape:
            self.pLogger.warning("Shape of '" + str(varName_) + "' is '" + str(pVarDataNumpy_.shape) + "', but should be: '" + str(varNumpyShape_) + "'.")
            self.pLogger.debug("Dimensions are unequal probalby due to a bug in command 'str(pVarDataNumpy = pMFNetCdfVariable [:]'. Trying to adapt Dimensions...")

            pVarDataNumpy = numpy.reshape(pVarDataNumpy_, varNumpyShape_)

            self.pLogger.debug("Shape of '" + str(varName_) + "' after reparation: '" + str(pVarDataNumpy.shape) + "'.")

            if varNumpyShape_ != pVarDataNumpy.shape:
                 raise Exception("Error in writing Numpy Data. Dimensions are still corrupt! Could not correct problem.")

        #Fixed bug that occured when indexing with a numpy array of length 1
        #Bug fixed since NetCDF v0.8.1
        elif pVarDataNumpy_.ndim == 0:
            self.pLogger.info("Dimensionsless variable '" + str(varName_) + "' detected (shape '" + str(pVarDataNumpy_.shape) + \
            "'). Must add one dimensions to numpy array...")
            pVarDataNumpy = numpy.expand_dims(pVarDataNumpy_, axis=0)

        else:
            pVarDataNumpy = pVarDataNumpy_
            
        return pVarDataNumpy



#_______________________________________________________________________________

class ModelPrint:
    """Class for printing data and metadata"""

    def __init__(self, pDataList_):
        """
        Constructor.

        INPUT_PARAMETERS:
        DataList        - List of internal model with dimensions, attributes and variables
            to print on screen
        """

        self.pDimList = pDataList_[0]
        self.pAttrList = pDataList_[1]
        self.pVarList = pDataList_[2]

        self.pLogger = logging.getLogger(INTERFACE_LOGGER_ROOT+"."+__name__+"."+self.__class__.__name__)

        self.pLogger.info("")
        self.pLogger.info("_____________________________________________________________________")
        self.pLogger.info("")
        self.pLogger.info("PRINT DATA MODEL")


    def __del__(self):
        """Destructor"""

        self.pLogger.info("")
        self.pLogger.info("_____________________________________________________________________")


    def printDimensions(self):
        """Print dimensions of internal model"""

        self.pLogger.info("")
        self.pLogger.info("---------------------------------------------------------------------")
        self.pLogger.info("DIMENSIONS:")
        self.pLogger.info("")

        for pDim in self.pDimList[:]:
            self.pLogger.info("    NAME: '" + str(pDim.getName()) + "'; LENGTH: '" + str(pDim.getLength()) + \
            "'; ISUNLIMITED: '" + str(pDim.getIsUnlimited()) + "'")

        return


    def printGlobalAttributes(self):
        """Print global attributes of internal model"""

        self.pLogger.info("")
        self.pLogger.info("---------------------------------------------------------------------")
        self.pLogger.info("GLOBAL ATTRIBUTES:")
        self.pLogger.info("")

        for pAttr in self.pAttrList[:]:
            self.pLogger.info("    NAME: '" + str(pAttr.getName()) + "'; VALUE: '" + str(pAttr.getValue()) + \
            "'; TYPE: '" + str(pAttr.getType()) + "'; SEPARATOR: '" + str(pAttr.getSeparator()) + "'")
            
        return


    def printVariables(self):
        """Print variables and attached local attributes of internal model"""

        self.pLogger.info("")
        self.pLogger.info("---------------------------------------------------------------------")
        self.pLogger.info("VARIABLES:")
        
        for pVar in self.pVarList[:]:
            self.pLogger.info("")
            self.pLogger.info("    NAME: '" + str(pVar.getName()) + "'; SHAPE: '" + str(pVar.getShape()) + "'; TYPE: '" + str(pVar.getType()) + "'")
            pVarDataNumpy = pVar.getData()
            self.pLogger.info("    DATA NUMPY - SHAPE: '" + str(pVarDataNumpy.shape) + "'; TYPE: '" + str(pVarDataNumpy.dtype) + "'")
            self.pLogger.info("    LOCAL ATTRIBUTES:")
            for pVarAttribute in pVar.getAttributes():
                self.pLogger.info("        NAME: '" + str(pVarAttribute.getName()) + "'; VALUE: '" + str(pVarAttribute.getValue()) + \
                "'; TYPE: '" + str(pVarAttribute.getType()) + "'; SEPARATOR: '" + str(pVarAttribute.getSeparator()) + "'")

        return


    def printCoordinateVariablesData(self):
        """Print data of coordinate variables of internal model"""

        self.pLogger.info("")
        self.pLogger.info("---------------------------------------------------------------------")
        self.pLogger.info("COORDINATE VARIABLES:")

        for pVar in self.pVarList[:]:
            if pVar.getName() in COORD_KEYWORDS: #if coordinate variable
                pVarDataNumpy = pVar.getData()
                self.pLogger.info("")
                self.pLogger.info("NAME: '" + str(pVar.getName()) + "'; SHAPE: '" + str(pVarDataNumpy.shape) + \
                "'; TYPE: '" + str(pVarDataNumpy.dtype) + "'")
                self.pLogger.info(pVarDataNumpy)

                raw_input("\nPress Enter to continue.") #Stop print out
                
        return


    def printDataVariablesData(self):
        """Print data of data variables of internal model"""

        self.pLogger.info("")
        self.pLogger.info("---------------------------------------------------------------------")
        self.pLogger.info("DATA VARIABLES:")

        for pVar in self.pVarList[:]:
            if pVar.getName() not in COORD_KEYWORDS: #if data variable
                pVarDataNumpy = pVar.getData()
                self.pLogger.info("")
                self.pLogger.info("NAME: '" + str(pVar.getName()) + "'; SHAPE: '" + str(pVarDataNumpy.shape) + \
                "'; TYPE: '" + str(pVarDataNumpy.dtype) + "'")
                self.pLogger.info(pVarDataNumpy)

                raw_input("\nPress Enter to continue.") #Stop print out
                
        return



#_______________________________________________________________________________

class ModelMetadataNcmlWrite:
     """Class for writing a NCML XML metadata file out of data of the internal model"""


     def __init__(self, infile_):
         """
         Constructor.

         INPUT_PARAMETERS:
         infile        - name of NCML file name without suffix (string)
         """

         self.ncmlFileName = str(infile_)+FILENAME_SUFFIX_NCML
         self.pProcessNcml = ProcessNcml(self.ncmlFileName)

         self.pLogger = logging.getLogger(INTERFACE_LOGGER_ROOT+"."+__name__+"."+self.__class__.__name__)

         self.pProcessNcml.createEmptyXmlFile("http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2", "netcdf")


     #def __del__ (self):
         #"""Destructor"""


     def printNcmlOnScreen(self):
         """Print NCML file on screen"""

         self.pProcessNcml.printXmlOnScreen()
         return


     def addDimensions(self, pDimList_):
         """Add dimension entries to NCML file by the use of the internal models dimension list"""

         pDimList = pDimList_
         for pDim in pDimList[:]:
             if pDim.getIsUnlimited():
                  self.pProcessNcml.addDimension(str(pDim.getName()), str(pDim.getLength()),'true')
             elif not pDim.getIsUnlimited(): #== False:
                  self.pProcessNcml.addDimension(str(pDim.getName()), str(pDim.getLength()), 'false')
         return


     def addGlobalAttributes(self, pAttrList_):
         """Add global attribute entries to NCML file by the use of the internal models global attribute list"""

         pAttrList = pAttrList_
         for pAttr in pAttrList[:]:
             self.pProcessNcml.addGlobalAttribute(str(pAttr.getName()), str(pAttr.getValue()), str(pAttr.getType()), str(pAttr.getSeparator()))
         return


     def addVariables(self, pVarList_):
         """Add variable metadata and local attribute entries to NCML file by the use of the internal models variable list"""

         pVarList = pVarList_
         
         for pVar in pVarList[:]:
             self.pProcessNcml.addVariable(str(pVar.getName()), str(pVar.getShape()), str(pVar.getType()))  
             for pVarAttr in pVar.getAttributes():
                 self.pProcessNcml.addLocalAttribute(str(pVar.getName()), str(pVarAttr.getName()), str(pVarAttr.getValue()), str(pVarAttr.getType()), str(pVarAttr.getSeparator()))
         return



#_______________________________________________________________________________

class ModelDataWrite:
    """Class for writing a numpy data array and a coordinate metadata file out of
    internal model"""


    def __init__(self, infile_):
        """
        Constructor.

        INPUT_PARAMETERS:
        infile        - file name without suffix (string). Both the numpy data array
            and the coordinate metadata file will have the same name (expect of suffix)
        """

        self.xmlFileName = infile_+FILENAME_SUFFIX_NUMPYXML
        self.numpyFileName = infile_+FILENAME_SUFFIX_NUMPYDATA

        self.pProcessNumpymeta = ProcessNumpymeta(self.xmlFileName)
        self.pProcessingTool = ProcessingTool()

        self.pLogger = logging.getLogger(INTERFACE_LOGGER_ROOT+"."+__name__+"."+self.__class__.__name__)


    #def __del__ (self):
        #"""Destructor"""


    def writeCoordinateVariables(self, pVarList_):
        """
        Get coordinate information from coordinate variables of internal model and
        write coordinates to coordinate metadata file.

        IMPORTANT:
        - All numpy arrays in the internal model that are attached to a coordinate variable
            need to have a single dimension containing their coordinates
        """

        pVarList = pVarList_

        self.pProcessNumpymeta.createEmptyXmlFile('None', 'numpymeta')
        
        for pVar in pVarList[:]:
            if pVar.getName() in TIME:
                pTimeNumpy = pVar.getData()
                self.pProcessNumpymeta.writeNumpyMetadataValues(pTimeNumpy, 'time')
               
            elif pVar.getName() in HEIGHT:
                pHeightNumpy = pVar.getData()
                self.pProcessNumpymeta.writeNumpyMetadataValues(pHeightNumpy, 'height')

            elif pVar.getName() in LATITUDE:
                pLatNumpy = pVar.getData()
                self.pProcessNumpymeta.writeNumpyMetadataValues(pLatNumpy, 'latitude')
                
            elif pVar.getName() in LONGITUDE:
                pLonNumpy = pVar.getData()
                self.pProcessNumpymeta.writeNumpyMetadataValues(pLonNumpy, 'longitude')

            elif pVar.getName() in ID:
                pIdsNumpy = pVar.getData()
                self.pProcessNumpymeta.writeNumpyMetadataValues(pIdsNumpy, 'id')

        return


    def writeDataVariables(self, pVarList_):
        """
        Get data values from data variables of internal model and write data variables
        to external numpy array file.

        IMPORTANT:
        - All numpy data arrays in the internal model (so each numpy array attached to a data variable)
        must have the same shape and type so that they can be merged in a new array
        - All numpy data arrays in the internal model have to have the shape (time, z, lat, lon)
        """
        
        pVarList = pVarList_
                
        #Get number of data variables in internal model and check data consistency
        #-------------------------------------------------------------------------------
        varNumpyNr = 0 #Number of variables will be obtained by incrementation
        
        for pVar in pVarList[:]:
            if pVar.getName() not in COORD_KEYWORDS: #if not a coordinate variable
                pVarDataNumpy = pVar.getData()

                #Data array must have four dimensions [time height latitude longitude]. Otherwise modify code (see below) and desactivate error message
                if pVarDataNumpy.ndim != 4:
                    raise Exception("Error in writing Numpy Data. Data array must have four dimensions [time height latitude longitude]. Found " + str(pVarDataNumpy.ndim) + " dimensions.")

                #Check if all data numpy arrays have same shape and type, so that they can be stored in one array
                if varNumpyNr > 0:
                    if pVarDataNumpy.shape != pVarDataNumpyComp.shape:
                        raise Exception("Error in writing Numpy Data. Data Variables have different shapes.")
                    if pVarDataNumpy.dtype != pVarDataNumpyComp.dtype:
                        raise Exception("Error in writing Numpy Data. Data Variables have different types.")
                pVarDataNumpyComp = numpy.copy(pVarDataNumpy)
                varNumpyNr = varNumpyNr+1

        #Output numpy array in the form [time height latitude longitude]
        pNumpyData = numpy.empty([varNumpyNr, pVarDataNumpy.shape[0], pVarDataNumpy.shape[1], pVarDataNumpy.shape[2], pVarDataNumpy.shape[3]], dtype = pVarDataNumpy.dtype)

        #!!! If height coordinate is missing use following commands below, and desactivate error message
        #pNumpyData = numpy.empty([varNumpyNr, pVarDataNumpy.shape[0], 1, pVarDataNumpy.shape[1], pVarDataNumpy.shape[2]], dtype = pVarDataNumpy.dtype)


        #Write data of data variables to output numpy array
        #-------------------------------------------------------------------------------
        varNumpyNr = 0
        for pVar in pVarList[:]:
            if pVar.getName() not in COORD_KEYWORDS: #all data variables must be of shape (time, z, lat, lon)
                pNumpyData[varNumpyNr,:,:,:,:] = pVar.getData()
                #pNumpyData[varNumpyNr,:,0,:,:] = pVar.getData() #If height coordinate is missing

                varNumpyNr = varNumpyNr+1

        numpy.save(self.numpyFileName, pNumpyData)

        return



#_______________________________________________________________________________

class ModelNetCdfWrite:
    """Class for writing data from the internal model to a NetCDF file"""


    def __init__(self, netCdfFileName_):
        """
        Constructor.

        INPUT_PARAMETERS:
        infile        - name of NetCDF file name without suffix (string)
        """

        if not netCdfFileName_.endswith(FILENAME_SUFFIX_NETCDF): #Add filename suffix '.nc' if this is missing
            netCdfFileName = netCdfFileName_ + FILENAME_SUFFIX_NETCDF
        else:
            netCdfFileName = netCdfFileName_

        self.pNetCdf = Dataset(netCdfFileName, 'w', True, format=NETCDF_FORMAT)
        self.pProcessingTool = ProcessingTool()

        self.pLogger = logging.getLogger(INTERFACE_LOGGER_ROOT+"."+__name__+"."+self.__class__.__name__)
 

    def __del__(self):
        """Destructor"""
        self.pNetCdf.close()


    def writeDimensions(self, pDimList_):
        """Write dimensions from the internal models dimension list to the NetCDF file"""

        pDimList = pDimList_
        pNetCdf = self.pNetCdf

        for pDim in pDimList[:]:

            #print 'DIMENSION - Name: ', pDim.getName(), '; Length: ', pDim.getLength(),'; IsUnlimited: ', pDim.getIsUnlimited()

            if pDim.getIsUnlimited():
                pNetCdf.createDimension(pDim.getName(), None)
            elif not pDim.getIsUnlimited(): #== False:
                pNetCdf.createDimension(pDim.getName(), pDim.getLength())
            else:
                raise Exception("Error in creating Dimension (Problem 'IsUnlimited' attribute).")
       
        #for dimname, dimobj in pNetCdf.dimensions.iteritems():
            #print dimname, len(dimobj), dimobj.isunlimited()

        #print pNetCdf.dimensions

        return


    def writeGlobalAttributes(self, pAttrList_):
        """Write global attributes from the internal models global attribute list to the NetCDF file"""

        pAttrList = pAttrList_
        pNetCdf = self.pNetCdf

        for pAttr in pAttrList[:]:
            #print 'GLOBAL ATTRIBUTE - Name:', pAttr.getName(), '; Type: ',pAttr.getType(),'; Value: ', pAttr.getValue()#,'; Separator: ', pAttr.getSeparator()
            attribute = pAttr.getName()
            setattr(pNetCdf, attribute, pAttr.getValue()) #--> pNetCdf.attribute = pAttr.getValue()

        #for name in pNetCdf.ncattrs():
        #    print 'Global attr', name, '=', getattr(pNetCdf,name)

        #print pNetCdf.__dict__

        return


    def writeVariables(self, pVarList_):
        """
        Write variables (data and metadata) and attached local attributes from the internal
        models variable list to the NetCDF file

        IMPORTANT:
        - The numpy data array must be consistent with the corresponding variable metadata
            (shape, type, _FillValue, etc.)
        - The numpy data array is allowed to have one to four dimensions (in general
            one for coordinate variables and four for data variables)
        - Type conversion of attributes from string to numeric is only employed in case that
            the attribute 'type' is set, otherwise it is considered as string
        - Attributes will be considered as single scalar value expect that the attribute 'separator'
            is set. In this case the attributes will be converted to a list of values, e.g. for 'valid_range'
        """
       
        pVarList = pVarList_
        pNetCdf = self.pNetCdf

        for pVar in pVarList[:]:

            #Create NetCDF variable and write its metadata to variable
            #-------------------------------------------------------------------------------
            varTypeConv = self.pProcessingTool.dataType_2NetCdf(pVar.getType()) #type conversion to NetCDF
            pListVarShapeConv = self.pProcessingTool.string2List(pVar.getShape(), ' ') #List with variable dimension names
            pVarDataNumpy = pVar.getData()

            # Since API NetCDF4 v0.9.2 _FillValue attribute must be set when creating variable! Doing it here...
            fillValue = None #default value
            for pVarAttr in pVar.getAttributes(): #Find '_FillValue' attribute and attached value
                if pVarAttr.getName() == '_FillValue':
                    try: #test if fillValue is numeric
                        isNumeric = float(pVarAttr.getValue())
                    except ValueError: #string is not numeric --> not valid --> Keyword that no FillValue is used
                        fillValue = None
                    else: #string is numeric, therefore a valid fillValue
                        if varTypeConv in ALL_INTS: #Type conversion vor nodata value necessary, here integer
                            fillValue = int(Decimal(pVarAttr.getValue())) #Hack to convert negativ integer value
                        else:
                            fillValue = float(pVarAttr.getValue()) #nodata value here float

            if fillValue != None: #Create Variable with valid fillValue
                pNetCdfVar = pNetCdf.createVariable(pVar.getName(),varTypeConv,(pListVarShapeConv), fill_value = fillValue)
            else: #Create Variable without fillValue since there is no fillValue or it is not valid
                pNetCdfVar = pNetCdf.createVariable(pVar.getName(),varTypeConv,(pListVarShapeConv))
           

            #Write data to NetCDF variable from attached numpy array
            #-------------------------------------------------------------------------------
            #print '\nVARIABLE - Name: ', pVar.getName(),'; Type: ', pVar.getType(),'; Shape: ', pListVarShapeConv
            #print '   NUMPY - Shape: ', pVarDataNumpy.shape, '; Type: ', pVarDataNumpy.dtype
            #print '   NetCDF - Type:', varTypeConv

            if len(pVarDataNumpy.shape) == 1: #coordinate variable
                pNetCdfVar[:] = pVarDataNumpy#[:]
            elif len(pVarDataNumpy.shape) == 2:
                pNetCdfVar[:,:] = pVarDataNumpy#[:,:]
            elif len(pVarDataNumpy.shape) == 3:    
                pNetCdfVar[:,:,:] = pVarDataNumpy#[:,:,:]
            elif len(pVarDataNumpy.shape) == 4: #data variable
                pNetCdfVar[:,:,:,:] = pVarDataNumpy#[:,:,:,:]
            else:
                raise Exception("Error: Dimension of data must be less then '4'. Dimension of data however is: '" + str(len(pVarDataNumpy.shape)) + "'!")

            #Write attached local attributes of variable to NetCDF variable and convert type if necessary
            #-------------------------------------------------------------------------------
            for pVarAttr in pVar.getAttributes():

                #print '   VARIALBE ATTRIBUTE - Name: ', pVarAttr.getName(),'; Type: ',pVarAttr.getType(),';  Value: ',  pVarAttr.getValue()#,'; Separator: ', pVarAttr.getSeparator()
                attrName = pVarAttr.getName()
                attrType = pVarAttr.getType()
                attrSeparator = pVarAttr.getSeparator()

                if not attrName == '_FillValue': #already set when creating variable

                    #Attribute value consists of multiple values, since the attribute 'separator' is set
                    if not attrSeparator == "":

                        attrValueListInput = self.pProcessingTool.string2List(pVarAttr.getValue(),attrSeparator) #Convert attribute value string to list
                        attrValueList = list() #Final output list
                        for elementList in attrValueListInput: #Convert all elements in input list
                            #Test if attribute is numeric, what is considered if attribute 'type' is set
                            if attrType in ALL_INTS: #Attribute type is integer
                                if attrType in BYTE:
                                    attrValue = int(elementList,8)
                                elif attrType in SHORT:
                                    attrValue = int(elementList,16)
                                elif attrType in INTEGER:
                                    attrValue = int(elementList,32)
                                else:
                                    attrValue = int(elementList)
                            elif attrType in ALL_FLOATS: #Attribute type is float
                                attrValue = float(elementList)

                            #Attribute 'type' is not set and attribute is thereof considered as string
                            else: #attribute is not numeric --> string
                                attrValue = str(elementList)

                            attrValueList.append(attrValue)
                          
                        self.pLogger.debug("Write listed local attribute from variable '" + str(pVar.getName()) + "' to NetCDF: Name: '" + str(attrName) + \
                        "'; Value: '" + str(attrValueList) + "'; Type: '" + str(attrType) + "' (" + str(type(attrValue)) + "); Separator: '" + str(attrSeparator) + "')")

                        setattr(pNetCdfVar, attrName, attrValueList) #--> pNetCdfVar.attribute = pVarAttr.getValue()


                    #Attribute value is considered as single value, since the attribute 'separator' is not set
                    else:
                        #Test if attribute is numeric, what is considered if attribute 'type' is set
                        if attrType in ALL_INTS: #Attribute type is integer
                            if attrType in BYTE:
                                attrValue = int(pVarAttr.getValue(),8)
                            elif attrType in SHORT:
                                attrValue = int(pVarAttr.getValue(),16)
                            elif attrType in INTEGER:
                                attrValue = int(pVarAttr.getValue(),32)
                            else:
                                attrValue = int(pVarAttr.getValue())
                        elif attrType in ALL_FLOATS: #Attribute type is float
                            attrValue = float(pVarAttr.getValue())

                        #Attribute 'type' is not set and attribute is thereof considered as string
                        else: #attribute is not numeric --> string
                            attrValue = pVarAttr.getValue()

                        self.pLogger.debug("Write single local attribute from variable '" + str(pVar.getName()) + "' to NetCDF: Name: '" + str(attrName) + \
                        "'; Value: '" + str(attrValue) + "'; Type: '" + str(attrType) + "' (" + str(type(attrValue)) + "); Separator: '" + str(attrSeparator) + "')")

                        setattr(pNetCdfVar, attrName, attrValue) #--> pNetCdfVar.attribute = pVarAttr.getValue()


        #print pNetCdf.variables

        return
   