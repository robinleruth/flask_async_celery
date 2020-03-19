from flask import Flask
from celery import Celery
from app import celeryconfig

celery = Celery(__name__, broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')
celery.config_from_object(celeryconfig)
from app.tasks import run_flask_request
# celery = Celery(__name__, broker=app.config['CELERY_BROKER_URL'])


def create_app() -> Flask:
    app = Flask(__name__)
    app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
    app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
    # app.config['CELERY_TASK_SERIALIZER'] = 'pickle'
    # app.config['CELERY_RESULT_SERIALIZER'] = 'pickle'
    # app.config['CELERY_ACCEPT_CONTENT'] = ['pickle']

    celery.conf.update(app.config)

    from.routes import bp as main_bp
    app.register_blueprint(main_bp)
    from .tasks import tasks_bp
    app.register_blueprint(tasks_bp)

    return app

