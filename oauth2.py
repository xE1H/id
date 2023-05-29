from flask import render_template, session, redirect, url_for, request

from app import app
from keygen import our_public_key
from utils import log, issue_jwt, is_valid_application
from config import authorised_clients


@app.route('/v2.0/keys')
def get_keys():
    return our_public_key


@app.route('/v2.0/authorize')
def authorize():
    try:
        client_id = request.args['client_id']
        redirect_uri = request.args['redirect_uri']
        if not is_valid_application(client_id, redirect_uri):
            log("Client not authorised or redirect URI does not match")
            return "Bad request", 400
    except KeyError as e:
        log("Missing parameters" + str(e))
        return "Bad request", 400

    session['our_redirect_uri'] = redirect_uri
    session['our_client_id'] = client_id

    return redirect(url_for('login'))


@app.route('/v2.0/login')
def login():
    if 'our_redirect_uri' not in session:
        log("Redirect URI not found")
        return "Bad request", 400

    if 'name' in session:
        return redirect(url_for('authorize_confirm'))

    return render_template('login.html', appId=authorised_clients[session['our_client_id']]['name'])


@app.route('/v2.0/confirm', methods=['GET', 'POST'])
def authorize_confirm():
    if 'our_redirect_uri' not in session:
        log("Redirect URI not found")
        return "Bad request", 400
    if request.method == 'GET':
        if 'name' not in session:
            return redirect(url_for('login'))

        return render_template('authorize_confirm.html', name=session['name'],
                               appId=authorised_clients[session['our_client_id']]['name'])
    else:
        if 'name' not in session:
            return redirect(url_for('login'))

        return issue_jwt(session['name'], session['our_client_id'])


@app.route('/v2.0/logout', methods=['GET', 'POST'])
def logout():
    session.pop("name")

    redirect_link = request.args.get('redirect')
    return redirect("/") if not redirect_link else redirect(redirect_link)
