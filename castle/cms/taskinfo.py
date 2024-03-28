import json


_task_descriptors = {
    'collective.celery.paste_items': 'Paste large number of items',
    'collective.celery.delete_items': 'Delete large number of items',
    'collective.celery.file_edited': 'Processing file',
    'collective.celery._celeryQueueJob': 'Converting file to document viewer',
    'collective.celery.aws_file_deleted': 'Remove file from AWS',
    'collective.celery.create_pdf': 'Create PDF',
    'collective.celery.index_batch_async': 'Index content',
    'collective.celery.process_video': 'Process video',
    'collective.celery.workflow_updated': 'Processing workflow',
    'collective.celery.trash_tree': 'Processing trash',
}


def get_task_name(_id):
    if _id in _task_descriptors:
        return _task_descriptors[_id]
    return _id


def get_info(task):
    try:
        kwargs = json.loads(task.get('kwargs', '{}').replace("'", '"'))
    except Exception:
        kwargs = {}

    try:
        args = json.loads(task.get('args', '{}').replace("'", '"'))
    except Exception:
        args = []

    label = _task_descriptors.get(task['name'], 'Generic task')
    return {
        'kwargs': kwargs,
        'args': args,
        'name': task.get('name'),
        'acknowledged': task.get('acknowledged'),
        'id': task.get('id'),
        'label': label
    }
