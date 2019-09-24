from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory

from main.copy import copy_and_link_component, copy_and_link_variable, copy_and_link_model
from main.models import CellModel, Component, Person, CompoundUnit, Variable, Reset


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

        self.cu1 = CompoundUnit(
            name="cu1",
            owner=self.person,
        )
        self.cu1.save()
        self.cu1.models.add(self.model)

        self.cu2 = CompoundUnit(
            name="cu2",
            owner=self.person
        )
        self.cu2.save()
        self.cu2.models.add(self.model)

        self.c1 = Component(
            name="c1",
            owner=self.person,
            model=self.model
        )
        self.c1.save()

        self.v1a = Variable(
            name="v1a",
            owner=self.person,
            component=self.c1,
            compoundunit=self.cu1
        )
        self.v1a.save()

        self.v1b = Variable(
            name="v1b",
            owner=self.person,
            component=self.c1,
            compoundunit=self.cu2
        )
        self.v1b.save()

        self.c2 = Component(
            name="c2",
            owner=self.person,
            model=self.model
        )
        self.c2.save()

        self.v2a = Variable(
            name="v2a",
            owner=self.person,
            component=self.c2,
            compoundunit=self.cu1
        )
        self.v2a.save()
        self.v2a.equivalent_variables.add(self.v1a)

        self.v2b = Variable(
            name="v2b",
            owner=self.person,
            component=self.c2,
            compoundunit=self.cu2
        )
        self.v2b.save()

        self.r1 = Reset(
            variable=self.v1a,
            component=self.c1,
            test_variable=self.v1b,
            order=1
        )
        self.r1.save()

        self.model.save()

    # def test_name(self):
    #     m = CellModel.objects.get(name='model1')
    #
    #     self.assertEqual(m.name, 'model1')
    #     self.assertEqual(self.model.name, "model1")
    #
    # def test_component(self):
    #     m = CellModel.objects.get(name='model1')
    #     c = Component.objects.get(name="c1")
    #
    #     self.assertEqual(c.model.name, m.name)
    #     self.assertEqual(m.all_components.all()[0], c)
    #     self.assertEqual(c.model, m)

    def test_copy_variable(self):
        person = Person.objects.all()[0]
        m1 = CellModel.objects.get(name='model1')
        c1 = m1.all_components.filter(name='c1').first()
        v1 = c1.variables.filter(name='v1a').first()

        v1_copy = copy_and_link_variable(v1, c1, person, False)

        self.assertEqual(v1.compoundunit.name, v1_copy.compoundunit.name)

        self.assertEqual(v1.component.name, v1_copy.component.name)
        self.assertEqual(v1.equivalent_variables.count(), 1)
        self.assertEqual(v1_copy.equivalent_variables.count(), 1)
        self.assertEqual(v1.equivalent_variables.all()[0].name, v1_copy.equivalent_variables.all()[0].name)

    def test_copy_component(self):
        person = Person.objects.all()[0]
        m1 = CellModel.objects.get(name='model1')
        c1 = m1.all_components.filter(name='c1').first()

        c1copy = copy_and_link_component(c1, m1, m1, person, False)
        # Have to add _copy to the un-copied one in order to compare the names because of the False in the call above
        list1 = set([("{}_copy".format(x[0]), x[1]) for x in c1.variables.values_list('name', 'compoundunit__name')])
        list2 = set([(x[0], x[1]) for x in c1copy.variables.values_list('name', 'compoundunit__name')])
        self.assertEqual(list1, list2)

        list1 = set(
            [("{}_copy".format(x[0]), "{}_copy".format(x[1]), x[2]) for x in
             c1.resets.values_list('variable__name', 'test_variable__name', 'order')]
        )
        list2 = set(
            [(x[0], x[1], x[2]) for x in c1copy.resets.values_list('variable__name', 'test_variable__name', 'order')]
        )
        self.assertEqual(list1, list2)

        # Removing _copy from the names so we can compare directly
        c2copy = copy_and_link_component(c1, m1, m1, person, True)
        list1 = set([(x[0], x[1]) for x in c1.variables.values_list('name', 'compoundunit__name')])
        list2 = set([(x[0], x[1]) for x in c2copy.variables.values_list('name', 'compoundunit__name')])
        self.assertEqual(list1, list2)

        list1 = set(
            [(x[0], x[1], x[2]) for x in
             c1.resets.values_list('variable__name', 'test_variable__name', 'order')]
        )
        list2 = set(
            [(x[0], x[1], x[2]) for x in c2copy.resets.values_list('variable__name', 'test_variable__name', 'order')]
        )
        self.assertEqual(list1, list2)

        c1copy.delete()

    def test_copy_model(self):
        m1 = CellModel.objects.get(name='model1')
        person = Person.objects.all()[0]

        m2 = copy_and_link_model(m1, person, True)

        list1 = set([x[0] for x in m1.all_components.values_list('name')])
        list2 = set([x[0] for x in m2.all_components.values_list('name')])
        self.assertEqual(list1, list2)

        list1 = set([x[0] for x in m1.compoundunits.values_list('name')])
        list2 = set([x[0] for x in m2.compoundunits.values_list('name')])
        self.assertEqual(list1, list2)

        for c1 in m1.all_components.all():
            c2 = m2.all_components.filter(name=c1.name).first()

            list1 = set([(x[0], x[1]) for x in c1.variables.values_list('name', 'compoundunit__name')])
            list2 = set([(x[0], x[1]) for x in c2.variables.values_list('name', 'compoundunit__name')])
            self.assertEqual(list1, list2)

            for v1 in c1.variables.filter(equivalent_variables__isnull=False):
                v2 = c1.variables.filter(name=v1.name).first()
                list1 = set([x[0] for x in v1.equivalent_variables.values_list('name', 'component__name')])
                list2 = set([x[0] for x in v2.equivalent_variables.values_list('name', 'component__name')])
                self.assertEqual(list1, list2)

            list1 = set(
                [(x[0], x[1], x[2]) for x in c1.resets.values_list('variable__name', 'test_variable__name', 'order')]
            )
            list2 = set(
                [(x[0], x[1], x[2]) for x in c2.resets.values_list('variable__name', 'test_variable__name', 'order')]
            )
            self.assertEqual(list1, list2)

    #
    # def test_model_create_by_shallow_copy(self):
    #     request = self.factory.get('/copy/cellmodel/{}'.format(self.model.id))
    #     request.user = self.user
    #
    #     m1 = CellModel.objects.get(name='model1')
    #     m1, m2 = create_by_shallow_copy(request, m1)
    #
    #     self.assertEqual(m1.name, m2.name)
    #     self.assertNotEqual(m1.imported_from, m2.imported_from)
    #     self.assertEqual(m1.all_components.count(), 1)
    #     self.assertEqual(m2.all_components.count(), 0)
    #
    # def test_model_create_by_link_copy(self):
    #     request = self.factory.get('/copy/cellmodel/{}'.format(self.model.id))
    #     request.user = self.user
    #     m1 = CellModel.objects.get(name='model1')
    #
    #     m1, m2 = create_by_shallow_copy(request, m1)
    #     link_copy(request, m1, m2)
    #
    #     self.assertEqual(m1.name, m2.name)
    #     self.assertEqual(m1.all_components.count(), 1)
    #     self.assertEqual(m2.all_components.count(), 1)
    #     self.assertEqual(m1.all_components.all()[0], m2.all_components.all()[0])
    #
    # def test_model_create_by_deep_copy(self):
    #     request = self.factory.get('/copy/cellmodel/{}'.format(self.model.id))
    #     request.user = self.user
    #     m1 = CellModel.objects.get(name='model1')
    #
    #     m1, m2 = create_by_shallow_copy(request, m1)
    #     deep_copy(request, m1, m2,
    #               exclude=['encapsulated_components', 'child_components', 'used_by', 'imported_to', 'imported_from'])
    #
    #     self.assertEqual(m1.name, m2.name)
    #     self.assertEqual(m1.all_components.count(), 1)
    #     self.assertEqual(m2.all_components.count(), 1)
    #
    #     self.assertNotEqual(m1.all_components.all()[0], m2.all_components.all()[0])
    #
    # def test_model_delete_item(self):
    #     request = self.factory.get('/delete/cellmodel/{}'.format(self.model.id))
    #     request.user = self.user
    #     m1 = CellModel.objects.get(name='model1')
    #
    #     m1, m2 = create_by_shallow_copy(request, m1)
    #     deep_copy(request, m1, m2)
    #
    #     self.assertEqual(m1.name, m2.name)
    #     self.assertEqual(m1.all_components.count(), 1)
    #     self.assertEqual(m2.all_components.count(), 1)
    #     self.assertNotEqual(m1.all_components.all()[0], m2.all_components.all()[0])
    #
    #     c2 = m2.components.all()
    #
    #     delete_item(request, m2, 'base')
    #
    #     self.assertEqual(Component.objects.count(), 2)
    #     self.assertEqual(CellModel.objects.count(), 1)
    #     self.assertEqual(c2[0].models, None)
    #
    #     delete_item(request, c2[0], 'base')
    #
    #     self.assertEqual(Component.objects.count(), 1)
    #
    # def test_model_delete_deep(self):
    #     request = self.factory.get('/delete/cellmodel/{}'.format(self.model.id))
    #     request.user = self.user
    #     m1 = CellModel.objects.get(name='model1')
    #
    #     m1, m2 = create_by_shallow_copy(request, m1)
    #     deep_copy(request, m1, m2)
    #
    #     self.assertEqual(m1.name, m2.name)
    #     self.assertEqual(m1.all_components.count(), 1)
    #     self.assertEqual(m2.all_components.count(), 1)
    #     self.assertNotEqual(m1.all_components.all()[0], m2.all_components.all()[0])
    #
    #     c2 = m2.components.all()
    #
    #     delete_item(request, m2, 'deep')
    #
    #     self.assertEqual(Component.objects.count(), 1)
    #     self.assertEqual(CellModel.objects.count(), 1)
