import libcellml
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import ForeignKey, ManyToManyField, AutoField, ManyToOneRel
from django.forms import modelform_factory, CheckboxSelectMultiple, RadioSelect
from django.shortcuts import render, redirect
from django.urls import reverse

from main.defines import MENU_OPTIONS
from main.forms import ReverseLinkForm, UnlinkForm, LoginForm, RegistrationForm, CopyForm, DeleteForm
from main.functions import build_tree_from_model, load_model, get_edit_locals_form, get_item_local_attributes, \
    get_child_fields, get_item_child_attributes, get_parent_fields, get_item_parent_attributes
from main.models import Math, TemporaryStorage, CellModel, CompoundUnit, Person, ImportedEntity


def test(request):
    messages.add_message(request, messages.ERROR, "HELLO!!")

    context = {
        'menu': MENU_OPTIONS['home']
    }
    return render(request, 'main/test.html', context)


def intro(request):
    return render(request, 'main/index.html', {'menu': MENU_OPTIONS['home']})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # Test whether there's a user with this username
            user = User.objects.filter(username=username).first()
            if user is not None:
                # User exists, now test password
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    if 'next' in request.GET:
                        return redirect(request.GET.get('next'))
                    return redirect('main:home')
                else:
                    messages.error(request, "Your password is not correct.  Please try again.")
            else:
                # User does not exist
                messages.error(request,
                               "Sorry, the username '{}' was not found.  "
                               "Please check it's correct, or register as a new user.".format(username))

    form = LoginForm()
    context = {
        'form': form,
    }

    return render(request, 'main/login.html', context)


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            repeat_password = form.cleaned_data['repeat_password']

            if password != repeat_password:
                messages.error(request, "The passwords do not match")
            else:
                # Test whether there's a user with this username
                user = User.objects.filter(username=username).first()
                if user is not None:
                    # User exists already
                    messages.error(request,
                                   "A user with that username already exists.  "
                                   "Please login instead, or choose another name.")
                else:
                    user = User(username=username)
                    user.save()
                    user.set_password(password)
                    user.save()
                    person = Person(user=user,
                                    first_name=form.cleaned_data['first_name'],
                                    last_name=form.cleaned_data['last_name'],
                                    email=form.cleaned_data['email']
                                    )
                    person.save()
                    return redirect('main:home')
    form = RegistrationForm()
    context = {
        'form': form,
    }
    return render(request, 'main/register.html', context)


def logout_view(request):
    logout(request)
    return redirect('main:home')


@login_required
def home(request):
    try:
        person = request.user.person
    except Exception as e:
        messages.error(request, "Could not get person instance")
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

    items = []
    types = ['cellmodel', 'component', 'math', 'compoundunit', 'unit', 'reset', 'variable']
    for type in types:
        items.append((
            type,
            ContentType.objects.get(app_label='main', model=type).get_all_objects_for_this_type().filter(owner=person)))

    context = {
        'person': person,
        'data': items,
        'menu': MENU_OPTIONS['home']
    }
    return render(request, 'main/home.html', context)


# --------------------- CREATE VIEWS --------------------
@login_required
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

    try:
        person = request.user.person
    except Exception as e:
        messages.error(request, "Could not get authenticated person from request: please login or register.")
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
    if 'is_standard' in all_fields:
        exclude_fields += ('is_standard',)

    create_form = modelform_factory(item_model.model_class(), exclude=exclude_fields)

    if request.POST:
        form = create_form(request.POST)
        if form.is_valid():
            item = form.save()
            item.owner = person
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


@login_required
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

    # TODO Protect with POST
    if request.method == 'POST':
        form = CopyForm(request.POST)
        if form.is_valid():

            # Duplicate the existing item by removing the id and primary keys and saving ...
            connection_fields = [x.name for x in item._meta.fields if
                                 type(x) == ForeignKey or type(x) == ManyToManyField and type(x) != AutoField]

            old_dict = {}
            for c in connection_fields:
                old_dict[c] = getattr(item, c)

            old_item_id = item.id
            attribution = "Copied from: {} ({})".format(item.name, item.owner)

            # NB: Setting the pk to None and saving triggers the copy
            item.pk = None
            item.id = None
            item.name += " (copy)"
            item.save()

            # TODO How to make deep copy? See issue #2
            for c in connection_fields:
                setattr(item, c, old_dict[c])
            item.owner = request.user.person

            imported_entity = ImportedEntity(
                source_type=item_type,
                source_id=old_item_id,
                attribution=attribution,
            )
            imported_entity.save()
            item.imported_from = imported_entity
            item.save()

            return redirect(reverse('main:display', kwargs={'item_type': item_type, 'item_id': item.id}))

    form = CopyForm()
    form.helper = FormHelper()
    form.helper.attrs = {'target': '_top'}
    form.helper.form_method = 'post'
    form.helper.add_input(Submit('submit', "OK"))
    form.helper.form_action = reverse('main:copy', kwargs={'item_type': item_type, 'item_id': item_id})

    context = {
        'form': form,
        'modal_text': 'Do you really want to send {}: "{}" to your library? '
                      'This will make a copy and allow you to edit it.'.format(item_type, item.name)
    }

    return render(request, 'main/form_modal.html', context)


@login_required
def edit_locals(request, item_type, item_id):
    """
    Basic view to edit the local attributes of an instance of the @p item_type
    :param request: request
    :param item_type: name of the class which will be created
    :param item_id: (optional) id of the item to edit
    :return: redirect to 'display' view of created item, or return to form with errors
    """

    item = None
    is_owner = False

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

    check_ownership(request, item)

    edit_form = get_edit_locals_form(item_model)

    if request.POST:
        form = edit_form(request.POST, instance=item)
        if form.is_valid():
            item = form.save()
            return redirect(reverse('main:display', kwargs={'item_type': item_type, 'item_id': item.id}))
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


@login_required
def link_forwards(request, item_type, item_id, related_name):
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

    check_ownership(request, item)

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
    form.helper.form_action = reverse('main:link_forwards',
                                      kwargs={'item_type': item_type, 'item_id': item_id, 'related_name': related_name})

    context = {
        'item_type': item_type,
        'item': item,
        'form': form,
    }
    return render(request, 'main/form_modal.html', context)


@login_required
def link_backwards(request, item_type, item_id, related_name):
    """
        Generic view to link parent onetomanyrel fields to the current item
        :param request: request
        :param item_type: the type of the current item
        :param item_id: the id of the current item
        :param related_name: the type of the parent item to link
        :return:
        """

    item_model = None
    item = None
    parent_model = None

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

    check_ownership(request, item)

    r = item._meta.get_field(related_name)
    parent_type = r.related_model()._meta.model_name
    parent_field = r.field.name

    try:
        parent_model = ContentType.objects.get(app_label="main", model=parent_type)
    except Exception as e:
        messages.error(request, "Can't find object type for the related name of '{}'".format(related_name))
        messages.error(request, " ... I tried looking for parent of type '{}'".format(parent_type))
        return redirect('main:error')

    if request.POST:
        form = ReverseLinkForm(request.POST, item_type=item_type, item_id=item_id, parent_type=parent_type)

        if form.is_valid():
            parent = form.cleaned_data['link_to_id']
            # try:
            #     parent = parent_model.get_object_for_this_type(id=parent_id)
            # except Exception as e:
            #     messages.error(request, "Can't find '{}' object with id of '{}'".format(parent_type, parent_id))
            #     messages.error(request, "{}: {}".format(type(e).__name__, e.args))
            #     return redirect('main:error')

            setattr(parent, r.field, [item_id])

            return redirect(reverse('main:display',
                                    kwargs={'item_type': item_type,
                                            'item_id': item.id}))
    else:
        form = ReverseLinkForm(item_type=item_type, item_id=item_id, parent_type=parent_type)

    form.helper = FormHelper()
    form.helper.form_method = 'post'
    form.helper.attrs = {'target': '_top'}
    form.helper.add_input(Submit('submit', "Save"))
    form.helper.form_action = reverse('main:link_backwards',
                                      kwargs={'item_type': item_type, 'item_id': item_id, 'related_name': related_name})

    context = {
        'item_type': item_type,
        'item': item,
        'form': form,
    }
    return render(request, 'main/form_modal.html', context)


# ---------------------- DELETE VIEWS -------------------

@login_required
def link_remove(request):
    if request.method == "POST":
        form = UnlinkForm(request.POST)
        if form.is_valid():

            item_type = form.data['unlink_item_type']
            item_id = form.data['unlink_item_id']
            related_name = form.data['unlink_related_name']
            related_id = form.data['unlink_related_id']

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

            check_ownership(request, item)

            r = item._meta.get_field(related_name)
            link_type = type(r)

            if link_type == ForeignKey:
                setattr(item, related_name, None)
                item.save()
            elif link_type == ManyToManyField:
                m2m = getattr(item, related_name)

            elif link_type == ManyToOneRel:
                pass
            else:
                pass

            return redirect(reverse('main:display', kwargs={'item_type': item_type, 'item_id': item_id}))


@login_required
def delete(request, item_type, item_id):
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

    if request.method == 'POST':
        form = DeleteForm(request.POST)
        if form.is_valid():
            check_ownership(request, item)
            item.delete()
            return redirect('main:home')

    form = DeleteForm()
    form.helper = FormHelper()
    form.helper.form_action = reverse('main:delete', kwargs={'item_type': item_type, 'item_id': item_id})
    form.helper.attrs = {'target': '_top'}
    form.helper.form_method = 'POST'
    form.helper.add_input(Submit('submit', 'Yes, delete it'))

    context = {
        'form': form,
        'modal_text': "Are you sure you want to delete '{i}'?".format(i=item.name)
    }

    return render(request, 'main/form_modal.html', context)


# --------------------- DISPLAY VIEWS -------------------
@login_required
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

    child_fields = get_child_fields(item_model)
    local_attrs = get_item_local_attributes(item, ['notes', 'name'])
    children = get_item_child_attributes(item)

    parent_fields = get_parent_fields(item_model)
    parents = get_item_parent_attributes(item)

    context = {
        'item': item,
        'item_type': item_type,
        'child_fields': child_fields,
        'locals': local_attrs,
        'children': children,
        'parent_fields': parent_fields,
        'parents': parents,
        'menu': MENU_OPTIONS['display'],
        'can_edit': request.user.person == item.owner
    }
    return render(request, 'main/display.html', context)


@login_required
def display_compoundunit(request, item_id):
    item = None
    try:
        item = CompoundUnit.objects.get(id=item_id)
    except Exception as e:
        messages.error(request, "Couldn't find CompoundUnit object with id of '{}'".format(item_id))
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

    context = {
        'item': item,
        'menu': MENU_OPTIONS['display'],
        'can_edit': request.user.person == item.owner
    }
    return render(request, 'main/display_compoundunit.html', context)


@login_required
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
        'menu': MENU_OPTIONS['display'],
        'can_edit': request.user.person == model.owner
    }
    return render(request, 'main/display_model.html', context)


@login_required
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
        'menu': MENU_OPTIONS['display'],
        'can_edit': request.user.person == math.owner
    }
    return render(request, 'main/display_math.html', context)


@login_required
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
@login_required
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


@login_required
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
        'model_name': storage.model_name,
        'tree': storage.tree,
        'menu': MENU_OPTIONS['upload'],
    }

    return render(request, 'main/upload_check.html', context)


@login_required
def upload_model(request):
    try:
        person = request.user.person
    except Exception as e:
        messages.error(request, "Could not get an authenticated user.  Please login or register.")
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

    # TODO should be cached or pickled instead of parsing->loading again?

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
        model = load_model(in_model, person)

        # TODO Need to draw the loaded detailed tree properly, including href components.  Will copy for now ...
        model.tree = storage.tree
        model.uploaded_from = storage.file.name
        model.name = storage.model_name
        model.owner = request.user.person
        model.save()

        # Delete the TemporaryStorage object, also deletes the uploaded file
        storage.delete()

        return redirect(reverse('main:display', kwargs={'item_type': 'model', 'item_id': model.id}))

    return redirect(reverse('main:error', kwargs={'message': "Did not receive POST request"}))


# --------------------- ERRORS & MESSAGES ---------------

def error(request):
    return render(request, 'main/error.html', {'menu': MENU_OPTIONS['display']})


# ------------------------------------ PERMISSIONS ------------------------------------------
def check_ownership(request, item):
    try:
        is_owner = item.owner == request.user.person
    except Exception as e:
        messages.error(request, "Could not get person from user instance.")
        messages.error(request, "{t}: {m}".format(t=type(e).__name__, m=e.args))
        return redirect("main:error")

    if not is_owner:
        messages.error(request, "You don't have edit permissions for this item.  Use the 'Send to my library' button "
                                "to import a copy you can edit.")
        return redirect(reverse("main:display", kwargs={'item_type': type(item).__name__, 'item_id': item.id}))

    return True
