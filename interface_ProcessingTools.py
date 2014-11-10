#! /usr/bin/python
# -*- coding: latin1 -*-

"""
Modul with processing tools.

This module contains classes as tools for processing interface related
data and is used by the module 'interface_Model'. Furthermore this module can be
used by other modules that are intended to convert data to and fromt the data model
"""

__author__= "Nicolai Holzer"
__author_email__ = "first-name dot last-name @ mailbox.tu-dresden.de"
__date__ ="2011-04-15"
__version__ = "v0.1.3"


#Changelog
#-------------------------------------------------------------------------------
#2001-04-15: v0.1.3 little changes for NcML attributes
#2011-01-14: v0.1.2 functionalities changed
#2010-11-23: v0.1.1 comments and docstrings added
#2010-10-08: v0.1.0 first version


#Imported libraries
#-------------------------------------------------------------------------------
#standard libraries
import time
from datetime import datetime, timedelta
import dateutil.parser
import xml.dom.minidom
from os import environ #for Udunits

#related libraries
import numpy
try:
    from netCDF4 import num2date, date2num
except ImportError:
    print "Warning: Import Error for API 'netCDF4'. Operations using this library won't work."

#local applications / library specific import
from interface_Settings import *

#===============================================================================



class ProcessingTool:
    """Class containing frequently used functions by the module 'interface_Model' that
    is designed so that it can also be used by other modules"""


    def createEvenlySpacedNumpy(self, min_, max_, quantity_, dataType_):
        """
        Create numpy array with evenly spaced values.

        This function creates a numpy array with evenly spaced values based on a minimum
        and maximum value as well as a value defining the number of values to generate and
        a data type

        INPUT_PARAMETERS:
        min         - Minimum value, first value in numpy array (float)
        max         - Maximum value, last value in numpy array (float)
        quantity    - Number of values to generate (integer)
        dataType    - Numpy data type defining the output data (numpy dtype)

        RETURN_VALUE:
        Numpy array with evenly spaced values
        """

######################Problem Output data type is only possible as double, otherwise problems with rounding!

        min = float(min_)
        max = float(max_)
        quantity = int(quantity_) #dimensions value

        #step = float((max-min)/(quantity-1))#and one value has to be skipped for calculation
        #pNumpy = numpy.arange(min, max, step, dtype=dataType_)  #pNumpy = numpy.arange(25, 43, 0.3, dtype=datatype)
        #pNumpy = numpy.append(pNumpy, max)#necessary because array from arange does not include last value

        pNumpy = numpy.linspace(min, max, quantity) #output is in float64 only when using this function!
        pNumpy = pNumpy.astype(dataType_)

        return pNumpy


    def checkNumpyEqualDataDistribution(self, pInNumpy_):
        """
        Check if values in a numpy array area equally distributed
        
        This function compares the intervals between values of a numpy array. If
        at least one of these intervals differentiates the data is not equally
        distributed. If it is equally distribute it can for example be represented
        with a minimum and maximum value as well as a value defining the number of values

        INPUT_PARAMETERS:
        pInNumpy        - Numpy array with one dimensions

        RETURN_VALUE:
        True if equally distributed, False if not
        """
    
        if pInNumpy_.shape[0] <= 1: #only one value in scalar dimension
            return True
        else:
            pNumpyGradient = numpy.gradient(pInNumpy_) #returns intervals between values in array
            for shape in range(1,pNumpyGradient.shape[0],1): #compare all intervalls
#################### ROUNDING necessary!
                valueMinus = numpy.round(pNumpyGradient[shape-1], 8)
                value = numpy.round(pNumpyGradient[shape], 8)

                if value != valueMinus: #Data not equally distribute if interval[i] isn't interval[i-1]
                    #print 'Data not equally distributed'
                    return False
        
            return True


    def createTimeValuesNumpy(self, units_, quantity_, timeStep_):
        """
        Creates numpy array with time values
        
        This function creates a one dimensional numpy array with time values defined by
        a reference time, a unit and a starting date, a number of values and a multiplicator
        for timedelta.
        
        INPUT_PARAMETERS:
        units           - Time unit and starting date of values (string) in the form of
            'unit since reference time' (e.g. 'hours since 1970-01-01 00:00:0.0'). The 
            following unit values are allowed: 'days', 'hours', 'minutes', 'seconds'
        quantity        - Duration, number of values to generate from the starting date (integer)
        timeStep        - Repeat interval, as multiplicator for timedelta (float), for example '0.5' (hours)
        
        RETURN_VALUE:
        Numpy array (one dimension) with time values        
        
        COMMENTS:
        The calculated time values in the numpy array have its reference date defined
        in the constant 'self.pDefaultSettings.varTimeAttrUnits' (module interface_Contants)
        """

        self.pDefaultSettings = DefaultSettings()

        dimTime = int(quantity_)
        timeStep = float(timeStep_)
        timeVarUnits = str(units_)

        #Split time unit and time starting date
        [timeVarRefUnit,timeVarRefTimeIso] = timeVarUnits.split(' since ')

        #Parse ISO8601 with python dateutil, convert to python datetime object
        pDatetimeVar = dateutil.parser.parse(timeVarRefTimeIso)

        #Necessary because keyword-arguments (like hours,...) cannot automatically filled in by a positional argument
        if timeVarRefUnit == 'days':
            pTimedelta = timedelta(days = timeStep)
        elif timeVarRefUnit == 'hours':
            pTimedelta = timedelta(hours = timeStep)
        elif timeVarRefUnit == 'minutes':
            pTimedelta = timedelta(minutes = timeStep)
        elif timeVarRefUnit == 'seconds':
            pTimedelta = timedelta(seconds = timeStep)
        #elif timeVarRefUnit == 'milliseconds': #not implemented yet
        #    pTimedelta = timedelta(milliseconds = timeStep)
        else:
            raise Exception("Error: Time unit unfortunately '" + str(timeVarRefUnit) + "' not implemented yet!")
        
        #Create Numpy array with time values by using NetCDF4 API functions
        dates = [pDatetimeVar+n*pTimedelta for n in range(dimTime)]
        pTimes = date2num(dates,units=str(self.pDefaultSettings.varTimeAttrUnits),calendar=str(self.pDefaultSettings.varTimeAttrCalendar))

############################################# PROBLEM TYPE OF TIME ARRAY, MUST ROUND IT
        #pTimes = pTimes.astype(numpy.float64)
        pTimes = numpy.around(pTimes, decimals = 8) #Necessary to round unequal values
     
        return pTimes


    def scaleNumpyDataVariable(self, pNumpyData_, varNr_, scaleFactor_):
        """Scale values of data variable #varNr in data variable array
        pNumpyData with value scaleFactor. varNr must be of same type as
        numpy data array"""

        pNumpyData = pNumpyData_

        #dimVar = pNumpyData.shape[0] #Number of variables in array
        dimT = pNumpyData.shape[1] #Time Dimension
        dimZ = pNumpyData.shape[2] #Level Dimensions
        dimY = pNumpyData.shape[3] #Last but one axis top to bottom: lat -> row
        dimX = pNumpyData.shape[4] #Last axis left to right: lon -> col

        pBuffer = numpy.zeros((dimY,dimX), dtype = pNumpyData.dtype)

        #Scale variable varNr_
        for i_time in range(0, dimT, 1):
            for i_z in range(0, dimZ, 1):
                pBuffer[:,:] = pNumpyData[varNr_,i_time,i_z,:,:]
                pBuffer[:,:] = numpy.cast[pNumpyData.dtype](pBuffer[:,:]*scaleFactor_)
                pNumpyData[varNr_,i_time,i_z,:,:] = pBuffer[:,:]

        return pNumpyData


    def dataType_2NetCdf(self, intype_):
        """Converts an input data type string to the related NetCDF data type string"""

#!!!Problems with string 'Byte' might occure, deactivate if necessary in module 'interface_Settings.py' (see known bugs)
        if (intype_ in BYTE):# or intype_ == 'Byte'): #'b' 'B' (byte)
            return 'i1'
        elif intype_ in SHORT: #'h' (short), 's'
            return 'i2'
        elif intype_ in INTEGER+LONG:#'i' (int), 'l' (long)
            return 'i4'
        elif intype_ in FLOAT: #'f' (float)
            return 'f4'
        elif intype_ in DOUBLE: #'d' (double)
            return 'f8'
        elif intype_ in STRING: #'c' (character)
            return 'S1'
        else:
            raise Exception("Type conversion failed: Data type '" + str(intype_) + \
            "' is unkown, not implemented yet, or not supported by NetCDF3. Valid data types are: '" + str(NETCDF3_DTYPES) + \
            "'. !!!Problems with string 'Byte' might occure, deactivate if necessary in module 'interface_Settings.py' (see known bugs)")


    def dataType_2Numpy(self, intype_):
        """Converts an input data type string to the related numpy dtype data type string"""

#!!!Problems with string 'Byte' might occure, deactivate if necessary in module 'interface_Settings.py' (see known bugs)
        #if intype_ in BOOL:
        #    return numpy.dtype(numpy.bool)
        if (intype_ in BYTE):# or intype_ == 'Byte'):
            return numpy.dtype(numpy.int8)
        #elif intype_ in U_BYTE:
        #    return numpy.dtype(numpy.uint8)
        elif intype_ in SHORT:
            return numpy.dtype(numpy.int16)
        elif intype_ in U_SHORT:
            return numpy.dtype(numpy.uint16)
        elif intype_ in FLOAT:
            return numpy.dtype(numpy.float32)
        elif intype_ in DOUBLE:
            return numpy.dtype(numpy.float64)
        elif intype_ in INTEGER:     
            return numpy.dtype(numpy.int32)
        elif intype_ in U_INTEGER:
            return numpy.dtype(numpy.uint32)
        elif intype_ in LONG:     
            return numpy.dtype(numpy.int64)
        elif intype_ in U_LONG:
            return numpy.dtype(numpy.uint64)
        else:
            raise Exception("Type conversion failed: Data type '" + str(intype_) + \
            "' is unkown, not implemented yet, or not supported by Numpy. Valid data types are: '" + str(NUMPY_DTYPES) + \
            "'. !!!Problems with string 'Byte' might occure, deactivate if necessary in module 'interface_Settings.py' (see known bugs)")


    def dataType_2Gdal(self, intype_):
        """Converts an input data type string to the related gdal data type string"""

#!!!Problems with string 'Byte' might occure, deactivate if necessary in module 'interface_Settings.py' (see known bugs)
        if (intype_ in BYTE or intype_ == 'Byte'):
            dataType = 'GDT_Byte'
        elif intype_ in SHORT:
            dataType = 'GDT_Int16'
        elif intype_ in U_SHORT:
            dataType = 'GDT_UInt16'
        elif intype_ in INTEGER:
            dataType = 'GDT_Int32'
        elif intype_ in U_INTEGER:
            dataType = 'GDT_UInt32'
        elif intype_ in FLOAT:
            dataType = 'GDT_Float32'
        elif intype_ in DOUBLE:
            dataType = 'GDT_Float64'
        else:
            raise Exception("Type conversion failed: Data type '" + str(intype_) + \
            "' is unkown, not implemented yet, or not supported by GDAL. Valid data types are: '" + str(GDAL_DTYPES) + \
            "'. !!!Problems with string 'Byte' might occure, deactivate if necessary in module 'interface_Settings.py' (see known bugs)")

        return dataType
    

    def string2List(self, inString_, separator_):
        """Converts a string to a list"""

        pList = (inString_.split(separator_))
        if pList == [''] or pList == ['None']: #e.g. for dimensionless variable
            return []
        else:
            return pList
        

    def list2String(self, inList_, oldSeparator_, newSeparator_):
        """Converts a list to a string by the use of an input list and a separator. Furthermore the separator
        can be changed to a new separator for the string (e.g. ',' replaced by ' ')"""

        string = oldSeparator_.join(inList_)
        return string.replace(oldSeparator_, newSeparator_)


    def convertBool(self, inBool_):
        """Converts an input boolean in the form of a string to a Python boolean"""

        text = str(inBool_)

        if text == "1" or text == "true" or text == "True":
            return True
        elif text == "0"  or text == "false" or text == "False" or text == '':
            return False
        else:
            raise Exception("Boolean value must be either true, True, 1, false, False, 0 or ''.")


    def checkDapperTimeSeriesFilename(self, infile_):
        """Check if a filename already ends with constant 'DECLARATION_NETCDF_STATION'
        and attaches this suffix if this is not the case"""

        infileName = str(infile_)
        if not infileName.endswith(DECLARATION_NETCDF_STATION):
            return infileName+DECLARATION_NETCDF_STATION #Add 'DECLARATION_NETCDF_STATION' to filename
        else:
            return infileName


    def checkUdunitsUnit(self, unit_):
        """Check if a unit is conform to the Udunits2 library.

        COMMENT:
        The program code of this function was adapted from the program 'cfchecks.py', version 2.0.2,
        written by Rosalyn Hatcher (Met Office, UK).

        IMPORTANT:
        Udunits2 must have been installed correctly with correct settings in this function as
        well as correct settings of the global Udunits constants in 'interface_Settings.py'.
        """

        self.pDefaultSettings = DefaultSettings()

        #Define settings
        #-------------------------------------------------------------------------------
        unit = unit_

        udunitsLib = self.pDefaultSettings.udunitsLib #UDUNITS_LIB
        udunitsKey = 'UDUNITS'

        # Use environment variables if available, otherwise udunits2.xml
        if environ.has_key(udunitsKey):
            udunits = environ[udunitsKey]
        else:
            udunits = str(self.pDefaultSettings.udunitsXml) #UDUNITS_XML
        udunits = udunits.strip()


        #Initialization of Udunits2
        #-------------------------------------------------------------------------------
        #--> Temporarily ignore messages to std error stream to prevent displaying of warnings "Defintion
        #override" by using ctypes callback functions to declare ut_error_message_handler(problem).
        #Solution supplied by Rosalyn Hatcher (Met Office, UK) that mentions the following source:
        #Trac #50, ctypes-mailing-list. 19.01.10

        problem = CFUNCTYPE(c_int,c_char_p)
        ut_set_error_message_handler = CFUNCTYPE(problem,problem)(("ut_set_error_message_handler",udunitsLib))
        ut_write_to_stderr = problem(("ut_write_to_stderr",udunitsLib))
        ut_ignore = problem(("ut_ignore",udunitsLib))
        old_handler = ut_set_error_message_handler(ut_ignore)

        udunitsUnitSystem = udunitsLib.ut_read_xml(udunits)
        if not udunitsUnitSystem:
            raise Exception("Error: Could not load Udunits2 XML database at location '" + str(udunits) + "'!")

        old_handler = ut_set_error_message_handler(ut_write_to_stderr)


        # Check if unit is recognized by Udunits package
        #-------------------------------------------------------------------------------
        # !Checks obviously no numbers if they are of type string!

        udunitsUnit = udunitsLib.ut_parse(udunitsUnitSystem, unit, "UT_ASCII")
        if udunitsUnit: #Unit recognized
            isUdunits = True
        else: #Unit not recognized
            isUdunits = False

        udunitsLib.ut_free(udunitsUnit) #Free up udunitsUnit ressources

        return isUdunits



#_______________________________________________________________________________

class ProcessXml:
    """Class with functions for processing xml files"""


    def __init__(self, xmlFileName_):
        """Constructor"""

        self.xmlFileName = str(xmlFileName_)
        self.pProcessingTool = ProcessingTool()

        self.pDefaultSettings = DefaultSettings()
       

    #def __del__(self):
        #"""Destructor"""

    
    def createEmptyXmlFile(self, namespaceURI_, qualifiedName_):
        """Creating new XML file with a namespace URI (string) and a qualified name (string)"""

        pDocXml = xml.dom.minidom.Document()
        pXmlElement = pDocXml.createElementNS(namespaceURI_, qualifiedName_)
        pXmlElement.setAttribute('xmlns', namespaceURI_) #Hack since xmlns is not written in step above

        pDocXml.appendChild(pXmlElement)

        pDocXml.writexml(open(str(self.xmlFileName), 'w'))
        pDocXml.unlink()

        return


    def createElement(self, posParentNode_, nameElement_):
        """Create new element (string) in parent node (string)"""

        pDocXml = xml.dom.minidom.parse(self.xmlFileName)

        for node_Element in pDocXml.getElementsByTagName(posParentNode_):
            newElement = pDocXml.createElement(nameElement_)

        node_Element.appendChild(newElement)

        pDocXml.writexml(open(str(self.xmlFileName), 'w'))
        pDocXml.unlink()

        return


    def checkIfElementExists(self, posParentNode_, nameElement_):
        """Check if element (string) in parent node (string) exists and return boolean"""

        pDocXml = xml.dom.minidom.parse(self.xmlFileName)

        for node_Element in pDocXml.getElementsByTagName(posParentNode_):
            if node_Element.getElementsByTagName(nameElement_):
                exists = True
            else:
                exists = False

        pDocXml.unlink()

        return exists


    def setAttribute(self, posParentNode_, posNameElement_, attrName_, attrValue_):
        """Set new attribute in XML file with name 'attrName' (string) and value 'attrValue'
        (string) at element with name 'posNameElement' (string) and parent node 'posParentNode' (string)"""

        pDocXml = xml.dom.minidom.parse(self.xmlFileName)

        for node_Element in pDocXml.getElementsByTagName(posNameElement_):
             if node_Element.parentNode.nodeName == posParentNode_:
                  node_Element.setAttribute(attrName_, attrValue_)

        pDocXml.writexml(open(str(self.xmlFileName), 'w'))
        pDocXml.unlink()

        return


    def readAttribute (self, posParentNode_, posNameElement_, posAttrName_):
        """Read attribute value with name 'posAttrName' (string) at element with name
        'posNameElement' (string) and its parent node with name 'posParentNode' (string)"""

        pDocXml = xml.dom.minidom.parse(self.xmlFileName)
               
        for node_Element in pDocXml.getElementsByTagName(posNameElement_):
            if node_Element.parentNode.nodeName == posParentNode_:
                attrValue = node_Element.getAttribute(posAttrName_)

        pDocXml.unlink()

        return attrValue


    def printXmlOnScreen(self):
        """Print Xml file on screen by using PrettyPrint"""

        #print result on screen
        pDocXml = xml.dom.minidom.parse(self.xmlFileName)
        xml.dom.ext.PrettyPrint(pDocXml)
        pDocXml.unlink()
        return


#-------------------------------------------------------------------------------

class ProcessNumpymeta(ProcessXml):
    """Class with functions for processing a coordinate metadata file (numpymeta). This class inherits
    from 'ProcessXML'"""

    def __init__(self, xmlFileName_):
        """Constructor"""
        ProcessXml.__init__(self, xmlFileName_) #call superclass


    #def __del__(self):
        #"""Desctructor"""


    def createMacroNumpymetaFile(self):
        """Creating a XML coordinate metatadata file by the use of the following macro"""

        infofile = open(str(self.xmlFileName),"w")

        #write file
        infofile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        infofile.write('<numpymeta>\n')
        infofile.write('    <time min="" max="" values= "" separator= ""/>\n')
        infofile.write('    <height min = "" max = "" values= "" separator= ""/>\n')
        infofile.write('    <latitude min = "" max = "" values= "" separator= ""/>\n')
        infofile.write('    <longitude min = "" max = "" values= "" separator= ""/>\n')
        infofile.write('    <id values= ""/>\n')
        infofile.write('</numpymeta>')

        infofile.close()

        return


    def writeNumpyMetadataValues(self, pNumpy_, tag_):
        """This function write values from a unidimensional numpy array to the XML coordinate
        metadata file at the element 'tag'(string) and creates this element if it does not exist.
        If data in the numpy array is equally distributed only the minimum and maximum value
        will be written to the XML file, otherwise all values."""

        numpyMin = numpy.min(pNumpy_)
        numpyMax = numpy.max(pNumpy_)

        if not self.checkIfElementExists('numpymeta', tag_): #add element if does not exist
            self.createElement('numpymeta', tag_)

        #Check if data in numpy array is equally distributed
        equalDataDistribution = self.pProcessingTool.checkNumpyEqualDataDistribution(pNumpy_)

        #if equally distribute write min and max values in metadata file
        if equalDataDistribution == True:
            if numpyMin == numpyMax: #if scalar value
                self.addNumpymetaValues(pNumpy_, tag_)
            else:
                self.setAttribute('numpymeta', tag_ , 'min', str(numpyMin))
                self.setAttribute('numpymeta', tag_ , 'max', str(numpyMax))

        #if not equally distributed write all values in metadata file
        else:
            self.addNumpymetaValues(pNumpy_, tag_)

        return


    def addNumpymetaValues(self, pDataNumpy_, tag_):
        """Adds values from a unidimensional numpy array to the XML coordinate
        metadata file at the element 'tag'(string) with its attribute 'values' that
        must already exist in the file."""

        pDataList = list() #value buffer
        pDataNumpy = pDataNumpy_
        for shape in range(0,pDataNumpy.shape[0],1):
            pDataList.append(str(pDataNumpy[shape]))
            pDataString = self.pProcessingTool.list2String(pDataList, ', ', ', ')
            self.setAttribute('numpymeta', tag_, 'values', str(pDataString))
            self.setAttribute('numpymeta', tag_, 'separator', ', ')

        return


#-------------------------------------------------------------------------------

class ProcessNcml(ProcessXml):
    """Class with functions for processing a NCML NetCDF XML file. All entries in this
    file must be in accordance with the NetCdf NCML XML file schema. This class inherits
    from 'ProcessXML'"""


    def __init__(self, xmlFileName_):
        """Constructor"""
        ProcessXml.__init__(self, xmlFileName_)


    #def __del__(self):
        #"""Destructor"""


    def createMacroNcmlFile(self):
        """Creates raw xml file according NetCDF Ncml XML schema, but without
        data variables. Attribute values are set according to CF-1.4 convention and internal
        definitions for gridded data, related to CEOP-AEGIS project."""

        
        infofile = open(str(self.xmlFileName),"w")
        
        #write header
        infofile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        infofile.write('<netcdf xmlns="http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2">\n')

        #write dimensions
        infofile.write('    <dimension name="'+str(self.pDefaultSettings.axisTimeName)+'" length="" isUnlimited="'+str(self.pDefaultSettings.dimTimeIsUnlimited)+'" />\n')
        infofile.write('    <dimension name="'+str(self.pDefaultSettings.axisHeightName)+'" length="" />\n')
        infofile.write('    <dimension name="'+str(self.pDefaultSettings.axisLatitudeName)+'" length="" />\n')
        infofile.write('    <dimension name="'+str(self.pDefaultSettings.axisLongitudeName)+'" length="" />\n')

        #write global attributes
        infofile.write('    <attribute name="Conventions" value="'+str(self.pDefaultSettings.attrConventions)+'" />\n')
        infofile.write('    <attribute name="title" value="" />\n')
        infofile.write('    <attribute name="institution" value="'+str(self.pDefaultSettings.attrInstitution)+'" />\n')
        infofile.write('    <attribute name="source" value="" />\n')
        infofile.write('    <attribute name="history" value="Ncml creation date: '+ \
        time.ctime(time.time())+'" />\n')
        infofile.write('    <attribute name="references" value="" />\n')
        infofile.write('    <attribute name="comment" value="" />\n')

        #write coordinate variables
        #---------------------------------------------------------------------------
        #write time variable
        infofile.write('    <variable name="'+str(self.pDefaultSettings.axisTimeName)+'" shape="'+str(self.pDefaultSettings.axisTimeName)+'" type="'+str(self.pDefaultSettings.varTimeType)+'">\n')
        infofile.write('        <attribute name="units" value="'+self.pDefaultSettings.varTimeAttrUnits+'" />\n')
        infofile.write('        <attribute name="long_name" value="time" />\n')
        infofile.write('        <attribute name="standard_name" value="time" />\n')
        infofile.write('        <attribute name="calendar" value="'+str(self.pDefaultSettings.varTimeAttrCalendar)+'" />\n')
        infofile.write('        <attribute name="axis" value="T" />\n')
        infofile.write('    </variable>\n')

        #write height variable
        infofile.write('    <variable name="'+str(self.pDefaultSettings.axisHeightName)+'" shape="'+str(self.pDefaultSettings.axisHeightName)+'" type="'+str(self.pDefaultSettings.varHeightType)+'">\n')#should be float!!!
        infofile.write('        <attribute name="units" value="" />\n')
        infofile.write('        <attribute name="long_name" value="" />\n')
        infofile.write('        <attribute name="standard_name" value="" />\n')
        infofile.write('        <attribute name="positive" value="'+str(self.pDefaultSettings.varHeightAttrPositive)+'" />\n')
        infofile.write('        <attribute name="axis" value="Z" />\n')
        infofile.write('    </variable>\n')

        #write latitude variable
        infofile.write('    <variable name="'+str(self.pDefaultSettings.axisLatitudeName)+'" shape="'+str(self.pDefaultSettings.axisLatitudeName)+'" type="'+str(self.pDefaultSettings.varLatitudeType)+'">\n')#should be float!!!
        infofile.write('        <attribute name="units" value="'+str(self.pDefaultSettings.varLatitudeAttrUnits)+'" />\n')
        infofile.write('        <attribute name="long_name" value="latitude" />\n')
        infofile.write('        <attribute name="standard_name" value="latitude" />\n')
        infofile.write('        <attribute name="axis" value="Y" />\n')
        infofile.write('    </variable>\n')

        #write longitude variable
        infofile.write('    <variable name="'+str(self.pDefaultSettings.axisLongitudeName)+'" shape="'+str(self.pDefaultSettings.axisLongitudeName)+'" type="'+str(self.pDefaultSettings.varLongitudeType)+'">\n')#should be float!!!
        infofile.write('        <attribute name="units" value="'+str(self.pDefaultSettings.varLongitudeAttrUnits)+'" />\n')
        infofile.write('        <attribute name="long_name" value="longitude" />\n')
        infofile.write('        <attribute name="standard_name" value="longitude" />\n')
        infofile.write('        <attribute name="axis" value="X" />\n')
        infofile.write('    </variable>\n')

        #write data variables --> done by other functions
        
        #write EOF
        infofile.write('</netcdf>')

        #close file
        infofile.close()

        return


    def changeMacroForStation(self):
        """Change entries of a NCML NetCDF XML macro file that was created for gridded data
        to the Dapper In-situ Data Conventions (epic-insitu-1.0) so that the resulting
        NetCDF file can be handled by DChart/Daper as in-situ time series data.

        IMPORTANT:
        - Data variables (in CF format of type float32) must furthermore have the attribute 'coordinates' with the value
            'time elev latitude longitude'
        - A NetCDF file that is considered as sation time series data must have the filename
            suffix '_time_series.nc'
        """

        #Dimensions
        #-------------------------------------------------------------------------------

####################TEMPORARILY UNLIMITED (for MFDataset), but must obvioulsy be limited for Dapper
        #Obviously 'time' dimension can't be of unlimited size
        #self.changeDimension(str(self.pDefaultSettings.axisTimeName), 'isUnlimited', 'false')

        #Dimension 'height' needs to to be named 'elev' due to a glitch in the dapperload program
        self.changeDimension(str(self.pDefaultSettings.axisHeightName), 'name', 'elev')

        #Dimensions 'height', 'latitude' and 'longitude' must be scalar (of length '1'), since they represents a time
        #series data of a station (for profile: dimension time = '1', height = variant)
        self.changeDimension('elev', 'length', '1')
        self.changeDimension(str(self.pDefaultSettings.axisLatitudeName), 'length', '1')
        self.changeDimension(str(self.pDefaultSettings.axisLongitudeName), 'length', '1')


        #Attributes
        #-------------------------------------------------------------------------------
        #Compare global attribute 'Conventions' that must be set to 'CF-1.4, epic-insitu-1.0'
        self.changeGlobalAttribute('Conventions', 'value', 'CF-1.4, epic-insitu-1.0')


        #Variables
        #-------------------------------------------------------------------------------

        #Coordinate variable 'height' needs to to be named 'elev' with shape 'elev' due to a glitch in the dapperload program
        self.changeVariable(str(self.pDefaultSettings.axisHeightName), 'name', 'elev')
        self.changeVariable('elev', 'shape', 'elev')
       
        #The 'time' coordinate variable must always be of the type 'float64'
        self.changeVariable(str(self.pDefaultSettings.axisTimeName), 'type', 'double')

        #The 'elev', 'latitude' and 'longitude' coordinate variables must be of the type 'float32' or 'float64'. They all must be of the same type.
        self.changeVariable('elev', 'type', 'float')
        self.changeVariable(str(self.pDefaultSettings.axisLatitudeName), 'type', 'float')
        self.changeVariable(str(self.pDefaultSettings.axisLongitudeName), 'type', 'float')

        #Exactly one scalar variable with name '_id' of type 'int32' and with a unique value for each entry of outer sequence is necessary
        self.addVariable('_id', "", 'int')
        self.addLocalAttribute('_id', 'long_name', "station id variable", "", "")


        #!Not to forget for data variables!

        #All data variables must either be of type 'float32' or 'double'. They all should have the same type
        #All data variables must have 'coordinates' attributes in the form of 'time elev latitude longitude'.
     

        #Miscellaneous
        #-------------------------------------------------------------------------------

        #NetCdf file as well as Dapper dataset must have filename suffix '_time_series.nc'!

        #Time unit 'milliseconds since 1970-01-01 00:00:0.0' is recommended by Dapper

        #If necessary, add global attributes according to
        #Unidata Point Observation Dataset Convention or Dapper In-situ Data Conventions !

        return


    def fillNcmlMacroWithNumpy(self, pNumpyData_):
        """Fill metadata in NCML file by the metadata that can be extracted out of 
        input numpy data array (numpy array in shape of grid or station file)"""
    
        #Get metadata information from file
        #-------------------------------------------------------------------------------
        pNumpyData = pNumpyData_

        if pNumpyData.ndim == 2: #(time, variable) considered as station data
            dimVar = pNumpyData.shape[1] #Number of variables in table
            dimT = pNumpyData.shape[0]  #Time Dimension
            dimZ = int(1) #Station only has one coordinate
            dimY = int(1)
            dimX = int(1)

        elif pNumpyData.ndim == 5: #(variable, time, z, lat, lon) considered as grid data
            dimVar = pNumpyData.shape[0] #Number of variables in array
            dimT = pNumpyData.shape[1] #Time Dimension
            dimZ = pNumpyData.shape[2] #Height Dimensions
            dimY = pNumpyData.shape[3] #Last but one axis top to bottom: lat -> row
            dimX = pNumpyData.shape[4] #Last axis left to right: lon -> col

        else:
            raise Exception("Error: Numpy data file can't be read since number of dimensions '" \
            + str(pNumpyData.ndim) + "' is not allowed.")

        #Write metadata NCML file
        #-------------------------------------------------------------------------------
        self.changeDimension(str(self.pDefaultSettings.axisTimeName), 'length', str(dimT))
        self.changeDimension(str(self.pDefaultSettings.axisHeightName), 'length', str(dimZ))
        self.changeDimension(str(self.pDefaultSettings.axisLatitudeName), 'length', str(dimY))
        self.changeDimension(str(self.pDefaultSettings.axisLongitudeName), 'length', str(dimX))
          

        #Write data variables
        for i_var in range(0,dimVar,1): # otherwise returns list of ints from >= start and < end: 0 .. 10
            varName = 'variable #'+str(i_var)
            stringVarShape = str(self.pDefaultSettings.axisTimeName) + " " + str(self.pDefaultSettings.axisHeightName) \
                + " " + str(self.pDefaultSettings.axisLatitudeName) + " " + str(self.pDefaultSettings.axisLongitudeName)
            self.addVariable(varName, stringVarShape, str(pNumpyData.dtype))
            self.addLocalAttribute(varName, "units", "", "", "")
            self.addLocalAttribute(varName, "long_name", "", "", "")
            self.addLocalAttribute(varName, "standard_name", "", "", "")
            self.addLocalAttribute(varName, "_FillValue", "", str(pNumpyData.dtype), "")

        return


    def addDimension(self, dimName_, dimLength_, dimIsUnlimited_):
        """Creates a dimension element in a NCML XML file with the name 'dimName' (string),
        the lenght 'dimLength' (string) and the value 'dimIsUnlimited' (string)
        in a NCML XML file unless 'dimIsUnlimited' is not set to '' """

        pDocNcml = xml.dom.minidom.parse(self.xmlFileName)

        for node_Dim in pDocNcml.getElementsByTagName('netcdf'):

            dim = pDocNcml.createElement('dimension')

            dim.setAttribute('name', dimName_)
            dim.setAttribute('length', dimLength_)

            #optional, if isUnlimited is necessary
            if dimIsUnlimited_ != '':
                dim.setAttribute('isUnlimited', dimIsUnlimited_)

            node_Dim.appendChild(dim)

        pDocNcml.writexml(open(str(self.xmlFileName), 'w'))
        pDocNcml.unlink()

        return
    

    def changeDimension(self, posDimName_, posDimAttr_, newAttrValue_):
        """Change the attribute value of the dimensions entry 'posDimAttr' (string)
        at the dimension 'posDimName' (string) with the new value 'newAttrValue' (string)
        in a NCML XML file"""

        pDocNcml = xml.dom.minidom.parse(self.xmlFileName)

        for node_Dim in pDocNcml.getElementsByTagName('dimension'):
            if node_Dim.parentNode.nodeName == 'netcdf':
                searchDimName = node_Dim.getAttributeNode('name')
                if searchDimName.value == posDimName_:
                    node_Dim.setAttribute(posDimAttr_, newAttrValue_)

        pDocNcml.writexml(open(str(self.xmlFileName), 'w'))
        pDocNcml.unlink()

        return

    
    def addGlobalAttribute(self, attrName_, attrValue_, attrType_, attrSeparator_):
        """Creates a global attribute element in a NCML XML file with the name 'attrName' (string),
        the value 'attrValue' (string),  the type 'attrType' (string) and the separator 'attrSeparator_' (char) in a NCML XML file
        unless type is not set to ''"""

        pDocNcml = xml.dom.minidom.parse(self.xmlFileName)

        for node_Attr in pDocNcml.getElementsByTagName('netcdf'):

            globalAttr = pDocNcml.createElement('attribute')

            globalAttr.setAttribute('name', attrName_)
            globalAttr.setAttribute('value', attrValue_)

            #optional, if type is necessary
            if attrType_ != '':
                globalAttr.setAttribute('type', attrType_)

            #optional, if type is necessary
            if attrSeparator_ != '':
                localAttr.setAttribute('separator', attrSeparator_)

            node_Attr.appendChild(globalAttr)

        pDocNcml.writexml(open(str(self.xmlFileName), 'w'))
        pDocNcml.unlink()

        return


    def changeGlobalAttribute(self, posAttrName_, posAttrType_, newAttrValue_):
        """Change a attribute value of the global attributes entry 'posAttrType' (string)
        at the global attribute 'posAttrName' (string) with the new value 'newAttrValue' (string)
        in a NCML XML file"""

        pDocNcml = xml.dom.minidom.parse(self.xmlFileName)

        for node_Attr in pDocNcml.getElementsByTagName('attribute'):
            if node_Attr.parentNode.nodeName == 'netcdf':
                searchAttrName = node_Attr.getAttributeNode('name')
                if searchAttrName.value == posAttrName_:
                    node_Attr.setAttribute(posAttrType_, newAttrValue_)

        pDocNcml.writexml(open(str(self.xmlFileName), 'w'))
        pDocNcml.unlink()

        return


    def addVariable(self, varName_, varShape_, varType_):
        """Add a new variable to a NCML XML file with the name 'varName' (string),
        the shape 'varShape' (string) and the type 'varType' (string)"""

        pDocNcml = xml.dom.minidom.parse(self.xmlFileName)

        for node_Var in pDocNcml.getElementsByTagName('netcdf'):

            var = pDocNcml.createElement('variable')

            var.setAttribute('name', varName_)
            var.setAttribute('shape', varShape_)
            var.setAttribute('type', varType_)

            node_Var.appendChild(var)

        pDocNcml.writexml(open(str(self.xmlFileName), 'w'))
        pDocNcml.unlink()

        return


    def changeVariable(self, posVarName_, posVarAttr_, newAttrValue_):
        """Change a variables metadata value with the new value 'newAttrValue' (string)
        at the entry 'posVarAttr' (string) at the variable with name 'posVarName' (string)
        in a NCML XML file"""

        pDocNcml = xml.dom.minidom.parse(self.xmlFileName)

        for node_Var in pDocNcml.getElementsByTagName('variable'):
            if node_Var.parentNode.nodeName == 'netcdf':
                searchVarName = node_Var.getAttributeNode('name')
                if searchVarName.value == posVarName_:
                    node_Var.setAttribute(posVarAttr_, newAttrValue_)

        pDocNcml.writexml(open(str(self.xmlFileName), 'w'))
        pDocNcml.unlink()

        return


    def addLocalAttribute(self, posVarName_, attrName_, attrValue_, attrType_, attrSeparator_):
        """Add a local attribute with name 'attrName' (string), value 'attrValue' (string),
        type 'attrType' (string) and separator 'attrSeparator_' (char) to the existing variable with name 'posVarName' (string) in a
        NCML XML file. If the type 'attrType' is set to '' there will be no entry"""

        pDocNcml = xml.dom.minidom.parse(self.xmlFileName)

        for node_Attr in pDocNcml.getElementsByTagName('variable'):
            if node_Attr.parentNode.nodeName == 'netcdf':
                searchVarName = node_Attr.getAttributeNode('name')
                if searchVarName.value == posVarName_:

                    localAttr = pDocNcml.createElement('attribute')

                    localAttr.setAttribute('name', attrName_)
                    localAttr.setAttribute('value', attrValue_)

                    #optional, if type is necessary
                    if attrType_ != '':
                        localAttr.setAttribute('type', attrType_)

                    #optional, if type is necessary
                    if attrSeparator_ != '':
                        localAttr.setAttribute('separator', attrSeparator_)

                    node_Attr.appendChild(localAttr)

        pDocNcml.writexml(open(str(self.xmlFileName), 'w'))
        pDocNcml.unlink()

        return


    def changeLocalAttribute(self, posVarName_, posAttrName_, posAttrType_, newAttrValue_):
        """Change a local attribute value with the new value 'newAttrValue' (string)
        at the entry 'posAttrType' (string) at the local attribute with name 'posAttrName'
        (string) attached to the variable with name 'posVarName' (string) in a NCML XML file"""

        pDocNcml = xml.dom.minidom.parse(self.xmlFileName)

        for node_Var in pDocNcml.getElementsByTagName('variable'):
            if node_Var.parentNode.nodeName == 'netcdf':
                searchVarName = node_Var.getAttributeNode('name')
                if searchVarName.value == posVarName_:
                    for node_Attr in node_Var.getElementsByTagName('attribute'):
                        searchAttrName = node_Attr.getAttributeNode('name')
                        if searchAttrName.value == posAttrName_:
                            node_Attr.setAttribute(posAttrType_, newAttrValue_)

        pDocNcml.writexml(open(str(self.xmlFileName), 'w'))
        pDocNcml.unlink()

        return


    def removeLocalAttribute(self, posVarName_, posAttrName_):
        """"Remove a local attribute with name 'posAttrName'
        (string) attached to the variable with name 'posVarName' (string) in a NCML XML file"""

        pDocNcml = xml.dom.minidom.parse(self.xmlFileName)

        for node_Var in pDocNcml.getElementsByTagName('variable'):
            if node_Var.parentNode.nodeName == 'netcdf':
                searchVarName = node_Var.getAttributeNode('name')
                if searchVarName.value == posVarName_:
                    for node_Attr in node_Var.getElementsByTagName('attribute'):
                        searchAttrName = node_Attr.getAttributeNode('name')
                        if searchAttrName.value == posAttrName_:
                            node_Var.removeChild(node_Attr)

        pDocNcml.writexml(open(str(self.xmlFileName), 'w'))
        pDocNcml.unlink()

        return

