from .checks import checkfile
import datetime

def __units(key):
    units = {"ADD": "mg/kg-day",
             "I": "mg/day",
             "Dexp": "mg/day",
             "NW": "workers",
             "LADD":"mg/kg-day",
             "ADD": "mg/kg-day",
             "APDR": "mg/kg-day",
             "NS": "sites",
             "Sd": "shift/workder-day",
             "EF":"mg/kg",
             "AH":"kg/worker-shift",
             "Ys":"dimensionless",
             "NWexp":"worker/site",
             "ED": "days/site-yr",
             "EY": "years",
             "BW": "kg",
             "ATc": "years",
             "AT": "years",
             "S":"cm^2",
             "Qu":"mg/cm^2-event",
             "Yderm":"dimensionless",
             "FT":"events/workers-day",
             "Cv":"ppm",
             "Cm":"mg/m^3",
             "T":"K",
             "G":"g/s",
             "MW":"g/mol",
             "Q":"ft^3/min",
             "k":"dimensionless",
             "X":"dimensionless",
             "VP":"torr",
             "Vm":"L/mol",
             "b":"m^3/hr",
             "h":"hrs/day",
             "KCk":"mg/m^3",
             "Ypel":"dimensionless",
             "Cvk":"ppm",
             "VPpel":"torr",
             "MWpel":"g/mol",
             "Ymist":"dimensionless",
             "Ysf":"dimensionless",
            }
    return units[key]

def date_stamp(prefix, suffix):
    """
    date_stamp(prefix, suffix)

    Introduce a date stamp into a string.

    For files that are generated by code, it is easy to distinguish different versions of the same
    file by adding a date to the file. The date in the form MMDDYYYY is added before the suffix of
    the file (e.g. file extenstion).

    Arguments
    ----------
    prefix : the root name of file
    suffix : the extension of the file
    out : a string that is of the form prefix_MMDDYYYY.suffix

    Returns
    ---------
    string, string with prefix and suffix joined with the date
    """

    hoy = str(datetime.date.today())
    hoy = hoy.split("-")
    hoy = [hoy[1],hoy[2],hoy[0]]
    return "_".join([prefix,"".join(hoy)])+"."+suffix


def json_report(model):
    """
    Description
    -----------
    Generate a JSON object that contains all attributes of a ChemSTEER model run

    Arguments
    ----------
    model: chemsteer.dermal or chemsteer.inhalation model class

    Returns
    ---------
    dictionary, JSON-like structure containing all model attributes
    """
    equations = {}
    for equation in model.equations.split("\n"):
        if equation.strip() == "": continue
        lhs = equation.split(" = ")[0].strip()
        rhs = equation.split(" = ")[-1].strip()
        equations[lhs] = rhs


    report = dict(route=model.route,
                  model_name = model.model_name,
                  scenario = model.scenario,
                  equations = equations,
                  inputs = model.inputs,
                  outputs = model.outputs)

    return report


def text_report(model):
    """
    Description
    -----------
    Generate a string that contains all attributes of a ChemSTEER model run

    Arguments
    ----------
    model: chemsteer.dermal or chemsteer.inhalation model class

    Returns
    ---------
    string, string containing all model attributes
    """
    report = json_report(model)
    k_len = (list(report['equations'].keys()) +
             list(report['inputs'].keys()) +
             list(report['outputs'].keys()))
    k_len = max([len(k) for k in k_len])

    s = "|"+"".join(["-"]*88)+"|\n"

    s += ("| Exposure Route: {route}{space:>{width}}|\n"
          .format(route=report['route'], space=" ",
                  width=90-19-len(report['route'])))
    s += ("| Exposure Model: {model}{space:>{width}}|\n"
          .format(model=report['model_name'],space=" ",
                  width=90-19-len(report['model_name'])))
    s += ("| Exposure Scenario: {model}{space:>{width}}|\n"
          .format(model=report['scenario'],space=" ",
                  width=90-22-len(report['scenario'])))

    s += ("|"+"".join(["-"]*88)+"|\n")

    s += ("| Model Equations: {space:>{width}}|\n"
          .format(model=report['scenario'],space=" ",width=90-20))

    for key, value in report['equations'].items():
        s += ("|     {rhs:>{rhsw}} = {lhs}{space:>{sw}}|\n"
              .format(rhs=key,rhsw=k_len,lhs=value,space=" ",
                      sw=90-5-k_len-len(key)-(k_len-len(key))-len(value)))

    s += ("|"+"".join(["-"]*88)+"|\n")

    s += ("| Model Inputs: {space:>{width}}|\n"
          .format(model=report['scenario'],space=" ",width=90-17))

    for key, value in report['inputs'].items():
        s += ("|     {rhs:>{rhsw}} = {lhs} {units}{space:>{sw}}|\n"
              .format(rhs=key,rhsw=k_len,lhs=value,units=__units(key),space=" ",
                      sw=90-6-k_len-len(key)-(k_len-len(key))-len(str(value))-len(__units(key))))

    s += ("|"+"".join(["-"]*88)+"|\n")

    s += ("| Model Results: {space:>{width}}|\n"
          .format(model=report['scenario'],space=" ",width=90-18))

    for key, value in report['outputs'].items():
        if type(value) == int:
            l = len("{lhs}".format(lhs=value))
            s += ("|     {rhs:>{rhsw}} = {lhs} {units}{space:>{sw}}|\n"
                  .format(rhs=key,rhsw=k_len,lhs=value,units=__units(key),
                          space=" ",sw=90-6-k_len-len(key)-(k_len-len(key))-l-len(__units(key))))
        else:
            test = "{:.5}".format(value)
            if len(test)>5:
                l = len("{lhs:.4e}".format(lhs=value))
                s += ("|     {rhs:>{rhsw}} = {lhs:.4e} {units}{space:>{sw}}|\n"
                      .format(rhs=key,rhsw=k_len,lhs=value,space=" ",units=__units(key),
                              sw=90-6-k_len-len(key)-(k_len-len(key))-l-len(__units(key))))
            else:
                l = len("{lhs:.5}".format(lhs=value))
                s += ("|     {rhs:>{rhsw}} = {lhs:.5} {units}{space:>{sw}}|\n"
                      .format(rhs=key,rhsw=k_len,lhs=value,space=" ",units=__units(key),
                              sw=90-6-k_len-len(key)-(k_len-len(key))-l-len(__units(key))))
    s += ("|"+"".join(["-"]*88)+"|\n")
    return s

def file_report(model,filename=None,check_file=True):
    """
    Description
    -----------
    Print a file that contains all information of a ChemSTEER model run

    Arguments
    ----------
    model     : chemsteer.dermal or chemsteer.inhalation model class
    filename  : None or string, name of file to contain model report; if None name is
                generated from `model`'s attributes: `model_name` and `scenario` (default:
                None)
    check_file: boolean, check whether or not filename exists in current working
                directory; if True, the same name will be used but with a unique integer
                appended to the file's name; if False, the existing file will be
                overridden (default: True)
    """
    report = json_report(model)
    if filename == None:
        filename = "_".join([report['model_name'].lower().replace(" ","_"),
                             report['scenario']])
        filename = date_stamp(prefix=filename,suffix="txt")
    if check_file:
        filename = checkfile(filename)
    report = text_report(model)

    with open(filename,'w') as f:
        f.write(report)

    return filename