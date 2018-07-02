from functools import wraps
from flask import Flask, render_template, request, redirect, jsonify, url_for
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup2 import Base, Category, Category_item, User, create_db
import random
import string
from sqlalchemy.pool import StaticPool
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
CLIENT_ID = json.loads(open(
    'g_client_secret.json', 'r').read())['web']['client_id']
app = Flask(__name__)
app.secret_key = "super secret key"

try:
    engine = create_engine('sqlite:///sportinggood_users.db', connect_args={
        'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session_db = DBSession()
except e:
    print("Database Exception ",e)


# Google based Login page
@app.route('/login')
def showLogin():
    """
    Shows the Login screen,
    generates 32 bit key.
    """
    state = ''.join(random.choice(
        string.ascii_uppercase + string.digits)for x in range(32))
    # print(state)
    login_session['state'] = state
    # print("login_session['state']: "+login_session['state'])
    return render_template('login.html', STATE=state)


# Google based ajax response function to verify and add the newly verified user
# this fuction return back the successful/fail response to the ajax call
@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    Saving data from GOOGLE API about the logged user
    (email, id, name, pic). It also sets the login_session variables.
    """
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    # print("got the authorization token")
    code = request.data
    # print("code from google: "+code)
    try:
        # print("creating google oauth object")
        oauth_flow = flow_from_clientsecrets('g_client_secret.json', scope='')
        # print("google oauth ok")
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        # print("Failed to upgrade the authorization code.")
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        return response

    access_token = credentials.access_token
    url = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
        % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # print("verifying the google result ")
    if result.get('error') is not None:
        response = make_response(json_dumps(result.get('error')), 50)
        response.headers['Content-Type'] = 'application/json'
    # Verify that access token is used
    gplus_id = credentials.id_token['sub']
    # print("gplus_id: "+gplus_id)
    # print("user_id: "+result['user_id'])

    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID. "), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # check for loggged in user
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected'), 200)
        response.headers['Content-Type'] = 'application/json'

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    # print("login credentials stored in the session")

    # if the user is successful, then get the user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    # get the user information and store it in 'login_session'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    user_id = getUserID(data['email'])
    if(user_id < 0):
        user_id = createUser(login_session)

    login_session['user_id'] = user_id
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius:150px;"'
    output += '"-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    # flash("you are now logged in as %s" % login_session['username'])
    return output


# Show all categories of the sportinggood website, it also points to the main
# Home page as well
@app.route('/')
@app.route('/catalog/')
def showCategories():
    categories = session_db.query(Category).all()
    # return "This page will show all the categories of the database"
    return render_template(
        'categories.html', categories=categories, session=login_session)
    # return "hello world"


# Show the items in the category
# @app.route('/catalog/<category>/')
@app.route('/catalog/<category>/items/')
def showItems(category):
    category = session_db.query(Category).filter_by(name=category).one()
    items = session_db.query(Category_item).filter_by(
        cat_id=category.id).all()
    if('username' not in login_session):
        return render_template(
            'items1.html', items=items, category=category,
            session=login_session)
    else:
        return render_template(
            'items1.html', items=items, category=category,
            session=login_session)


# Show the items in the category
@app.route('/catalog/<category>/<item_name>/')
def showItem(category, item_name):
    category = session_db.query(Category).filter_by(name=category).one()
    item = session_db.query(Category_item).filter_by(
        cat_id=category.id, name=item_name).one()
    creator = getUserInfo(item.user_id)
    if(('username' not in login_session) or
            (item.user_id != login_session['user_id'])):
        return render_template(
            'item_user.html', item=item, category=category.name,
            session=login_session, is_editable=False)
    else:
        return render_template(
            'item_user.html', item=item, category=category,
            session=login_session, is_editable=True)


# Create a new Category item
@app.route(
    '/catalog/<category>/item/new/', methods=['GET', 'POST'])
def newCatItem(category):
    category_list = session_db.query(Category).all()
    print("running the new item function after sign-in veification")
    if('username' not in login_session):
        return redirect(url_for('showLogin'))
    else:
        if request.method == 'POST':
            cat_selection = request.form['category']
            category = session_db.query(Category).filter_by(
                name=cat_selection).one_or_none()
            newItem = Category_item(
                name=request.form['name'],
                description=request.form['description'],
                cat_id=category.id, user_id=login_session['user_id'])
            session_db.add(newItem)
            session_db.commit()
            return redirect(
                url_for(
                    'showItems', category=category.name,
                    session=login_session))

        return render_template(
            'newcatitem.html', category=category, cat_list=category_list,
            session=login_session)


# Edit a Category item
@app.route('/catalog/<category>/items/<item_name>/edit',
           methods=['GET', 'POST'])
# @login_required
def editCatItem(category, item_name):

    if('username' not in login_session):
        return redirect(url_for('showLogin'))
    else:
        category = session_db.query(Category).filter_by(
            name=category).one_or_none()
        category_list = session_db.query(Category).all()
        editedItem = session_db.query(Category_item).filter_by(
            name=item_name, cat_id=category.id).one_or_none()
        if request.method == 'POST':
            cat_selection = request.form['category']
            category = session_db.query(Category).filter_by(
                name=cat_selection).one_or_none()
            if(editedItem.user_id == login_session['user_id']):
                if request.form['name']:
                    editedItem.name = request.form['name']
                if request.form['description']:
                    editedItem.description = request.form['description']
                editedItem.cat_id = category.id
                session_db.add(editedItem)
                session_db.commit()
                return redirect(url_for(
                    'showItems', category=category.name,
                    session=login_session))
            else:
                return render_template(
                    'editcatitem.html', item=editedItem,
                    cat_list=category_list, session=login_session)
        return render_template(
            'editcatitem.html', item=editedItem, cat_list=category_list,
            session=login_session)


# Delete a Category item
@app.route(
    '/catalog/<category>/items/<item_name>/delete', methods=['GET', 'POST'])
# @login_required
def deleteCatItem(category, item_name):
    if('username' not in login_session):
        return redirect(url_for('showLogin'))
    else:
        category = session_db.query(Category).filter_by(
            name=category).one_or_none()
        itemToDelete = session_db.query(Category_item).filter_by(
            name=item_name, cat_id=category.id).one_or_none()

        if request.method == 'POST':
            if(itemToDelete.user_id == login_session['user_id']):
                session_db.delete(itemToDelete)
                session_db.commit()
                return redirect(url_for(
                    'showItems', category=category.name,
                    session=login_session))
            else:
                return render_template(
                    'deletecatitem.html', item=itemToDelete,
                    session=login_session)
        else:
            # return "Item to be deleted"
            return render_template(
                'deletecatitem.html', item=itemToDelete, session=login_session)


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Json response of the catelog
@app.route('/catalog.json', methods=['GET'])
def catalog_json():
    return all_Catalog()
    # return "hello world"


# User Helper Functions to get User-info
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session_db.add(newUser)
    session_db.commit()
    user = session_db.query(User).filter_by(
        email=login_session['email']).one_or_none()
    return user.id


# Json response function for list down all the categories
def all_Catalog():
    category_list = session_db.query(Category).all()
    return jsonify(category_list=[i.serialize for i in category_list])


# getting the user_id to map on category_item table
def getUserInfo(user_id):
    user = session_db.query(User).filter_by(id=user_id).one_or_none()
    # print("user-object: ",user)
    return user


# function returns user_id against a valid email address else return -1
def getUserID(email):
    try:
        user = session_db.query(User).filter_by(email=email).one_or_none()
        return user.id
    except:
        return -1


if __name__ == '__main__':
    create_db.new_db()
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
