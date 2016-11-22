from Products.CMFCore.FSFile import FSFile
from plone.resource.directory import FilesystemResourceDirectory
from Products.Five.browser.resource import DirectoryResource
from Products.Five.browser.resource import FileResource
from plone.resource.file import FilesystemFile
import os


def get_js_resource_object(site, resource):
    if resource.js:
        return site.unrestrictedTraverse(str(resource.js), None)


def get_resource_object(site, path):
    if path:
        return site.unrestrictedTraverse(str(path), None)


def get_url_resource_object(site, resource):
    if resource.url:
        return site.unrestrictedTraverse(resource.url, None)


def remove_extension(filepath):
    parts = filepath.split('.')
    return '.'.join(parts[:-1])


def recursive_resources(base, fs_path):
    paths = {}
    for filename in os.listdir(fs_path):
        filepath = os.path.join(fs_path, filename)
        path_name = os.path.join(base, filename)
        if os.path.isdir(filepath):
            paths.update(recursive_resources(path_name, filepath))
        elif filename.split('.')[-1] in ('js',):
            paths[path_name] = remove_extension(filepath)
        else:
            paths[path_name] = filepath
    return paths


def get_module_dir(mod):
    return os.path.dirname(mod.__file__)


def resource_to_path(resource, file_type='.js'):
    if isinstance(resource, FilesystemFile):
        return resource.path
    elif isinstance(resource, FileResource):
        return resource.chooseContext().path
    elif isinstance(resource, DirectoryResource):
        return resource.context.path
    elif isinstance(resource, FilesystemResourceDirectory):
        return resource.directory
    elif isinstance(resource, FSFile):
        return resource._filepath
    else:
        print("Missing resource type")
        return None
