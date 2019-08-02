from . import checks
from . import exposures

class dermal_model(object):
    """
    A Python class for creating a dermal exposure model from ChemSTEER
    """
    def __init__(self, ED=1, NWexp=1, NS=1, EY=40, BW=70, ATc=70, AT=40):
        """
        Attributes:
        -------------------
        route   : string, declares model route to be dermal
        ED      : integer, days exposed per year; 0 <= ED <= 365 (default: 1 days/site-yr)
        NWExp   : integer, number of workers exposed while performing the activity
                  (default: 1 workers/site)
        NS      : integer, number of sites (default: 1 site)
        EY      : integer, years of occupational exposure; 0 <= EY (default: 40 years)
        BW      : float, body weight; (0 <= BW*) (default: 70 kg)
        ATc     : float, averaging time over a lifetime (0 <= ATc); (default: 70 years)
        AT      : float, averaging time (EY <= AT <= ATc); (default: 40 years)
        skips   : attributes to skip when creating the `inputs` and `outputs` attributes
                  in the model-specific subclasses
        """
        self.route = 'dermal'
        kwargs = {"ED": checks.check_ul('ED',ED,0,365),
                  "NWexp": NWexp,
                  "NS": NS,
                  "EY": checks.check_l('EY',EY,0),
                  "BW": checks.check_l('BW',BW,0),
                  "ATc": checks.check_l('ATc',ATc,0),
                  "AT": EY,
                  "skips": ['self','model_name','equations', 'scenario','route','skips'],}
        return kwargs

    def model_args(self,kwargs):
        """
        Create a dictionary of model arguments and their corresponding values; used to
        create the `inputs` and `outputs` arguments in model subclasses
        """
        return {k:v for k, v in kwargs.items() if k not in kwargs['skips']}

class one_hand_liquid_contact(dermal_model):
    """
    Class for ChemSTEER's EPA-OPPT 1-Hand Dermal Contact with Liquid Exposure Model
    """
    def __init__(self, Yderm, scenario='high', S=535, Qu=2.1, FT=1,
                 ED=1, NWexp=1, NS=1, EY=40, BW=70, ATc=70, AT=40):
        """
        Required Arguments:
        ------------------
        Yderm : float, weight fraction of chemical in liquid; 0 <= Yderm <= 1
                (dimensionless)

        Optional Arguments:
        -------------------
        scenario: string, which type of scenario to use for model calculation
                  ['low'|'high'|'user'] (default: 'high')
        S       : float, sufrace area of contact for one hand (default: 535 cm^2)
        Qu      : float, quantity remaining on skin (default: 2.1 mg/cm^2-event)
        FT      : integer, frequency of events; 0 <= FT (default: 1 events/worker-day)
        NWExp   : integer, number of workers exposed while performing the activity
                  (default: 1 workers/site)
        NS      : integer, number of sites (default: 1 site)
        ED      : integer, days exposed per year; 0 <= ED <= 365 (default: 1 days/site-yr)
        EY      : integer, years of occupational exposure; 0 <= EY (default: 40 years)
        BW      : float, body weight; (0 <= BW*) (default: 70 kg)
        ATc     : float, averaging time over a lifetime (0 <= ATc); (default: 70 years)
        AT      : float, averaging time (EY <= AT <= ATc); (default: 40 years)

        Stored Attributes
        -------------------
        model_name: string, name of model as it appears in ChemSTEER
        equations : string, equations for ChemSTEER model taken from the User Guide and
                    compared against the ChemSTEER program
        options   : list, names of provided scenarios available in ChemSTEER; an addition
                    `user` option has been added for full flexible use of the model

        Computed Attributes
        -------------------
        Dexp: float, dermal potential dose rate (mg/day)
        NW  : int, total number of workers exposed (workers)
        LADD: lifetime average daily dose (mg/kg-day)
        ADD : average daily dose (mg/kg-day)
        APDR: acute potential dose rate (mg/kg-day)

        Compiled Attributes
        -------------------
        inputs : dictionary, all input values into the ChemSTEER model;
                 {input name:input value}
        outputs: dictionary, all calculated exposure values from ChemSTEER model;
                 {output name: output value}

        Notes
        -------------------
        * Indicates potential typographical error in the ChemSTEER User Guide (p 327);
          original text (0 <= ATc)
        """
        kwargs = dermal_model.__init__(self, ED=ED, NWexp=NWexp, NS=NS,
                                       EY=EY, BW=BW, ATc=ATc, AT=AT)
        self.model_name = 'EPA-OPPT 1-Hand Dermal Contact with Liquid'
        self.equations = """
                         Dexp = S * Qu * Yderm * FT
                         NW   = NWexp * NS
                         LADD = (Dexp * ED * EY) / (BW * ATc * days_per_year)
                         ADD  = (Dexp * ED * EY) / (BW * AT * days_per_year)
                         APDR = Dexp / BW
                         """
        self.scenario = str(scenario).lower().replace(", ",",")
        if (self.scenario not in self.get_scenarios()):
            raise ScenarioException("Error! Invalid value for class argument 'scenario' ("
                                    + str(scenario)+"). Options are '"
                                    + "', '".join(self.get_scenarios()) + "'.")

        kwargs['route'] = self.route

        kwargs['S'] = S
        if (self.scenario == "low"):
            kwargs['Qu'] = 0.7   ## mg/cm^2-event
        elif (self.scenario == "high"):
            kwargs['Qu'] = 2.1   ## mg/cm^2-event
        elif (self.scenario == "user"):
            kwargs['Qu'] = Qu   ## mg/cm^2-event

        kwargs['FT'] = checks.check_l('FT',FT,0)
        kwargs['Yderm'] = checks.check_ul('Yderm',Yderm,0,1)

        self.inputs = self.model_args(kwargs)
        kwargs['skips'] = kwargs['skips'] + list(kwargs.keys())

        kwargs['PDR'] = exposures.potential_dose_rate(**kwargs)
        kwargs['NW'] = exposures.workers_exposed(**kwargs)
        kwargs['LADD'] = exposures.daily_dose(t=kwargs['ATc'], **kwargs)
        kwargs['ADD'] = exposures.daily_dose(t=kwargs['AT'], **kwargs)
        kwargs['APDR'] = exposures.acute_potential_dose_rate(**kwargs)

        self.outputs = self.model_args(kwargs)
        self.outputs['Dexp'] = self.outputs.pop('PDR')

        return

    @classmethod
    def get_scenarios(self):
        return ['low','high','user']


class two_hand_liquid_contact(dermal_model):
    """
    Class for ChemSTEER's EPA-OPPT 2-Hand Dermal Contact with Liquid Exposure Model
    """

    def __init__(self, Yderm, scenario='high',S=1070, Qu=2.1, FT=1,
                 ED=1, NWexp=1, NS=1, EY=40, BW=70, ATc=70, AT=40):
        """
        Required Arguments:
        ------------------
        Yderm : float, weight fraction of chemical in liquid; 0 <= Yderm <= 1
                (dimensionless)

        Optional Arguments:
        -------------------
        scenario: string, which type of scenario to use for model calculation
                  ['low'|'high'|'user'] (default: 'high')
        S       : float, sufrace area of contact for one hand (default: 1070 cm^2)
        Qu      : float, quantity remaining on skin (default: 2.1 mg/cm^2-event)
        FT      : integer, frequency of events; 0 <= FT (default: 1 events/worker-day)
        NWExp   : integer, number of workers exposed while performing the activity
                  (default: 1 workers/site)
        NS      : integer, number of sites (default: 1 site)
        ED      : integer, days exposed per year; 0 <= ED <= 365 (default: 1 days/site-yr)
        EY      : integer, years of occupational exposure; 0 <= EY (default: 40 years)
        BW      : float, body weight; (0 <= BW*) (default: 70 kg)
        ATc     : float, averaging time over a lifetime (0 <= ATc); (default: 70 years)
        AT      : float, averaging time (EY <= AT <= ATc); (default: 40 years)

        Stored Attributes
        -------------------
        model_name: string, name of model as it appears in ChemSTEER
        equations : string, equations for ChemSTEER model taken from the User Guide and
                    compared against the ChemSTEER program
        options   : list, names of provided scenarios available in ChemSTEER; an addition
                    `user` option has been added for full flexible use of the model

        Computed Attributes
        -------------------
        Dexp: float, dermal potential dose rate (mg/day)
        NW  : int, total number of workers exposed (workers)
        LADD: lifetime average daily dose (mg/kg-day)
        ADD : average daily dose (mg/kg-day)
        APDR: acute potential dose rate (mg/kg-day)

        Compiled Attributes
        -------------------
        inputs : dictionary, all input values into the ChemSTEER model;
                 {input name:input value}
        outputs: dictionary, all calculated exposure values from ChemSTEER model;
                 {output name: output value}

        Notes
        -------------------
        * Indicates potential typographical error in the ChemSTEER User Guide (p 327);
          original text (0 <= ATc)
        """
        kwargs = dermal_model.__init__(self, ED=ED, NWexp=NWexp, NS=NS,
                                       EY=EY, BW=BW, ATc=ATc, AT=AT)
        self.model_name = 'EPA-OPPT 2-Hand Dermal Contact with Liquid'
        self.equations = """
                         Dexp = S * Qu * Yderm * FT
                         NW   = NWexp * NS
                         LADD = (Dexp * ED * EY) / (BW * ATc * days_per_year)
                         ADD  = (Dexp * ED * EY) / (BW * AT * days_per_year)
                         APDR = Dexp / BW
                         """
        self.scenario = str(scenario).lower().replace(", ",",")
        if (self.scenario not in self.get_scenarios()):
            raise ScenarioException("Error! Invalid value for class argument 'scenario' ("
                                    + str(scenario)+"). Options are '"
                                    + "', '".join(self.get_scenarios()) + "'.")
        kwargs['route'] = self.route
        kwargs['S'] = S
        if (self.scenario == "low"):
            kwargs['Qu'] = 0.7   ## mg/cm^2-event
        elif (self.scenario == "high"):
            kwargs['Qu'] = 2.1   ## mg/cm^2-event
        elif (self.scenario == "user"):
            kwargs['Qu'] = Qu   ## mg/cm^2-event

        kwargs['FT'] = checks.check_l('FT',FT,0)
        kwargs['Yderm'] = checks.check_ul('Yderm',Yderm,0,1)

        self.inputs = self.model_args(kwargs)
        kwargs['skips'] = kwargs['skips'] + list(kwargs.keys())

        kwargs['PDR'] = exposures.potential_dose_rate(**kwargs)
        kwargs['NW'] = exposures.workers_exposed(**kwargs)
        kwargs['LADD'] = exposures.daily_dose(t=kwargs['ATc'], **kwargs)
        kwargs['ADD'] = exposures.daily_dose(t=kwargs['AT'], **kwargs)
        kwargs['APDR'] = exposures.acute_potential_dose_rate(**kwargs)

        self.outputs = self.model_args(kwargs)
        self.outputs['Dexp'] = self.outputs.pop('PDR')

        return

    @classmethod
    def get_scenarios(self):
        return ['low','high','user']


class two_hand_liquid_immersion(dermal_model):
    """
    Class for ChemSTEER's EPA-OPPT 2-Hand Dermal Immersion with Liquid Exposure Model
    """
    def __init__(self,Yderm,scenario='high',S=1070, Qu=10.3, FT=1,
                 ED=1, NWexp=1, NS=1, EY=40, BW=70, ATc=70, AT=40):
        """
        Required Arguments:
        ------------------
        Yderm : float, weight fraction of chemical in liquid; 0 <= Yderm <= 1
                (dimensionless)

        Optional Arguments:
        -------------------
        scenario: string, which type of scenario to use for model calculation
                  ['low'|'high'|'user'] (default: 'high')
        S       : float, sufrace area of contact for one hand (default: 1070 cm^2)
        Qu      : float, quantity remaining on skin (default: 10.3 mg/cm^2-event)
        FT      : integer, frequency of events; 0 <= FT (default: 1 events/worker-day)
        NWExp   : integer, number of workers exposed while performing the activity
                  (default: 1 workers/site)
        NS      : integer, number of sites (default: 1 site)
        ED      : integer, days exposed per year; 0 <= ED <= 365 (default: 1 days/site-yr)
        EY      : integer, years of occupational exposure; 0 <= EY (default: 40 years)
        BW      : float, body weight; (0 <= BW*) (default: 70 kg)
        ATc     : float, averaging time over a lifetime (0 <= ATc); (default: 70 years)
        AT      : float, averaging time (EY <= AT <= ATc); (default: 40 years)

        Stored Attributes
        -------------------
        model_name: string, name of model as it appears in ChemSTEER
        equations : string, equations for ChemSTEER model taken from the User Guide and
                    compared against the ChemSTEER program
        options   : list, names of provided scenarios available in ChemSTEER; an addition
                    `user` option has been added for full flexible use of the model

        Computed Attributes
        -------------------
        Dexp: float, dermal potential dose rate (mg/day)
        NW  : int, total number of workers exposed (workers)
        LADD: lifetime average daily dose (mg/kg-day)
        ADD : average daily dose (mg/kg-day)
        APDR: acute potential dose rate (mg/kg-day)

        Compiled Attributes
        -------------------
        inputs : dictionary, all input values into the ChemSTEER model;
                 {input name:input value}
        outputs: dictionary, all calculated exposure values from ChemSTEER model;
                 {output name: output value}

        Notes
        -------------------
        * Indicates potential typographical error in the ChemSTEER User Guide (p 327);
          original text (0 <= ATc)
        """
        kwargs = dermal_model.__init__(self, ED=ED, NWexp=NWexp, NS=NS,
                                       EY=EY, BW=BW, ATc=ATc, AT=AT)
        self.model_name = 'EPA-OPPT 2-Hand Dermal Immersion with Liquid'
        self.equations = """
                         Dexp = S * Qu * Yderm * FT
                         NW   = NWexp * NS
                         LADD = (Dexp * ED * EY) / (BW * ATc * days_per_year)
                         ADD  = (Dexp * ED * EY) / (BW * AT * days_per_year)
                         APDR = Dexp / BW
                         """
        self.scenario = str(scenario).lower().replace(", ",",")
        if (self.scenario not in self.get_scenarios()):
            raise ScenarioException("Error! Invalid value for class argument 'scenario' ("
                                    + str(scenario)+"). Options are '"
                                    + "', '".join(self.get_scenarios()) + "'.")
        kwargs['route'] = self.route
        kwargs['S'] = S
        if (self.scenario == "low"):
            kwargs['Qu'] = 1.3   ## mg/cm^2-event
        elif (self.scenario == "high"):
            kwargs['Qu'] = 10.3   ## mg/cm^2-event
        elif (self.scenario == "user"):
            kwargs['Qu'] = Qu   ## mg/cm^2-event

        kwargs['FT'] = checks.check_l('FT',FT,0)
        kwargs['Yderm'] = checks.check_ul('Yderm',Yderm,0,1)

        self.inputs = self.model_args(kwargs)
        kwargs['skips'] = kwargs['skips'] + list(kwargs.keys())

        kwargs['PDR'] = exposures.potential_dose_rate(**kwargs)
        kwargs['NW'] = exposures.workers_exposed(**kwargs)
        kwargs['LADD'] = exposures.daily_dose(t=kwargs['ATc'], **kwargs)
        kwargs['ADD'] = exposures.daily_dose(t=kwargs['AT'], **kwargs)
        kwargs['APDR'] = exposures.acute_potential_dose_rate(**kwargs)

        self.outputs = self.model_args(kwargs)
        self.outputs['Dexp'] = self.outputs.pop('PDR')

        return

    @classmethod
    def get_scenarios(self):
        return ['low','high','user']


class two_hand_solids_contact(dermal_model):
    """
    Class for ChemSTEER's EPA-OPPT 2-Hand Dermal Contact with Solids Exposure Model
    """
    def __init__(self, Yderm, scenario='high', SQu=3100, FT=1,
                 ED=1, NWexp=1, NS=1, EY=40, BW=70, ATc=70, AT=40):
        """
        Required Arguments:
        ------------------
        Yderm : float, weight fraction of chemical in liquid; 0 <= Yderm <= 1
                (dimensionless)

        Optional Arguments:
        -------------------
        scenario: string, which type of scenario to use for model calculation
                  ['low'|'high'|'user'] (default: 'high')
        SQu     : float, total amount of solids on skin (default: 3100 mg/event)
        FT      : integer, frequency of events; 0 <= FT (default: 1 events/worker-day)
        NWExp   : integer, number of workers exposed while performing the activity
                  (default: 1 workers/site)
        NS      : integer, number of sites (default: 1 site)
        ED      : integer, days exposed per year; 0 <= ED <= 365 (default: 1 days/site-yr)
        EY      : integer, years of occupational exposure; 0 <= EY (default: 40 years)
        BW      : float, body weight; (0 <= BW*) (default: 70 kg)
        ATc     : float, averaging time over a lifetime (0 <= ATc); (default: 70 years)
        AT      : float, averaging time (EY <= AT <= ATc); (default: 40 years)

        Stored Attributes
        -------------------
        model_name: string, name of model as it appears in ChemSTEER
        equations : string, equations for ChemSTEER model taken from the User Guide and
                    compared against the ChemSTEER program
        options   : list, names of provided scenarios available in ChemSTEER; an addition
                    `user` option has been added for full flexible use of the model

        Computed Attributes
        -------------------
        Dexp: float, dermal potential dose rate (mg/day)
        NW  : int, total number of workers exposed (workers)
        LADD: lifetime average daily dose (mg/kg-day)
        ADD : average daily dose (mg/kg-day)
        APDR: acute potential dose rate (mg/kg-day)

        Compiled Attributes
        -------------------
        inputs : dictionary, all input values into the ChemSTEER model;
                 {input name:input value}
        outputs: dictionary, all calculated exposure values from ChemSTEER model;
                 {output name: output value}

        Notes
        -------------------
        * Indicates potential typographical error in the ChemSTEER User Guide (p 327);
          original text (0 <= ATc)
        """
        kwargs = dermal_model.__init__(self, ED=ED, NWexp=NWexp, NS=NS,
                                       EY=EY, BW=BW, ATc=ATc, AT=AT)
        self.model_name = 'EPA-OPPT 2-Hand Dermal Contact with Solids'
        self.equations = """
                         Dexp = S * Qu * Yderm * FT
                         NW   = NWexp * NS
                         LADD = (Dexp * ED * EY) / (BW * ATc * days_per_year)
                         ADD  = (Dexp * ED * EY) / (BW * AT * days_per_year)
                         APDR = Dexp / BW
                         """
        self.scenario = str(scenario).lower().replace(", ",",")
        if (self.scenario not in self.get_scenarios()):
            raise ScenarioException("Error! Invalid value for class argument 'scenario' ("
                                    + str(scenario)+"). Options are '"
                                    + "', '".join(self.get_scenarios()) + "'.")
        kwargs['route'] = self.route
        if (self.scenario == "high"):
            kwargs['SQu'] = 3100
        elif (self.scenario == "user"):
            kwargs['SQu'] = SQu

        kwargs['FT'] = checks.check_l('FT',FT,0)
        kwargs['Yderm'] = checks.check_ul('Yderm',Yderm,0,1)

        self.inputs = self.model_args(kwargs)
        kwargs['skips'] = kwargs['skips'] + list(kwargs.keys())

        kwargs['PDR'] = exposures.potential_dose_rate(**kwargs)
        kwargs['NW'] = exposures.workers_exposed(**kwargs)
        kwargs['LADD'] = exposures.daily_dose(t=kwargs['ATc'], **kwargs)
        kwargs['ADD'] = exposures.daily_dose(t=kwargs['AT'], **kwargs)
        kwargs['APDR'] = exposures.acute_potential_dose_rate(**kwargs)

        self.outputs = self.model_args(kwargs)
        self.outputs['Dexp'] = self.outputs.pop('PDR')

        return

    @classmethod
    def get_scenarios(self):
        return ['high','user']


class two_hand_container_surface_contact(dermal_model):
    """
    Class for ChemSTEER's EPA-OPPT 2-Hand Dermal Contact with Container Surfaces Exposure Model
    """
    def __init__(self, Yderm, scenario='high', SQu=1100, FT=1,
                 ED=1, NWexp=1, NS=1, EY=40, BW=70, ATc=70, AT=40):
        """
        Required Arguments:
        ------------------
        Yderm : float, weight fraction of chemical in liquid; 0 <= Yderm <= 1
                (dimensionless)

        Optional Arguments:
        -------------------
        scenario: string, which type of scenario to use for model calculation
                  ['low'|'high'|'user'] (default: 'high')
        SQu     : float, total amount of solids on skin (default: 1100 mg/event)
        FT      : integer, frequency of events; 0 <= FT (default: 1 events/worker-day)
        NWExp   : integer, number of workers exposed while performing the activity
                  (default: 1 workers/site)
        NS      : integer, number of sites (default: 1 site)
        ED      : integer, days exposed per year; 0 <= ED <= 365 (default: 1 days/site-yr)
        EY      : integer, years of occupational exposure; 0 <= EY (default: 40 years)
        BW      : float, body weight; (0 <= BW*) (default: 70 kg)
        ATc     : float, averaging time over a lifetime (0 <= ATc); (default: 70 years)
        AT      : float, averaging time (EY <= AT <= ATc); (default: 40 years)

        Stored Attributes
        -------------------
        model_name: string, name of model as it appears in ChemSTEER
        equations : string, equations for ChemSTEER model taken from the User Guide and
                    compared against the ChemSTEER program
        options   : list, names of provided scenarios available in ChemSTEER; an addition
                    `user` option has been added for full flexible use of the model

        Computed Attributes
        -------------------
        Dexp: float, dermal potential dose rate (mg/day)
        NW  : int, total number of workers exposed (workers)
        LADD: lifetime average daily dose (mg/kg-day)
        ADD : average daily dose (mg/kg-day)
        APDR: acute potential dose rate (mg/kg-day)

        Compiled Attributes
        -------------------
        inputs : dictionary, all input values into the ChemSTEER model;
                 {input name:input value}
        outputs: dictionary, all calculated exposure values from ChemSTEER model;
                 {output name: output value}

        Notes
        -------------------
        * Indicates potential typographical error in the ChemSTEER User Guide (p 327);
          original text (0 <= ATc)
        """
        kwargs = dermal_model.__init__(self, ED=ED, NWexp=NWexp, NS=NS,
                                       EY=EY, BW=BW, ATc=ATc, AT=AT)
        self.model_name = 'EPA-OPPT 2-Hand Dermal Contact with Container Surfaces'
        self.equations = """
                         Dexp = S * Qu * Yderm * FT
                         NW   = NWexp * NS
                         LADD = (Dexp * ED * EY) / (BW * ATc * days_per_year)
                         ADD  = (Dexp * ED * EY) / (BW * AT * days_per_year)
                         APDR = Dexp / BW
                         """
        self.scenario = str(scenario).lower().replace(", ",",")
        if (self.scenario not in self.get_scenarios()):
            raise ScenarioException("Error! Invalid value for class argument 'scenario' ("
                                    + str(scenario)+"). Options are '"
                                    + "', '".join(self.get_scenarios()) + "'.")
        kwargs['route'] = self.route
        if (self.scenario == "high"):
            kwargs['SQu'] = 1100
        elif (self.scenario == "user"):
            kwargs['SQu'] = SQu

        kwargs['FT'] = checks.check_l('FT',FT,0)
        kwargs['Yderm'] = checks.check_ul('Yderm',Yderm,0,1)

        self.inputs = self.model_args(kwargs)
        kwargs['skips'] = kwargs['skips'] + list(kwargs.keys())

        kwargs['PDR'] = exposures.potential_dose_rate(**kwargs)
        kwargs['NW'] = exposures.workers_exposed(**kwargs)
        kwargs['LADD'] = exposures.daily_dose(t=kwargs['ATc'], **kwargs)
        kwargs['ADD'] = exposures.daily_dose(t=kwargs['AT'], **kwargs)
        kwargs['APDR'] = exposures.acute_potential_dose_rate(**kwargs)

        self.outputs = self.model_args(kwargs)
        self.outputs['Dexp'] = self.outputs.pop('PDR')

        return

    @classmethod
    def get_scenarios(self):
        return ['high','user']


class user_defined_dermal(dermal_model):
    """
    Class for ChemSTEER's User-defined Dermal Exposure Model
    """
    def __init__(self, Yderm, scenario="high", S=1070, Qu=2.1, FT=1,
                 ED=1, NWexp=1, NS=1, EY=40, BW=70, ATc=70, AT=40):
        """
        Required Arguments:
        ------------------
        Yderm : float, weight fraction of chemical in liquid; 0 <= Yderm <= 1
                (dimensionless)

        Optional Arguments:
        -------------------
        scenario: string, which type of scenario to use for model calculation
                  ['low'|'high'|'user'] (default: 'high')
        S       : float, sufrace area of contact for one hand (default: 1070 cm^2)
        Qu      : float, quantity remaining on skin (default: 2.1 mg/cm^2-event)
        FT      : integer, frequency of events; 0 <= FT (default: 1 events/worker-day)
        NWExp   : integer, number of workers exposed while performing the activity
                  (default: 1 workers/site)
        NS      : integer, number of sites (default: 1 site)
        ED      : integer, days exposed per year; 0 <= ED <= 365 (default: 1 days/site-yr)
        EY      : integer, years of occupational exposure; 0 <= EY (default: 40 years)
        BW      : float, body weight; (0 <= BW*) (default: 70 kg)
        ATc     : float, averaging time over a lifetime (0 <= ATc); (default: 70 years)
        AT      : float, averaging time (EY <= AT <= ATc); (default: 40 years)

        Stored Attributes
        -------------------
        model_name: string, name of model as it appears in ChemSTEER
        equations : string, equations for ChemSTEER model taken from the User Guide and
                    compared against the ChemSTEER program
        options   : list, names of provided scenarios available in ChemSTEER; an addition
                    `user` option has been added for full flexible use of the model

        Computed Attributes
        -------------------
        Dexp: float, dermal potential dose rate (mg/day)
        NW  : int, total number of workers exposed (workers)
        LADD: lifetime average daily dose (mg/kg-day)
        ADD : average daily dose (mg/kg-day)
        APDR: acute potential dose rate (mg/kg-day)

        Compiled Attributes
        -------------------
        inputs : dictionary, all input values into the ChemSTEER model;
                 {input name:input value}
        outputs: dictionary, all calculated exposure values from ChemSTEER model;
                 {output name: output value}

        Notes
        -------------------
        * Indicates potential typographical error in the ChemSTEER User Guide (p 327);
          original text (0 <= ATc)
        """
        kwargs = dermal_model.__init__(self, ED=ED, NWexp=NWexp, NS=NS,
                                       EY=EY, BW=BW, ATc=ATc, AT=AT)
        self.model_name = 'User-defined Dermal'
        self.equations = """
                         Dexp = S * Qu * Yderm * FT
                         NW   = NWexp * NS
                         LADD = (Dexp * ED * EY) / (BW * ATc * days_per_year)
                         ADD  = (Dexp * ED * EY) / (BW * AT * days_per_year)
                         APDR = Dexp / BW
                         """
        self.scenario = str(scenario).lower().replace(", ",",")
        if (self.scenario not in self.get_scenarios()):
            raise ScenarioException("Error! Invalid value for class argument 'scenario' ("
                                    + str(scenario)+"). Options are '"
                                    + "', '".join(self.get_scenarios()) + "'.")
        kwargs['route'] = self.route
        if (self.scenario == "low"):
            kwargs['S'] = 535
            kwargs['Qu'] = 0.7   ## mg/cm^2-event
        elif (self.scenario == "high"):
            kwargs['S'] = 1070
            kwargs['Qu'] = 2.1   ## mg/cm^2-event
        elif (self.scenario == "user"):
            kwargs['S'] = S
            kwargs['Qu'] = Qu

        kwargs['FT'] = checks.check_l('FT',FT,0)
        kwargs['Yderm'] = checks.check_ul('Yderm',Yderm,0,1)

        self.inputs = self.model_args(kwargs)
        kwargs['skips'] = kwargs['skips'] + list(kwargs.keys())

        kwargs['PDR'] = exposures.potential_dose_rate(**kwargs)
        kwargs['NW'] = exposures.workers_exposed(**kwargs)
        kwargs['LADD'] = exposures.daily_dose(t=kwargs['ATc'], **kwargs)
        kwargs['ADD'] = exposures.daily_dose(t=kwargs['AT'], **kwargs)
        kwargs['APDR'] = exposures.acute_potential_dose_rate(**kwargs)

        self.outputs = self.model_args(kwargs)
        self.outputs['Dexp'] = self.outputs.pop('PDR')

        return

    @classmethod
    def get_scenarios(self):
        return ['low','high','user']
