#!/usr/bin/env python3

from sanic import Sanic
from sanic.exceptions import abort
from sanic.response import html
from sanic_compress import Compress
import pymysql
import toml


_CONFIG_PATH = '/config.toml'

_CSS = '''
<style>
    html, body {
        background-color: #5d9bc7;
        color: white;
        font-family: 'Open Sans', sans-serif;
        font-size: 10px;
        padding: 2rem;
    }

    h3 {
        font-family: 'Zilla Slab', 'Open Sans', sans-serif;
    }

    form {
        background-color: #5288af;
        padding: 2rem;
        border-radius: 0.5rem;
    }

    input[type="email"] {
        margin-bottom: 1.5rem;
        height: 1.75rem;
        background-color: #d2d9de;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem;
        font-size: 1.6rem;
    }

    input[type="checkbox"] {
        position: absolute;
        left: -1000em;
    }

    input[type="checkbox"] + label:before {
        content: "";
        display: table-cell;
        width: 3rem;
        height: 3rem;
        position: relative;
        top: -2rem;
        background: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADwAAADwCAMAAABrCPePAAAAMFBMVEX///////////////9MaXH////////////////////////////////////////////28dxAAAAAEHRSTlMyw7SLALxvSzoSq1qDHpp74pmH4AAAAqRJREFUaN7tl223oyAMhBFrEl6U//9vF7UKtbY14Z49u72Zzz4HmA40Y26rHMbJ2wvyU0R3h8yKgmUpuQJTXnMYuosahrw+bTBmtGMp47jCtLAekMwFEYJfaJph5zM7gGEIMmC9yzDMbDAshZmGm3HWdh0YpqDrrHUG88LesOXz0mhihoEPQ4ajmfKukQ9j3vdkfIaJD1OGvZn9MgLNjimssMIKK6ywwgr/FNw00DSNUk1DXNP42DS4No3MbcN6U01oKyht1YhfyqAqZW11ULukdskv6JIhAQq7JE1zQED2jzGt8QoSON6zOQlg2ILt+TDud4e/Mtn9SvHPPO1sYrvdd4+b5sC7WZ0nLhzKE4LcsQKPZjFg8jsL7IGmmNWzp6H0bNZluJhliTuHlVQOyB3izs26CJdUxg/jI0w+0ukVLql8BS+rWHyfyhfw/cuKDq/Meoa34+00naXyBbz7eqcro9PHeTseDnieyhdwdXdmOr0x68Tt4k/+vkolXqoJNV2MDhc7RjgZTeByQQlPbM9oN3BgJ1Y1eqQt8XpVTQ/ILWXlB+4Cv9Gld6n8+BjET2a9fUkWeiJhl8SUgnZJ7ZJf0SXdyHF7dBXs+AlzGzwagcYVFrELbSR73nZubkasXAflsDOjHG5AVSqVSqVSqVSqvzd9jm0jc9Ow3lYTmgpKWzVqK2VtdZAJj9oltUv+i8IQSMpCnxUa2L5HCRtWtocGtk8CrzZWsDLFHeafOe1skBot2vRuVp9Iblak32aW+V/Mop8x6xMbIB1emetGL19GFKUyPHnKMBqOH3KMTsdlOEbD4YCsVFa7nGlmKrGm2aksQJ/4qaxoQSqfaRBdXskVfqS5V7imI8qfHcmfaZBf/xJMyf/wRgvZZXBB873SLvkruuQfKzspfJkcxMIAAAAASUVORK5CYII=);
        background-size: 3rem auto;
    }

    input[type="checkbox"]:checked + label:before {
        background-position: 0 -3rem;
    }

    input[type="checkbox"]:disabled + label:before {
        background-position: 0 -6rem;
    }

    input[type="checkbox"]:checked:disabled + label:before {
        background-position: 0 -9rem;
    }

    label::before {
        margin-right: 0.5rem;
    }

    label {
        font-size: 1.8rem;
    }

    a:link,
    a:visited,
    a:hover,
    a:active {
        color: white;
    }

    input[type="submit"] {
        background-color: #48779a;
        border: none;
        border-radius: 0.5rem;
        padding: 1rem;
        color: white;
    }

    input[type="submit"]:hover,
    input[type="submit"]:active {
        background-color: #658196;
    }
</style>
'''

_FORM = '''
<!DOCTYPE html>
<html lang="en">
    <head>
        <title>Update Subscription - Mozilla IoT</title>
        {css}
    </head>
    <body>
        <h1>Update Mozilla IoT Email Subscription</h1>
        <form method="post">
            <input type="email" name="email" id="email"
                placeholder="Email address" value="{value}" required>
            <br>
            <input type="checkbox" name="subscribe" id="subscribe"
                value="1" checked>
            <label for="subscribe">
                Please keep me updated about new features and contribution
                opportunities.
                <a href="https://www.mozilla.org/en-US/privacy/">
                    Privacy Policy
                </a>
            </label>
            <br>
            <input type="submit">
        </form>
    </body>
</html>
'''

_SUCCESS = '''
<!DOCTYPE html>
<html lang="en">
    <head>
        <title>Update Subscription - Mozilla IoT</title>
        {css}
    </head>
    <body>
        <h1>Thank you for updating your preferences.</h1>
    </body>
</html>
'''

_ERROR = '''
<!DOCTYPE html>
<html lang="en">
    <head>
        <title>Update Subscription - Mozilla IoT</title>
        {css}
    </head>
    <body>
        <h1>There was an error updating your preferences.</h1>
    </body>
</html>
'''


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


def update_optout(email, optout):
    conn = open_database()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'UPDATE accounts SET optout = %s WHERE email = %s',
                (1 if optout else 0, email)
            )
            conn.commit()
            cursor.close()
    except Exception:
        pass

    conn.close()

    return True


app = Sanic()
Compress(app)


@app.route('/preferences', methods=['GET'])
async def get_form(request):
    value = request.args.get('email', '')
    value = value\
        .replace('&', '&amp;')\
        .replace('<', '&lt;')\
        .replace('>', '&gt;')\
        .replace('"', '&quot;')\
        .replace("'", '&#39;')
    return html(_FORM.format(css=_CSS, value=value))


@app.route('/preferences', methods=['POST'])
async def post_form(request):
    email = request.form.get('email', None)
    if not email:
        abort(400)

    optout = request.form.get('subscribe', '0') != '1'

    if update_optout(email, optout):
        return html(_SUCCESS.format(css=_CSS))

    return html(_ERROR.format(css=_CSS))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
