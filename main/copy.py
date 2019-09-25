from main.functions import is_standard_unit
from main.models import CellModel, Component, Math, Variable, Reset, CompoundUnit, Unit, Person


def copy_and_link_model(in_model, person, remove_copy=False):
    # Create the CellModel instance:
    model = CellModel(
        name="{}_copy".format(in_model.name),
        cellml_id=in_model.id,
        owner=person,
        # TODO save attribution somehow ...
    )
    model.save()

    # Add the compound units
    for u in in_model.compoundunits.all():
        new_u, created = copy_and_link_compoundunit(u, model, person)

    if in_model.encapsulated_components.count() > 0:
        for c in in_model.encapsulated_components.all():
            copy_and_link_component(c, model, model, person, remove_copy=False)
    else:
        for c in in_model.all_components.all():
            copy_and_link_component(c, model, model, person, remove_copy=False)

    # Remove the _copy extension from everything except the model
    if remove_copy:
        for c in model.all_components.all():
            c.name = c.name.replace('_copy', '')
            c.save()
            for v in c.variables.all():
                v.name = v.name.replace('_copy', '')
                v.save()

    return model


def copy_and_link_component(in_component, out_parent, out_model, person, remove_copy=False):
    out_component = copy_component(in_component, out_parent, out_model, person)
    out_component = link_component(out_component, out_model, in_component, person)
    # delete the _copy from variables?
    if remove_copy:
        for v in out_component.variables.all():
            v.name = v.name.replace("_copy", "")
            v.save()
    return out_component


def copy_and_link_variable(in_variable, out_component, person, remove_copy=False):
    out_variable = copy_variable(in_variable, out_component, out_component.model, person)
    out_variable = link_variable(out_variable, out_component.model, in_variable, person)
    if remove_copy:
        out_variable.name = out_variable.name.replace("_copy", "")
        out_variable.save()
    return out_variable


def copy_component(in_component, out_parent, out_model, person):
    # Check whether copying this component will duplicate names in the parent set, and if so, add "copy" to the name
    name = "{}_copy".format(in_component.name)

    out_component = Component(
        name="{}_copy".format(in_component.name),
        owner=person,
        model=out_model,
    )

    # Parent and child components represent the encapsulation structure, model simply records the presence in the model
    if type(out_parent).__name__.lower() == 'component':
        out_component.parent_component = out_parent
    else:
        out_component.parent_model = out_model
    out_component.save()

    # Load variables in this component
    for v in in_component.variables.all():
        copy_variable(v, out_component, out_model, person)

    # This is done in the link components?
    for r in in_component.resets.all():
        copy_reset(r, out_component, person)

    for c in in_component.child_components.all():
        copy_component(c, out_component, out_model, person)

    return out_component


def copy_and_link_compoundunit(in_units, out_model=None, person=None):
    if person is None:
        person = Person.objects.all()[0]

    out_compound_unit = None
    if in_units.is_standard:
        # Create a reference to the standard unit
        base_unit = CompoundUnit.objects.filter(name=in_units.name, is_standard=True).first()
        out_model.units.add(base_unit)
        return base_unit, False

    if out_model is not None:
        out_compound_unit = out_model.compoundunits.filter(name=in_units.name).first()
        if out_compound_unit is not None:
            # Then it already exists in the out_model, return
            return out_compound_unit, False

    if out_compound_unit is None:
        out_compound_unit = CompoundUnit(
            name=in_units.name,
            owner=person,
            symbol=in_units.symbol
        )
        out_compound_unit.save()
        if out_model is not None:
            out_compound_unit.models.add(out_model)

        for product in in_units.product_of.all():
            child = None
            if out_model is None:
                # duplicate the linked compoundunit
                child, created = copy_and_link_compoundunit(product.child_cu, out_model, person)
            elif is_standard_unit(product.child_cu):
                # then don't need to do anything except link it
                # try to find in the current model
                child, created = product.child_cu
            else:
                child = out_model.compoundunits.filter(
                    name=product.child_cu.name).first()
            if child is None:
                child, created = copy_and_link_compoundunit(product.child_cu, out_model, person)

            unit = Unit(
                prefix=product.prefix,
                multiplier=product.multiplier,
                exponent=product.exponent,
                parent_cu=out_compound_unit,
                child_cu=child,
                owner=person,
            )
            unit.save()

        out_compound_unit.update_symbol()

        return out_compound_unit, True
    return None, False


# def copy_this_unit(parent_unit, in_compoundunit, model, person):
#     for cu in in_compoundunit.product_of.all():
#         child_unit = None
#         if is_standard_unit(cu):
#             child_unit = CompoundUnit.objects.filter(name=cu.name).first()
#         elif model is not None:
#             child_unit = model.compoundunits.filter(
#                 name=cu.name).first()  # unit must be in this model first
#
#         if child_unit is None:
#             # Duplicate the entire child unit to the same location as this, then add in
#             child_unit, created = copy_and_link_compoundunit(in_compoundunit, model, person)
#
#         unit = Unit(
#             prefix=cu.prefix,
#             multiplier=cu.multiplier,
#             exponent=cu.exponent,
#             name=cu.name,
#             parent_cu=parent_unit,
#             child_cu=child_unit,
#             owner=person,
#         )
#         unit.save()
#
#     return


def copy_variable(in_variable, out_component, out_model, person):
    out_variable = Variable(
        name="{}_copy".format(in_variable.name),
        # interface_type=in_variable.interfaceType(),  # TODO get dictionary of interfaceTypes ...
        owner=person,
    )
    out_variable.component = out_component

    # in link instead?
    # cu = out_model.compoundunits.filter(name=in_variable.compoundunit.name).first()
    # out_variable.compoundunit = cu

    out_variable.save()

    return out_variable


def copy_reset(in_reset, out_component, person):
    reset_value = None
    test_value = None
    if in_reset.test_value is not None:
        test_value = Math(
            math_ml=in_reset.test_value.math_ml,
            owner=person,
        )
        test_value.save()

    if in_reset.reset_value is not None:
        reset_value = Math(
            math_ml=in_reset.reset_value.math_ml,
            owner=person
        )
        reset_value.save()

    test_variable = out_component.variables.filter(name="{}_copy".format(in_reset.test_variable.name)).first()
    variable = out_component.variables.filter(name="{}_copy".format(in_reset.variable.name)).first()

    out_reset = Reset(
        order=int(in_reset.order),
        component=out_component,
        variable=variable,
        test_variable=test_variable,
        reset_value=reset_value,
        test_value=test_value,
        owner=person,
    )
    out_reset.save()

    return out_reset


# def copy_connected_equivalent_variables(component, in_component):
#     for in_variable in in_component.variables.all():
#         variable = component.variables.filter(name="{}_copy".format(in_variable.name)).first()
#         copy_equivalent_variables(variable, in_variable)
#
#         #
#         #
#         # for in_equiv in in_variable.equivalent_variables.all():
#         #     in_equiv_component = in_equiv.component
#         #     in_equiv_grandparent = in_equiv_component.parent_component
#         #     if not in_equiv_grandparent:
#         #         in_equiv_grandparent = in_equiv_component.parent_model
#         #
#         #     out_equiv_component = component.model.all_components.filter(
#         #         name="{}_copy".format(in_equiv_component.name)).first()
#         #
#         #     # Look for variable in the sibling component set
#         #     if out_equiv_component:
#         #        out_equiv_variable = out_equiv_component.variables.filter(name="{}_copy".format(in_equiv.name)).first()
#         #     else:
#         #         pass
#         #
#         #     if out_equiv_variable:
#         #         variable.equivalent_variables.add(out_equiv_variable)
#         #     else:
#         #         pass
#
#     # for in_child_component in in_component.child_components.all():
#     #     child_component = component.child_components.fitler(name="{}_copy".format(in_equiv_component.name)).first()
#     #     copy_connected_equivalent_variables(child_component, in_child_component)
#     return


# def copy_equivalent_variables(variable, in_variable):
#     for in_equiv in in_variable.equivalent_variables.all():
#         in_equiv_component = in_equiv.component
#         in_equiv_grandparent = in_equiv_component.parent_component
#         if not in_equiv_grandparent:
#             in_equiv_grandparent = in_equiv_component.parent_model
#
#         out_equiv_component = variable.component.model.all_components.filter(
#             name="{}_copy".format(in_equiv_component.name)
#         ).first()
#
#         # Look for variable in the sibling component set
#         if out_equiv_component:
#             out_equiv_variable = out_equiv_component.variables.filter(name="{}_copy".format(in_equiv.name)).first()
#         else:
#             pass
#
#         if out_equiv_variable:
#             variable.equivalent_variables.add(out_equiv_variable)
#         else:
#             pass


# def copy_connected_component_items(component, model, in_component, person):
#     for in_variable in in_component.variables.all():
#         variable = component.variables.filter(name="{}_copy".format(in_variable.name)).first()
#         link_variable(variable, model, in_variable, person)
#
#     for reset in in_component.resets.all():
#         copy_reset(reset, component, person)
#
#     for child_component in component.child_components.all():
#         copy_connected_component_items(child_component, model, in_component, person)
#     return


def link_variable(variable, model, in_variable, person):
    in_units = in_variable.compoundunit

    # Test for built-in units
    if is_standard_unit(in_units) and model.compoundunits.filter(name=in_units.name).first() is None:
        model.compoundunits.add(in_units)
        u_new = in_units
    elif model.compoundunits.filter(name=in_units.name).first() is None:
        # Creating new compound unit if it doesn't exist in the model
        u_new, created = copy_and_link_compoundunit(in_units, model, person)
    else:
        u_new = model.compoundunits.filter(name=in_units.name).first()

    variable.compoundunit = u_new

    # Linking to initial variables
    if in_variable.initial_value_variable is not None:
        variable.initial_value_variable = variable.component.variables.get(
            name="{}_copy".format(in_variable.initial_value_variable.name)
        )
    else:
        variable.initial_value_variable = None
    variable.initial_value_constant = in_variable.initial_value_constant
    variable.save()

    # Linking for equivalent variables.  Note that these are only copied if the evs exist with _copy in their name, so
    # are a product of a recent copy operation
    for ev_in in in_variable.equivalent_variables.filter(component__isnull=False):

        # if the copied variable exists in the same component as the source variable, then duplicate the
        # equivalent_variable links as they are
        if in_variable.component.id == variable.component.id:
            # Search for the equivalent component name in our model
            ev_component = model.all_components.filter(name=ev_in.component.name).first()

            # Search for the variable in the ev_component
            if ev_component is not None:
                ev = ev_component.variables.filter(name=ev_in.name).first()
                variable.equivalent_variables.add(ev)

        # If the copied variable exists in a different component, then search for variables inside a _copy component
        # instead
        else:
            ev_component = model.all_components.filter(name="{}_copy".format(ev_in.component.name)).first()
            if ev_component is not None:
                ev = ev_component.variables.filter(name="{}_copy".format(ev_in.name)).first()
                variable.equivalent_variables.add(ev)

    return variable


def link_component(component, model, in_component, person):
    for in_variable in in_component.variables.all():
        variable = component.variables.filter(name="{}_copy".format(in_variable.name)).first()
        link_variable(variable, model, in_variable, person)

    for reset in in_component.resets.all():
        copy_reset(reset, component, person)

    for child_component in component.child_components.all():
        link_component(child_component, model, in_component, person)

    return component
