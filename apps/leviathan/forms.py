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

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class Generic(FlaskForm):
    submit = SubmitField('Submit')

class UserLogs(FlaskForm):
    user = StringField('User ID', validators=[DataRequired()])
    submit = SubmitField('Submit')

class ExportUserLogs(FlaskForm):
    export = SubmitField('Export CSV')

class ExportCSV(FlaskForm):
    export = SubmitField('Export CSV')
    back = SubmitField('Back')
    
class System(FlaskForm):
    elastic = SubmitField('Elastic Connection')

class Search(FlaskForm):
    searchbar = StringField("Search")
    submit = SubmitField("Submit")
    export = SubmitField('Export')

