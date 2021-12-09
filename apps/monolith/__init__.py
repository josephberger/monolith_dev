#
# Joseph Berger <airmanberger@gmail.com>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#

from flask import Flask
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

from apps.monolith import routes
from .utils import filters

def create_app():

    return app

from werkzeug.middleware.dispatcher import DispatcherMiddleware

monolith = create_app()

# from .vpn import create_app as app_vpn
# vpn = app_vpn()
#
# from .firewall import create_app as app_firewall
# firewall = app_firewall()
#
# from .api import create_app as app_api
# api = app_api()
#
# from .swtich import create_app as app_switch
# switch = app_switch()

# merge
application = DispatcherMiddleware(
    monolith, {
        # '/vpn': vpn,
        # '/firewall' : firewall,
        # '/api' : api,
        # '/switch': switch,
    })
