import libcellml
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.db.models import ForeignKey, ManyToManyField, AutoField
from django.forms import modelform_factory, CheckboxSelectMultiple, RadioSelect
from django.shortcuts import render, redirect
from django.urls import reverse

from main.defines import MENU_OPTIONS
from main.functions import build_tree_from_model, load_model, get_edit_locals_form, get_item_local_attributes, \
    get_child_fields, get_item_child_attributes
from main.models import Math, TemporaryStorage, CellModel


def home(request):
    return render(request, 'main/index.html', {'menu': MENU_OPTIONS['home']})


def test(request):
    messages.add_message(request, messages.ERROR, "HELLO!!")

    context = {
        'menu': MENU_OPTIONS['home']
    }
    return render(request, 'main/test.html', context)


# --------------------- CREATE VIEWS --------------------

def create(request, item_type):
    """
    Basic view to create one instance of the @p item_type
    :param request: request
    :param item_type: name of the class which will be created
    :param item_id: (optional) id of the item to edit
    :return: redirect to 'display' view of created item, or return to form with errors
    """

    item_model = None

    try:
        item_model = ContentType.objects.get(app_label="main", model=item_type)
    except Exception as e:
        messages.error(request, "Could not get object type called '{}'".format(item_type))
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

    exclude_fields = ()
    all_fields = [x.name for x in item_model.model_class()._meta.fields]
    if 'tree' in all_fields:
        exclude_fields += ('tree',)
    if 'cellml_index' in all_fields:
        exclude_fields += ('cellml_index',)
    if 'owner' in all_fields:
        exclude_fields += ('owner',)
    if 'ready' in all_fields:
        exclude_fields += ('ready',)

    create_form = modelform_factory(item_model.model_class(), exclude=exclude_fields)

    if request.POST:
        form = create_form(request.POST)
        if form.is_valid():
            item = form.save()
            return redirect(reverse('main:display',
                                    kwargs={'item_type': item_type, 'item_id': item.id}))
    else:
        form = create_form()

    form.helper = FormHelper()
    form.helper.form_method = 'post'
    form.helper.add_input(Submit('submit', "Save"))
    form.helper.form_action = reverse('main:create', kwargs={'item_type': item_type})

    existing_items = item_model.model_class().objects.all()

    context = {
        'item_type': item_type,
        'form': form,
        'existing_items': existing_items,
        'menu': MENU_OPTIONS['create']
    }
    return render(request, 'main/create.html', context)


def copy(request, item_type, item_id):
    """
    Function to duplicate an existing item of item_type
    :param request: request
    :param item_type: the model class to be duplicated
    :param item_id: the id of the item to be duplicated
    :return: redirects to edit page of the new item
    """
    item_model = None
    item = None
    try:
        item_model = ContentType.objects.get(app_label="main", model=item_type)
    except Exception as e:
        messages.error(request, "Could not get object type called '{}'".format(item_type))
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

    try:
        item = item_model.get_object_for_this_type(id=item_id)
    except Exception as e:
        messages.error(request, "Couldn't find {} object with id of '{}'".format(item_type, item_id))
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

        # Duplicate the existing item by removing the id and primary keys and saving ...
    connection_fields = [x.name for x in item._meta.fields if
                         type(x) == ForeignKey or type(x) == ManyToManyField and type(x) != AutoField]

    old_dict = {}
    for c in connection_fields:
        old_dict[c] = getattr(item, c)

    item.pk = None
    item.id = None
    item.name += "_copied"
    item.save()
    # TODO not sure if this will work for the m2m fields??
    for c in connection_fields:
        setattr(item, c, old_dict[c])
    item.save()

    return redirect(reverse('main:display', kwargs={'item_type': item_type, 'item_id': item.id}))


def edit_locals(request, item_type, item_id):
    """
    Basic view to edit the local attributes of an instance of the @p item_type
    :param request: request
    :param item_type: name of the class which will be created
    :param item_id: (optional) id of the item to edit
    :return: redirect to 'display' view of created item, or return to form with errors
    """

    item = None
    try:
        item_model = ContentType.objects.get(app_label="main", model=item_type)
    except Exception as e:
        messages.error(request, "Couldn't find an object type called '{}'".format(item_type))
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

    try:
        item = item_model.get_object_for_this_type(id=item_id)
    except Exception as e:
        messages.error(request, "Couldn't find {} object with id of '{}'".format(item_type, item_id))
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

    edit_form = get_edit_locals_form(item_model)

    if request.POST:
        form = edit_form(request.POST, instance=item)
        if form.is_valid():
            item = form.save()
            return redirect(reverse('main:display',
                                    kwargs={'item_type': item_type, 'item_id': item.id}))
    else:
        form = edit_form(instance=item)

    form.helper = FormHelper()
    form.helper.form_method = "POST"
    form.helper.attrs = {'target': '_top'}  # Triggers reload of the parent page of this modal
    form.helper.form_action = reverse('main:edit_locals', kwargs={'item_type': item_type, 'item_id': item_id})
    form.helper.add_input(Submit('submit', 'Save'))

    context = {
        'item_type': item_type,
        'form': form,
        'item': item
    }
    return render(request, 'main/form_modal.html', context)


def link(request, item_type, item_id, related_name):
    """
    Generic view to link foreign keys and many-to-many fields into a parent item
    :param request: request
    :param item_type: the type of the parent item
    :param item_id: the id of the parent item
    :param related_name: the type of the child item to include in the parent
    :return:
    """

    item_model = None
    item = None
    child_model = None

    try:
        item_model = ContentType.objects.get(app_label="main", model=item_type)
    except Exception as e:
        messages.error(request, "Can't find object type called '{}'".format(item_type))
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

    try:
        item = item_model.get_object_for_this_type(id=item_id)
    except Exception as e:
        messages.error(request, "Can't find '{}' object with id of '{}'".format(item_type, item_id))
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

    r = item._meta.get_field(related_name)
    # child_type = r.related_model()._meta.model_name

    # try:
    #     child_model = ContentType.objects.get(app_label="main", model=child_type)
    # except Exception as e:
    #     messages.error(request, "Can't find object type for the related name of '{}'".format(related_name))
    #     messages.error(request, " ... I tried looking for child_type '{}'".format(child_type))
    #     return redirect('main:error')

    if type(r).__name__ == 'ManyToOneRel' or type(r).__name__ == 'ForeignKey':
        widgets = {related_name: RadioSelect()}
    else:
        widgets = {related_name: CheckboxSelectMultiple()}

    link_form = modelform_factory(item_model.model_class(),
                                  fields=(related_name,),
                                  widgets=widgets)

    if request.POST:
        form = link_form(request.POST, instance=item)
        if form.is_valid():
            item = form.save()
            return redirect(reverse('main:display',
                                    kwargs={'item_type': item_type,
                                            'item_id': item.id}))
    else:
        form = link_form(instance=item)

    form.helper = FormHelper()
    form.helper.form_method = 'post'
    form.helper.attrs = {'target': '_top'}
    form.helper.add_input(Submit('submit', "Save"))
    form.helper.form_action = reverse('main:link',
                                      kwargs={'item_type': item_type, 'item_id': item_id, 'related_name': related_name})

    context = {
        'item_type': item_type,
        'item': item,
        'form': form,
    }
    return render(request, 'main/form_modal.html', context)


# --------------------- DISPLAY VIEWS -------------------

def display(request, item_type, item_id):
    item = None

    try:
        item_model = ContentType.objects.get(app_label="main", model=item_type)
    except Exception as e:
        messages.error(request, "Couldn't find an object type called '{}'".format(item_type))
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

    try:
        item = item_model.get_object_for_this_type(id=item_id)
    except Exception as e:
        messages.error(request, "Couldn't find {} object with id of '{}'".format(item_type, item_id))
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

    # Make the create/edit links here instead of in template so we can tell the difference between parent and child
    # sides?

    context = {
        'item': item,
        'item_type': item_type,
        'child_fields': get_child_fields(item_model),
        'locals': get_item_local_attributes(item),
        'children': get_item_child_attributes(item),
        'menu': MENU_OPTIONS['display'],
    }
    return render(request, 'main/display.html', context)


def display_model(request, item_id):
    model = None

    try:
        model = CellModel.objects.get(id=item_id)
    except Exception as e:
        messages.error(request, "Couldn't find CellModel object with id of '{}'".format(item_id))
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

    context = {
        'model': model,
        'menu': MENU_OPTIONS['display']
    }
    return render(request, 'main/display_model.html', context)


def display_math(request, item_id):
    math = None
    try:
        math = Math.objects.get(id=item_id)
    except Exception as e:
        messages.error(request, "Could not find Math object with id of '{}'".format(item_id))
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

    context = {
        'math': math,
        'menu': MENU_OPTIONS['display']
    }
    return render(request, 'main/display_math.html', context)


def browse(request, item_type):
    item_model = None
    try:
        item_model = ContentType.objects.get(app_label="main", model=item_type)
    except Exception as e:
        messages.error(request, "Couldn't find an object type called '{}'".format(item_type))
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

    # Go through all fields in the item_model:

    # fields = [x.name for x in item_model.model_class()._meta.get_fields() if
    #           type(x) != AutoField ]
    #
    # ids = item_model.model_class().objects.values_list('id')
    #
    # data = serializers.serialize('python', item_model.model_class().objects.all(), fields=fields)
    # data = zip(ids, data)

    items = item_model.model_class().objects.all()

    context = {
        'item_type': item_type,
        'items': items,
        'menu': MENU_OPTIONS['display']
        # 'data': data,
        # 'fields': fields
    }
    return render(request, 'main/browse.html', context)


# -------------------- UPLOAD VIEWS --------------------

def upload(request):
    # Set up import form for cellml text input:
    form_type = modelform_factory(TemporaryStorage, exclude=('tree',))

    if request.POST:
        form = form_type(request.POST, request.FILES)
        if form.is_valid():
            item = form.save()
            return redirect(reverse('main:upload_check',
                                    kwargs={'item_id': item.id}))

    else:
        form = form_type()

    form.helper = FormHelper()
    form.helper.form_method = 'post'
    form.helper.add_input(Submit('submit', "Save"))
    form.helper.form_action = reverse('main:upload')

    context = {
        'form': form,
        'menu': MENU_OPTIONS['upload']
    }
    return render(request, 'main/upload.html', context)


def upload_check(request, item_id):
    # This view makes a scratchpad from the uploaded file, and allows users to select which parts to save
    # retrieve the file
    try:
        storage = TemporaryStorage.objects.get(id=item_id)
    except Exception as e:
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

    # open the file from memory
    try:
        f = open(storage.file.path, "r")
        cellml_text = f.read()
    except Exception as e:
        messages.error("{t}: {a}".format(t=type(e).__name__, a=e.args))
        return redirect('main:error')

    # Parse the model using libcellml:
    parser = libcellml.Parser()
    model = parser.parseModel(cellml_text)

    build_tree_from_model(storage, model)

    context = {
        'storage': storage,
        'model_name': model.name(),
        'tree': storage.tree,
        'menu': MENU_OPTIONS['upload']
    }

    return render(request, 'main/upload_check.html', context)


def upload_model(request):
    # Recreate the CellML model ... TODO should be cached or pickled instead of parsing->loading again?

    storage_id = None
    storage = None

    if request.method == 'POST':
        try:
            storage_id = request.POST.get('storage_id')
        except Exception as e:
            messages.error(request, "Could not get 'storage_id' from request.POST")
            messages.error(request, "{}: {}".format(type(e).__name__, e.args))
            return redirect('main:error')

        try:
            storage = TemporaryStorage.objects.get(id=storage_id)
        except Exception as e:
            messages.error(request, "Could not find storage with id of {}".format(storage_id))
            messages.error(request, "{}: {}".format(type(e).__name__, e.args))
            return redirect('main:error')

        try:
            f = open(storage.file.path, "r")
            cellml_text = f.read()
        except Exception as e:
            messages.error(request, "Could not read the file at '{}'".format(storage.file.path))
            messages.error(request, "{}: {}".format(type(e).__name__, e.args))
            return redirect('main:error')

        # Parse the model using libcellml:
        parser = libcellml.Parser()
        in_model = parser.parseModel(cellml_text)

        # Load into database
        model = load_model(in_model)

        # TODO Need to draw the loaded detailed tree properly, including href components.  Will copy for now ...
        model.tree = storage.tree
        model.save()

        # Delete the TemporaryStorage object
        storage.delete()

        return redirect(reverse('main:display', kwargs={'item_type': 'model', 'item_id': model.id}))

    return redirect(reverse('main:error', kwargs={'message': "Did not receive POST request"}))


# --------------------- ERRORS & MESSAGES ---------------

def error(request):
    return render(request, 'main/error.html', {'menu': MENU_OPTIONS['display']})
