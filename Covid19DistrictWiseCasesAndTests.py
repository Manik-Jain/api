# -*- coding: utf-8 -*-

import requests
import json
import os
import datetime

covid_tests = requests.get("https://api.covid19india.org/state_test_data.json").json()

raw_innput_data = [requests.get("https://api.covid19india.org/raw_data1.json").json(), 
        requests.get("https://api.covid19india.org/raw_data2.json").json(),
        requests.get("https://api.covid19india.org/raw_data3.json").json()]

country_dict = {}
test_dict = {}
tested = 0

def fillCaseDictionary(hospitalized, recovered, deceased):
    return {
            'hospitalized' : hospitalized,
            'recovered' : recovered,
            'deceased' : deceased
            }

def fillTestDict(value):
    global tested
    tested += int(value.get('totaltested')) if value.get('totaltested') else 0
    return {
            'positive' : int(value.get('positive')) if value.get('positive') else "Data not available",
            'negative' : int(value.get('negative')) if value.get('negative') else "Data not available",
            'unconfirmed' : int(value.get('unconfirmed')) if value.get('unconfirmed') else "Data not available",
            'total_tested' : int(value.get('totaltested')) if value.get('totaltested') else "Data not available",
            'people_in_quarantine' : int(value.get('totalpeoplecurrentlyinquarantine')) if value.get('totalpeoplecurrentlyinquarantine') else "Data not available",
            'people_released' : int(value.get('totalpeoplereleasedfromquarantine')) if value.get('totalpeoplereleasedfromquarantine') else "Data not available",
            }

def filterCases(value):
    hospitalized = int(value.get('numcases')) if (value.get('currentstatus') == "Hospitalized") else 0
    recovered = int(value.get('numcases')) if (value.get('currentstatus') == "Recovered") else 0
    deceased = int(value.get('numcases')) if (value.get('currentstatus') == "Deceased") else 0
    country_cases.update(fillCaseDictionary(country_cases.get('hospitalized') + hospitalized,
                                            country_cases.get('recovered') + recovered,
                                            country_cases.get('deceased') + deceased,
                                            ))
    return fillCaseDictionary(hospitalized, recovered, deceased)

def extractData(value, currentStateCases, currentDistrictCases):
    districtCases = filterCases(value)
    extractedData = {
            value.get('dateannounced') : districtCases,
            'stateCases' : {}
            }
    
    if currentStateCases == 0:
        extractedData.update({'stateCases' : districtCases })
    
    elif currentStateCases != 0 and currentDistrictCases == 0:
        currentStateCases.update(fillCaseDictionary(int(currentStateCases.get('hospitalized')) + int(districtCases.get('hospitalized')),
                                                    int(currentStateCases.get('recovered')) + int(districtCases.get('recovered')),
                                                    int(currentStateCases.get('deceased')) + int(districtCases.get('deceased'))))
        extractedData.update({'stateCases' : currentStateCases })
    
    elif currentStateCases != 0 and currentDistrictCases != 0:
        h = 0
        r = 0
        if int(districtCases.get('hospitalized')) > 0 :
            h = int(districtCases.get('hospitalized'))
        elif int(districtCases.get('recovered')) > 0 :
            r = int(districtCases.get('recovered'))
        
        if value.get('dateannounced') in currentDistrictCases:
            currentCases = currentDistrictCases.get(value.get('dateannounced')).get(value.get('dateannounced'))
            updated_date_for_date = fillCaseDictionary(int(currentCases.get('hospitalized')) + int(districtCases.get('hospitalized')),
                                                       int(currentCases.get('recovered')) + int(districtCases.get('recovered')),
                                                       int(currentCases.get('deceased')) + int(districtCases.get('deceased')))
            extractedData.get(value.get('dateannounced')).update(updated_date_for_date)
            
            extractedData.get('stateCases').update(fillCaseDictionary(int(currentStateCases.get('hospitalized')) + (h),
                                                   int(currentStateCases.get('recovered')) + r,
                                                   int(currentStateCases.get('deceased')) + int(districtCases.get('deceased'))))
        else: 
            extractedData.get('stateCases').update(fillCaseDictionary(int(currentStateCases.get('hospitalized')) + (h),
                                                   int(currentStateCases.get('recovered')) + r,
                                                   int(currentStateCases.get('deceased')) + int(districtCases.get('deceased'))))
    return extractedData
     
def prepareTestData():    
    for test_data in covid_tests.values():
        for value in test_data:
            detectedTestState = value.get('state')
            detectedTestDate = value.get('updatedon')
            if not detectedTestState:
                detectedTestState = "UnDeclared_State"
            if not detectedTestDate:
                 detectedTestDate = "Undeclared_date"
            if detectedTestState in test_dict.keys():
                test_dict.get(detectedTestState).update({detectedTestDate : fillTestDict(value)})
            else:
                test_dict[detectedTestState] = {detectedTestDate : fillTestDict(value)}

country_cases = fillCaseDictionary(0,0,0)
def prepareCountryReport():
    prepareTestData()
    for raw_data in raw_innput_data:
        for covid_case in raw_data.values():
            for value in covid_case:
                detectedState = value.get('detectedstate')
                detecteddistrict = value.get('detecteddistrict')
                if not detectedState:
                    detectedState = "UnDeclared_State"
                elif not detecteddistrict:
                    detecteddistrict = "UnDeclared_District"
                if not value.get('numcases') or int(value.get('numcases')) < 0:
                    value.update({'numcases' : 0})
                
                if country_dict.get(detectedState) :
                    if detecteddistrict in country_dict.get(detectedState).keys():
                        last_key = list(country_dict.get(detectedState).get(detecteddistrict).keys())[-1]
                        data = extractData(value, country_dict.get(detectedState).get('stateCases'), country_dict.get(detectedState).get(detecteddistrict))
                        country_dict.get(detectedState).get(detecteddistrict).update({value.get('dateannounced') : data})
                        country_dict.get(detectedState).update({'stateCases' : data.get('stateCases')})
                    else :
                        currentStateCases = country_dict.get(detectedState)
                        data = extractData(value, country_dict.get(detectedState).get('stateCases'), 0)
                        country_dict[detectedState][detecteddistrict] = {value.get('dateannounced') : data}
                        country_dict.get(detectedState).update({'stateCases' : data.get('stateCases')})
                else :
                    data = extractData(value, 0, 0)
                    country_dict[detectedState]= { detecteddistrict : {list(data.keys())[0] : data}, 
                                               'stateCases' : data.get('stateCases'),
                                               'tests_conducted' : test_dict.get(detectedState)}
    
    country_dict.update({'countryCases' : country_cases, 'totalTests' : tested})

def main():
    print('Preparing Covid19 report untill ' + str(datetime.datetime.now()))
    prepareCountryReport()
    if not os.path.exists("../json"):
        os.makedirs("../json")
        
    with open("../json/daily_country_cases_and_tests.json", "w") as f:
        json.dump(country_dict, f, indent = 4)
    
    print('report prepared and downloaded.')

if __name__ == "__main__":
    main()