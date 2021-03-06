Midterm Project for the SI364 class (web app)

UPDATE: The app can be now run in browser, go to www.eatornot.us

# FOOD HEALTH ESTIMATOR
  This is the midterm project for class:
  SI364  class (Interractive App Building)

## Short Description
This software allows user to find out how healthy any food that is (as long as known to USDA).

## Long Description
I created a web application that lets user lookup foods and get an instant insight on how food might impact one's health. In order to simplify the rankings of the foods, I developed a measure that I called  health points. This index takes into account Macro and Micro nutrients of given food product while taking calories out of equation.

Health Points can be used to evaluate how healthy a food is relative to other foods. I used water as a baseline to be 0. Foods above 0 are likely good for human body, foods above 200 could be likely called superfood, and foods below 0 are unhealthy.


## Getting started

### Prerequisites
Python version used **3.6.4** (any version above 3 will be good)
Use requirements.txt to set up the virtual environment or intall missing modules manually (pip install for example).

### Running
* Activate the virtual environment with packages requred
* Start the postgresql `pg_ctl -D /usr/local/var/postgres start`
* Run the interractive.py file in the cmd or terminal
```
python3 SI364midterm.py runserver

or

gunicorn SI364midterm:app
```
* Open http://localhost:5000/ in your browser if it didn't open with the run of the app

### Using the app
* Enter your name on the home page if you'd like to save a list of favorites later
* Click on the Search button in the navigation bar
* Search for any foods you can think of
* If you do not see the desired food in the results, increase the number results returned
* Click on any food in results to view its "Health Score" or click on the star next to it to add to favorites
* Use favortes tab in the navigation bar to see your favorite foods at any time
* To change the user, navigate to 

### Pages
Here is the list of pages and the tamplates used to render them

* http://localhost:5000/          -> home.html
* http://localhost:5000/names     -> names.html
* http://localhost:5000/search    -> search.html
* http://localhost:5000/favorites -> favorites.html
* http://localhost:5000/food_stats/<ndbno>   -> food_stats.html
* http://localhost:5000/add_favorite/<ndbno> -> search_results.html



## Authors
* **Vanya Prokopovich** - [supervanya](https://github.com/supervanya)


