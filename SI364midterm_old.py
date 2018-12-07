###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_script import Manager, Shell
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField # Note that you may need to import more here! Check out examples that do what you want to figure out what.
from wtforms.validators import Required,NumberRange # Here, too
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from pprint     import pprint
import webbrowser

# my own modules
from cache import *
import maps  


## App setup code
app = Flask(__name__)
app.debug = True

## All app.config values
app.config['SECRET_KEY'] = 'hardtoguessstringfromsi364'
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/midterm_test"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Set up Flask debug stuff
manager = Manager(app)
db = SQLAlchemy(app) # For database use

migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


## Statements for db setup (and manager setup if using Manager)
db = SQLAlchemy(app)


######################################
######## HELPER FXNS (If any) ########
######################################
DATAGOV_APIKEY = 'DEMO_KEY'
DEBUG = False # this is for debuggin the nutrition data

def fetch_ndbnos_list(search_term, offset=0):
    # documentation is here:
    # https://ndb.nal.usda.gov/ndb/doc/apilist/API-SEARCH.md
    base_url = "https://api.nal.usda.gov/ndb/search/"
    
    p = {
        "format":"json",
        "q":search_term,
        "sort":"r",
        "max":session['results_num'],           # return first n results
                            # lets paging possible

        "offset":offset,    # this will return starting at a certain number, 
                            # helpful if user wants to see more
        "ds":"", # 'Standard Reference' or 'Branded Food Products' or ''
        "api_key":DATAGOV_APIKEY
    }

    # making a request with caching to the USDA
    json_data = cached_reqest(base_url,params = p)

    ndbnos_list = None
    try: 
        ndbnos_list = json_data['list']['item']
        return ndbnos_list
    except:
        print(json_data)
        return None
def fetch_nutrition(ndbno):
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
    #   ndbno     y   n/a         A list of up to 50 NDB numbers
    #   type      n   b(basic)    Report type: [b]asic or [f]ull or [s]tats
    #   format1   n   JSON        Report format: xml or json

    # TODO, switch 'type' to f if needed full report
    base_url = "https://api.nal.usda.gov/ndb/V2/reports"
    p = {
        "format":"json",
        "ndbno": ndbno,
        "type":"b",
        "api_key":DATAGOV_APIKEY
    }
    
    json_data = cached_reqest(base_url,params = p)

    try:
        error_test = json_data['foods']
    except:
        return (0,'api_error')


    # blank dictonary to hold values of interest
    data = maps.blank_nutri_map

    # saving nutri name and ndbno into the dict
    data['name']= json_data['foods'][0]['food']['desc']['name']
    data['kcal']= float(json_data['foods'][0]['food']['nutrients'][1]['value'])
    data['ndbno']= ndbno

    # extracting the values from the JSON data
    for nutrient in json_data['foods'][0]['food']['nutrients']:
        nutrient_id    = int(nutrient['nutrient_id'])
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
def get_nutri_index(data):
    # DESCR:    calculates health index of a food item
    #           data can be recieved from fetch_nutrition
    # RETURN:   health index value
    # REQUIRES: nutrition data dictionary
    # MODIFIES: nothing

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

    # returning the health index in percent
    return hlth_idx * 100
def redirect_url(default='home'):
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)

def get_or_create_food(name):
    newfood = Food.query.filter_by(name=name).first()
    if not newfood:
        newfood = Food(name=name)
        db.session.add(newfood)
        db.session.commit()
    return newfood

def get_or_create_user(name):
    newuser = Name.query.filter_by(name=name).first()
    if not newuser:
        newuser = Name(name=name)
        db.session.add(newuser)
        db.session.commit()
    return newuser


##################
##### MODELS #####
##################
class Name(db.Model):
    __tablename__ = "names"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64))
    foods = db.relationship('Food',backref='Name')

    def __repr__(self):
        return "{} (ID: {})".format(self.name, self.id)


class Food(db.Model):
    __tablename__ = "foods"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64))
    health_index = db.Column(db.Integer)
    user_id = db.Column(db.Integer,db.ForeignKey("names.id"))



###################
###### FORMS ######
###################

def num_checker(min = 1):
    error_message = "Should be a number!"

    def _num_checker(form,field):
        if num < min:
            raise ValidationError(error_message)
    return _word_count_check


class NameForm(FlaskForm):
    name = StringField("Please enter your name  >",validators=[Required()])
    submit = SubmitField()

class SearchForm(FlaskForm):
    search_term = StringField("Enter search term",validators=[Required()])
    myChoices   = [('1','1'),('5','5'),('10','10'),('20','20'),('30','30'),('50','50'),('100','100'),('1000','1000')] 
    results_num = SelectField("Result number", choices = myChoices, default=10)
    submit = SubmitField()

class SelectFoodForm(FlaskForm):
    select = SubmitField('Calculate index')
    favorite = SubmitField('★')
        



#######################
###### VIEW FXNS ######
#######################

@app.context_processor
def inject_search_form():
    search_form = SearchForm()
    return dict(search_form=search_form)


@app.route('/', methods=['GET', 'POST'])
def home():
    form = NameForm() # User should be able to enter name after name and each one will be saved, even if it's a duplicate! Sends data with GET
    if form.validate_on_submit():
        name = form.name.data
        session['name'] = name

        # checking if the user exists already in the DB
        user_name = Name.query.filter_by(name=name).first()
        if not user_name:
            newname = Name(name=name)
            db.session.add(newname)
            db.session.commit()

        return redirect(url_for('all_names'))
    return render_template('home.html',form=form)

@app.route('/names')
def all_names():
    names = Name.query.all()
    return render_template('name_example.html', names=names)





# {{back_link}}


@app.route('/search', methods=['GET', 'POST'])
def food_search():
    # create a form to ask for search term
    search_form = SearchForm()

    # if form was not submitted yet:
    if request.args.get("search_term") == None:
        # print the form for the user
        return render_template('search.html', search_form=search_form)
    else:
        # this is the form to be used when selecting which result to calculate
        form_select = SelectFoodForm()


        # recording the GET parammeters
        search_term = request.args.get("search_term")
        results_num = int(request.args.get("results_num"))

        # setting the number of results used by the user
        session['results_num'] = results_num
        search_results = fetch_ndbnos_list(search_term)
        print(search_results,search_term)

        return render_template('search_results.html', search_term = search_term, search_results=search_results, form_select=form_select)
        # ,search_term=search_term, num=session['results_num'] 


@app.route('/food_stats/<ndbno>', methods=['GET','POST'])
def food_stats(ndbno):
    food_data = fetch_nutrition(ndbno)
    health_idx = get_nutri_index(food_data)
    if health_idx < 0:
        bgcolor = "background-color: #e01717;"
    else: bgcolor = "background-color: #2cbb80;"
    return render_template('food_stats.html', health_idx = health_idx, name = food_data['name'], bgcolor=bgcolor, back_link=redirect_url())





@app.route('/add_favorite/<ndbno>', methods=['GET','POST'])
def add_favorite(ndbno):
    user = get_or_create_user(name = session['name'])
    food = get_or_create_food(ndbno = ndbno)
    user.foods.append()
    return redirect (redirect_url())


@app.route('/favorites/', methods=['GET','POST'])
def favorites():

    return session['name']




@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', e = e)

## Code to run the application...
# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
if __name__ == '__main__':
    webbrowser.open('http://localhost:5000/')
    db.create_all()
    manager.run() # NEW: run with this: python main_app.py runserver
    # Also provides more tools for debugging


