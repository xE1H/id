from __main__ import app
from flask import session, request, redirect, url_for, render_template
from config import URL
from database import DB
from log import log
from bleach import clean as c

db = DB()


@app.route('/dashboard')
def dashboard():
    if 'name' not in session:
        return redirect(URL + "/v2.0/authorize?client_id=dashboard&redirect_uri=" + URL + "/dashboard")

    return render_template('dashboard.html')


@app.route('/registerApp', methods=['GET', 'POST'])
def add_application():
    if request.method == 'GET':
        # Make sure the user is logged in
        if 'name' not in session:
            return redirect(url_for('dashboard'))

        return render_template('registerApp.html')
    else:
        if 'name' not in session:
            return "Unauthorized (WHAT ARE YOU DOING IN MY SWAMP?)", 401
        try:
            db.register_app(c(session['name']), c(request.form['name']), c(request.form['kilmininkas']),
                            c(request.form['email']),
                            c(request.form['redirect_uris']), c(request.form['client_id']))

        except Exception as ex:
            log("Register app failed with error: " + str(ex) + ", " + str(request.form))
            return "Error (gal jau yra toks ID?) " + str(ex), 400
        log("Registered new app: " + request.form['name'] + " (" + request.form['client_id'] + ")" + " by " +
            session['name'])
        return "Success <br><a href='/dashboard'>Aplikacijų valdymas</a>", 200


@app.route('/editApp/<client_id>', methods=['GET', 'POST'])
def edit_application(client_id):
    if request.method == 'GET':
        # Make sure the user is logged in
        if 'name' not in session:
            return redirect(url_for('dashboard'))

        app = db.get_app(client_id)
        print(app)

        return render_template('editApp.html', app=app)
    else:
        if 'name' not in session:
            return "Unauthorized (WHAT ARE YOU DOING IN MY SWAMP?)", 401
        try:
            db.edit_app(session['name'], request.form['name'], request.form['kilmininkas'], request.form['email'],
                        request.form['redirect_uris'], client_id)
        except Exception as ex:
            log("Edit app failed with error: " + str(ex) + ", " + str(request.form))
            return "Error (kazkas blogai!!!)", 400

        log("Edited app: " + request.form['name'] + " (" + client_id + ")" + " by " + session['name'])
        return "Success<br><a href='/dashboard'>Aplikacijų valdymas</a>", 200


@app.route('/deleteApp/<client_id>', methods=['GET'])
def delete_application(client_id):
    # Make sure the user is logged in
    if 'name' not in session:
        return redirect(url_for('dashboard'))

    db.delete_app(client_id)

    log("Deleted app: " + client_id + " by " + session['name'])
    return "Success<br><a href='/dashboard'>Aplikacijų valdymas</a>", 200


@app.route('/allApps')
def all_apps():
    if 'name' not in session:
        return redirect(url_for('dashboard'))

    apps = db.get_apps()
    print(apps)

    return render_template('allApps.html', apps=apps)


@app.route('/yourApps')
def your_apps():
    if 'name' not in session:
        return redirect(url_for('dashboard'))

    apps = db.get_apps()
    # Sort to only show the user's apps
    apps = [app for app in apps if app['owner'] == session['name']]

    return render_template('yourApps.html', apps=apps)
