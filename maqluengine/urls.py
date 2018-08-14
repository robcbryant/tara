"""urlconf for the maqlu-engine application"""


from django.urls import path
from . import views

app_name = "maqluengine"
urlpatterns = [
    path('', views.index, name='index'),
    path('dev/', views.dev_index, name='dev_index'),
    path('blogpost/<int:post_id>/', views.blogpost, name='blogpost'),
    path('project/<int:project_id>/', views.project, name='project'),
    path('webpage/<int:webpage_id>/', views.webpage, name='webpage'),
    path('form/<int:form_id>/', views.form, name='form'),
    path('formtype/<int:formtype_id>/', views.formtype, name='formtype'),
    
    path('geoengine/', views.geoengine, name='geoengine'),
    path('browseengine/', views.browseengine, name='browseengine'),
    path('queryengine/', views.queryengine, name='queryengine'),
    
    path('features/', views.features, name='features'),
    path('history/', views.history, name='history'),
    path('documentation/', views.documentation, name='documentation'),
    path('contact/', views.contact, name='contact'),
    path('project/', views.project_list, name='project_list'),
    
    #================================================================================================
    #   API ENDPOINTS
    #================================================================================================
    path('api/', views.api_v1_main, name='api_main'),
    path('api/blogposts/', views.api_v1_blogposts, name='api_blogposts'),
    path('api/blogposts/<int:blogpost_id>/', views.api_v1_blogposts, name='api_blogposts'),
    path('api/projects/', views.api_v1_projects, name='api_projects'),
    path('api/projects/<int:project_id>/', views.api_v1_projects, name='api_projects'),
    path('api/formtypes/', views.api_v1_formtypes, name='api_formtypes'),
    path('api/formtypes/<int:formtype_id>/', views.api_v1_formtypes, name='api_formtypes'),
    path('api/forms/', views.api_v1_forms, name='api_forms'),
    path('api/forms/<int:form_id>/', views.api_v1_forms, name='api_forms'),
    path('api/webpages/', views.api_v1_webpages, name='api_webpages'),
    path('api/webpages/<int:webpage_id>/', views.api_v1_webpages, name='api_webpages'),
]




