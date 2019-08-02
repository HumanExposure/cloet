#!/usr/bin/env python

def potential_dose_rate(route,**kwargs):
    """
    Potential dose rate

    Usage
    -----
    potential_dose_rate(route,**kwargs)

    Arguments
    ---------
    route   : string, type of exposure route whose arguments are passed ['dermal'|
              'inhalation']; if 'dermal', `Dexp` is calculated; if 'inhalation', `I` is
              calculated
    **kwargs: dictionary, terms of exposure equation; dependent on exposure route passed

    Returns
    --------
    float, potential dose rate (mg/day)
    """
    if route == "dermal":
        if 'SQu' in kwargs.keys():
            return kwargs['SQu'] * kwargs['Yderm'] * kwargs['FT']
        else:
            return kwargs['S'] * kwargs['Qu'] * kwargs['Yderm'] * kwargs['FT']
    elif route == 'inhalation':
        if 'Cm' in kwargs.keys():
            return kwargs['Cm'] * kwargs['b'] * kwargs['h']
        else:
            return kwargs['EF'] * kwargs['AH'] * kwargs['Ys'] * kwargs['Sd']
    else:
        raise RouteException("unknown exposure route provided ("+str(route)+")")


def workers_exposed(NWexp,NS,**kwargs):
    """
    Total number of workers exposed

    Usage
    -----
    workers_exposed(NWexp,NS)

    Arguments
    ---------
    NWexp: number of workers exposed while performing an activity at a single site
    NS   : number of sites where activity is performed

    Returns
    --------
    integer, total number of workers exposed (workers)
    """
    return NWexp * NS


def daily_dose(PDR, ED, EY, BW, t, **kwargs):
    """
    (Lifetime) Average daily dose

    Usage
    -----
    daily_dose(route,**kwargs)

    Arguments
    ---------
    PDR: potential dose rate (mg/day)
    ED : days exposed per year (days/site-yr)
    EY : years of occupational exposure (years)
    BW : body weight (kg)
    t  : averaging time (years)

    Returns
    --------
    float, average daily dose (mg/kg-day)
    """
    days_per_year = 365
    return (PDR * ED * EY) / (BW * t * days_per_year)

def acute_potential_dose_rate(PDR, BW, **kwargs):
    """
    Acute potential dose rate

    Usage
    -----
    acute_potential_dose_rate(PDR,BW)

    Arguments
    ---------
    PDR: potential dose rate (mg/day)
    BW : body weight (kg)

    Returns
    --------
    float, acute potential dose rate (mg/kg-day)
    """
    return PDR / BW
