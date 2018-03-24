from flask import Flask, render_template, request, redirect
from flask import url_for, jsonify, make_response, flash
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from database_setup import Base, User, Category, Item
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import json
import httplib2
import requests
import random
import string


app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']


# Connect to database and create database session
engine = create_engine('sqlite:///catalogapp.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, CLIENT_ID=CLIENT_ID)


# OAuth2 login
@app.route('/oauth/<string:provider>', methods=['POST'])
def login(provider):
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps("Invalid state parameter."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code
    auth_code = request.data

    # Google+ login
    if provider == 'google':

        # Check for CSRF
        if not request.headers.get('X-Requested-With'):
            response = make_response(json.dumps("Possible CSRF attack."), 403)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Upgrade the authorization code into a credentials object
        try:
            oauth_flow = flow_from_clientsecrets('client_secrets.json',
                                                 scope='',
                                                 redirect_uri='postmessage')
            credentials = oauth_flow.step2_exchange(auth_code)
        except FlowExchangeError:
            response = make_response(
                json.dumps("Failed to upgrade the authorization code."), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Check that the access token is valid.
        access_token = credentials.access_token
        url = (
            'https://www.googleapis.com/oauth2/v2/tokeninfo?access_token=%s'
            % access_token)
        h = httplib2.Http()
        result = json.loads(h.request(url, 'GET')[1])

        # If there was an error in the access token info, abort.
        if result.get('error') is not None:
            response = make_response(json.dumps(result.get('error')), 500)
            response.headers['Content-Type'] = 'application/json'

        # Verify that the access token is used for the intended user.
        gplus_id = credentials.id_token['sub']
        if result['user_id'] != gplus_id:
            response = make_response(
                json.dumps("Token's user ID doesn't match given user ID."),
                401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Verify that the access token is valid for this app.
        if result['issued_to'] != CLIENT_ID:
            response = make_response(
                json.dumps("Token's client ID does not match app's."), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Check if user is already logged in
        stored_credentials = login_session.get('credentials')
        stored_gplus_id = login_session.get('gplus_id')
        if stored_credentials is not None and gplus_id == stored_gplus_id:
            response = make_response(
                json.dumps("Current user is already connected."), 200)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Request to API
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        params = {'access_token': access_token, 'alt': 'json'}
        answer = requests.get(userinfo_url, params=params)

        data = answer.json()

        name = data['name']
        picture = data['picture']
        email = data['email']

        # Check if user exists
        user = session.query(User).filter_by(email=email).one_or_none()
        if user is None:
            # Create new user
            user = User(name=name, picture=picture, email=email)
            session.add(user)
            session.commit()

        # Store user information in session
        login_session['access_token'] = access_token
        login_session['gplus_id'] = gplus_id
        login_session['name'] = name
        login_session['picture'] = picture
        login_session['email'] = email
        login_session['user_id'] = getUserID(email)
        login_session['provider'] = 'google'

        return 'Login successful!'

    else:
        return 'Unrecognized Provider'


# Logout
@app.route("/logout")
def logout():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps("Current user not connected."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    if 'provider' in login_session:
        # Google+ logout specifics
        if login_session['provider'] == 'google':

            url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
                % access_token
            h = httplib2.Http()
            result = h.request(url, 'GET')[0]

            if result['status'] == '200':
                del login_session['gplus_id']
            else:
                response = make_response(
                    json.dumps("Failed to revoke token for given user."), 400)
                response.headers['Content-Type'] = 'application/json'
                return response

        del login_session['access_token']
        del login_session['name']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']

        flash("Log out successful")
        return redirect(url_for('showCatalog'))

    else:
        response = make_response(
            json.dumps("You were not logged in"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response


# User helper function
def getUserID(email):
    user = session.query(User).filter_by(email=email).one_or_none()
    if user is not None:
        return user.id
    else:
        return None


# JSON helper function
def toJSON(category):
    items = session.query(Item).filter_by(category_id=category.id).all()

    return {'id': category.id,
            'name': category.name,
            'Item': [item.serialize for item in items]}


# Catalog JSON API endpoint
@app.route('/catalog.json')
def catalogJSON():
    categories = session.query(Category).all()

    return jsonify(Category=[toJSON(category) for category in categories])


# Categories JSON API endpoint
@app.route('/catalog/categories.json')
def categoriesJSON():
    categories = session.query(Category).all()

    return jsonify(Category=[category.serialize for category in categories])


# Items JSON API endpoint
@app.route('/catalog/items.json')
def itemsJSON():
    items = session.query(Item).all()

    return jsonify(Item=[item.serialize for item in items])


# Category items JSON API endpoint
@app.route('/catalog/<string:category_name>.json')
@app.route('/catalog/<string:category_name>/items.json')
def categoryItemsJSON(category_name):
    category = session.query(Category).filter_by(
        name=category_name).one_or_none()

    # Check if category is in database
    if category is None:
        response = make_response(json.dumps("Category does not exist."), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

    items = session.query(Item).filter_by(category_id=category.id).all()

    return jsonify(Item=[item.serialize for item in items])


# Home page
# Displays all current categories with the latest added items
@app.route('/')
@app.route('/catalog/')
def showCatalog():
    categories = session.query(Category).all()
    recent_items = session.query(Item).order_by(Item.id.desc()).limit(10).all()

    return render_template('index.html',
                           categories=categories,
                           recent_items=recent_items)


# Category page
# Shows all the items available for selected category
@app.route('/catalog/<string:category_name>')
@app.route('/catalog/<string:category_name>/items')
def showCategoryItems(category_name):
    category = session.query(Category).filter_by(
        name=category_name).one_or_none()
    # Check if category is in database
    if category is None:
        response = make_response(json.dumps("Category does not exist."), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

    items = session.query(Item).filter_by(category_id=category.id).all()
    categories = session.query(Category).all()

    return render_template('categoryitems.html',
                           categories=categories,
                           category=category,
                           items=items)


# Item page
# Shows specific information about selected item
@app.route('/catalog/<string:category_name>/<string:item_name>')
def showItem(category_name, item_name):
    category = session.query(Category).filter_by(
        name=category_name).one_or_none()
    # Check if category exists in database
    if category is None:
        response = make_response(json.dumps("Category does not exist."), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

    item = session.query(Item).filter_by(name=item_name).one_or_none()
    # Check if item exists in database
    if item is None:
        response = make_response(json.dumps("Item does not exist."), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check if item is in category
    if category.id != item.category_id:
        response = make_response(
            json.dumps("Item does not exist in category."), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

    return render_template('item.html',
                           item=item,
                           category_name=category_name)


# New item
# Users allowed to create new items
@app.route('/catalog/new/', methods=['GET', 'POST'])
def createItem():
    # Check user authorization
    if 'name' not in login_session:
        flash("You must be logged in before creating a new item.")
        return redirect(url_for('showLogin'))

    categories = session.query(Category).all()

    if request.method == 'POST':
        newItem = Item(name=request.form['name'],
                       description=request.form['description'],
                       category_id=request.form['category'],
                       user_id=login_session['user_id'])

        # Check if item already exists (no duplicates allowed)
        try:
            session.add(newItem)
            session.commit()
        except (IntegrityError):
            session.rollback()
            response = make_response(
                json.dumps("Item already exists."), 400)
            response.headers['Content-Type'] = 'application/json'
            return response

        return redirect(url_for('showCatalog'))

    else:
        return render_template('newitem.html', categories=categories)


# Edit item
# Users allowed to edit items
@app.route('/catalog/<string:item_name>/edit', methods=['GET', 'POST'])
def editItem(item_name):
    # Check user authorization
    if 'name' not in login_session:
        flash("You must be logged in before editing an item.")
        return redirect(url_for('showLogin'))

    categories = session.query(Category).all()
    item = session.query(Item).filter_by(name=item_name).one_or_none()

    # Check if item exists in database
    if item is None:
        response = make_response(json.dumps("Item does not exist."), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

    category = session.query(Category).filter_by(
        id=item.category_id).one_or_none()

    # Check if user owns the item
    if item.user_id != login_session['user_id']:
        flash("You are not authorized to edit this item. "
              "Please create your own item in order to edit.")
        return redirect(url_for('showItem',
                                category_name=category.name,
                                item_name=item.name))

    if request.method == 'POST':
        if request.form['name']:
            item.name = request.form['name']
        if request.form['description']:
            item.description = request.form['description']
        if request.form['category']:
            item.category_id = request.form['category']

        # Check if item already exists (no duplicates allowed)
        try:
            session.add(item)
            session.commit()
        except (IntegrityError):
            session.rollback()
            response = make_response(
                json.dumps("Item already exists."), 400)
            response.headers['Content-Type'] = 'application/json'
            return response

        return redirect(url_for('showCatalog'))

    else:
        return render_template('edititem.html',
                               categories=categories,
                               item=item,
                               category=category)


# Delete item
# Users allowed to delete items
@app.route('/catalog/<string:item_name>/delete', methods=['GET', 'POST'])
def deleteItem(item_name):
    # Check user authorization
    if 'name' not in login_session:
        flash("You must be logged in before deleting an item.")
        return redirect(url_for('showLogin'))

    item = session.query(Item).filter_by(name=item_name).one_or_none()

    # Check if item is in database
    if item is None:
        response = make_response(json.dumps("Item does not exist."), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

    category = session.query(Category).filter_by(
        id=item.category_id).one_or_none()

    if category is None:
        # Should be impossible to have an item without a category
        response = make_response(
            json.dumps("Item exists without a category."), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check if user owns the item
    if item.user_id != login_session['user_id']:
        flash("You are not authorized to delete this item. "
              "Please create your own item in order to delete.")
        return redirect(url_for('showItem',
                                category_name=category.name,
                                item_name=item.name))

    if request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(url_for('showCatalog'))

    else:
        return render_template('deleteitem.html', category=category, item=item)


if __name__ == '__main__':
    app.secret_key = '\xd2\x81Z\xd5\x97d\xb0\xb3\xb7\xdc\xee\xb9B' \
                     '\xda\x00\x1a\xaf\xa2\x1c\x87\xac\xaa\x91/'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
