from flask import request
def log(message, route=None):
    if route is None:
        try:
            route = request.path
        except:
            route = 'APP'

    BLUE = '\033[94m'
    GREEN = '\033[92m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

    print(BLUE + BOLD + " * " + route + ENDC + GREEN + ' | ' + ENDC + message)