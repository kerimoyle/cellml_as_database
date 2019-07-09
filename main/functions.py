from django.contrib.contenttypes.models import ContentType
from django.db.models import ForeignKey, ManyToManyField, AutoField, ManyToOneRel
from django.forms import modelform_factory

from main.models import Variable, CellModel, Component, Reset, CompoundUnit, Unit, \
    Math


# ---------------------- CELLML FUNCTIONS -------------------------------------

def print_cellml(item):
    """
    Calls the libCellML library routine to change this into valid CellML
    :param item: the object to serialise
    :return: cellml markup of the object
    """

    return "TODO This is where the serialised CellML text (or other language if desired) could go"


# --------------------- PREVIEW FUNCTIONS -------------------------------------

def build_tree_from_model(storage, model):
    tree = "["
    parents = {}

    # Add the components
    for c in range(model.componentCount()):
        tree = build_tree_from_component(storage, model.component(c), tree, c, parents)

    # Add the units
    for u in range(model.unitsCount()):
        tree = build_tree_from_units(storage, model.units(u), tree, u, parents)

    tree += "]"
    storage.tree = tree
    storage.save()


def build_tree_from_component(storage, component, tree, index, parents):
    tree += "{text: 'Component: " + component.name() + "',"
    tree += "nodes: ["

    # parents['component'] = index
    # record = TemporaryStorageItem(
    #     storage=storage,
    #     dict_string="{}".format(parents)
    # )
    # record.save()

    # Add the variables
    for v in range(component.variableCount()):
        tree = build_tree_from_variable(storage, component.variable(v), tree, v, parents)

    # Add the resets
    for r in range(component.resetCount()):
        tree = build_tree_from_reset(storage, component.reset(r), tree, r, parents)

    tree += "]},"
    return tree


def build_tree_from_units(storage, units, tree, index, parents):  # parents not used until encapsulation is added
    tree += "{text:'Units: " + units.name() + "'},"
    # parents['units'] = index
    # record = TemporaryStorageItem(
    #     storage=storage,
    #     dict_string="{}".format(parents)
    # )
    # record.save()
    return tree


def build_tree_from_variable(storage, variable, tree, index, parents):
    units = variable.units()
    if type(units) is str:
        units_name = units
    else:
        try:
            units_name = units.name()
        except Exception as e:  # TODO could be more useful ... !
            message = "{text:'Something went wrong! {t}: {a}'},".format(t=type(e).__name__, a=e.args)
            tree += message
            return tree

    tree += "{text:'Variable: " + variable.name() + " (" + units_name + ")'},"

    # parents['variable'] = index
    # record = TemporaryStorageItem(
    #     storage=storage,
    #     dict_string="{}".format(parents)
    # )
    # record.save()

    return tree


def build_tree_from_reset(storage, reset, tree, index, parents):
    variable = reset.variable()

    tree += "{text:'Reset: " + variable.name() + "'},"

    # parents['reset'] = index
    # record = TemporaryStorageItem(
    #     storage=storage,
    #     dict_string="{}".format(parents)
    # )
    # record.save()

    return tree


# -------------------- LOADING FUNCTIONS -------------------------------------

def load_model(in_model):
    # Create the CellModel instance:
    model = CellModel(
        name=in_model.name(),
        cellml_id=in_model.id(),
        # TODO save attribution somehow ...
    )
    model.save()

    # TODO Add the encapsulations

    # Add the components
    for c in range(in_model.componentCount()):
        load_component(c, in_model, model)

    # Add the units
    for u in range(in_model.unitsCount()):
        load_compound_units(u, in_model, model)

    # Once everything is loaded into the database, we have to make the connections between items
    for component in model.components.all():
        in_component = in_model.component(component.cellml_index)
        for variable in component.variables.all():
            # Link to units if they exist, or set to None
            in_variable = in_component.variable(variable.cellml_index)
            in_units = in_variable.units()
            if type(in_units).__name__ == 'str':
                # not sure how to deal with base units here ...
                pass
            else:
                variable.units = model.units.filter(name=in_units.name()).first()
                variable.save()

            # Set equivalent variables
            # TODO How to get the parent component of the "other" variable from SWIG?
            # for ev in range(in_variable.equivalentVariableCount()):
            #     in_ev = in_variable.equivalentVariable(ev)
            #     in_other_comp = in_ev.parent()
            #     eq_component = model.components.filter(name=in_other_comp.name()).first()
            #     if eq_component:
            #         eq_var = eq_component.variables.filter(name=in_ev.name()).first()
            #         if eq_var:
            #             variable.equivalent_variables.add(eq_var)

        for reset in component.resets.all():
            # add the variable, test_variable
            in_reset = in_component.reset(reset.cellml_index)
            reset.variable = component.variables.filter(name=in_reset.variable.name()).first()
            reset.test_variable = component.variables.filter(name=in_reset.test_variable.name()).first()

    for c_unit in model.units.all():
        for unit in c_unit.units.all():
            # Want to find the unit in the model whose name = reference, and link
            # to standard unit or compound unit as appropriate
            standard_unit = StandardUnit.objects.filter(name=unit.reference).first()
            if standard_unit:
                unit.based_on_standard_unit = standard_unit
                unit.save()
                continue

            other_unit = model.units.filter(name=unit.reference).first()
            if other_unit:
                unit.based_on_compound_unit = other_unit
                unit.save()
                continue

            # If we get to this point then the unit for this compound unit does not exist in the model: add todo item

    return model


def load_component(index, in_model, model):
    in_component = in_model.component(index)

    out_component = Component(
        name=in_component.name(),
        cellml_index=index,
        cellml_id=in_component.id(),
        model=model
    )
    out_component.save()

    # Load variables in this component
    for v in range(in_component.variableCount()):
        load_variable(v, in_component, out_component)

    # Load resets in this component
    for r in range(in_component.resetCount()):
        load_reset(r, in_component, out_component)

    return


def load_compound_units(index, in_model, model):
    in_units = in_model.units(index)

    if in_units.isBaseUnit():  # TODO check why libcellml has this as *base* unit not *standard* unit?
        # then don't need to add to the database, but do need to reference from model
        try:
            base_unit = CompoundUnit.objects.get(name=in_units.name(), is_standard=True)
        except CompoundUnit.DoesNotExist:
            # TODO must make sure that this is populated through initial data migration?
            return

        model.units.add(base_unit)

        return

    out_compound_units = CompoundUnit(
        name=in_units.name(),
        cellml_index=index,
        model=model,
    )
    out_compound_units.save()

    for u in range(in_units.unitCount()):
        reference, prefix, multiplier, exponent, local_id = in_units.unitAttributes(u)

        unit = Unit(
            cellml_index=u,
            reference=reference,
            prefix_string=prefix,
            multiplier=multiplier,
            exponent=exponent,
            cellml_id=local_id
        )

    # TODO Need to narrow scope to the current model here, at the moment it's searching the whole db!!
        # Have to locate the reference before this will make any sense ...
        su = CompoundUnit.objects.filter(name=reference, is_standard=True).first()
        if su:  # Then is related to a standard unit ...
            unit.compoundunit = su
        else:
            # Try to find named unit item
            cu = CompoundUnit.objects.filter(name=reference).first()
            if cu:
                unit.compoundunit = cu

        unit.save()
        out_compound_units.units.add(unit)

    return


def load_variable(index, in_component, out_component):
    in_variable = in_component.variable(index)
    out_variable = Variable(
        cellml_index=index,
        name=in_variable.name(),
        initial_value=in_variable.initialValue(),
        # interface_type=in_variable.interfaceType(),  # TODO get dictionary of interfaceTypes ...
        component=out_component,
    )
    out_variable.save()


def load_reset(index, in_component, out_component):
    in_reset = in_component.reset(index)

    test_value = Math(
        math_ml=in_reset.test_value()
    )
    test_value.save()

    reset_value = Math(
        math_ml=in_reset.reset_value()
    )
    reset_value.save()

    out_reset = Reset(
        cellml_index=index,
        order=int(in_reset.order()),
        component=out_component,
        reset_value=reset_value,
        test_value=test_value
    )
    out_reset.save()


# ------------------------------------ EDIT FUNCTIONS ----------------------------------------

def get_edit_locals_form(item_model):
    edit_form = modelform_factory(item_model.model_class(), fields=get_local_fields(item_model))
    return edit_form


def get_local_fields(item_model):
    local_fields = [x.name for x in item_model.model_class()._meta.fields if
                    type(x) != ForeignKey and type(x) != ManyToManyField and type(x) != AutoField and
                    type(x) != ManyToOneRel]

    if 'tree' in local_fields:
        local_fields.remove('tree')
    if 'cellml_index' in local_fields:
        local_fields.remove('cellml_index')
    if 'ready' in local_fields:
        local_fields.remove('ready')

    return local_fields


def get_child_connection_fields(item_model):
    m2m_fields = [x.name for x in item_model.model_class()._meta.get_fields(include_parents=False) if
                  type(x) == ManyToManyField]

    fk_fields = [x.name for x in item_model.model_class()._meta.get_fields(include_parents=False) if
                 type(x) == ForeignKey]

    if 'owner' in fk_fields:
        fk_fields.remove('owner')
    if 'imported_from' in fk_fields:
        fk_fields.remove('imported_from')

    return fk_fields, m2m_fields


def get_child_fields(item_model):
    child_fields = [x.name for x in item_model.model_class()._meta.get_fields(include_parents=False) if
                    (type(x) == ForeignKey and x.name != 'owner' and x.name != 'imported_from') or
                    (type(x) == ManyToManyField)]

    return child_fields


def get_item_child_attributes(item):
    fk_fields, m2m_fields = get_child_connection_fields(ContentType.objects.get_for_model(item))

    item_children = []
    for l in m2m_fields:
        m2m = getattr(item, l)
        m2m_2 = getattr(m2m, 'all')()
        for m in m2m_2:
            item_children.append((l, m._meta.model_name, m))

    for l in fk_fields:
        m = getattr(item, l)
        if m is not None:
            item_children.append((l, m._meta.model_name, m))
        else:
            pass

    return item_children


def get_item_local_attributes(item):
    # Get the local attributes of this item (ie: not fk, m2m, o2o)
    local_fields = get_local_fields(ContentType.objects.get_for_model(item))
    item_locals = []
    for l in local_fields:
        item_locals.append((l, getattr(item, l)))

    return item_locals


def get_relationship_menu(item_model):
    """
    This is the dropdown menu for the display page defining adding new relationships
    :param item_model:
    :return:
    """

# --------------------- Others ----------------------------------


# def ajax_import_item(request):
#     message = ''
#     my_style = ''
#     status = ''
#
#     if request.POST:
#         item_type = request.POST.get('item_type')
#         item_index = request.POST.get('item_index')
#         app_name = 'main'
#         try:
#             model_name = MODEL_NAME_DICT[item_type]
#         except KeyError:
#             message = "Unable to find database table for '{type}'".format(type=item_type)
#             status = 400  # "Bad request" code
#
#         # TODO maybe change the format to go through a table so that only tested keys are allowed?
#         if not status:
#             message, my_style, status = eval("cellml_{item_type}_import(request.POST)".format(item_type=item_type))
#
#     data = {
#         'status': status,
#         'message': message,
#         'style': my_style
#     }
#
#     return JsonResponse(data)


# def cellml_import_from_storage(storage_id, item_id):
#     storage = TemporaryStorage.objects.get(id=storage_id)
#     item = storage.items.all()[item_id - 1]
#
#     # translate item.dict_string into instructions for entity to write to database
#     item_dict = literal_eval(item.dict_string)
#
#     # need to store as an orderedDict?  https://stackoverflow.com/questions/5629023/the-order-of-keys-in-dictionaries
#     # so that we retrieve the parents in the right order before the item (eg: component and then variable)
#
#
# def cellml_variable_import(input_dict):
#     """
#     Function to import a variable from CellML into the database
#     :param input_dict:
#     :return:
#     """
#     fields_dict = {
#         'name': input
#     }
#
#     try:
#         new_item, created = Variable.objects.get_or_create(**fields_dict)
#         new_item.save()
#     except Exception as e:
#         message = "Failed to create! {t}: {a}".format(t=type(e).__name__, a=e.args)
#         return message, "update_failure", 0
#
#     if created:
#         message = "Created: {}".format(new_item)
#         style = "update_success"
#         status = 200
#     else:
#         message = "Failed ..."
#         style = "update_failure"
#         status = 400
#
#     return message, style, status
