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

from flask import Flask, render_template
from flask_restx import Api

from config import Config
from ctrl import Retrieve, TaskMgr

plugin_mods = Config.PLUGIN_MODS
retrieve = Retrieve(Config)
taskmgr = TaskMgr(Config)

app = Flask(__name__)
app.config.from_object(Config)
app.config["PROPAGATE_EXCEPTIONS"] = False
app.config['ERROR_404_HELP'] = False

@app.route('/')
@app.route('/index')
def index():

    return render_template('index.html')

api = Api(app, doc='/docs')

from ..leviathan import routes
from .utils import filters

def create_app():

    return app
