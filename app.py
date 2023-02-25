from flask import Flask, render_template, session, redirect, url_for, request
import random
import jwt
import datetime, os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from config import URL, authorised_clients, pkpass, ms_client_id, enableTest
from webdriver_manager.chrome import ChromeDriverManager
issuer = URL

##### ID sistema
##### Nojus Adomaitis, 2023
##### xE1H.xyz

## Utility functions

def get_random_string(length):
    return ''.join(random.choice('0123456789abcdef') for _ in range(length))

def log(message):
    try:
        route = request.path
    except:
        route = 'APP'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'
    print(BLUE + BOLD + " * " + route + ENDC + GREEN + ' | ' + ENDC + message)

## Generate public and private keys of they do not exist

try:
    raw_private_key = open('keys/private.pem', 'r').read()
    our_public_key = open('keys/public.pem', 'r').read()
    our_private_key = serialization.load_pem_private_key(raw_private_key.encode(), pkpass.encode())

    log("Loaded keys from file")
except:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    our_private_key = key.private_bytes(encoding=serialization.Encoding.PEM,
                                        format=serialization.PrivateFormat.PKCS8,
                                        encryption_algorithm=serialization.BestAvailableEncryption(pkpass.encode()))
    our_public_key = key.public_key().public_bytes(encoding=serialization.Encoding.PEM,
                                                   format=serialization.PublicFormat.SubjectPublicKeyInfo)
    # Make sure the keys folder exists
    if os.path.isdir('keys') is False:
        os.mkdir('keys')
    open('keys/private.pem', 'w').write(our_private_key.decode())
    open('keys/public.pem', 'w').write(our_public_key.decode())
    log("Generated new keys")

####################

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

app.secret_key = pkpass


# Make session permanent

@app.before_request
def before_request():
    session.permanent = True


@app.route('/')
def index():
    return "ID<br><a href='mailto:me@xe1h.xyz'>Nojus Adomaitis</a>, 2023"


# semi oauth2 flow

@app.route('/v2.0/keys')
def get_keys():
    return our_public_key


@app.route('/v2.0/authorize')
def authorize():
    try:
        client_id = request.args['client_id']
        redirect_uri = request.args['redirect_uri']
        if client_id not in authorised_clients or redirect_uri not in authorised_clients[client_id]['request_uris']:
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
                    "?client_id=" + ms_client_id +
                    "&response_type=id_token" +
                    "&redirect_uri=" + URL + "/microsoft/callback" +
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
                               audience=ms_client_id)

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
        if username == password and enableTest:
            session['name'] = password
            return issue_jwt(password, session['our_client_id'])
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
        driver.get("https://dienynas.tamo.lt/Prisijungimas/Login")

        driver.find_element_by_id('UserName').send_keys(username)
        driver.find_element_by_id('Password').send_keys(password)

        driver.find_element_by_css_selector('.c_btn.submit').click()


        if driver.current_url != 'https://dienynas.tamo.lt/DashboardStudents' and driver.current_url != 'https://dienynas.tamo.lt/Dashboard':
            driver.close()
            return redirect("/tamo/login?error=1")

        schoolName = driver.find_element_by_css_selector(
            'html > body.container > div#top_section.row > div.col-md-14 > div.row.top_section_back > div.col-md-10 > span').text

        if schoolName != 'Vilniaus licėjus':
            driver.close()
            return redirect("/tamo/login?error=2")

        name = driver.find_element_by_css_selector(
            'html > body.container > div#header_section.row > div.col-md-14 > div > div > div.header-box > div > div > div > div > div').text

        driver.close()
        session['name'] = name

        return issue_jwt(name, session['our_client_id'])


if __name__ == '__main__':
    app.run()
