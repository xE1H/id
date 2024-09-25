import os

URL = os.environ["id_base_url"]
pkpass = os.environ["id_enc_key"]

ms_client_id = os.environ["id_ms_client_id"]
ms_client_secret = os.environ["id_ms_client_secret"]
ms_tenant = os.environ["id_ms_tenant"]

enable_test = os.environ["id_enable_test"] == "true"

authorised_clients = {
    "dashboard": {
        "request_uris": URL + "/dashboard"  # url of request redirect
    }
}  # default clients owned by system
