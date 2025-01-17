# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
from copy import copy
from io import StringIO
from collections import Counter

import pytest
import numpy as np

from astropy.io.registry import _readers, _writers, _identifiers
from astropy.io import registry as io_registry
from astropy.table import Table
from astropy import units as u

# Since we reset the readers/writers below, we need to also import any
# sub-package that defines readers/writers first
from astropy import timeseries  # noqa

# Cache original _readers, _writers, _identifiers in setup_function
# since tests modify them.  Important to do caching in setup_function
# and not globally (as was the original implementation) because e.g.
# CCDData reader/writers get registered *after* this module gets imported
# during test collection but *before* tests (and the final teardown) get run.
# This leaves the registry corrupted.
ORIGINAL = {}


class TestData:
    read = classmethod(io_registry.read)
    write = io_registry.write


def setup_function(function):
    ORIGINAL['readers'] = copy(_readers)
    ORIGINAL['writers'] = copy(_writers)
    ORIGINAL['identifiers'] = copy(_identifiers)

    _readers.clear()
    _writers.clear()
    _identifiers.clear()


def empty_reader(*args, **kwargs):
    return TestData()


def empty_writer(table, *args, **kwargs):
    pass


def empty_identifier(*args, **kwargs):
    return True


def test_get_reader_invalid():
    with pytest.raises(io_registry.IORegistryError) as exc:
        with pytest.warns(FutureWarning):
            io_registry.get_reader('test', TestData)
    assert str(exc.value).startswith(
        "No reader defined for format 'test' and class 'TestData'")


def test_get_writer_invalid():
    with pytest.raises(io_registry.IORegistryError) as exc:
        with pytest.warns(FutureWarning):
            io_registry.get_writer('test', TestData)
    assert str(exc.value).startswith(
        "No writer defined for format 'test' and class 'TestData'")


def test_register_reader():

    io_registry.register_reader('test1', TestData, empty_reader)
    io_registry.register_reader('test2', TestData, empty_reader)

    assert io_registry.get_reader('test1', TestData) == empty_reader
    assert io_registry.get_reader('test2', TestData) == empty_reader

    io_registry.unregister_reader('test1', TestData)

    with pytest.raises(io_registry.IORegistryError):
        io_registry.get_reader('test1', TestData)
    assert io_registry.get_reader('test2', TestData) == empty_reader

    with pytest.warns(FutureWarning):
        io_registry.unregister_reader('test2', TestData)

    with pytest.raises(io_registry.IORegistryError):
        with pytest.warns(FutureWarning):
            io_registry.get_reader('test2', TestData)


def test_register_writer():

    io_registry.register_writer('test1', TestData, empty_writer)
    io_registry.register_writer('test2', TestData, empty_writer)

    assert io_registry.get_writer('test1', TestData) == empty_writer
    assert io_registry.get_writer('test2', TestData) == empty_writer

    io_registry.unregister_writer('test1', TestData)

    with pytest.raises(io_registry.IORegistryError):
        io_registry.get_writer('test1', TestData)
    assert io_registry.get_writer('test2', TestData) == empty_writer

    with pytest.warns(FutureWarning):
        io_registry.unregister_writer('test2', TestData)

    with pytest.raises(io_registry.IORegistryError):
        with pytest.warns(FutureWarning):
            io_registry.get_writer('test2', TestData)


def test_register_identifier():

    io_registry.register_identifier('test1', TestData, empty_identifier)
    io_registry.register_identifier('test2', TestData, empty_identifier)

    io_registry.unregister_identifier('test1', TestData)
    io_registry.unregister_identifier('test2', TestData)


def test_register_reader_invalid():
    io_registry.register_reader('test', TestData, empty_reader)
    with pytest.raises(io_registry.IORegistryError) as exc:
        io_registry.register_reader('test', TestData, empty_reader)
    assert (str(exc.value) == "Reader for format 'test' and class 'TestData' "
                              "is already defined")


def test_register_writer_invalid():
    io_registry.register_writer('test', TestData, empty_writer)
    with pytest.raises(io_registry.IORegistryError) as exc:
        io_registry.register_writer('test', TestData, empty_writer)
    assert (str(exc.value) == "Writer for format 'test' and class 'TestData' "
                              "is already defined")


def test_register_identifier_invalid():
    io_registry.register_identifier('test', TestData, empty_identifier)
    with pytest.raises(io_registry.IORegistryError) as exc:
        io_registry.register_identifier('test', TestData, empty_identifier)
    assert (str(exc.value) == "Identifier for format 'test' and class "
                              "'TestData' is already defined")


def test_unregister_reader_invalid():
    with pytest.raises(io_registry.IORegistryError) as exc:
        io_registry.unregister_reader('test', TestData)
    assert str(exc.value) == "No reader defined for format 'test' and class 'TestData'"


def test_unregister_writer_invalid():
    with pytest.raises(io_registry.IORegistryError) as exc:
        io_registry.unregister_writer('test', TestData)
    assert str(exc.value) == "No writer defined for format 'test' and class 'TestData'"


def test_unregister_identifier_invalid():
    with pytest.raises(io_registry.IORegistryError) as exc:
        io_registry.unregister_identifier('test', TestData)
    assert str(exc.value) == "No identifier defined for format 'test' and class 'TestData'"


def test_register_reader_force():
    io_registry.register_reader('test', TestData, empty_reader)
    io_registry.register_reader('test', TestData, empty_reader, force=True)


def test_register_writer_force():
    io_registry.register_writer('test', TestData, empty_writer)
    io_registry.register_writer('test', TestData, empty_writer, force=True)


def test_register_identifier_force():
    io_registry.register_identifier('test', TestData, empty_identifier)
    io_registry.register_identifier('test', TestData, empty_identifier, force=True)


def test_read_noformat():
    with pytest.raises(io_registry.IORegistryError) as exc:
        with pytest.warns(FutureWarning):
            TestData.read()
    assert str(exc.value).startswith("Format could not be identified based on the"
                                     " file name or contents, please provide a"
                                     " 'format' argument.")


def test_write_noformat():
    with pytest.raises(io_registry.IORegistryError) as exc:
        with pytest.warns(FutureWarning):
            TestData().write()
    assert str(exc.value).startswith("Format could not be identified based on the"
                                     " file name or contents, please provide a"
                                     " 'format' argument.")


def test_read_noformat_arbitrary():
    """Test that all identifier functions can accept arbitrary input"""
    _identifiers.update(ORIGINAL['identifiers'])
    with pytest.raises(io_registry.IORegistryError) as exc:
        with pytest.warns(FutureWarning):
            TestData.read(object())
    assert str(exc.value).startswith("Format could not be identified based on the"
                                     " file name or contents, please provide a"
                                     " 'format' argument.")


def test_read_noformat_arbitrary_file(tmpdir):
    """Tests that all identifier functions can accept arbitrary files"""
    _readers.update(ORIGINAL['readers'])
    testfile = str(tmpdir.join('foo.example'))
    with open(testfile, 'w') as f:
        f.write("Hello world")

    with pytest.raises(io_registry.IORegistryError) as exc:
        Table.read(testfile)
    assert str(exc.value).startswith("Format could not be identified based on the"
                                     " file name or contents, please provide a"
                                     " 'format' argument.")


def test_write_noformat_arbitrary():
    """Test that all identifier functions can accept arbitrary input"""
    _identifiers.update(ORIGINAL['identifiers'])
    with pytest.raises(io_registry.IORegistryError) as exc:
        with pytest.warns(FutureWarning):
            TestData().write(object())
    assert str(exc.value).startswith("Format could not be identified based on the"
                                     " file name or contents, please provide a"
                                     " 'format' argument.")


def test_write_noformat_arbitrary_file(tmpdir):
    """Tests that all identifier functions can accept arbitrary files"""
    _writers.update(ORIGINAL['writers'])
    testfile = str(tmpdir.join('foo.example'))

    with pytest.raises(io_registry.IORegistryError) as exc:
        Table().write(testfile)
    assert str(exc.value).startswith("Format could not be identified based on the"
                                     " file name or contents, please provide a"
                                     " 'format' argument.")


def test_read_toomanyformats():
    io_registry.register_identifier('test1', TestData, lambda o, *x, **y: True)
    io_registry.register_identifier('test2', TestData, lambda o, *x, **y: True)
    with pytest.raises(io_registry.IORegistryError) as exc:
        TestData.read()
    assert str(exc.value) == (
        "Format is ambiguous - options are: test1, test2"
    )


def test_write_toomanyformats():
    io_registry.register_identifier('test1', TestData, lambda o, *x, **y: True)
    io_registry.register_identifier('test2', TestData, lambda o, *x, **y: True)
    with pytest.raises(io_registry.IORegistryError) as exc:
        TestData().write()
    assert str(exc.value) == (
        "Format is ambiguous - options are: test1, test2"
    )


def test_read_uses_priority():
    counter = Counter()

    def counting_reader1(*args, **kwargs):
        counter["test1"] += 1
        return TestData()

    def counting_reader2(*args, **kwargs):
        counter["test2"] += 1
        return TestData()

    io_registry.register_reader('test1', TestData, counting_reader1, priority=1)
    io_registry.register_reader('test2', TestData, counting_reader2, priority=2)
    io_registry.register_identifier('test1', TestData, lambda o, *x, **y: True)
    io_registry.register_identifier('test2', TestData, lambda o, *x, **y: True)

    TestData.read()
    assert counter["test2"] == 1
    assert counter["test1"] == 0


def test_write_uses_priority():
    counter = Counter()

    def counting_writer1(*args, **kwargs):
        counter["test1"] += 1

    def counting_writer2(*args, **kwargs):
        counter["test2"] += 1

    io_registry.register_writer('test1', TestData, counting_writer1, priority=1)
    io_registry.register_writer('test2', TestData, counting_writer2, priority=2)
    io_registry.register_identifier('test1', TestData, lambda o, *x, **y: True)
    io_registry.register_identifier('test2', TestData, lambda o, *x, **y: True)

    TestData().write()
    assert counter["test2"] == 1
    assert counter["test1"] == 0


def test_read_format_noreader():
    with pytest.raises(io_registry.IORegistryError) as exc:
        with pytest.warns(FutureWarning):
            TestData.read(format='test')
    assert str(exc.value).startswith(
        "No reader defined for format 'test' and class 'TestData'")


def test_write_format_nowriter():
    with pytest.raises(io_registry.IORegistryError) as exc:
        with pytest.warns(FutureWarning):
            TestData().write(format='test')
    assert str(exc.value).startswith(
        "No writer defined for format 'test' and class 'TestData'")


def test_read_identifier(tmpdir):

    io_registry.register_identifier(
        'test1', TestData,
        lambda o, path, fileobj, *x, **y: path.endswith('a'))
    io_registry.register_identifier(
        'test2', TestData,
        lambda o, path, fileobj, *x, **y: path.endswith('b'))

    # Now check that we got past the identifier and are trying to get
    # the reader. The io_registry.get_reader will fail but the error message
    # will tell us if the identifier worked.

    filename = tmpdir.join("testfile.a").strpath
    open(filename, 'w').close()
    with pytest.raises(io_registry.IORegistryError) as exc:
        with pytest.warns(FutureWarning):
            TestData.read(filename)
    assert str(exc.value).startswith(
        "No reader defined for format 'test1' and class 'TestData'")

    filename = tmpdir.join("testfile.b").strpath
    open(filename, 'w').close()
    with pytest.raises(io_registry.IORegistryError) as exc:
        with pytest.warns(FutureWarning):
            TestData.read(filename)
    assert str(exc.value).startswith(
        "No reader defined for format 'test2' and class 'TestData'")


def test_write_identifier():

    io_registry.register_identifier('test1', TestData, lambda o, *x, **y: x[0].startswith('a'))
    io_registry.register_identifier('test2', TestData, lambda o, *x, **y: x[0].startswith('b'))

    # Now check that we got past the identifier and are trying to get
    # the reader. The io_registry.get_writer will fail but the error message
    # will tell us if the identifier worked.

    with pytest.raises(io_registry.IORegistryError) as exc:
        with pytest.warns(FutureWarning):
            TestData().write('abc')
    assert str(exc.value).startswith(
        "No writer defined for format 'test1' and class 'TestData'")

    with pytest.raises(io_registry.IORegistryError) as exc:
        with pytest.warns(FutureWarning):
            TestData().write('bac')
    assert str(exc.value).startswith(
        "No writer defined for format 'test2' and class 'TestData'")


def test_identifier_origin():

    io_registry.register_identifier('test1', TestData, lambda o, *x, **y: o == 'read')
    io_registry.register_identifier('test2', TestData, lambda o, *x, **y: o == 'write')
    io_registry.register_reader('test1', TestData, empty_reader)
    io_registry.register_writer('test2', TestData, empty_writer)

    # There should not be too many formats defined
    TestData.read()
    TestData().write()

    with pytest.raises(io_registry.IORegistryError) as exc:
        TestData.read(format='test2')
    assert str(exc.value).startswith(
        "No reader defined for format 'test2' and class 'TestData'")

    with pytest.raises(io_registry.IORegistryError) as exc:
        TestData().write(format='test1')
    assert str(exc.value).startswith(
        "No writer defined for format 'test1' and class 'TestData'")


def test_read_valid_return():
    io_registry.register_reader('test', TestData, lambda: TestData())
    t = TestData.read(format='test')
    assert isinstance(t, TestData)


def test_non_existing_unknown_ext():
    """Raise the correct error when attempting to read a non-existing
    file with an unknown extension."""
    with pytest.raises(OSError):
        data = Table.read('non-existing-file-with-unknown.ext')


def test_read_basic_table():
    data = np.array(list(zip([1, 2, 3], ['a', 'b', 'c'])),
                    dtype=[('A', int), ('B', '|U1')])
    io_registry.register_reader('test', Table, lambda x: Table(x))
    t = Table.read(data, format='test')
    assert t.keys() == ['A', 'B']
    for i in range(3):
        assert t['A'][i] == data['A'][i]
        assert t['B'][i] == data['B'][i]


def test_register_readers_with_same_name_on_different_classes():
    # No errors should be generated if the same name is registered for
    # different objects...but this failed under python3
    io_registry.register_reader('test', TestData, lambda: TestData())
    io_registry.register_reader('test', Table, lambda: Table())
    t = TestData.read(format='test')
    assert isinstance(t, TestData)
    tbl = Table.read(format='test')
    assert isinstance(tbl, Table)


def test_inherited_registration():
    # check that multi-generation inheritance works properly,
    # meaning that a child inherits from parents before
    # grandparents, see astropy/astropy#7156

    class Child1(Table):
        pass

    class Child2(Child1):
        pass

    def _read():
        return Table()

    def _read1():
        return Child1()

    # check that reader gets inherited
    io_registry.register_reader('test', Table, _read)
    assert io_registry.get_reader('test', Child2) is _read

    # check that nearest ancestor is identified
    # (i.e. that the reader for Child2 is the registered method
    #  for Child1, and not Table)
    io_registry.register_reader('test', Child1, _read1)
    assert io_registry.get_reader('test', Child2) is _read1


def teardown_function(function):
    _readers.clear()
    _writers.clear()
    _identifiers.clear()
    _readers.update(ORIGINAL['readers'])
    _writers.update(ORIGINAL['writers'])
    _identifiers.update(ORIGINAL['identifiers'])


class TestSubclass:
    """
    Test using registry with a Table sub-class
    """

    def test_read_table_subclass(self):
        class MyTable(Table):
            pass
        data = ['a b', '1 2']
        mt = MyTable.read(data, format='ascii')
        t = Table.read(data, format='ascii')
        assert np.all(mt == t)
        assert mt.colnames == t.colnames
        assert type(mt) is MyTable

    def test_write_table_subclass(self):
        buffer = StringIO()

        class MyTable(Table):
            pass
        mt = MyTable([[1], [2]], names=['a', 'b'])
        mt.write(buffer, format='ascii')
        assert buffer.getvalue() == os.linesep.join(['a b', '1 2', ''])

    def test_read_table_subclass_with_columns_attributes(self, tmpdir):
        """Regression test for https://github.com/astropy/astropy/issues/7181
        """

        class MTable(Table):
            pass

        mt = MTable([[1, 2.5]], names=['a'])
        mt['a'].unit = u.m
        mt['a'].format = '.4f'
        mt['a'].description = 'hello'

        testfile = str(tmpdir.join('junk.fits'))
        mt.write(testfile, overwrite=True)

        t = MTable.read(testfile)
        assert np.all(mt == t)
        assert mt.colnames == t.colnames
        assert type(t) is MTable
        assert t['a'].unit == u.m
        assert t['a'].format == '{:13.4f}'
        assert t['a'].description == 'hello'


def test_directory(tmpdir):

    # Regression test for a bug that caused the I/O registry infrastructure to
    # not work correctly for datasets that are represented by folders as
    # opposed to files, when using the descriptors to add read/write methods.

    io_registry.register_identifier('test_folder_format', TestData,
                                    lambda o, *x, **y: o == 'read')
    io_registry.register_reader('test_folder_format', TestData,
                                empty_reader)

    filename = tmpdir.mkdir('folder_dataset').strpath

    # With the format explicitly specified
    dataset = TestData.read(filename, format='test_folder_format')
    assert isinstance(dataset, TestData)

    # With the auto-format identification
    dataset = TestData.read(filename)
    assert isinstance(dataset, TestData)
