"""Custom fields for the WTForms library."""

from wtforms import FieldList, SelectField
from wtforms.fields import _unset_value


class FieldDict(FieldList):
    """Acts just like a FieldList, but works with a `dict` instead of
    a `list`.

    The `keys` of the `dict` are used as labels for the generated
    fields.

    Warning: the character '-' must not be used in the `keys` of the
    `dict` because it is already used to separate the parts of the
    names/ids of the form fields. This should be configurable but
    it would require a lot of changes in WTForms.
    """
    def __init__(self, unbound_field, label=None, validators=None,
                 min_entries=0, max_entries=None, default=dict, **kwargs):
        super(FieldDict, self).__init__(unbound_field, label,
                    validators, min_entries=min_entries,
                    max_entries=max_entries, default=default, **kwargs)

    def process(self, formdata, data=_unset_value):

        self.entries = []
        if data is _unset_value or not data:
            try:
                data = self.default()
            except TypeError:
                data = self.default

        self.object_data = data

        if formdata:
            indices = sorted(set(self._extract_indices(self.name, formdata)))
            if self.max_entries:
                indices = indices[:self.max_entries]

            idata = iter(data.items())
            for index in indices:
                try:
                    obj_data = next(idata)
                except StopIteration:
                    obj_data = _unset_value
                self._add_entry(formdata, obj_data, index=index)
        else:
            for obj_data in data.items():
                self._add_entry(formdata, obj_data)

        while len(self.entries) < self.min_entries:
            self._add_entry(formdata)

    def _extract_indices(self, prefix, formdata):
        offset = len(prefix) + 1
        for k in formdata:
            if k.startswith(prefix):
                k = k[offset:].split('-', 1)[0]
                yield k

    def _add_entry(self, formdata=None, data=_unset_value, index=None):
        assert not self.max_entries or len(self.entries) < self.max_entries, \
            'You cannot have more than max_entries entries in this FieldList'
        new_index, actual_data = data

        name = '{}-{}'.format(self.short_name, new_index)
        id = '{}-{}'.format(self.id, new_index)

        field = self.unbound_field.bind(label=new_index, form=None, name=name,
                                        prefix=self._prefix, id=id)
        field.process(formdata, actual_data)
        self.entries.append(field)
        return field


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
