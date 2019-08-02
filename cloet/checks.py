#!/usr/bin/env python
import os

class BoundsException(Exception):
    def __init__(self,msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class ScenarioException(Exception):
    def __init__(self,msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class RouteException(Exception):
    def __init__(self,msg):
        self.msg = msg
    def __str__(self):
        return self.msg


def check_ul(name,value,min_val=0,max_val=1):
    """
    Description
    -----------
    Check that a value is within the minimum and maximum bounds for a parameter

    Arguments
    ----------
    name   : string, name of parameter being evaluated
    value  : float, value of parameter to be evaluated
    min_val: float, minimum value that parameter can have
    max_val: flaot, maximum value that parameter can have

    Returns
    ---------
    float, passed value if value within both bounds, otherwise and exception is raised
    """
    if (value < min_val) or (value > max_val):
        raise BoundsException("bounds of "+name+" are outside of range ("+
                              str(min_val)+" <= value <= "+str(max_val)+")")

    return value

def check_l(name,value,min_val=0):
    """
    Description
    -----------
    Check that a value is above the minimum value for a parameter

    Arguments
    ----------
    name   : string, name of parameter being evaluated
    value  : float, value of parameter to be evaluated
    min_val: float, minimum value that parameter can have

    Returns
    ---------
    float, passed value if value above the lower bound, otherwise and exception is raised
    """
    if (value < min_val):
        raise BoundsException("bounds of "+name+" are outside of range ("+
                              str(min_val)+" <= value <= "+str(max_val)+")")

    return value

def check_u(name,value,max_val=1):
    """
    Description
    -----------
    Check that a value is below the maximum value for a parameter

    Arguments
    ----------
    name   : string, name of parameter being evaluated
    value  : float, value of parameter to be evaluated
    max_val: float, maximum value that parameter can have

    Returns
    ---------
    float, passed value if value below the upper bound, otherwise and exception is raised
    """
    if (value < min_val) or (value > max_val):
            raise BoundsException("bounds of "+name+" are outside of range ("+
                                  str(min_val)+" <= value <= "+str(max_val)+")")

    return value

def checkfile(file_name):
    """
    checkfile(file_name)

    (Hidden) Function to check if a file name exists in the current working
    directory and rename the new file, rather than overwrite the old file
    with new data.

    Arguments
    ----------
    file_name : database name tag in .my.cnf file (default=None)

    Returns
    ---------
    string, name of non-existent file in current working directory
    """
    cwd = os.getcwd()
    cwf = os.path.join(cwd,file_name)
    if not os.path.exists(cwf):
        return cwf
    root, ext = os.path.splitext(os.path.expanduser(cwf))
    dir = os.path.dirname(root)
    fname = os.path.basename(root)
    candidate = fname+ext
    index = 1
    ls = set(os.listdir(dir))
    while candidate in ls:
        candidate = "{}_{}{}".format(fname,index,ext)
        index += 1
    return os.path.join(dir,candidate)
