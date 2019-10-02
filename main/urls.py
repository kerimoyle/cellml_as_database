from django.urls import path

from main import views

urlpatterns = [
    path('test/', views.test, name='test'),
    path('error/', views.error, name='error'),

    # Alphabetical order of views
    path('ajax_validate/', views.ajax_validate, name='ajax_validate'),

    path('ajax_get_validation_list/<item_type>/<int:item_id>/', views.ajax_get_validation_list,
         name='ajax_get_validation_list'),
    path('browse/<item_type>/', views.browse, name='browse'),

    path('copy/<item_type>/<int:item_id>/', views.copy, name='copy'),
    path('create_unit/<cu_id>/<in_modal>', views.create_unit, name='create_unit', ),
    path('create_unit/<cu_id>/', views.create_unit, name='create_unit', kwargs={'in_modal': False}),
    path('create/<item_type>/<in_modal>', views.create, name='create'),
    path('create/<item_type>/', views.create, name='create', kwargs={'in_modal': False}),

    path('delete/<item_type>/<int:item_id>/', views.delete, name='delete'),
    path('delete_unit/<int:unit_id>/', views.delete_unit, name='delete_unit'),
    # path('display/cellmodel/<int:item_id>/', views.display_model, name='display_model'),  # aliased ...
    # path('display/compoundunit/<int:item_id>/', views.display_compoundunit, name='display_compoundunit'),
    # aliased ...
    path('display/math/<int:item_id>/', views.display_math, name='display_math'),
    # path('display/model/<int:item_id>/', views.display_model, name='display_model'),
    # path('display/reset/<int:item_id>/', views.display_reset, name='display_reset'),
    path('display/temporarystorage/<int:item_id>/', views.display_storage, name='display_storage'),
    path('display/<item_type>/<int:item_id>/', views.display, name='display'),

    path('edit_field/<item_type>/<int:item_id>/<item_field>/', views.edit_field, name='edit_field'),
    path('edit_locals/<item_type>/<int:item_id>/', views.edit_locals, name='edit_locals'),
    path('edit_unit/<int:item_id>/', views.edit_unit, name='edit_unit'),

    path('convert_model/<int:item_id>/', views.convert_model, name='convert_model'),

    path('home/', views.home, name='home'),
    path('intro/', views.intro, name='intro'),

    path('link_downstream/<item_type>/<int:item_id>/<related_name>', views.link_downstream, name='link_downstream'),
    path('link_upstream/<item_type>/<int:item_id>/<related_name>', views.link_upstream, name='link_upstream'),
    path('link_remove/', views.link_remove, name='link_remove'),
    path('login_view/', views.login_view, name='login_view'),
    path('logout_view/', views.logout_view, name='logout_view'),

    path('register/', views.register, name='register'),
    path('refresh_error_tree/<item_type>/<int:item_id>/', views.refresh_error_tree, name='refresh_error_tree'),

    path('set_privacy/', views.set_privacy, name='set_privacy'),
    path('set_validity/', views.set_validity, name='set_validity'),
    path('show_errors/<item_type>/<int:item_id>/', views.show_errors, name='show_errors'),

    path('upload/', views.upload, name='upload'),
    # path('upload_check/<int:item_id>/', views.upload_check, name='upload_check'),
    # path('upload_model/', views.upload_model, name='upload_model'),

    path('validate/<item_type>/<int:item_id>/', views.validate, name='validate'),

    path('', views.home, name='home'),

]
# + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
