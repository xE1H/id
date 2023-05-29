import sqlite3

from config import authorised_clients
from log import log

class DB:
    def __init__(self):
        self.conn = sqlite3.connect('applications.db', check_same_thread=False)
        self.cur = self.conn.cursor()
        self.cur.execute(
            'CREATE TABLE IF NOT EXISTS applications (owner TEXT, name TEXT, kilmininkas TEXT, email TEXT, redirect_uris TEXT, client_id TEXT UNIQUE)')
        self.conn.commit()
        log("Database initialized", "DATABASE")

    def register_app(self, owner, name, kilmininkas, email, redirect_uris, client_id):
        self.cur.execute('INSERT INTO applications VALUES(?, ?, ?, ?, ?, ?)',
                         (owner, name, kilmininkas, email, redirect_uris.replace("\r", ""), client_id))
        self.conn.commit()

    def get_apps(self):
        self.cur.execute('SELECT * FROM applications')
        rows = self.cur.fetchall()
        rows = [{'owner': row[0], 'name': row[1], 'kilmininkas': row[2], 'email': row[3],
                 'redirect_uris': row[4].split("\n"), 'client_id': row[5]} for row in rows]
        for client in authorised_clients:
            rows.append({'owner': "SYSTEM", 'name': client, 'email': "me+" + client + "@xe1h.xyz",
                         'redirect_uris': authorised_clients[client]['request_uris'], 'client_id': client})
        return rows

    def edit_app(self, owner, name, kilmininkas, email, redirect_uris, client_id):
        self.cur.execute(
            'UPDATE applications SET owner = ?, name = ?, kilmininkas = ?, email = ?, redirect_uris = ? WHERE client_id = ?',
            (owner, name, kilmininkas, email, redirect_uris.replace("\r", ""), client_id))
        self.conn.commit()

    def get_app(self, client_id):
        self.cur.execute('SELECT * FROM applications WHERE client_id = ?', (client_id,))
        row = self.cur.fetchone()
        row = {'owner': row[0], 'name': row[1], 'kilmininkas': row[2], 'email': row[3], 'redirect_uris': row[4].split("\n"),
               'client_id': row[5]}
        return row

    def delete_app(self, client_id):
        self.cur.execute('DELETE FROM applications WHERE client_id = ?', (client_id,))
        self.conn.commit()

    def verify_app(self, client_id, redirect_uri):
        try:
            app = self.get_app(client_id)
            if redirect_uri in app['redirect_uris']:
                return True
        except Exception as ex:
            log("Verify app failed with error: " + str(ex))
        finally:
            return False
