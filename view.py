from flask import render_template, redirect, url_for, flash, request
from pprint import pprint
import webbrowser
from __main__ import app



# Importing FORMS
from forms import *

# Importing MODELS
from models import *


#######################
###### VIEW FXNS ######
#######################

@app.context_processor
def inject_search_form():
    search_form = SearchForm()
    return dict(search_form=search_form)

@app.route('/welcome', methods=['GET', 'POST'])
def welcome():
    pass
    # return render_template('welcome.html',form=form)


@app.route('/', methods=['GET', 'POST'])
def home():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # creating user if doesn't exist
        user = get_or_create_user(username, password)

        # loggin in user or flashing login error
        if login(username, password):
            flash('Thanks {}, you are logged in!'.format(username))
            return redirect(url_for('all_names'))
        else:
            flash('Sorry, could not log you in. Wrong password?')
            return redirect(url_for('home'))
    # else:
    #     flash('Something went wrong')
    #     for fieldName, errorMessages in form.errors.items():
    #         print(errorMessages)
    #         print(fieldName)
    #         for err in errorMessages:
    #             pass
    #             # print(err + fieldName)


    return render_template('home.html',form=form)

@app.route('/names')
def all_names():
    users = User.query.all()
    return render_template('names.html', users=users)

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
        # print(search_results, search_term)

        return render_template('search_results.html', search_term = search_term, search_results=search_results, form_select=form_select)
        # ,search_term=search_term, num=session['results_num'] 


@app.route('/food_stats/<ndbno>', methods=['GET','POST'])
def food_stats(ndbno):
    food_data = fetch_nutrition(ndbno)
    health_idx = get_nutri_index(food_data)
    if health_idx < 0:
        bgcolor = "background-color: #e01717;"
    else: bgcolor = "background-color: #2cbb80;"
    # print(food_data)
    return render_template('food_stats.html', health_idx = health_idx, name = food_data['name'], bgcolor=bgcolor, back_link=redirect_url())





@app.route('/add_favorite/<ndbno>', methods=['GET','POST'])
def add_favorite(ndbno):
    user = get_or_create_user(name = session['name'])
    food = get_or_create_food(ndbno = ndbno, user_id=user.id)
    user.foods.append(food)
    return redirect (redirect_url())


@app.route('/favorites/', methods=['GET','POST'])
def favorites():
    form_select = SelectFoodForm()
    name = session.get('name')

    # if user is logged in:
    if name:
        user = get_or_create_user(name = name)
        foods = user.foods
        return render_template('favorites.html',foods=foods, form_select = form_select)
    else:
        return render_template('names.html', names = None)


# Handilng Error routes
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', e = e)
