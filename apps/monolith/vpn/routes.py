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

from io import BytesIO

from flask import render_template, redirect, url_for, send_file, send_from_directory, request, jsonify

from ..vpn import app
from ..vpn.forms import UserLogs, ExportUserLogs, ExportCSV
from config import LoggerConfig
import ctrl

logger = LoggerConfig.LOGGER

@app.route('/')
def index():
    """ index of the app
    """
    
    return render_template('vpn/index.html', title='VPN')

@app.route('/gateways', methods=['GET', 'POST'])
def gateways():
    """ Displays the available gateways
    """
    
    form = ExportCSV()

    gateways = ctrl.vpn.get_gateways()
    total = 0

    for gw in gateways:

        total += int(gw["users"])

    if form.is_submitted():
        response_stream = BytesIO(ctrl.to_csv(gateways).encode())
        print(type(form.export.label.text))
        print(type(form.back))
        return send_file(
            response_stream,
            mimetype="text/csv",
            attachment_filename="gateways_export.csv",
            as_attachment=True,
        )

    return render_template('vpn/gateways.html', title='Global Protect Gateways', form=form, gateways=gateways, total=total)

@app.route('/gateway_users/<gw>', methods=['GET','POST'])
def gateway_users(gw):
        """ Displays the users for specified gateway
        
        Parameters
        ----------
            gw: str
                gateway name

        """
        form=ExportCSV()

        users = ctrl.vpn.get_gateway_users(gw)
        status = ctrl.vpn.get_gateway_status(gw)
        
        vsix_users = 0
        
        for u in users:
            if u['public_ipv6'] == "::":
                pass
            else:
                vsix_users += 1
                
        if form.is_submitted():
            response_stream = BytesIO(ctrl.to_csv(users).encode())
            print(type(form.export.label.text))
            print(type(form.back))
            return send_file(
                response_stream,
                mimetype="text/csv",
                attachment_filename=f"{gw}_users_export.csv",
                as_attachment=True,
            )

        return render_template('vpn/gateway_users.html', title='Global Protect Users', vsix_users=vsix_users, form=form, users=users, status=status)

@app.route('/userlogs/<user>', methods=['GET', 'POST'])
def userlogs(user='none'):
    """ Presents page to enter a username

    Parameters
    ----------
        user: str
            username to query logs

    """
    form = UserLogs()

    if "none" not in user:
        form.user.data = user

    search_user = form.user.data

    if form.is_submitted():

        return redirect(url_for('userlog_results', search_user=search_user))

    return render_template('vpn/userlogs.html', title='User Logs', form=form )

@app.route('/userlog_results/<search_user>', methods=['GET', 'POST'])
def userlog_results(search_user):
    """ Queries global protect device for logs related to specific username

    Parameters
    ----------
        search_user: str
            username that is being searched

    """
    logs = ctrl.vpn.get_user_logs(search_user)
    for key in logs.keys():
        print(key)
    form = ExportUserLogs()

    if form.is_submitted():

        response_stream = BytesIO(ctrl.to_csv_multi(logs).encode())

        return send_file(
            response_stream,
            mimetype="text/csv",
            attachment_filename="export.csv",
            as_attachment=True,
        )

    return render_template('vpn/userlog_results.html', title='User Log Result', form=form, gp_logs=logs['globalprotect'], sys_logs=logs['system'] )

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html', error=error), 404

@app.errorhandler(400)
def bad_request(error):
    return "bad request"

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html', error=error), 500