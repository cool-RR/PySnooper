# Copyright 2019 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

import tempfile
import shutil
import io
import sys
from . import pathlib
from . import contextlib



@contextlib.contextmanager
def BlankContextManager():
    yield

@contextlib.contextmanager
def create_temp_folder(prefix=tempfile.template, suffix='',
                       parent_folder=None, chmod=None):
    '''
    Context manager that creates a temporary folder and deletes it after usage.

    After the suite finishes, the temporary folder and all its files and
    subfolders will be deleted.

    Example:

        with create_temp_folder() as temp_folder:

            # We have a temporary folder!
            assert temp_folder.is_dir()

            # We can create files in it:
            (temp_folder / 'my_file').open('w')

        # The suite is finished, now it's all cleaned:
        assert not temp_folder.exists()

    Use the `prefix` and `suffix` string arguments to dictate a prefix and/or a
    suffix to the temporary folder's name in the filesystem.

    If you'd like to set the permissions of the temporary folder, pass them to
    the optional `chmod` argument, like this:

        create_temp_folder(chmod=0o550)

    '''
    temp_folder = pathlib.Path(tempfile.mkdtemp(prefix=prefix, suffix=suffix,
                                                dir=parent_folder))
    try:
        if chmod is not None:
            temp_folder.chmod(chmod)
        yield temp_folder
    finally:
        shutil.rmtree(str(temp_folder))


class NotInDict:
    '''Object signifying that the key was not found in the dict.'''


class TempValueSetter(object):
    '''
    Context manager for temporarily setting a value to a variable.

    The value is set to the variable before the suite starts, and gets reset
    back to the old value after the suite finishes.
    '''

    def __init__(self, variable, value, assert_no_fiddling=True):
        '''
        Construct the `TempValueSetter`.

        `variable` may be either an `(object, attribute_string)`, a `(dict,
        key)` pair, or a `(getter, setter)` pair.

        `value` is the temporary value to set to the variable.
        '''

        self.assert_no_fiddling = assert_no_fiddling


        #######################################################################
        # We let the user input either an `(object, attribute_string)`, a
        # `(dict, key)` pair, or a `(getter, setter)` pair. So now it's our job
        # to inspect `variable` and figure out which one of these options the
        # user chose, and then obtain from that a `(getter, setter)` pair that
        # we could use.

        bad_input_exception = Exception(
            '`variable` must be either an `(object, attribute_string)` pair, '
            'a `(dict, key)` pair, or a `(getter, setter)` pair.'
        )

        try:
            first, second = variable
        except Exception:
            raise bad_input_exception
        if hasattr(first, '__getitem__') and hasattr(first, 'get') and \
           hasattr(first, '__setitem__') and hasattr(first, '__delitem__'):
            # `first` is a dictoid; so we were probably handed a `(dict, key)`
            # pair.
            self.getter = lambda: first.get(second, NotInDict)
            self.setter = lambda value: (first.__setitem__(second, value) if
                                         value is not NotInDict else
                                         first.__delitem__(second))
            ### Finished handling the `(dict, key)` case. ###

        elif callable(second):
            # `second` is a callable; so we were probably handed a `(getter,
            # setter)` pair.
            if not callable(first):
                raise bad_input_exception
            self.getter, self.setter = first, second
            ### Finished handling the `(getter, setter)` case. ###
        else:
            # All that's left is the `(object, attribute_string)` case.
            if not isinstance(second, str):
                raise bad_input_exception

            parent, attribute_name = first, second
            self.getter = lambda: getattr(parent, attribute_name)
            self.setter = lambda value: setattr(parent, attribute_name, value)
            ### Finished handling the `(object, attribute_string)` case. ###

        #
        #
        ### Finished obtaining a `(getter, setter)` pair from `variable`. #####


        self.getter = self.getter
        '''Getter for getting the current value of the variable.'''

        self.setter = self.setter
        '''Setter for Setting the the variable's value.'''

        self.value = value
        '''The value to temporarily set to the variable.'''

        self.active = False


    def __enter__(self):

        self.active = True

        self.old_value = self.getter()
        '''The old value of the variable, before entering the suite.'''

        self.setter(self.value)

        # In `__exit__` we'll want to check if anyone changed the value of the
        # variable in the suite, which is unallowed. But we can't compare to
        # `.value`, because sometimes when you set a value to a variable, some
        # mechanism modifies that value for various reasons, resulting in a
        # supposedly equivalent, but not identical, value. For example this
        # happens when you set the current working directory on Mac OS.
        #
        # So here we record the value right after setting, and after any
        # possible processing the system did to it:
        self._value_right_after_setting = self.getter()

        return self


    def __exit__(self, exc_type, exc_value, exc_traceback):

        if self.assert_no_fiddling:
            # Asserting no-one inside the suite changed our variable:
            assert self.getter() == self._value_right_after_setting

        self.setter(self.old_value)

        self.active = False

class OutputCapturer(object):
    '''
    Context manager for catching all system output generated during suite.

    Example:

        with OutputCapturer() as output_capturer:
            print('woo!')

        assert output_capturer.output == 'woo!\n'

    The boolean arguments `stdout` and `stderr` determine, respectively,
    whether the standard-output and the standard-error streams will be
    captured.
    '''
    def __init__(self, stdout=True, stderr=True):
        self.string_io = io.StringIO()

        if stdout:
            self._stdout_temp_setter = \
                TempValueSetter((sys, 'stdout'), self.string_io)
        else: # not stdout
            self._stdout_temp_setter = BlankContextManager()

        if stderr:
            self._stderr_temp_setter = \
                TempValueSetter((sys, 'stderr'), self.string_io)
        else: # not stderr
            self._stderr_temp_setter = BlankContextManager()

    def __enter__(self):
        '''Manage the `OutputCapturer`'s context.'''
        self._stdout_temp_setter.__enter__()
        self._stderr_temp_setter.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        # Not doing exception swallowing anywhere here.
        self._stderr_temp_setter.__exit__(exc_type, exc_value, exc_traceback)
        self._stdout_temp_setter.__exit__(exc_type, exc_value, exc_traceback)

    output = property(lambda self: self.string_io.getvalue(),
                      doc='''The string of output that was captured.''')


class TempSysPathAdder(object):
    '''
    Context manager for temporarily adding paths to `sys.path`.

    Removes the path(s) after suite.

    Example:

        with TempSysPathAdder('path/to/fubar/package'):
            import fubar
            fubar.do_stuff()

    '''
    def __init__(self, addition):
        self.addition = [str(addition)]


    def __enter__(self):
        self.entries_not_in_sys_path = [entry for entry in self.addition if
                                        entry not in sys.path]
        sys.path += self.entries_not_in_sys_path
        return self


    def __exit__(self, *args, **kwargs):

        for entry in self.entries_not_in_sys_path:

            # We don't allow anyone to remove it except for us:
            assert entry in sys.path

            sys.path.remove(entry)


