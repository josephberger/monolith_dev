from io import BytesIO

from flask import render_template, send_file, request

from apps.leviathan import app
from apps.leviathan.forms import Generic
from config import GlobalConfig
from ctrl.retrieve import retrieve_jobs_all


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