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

from flask import render_template, send_file, request, redirect, url_for, flash

import ctrl
from ctrl.retrieve import retrieve_jobs_all
from apps.leviathan import app
from config import GlobalConfig
from tasks.rediscover import rediscover_device_info, rediscover_nmap_info
from .forms import SwitchSearch, Generic


@app.route('/')
@app.route('/index')
def index():

    return render_template('index.html')


@app.route('/endpoint_search', methods=['POST','GET'])
def endpoint_search():

    #method variables
    form = SwitchSearch()
    device_query = None

    #if a query string exists, query.
    if request.args.get("query"):
        query = request.args.get("query")
        device_query = ctrl.retrieve.reteive_device_info_query(query)

    if form.is_submitted():

        #if search button is pressed, get the query from the search box and redirect with requests
        if request.form.get("submit"):
            query = request.form.get("searchbar")
            return redirect(f"{request.url_root}endpoint_search?query={query}")

    return render_template('endpoint_search/endpoint_search.html', title='Endpoint Search', form=form,
                           searchbar=True,device_query=device_query, root_uri=request.url_root)


@app.route('/endpoint_info/<hostname>', methods=['POST','GET'])
def endpoint_info(hostname=None):

    #method variables
    form = Generic()
    device = None

    if hostname:

        hostname = hostname.replace('"','')
        device = ctrl.reteive_device_all(hostname)

    if form.is_submitted():

        if request.form.get("rediscover"):
            job = GlobalConfig.DEFAULT_QUEUE.enqueue(rediscover_device_info.run, device['info'])
            flash(f"Rediscovering device at ip:{device['info']['ip']}.  Task ID:{job.id}","information")
            return redirect(url_for("endpoint_search"))

        if request.form.get("update_nmap"):
            job = GlobalConfig.HIGH_QUEUE.enqueue(rediscover_nmap_info.run, device['info'])
            flash(f"Updating scan info for ip:{device['info']['ip']}.  Task ID:{job.id}","information")
            return redirect(url_for("endpoint_search"))

    if device:
        return render_template('device_info/endpoint_info.html', title=f'Endpoint Info - {hostname}', device=device,
                               form=form)
    else:
        return render_template('device_info/endpoint_info.html', title='Endpoint Info', device=None,
                               form=form)

@app.route('/tasks', methods=['POST','GET'])
def tasks():

    form = Generic()

    task_info = {}

    high_tasks = {"headers": ["description", "started_at", "finished_at","enqueued_at", "status"],
                 "data_keys": ["description","started_at", "finished_at","enqueued_at", "status"],
                 "data": retrieve_jobs_all(GlobalConfig.HIGH_QUEUE)}


    task_info['High Tasks'] = high_tasks

    default_tasks = {"headers": ["description","started_at", "finished_at","enqueued_at", "status"],
                 "data_keys": ["description","started_at", "finished_at","enqueued_at", "status"],
                 "data": retrieve_jobs_all(GlobalConfig.DEFAULT_QUEUE)}


    task_info['Default Tasks'] = default_tasks

    if form.is_submitted():

        if request.form.get("fullscreen"):
            card = request.form.get("fullscreen")
            if card in task_info:
                return render_template("tasks/fullscreen.html", title=card, table_data=task_info[card])

        elif request.form.get("export_csv"):
            card = request.form.get("export_csv")
            response_csv = ",".join(task_info[card]['data_keys']) + "\n"
            for item in task_info[card]['data']:
                line = ''
                for key in task_info[card]['data_keys']:
                    try:
                        line = line + f"{str(item[key]).replace(',', '')},"
                    except KeyError as e:
                        line = line + ","

                line = line[:-1]
                response_csv += line + "\n"

            response_stream = BytesIO(response_csv.encode())
            return send_file(
                response_stream,
                mimetype="text/csv",
                attachment_filename=f"export.csv",
                as_attachment=True,
            )

    return render_template('tasks/tasks.html', title='Tasks', form=form, task_info=task_info)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html', error=error), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html', error=error), 500