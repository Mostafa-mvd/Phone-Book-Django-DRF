from celery import Celery

app = Celery(__name__, broker='pyamqp://guest@localhost//', backend='rpc://')


@app.task
def greeting():
    return 'hello'
