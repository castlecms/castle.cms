from collective.celery.utils import getCelery

app = getCelery()

@app.task()
def add(x, y):
    print('made it to task!')
    import time
    time.sleep(500)
    return x + y