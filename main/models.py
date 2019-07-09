# """
#     First go at getting CellML into a database structure.  This takes the current (24.6.19) object structure and
#     interprets it into a POSTGreSQL-friendly Django format.
#
# """
#
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import (IntegerField, ManyToManyField, FloatField, CharField, TextField, ForeignKey,
                              DO_NOTHING, NullBooleanField, URLField, FileField, CASCADE, OneToOneField, EmailField,
                              BooleanField)
from django.db.models import Model as DjangoModel


# -------------------- ABSTRACT MODELS --------------------

class NamedCellMLEntity(DjangoModel):
    # These are the dynamic parts of a model which can be changed by the users
    name = CharField(blank=False, max_length=100)  # The name of the entity
    ready = NullBooleanField()  # object in database has all fields completed TODO not working yet
    notes = TextField(blank=True)
    owner = ForeignKey('Person', blank=True, null=True, on_delete=DO_NOTHING)  # TODO give a default "owner"
    imported_from = ForeignKey('ImportedEntity', on_delete=DO_NOTHING,
                               related_name="imported_%(class)s_objects", blank=True, null=True)

    # CellML and libCellML fields:
    cellml_id = CharField(blank=True, max_length=100)  # Mimics the cellml field 'id', not needed here
    cellml_index = IntegerField(default=-1, null=True)  # the corresponding item index inside libcellml

    # cellml_code = TextField(blank=True)
    #       Raw XML field, useful for providing different options when creating/changing stuff
    # tree = TextField(blank=True)

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


class Prefix(DjangoModel):
    value = IntegerField(default=0)
    name = CharField(max_length=20)

    def __str__(self):
        return self.name


# --------------------- ITEM MODELS ---------------------

class ImportedEntity(DjangoModel):
    """
    This class allows models and parts of models to be imported into the database.  Importing will create an instance
    of the selected item(s) in the database, and return a reference to it.  It can then be accessed using the
    source_type, source_id combination.
    """
    source_type = CharField(max_length=100, null=True, blank=True)  # eg: Component, CompoundUnit etc
    source_reference = URLField(blank=True, null=True)  # eg: address of file which was imported to generate it
    source_id = IntegerField(default=-1, blank=True,
                             null=True)  # eg: The id of the item generated after import in *this* database
    attribution = TextField(blank=True, null=True)


class Variable(NamedCellMLEntity):
    INTERFACE_TYPE = [
        ("Public", "PU"),
        ("Private", "PR"),
        ("Public and private", "PP"),
        ("None", "NA")
    ]

    equivalent_variables = ManyToManyField("Variable", symmetrical=True, blank=True)

    initial_value = CharField(max_length=100, null=True)
    interface_type = CharField(max_length=2, choices=INTERFACE_TYPE, default="NA", null=True, blank=True)
    compoundunit = ForeignKey("CompoundUnit", related_name="variables", on_delete=DO_NOTHING, null=True, blank=True)
    component = ForeignKey("Component", related_name="variables", on_delete=DO_NOTHING, null=True, blank=True)

    def __str__(self):
        return self.name


class Unit(NamedCellMLEntity):
    prefix = ForeignKey("Prefix", on_delete=DO_NOTHING, null=True, blank=True)

    compoundunits = ManyToManyField("CompoundUnit", related_name="made_of", blank=True)

    multiplier = FloatField(default=0.0, null=True)
    exponent = FloatField(default=0.0, null=True)
    reference = CharField(max_length=100,
                          null=True)  # Reference is stored as a string, will be processed into fks below

    is_standard = BooleanField(default=False)
    based_on = ForeignKey("CompoundUnit", related_name='child_units', blank=True, null=True,
                          on_delete=DO_NOTHING)

    def __str__(self):
        return self.name

    def delete(self, args, kwargs):
        # prevent deleting if is standard
        if self.is_standard:
            return
        super.delete(args, kwargs)

    def is_base(self):
        if self.based_on is not None:
            return False
        return True


class CompoundUnit(NamedCellMLEntity):
    model = ForeignKey("CellModel", on_delete=CASCADE, related_name="compoundunits", blank=True, null=True)

    is_standard = BooleanField(default=False)

    def __str__(self):
        return self.name

    def delete(self, args, kwargs):
        # prevent deleting if is standard
        if self.is_standard:
            return
        super.delete(args, kwargs)


class Math(NamedCellMLEntity):
    model = ForeignKey("CellModel", on_delete=CASCADE, related_name="maths", null=True, blank=True)
    math_ml = TextField(blank=True)

    # TODO how to make a parent fk to *either*
    def __str__(self):
        return self.name


class Component(NamedCellMLEntity):
    model = ForeignKey("CellModel", null=True, on_delete=CASCADE, related_name="components")

    def __str__(self):
        return self.name


class Encapsulation(NamedCellMLEntity):
    pass


class Reset(NamedCellMLEntity):  # TODO should this be inherited or not?
    variable = ForeignKey("Variable", related_name="reset_variables", on_delete=DO_NOTHING, null=True, blank=True)
    test_variable = ForeignKey("Variable", related_name="reset_test_variables", on_delete=DO_NOTHING, null=True,
                               blank=True)
    order = IntegerField(default=0)
    reset_value = ForeignKey("Math", null=True, blank=True, on_delete=DO_NOTHING, related_name="reset_values")
    test_value = ForeignKey("Math", null=True, blank=True, on_delete=DO_NOTHING, related_name="test_values")
    component = ForeignKey("Component", null=True, blank=True, on_delete=CASCADE, related_name="resets")

    def __str__(self):
        return self.name


class CellModel(NamedCellMLEntity):
    pass

    def __str__(self):
        return self.name


class TemporaryStorage(DjangoModel):
    # This is the storage and reading of the initial cellml file
    file = FileField(blank=False)
    tree = TextField(blank=True)

# class TemporaryStorageItem(DjangoModel):
#     # this is a list of the identified entities (components, variable, units etc) in the file and their
#     # unique paths to retrieval
#     storage = ForeignKey(TemporaryStorage, on_delete=CASCADE, related_name='items')
#     dict_string = TextField(blank=True)
#
#     class Meta:
#         ordering = ['id']


# class Dictionary(DjangoModel):
#     """
#         A model that represents a dictionary. This model implements most of the dictionary interface,
#         allowing it to be used like a python dictionary.
#     """
#     name = CharField(max_length=255)
#
#     @staticmethod
#     def getDict(name):
#         """Get the Dictionary of the given name.
#
#         """
#         df = Dictionary.objects.select_related().get(name=name)
#
#         return df
#
#     def __getitem__(self, key):
#         """Returns the value of the selected key.
#
#         """
#         return self.keyvaluepair_set.get(key=key).value
#
#     def __setitem__(self, key, value):
#         """Sets the value of the given key in the Dictionary.
#
#         """
#         try:
#             kvp = self.keyvaluepair_set.get(key=key)
#
#         except KeyValuePair.DoesNotExist:
#             KeyValuePair.objects.create(container=self, key=key, value=value)
#
#         else:
#             kvp.value = value
#             kvp.save()
#
#     def __delitem__(self, key):
#         """Removed the given key from the Dictionary.
#
#         """
#         try:
#             kvp = self.keyvaluepair_set.get(key=key)
#
#         except KeyValuePair.DoesNotExist:
#             raise KeyError
#
#         else:
#             kvp.delete()
#
#     def __len__(self):
#         """Returns the length of this Dictionary.
#
#         """
#         return self.keyvaluepair_set.count()
#
#     def iterkeys(self):
#         """Returns an iterator for the keys of this Dictionary.
#
#         """
#         return iter(kvp.key for kvp in self.keyvaluepair_set.all())
#
#     def itervalues(self):
#         """Returns an iterator for the keys of this Dictionary.
#
#         """
#         return iter(kvp.value for kvp in self.keyvaluepair_set.all())
#
#     __iter__ = iterkeys
#
#     def iteritems(self):
#         """Returns an iterator over the tuples of this Dictionary.
#
#         """
#         return iter((kvp.key, kvp.value) for kvp in self.keyvaluepair_set.all())
#
#     def keys(self):
#         """Returns all keys in this Dictionary as a list.
#
#         """
#         return [kvp.key for kvp in self.keyvaluepair_set.all()]
#
#     def values(self):
#         """Returns all values in this Dictionary as a list.
#
#         """
#         return [kvp.value for kvp in self.keyvaluepair_set.all()]
#
#     def items(self):
#         """Get a list of tuples of key, value for the items in this Dictionary.
#         This is modeled after dict.items().
#
#         """
#         return [(kvp.key, kvp.value) for kvp in self.keyvaluepair_set.all()]
#
#     def get(self, key, default=None):
#         """Gets the given key from the Dictionary. If the key does not exist, it
#         returns default.
#
#         """
#         try:
#             return self[key]
#
#         except KeyError:
#             return default
#
#     def has_key(self, key):
#         """Returns true if the Dictionary has the given key, false if not.
#
#         """
#         return self.contains(key)
#
#     def contains(self, key):
#         """Returns true if the Dictionary has the given key, false if not.
#
#         """
#         try:
#             self.keyvaluepair_set.get(key=key)
#             return True
#
#         except KeyValuePair.DoesNotExist:
#             return False
#
#     def clear(self):
#         """Deletes all keys in the Dictionary.
#
#         """
#         self.keyvaluepair_set.all().delete()
#
#     def __str__(self):
#         return str(self.asPyDict())
#
#     def asPyDict(self):
#         """Get a python dictionary that represents this Dictionary object.
#         This object is read-only.
#
#         """
#         fieldDict = dict()
#
#         for kvp in self.keyvaluepair_set.all():
#             fieldDict[kvp.key] = kvp.value
#
#         return fieldDict
#
#
# class KeyValuePair(DjangoModel):
#     """A Key-Value pair with a pointer to the Dictionary that owns it.
#
#     """
#     container = ForeignKey('Dictionary', db_index=True, on_delete=DO_NOTHING)
#     key = CharField(max_length=240, db_index=True)
#     value = TextField(db_index=True)
#
#
# class TempSpreadsheet(DjangoModel):
#     fields = OneToOneField(Dictionary,
#                            on_delete=CASCADE)  # Delete fields when parent Dictionary is deleted
#     app_name = CharField(max_length=100)
#     model_name = CharField(max_length=100)
#
#     def __str__(self):
#         return "Temporary storage"
#
#
# class TempRow(DjangoModel):
#     row_index = IntegerField()
#     spreadsheet = ForeignKey('TempSpreadsheet', related_name='rows', on_delete=DO_NOTHING)
#     data = OneToOneField('Dictionary', on_delete=CASCADE)  # Delete data when parent Dictionary is deleted
#     message = TextField(default="")
#
#     def __str__(self):
#         return "Row {}".format(self.row_index)
