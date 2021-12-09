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
from flask_wtf.file import FileField
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired

class GenerateAudit(FlaskForm):
    file = FileField()
    submit = SubmitField('Generate')

class GenAduit_API(FlaskForm):
    rsa = PasswordField('Passcode', validators=[DataRequired()])
    submit = SubmitField('Generate')

class UserLogs(FlaskForm):
    user = StringField('User ID', validators=[DataRequired()])
    submit = SubmitField('Submit')

class ExportUserLogs(FlaskForm):
    export = SubmitField('Export CSV')

class ExportCSV(FlaskForm):
    export = SubmitField('Export CSV')
    back = SubmitField('Back')

class IfaceRoutes(FlaskForm):
    csv = SubmitField('CSV')

class ZoneLookup(FlaskForm):
    ip = StringField('IP Address or Subnet', validators=[DataRequired()])
    submit = SubmitField('Submit')

class PolicyTest(FlaskForm):
    src_ip = StringField('Source IP or Subnet', validators=[DataRequired()])
    dst_ip = StringField('Destination IP or Subnet', validators=[DataRequired()])
    service = StringField('Service (ex: tcp/80)', validators=[DataRequired()])
    submit = SubmitField('Submit')

class Audits(FlaskForm):
    delete = SubmitField('Delete')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class Search(FlaskForm):
    searchbar = StringField("Search")
    submit = SubmitField("Submit")
    export = SubmitField('Export')
    
class FWSearch(FlaskForm):
    export = SubmitField('Export')