import os
import argparse
import time
import hashlib

parser = argparse.ArgumentParser(description='')
parser.add_argument('--command', dest='command')
parser.add_argument('--dirs', dest='dirs', nargs='+')

args = parser.parse_args()

times = {}


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def check(directory):
    changed = False
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)

        if os.path.isdir(filepath):
            if check(filepath):
                changed = True
        else:
            hashed = md5(filepath)
            current_hash = times.get(filepath, None)

            times[filepath] = hashed

            if hashed != current_hash:
                print(filepath + ' has changed!')
                changed = True

    return changed


def check_all(directories):
    changed = False
    for directory in directories:
        if check(directory):
            changed = True

    return changed


# initialize values...
def initialize(directory):
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)

        if os.path.isdir(filepath):
            initialize(filepath)
        else:
            changed_time = os.stat(filepath).st_mtime
            times[filepath] = changed_time


for directory in args.dirs:
    initialize(directory)


os.system(args.command)

while True:
    if check_all(args.dirs):
        # now run command...
        os.system(args.command)
    time.sleep(0.5)
