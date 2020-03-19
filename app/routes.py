import os
import random
import time
from app import celery
from app.tasks import async_task


from flask import Flask
from flask import url_for
from flask import jsonify
from flask import Blueprint
from celery import Celery

bp = Blueprint('main', __name__)

basedir = os.path.abspath(os.path.dirname(__name__))


@bp.route('/')
@async_task
def my_bg_task():
    file_name = os.path.join(basedir, 'test.txt')
    with open(file_name, 'w') as f:
        f.write(f'test')
    return file_name



# @celery.task(bind=True) # bind sends a "self" argument than can be used to record status updates
@bp.route('/longtask')
@async_task
def long_task(self):
    """Background task that runs a long function with progress reports."""
    verb = ['Starting up', 'Booting', 'Repairing', 'Loading', 'Checking']
    adjective = ['master', 'radiant', 'silent', 'harmonic', 'fast']
    noun = ['solar array', 'particle reshaper', 'cosmic ray', 'orbiter', 'bit']
    message = ''
    total = random.randint(10, 50)
    for i in range(total):
        if not message or random.random() < 0.25:
            message = '{0} {1} {2}...'.format(random.choice(verb),
                                              random.choice(adjective),
                                              random.choice(noun))
        # update_state is how Celery receives these task updates
        # there are numbers of built-in states such as STARTED, SUCCESS...
        # You can use custom ones as "PROGRESS"
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total,
                                'status': message})
        time.sleep(1)
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}


# @bp.route('/status/<task_id>')
# def taskstatus(task_id):
#     task = long_task.AsyncResult(task_id)
#     if task.state == 'PENDING':
#         # job did not start yet
#         response = {
#             'state': task.state,
#             'current': 0,
#             'total': 1,
#             'status': 'Pending...'
#         }
#     elif task.state != 'FAILURE':
#         response = {
#             'state': task.state,
#             'current': task.info.get('current', 0),
#             'total': task.info.get('total', 1),
#             'status': task.info.get('status', '')
#         }
#         if 'result' in task.info:
#             response['result'] = task.info['result']
#     else:
#         # something went wrong in the background job
#         response = {
#             'state': task.state,
#             'current': 1,
#             'total': 1,
#             'status': str(task.info),  # this is the exception raised
#         }
#     return jsonify(response)


