#!/usr/bin/env python3

import pymysql
import sys
import toml


_CONFIG_PATH = '/home/ec2-user/moziot/config/config.toml'


def open_database():
    config = None
    try:
        with open(_CONFIG_PATH, 'rt') as f:
            config = toml.load(f)
    except Exception:
        return None

    # Parse the database path into its parts.
    db_path = config['general']['db_path']
    db_path = db_path[len('mysql://'):]
    user, db_path = db_path.split(':', 1)
    password, db_path = db_path.split('@', 1)
    host, db_name = db_path.split('/', 1)

    try:
        conn = pymysql.connect(host=host,
                               user=user,
                               password=password,
                               db=db_name)
        return conn
    except Exception:
        return None


def get_optout(email):
    conn = open_database()
    if not conn:
        return None

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT optout FROM accounts WHERE email = %s',
                (email,)
            )

            result = cursor.fetchone()
            conn.close()

            if result:
                print(result)
                return result[0] != 0

            return None
    except Exception:
        conn.close()
        return None


if __name__ == '__main__':
    print(get_optout(sys.argv[1]))
