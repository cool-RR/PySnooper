import datetime as datetime_module
import re

from . import utils
from .third_party import six


class Event(object):
    def __init__(self, frame, event, arg, depth):
        self.frame = frame
        self.event = event
        self.arg = arg
        self.depth = depth

        self.variables = []
        self.source = get_source_from_frame(self.frame)
        self.line_no = self.frame.f_lineno

        if self.event == 'call' and self.source_line.lstrip().startswith('@'):
            # If a function decorator is found, skip lines until an actual
            # function definition is found.
            while True:
                self.line_no += 1
                try:
                    if self.source_line.lstrip().startswith('def'):
                        break
                except IndexError:
                    self.line_no = self.frame.lineno
                    break

    @property
    def source_line(self):
        return self.source[self.line_no - 1]

    @property
    def entries(self):
        result = self.variables[:]
        result.append(self)
        if self.event == 'return':
            result.append(ReturnValueEntry(
                value=self.arg,
            ))
        return result


class Entry(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class VariableEntry(Entry):
    pass


class ReturnValueEntry(Entry):
    pass


class DefaultFormatter(object):
    datetime_format = '%H:%M:%S.%f'

    def __init__(self, prefix):
        self.prefix = six.text_type(prefix)
        self.now_length = len(self.now_string())

    def now_string(self):
        return datetime_module.datetime.now().strftime(self.datetime_format)

    def format(self, event):
        indent = event.depth * u'    '
        return ''.join([
            (
                    self.prefix
                    + indent
                    + self.format_entry(entry, event)
                    + u'\n'
            )
            for entry in event.entries
        ])

    def format_entry(self, entry, event):
        method = getattr(self, 'format_' + entry.__class__.__name__)
        return method(entry, event)

    def format_Event(self, entry, _event):
        return u'{now_string} {event:9} {line_no:4} {source_line}'.format(
            now_string=self.now_string(),
            source_line=entry.source_line,
            **entry.__dict__
        )

    def format_VariableEntry(self, entry, _event):
        return u'{description} {name} = {value_repr}'.format(
            description=u'{entry.type} var:'
                .format(entry=entry)
                .ljust(self.now_length, '.'),
            **entry.__dict__
        )

    def format_ReturnValueEntry(self, entry, _event):
        return u'{description} {value_repr}'.format(
            description=u'Return value:'.ljust(self.now_length, '.'),
            value_repr=utils.get_shortish_repr(entry.value),
        )


class UnavailableSource(object):
    def __getitem__(self, i):
        return u'SOURCE IS UNAVAILABLE'


source_cache = {}
ipython_filename_pattern = re.compile('^<ipython-input-([0-9]+)-.*>$')


def get_source_from_frame(frame):
    globs = frame.f_globals or {}
    module_name = globs.get('__name__')
    file_name = frame.f_code.co_filename
    cache_key = (module_name, file_name)
    try:
        return source_cache[cache_key]
    except KeyError:
        pass
    loader = globs.get('__loader__')

    source = None
    if hasattr(loader, 'get_source'):
        try:
            source = loader.get_source(module_name)
        except ImportError:
            pass
        if source is not None:
            source = source.splitlines()
    if source is None:
        ipython_filename_match = ipython_filename_pattern.match(file_name)
        if ipython_filename_match:
            entry_number = int(ipython_filename_match.group(1))
            try:
                import IPython
                ipython_shell = IPython.get_ipython()
                ((_, _, source_chunk),) = ipython_shell.history_manager. \
                    get_range(0, entry_number, entry_number + 1)
                source = source_chunk.splitlines()
            except Exception:
                pass
        else:
            try:
                with open(file_name, 'rb') as fp:
                    source = fp.read().splitlines()
            except utils.file_reading_errors:
                pass
    if source is None:
        source = UnavailableSource()

    # If we just read the source from a file, or if the loader did not
    # apply tokenize.detect_encoding to decode the source into a
    # string, then we should do that ourselves.
    if isinstance(source[0], bytes):
        encoding = 'ascii'
        for line in source[:2]:
            # File coding may be specified. Match pattern from PEP-263
            # (https://www.python.org/dev/peps/pep-0263/)
            match = re.search(br'coding[:=]\s*([-\w.]+)', line)
            if match:
                encoding = match.group(1).decode('ascii')
                break
        source = [six.text_type(sline, encoding, 'replace') for sline in
                  source]

    source_cache[cache_key] = source
    return source
