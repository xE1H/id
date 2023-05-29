from flask import Flask, session

from config import pkpass

# ID sistema
# Nojus Adomaitis, 2023
# xE1H.xyz

app = Flask(__name__)

app.secret_key = pkpass


# Make session permanent

@app.before_request
def before_request():
    session.permanent = True


@app.route('/')
def index():
    return "id.licejus.lt<br><a href='mailto:me+id@xe1h.xyz'>Nojus Adomaitis</a>, 2023<br><a href='/dashboard'>Nori registruoti savo aplikaciją?</a>"


import oauth2, tamo, microsoft, management  # NOQA

if __name__ == '__main__':
    app.run()
