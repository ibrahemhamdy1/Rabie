# import flask modules
from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash
# importing sqlalchemy modules to connect to database
from sqlalchemy import create_engine, asc, desc, and_, or_
from sqlalchemy.orm import sessionmaker
# from database_setup modeule imort required metadata objects and base class
from database_setup import Base, Category, Item, User
# to store user info in the session
from flask import session as login_session
# to Create anti-forgery state token
import random
import string

# to deal with google api and read json response
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

# create an instance of flask with the name of the running application
app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog Web Application"

# Connect to Database and create database session
engine = create_engine('sqlite:///itemscatalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create anti-forgery state token


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)

# connect to the site using third authintication
# part which is Google Plus using google api


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code

    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)

    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps(
            "Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps(
            "Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

# get and verify Aceess token and google plus id
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info and stored it in the session for later use
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # check if the user exist in the database or not , if not create a new one
    userid = getUserID(login_session['email'])
    if userid:
        login_session['user_id'] = userid
    else:
        userid = createUser(login_session)
        login_session['user_id'] = userid

    output = ''
    output += '<h3>Welcome, '
    output += login_session['username']
    output += '!</h3>'
    output += '<img id ="userimg" src="'
    output += login_session['picture']
    output += ' ">'
    flash("you are now logged in as %s" % login_session['username'])
    return output

#  dissconnect current user by Revoke it's token and reset his login_session


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps(
            'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # get user name for flash
    name = login_session['username']

    url = 'https://accounts.google.com/o/oauth2/revoke?',
    'token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        flash(" Good Bye %s ...  you are seccessfully logged out " % name)

        return redirect(url_for("showCategories"))

    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

# to return json object contain all categories


@app.route('/catalog.json')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(category=[r.serialize for r in categories])


# Show all Categories
@app.route('/')
@app.route('/categories/')
def showCategories():
    # return "all categories and the latest added items are showing here "
    categories = session.query(Category).order_by(asc(Category.name)).all()
    latestItems = session.query(Item).order_by(desc(Item.id)).limit(10)

    if 'username' not in login_session:
        return render_template(
            "publiccategories.html",
            categories=categories, items=latestItems,
            categoryItems="", category=""
        )
    else:
        # get all categories and the latest added items  for this user
        user_id = getUserID(login_session['email'])
        categories = session.query(Category).filter_by(user_id=user_id).all()
        if categories:
            latestItems = session.query(Item).filter_by(user_id=user_id).all()
            if latestItems is None:
                latestItems = ""
            return render_template(
                "categories.html",
                categories=categories, items=latestItems,
                categoryItems="", category=""
            )
        else:
            return render_template(
                "categories.html",
                categories="", items="", categoryItems="", category=""
            )

# Create a new category


@app.route('/category/new/', methods=['GET', 'POST'])
def newCategory():
    # "new category is processed here either for Get Or POST Requests"
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCategory = Category(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('newcategory.html')

# Edit a category


@app.route('/category/<string:category_name>/edit/', methods=['GET', 'POST'])
def editCategory(category_name):
    # " category edited here "
    if 'username' not in login_session:
        return redirect('/login')
    user_id = getUserID(login_session['email'])
    editedCategory = session.query(Category).filter_by(
        name=category_name).filter_by(user_id=user_id).one()

    if login_session['user_id'] != editedCategory.user_id:
        return render_template('publiccategories.html')

    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            flash('Category Successfully Edited %s' % editedCategory.name)
            return redirect(url_for('showCategories'))
    else:
        return render_template('editcategory.html', category=editedCategory)


# Delete a category
@app.route('/category/<string:category_name>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_name):
    # " category deleted here "
    if 'username' not in login_session:
        return redirect('/login')
    user_id = getUserID(login_session['email'])
    categoryToDelete = session.query(Category).filter_by(
        name=category_name).filter_by(user_id=user_id).one()
    if categoryToDelete.user_id != login_session['user_id']:
        return """<script> function myfunction(){alert('you are
         not authorized to delete this Category .
          please create your own Category in order to delete
           ');} </script> <body onload=myfunction()"""
    if request.method == 'POST':
        items = session.query(Item).filter_by(
            category_id=categoryToDelete.id).all()
        for item in items:
            session.delete(item)
            session.commit()
        session.delete(categoryToDelete)
        flash('%s Successfully Deleted and all of its Items' %
              categoryToDelete.name)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template(
            'deletecategory.html', category=categoryToDelete
        )

# Show a category items


@app.route('/category/<string:category_name>/')
@app.route('/category/<string:category_name>/items/')
def showItems(category_name):
    # return " category items show here "

    categories = session.query(Category).order_by(asc(Category.name)).all()
    category = session.query(Category).filter_by(name=category_name).one()
    cretr = getUserInfo(category.user_id)
    items = session.query(Item).filter_by(category_id=category.id).all()
    if 'username' not in login_session or cretr.id != login_session['user_id']:
        return render_template(
            "publiccategories.html",
            categories=categories, items="",
            categoryItems=items, category=category
        )
    else:
        user_id = getUserID(login_session['email'])
        categories = session.query(Category).filter_by(
            user_id=user_id).order_by(asc(Category.name)).all()
        items = session.query(Item).filter_by(
            category_id=category.id).order_by(asc(Item.name)).all()
        return render_template(
            "categories.html",
            categories=categories, items="",
            categoryItems=items, category=category
        )

# Show details of an  item


@app.route('/category/<string:category_name>/<string:item_name>')
def showItemDetails(category_name, item_name):
    # return " category items show here "
    category = session.query(Category).filter_by(name=category_name).one()
    cretr = getUserInfo(category.user_id)
    item = session.query(Item).filter_by(
        name=item_name).filter_by(category_id=category.id).one()
    if 'username' not in login_session or cretr.id != login_session['user_id']:
        return render_template(
            "publicitem.html",
            item=item, category=category
        )
    else:
        return render_template(
            "itemdetails.html",
            item=item, category=category
        )


# Create a new category item
@app.route('/category/<string:category_name>/items/new/',
           methods=['GET', 'POST']
           )
def newCategoryItem(category_name):
    # " new category item is created  here "
    user_id = getUserID(login_session['email'])
    category = session.query(Category).filter_by(
        name=category_name).filter_by(user_id=user_id).one()
    cretr = getUserInfo(category.user_id)
    if 'username' not in login_session or cretr.id != login_session['user_id']:
        return redirect('/login')
    if request.method == 'POST':
        if request.form['name'] == "":
            return redirect(url_for('showCategories'))
        newItem = Item(
            name=request.form['name'], description=request.form['description'],
            category_id=category.id, user_id=user_id)
        session.add(newItem)
        session.commit()
        flash('New Menu %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showCategories'))
    else:
        return render_template(
            'newcategoryitem.html',
            category_name=category.name
        )

# Edit a category item


@app.route('/category/<string:category_name>/item/<string:item_name>/edit',
           methods=['GET', 'POST']
           )
def editCategoryItem(category_name, item_name):
    # category item is edited  here
    user_id = getUserID(login_session['email'])
    category = session.query(Category).filter_by(
        name=category_name).filter_by(user_id=user_id).one()
    cretr = getUserInfo(category.user_id)
    if 'username' not in login_session or cretr.id != login_session['user_id']:
        return redirect('/login')
    itemToEdit = session.query(Item).filter_by(
        name=item_name).filter_by(user_id=user_id).one()
    if itemToEdit.user_id != login_session['user_id']:
        return "<script> function myfunction(){alert('you are not authorized"
        + "to Edit this Item . please create your own Items in order to Edit"
        + "');} </script> <body onload=myfunction()"

    if request.method == 'POST':
        if request.form['name']:
            itemToEdit.name = request.form['name']
        if request.form['description']:
            itemToEdit.description = request.form['description']
        itemToEdit.user_id = user_id
        itemToEdit.category_id = category.id
        session.add(itemToEdit)
        session.commit()
        flash('Category Item Successfully Edited')
        return redirect(url_for('showCategories'))
    else:
        return render_template(
            'edititem.html', item=itemToEdit,
            category=category
        )


# Delete a menu item
@app.route('/category/<string:category_name>/item/<string:item_name>/delete',
           methods=['GET', 'POST']
           )
def deleteCategoryItem(category_name, item_name):
    # category item is deleted   here
    user_id = getUserID(login_session['email'])
    category = session.query(Category).filter_by(
        name=category_name).filter_by(user_id=user_id).one()
    cretr = getUserInfo(category.user_id)
    if 'username' not in login_session or cretr.id != login_session['user_id']:
        return redirect('/login')
    itemToDelete = session.query(Item).filter_by(
        name=item_name).filter_by(user_id=user_id).one()
    if itemToDelete.user_id != login_session['user_id']:
        return "<script> function myfunction(){alert('you are not"
        +" authorized to delete this Item . please create your own"
        +" Items in order to delete"
        +" ');} </script> <body onload=myfunction()"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Category Item Successfully Deleted')
        return redirect(url_for('showCategories'))
    else:
        return render_template(
            'deleteitem.html',
            item=itemToDelete, category=category
        )

# create new user and store it in the database


def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture']
                   )
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

# read user information based on user id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

# return user id based on user email


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
