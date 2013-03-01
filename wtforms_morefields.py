"""Custom fields for the WTForms library."""

import itertools

from wtforms import FieldList, SelectField, BooleanField
from wtforms.fields import _unset_value
from wtforms.compat import izip


class FieldDict(FieldList):
    """Acts just like a FieldList, but works with a `dict` instead of
    a `list`. Also, it wouldn't make sense to have `min_entries` and
    `max_entries` params, so they are not provided.

    The `keys` of the `dict` are used as labels for the generated
    fields.

    Warning: the character '-' must not be used in the `keys` of the
    `dict` because it is already used to separate the parts of the
    names/ids of the form fields. This should be configurable but
    it would require a lot of changes in WTForms.
    """
    def __init__(self, unbound_field, label=None, validators=None,
                 default=dict, **kwargs):
        super(FieldDict, self).__init__(unbound_field, label,
                    validators, min_entries=0, max_entries=None,
                    default=default, **kwargs)

    def process(self, formdata, data=_unset_value):

        self.entries = []
        if data is _unset_value or not data:
            try:
                data = self.default()
            except TypeError:
                data = self.default

        self.object_data = data

        if formdata:
            # Union with data.keys() because unchecked checkboxes are
            # not sent in the request. If we only take indices in the
            # formdata, unchecked checkboxes will simply not be present
            # in the resulting form.
            indices = sorted(set(self._extract_indices(self.name, formdata)) |
                             set(data.keys()))

            for index in indices:
                try:
                    obj_data = data[index]
                except KeyError:
                    obj_data = _unset_value
                self._add_entry(formdata, obj_data, index=index)
        else:
            for index, obj_data in data.items():
                self._add_entry(formdata, obj_data, index)

    def _extract_indices(self, prefix, formdata):
        offset = len(prefix) + 1
        for k in formdata:
            if k.startswith(prefix):
                k = k[offset:].split('-', 1)[0]
                yield k

    def _add_entry(self, formdata=None, data=_unset_value, index=None):
        name = '{}-{}'.format(self.short_name, index)
        id = '{}-{}'.format(self.id, index)

        field = self.unbound_field.bind(label=index, form=None, name=name,
                                        prefix=self._prefix, id=id)
        field.process(formdata, data)
        self.entries.append(field)
        return field

    def append_entry(self, data=None):
        if not data:
            raise TypeError('To add an entry to a FieldDict, you must at ' \
                            'least provide a valid `dict`, containing at ' \
                            'least one key.')
        return self._add_entry(data=data)

    def populate_obj(self, obj, name):
        dic = getattr(obj, name, {})
        _fake = type(str('_fake'), (object, ), {})

        for field in self.entries:
            id = self._extract_entry_id(field)
            fake_obj = _fake()
            fake_obj.data = dic.get(id, None)
            field.populate_obj(fake_obj, 'data')
            dic[id] = fake_obj.data

    @property
    def data(self):
        return {self._extract_entry_id(e): e.data for e in self.entries}

    def _extract_entry_id(self, entry):
        offset = len(self.name) + 1
        return entry.id[offset:]


class SelectObjectField(SelectField):
    """Automatically present a list of objects in a WTForms `SelectField`.

    >>> myoptions = [MyOption(pk=44, name='Option 44')]
    >>> options = SelectObjectField('My Options', choices=myoptions,
                                    idprop='pk', labelprop='name')

    :param choices:
        List of objects to display.
    :param idprop:
        Name of the unique identifier property of the object.
    :param label:
        Name of the property of the object used to display it.
    """
    def __init__(self, label=None, validators=None, choices=None,
                 idprop='id', labelprop='label', **kwargs):
        super(SelectField, self).__init__(label, validators, **kwargs)
        self.idprop = idprop
        self.labelprop = labelprop
        self.choices = {getattr(c, self.idprop): c for c in choices}

    def iter_choices(self):
        for key, obj in self.choices.items():
            label = getattr(obj, self.labelprop)
            selected = (key == getattr(self.data, self.idprop))
            yield (key, label, selected)

    def process_data(self, obj):
        self.data = obj

    def process_formdata(self, keylist):
        if keylist:
            try:
                self.data = self.choices[keylist[0]]
            except KeyError:
                raise ValueError(self.gettext(u'Invalid Choice: could \
                                 not find the object.'))

    def pre_validate(self, form):
        for obj in self.choices.values():
            if self.data == obj:
                break
        else:
            raise ValueError(self.gettext(u'Not a valid choice'))


class PersistentBooleanField(BooleanField):
    """This is a variant of BooleanField meant to overcome the problem
    of unchecked checkboxes not being sent in the request.

    The default behaviour of browsers is to ignore checkboxes that are
    not checked and to send only the checked ones. The problems is
    that when we try to merge the data from the incoming form and the
    data from the original object, these fields are ignored and not
    added to the resulting form.
    """

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = valuelist[0]
        # If we get here, that means a form was submitted but didn't
        # contain this field. We assume this checkbox was unchecked and
        # store the default data accordingly.
        else:
            self.data = False
