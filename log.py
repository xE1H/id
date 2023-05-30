from flask import request
from datetime import datetime

# Create log file if it doesn't exist
f = open("log.txt", "a")


def log(message, route=None):
    if route is None:
        try:
            route = request.path
        except:
            route = 'APP'

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    BLUE = '\033[94m'
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

    print(BLUE + BOLD + " * " + route + ENDC + GREEN + ' | ' + CYAN + str(timestamp) + GREEN + " | " + ENDC + message)
    f.write(f"{timestamp} | {route} | {message}\n")
