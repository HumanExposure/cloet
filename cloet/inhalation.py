from . import checks
from . import exposures

class inhalation_model(object):
    def __init__(self, ED=1, NWexp=1, NS=1, EY=40, BW=70, ATc=70, AT=40):
        """
        Attributes:
        -------------------
        route   : string, declares model route to be inhalation
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
        self.route = 'inhalation'
        kwargs = {"ED": checks.check_ul('ED',ED,0,365),
                  "NWexp": NWexp,
                  "NS": NS,
                  "EY": checks.check_l('EY',EY,0),
                  "BW": checks.check_l('BW',BW,0),
                  "ATc": checks.check_l('ATc',ATc,0),
                  "AT": AT,
                  "skips": ['self','model_name','equations', 'scenario','route','skips'],}
        return kwargs

    def model_args(self, kwargs):
        """
        Create a dictionary of model arguments and their corresponding values; used to
        create the `inputs` and `outputs` arguments in model subclasses
        """
        return {k:v for k, v in kwargs.items() if k not in kwargs['skips']}

class small_volume_solids_handling(inhalation_model):
    """
    Class for ChemSTEER's EPA-OPPT Small Volume Solids Handling Inhalation Exposure Model
    """


    def __init__(self, Ys, scenario="typical", EF=0.0477, AH=1, Sd=1,
                 ED=1, NWexp=1, NS=1, EY=40, BW=70, ATc=70, AT=40):
        """
        Required Arguments:
        ------------------
        Ys : float, weight fraction of chemical in particulate; 0 <= Ys <= 1
             (dimensionless)

        Optional Arguments:
        -------------------
        scenario: string, which type of scenario to use for model calculation
                  ['typical'|'worst-case'|'user'] (default: 'typical')
        EF      : float, exposure factor (default: 0.0477 mg/kg)
        AH      : float, the amoun of solid/powder (containing the chemical) handled
                  (default: 1 kg/worker-shift)
        Sd      : integer, number of shifts workd by each worker during a workday;
                  0 <= Sd <= 3 (default: 1 shift/workder-day)
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
        I   : float, inhalation potential dose rate (mg/day)
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
        kwargs = inhalation_model.__init__(self, ED=ED, NWexp=NWexp, NS=NS,
                                           EY=EY, BW=BW, ATc=ATc, AT=AT)
        self.model_name = 'EPA-OPPT Small Volume Solids Handling'
        self.equations = """
                         I    = EF * AH * Ys * Sd
                         NW   = NWexp * NS
                         LADD = (I * ED * EY) / (BW * ATc * days_per_year)
                         ADD  = (I * ED * EY) / (BW * AT * days_per_year)
                         APDR = I / BW
                         """

        self.scenario = str(scenario).lower().replace(", ",",")
        if (self.scenario not in self.get_scenarios()):
            raise ScenarioException("Error! Invalid value for class argument 'scenario' ("
                                    + str(self.scenario)+"). Options are '"
                                    + "', '".join(self.get_scenarios()) + "'.")

        kwargs["route"] = self.route
        kwargs["AH"] = checks.check_ul('AH',AH,0,54)
        kwargs["Ys"] = checks.check_ul('Ys',Ys,0,1)
        kwargs["Sd"] = checks.check_ul('Sd',Sd,0,3)

        if (self.scenario == "typical"):
            kwargs["EF"] = 0.0477
        elif (self.scenario == "worst-case"):
            kwargs["EF"] = 0.161
        elif (self.scenario == "user"):
            kwargs["EF"] = EF

        self.inputs = self.model_args(kwargs)
        kwargs['skips'] = kwargs['skips'] + list(kwargs.keys())

        kwargs['PDR'] = exposures.potential_dose_rate(**kwargs)
        kwargs['NW'] = exposures.workers_exposed(**kwargs)
        kwargs['LADD'] = exposures.daily_dose(t=kwargs['ATc'],**kwargs)
        kwargs['ADD'] = exposures.daily_dose(t=kwargs['AT'],**kwargs)
        kwargs['APDR'] = exposures.acute_potential_dose_rate(**kwargs)

        self.outputs = self.model_args(kwargs)
        self.outputs['I'] = self.outputs.pop('PDR')

        return

    @classmethod
    def get_scenarios(self):
        return ['typical','worst-case','user']

class mass_balance(inhalation_model):
    """
    Class for ChemSTEER's EPA-OPPT Mass Balance Inhalation Exposure Model
    """
    def __init__(self, G, MW, VP, X, scenario='indoor,typical', T=298, Q=3000, k=0.5,
                 Vm=24.45, b=1.25, h=8 ,vz=440, ED=1, NWexp=1, NS=1, EY=40, BW=70, ATc=70,
                 AT=40):
        """
        Required Arguments:
        ------------------
        G  : float, vapor generation rate (g/s)
        MW : float, molecular weight of the chemical (g/mol)
        VP : float, vapor pressure of the pure chemical being assessed (torr)

        Optional Arguments:
        -------------------
        scenario: string, which type of scenario to use for model calculation
                  ['indoor,typical'|'indoor,worst-case'|'outdoor,typical'|
                   'outdoor,worst-case'|'user'] (default: 'indoor,typical')
        T       : float, temperature of air (default: 298 K)
        Q       : float, ventilation rate; 0 < Q (default: 3000 ft3/min)
        k       : float, mixing factor; 0 <= k <= 1 (default: 0.5 dimensionless)
        X       : float, vapor pressure correction factor (mole fraction or other)
        Vm      : float, molar volume; 0 <= Vm (default: 24.45 L/mol, assuming room
                  temperature and pressure)
        b       : volumetric inhalation rate; 0 <= b <=7.9 (default: 1.25 m^3/hr)
        h       : daily exposure duration; 0 <= h <= 24 (default: 8 hrs/day)
        ED      : integer, days exposed per year; 0 <= ED <= 365 (default: 1 days/site-yr)
        NWExp   : integer, number of workers exposed while performing the activity
                  (default: 1 workers/site)
        NS      : integer, number of sites (default: 1 site)
        EY      : integer, years of occupational exposure; 0 <= EY (default: 40 years)
        BW      : float, body weight; (0 <= BW) (default: 70 kg)
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
        Cv  : volumetric concentration of chemical in air (ppm)
        Cm  : mass concentration of chemical in air (mg/m^3)
        I   : float, inhalation potential dose rate (mg/day)
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
        """
        kwargs = inhalation_model.__init__(self, ED=ED, NWexp=NWexp, NS=NS,
                                           EY=EY, BW=BW, ATc=ATc, AT=AT)
        self.model_name = 'EPA-OPPT Mass Balance'
        self.equations = """
                         Cv = min(((170000 * T * G) / (MW * Q * k)),(1000000 * X * VP / 760))
                         Cm = Cv * MW / Vm
                         I = Cm * b * h
                         NW = NWexp * NS
                         LADD = (I * ED * EY) / (BW * ATc * days_per_year)
                         ADD = (I * ED * EY) / (BW * AT * days_per_year)
                         APDR = I / BW
                         """
        self.scenario = str(scenario).lower().replace(", ",",")

        if (self.scenario not in self.get_scenarios()):
            raise ScenarioException("Error! Invalid value for class argument 'scenario' ("
                                    + str(self.scenario)+"). Options are '"
                                    + "', '".join(self.get_scenarios()) + "'.")
        kwargs['route'] = self.route
        kwargs['T'] = T
        kwargs['G'] = G
        kwargs['MW'] = MW
        kwargs['X'] = X
        kwargs['VP'] = VP
        kwargs['Vm'] = Vm
        kwargs['b'] = b
        kwargs['h'] = h
        kwargs['EY'] = EY
        kwargs['BW'] = BW
        kwargs['ATc'] = ATc
        kwargs['AT'] = AT
        if self.scenario == 'indoor,typical':
            kwargs['Q'] = 3000
            kwargs['k'] = 0.5
        elif self.scenario == 'indoor,worst-case':
            kwargs['Q'] = 500
            kwargs['k'] = 0.1
        elif self.scenario == 'outdoor,typical':
            kwargs['Q'] = 237600
            kwargs['k'] = 0.5
        elif self.scenario == 'outdoor,worst-case':
            kwargs['Q'] = 26400 * (60 * vz / 5280)**3
            kwargs['k'] = 0.1
        elif self.scenario == 'user':
            kwargs['Q'] = Q
            kwargs['k'] = k

        self.inputs = self.model_args(kwargs)
        kwargs['skips'] = kwargs['skips'] + list(kwargs.keys())

        kwargs['Cv'] = self._Cv(**kwargs)
        kwargs['Cm'] = self._Cm(**kwargs)
        kwargs['PDR'] = exposures.potential_dose_rate(**kwargs)
        kwargs['NW'] = exposures.workers_exposed(**kwargs)
        kwargs['LADD'] = exposures.daily_dose(t=kwargs['ATc'], **kwargs)
        kwargs['ADD'] = exposures.daily_dose(t=kwargs['AT'], **kwargs)
        kwargs['APDR'] = exposures.acute_potential_dose_rate(**kwargs)

        self.outputs = self.model_args(kwargs)
        self.outputs['I'] = self.outputs.pop('PDR')

        return

    def _Cv(self,T, G, MW, Q, k, X, VP, **kwargs):

        return min(((170000 * T * G) / (MW * Q * k)),
                      (1000000 * X * VP / 760))

    def _Cm(self,Cv, MW, Vm, **kwargs):
        return Cv * MW / Vm

    @classmethod
    def get_scenarios(self):
        return ['indoor,typical','indoor,worst-case',
                'outdoor,typical', 'outdoor,worst-case',
                'user']


class pel_limiting_particulates(inhalation_model):
    """
    Class for ChemSTEER's OSHA PEL-limiting Model for Substance-specific Particulates Exposure Model
    """
    def __init__(self, Ys, scenario='user', KCk=15, Ypel=1, b=1.25, h=8,
                 ED=1, NWexp=1, NS=1, EY=40, BW=70, ATc=70, AT=40):
        """
        Required Arguments:
        ------------------
        Ys : float, weight fraction of chemical in particulate; 0 <= Ys <= 1
             (dimensionless)

        Optional Arguments:
        -------------------
        scenario: string, which type of scenario to use for model calculation
                  ['user'] (default: 'user')
        KCk     : float, mass concentration of the chemical or metal with a PEL in air;
                  based on an OSHA PEL-TWA (default: 15 mg/m^3)
        Ypel    : weight fraction of chemical or metal with a PEL in particulate;
                  0 < YPel <= 1 (default: 1 dimensionless)
        b       : volumetric inhalation rate; 0 <= b <=7.9 (default: 1.25 m^3/hr)
        h       : daily exposure duration; 0 <= h <= 24 (default: 8 hrs/day)
        NWExp   : integer, number of workers exposed while performing the activity
                  (default: 1 workers/site)
        NS      : integer, number of sites (default: 1 site)
        ED      : integer, days exposed per year; 0 <= ED <= 365 (default: 1 days/site-yr)
        EY      : integer, years of occupational exposure; 0 <= EY (default: 40 years)
        BW      : float, body weight; (0 <= BW) (default: 70 kg)
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
        Cm  : mass concentration of chemical in air (mg/m^3)
        I   : float, inhalation potential dose rate (mg/day)
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
        """
        kwargs = inhalation_model.__init__(self, ED=ED, NWexp=NWexp, NS=NS,
                                           EY=EY, BW=BW, ATc=ATc, AT=AT)
        self.model_name = 'OSHA PEL-limiting Model for Substance-specific Particulates'
        self.equations = """
                         Cm = KCk * Ys / Ypel
                         I = Cm * b * h
                         NW = NWexp * NS
                         LADD = (I * ED * EY) / (BW * ATc * days_per_year)
                         ADD =  (I * ED * EY) / (BW * AT * days_per_year)
                         APDR = I / BW
                         """
        self.scenario = str(scenario).lower().replace(", ",",")
        if scenario not in self.get_scenarios():
            raise ScenarioException("Error! Invalid value for class argument 'scenario' ("
                                    + str(self.scenario)+"). Options are '"
                                    + "', '".join(self.get_scenarios()) + "'.")

        kwargs['route'] = self.route
        kwargs['KCk'] = KCk
        kwargs['Ys'] = checks.check_ul('Ys',Ys,0,1)
        kwargs['Ypel'] = checks.check_ul('Ypel',Ypel,0,1)
        kwargs['b'] = checks.check_ul('b',b,0,7.9)
        kwargs['h'] = checks.check_ul('h',h,0,24)

        self.inputs = self.model_args(kwargs)
        kwargs['skips'] = kwargs['skips'] + list(kwargs.keys())

        kwargs['Cm'] = self._Cm(**kwargs)
        kwargs['PDR'] = exposures.potential_dose_rate(**kwargs)
        kwargs['NW'] = exposures.workers_exposed(**kwargs)
        kwargs['LADD'] = exposures.daily_dose(t=kwargs['ATc'], **kwargs)
        kwargs['ADD'] = exposures.daily_dose(t=kwargs['AT'], **kwargs)
        kwargs['APDR'] = exposures.acute_potential_dose_rate(**kwargs)

        self.outputs = self.model_args(kwargs)
        self.outputs['I'] = self.outputs.pop('PDR')

        return

    def _Cm(self, KCk, Ys, Ypel, **kwargs):
        return KCk * Ys / Ypel

    @classmethod
    def get_scenarios(self):
        return ['user']


class pel_limiting_vapors(inhalation_model):
    """
    Class for ChemSTEER's OSHA PEL-limiting Model for Substance-specific Vapors Inhalation Exposure Model
    """
    def __init__(self, Cvk, VP, Ys, MW, VPpel, Ypel, MWpel, X, scenario='user', Vm=24.45,
                 b=1.25, h=8, ED=1, NWexp=1, NS=1, EY=40, BW=70, ATc=70, AT=40):
        """
        Required Arguments:
        ------------------
        Cvk  : float, vapor concentration of the chemical with a PEL in air (ppm)
        VP   : float, vapor pressure of the pure chemical being assessed (torr)
        Ys   : float, weight fraction of the chemical in mixture (dimensionless)
        MW   : float, molecular weight of the chemical (g/mol)
        VPpel: float, vapor pressure of the pure PEL chemical (torr)
        Ypel : float, weight fraction of the chemical with PEL in mixture (dimensionless)
        MWpel: float, molecular weight of the PEL chemical (g/mol)
        X    : vapor pressure correction factor (mole fraction or other); 0 <= X <= 1
               (dimensionless)

        Optional Arguments:
        -------------------
        scenario: string, which type of scenario to use for model calculation
                  ['user'] (default: 'user')
        Vm      : float, molar volume; 0 <= Vm (default: 24.45 L/mol, assuming room
                  temperature and pressure)
        b       : volumetric inhalation rate; 0 <= b <=7.9 (default: 1.25 m^3/hr)
        h       : daily exposure duration; 0 <= h <= 24 (default: 8 hrs/day)
        ED      : integer, days exposed per year; 0 <= ED <= 365 (default: 1 days/site-yr)
        NWExp   : integer, number of workers exposed while performing the activity
                  (default: 1 workers/site)
        NS      : integer, number of sites (default: 1 site)
        EY      : integer, years of occupational exposure; 0 <= EY (default: 40 years)
        BW      : float, body weight; (0 <= BW) (default: 70 kg)
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
        Cv* : volumetric concentration of chemical in air (ppm)
        Cm  : mass concentration of chemical in air (mg/m^3)
        I   : float, inhalation potential dose rate (mg/day)
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
        * Indicates potential typographical error in the ChemSTEER User Guide (p 289);
          original text (Cvk is volumetric concentration of chemical in air). This
          correction corresponds with the equation provided by the ChemSTEER program.
        """
        kwargs = inhalation_model.__init__(self, ED=ED, NWexp=NWexp, NS=NS,
                                           EY=EY, BW=BW, ATc=ATc, AT=AT)
        self.model_name = 'OSHA PEL-limiting Model for Substance-specific Vapors'
        self.equations = """
                         Cv = min(Cvk * (VP * Ys / MW) / (Vppel * Ypel / Mwpel),
                                  (1000000 * X * VP / 760))
                         Cm   = Cv * MW / Vm
                         I    = Cm x b * h
                         NW   = NWexp * NS
                         LADD = (I * ED * EY) / (BW * ATc * days_per_year)
                         ADD  = (I * ED * EY) / (BW * AT * days_per_year)
                         APDR = I / BW
                         """
        self.scenario = str(scenario).lower().replace(", ",",")
        if scenario not in self.get_scenarios():
            raise ScenarioException("Error! Invalid value for class argument 'scenario' ("
                                    + str(self.scenario)+"). Options are '"
                                    + "', '".join(self.get_scenarios()) + "'.")
        kwargs['route'] = self.route
        kwargs['Cvk'] = Cvk
        kwargs['VP'] = VP
        kwargs['Ys'] = checks.check_ul('Ys',Ys,0,1)
        kwargs['MW'] = MW
        kwargs['VPpel'] = VPpel
        kwargs['Ypel'] = 1 - kwargs['Ys']
        kwargs['MWpel'] = MWpel
        kwargs['X'] = checks.check_ul('X',X,0,1)
        kwargs['Vm'] = checks.check_l('Vm',Vm,0)
        kwargs['b'] = checks.check_ul('b',b,0,7.9)
        kwargs['h'] = checks.check_ul('h',h,0,24)

        self.inputs = self.model_args(kwargs)
        kwargs['skips'] = kwargs['skips'] + list(kwargs.keys())

        kwargs['Cv'] = self._Cv(**kwargs)
        kwargs['Cm']   = self._Cm(**kwargs)
        kwargs['PDR'] = exposures.potential_dose_rate(**kwargs)
        kwargs['NW']   = exposures.workers_exposed(**kwargs)
        kwargs['LADD'] = exposures.daily_dose(t=kwargs['ATc'], **kwargs)
        kwargs['ADD']  = exposures.daily_dose(t=kwargs['AT'], **kwargs)
        kwargs['APDR'] = exposures.acute_potential_dose_rate(**kwargs)

        self.outputs = self.model_args(kwargs)
        self.outputs['I'] = self.outputs.pop('PDR')
        return

    def _Cv(self, Cvk, VP, Ys, MW, VPpel, Ypel, MWpel, X, **kwargs):
        return min((Cvk * (VP * Ys / MW) / (VPpel * Ypel / MWpel)),
                   (1000000 * X * VP / 760))

    def _Cm(self,Cv, MW, Vm, **kwargs):
        return Cv * MW / Vm

    @classmethod
    def get_scenarios(self):
        return ['user']


class total_pnor_pel_limiting(inhalation_model):
    """
    Class for ChemSTEER's OSHA Total PNOR PEL-limiting Inhalation Exposure Model
    """
    def __init__(self, Ys, scenario='user', KCk=15, b=1.25, h=8,
                 ED=1, NWexp=1, NS=1, EY=40, BW=70, ATc=70, AT=40):
        """
        Required Arguments:
        ------------------
        Ys   : float, weight fraction of the chemical in mixture (dimensionless)

        Optional Arguments:
        -------------------
        scenario: string, which type of scenario to use for model calculation
                  ['user'] (default: 'user')
        KCk     : float, mass concentration total particulate in air; based on an OSHA PEL
                  for PNOR-TWA (default: 15 mg/m^3)
        b       : volumetric inhalation rate; 0 <= b <=7.9 (default: 1.25 m^3/hr)
        h       : daily exposure duration; 0 <= h <= 24 (default: 8 hrs/day)
        ED      : integer, days exposed per year; 0 <= ED <= 365 (default: 1 days/site-yr)
        NWExp   : integer, number of workers exposed while performing the activity
                  (default: 1 workers/site)
        NS      : integer, number of sites (default: 1 site)
        EY      : integer, years of occupational exposure; 0 <= EY (default: 40 years)
        BW      : float, body weight; (0 <= BW) (default: 70 kg)
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
        Cm  : mass concentration of chemical in air (mg/m^3)
        I   : float, inhalation potential dose rate (mg/day)
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
        """
        kwargs = inhalation_model.__init__(self, ED=ED, NWexp=NWexp, NS=NS,
                                           EY=EY, BW=BW, ATc=ATc, AT=AT)
        self.model_name = 'OSHA Total PNOR PEL-limiting'
        self.equations = """
                         Cm   = KCk * Ys
                         I    = Cm * b * h
                         NW   = NWexp * NS
                         LADD = (I * ED * EY) / (BW * ATc * days_per_year)
                         ADD  = (I * ED * EY) / (BW * AT * days_per_year)
                         APDR = I / BW
                         """
        self.scenario = str(scenario).lower().replace(", ",",")
        if scenario not in self.get_scenarios():
            raise ScenarioException("Error! Invalid value for class argument 'scenario' ("
                                    + str(self.scenario)+"). Options are '"
                                    + "', '".join(self.get_scenarios()) + "'.")

        kwargs['route'] = self.route

        kwargs['KCk'] = KCk
        kwargs['Ys'] = checks.check_ul('Ys',Ys,0,1)
        kwargs['b'] = checks.check_ul('b',b,0,7.9)
        kwargs['h'] = checks.check_ul('h',h,0,24)

        self.inputs = self.model_args(kwargs)
        kwargs['skips'] = kwargs['skips'] + list(kwargs.keys())
        # for k,v in kwargs.items():
        #     print(k,v)
        kwargs['Cm'] = self._Cm(**kwargs)
        kwargs['PDR'] = exposures.potential_dose_rate(**kwargs)
        kwargs['NW'] = exposures.workers_exposed(**kwargs)
        kwargs['LADD'] = exposures.daily_dose(t=kwargs['ATc'], **kwargs)
        kwargs['ADD'] = exposures.daily_dose(t=kwargs['AT'], **kwargs)
        kwargs['APDR'] = exposures.acute_potential_dose_rate(**kwargs)

        self.outputs = self.model_args(kwargs)
        self.outputs['I'] = self.outputs.pop('PDR')

        return

    def _Cm(self,KCk, Ys, **kwargs):
        return KCk * Ys

    @classmethod
    def get_scenarios(self):
        return ['user']


class respirable_pnor_pel_limiting(inhalation_model):
    """
    Class for ChemSTEER's OSHA Respirable PNOR PEL-limiting Inhalation Exposure Model
    """
    def __init__(self, Ys, scenario='user', KCk=5, b=1.25, h=8,
                 ED=1, NWexp=1, NS=1, EY=40, BW=70, ATc=70, AT=40):
        """
        Required Arguments:
        ------------------
        Ys   : float, weight fraction of the chemical in mixture (dimensionless)

        Optional Arguments:
        -------------------
        scenario: string, which type of scenario to use for model calculation
                  ['user'] (default: 'user')
        KCk     : float, mass concentration total particulate in air; based on an OSHA PEL
                  for PNOR-TWA (default: 5 mg/m^3)
        b       : volumetric inhalation rate; 0 <= b <=7.9 (default: 1.25 m^3/hr)
        h       : daily exposure duration; 0 <= h <= 24 (default: 8 hrs/day)
        ED      : integer, days exposed per year; 0 <= ED <= 365 (default: 1 days/site-yr)
        NWExp   : integer, number of workers exposed while performing the activity
                  (default: 1 workers/site)
        NS      : integer, number of sites (default: 1 site)
        EY      : integer, years of occupational exposure; 0 <= EY (default: 40 years)
        BW      : float, body weight; (0 <= BW) (default: 70 kg)
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
        Cm  : mass concentration of chemical in air (mg/m^3)
        I   : float, inhalation potential dose rate (mg/day)
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
        """
        kwargs = inhalation_model.__init__(self, ED=ED, NWexp=NWexp, NS=NS,
                                           EY=EY, BW=BW, ATc=ATc, AT=AT)
        self.model_name = 'OSHA Respirable PNOR PEL-limiting'
        self.equations = """
                         Cm   = KCk * Ys
                         I    = Cm * b * h
                         NW   = NWexp * NS
                         LADD = (I * ED * EY) / (BW * ATc * days_per_year)
                         ADD  = (I * ED * EY) / (BW * AT * days_per_year)
                         APDR = I / BW
                         """
        self.scenario = str(scenario).lower().replace(", ",",")
        if scenario not in self.get_scenarios():
            raise ScenarioException("Error! Invalid value for class argument 'scenario' ("
                                    + str(self.scenario)+"). Options are '"
                                    + "', '".join(self.get_scenarios()) + "'.")

        kwargs['route'] = self.route

        kwargs['KCk'] = KCk
        kwargs['Ys'] = checks.check_ul('Ys',Ys,0,1)
        kwargs['b'] = checks.check_ul('b',b,0,7.9)
        kwargs['h'] = checks.check_ul('h',h,0,24)

        self.inputs = self.model_args(kwargs)
        kwargs['skips'] = kwargs['skips'] + list(kwargs.keys())

        kwargs['Cm'] = self._Cm(**kwargs)
        kwargs['PDR'] = exposures.potential_dose_rate(**kwargs)
        kwargs['NW'] = exposures.workers_exposed(**kwargs)
        kwargs['LADD'] = exposures.daily_dose(t=kwargs['ATc'], **kwargs)
        kwargs['ADD'] = exposures.daily_dose(t=kwargs['AT'], **kwargs)
        kwargs['APDR'] = exposures.acute_potential_dose_rate(**kwargs)

        self.outputs = self.model_args(kwargs)
        self.outputs['I'] = self.outputs.pop('PDR')

        return

    def _Cm(self, KCk, Ys, **kwargs):
        return KCk * Ys

    @classmethod
    def get_scenarios(self):
        return ['user']


class automobile_oem_spray_coating(inhalation_model):
    """
    Class for ChemSTEER's EPA-OPPT automobile OEM Spray Coating Inhalation Exposure Model
    """
    def __init__(self, Ymist, scenario='conventional,downdraft', KCk=2.3, Ys=None,
                 Ysf=0.25, b=1.25, h=8, ED=1, NWexp=17, NS=1, EY=40, BW=70, ATc=70, AT=40):
        """
        Required Arguments:
        ------------------
        Ymist : float, weight fraction of the chemical in mist; 0 <= Ymist <= 1
                (dimensionless)

        Optional Arguments:
        -------------------
        scenario: string, which type of scenario to use for model calculation
                  ['conventional,downdraft'|'conventional,crossdraft'|'hvlp,downdraft'|
                   'hvlp,crossdraft'|'user'] (default: 'conventional,downdraft')
        KCk     : float, mass concentration total particulate in air; based on an OSHA PEL
                  for PNOR-TWA (default: 2.3 mg/m^3)
        Ys      : None or float, weight fraction of the chemical in particulate or solids
                  fraction of mist; 0 <= Ymist <= 1; if None is min(Ymist/Ysf,1)
                  (default: None dimensionless)
        b       : volumetric inhalation rate; 0 <= b <=7.9 (default: 1.25 m^3/hr)
        h       : daily exposure duration; 0 <= h <= 24 (default: 8 hrs/day)
        ED      : integer, days exposed per year; 0 <= ED <= 365 (default: 1 days/site-yr)
        NWExp   : integer, number of workers exposed while performing the activity
                  (default: 17 workers/site)
        NS      : integer, number of sites (default: 1 site)
        EY      : integer, years of occupational exposure; 0 <= EY (default: 40 years)
        BW      : float, body weight; (0 <= BW) (default: 70 kg)
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
        Cm  : mass concentration of chemical in air (mg/m^3)
        I   : float, inhalation potential dose rate (mg/day)
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
        """
        kwargs = inhalation_model.__init__(self, ED=ED, NWexp=NWexp, NS=NS,
                                           EY=EY, BW=BW, ATc=ATc, AT=AT)
        self.model_name = 'EPA-OPPT automobile OEM Spray Coating'
        self.equations = """
                         Cm = KCk * Ys
                         I = Cm * b * h
                         NW = NWexp * NS
                         LADD = (I * ED * EY) / (BW * ATc * days_per_year)
                         ADD = (I * ED * EY) / (BW * AT * days_per_year)
                         APDR = I / BW
                         """
        self.scenario = str(scenario).lower().replace(", ",",")
        if (self.scenario not in self.get_scenarios()):
            raise ScenarioException("Error! Invalid value for class argument 'scenario' ("
                                    + str(self.scenario)+"). Options are '"
                                    + "', '".join(self.get_scenarios()) + "'.")

        kwargs['route'] = self.route

        if (self.scenario == "conventional,downdraft"):
            kwargs['KCk'] = 2.3
        elif (self.scenario == "conventional,crossdraft"):
            kwargs['KCk'] = 15
        elif (self.scenario == "hvlp,downdraft"):
            kwargs['KCk'] = 1.9
        elif (self.scenario == "hvlp,crossdraft"):
            kwargs['KCk'] = 15
        elif (self.scenario == "user"):
            kwargs['KCk'] = KCk

        kwargs['Ymist'] = checks.check_ul('Ymist',Ymist,0,1)
        kwargs['Ysf'] = checks.check_ul('Ysf',Ysf,0,1)

        if Ys == None:
            kwargs['Ys'] = checks.check_ul('Ys',min((kwargs['Ymist']/kwargs['Ysf']), 1),0,1)
        else:
            kwargs['Ys'] = checks.check_ul('Ys',Ys,0,1)

        kwargs['b'] = checks.check_ul('b',b,0,7.9)
        kwargs['h'] = checks.check_ul('h',h,0,24)

        self.inputs = self.model_args(kwargs)
        kwargs['skips'] = kwargs['skips'] + list(kwargs.keys())

        kwargs['Cm'] = self._Cm(**kwargs)
        kwargs['PDR'] = exposures.potential_dose_rate(**kwargs)
        kwargs['NW'] = exposures.workers_exposed(**kwargs)
        kwargs['LADD'] = exposures.daily_dose(t=kwargs['ATc'], **kwargs)
        kwargs['ADD'] =   exposures.daily_dose(t=kwargs['AT'], **kwargs)
        kwargs['APDR'] = exposures.acute_potential_dose_rate(**kwargs)

        self.outputs = self.model_args(kwargs)
        self.outputs['I'] = self.outputs.pop('PDR')

        return

    def _Cm(self, KCk, Ys, **kwargs):
        return KCk * Ys

    @classmethod
    def get_scenarios(self):
        return ['conventional,downdraft', 'conventional,crossdraft',
                'hvlp,downdraft', 'hvlp,crossdraft', 'user']


class automobile_refinish_spray_coating(inhalation_model):
    """
    Class for ChemSTEER's EPA-OPPT Automobile Refinish Spray Coating Inhalation Exposure Model
    """
    def __init__(self, Ymist, scenario="conventional,crossdraft", Ys=None, KCk=15,
                 Ysf=0.25, b=1.25, h=8, ED=1, NWexp=3, NS=1, EY=40, BW=70, ATc=70, AT=40):
        """
        Required Arguments:
        ------------------
        Ymist : float, weight fraction of the chemical in mist; 0 <= Ymist <= 1
                (dimensionless)

        Optional Arguments:
        -------------------
        scenario: string, which type of scenario to use for model calculation
                  ['conventional,downdraft'|'conventional,crossdraft'|'hvlp,downdraft'|
                   'hvlp,crossdraft'|'user'] (default: 'conventional,crossdraft')
        KCk     : float, mass concentration total particulate in air; based on an OSHA PEL
                  for PNOR-TWA (default: 15 mg/m^3)
        Ys      : None or float, weight fraction of the chemical in particulate or solids
                  fraction of mist; 0 <= Ymist <= 1; if None is min(Ymist/Ysf,1)
                  (default: None dimensionless)
        b       : volumetric inhalation rate; 0 <= b <=7.9 (default: 1.25 m^3/hr)
        h       : daily exposure duration; 0 <= h <= 24 (default: 8 hrs/day)
        ED      : integer, days exposed per year; 0 <= ED <= 365 (default: 1 days/site-yr)
        NWExp   : integer, number of workers exposed while performing the activity
                  (default: 3 workers/site)
        NS      : integer, number of sites (default: 1 site)
        EY      : integer, years of occupational exposure; 0 <= EY (default: 40 years)
        BW      : float, body weight; (0 <= BW) (default: 70 kg)
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
        Cm  : mass concentration of chemical in air (mg/m^3)
        I   : float, inhalation potential dose rate (mg/day)
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
        """
        kwargs = inhalation_model.__init__(self, ED=ED, NWexp=NWexp, NS=NS,
                                           EY=EY, BW=BW, ATc=ATc, AT=AT)
        self.model_name = 'EPA-OPPT Automobile Refinish Spray Coating'
        self.equations = """
                         Cm = KCk * Ys
                         I = Cm * b * h
                         NW = NWexp * NS
                         LADD = (I * ED * EY) / (BW * ATc * days_per_year)
                         ADD = (I * ED * EY) / (BW * AT * days_per_year)
                         APDR = I / BW
                         """
        self.scenario = str(scenario).lower().replace(", ",",")
        if (self.scenario not in self.get_scenarios()):
            raise ScenarioException("Error! Invalid value for class argument 'scenario' ("
                                    + str(self.scenario)+"). Options are '"
                                    + "', '".join(self.get_scenarios()) + "'.")
        kwargs['route'] = self.route

        if (self.scenario == "conventional,downdraft"):
            kwargs['KCk'] = 2.3
        elif (self.scenario == "conventional,crossdraft"):
            kwargs['KCk'] = 15
        elif (self.scenario == "hvlp,downdraft"):
            kwargs['KCk'] = 1.9
        elif (self.scenario == "hvlp,crossdraft"):
            kwargs['KCk'] = 15
        elif (self.scenario == "user"):
            kwargs['KCk'] = KCk


        kwargs['Ymist'] = checks.check_ul('Ymist',Ymist,0,1)
        kwargs['Ysf'] = checks.check_ul('Ysf',Ysf,0,1)

        if Ys == None:
            kwargs['Ys'] = checks.check_ul('Ys',min((kwargs['Ymist']/kwargs['Ysf']), 1),0,1)
        else:
            kwargs['Ys'] = checks.check_ul('Ys',Ys,0,1)

        kwargs['b'] = checks.check_ul('b',b,0,7.9)
        kwargs['h'] = checks.check_ul('h',h,0,24)

        self.inputs = self.model_args(kwargs)
        kwargs['skips'] = kwargs['skips'] + list(kwargs.keys())

        kwargs['Cm'] = self._Cm(**kwargs)
        kwargs['PDR'] = exposures.potential_dose_rate(**kwargs)
        kwargs['NW'] = exposures.workers_exposed(**kwargs)
        kwargs['LADD'] = exposures.daily_dose(t=kwargs['ATc'], **kwargs)
        kwargs['ADD'] = exposures.daily_dose(t=kwargs['AT'], **kwargs)
        kwargs['APDR'] = exposures.acute_potential_dose_rate(**kwargs)

        self.outputs = self.model_args(kwargs)
        self.outputs['I'] = self.outputs.pop('PDR')

        return

    def _Cm(self,KCk, Ys, **kwargs):
        return KCk * Ys

    @classmethod
    def get_scenarios(self):
        return ['conventional,downdraft', 'conventional,crossdraft',
                'hvlp,downdraft', 'hvlp,crossdraft', 'user']


class automobile_spray_coating(inhalation_model):
    """
    Class for ChemSTEER's EPA-OPPT Automobile Spray Coating Inhalation Exposure Model
    """
    def __init__(self, scenario='high,conventional,crossdraft', KCk=18.4, b=1.25, h=8,
                 ED=1, NWexp=3, NS=1, EY=40, BW=70, ATc=70, AT=40):
        """
        Required Arguments:
        ------------------

        Optional Arguments:
        -------------------
        scenario: string, which type of scenario to use for model calculation
                  ['low,conventional,crossdraft'|'high,conventional,crossdraft'|
                   'low,conventional,downdraft'|'high,conventional,downdraft',
                   'low,hvlp,crossdraft'|'high,hvlp,crossdraft'|'low,hvlp,downdraft'|
                   'high,hvlp,downdraft'] (default: 'high,conventional,crossdraft')
        KCk     : float, mass concentration total particulate in air
                  (default: 18.4 mg/m^3)
        b       : volumetric inhalation rate; 0 <= b <=7.9 (default: 1.25 m^3/hr)
        h       : daily exposure duration; 0 <= h <= 24 (default: 8 hrs/day)
        ED      : integer, days exposed per year; 0 <= ED <= 365 (default: 1 days/site-yr)
        NWExp   : integer, number of workers exposed while performing the activity
                  (default: 3 workers/site)
        NS      : integer, number of sites (default: 1 site)
        EY      : integer, years of occupational exposure; 0 <= EY (default: 40 years)
        BW      : float, body weight; (0 <= BW) (default: 70 kg)
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
        Cm  : mass concentration of chemical in air (mg/m^3)
        I   : float, inhalation potential dose rate (mg/day)
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
        """
        kwargs = inhalation_model.__init__(self, ED=ED, NWexp=NWexp, NS=NS,
                                           EY=EY, BW=BW, ATc=ATc, AT=AT)
        self.model_name = 'EPA-OPPT Automobile Spray Coating'
        self.equations = """
                         Cm = KCk
                         I = Cm * b * h
                         NW = NWexp * NS
                         LADD = (I * ED * EY) / (BW * ATc * days_per_year)
                         ADD = (I * ED * EY) / (BW * AT * days_per_year)
                         APDR = I / BW
                         """
        self.scenario = str(scenario).lower().replace(", ",",")
        if (self.scenario not in self.get_scenarios()):
            raise ScenarioException("Error! Invalid value for class argument 'scenario' ("
                                    + str(self.scenario)+"). Options are '"
                                    + "', '".join(self.get_scenarios()) + "'.")
        kwargs['route'] = self.route

        if (self.scenario == "low,conventional,crossdraft"):
            kwargs['KCk'] = 0.05
        elif (self.scenario == "high,conventional,crossdraft"):
            kwargs['KCk'] = 18.4
        elif (self.scenario == "low,conventional,downdraft"):
            kwargs['KCk'] = 0.01
        elif (self.scenario == "high,conventional,downdraft"):
            kwargs['KCk'] = 3.7
        elif (self.scenario == "low,hvlp,crossdraft"):
            kwargs['KCk'] = 1.0
        elif (self.scenario == "high,hvlp,crossdraft"):
            kwargs['KCk'] = 5.2
        elif (self.scenario == "low,hvlp,downdraft"):
            kwargs['KCk'] = 0.6
        elif (self.scenario == "high,hvlp,downdraft"):
            kwargs['KCk'] = 1.4
        elif (self.scenario == "user"):
            kwargs['KCk'] = KCk

        kwargs['b'] = b
        kwargs['h'] = h

        self.inputs = self.model_args(kwargs)
        kwargs['skips'] = kwargs['skips'] + list(kwargs.keys())

        kwargs['Cm'] = self._Cm(**kwargs)
        kwargs['PDR'] = exposures.potential_dose_rate(**kwargs)
        kwargs['NW'] = exposures.workers_exposed(**kwargs)
        kwargs['LADD'] = exposures.daily_dose(t=kwargs['ATc'], **kwargs)
        kwargs['ADD'] = exposures.daily_dose(t=kwargs['AT'], **kwargs)
        kwargs['APDR'] = exposures.acute_potential_dose_rate(**kwargs)

        self.outputs = self.model_args(kwargs)
        self.outputs['I'] = self.outputs.pop('PDR')

        return

    def _Cm(self, KCk, **kwargs):
        return KCk

    @classmethod
    def get_scenarios(self):
        return ['low,conventional,crossdraft', 'high,conventional,crossdraft',
                'low,conventional,downdraft', 'high,conventional,downdraft',
                'low,hvlp,crossdraft', 'high,hvlp,crossdraft',
                'low,hvlp,downdraft', 'high,hvlp,downdraft']

class uv_roll_coating(inhalation_model):
    """
    Class for ChemSTEER's EPA-OPPT UV Roll Coating Inhalation Exposure Model
    """
    def __init__(self, Ymist, scenario='high end of range', KCk=0.26, Ys=None, Ysf=0.25,
                 b=1.25, h=8, ED=1, NWexp=1, NS=1, EY=40, BW=70, ATc=70, AT=40):
        """
        Required Arguments:
        ------------------
        Ymist : float, weight fraction of the chemical in mist; 0 <= Ymist <= 1
                (dimensionless)

        Optional Arguments:
        -------------------
        scenario: string, which type of scenario to use for model calculation
                  ['low end of range'|'high end of range']
                  (default: 'conventional,crossdraft')
        KCk     : float, mass concentration total particulate in air; based on an OSHA PEL
                  for PNOR-TWA (default: 0.26 mg/m^3)
        Ys      : None or float, weight fraction of the chemical in particulate or non-
                  volatiles fraction of mist; 0 <= Ymist <= 1; if None is min(Ymist/Ysf,1)
                  (default: None dimensionless)
        b       : volumetric inhalation rate; 0 <= b <=7.9 (default: 1.25 m^3/hr)
        h       : daily exposure duration; 0 <= h <= 24 (default: 8 hrs/day)
        ED      : integer, days exposed per year; 0 <= ED <= 365 (default: 1 days/site-yr)
        NWExp   : integer, number of workers exposed while performing the activity
                  (default: 1 workers/site)
        NS      : integer, number of sites (default: 1 site)
        EY      : integer, years of occupational exposure; 0 <= EY (default: 40 years)
        BW      : float, body weight; (0 <= BW) (default: 70 kg)
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
        Cm  : mass concentration of chemical in air (mg/m^3)
        I   : float, inhalation potential dose rate (mg/day)
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
        """
        kwargs = inhalation_model.__init__(self, ED=ED, NWexp=NWexp, NS=NS,
                                           EY=EY, BW=BW, ATc=ATc, AT=AT)
        self.model_name = 'EPA-OPPT UV Roll Coating'
        self.equations = """
                         Cm = KCk * Ys
                         I = Cm * b * h
                         NW = NWexp * NS
                         LADD = (I * ED * EY) / (BW * ATc * days_per_year)
                         ADD = (I * ED * EY) / (BW * AT * days_per_year)
                         APDR = I / BW
                         """
        self.scenario = str(scenario).lower().replace(", ",",")
        if (self.scenario not in self.get_scenarios()):
            raise ScenarioException("Error! Invalid value for class argument 'scenario' ("
                                    + str(self.scenario)+"). Options are '"
                                    + "', '".join(self.get_scenarios()) + "'.")

        kwargs['route'] = self.route
        if (self.scenario == "low end of range"):
            kwargs['KCk'] = 0.04
        elif (self.scenario == "high end of range"):
            kwargs['KCk'] = 0.26
        elif (self.scenario == "user"):
            kwargs['KCk'] = KCk

        kwargs['Ymist'] = checks.check_ul('Ymist',Ymist,0,1)
        kwargs['Ysf'] = checks.check_ul('Ysf',Ysf,0,1)

        if Ys == None:
            kwargs['Ys'] = checks.check_ul('Ys',min((kwargs['Ymist']/kwargs['Ysf']), 1),0,1)
        else:
            kwargs['Ys'] = checks.check_ul('Ys',Ys,0,1)

        kwargs['b'] = checks.check_ul('b',b,0,7.9)
        kwargs['h'] = checks.check_ul('h',h,0,24)

        self.inputs = self.model_args(kwargs)
        kwargs['skips'] = kwargs['skips'] + list(kwargs.keys())

        kwargs['Cm'] = self._Cm(**kwargs)
        kwargs['PDR'] = exposures.potential_dose_rate(**kwargs)
        kwargs['NW'] = exposures.workers_exposed(**kwargs)
        kwargs['LADD'] = exposures.daily_dose(t=kwargs['ATc'], **kwargs)
        kwargs['ADD'] = exposures.daily_dose(t=kwargs['AT'], **kwargs)
        kwargs['APDR'] = exposures.acute_potential_dose_rate(**kwargs)

        self.outputs = self.model_args(kwargs)
        self.outputs['I'] = self.outputs.pop('PDR')

        return

    def _Cm(self, KCk, Ys, **kwargs):
        return KCk * Ys

    @classmethod
    def get_scenarios(self):
        return ['low end of range', 'high end of range']


class user_defined_inhalation(inhalation_model):
    """
    Class for ChemSTEER's User-defined Inhalation Exposure Model
    """
    def __init__(self, Cv, MW, h, scenario='user', Cm=None, Vm=24.45, Ys=1, b=1.25,
                 ED=1, NWexp=1, NS=1, EY=40, BW=70, ATc=70, AT=40):
        """
        Required Arguments:
        ------------------
        Cv : float, volumetric concentration of chemical in air; 0 <= Cv (ppm)
        MW : float, molecular weight of chemical; 0 <= MW (g/mol)
        h  : daily exposure duration; 0 <= h <= 24 (hrs/day)

        Optional Arguments:
        -------------------
        scenario: string, which type of scenario to use for model calculation
                  ['user'] (default: 'user')
        Cm      : None or float,  mass concentration of chemical in air; 0 <= Cm; if None
                  value is evaluated with model equation for Cm (mg/m^3)
        Ys      : float, weight fraction of the chemical in particulate or solids in
                  mixture; 0 <= Ymist <= 1 (default: 1 dimensionless)
        b       : volumetric inhalation rate; 0 <= b <=7.9 (default: 1.25 m^3/hr)
        ED      : integer, days exposed per year; 0 <= ED <= 365 (default: 1 days/site-yr)
        NWExp   : integer, number of workers exposed while performing the activity
                  (default: 3 workers/site)
        NS      : integer, number of sites (default: 1 site)
        EY      : integer, years of occupational exposure; 0 <= EY (default: 40 years)
        BW      : float, body weight; (0 <= BW) (default: 70 kg)
        ATc     : float, averaging time over a lifetime (0 <= ATc); (default: 70 years)
        AT      : float, averaging time (EY <= AT <= ATc); (default: 40 years)

        Stored Attributes
        -------------------
        model_name: string, name of model as it appears in ChemSTEER
        equations : string, equations for ChemSTEER model taken from the User Guide and
                    compared against the ChemSTEER program

        Computed Attributes
        -------------------
        Cm  : mass concentration of chemical in air (mg/m^3)
        I   : float, inhalation potential dose rate (mg/day)
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

        Methods
        -------------------
        get_scenarios : list, names of provided scenarios available in ChemSTEER; an
                        additional `user` option has been added for full flexible use of
                        the model
        """
        kwargs = inhalation_model.__init__(self, ED=ED, NWexp=NWexp, NS=NS,
                                           EY=EY, BW=BW, ATc=ATc, AT=AT)
        self.model_name = 'User-defined Inhalation'
        self.equations = """
                         Cm = Cv * MW / Vm * Ys
                         I = Cm * b * h
                         NW = NWexp * NS
                         LADD = (I * ED * EY) / (BW * ATc * days_per_year)
                         ADD = (I * ED * EY) / (BW * AT * days_per_year)
                         APDR = I / BW
                         """
        self.scenario = str(scenario).lower().replace(", ",",")
        if scenario not in self.get_scenarios():
            raise ScenarioException("Error! Invalid value for class argument 'scenario' ("
                                    + str(self.scenario)+"). Options are '"
                                    + "', '".join(self.get_scenarios()) + "'.")

        kwargs['route'] = self.route
        kwargs['Cv'] = Cv
        kwargs['MW'] = MW
        kwargs['Vm'] = checks.check_l('Vm',Vm,0)
        kwargs['Ys'] = checks.check_ul('Ys',Ys,0,1)

        if Cm == None:
            kwargs['Cm'] = checks.check_l('Cm',Cv * MW / Vm * Ys,0)
        else:
            kwargs['Cm'] = checks.check_l('Cm',Cm,0)

        kwargs['b'] = checks.check_ul('b',b,0,7.9)
        kwargs['h'] = checks.check_ul('h',h,0,24)

        self.inputs = self.model_args(kwargs)
        kwargs['skips'] = kwargs['skips'] + list(kwargs.keys())

        kwargs['PDR'] = exposures.potential_dose_rate(**kwargs)
        kwargs['NW'] = exposures.workers_exposed(**kwargs)
        kwargs['LADD'] = exposures.daily_dose(t=kwargs['ATc'], **kwargs)
        kwargs['ADD'] = exposures.daily_dose(t=kwargs['AT'], **kwargs)
        kwargs['APDR'] = exposures.acute_potential_dose_rate(**kwargs)

        self.outputs = self.model_args(kwargs)
        self.outputs['I'] = self.outputs.pop('PDR')

        return

    @classmethod
    def get_scenarios(self):
        return ['user']
