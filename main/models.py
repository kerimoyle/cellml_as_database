# """
#     First go at getting CellML into a database structure.  This takes the current (24.6.19) object structure and
#     interprets it into a POSTGreSQL-friendly Django format.
#
# """
#
import os

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import (IntegerField, ManyToManyField, CharField, TextField, ForeignKey,
                              NullBooleanField, URLField, FileField, CASCADE, OneToOneField, EmailField,
                              BooleanField, SET_NULL)
from django.db.models import Model as DjangoModel
# -------------------- ABSTRACT MODELS --------------------
from django.db.models.signals import post_delete
from django.dispatch import receiver


class NamedCellMLEntity(DjangoModel):
    PRIVACY_LEVELS = [
        ("Everyone", "Everyone"),
        ("Only me", "Only me"),
    #     ("Selected ", "SU"),
    ]

    # These are the dynamic parts of a model which can be changed by the users
    name = CharField(blank=False, max_length=100)  # The name of the entity
    ready = NullBooleanField()  # object in database has all fields completed TODO not working yet
    privacy = CharField(max_length=9, choices=PRIVACY_LEVELS, default="Only me", null=True, blank=True)
    notes = TextField(blank=True)
    owner = ForeignKey('Person', blank=True, null=True, on_delete=SET_NULL)  # TODO set to admin
    imported_from = ForeignKey('ImportedEntity', on_delete=SET_NULL, related_name="imported_%(class)s_objects",
                               blank=True, null=True)

    # CellML and libCellML fields:
    cellml_id = CharField(blank=True, max_length=100)  # Mimics the cellml field 'id', not needed here
    cellml_index = IntegerField(default=-1, null=True)  # the corresponding item index inside libcellml

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    # def is_visible_to_user(self, person):
    #     return self.privacy == 2 or self.owner == person


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


# --------------------- ITEM MODELS ---------------------

class ImportedEntity(DjangoModel):
    """
    This class allows models and parts of models to be imported into the database.  Importing will create an instance
    of the selected item(s) in the database, and return a reference to it.  It can then be accessed using the
    source_type, source_id combination.
    """
    source_type = CharField(max_length=100, null=True, blank=True)  # eg: Component, CompoundUnit etc
    source_reference = URLField(blank=True, null=True)  # eg: TODO address of file which was imported to generate it
    source_id = IntegerField(default=-1, blank=True,
                             null=True)  # eg: The id of the item generated after import in *this* database
    attribution = TextField(blank=True, null=True)  # the original attribution field

    def __str__(self):
        return self.attribution


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

    component = ForeignKey("Component", related_name="variables", blank=True, null=True, on_delete=SET_NULL)

    def __str__(self):
        return self.name


def get_default_prefix():
    p = Prefix.objects.get(name="")
    return p.id


class Unit(NamedCellMLEntity):
    prefix = ForeignKey("Prefix", on_delete=get_default_prefix, default=get_default_prefix)

    parent_cu = ForeignKey("CompoundUnit", related_name='product_of', blank=True, null=True, on_delete=SET_NULL)
    child_cu = ForeignKey("CompoundUnit", related_name='part_of', blank=True, null=True, on_delete=SET_NULL)

    multiplier = IntegerField(default=1, null=True)
    exponent = IntegerField(default=1, null=True)
    reference = CharField(max_length=100, null=True, blank=True)


class CompoundUnit(NamedCellMLEntity):
    models = ManyToManyField("CellModel", related_name="compoundunits", blank=True)
    is_standard = BooleanField(default=False)
    symbol = CharField(max_length=100, null=True, blank=True)
    variables = ManyToManyField("Variable", related_name="compoundunits", blank=True)

    def __str__(self):
        return "{n}".format(n=self.name)

    def save(self, *args, **kwargs):
        # If there is no symbol defined for this compound unit then use the product of the children
        if self.symbol is None and self.product_of.count() != 0:
            # Create from amalgamation of children
            self.symbol = "("

            for unit in self.product_of.all():
                if unit.child_cu is None:
                    continue
                else:
                    my_symbol = ""
                    if unit.prefix is not None:
                        my_symbol += unit.prefix.symbol
                    if unit.child_cu.symbol:
                        my_symbol += unit.child_cu.symbol
                    if unit.exponent != 1:
                        my_symbol += "<sup>{}</sup>".format(unit.exponent)
                    self.symbol = "{}{}".format(self.symbol, my_symbol)

            self.symbol = "{})".format(self.symbol)

        super(CompoundUnit, self).save(args, kwargs)

    def delete(self, *args, **kwargs):
        # prevent deleting if is standard
        if self.is_standard:
            return "Could not delete Compound Unit '{}' because it is built-in.".format(self.name)
        super(CompoundUnit, self).delete(args, kwargs)


class Math(NamedCellMLEntity):
    components = ManyToManyField("Component", related_name="maths", blank=True)
    math_ml = TextField(blank=True)

    # TODO how to make a parent fk to *either* model or reset?
    def __str__(self):
        return self.name


class Component(NamedCellMLEntity):
    models = ManyToManyField("CellModel", blank=True, related_name="components")

    def __str__(self):
        return self.name


class Encapsulation(NamedCellMLEntity):
    pass


class Reset(NamedCellMLEntity):  # TODO should this be inherited or not?
    variable = ForeignKey("Variable", related_name="reset_variables", on_delete=SET_NULL, null=True, blank=True)
    test_variable = ForeignKey("Variable", related_name="reset_test_variables", on_delete=SET_NULL, null=True,
                               blank=True)
    order = IntegerField(default=0)
    reset_value = ForeignKey("Math", null=True, blank=True, on_delete=SET_NULL, related_name="reset_values")
    test_value = ForeignKey("Math", null=True, blank=True, on_delete=SET_NULL, related_name="test_values")
    component = ForeignKey("Component", null=True, blank=True, on_delete=CASCADE, related_name="resets")

    def __str__(self):
        return self.name


class CellModel(NamedCellMLEntity):
    uploaded_from = CharField(max_length=250, blank=True, null=True)
    pass

    def __str__(self):
        return self.name


class TemporaryStorage(DjangoModel):
    # This is the storage and reading of the initial cellml file
    file = FileField(blank=False)
    tree = TextField(blank=True)
    model_name = CharField(blank=False, max_length=100)
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

# @receiver(pre_save, sender=TemporaryStorage)
# def auto_delete_file_on_change(sender, instance, **kwargs):
#     """
#     Deletes old file from filesystem
#     when corresponding `MediaFile` object is updated
#     with new file.
#     """
#     if not instance.pk:
#         return False
#
#     try:
#         old_file = sender.objects.get(pk=instance.pk).file
#     except sender.DoesNotExist:
#         return False
#
#     new_file = instance.file
#     if not old_file == new_file:
#         if os.path.isfile(old_file.path):
#             os.remove(old_file.path)

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
