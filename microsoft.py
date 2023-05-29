import jwt
from flask import session, redirect, request

from app import app
from config import URL, ms_client_id
from utils import get_random_string, log, issue_jwt

# Microsoft OpenID Connect

ms_jwks_url = 'https://login.microsoftonline.com/common/discovery/v2.0/keys'
ms_jwks_client = jwt.PyJWKClient(ms_jwks_url)


@app.route('/microsoft/login')
def microsoft_login():
    nonce = get_random_string(32)
    session['nonce'] = nonce
    return redirect("https://login.microsoftonline.com/1e950737-93b0-4876-a969-e74b03acddac/oauth2/v2.0/authorize" +
                    "?client_id=" + ms_client_id +
                    "&response_type=id_token" +
                    "&redirect_uri=" + URL + "/microsoft/callback" +
                    "&response_mode=form_post" +
                    "&scope=openid%20profile" +
                    "&domain_hint=licejus.lt" +
                    "&prompt=select_account" +
                    f"&nonce={nonce}")


@app.route('/microsoft/callback', methods=['POST'])
def microsoft_callback():
    try:
        session['our_redirect_uri']
    except:
        return "Bad request", 400

    try:
        if request.form['error'] is not None:
            log(f"Error in Microsoft callback: {request.form['error']}, {request.form['error_description']}")
            return redirect(session['our_redirect_uri'] + "?error=true")
    except:
        pass

    try:
        id_token = request.form['id_token']
        pk = ms_jwks_client.get_signing_key_from_jwt(id_token)
        user_data = jwt.decode(id_token, pk.key, algorithms=['RS256'],
                               audience=ms_client_id)

        if user_data['nonce'] != session['nonce']:
            log("Nonce mismatch in Microsoft callback: expected " + session['nonce'] + ", but got " + user_data[
                'nonce'])
            return redirect(session['our_redirect_uri'] + "?error=true")

        name = user_data['name']
        session['name'] = name

        return issue_jwt(name, session['our_client_id'])

    except Exception as e:
        log("Error decoding JWT in Microsoft callback: " + str(e))
        return redirect(session['our_redirect_uri'] + "?error=true")
