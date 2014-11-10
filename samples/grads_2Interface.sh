#!bin/sh

#Batch to convert GRADS readable files to NetCDF
#__author__= "Nicolai Holzer"
#__author_email__ = "first-name dot last-name @ mailbox.tu-dresden.de"
#__date__ ="2011-01-07"
#__version__ = "v0.1.1" #MajorVersion(backward_incompatible).MinorVersion(backward_compatible).Patch(Bug_fixes)


#Define Input data
DATADIR='data/' #Directory of data
DATAFILES='post.ctl_2008*' #Name of data files with or without wildcard
SUFFIX=''


clear

#Convert all GRADS files to data model files
for i in $DATADIR$DATAFILES$SUFFIX
do
    python grads_2Interface.py grads2Model $i -c -n 0 -p '' -s 25 72 -t float32 # -l
done


#Convert all data model files to NetCDF files
for j in $DATADIR$DATAFILES'__data.npy'
do
    python interface_Main.py model2Nc $j -p '' -f '' #-i -c -m -v -l
done


#Optional: Aggregate all NetCDF files to one single NetCDF file
python interface_Main.py nc2Nc $DATAFILES -p $DATADIR -f cf+default #-i -c -m -v -l


#echo `pwd`