
from unittest import TestCase

from wtforms.fields import TextField, FormField
from wtforms.form import Form
from wtforms import validators
from wtforms_morefields import FieldDict


class DummyPostData(dict):
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


class AttrDict(object):
    def __init__(self, *args, **kw):
        self.__dict__.update(*args, **kw)


def make_form(_name='F', **fields):
    return type(str(_name), (Form, ), fields)


class TestFieldDict(TestCase):
    t = TextField(validators=[validators.Required()])

    def test_form(self):
        F = make_form(a=FieldDict(self.t))
        data = {'foo': 'fooval', 'hi': 'hival', 'rawr': 'rawrval'}
        a = F(a=data).a
        self.assertEqual(a.entries[1].data, 'hival')
        self.assertEqual(a.entries[1].name, 'a-hi')
        self.assertEqual(a.data, data)
        self.assertEqual(len(a.entries), 3)

        pdata = DummyPostData({'a-bleh': ['blehval'],
                               'a-yarg': ['yargval'],
                               'a-e': [''],
                               'a-mmm': ['mmmval']})
        form = F(pdata)
        self.assertEqual(len(form.a.entries), 4)
        self.assertEqual(form.a.data, {'bleh': 'blehval', 'yarg': 'yargval',
                                       'e': '', 'mmm': 'mmmval'})
        self.assertFalse(form.validate())

        form = F(pdata, a=data)
        self.assertEqual(form.a.data, {'bleh': 'blehval', 'yarg': 'yargval',
                                       'e': '', 'mmm': 'mmmval'})
        self.assertFalse(form.validate())

        # Test for formdata precedence
        pdata = DummyPostData({'a-a': ['a'], 'a-b': ['b']})
        form = F(pdata, a=data)
        self.assertEqual(len(form.a.entries), 2)
        self.assertEqual(form.a.data, {'a': 'a', 'b': 'b'})

    def test_enclosed_subform(self):
        make_inner = lambda: AttrDict(a=None)
        F = make_form(
            a=FieldDict(FormField(make_form('FChild', a=self.t),
                                  default=make_inner))
        )
        data = {'stuff': {'a': 'hella'}}
        form = F(a=data)
        self.assertEqual(form.a.data, data)
        self.assertTrue(form.validate())

        self.assertRaises(TypeError, form.a.append_entry)
        self.assertRaises(TypeError, form.a.append_entry, {})

        pdata = DummyPostData({'a-0': ['fake'],
                               'a-0-a': ['foo'],
                               'a-1-a': ['bar']})
        form = F(pdata, a=data)
        self.assertEqual(form.a.data, {'0': {'a': 'foo'}, '1': {'a': 'bar'}})

        inner_obj = make_inner()
        inner_dict = {'0': inner_obj}
        obj = AttrDict(a=inner_dict)
        form.populate_obj(obj)
        self.assertEqual(len(obj.a), 2)
        self.assertTrue(obj.a['0'] is inner_obj)
        self.assertEqual(obj.a['0'].a, 'foo')
        self.assertEqual(obj.a['1'].a, 'bar')

    def test_entry_management(self):
        # The order of the entries cannot be predicted for now
        F = make_form(a=FieldDict(self.t))
        a = F(a={'0': 'hello', '1': 'bye'}).a
        popped = a.pop_entry()
        self.assertIn(popped.name, ['a-0', 'a-1'])
        if popped.name == 'a-0':
            self.assertEqual(a.data, {'1': 'bye'})
        elif popped.name == 'a-1':
            self.assertEqual(a.data, {'0': 'hello'})
        a.pop_entry()
        self.assertRaises(IndexError, a.pop_entry)

