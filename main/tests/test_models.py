from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory

from main.copy import copy_and_link_component, copy_and_link_variable, copy_and_link_model, copy_and_link_compoundunit
from main.models import CellModel, Component, Person, CompoundUnit, Variable, Reset, Unit


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

    def test_name(self):
        m = CellModel.objects.get(name='model1')

        self.assertEqual(m.name, 'model1')
        self.assertEqual(self.model.name, "model1")

    def test_component(self):
        m = CellModel.objects.get(name='model1')
        c = Component.objects.get(name="c1")

        self.assertEqual(c.model.name, m.name)
        self.assertEqual(m.all_components.filter(name="c1")[0], c)
        self.assertEqual(c.model, m)

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

    def test_copy_compoundunits(self):
        m1 = CellModel.objects.get(name='model1')
        person = Person.objects.filter(first_name="Daffy").first()

        # Create a couple of generations of compound units and test that they are copied successfully
        grandfather = CompoundUnit(name="grandfather", symbol="poppa")
        grandfather.save()
        m1.compoundunits.add(grandfather)
        grandmother = CompoundUnit(name="grandmother", symbol="nanna")
        grandmother.save()
        m1.compoundunits.add(grandmother)

        # Check the copy of base unit:
        greataunt, copied = copy_and_link_compoundunit(grandmother, None, person)
        greataunt.name = "greataunt"
        greataunt.save()
        self.assertEqual("greataunt", greataunt.name)
        self.assertEqual("nanna", greataunt.symbol)
        greataunt.symbol = ""
        greataunt.save()
        self.assertEqual("greataunt", greataunt.symbol)

        mother = CompoundUnit(name="mother")
        mother.save()
        u1 = Unit(child_cu=grandfather, parent_cu=mother, exponent=1)
        u1.save()
        u2 = Unit(child_cu=grandmother, parent_cu=mother, exponent=1)
        u2.save()
        mother.symbol = ""
        mother.update_symbol()

        self.assertTrue(grandmother.symbol in mother.symbol and grandfather.symbol in mother.symbol)
        u1.delete()
        u2.delete()
        mother.symbol = ""
        mother.update_symbol()
        self.assertEqual(mother.symbol, "mother")

        father = CompoundUnit(name="father", symbol="father")
        father.save()
        m1.compoundunits.add(father)

        u3 = Unit(child_cu=grandfather, parent_cu=father, exponent=2)
        u3.save()
        u4 = Unit(child_cu=grandmother, parent_cu=father, exponent=3)
        u4.save()

        father.symbol = ""
        father.save()  # will update symbol too

        self.assertTrue(
            "({u})<sup>{e}</sup>".format(u=grandmother.symbol, e=u4.exponent) in father.symbol and
            "({u})<sup>{e}</sup>".format(u=grandfather.symbol, e=u3.exponent) in father.symbol
        )

        # Test copying one generation.  This should copy grandmother and grandfather too because model is None
        uncle, copied = copy_and_link_compoundunit(father, None, person)
        self.assertTrue(copied)
        uncle_parents = [x[0] for x in uncle.product_of.values_list('child_cu__name')]
        self.assertIn("grandfather", uncle_parents)
        self.assertIn("grandmother", uncle_parents)

        self.assertTrue(
            "({u})<sup>{e}</sup>".format(u=grandmother.symbol, e=u4.exponent) in uncle.symbol and
            "({u})<sup>{e}</sup>".format(u=grandfather.symbol, e=u3.exponent) in uncle.symbol
        )

        # Test copying one generation into the same parent model - shouldn't copy it at all?
        aunt, copied = copy_and_link_compoundunit(father, m1, person)
        self.assertFalse(copied)

        # Test copying one generation into another parent model - should copy product_of

        daughter = CompoundUnit(name="daughter")
        daughter.save()

        u5 = Unit(child_cu=mother, parent_cu=daughter, exponent=4)
        u5.save()
        u6 = Unit(child_cu=father, parent_cu=daughter, exponent=5)
        u6.save()

        daughter.symbol = ""
        daughter.update_symbol()

        self.assertTrue(mother.symbol in daughter.symbol
                        and ("({u})<sup>{e}</sup>".format(u=father.symbol, e=u6.exponent) in daughter.symbol))

        son, copied = copy_and_link_compoundunit(daughter, None, person)
        son.name = "son"
        son.symbol = ""
        son.save()

        # There is no specified order to the fields so can't guarantee any order here?
        self.assertTrue(("({u})<sup>{e}</sup>".format(u=mother.symbol, e=u5.exponent) in son.symbol)
                        and ("({u})<sup>{e}</sup>".format(u=father.symbol, e=u6.exponent) in son.symbol))

        # TODO pretty sure there are bits here I've missed ...


