from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test import TestCase, RequestFactory

from main.functions import create_by_shallow_copy, link_copy, deep_copy, delete_item, delete_deep
from main.models import CellModel, Component, Person


# class NamedCellMLEntity(DjangoModel):
#     # These are the dynamic parts of a model which can be changed by the users
#     name = CharField(blank=False, max_length=100)  # The name of the entity
#     ready = NullBooleanField()  # object in database has all fields completed TODO not working yet
#     notes = TextField(blank=True)
#     owner = ForeignKey('Person', blank=True, null=True, on_delete=SET_NULL)  # TODO set to admin
#     imported_from = ForeignKey('ImportedEntity', on_delete=SET_NULL, related_name="imported_%(class)s_objects",
#                                blank=True, null=True)
#
#     # CellML and libCellML fields:
#     cellml_id = CharField(blank=True, max_length=100)  # Mimics the cellml field 'id', not needed here
#     cellml_index = IntegerField(default=-1, null=True)  # the corresponding item index inside libcellml
#
#     class Meta:
#         abstract = True
#
#     def __str__(self):
#         return self.name


class CellModelTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='daffy', email='daffy@duck.com', password='top_secret')

        self.person = Person.objects.create(
            user=self.user,
            first_name="Daffy",
            last_name="Duck"
        )
        self.person.save()

        self.model = CellModel(
            name="model1",
            notes="notes go here",
            owner=self.person
        )
        self.model.save()

        self.component = Component(
            name="c1",
            owner=self.person
        )
        self.component.save()
        self.component.models.add(self.model)

    def test_name(self):
        m = CellModel.objects.get(name='model1')
        self.assertEqual(m.name, 'model1')

        self.assertEqual(self.model.name, "model1")

    def test_component(self):
        c = Component.objects.get(name="c1")
        self.assertEqual(c.models.all()[0].name, "model1")

    def test_model_create_by_shallow_copy(self):

        request = self.factory.get('/copy/cellmodel/{}'.format(self.model.id))
        request.user = self.user

        m2, m1 = create_by_shallow_copy(request, self.model)
        self.assertEqual(m1.name, m2.name)
        self.assertNotEqual(m1.imported_from, m2.imported_from)
        self.assertEqual(m1.components.count(), 1)
        self.assertEqual(m2.components.count(), 0)

    def test_model_create_by_link_copy(self):

        request = self.factory.get('/copy/cellmodel/{}'.format(self.model.id))
        request.user = self.user

        m2, m1 = create_by_shallow_copy(request, self.model)
        link_copy(request, m1, m2)

        self.assertEqual(m1.name, m2.name)
        self.assertEqual(m1.components.count(), 1)
        self.assertEqual(m2.components.count(), 1)
        self.assertEqual(m1.components.all()[0], m2.components.all()[0])

    def test_model_create_by_deep_copy(self):
        request = self.factory.get('/copy/cellmodel/{}'.format(self.model.id))
        request.user = self.user

        m2, m1 = create_by_shallow_copy(request, self.model)
        deep_copy(request, m1, m2)

        self.assertEqual(m1.name, m2.name)
        self.assertEqual(m1.components.count(), 1)
        self.assertEqual(m2.components.count(), 1)

        self.assertNotEqual(m1.components.all()[0], m2.components.all()[0])

    def test_model_delete_item(self):
        request = self.factory.get('/delete/cellmodel/{}'.format(self.model.id))
        request.user = self.user

        m2, m1 = create_by_shallow_copy(request, self.model)
        deep_copy(request, m1, m2)

        self.assertEqual(m1.name, m2.name)
        self.assertEqual(m1.components.count(), 1)
        self.assertEqual(m2.components.count(), 1)
        self.assertNotEqual(m1.components.all()[0], m2.components.all()[0])

        c2 = m2.components.all()

        delete_item(request, m2, 'base')

        self.assertEqual(Component.objects.count(), 2)
        self.assertEqual(CellModel.objects.count(), 1)
        self.assertEqual(c2[0].models, None)

        delete_item(request, c2[0], 'base')

        self.assertEqual(Component.objects.count(), 1)

    def test_model_delete_deep(self):
        request = self.factory.get('/delete/cellmodel/{}'.format(self.model.id))
        request.user = self.user

        m2, m1 = create_by_shallow_copy(request, self.model)
        deep_copy(request, m1, m2)

        self.assertEqual(m1.name, m2.name)
        self.assertEqual(m1.components.count(), 1)
        self.assertEqual(m2.components.count(), 1)
        self.assertNotEqual(m1.components.all()[0], m2.components.all()[0])

        c2 = m2.components.all()

        delete_item(request, m2, 'deep')

        self.assertEqual(Component.objects.count(), 1)
        self.assertEqual(CellModel.objects.count(), 1)












