from werkzeug.serving import run_simple

from apps.leviathan import app

if __name__ == '__main__':
    run_simple(
        hostname='0.0.0.0',
        port=5000,
        application=app,
        use_reloader=True,
        #use_debugger=True,
        use_evalex=True)