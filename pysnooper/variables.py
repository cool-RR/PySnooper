import itertools
from copy import deepcopy

from .utils import get_shortish_repr, ensure_tuple


class BaseVariable(object):
    def __init__(self, source, exclude=()):
        self.source = source
        self.exclude = ensure_tuple(exclude)
        self.code = compile(source, '<variable>', 'eval')

    def items(self, frame):
        try:
            main_value = eval(self.code, frame.f_globals, frame.f_locals)
        except Exception:
            return ()
        return self._items(main_value)

    def _items(self, key):
        raise NotImplementedError()


class CommonVariable(BaseVariable):
    def _items(self, main_value):
        result = [(self.source, get_shortish_repr(main_value))]
        for key in self._safe_keys(main_value):
            if key in self.exclude:
                continue
            try:
                value = self._get_value(main_value, key)
            except Exception:
                continue
            result.append((
                '({}){}'.format(self.source, self._format_key(key)),
                get_shortish_repr(value)
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
        raise NotImplementedError()

    def _get_value(self, main_value, key):
        raise NotImplementedError()


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
        return '[{!r}]'.format(key)

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


class Exploded(BaseVariable):
    def _items(self, main_value):
        typ = main_value.__class__

        def has_method(name):
            return callable(getattr(typ, name, None))

        cls = Attrs
        if has_method('__getitem__'):
            if has_method('keys'):
                cls = Keys
            elif has_method('__len__'):
                cls = Indices

        return cls(self.source, self.exclude)._items(main_value)
