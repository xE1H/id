"""
SQLite database interface for storing applications
"""
# pylint: disable=import-error, broad-exception-caught
import sqlite3

from config import authorised_clients
from log import log


class DB:
    """
    Database class
    """

    def __init__(self):
        self.conn = sqlite3.connect('applications.db', check_same_thread=False)
        self.cur = self.conn.cursor()
        self.cur.execute(
            'CREATE TABLE IF NOT EXISTS applications (owner TEXT, name TEXT, kilmininkas TEXT, '
            'email TEXT, redirect_uris TEXT, client_id TEXT UNIQUE)')
        self.conn.commit()
        log("Database initialized", "DATABASE")

    def register_app(self, owner, name, kilmininkas, email, redirect_uris, client_id):
        """
        Register a new application
        :param owner: Owner of the application (full name)
        :param name: Application name
        :param kilmininkas: kilmininko linksnis
        :param email: Email the owner supplied when registering
        :param redirect_uris: String of comma seperated URI's
        :param client_id: Made up client id for the application
        :return:
        """
        self.cur.execute(
            'INSERT INTO applications VALUES(?, ?, ?, ?, ?, ?)',
            (owner,
             name,
             kilmininkas,
             email,
             redirect_uris.replace(
                 "\r",
                 ""),
             client_id))
        self.conn.commit()

    def get_apps(self):
        """
        Get all applications
        :return: List of dicts of all applications
        """
        self.cur.execute('SELECT * FROM applications')
        rows = self.cur.fetchall()
        rows = [{'owner': row[0],
                 'name': row[1],
                 'kilmininkas': row[2],
                 'email': row[3],
                 'redirect_uris': row[4].split("\n"),
                 'client_id': row[5]} for row in rows]
        for client in authorised_clients:
            rows.append({'owner': "SYSTEM",
                         'name': client,
                         'email': "me+" + client + "@nojus.dev",
                         'redirect_uris': authorised_clients[client]['request_uris'],
                         'client_id': client})
        return rows

    def edit_app(self, owner, name, kilmininkas, email, redirect_uris, client_id):
        """
        Edit an application
        :param owner: Full name of the owner
        :param name: Name of the application
        :param kilmininkas: Kilmininko linksnis
        :param email: Email the owner supplied when registering
        :param redirect_uris: String of comma seperated URI's
        :param client_id: Made up client id for the application
        :return:
        """
        self.cur.execute(
            'UPDATE applications SET owner = ?, name = ?, kilmininkas = ?, '
            'email = ?, redirect_uris = ? WHERE client_id = ?',
            (owner, name, kilmininkas, email, redirect_uris.replace("\r", ""), client_id))
        self.conn.commit()

    def get_app(self, client_id):
        """
        Get an application
        :param client_id: Client id of the application
        :return: Dict of the application
        """
        self.cur.execute(
            'SELECT * FROM applications WHERE client_id = ?', (client_id,))
        row = self.cur.fetchone()
        row = {
            'owner': row[0],
            'name': row[1],
            'kilmininkas': row[2],
            'email': row[3],
            'redirect_uris': row[4].split("\n"),
            'client_id': row[5]}
        return row

    def delete_app(self, client_id):
        """
        Delete an application
        :param client_id: Client id of the application
        :return:
        """
        self.cur.execute(
            'DELETE FROM applications WHERE client_id = ?', (client_id,))
        self.conn.commit()

    def verify_app(self, client_id, redirect_uri):
        """
        Verify an application
        :param client_id: Client id of the application
        :param redirect_uri: Redirect URI of the application
        :return: Boolean
        """
        try:
            app = self.get_app(client_id)
            if redirect_uri in app['redirect_uris']:
                return True
        except Exception as ex:
            log("Verify app failed with error: " + str(ex))
        return False

    def get_app_display_name(self, client_id):
        """
        Get the display name of an application
        :param client_id: Client id of the application
        :return: Kilmininko linksnis
        """
        try:
            app = self.get_app(client_id)
            return app['kilmininkas']
        except Exception as ex:
            log("Get app display name failed with error: " + str(ex))
        return "Unknown"
