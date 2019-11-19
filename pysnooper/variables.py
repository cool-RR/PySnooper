import itertools
import abc
try:
    from collections.abc import Mapping, Sequence
except ImportError:
    from collections import Mapping, Sequence
from copy import deepcopy

from . import utils
from . import pycompat


def needs_parentheses(source):
    def code(s):
        return compile(s, '<variable>', 'eval').co_code

    return code('{}.x'.format(source)) != code('({}).x'.format(source))


class BaseVariable(pycompat.ABC):
    def __init__(self, source, exclude=()):
        self.source = source
        self.exclude = utils.ensure_tuple(exclude)
        self.code = compile(source, '<variable>', 'eval')
        if needs_parentheses(source):
            self.unambiguous_source = '({})'.format(source)
        else:
            self.unambiguous_source = source

    def items(self, frame, normalize=False):
        try:
            main_value = eval(self.code, frame.f_globals or {}, frame.f_locals)
        except Exception:
            return ()
        return self._items(main_value, normalize)

    @abc.abstractmethod
    def _items(self, key, normalize=False):
        raise NotImplementedError

    @property
    def _fingerprint(self):
        return (type(self), self.source, self.exclude)

    def __hash__(self):
        return hash(self._fingerprint)

    def __eq__(self, other):
        return (isinstance(other, BaseVariable) and
                                       self._fingerprint == other._fingerprint)


class CommonVariable(BaseVariable):
    def _items(self, main_value, normalize=False):
        result = [(self.source, utils.get_shortish_repr(main_value, normalize=normalize))]
        for key in self._safe_keys(main_value):
            try:
                if key in self.exclude:
                    continue
                value = self._get_value(main_value, key)
            except Exception:
                continue
            result.append((
                '{}{}'.format(self.unambiguous_source, self._format_key(key)),
                utils.get_shortish_repr(value)
            ))
        return result

    def _safe_keys(self, main_value):
        try:
            for key in self._keys(main_value):
                yield key
        except Exception:
            pass

    def _keys(self, main_value):
        return ()

    def _format_key(self, key):
        raise NotImplementedError

    def _get_value(self, main_value, key):
        raise NotImplementedError


class Attrs(CommonVariable):
    def _keys(self, main_value):
        return itertools.chain(
            getattr(main_value, '__dict__', ()),
            getattr(main_value, '__slots__', ())
        )

    def _format_key(self, key):
        return '.' + key

    def _get_value(self, main_value, key):
        return getattr(main_value, key)


class Keys(CommonVariable):
    def _keys(self, main_value):
        return main_value.keys()

    def _format_key(self, key):
        return '[{}]'.format(utils.get_shortish_repr(key))

    def _get_value(self, main_value, key):
        return main_value[key]


class Indices(Keys):
    _slice = slice(None)

    def _keys(self, main_value):
        return range(len(main_value))[self._slice]

    def __getitem__(self, item):
        assert isinstance(item, slice)
        result = deepcopy(self)
        result._slice = item
        return result


class Exploding(BaseVariable):
    def _items(self, main_value, normalize=False):
        if isinstance(main_value, Mapping):
            cls = Keys
        elif isinstance(main_value, Sequence):
            cls = Indices
        else:
            cls = Attrs

        return cls(self.source, self.exclude)._items(main_value, normalize)
