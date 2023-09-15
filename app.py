"""
ID sistema
Nojus Adomaitis, 2023
nojus.dev
"""

# pylint: disable=import-error, unused-import, wrong-import-position

from flask import Flask, session, redirect

from config import pkpass


with open("build.number", "r", encoding="utf-8") as f:
    build = f.read()

with open("date.number", "r", encoding="utf-8") as f:
    date = f.read()

app = Flask(__name__)

app.secret_key = pkpass


# Make session permanent

@app.before_request
def before_request():
    """
    Make session permanent
    :return:
    """
    session.permanent = True


@app.route('/')
def index():
    """
    Main page of the website
    :return: HTML of the main page
    """
    return """id.licejus.lt<br>
    <a href='mailto:me+id@nojus.dev'>Nojus Adomaitis</a>, 2023<br><br>
    <a href='https://github.com/xE1H/id'>Pilnas sistemos kodas</a><br>
    <a href='/dashboard'>Nori registruoti savo aplikaciją?</a><br><br><br>v
    """ + build + " (" + date.strip() + ")"


@app.route("/docs")
def docs():
    """
    Redirects to the documentation
    :return: Redirect to the documentation
    """
    return redirect("https://github.com/xE1H/id/blob/master/README.md")

import microsoft
import tamo
import oauth2
import management

if __name__ == '__main__':
    app.run()
