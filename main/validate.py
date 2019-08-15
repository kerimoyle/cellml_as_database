"""
    This file contains the functions needed to validate any item by calling the libCellML validators.
"""

import libcellml

from main.models import ItemError, CompoundUnit


def validate_variable(variable):
    for e in variable.errors.all():
        e.delete()

    try:
        initial_component_id = variable.initial_value_variable.component.id
    except Exception as e:
        initial_component_id = None
    try:
        initial_unit_id = variable.initial_value_variable.compoundunit.id
    except Exception as e:
        initial_unit_id = None

    # Validate name
    is_valid, hints = is_cellml_identifier(variable.name)
    if not is_valid:
        err = ItemError(
            hints="Invalid variable name <i>{n}</i>: {h}".format(
                n=variable.name,
                h=hints),
            spec='11.1.1.1'
        )
        err.save()
        variable.errors.add(err)

    # Check that variable has units
    if variable.compoundunit is None:
        err = ItemError(
            hints="Variable <i>{}</i> does not have any units.".format(variable.name),
            spec="11.1.1.2"
        )
        err.save()
        variable.errors.add(err)
        is_valid = False
    elif initial_unit_id is not None:
        if initial_unit_id != variable.compoundunit.id:
            err = ItemError(
                hints=
                "Variable has units of <i>{u}</i> but is initialised by variable <i>{vi}</i> "
                "which has units of <i>{ui}</i>.".format(
                    u=variable.compoundunit.name,
                    vi=variable.initial_value_variable.name,
                    ui=variable.initial_value_variable.compoundunit.name),
                spec="11?"
            )
            err.save()
            variable.errors.add(err)
            is_valid = False

    if initial_component_id is not None:
        if initial_component_id != variable.component:
            err = ItemError(
                hints=
                "Variable <i>{v}</i> in component <i>{c}</i> is initialised by variable <i>{vi}</i> "
                "which is in another component <i>{ci}</i>.".format(
                    v=variable.name,
                    c=variable.component.name,
                    vi=variable.initial_value_variable.name,
                    ci=variable.initial_value_variable.component.name),
                spec="11.1.2.1"
            )
            err.save()
            variable.errors.add(err)
            is_valid = False

    if variable.initial_value_variable is not None and variable.initial_value_constant is not None:
        err = ItemError(
            hints=
            "Variable <i>{v}</i> in component <i>{c}</i> is initialised by variable <i>{vi}</i> "
            "as well as by the constant value <i>{ci}</i>. There can be only one.".format(
                v=variable.name,
                c=variable.component.name,
                vi=variable.initial_value_variable.name,
                ci=variable.initial_value_constant),
            spec="11.1.2.1"
        )
        err.save()
        variable.errors.add(err)
        is_valid = False

    return is_valid


def validate_compoundunit(cu):
    for e in cu.errors.all():
        e.delete()

    # Checking the name
    is_valid, hints = is_cellml_identifier(cu.name)
    if not is_valid:
        err = ItemError(
            hints="Invalid compound_units name <i>{n}</i>: {h}".format(
                n=cu.name,
                h=hints),
            spec='8.1.1'
        )
        err.save()
        cu.errors.add(err)

    if CompoundUnit.objects.filter(name=cu.name, is_standard=True).count() > 0:
        err = ItemError(
            hints="The name cannot be the same as a built-in units name, <i>{}</i>".format(cu.name),
            spec="8.1.3"
        )
        err.save()
        cu.errors.add(err)
        is_valid = False

    # 8.1.2 Checking for name uniqueness within the infoset - can only be done in context of use
    # Also need to check the unit elements of this compound unit here as they can't be accessed individually
    for u in cu.product_of.all():
        is_valid = is_valid and validate_unit(u)

    return is_valid


def validate_unit(unit):
    is_valid = True
    for e in unit.errors.all():
        e.delete()

    # # 9.1.1 check that the reference is valid cellml? TODO do we need this really? can't just check parent/child?
    # if not unit.reference:
    #     err = ItemError(
    #         hints="Unit in units <i>{p}</i> does not have a valid units reference: the field is blank".format(
    #             p=unit.parent_cu.name
    #         ),
    #         spec="9.1.1"
    #     )
    #     err.save()
    #     unit.parent_cu.errors.add(err)
    #     is_valid = False
    # else:
    #     is_valid, hints = is_cellml_identifier(unit.reference)
    #     if not is_valid:
    #         err = ItemError(
    #             hints="Unit in units <i>{p}</i>, reference <i>{r}</i> does not have a valid units reference: {h}".format(
    #                 p=unit.parent_cu.name,
    #                 r=unit.reference,
    #                 h=hints),
    #             spec='9.1.1'
    #         )
    #         err.save()
    #         unit.parent_cu.errors.add(err)

    # 9.1.1 Check that the pointers are valid
    if not unit.child_cu:
        err = ItemError(
            hints="Unit in units <i>{p}</i> points to a blank unit".format(
                p=unit.parent_cu.name),
            spec='9.1.1'
        )
        err.save()
        unit.parent_cu.errors.add(err)

    return is_valid


def validate_math(math):
    return True


def validate_reset(reset):
    is_valid = True
    for e in reset.errors.all():
        e.delete()

    if not reset.order:
        err = ItemError(
            hints="Reset order is not set",
            spec="12.1.2"
        )
        err.save()
        reset.errors.add(err)
        is_valid = False

    if reset.test_value is None:
        err = ItemError(
            hints="Reset does not reference a test_value",
            spec="12"  # TODO find correct code for resets
        )
        err.save()
        reset.errors.add(err)
        is_valid = False

    if reset.reset_value is None:
        err = ItemError(
            hints="Reset does not reference a reset_value",
            spec="12"  # TODO find correct code for resets
        )
        err.save()
        reset.errors.add(err)
        is_valid = False

    if reset.component is None:
        err = ItemError(
            hints="Reset does not have a component",
            spec="10.1.2.2"
        )
        err.save()
        reset.errors.add(err)
        is_valid = False

    if reset.variable is None:
        err = ItemError(
            hints="Reset does not reference a variable",
            spec="12.1.1"
        )
        err.save()
        reset.errors.add(err)
        is_valid = False

    if reset.test_variable is None:
        err = ItemError(
            hints="Reset does not reference a test_variable",
            spec="12"  # TODO find correct code for resets
        )
        err.save()
        reset.errors.add(err)
        is_valid = False

    if reset.component is not None:
        if reset.variable is not None and reset.component != reset.variable.component:
            err = ItemError(
                hints="Reset in component <i>{c}</i> refers to a variable <i>{v}</i> in a different component, "
                      "<i>{vc}</i>".format(
                    c=reset.component.name,
                    v=reset.variable.name,
                    vc=reset.variable.component.name),
                spec="12"  # TODO find correct code for resets
            )
            err.save()
            reset.errors.add(err)
            is_valid = False

        if reset.test_variable is not None and reset.component != reset.test_variable.component:
            err = ItemError(
                hints="Reset in component <i>{c}</i> refers to a test_variable <i>{v}</i> in a different component, <i>{vc}</i>".format(
                    c=reset.component.name,
                    v=reset.test_variable.name,
                    vc=reset.test_variable.component.name),
                spec="12"  # TODO find correct code for resets
            )
            err.save()
            reset.errors.add(err)
            is_valid = False

    return is_valid


def validate_component(component):
    is_valid = True
    for e in component.errors.all():
        e.delete()

    is_valid, hints = is_cellml_identifier(component.name)
    if not is_valid:
        err = ItemError(
            hints="Invalid component name <i>{n}</i>: {h}".format(
                n=component.name,
                h=hints),
            spec='10.1.1'
        )
        err.save()
        component.errors.add(err)
    # 10.1.1 Can only check uniqueness of name in context of use

    return is_valid


VALIDATE_DICT = {
    'cellmodel': libcellml.Validator.validateModel,
    'variable': validate_variable,
    'compoundunit': validate_compoundunit,
    'math': validate_math,
    'component': validate_component,
    'reset': validate_reset,
}


def is_cellml_identifier(name):
    result = True
    notes = ""

    if len(name):
        if name[0].isdigit():
            result = False
            notes += "CellML identifiers must not begin with a European numeric character [0-9], "

        temp = name.replace("_", "")
        if not temp.isalnum():
            result = False
            notes += "CellML identifiers must not contain any characters other than [a-zA-Z0-9_], "

    else:
        result = False
        notes += "CellML identifiers must contain one of more basic Latin alphabetic characters, "

    return result, notes
