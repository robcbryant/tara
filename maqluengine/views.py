
#################################################################################################################################################################################################################################################################################################################################
#################################################################################################################################################################################################################################################################################################################################
#################################################################################################################################################################################################################################################################################################################################
#                  Views.Py
#################################################################################################################################################################################################################################################################################################################################
#  *File coded by Robert Bryant and Malkia Oketch
#  *This views.py will serve as the public front-end and essentially replicate the admin.py file I've already written but with limited functionality.
#  *Because it's a public API, this will have no acccess to MODIFY or DELETE items from the database--it can only ACCESS them through GET requests
#  *This is created on behalf of an UPENN Museum project directed by Holly Pittman, and Steve Tinney
#  *Licensing has not yet been determined by the project so distribution is not allowed until source is made available on GIT with an associated license file
#
#
#===========================================================================================================================================================
from django.contrib.admin.views.main import ChangeList
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.safestring import mark_safe
from datetime import datetime
from django.utils.http import urlencode
from django.contrib import messages
from django.contrib.auth.models import User
import csv
import sys
from django.db.models import Q, Count, Max
import re
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render
from django.template import RequestContext
import urllib
from django.conf import settings
from django.contrib import admin
from maqluengine.models import *
from .models import FormProject, Form, FormRecordAttributeType, FormRecordAttributeValue
from .models import FormRecordReferenceType, FormRecordReferenceValue, FormType
from django.urls import reverse
from django.utils.safestring import mark_safe    
from django.urls import resolve

from django.utils.functional import cached_property
from django.contrib.admin import AdminSite
from django.http import HttpResponse
from django.urls import re_path, include
from django.views import generic
from django.http import Http404

from time import sleep
from django.contrib.staticfiles.storage import staticfiles_storage

import json
from django.core.serializers.json import DjangoJSONEncoder

#DEPRECATED  -- Probably safe to delete -- from django.utils.encoding import smart_text

from django.shortcuts import redirect
import random
import time
from django.core import serializers

import uuid
import math
import zipfile
import io
import contextlib

from django.urls import resolve
from django.shortcuts import render
import inspect #Needed for getting method names

import copy

from django.db import connections
from django.db.models.query import QuerySet


from django.views.decorators.csrf import requires_csrf_token
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

###########################################################################################################
#      ERROR / INFO LOGGER SETUP
###########################################################################################################
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
hdlr = logging.FileHandler('/home/tara/log/django-db-log.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 









###########################################################################################################        
###########################################################################################################




##==========================================================================================================================    
##==========================================================================================================================    
##  HELPER FUNCTIONS  ****************************************************************************************************
##==========================================================================================================================  

def SECURITY_log_security_issues(user, viewname, errormessage, META):
    #This just prints some information to the server log about any errors/attempted hacks that need to be flagged
    FLAG = "!!!! SECURITY FLAG !!!!  ===>  "
    try: FLAG += "User: PUBLIC  - Access Level: PUBLIC  - in View: " + viewname + "  -- UserIP: " +  str(META.get('HTTP_X_FORWARDED_FOR', '') or META.get('REMOTE_ADDR')) + " - with Message: " + errormessage
    except Exception as inst: FLAG += str(inst) + "  SOMETHING WENT WRONG - in View: " + viewname + "  -- UserIP: " +  str(META.get('HTTP_X_FORWARDED_FOR', '') or META.get('REMOTE_ADDR')) +  " - with Message: " + errormessage
    logger.info(FLAG)
 
 
def get_api_endpoints():

    #------------------------------------------------------------------------------------------------------------------------------------
    #:::This endpoint returns a JSON list of all urls to the relevant custom API endpoints in a key:value json object for admin views to pass to their
    #   --templates, which the javascript functions will access to get dynamic URLS without having to change them later
    #
    #   This endpoint is not project specific so there is no security by project--only the access level of being an admin user
    #------------------------------------------------------------------------------------------------------------------------------------
    #Make a key value list of our URLS and add them by name
    
    jsonData = {}


    #Get Endpoints
    jsonData['get_rtypes'] = reverse('maqluengine:get_rtypes')
    jsonData['get_projects'] = reverse('maqluengine:get_projects')
    jsonData['get_formtypes'] = reverse('maqluengine:get_formtypes')
    jsonData['get_deep_rtypes'] = reverse('maqluengine:get_deep_rtypes')
    jsonData['get_form_rtypes'] = reverse('maqluengine:get_form_rtypes')
    jsonData['get_forms_search'] = reverse('maqluengine:get_forms_search')
    
    jsonData['get_formtype_forms'] = reverse('maqluengine:get_formtype_forms')
    jsonData['get_geo_formtypes'] = reverse('maqluengine:get_geospatial_formtypes')

    
    #Run Various Tools Endpoints
    jsonData['run_master_query_engine'] = reverse('maqluengine:run_master_query_engine')
    jsonData['run_master_query_pagination'] = reverse('maqluengine:navigate_master_query_pagination')
    jsonData['run_check_progress_query'] = reverse('maqluengine:check_progress_query')
  
    #Public API
    jsonData['api_webpages'] = reverse('maqluengine:api_webpages')
    
    
    #convert python dict to a json string and send it back as a response
    jsonData = json.dumps(jsonData)
    return jsonData       



def get_unique_rtype_val_list(code, entity_pk, parent_formtype):
    form_rval_list = {}    
    #parent_formtype = FormType.objects.get(pk=request.POST['formtype_pk'])
    #Setup out necessary lists etc.
    new_form_rval_list = {}
    distinct_value_list = []          
    logger.info("IN THE UNIQUE VAL FUNCTION")
    if   code == "DEEP_FRAT":   # We need to get all the unique rvals of the provided related FRAT        
        #Load our DEEP FRAT
        entity_type = FormRecordAttributeType.objects.get(pk=entity_pk, flagged_for_deletion=False) 
        distinct_value_list = entity_type.formrecordattributevalue_set.order_by('record_value').distinct().values_list('record_value', flat=True)
        distinct_value_list = list(distinct_value_list)
        logger.info("****** in the main function")
        logger.info(distinct_value_list)
        #Do some last minute cleanup here, like sorting the lists etc.
        distinct_value_list = list(set(distinct_value_list))            
                  
  
    elif code == "DEEP_FRRT":   # We need to get all the unique form IDs of the FRRT's related FRRTs FormType
        #Load our DEEP FRAT
        entity_type = FormRecordReferenceType.objects.get(pk=entity_pk, flagged_for_deletion=False) 
        test_list = entity_type.formrecordreferencevalue_set.values_list('record_reference__form_name', flat=True)
        test_list = list(set(test_list))
        logger.info(test_list)
        #Do some last minute cleanup here, like sorting the lists etc.
        distinct_value_list = test_list   

    elif code == "DEEP_FORMID":     # We need to get all the unique form IDs of the FRRT's related FormType
        entity_type = FormRecordReferenceType.objects.get(pk=entity_pk, flagged_for_deletion=False)
        test_list = entity_type.formrecordreferencevalue_set.values_list('record_reference__form_name', flat=False)
        test_list = list(set(test_list))
        logger.info(test_list)
        #Do some last minute cleanup here, like sorting the lists etc.
        distinct_value_list = test_list   
    elif code == "FORMID":      # We need to get all the unique form IDs of this current FormType
        entity_type = FormType.objects.get(pk=entity_pk, flagged_for_deletion=False)    
        distinct_value_list = entity_type.form_set.order_by('form_name').distinct().values_list('form_name', flat=False)
    elif code == "FRAT":        #We need to get all the unique values of the provided FRAT's RVALs
        entity_type = FormRecordAttributeType.objects.get(pk=entity_pk, flagged_for_deletion=False)    
        distinct_value_list = entity_type.formrecordattributevalue_set.order_by('record_value').distinct().values_list('record_value', flat=False)
        distinct_value_list = list(distinct_value_list)
        logger.info("****** in the main function")
        logger.info(distinct_value_list)
        form_rval_list = entity_type.formrecordattributevalue_set.values('form_parent__pk','record_value')   
                    
    elif code == "BACK_FRRT":
        #We need a distinct list of the given frrt's formtype_parent form ids
        #We then need a form list of the CURRENT formtype's forms that have a match
        #  So using the same Grid Square Metaphor--we have a reverse lookup to "Object Forms" that are referencing a grid square.
        #       **First let's get a list of all the Grid Squares
        #       **Then we need a list of all the Object Forms referencing each grid square in a loop and add them to a list to return
        entity_type = FormRecordReferenceType.objects.get(pk=entity_pk, flagged_for_deletion=False) 
        #Load up our grid squares
        forms = parent_formtype.form_set.all();
        #activate the query to load it in cache before we loop through it
        if forms:
            for parent_form in forms:
                values = []
                #Do the reverse query lookup to get all the frrvs referencing the main parent form
                back_reference_frrvs = parent_form.ref_to_value_form.all()
                #Now we need to store all these frrv's parent forms' form names in a list and attach it to our current parent form in the loop
                if back_reference_frrvs:
                    for back_ref_frrv in back_reference_frrvs:
                        values.append(back_ref_frrv.form_parent.form_name)
                    #Make sure we only have distinct values
                    values = list(set(values))
                    #Now add our list with injected commas as a string to out value lists
                    distinct_value_list.append(",".join(values))
                    new_form_rval_list[parent_form.pk] = ",".join(values)
                else:
                    new_form_rval_list[parent_form.pk] = "" 
        #sort our list and add it to our JSON
        distinct_value_list = sorted(distinct_value_list)    
        
    elif code == "BACK_DEEP_FRAT":
        back_frat_pk, frrt_pk = entity_pk.split(',')
        entity_type = FormRecordAttributeType.objects.get(pk=back_frat_pk, flagged_for_deletion=False) 
        frrt_ref = FormRecordReferenceType.objects.get(pk=frrt_pk, flagged_for_deletion=False) 
        forms = frrt_ref.form_type_reference.form_set.all()
        #First we need a distinct list of the back frat's unique values
       
        #Now we need a list of all the parent formtype(the formtype that's making the backwards request to the back frat) and their values for this FRAT
        new_form_rval_list = {}#parent_formtype.formrecordattributevalue_set.values('form_parent__pk','record_value')   

        if forms:
            for form in forms:
                try:
                    #Get all the FRRVs linking to this form 
                    ref_val = form.ref_to_value_form.filter(record_reference_type__pk=frrt_pk)
                    #Use the first FRRV from the list (for now)
                    logger.info( ref_val)
                    logger.info( ref_val.count())
                    if ref_val:
                        values = []
                        logger.info( "Working?")
                        for refval in ref_val:
                            values.append(refval.form_parent.formrecordattributevalue_set.filter(record_attribute_type__pk=back_frat_pk, record_attribute_type__flagged_for_deletion=False)[0].record_value)
                        logger.info( "Working?")
                        values = list(set(values)) 
                        teststring =  ",".join(values)
                        logger.info( teststring)
                        distinct_value_list.append(teststring)
                        new_form_rval_list[form.pk] = teststring
                except:
                    new_form_rval_list[form.pk] = ""
        distinct_value_list = list(set(distinct_value_list))                  
    logger.info("ABOUT TO EXIT THE UNIQUE VAL FUNCTION")    
    distinct_value_list = filter(None, distinct_value_list)
    return list(distinct_value_list)

    
#=======================================================================================================================================================================================================================================
#=======================================================================================================================================================================================================================================
#       END OF CUSTOM HELPER FUNCTIONS
#=======================================================================================================================================================================================================================================
#=======================================================================================================================================================================================================================================        

     
##==========================================================================================================================    
##==========================================================================================================================    
##  START OF COMPLEX API ENDPOINTS   ****************************************************************************************************
##==========================================================================================================================  
#=======================================================#
#   GET_PROJECTS() *RECYCLING
#=======================================================#   
def get_projects(request, **kwargs):
    #----------------------------------------------------------------------------------------------------------------------------
    #   This Endpoint returns a list of all projects. This is used mainly by the query engine
    #   --to figure out which rtypes to search by when a record reference type is chosen.
    ERROR_MESSAGE = ""
    
    #We need to return a json list of all formtype RTYPES that match the provided formtype pk
    #let's get all the public projects, which may not include our own, so let's redundantly merge it and then call distinct()
    publicProjects = FormProject.objects.filter(is_public=True)

    finalJSON = {}
    project_list = []
    
    if publicProjects:
        for aProject in publicProjects:
           project_list.append({"name":aProject.name, "pk":aProject.pk})
            
        finalJSON['project_list'] = project_list
        finalJSON = json.dumps(finalJSON)
        return HttpResponse(finalJSON, content_type="application/json" )
    else: ERROR_MESSAGE += "Error: no projects were found"

    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'views.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")    
    
#=======================================================#
#   GET_FORMTYPES() *RECYCLING
#=======================================================#   
def get_formtypes(request, **kwargs):

    #----------------------------------------------------------------------------------------------------------------------------
    #   This Endpoint returns a list of all formtypes for a provided project pk. This is used mainly by the query engine
    #   --to figure out which formtypes to add to a dropdown select by when a project is chosen.
    ERROR_MESSAGE = ""
    
    #We need to return a json list of all formtype RTYPES that match the provided formtype pk
    #Let's get all available public formtypes not in recycling
    allFormTypes = FormType.objects.filter(is_public=True, project__pk=request.GET['project_pk'], flagged_for_deletion=False)
        
    if allFormTypes:
        finalJSON = {}
        formtype_list = []

        for aFormType in allFormTypes:
           formtype_list.append({"name":aFormType.form_type_name, "pk":aFormType.pk})
            
        finalJSON['formtype_list'] = formtype_list
        finalJSON = json.dumps(finalJSON)
        return HttpResponse(finalJSON, content_type="application/json" )
        
    else: ERROR_MESSAGE += "Error: no form types were found for this project"

    
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'views.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")    
   
#=======================================================#
#   GET_GEOSPATIAL_FORMTYPES() *RECYCLING
#=======================================================#   
def get_geospatial_formtypes(request, **kwargs):         
    #----------------------------------------------------------------------------------------------------------------------------
    #   This Endpoint returns a list of all formtypes for a provided project pk. This is used mainly by the query engine
    #   --to figure out which formtypes to add to a dropdown select by when a project is chosen.
    ERROR_MESSAGE = ""

    #Let's get all available public formtypes not in recycling--unless the formtypes are from the users current, project.
    #If it is the users current project, then don't use a is_public filter
    logger.info( request.POST['project_pk']  + "  :  ")

    allFormTypes = FormType.objects.filter(is_public=True, project__pk=request.GET['project_pk'], flagged_for_deletion=False)
        
    if allFormTypes:
        finalJSON = {}
        formtype_list = []

        for aFormType in allFormTypes:
            #if aFormType.form_geojson_string != None:
            formtype_list.append({"name":aFormType.form_type_name, "pk":aFormType.pk})
            
        finalJSON['formtype_list'] = formtype_list
        finalJSON = json.dumps(finalJSON)
        return HttpResponse(finalJSON, content_type="application/json" )
        
    else: ERROR_MESSAGE += "Error: no form types were found for this project"
    
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'views.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")    
   
   
      
#=======================================================#
#   GET_FORMTYPE_FORMS()   *Recycling            
#=======================================================#    
def get_formtype_forms(request, **kwargs):
    #------------------------------------------------------------------------------------------------------------------------------------
    #:::This endpoint returns a JSON list of all form names and pk values attached to a specific formtype. It's used mainly to
    #   --to help drop-down menu widgets function, but may be used by other features as well.
    #
    #------------------------------------------------------------------------------------------------------------------------------------
    ERROR_MESSAGE = ""
    
    currentFormType = FormType.objects.get(pk=request.GET['formtype_pk'])                       
    if currentFormType.is_public and currentFormType.flagged_for_deletion == False:
        jsonData = {}
        form_list = []
        jsonData['form_list'] = form_list
        
        #*** RECYCLING BIN *** Make sure Forms are filtered by their deletion flags
        for aForm in currentFormType.form_set.all().filter(flagged_for_deletion=False):
            currentForm = {}
            currentForm['form_label'] = aForm.form_name
            currentForm['form_pk'] = aForm.pk
            form_list.append(currentForm)
        #convert python dict to a json string and send it back as a response
        jsonData = json.dumps(jsonData)
        return HttpResponse(jsonData, content_type="application/json")    
    else: ERROR_MESSAGE += "Error: Either the requested formtype doesn't exist or you are attempting to access a private formtype!"                

    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'views.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")        



#=======================================================#
#   GET_RTYPES *RECYCLING
#=======================================================#   
def get_rtypes(request, **kwargs):
    #----------------------------------------------------------------------------------------------------------------------------
    #   This Endpoint returns a list of all rtypes for a provided formtype pk. This is used mainly by the query engine
    #   --to figure out which formtypes to add to a dropdown select by when a project is chosen.
    ERROR_MESSAGE = ""
    
    if 'formtype_pk' in request.GET:    currentFormType = FormType.objects.get(pk=request.GET['formtype_pk'])
    else:                               currentFormType = FormRecordReferenceType.objects.get(pk=request.GET['frrt-pk']).form_type_reference
    #If the requested formtype isn't the user's project, and flagged as being inaccessible then stop the request
    if currentFormType.flagged_for_deletion or currentFormType.is_public == False:
        ERROR_MESSAGE += "Error: You are attempting to access records that don't exist. This probably occurred because your client attempted altering the GET data before sending"
    #Otherwise we are in the clear so grab the list and return it
    else:
        finalJSON = {}
        rtypeList = []    
        #***RECYCLING BIN***  Make sure that the returned FRAT AND FRRTS are filtered by their deletion flags. Don't want them returned in the query
        for FRAT in currentFormType.formrecordattributetype_set.all().filter(flagged_for_deletion=False, is_public=True):
            currentRTYPE = {}
            currentRTYPE['label'] = FRAT.record_type
            currentRTYPE['pk'] = FRAT.pk
            currentRTYPE['rtype'] = 'FRAT'
            rtypeList.append(currentRTYPE)
        #***RECYCLING BIN***  Make sure that the returned FRAT AND FRRTS are filtered by their deletion flags. Don't want them returned in the query    
        for FRRT in currentFormType.ref_to_parent_formtype.all().filter(flagged_for_deletion=False, is_public=True):
            currentRTYPE = {}
            currentRTYPE['label'] = FRRT.record_type
            currentRTYPE['pk'] = FRRT.pk
            if FRRT.form_type_reference: currentRTYPE['ref_formtype_pk'] = FRRT.form_type_reference.pk
            else: currentRTYPE['ref_formtype_pk'] = "None"
            currentRTYPE['rtype'] = 'FRRT'
            rtypeList.append(currentRTYPE)
       
        #sort our rtype list by the label
        rtypeList = sorted(rtypeList, key=lambda k: k['label']) 
        
        #Return the JSON response
        finalJSON['rtype_list'] = rtypeList
        finalJSON = json.dumps(finalJSON)
        return HttpResponse(finalJSON, content_type="application/json" )

    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'views.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")    


#=======================================================#
#   GET_DEEP_RTYPES *RECYCLING
#=======================================================#   
def get_deep_rtypes(request, **kwargs):         
    #----------------------------------------------------------------------------------------------------------------------------
    #   This Endpoint returns a list of all rtypes AND their DEEP related rtypes for a provided formtype pk. This is used mainly by the query engine
    #   --to figure out which formtypes to add to a dropdown select by when a project is chosen.
    ERROR_MESSAGE = ""
    

    currentFormType = FormType.objects.get(pk=request.GET['formtype_pk'])
    #If the requested formtype isn't the user's project, and flagged as being inaccessible then stop the request
    if currentFormType.flagged_for_deletion or currentFormType.is_public == False:
        ERROR_MESSAGE += "Error: You are attempting to access records that don't exist. This probably occurred because your client attempted altering the POST data before sending"
    #Otherwise we are in the clear so grab the list and return it
    else:
        finalJSON = {}
        rtypeList = []    
     
        #***RECYCLING BIN***  Make sure that the returned FRAT AND FRRTS are filtered by their deletion flags. Don't want them returned in the query
        for FRAT in currentFormType.formrecordattributetype_set.all().filter(flagged_for_deletion=False, is_public=True):
            currentRTYPE = {}
            currentRTYPE['label'] = FRAT.record_type
            currentRTYPE['pk'] = FRAT.pk
            currentRTYPE['rtype'] = 'FRAT'
            rtypeList.append(currentRTYPE)
        #***RECYCLING BIN***  Make sure that the returned FRAT AND FRRTS are filtered by their deletion flags. Don't want them returned in the query    
        for FRRT in currentFormType.ref_to_parent_formtype.all().filter(flagged_for_deletion=False, is_public=True):
            currentRTYPE = {}
            currentRTYPE['label'] = FRRT.record_type
            currentRTYPE['pk'] = FRRT.pk
            if FRRT.form_type_reference: currentRTYPE['ref_formtype_pk'] = FRRT.form_type_reference.pk
            else: currentRTYPE['ref_formtype_pk'] = "None"
            currentRTYPE['rtype'] = 'FRRT'
            rtypeList.append(currentRTYPE)
            #Now look for all the RTYPES of this particular FRRT and add the DEEP RTYPES to our list
            deepFRATs = FRRT.form_type_reference.formrecordattributetype_set.all().filter(flagged_for_deletion=False, is_public=True)
            if deepFRATs:
                for deepFRAT in deepFRATs:
                    currentDeepRTYPE = {}
                    currentDeepRTYPE['label'] = FRRT.record_type + " :: " + deepFRAT.record_type
                    currentDeepRTYPE['pk'] = deepFRAT.pk
                    currentDeepRTYPE['rtype'] = 'DEEP-FRAT'
                    currentDeepRTYPE['parent_pk'] = FRRT.pk
                    rtypeList.append(currentDeepRTYPE)
            deepFRRTs = FRRT.form_type_reference.ref_to_parent_formtype.all().filter(flagged_for_deletion=False, is_public=True)
            if deepFRRTs:
                for deepFRRT in deepFRRTs:
                    currentDeepRTYPE = {}
                    currentDeepRTYPE['label'] = FRRT.record_type + " :: " + deepFRRT.record_type
                    currentDeepRTYPE['pk'] = deepFRRT.pk
                    currentDeepRTYPE['rtype'] = 'DEEP-FRRT'  
                    currentDeepRTYPE['parent_pk'] = FRRT.pk
                    if FRRT.form_type_reference: currentDeepRTYPE['ref_formtype_pk'] = deepFRRT.form_type_reference.pk
                    else: currentDeepRTYPE['ref_formtype_pk'] = "None"
                    rtypeList.append(currentDeepRTYPE)
        # Let's try getting all the reverse relationships, e.g. the formtypes that reference this requested formtype. E.g. If this is
        #   is a set of geospatial grids at a site, there might be an object formtype that contains a reference to it. Rather than add
        #   a reference to objects from the grids, let's look for them indirectly
        referencingFRRTs = FormRecordReferenceType.objects.filter(form_type_reference__pk=currentFormType.pk, flagged_for_deletion=False, is_public=True)
        if referencingFRRTs:
            for FRRT in referencingFRRTs:
                currentRTYPE = {}
                currentRTYPE['label'] = FRRT.form_type_parent.form_type_name
                currentRTYPE['pk'] = FRRT.pk
                currentRTYPE['ref_formtype_pk'] = FRRT.form_type_parent.pk
                currentRTYPE['rtype'] = 'BACK-FRRT'
                rtypeList.append(currentRTYPE)     
                deepFRATs = FRRT.form_type_parent.formrecordattributetype_set.all().filter(flagged_for_deletion=False, is_public=True)
                if deepFRATs:
                    for deepFRAT in deepFRATs:
                        currentDeepRTYPE = {}
                        currentDeepRTYPE['label'] = currentRTYPE['label'] + " :: " + deepFRAT.record_type
                        currentDeepRTYPE['pk'] = str(deepFRAT.pk)+","+str(FRRT.pk)
                        currentDeepRTYPE['rtype'] = 'BACK-DEEP-FRAT'
                        rtypeList.append(currentDeepRTYPE)   
                deepFRRTs = FRRT.form_type_parent.ref_to_parent_formtype.all().filter(flagged_for_deletion=False, is_public=True)
                if deepFRRTs:
                    for deepFRRT in deepFRRTs:
                        currentDeepRTYPE = {}
                        currentDeepRTYPE['label'] = currentRTYPE['label'] + " :: " + deepFRRT.record_type
                        currentDeepRTYPE['pk'] = str(deepFRRT.pk)+","+str(FRRT.pk)
                        currentDeepRTYPE['rtype'] = 'BACK-DEEP-FRRT'
                        rtypeList.append(currentDeepRTYPE)                                     

           
        #sort our rtype list by the label
        rtypeList = sorted(rtypeList, key=lambda k: k['label']) 
        
        #Return the JSON response
        finalJSON['rtype_list'] = rtypeList
        finalJSON = json.dumps(finalJSON)
        return HttpResponse(finalJSON, content_type="application/json" )

    
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'views.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")    


#=======================================================#
#   GET_FORM_RTYPES()      
#=======================================================#    
def get_form_rtypes(request, **kwargs):
    #------------------------------------------------------------------------------------------------------------------------------------
    #:::This endpoint returns a JSON list of all rtype values(their values and pk's) associated with a given form. We are only accessing data
    #   --so the access level is 1. Any user should be able to use this endpoint.
    #
    #   Returned JSON Example:  {"rtype_list":[
    #                                               {"rtype_pk":    "1",
    #                                                "rtype_label": "Object Shape",
    #                                                "rtype":       "FRAT",
    #                                                "rval":    {"pk":"12345","value:"Some Value"}, <-- This will similarly be a json object with 1 key/val pair
    #                                                
    #                                               },
    #                                               {"rtype_pk":    "6",
    #                                                "rtype_label": "Associated Unit",
    #                                                "rtype":       "FRRT",
    #                                                "rval":    [{"pk":"12345","value:"Some Value"},{"pk":"12345","value:"Some Value"}],    <-- if this is a frrt, then this will be another json object of key/val pairs 
    #                                                "ext_key": "1,2"  <-- This is just the raw ext key string
    #                                                "thumbnail":"www.geioh.coms/hoidjjds.jpg"
    #                                               },
    #                                         ]}
    #
    # EXPECTED POST VARIABLES:
    #   -- 'form_pk'
    #------------------------------------------------------------------------------------------------------------------------------------
    
    ERROR_MESSAGE = ""
    
    
    currentForm = Form.objects.get(pk=request.GET['form_pk'])
    
    if currentForm.is_public and currentForm.flagged_for_deletion == False:
        jsonData = {}
        rtype_list = []
        jsonData['rtype_list'] = rtype_list
        jsonData['form_name'] = currentForm.form_name
        jsonData['form_pk'] = currentForm.pk
        jsonData['formtype_name'] = currentForm.form_type.form_type_name
        jsonData['formtype_pk'] = currentForm.form_type.pk
        #Alright--let's load our RTYPEs from the current Form requested
        #*** RECYCLING BIN *** Let's filter them out by their recycling flags as well
        frav_list = currentForm.formrecordattributevalue_set.all().filter(flagged_for_deletion=False, is_public=True)
        frrv_list = currentForm.ref_to_parent_form.all().filter(flagged_for_deletion=False, is_public=True)
        
        #Let's try and grab our backward referencing forms now.
        back_frrv_list = None
        if  'no_back_refs' not in request.GET:
            back_frrv_list = currentForm.ref_to_value_form.all().filter(flagged_for_deletion=False, is_public=True)
        
        
        #If Statement forces evaluation of the query set before the loop
        if frav_list:                    
            #Let's load all the FRATs and FRAVs first
            for FRAV in frav_list:
                currentRTYPE = {}
                currentRVAL = {}
                currentRTYPE['rtype_pk'] = FRAV.record_attribute_type.pk
                currentRTYPE['rtype_label'] = FRAV.record_attribute_type.record_type
                currentRTYPE['rtype'] = "FRAT"
                currentRVAL['pk'] = FRAV.pk
                currentRVAL['value'] = FRAV.record_value
                currentRTYPE['rval'] = currentRVAL
                rtype_list.append(currentRTYPE)
                
        #If Statement forces evaluation of the query set before the loop
        if frrv_list:
            for FRRV in frrv_list:
                currentRTYPE = {}
                rvalList = []
                logger.info(FRRV.pk)
                currentRTYPE['rtype_pk'] = FRRV.record_reference_type.pk
                currentRTYPE['rtype_label'] = FRRV.record_reference_type.record_type
                currentRTYPE['rtype'] = "FRRT"
                #sometimes if not initialized, there won't be a FRRT reference--it will be a "NoneType" or "Null"
                #--if that's the case, there will be no PK value, so we will set the ref_formtype to "None" in that case
                if FRRV.record_reference_type.form_type_reference != None: currentRTYPE['ref_formtype'] = FRRV.record_reference_type.form_type_reference.pk
                else: currentRTYPE['ref_formtype'] = "None"
                currentRTYPE['ext_key'] = FRRV.external_key_reference
                currentRTYPE['rval_pk'] = FRRV.pk
                for FRRV_REF in FRRV.record_reference.filter(flagged_for_deletion=False, is_public=True):
                    currentRVAL = {}
                    currentRVAL['pk'] = FRRV_REF.pk
                    currentRVAL['name'] = FRRV_REF.form_name
                    currentRVAL['thumbnail'] = FRRV_REF.get_ref_thumbnail()
                    currentRVAL['url'] = reverse('maqlu_admin:edit_form',kwargs={'project_pk': request.user.permissions.project.pk, 'form_type_pk':FRRV_REF.form_type.pk, 'form_pk': FRRV_REF.pk})
                    rvalList.append(currentRVAL)
                currentRTYPE['rval'] = rvalList
                rtype_list.append(currentRTYPE)
        #If there are no FRRVs then just attach a list of the FRRT's instead with no rval data 
        else:       
            frrt_list = currentForm.form_type.ref_to_parent_formtype.filter(flagged_for_deletion=False, is_public=True)
            logger.info(frrt_list)
            if frrt_list:
                for FRRT in frrt_list:
                    logger.info(FRRT.form_type_reference)
                    currentRTYPE = {}
                    currentRTYPE['rtype_pk'] = FRRT.pk
                    currentRTYPE['rtype_label'] = FRRT.record_type
                    currentRTYPE['rtype'] = "FRRT"
                    currentRTYPE['ref_formtype'] = FRRT.form_type_reference.pk
                    currentRTYPE['ext_key'] = ""
                    currentRTYPE['rval_pk'] = ""
                    currentRTYPE['rval'] = ""
                    rtype_list.append(currentRTYPE)   

        #If Statement forces evaluation of the query set before the loop
        if back_frrv_list:
            flattened_list = back_frrv_list.values('form_parent__pk','form_parent__form_name','form_parent__form_type__pk','form_parent__pk','form_parent__form_type__form_type_name',)
            formTypeList = {}
            for FRRV in flattened_list:
                logger.info(FRRV)
                #Create Our RVAL
                newRVAL = {}
                newRVAL['form_pk'] = FRRV['form_parent__pk']
                newRVAL['form_name'] = FRRV['form_parent__form_name']
                newRVAL['thumbnail'] = staticfiles_storage.re_path("/site-images/no-thumb-file.png") 
                newRVAL['url'] =  reverse('maqlu_admin:edit_form',kwargs={'project_pk': request.user.permissions.project.pk, 'form_type_pk':FRRV['form_parent__form_type__pk'], 'form_pk': FRRV['form_parent__pk']})
                #create Our Back FRRT RTYPE dictionary entry
                #We only need to create it once--if it already exists, then just add the rval to its existing list 
                if FRRV['form_parent__form_type__pk'] in formTypeList:
                    formTypeList[FRRV['form_parent__form_type__pk']]['rval'].append(newRVAL)
                else:
                    formRef = {}
                    formRef['rtype'] = "BACK_FRRT"
                    formRef['formtype_name'] = FRRV['form_parent__form_type__form_type_name']
                    formRef['formtype_pk'] = FRRV['form_parent__pk']
                    formRef['rval'] = []
                    formRef['rval'].append(newRVAL)
                    formTypeList[FRRV['form_parent__form_type__pk']] = formRef
            #Now add it to the format in our rtype_list    
            for key in formTypeList:
                rtype_list.append(formTypeList[key])                    

        #convert python dict to a json string and send it back as a response
        jsonData = json.dumps(jsonData);
        return HttpResponse(jsonData, content_type="application/json")    
        
    else: ERROR_MESSAGE += "Error: This Form does not exist or is restricted."
    
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'views.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")        


    
#=======================================================#
#   GET_FORMS_SEARCH() 
#=======================================================#        
def get_forms_search(request, **kwargs):         
    #----------------------------------------------------------------------------------------------------------------------------
    #   This Endpoint does nothing but return a small list of forms that match the provided query string
    #   --It acts as a simple Google style search bar that autocompletes the user's typing. This is handy
    #   --when a project may have upwards of 5000 forms and scrolling through/loading a list of 5000 forms is a bit slow and unwieldy
    #
    # Speed:  This function, on a low-end server, can produce an answer in less than a second

    ERROR_MESSAGE = ""

    if request.method == 'GET':
        if 'query' in request.GET:
            #initialize our variables we'll need
            projectPK = request.GET['projectID']
            formtypePK = request.GET['formtypeID']
            searchString = request.GET['query']
            jsonResponse = {}
            form_list = []
            jsonResponse['form_list'] = form_list
            
            #Only search if the searchString isn't empty
            if len(searchString) != 0:
                #Initialize our query to contain all forms of this formtype and project
                queriedForms = Form.objects.all().filter(form_type__pk=formtypePK)
                #***RECYCLING BIN***  Make sure that we filter out any forms flagged for deletion or not set to PUBLIC
                queriedForms.filter(flagged_for_deletion=False, is_public=True)
                allTerms = searchString.split(' ')
                
                #I'd like to do a starts with filter if there is less than 2 letters in the first term, otherwise 
                #--go back to a normal icontains.
                if len(allTerms) == 1:
                    if len(searchString) < 3:
                        newQuery = queriedForms.filter(form_name__istartswith=searchString)
                        #Now let's make this just a tad bit more robust--if it finds zero matches with istartswith--then default back to icontains until it finds a match
                        if newQuery.exists() != True:
                            queriedForms = queriedForms.filter(form_name__icontains=searchString)
                        else:
                            queriedForms = newQuery
                    else:
                        queriedForms = queriedForms.filter(form_name__icontains=searchString)
                elif len(allTerms) > 1:        
                    for term in allTerms:
                        queriedForms = queriedForms.filter(form_name__icontains=term)
                        
                #We need to get a list no longer than 5 long of the submitted results    
                queriedForms = queriedForms[:5]
                #create our python dict to send as JSON
                for form in queriedForms:
                    currentForm = {}
                    currentForm['projectPK'] = form.project.pk
                    currentForm['formtypePK'] = form.form_type.pk
                    currentForm['formPK'] = form.pk
                    currentForm['label'] = form.form_name
                    currentForm['longLabel'] = form.form_type.form_type_name + " - " + form.form_name
                    currentForm['thumbnail'] = form.get_ref_thumbnail()
                    currentForm['url'] = reverse('maqluengine:form',kwargs={'form_id':form.pk})
                    form_list.append(currentForm)
                #return the finished JSON
                jsonResponse = json.dumps(jsonResponse)
                return HttpResponse(jsonResponse, content_type="application/json")
            ERROR_MESSAGE += "Error: You submitted an empty query"
    ERROR_MESSAGE += "Error: You have not submitted through GET"
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")           
    
    

#=======================================================#
#   CHECK_PROGRESS_QUERY()
#=======================================================#          
def check_progress_query(request, **kwargs):
    #----------------------------------------------------------------------------------------------------------------------------
    #   This Endpoint just checks the progress of the submitted UUID Progress Object
    #   --It's used by longer functions that require time on the server to process to keep the usser updated on the progress of their
    #   --query submitted. Security isn't particularly important here, because the information provided isn't particularly sensitive,
    #   --and this model/object doesn't have a foreign key to a project. It can only be accessed by a UUID(unique ID) provided by the user
    #   --and the chance of someone figuring out a 32character long random string in the small amount of time it takes to process the server
    #   --function is considerably low--and even if they DID manage to hack it, the information they recieve is essentially rubbish and offers
    #   --no sensitive data except perhaps the name or label of some rtypes--and associated counts for the query. I suppose that could be
    #   --potentially sensitive--but the security  risk is so low--and client-based-- that I won't spend time worrying about it for now--but creating
    #   --unique session tokens for individual IPs is one way to handle it.

    
    ERROR_MESSAGE = ""
    #Returns a JSON string to an AJAX request given a provided UUID   
    try:
        currentProcessObject = AJAXRequestData.objects.filter(uuid=request.GET['uuid'])[0]
        currentProcessObject.keep_alive = True
        currentProcessObject.save()
        currentJson = currentProcessObject.jsonString
        #If finished, then delete the process object
        if currentProcessObject.is_finished:
            logger.info( "DELETING OBJECT I GUESS?")
            currentProcessObject.delete()
            currentJson = json.loads(currentJson)
            currentJson['is_complete'] = "True"
            if 'server_error' in currentJson: currentJson['message'] = "There was an error server side: " + currentJson['server_error'] + " ------------ Last Message received: " +  currentJson['message']
            currentJson = json.dumps(currentJson)
        #return the json response      
        return HttpResponse(currentJson, content_type="application/json")  
    except Exception as e:
        logger.info( "Whoops---hmmm.....")
        logger.info( e)
        ERROR_MESSAGE += "Something happened during the check to the Progress Object--it might not have been created yet, and we are checking too quickly..."
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"False", "row_total":"0", "row_timer":"0"}',content_type="application/json")                  

    
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'views.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")              

#=======================================================#
#   ACCESS LEVEL :  1       NAVIGATE_MASTER_QUERY_PAGINATION() *RECYCLING
#=======================================================#   
@require_POST
@csrf_exempt
def navigate_master_query_pagination(request, **kwargs):
    ERROR_MESSAGE = ""
    
 
    #We need to make sure we have permission to deal with the formtype--e.g. it's part of the user's current project
    formtype = FormType.objects.get(pk=request.POST['formtype_id'])
    
    #If the project IDs match, then we're good to go! Also if it's not the project, but the formtype is set to PUBLIC then we are also good to go
    if formtype.is_public and formtype.flagged_for_deletion == False:
        #First let's setup our header field of ordered labels 
        logger.info(  "Timer Start"                )
        form_att_type_list = []
        #***RECYCLING BIN*** Make sure our RTYPES are filtered by their deletion flags
        for attType in formtype.formrecordattributetype_set.all().filter(flagged_for_deletion=False, is_public=True).order_by('order_number')[:5]:
            form_att_type_list.append((attType.order_number,'frat',attType.pk,attType.record_type)) 
 
        #***RECYCLING BIN*** Make sure our RTYPES are filtered by their deletion flags
        for refType in formtype.ref_to_parent_formtype.all().filter(flagged_for_deletion=False, is_public=True).order_by('order_number')[:5]:
            form_att_type_list.append((refType.order_number,'frrt',refType.pk,refType.record_type)) 
        #sort the new combined reference ad attribute type list combined
        form_att_type_list = sorted(form_att_type_list, key=lambda att: att[0])
        #we only want the first 5 types
        form_att_type_list = form_att_type_list[0:5]

        formList = []                
       
        
        #Setup a list to hold the attribute types from the query. We want to show the record types that are part of the search terms,
        #   --rather than the default types that are in order. If there are less than 5 query record types, use the ordered record type list
        #   --until 5 are met.
        logger.info(request.POST['pagination_rtype_header'])
        queryRTYPElist = json.loads(request.POST['pagination_rtype_header'])


        
        
        #We need to check the # of rtypes in our header list now--if it's less than 5, then let's add from the ordered list
        #We also need to make sure we aren't adding duplicates of the RTYPES, e.g. if we're looking for a match under "Object Number" and Object Number is already
        #--in our sorted order-num list--let's not re-add it.
        for attType in form_att_type_list:
            logger.info( "AttTypeList:  " + str(attType))
            matchfound = False
            for queryAttType in queryRTYPElist:
                if attType[2] == queryAttType[2]:
                    matchfound = True
            if matchfound == False and len(queryRTYPElist) < 5:    
                #let's arbitrarily add '100' to the order number so that our queries are definitely in front of these
                queryRTYPElist.append((attType[0] + 100,attType[1],attType[2],attType[3]))
                
        for q in queryRTYPElist:
            logger.info( "QTypeList:  " + str(q))


        logger.info( request.POST)        
        queryCounter = 0
        logging.info("TEST A")
        logging.info("TEST A END")
        logger.info( request.POST['form_list'])
        masterQuery = request.POST['form_list'].split(',')
        #Figure out if we requested ALL results or just a single page
        
        if request.POST['requestedPageNumber'] != 'ALL':
            #Setup our Pagination values given in the POST string
            requestedPageNumber = int(request.POST['requestedPageNumber'])
            resultsPerPage = int(request.POST['resultsPerPage'])
            #Get our queryset slice values
            startIndex = (resultsPerPage * requestedPageNumber) - resultsPerPage
            endIndex = resultsPerPage * requestedPageNumber
        else:
            #We are asking for ALL results of this query--could take longer to load
            requestedPageNumber = "ALL"
            resultsPerPage = request.POST['numberOfResults']
            startIndex = 0
            endIndex = request.POST['numberOfResults']
        
        logger.info( startIndex)
        logger.info( endIndex)

        masterQuery = masterQuery[startIndex:endIndex]
        logger.info( "TIMER RR"+ " : " + str(time.process_time()))
        #count the query so we only make one database hit before looping(otherwise each loop would be another hit)

        for form_pk in masterQuery:
            aForm = Form.objects.get(pk=form_pk)
            logger.info( "TIMER S"+ " : " + str(time.process_time()))
            rowList = []
            #Let's loop through each item in the queryRTYPE list and match up the frav's in each queried form so the headers match the form attribute values
            for rtype in queryRTYPElist:
                if rtype[1] == 'frat':
                    #logger.info( str(rtype[2]) + '  ' + str(aForm.formrecordattributevalue_set.all().filter(record_attribute_type__pk=rtype[2]).count()))
                    logger.info( "TIMER X"+ " : " + str(time.process_time()))
                    formRVAL = aForm.formrecordattributevalue_set.all().filter(record_attribute_type__pk=rtype[2], is_public=True, flagged_for_deletion=False)
                    #We need to check for NULL FRAV's here. When a user manually creates new forms, they don't always have FRAVS created for them if they leave it blank
                    if formRVAL.exists():
                        rowList.append((rtype[0],'frav',formRVAL[0].record_value, formRVAL[0].pk))
                    else:
                        logger.info( "Whoops--something happened. There are no RVALS for 'frats' using: " + str(rtype[2]))
                    logger.info( "TIMER Y"+ " : " + str(time.process_time()))
                else:
                    #for frrt in aForm.ref_to_parent_form.all():
                        #logger.info( "" + str(frrt.pk))
                    formRVAL = aForm.ref_to_parent_form.all().filter(record_reference_type__pk=rtype[2], is_public=True, flagged_for_deletion=False)
                    if formRVAL.exists():
                        formRVAL = formRVAL[0]
                        #First check to see if there are any relations stored in the many to many relationship
                        #   --if there are, then load them normally, and if not change the value to a frrv-ext tag and store the external ID for the
                        #   --ajax request to process properly
                        allReferences = formRVAL.record_reference.all()
                        refCount = allReferences.count()
                        if refCount > 0:
                            if allReferences:
                                #we need to store a list of its references--it's a manytomany relationship
                                #A comma should be sufficient to separate them, but to be safe--we'll make our delimeter a ^,^
                                #-- we also need to provide the formtype pk value for the link
                                listOfRefs = ""
                                for rec in allReferences:
                                    listOfRefs += str(rec) + '|^|' + str(rec.form_type.pk) + '|^|' + str(rec.pk) + "^,^"
                                #remove the last delimeter
                                listOfRefs = listOfRefs[0:-3]
                            rowList.append((rtype[0],'frrv',listOfRefs, formRVAL.pk))
                        else:
                            #Store the external key value instead and change it to a frrv-ext for the AJAX callable
                            rowList.append((rtype[0],'frrv-ext',formRVAL.external_key_reference, formRVAL.pk))
                    else:
                        #Store the external key value instead and change it to a frrv-null for the AJAX callable
                        rowList.append((rtype[0],'frrv-null',"", ""))

                        
            #sort the new combined reference ad attribute type list combined
            rowList = sorted(rowList, key=lambda att: att[0])
            #logger.info( str(rowList))
            #Now let's handle the thumbnail bit of business for the query
            #--If the current form IS a media type already, then use itself to grab the thumbnail URI
            logger.info('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ ABOUT TO GET THUMBNAILS')
            if aForm.form_type.type == 1:
                thumbnailURI = aForm.get_thumbnail_type()
            else:
                logger.info("LOOKING FOR A FRRT")
                #let's find the first media type in the order but offer a default to "NO PREVIEW" if not found
                thumbnailURI = staticfiles_storage.re_path("/site-images/no-thumb-missing.png")
                for record in rowList:            
                    #if it's a reference
                    if record[1] == 'frrv' or record[1] == 'frrv-ext':
                        currentRTYPE = FormRecordReferenceValue.objects.get(pk=int(record[3]))
                        #if it's not a NoneType reference:
                        if currentRTYPE.record_reference_type.form_type_reference != None:
                            #If its a reference to a media type
                            if currentRTYPE.record_reference_type.form_type_reference.type == 1:
                                logger.info( "WE GOT A MATCH")
                                #Because a form record reference value is a ManyToMany relationship, we just grab the first one in the list
                                #TODO this may need to be edited later--because you can't order the selections. I may add another ForeignKey called
                                #"Thumbnail Reference" which links to a single relation to a form of a media type--this would also
                                #probably solve the complexity of looping through to grab it as it stands right now
                                #****WE also have to check for NULL references
                                if currentRTYPE.record_reference.all().count() > 0:
                                    thumbnailURI = currentRTYPE.record_reference.all(is_public=True, flagged_for_deletion=False)[0].get_thumbnail_type()
                                break
                #Finally--if there aren't any relevant media types in our frrts, let's do a last second check for ANY frrts that are media types
                #--that AREN'T in our RTYPE list
                if thumbnailURI == staticfiles_storage.re_path("/site-images/no-thumb-missing.png"):
                    logger.info("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%    We're TRYING TO GET A THUMBNAIL")
                    currentRVAL = aForm.ref_to_parent_form.filter(record_reference_type__form_type_reference__type=1)
                    logger.info(currentRVAL)
                    if currentRVAL.exists():
                        #Just get the first one out of the list
                        if len(currentRVAL[0].record_reference.all()) > 0:
                            logger.info(currentRVAL[0].record_reference.filter(is_public=True, flagged_for_deletion=False)[0].form_name)
                            thumbnailURI = currentRVAL[0].record_reference.filter(is_public=True, flagged_for_deletion=False)[0].get_thumbnail_type()
                            

            formList.append([thumbnailURI,str(aForm.pk), aForm, rowList])                                       
            
        form_att_type_list, form_list = form_att_type_list, formList

        finishedJSONquery = {}
        
        headerList=[]
        for rtype in queryRTYPElist:
            rtypeDict = {}
            rtypeDict["index"] = rtype[0]
            rtypeDict["rtype"] = rtype[1]
            rtypeDict["pk"] = rtype[2]
            rtypeDict["name"] = rtype[3]
            headerList.append(rtypeDict)

        
        finishedJSONquery["rtype_header"] = headerList
        allFormList = []
        counter = 0
        total = len(formList)
        for form in formList:                   
            formDict = {}
            formDict["thumbnail_URI"] = form[0]
            formDict["pk"] = form[1]
            if formtype.is_hierarchical: formDict["form_id"] = form[2].get_hierarchy_label()
            else: formDict["form_id"] = form[2].form_name
            formRVALS = []
            for rval in form[3]:
                rvalDict = {}
                rvalDict["index"] = rval[0]
                rvalDict["rtype"] = rval[1]
                rvalDict["value"] = rval[2]
                rvalDict["pk"] = rval[3]
                formRVALS.append(rvalDict)
            formDict["rvals"] = formRVALS
            allFormList.append(formDict)

        finishedJSONquery["pagination_rtype_header"] = queryRTYPElist
        finishedJSONquery["form_list"] = allFormList
        finishedJSONquery["formtype"] = formtype.form_type_name
        finishedJSONquery["formtype_pk"] = formtype.pk
        finishedJSONquery["project_pk"] = request.POST['project_id']
        finishedJSONquery["pagination_page"] = requestedPageNumber
        finishedJSONquery["resultsCount"] = request.POST['numberOfResults'] 
        finishedJSONquery["pagination_form_list"] = request.POST['form_list']

        
        #save our stats to the returned JSON
        #convert to JSON
        finishedJSONquery = json.dumps(finishedJSONquery)

        logger.info(  "Timer End"     )
        return HttpResponse(finishedJSONquery, content_type="application/json")


        
    ERROR_MESSAGE += "Error: Trying to access missing or forbidden data"
    
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'views.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")        
    



#=======================================================#
#   ACCESS LEVEL :  1       RUN_MASTER_QUERY_ENGINE() *Recycling
#=======================================================#   
def run_master_query_engine(request, **kwargs):
    #------------------------------------------------------------------------------------------------------------------------------------ 
    #  This is the real magic of the database in terms of non-geospatial data. This Query engine takes complicated input from json POST data 
    #   --and runs it through a long complex Django filter series to perform 1 of 2 tasks--the first is to produce a long set of counts in their
    #   --given search parameters in order to generate several graphs/charts of the data. The second function is to actually produce a list of
    #   --forms from the provided parameters to inspect and bulk edit. 
    #
    #   This takes 3 layers of parameters:
    #           *The main query, which produces the form results, and has complex search options and AND/OR statements
    #           *The option constraints query, which acts as an additional parameter when looking for deep counts with a comparison
    #           *The primary contraints query, which acts as a further nested constraint on the previous 2
    #       --Essentially each, parameter is an axis of a graph or dimension/each new parameter adds another dimension to that axis. It's more obviously
    #       --apparent when actually seeing the results of a query
    #  
    #   There is a tremendous amount of code--which could probably be reduced in line count and size, but it was my first major foray into Django's%s
    #   --query engine, so no doubt there are probably redundant lines. It's a bit complex because I needed 3 layers of parameters, and also needed
    #   --the ability to perform queries when those parameters included relations. I had spent some time looking into nested functions to help deal with
    #   --what felt like a lot of boiler plate for each section, but--I couldn't figure it out. It works--and I need to move on to other pastures with
    #   --the project for now.
    #
    #   SPEED: I spent a great deal of time looking for alternative ways to speed up the queries behind this--it does take time. I haven't had a query
    #   --take longer than a minute, but the potential is there. A minute isn't long in the grand scheme of things, but still. The time it takes to query
    #   --also depends upon how many forms are part of the query-e.g. the test case of Ceramics in the AL-Hiba project has roughly 110,000 individual forms.
    #   --A formtype with only 5000 forms wouldn't take time at all to process in comparison. The speed loss comes with nested queries(MYSQL doesn't like these)
    #   --as well as INNER JOINS when dealing with the relations. I was able to cut the time in half from the first iteration--which is significant, but there
    #   --are probably other ways I can increase the speed further still. TODO: One option to try is to grab a value list of PKs to submit to another query
    #   --rather than chaining 2 querysets together(which causes an INNER JOIN in SQL) I tentatively tried this before--but without much success. I know
    #   --what I'm doing far more now and it's worth trying out again in the future, but for now--this works, and provides user feedback to keep them
    #   --updated with the goings on behind the curtain.
    #
    #   TODO: I've also moved this into an API Endpoint rather than as a process of the view itself. There may be some strange code decisions left in here
    #   --as a function of that transition

    ERROR_MESSAGE = ""
    
    CS_CONTAINS = '0';
    CONTAINS = '1';
    EXACT_MATCH = '2';
    EXCLUDES = '3';
    IS_NULL = '4';
    ALL_UNIQUE_TERMS = '5';
    
                
    logger.info( request.GET)
    #Make the AJAX Request Data Model for subsequent AJAX calls
    progressDataMessage = {}
    progressDataMessage['message'] = "Loading Query from GET"
    progressDataMessage['current_query'] = ""
    progressDataMessage['current_term'] = ""
    progressDataMessage['percent_done'] = "0"
    progressDataMessage['current_constraint'] = ""
    progressDataMessage['is_complete'] = "False"
    #!!!!!!!!!!!!!!PROGRESS UPDATE
    progressData = AJAXRequestData(uuid=request.GET.get('uuid'), jsonString=json.dumps(progressDataMessage) )
    progressData.is_finished = False
    progressData.save()
    
    try:
    
        #We need to loop through EACH project query in the JSON header and create a separate results box for each one
        masterProjectQuery = json.loads(request.GET['master_query'])
        
        masterQueryResults = {}
        all_project_queries = []
        masterQueryResults['final_query_set'] = all_project_queries
        query_set = masterProjectQuery['query_list']
       
        progressDataParentQueryCounter = 0;
        for query in query_set:
            logger.info( "Starting a query?")
            # PROGRESS REPORT *****************************************
            #!!!!!!!!!!!!!!PROGRESS UPDATE
            progressDataBasePercentage = (80.0/len(query_set)) * progressDataParentQueryCounter
            progressDataMessage['message'] = "Performing Database Query"
            progressDataMessage['current_query'] = query['project_label'] + " : " + query['formtype_label']
            progressDataMessage['current_term'] = ""
            progressDataMessage['percent_done'] = progressDataBasePercentage
            progressData.jsonString = json.dumps(progressDataMessage) 
            progressData.save()
            
            queryProject = FormProject.objects.get(pk=query['project_pk']) 
            queryFormtype = FormType.objects.get(pk=query['formtype_pk'])
            #If the project or formtype requests are not public or flagged for deletion then throw an error
            if (queryProject.is_public == False) or (queryFormtype.flagged_for_deletion or queryFormtype.is_public == False):
                ERROR_MESSAGE += "Error: You are trying to access a project or formtype that doesn't exist or access is not allowed. This has been logged to the network administrator"
                #Delete Our progress object
                logger.info( "Hmmm are we exiting here?")
                progressData.is_finished = True;
                progressDataMesssage['server_error'] = ERROR_MESSAGE
                progressData.jsonString = json.dumps(progressDataMessage) 
                progressData.save()
                #break the loop and return the security message
                break
            #Otherwise continue
            else:
                #create a dictionary to store the query statistics
                queryStats = {}
                queryStats['all_forms_count'] = 0
                queryStats['formtype'] = query['formtype_label']
                queryStats['formtype_pk'] = query['formtype_pk']
                queryStats['project'] = query['project_label']
                queryStats['project_pk'] = query['project_pk']
                queryStats['primary_constraints'] = []
                queryStats['secondary_constraints'] = []
                queryStats['secondary_constraints_test'] = []
                queryList = []
                queryStats['query_list'] = queryList
                primaryConstraintList = []
                
                logger.info(  queryStats['project_pk']  + "  :  "  + query['project_pk'])
                
                
                
                #First let's setup our header field of ordered labels            )
                form_att_type_list = []
                #***RECYCLING BIN*** Make sure our RTYPES are filtered by their deletion flags
                for attType in queryFormtype.formrecordattributetype_set.all().filter(flagged_for_deletion=False, is_public=True).order_by('order_number'):
                    form_att_type_list.append((attType.order_number,'frat',attType.pk,attType.record_type)) 
         
                #***RECYCLING BIN*** Make sure our RTYPES are filtered by their deletion flags
                for refType in queryFormtype.ref_to_parent_formtype.all().filter(flagged_for_deletion=False, is_public=True).order_by('order_number'):
                    form_att_type_list.append((refType.order_number,'frrt',refType.pk,refType.record_type)) 

                #sort the new combined reference ad attribute type list combined
                form_att_type_list = sorted(form_att_type_list, key=lambda att: att[0])
                #we only want the first 5 types
                form_att_type_list = form_att_type_list[0:5]
                
                #Finally let's organize all of our reference and attribute values to match their provided order number
                formList = []                
               
                #Setup our inital queryset that includes all forms
                masterQuery = queryFormtype.form_set.all().filter(flagged_for_deletion=False).exclude(is_public=False)  
                queryStats['all_forms_count'] = masterQuery.count()
                
                #Setup a list to hold the attribute types from the query. We want to show the record types that are part of the search terms,
                #   --rather than the default types that are in order. If there are less than 5 query record types, use the ordered record type list
                #   --until 5 are met.
                queryRTYPElist = []
                uniqueRTYPES = []
                rtypeCounter = 1
                
                #Some progress data report variables
                termCounter = 0.0
                termTotalPercent = 60.0
                termCount = len(query['terms'])
                termMinPercent = 10.0
                for index,term in enumerate(query['terms']):
                    progressDataMessage['current_term'] = term['TVAL']
                   
                    currentTermPercent = termMinPercent + ((termTotalPercent/termCount) * termCounter)
                    logger.info("<!------------------------------------------  " + str(currentTermPercent))
                    progressDataMessage['percent_done'] = str(int(currentTermPercent))
                    progressData.jsonString = json.dumps(progressDataMessage) 
                    progressData.save()


                    #setup a dictionary of key values of the query stats to add to the main querystas dictionary later
                    singleQueryStats = {} 
                    singleQueryStats['original_query'] = {}
                    singleQueryStats['original_query']['query_list'] = []
                    singleQueryStats['original_query']['query_list'].append( copy.deepcopy(query))
                    logger.info(singleQueryStats['original_query']['query_list'])
                    logger.info(singleQueryStats['original_query']['query_list'][0])
                    singleQueryStats['original_query']['query_list'][0]['terms'] = singleQueryStats['original_query']['query_list'][0]['terms'][index:index+1]
                    singleQueryStats['original_query']['query_list'][0]['terms'][0]['ANDOR'] = "INITIAL"
                    queriedForms = queryFormtype.form_set.filter(flagged_for_deletion=False).exclude(is_public=False)
                    
                    uniqueQuery = False
                    #Let's not allow any duplicate rtypes in the query rtype list header e.g. we don't want "Object ID" to show up 4 times 
                    #--if the user makes a query that compares it 4 times in 4 separate queries
                    if (term['pk']+ '_' +term['RTYPE']) not in uniqueRTYPES: 
                        uniqueRTYPES.append((term['pk']+ '_' +term['RTYPE']))
                        uniqueQuery = True
                    
                    #We need to check whether or not this query is an AND/OR  or a null,e.g. the first one(so there is no and/or)
                    rtype = term['RTYPE']
                    rtypePK = term['pk']
                    
                    logger.info( rtype + " :    <!----------------------------------------------------------------")
                    #########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
                    # (FRAT) FormRecordAttributeType Lookups
                    #########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
                    if rtype == 'FRAT':
                        #store the record type in a new rtype list if unique
                        if uniqueQuery: queryRTYPElist.append((rtypeCounter,'frat',rtypePK,term['LABEL'])) 
                        rtypeCounter += 1
                        tCounter = 0
                         
                        #store stats
                        singleQueryStats['rtype_name'] = term['LABEL']
                        singleQueryStats['rtype_pk'] = rtypePK
                        singleQueryStats['rtype'] = rtype
                        termStats = []
                        singleQueryStats['all_terms'] = termStats
                        #Now begin modifying the SQL query which each term of each individual query
                        #skip the term if the field was left blank
                        if term['TVAL'] != "" or term['QCODE'] == '4':
                            logger.info("WE MADE IT!!!!   => QCODE = " + term['QCODE'] + "      " + str(queriedForms.count()))
                            newQuery = None
                            if term['ANDOR'] != 'or':#We can assume it is an AND like addition if it's anything but 'or'
                                #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                if   term['QCODE'] == CONTAINS: newQuery = queriedForms.filter(formrecordattributevalue__record_value__icontains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#CONTAINS    
                                elif term['QCODE'] == CS_CONTAINS: newQuery = queriedForms.filter(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#ICONTAINS                                   
                                elif term['QCODE'] == EXACT_MATCH: newQuery = queriedForms.filter(formrecordattributevalue__record_value__exact=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#MATCHES EXACT                                    
                                elif term['QCODE'] == EXCLUDES: newQuery = queriedForms.exclude(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#EXCLUDES                                   
                                elif term['QCODE'] == IS_NULL: newQuery = queriedForms.filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=rtypePK) | (queryFormtype.form_set.all().filter(formrecordattributevalue__record_value__icontains="", formrecordattributevalue__record_attribute_type__pk=rtypePK))#IS_NULL        
                                term['count'] =  newQuery.count()
                                termStats.append(term)
                                masterQuery = (newQuery & masterQuery)
                                singleQueryStats['intersections'] = masterQuery.count()
                            else:#Otherwise it's an OR statement
                                #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                if   term['QCODE'] == CONTAINS: newQuery = (queryFormtype.form_set.all().filter(formrecordattributevalue__record_value__icontains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK))#CONTAINS    
                                elif term['QCODE'] == CS_CONTAINS: newQuery = (queryFormtype.form_set.all().filter(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK))#ICONTAINS                                   
                                elif term['QCODE'] == EXACT_MATCH: newQuery = (queryFormtype.form_set.all().filter(formrecordattributevalue__record_value__exact=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK))#MATCHES EXACT                                    
                                elif term['QCODE'] == EXCLUDES: newQuery = (queryFormtype.form_set.all().exclude(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK))#EXCLUDES                                   
                                elif term['QCODE'] == IS_NULL: newQuery = (queryFormtype.form_set.all().filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=rtypePK)) | (queryFormtype.form_set.all().filter(formrecordattributevalue__record_value__icontains="", formrecordattributevalue__record_attribute_type__pk=rtypePK))#IS_NULL 
                                #Adding an additional booleanfield to the filters is causing drastic slowdown--a temp fix is to keep the original query for chaining
                                #--but start using an extrapolated values_list to perform the actual count--this might be useful for all these queries to speed up counts?
                                #finalQuery = [entry for entry in newQuery.values_list('is_public',flat=True) if entry != 'False']
                                #save stats and query
                                #term['count'] =  len(finalQuery)
                                #termStats.append(term)
                                #masterQuery = (newQuery | masterQuery)
                                #finalQuery = [entry for entry in masterQuery.values_list('is_public',flat=True) if entry != 'False']
                                #singleQueryStats['additions'] = len(finalQuery)
                                #save stats and query
                                term['count'] =  newQuery.count()
                                termStats.append(term)
                                masterQuery = (newQuery | masterQuery)
                                singleQueryStats['additions'] = masterQuery.count()
                                
                    #########################################$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#########################################$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#########################################$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$     
                    # (FRRT) FormRecordReferenceType Lookups            
                    # This is where things can get complicated. I've added a 'deep' search -- or the ability to search fields from a related model
                    # --Right now, this just looks at the form IDs of the related field and looks for matches--it will still need to do that, but
                    # --it also needs to be able to look up FRAT or FRRTs in the same field--that will essentially double the code for this blocks
                    # --to do all of this, and will also cause the time of the query to significantly increase because we are doing another JOIN in the
                    # --SQL lookup to span this relationship. This won't affect the list of queried forms directly--they will be limited by what the
                    # --query finds obviously--but the user will only see the column for the related FRRT that had a match--not specifically the field that matched
                    # ----It WILL affect the counts for the graphs etc.
                    #########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&#########################################$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#########################################$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
                    elif rtype == 'FRRT':
                        #store the record type in a new rtype list if unique
                        if uniqueQuery: queryRTYPElist.append((rtypeCounter,'frrt',rtypePK,term['LABEL'])) 
                        rtypeCounter += 1
                        tCounter = 0
                        
                        #store stats
                        singleQueryStats['rtype_name'] = term['LABEL']
                        singleQueryStats['rtype_pk'] = rtypePK
                        singleQueryStats['rtype'] = rtype
                        termStats = []
                        singleQueryStats['all_terms'] = termStats
                        #get the deep values
                        deepPK, deepRTYPE = term['RTYPE-DEEP'].split('__')
                        logger.info( deepPK + "  :  " + deepRTYPE + " <!-------------------------------------------")
                        #==========================================================================================================================================================================================
                        # IF WE ARE JUST LOOKING UP THE RTYPE FORM ID
                        #==========================================================================================================================================================================================
                        #TODO: This also needs to check external reference values if no match is found
                        if deepRTYPE == 'FORMID':
                            logger.info( "WTF")
                            #Now begin modifying the SQL query which each term of each individual query
                            #skip the term if the field was left blank
                            if term['TVAL'] != "" or term['QCODE'] == '4':
                                newQuery = None
                                if term['ANDOR'] != 'or':#We can assume it is an AND like addition if it's anything but 'or'
                                    #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                    if   term['QCODE'] == CONTAINS: newQuery = queriedForms.filter(ref_to_parent_form__record_reference__form_name__icontains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK) #CONTAINS    
                                    elif term['QCODE'] == CS_CONTAINS: newQuery = queriedForms.filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK) #ICONTAINS                                   
                                    elif term['QCODE'] == EXACT_MATCH: newQuery = queriedForms.filter(ref_to_parent_form__record_reference__form_name__exact=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK)#MATCHES EXACT                                    
                                    elif term['QCODE'] == EXCLUDES: newQuery = queriedForms.exclude(ref_to_parent_form__record_reference__form_name__contains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK)#EXCLUDES                                   
                                    elif term['QCODE'] == IS_NULL: newQuery = queriedForms.filter(ref_to_parent_form__record_reference__isnull=True, ref_to_parent_form__record_reference_type__pk=rtypePK)#IS_NULL        
                                    term['count'] =  newQuery.count()
                                    termStats.append(term)
                                    masterQuery = (newQuery & masterQuery)
                                    singleQueryStats['intersections'] = masterQuery.count()
                                else:#Otherwise it's an OR statement
                                    #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                    if   term['QCODE'] == CONTAINS: newQuery = (queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__form_name__icontains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK))#CONTAINS    
                                    elif term['QCODE'] == CS_CONTAINS: newQuery = (queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK))#ICONTAINS                                   
                                    elif term['QCODE'] == EXACT_MATCH: newQuery = (queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__form_name__exact=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK))#MATCHES EXACT                                    
                                    elif term['QCODE'] == EXCLUDES: newQuery = (queryFormtype.form_set.all().exclude(ref_to_parent_form__record_reference__form_name__contains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK))#EXCLUDES                                   
                                    elif term['QCODE'] == IS_NULL: newQuery = (queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__isnull=True, ref_to_parent_form__record_reference_type__pk=rtypePK))#IS_NULL 
                                    term['count'] =  newQuery.count()
                                    termStats.append(term)
                                    masterQuery = (newQuery | masterQuery)
                                    singleQueryStats['additions'] = masterQuery.count()
                        #==========================================================================================================================================================================================
                        # IF WE ARE LOOKING UP THE RELATIONS FRAT
                        #==========================================================================================================================================================================================
                        elif deepRTYPE == 'FRAT':
                            logger.info( "We should be here")
                            #grab the formtype in question
                            deepFormType = FormType.objects.filter(pk=FormRecordAttributeType.objects.get(pk=deepPK).form_type.pk)
                            #***RECYCLING BIN*** Make sure our this Deep query FormType is always filtered by recycling bin flags
                            deepFormType = deepFormType.filter(flagged_for_deletion=False, is_public=True)
                            deepFormType = deepFormType[0]
                            #Now begin modifying the SQL query which each term of each individual query
                            #skip the term if the field was left blank
                            if term['TVAL'] != "" or term['QCODE'] == '4':
                                newQuery = None
                                #----------------------------------------------------------
                                # AND STATEMENT FOR A --TERM--
                                if term['ANDOR'] != 'or':#We can assume it is an AND like addition if it's anything but 'or'
                                    #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                    #First we Get a flattened list of form pk values from the deepFormType
                                    #Then we filter our current formtype queryset's frrt manytomany pks by the pk value list just created 
                                    if   term['QCODE'] == CONTAINS: 
                                        flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__icontains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                        newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                    elif term['QCODE'] == CS_CONTAINS: 
                                        flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                        newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                    elif term['QCODE'] == EXACT_MATCH: 
                                        flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__exact=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                        newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                    elif term['QCODE'] == EXCLUDES: 
                                        flattenedSet = list(deepFormType.form_set.all().exclude(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                        newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                    elif term['QCODE'] == IS_NULL: 
                                        flattenedSet = list(   (deepFormType.form_set.all().filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=deepPK) | deepFormType.form_set.all().filter(formrecordattributevalue__record_value__icontains="", formrecordattributevalue__record_attribute_type__pk=deepPK) ).values_list('pk', flat=True)) #IS EMPTY    
                                        newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                    term['count'] =  newQuery.count()
                                    termStats.append(term)
                                    masterQuery = (newQuery & masterQuery)
                                    singleQueryStats['intersections'] = masterQuery.count()
                                #--------------------------------------------------------
                                # OR STATEMENT FOR a --TERM--
                                else:
                                    #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                    if   term['QCODE'] == CONTAINS: 
                                        flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__icontains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                        newQuery = queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                    elif term['QCODE'] == CS_CONTAINS: 
                                        flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                        newQuery = queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                    elif term['QCODE'] == EXACT_MATCH: 
                                        flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__exact=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                        newQuery = queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                    elif term['QCODE'] == EXCLUDES: 
                                        flattenedSet = list(deepFormType.form_set.all().exclude(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                        newQuery = queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                    elif term['QCODE'] == IS_NULL: 
                                        flattenedSet = list(   (deepFormType.form_set.all().filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=deepPK) | deepFormType.form_set.all().filter(formrecordattributevalue__record_value__icontains="", formrecordattributevalue__record_attribute_type__pk=deepPK) ).values_list('pk', flat=True)) #IS EMPTY  
                                        newQuery = queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                    term['count'] =  newQuery.count()
                                    termStats.append(term)
                                    masterQuery = (newQuery | masterQuery)
                                    singleQueryStats['additions'] = masterQuery.count()            
                        #==========================================================================================================================================================================================
                        # IF WE ARE LOOKING UP THE RELATION'S FRRT(Only form ID allowed)
                        #==========================================================================================================================================================================================
                        elif deepRTYPE == 'FRRT':
                            logger.info( "We should be here 3")
                            #grab the formtype in question
                            try:
                                deepFormType = FormType.objects.get(pk=FormRecordReferenceType.objects.get(pk=deepPK).form_type_parent.pk, flagged_for_deletion=False, is_public=True)
                            except:
                                ERROR_MESSAGE += "Error: You've attempted to access a Deep Form Type that is either non-existent, or is flagged for deletion"
                                break
                            #Now begin modifying the SQL query which each term of each individual query
                            #skip the term if the field was left blank
                            if term['TVAL'] != "" or term['QCODE'] == '4':
                                newQuery = None
                                #----------------------------------------------------------
                                # AND STATEMENT FOR A --TERM--
                                if term['ANDOR'] != 'or':#We can assume it is an AND like addition if it's anything but 'or'
                                    #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                    #First we Get a flattened list of form pk values from the deepFormType
                                    #Then we filter our current formtype queryset's frrt manytomany pks by the pk value list just created 
                                    if   term['QCODE'] == CONTAINS: 
                                        flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__icontains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS 
                                        newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                    elif term['QCODE'] == CS_CONTAINS: 
                                        flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=deepPK).values_list('pk', flat=True)) #ICONTAINS    
                                        newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                    elif term['QCODE'] == EXACT_MATCH: 
                                        flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__exact=term['TVAL'], ref_to_parent_form__record_reference_type__pk=deepPK).values_list('pk', flat=True)) #EXACT MATCH
                                        newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                    elif term['QCODE'] == EXCLUDES: 
                                        flattenedSet = list(deepFormType.form_set.all().exclude(ref_to_parent_form__record_reference__form_name__contains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=deepPK).values_list('pk', flat=True)) #EXCLUDES   
                                        newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                    elif term['QCODE'] == IS_NULL: 
                                        flattenedSet = list(   (  deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__isnull=True, ref_to_parent_form__record_reference_type__pk=deepPK) |  deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__iexact="", ref_to_parent_form__record_reference_type__pk=deepPK)    ).values_list('pk', flat=True)    ) #IS NULL  
                                        newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                    term['count'] =  newQuery.count()
                                    termStats.append(term)
                                    masterQuery = (newQuery & masterQuery)
                                    singleQueryStats['intersections'] = masterQuery.count()
                                #--------------------------------------------------------
                                # OR STATEMENT FOR a --TERM--
                                else:
                                    #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                    if   term['QCODE'] == CONTAINS: 
                                        flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__icontains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                        newQuery = queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                    elif term['QCODE'] == CS_CONTAINS: 
                                        flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=deepPK).values_list('pk', flat=True)) #ICONTAINS    
                                        newQuery = queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                    elif term['QCODE'] == EXACT_MATCH: 
                                        flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__exact=term['TVAL'], ref_to_parent_form__record_reference_type__pk=deepPK).values_list('pk', flat=True)) #EXACT MATCH
                                        newQuery = queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                    elif term['QCODE'] == EXCLUDES: 
                                        flattenedSet = list(deepFormType.form_set.all().exclude(ref_to_parent_form__record_reference__form_name__contains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=deepPK).values_list('pk', flat=True)) #EXCLUDES 
                                        newQuery = queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                    elif term['QCODE'] == IS_NULL: 
                                        flattenedSet = list(   (  deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__isnull=True, ref_to_parent_form__record_reference_type__pk=deepPK) |  deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__iexact="", ref_to_parent_form__record_reference_type__pk=deepPK)    ).values_list('pk', flat=True)    ) #IS NULL  
                                        newQuery = queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                    term['count'] =  newQuery.count()
                                    termStats.append(term)
                                    masterQuery = (newQuery | masterQuery)
                                    singleQueryStats['additions'] = masterQuery.count()               
     

                    #########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
                    # (Form ID) Lookups
                    #########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
                    elif rtype == "FORMID":
                            tCounter = 0
                            #store stats
                            singleQueryStats['rtype_name'] = term['LABEL']
                            singleQueryStats['rtype_pk'] = rtypePK
                            singleQueryStats['rtype'] = rtype
                            termStats = []
                            singleQueryStats['all_terms'] = termStats
                            logging.info("TimerD"+ " : " + str(time.process_time()))

                            #Now begin modifying the SQL query which each term of each individual query
                            #skip the term if the field was left blank
                            if term['TVAL'] != "" or term['QCODE'] == '4':
                                newQuery = None
                                logger.info( str(queryFormtype.form_set.all().filter(form_name__contains=term['TVAL'])))
                                if term['ANDOR'] != 'or':#We can assume it is an AND like addition if it's anything but 'or'
                                    logger.info( "Is it working?")
                                    #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                    if   term['QCODE'] == CONTAINS: newQuery = queriedForms.filter(form_name__icontains=term['TVAL']) #CONTAINS    
                                    elif term['QCODE'] == CS_CONTAINS: newQuery = queriedForms.filter(form_name__contains=term['TVAL']) #ICONTAINS                                   
                                    elif term['QCODE'] == EXACT_MATCH: newQuery = queriedForms.filter(form_name__exact=term['TVAL'])#MATCHES EXACT                                    
                                    elif term['QCODE'] == EXCLUDES: newQuery = queriedForms.exclude(form_name__contains=term['TVAL'])#EXCLUDES                                   
                                    elif term['QCODE'] == IS_NULL: newQuery = queriedForms.filter(form_name__isnull=True) #IS_NULL        
                                    term['count'] =  newQuery.count()
                                    termStats.append(term)
                                    masterQuery = (newQuery & masterQuery)
                                    singleQueryStats['intersections'] = masterQuery.count()
                                else:#Otherwise it's an OR statement
                                    #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                    if   term['QCODE'] == CONTAINS: newQuery = (queryFormtype.form_set.all().filter(form_name__icontains=term['TVAL']))#CONTAINS    
                                    elif term['QCODE'] == CS_CONTAINS: newQuery = (queryFormtype.form_set.all().filter(form_name__contains=term['TVAL']))#ICONTAINS                                   
                                    elif term['QCODE'] == EXACT_MATCH: newQuery = (queryFormtype.form_set.all().filter(form_name__exact=term['TVAL']))#MATCHES EXACT                                    
                                    elif term['QCODE'] == EXCLUDES: newQuery = (queryFormtype.form_set.all().exclude(form_name__contains=term['TVAL']))#EXCLUDES                                   
                                    elif term['QCODE'] == IS_NULL: newQuery = (queryFormtype.form_set.all().filter(form_name__isnull=True))#IS_NULL 
                                    term['count'] =  newQuery.count()
                                    termStats.append(term)
                                    masterQuery = (newQuery | masterQuery)
                                    singleQueryStats['additions'] = masterQuery.count()               

            
                    queryList.append(singleQueryStats)  
                    singleQueryStats['ANDOR'] = term['ANDOR']
                    singleQueryStats['count'] = masterQuery.count()
                    queryStats['count'] = singleQueryStats['count']
                   
                    logger.info("ABOUT TO HIT CONSTRAINTS")

                    #--------------------------------------------------------------------------------------------------------------------
                    #   PRIMARY CONSTRAINTS
                    #
                    #Let's add a count for our constraints and some information about the constraints
                    #These are just used to flesh out more information for graphs, and don't produce queried results
                    #--Doing it this way will improve the speed of queries significantly, as we don't NEED to get individual database
                    #--record information for each query--just count()'s  -- These will all essentially be 'AND' statements for the query
                    #--!!!Make sure we are using this specific query's queryset and not the amalgamated masterQuery--otherwise each constraint will be affected
                    primary_constraints = []
                    singleQueryStats['constraints'] = primary_constraints
                    primaryCount = 0.0
                    secondaryCount = 1.0
                    logger.info("COUNTS BELOW WTF")
                    logger.info(str(primaryCount) + "    :    " + str(secondaryCount))
                    logger.info(query['primary_constraints']['terms'])
                    logger.info(len(query['primary_constraints']['terms']) )
                    if 'primary_constraints' in query: 
                        primaryCount = float(len(query['primary_constraints']['terms']) )
                        logger.info("PRIMARY COUNT")
                        logger.info(primaryCount)
                    if 'secondary_constraints' in query: secondaryCount = len(query['secondary_constraints']['terms']) + 1 
                    totalNumberOfAllConstraints = primaryCount * secondaryCount
                    logger.info("COUNTS BELOW WTF")
                    logger.info(str(float(primaryCount)) + "    :    " + str(secondaryCount))
                    currentConstraintCount = 0.0
                    
                    if 'primary_constraints' in query:
                        constraint = query['primary_constraints']
                        p_terms = constraint['terms']
                        logger.info("OUR TERMS BELOW")
                        logger.info(p_terms)
                        logger.info(query['primary_constraints']['terms'])
                        unique_rtype_code = ""
                        unique_pk = constraint['pk']
                        if constraint['QCODE'] == ALL_UNIQUE_TERMS: 
                            if constraint['RTYPE'] == "FRRT": 
                                unique_rtype_code = "DEEP_" + constraint['RTYPE-DEEP'].split('__')[1]
                                if unique_rtype_code != "DEEP_FORMID": unique_pk = constraint['RTYPE-DEEP'].split('__')[0]
                            else: unique_rtype_code = constraint['RTYPE'] 
                            logger.info("STARTING UNIQUE RVAL SEARCH")
                            p_terms = get_unique_rtype_val_list(unique_rtype_code, unique_pk, queryFormtype)
                            logger.info(p_terms)
                            logger.info("IN ALL UNIQUE TERMS-- End of it")
                            #We also need to set the QCODE to a NEW QCODE--because we have exact matches, let's now reset it to QCODE EXACT_MATCH
                            constraint['QCODE'] = EXACT_MATCH
                            constraint['terms'] = p_terms
                            query['primary_constraints']['terms'] = p_terms
                            primaryCount = len(p_terms)
                            totalNumberOfAllConstraints = primaryCount * secondaryCount
                        for P_TVAL in p_terms:
                            
                            progressDataMessage['current_constraint'] = P_TVAL
                            logger.info((str(currentTermPercent) + " + "  + "(((" + str(termTotalPercent) + "/" +str(termCount)+ ")/" +str(totalNumberOfAllConstraints)+ ") * " +str(currentConstraintCount)))
                            logger.info((currentTermPercent + (((termTotalPercent/termCount)/totalNumberOfAllConstraints) * currentConstraintCount)))
                            progressDataMessage['percent_done'] = str(int(currentTermPercent + (((termTotalPercent/termCount)/totalNumberOfAllConstraints) * currentConstraintCount)))
                            progressData.jsonString=json.dumps(progressDataMessage)
                            progressData.save()
                            
                            #Only check if the entry box was filled in--if it's blank then do nothing and ignore it
                            if P_TVAL != "" and P_TVAL != None or constraint['QCODE'] == IS_NULL:  
                                #Check whether or not it's a frat or frrt
                                #We don't use an 'else' statement because I want to make sure that if someone edits the json before
                                #sending, that it will do nothing if it doesn't get the proper code
                                rtype = constraint['RTYPE']
                                rtypePK = constraint['pk']
                                rtypeLabel = ""
                                logger.info(rtype + " :======RTYPE==================>  " + term['TVAL']   + "  using term: " + P_TVAL)
                                if rtype == 'FRAT':
                                    logging.info("TimerZ START" + " : " + str(time.process_time()))
                                    if   constraint['QCODE'] == CONTAINS: constraintQuery = newQuery.filter(formrecordattributevalue__record_value__icontains=P_TVAL, formrecordattributevalue__record_attribute_type__pk=rtypePK) 
                                    elif constraint['QCODE'] == CS_CONTAINS: constraintQuery = newQuery.filter(formrecordattributevalue__record_value__contains=P_TVAL, formrecordattributevalue__record_attribute_type__pk=rtypePK)#ICONTAINS                                   
                                    elif constraint['QCODE'] == EXACT_MATCH: constraintQuery = newQuery.filter(formrecordattributevalue__record_value__exact=P_TVAL, formrecordattributevalue__record_attribute_type__pk=rtypePK)#MATCHES EXACT                                    
                                    elif constraint['QCODE'] == EXCLUDES: constraintQuery = newQuery.exclude(formrecordattributevalue__record_value__contains=P_TVAL, formrecordattributevalue__record_attribute_type__pk=rtypePK)#EXCLUDES                                   
                                    elif constraint['QCODE'] == IS_NULL: constraintQuery = newQuery.filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=rtypePK)#IS_NULL       
                                    logging.info("TimerZ END" + "-- : " + str(time.process_time()))  
                                elif rtype == 'FORMID':
                                    if   constraint['QCODE'] == CONTAINS: constraintQuery = newQuery.filter(form_name__icontains=P_TVAL) #CONTAINS    
                                    elif constraint['QCODE'] == CS_CONTAINS: constraintQuery = newQuery.filter(form_name__contains=P_TVAL) #ICONTAINS                                   
                                    elif constraint['QCODE'] == EXACT_MATCH: constraintQuery = newQuery.filter(form_name__exact=P_TVAL)#MATCHES EXACT                                    
                                    elif constraint['QCODE'] == EXCLUDES: constraintQuery = newQuery.exclude(form_name__contains=P_TVAL)#EXCLUDES                                   
                                    elif constraint['QCODE'] == IS_NULL: constraintQuery = newQuery.filter(form_name__isnull=True) #IS_NULL          
                                elif rtype == 'FRRT':
                                    deepFormType = FormType.objects.filter(pk=FormRecordReferenceType.objects.get(pk=rtypePK).form_type_reference.pk)
                                    #***RECYCLING BIN*** Make sure our this Deep query FormType is always filtered by recycling bin flags
                                    deepFormType = deepFormType.filter(flagged_for_deletion=False, is_public=True)
                                    deepFormType = deepFormType[0]
                                    deepPK, deepRTYPE = constraint['RTYPE-DEEP'].split('__')
                                    logger.info(deepRTYPE + " <!=========DEEP RTYPE====================  " + P_TVAL)
                                    if deepRTYPE == 'FORMID':
                                        rtypeLabel = "Form ID"
                                        if   constraint['QCODE'] == CONTAINS: constraintQuery = newQuery.filter(ref_to_parent_form__record_reference__form_name__icontains=P_TVAL, ref_to_parent_form__record_reference_type__pk=rtypePK)#CONTAINS    
                                        elif constraint['QCODE'] == CS_CONTAINS: constraintQuery = newQuery.filter(ref_to_parent_form__record_reference__form_name__contains=P_TVAL, ref_to_parent_form__record_reference_type__pk=rtypePK)#ICONTAINS                                   
                                        elif constraint['QCODE'] == EXACT_MATCH: constraintQuery = newQuery.filter(ref_to_parent_form__record_reference__form_name__exact=P_TVAL, ref_to_parent_form__record_reference_type__pk=rtypePK)#MATCHES EXACT                                    
                                        elif constraint['QCODE'] == EXCLUDES: constraintQuery = newQuery.exclude(ref_to_parent_form__record_reference__form_name__contains=P_TVAL, ref_to_parent_form__record_reference_type__pk=rtypePK)#EXCLUDES                                   
                                        elif constraint['QCODE'] == IS_NULL: constraintQuery = newQuery.filter(ref_to_parent_form__record_reference__isnull=True, ref_to_parent_form__record_reference_type__pk=rtypePK).count()#IS_NULL                                           
                                    elif deepRTYPE == 'FRRT':
                                        rtypeLabel = FormRecordReferenceType.objects.get(pk=deepPK).record_type
                                        if   constraint['QCODE'] == CONTAINS: 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__icontains=P_TVAL).values_list('pk', flat=True)) #ICONTAINS    
                                            constraintQuery = newQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet) 
                                        elif constraint['QCODE'] == CS_CONTAINS:
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=P_TVAL).values_list('pk', flat=True)) #ICONTAINS    
                                            constraintQuery = newQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)                                    
                                        elif constraint['QCODE'] == EXACT_MATCH: 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__exact=P_TVAL).values_list('pk', flat=True)) #ICONTAINS    
                                            constraintQuery = newQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet) 
                                        elif constraint['QCODE'] == EXCLUDES:
                                            flattenedSet = list(deepFormType.form_set.all().exclude(ref_to_parent_form__record_reference__form_name__contains=P_TVAL).values_list('pk', flat=True)) #ICONTAINS    
                                            constraintQuery = newQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif constraint['QCODE'] == IS_NULL: 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__isnull=True).values_list('pk', flat=True)) #ICONTAINS    
                                            constraintQuery = newQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet) 
                                    elif deepRTYPE == 'FRAT':
                                        rtypeLabel = FormRecordAttributeType.objects.get(pk=deepPK).record_type
                                        if   constraint['QCODE'] == CONTAINS:
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__icontains=P_TVAL, formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS     
                                            constraintQuery = newQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif constraint['QCODE'] == CS_CONTAINS:
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__contains=P_TVAL, formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            constraintQuery = newQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif constraint['QCODE'] == EXACT_MATCH:
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__exact=P_TVAL, formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            constraintQuery = newQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif constraint['QCODE'] == EXCLUDES: 
                                            flattenedSet = list(deepFormType.form_set.all().exclude(formrecordattributevalue__record_value__contains=P_TVAL, formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            constraintQuery = newQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif constraint['QCODE'] == IS_NULL: 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            constraintQuery = newQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                primaryConstraintStat = {}                                        
                                primaryConstraintStat['count'] = constraintQuery.count()
                                primaryConstraintStat['name'] = constraint['LABEL'] + " : " + rtypeLabel
                                primaryConstraintStat['rtype_pk'] = rtypePK
                                primaryConstraintStat['rtype'] = rtype
                                primaryConstraintStat['qcode'] = constraint['QCODE']
                                primaryConstraintStat['tval'] = P_TVAL
                                primaryConstraintStat['parent_term'] = term['TVAL']
                                primaryConstraintStat['parent_label'] = term['LABEL']
                                primary_constraints.append(primaryConstraintStat)
                                queryStats['primary_constraints'].append(primaryConstraintStat)
                                #--------------------------------------------------------------------------------------------------------------------
                                #   SECONDARY CONSTRAINTS
                                #
                                #Let's add a count for our secnodary constraints and some information about them
                                #These are just used to flesh out more information for graphs, and don't produce queried results
                                #--Doing it this way will improve the speed of queries significantly, as we don't NEED to get individual database
                                #--record information for each query--just count()'s  -- These will all essentially be 'AND' statements for the query
                                #--!!!Make sure we are using this specific query's queryset and not the amalgamated masterQuery--otherwise each constraint will be affected
                                #--This also differs from a normal constraint in that a secondary constraint is seen as another dimensional control over the results.
                                secondary_constraints = []
                                if 'secondary_constraints' in query:
                                    secondaryConstraint = query['secondary_constraints']
                                    s_terms = secondaryConstraint['terms']
                                    logger.info("OUR TERMS BELOW SECOND??")
                                    logger.info(s_terms)
                                    unique_rtype_code = ""
                                    unique_pk = secondaryConstraint['pk']
                                    if secondaryConstraint['QCODE'] == ALL_UNIQUE_TERMS: 
                                        if secondaryConstraint['RTYPE'] == "FRRT": 
                                            unique_rtype_code = "DEEP_" + secondaryConstraint['RTYPE-DEEP'].split('__')[1]
                                            if unique_rtype_code != "DEEP_FORMID": unique_pk = secondaryConstraint['RTYPE-DEEP'].split('__')[0]
                                        else: unique_rtype_code = secondaryConstraint['RTYPE'] 
                                        logger.info("STARTING UNIQUE RVAL SEARCH")
                                        s_terms = get_unique_rtype_val_list(unique_rtype_code, unique_pk, queryFormtype)
                                        logger.info(s_terms)
                                        logger.info("IN ALL UNIQUE TERMS-- End of it")
                                        #We also need to set the QCODE to a NEW QCODE--because we have exact matches, let's now reset it to QCODE EXACT_MATCH
                                        secondaryConstraint['QCODE'] = EXACT_MATCH
                                        secondaryConstraint['terms'] = s_terms
                                        query['secondary_constraints']['terms'] = s_terms
                                        secondaryCount = len(s_terms)
                                        totalNumberOfAllConstraints = primaryCount * secondaryCount
                                    
                                    for secondaryTVAL in s_terms:
                                        logger.info("WERE LOOPING THROUGH SECOND VALS??")
                                        logger.info(secondaryTVAL)
                                        progressDataMessage['current_constraint'] = P_TVAL + " => " + secondaryTVAL
                                        progressData.jsonString=json.dumps(progressDataMessage) 
                                        progressData.save()                                            
                                        #Only check if the entry box was filled in--if it's blank then do nothing and ignore it
                                        if secondaryTVAL != "" or secondaryConstraint['QCODE'] == '4': 
                                            #Check whether or not it's a frat or frrt
                                            #We don't use an 'else' statement because I want to make sure that if someone edits the json before
                                            #sending, that it will do nothing if it doesn't get the proper code
                                            rtype = secondaryConstraint['RTYPE']
                                            rtypePK = secondaryConstraint['pk']
                                            rtypeTwoLabel = ""
                                            if rtype == 'FRAT':
                                                logging.info("TimerKK START" + " : " + str(time.process_time()))
                                                if   secondaryConstraint['QCODE'] == CONTAINS: secondaryConstraintQuery = constraintQuery.filter(formrecordattributevalue__record_value__icontains=secondaryTVAL, formrecordattributevalue__record_attribute_type__pk=rtypePK)
                                                elif secondaryConstraint['QCODE'] == CS_CONTAINS: secondaryConstraintQuery = constraintQuery.filter(formrecordattributevalue__record_value__contains=secondaryTVAL, formrecordattributevalue__record_attribute_type__pk=rtypePK)#ICONTAINS                                   
                                                elif secondaryConstraint['QCODE'] == EXACT_MATCH: secondaryConstraintQuery = constraintQuery.filter(formrecordattributevalue__record_value__exact=secondaryTVAL, formrecordattributevalue__record_attribute_type__pk=rtypePK)#MATCHES EXACT                                    
                                                elif secondaryConstraint['QCODE'] == EXCLUDES: secondaryConstraintQuery = constraintQuery.exclude(formrecordattributevalue__record_value__contains=secondaryTVAL, formrecordattributevalue__record_attribute_type__pk=rtypePK)#EXCLUDES                                   
                                                elif secondaryConstraint['QCODE'] == IS_NULL: secondaryConstraintQuery = constraintQuery.filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=rtypePK)#IS_NULL      
                                            elif rtype == 'FORMID':
                                                if   secondaryConstraint['QCODE'] == CONTAINS: secondaryConstraintQuery = constraintQuery.filter(form_name__icontains=secondaryTVAL, ref_to_parent_form__record_reference_type__pk=rtypePK) #CONTAINS    
                                                elif secondaryConstraint['QCODE'] == CS_CONTAINS: secondaryConstraintQuery = constraintQuery.filter(form_name__contains=secondaryTVAL, ref_to_parent_form__record_reference_type__pk=rtypePK) #ICONTAINS                                   
                                                elif secondaryConstraint['QCODE'] == EXACT_MATCH: secondaryConstraintQuery = constraintQuery.filter(form_name__exact=secondaryTVAL, ref_to_parent_form__record_reference_type__pk=rtypePK)#MATCHES EXACT                                    
                                                elif secondaryConstraint['QCODE'] == EXCLUDES: secondaryConstraintQuery = constraintQuery.exclude(form_name__icontains=secondaryTVAL, ref_to_parent_form__record_reference_type__pk=rtypePK)#EXCLUDES                                   
                                                elif secondaryConstraint['QCODE'] == IS_NULL: secondaryConstraintQuery = constraintQuery.filter(form_name__isnull=True, ref_to_parent_form__record_reference_type__pk=rtypePK) #IS_NULL       
                                            elif rtype == 'FRRT':
                                                deepFormType = FormType.objects.filter(pk=FormRecordReferenceType.objects.get(pk=rtypePK).form_type_parent.pk)
                                                #***RECYCLING BIN*** Make sure our this Deep query FormType is always filtered by recycling bin flags
                                                deepFormType = deepFormType.filter(flagged_for_deletion=False, is_public=True)
                                                deepFormType = deepFormType[0]
                                                deepPK, deepRTYPE = secondaryConstraint['RTYPE-DEEP'].split('__')
                                                logger.info(secondaryConstraint)
                                                if deepRTYPE == 'FORMID':
                                                    rtypeTwoLabel = "Form ID"
                                                    if   secondaryConstraint['QCODE'] == CONTAINS: secondaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__form_name__icontains=secondaryTVAL, ref_to_parent_form__record_reference_type__pk=rtypePK)#CONTAINS    
                                                    elif secondaryConstraint['QCODE'] == CS_CONTAINS: secondaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__form_name__contains=secondaryTVAL, ref_to_parent_form__record_reference_type__pk=rtypePK)#ICONTAINS                                   
                                                    elif secondaryConstraint['QCODE'] == EXACT_MATCH: secondaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__form_name__exact=secondaryTVAL, ref_to_parent_form__record_reference_type__pk=rtypePK)#MATCHES EXACT                                    
                                                    elif secondaryConstraint['QCODE'] == EXCLUDES: secondaryConstraintQuery = constraintQuery.exclude(ref_to_parent_form__record_reference__form_name__contains=secondaryTVAL, ref_to_parent_form__record_reference_type__pk=rtypePK)#EXCLUDES                                   
                                                    elif secondaryConstraint['QCODE'] == IS_NULL: secondaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__isnull=True, ref_to_parent_form__record_reference_type__pk=rtypePK)#IS_NULL                                                
                                                    logging.info("TimerKK END" + "-- : " + str(time.process_time()))   
                                                elif deepRTYPE == 'FRRT':  
                                                    rtypeTwoLabel = FormRecordReferenceType.objects.get(pk=deepPK).record_type
                                                    if   secondaryConstraint['QCODE'] == CONTAINS: 
                                                        flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__icontains=secondaryTVAL).values_list('pk', flat=True)) #ICONTAINS    
                                                        secondaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet) 
                                                    elif secondaryConstraint['QCODE'] == CS_CONTAINS:
                                                        flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=secondaryTVAL).values_list('pk', flat=True)) #ICONTAINS    
                                                        secondaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)                                    
                                                    elif secondaryConstraint['QCODE'] == EXACT_MATCH: 
                                                        flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__exact=secondaryTVAL).values_list('pk', flat=True)) #ICONTAINS    
                                                        secondaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet) 
                                                    elif secondaryConstraint['QCODE'] == EXCLUDES:
                                                        flattenedSet = list(deepFormType.form_set.all().exclude(ref_to_parent_form__record_reference__form_name__contains=secondaryTVAL).values_list('pk', flat=True)) #ICONTAINS    
                                                        secondaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                                    elif secondaryConstraint['QCODE'] == IS_NULL: 
                                                        flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__isnull=True).values_list('pk', flat=True)) #ICONTAINS    
                                                        secondaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet) 
                                                elif deepRTYPE == 'FRAT':
                                                    rtypeTwoLabel = FormRecordAttributeType.objects.get(pk=deepPK).record_type
                                                    if   secondaryConstraint['QCODE'] == CONTAINS:
                                                        flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__icontains=secondaryTVAL, formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                                        secondaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                                    elif secondaryConstraint['QCODE'] == CS_CONTAINS:
                                                        flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__contains=secondaryTVAL, formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                                        secondaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                                    elif secondaryConstraint['QCODE'] == EXACT_MATCH:
                                                        flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__exact=secondaryTVAL, formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                                        secondaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                                    elif secondaryConstraint['QCODE'] == EXCLUDES: 
                                                        flattenedSet = list(deepFormType.form_set.all().exclude(formrecordattributevalue__record_value__contains=secondaryTVAL, formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                                        secondaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                                    elif secondaryConstraint['QCODE'] == IS_NULL: 
                                                        flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                                        secondaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                        
                                            secondaryConstraintStat = {}
                                            secondaryConstraintStat['count'] = secondaryConstraintQuery.count()
                                            secondaryConstraintStat['name'] = secondaryConstraint['LABEL'] + " : " + rtypeTwoLabel
                                            secondaryConstraintStat['rtype_pk'] = rtypePK
                                            secondaryConstraintStat['rtype'] = rtype
                                            secondaryConstraintStat['qcode'] = secondaryConstraint['QCODE']
                                            secondaryConstraintStat['tval'] = secondaryTVAL
                                            secondaryConstraintStat['parent_term'] = P_TVAL
                                            secondaryConstraintStat['parent_label'] = constraint['LABEL']
                                            secondaryConstraintStat['big_parent_term'] = term['TVAL']
                                            secondaryConstraintStat['big_parent_label'] = term['LABEL']
                                            secondaryConstraintStat['data_label'] = secondaryConstraintStat['name'] + ' ' + secondaryConstraintStat['tval'] +' - ' + primaryConstraintStat['name'] + ' ' + primaryConstraintStat['tval'] +' - ' + singleQueryStats['rtype_name'] + ' ' + singleQueryStats['all_terms'][0]['TVAL']
                                            secondary_constraints.append(secondaryConstraintStat)
                                            queryStats['secondary_constraints'].append(secondaryConstraintStat)
                                        currentConstraintCount+=1    
                                     
                                    
                                    logging.info("TimerG"+ " : " + str(time.process_time()))
                            currentConstraintCount+=1
                    #Increment our progressData stats counter for the term
                    #We've been modifying it in the constraints--so let's round it down before incrementing it a full step
                    termCounter +=  1
                progressDataMessage['message'] = "Loading Queried Forms & Sending generated stats now..."
                progressDataMessage['current_query'] = ""
                progressDataMessage['current_term'] = ""
                progressDataMessage['current_constraint'] = ""
                progressDataMessage['percent_done'] = "70"
                progressDataMessage['stats'] = queryStats
                progressData.jsonString=json.dumps(progressDataMessage)
                progressData.save() 
                
                
                logger.info("*********************************************************************************************************************************************************************************************************")
                
                
                #Now make sure our final queried list has distint values--merging querysets has a tendency to create duplicates
                masterQuery = masterQuery.distinct()
                #***RECYCLING BIN*** A Final redundant recycling bin filter--just to be safe
                masterQuery = masterQuery.exclude(is_public=False)                      
            

                
                #We need to check the # of rtypes in our header list now--if it's less than 5, then let's add from the ordered list
                #We also need to make sure we aren't adding duplicates of the RTYPES, e.g. if we're looking for a match under "Object Number" and Object Number is already
                #--in our sorted order-num list--let's not re-add it.
                for attType in form_att_type_list:
                    logger.info( "AttTypeList:  " + str(attType))
                    matchfound = False
                    for queryAttType in queryRTYPElist:
                        if attType[2] == queryAttType[2]:
                            matchfound = True
                    if matchfound == False and len(queryRTYPElist) < 5:    
                        #let's arbitrarily add '100' to the order number so that our queries are definitely in front of these
                        queryRTYPElist.append((attType[0] + 100,attType[1],attType[2],attType[3]))
                        
                #We need to grab ALL the form pk values in a similarly sorted list 
                paginationFormList = masterQuery.order_by('sort_index').values_list('pk', flat=True)

                
                numberOfFormsPerPage = 25
                #-----------------------------------------------------------------------------------------------------------
                # Here we need to determine whether or not the form type being queried is hierchical.
                #   --If it is hierachical, then we just organize the masterQuery and sort it with the hierachy in mind
                #   --as well as with its hierchical labels--otherwise just perform a normal sort by its label
                if queryFormtype.is_hierarchical:
                    global hierarchyFormList
                    hierarchyFormList = []
                    #Finally let's organize all of our reference and attribute values to match their provided order number
                    #We want to find all the forms that have no parent element first--these are the top of the nodes
                    #Then we'll organize the forms by hierarchy--which can then be put through the normal ordered query
                    masterQuery =  masterQuery.filter(hierarchy_parent=None).exclude(form_number=None, form_name=None)[:numberOfFormsPerPage]
                    #CACHE -- this caches the query for the loop
                    if masterQuery:
                        for aForm in masterQuery: 
                            logging.info(aForm.form_name)
                            hierarchyFormList.append(aForm)
                            #Make a recursive function to search through all children
                            def find_children(currentParentForm):          
                                global hierarchyFormList
                                for currentChild in currentParentForm.form_set.all(): 
                                    hierarchyFormList.append(currentChild)
                                    find_children(currentChild)
                            find_children(aForm)
                    #reset our masterQuery to our new hierachical list!
                    masterQuery = hierarchyFormList
                else:             
                    #sort the formlist by their sort_index
                    logger.info("========================================TESTING: PRE SORT/SLICE")
                    masterQuery = masterQuery.order_by('sort_index')[:numberOfFormsPerPage]
                    logger.info("AFTER SLICE/SORT")
                progressDataMessage['message'] = "Performing SQL query to pull out all forms--may take time"
                progressDataMessage['percent_done'] = "75"
                progressDataMessage['stats'] = queryStats
                progressData.jsonString=json.dumps(progressDataMessage)
                progressData.save()                        
                #CACHE -- This cache's the query before looping through it
                logger.info("BEFORE CACHING QUERY/EVALUATING")
                logger.info(masterQuery.query)
                if masterQuery:
                    logger.info("AFTER CACHEING QUERY/EVALUATING")
                    formCounter = 0 
                    for aForm in masterQuery:
                        logger.info("form loop")
                        progressDataMessage['message'] = "Running through forms and converting to a usable format for navigation"
                        progressDataMessage['percent_done'] = str(int(75+((25.0/numberOfFormsPerPage) * formCounter) ))
                        progressDataMessage['stats'] = queryStats
                        progressData.jsonString=json.dumps(progressDataMessage)
                        progressData.save()    
                        rowList = []
                        #Let's loop through each item in the queryRTYPE list and match up the frav's in each queried form so the headers match the form attribute values
                        for rtype in queryRTYPElist:
                            if rtype[1] == 'frat':
                                #logger.info( str(rtype[2]) + '  ' + str(aForm.formrecordattributevalue_set.all().filter(record_attribute_type__pk=rtype[2]).count()))
                                formRVAL = aForm.formrecordattributevalue_set.all().filter(record_attribute_type__pk=rtype[2])
                                #We need to check for NULL FRAV's here. When a user manually creates new forms, they don't always have FRAVS created for them if they leave it blank
                                if formRVAL.exists():
                                    rowList.append((rtype[0],'frav',formRVAL[0].record_value, formRVAL[0].pk))
                                else:
                                    logger.info( "Whoops--something happened. There are no RVALS for 'frats' using: " + str(rtype[2]))
                                    #If there isn't an RVAL for this RTYPE then make a new one and return it instead
                                    newFRAV = FormRecordAttributeValue()
                                    newFRAV.record_attribute_type = FormRecordAttributeType.objects.get(pk=rtype[2])
                                    newFRAV.form_parent = aForm
                                    newFRAV.project = aForm.project
                                    newFRAV.record_value = ""
                                    newFRAV.save()
                                    rowList.append((rtype[0],'frav',newFRAV.record_value, newFRAV.pk))
                            else:
                                #logger.info( aForm.ref_to_parent_form.all().count())
                                #logger.info( aForm.pk)
                                #for frrt in aForm.ref_to_parent_form.all():
                                #    logger.info( "" + str(frrt.pk))
                                formRVAL = aForm.ref_to_parent_form.all().filter(record_reference_type__pk=rtype[2])
                                if formRVAL.exists():
                                    formRVAL = formRVAL[0]
                                    #First check to see if there are any relations stored in the many to many relationship
                                    #   --if there are, then load them normally, and if not change the value to a frrv-ext tag and store the external ID for the
                                    #   --ajax request to process properly
                                    if formRVAL.record_reference.all().count() > 0:
                                        #we need to store a list of its references--it's a manytomany relationship
                                        #A comma should be sufficient to separate them, but to be safe--we'll make our delimeter a ^,^
                                        #-- we also need to provide the formtype pk value for the link
                                        listOfRefs = ""
                                        for rec in formRVAL.record_reference.all():
                                            listOfRefs += str(rec) + '|^|' + str(rec.form_type.pk) + '|^|' + str(rec.pk) + "^,^"
                                        #remove the last delimeter
                                        listOfRefs = listOfRefs[0:-3]
                                        rowList.append((rtype[0],'frrv',listOfRefs, formRVAL.pk))
                                    else:
                                        #Store the external key value instead and change it to a frrv-ext for the AJAX callable
                                        rowList.append((rtype[0],'frrv-ext',formRVAL.external_key_reference, formRVAL.pk))
                                else:
                                    #Store the external key value instead and change it to a frrv-null for the AJAX callable
                                    rowList.append((rtype[0],'frrv-null',"", ""))

                       
                        #sort the new combined reference ad attribute type list combined
                        rowList = sorted(rowList, key=lambda att: att[0])
                        #logger.info( str(rowList))
                        #Now let's handle the thumbnail bit of business for the query
                        #--If the current form IS a media type already, then use itself to grab the thumbnail URI
                        #logger.info('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ ABOUT TO GET THUMBNAILS')
                        if aForm.form_type.type == 1:
                            thumbnailURI = aForm.get_thumbnail_type()
                        else:
                            logger.info("LOOKING FOR A FRRT")
                            #let's find the first media type in the order but offer a default to "NO PREVIEW" if not found
                            thumbnailURI = staticfiles_storage.re_path("/site-images/no-thumb-missing.png")
                            for record in rowList:            
                                #if it's a reference
                                if record[1] == 'frrv' or record[1] == 'frrv-ext':
                                    currentRTYPE = FormRecordReferenceValue.objects.get(pk=int(record[3]))
                                    #if it's not a NoneType reference:
                                    if currentRTYPE.record_reference_type.form_type_reference != None:
                                        #If its a reference to a media type
                                        if currentRTYPE.record_reference_type.form_type_reference.type == 1:
                                            logger.info( "WE GOT A MATCH")
                                            #Because a form record reference value is a ManyToMany relationship, we just grab the first one in the list
                                            #TODO this may need to be edited later--because you can't order the selections. I may add another ForeignKey called
                                            #"Thumbnail Reference" which links to a single relation to a form of a media type--this would also
                                            #probably solve the complexity of looping through to grab it as it stands right now
                                            #****WE also have to check for NULL references
                                            if currentRTYPE.record_reference.all().count() > 0:
                                                thumbnailURI = currentRTYPE.record_reference.all()[0].get_thumbnail_type()
                                            break
                            #Finally--if there aren't any relevant media types in our frrts, let's do a last second check for ANY frrts that are media types
                            #--that AREN'T in our RTYPE list
                            if thumbnailURI == staticfiles_storage.re_path("/site-images/no-thumb-missing.png"):
                                logger.info("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%    We're TRYING TO GET A THUMBNAIL")
                                currentRVAL = aForm.ref_to_parent_form.filter(record_reference_type__form_type_reference__type=1)
                                logger.info(currentRVAL)
                                if currentRVAL.exists():
                                    #Just get the first one out of the list
                                    if len(currentRVAL[0].record_reference.all()) > 0:
                                        logger.info(currentRVAL[0].record_reference.all()[0].form_name)
                                        thumbnailURI = currentRVAL[0].record_reference.all()[0].get_thumbnail_type()
                                        
                        formList.append([thumbnailURI,str(aForm.pk), aForm, rowList])   
                        formCounter += 1
                form_att_type_list, form_list = form_att_type_list, formList
                
                logger.info("TESTING============================================================================")

                
                finishedJSONquery = {}
                
                headerList=[]
                for rtype in queryRTYPElist:
                    rtypeDict = {}
                    rtypeDict["index"] = rtype[0]
                    rtypeDict["rtype"] = rtype[1]
                    rtypeDict["pk"] = rtype[2]
                    rtypeDict["name"] = rtype[3]
                    headerList.append(rtypeDict)


                
                finishedJSONquery["rtype_header"] = headerList
                allFormList = []
                counter = 0
                total = len(formList)
                for form in formList:
                    #update our progress bar
                    counter += 1
                    currentPercent = 93 + int((counter*(5.0/total)))

                    
                    formDict = {}
                    formDict["thumbnail_URI"] = form[0]
                    formDict["pk"] = form[1]
                    if queryFormtype.is_hierarchical: formDict["form_id"] = form[2].get_hierarchy_label()
                    else: formDict["form_id"] = form[2].form_name
                    formRVALS = []
                    for rval in form[3]:
                        rvalDict = {}
                        rvalDict["index"] = rval[0]
                        rvalDict["rtype"] = rval[1]
                        rvalDict["value"] = rval[2]
                        rvalDict["pk"] = rval[3]
                        formRVALS.append(rvalDict)
                    formDict["rvals"] = formRVALS
                    allFormList.append(formDict)

                finishedJSONquery["pagination_rtype_header"] = queryRTYPElist
                finishedJSONquery["form_list"] = allFormList
                finishedJSONquery["currentQuery"] = request.GET['master_query']
                finishedJSONquery["totalResultCount"] = queryStats['count']
                finishedJSONquery['formtype'] = query['formtype_label']
                finishedJSONquery['formtype_pk'] = query['formtype_pk']
                finishedJSONquery['project'] = query['project_label']
                finishedJSONquery['project_pk'] = query['project_pk']
                finishedJSONquery['pagination_form_list'] = list(paginationFormList)
                finishedJSONquery['query_stats'] = queryStats
                logger.info(queryStats['query_list'])
                logger.info(json.dumps(queryStats['query_list']))
                all_project_queries.append(finishedJSONquery)
    except Exception as e:
        logger.info("LONG QUERY ERROR")
        logger.info(e)
        progressDataMessage['SERVER_ERROR'] = e
        progressData.jsonString=json.dumps(progressDataMessage)
        progressData.is_finished = True
        progressData.save()      
        logging.exception("message")
        return HttpResponse(progressDataMessage, content_type="application/json")
    #convert to JSON
    progressDataMessage['completed_process_data'] = all_project_queries
    all_project_queries = json.dumps(all_project_queries)

    progressDataMessage['message'] = "Finished"
    progressDataMessage['percent_done'] = "100"
    progressDataMessage['stats'] = queryStats
    
    progressDataMessage['is_complete'] = "True"
    progressData.jsonString=json.dumps(progressDataMessage)
    progressData.is_finished = True
    progressData.save()         
    logger.info(  "Timer End"     )
    return HttpResponse(all_project_queries, content_type="application/json")

    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'views.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")   








##==========================================================================================================================    
##==========================================================================================================================    
##==========================================================================================================================    
##  END OF COMPLEX API ENDPOINTS   ****************************************************************************************************
##==========================================================================================================================        
##==========================================================================================================================    
##==========================================================================================================================    



##==========================================================================================================================    
##==========================================================================================================================    
## PUBLIC MODEL VIEWS   ****************************************************************************************************
##==========================================================================================================================  


    
#=====================================================================================#
#  BLOGPOST()
#=====================================================================================#       
def blogpost(request, **kwargs):
    logger.info(request)
    logger.info('RIGHT HERE')
    blogpost = BlogPost.objects.get(pk=kwargs['post_id'])
    #Make sure we don't populate our lists below with the current requested post
    blogposts = BlogPost.objects.filter(project=None).exclude(id=kwargs['post_id']).order_by('-date_created') 
    recentposts = BlogPost.objects.exclude(id=kwargs['post_id']).order_by('-date_created')[:5]
    blogposts = blogposts[0:10]
    kwargs.update({'blogpost':blogpost})
    kwargs.update({'blogpost_list':blogposts}) 
    kwargs.update({'recentposts_list':recentposts})     
    
    
    
    return HttpResponse(render(request, 'public_frontend/blogpost.html', kwargs, RequestContext(request)))  
    
#=====================================================================================#
#  PROJECT()
#=====================================================================================#       
def project(request, **kwargs):
    #-----------------------------------------------------------------------------------
    #   This view delivers the project overview of users/stats etc. as well as give
    #       --public users a list of formtypes etc. in the template
    
    #First check if the project requested exists
    try: project = FormProject.objects.get(pk=kwargs['project_pk'])
    except: raise Http404("Project Does Not Exist!")       
    
    #Now make sure it's set to public or log the attempted access to the security logs, and give the user a 404 error page
    if project.is_public:
        kwargs.update({'project':project})      
        return HttpResponse(render(request, 'public_frontend/project.html', kwargs, RequestContext(request)))    
    else:
        SECURITY_log_security_issues('views.py - ' + str(sys._getframe().f_code.co_name), "PROJECT IS NOT PUBLIC", request.META)
        raise Http404("Project Does Not Exist!")  

    
#=====================================================================================#
#  FORMTYPE()
#=====================================================================================#       
def formtype(request, **kwargs):
    formtype = FormType.objects.get(pk=kwargs['formtype_id'], flagged_for_deletion=False, is_public=True)
    if formtype:
        results_per_page = 30
        page_number = 1
        if 'page_num' in kwargs: page_number = kwargs['page_num']
        startIndex = (results_per_page * page_number) - results_per_page
        endIndex = results_per_page * page_number
        forms = formtype.form_set.filter(is_public=True, flagged_for_deletion=False)[startIndex:endIndex]
        kwargs['formtype'] = formtype
        form_list = []
        if forms:
            for form in forms:
                new_form = {}
                new_form['name'] = form.form_name
                new_form['pk'] =    form.pk
                new_form['thumbnail'] = form.get_ref_thumbnail()
                new_form['fravs'] = form.formrecordattributevalue_set.filter(is_public=True, flagged_for_deletion=False)
                new_form['frrvs'] = form.ref_to_parent_form.filter(is_public=True, flagged_for_deletion=False)
                form_list.append(new_form)            
        kwargs['form_list'] = form_list
        kwargs['project_override_template'] = "public_frontend/public_base.html"
        kwargs['project'] = formtype.project
        kwargs['menugroups'] = kwargs['project'].menugroup_set.all()
        kwargs['formtypes'] = FormType.objects.filter(project__pk=kwargs['project'].pk, is_public=True, flagged_for_deletion=False)
        kwargs['webpage_list'] = Webpage.objects.filter(project__pk=kwargs['project'].pk, is_public=True, flagged_for_deletion=False)
        kwargs['api_urls'] = get_api_endpoints()
        ftgs = []
        for formtypegroup in kwargs['project'].formtypegroup_set.all():
            if formtypegroup.formtype_set.filter(is_public=True, flagged_for_deletion=False).count() > 0:
                ftgs.append(formtypegroup)
        kwargs['formtypegroups'] = ftgs
        #SETUP PAGINATION BAR
        pagination = {}
        kwargs['pagination'] = pagination
        pagination['total_results'] = formtype.form_set.filter(is_public=True, flagged_for_deletion=False).count()
        pagination['results_per_page'] = results_per_page
        pagination['current_page'] = page_number
        pagination['last_page'] =  int(math.ceil(pagination['total_results'] /results_per_page))
        divs = []
        pagination['html_element_list'] = divs
        
        divs.append({"url":reverse("maqluengine:formtype", kwargs={"formtype_id":formtype.pk,"page_num":1}),"class":"page-CONTROL", "page_num":"|<"})
        
        if page_number-1<1: divs.append({"url":reverse("maqluengine:formtype", kwargs={"formtype_id":formtype.pk,"page_num":1}),"class":"page-CONTROL",  "page_num":"<<"})
        else:               divs.append({"url":reverse("maqluengine:formtype", kwargs={"formtype_id":formtype.pk,"page_num":page_number-1}),"class":"page-CONTROL",  "page_num":"<<"})
       
        counter = 4
        while counter > 0:
            if page_number-counter<1: divs.append({"url":"#","class":"page-EMPTY", "page_num":"ʘ"})
            else:               divs.append({"url":reverse("maqluengine:formtype", kwargs={"formtype_id":formtype.pk,"page_num":page_number-counter}),"class":"page-NUMBER", "page_num":page_number-counter})
            counter-=1
            
        divs.append({"url":reverse("maqluengine:formtype", kwargs={"formtype_id":formtype.pk,"page_num":page_number}),"class":"page-CURRENT", "page_num":page_number})
        
        counter = 1
        while counter < 5:
            if page_number+counter > pagination['last_page']: divs.append({"url":"#","class":"page-EMPTY", "page_num":"ʘ"})
            else:               divs.append({"url":reverse("maqluengine:formtype", kwargs={"formtype_id":formtype.pk,"page_num":page_number+counter}),"class":"page-NUMBER", "page_num":page_number+counter})
            counter+=1   
            
        if page_number+1>pagination['last_page']: divs.append({"url":reverse("maqluengine:formtype", kwargs={"formtype_id":formtype.pk,"page_num":pagination['last_page']}),"class":"page-CONTROL",  "page_num":">>"})
        else:                                     divs.append({"url":reverse("maqluengine:formtype", kwargs={"formtype_id":formtype.pk,"page_num":page_number+1}),"class":"page-CONTROL",  "page_num":">>"})
        
        divs.append({"url":reverse("maqluengine:formtype", kwargs={"formtype_id":formtype.pk,"page_num":pagination['last_page']}),"class":"page-CONTROL",  "page_num":">|"})
        
        
        return HttpResponse(render(request, 'public_frontend/formtype.html', kwargs, RequestContext(request)))
    else:
        SECURITY_log_security_issues(request.user, 'views.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return Http404("Project Does Not Exist!")   
#=====================================================================================#
#   FORM()
#=====================================================================================#       
def form(request, **kwargs):
    form = Form.objects.get(pk=kwargs['form_id'], flagged_for_deletion=False, is_public=True)
    logger.info(form)
    if form:
        kwargs['form'] = form
        kwargs['formtype'] = form.form_type
        kwargs['api_urls'] = get_api_endpoints()
        kwargs['project_override_template'] = "public_frontend/public_base.html"
        kwargs['project'] = form.project
        kwargs['menugroups'] = kwargs['project'].menugroup_set.all()
        kwargs['formtypes'] = FormType.objects.filter(project__pk=kwargs['project'].pk, is_public=True, flagged_for_deletion=False)
        kwargs['webpage_list'] = Webpage.objects.filter(project__pk=kwargs['project'].pk, is_public=True, flagged_for_deletion=False)
        #Now let's get all of our RTYPES for the form
        kwargs['thumbnail'] = form.get_ref_thumbnail()
        kwargs['fravs'] = form.formrecordattributevalue_set.filter(is_public=True, flagged_for_deletion=False).values('record_attribute_type__record_type','record_value')
        kwargs['frrvs'] = form.ref_to_parent_form.filter(is_public=True, flagged_for_deletion=False).values('record_reference_type__record_type','record_reference')
        logger.info("LOADING FORM AND PASSING TO TEMPLATE")
        return HttpResponse(render(request, 'public_frontend/form.html', kwargs, RequestContext(request)))
    else:
        SECURITY_log_security_issues(request.user, 'views.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return Http404("Project Does Not Exist!")  
#=====================================================================================#
#   WEBPAGE()
#=====================================================================================#       
def webpage(request, **kwargs):
    kwargs['webpage'] = Webpage.objects.get(pk=kwargs['webpage_id'], flagged_for_deletion=False)
    if kwargs['webpage'].project: 
        kwargs['project_override_template'] = "public_frontend/public_base.html"
        kwargs['project'] = kwargs['webpage'].project
        kwargs['menugroups'] = kwargs['project'].menugroup_set.all()
        kwargs['formtypes'] = FormType.objects.filter(project__pk=kwargs['webpage'].project.pk, is_public=True, flagged_for_deletion=False)
        kwargs['webpage_list'] = Webpage.objects.filter(project__pk=kwargs['webpage'].project.pk, is_public=True, flagged_for_deletion=False)
        ftgs = []
        for formtypegroup in kwargs['project'].formtypegroup_set.all():
            if formtypegroup.formtype_set.filter(is_public=True, flagged_for_deletion=False).count() > 0:
                ftgs.append(formtypegroup)
        kwargs['formtypegroups'] = ftgs
        logger.info(ftgs)
    return HttpResponse(render(request, 'public_frontend/webpage.html', kwargs, RequestContext(request)))

     
     
##==========================================================================================================================    
##==========================================================================================================================    
## TARA PUBLIC PAGES   ****************************************************************************************************
##==========================================================================================================================      

#=====================================================================================#
#  INDEX() 
#=====================================================================================#       
def index(request, **kwargs):
    logger.info("TESTING PROJECT TENANCY")
    logger.info(request)
    logger.debug(render(request, 'public_frontend/index.html', kwargs, RequestContext(request)))
    return HttpResponse(render(request, 'public_frontend/index.html', kwargs, RequestContext(request)))    

def dev_index(request, **kwargs):
    logger.info("TESTING PROJECT TENANCY")
    logger.info(request)
    logger.debug(render(request, 'public_frontend/dev_index.html', kwargs, RequestContext(request)))
    
    projects = FormProject.objects.filter(is_public=True)
    blogposts = BlogPost.objects.filter(project=None).order_by('-date_created') 
    recentposts = BlogPost.objects.all().order_by('-date_created')[:5]
    firstpost = blogposts[0]
    blogposts = blogposts[1:10]
    test_post = '16'
    kwargs = {'test_post':test_post,'firstpost':firstpost,'project_list':projects,'blogpost_list':blogposts,'recentposts_list':recentposts}
    #kwargs.update({'firstpost':firstpost})
    #kwargs.update({'project_list':projects})
    #kwargs.update({'blogpost_list':blogposts}) 
    #kwargs.update({'recentposts_list':recentposts})     
    
    return render(request, 'public_frontend/dev_index.html', kwargs)    

    
#=====================================================================================#
#   QUERYENGINE() 
#=====================================================================================# 
      
def queryengine( request, **kwargs):
    kwargs['api_urls'] = get_api_endpoints()
    return HttpResponse(render(request, 'public_frontend/queryengine.html', kwargs, RequestContext(request)))
#=====================================================================================#
#   GEOENGINE() 
#=====================================================================================#       
def geoengine( request, **kwargs):
    return HttpResponse(render(request, 'public_frontend/geoengine.html', kwargs, RequestContext(request)))

#=====================================================================================#
#   BROWSEENGINE() 
#=====================================================================================#       
def browseengine(request, **kwargs):
    return HttpResponse(render(request, 'public_frontend/browseengine.html', kwargs, RequestContext(request)))

        
#=====================================================================================#
#   FEATURES()
#=====================================================================================#       
def features(request, **kwargs):
    return HttpResponse(render(request, 'public_frontend/tara_features.html', kwargs, RequestContext(request)))

        
#=====================================================================================#
#   HISTORY()
#=====================================================================================#       
def history(request, **kwargs):
    return HttpResponse(render(request, 'public_frontend/tara_history.html', kwargs, RequestContext(request)))

        
#=====================================================================================#
#   DOCUMENTATION()
#=====================================================================================#       
def documentation(request, **kwargs):
    return HttpResponse(render(request, 'public_frontend/tara_documentation.html', kwargs, RequestContext(request)))

        
#=====================================================================================#
#   CONTACT()
#=====================================================================================#       
def contact(request, **kwargs):
    return HttpResponse(render(request, 'public_frontend/tara_contact.html', kwargs, RequestContext(request)))

        
#=====================================================================================#
#   PROJECT_LIST()
#=====================================================================================#       
def project_list(request, **kwargs):
    projects = []
    project_list = FormProject.objects.all()
    for project in project_list:
        if project.webpage_set.filter(is_public=True).count() > 0 or project.is_public == True:
            projects.append(project)
    kwargs['project_list'] = projects
    return HttpResponse(render(request, 'public_frontend/tara_projects.html', kwargs, RequestContext(request)))

                
     
     
     
##==========================================================================================================================    
##==========================================================================================================================    
##  PUBLIC API ENDPOINTS ****************************************************************************************************
##==========================================================================================================================     

def get_api_endpoint_names():
    mod = sys.modules[__name__]
    function_list = [func.__name__ for func in mod.__dict__.values() if inspect.isfunction(func) and inspect.getmodule(func) == mod]
    final_functions = []
    for function in function_list: 
        if 'api_v' in function: final_functions.append(function.split('_')[-1] )
    return sorted(final_functions)

def api_v1_main(request, **kwargs):    
    kwargs.update({'endpoint':request.get_full_path()})
    kwargs.update({'status':'200'})
    kwargs.update({'allow':'GET'})
    kwargs.update({'content_type':'application/json'})
    kwargs.update({'endpoints': get_api_endpoint_names()})
    kwargs.update({'current_endpoint': sys._getframe().f_code.co_name.split('_')[-1]})
    kwargs.update({'api_version':sys._getframe().f_code.co_name.split('_')[1]})
    cleanJSON = '{"welcome_message":"This part of the API isn\'t working yet", "help":"A help message similar to the -h console command will be here at some point"}'
    if 'json' in request.GET: return HttpResponse(cleanJSON, content_type="application/json")        
    else: return HttpResponse(render(request, 'api/api_main.html', kwargs, RequestContext(request)))    
    
def api_v1_blogposts(request, **kwargs):
    #Setup API vars
    kwargs.update({'endpoint':request.get_full_path()})
    kwargs.update({'status':'200'})
    kwargs.update({'allow':'GET'})
    kwargs.update({'content_type':'application/json'})
    kwargs.update({'endpoints': get_api_endpoint_names()})
    kwargs.update({'current_endpoint': sys._getframe().f_code.co_name.split('_')[-1]})
    kwargs.update({'api_version':sys._getframe().f_code.co_name.split('_')[1]})
    try:
        post = BlogPost.objects.get(pk=kwargs['blogpost_id'])
        serialized = post.serialize_to_dictionary()
    except:
        posts = BlogPost.objects.all()[:10]
        serialized = []
        if posts:#Force the Query Evaluation before the loop
            for post in posts:
                serialized.append(post.serialize_to_dictionary())
    cleanJSON = json.dumps(serialized, cls=DjangoJSONEncoder)
    kwargs.update({'json':cleanJSON})
    kwargs.update({'api_endpoint':request.get_full_path()})
    if 'json' in request.GET: 
        response = HttpResponse(cleanJSON, content_type="application/json")
        return response        
    else: 
        return HttpResponse(render(request, 'api/api_blogposts.html', kwargs, RequestContext(request)))
    
def api_v1_projects(request, **kwargs):
    #Setup API vars
    kwargs.update({'endpoint':request.get_full_path()})
    kwargs.update({'status':'200'})
    kwargs.update({'allow':'GET'})
    kwargs.update({'content_type':'application/json'})
    kwargs.update({'endpoints': get_api_endpoint_names()})
    kwargs.update({'current_endpoint': sys._getframe().f_code.co_name.split('_')[-1]})
    kwargs.update({'api_version':sys._getframe().f_code.co_name.split('_')[1]})
    try:
        project = FormProject.objects.get(pk=kwargs['project_id'])
        serialized = project.serialize_to_dictionary()
    except:
        projects = FormProject.objects.filter(is_public=True, flagged_for_deletion=False)[:10]
        serialized = []
        if projects:#Force the Query Evaluation before the loop
            for project in projects:
                serialized.append(project.serialize_to_dictionary())
    cleanJSON = json.dumps(serialized, cls=DjangoJSONEncoder)
    kwargs.update({'json':cleanJSON})
    kwargs.update({'api_endpoint':request.get_full_path()})
    if 'json' in request.GET: 
        response = HttpResponse(cleanJSON, content_type="application/json")
        return response        
    else: 
        return HttpResponse(render(request, 'api/api_projects.html', kwargs, RequestContext(request)))
    
def api_v1_formtypes(request, **kwargs):
    #Setup API vars
    kwargs.update({'endpoint':request.get_full_path()})
    kwargs.update({'status':'200'})
    kwargs.update({'allow':'GET'})
    kwargs.update({'content_type':'application/json'})
    kwargs.update({'endpoints': get_api_endpoint_names()})
    kwargs.update({'current_endpoint': sys._getframe().f_code.co_name.split('_')[-1]})
    kwargs.update({'api_version':sys._getframe().f_code.co_name.split('_')[1]})
    try:
        formtype = FormType.objects.filter(is_public=True, flagged_for_deletion=False,pk=kwargs['formtype_id'])[0]
        serialized = formtype.serialize_to_dictionary()
    except:
        formtypes = FormType.objects.filter(is_public=True, flagged_for_deletion=False)[:10]
        serialized = []
        if formtypes:#Force the Query Evaluation before the loop
            for formtype in formtypes:
                serialized.append(formtype.serialize_to_dictionary())
    cleanJSON = json.dumps(serialized, cls=DjangoJSONEncoder)
    kwargs.update({'json':cleanJSON})
    kwargs.update({'api_endpoint':request.get_full_path()})
    if 'json' in request.GET: 
        response = HttpResponse(cleanJSON, content_type="application/json")
        return response        
    else: 
        return HttpResponse(render(request, 'api/api_formtypes.html', kwargs, RequestContext(request)))

def api_v1_forms(request, **kwargs):
    #Setup API vars
    kwargs.update({'endpoint':request.get_full_path()})
    kwargs.update({'status':'200'})
    kwargs.update({'allow':'GET'})
    kwargs.update({'content_type':'application/json'})
    kwargs.update({'endpoints': get_api_endpoint_names()})
    kwargs.update({'current_endpoint': sys._getframe().f_code.co_name.split('_')[-1]})
    kwargs.update({'api_version':sys._getframe().f_code.co_name.split('_')[1]})
    if 'form_id' in kwargs:
        try:
            form = Form.objects.get(pk=kwargs['form_id'], is_public=True, flagged_for_deletion=False)
            serialized = form.serialize_to_dictionary()
        except:
            serialized = {"status":"404", "message":"Resource not found in database"}
            kwargs['status'] = '404'        
    else:
        try:
            forms = Form.objects.all().filter(is_public=True, flagged_for_deletion=False)[:10]
            serialized = []
            if forms:#Force the Query Evaluation before the loop
                for form in forms:
                    serialized.append(form.serialize_to_dictionary())
        except:
            serialized = {"status":"404", "message":"Resource not found in database"}
            kwargs['status'] = '404'    
            
    #Sort the dictionary
    #serialized = sorted(serialized, key=lambda k: k['name'], reverse=True) 
    cleanJSON = json.dumps(serialized, cls=DjangoJSONEncoder)
    kwargs.update({'json':cleanJSON})
    kwargs.update({'api_endpoint':request.get_full_path()})
    
    if 'json' in request.GET: 
        response = HttpResponse(cleanJSON, content_type="application/json")
        return response        
    else: 
        return HttpResponse(render(request, 'api/api_forms.html', kwargs, RequestContext(request)))
    
def api_v1_webpages(request, **kwargs):
    #Setup API vars
    kwargs.update({'endpoint':request.get_full_path()})
    kwargs.update({'status':'200'})
    kwargs.update({'allow':'GET'})
    kwargs.update({'content_type':'application/json'})
    kwargs.update({'endpoints': get_api_endpoint_names()})
    kwargs.update({'current_endpoint': sys._getframe().f_code.co_name.split('_')[-1]})
    kwargs.update({'api_version':sys._getframe().f_code.co_name.split('_')[1]})
    try:
        webpage = Webpage.objects.get(pk=kwargs['webpage_id'], flagged_for_deletion=False)
        serialized = webpage.serialize_to_dictionary()
    except:
        webpages = Webpage.objects.filter(flagged_for_deletion=False)[:10]
        serialized = []
        if webpages:#Force the Query Evaluation before the loop
            for webpage in webpages:
                serialized.append(webpage.serialize_to_dictionary())
    cleanJSON = json.dumps(serialized, cls=DjangoJSONEncoder)
    kwargs.update({'json':cleanJSON})
    kwargs.update({'api_endpoint':request.get_full_path()})
    if 'json' in request.GET: 
        response = HttpResponse(cleanJSON, content_type="application/json")
        return response        
    else: 
        return HttpResponse(render(request, 'api/api_webpages.html', kwargs, RequestContext(request)))
     