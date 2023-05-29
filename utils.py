import datetime
import random

import jwt
from flask import request, session, redirect

from keygen import our_private_key
from config import URL, authorised_clients
from management import db

issuer = URL


def get_random_string(length):
    return ''.join(random.choice('0123456789abcdef') for _ in range(length))


from log import log  # For backwords compatibility


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


def is_valid_application(client_id, redirect_uri):
    try:
        hard_coded = client_id in authorised_clients or (
                redirect_uri in authorised_clients[client_id]['request_uris'])
    except KeyError:
        hard_coded = False

    return hard_coded or db.verify_app(client_id, redirect_uri)


def get_app_display_name(client_id):
    try:
        return authorised_clients[client_id]['name']
    except KeyError:
        return db.get_app_display_name(client_id)
