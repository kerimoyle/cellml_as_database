import libcellml
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.db.models import ForeignKey, ManyToManyField, AutoField, ManyToOneRel, ManyToManyRel
from django.forms import modelform_factory
from django.shortcuts import redirect

from main.models import Variable, CellModel, Component, Reset, CompoundUnit, Unit, \
    Math, Prefix, Person


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

def load_model(in_model, owner):
    # Create the CellModel instance:
    model = CellModel(
        name=in_model.name(),
        cellml_id=in_model.id(),
        owner=owner,
        # TODO save attribution somehow ...
    )
    model.save()

    # TODO Add the encapsulations

    # Add the components
    for c in range(in_model.componentCount()):
        load_component(c, in_model, model, owner)

    # Add the compound units
    for u in range(in_model.unitsCount()):
        load_compound_units(u, in_model, model, owner)

    for u in model.compoundunits.all():
        load_units(u, in_model, model, owner)
        u.save()

    # Once everything is loaded into the database, we have to make the connections between items
    for component in model.components.all():
        in_component = in_model.component(component.cellml_index)
        for variable in component.variables.all():
            # Link to units if they exist, or set to None
            in_variable = in_component.variable(variable.cellml_index)
            in_units = in_variable.units()
            if type(in_units).__name__ == 'str':
                u = CompoundUnit.objects.filter(is_standard=True, name=in_units).first()
                if u is not None:
                    # Then is built-in unit
                    variable.compoundunits.add(u)
                    break

                u = CompoundUnit.objects.filter(name=in_units, models=model).first()
                if u is not None:
                    variable.compoundunits.add(u)

                else:
                    # Then is new base unit.  Create compound unit with no downstream
                    u_new = CompoundUnit(
                        name=in_units,
                        symbol=in_units,
                        is_standard=False,
                        owner=owner,
                    )
                    u_new.save()
                    u_new.models.add(model)
                    variable.save()
                    u_new.variables.add(variable)
            else:
                variable.compoundunits = model.compoundunits.filter(name=in_units.name()).first()
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

    # for c_unit in model.compoundunits.all():
    #     for unit in c_unit.units.all():
    #
    #         other_unit = model.units.filter(name=unit.reference).first()
    #         if other_unit:
    #             unit.based_on_compound_unit = other_unit
    #             unit.save()
    #             continue

    # If we get to this point then the unit for this compound unit does not exist in the model: add todo item

    return model


def load_component(index, in_model, model, owner):
    in_component = in_model.component(index)

    out_component = Component(
        name=in_component.name(),
        cellml_index=index,
        cellml_id=in_component.id(),
        owner=owner,
    )
    out_component.save()
    out_component.models.add(model)

    # Load variables in this component
    for v in range(in_component.variableCount()):
        load_variable(v, in_component, out_component, owner)

    # Load resets in this component
    for r in range(in_component.resetCount()):
        load_reset(r, in_component, out_component, owner)

    # Load math in this component
    if in_component.math():
        math = Math(
            math_ml=in_component.math(),
            owner=owner,
        )
        math.save()
        math.components.add(out_component)

    return


def load_compound_units(index, in_model, model, owner):
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
        owner=owner,
    )
    out_compound_units.save()
    out_compound_units.models.add(model)

    return

    # for u in range(in_units.unitCount()):
    #     reference, prefix_string, multiplier, exponent, local_id = in_units.unitAttributes(u)
    #
    #     prefix = Prefix.objects.get(name=prefix_string)
    #
    #     unit = Unit(
    #         cellml_index=u,
    #         reference=reference,
    #         prefix=prefix,
    #         multiplier=multiplier,
    #         exponent=exponent,
    #         cellml_id=local_id
    #     )
    #
    #     # TODO Need to narrow scope to the current model here, at the moment it's searching the whole db!!
    #     # Have to locate the reference before this will make any sense ...
    #
    #     su = CompoundUnit.objects.filter(name=reference, is_standard=True).first()
    #     if su:  # Then is related to a standard unit ...
    #         unit.base = su
    #     else:
    #         # Try to find named unit item
    #         cu = CompoundUnit.objects.filter(name=reference).first()
    #         if cu:
    #             unit.base = cu
    #
    #     unit.save()
    #     out_compound_units.units.add(unit)
    #
    # return


def load_units(compoundunit, in_model, model, owner):
    in_units = in_model.units(compoundunit.cellml_index)

    for u in range(in_units.unitCount()):
        reference, prefix_string, exponent, multiplier, local_id = in_units.unitAttributes(u)

        prefix = Prefix.objects.get(name=prefix_string)

        unit = Unit(
            cellml_index=u,
            prefix=prefix,
            multiplier=multiplier,
            exponent=exponent,
            cellml_id=local_id,
            name=reference,
            parent_cu=compoundunit,
            owner=owner,
        )
        unit.save()

        # TODO Need to narrow scope to the current model here, at the moment it's searching the whole db!!
        # Have to locate the reference before this will make any sense ...

        base = CompoundUnit.objects.filter(name=reference, models=model).first()
        if base:
            unit.child_cu = base
            unit.save()
        else:
            base = CompoundUnit.objects.filter(name=reference, is_standard=True).first()
            if base:
                unit.child_cu = base
                unit.save()
            else:
                pass

    return


def load_variable(index, in_component, out_component, owner):
    in_variable = in_component.variable(index)
    out_variable = Variable(
        cellml_index=index,
        name=in_variable.name(),
        initial_value=in_variable.initialValue(),
        # interface_type=in_variable.interfaceType(),  # TODO get dictionary of interfaceTypes ...
        owner=owner,
    )
    out_variable.component = out_component
    out_variable.save()


def load_reset(index, in_component, out_component, owner):
    in_reset = in_component.reset(index)

    test_value = Math(
        math_ml=in_reset.test_value(),
        owner=owner,
    )
    test_value.save()

    reset_value = Math(
        math_ml=in_reset.reset_value(),
        owner=owner
    )
    reset_value.save()

    out_reset = Reset(
        cellml_index=index,
        order=int(in_reset.order()),
        component=out_component,
        reset_value=reset_value,
        test_value=test_value,
        owner=owner,
    )
    out_reset.save()


# -------------------------------- EXPORTING FUNCTIONS ---------------------------------

def export_to_cellml_model(in_model):
    """
    Function to create an instance of a CellML model which can then be printed
    :param model: CellModel instance
    :return: libcellml->Model instance
    """

    model = libcellml.Model()

    export_components(in_model, model)

    export_compoundunits(in_model, model)

    return model


def export_components(in_model, model):
    for c in in_model.components.all():
        component = libcellml.Component()
        component.setName(c.name)
        if c.cellml_id is not None:
            component.setId(c.cellml_id)

        for v in c.variables.all():
            variable = libcellml.Variable()

            variable.setName(v.name)
            variable.setId(v.cellml_id)
            if v.compoundunits.count() > 0:
                # many to many field ... which one to set here?
                variable.setUnits(v.compoundunits.all()[0].name)

            # TODO print equivalent variables
            # for e in v.equivalent_variables.all():
            #     variable.addEquivalence(e.name)

            component.addVariable(variable)

        # TODO add resets resets: need to wait for new format to be in libcellml

        # TODO add maths
        if c.maths is not None:
            component.setMath("")
            for m_in in c.maths.all():
                component.appendMath(m_in.math_ml)

        model.addComponent(component)
    return


def export_compoundunits(in_model, model):
    for cu in in_model.compoundunits.all():
        compoundunit = libcellml.Units()
        compoundunit.setName(cu.name)
        compoundunit.setId(cu.cellml_id)

        for u in cu.product_of.all():
            compoundunit.addUnit(
                u.name,
                u.prefix.name,
                u.exponent,
                u.multiplier
            )

        model.addUnits(compoundunit)
    return


# void addUnit(const std::string &reference, const std::string &prefix,
#   double exponent=1.0, double multiplier=1.0)
# u.addUnit('blabla', 'hello', 1.2, 3.4, 'unitid')


# def load_compound_units(index, in_model, model, owner):
#     in_units = in_model.units(index)
#
#     if in_units.isBaseUnit():  # TODO check why libcellml has this as *base* unit not *standard* unit?
#         # then don't need to add to the database, but do need to reference from model
#         try:
#             base_unit = CompoundUnit.objects.get(name=in_units.name(), is_standard=True)
#         except CompoundUnit.DoesNotExist:
#             # TODO must make sure that this is populated through initial data migration?
#             return
#
#         model.units.add(base_unit)
#
#         return
#
#     out_compound_units = CompoundUnit(
#         name=in_units.name(),
#         cellml_index=index,
#         owner=owner,
#     )
#     out_compound_units.save()
#     out_compound_units.models.add(model)
#
#     return


# ------------------------------------ EDIT FUNCTIONS ----------------------------------------

def get_edit_locals_form(item_model):
    edit_form = modelform_factory(item_model.model_class(), fields=get_local_fields(item_model))
    return edit_form


def get_edit_form(item_model, fields):
    edit_form = modelform_factory(item_model.model_class(), fields=fields)
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
    if 'is_standard' in local_fields:
        local_fields.remove('is_standard')
    if 'privacy' in local_fields:
        local_fields.remove('privacy')

    return local_fields


def get_upstream_connection_fields(item_model, excluding=[]):
    m2m_fields = [x.name for x in item_model.model_class()._meta.get_fields(include_parents=False) if
                  type(x) == ManyToManyField]

    fk_fields = [x.name for x in item_model.model_class()._meta.get_fields(include_parents=False) if
                 type(x) == ForeignKey]

    if 'owner' in fk_fields:
        fk_fields.remove('owner')
    if 'imported_from' in fk_fields:
        fk_fields.remove('imported_from')
    if 'annotations' in fk_fields:
        fk_fields.remove('annotations')

    for e in excluding:
        if e in fk_fields:
            fk_fields.remove(e)
        if e in m2m_fields:
            m2m_fields.remove(e)

    return fk_fields, m2m_fields


def get_upstream_fields(item_model, excluding=[]):
    upstream_fields = [x.name for x in item_model.model_class()._meta.get_fields(include_parents=False) if
                       (type(x) == ForeignKey and x.name != 'owner' and x.name != 'imported_from') or
                       (type(x) == ManyToManyField)]

    for e in excluding:
        if e in upstream_fields:
            upstream_fields.remove(e)

    return upstream_fields


def get_item_upstream_attributes(item, excluding=[]):
    fk_fields, m2m_fields = get_upstream_connection_fields(ContentType.objects.get_for_model(item), excluding=[])

    upstream = []
    for l in m2m_fields:
        m2m = getattr(item, l)
        m2m_2 = getattr(m2m, 'all')()
        for m in m2m_2:
            upstream.append((l, m._meta.model_name, m))

    for l in fk_fields:
        m = getattr(item, l)
        if m is not None:
            upstream.append((l, m._meta.model_name, m))
        else:
            pass

    return upstream


def get_downstream_fields(item_model, excluding=[]):
    downstream_fields = [x.name for x in item_model.model_class()._meta.get_fields(include_parents=False) if
                         type(x) == ManyToOneRel or type(x) == ManyToManyRel]

    for e in excluding:
        if e in downstream_fields:
            downstream_fields.remove(e)

    return downstream_fields


def get_item_downstream_attributes(item, excluding=[]):
    downstream_fields = get_downstream_fields(ContentType.objects.get_for_model(item), excluding)

    downstream = []

    for l in downstream_fields:
        m2m = getattr(item, l)
        m2m_2 = getattr(m2m, 'all')()
        for m in m2m_2:
            downstream.append((l, m._meta.model_name, m))

    return downstream


def get_item_local_attributes(item, excluding=[]):
    # Get the local attributes of this item (ie: not fk, m2m, o2o)
    local_fields = get_local_fields(ContentType.objects.get_for_model(item))

    for l in excluding:
        try:
            local_fields.remove(l)
        except KeyError:
            pass

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


# ------------------------------- COPY FUNCTIONS ------------------------------------------

def create_by_shallow_copy(request, item, exclude=[], options=[]):
    """
    This just copies the local attributes of the item from one to another. It is used by both the deep and shallow copy
    functions later on, but the placeholder object creation happens here.
    :param item_type: type of the item
    :param item: source to copy from
    :return: newly created item copied from the from_item
    """

    # imported_entity = ImportedEntity(
    #     source_type=type(item).__name__.lower(),
    #     source_id=item.id,
    # )
    # imported_entity.save()

    old_id = item.id
    item_type = ContentType.objects.get(app_label='main', model=type(item).__name__.lower())

    item.pk = None  # NB: Setting the pk to None and saving triggers the copy
    item.id = None
    item.save()  # Now this is the new object

    item.owner = request.user.person

    try:
        item.is_standard = False
    except Exception as e:
        pass

    # Making sure we pass back the reference to the old object too ...
    old_item = item_type.get_object_for_this_type(id=old_id)
    item.imported_from = old_item
    item.save()

    return old_item, item


def link_copy(request, from_item, to_item, exclude=[], options=[]):
    """
    Copies the related fields by transferring the existing reference not by creating new objects
    :param request: request (for passing back messages)
    :param item_type: type of item to link
    :param from_item: source item
    :param to_item: target item
    :return:
    """

    # Get the item type
    item_type = type(from_item).__name__.lower()
    try:
        item_model = ContentType.objects.get(app_label='main', model=item_type)
    except Exception as e:
        messages.error(request, "Could not find class with name '{t}'".format(t=item_type))
        messages.error(request, "{t}: {a}".format(t=type(e).__name__, a=e.args))
        return redirect('main:error')

    exclude.append('owner')
    exclude.append('imported_from')

    # Get a list of all the relational fields in the model
    fields = [x.name for x in from_item._meta.get_fields() if type(x) == ForeignKey and x.name not in exclude]
    for f in fields:
        setattr(to_item, f, getattr(from_item, f))

    fields = [(x.name, x.field.name) for x in from_item._meta.get_fields()
              if type(x) == ManyToManyRel
              and x.name not in exclude]
    for f, r in fields:
        for related_object in getattr(from_item, f).all():
            getattr(related_object, r).add(to_item)

    fields = [x.name for x in from_item._meta.get_fields()
              if type(x) == ManyToManyField
              and x.name not in exclude]
    for f in fields:
        for related_object in getattr(from_item, f).all():
            getattr(to_item, f).add(related_object)

    fields = [x.name for x in from_item._meta.get_fields() if type(x) == ManyToOneRel and x.name not in exclude]
    for f in fields:
        for related_object in getattr(from_item, f).all():
            getattr(to_item, f).add(related_object)

    to_item.depends_on = from_item
    to_item.imported_from = from_item
    to_item.save()

    return from_item, to_item


def deep_copy(request, from_item, to_item, exclude=[], options=[]):
    """
    Makes a duplicate of all connected items instead of copying them as a link
    :param request:
    :param from_item:
    :param to_item:
    :return:
    """

    # Get a list of all the relational fields in the model
    # fk_fields = [x.name for x in from_item._meta.get_fields() if type(x) == ForeignKey]
    # fk_fields.remove('owner')
    # fk_fields.remove('imported_from')
    # for f in fk_fields:
    #     # Duplicate foreign key item
    #     related_object = getattr(from_item, f)
    #     new_related_object, related_object = create_by_shallow_copy(request, related_object)
    #     deep_copy(request, related_object, new_related_object)
    #     setattr(to_item, f, new_related_object)

    m2o_fields = [x.name for x in from_item._meta.get_fields()
                  if type(x) == ManyToOneRel
                  and x.name not in exclude]

    for f in m2o_fields:
        for related_object in getattr(from_item, f).all():
            # Create new related object
            related_object, new_related_object = create_by_shallow_copy(request, related_object, exclude, options)
            deep_copy(request, related_object, new_related_object, exclude, options)
            getattr(to_item, f).add(new_related_object)

    m2mr_fields = [(x.name, x.field.name) for x in from_item._meta.get_fields()
                   if type(x) == ManyToManyRel
                   and x.name not in exclude]

    for f, r in m2mr_fields:
        for related_object in getattr(from_item, f).all():
            # Create new related object
            related_object, new_related_object = create_by_shallow_copy(request, related_object, exclude, options)
            deep_copy(request, related_object, new_related_object, exclude, options)
            getattr(to_item, f).add(new_related_object)

    # # Upstream manytomany fields still copied as links - have to link to new items
    # m2mf_fields = [x.name for x in from_item._meta.get_fields() if type(x) == ManyToManyField]
    # for f in m2mf_fields:
    #     for related_object in getattr(from_item, f).all():
    #         getattr(to_item, f).add(related_object)

    to_item.depends_on = None
    to_item.imported_from = from_item.imported_from
    to_item.save()

    return from_item, to_item


def copy_item(request, from_item, exclude=[], options=''):
    item_type = type(from_item).__name__.lower()
    try:
        item_model = ContentType.objects.get(app_label='main', model=item_type)
    except Exception as e:
        messages.error(request, "Could not find class with name '{t}'".format(t=item_type))
        messages.error(request, "{t}: {a}".format(t=type(e).__name__, a=e.args))
        return redirect('main:error')

    from_item, to_item = create_by_shallow_copy(request, from_item, exclude, options)
    # Resetting the "from_item" after the copy as the pointers are changed by the change in pk?

    if options == 'link':
        from_item, to_item = link_copy(request, from_item, to_item, exclude, options)

    if options == 'deep':
        from_item, to_item = deep_copy(request, from_item, to_item, exclude, options)

    return from_item, to_item


def detach_links(request, item, exclude=[]):

    m2o_fields = [x.name for x in item._meta.get_fields()
                  if type(x) == ManyToOneRel
                  and x.name not in exclude]

    for f in m2o_fields:
        for related_object in getattr(item, f).all():
            # Remove related objects
            detach_links(request, related_object, exclude)

    m2mr_fields = [(x.name, x.field.name) for x in item._meta.get_fields()
                   if type(x) == ManyToManyRel
                   and x.name not in exclude]
    for f, r in m2mr_fields:
        for related_object in getattr(item, f).all():
            # Remove related object
            detach_links(request, related_object, exclude)

    item.owner = Person.objects.get(user__username="trash")
    item.save()

    return "Could not delete completely as the item is linked.  It has been moved to the recycle bin."


def delete_item(request, item, exclude=[], options=''):

    if options == 'deep':
        m = delete_deep(request, item, exclude)
    else:
        m = item.delete()
    return m


def delete_deep(request, item, exclude=[]):

    if item.owner != request.user.person:
        return "{} skipped - not yours to delete".format(item.name)  # not actually displayed anywhere ... ?

    if item.used_by.count() > 0:
        m = detach_links(request, item, exclude)
        return m

    m2o_fields = [x.name for x in item._meta.get_fields()
                  if type(x) == ManyToOneRel
                  and x.name not in exclude]

    for f in m2o_fields:
        for related_object in getattr(item, f).all():
            # Remove related objects
            delete_deep(request, related_object, exclude)

    m2mr_fields = [(x.name, x.field.name) for x in item._meta.get_fields()
                   if type(x) == ManyToManyRel
                   and x.name not in exclude]

    for f, r in m2mr_fields:
        for related_object in getattr(item, f).all():
            # Remove related object
            delete_deep(request, related_object, exclude)

    return item.delete()

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
