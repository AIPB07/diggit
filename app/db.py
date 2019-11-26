import mysql.connector
from mysql.connector import errorcode
import click
from flask import current_app, g
from flask.cli import with_appcontext

from . import schema


def get_db():
    # if db connection for request doesn't exist yet, create one
    if 'db' not in g:
        try:
            g.db = mysql.connector.connect(
                host=current_app.config['HOST'],
                user=current_app.config['USER'],
                passwd=current_app.config['PASSWD'],
                database=current_app.config['DB_NAME']
            )
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print('Invalid username or password')
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print('Database does not exist')
            else:
                print(err)

    return g.db


def close_db(e=None):
    # if db connection exists, close it
    db=g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    # get db connection and cursor
    db = get_db()
    cursor = db.cursor()

    # create tables
    for table in schema.TABLES:
        table_description = schema.TABLES[table]
        try:
            print("Creating table {}: ".format(table), end='')
            cursor.execute(table_description)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print('already exists')
            else:
                print(err)
        else:
            print('OK')
    
    cursor.close()


# define a command line command 'init-db' that calls init_db()
@click.command('init-db')
@with_appcontext
def init_db_command():
    """Create new tables"""
    init_db()
    click.echo('Initialized the database.')


def init_app(app):
    """Register close_db() and init_db_command() with application instance"""
    # call close_db() when cleaning up after returning response
    app.teardown_appcontext(close_db)
    # add command that can be called with the flask command
    app.cli.add_command(init_db_command)