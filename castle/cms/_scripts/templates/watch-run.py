import os
import argparse
import time
import hashlib

parser = argparse.ArgumentParser(description='')
parser.add_argument('--command', dest='command')
parser.add_argument('--dirs', dest='dirs', nargs='+')

args = parser.parse_args()

times = {}


def sha256(fname):
    encrypt_sha256 = hashlib.sha256()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            encrypt_sha256.update(chunk)
    return encrypt_sha256.hexdigest()


def check(directory):
    changed = False
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)

        if os.path.isdir(filepath):
            if check(filepath):
                changed = True
        else:
            fi = open('/Users/katieschramm/dev/git/FBI/fbigov-dev/sha256_check', 'a')
            path = 'castle/cms/_scripts/templates/watch-run.py check'
            fi.write(path + '\n')
            fi.close()
            encrypted = sha256(filepath)
            current_encrypt = times.get(filepath, None)

            times[filepath] = encrypted

            if encrypted != current_encrypt:
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
