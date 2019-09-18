import datetime

import libcellml
import pytz
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import ForeignKey, ManyToManyField, ManyToOneRel, ManyToManyRel, Q
from django.forms import modelform_factory, CheckboxSelectMultiple, RadioSelect
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from main.defines import MENU_OPTIONS, DISPLAY_DICT
from main.forms import DownstreamLinkForm, UnlinkForm, LoginForm, RegistrationForm, CopyForm, DeleteForm
from main.functions import load_model, get_edit_locals_form, get_item_local_attributes, \
    get_item_upstream_attributes, copy_item, \
    delete_item, convert_to_cellml_model, get_item_downstream_attributes, draw_error_tree, draw_object_tree, \
    add_child_errors, draw_error_branch, draw_object_child_tree, get_local_error_messages
from main.models import Math, TemporaryStorage, CellModel, CompoundUnit, Person, Unit, Prefix, Reset
from main.validate import VALIDATE_DICT


def test(request):
    context = {
        'menu': MENU_OPTIONS['home']
    }
    return render(request, 'main/test_drag_and_drop.html', context)


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
                    messages.success(request, "Your registration was successful! Please login below.")
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
        messages.error(request, "{t}: {a}".format(
            t=type(e).__name__,
            a=e.args)
                       )
        return redirect('main:error')

    items = []
    types = ['cellmodel', 'component', 'math', 'compoundunit', 'unit', 'reset', 'variable']
    for t in types:
        items.append((
            t,
            ContentType.objects.get(app_label='main', model=t).get_all_objects_for_this_type().filter(owner=person)))

    context = {
        'person': person,
        'data': items,
        'menu': MENU_OPTIONS['home']
    }
    return render(request, 'main/home.html', context)


# --------------------- CREATE VIEWS --------------------
@login_required
def create(request, item_type, in_modal):
    """
    Basic view to create one instance of the @p item_type
    :param request: request
    :param item_type: name of the class which will be created
    :param in_modal: (optional) whether or not to call the form_modal template
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
    if 'imported_from' in all_fields:
        exclude_fields += ('imported_From',)

    exclude_fields = ['tree', 'cellml_index', 'owner', 'ready', 'is_standard', 'imported_from', 'depends_on',
                      'is_valid', 'errors', 'last_checked']

    create_form = modelform_factory(item_model.model_class(), exclude=exclude_fields)

    if request.POST:
        form = create_form(request.POST)
        if form.is_valid():
            item = form.save()
            item.owner = person
            item.child_list = draw_object_child_tree(item)
            item.save()
            return redirect(reverse('main:display',
                                    kwargs={'item_type': item_type, 'item_id': item.id}))
    else:
        form = create_form()

    form.helper = FormHelper()
    form.helper.form_method = 'post'
    form.helper.form_action = reverse('main:create', kwargs={'item_type': item_type})

    existing_items = item_model.model_class().objects.filter(Q(privacy="public") | Q(owner=person))

    context = {
        'item_type': item_type,
        'form': form,
        'existing_items': existing_items,
        'menu': MENU_OPTIONS['create']
    }
    if in_modal:
        form.helper.attrs = {'target': '_top', 'id': 'modal_form_id'}
        return render(request, 'main/form_modal.html', context)
    else:
        form.helper.add_input(Submit('submit', "Save"))
        return render(request, 'main/create.html', context)


@login_required
def create_unit(request, cu_id, in_modal):
    """
    Creates a unit object - the connection involving prefix/multiplier/exponent between two compound units
    :param request: request
    :param cu_id: the id of the compound unit which is defined by adding this new unit as a factor
    :param in_modal: whether
    :return:
    """

    try:
        cu = CompoundUnit.objects.get(id=cu_id)
    except Exception as e:
        messages.error(request, "Could not get CompountUnit with id={} to add the new Unit to".format(cu_id))
        messages.error(request, "{t}: {a}".format(t=type(e).__name__, a=e.args))
        redirect('main:error')

    try:
        person = request.user.person
    except Exception as e:
        messages.error(request, "Could not get authenticated person from request: please login or register.")
        messages.error(request, "{t}: {a}".format(t=type(e).__name__, a=e.args))
        return redirect('main:error')

    create_form = modelform_factory(Unit, fields=('prefix', 'child_cu', 'multiplier', 'exponent'))

    if request.POST:
        form = create_form(request.POST)
        if form.is_valid():
            item = form.save()
            if item.prefix is None:
                item.prefix = Prefix.objects.get(name="")
            item.owner = person
            item.parent_cu = cu
            item.save()
            return redirect(reverse('main:display',
                                    kwargs={'item_type': 'compoundunit', 'item_id': cu.id}))
    else:
        form = create_form()

    form.helper = FormHelper()
    form.helper.form_method = 'post'
    form.helper.form_action = reverse('main:create_unit', kwargs={'cu_id': cu_id, 'in_modal': in_modal})

    context = {
        'item_type': 'compoundunit',
        'form': form,
        'menu': MENU_OPTIONS['create']
    }
    if in_modal:
        form.helper.attrs = {'target': '_top', 'id': 'modal_form_id'}
        return render(request, 'main/form_modal.html', context)
    else:
        form.helper.add_input(Submit('submit', "Save"))
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

    if request.method == 'POST':
        form = CopyForm(request.POST)
        if form.is_valid():
            options = form.cleaned_data['options']
            item, item_copy = copy_item(request, item,
                                        ['used_by', 'depends_on', 'imported_from', 'imported_to'],
                                        options)
            if item_copy:
                return redirect(reverse('main:display', kwargs={'item_type': item_type, 'item_id': item_copy.id}))

    form = CopyForm()
    form.helper = FormHelper()
    form.helper.attrs = {'target': '_top', 'id': 'modal_form_id'}
    form.helper.form_method = 'post'
    # form.helper.add_input(Submit('submit', "OK"))
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

    if check_ownership(request, item):
        excluding = ['tree', 'cellml_index', 'ready', 'is_standard', 'privacy', 'is_valid', 'last_checked', 'errors']
        edit_form = get_edit_locals_form(item_model, excluding)

        if request.POST:
            form = edit_form(request.POST, instance=item)
            if form.is_valid():
                item = form.save()
                return redirect(reverse('main:display', kwargs={'item_type': item_type, 'item_id': item.id}))
        else:
            form = edit_form(instance=item)

        form.helper = FormHelper()
        form.helper.form_method = "POST"
        form.helper.attrs = {'target': '_top',
                             'id': 'modal_form_id'}  # Triggers reload of the parent page of this modal
        form.helper.form_action = reverse('main:edit_locals', kwargs={'item_type': item_type, 'item_id': item_id})
        # form.helper.add_input(Submit('submit', 'Save'))

        context = {
            'item_type': item_type,
            'form': form,
            'item': item
        }
        return render(request, 'main/form_modal.html', context)
    else:
        context = {
            'item_type': item_type,
            'item': item,
            'modal_text': "You don't have permission to edit this item.  The owner is {}.".format(item.owner)
        }
        return render(request, 'main/form_modal.html', context)


@login_required
def edit_unit(request, item_id):
    item = None
    is_owner = False

    try:
        item = Unit.objects.get(id=item_id)
    except Exception as e:
        messages.error(request, "Couldn't find Unit object with id of '{}'".format(item_id))
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

    if not check_ownership(request, item):
        context = {
            'item': item,
            'modal_text': "You don't have permission to edit this item.  The owner is {}.".format(item.owner)
        }
        return render(request, 'main/form_modal.html', context)

    edit_form = modelform_factory(Unit, fields=('prefix', 'child_cu', 'multiplier', 'exponent'))

    if request.POST:
        form = edit_form(request.POST, instance=item)
        if form.is_valid():
            item = form.save()
            return redirect(reverse('main:display', kwargs={'item_type': 'compoundunit', 'item_id': item.parent_cu.id}))
    else:
        form = edit_form(instance=item)

    form.helper = FormHelper()
    form.helper.form_method = "POST"
    form.helper.attrs = {'target': '_top', 'id': 'modal_form_id'}  # Triggers reload of the parent page of this modal
    form.helper.form_action = reverse('main:edit_unit', kwargs={'item_id': item_id})
    # form.helper.add_input(Submit('submit', 'Save'))

    context = {
        'form': form,
        'item': item
    }
    return render(request, 'main/form_modal.html', context)


@login_required
def edit_field(request, item_type, item_id, item_field):
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

    if check_ownership(request, item):

        all_fields = item_model.model_class()._meta.fields
        excluding = [x.name for x in all_fields if x.name != item_field]

        edit_form = get_edit_locals_form(item_model, excluding)

        if request.POST:
            form = edit_form(request.POST, instance=item)
            if form.is_valid():
                item = form.save()
                return redirect(reverse('main:display', kwargs={'item_type': item_type, 'item_id': item.id}))
        else:
            form = edit_form(instance=item)

        form.helper = FormHelper()
        form.helper.form_method = "POST"
        form.helper.attrs = {'target': '_top',
                             'id': 'modal_form_id'}  # Triggers reload of the parent page of this modal
        form.helper.form_action = reverse('main:edit_field',
                                          kwargs={'item_type': item_type, 'item_id': item_id, 'item_field': item_field})

        context = {
            'item_type': item_type,
            'form': form,
            'item': item
        }
        return render(request, 'main/form_modal.html', context)
    else:
        context = {
            'item_type': item_type,
            'item': item,
            'modal_text': "You don't have permission to edit this item.  The owner is {}.".format(item.owner)
        }
        return render(request, 'main/form_modal.html', context)


# @login_required
# def link_compoundunit_factors(request, item_id):
#     item = None
#     try:
#         item = CompoundUnit.objects.get(id=item_id)
#     except Exception as e:
#         messages.error(request, "Can't find CompoundUnit with id of '{}'".format(item_id))
#         messages.error(request, "{}: {}".format(type(e).__name__, e.args))
#         return redirect('main:error')


@login_required
def link_upstream(request, item_type, item_id, related_name):
    """
    Generic view to link foreign keys and many-to-many fields into a parent item
    :param request: request
    :param item_type: the type of the parent item
    :param item_id: the id of the parent item
    :param related_name: the type of the upstream item to include in the parent
    :return:
    """

    item_model = None
    item = None
    upstream_model = None

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

    if not check_ownership(request, item):
        messages.error(request, "Cannot create link from an item you don't own.")
        return redirect(reverse('main:display', kwargs={'item_type': item_type, 'item_id': item_id}))

    r = item._meta.get_field(related_name)

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
    form.fields[related_name].queryset = r.related_model.objects.filter(owner=request.user.person)
    form.helper.attrs = {'target': '_top', 'id': 'modal_form_id'}
    form.helper.form_action = reverse('main:link_upstream',
                                      kwargs={'item_type': item_type, 'item_id': item_id, 'related_name': related_name})

    context = {
        'item_type': item_type,
        'item': item,
        'form': form,
    }
    return render(request, 'main/form_modal_searchable.html', context)


@login_required
def link_downstream(request, item_type, item_id, related_name):
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

    if not check_ownership(request, item):
        messages.error(request, "Cannot create link to an item you don't own.")
        return redirect(reverse('main:display', kwargs={'item_type': item_type, 'item_id': item_id}))

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
        form = DownstreamLinkForm(request.POST, item_type=item_type, item_id=item_id, parent_type=parent_type)

        if form.is_valid():
            add_me = form.cleaned_data['link_to_id']

            for related_object in add_me:
                getattr(related_object, parent_field).add(item)

            # TODO how to direct to correct tab on the display page?
            return redirect("{url}#tab_{tab}".format(url=reverse('main:display',
                                                                 kwargs={'item_type': item_type,
                                                                         'item_id': item.id}),
                                                     tab=related_name))
    else:
        form = DownstreamLinkForm(item_type=item_type,
                                  item_id=item_id,
                                  parent_type=parent_type)

    form.helper = FormHelper()
    form.helper.form_method = 'post'
    form.helper.attrs = {'target': '_top', 'id': 'modal_form_id'}
    form.helper.form_action = reverse('main:link_downstream',
                                      kwargs={'item_type': item_type, 'item_id': item_id, 'related_name': related_name})

    context = {
        'item_type': item_type,
        'item': item,
        'form': form,
    }
    return render(request, 'main/form_modal_searchable.html', context)


# ---------------------- DELETE VIEWS -------------------

@login_required
def link_remove(request):
    if request.method == "POST":
        form = UnlinkForm(request.POST)
        if form.is_valid():

            item_type = form.data['unlink_item_type']
            item_id = int(form.data['unlink_item_id'])
            related_name = form.data['unlink_related_name']
            related_id = int(form.data['unlink_related_id'])

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

            if not check_ownership(request, item):
                messages.error(request, "Cannot remove link when you don't own the item.")
                return redirect(reverse('main:display', kwargs={'item_type': item_type, 'item_id': item_id}))

            r = item._meta.get_field(related_name)
            link_type = type(r)

            if link_type == ForeignKey:
                setattr(item, related_name, None)
                item.save()
            elif link_type == ManyToManyRel:
                getattr(item, related_name).remove(related_id)
            elif link_type == ManyToManyField:
                getattr(item, related_name).remove(related_id)
            elif link_type == ManyToOneRel:
                related_item = r.related_model.objects.get(id=related_id)
                setattr(related_item, item_type, None)
                related_item.save()
            else:
                pass

            return redirect(
                "{url}#tab_{tab}".format(
                    url=reverse('main:display', kwargs={'item_type': item_type, 'item_id': item_id}),
                    tab=related_name))


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

    if not check_ownership(request, item):
        return render(request, 'main/form_modal.html',
                      {'modal_text': "Sorry, you don't have permission to delete this item."})

    if request.method == 'POST':
        form = DeleteForm(request.POST)
        if form.is_valid():
            name = item.name
            id = item.id
            options = form.cleaned_data['options']
            m = delete_item(request, item, ['used_by', 'imported_from', 'imported_to', 'depends_on'], options)

            try:
                item_model.get_object_for_this_type(id=item_id)
                messages.success(request,
                                 "The {t} {n} was moved to the Recycle Bin as it has links to other items.".format(
                                     t=item_type,
                                     n=item.name))
                return redirect('main:home')
            except Exception as e:
                messages.success(request, "The {t} {n} was deleted successfully.".format(t=item_type, n=item.name))
                return redirect('main:home')
        else:
            messages.error(request, "The {t} {n} item could not be deleted.".format(t=item_type, n=item.name))
            return redirect(reverse("main:display", kwargs={'item_type': item_type, 'item_id': item_id}))

    form = DeleteForm()
    form.helper = FormHelper()
    form.helper.form_action = reverse('main:delete', kwargs={'item_type': item_type, 'item_id': item_id})
    form.helper.attrs = {'target': '_top', 'id': 'modal_form_id'}
    form.helper.form_method = 'POST'
    # form.helper.add_input(Submit('submit', 'Yes, delete it'))

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
        person = request.user.person
    except Exception as e:
        messages.error(request, "Couldn't find a registered user.  Please login.")
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

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

    # Check visibility for user
    if not (item.owner == person or item.privacy == 'public'):
        messages.error(request, "Sorry, you do not have permission to view this {i}.  "
                                "Please contact the owner ({f} {l})for access.".format(
            i=item_type,
            f=item.owner.first_name,
            l=item.owner.last_name))
        return redirect('main:error')

    local_attrs = get_item_local_attributes(item, ['cellml_index',
                                                   'privacy',
                                                   'error_tree',
                                                   'child_list'])
    local_fields = []
    skip_fields = ['is_valid', 'last_checked']
    for local in local_attrs:
        errs = item.errors.filter(fields__icontains=local[0])
        validity = None if local[0] in skip_fields else errs.count() == 0

        local_fields.append((local[0], local[1], errs, validity))

    can_change_privacy = len(
        get_item_upstream_attributes(item, ['errors', 'owner', 'imported_from', 'annotations'])
    ) == 0

    data = []
    for tab in DISPLAY_DICT[item_type]['tabs']:
        field = tab['field']
        data.append((
            field,
            tab['obj_type'],
            getattr(item, field).all(),
            tab['title'],
            tab['template']
        ))

    present_in = []
    for tab in DISPLAY_DICT[item_type]['present_in']:
        field = tab['field']
        present_in.append((
            field,
            tab['obj_type'],
            getattr(item, field),
            tab['title']
        ))

    foreign_keys = []
    for tab in DISPLAY_DICT[item_type]['foreign_keys']:
        field = tab['field']
        foreign_keys.append((
            field,
            tab['obj_type'],
            getattr(item, field),
            tab['title']
        ))

    # TODO This should be moved to wherever the item can be altered, including by downstream m2m fields
    item.child_list = draw_object_child_tree(item)
    item.save()

    context = {
        'item': item,
        'item_type': item_type,
        'data': data,
        'present_in': present_in,
        'foreign_keys': foreign_keys,
        'summary_tab': DISPLAY_DICT[item_type]['summary_template'],
        'validity_tab':
            None if DISPLAY_DICT[item_type]['summary_template'] is None
            else DISPLAY_DICT[item_type]['validity_template'],
        'error_tree': None if item.error_tree is None else item.error_tree['tree_html'],
        'locals': local_fields,
        'menu': MENU_OPTIONS['display'],
        'can_edit': request.user.person == item.owner,
        'can_change_privacy': can_change_privacy,
    }
    return render(request, 'main/display.html', context)


@login_required
def display_storage(request, item_id):
    item = None
    try:
        item = TemporaryStorage.objects.get(id=item_id)
    except Exception as e:
        messages.error(request, "Couldn't find TemporaryStorage object with id of '{}'".format(item_id))
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

    context = {
        'item': item,
        'item_type': 'temporarystorage',
        'menu': MENU_OPTIONS['display'],
        'can_edit': request.user.person == item.owner
    }
    return render(request, 'main/display_storage.html', context)


@login_required
def display_compoundunit(request, item_id):
    item = None
    try:
        item = CompoundUnit.objects.get(id=item_id)
    except Exception as e:
        messages.error(request, "Couldn't find CompoundUnit object with id of '{}'".format(item_id))
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

    formula = []
    multiplier = 1
    for u in item.product_of.all():
        multiplier *= u.multiplier
        if u.exponent == 1:
            formula.append("{p}{u} ".format(p=u.prefix.symbol, u=u.child_cu.symbol))
        else:
            formula.append("{p}{u}<sup>{e}</sup>".format(p=u.prefix.symbol, u=u.child_cu.symbol, e=u.exponent))

    context = {
        'item': item,
        'item_type': 'compoundunit',
        'menu': MENU_OPTIONS['display'],
        'can_edit': request.user.person == item.owner,
        'formula': formula,
        'multiplier': multiplier,
        'can_change_privacy': len(get_item_upstream_attributes(item)) == 0,
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
        'item': model,
        'item_type': 'cellmodel',
        'menu': MENU_OPTIONS['display'],
        'can_edit': request.user.person == model.owner,
        'can_change_privacy': True,
        'last_checked': "{}".format(model.last_checked.strftime("%b. %d, %Y, %-I:%M %p")),
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
def display_reset(request, item_id):
    item = None
    try:
        item = Reset.objects.get(id=item_id)
    except Exception as e:
        messages.error(request, "Could not find Reset object with id of '{}'".format(item_id))
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

    foreign_keys = []
    for tab in DISPLAY_DICT['reset']['foreign_keys']:
        field = tab['field']
        foreign_keys.append((
            field,
            tab['obj_type'],
            getattr(item, field),
            tab['title']
        ))

    context = {
        'item': item,
        'item_type': "reset",
        'menu': MENU_OPTIONS['display'],
        'can_edit': request.user.person == item.owner,
        'foreign_keys': foreign_keys,
        # 'item_fields': ['variable', 'test_variable', 'reset_value', 'test_value', 'component']
    }
    return render(request, 'main/display_reset.html', context)


@login_required
def browse(request, item_type):
    try:
        person = request.user.person
    except Exception as e:
        messages.error(request, "Cannot find registered user.  Please create a login for yourself.")
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

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

    items = item_model.model_class().objects.filter(Q(owner=person) | Q(privacy='public'))

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
    try:
        person = request.user.person
    except Exception as e:
        messages.error(request, "Could not get an authenticated user.  Please login or register.")
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

    # Set up import form for cellml text input:
    form_type = modelform_factory(TemporaryStorage, exclude=('tree', 'owner'))

    if request.POST:
        form = form_type(request.POST, request.FILES)
        if form.is_valid():
            storage = form.save()
            storage.owner = request.user.person
            storage.save()

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
            if parser.errorCount() > 0:
                for e in range(0, parser.errorCount()):
                    err = parser.error(e)
                    messages.error(request,
                                   "{}".format(err.description()))
                return redirect('main:error')

            # validator = libcellml.Validator()
            # validator.validateModel(in_model)
            # if validator.errorCount() > 0:
            #     for e in range(0, validator.errorCount()):
            #         err = validator.error(e)
            #         messages.error(request,
            #                        "{}".format(err.description()))
            #     return redirect('main:error')

            # Load into database
            model = load_model(in_model, person)

            # Keep track of origins
            # imported_from = ImportedEntity(
            #     source_type="temporarystorage",
            #     source_id=storage.id,
            #     attribution="Uploaded from {}".format(storage.file.name)
            # )
            # imported_from.save()

            model.uploaded_from = storage.file.name
            model.name = storage.model_name
            model.owner = request.user.person
            model.imported_from = None
            model.privacy = 'private'
            model.child_list = draw_object_child_tree(model)
            model.save()

            # Delete the TemporaryStorage object, also deletes the uploaded file TODO Check what is wanted here?
            storage.delete()

            return redirect(reverse('main:display', kwargs={'item_type': 'cellmodel', 'item_id': model.id}))

        return redirect(reverse('main:error', kwargs={'message': "Did not receive POST request"}))

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


# @login_required
# def upload_check(request, item_id):
#     # This view makes a scratchpad from the uploaded file, and allows users to select which parts to save
#     # retrieve the file
#     try:
#         storage = TemporaryStorage.objects.get(id=item_id)
#     except Exception as e:
#         messages.error(request, "{}: {}".format(type(e).__name__, e.args))
#         return redirect('main:error')
#
#     # open the file from memory
#     try:
#         f = open(storage.file.path, "r")
#         cellml_text = f.read()
#     except Exception as e:
#         messages.error("{t}: {a}".format(t=type(e).__name__, a=e.args))
#         return redirect('main:error')
#
#     # Parse the model using libcellml:
#     parser = libcellml.Parser()
#     model = parser.parseModel(cellml_text)
#
#     build_tree_from_model(storage, model)
#
#     context = {
#         'storage': storage,
#         'model_name': storage.model_name,
#         'tree': storage.tree,
#         'menu': MENU_OPTIONS['upload'],
#     }
#
#     return render(request, 'main/upload_check.html', context)
#
#
# @login_required
# def upload_model(request):
#     try:
#         person = request.user.person
#     except Exception as e:
#         messages.error(request, "Could not get an authenticated user.  Please login or register.")
#         messages.error(request, "{}: {}".format(type(e).__name__, e.args))
#         return redirect('main:error')
#
#     # TODO should be cached or pickled instead of parsing->loading again?
#
#     storage_id = None
#     storage = None
#
#     if request.method == 'POST':
#         try:
#             storage_id = request.POST.get('storage_id')
#         except Exception as e:
#             messages.error(request, "Could not get 'storage_id' from request.POST")
#             messages.error(request, "{}: {}".format(type(e).__name__, e.args))
#             return redirect('main:error')
#
#         try:
#             storage = TemporaryStorage.objects.get(id=storage_id)
#         except Exception as e:
#             messages.error(request, "Could not find storage with id of {}".format(storage_id))
#             messages.error(request, "{}: {}".format(type(e).__name__, e.args))
#             return redirect('main:error')
#
#         try:
#             f = open(storage.file.path, "r")
#             cellml_text = f.read()
#         except Exception as e:
#             messages.error(request, "Could not read the file at '{}'".format(storage.file.path))
#             messages.error(request, "{}: {}".format(type(e).__name__, e.args))
#             return redirect('main:error')
#
#         # Parse the model using libcellml:
#         parser = libcellml.Parser()
#         in_model = parser.parseModel(cellml_text)
#
#         # Load into database
#         model = load_model(in_model, person)
#
#         imported_from = ImportedEntity(
#             source_type="temporarystorage",
#             source_id=storage.id,
#             attribution="Uploaded from {}".format(storage.file.name)
#         )
#         imported_from.save()
#
#         # TODO Need to draw the loaded detailed tree properly, including href components.  Will copy for now ...
#         model.tree = storage.tree
#         model.uploaded_from = storage.file.name
#         model.name = storage.model_name
#         model.owner = request.user.person
#         model.imported_from = imported_from
#         model.save()
#
#         # Delete the TemporaryStorage object, also deletes the uploaded file
#         storage.delete()  # TODO Removed this for now ... not sure how best to handle it wrt import references?
#
#         return redirect(reverse('main:display', kwargs={'item_type': 'model', 'item_id': model.id}))
#
#     return redirect(reverse('main:error', kwargs={'message': "Did not receive POST request"}))


# --------------------- ERRORS & MESSAGES ---------------

def error(request):
    return render(request, 'main/error.html', {'menu': MENU_OPTIONS['display']})


# ------------------------- EXPORT VIEWS ----------------------------

def convert_model(request, item_id):
    # want to make sure that we can write valid cellml from a linked model
    model = None

    try:
        person = request.user.person
    except Exception as e:
        messages.error(request, "Couldn't find a registered user.  Please login.")
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

    try:
        model = CellModel.objects.get(id=item_id)
    except Exception as e:
        messages.error(request, "Could not find model with id={id}.".format(id=item_id))
        messages.error(request, "{}: {}".format(type(e).__name__, e.args))
        return redirect('main:error')

    cellml_model = convert_to_cellml_model(model)
    printer = libcellml.Printer()
    cellml_text = printer.printModel(cellml_model)

    #
    # temp_path = '{}/{}'.format(settings.MEDIA_ROOT, 'temp')
    # temp_file = '{}/{}/{}'.format(settings.MEDIA_ROOT, 'temp', file_name)
    #
    # if not os.path.exists(temp_path):
    #     os.makedirs(temp_path)
    #
    # document.save(temp_file)
    #
    # response = HttpResponse(open(temp_file, 'rb').read())
    # response['Content-Type'] = 'mimetype/submimetype'
    # response['Content-Disposition'] = 'attachment; filename={filename}'.format(filename=file_name)
    #
    # return response

    context = {
        'cellml_text': cellml_text,
        'model': model
    }
    return render(request, 'main/export.html', context)


# TODO write to file view

# ------------------------------------ PERMISSIONS & PRIVACY ---------------------------------
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
        return False

    return True


def set_privacy(request):
    if request.method == "POST":

        item_id = request.POST.get('item_id')
        item_type = request.POST.get('item_type')
        privacy_level = request.POST.get('privacy_level')

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

        # Check item for parents - if the item has upstream items then can't set its privacy independently

        upstream = get_item_upstream_attributes(item)
        if len(upstream):
            # then cannot set the privacy here, need to do it at the upstream item instead
            messages.error(request, "Privacy cannot be set for this item here, please set it at the "
                                    "upstream item instead.")
            return redirect(reverse('main:display', kwargs={'item_type': item_type, 'item_id': item_id}))

        item.privacy = privacy_level
        item.save()

        item_list = get_item_downstream_attributes(item)
        for name, model_name, downstream in item_list:
            if downstream.owner == item.owner:
                downstream.privacy = item.privacy
                downstream.save()

        return redirect(reverse('main:display', kwargs={'item_type': item_type, 'item_id': item_id}))

    else:
        messages.error("Did not get POST request")
        return redirect('main:error')


# --------------------------------- ERROR VIEWS -----------------------

def show_errors(request, item_type, item_id):
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

    # TODO This is slow ...
    tree = []
    tree = add_child_errors(item, tree)

    context = {
        'item': item,
        'item_type': item_type,
        'errors': item.errors.all(),
        'tree': tree,
        'last_checked': "{}".format(item.last_checked.strftime("%b. %d, %Y, %-I:%M %p")),
        'can_edit': request.user.person == item.owner,
    }

    return render(request, 'main/show_errors.html', context)


# ------------------------------- AJAX FUNCTIONS ----------------------------------------


def validate(request, item_type, item_id):
    """
    :param request:
    :param item_type: the name of the item type to be validated
    :param item_id: the object id
    :return:
    """

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

    # Select the function to call from the dictionary
    is_valid = VALIDATE_DICT[item_type](item)
    item.is_valid = is_valid
    item.last_checked = datetime.datetime.now(pytz.utc)

    item.save()

    style = "btn btn-secondary validity_banner_{}".format(item.is_valid)

    local_attrs = get_item_local_attributes(item, ['cellml_index',
                                                   'privacy',
                                                   'error_tree',
                                                   'child_list'])
    local_fields = []
    skip_fields = ['is_valid', 'last_checked']
    for local in local_attrs:
        errs = item.errors.filter(fields__icontains=local[0])
        errors = []
        for e in errs:
            errors.append("{}: {}<br>".format(e.spec, e.hints))

        validity = None if local[0] in skip_fields else errs.count() == 0

        local_fields.append((local[0], local[1], errors, validity))

    data = {
        'status': 200,
        'style': style,
        'last_checked': "{}".format(item.last_checked.strftime("%b. %d, %Y, %-I:%M %p")),
        # 'errors': errors,
        'fields': local_fields
    }

    return JsonResponse(data)


def ajax_validate(request):
    """
    :param request:
    :param item_type: the name of the item type to be validated
    :param item_id: the object id
    :return:
    """

    item = None
    item_type = request.GET.get('item_type')
    item_id = request.GET.get('item_id')

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

    # Select the function to call from the dictionary
    is_valid = VALIDATE_DICT[item_type](item)
    item.is_valid = is_valid
    item.last_checked = datetime.datetime.now(pytz.utc)

    style = "validity_list_{}".format(item.is_valid)
    # error_tree = draw_object_error_tree(item)
    error_tree = get_local_error_messages(item)
    item.error_tree = {'tree_html': error_tree}

    item.child_list = draw_object_child_tree(item)

    item.save()

    data = {
        'status': 200,
        # 'style': style,
        'html': error_tree,
        'is_valid': is_valid,
    }

    return JsonResponse(data)


def ajax_get_validation_list(request, item_type, item_id):
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

    tree = draw_object_tree(item)

    data = {
        'status': 200,
        'tree': tree
    }
    return JsonResponse(data)


def refresh_error_tree(request, item_type, item_id):
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

    error_tree, error_count = draw_error_tree(item)
    item.error_tree = {'tree_html': error_tree, 'error_count': error_count}
    item.save()

    data = {
        'status': 200,
        'tree_html': item.error_tree['tree_html'],
    }

    return JsonResponse(data)


def set_validity(request):
    # TODO not sure why this doesn't work with a POST request?
    item_id = request.GET.get('item_id')
    item_type = request.GET.get('item_type')
    todo = request.GET.get('todo')

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

    item.is_valid = int(todo) == 0
    error_tree, length_of_tree = draw_error_branch(item)
    item.error_tree = {'tree_html': error_tree, 'error_count': length_of_tree}
    item.save()

    data = {
        'status': 200
    }
    return JsonResponse(data)
