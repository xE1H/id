from flask import Flask, session, redirect

from config import pkpass

# ID sistema
# Nojus Adomaitis, 2023
# xE1H.xyz

with open("build.number", "r") as f:
    build = f.read()

with open("date.number", "r") as f:
    date = f.read()

app = Flask(__name__)

app.secret_key = pkpass


# Make session permanent

@app.before_request
def before_request():
    session.permanent = True


@app.route('/')
def index():
    return "id.licejus.lt<br><a href='mailto:me+id@xe1h.xyz'>Nojus Adomaitis</a>, 2023<br><a href='/dashboard'>Nori registruoti savo aplikaciją?</a><br> v" + build + " (" + date.strip() + ")"


@app.route("/docs")
def docs():
    return redirect("https://hackmd.io/@xE1H/ryD7UtMI3")


import oauth2, tamo, microsoft, management  # NOQA

if __name__ == '__main__':
    app.run()
