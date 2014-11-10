#! /usr/bin/python
# -*- coding: latin1 -*-

"""
Data class for Interface.

This class is storing metadata of dimensions, attributes and variables as well as
data of variables in an internal data model.
Metadata information must be provided according to NetCDF NCML XML file schema.
Data information can be attached to a variable as numpy array.
"""

__author__= "Nicolai Holzer"
__author_email__ = "first-name dot last-name @ mailbox.tu-dresden.de"
__date__ ="2011-04-14"
__version__ = "v0.1.2"


#Changelog
#-------------------------------------------------------------------------------
#2001-04-14: v0.1.2 little changes for new data conversions
#2010-11-22: v0.1.1 comments and docstrings added
#2010-10-08: v0.1.0 first version


#Imported libraries
#-------------------------------------------------------------------------------
#standard libraries
#related libraries
import numpy

#local applications / library specific import

#===============================================================================



class Dimension:
    """Class for storing NetCDF dimension information"""


    def __init__(self, name_, length_, isUnlimited_ ):
        """
        Constructor for new dimension.

        INPUT_PARAMETERS:
        name        - name of dimension (string)
        length      - length of dimension (integer)
        isUnlimited - flag if dimension is unlimited (boolean)
        """
       
        self.name = str(name_)
        self.length = int(length_)
        self.isUnlimited = bool(isUnlimited_)


    def getName(self):
        """Return dimension name"""
        return self.name


    def getLength(self):
        """Return dimension lenght"""
        return self.length


    def getIsUnlimited(self):
        """Return boolean if dimension is of unlimited lenght"""
        return self.isUnlimited


#_______________________________________________________________________________

class Attribute:
    """Class for storing NetCDF attribute information"""


    def __init__(self, name_, type_, value_, separator_):
        """
        Constructor for new attribute.

        INPUT_PARAMETERS:
        name        - name of attribute (string)
        type        - type of attribute (string). Valid declarations defined in 'interface_Settings'
        value       - value of attribute (string)
        separator   - separator for multiple attribute values (character)
        """

        self.name = str(name_)
        self.type = str(type_)
        self.value = str(value_)
        self.separator = str(separator_)


    def getName(self):
        """Return attribute name"""
        return self.name


    def getType(self):
        """Return attribute type"""
        return self.type


    def getValue(self):
        """Return attribute value"""
        return self.value

    def getSeparator(self):
        """Return attribute separator"""
        return self.separator

#_______________________________________________________________________________

class Variable:
    """Class for storing NetCDF variable information"""


    def __init__(self, name_, shape_, type_):
        """
        Constructor for new variable.

        INPUT_PARAMETERS:
        name        - name of variable (string)
        shape       - shape of variable (string). Names of shapes separated by space
        type        - type of variable (string). Valid declarations defined in 'interface_Settings'
        """

        self.name = str(name_)
        self.shape = str(shape_)
        self.type = str(type_)

        self.pAttributeList = list()


    def addAttribute(self, name_, type_, value_, separator_):
        """Add attribute to variable by attaching new attribute class to variable attribute list"""
        pAttribute = Attribute(name_, type_, value_, separator_)
        self.pAttributeList.append(pAttribute)
        return


    def addData(self, numpy_):
        """Attach data to variable as numpy array"""
        self.pDataNumpy = numpy_
        return


    def getData(self):
        """Return attached data of variable as numpy array"""
        return self.pDataNumpy


    def getName(self):
        """Return variable name"""
        return self.name


    def getShape(self):
        """Return variable shape"""
        return self.shape


    def getType(self):
        """Return variable type"""
        return self.type


    def getAttributes(self):
        """Return list of variable attribute classes"""
        return self.pAttributeList
