import helper
import texts

import maps
import models
from pprint     import pprint
from maps       import *
from secrets    import *
from cache      import *
from api_key    import *

DEBUG = False



# here are all the classes for the FOOD HEALTH ESTIMATOR

# class food
class Food():
    def __init__(self, ndbno):

        # getting the complete nutrition information 
        self.data  = self.fetch_nutrition()

        # calculationg the health points for the food
        self.index  = self.nutri_index()


        # this are redundant but for ease of access
        self.ndbno  = ndbno
        self.name   = self.data['name']
        self.kcal   = self.data['kcal']

        # for conveniece aliasing the map as d
        d = maps.RNP 
        self.protein    = self.data[ d['Protein'] ]['value']
        self.carbs      = self.data[ d['Carbs'  ] ]['value']
        self.fats       = self.data[ d['Fats'   ] ]['value']
        self.fiber      = self.data[ d['Fiber'  ] ]['value']
        self.sugars     = self.data[ d['Sugars' ] ]['value']


    def fetch_nutrition(self):
        '''
        DESCR:     gets nutrition data about given food item
                   ndbno numbers can be recieved from fetch_ndbno_list
        RETURN:    dictionary with food item nutrition (id is key)
                   data = {
                        "203": {'name':' ', 'unit': 'None', 'value':0},
                        "204": {'name':' ', 'unit': 'None', 'value':0},
                        ...
                        "name":         "",
                        "kcal":         0,
                        "ndbno":        0,
                        "health_index": 0
                   }
                   see maps.py for complete documentation
        REQUIRES:  ndbno of food
        MODIFIES:  nothing
        '''

        # URL: https://ndb.nal.usda.gov/ndb/doc/apilist/API-FOOD-REPORTV2.md
        # PARAMETERS:
        #   api_key   y   n/a         Must be a data.gov registered API key
        #   ndbno     y   n/a         A list of up to 50 NDB numbers {!!!!!!!}
        #   type      n   b(basic)    Report type: [b]asic or [f]ull or [s]tats
        #   format1   n   JSON        Report format: xml or json

        # TODO, switch 'type' to f if needed full report
        # to get it from terminal use: curl -H "Content-Type:application/json" -d '{"ndbno":["01009","45202763","35193"],"type":"b"}' DEMO_KEY@api.nal.usda.gov/ndb/V2/reports
        base_url = "https://api.nal.usda.gov/ndb/V2/reports"
        p = {
            "format":"json",
            "ndbno": self.ndbno,
            "type":"b",
            "api_key":DATAGOV_APIKEY
        }
        
        json_data = cached_reqest(base_url,params = p)

        try:
            error_test = json_data['foods']
        except:
            print("FATAL ERROR: api did not return a valid response\nAPI RESPONSE:" + str(json_data))
            return (0,'api_error')


        # blank dictonary to hold values of interest
        data = maps.blank_nutri_map

        # saving nutri name and ndbno into the dict
        data['name']= json_data['foods'][0]['food']['desc']['name']
        data['kcal']= float(json_data['foods'][0]['food']['nutrients'][1]['value'])
        data['ndbno']= self.ndbno

        # extracting the values from the JSON data
        for nutrient in json_data['foods'][0]['food']['nutrients']:
            nutrient_id = int(nutrient['nutrient_id'])
            data[nutrient_id] = {
                "name": nutrient['name'],
                "unit": nutrient['unit'],
                "value": float(nutrient['value']),
                # TODO: this one is measures for common serving, not needed yet
                # implement it if you'd like to give people calculating options
                # "measures": nutrient['measures']
            }

        data['health_index'] = get_nutri_index(data)

        # for debugging purposes
        if DEBUG == True:
          pprint(data)

        return data 

    def get_nutri_index(self):
        # DESCR:    calculates health index of a food item
        #           data can be recieved from fetch_nutrition
        # RETURN:   health index value
        # REQUIRES: nutrition data dictionary
        # MODIFIES: nothing

        data = self.data

        # extracting necessary data for calculating HLTH_IDX
        name    = data['name']
        kcal    = data[208]['value'] if data[208]['value'] else 1
        vit_c   = data[401]['value']
        vit_a   = data[318]['value']
        vit_k   = data[430]['value']
        vit_d   = data[324]['value']

        # for conveniece aliasing the map as d
        d = maps.RNP 
        protein     = data[ d['Protein'               ] ]['value']
        carbs       = data[ d['Carbs'                 ] ]['value']
        fats        = data[ d['Fats'                  ] ]['value']
        fiber       = data[ d['Fiber'                 ] ]['value']
        sugars      = data[ d['Sugars'                ] ]['value']
        cholesterol = data[ d['Cholesterol'           ] ]['value']
        sodium      = data[ d['Sodium'                ] ]['value']
        sat_f       = data[ d['Saturated Fat'         ] ]['value']
        trans_f     = data[ d['Trans Fat'             ] ]['value']
        pol_f       = data[ d['Polyunsaturated Fat'   ] ]['value']
        mon_f       = data[ d['Monounsaturated Fat'   ] ]['value']


        # GOOD STUFF
        good_fats       = (pol_f*8 + mon_f*4)
        good_vitamins   = (vit_k/7 + vit_a/800 + vit_c + vit_d)
        good_protein    = protein*4

        # BAD STUFF
        bad_fats        = (sat_f*16 + trans_f*400)
        bad_sodium      = sodium
        bad_sugar       = (sugars*15 - fiber*150)
        bad_cholesterol = (cholesterol*7)


        # my proprietary formula for calculating HLTH IDX
        hlth_idx = (kcal 
            + good_fats 
            + good_vitamins
            + good_protein
            - bad_fats
            - bad_sodium 
            - bad_sugar
            - bad_cholesterol)/kcal/2

        # baseline - Water's IDX = 0 %
        hlth_idx_water  = 0

        # returning the health index
        return hlth_idx * 100

    def __str__(self):
        index = round(self.index)

        if index >  400:
            emoji = "🤩🤩🤩🌱"
            percent = "|████████|"
        elif index >= 100:
            emoji = "🤩"
            percent = "|██████░░|"
        elif index >= 50:
            emoji = "😋"
            percent = "|█████░░░|"
        elif index >=0:
            emoji = "😐"
            percent = "|████░░░░|"
        elif index >= -50:
            emoji = "😖"
            percent = "|███░░░░░|"
        elif index >= -150:
            emoji = "🤢"
            percent = "|██░░░░░░|"
        elif index >= -250:
            emoji = "🤮"
            percent = "|█░░░░░░░|"
        else:
            emoji = "🤢🤢🤮🤢🤢"
            percent = "|░░░░░░░░|"

        major_nutrients = [self.name,repr(index),percent,emoji,self.protein,self.carbs,self.fats,self.fiber,self.sugars,self.ndbno]
        return {'emoji':emoji,'nutrition':major_nutrients}

def fetch_ndbnos_list(search_term, offset=0):
    '''
    DESCR:    returns food name&ndbno numbers, used by fetch_nutrition()
    RETURN:   list of ndbno numbers
    REQUIRES: 'search term' (required), 
              'offset'      (optional)
    MODIFIES: Nothing
    '''

    # Documentation      https://ndb.nal.usda.gov/ndb/doc/apilist/API-SEARCH.md
    # TODO try using 'Branded Food Products' for 'ds'
    # TODO IDEA: you can use 
    base_url = "https://api.nal.usda.gov/ndb/search/"
    p = {
        "format":"json",
        "q":search_term,
        "sort":"r",
        "max":11,           # return first 11 results
                            # lets paging possible

        "offset":offset,    # this will return starting at a certain number, 
                            # helpful if user wants to see more
        "ds":"Standard Reference", # or 'Branded Food Products'
        "api_key":DATAGOV_APIKEY
    }

    # making a request with caching to the USDA
    json_data = cached_reqest(base_url,params = p)

    ndbnos_list = None
    try: 
        ndbnos_list = json_data['list']['item']
        return ndbnos_list
    except: 
        return None

if __name__=="__main__":

    kale     = Food(11233)
    kale.compare_to(Food(14555))
    kale.compare_to_many([Food(19375),Food(14156)])

    # Food(14555) - water
    # food_list = [Food(19375),Food(14156)] - kale and redbull



# data-base
# cache
# test cases show
# run them
# interractive