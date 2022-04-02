#!/usr/bin/env python
# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.


'''
Generate an AUTHORS file for your Git repo.

This will list the authors by chronological order, from their first
contribution.

You probably want to run it this way:

    ./generate_authors > AUTHORS

'''


import subprocess
import sys

# This is used for people who show up more than once:
deny_list = frozenset((
    'Lumir Balhar',
))


def drop_recurrences(iterable):
    s = set()
    for item in iterable:
        if item not in s:
            s.add(item)
            yield item


def iterate_authors_by_chronological_order(branch):
    log_call = subprocess.run(
        (
            'git', 'log', branch, '--encoding=utf-8', '--full-history',
            '--reverse', '--format=format:%at;%an;%ae'
        ),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    log_lines = log_call.stdout.decode('utf-8').split('\n')
    
    authors = tuple(line.strip().split(";")[1] for line in log_lines)
    authors = (author for author in authors if author not in deny_list)
    return drop_recurrences(authors)


def print_authors(branch):
    for author in iterate_authors_by_chronological_order(branch):
        sys.stdout.buffer.write(author.encode())
        sys.stdout.buffer.write(b'\n')


if __name__ == '__main__':
    try:
        branch = sys.argv[1]
    except IndexError:
        branch = 'master'
    print_authors(branch)
