"""
    This file contains the functions needed to validate any item by calling the libCellML validators.
"""

from django.db.models import Count

from main.functions import draw_error_tree
from main.models import ItemError, CompoundUnit


def validate_variable(variable):
    # Variables are all local validation - no need for a duplicate
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
            spec='11.1.1.1',
            fields=["name"]
        )
        err.save()
        variable.errors.add(err)

    # Check that variable has units
    if variable.compoundunit is None:
        err = ItemError(
            hints="Variable <i>{}</i> does not have any units.".format(variable.name),
            spec="11.1.1.2",
            fields=["compoundunit"]
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
                spec="11?",
                fields=["initial_value"]
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
                spec="11.1.2.1",
                fields=['initial_value_variable', 'component']
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
            spec="11.1.2.1",
            fields=['initial_value_variable', 'initial_value_constant']
        )
        err.save()
        variable.errors.add(err)
        is_valid = False

    error_tree, error_count = draw_error_tree(variable)
    error_count += variable.errors.count()
    variable.error_tree = {'tree_html': error_tree, 'error_count': error_count}
    variable.is_valid = is_valid
    variable.save()

    return is_valid


def validate_compoundunit(cu):
    for e in cu.errors.all():
        e.delete()

    # Built-in units are valid
    if cu.is_standard:
        return True

    cu.error_tree = None

    # Checking the name
    is_valid, hints = is_cellml_identifier(cu.name)
    if not is_valid:
        err = ItemError(
            hints="Invalid compound_units name <i>{n}</i>: {h}".format(
                n=cu.name,
                h=hints),
            spec='8.1.1',
            fields=['name']
        )
        err.save()
        cu.errors.add(err)

    if CompoundUnit.objects.filter(name=cu.name, is_standard=True).count() > 0:
        err = ItemError(
            hints="The name cannot be the same as a built-in units name, <i>{}</i>".format(cu.name),
            spec="8.1.3",
            fields=['name']
        )
        err.save()
        cu.errors.add(err)
        is_valid = False

    # Also need to check the unit elements of this compound unit here as they can't be accessed individually
    for u in cu.product_of.all():
        is_valid = validate_unit(u) and is_valid

    error_tree, error_count = draw_error_tree(cu)
    error_count += cu.errors.count()
    cu.error_tree = {'tree_html': error_tree, 'error_count': error_count}
    cu.is_valid = is_valid
    cu.save()

    return is_valid


def validate_unit(unit):
    is_valid = True
    for e in unit.errors.all():
        e.delete()
    unit.error_tree = None

    # 9.1.1 Check that the pointers are valid
    if not unit.child_cu:
        is_valid = False
        err = ItemError(
            hints="Unit in units <i>{p}</i> points to a blank unit".format(
                p=unit.parent_cu.name),
            spec='9.1.1',
            fields=['child_cu']
        )
        err.save()
        unit.parent_cu.errors.add(err)

    error_tree, error_count = draw_error_tree(unit)
    error_count += unit.errors.count()
    unit.error_tree = {'tree_html': error_tree, 'error_count': error_count}
    unit.is_valid = is_valid
    unit.save()

    return is_valid


def validate_math(math):
    return True


def validate_reset(reset):
    is_valid = True
    for e in reset.errors.all():
        e.delete()

    if reset.order == '' or reset.order is None:
        err = ItemError(
            hints="Reset <i>{r}</i> does not have an order set".format(r=reset.name),
            spec="12.1.2",
            fields=["order"]
        )
        err.save()
        reset.errors.add(err)
        is_valid = False

    if reset.test_value is None:
        err = ItemError(
            hints="Reset <i>{r}</i> does not reference a test_value".format(r=reset.name),
            spec="12",  # TODO find correct code for resets
            fields=['test_value']
        )
        err.save()
        reset.errors.add(err)
        is_valid = False

    if reset.reset_value is None:
        err = ItemError(
            hints="Reset <i>{r}</i> does not reference a reset_value".format(r=reset.name),
            spec="12",  # TODO find correct code for resets
            fields=['reset_value']
        )
        err.save()
        reset.errors.add(err)
        is_valid = False

    if reset.component is None:
        err = ItemError(
            hints="Reset <i>{r}</i> does not have a component".format(r=reset.name),
            spec="10.1.2.2",
            fields=['component']
        )
        err.save()
        reset.errors.add(err)
        is_valid = False

    if reset.variable is None:
        err = ItemError(
            hints="Reset <i>{r}</i> does not reference a variable".format(r=reset.name),
            spec="12.1.1",
            fields=['variable']
        )
        err.save()
        reset.errors.add(err)
        is_valid = False

    if reset.test_variable is None:
        err = ItemError(
            hints="Reset <i>{r}</i> does not reference a test_variable".format(r=reset.name),
            spec="12",  # TODO find correct code for resets
            fields=['test_variable']
        )
        err.save()
        reset.errors.add(err)
        is_valid = False

    if reset.component is not None:
        if reset.variable is not None and reset.component != reset.variable.component:
            err = ItemError(
                hints="Reset <i>{r}</i> in component <i>{c}</i> refers to a variable <i>{v}</i> which is in a "
                      "different component, <i>{vc}</i>".format(
                    r=reset.name,
                    c=reset.component.name,
                    v=reset.variable.name,
                    vc=reset.variable.component.name),
                spec="12",  # TODO find correct code for resets
                fields=['variable', 'component']
            )
            err.save()
            reset.errors.add(err)
            is_valid = False

        if reset.test_variable is not None and reset.component != reset.test_variable.component:
            err = ItemError(
                hints="Reset <i>{r}</i> in component <i>{c}</i> refers to a test_variable <i>{v}</i> in a different "
                      "component, <i>{vc}</i>".format(
                    r=reset.name,
                    c=reset.component.name,
                    v=reset.test_variable.name,
                    vc=reset.test_variable.component.name),
                spec="12",  # TODO find correct code for resets
                fields=['test_variable', 'component']
            )
            err.save()
            reset.errors.add(err)
            is_valid = False

    error_tree, error_count = draw_error_tree(reset)
    error_count += reset.errors.count()
    reset.error_tree = {'tree_html': error_tree, 'error_count': error_count}
    reset.is_valid = is_valid
    reset.save()

    return is_valid


def validate_component_locally(component):
    is_valid = True
    for e in component.errors.all():
        e.delete()

    is_valid, hints = is_cellml_identifier(component.name)
    if not is_valid:
        err = ItemError(
            hints="Invalid component name <i>{n}</i>: {h}".format(
                n=component.name,
                h=hints),
            spec='10.1.1',
            fields=['name']
        )
        err.save()
        component.errors.add(err)

    # Check component's variables for duplicate names
    duplicates = component.variables.values('name').annotate(name_count=Count('name')).filter(name_count__gt=1)
    for d in duplicates:
        err = ItemError(
            hints="Variable name <i>{n}</i> is duplicated {x} times in component <i>{m}</i>".format(
                n=d['name'],
                x=d['name_count'],
                m=component.name),
            spec='11.1.1.1',
            fields=['variables']
        )
        err.save()
        component.errors.add(err)  # It's an error of the *component* not of the variable itself ...
        is_valid = False

    return is_valid


def validate_component(component):
    is_valid = validate_component_locally(component)

    for child_component in component.child_components.all():
        is_valid = validate_component(child_component) and is_valid

    for variable in component.variables.all():
        is_valid = validate_variable(variable) and is_valid

    for reset in component.resets.all():
        is_valid = validate_reset(reset) and is_valid

    for math in component.maths.all():
        is_valid = validate_math(math) and is_valid

    error_tree, error_count = draw_error_tree(component)
    error_count += component.errors.count()
    component.error_tree = {'tree_html': error_tree, 'error_count': error_count}
    component.is_valid = is_valid
    component.save()

    return is_valid


def validate_cellmodel_locally(model):
    is_valid = True
    for e in model.errors.all():
        e.delete()
    model.error_tree = None

    # Check model name
    is_valid, hints = is_cellml_identifier(model.name)
    if not is_valid:
        err = ItemError(
            hints="Invalid model name <i>{n}</i>: {h}".format(
                n=model.name,
                h=hints),
            spec='4.2.1',
            fields=['name']
        )
        err.save()
        model.errors.add(err)
        is_valid = False

    # Check model's components for duplicate names
    duplicates = model.components.values('name').annotate(name_count=Count('name')).filter(name_count__gt=1)
    for d in duplicates:
        err = ItemError(
            hints="Component name <i>{n}</i> is duplicated {x} times in model <i>{m}</i>".format(
                n=d['name'],
                x=d['name_count'],
                m=model.name),
            spec='10.1.1',
        )
        err.save()
        model.errors.add(err)  # It's an error of the *model* not of the component itself ...
        is_valid = False

    # Check model units
    duplicates = model.compoundunits.values('name').annotate(name_count=Count('name')).filter(name_count__gt=1)
    for d in duplicates:
        err = ItemError(
            hints="Units name <i>{n}</i> is duplicated {x} times in model <i>{m}</i>".format(
                n=d['name'],
                x=d['name_count'],
                m=model.name),
            spec='8.1.2',
        )
        err.save()
        model.errors.add(err)  # It's an error of the *model* not of the compoundunit itself ...
        is_valid = False

    # Check that the set of compound units used by the variables exists in the model
    required = model.components.values_list('name', 'variables__name', 'variables__compoundunit__name')
    available = model.compoundunits.values_list('name').distinct()
    missing = [(c, v, u) for c, v, u in required
               if (u,) not in available
               and u is not None
               and (u,) not in CompoundUnit.objects.filter(is_standard=True).values_list('name')]

    for c, v, u in missing:
        err = ItemError(
            hints="Variable <i>{v}</i> in component <i>{c}</i> has units <i>{u}</i> which do not exist in this "
                  "model, and are not built-in.".format(c=c, u=u, v=v),
            spec="11.1.1.2"
        )
        err.save()
        model.errors.add(err)
        is_valid = False

    return is_valid


def validate_cellmodel(model):
    is_valid = validate_cellmodel_locally(model)

    for component in model.components.all():
        is_valid = validate_component(component) and is_valid

    for compoundunit in model.compoundunits.all():
        is_valid = validate_compoundunit(compoundunit) and is_valid

    # Validate connections and equivalent variable networks in the model
    is_valid = validate_connections(model) and is_valid

    error_tree, error_count = draw_error_tree(model)
    error_count += model.errors.count()
    model.error_tree = {'tree_html': error_tree, 'error_count': error_count}
    model.is_valid = is_valid
    model.save()

    return is_valid


def validate_connections(model):
    is_valid = True
    for component in model.components.all():
        for variable in component.variables.filter(equivalent_variables__isnull=False):
            # Check that equivalent variables are not in the same component
            for ev in variable.equivalent_variables.filter(component=component):
                err = ItemError(
                    hints="Variable <i>{v1}</i> and equivalent variable <i>{v2}</i> are both in the same component "
                          "<i>{c}</i>".format(
                        v1=variable.name,
                        v2=ev.name,
                        c=component.name
                    ),
                    spec="17.1.2",
                )
                err.save()
                component.errors.add(err)
                is_valid = False

                # Check that the variables have a valid parent component
                if ev.component is None:
                    err = ItemError(
                        hints="Variable <i>{ev}</i> is equivalent to variable <i>{v}</i> in component <i>{c}</i> but "
                              "does not have a parent component".format(
                            ev=ev.name,
                            v=variable.name,
                            c=component.name,
                        ),
                        spec="17.?",
                    )
                    err.save()
                    ev.errors.add(err)
                    component.errors.add(err)
                    is_valid = False

    cycle_list = model_cyclic_variables_found(model)
    loop_count = len(cycle_list)
    if loop_count > 0:
        loops = " loops" if loop_count > 1 else " loop"
        des = ''.join(cycle_list)
        err = ItemError(
            hints="Cyclic variables exist, " + str(loop_count) + loops + " found (Component,Variable): <br>" + des,
            spec="19.10.5"
        )
        err.save()
        model.errors.add(err)
        is_valid = False
    else:
        # Check order uniqueness in resets
        total_done_list = []
        for component in model.components.all():
            for variable in component.variables.filter(equivalent_variables__isnull=False).exclude(
                    id__in=total_done_list):
                local_done_list = []
                reset_map = {}
                local_done_list, reset_map = fetch_connected_resets(variable, local_done_list, reset_map)

                total_done_list.extend(local_done_list)

                for order, resets in reset_map.items():
                    if len(resets) > 1:
                        des = "Non-unique reset order of " + order + " found within equivalent variable set: "
                        for r in resets:
                            des += "<br>  - variable <i>" + r.variable.name + "</i> in component <i>" + \
                                   r.variable.component.name + "</i> has reset with order " + order
                        err = ItemError(
                            hints=des,
                            spec='12.1.1.2'
                        )
                        err.save()
                        model.errors.add(err)
                        is_valid = False

    return is_valid


VALIDATE_DICT = {
    'cellmodel': validate_cellmodel_locally,
    'variable': validate_variable,
    'compoundunit': validate_compoundunit,
    'math': validate_math,
    'component': validate_component_locally,
    'reset': validate_reset,
    'unit': validate_unit,
}


def fetch_connected_resets(variable, local_done_list, reset_map):
    for equiv in variable.equivalent_variables.exclude(id__in=local_done_list):
        component = equiv.component

        for reset in component.resets.filter(variable=equiv):
            reset_map[str(reset.order)].append(reset)
        local_done_list.append(equiv)

        local_done_list, reset_map = fetch_connected_resets(equiv, local_done_list, reset_map)

    return local_done_list, reset_map


def model_cyclic_variables_found(model):
    all_variable_list = []
    total_list = []
    hint_list = []

    for component in model.components.all():
        for variable in component.variables.annotate(num_ev=Count('equivalent_variables')
                                                     ).filter(num_ev__gte=2).exclude(id__in=all_variable_list):
            for eq in variable.equivalent_variables.all():
                check_list = [variable]
                found, check_list, all_variable_list = cyclic_variable_found(variable, eq, check_list,
                                                                             all_variable_list)
                if found:
                    total_list.append(check_list)

    for temp_list in total_list:
        start = min(temp_list.values_list('name'))  # Getting the first name alphabetically and only reporting this loop
        if temp_list[0] == start:

            description = ''
            reverse_description = ''
            separator = ''

            for v in temp_list:
                parent = v.component
                description += separator + "(<i>" + parent.name + ", " + v.name + "</i>)"
                reverse_description = "(<i>" + parent.name + ", " + v.name + "</i>)" + separator + reverse_description
                separator = " -> "
            description += "<br>"
            reverse_description += "<br>"

            # if this info has not yet been added to the error list, add it
            if description not in hint_list and reverse_description not in hint_list:
                hint_list.append(description)

    return hint_list


def cyclic_variable_found(parent, child, check_list, all_variable_list):
    all_variable_list.append(child)

    if child in check_list:
        check_list.append(child)
        while check_list[0] != check_list[-1]:
            check_list.remove(check_list[0])
        return True, check_list, all_variable_list

    check_list.append(child)

    for eq in child.equivalent_variables.all():
        if eq == parent:
            continue
        found, check_list, all_variable_list = cyclic_variable_found(child, eq, check_list, all_variable_list)
        if found:
            return True, check_list, all_variable_list

    return False, check_list, all_variable_list


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
