#!/usr/bin/env
import re
import pandas as pd
import chemsteer as cs


def test_models(model_dict):
    # model_dict = params.copy()
    s = ['/','*','+','-']
    data = []
    i = 0
    for key, value in model_dict.items():
        kwargs = value['args'].copy()
        for kwarg in kwargs.keys():
            if hasattr(kwargs[kwarg],'__iter__'):
                kwargs[kwarg] = pd.np.random.choice(kwargs[kwarg],size=1)[0]
        for scenario in value['method'].get_scenarios():
            kwargs['scenario'] = scenario
            model = value['method'](**kwargs)
            report = cs.reports.json_report(model)
            equations = report['equations']
            if report['route'] == 'dermal':
                outputs = ['Dexp','NW','LADD','ADD','APDR']
            elif report['route'] == 'inhalation':
                outputs = ['Cv','Cm','I','NW','LADD','ADD','APDR']
            # print(key, scenario)
            i += 1
            j = 0
            for rk in outputs:
                if rk not in equations.keys(): continue
                rv = equations[rk]
                record = {}
                record['meta_equation'] = rk+' = '+rv
                record['results_parameter'] = rk
                if (len(re.findall('\(([^)]+)\)',rv)) == 0):
                    terms = [v.strip('(').strip(')').strip() for v in rv.split() if v not in s]
                else:
                    terms = re.findall('\(([^)]+)\)',rv)
                    terms = [v.strip('(').strip(')').strip() for t in terms for v in t.split() if v not in s]
                for term in terms:
                    if term in report['inputs'].keys():
                        record['input_'+term] = report['inputs'][term]
                if ('SQu' in report['inputs'].keys()) and (('S' in terms) and ('Qu' in terms)):
                    record['input_SQu'] = report['inputs']['SQu']
                if rk in report['outputs'].keys():
                    record['results_value'] = report['outputs'][rk]
                record['meta_scenario'] = report['scenario']
                record['meta_model_name'] = report['model_name']
                record['meta_route'] = report['route']
                j += 1
                record['meta_equation_id'] = j
                record['meta_model_run_id'] = i
                data.append(record)
    return data
dermal_models = {'one_hand_liquid_contact':{"method":cs.dermal.one_hand_liquid_contact,
                                            "args":{"Yderm":0.1}},
                 'two_hand_liquid_contact':{"method":cs.dermal.two_hand_liquid_contact,
                                            "args":{"Yderm":0.2}},
                 'two_hand_liquid_immersion':{"method":cs.dermal.two_hand_liquid_immersion,
                                            "args":{"Yderm":0.3}},
                 'two_hand_solids_contact':{"method":cs.dermal.two_hand_solids_contact,
                                            "args":{"Yderm":0.4}},
                 'two_hand_container_surface_contact':{"method":cs.dermal.two_hand_container_surface_contact,
                                            "args":{"Yderm":0.5}},
                 'user_defined_dermal':{"method":cs.dermal.user_defined_dermal,
                                            "args":{"Yderm":0.6}},
                }
inhaltion_models = {'small_volume_solids_handling': {"method":cs.inhalation.small_volume_solids_handling,
                                                     "args":{'Ys':0.1}},
                    'mass_balance': {'method':cs.inhalation.mass_balance,
                                     'args':{"G":1, "MW":92.141, "VP":28.4, 'X':0.2}},
                    'pel_limiting_particulates': {'method':cs.inhalation.pel_limiting_particulates,
                                                  'args':{"Ys": 0.3}},
                    'pel_limiting_vapors': {'method':cs.inhalation.pel_limiting_vapors,
                                            'args': {"Cvk":500, "VP":23.7564, "Ys":0.4, "MW":18.015, "VPpel":28.4, "Ypel":0.6, "MWpel":92.141, "X":0.5}},
                    'total_pnor_pel_limiting': {'method':cs.inhalation.total_pnor_pel_limiting,
                                                'args': {"Ys": 0.5}},
                    'respirable_pnor_pel_limiting': {'method':cs.inhalation.respirable_pnor_pel_limiting,
                                                     'args': {"Ys": 0.6}},
                    'automobile_oem_spray_coating': {'method':cs.inhalation.automobile_oem_spray_coating,
                                                     'args':{"Ymist": 0.7}},
                    'automobile_refinish_spray_coating': {'method':cs.inhalation.automobile_refinish_spray_coating,
                                                          'args':{"Ymist":0.8}},
                    'automobile_spray_coating': {'method': cs.inhalation.automobile_spray_coating,
                                                 'args':{}},
                    'uv_roll_coating': {'method': cs.inhalation.uv_roll_coating,
                                        "args":{"Ymist":0.9}},
                    'user_defined_inhalation': {'method':cs.inhalation.user_defined_inhalation,
                                                'args':{"Cv":500, "MW":92.141, "h":8}}}


dermal = pd.DataFrame(test_models(dermal_models))

inhalation = []
for i in range(3):
    df = pd.DataFrame(test_models(inhaltion_models))
    df['meta_test_id'] = i+1
    inhalation.append(df)
inhalation = pd.concat(inhalation)
inhalation.sort_values(by=['meta_test_id','meta_model_run_id','meta_equation_id'],inplace=True)
inhalation.drop(['meta_test_id','meta_model_run_id','meta_equation_id'],axis=1,inplace=True)
inhalation.to_excel("C:/Users/kphillip/Documents/chemsteer_automation/inhalation_model_tests.xlsx",index=False)
