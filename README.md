
# WTForms-MoreFields

This is just a collection of useful fields that are not present in
WTForms. For now, it only contains:

* `FieldDict`: used like `FieldList`, but takes a `dict` instead of a `list`.
* `SelectObjectField`: used like `SelectField`, but is able to display a
  list of objects.

## Usage

    from wtforms_morefields import FieldDict, SelectObjectField

    class AForm(Form):
        attributes = FieldDict(StringField())

    def aview():
        attributes = {'anattribute': 'avalue',
                      'anotherattribute': 'anothervalue'}
        resource = {'attributes': attributes}
        form = AForm(obj=resource)


    class AnotherForm(Form):
        # `idprop` is the name of the unique identifier property of
        # the objects.
        # `labelprop` is the name of the property used to display the
        # objects in the select.
        myselect = SelectObjectField('Options', choices=a_list_of_objects,
                                     idprop='id', labelprop='name')


## Notes

In `FieldDict`, the `dict` keys are used as labels for the generated
fields. It suits my use case, but I'm not sure this is the best way
to do it.


