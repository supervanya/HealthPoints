# Impots for models to work
from __main__ import app
from api_key import DATAGOV_APIKEY
from flask_sqlalchemy import SQLAlchemy
import cache # cache is used for caching the requests to API
import maps # this is a map of nutrients to their names

# Imports for login management
from flask_login import LoginManager, login_required, logout_user, login_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Login configurations setup
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(app)

## Statements for db setup
db = SQLAlchemy(app)

# debug switch, if True will print out function returns to the terminal
DEBUG = False


##################
##### MODELS #####
##################

# association table between Users and Foods (to save favorites)
users_favorites = db.Table('favorites',
                    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                    db.Column('food_id', db.Integer, db.ForeignKey('foods.id'))
                    )

# users model that handles stores passwords, usernames and interfaces to favorites
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    favorites = db.relationship('Food',
                                secondary=users_favorites,
                                backref=db.backref('users', lazy='dynamic'),
                                lazy='dynamic')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

# food model that provides interfacet to work with food items
class Food(db.Model):
    __tablename__ = "foods"
    id = db.Column(db.Integer, primary_key=True)
    ndbno = db.Column(db.Integer, unique=True)
    name  = db.Column(db.String(256))
    hp = db.Column(db.Integer)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data  = self.fetch_nutrition()
        self.hp = self.get_health_points()
        self.name = self.data['name']




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
        
        json_data = cache.cached_reqest(base_url,params = p)

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

        # for debugging purposes
        if DEBUG == True:
          pprint(data)

        return data 

    def get_health_points(self):
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
        protein     = data[ d['Protein'            ] ]['value']
        carbs       = data[ d['Carbs'              ] ]['value']
        fats        = data[ d['Fats'               ] ]['value']
        fiber       = data[ d['Fiber'              ] ]['value']
        sugars      = data[ d['Sugars'             ] ]['value']
        cholesterol = data[ d['Cholesterol'        ] ]['value']
        sodium      = data[ d['Sodium'             ] ]['value']
        sat_f       = data[ d['Saturated Fat'      ] ]['value']
        trans_f     = data[ d['Trans Fat'          ] ]['value']
        pol_f       = data[ d['Polyunsaturated Fat'] ]['value']
        mon_f       = data[ d['Monounsaturated Fat'] ]['value']


        # GOOD STUFF
        good_fats       = (pol_f*8 + mon_f*4)
        good_vitamins   = (vit_k/7 + vit_a/800 + vit_c + vit_d)
        good_protein    = protein*4

        # BAD STUFF
        bad_fats        = (sat_f*16 + trans_f*400)
        bad_sodium      = sodium
        bad_sugar       = (sugars*15 - fiber*150)
        bad_cholesterol = (cholesterol*7)

        # baseline - Water's IDX = 0 %
        hlth_idx_water  = 0

        # my proprietary formula for calculating HLTH IDX
        hlth_idx = (kcal 
            + good_fats 
            + good_vitamins
            + good_protein
            - bad_fats
            - bad_sodium 
            - bad_sugar
            - bad_cholesterol)/kcal/2

        # normalizing to points and saving to 
        health_points = int(hlth_idx * 100)
        self.data['health_index'] = health_points

        # returning the health index
        return health_points

##### USER LOGIN #####

## DB load functions
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) # returns User object or None


##################
##### HELPERS ####
##################

def get_or_create_food(ndbno):
    food = Food.query.filter_by(ndbno=ndbno).first()

    if food: 
        food.__init__()
        print("Food exists! Returning it!")
    else:
        food = Food(ndbno=ndbno)
        db.session.add(food)
        db.session.commit()
        print("created a food item!")
    return food

def add_favorite(food,current_user = current_user):
    if food in current_user.favorites.all():
        print("Food already exists!")
    else:
        current_user.favorites.append(food)
        db.session.commit()
        print("New favorite food! Shiny")



def del_favorite(food):
    current_user.favorites.remove(food)
    db.session.commit()
    print("Bye favorite food! :(")


def update_username(new_username):
    current_user.username = new_username
    db.session.commit()
    print("new username! Shiny!")

def check_username(username):
    user = User.query.filter_by(username = username).first()
    if user:
        return user
    else:
        return False

def get_or_create_user(username, password):
    # returns user either existing or creates a new one
    user = check_username(username)
    if user:
        print("user already exists! returning it")
        return user
    else:
        new_user = User(username = username, password = password)
        db.session.add(new_user)
        db.session.commit()
        print("created a new user! returning it")
        return new_user

def login(username, password):
    # returns user if logged in success or returns None if unsuccessful
    user = check_username(username)
    if user and user.verify_password(password):
        login_user(user)
        print("success = loged in now!")
        return user
    else:
        print("not sure why = but I can't log you in. Check username or password")
        return None

def logout():
    print("Logged out!")
    logout_user()


# kale = Food(ndbno="11233")
# vanya = User(username = "supervanya", password = "010593")

# kale = Food.query.filter_by(ndbno=11233).first()
# vanya = User.query.filter_by(username = "supervanya").first()
# vanya.favorites.append(kale)

# db.session.commit()


# kale = Food(ndbno="11233")
# vanya = User(username = "supervanya", password = "010593")

# kale = Food.query.filter_by(ndbno=11233).first()
# vanya = User.query.filter_by(username = "supervanya").first()
# vanya.favorites.append(kale)

# db.session.commit()
# login_user(vanya) , form.remember_me.data)


# from playground import *
# vanya = User.query.filter_by(username = "supervanya").first()
# login_user(vanya)
# food = Food(ndbno="11223")

# add_favorite(food)

