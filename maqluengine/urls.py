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
    path('formtype/<int:formtype_id>/<int:page_num>/', views.formtype, name='formtype'),
    
    path('geoengine/', views.geoengine, name='geoengine'),
    path('browseengine/', views.browseengine, name='browseengine'),
    path('queryengine/', views.queryengine, name='queryengine'),
    
    path('features/', views.features, name='features'),
    path('history/', views.history, name='history'),
    path('documentation/', views.documentation, name='documentation'),
    path('contact/', views.contact, name='contact'),
    path('project/', views.project_list, name='project_list'),
    
    #================================================================================================
    #   RESTful API ENDPOINTS
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
    
    #================================================================================================
    #   CUSTOM BACKEND API ENDPOINTS
    #================================================================================================    
    path('xapi/get_projects/', views.get_projects, name='get_projects'),
    path('xapi/get_formtypes/', views.get_formtypes, name='get_formtypes'),
    path('xapi/get_rtypes/', views.get_rtypes, name='get_rtypes'),
    path('xapi/get_deep_rtypes/', views.get_deep_rtypes, name='get_deep_rtypes'),
    path('xapi/get_form_rtypes/', views.get_form_rtypes, name='get_form_rtypes'),
    path('xapi/get_formtype_forms/', views.get_formtype_forms, name='get_formtype_forms'),
    path('xapi/get_geospatial_formtypes/', views.get_geospatial_formtypes, name='get_geospatial_formtypes'),
    path('xapi/get_forms_search/', views.get_forms_search, name='get_forms_search'),
    
    path('xapi/run_master_query_engine/', views.run_master_query_engine, name='run_master_query_engine'),
    path('xapi/navigate_master_query_pagination/', views.navigate_master_query_pagination, name='navigate_master_query_pagination'),
    path('xapi/check_progress_query/', views.check_progress_query, name='check_progress_query'),

    
]




