##############################
## ID sistemos konfiguracija##
##############################

URL = 'http://localhost:5000'

## Autorizuoti klientai

authorised_clients = {
    'fablab': {
        "request_uris": [
            'http://localhost:3000/login'
        ],
        "name": "fablab'o sistemos" # K. linksnis
    },
    'kirciuokle': {
        "request_uris": [
            'http://localhost:3000/login'
        ],
        "name": "kirčiuoklės"
    }
}

## Microsoft logino conf

ms_client_id = "632effdc-4ee3-4cb6-9143-f773f1ed2069"

## Tamo logino conf

enableTest = False
# Leidzia prisijungti bet kokiu vardu, kai username == password == vardas, kurio norite (per tamo)

## Private key pass

pkpass = "i7YQ%9tzPGYF67FVo9pfJEgx7eDmLupn5W$R*FZeK*EyHEn88CCmvdHYShnfzYw#LxZvCnAL&FwELr!D^2qLqh6aDjWpVHc^&S4^eHp5J2!X%QhMcL%Z*h88U#6%AND5"