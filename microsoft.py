import jwt
from flask import session, redirect, request

from app import app
from config import URL, ms_client_id, ms_client_secret
from config import ms_tenant as TENANT
from utils import get_random_string, log, issue_jwt
from requests import get, post

# Microsoft OpenID Connect

ms_jwks_url = 'https://login.microsoftonline.com/common/discovery/v2.0/keys'
ms_jwks_client = jwt.PyJWKClient(ms_jwks_url)


@app.route('/microsoft/login')
def microsoft_login():
    return redirect(f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/authorize" +
                    "?client_id=" + ms_client_id +
                    "&response_type=code" +
                    "&redirect_uri=" + URL + "/microsoft/callback" +
                    "&response_mode=form_post" +
                    "&scope=offline_access%20user.read" +
                    "&domain_hint=licejus.lt" +
                    "&prompt=select_account")


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
        code = request.form['code']
        access_token = post(f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/token", data={
            "client_id": ms_client_id,
            "scope": "user.read",
            "code": code,
            "redirect_uri": URL + "/microsoft/callback",
            "grant_type": "authorization_code",
            "client_secret": ms_client_secret}).json()['access_token']

        raw_data = get("https://graph.microsoft.com/v1.0/me", headers={
            "Authorization": "Bearer " + access_token
        }).json()

        raw_title = raw_data['jobTitle']
        grade = ""
        roles = []

        if "mokinys" in raw_title or "mokinė" in raw_title:
            grade = raw_title.split(" ")[0]
            grade = grade[:-1].upper() + grade[-1]
            roles += ["student"]
        if "mokytojas" in raw_title or "mokytoja" in raw_title:
            roles += ["teacher"]

        user_data = {
            "name": raw_data['displayName'],
            "full_name": raw_data['displayName'],
            "first_name": raw_data['givenName'],
            "last_name": raw_data['surname'],
            "raw_title": raw_title,
            "grade": grade,
            "roles": roles,
            # Other data that can not be gathered from Microsoft
            "dependants": []
        }

        session["user_data"] = user_data

        return issue_jwt(user_data, session['our_client_id'])

    except Exception as e:
        log("Error in getting userdata in Microsoft callback: " + str(e))
        return redirect(session['our_redirect_uri'] + "?error=true")
