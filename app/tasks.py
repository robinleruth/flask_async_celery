from functools import wraps
from io import BytesIO
from . import celery

from flask import Blueprint, abort, g, request
from flask import jsonify
from werkzeug.exceptions import InternalServerError
from celery import states

from . import celery
from .utils import url_for

text_types = (str, bytes)

tasks_bp = Blueprint('tasks', __name__)


@celery.task(bind=True)
def run_flask_request(self, environ):
    from app import create_app
    app = create_app()

    if '_wsgi.input' in environ:
        environ['wsgi.input'] = BytesIO(environ['_wsgi.input'])

    # Create a request context similar to that of the original request
    # so that the task can have access to flask.g, flask.request, etc.
    with app.request_context(environ):
        # Record the fact that we are running in the Celery worker now
        g.in_celery = True
        g.task_instance = self

        # Run the route function and record the response
        try:
            rv = app.full_dispatch_request()
        except:
            # If we are in debug mode we want to see the exception
            # Else, return a 500 error
            if app.debug:
                raise
            rv = app.make_response(InternalServerError())
        return (rv.get_data(), rv.status_code, rv.headers)


def async_task(f):
    """
    This decorator transforms a sync route to asynchronous by running it
    in a background thread.
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        # if we are already running the request on the celery side, then we
        # just called the wrapped function to allow the request to execute
        if getattr(g, 'in_celery', False):
            return f(g.task_instance, *args, **kwargs)

        # launch the task
        environ = {k: v for k, v in request.environ.items()
                   if isinstance(v, text_types)}
        if 'wsgi.input' in request.environ:
            environ['_wsgi.input'] = request.get_data()
        t = run_flask_request.apply_async(args=(environ,))

        # Return a 202 response, with a link that the client can use to
        # obtain task status
        if t.state == states.PENDING or t.state == states.RECEIVED or \
                t.state == states.STARTED:
            return jsonify({}), 202, {'Location': url_for('tasks.get_status', id=t.id)}

        # If the task already finished, return its return value as response
        return t.info
    return wrapped


@tasks_bp.route('/status/<id>', methods=['GET'])
def get_status(id):
    """
    Return status about an asynchronous task. If this request returns a 202
    status code, it means that task hasn't finished yet. Else, the response
    from the task is returned.
    """
    task = run_flask_request.AsyncResult(id)
    if task.state == states.PENDING:
        abort(404)
    if task.state == 'PROGRESS':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
        return jsonify(response), 206, {'Location': url_for('tasks.get_status', id=id)}
    if task.state == states.RECEIVED or task.state == states.STARTED:
        return '', 202, {'Location': url_for('tasks.get_status', id=id)}
    return task.info

