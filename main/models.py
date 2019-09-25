# """
#     First go at getting CellML into a database structure.  This takes the current (24.6.19) object structure and
#     interprets it into a POSTGreSQL-friendly Django format.
#
# """
#
import os

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db.models import (IntegerField, ManyToManyField, CharField, TextField, ForeignKey,
                              NullBooleanField, URLField, FileField, CASCADE, OneToOneField, EmailField,
                              BooleanField, SET_NULL, ManyToOneRel, ManyToManyRel, DO_NOTHING, DateTimeField,
                              FloatField)
from django.db.models import Model as DjangoModel
# -------------------- ABSTRACT MODELS --------------------
from django.db.models.signals import post_delete
from django.dispatch import receiver


class NamedCellMLEntity(DjangoModel):
    PRIVACY_LEVELS = [
        ("Public", "Public"),
        ("Private", "Private"),
        #     ("Selected ", "SU"),
    ]

    # These are the dynamic parts of a model which can be changed by the users
    name = CharField(blank=False, max_length=100)  # The name of the entity
    # ready = NullBooleanField()  # object in database has all fields completed TODO not working yet
    privacy = CharField(max_length=9, choices=PRIVACY_LEVELS, default="private", null=True, blank=True)
    notes = TextField(blank=True)
    owner = ForeignKey('Person', blank=True, null=True, on_delete=SET_NULL)  # TODO set to admin
    annotations = ManyToManyField('Annotation', blank=True, related_name="used_by_%(class)s_objects")

    # CellML and libCellML fields:
    cellml_id = CharField(blank=True, max_length=100)  # Mimics the cellml field 'id', not really needed here
    cellml_index = IntegerField(default=-1, null=True)  # The corresponding item index as read by libCellML

    # Validation and error checking fields
    is_valid = NullBooleanField()
    last_checked = DateTimeField(blank=True, null=True)
    errors = ManyToManyField('ItemError', blank=True, related_name="error_in_%(class)s_objects")
    # This is the list of all downstream errors from this object, it's expensive to build so will update when asked
    error_tree = JSONField(blank=True, null=True)
    child_list = JSONField(blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


# -------------------- UTILITY MODELS ---------------------

class Person(DjangoModel):
    first_name = CharField(max_length=100)
    last_name = CharField(max_length=100)
    user = OneToOneField(User, related_name="person", on_delete=CASCADE)
    email = EmailField(blank=True)

    def __str__(self):
        return "{} {}".format(self.first_name, self.last_name)


class Prefix(DjangoModel):
    value = IntegerField(default=0)
    name = CharField(max_length=20)
    symbol = CharField(max_length=10)

    def __str__(self):
        return self.name


class ItemError(DjangoModel):
    hints = TextField(blank=True)
    spec = CharField(max_length=25, null=True, blank=True)
    # The 'fields' field collects names of the type of item so that the display pages know
    # which attribute lines to label with this error

    fields = ArrayField(
        CharField(max_length=50),
        null=True, blank=True
    )


class CellMLSpecification(DjangoModel):
    notes = TextField(null=True, blank=True)
    code = CharField(max_length=25, null=True, blank=True)


# --------------------- ITEM MODELS ---------------------


class Annotation(DjangoModel):
    name = TextField(blank=True, null=True)
    code = CharField(max_length=100, blank=True, null=True)
    source = URLField(blank=True, null=True)


class Variable(NamedCellMLEntity):
    INTERFACE_TYPE = [
        ("Public", "PU"),
        ("Private", "PR"),
        ("Public and private", "PP"),
        ("None", "NA")
    ]

    equivalent_variables = ManyToManyField("Variable", symmetrical=True, blank=True)

    initial_value_constant = FloatField(null=True, blank=True)
    initial_value_variable = ForeignKey('Variable', related_name='will_initialise', on_delete=DO_NOTHING, null=True,
                                        blank=True)
    compoundunit = ForeignKey("CompoundUnit", related_name='variables', blank=True, null=True, on_delete=DO_NOTHING)

    interface_type = CharField(max_length=2, choices=INTERFACE_TYPE, default="NA", null=True, blank=True)
    component = ForeignKey("Component", related_name="variables", blank=True, null=True, on_delete=SET_NULL)

    # import tracking fields
    imported_from = ForeignKey('Variable', related_name='imported_to', on_delete=DO_NOTHING, blank=True, null=True)
    depends_on = ForeignKey('Variable', related_name='used_by', on_delete=DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return "{} ({})".format(self.name, self.component.name)


def get_default_prefix():
    p = Prefix.objects.get(name="")
    return p.id


class Unit(NamedCellMLEntity):
    prefix = ForeignKey("Prefix", on_delete=get_default_prefix, default=get_default_prefix)

    parent_cu = ForeignKey("CompoundUnit", related_name='product_of', blank=True, null=True, on_delete=SET_NULL)
    child_cu = ForeignKey("CompoundUnit", related_name='part_of', blank=True, null=True, on_delete=SET_NULL)

    multiplier = FloatField(default=1.0, null=True)
    exponent = IntegerField(default=1, null=True)
    reference = CharField(max_length=100, null=True, blank=True)

    imported_from = ForeignKey('Unit', related_name='imported_to', on_delete=DO_NOTHING, blank=True, null=True)
    depends_on = ForeignKey('Unit', related_name='used_by', on_delete=DO_NOTHING, blank=True, null=True)

    # TODO should we override the save() method here to update symbols of parent compoundunits?

    def __str__(self):
        m = "" if self.multiplier == 1.0 else "({})".format(self.multiplier)
        c = self.child_cu.name if self.child_cu.symbol is None or self.child_cu.symbol == "" else self.child_cu.symbol
        e = "^{}".format(self.exponent) if self.exponent != 1 else ""
        return "{m}{p}{c}{e}".format(m=m, p=self.prefix.symbol, c=c, e=e)


class CompoundUnit(NamedCellMLEntity):
    models = ManyToManyField("CellModel", related_name="compoundunits", blank=True)
    is_standard = BooleanField(default=False)
    symbol = CharField(max_length=100, null=True, blank=True)

    imported_from = ForeignKey('CompoundUnit', related_name='imported_to', on_delete=DO_NOTHING, blank=True, null=True)
    depends_on = ForeignKey('CompoundUnit', related_name='used_by', on_delete=DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return "{n}".format(n=self.name)

    def save(self, *args, **kwargs):
        # If there is no symbol defined for this compound unit then use the product of the children
        self.update_symbol()
        super(CompoundUnit, self).save(args, kwargs)

    def delete(self, *args, **kwargs):
        # prevent deleting if is standard
        if self.is_standard:
            return "Could not delete Compound Unit '{}' because it is built-in.".format(self.name)
        super(CompoundUnit, self).delete(args, kwargs)

    def update_symbol(self):
        if (self.symbol == "" or self.symbol is None) and self.product_of.count() != 0:
            # Create from amalgamation of children
            # self.symbol = "("

            for unit in self.product_of.all():
                if unit.child_cu is None:
                    continue
                else:
                    unit.child_cu.update_symbol()
                    my_symbol = ""
                    if unit.prefix != "":
                        my_symbol += unit.prefix.symbol
                    if unit.child_cu.symbol:
                        my_symbol += "({})".format(unit.child_cu.symbol)
                    if unit.exponent != 1:
                        my_symbol += "<sup>{}</sup>".format(unit.exponent)
                    if self.symbol:
                        self.symbol = "{}.{}".format(self.symbol, my_symbol)
                    else:
                        self.symbol = "{}".format(my_symbol)

            # self.symbol = "{})".format(self.symbol)
        elif self.symbol == "" or self.symbol is None:
            self.symbol = self.name

        super(CompoundUnit, self).save()
        return self.symbol


class Math(NamedCellMLEntity):
    components = ManyToManyField("Component", related_name="maths", blank=True)
    math_ml = TextField(blank=True, null=True)

    imported_from = ForeignKey('Math', related_name='imported_to', on_delete=DO_NOTHING, blank=True, null=True)
    depends_on = ForeignKey('Math', related_name='used_by', on_delete=DO_NOTHING, blank=True, null=True)

    # TODO how to make a parent fk to *either* model or reset - should be generic fk?
    def __str__(self):
        return self.name


class Component(NamedCellMLEntity):
    model = ForeignKey("CellModel", blank=True, related_name="all_components", on_delete=DO_NOTHING, null=True)

    # These fields represents the effects of encapsulation
    parent_component = ForeignKey('Component', related_name='child_components', on_delete=DO_NOTHING, blank=True,
                                  null=True)
    parent_model = ForeignKey("CellModel", blank=True, related_name="encapsulated_components", on_delete=DO_NOTHING,
                              null=True)

    imported_from = ForeignKey('Component', related_name='imported_to', on_delete=DO_NOTHING, blank=True, null=True)
    depends_on = ForeignKey('Component', related_name='used_by', on_delete=DO_NOTHING, blank=True, null=True)

    def __str__(self):
        if self.child_components.count():
            return "{} (encapsulates {} components)".format(self.name, self.child_components.count())
        return self.name


class Encapsulation(NamedCellMLEntity):
    imported_from = ForeignKey('Encapsulation', related_name='imported_to', on_delete=DO_NOTHING, blank=True, null=True)
    depends_on = ForeignKey('Encapsulation', related_name='used_by', on_delete=DO_NOTHING, blank=True, null=True)


class Reset(NamedCellMLEntity):  # TODO should this be inherited or not?
    variable = ForeignKey("Variable", related_name="reset_variables", on_delete=SET_NULL, null=True, blank=True)
    test_variable = ForeignKey("Variable", related_name="reset_test_variables", on_delete=SET_NULL, null=True,
                               blank=True)
    order = IntegerField(blank=True, null=True)
    reset_value = ForeignKey("Math", null=True, blank=True, on_delete=SET_NULL, related_name="reset_values")
    test_value = ForeignKey("Math", null=True, blank=True, on_delete=SET_NULL, related_name="test_values")
    component = ForeignKey("Component", null=True, blank=True, on_delete=CASCADE, related_name="resets")

    imported_from = ForeignKey('Reset', related_name='imported_to', on_delete=DO_NOTHING, blank=True, null=True)
    depends_on = ForeignKey('Reset', related_name='used_by', on_delete=DO_NOTHING, blank=True, null=True)

    def __str__(self):
        c = "None"
        v = "None"
        if self.component:
            c = self.component.name
        if self.variable:
            v = self.variable.name

        return "{r} ({c}, {v})".format(r=self.name, c=c, v=v)


class CellModel(NamedCellMLEntity):
    uploaded_from = CharField(max_length=250, blank=True, null=True)
    imported_from = ForeignKey('CellModel', related_name='imported_to', on_delete=DO_NOTHING, blank=True, null=True)
    depends_on = ForeignKey('CellModel', related_name='used_by', on_delete=DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return self.name


class TemporaryStorage(DjangoModel):
    # This is the storage and reading of the initial cellml file
    file = FileField(blank=False)
    tree = TextField(blank=True)
    owner = ForeignKey(Person, related_name="stored_files", on_delete=CASCADE, null=True, blank=True)


@receiver(post_delete, sender=TemporaryStorage)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `FileField` object is deleted.
    """
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)


def get_parent_fields_for_model(item_model):
    parent_fields = [x.name for x in item_model.model_class()._meta.get_fields(include_parents=False) if
                     type(x) == ManyToOneRel or type(x) == ManyToManyRel]

    return parent_fields


def get_item_parent_attributes_for_model(item):
    parent_fields = get_parent_fields_for_model(ContentType.objects.get_for_model(item))

    item_parents = []

    for l in parent_fields:
        m2m = getattr(item, l)
        m2m_2 = getattr(m2m, 'all')()
        for m in m2m_2:
            item_parents.append(m)

    return item_parents
