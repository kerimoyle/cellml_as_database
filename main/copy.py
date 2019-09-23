from main.functions import is_standard_unit
from main.models import CellModel, Component, Math, Variable, Reset, CompoundUnit, Unit


def copy_model(in_model, person):
    # Create the CellModel instance:
    model = CellModel(
        name=in_model.name,
        cellml_id=in_model.id,
        owner=person,
        # TODO save attribution somehow ...
    )
    model.save()

    # Add the compound units
    for u in in_model.compoundunits.all():
        copy_compoundunit(u, model, person)

    # Link the compound units
    for old_unit in in_model.compoundunits.all():
        new_unit = model.compoundunits.filter(name=old_unit.name).first()
        copy_units(new_unit, old_unit, model, person)

    # Add the components
    for c in in_model.all_components.all():
        copy_component(c, model, model, person)

    # Once everything is loaded into the database, we have to make the connections between items
    # Note that components are loaded twice - once into the all_components field of the parent model, independently of
    # the encapsulation structure, and again into the encapsulated_components field, which reflects the hierarchy, if
    # present
    for in_component in in_model.encapsulated_components.all():
        component = model.all_components.filter(name=in_component.name).first()
        copy_connected_component_items(component, model, in_component, person)

    for in_component in in_model.encapsulated_components.all():
        component = model.all_components.filter(name=in_component.name).first()
        copy_connected_equivalent_variables(component, in_component)

    return model


def copy_component(in_component, out_parent, out_model, person):
    # Check whether copying this component will duplicate names in the parent set, and if so, add "copy" to the name
    name = "{}_copy".format(in_component.name) \
        if out_model.all_components.filter(name=in_component.name).count() == 0 \
        else in_component.name

    out_component = Component(
        name=name,
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

    for r in in_component.resets.all():
        copy_reset(r, out_component, person)

    for c in in_component.child_components.all():
        copy_component(c, out_component, out_model, person)

    return out_component


def copy_compoundunit(in_units, model, person):
    if model is not None:
        if in_units.is_standard:
            # Create a reference to the standard unit
            base_unit = CompoundUnit.objects.filter(name=in_units.name, is_standard=True).first()
            model.units.add(base_unit)
            return
        out_compound_unit = model.compoundunits.filter(name=in_units.name).first()

        name = "{}_copy".format(in_units.name) \
            if model.compoundunits.filter(name=in_units.name).count() == 0 \
            else in_units.name

        if out_compound_unit is None:
            out_compound_unit = CompoundUnit(
                name=name,
                owner=person,
            )
            out_compound_unit.save()
            out_compound_unit.models.add(model)
        for product in in_units.product_of.all():
            copy_compoundunit(product, model, person)
            copy_units(out_compound_unit, product, model, person)
        return out_compound_unit
    else:
        # messages.warning(
        #                  "Did not copy compound unit {cu} as this requires a model first.".format(cu=in_units.name))
        return None


def copy_units(parent_unit, in_compoundunit, model, person):
    for u in in_compoundunit.product_of.all():
        if is_standard_unit(u):
            child_unit = CompoundUnit.objects.filter(name=u.name).first()
        else:
            child_unit = model.compoundunits.filter(name=u.name).first()  # unit must be in this model first

        unit = Unit(
            prefix=u.prefix,
            multiplier=u.multiplier,
            exponent=u.exponent,
            name=u.name,
            parent_cu=parent_unit,
            child_cu=child_unit,
            owner=person,
        )
        unit.save()

    return


def copy_variable(in_variable, out_component, out_model, person):
    name = "{}_copy".format(in_variable.name) \
        if out_model.all_components.filter(name=in_variable.name).count() == 0 \
        else in_variable.name

    out_variable = Variable(
        name=name,
        # interface_type=in_variable.interfaceType(),  # TODO get dictionary of interfaceTypes ...
        owner=person,
    )
    out_variable.component = out_component
    cu = out_model.compoundunits.filter(name="{}_copy".format(in_variable.compoundunit.name)).first()
    if cu is None:
        cu = out_model.compoundunits.filter(name=in_variable.compoundunit.name).first()

    out_variable.compoundunit = cu
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

    test_variable = out_component.variables.filter(name=in_reset.test_variable.name).first()
    variable = out_component.variables.filter(name=in_reset.variable.name).first()

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


def copy_connected_equivalent_variables(component, in_component):
    for in_variable in in_component.variables.all():

        variable = component.variables.filter(name="{}_copy".format(in_variable.name)).first()
        if variable is None:
            variable = component.variables.filter(name=in_variable.name).first()

        for in_equiv in in_variable.equivalent_variables.all():
            in_equiv_component = in_equiv.component
            in_equiv_grandparent = in_equiv_component.parent_component
            if not in_equiv_grandparent:
                in_equiv_grandparent = in_equiv_component.parent_model

            out_equiv_component = component.model.all_components.filter(name=in_equiv_component.name).first()

            # Look for variable in the sibling component set
            if out_equiv_component:
                out_equiv_variable = out_equiv_component.variables.filter(name=in_equiv.name).first()
            else:
                pass

            if out_equiv_variable:
                variable.equivalent_variables.add(out_equiv_variable)
            else:
                pass

    for in_child_component in in_component.child_components.all():
        child_component = component.child_components.fitler(name=in_equiv_component.name).first()
        copy_connected_equivalent_variables(child_component, in_child_component)

    return


def copy_connected_component_items(component, model, in_component, person):
    for variable in component.variables.all():
        # Link to units if they exist, or set to None
        in_variable = in_component.variables.get(name=variable.name)
        in_units = in_variable.compoundunit
        if in_units is None:
            pass
        else:
            builtin_unit = CompoundUnit.objects.filter(is_standard=True, name=in_units).first()
            spec_unit = CompoundUnit.objects.filter(name=in_units, models=model).first()
            if builtin_unit is not None:
                variable.compoundunit = builtin_unit
            elif spec_unit is not None:
                variable.compoundunit = spec_unit
            else:
                # Then is new base unit.  Should have been added already??
                u_new = CompoundUnit(
                    name=in_units.name,
                    symbol=in_units.symbol,  # not sure about this one?
                    is_standard=False,
                    owner=person,
                )
                u_new.save()
                u_new.models.add(model)
                variable.compoundunit = u_new

        variable.initial_value_variable = component.variables.get(name=in_variable.initial_value_variable.name)
        variable.initial_value_constant = in_variable.initial_value_constant
        variable.save()

    for reset in in_component.resets.all():
        copy_reset(reset, component, person)

    for child_component in component.child_components.all():
        copy_connected_component_items(child_component, model, in_component, person)
    return
