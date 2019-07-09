from django.urls import path

from main import views

urlpatterns = [
    path('test/', views.test, name='test'),
    path('error/', views.error, name='error'),

    # Alphabetical order of views
    path('browse/<item_type>/', views.browse, name='browse'),

    path('copy/<item_type>/<int:item_id>/', views.copy, name='copy'),
    path('create/<item_type>/', views.create, name='create'),

    path('display/math/<int:item_id>/', views.display_math, name='display_math'),
    path('display/cellmodel/<int:item_id>/', views.display_model, name='display_model'),  # aliased ...
    path('display/model/<int:item_id>/', views.display_model, name='display_model'),

    path('display/<item_type>/<int:item_id>/', views.display, name='display'),

    path('edit_locals/<item_type>/<int:item_id>/', views.edit_locals, name='edit_locals'),

    path('link/<item_type>/<int:item_id>/<related_name>', views.link, name='link'),

    path('upload/', views.upload, name='upload'),
    path('upload_check/<int:item_id>/', views.upload_check, name='upload_check'),
    path('upload_model/', views.upload_model, name='upload_model'),

    path('', views.home, name='home'),

]
# + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
