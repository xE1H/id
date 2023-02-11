from flask import Flask, render_template, session, redirect, url_for, request
import random
import jwt
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

issuer = 'http://localhost:5000'

authorised_clients = {
    'client': {
        "request_uri": 'http://localhost:5000/test/redirect',
        "name": "kirčiuoklės" # Kilmininko linksnis pls :D
    }
}
our_private_key = """-----BEGIN RSA PRIVATE KEY-----
MIICXgIBAAKBgQDbvpA1fFn7dvMAnZ9HsVJyLUA9HVDXNaWiEm/cmyMbKCNERu2g
9jn1YrcdXiPaP9Nv+dBsXyePe26LINsom/xi2DeOMPXXkYhy7/8aepQlPpxMhpnV
wuWMfMPWyg2rNdlok41MQY4rV7RUFu8dk9EapxL8eYNZK7SlVMGEGLrGBwIDAQAB
AoGBALjdAjjc2l5g3WHhOMR5euCvDOHdLcs/SI6mcBDpOol4JOMlwHevbWbwmxhL
wGG1XE1RnnPtQTzGHGNTSsxJHfMB5oV5gWT/SsD2AmBY7Yq+khXbfZQAU4D5oRvy
GK2YuaYNG6J4b2GUa4LDdv+IEWmFyFHQknW06Jz+nsB5vs4BAkEA/j90kOHId2+y
PKfy01aJRumInX6s1esX5wyEqMPVKq1fZY7GRK+fjjGky/gpf/H9HEyx8RyYlogM
nZUZD/N7hwJBAN1CPKKZqTnpzJfMxC4NhCNSf/Hkyjtno77a0M92ZNzrbSK7MG5l
pT4F0DyXHyvRJCOjyzYTWWdacbwIENeCAYECQQC19UYAVoZ47Ah8npoLpDgU9xfd
14XshxcRNYVPnu/VXkUS0s6U47fmNSNDEvToa5CBC2aiL5wIx493y/gm0VPLAkAE
Np6w+fwe/jTHLz8NIXTCt294S8MOHosft0sCqF6DVnhdkPL7JzReWf39KWOOkgz+
IMBd50Bsl2xTCFRJxlABAkEA73PBjffQB2ZLvZBZEImkk3xq2Ck18zMMW9lSSbQN
LkP206RffSBtaa5VFvD7/dGtsSTYs8O9BJsr9mHBAJVCIw==
-----END RSA PRIVATE KEY-----"""

our_public_key = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDbvpA1fFn7dvMAnZ9HsVJyLUA9
HVDXNaWiEm/cmyMbKCNERu2g9jn1YrcdXiPaP9Nv+dBsXyePe26LINsom/xi2DeO
MPXXkYhy7/8aepQlPpxMhpnVwuWMfMPWyg2rNdlok41MQY4rV7RUFu8dk9EapxL8
eYNZK7SlVMGEGLrGBwIDAQAB
-----END PUBLIC KEY-----"""


## Utility functions

def get_random_string(length):
    return ''.join(random.choice('0123456789abcdef') for _ in range(length))


def log(message):
    route = request.path
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'
    print(BLUE + BOLD + " * " + route + ENDC + GREEN + ' | ' + ENDC + message)

def issue_jwt(name, intended_aud):
    try:
        uri = session['our_redirect_uri']
        aud = session['our_client_id']
        if uri is not None and aud == intended_aud:
            token = jwt.encode({'name': name, 'iss': issuer, 'aud': aud,
                                'exp': datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(
                                    minutes=10)}, our_private_key, algorithm='RS256',
                               headers={'kid': '87c0615c19dd98fdc301615d522601f5'})
            uri += f"?id_token={token}"

            session.pop('our_redirect_uri')
            session.pop('our_client_id')

            return redirect(uri)
    except Exception as e:
        log("Redirect URI not found or JWT encode failed with error: " + str(e))
        return redirect(session['our_redirect_uri'] + "?error=true")


## App

app = Flask(__name__)

app.secret_key = "sdaasddsfrjg438566574546g7k80g4k567f450l6dff6309745fl63f-45876f354l-36f450769lf3-4560f374506-f84"


# Make session permanent
@app.before_request
def before_request():
    session.permanent = True


@app.route('/')
def index():
    return "<a href='/v2.0/authorize?client_id=client&redirect_uri=http://localhost:5000/test/redirect'>Login</a>"


@app.route('/test/redirect')
def test_othersite_redirect():
    id_token = request.args['id_token']

    decoded = jwt.decode(id_token, our_public_key, algorithms=['RS256'], audience='client')
    return f"You are logged in as {decoded['name']}"


# semi oauth2 flow

@app.route('/v2.0/keys')
def get_keys():
    return our_public_key


@app.route('/v2.0/authorize')
def authorize():
    try:
        client_id = request.args['client_id']
        redirect_uri = request.args['redirect_uri']
        if client_id not in authorised_clients or authorised_clients[client_id]['request_uri'] != redirect_uri:
            log("Client not authorised or redirect URI does not match")
            return "Bad request", 400
    except KeyError:
        log("Missing parameters")
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

        return render_template('authorize_confirm.html', name=session['name'], appId=authorised_clients[session['our_client_id']]['name'])
    else:
        if 'name' not in session:
            return redirect(url_for('login'))

        return issue_jwt(session['name'], session['our_client_id'])


@app.route('/v2.0/logout', methods=['POST'])
def logout():
    session.pop("name")
    return redirect(url_for('login'))

# Microsoft OpenID Connect

ms_jwks_url = 'https://login.microsoftonline.com/common/discovery/v2.0/keys'
ms_jwks_client = jwt.PyJWKClient(ms_jwks_url)


@app.route('/microsoft/login')
def microsoft_login():
    nonce = get_random_string(32)
    session['nonce'] = nonce
    return redirect("https://login.microsoftonline.com/1e950737-93b0-4876-a969-e74b03acddac/oauth2/v2.0/authorize" +
                    "?client_id=f4ecaa21-8521-402c-8cb9-dd8b51399d77" +
                    "&response_type=id_token" +
                    "&redirect_uri=http://localhost:5000/microsoft/callback" +
                    "&response_mode=form_post" +
                    "&scope=openid%20profile" +
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
                               audience='f4ecaa21-8521-402c-8cb9-dd8b51399d77')

        if user_data['nonce'] != session['nonce']:
            log("Nonce mismatch in Microsoft callback: expected " + session['nonce'] + ", but got " + user_data['nonce'])
            return redirect(session['our_redirect_uri'] + "?error=true")

        name = user_data['name']
        session['name'] = name

        return issue_jwt(name, session['our_client_id'])

    except Exception as e:
        log("Error decoding JWT in Microsoft callback: " + str(e))
        return redirect(session['our_redirect_uri'] + "?error=true")


# Tamo login

@app.route('/tamo/login', methods=['GET', 'POST'])
def tamo_login():
    try:
        session['our_redirect_uri']
    except:
        return "Bad request", 400
    if request.method == 'GET':
        return render_template('tamo_login.html', appId = authorised_clients[session['our_client_id']]['name'], error = request.args.get('error'))
    else:
        username = request.form['username']
        password = request.form['password']

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://dienynas.tamo.lt/Prisijungimas/Login")

        driver.find_element_by_id('UserName').send_keys(username)
        driver.find_element_by_id('Password').send_keys(password)

        driver.find_element_by_css_selector('.c_btn.submit').click()

        if driver.current_url != 'https://dienynas.tamo.lt/DashboardStudents':
            driver.close()
            return redirect("/tamo/login?error=1")

        name = driver.find_element_by_css_selector(
            'html > body.container > div#header_section.row > div.col-md-14 > div > div > div.header-box > div > div > div > div > div').text
        schoolName = driver.find_element_by_css_selector(
            'html > body.container > div#top_section.row > div.col-md-14 > div.row.top_section_back > div.col-md-10 > span').text

        if schoolName != 'Vilniaus licėjus':
            driver.close()
            return redirect("/tamo/login?error=2")

        driver.close()
        session['name'] = name

        return issue_jwt(name, session['our_client_id'])


if __name__ == '__main__':
    app.run()
