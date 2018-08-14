
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
from django.shortcuts import render_to_response
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
from django.conf.urls import url, include
from django.views import generic
from django.http import Http404

from time import sleep
from django.contrib.staticfiles.storage import staticfiles_storage

import json
from django.core.serializers.json import DjangoJSONEncoder

from django.utils.encoding import smart_text

from django.shortcuts import redirect
import random
import time
from django.core import serializers

import uuid

import zipfile
import io
import contextlib

from django.urls import resolve
from django.shortcuts import render
import inspect #Needed for getting method names

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

def SECURITY_log_security_issues(viewname, errormessage, META):
    #This just prints some information to the server log about any errors/attempted hacks that need to be flagged
    FLAG = "!!!! SECURITY FLAG !!!!  ===>  "
    try: FLAG += "User: PUBLIC  - Access Level: PUBLIC  - in View: " + viewname + "  -- UserIP: " +  str(META.get('HTTP_X_FORWARDED_FOR', '') or META.get('REMOTE_ADDR')) + " - with Message: " + errormessage
    except Exception as inst: FLAG += str(inst) + "  SOMETHING WENT WRONG - in View: " + viewname + "  -- UserIP: " +  str(META.get('HTTP_X_FORWARDED_FOR', '') or META.get('REMOTE_ADDR')) +  " - with Message: " + errormessage
    print >>sys.stderr, FLAG


##==========================================================================================================================    
##==========================================================================================================================    
##  TEMPLATE VIEWS   ****************************************************************************************************
##==========================================================================================================================  

#=======================================================#
#   ACCESS LEVEL :  1    EXPORT_FORMTYPE()
#=======================================================#     
def export_formtype(self, request, **kwargs):
    #***************#
    ACCESS_LEVEL = 1
    #***************#  
    
    #----------------------------------------------------------------------------------------------------------------------------
    #   This endpoint takes a FormType pk value and returns a flattened .csv file export of all associated forms childed to this
    #   --FormType in the project, or a JSON dump of the created Python Dictionary
    #
    #   The CSV file has the following columns:
    #                                                                                   
    #   -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -- - - --- ----
    #   |  Form_PK  |   Form_Name   |   FormType_PK |   FormType_Name   |  Att_Name_1 | Att_Name_2  |     Ref_Att_Name_1_PKs     | Ref_Att_Name_1_Labels | Reff Ref_Att_Name_2 | ...... ..... .....
    #   ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- --   -- - --  --
    #   |  000      |   Object A    |       000     |    Object Sheet   |  Att Value  |  Att Value  |  Val1_pk, Val2_pk, Val3_pk | Val1, Val2, Val3      |  .....  ....   .... ... . .. 
    #
    #   This is essentially a list of forms with column headings a direct 1:1 copy of FRATs. The FRRTs are a little more complex. Each FRRT is given in
    #   --2 columns to provide both a comma separated list of referenced form names, and a comma seperated list of their database PK values. The names
    #   --might be enough, but I like to have both for completion sake.
    
    
    ERROR_MESSAGE = ""
    print >> sys.stderr, request
    #Check our user's session and access level  
    if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
        formtype = FormType.objects.get(pk=request.GET['id'])
        if formtype.project.pk == request.user.permissions.project.pk and formtype.flagged_for_deletion == False:

            #Make the AJAX Request Data Model for subsequent AJAX calls
            progressData = AJAXRequestData(uuid=request.POST.get('uuid'), jsonString='{"row_index":"0","row_total":"0","is_complete":"False","row_timer":"0"}')
            progressData.save()                
            keepAliveTimer = time.clock()
        
            csv_string = ""
            all_forms = formtype.form_set.all().filter(flagged_for_deletion=False)
            # Load all of our FRATs and FRRTs
            all_FRATs = formtype.formrecordattributetype_set.all();
            all_FRRTs = formtype.ref_to_parent_formtype.all();
            
            csv_dict = []
          
            formCounter = 0
            total_forms = len(all_forms);
            form_pct_interval = 100.0 / total_forms;
            #Start loading all the forms by row now
            if all_forms:
                for form in all_forms:
                    #-------------------------------------------------------------------------------------------------
                    #   This block handles the AJAX progress calls before every form is processed
                    #vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
                    form_pct_done = formCounter * form_pct_interval
                    form_pct_done = int(form_pct_done * 100) / 100.0
                    #We re-initialize the progressData instance so it refreshes the values changed by the checkProgress() function
                    progressData = AJAXRequestData.objects.get(pk=progressData.pk)
                    progressData.jsonString = '{"percent_done":"'+str(form_pct_done)+'","current_formtype":"'+str(formtype.form_type_name)+'","is_complete":"False", "formtype_total":"1", "current_form":"'+str(form.form_name)+'", "total_forms":"'+str(total_forms)+'"}'
                    progressData.is_complete = False
                    #We want to make sure that our timer is set at 5 second itnervals. The AJAX script sets the keep alive variable to True
                    #   --every 1 second. I've set it to 5 seconds here to account for any delays that might occur over the network.
                    #   --Every 5 seconds, this script resets the keep_alive variable to 'False', if it is already False--that means the user exited
                    #   --the process on their AJAX end so we should stop adding this to the database and delete what we've already done.
                    print >>sys.stderr, str(time.clock()) + "  - " + str(keepAliveTimer) + "    :    " + str(progressData.keep_alive)
                    if time.clock() - keepAliveTimer > 5:
                        print >> sys.stderr, str (time.clock() - keepAliveTimer) + "  : We are at the 5 second interval!  " + str(formCounter) 
                        #restart the keepAlive timer to the current time
                        keepAliveTimer = time.clock()
                        #delete the data if the user's AJAX end is unresponsive
                        if progressData.keep_alive == False:
                            print >> sys.stderr, "We are deleting our progress now--wish us luck!"
                            #TODO Delete all formtypes FRAT/FRRTs  that we just tried making
                            progressData.delete()
                            #break from loop
                            print >>sys.stderr, "Breaking from export function--user/client was unresponsive"
                            ERROR_MESSAGE = "Breaking from export function--user/client was unresponsive"
                            SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
                            return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")   
                        else:
                            progressData.keep_alive = False
                    progressData.save()
                    formCounter += 1
                    
                    # End of AJAX Progress processing for this iteration
                    #-------------------------------------------------------------------------------------------------                    
                    new_row = {'Form Name':form.form_name,'Form PK':str(form.pk),'Form Type Parent':formtype.form_type_name,'Form Type Parent PK':str(formtype.pk),}
                    #now load all the FRAVs
                    for FRAT in all_FRATs:
                        currentFRAV = FRAT.formrecordattributevalue_set.all().filter(form_parent__pk=form.pk)
                        if currentFRAV.exists():
                            currentFRAV = currentFRAV[0]
                            new_row[FRAT.record_type] = currentFRAV.record_value
                        else:
                            new_row[FRAT.record_type] = ""
                    #now load all the FRRVs
                    for FRRT in all_FRRTs:
                        currentFRRV = FRRT.formrecordreferencevalue_set.all().filter(form_parent__pk=form.pk)
                        if currentFRRV.exists():
                            if currentFRRV[0].record_reference.all().exists():
                                allLabels = ""
                                allPKs = ""
                                for ref in currentFRRV[0].record_reference.all():
                                    allPKs += '"' +str(ref.pk) + ","
                                    allLabels += ref.form_name + ","
                                new_row[FRRT.record_type] = allLabels
                                new_row[FRRT.record_type+'__PKs'] = allPKs
                            else:
                                #Add a blank PK list and use the external key for the label list
                                new_row[FRRT.record_type] = currentFRRV[0].external_key_reference
                                new_row[FRRT.record_type+'__PKs'] = ""
                        else:
                            new_row[FRRT.record_type] = ""
                            new_row[FRRT.record_type+'__PKs'] = ""
                    #remove the trailing comma after the last column heading and end the line
                    csv_dict.append(new_row)
            #End our AJAX MEssaging
            progressData = AJAXRequestData.objects.get(pk=progressData.pk)
            progressData.jsonString = '{"percent_done":"100","current_formtype":"None","is_complete":"True", "formtype_total":"1", "current_form":"None", "total_forms":"None"}'
            progressData.is_complete = True;
            progressData.save();                  
            
            if(request.POST['export_format'] == "CSV"):
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="'+formtype.form_type_name+'__'+request.user.username+'.csv"'
                keys = csv_dict[0].keys()
                csv_file = csv.DictWriter(response, fieldnames=keys)
                csv_file.writerow(dict((fn,fn) for fn in keys))
                csv_file.writerows(csv_dict)
                return response
            elif (request.POST['export_format'] == "JSON"):
                jsonResponse = json.dumps(csv_dict)
                response = HttpResponse(jsonResponse, mimetype='application/json')
                response['Content-Disposition'] = 'attachment; filename="'+formtype.form_type_name+'__'+request.user.username+'.json"'
                return response
            else:
                return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")       
            #SUCCESS!!
            return HttpResponse('{"MESSAGE":"SUCCESS!"}',content_type="application/json") 
        else: ERROR_MESSAGE += "Error: You are attempting to access another project's data!"            
    else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
    
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")       

#-------------------------------------------------------------------------------------------------------
# MODEL QUERY ENDPOINTS

#=======================================================#
#  GET_PROJECTS() *RECYCLING
#=======================================================#   
def get_projects(self, request):
    #----------------------------------------------------------------------------------------------------------------------------
    #   This Endpoint returns a list of all projects. This is used mainly by the query engine
    #   --to figure out which rtypes to search by when a record reference type is chosen.
    
    ERROR_MESSAGE = ""
    #We need to return a json list of all formtype RTYPES that match the provided formtype pk
    if request.method == "GET":
        #let's get all the public projects, which may not include our own, so let's redundantly merge it and then call distinct()
        publicProjects = FormProject.objects.filter(is_public=True)
        userProject = FormProject.objects.filter(pk=request.user.permissions.project.pk)
        if publicProjects.exists():
            finalProjects = (publicProjects |userProject).distinct()
        else:
            finalProjects = userProject 
        finalJSON = {}
        project_list = []

        for aProject in finalProjects:
           project_list.append({"name":aProject.name, "pk":aProject.pk})
            
        finalJSON['project_list'] = project_list
        finalJSON = json.dumps(finalJSON)
        return HttpResponse(finalJSON, content_type="application/json" )

        ERROR_MESSAGE += "Error: You have not submitted through GET"
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues('views.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")    

#=======================================================#
#   ACCESS LEVEL :  1      GET_FORMTYPES() *RECYCLING
#=======================================================#   
def get_formtypes(self, request):
    #***************#
    ACCESS_LEVEL = 1
    #***************#            
    
    #----------------------------------------------------------------------------------------------------------------------------
    #   This Endpoint returns a list of all formtypes for a provided project pk. This is used mainly by the query engine
    #   --to figure out which formtypes to add to a dropdown select by when a project is chosen.
    
    
    ERROR_MESSAGE = ""
    
    #Check our user's session and access level
    if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
    
        #We need to return a json list of all formtype RTYPES that match the provided formtype pk
        if request.method == "POST":
            #Let's get all available public formtypes not in recycling--unless the formtypes are from the users current, project.
            #If it is the users current project, then don't use a is_public filter
            print >>sys.stderr, request.POST['project_pk']  + "  :  "
            if str(request.user.permissions.project.pk) == request.POST['project_pk']:
                print >>sys.stderr, "What...?" + str(request.user.permissions.project.pk)
                allFormTypes = FormType.objects.filter(project__pk=request.POST['project_pk'], flagged_for_deletion=False)
            else:
                allFormTypes = FormType.objects.filter(is_public=True, project__pk=request.POST['project_pk'], flagged_for_deletion=False)
                
            if allFormTypes:
                finalJSON = {}
                formtype_list = []

                for aFormType in allFormTypes:
                   formtype_list.append({"name":aFormType.form_type_name, "pk":aFormType.pk})
                    
                finalJSON['formtype_list'] = formtype_list
                finalJSON = json.dumps(finalJSON)
                return HttpResponse(finalJSON, content_type="application/json" )
                
            else: ERROR_MESSAGE += "Error: no form types were found for this project"
        else: ERROR_MESSAGE += "Error: You have not submitted through POST"
        
    else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
    
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")    
   
#=======================================================#
#   ACCESS LEVEL :  1      GET_GEOSPATIAL_FORMTYPES() *RECYCLING
#=======================================================#   
def get_geospatial_formtypes(self, request):
    #***************#
    ACCESS_LEVEL = 1
    #***************#            
    
    #----------------------------------------------------------------------------------------------------------------------------
    #   This Endpoint returns a list of all formtypes for a provided project pk. This is used mainly by the query engine
    #   --to figure out which formtypes to add to a dropdown select by when a project is chosen.
    
    
    ERROR_MESSAGE = ""
    
    #Check our user's session and access level
    if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
    
        #We need to return a json list of all formtype RTYPES that match the provided formtype pk
        if request.method == "POST":
            #Let's get all available public formtypes not in recycling--unless the formtypes are from the users current, project.
            #If it is the users current project, then don't use a is_public filter
            print >>sys.stderr, request.POST['project_pk']  + "  :  "
            if str(request.user.permissions.project.pk) == request.POST['project_pk']:
                print >>sys.stderr, "What...?" + str(request.user.permissions.project.pk)
                allFormTypes = FormType.objects.filter(project__pk=request.POST['project_pk'], flagged_for_deletion=False)
            else:
                allFormTypes = FormType.objects.filter(is_public=True, project__pk=request.POST['project_pk'], flagged_for_deletion=False)
                
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
        else: ERROR_MESSAGE += "Error: You have not submitted through POST"
        
    else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
    
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")    
   
   
#=======================================================#
#   ACCESS LEVEL :  1      GET_FORMTYPE_GEOSPATIAL_LAYERS() *RECYCLING
#=======================================================#   
def get_formtype_geospatial_layers(self, request):
    #***************#
    ACCESS_LEVEL = 1
    #***************#            
    
    #----------------------------------------------------------------------------------------------------------------------------
    #   This Endpoint returns a list of geoJSON  'geometry' layers to add to a openlayers map
    
    
    ERROR_MESSAGE = ""
    
    #Check our user's session and access level
    if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
    

        if request.method == "POST":
            print >>sys.stderr, request.POST['formtype_pk']  + "  :  "
            currentFormType = FormType.objects.get(pk=request.POST['formtype_pk'])
            if request.user.permissions.project.pk == currentFormType.project.pk:
                #geometry needs to be stored as a list of 'features'

                allGeometry = {}
                allGeometry['type'] = "FeatureCollection"
                allGeometry['name'] = currentFormType.form_type_name
                #allGeometry['crs'] = json.loads('{ "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::32638" } }')
                featureList = []
                allGeometry['features'] = featureList
                allForms = currentFormType.form_set.all()
                if allForms:
                    for aForm in allForms:
                        properties = {}
                        #allFRATs = aForm.form_type.formrecordattributetype_set.all();
                        #if allFRATs:
                        #    for FRAT in allFRATs:
                        #        properties[FRAT.record_type]  = FormRecordAttributeValue.objects.get(record_attribute_type=FRAT, form_parent=aForm).record_value
                        feature = {}
                        feature['properties'] = properties
                        feature['type'] = "Feature"
                        feature['geometry'] = json.loads(aForm.form_geojson_string)
                        #print >>sys.stderr, "Loaded Timer"
                        featureList.append(feature)
                    
                allGeometry = json.dumps(allGeometry)
                return HttpResponse(allGeometry,content_type="application/json")    
                
            else: ERROR_MESSAGE += "You do not have permission to access this form type from another project"
        else: ERROR_MESSAGE += "Error: You have not submitted through POST"
        
    else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
    
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")    

   
#=======================================================#
#   ACCESS LEVEL :  1      GET_RTYPES *RECYCLING
#=======================================================#   
def get_rtypes(self, request):
    #***************#
    ACCESS_LEVEL = 1
    #***************#            
    
    #----------------------------------------------------------------------------------------------------------------------------
    #   This Endpoint returns a list of all rtypes for a provided formtype pk. This is used mainly by the query engine
    #   --to figure out which formtypes to add to a dropdown select by when a project is chosen.
    
    
    ERROR_MESSAGE = ""
    
    #Check our user's session and access level
    if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
    
        #We need to return a json list of all formtype RTYPES that match the provided formtype pk
        if request.method == "POST":
            #Grab the formtype
            currentFormType = FormType.objects.get(pk=request.POST['formtype_pk'])
            #If the requested formtype isn't the user's project, and flagged as being inaccessible then stop the request
            if currentFormType.project.pk != request.user.permissions.project.pk and (currentFormType.flagged_for_deletion == True or currentFormType.is_public == False):
                ERROR_MESSAGE += "Error: You are attempting to access records that don't exist. This probably occurred because your client attempted altering the POST data before sending"
            #Otherwise we are in the clear so grab the list and return it
            else:
                finalJSON = {}
                rtypeList = []    
                #Don't filter out the public flags if this formtype is the users project--if it's not then absolutely use the is_public flags
                if currentFormType.project.pk == request.user.permissions.project.pk:          
                    #***RECYCLING BIN***  Make sure that the returned FRAT AND FRRTS are filtered by their deletion flags. Don't want them returned in the query
                    for FRAT in currentFormType.formrecordattributetype_set.all().filter(flagged_for_deletion=False):
                        currentRTYPE = {}
                        currentRTYPE['label'] = FRAT.record_type
                        currentRTYPE['pk'] = FRAT.pk
                        currentRTYPE['rtype'] = 'FRAT'
                        rtypeList.append(currentRTYPE)
                    #***RECYCLING BIN***  Make sure that the returned FRAT AND FRRTS are filtered by their deletion flags. Don't want them returned in the query    
                    for FRRT in currentFormType.ref_to_parent_formtype.all().filter(flagged_for_deletion=False):
                        currentRTYPE = {}
                        currentRTYPE['label'] = FRRT.record_type
                        currentRTYPE['pk'] = FRRT.pk
                        if FRRT.form_type_reference: currentRTYPE['ref_formtype_pk'] = FRRT.form_type_reference.pk
                        else: currentRTYPE['ref_formtype_pk'] = "None"
                        currentRTYPE['rtype'] = 'FRRT'
                        rtypeList.append(currentRTYPE)
                else:
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
                

        else: ERROR_MESSAGE += "Error: You have not submitted through POST"
        
    else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
    
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")    

#=======================================================#
#   ACCESS LEVEL :  1      GET_RTYPE_LIST() *RECYCLING
#=======================================================#   
def get_rtype_list(self, request):
    #***************#
    ACCESS_LEVEL = 1
    #***************#            
    
    #----------------------------------------------------------------------------------------------------------------------------
    #   This Endpoint returns a list of all record types in a formtype template. This is used  mainly by the query engine
    #   --to figure out which rtypes to search by when a record reference type is chosen.
    
    
    ERROR_MESSAGE = ""
    
    #Check our user's session and access level
    if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
    
        #We need to return a json list of all formtype RTYPES that match the provided formtype pk
        if request.method == "POST":
            if 'frrt-pk' in request.POST:
                currentFormType = FormType.objects.get(pk=FormRecordReferenceType.objects.get(pk=request.POST['frrt-pk']).form_type_reference.pk)
            elif 'formtype_pk' in request.POST:
                currentFormType = FormType.objects.get(pk=request.POST['formtype_pk'])
            if currentFormType:
                # $$$-SECURITY-$$$: Make sure we filter by the users project as usual
                #TODO: This will obviously trigger server side errors if the returned query is empty(e.g. the user tries to access a formtype that isn't attached to their project)
                if currentFormType.project.pk == request.user.permissions.project.pk:
                    finalJSON = {}
                    rtypeList = []
                    #***RECYCLING BIN***  Make sure that the returned FRAT AND FRRTS are filtered by their deletion flags. Don't want them returned in the query
                    for FRAT in currentFormType.formrecordattributetype_set.all().filter(flagged_for_deletion=False):
                        currentRTYPE = {}
                        currentRTYPE['label'] = FRAT.record_type
                        currentRTYPE['pk'] = FRAT.pk
                        currentRTYPE['rtype'] = 'FRAT'
                        rtypeList.append(currentRTYPE)
                    #***RECYCLING BIN***  Make sure that the returned FRAT AND FRRTS are filtered by their deletion flags. Don't want them returned in the query    
                    for FRRT in currentFormType.ref_to_parent_formtype.all().filter(flagged_for_deletion=False):
                        currentRTYPE = {}
                        currentRTYPE['label'] = FRRT.record_type
                        currentRTYPE['pk'] = FRRT.pk
                        if FRRT.form_type_reference: currentRTYPE['ref_formtype_pk'] = FRRT.form_type_reference.pk
                        else: currentRTYPE['ref_formtype_pk'] = "None"
                        currentRTYPE['rtype'] = 'FRRT'
                        rtypeList.append(currentRTYPE)
                        
                    finalJSON['rtype_list'] = rtypeList
                    finalJSON = json.dumps(finalJSON)
                    return HttpResponse(finalJSON, content_type="application/json" )
                ERROR_MESSAGE += "Error: You are trying to access a FRRT that doesn't belong to this project!"
            ERROR_MESSAGE += "Error: no FormRecordReferenceType in POST"
        ERROR_MESSAGE += "Error: You have not submitted through POST"
        
    else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
    
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")    

#=======================================================#
#   ACCESS LEVEL :  1      GET_DEEP_RTYPES *RECYCLING
#=======================================================#   
def get_deep_rtypes(self, request):
    #***************#
    ACCESS_LEVEL = 1
    #***************#            
    
    #----------------------------------------------------------------------------------------------------------------------------
    #   This Endpoint returns a list of all rtypes AND their DEEP related rtypes for a provided formtype pk. This is used mainly by the query engine
    #   --to figure out which formtypes to add to a dropdown select by when a project is chosen.
    
    
    ERROR_MESSAGE = ""
    
    #Check our user's session and access level
    if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
    
        #We need to return a json list of all formtype RTYPES that match the provided formtype pk
        if request.method == "POST":
            #Grab the formtype
            currentFormType = FormType.objects.get(pk=request.POST['formtype_pk'])
            #If the requested formtype isn't the user's project, and flagged as being inaccessible then stop the request
            if currentFormType.project.pk != request.user.permissions.project.pk and (currentFormType.flagged_for_deletion == True or currentFormType.is_public == False):
                ERROR_MESSAGE += "Error: You are attempting to access records that don't exist. This probably occurred because your client attempted altering the POST data before sending"
            #Otherwise we are in the clear so grab the list and return it
            else:
                finalJSON = {}
                rtypeList = []    
                #Don't filter out the public flags if this formtype is the users project--if it's not then absolutely use the is_public flags
                if currentFormType.project.pk == request.user.permissions.project.pk:          
                    #***RECYCLING BIN***  Make sure that the returned FRAT AND FRRTS are filtered by their deletion flags. Don't want them returned in the query
                    for FRAT in currentFormType.formrecordattributetype_set.all().filter(flagged_for_deletion=False):
                        currentRTYPE = {}
                        currentRTYPE['label'] = FRAT.record_type
                        currentRTYPE['pk'] = FRAT.pk
                        currentRTYPE['rtype'] = 'FRAT'
                        rtypeList.append(currentRTYPE)
                    #***RECYCLING BIN***  Make sure that the returned FRAT AND FRRTS are filtered by their deletion flags. Don't want them returned in the query    
                    for FRRT in currentFormType.ref_to_parent_formtype.all().filter(flagged_for_deletion=False):
                        currentRTYPE = {}
                        currentRTYPE['label'] = FRRT.record_type
                        currentRTYPE['pk'] = FRRT.pk
                        if FRRT.form_type_reference: currentRTYPE['ref_formtype_pk'] = FRRT.form_type_reference.pk
                        else: currentRTYPE['ref_formtype_pk'] = "None"
                        currentRTYPE['rtype'] = 'FRRT'
                        rtypeList.append(currentRTYPE)
                        #Now look for all the RTYPES of this particular FRRT and add the DEEP RTYPES to our list
                        for deepFRAT in FRRT.form_type_reference.formrecordattributetype_set.all().filter(flagged_for_deletion=False):
                            currentDeepRTYPE = {}
                            currentDeepRTYPE['label'] = FRRT.record_type + " :: " + deepFRAT.record_type
                            currentDeepRTYPE['pk'] = deepFRAT.pk
                            currentDeepRTYPE['rtype'] = 'DEEP-FRAT'
                            rtypeList.append(currentDeepRTYPE)
                        for deepFRRT in FRRT.form_type_reference.ref_to_parent_formtype.all().filter(flagged_for_deletion=False):
                            currentDeepRTYPE = {}
                            currentDeepRTYPE['label'] = FRRT.record_type + " :: " + deepFRRT.record_type
                            currentDeepRTYPE['pk'] = deepFRRT.pk
                            currentDeepRTYPE['rtype'] = 'DEEP-FRRT'  
                            if FRRT.form_type_reference: currentDeepRTYPE['ref_formtype_pk'] = deepFRRT.form_type_reference.pk
                            else: currentDeepRTYPE['ref_formtype_pk'] = "None"
                            rtypeList.append(currentDeepRTYPE)
                else:
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
                

        else: ERROR_MESSAGE += "Error: You have not submitted through POST"
        
    else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
    
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")    

#=======================================================#
#   ACCESS LEVEL :  1       GET_FORM_RTYPES()  *Recycling           
#=======================================================#    
def get_form_rtypes(self, request):
    #***************#
    ACCESS_LEVEL = 1
    #***************#
    #------------------------------------------------------------------------------------------------------------------------------------
    #:::This endpoint returns a JSON list of all rtype values(their values and pk's) associated with a given form. We are only accessing data
    #   --so the access level is 1. Any user should be able to use this endpoint.
    #
    #   Returned JSON Example:  {"rtype_list":[
    #                                               {"rtype_pk":    "1",
    #                                                "rtype_label": "Object Shape",
    #                                                "rtype":       "FRAT",
    #                                                "rval":    {"Spherical":"<pk#>"}, <-- This will similarly be a json object with 1 key/val pair
    #                                                
    #                                               },
    #                                               {"rtype_pk":    "6",
    #                                                "rtype_label": "Associated Unit",
    #                                                "rtype":       "FRRT",
    #                                                "rval":    {"Unit 1":"<pk#>", "Unit 2":"<pk#>"},    <-- if this is a frrt, then this will be another json object of key/val pairs 
    #                                                "ext_key": "1,2"  <-- This is just the raw ext key string
    #                                                "thumbnail":"www.geioh.coms/hoidjjds.jpg"
    #                                               },
    #                                         ]}
    #
    # EXPECTED POST VARIABLES:
    #   -- 'form_pk'
    #------------------------------------------------------------------------------------------------------------------------------------
    
    ERROR_MESSAGE = ""
    
    #Check our user's session and access level
    if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
        #$$$ SECURITY $$$ Make sure we only take POST requests
        if request.method == 'POST':         
            currentForm = Form.objects.get(pk=request.POST['form_pk'])
            #$$$ SECURITY $$$ Make sure form is in the same project space as the user or refuse the request for the list
            if currentForm.project.pk == request.user.permissions.project.pk:
                jsonData = {}
                rtype_list = []
                jsonData['rtype_list'] = rtype_list
                
                #Alright--let's load our RTYPEs from the current Form requested
                #*** RECYCLING BIN *** Let's filter them out by their recycling flags as well
                frav_list = currentForm.formrecordattributevalue_set.all().filter(flagged_for_deletion=False)
                frrv_list = currentForm.ref_to_parent_form.all().filter(flagged_for_deletion=False)
                
                #If Statement forces evaluation of the query set before the loop
                if frav_list:                    
                    #Let's load all the FRATs and FRAVs first
                    for FRAV in frav_list:
                        currentRTYPE = {}
                        currentRVAL = {}
                        currentRTYPE['rtype_pk'] = FRAV.record_attribute_type.pk
                        currentRTYPE['rtype_label'] = FRAV.record_attribute_type.record_type
                        currentRTYPE['rtype'] = "FRAT"
                        currentRVAL[FRAV.pk] = FRAV.record_value
                        currentRTYPE['rval'] = currentRVAL
                        rtype_list.append(currentRTYPE)
                        
                #If Statement forces evaluation of the query set before the loop
                if frrv_list:
                    print >>sys.stderr, frrv_list
                    for FRRV in frrv_list:
                        currentRTYPE = {}
                        rvalList = []
                        print >>sys.stderr, FRRV.pk
                        currentRTYPE['rtype_pk'] = FRRV.record_reference_type.pk
                        currentRTYPE['rtype_label'] = FRRV.record_reference_type.record_type
                        currentRTYPE['rtype'] = "FRRT"
                        #sometimes if not initialized, there won't be a FRRT reference--it will be a "NoneType" or "Null"
                        #--if that's the case, there will be no PK value, so we will set the ref_formtype to "None" in that case
                        if FRRV.record_reference_type.form_type_reference != None: currentRTYPE['ref_formtype'] = FRRV.record_reference_type.form_type_reference.pk
                        else: currentRTYPE['ref_formtype'] = "None"
                        currentRTYPE['ext_key'] = FRRV.external_key_reference
                        currentRTYPE['rval_pk'] = FRRV.pk
                        for FRRV_REF in FRRV.record_reference.all():
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
                    frrt_list = currentForm.form_type.ref_to_parent_formtype.all()
                    print >>sys.stderr, frrt_list
                    
                    if frrt_list:
                        for FRRT in frrt_list:
                            print >>sys.stderr, FRRT.form_type_reference
                            currentRTYPE = {}
                            currentRTYPE['rtype_pk'] = FRRT.pk
                            currentRTYPE['rtype_label'] = FRRT.record_type
                            currentRTYPE['rtype'] = "FRRT"
                            currentRTYPE['ref_formtype'] = FRRT.form_type_reference.pk
                            currentRTYPE['ext_key'] = ""
                            currentRTYPE['rval_pk'] = ""
                            currentRTYPE['rval'] = ""
                            rtype_list.append(currentRTYPE)   
                            
                #convert python dict to a json string and send it back as a response
                jsonData = json.dumps(jsonData);
                return HttpResponse(jsonData, content_type="application/json")    
                
            ERROR_MESSAGE += "Error: You do not have permission to accesss this project."
        ERROR_MESSAGE += "Error: You have not submitted through POST"
    else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")        


#=======================================================#
#   ACCESS LEVEL :  1       GET_FORMTYPE_FORM_LIST()   *Recycling            
#=======================================================#    
def get_formtype_form_list(self, request):
    #***************#
    ACCESS_LEVEL = 1
    #***************#
    #------------------------------------------------------------------------------------------------------------------------------------
    #:::This endpoint returns a JSON list of all form names and pk values attached to a specific formtype. It's used mainly to
    #   --to help drop-down menu widgets function, but may be used by other features as well.
    #
    #------------------------------------------------------------------------------------------------------------------------------------
    
    ERROR_MESSAGE = ""
    
    #Check our user's session and access level
    if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
        #$$$ SECURITY $$$ Make sure we only take POST requests
        if request.method == 'POST':   
            print >>sys.stderr, request.POST
            currentFormType = FormType.objects.get(pk=request.POST['formtype_pk'])                       
            #$$$ SECURITY $$$ Make sure form is in the same project space as the user or refuse the request for the list
            if currentFormType.project.pk == request.user.permissions.project.pk:
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
                jsonData = json.dumps(jsonData);
                return HttpResponse(jsonData, content_type="application/json")    
                
            ERROR_MESSAGE += "Error: You do not have permission to accesss this project."
        ERROR_MESSAGE += "Error: You have not submitted through POST"
    else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")        


#=======================================================#
#   ACCESS LEVEL :  5      GET_USER_LIST()
#=======================================================#       
def get_user_list(self, request):        
    #***************#
    ACCESS_LEVEL = 5
    #***************#        
    #------------------------------------------------------------------------------------------------------------------------------------
    #   :::This function just returns a list of users with their information for the project's userform
    #   --Obviously it should only give access to those with the admin level permissions. This will not return a pass word, nor allow edits
    #   --But for privacy reasons, let's keep it limited to level 5 access.
    #   --The main project control panel will show limited user information to those without access, so let's keep it that way
    #------------------------------------------------------------------------------------------------------------------------------------  
    
    ERROR_MESSAGE = ""        
    
    #Check our user's session and access level
    if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
        #Make sure we only take POST requests
        if request.method == 'POST':
            returnedJSON = {}
            userList = []
            returnedJSON['userlist'] = userList
            # $$$-SECURITY-$$$: Make sure we filter by the users project as usual
            projectUsers = User.objects.all().filter(permissions__project__pk=request.user.permissions.project.pk)
            count = len(projectUsers)
            for aUser in projectUsers:
                currentUser = {}
                currentUser['user_id'] = aUser.pk
                currentUser['username'] = aUser.username
                currentUser['access_level'] = aUser.permissions.access_level
                currentUser['name'] = aUser.first_name + " " + aUser.last_name
                currentUser['title'] = aUser.permissions.job_title
                currentUser['email'] = aUser.email
                userList.append(currentUser)
            returnedJSON = json.dumps(returnedJSON);
            return HttpResponse(returnedJSON,content_type="application/json") 
        ERROR_MESSAGE += "Error: You have not submitted through POST"
    else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")        
    
 
#=======================================================#
#   ACCESS LEVEL :  1      GET_ALL_UNIQUE_FRAT_RVALS *RECYCLING
#=======================================================#   
def get_all_unique_frat_rvals(self, request):
    #***************#
    ACCESS_LEVEL = 1
    #***************#            
    
    #----------------------------------------------------------------------------------------------------------------------------
    #   This Endpoint returns a list of all unique values for a given FRAT's RVALS
    
    
    ERROR_MESSAGE = ""
    
    #Check our user's session and access level
    if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
    
        #We need to return a json list of all RVALS that match the provided RTYPE
        if request.method == "POST":
            #Figure out if a FRRT or FRAT was submitted

            rtype = FormRecordAttributeType.objects.get(pk=request.POST['rtype_pk'])    

            #If the requested formtype isn't the user's project, and flagged as being inaccessible then stop the request
            if rtype.project.pk != request.user.permissions.project.pk and (rtype.flagged_for_deletion == True or rtype.is_public == False):
                ERROR_MESSAGE += "Error: You are attempting to access records that don't exist. This probably occurred because your client attempted altering the POST data before sending"
            #Otherwise we are in the clear so grab the list and return it
            else:
                finalJSON = {}
                rvalList = []    
                
               
                #sort our rtype list by the label
                rvalList = sorted(rtypeList, key=lambda k: k['label']) 
                
                #Return the JSON response
                finalJSON['rval_list'] = rvalList
                finalJSON = json.dumps(finalJSON)
                return HttpResponse(finalJSON, content_type="application/json" )
                

        else: ERROR_MESSAGE += "Error: You have not submitted through POST"
        
    else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
    
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")    

 
#=======================================================#
#   ACCESS LEVEL :  1      CHECK_PROGRESS()
#=======================================================#   
def check_progress(self, request):
    #***************#
    ACCESS_LEVEL = 1
    #***************#   

    #----------------------------------------------------------------------------------------------------------------------------
    #   This Endpoint just checks the progress of the submitted UUID Progress Object
    #   --It's used by longer functions that require time on the server to process to keep the usser updated on the progress of their
    #   --formtype generator submitted. Security isn't particularly important here, because the information provided isn't particularly sensitive,
    #   --and this model/object doesn't have a foreign key to a project. It can only be accessed by a UUID(unique ID) provided by the user
    #   --and the chance of someone figuring out a 32character long random string in the small amount of time it takes to process the server
    #   --function is considerably low--and even if they DID manage to hack it, the information they recieve is essentially rubbish and offers
    #   --no sensitive data except perhaps the name or label of some rtypes--and associated counts for the query. I suppose that could be
    #   --potentially sensitive--but the security  risk is so low that I won't spend time worrying about it.
    #
    #   TODO: an option to secure this, is to attach a foreign key to the ProgressObject to the project in question. This Endpoint could then 
    #       --cross check the session user's project and make sure they're only accessing progress objects that are part of their project. Once
    #       --again--not a priority right now but I ahve it in a TODO tag for future edits when time is more available
    

    ERROR_MESSAGE = ""
    
    #Check our user's session and access level  
    if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):   
        #print >> sys.stderr, request.POST
        #Returns a JSON string to an AJAX request given a provided UUID   
        try:
            currentProcessObject = AJAXRequestData.objects.filter(uuid=request.POST['uuid'])[0]
            #print >>sys.stderr, "Keeping Alive?" 
            currentProcessObject.keep_alive = True
            currentProcessObject.save()
            #If finished, then delete the process object
            if currentProcessObject.is_finished:
                print >> sys.stderr, "DELETING OBJECT I GUESS?"
                currentProcessObject.delete()
            currentJson = currentProcessObject.jsonString
            #print >>sys.stderr, currentProcessObject.jsonString
            #return the json response      
            return HttpResponse(currentJson, content_type="application/json")  
        except Exception as e:
            print >>sys.stderr, "Whoops---hmmm....."
            print >>sys.stderr, e
            ERROR_MESSAGE += "Something happened during the check to the Progress Object--it might not have been created yet, and we are checking too quickly..." + str(e)
                 

    else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
    
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"False", "row_total":"0", "row_timer":"0"}',content_type="application/json")     

   
#=======================================================#
#   ACCESS LEVEL :  1      CHECK_PROGRESS_QUERY()
#=======================================================#          
def check_progress_query(self, request):
    #***************#
    ACCESS_LEVEL = 1
    #***************#  

    
    #----------------------------------------------------------------------------------------------------------------------------
    #   This Endpoint just checks the progress of the submitted UUID Progress Object
    #   --It's used by longer functions that require time on the server to process to keep the usser updated on the progress of their
    #   --query submitted. Security isn't particularly important here, because the information provided isn't particularly sensitive,
    #   --and this model/object doesn't have a foreign key to a project. It can only be accessed by a UUID(unique ID) provided by the user
    #   --and the chance of someone figuring out a 32character long random string in the small amount of time it takes to process the server
    #   --function is considerably low--and even if they DID manage to hack it, the information they recieve is essentially rubbish and offers
    #   --no sensitive data except perhaps the name or label of some rtypes--and associated counts for the query. I suppose that could be
    #   --potentially sensitive--but the security  risk is so low that I won't spend time worrying about it.
    #   TODO: an option to secure this, is to attach a foreign key to the ProgressObject to the project in question. This Endpoint could then 
    #       --cross check the session user's project and make sure they're only accessing progress objects that are part of their project. Once
    #       --again--not a priority right now but I ahve it in a TODO tag for future edits when time is more available
    
    ERROR_MESSAGE = ""
    
    #Check our user's session and access level  
    if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):   
    
        #Returns a JSON string to an AJAX request given a provided UUID   
        try:
            currentProcessObject = AJAXRequestData.objects.filter(uuid=request.GET['uuid'])[0]
            currentProcessObject.keep_alive = True
            currentProcessObject.save()
            #If finished, then delete the process object
            if currentProcessObject.is_finished:
                print >> sys.stderr, "DELETING OBJECT I GUESS?"
                currentProcessObject.delete()
            currentJson = currentProcessObject.jsonString
            #return the json response      
            return HttpResponse(currentJson, content_type="application/json")  
        except Exception as e:
            print >>sys.stderr, "Whoops---hmmm....."
            print >>sys.stderr, e
            ERROR_MESSAGE += "Something happened during the check to the Progress Object--it might not have been created yet, and we are checking too quickly..."
            return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"False", "row_total":"0", "row_timer":"0"}',content_type="application/json")                  

    else: ERROR_MESSAGE += "Error: You do not have permission to access checking a query UUID progress object"
    
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")              
                   

#=======================================================#
#   ACCESS LEVEL :  1      GET_FORM_SEARCH_LIST() *RECYCLING
#=======================================================#        
def get_form_search_list(self, request):
    #***************#
    ACCESS_LEVEL = 1
    #***************#            
    #----------------------------------------------------------------------------------------------------------------------------
    #   This Endpoint does nothing but return a small list of forms that match the provided query string
    #   --It acts as a simple Google style search bar that autocompletes the user's typing. This is handy
    #   --when a project may have upwards of 5000 forms and scrolling through/loading a list of 5000 forms is a bit slow and unwieldy
    #
    # Speed:  This function, on a low-end server, can produce an answer in less than a second

    ERROR_MESSAGE = ""
    
    #Check our user's session and access level
    if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):

        if request.method == 'POST':
            if 'query' in request.POST:
                #initialize our variables we'll need
                projectPK = request.POST['projectID']
                formtypePK = request.POST['formtypeID']
                searchString = request.POST['query']
                jsonResponse = {}
                form_list = []
                jsonResponse['form_list'] = form_list
                
                #Only search if the searchString isn't empty
                if len(searchString) != 0:
                    #Initialize our query to contain all forms of this formtype and project
                    queriedForms = Form.objects.all().filter(form_type__pk=formtypePK)
                    # $$$-SECURITY-$$$: Make sure we filter by the users project as usual
                    queriedForms.filter(project__pk=request.user.permissions.project.pk)
                    #***RECYCLING BIN***  Make sure that we filter out any forms flagged for deletion
                    queriedForms.filter(flagged_for_deletion=False)
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
                        currentForm['url'] = reverse('maqlu_admin:edit_form',kwargs={'project_pk': request.user.permissions.project.pk, 'form_type_pk': form.form_type.pk, 'form_pk':form.pk})
                        form_list.append(currentForm)
                    #return the finished JSON
                    jsonResponse = json.dumps(jsonResponse)
                    return HttpResponse(jsonResponse, content_type="application/json")
        ERROR_MESSAGE += "Error: You have not submitted through POST"
    else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")       

      
#=======================================================#
#   ACCESS LEVEL :  1      GET_PREVIOUS_NEXT_FORMS() *RECYCLING
#=======================================================#   
def get_previous_next_forms(self, request):
    #***************#
    ACCESS_LEVEL = 1
    #***************#        
    #This API EndPoint takes a formtype PK and a form PK and returns the previous, current, and next forms in a sorted list
    #--This gives back and forward functionality when navigating forms.
    #--It first filters out only the forms related to the formtype, and then sorts them by the indexed value
    #--'sort_index' -- sort_index is a Form attribute that is a unique indexed value "<form_name>---<form_pk>"
    #--We then submit the parsed out name and pk numbers for the previous and next forms for the form requested
    #--This also forces a users project as a filter--jsut in case they manage to find a way to pass a form_type that doesn't belong to their project
    #----------------------------------------------------------------------------------------------------------------------------
    # Speed:  This function, on a low-end server, can produce an answer in ~1.5 secs for a sort of ~100,000 rows
    #            --Anything less than that easily hits under a second--which is nice and fast
    #            --I assume on a deployment server with better cpus/RAM this will be even faster

    ERROR_MESSAGE = ""
    
    #Check our user's session and access level
    if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
        #Make sure we only take POST requests        
        if request.method == 'POST':
            #POST values submitted are :  formtype_pk   &  form_pk & project_pk
            #Check if they exist, and only continue if they do
            if 'formtype_pk' in request.POST and 'form_pk' in request.POST and 'project_pk' in request.POST:
                
                thisQuery = Form.objects.filter(form_type__pk=request.POST['formtype_pk'])
                # $$$-SECURITY-$$$: Make sure we filter by the users project as usual
                thisQuery.filter( project__pk=request.user.permissions.project.pk)
                #***RECYCLING BIN***  Make sure that the returned Forms aren't flagged for deletion
                thisQuery.filter(flagged_for_deletion=False)
                #Sort the query now
                thisQuery = thisQuery.order_by('sort_index')

                allVals = thisQuery.values_list('sort_index', flat=True)

                formPKToLookFor = request.POST['form_pk']

                for index, value in enumerate(allVals):
                    #Our delimiter is "---" for 'sort_index'
                    label, pkVal = value.split('---')
                    #Only activate if we find the matching form PK in the list
                    if formPKToLookFor == pkVal:
                        #Once we find our match, we simply get the values for the previous and next forms in our list by adding or subtracting from the index
                        #--Now, what if we are at the first or last form in the list? This will obviously trip an Index Error in Python so let's fix that.
                        #--We'll add functionality to cycle to the last index if at the beginning, or the first index if at the end
                        lastIndex = len(allVals)-1
                        #First test for our previousForm values
                        if (index-1) < 0: previousForm = allVals[lastIndex].split('---')
                        else:             previousForm = allVals[index-1].split('---')
                        #Then test for our NextForm values
                        if (index+1) > lastIndex: nextForm = allVals[0].split('---')
                        else:                     nextForm = allVals[index+1].split('---')
                        
                        #Now create the json string to submit
                        jsonResponse = '{"previous_label":"'+previousForm[0]+'","previous_pk":"'+previousForm[1]+'","next_label":"'+nextForm[0]+'","next_pk":"'+nextForm[1]+'","current_label":"'+label+'","current_pk":"'+pkVal+'","formtype_pk":"'+request.POST['formtype_pk']+'","project_pk":"'+request.POST['project_pk']+'"}'
                return HttpResponse(jsonResponse, content_type="application/json")
            
        #return an indicator to trigger empty "#" links if there is missing data in the POST data
        return HttpResponse('{"ERROR":"There were missing POST values in this request--either javascript is deactivated, or maybe someone is trying to do a little client-side hacking Hmm?"}',content_type="application/json")
    else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")      


#=======================================================#
#   ACCESS LEVEL :  1       NAVIGATE_MASTER_QUERY_PAGINATION() *RECYCLING
#=======================================================#   
def navigate_master_query_pagination(self, request):
    #***************#
    ACCESS_LEVEL = 1
    #***************#
    
    #------------------------------------------------------------------------------------------------------------------------------------ 
    #  This is the real magic of the database in terms of non-geospatial data. This Query engine takes complicated input from json POST data 

    ERROR_MESSAGE = ""
    
    #Check our user's session and access level
    if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
    
        if request.method == 'POST':
            print >>sys.stderr, "do something"
            #We need to make sure we have permission to deal with the formtype--e.g. it's part of the user's current project
            formtype = FormType.objects.get(pk=request.POST['formtype_id'])
            
            #If the project IDs match, then we're good to go! Also if it's not the project, but the formtype is set to PUBLIC then we are also good to go
            if formtype.project.pk == request.user.permissions.project.pk or (formtype.project.pk != request.user.permissions.project.pk and formtype.is_public == True):
            
                #First let's setup our header field of ordered labels 
                print >>sys.stderr,  "Timer Start"                
                form_att_type_list = []
                #***RECYCLING BIN*** Make sure our RTYPES are filtered by their deletion flags
                for attType in formtype.formrecordattributetype_set.all().filter(flagged_for_deletion=False).order_by('order_number')[:5]:
                    form_att_type_list.append((attType.order_number,'frat',attType.pk,attType.record_type)) 
         
                #***RECYCLING BIN*** Make sure our RTYPES are filtered by their deletion flags
                for refType in formtype.ref_to_parent_formtype.all().filter(flagged_for_deletion=False).order_by('order_number')[:5]:
                    form_att_type_list.append((refType.order_number,'frrt',refType.pk,refType.record_type)) 
                #sort the new combined reference ad attribute type list combined
                form_att_type_list = sorted(form_att_type_list, key=lambda att: att[0])
                #we only want the first 5 types
                form_att_type_list = form_att_type_list[0:5]

                formList = []                
               
                
                #Setup a list to hold the attribute types from the query. We want to show the record types that are part of the search terms,
                #   --rather than the default types that are in order. If there are less than 5 query record types, use the ordered record type list
                #   --until 5 are met.
                queryRTYPElist = []
                uniqueRTYPES = []
                rtypeCounter = 1


                #We need to check the # of rtypes in our header list now--if it's less than 5, then let's add from the ordered list
                #We also need to make sure we aren't adding duplicates of the RTYPES, e.g. if we're looking for a match under "Object Number" and Object Number is already
                #--in our sorted order-num list--let's not re-add it.
                for attType in form_att_type_list:
                    print >>sys.stderr, "AttTypeList:  " + str(attType)
                    matchfound = False;
                    for queryAttType in queryRTYPElist:
                        if attType[2] == queryAttType[2]:
                            matchfound = True
                    if matchfound == False and len(queryRTYPElist) < 5:    
                        #let's arbitrarily add '100' to the order number so that our queries are definitely in front of these
                        queryRTYPElist.append((attType[0] + 100,attType[1],attType[2],attType[3]))
                        
                for q in queryRTYPElist:
                    print >>sys.stderr, "QTypeList:  " + str(q)


                print >>sys.stderr, request.POST
                #serializeTest = serializers.serialize("json", masterQuery)         
                queryCounter = 0
                logging.info("TEST A")
                logging.info("TEST A END")
                print >> sys.stderr, request.POST['form_list']
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
                
                print >>sys.stderr, startIndex;
                print >>sys.stderr, endIndex;

                masterQuery = masterQuery[startIndex:endIndex]
                print >>sys.stderr, "TIMER RR"+ " : " + str(time.clock())
                #count the query so we only make one database hit before looping(otherwise each loop would be another hit)

                for form_pk in masterQuery:
                    aForm = Form.objects.get(pk=form_pk)
                    print >>sys.stderr, "TIMER S"+ " : " + str(time.clock())
                    rowList = []
                    #Let's loop through each item in the queryRTYPE list and match up the frav's in each queried form so the headers match the form attribute values
                    for rtype in queryRTYPElist:
                        if rtype[1] == 'frat':
                            #print >>sys.stderr, str(rtype[2]) + '  ' + str(aForm.formrecordattributevalue_set.all().filter(record_attribute_type__pk=rtype[2]).count())
                            print >>sys.stderr, "TIMER X"+ " : " + str(time.clock())
                            formRVAL = aForm.formrecordattributevalue_set.all().filter(record_attribute_type__pk=rtype[2])
                            #We need to check for NULL FRAV's here. When a user manually creates new forms, they don't always have FRAVS created for them if they leave it blank
                            if formRVAL.exists():
                                rowList.append((rtype[0],'frav',formRVAL[0].record_value, formRVAL[0].pk))
                            else:
                                print >>sys.stderr, "Whoops--something happened. There are no RVALS for 'frats' using: " + str(rtype[2])
                            print >>sys.stderr, "TIMER Y"+ " : " + str(time.clock())
                        else:
                            #for frrt in aForm.ref_to_parent_form.all():
                                #print >>sys.stderr, "" + str(frrt.pk)
                            formRVAL = aForm.ref_to_parent_form.all().filter(record_reference_type__pk=rtype[2])
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

                    print >>sys.stderr, "TIMER Z"+ " : " + str(time.clock())
                    #sort the new combined reference ad attribute type list combined
                    rowList = sorted(rowList, key=lambda att: att[0])
                    # print >> sys.stderr, str(rowList)
                    #Now let's handle the thumbnail bit of business for the query
                    #--If the current form IS a media type already, then use itself to grab the thumbnail URI
                    if aForm.form_type.type == 1:
                        thumbnailURI = aForm.get_thumbnail_type()
                    else:
                        #let's find the first media type in the order but offer a default to "NO PREVIEW" if not found
                        thumbnailURI = staticfiles_storage.url("/static/site-images/no-thumb-missing.png")
                        for record in rowList:            
                            #if it's a reference
                            if record[1] == 'frrv' or record[1] == 'frrv-ext':
                                currentRTYPE = FormRecordReferenceValue.objects.get(pk=int(record[3]))
                                #if it's not a NoneType reference:
                                if currentRTYPE.record_reference_type.form_type_reference != None:
                                    #If its a reference to a media type
                                    if currentRTYPE.record_reference_type.form_type_reference.type == 1:
                                        print >> sys.stderr, "WE GOT A MATCH"
                                        #Because a form record reference value is a ManyToMany relationship, we just grab the first one in the list
                                        #TODO this may need to be edited later--because you can't order the selections. I may add another ForeignKey called
                                        #"Thumbnail Reference" which links to a single relation to a form of a media type--this would also
                                        #probably solve the complexity of looping through to grab it as it stands right now
                                        #****WE also have to check for NULL references
                                        if currentRTYPE.record_reference.all().count() > 0:
                                            thumbnailURI = currentRTYPE.record_reference.all()[0].get_thumbnail_type()
                                        break
                                
                    #we only want the first 5 values from the final ordered list of attributes
                    rowList = rowList[0:5]


                    formList.append([thumbnailURI,str(aForm.pk), aForm, rowList])   
                    print >>sys.stderr, "TIMER ZZ"+ " : " + str(time.clock())
                    
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

                print >>sys.stderr,  "Timer End"     
                return HttpResponse(finishedJSONquery, content_type="application/json")


                
            ERROR_MESSAGE += "Error: Trying to access missing or forbidden data"
        ERROR_MESSAGE += "Error: You have not submitted through POST"
    else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")        
    
           
#=======================================================#
#   ACCESS LEVEL :  1       NAVIGATE_QUERY_PAGINATION() *RECYCLING
#=======================================================#   
def navigate_query_pagination(self, request):
    #***************#
    ACCESS_LEVEL = 1
    #***************#
    
    #------------------------------------------------------------------------------------------------------------------------------------ 
    #  This is the real magic of the database in terms of non-geospatial data. This Query engine takes complicated input from json POST data 

    ERROR_MESSAGE = ""
    
    #Check our user's session and access level
    if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
    
        if request.method == 'POST':

            #We need to make sure we have permission to deal with the formtype--e.g. it's part of the user's current project
            formtype = FormType.objects.get(pk=request.POST['formtype_id'])
            
            #If the project IDs match, then we're good to go! Also if it's not the project, but the formtype is set to PUBLIC then we are also good to go
            if formtype.project.pk == request.user.permissions.project.pk or (formtype.project.pk != request.user.permissions.project.pk and formtype.is_public == True):
            
                #Make the AJAX Request Data Model for subsequent AJAX calls
                progressData = AJAXRequestData(uuid=request.POST.get('uuid'), jsonString='{"message":"Loading Json","current_query":"","current_term":"","percent_done":"0","is_complete":"False"}')
                progressData.save()

                
                #First let's setup our header field of ordered labels 
                print >>sys.stderr,  "Timer Start"                
                form_att_type_list = []
                #***RECYCLING BIN*** Make sure our RTYPES are filtered by their deletion flags
                for attType in formtype.formrecordattributetype_set.all().filter(flagged_for_deletion=False).order_by('order_number')[:5]:
                    form_att_type_list.append((attType.order_number,'frat',attType.pk,attType.record_type)) 
         
                #***RECYCLING BIN*** Make sure our RTYPES are filtered by their deletion flags
                for refType in formtype.ref_to_parent_formtype.all().filter(flagged_for_deletion=False).order_by('order_number')[:5]:
                    form_att_type_list.append((refType.order_number,'frrt',refType.pk,refType.record_type)) 
                #sort the new combined reference ad attribute type list combined
                form_att_type_list = sorted(form_att_type_list, key=lambda att: att[0])
                #we only want the first 5 types
                form_att_type_list = form_att_type_list[0:5]
                
                #Finally let's organize all of our reference and attribute values to match their provided order number
                formList = []                
               
                #Setup our inital queryset that includes all forms
                #***RECYCLING BIN*** Make sure our Forms are filtered by their deletion flags
                masterQuery = formtype.form_set.all().filter(flagged_for_deletion=False) 
                
                
                #Setup a list to hold the attribute types from the query. We want to show the record types that are part of the search terms,
                #   --rather than the default types that are in order. If there are less than 5 query record types, use the ordered record type list
                #   --until 5 are met.
                queryRTYPElist = []
                uniqueRTYPES = []
                rtypeCounter = 1
                #Load the JSON query from POST
                masterQueryJSON = json.loads(request.POST['currentQueryJSON'])
                
                #Update our progressbar to show we're at 10%
                progressData.jsonString = '{"message":"Performing Query","current_query":"","current_term":"","percent_done":"5","is_complete":"False"}'
                progressData.save() 
                
                #Loop through each separate query
                for query in sorted(masterQueryJSON['query_list']):
                    print >>sys.stderr, query
                    #setup a dictionary of key values of the query stats to add to the main querystas dictionary later
                    singleQueryStats = {} 
                    
                    #***RECYCLING BIN*** Make sure our Forms are filtered by their deletion flags
                    queriedForms = formtype.form_set.all().filter(flagged_for_deletion=False)
                    
                    currentJSONQuery = masterQueryJSON['query_list'][query]
                    
                    uniqueQuery = False
                    #Let's not allow any duplicate rtypes in the query rtype list header e.g. we don't want "Object ID" to show up 4 times 
                    #--if the user makes a query that compares it 4 times in 4 separate queries
                    if currentJSONQuery['RTYPE'] not in uniqueRTYPES: 
                        uniqueRTYPES.append(currentJSONQuery['RTYPE'])
                        uniqueQuery = True
                    
                    #We need to check whether or not this query is an AND/OR  or a null,e.g. the first one(so there is no and/or)
                    rtype, rtypePK = currentJSONQuery['RTYPE'].split("-")
                    
                    #store our percentDone variable to update the ajax progress message object
                    percentDone = 0
                    
                    #########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
                    # (FRAT) FormRecordAttributeType Lookups
                    #########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
                    if rtype == 'FRAT':
                        #thisRTYPE = FormRecordAttributeType.objects.get(pk=rtypePK)

                        #store the record type in a new rtype list if unique
                        if uniqueQuery: queryRTYPElist.append((rtypeCounter,'frat',rtypePK,currentJSONQuery['LABEL'])) 
                        rtypeCounter += 1
                        tCounter = 0;
                        logging.info("TimerA"+ " : " + str(time.clock()))
                        for term in currentJSONQuery['TERMS']:
                            #Now begin modifying the SQL query which each term of each individual query
                            #skip the term if the field was left blank
                            if term['TVAL'] != "" or term['QCODE'] == '4':
                                newQuery = None
                                if term['T-ANDOR'] != 'or':#We can assume it is an AND like addition if it's anything but 'or'
                                    #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                    if   term['QCODE'] == '0': newQuery = queriedForms.filter(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#CONTAINS    
                                    elif term['QCODE'] == '1': newQuery = queriedForms.filter(formrecordattributevalue__record_value__icontains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#ICONTAINS                                   
                                    elif term['QCODE'] == '2': newQuery = queriedForms.filter(formrecordattributevalue__record_value__exact=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#MATCHES EXACT                                    
                                    elif term['QCODE'] == '3': newQuery = queriedForms.exclude(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#EXCLUDES                                   
                                    elif term['QCODE'] == '4': newQuery = queriedForms.filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=rtypePK)#IS_NULL        
                                    #save stats and query

                                    queriedForms = newQuery
                                else:#Otherwise it's an OR statement
                                    #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                    if   term['QCODE'] == '0': newQuery = (formtype.form_set.all().filter(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK))#CONTAINS    
                                    elif term['QCODE'] == '1': newQuery = (formtype.form_set.all().filter(formrecordattributevalue__record_value__icontains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK))#ICONTAINS                                   
                                    elif term['QCODE'] == '2': newQuery = (formtype.form_set.all().filter(formrecordattributevalue__record_value__exact=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK))#MATCHES EXACT                                    
                                    elif term['QCODE'] == '3': newQuery = (formtype.form_set.all().exclude(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK))#EXCLUDES                                   
                                    elif term['QCODE'] == '4': newQuery = (formtype.form_set.all().filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=rtypePK))#IS_NULL 
                                    #save stats and query
                                    
                                    queriedForms = (newQuery | queriedForms)
                            logging.info("TimerB"+ " : " + str(time.clock()))
                            #We'll calculate percent by claiming finishing the query is at 50% when complete and at 20% when starting this section.
                            logging.info(rtypeCounter)
                            logging.info(len(masterQueryJSON['query_list']))
                            Qpercent = ((rtypeCounter-2) * (50.0/len(masterQueryJSON['query_list'])))
                            percentDone =  5 + Qpercent +  (tCounter * (Qpercent / len(currentJSONQuery['TERMS'])) )
                            progressData.jsonString = '{"message":"Performing Query # '+ str(rtypeCounter-1) + ' on term: '+term['TVAL']+'","current_query":"'+ currentJSONQuery['RTYPE'] + '","current_term":"'+term['TVAL']+'","percent_done":"'+ str(int(percentDone)) +'","is_complete":"False"}'
                            progressData.save() 
                            tCounter += 1
                            logging.info("TimerC"+ " : " + str(time.clock()))
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
                        #thisRTYPE = FormRecordReferenceType.objects.get(pk=rtypePK)
                        #store the record type in a new rtype list if unique
                        if uniqueQuery: queryRTYPElist.append((rtypeCounter,'frrt',rtypePK,currentJSONQuery['LABEL'])) 
                        rtypeCounter += 1
                        tCounter = 0;
                        logging.info("TimerD"+ " : " + str(time.clock()))
                        
                        #get the deep values
                        deepRTYPE, deepPK = currentJSONQuery['RTYPE-DEEP'].split('-')
                        
                        for term in currentJSONQuery['TERMS']:
                            #==========================================================================================================================================================================================
                            # IF WE ARE JUST LOOKING UP THE RTYPE FORM ID
                            #==========================================================================================================================================================================================
                            #TODO: This also needs to check external reference values if no match is found
                            if deepRTYPE == 'FORMID':
                                #Now begin modifying the SQL query which each term of each individual query
                                #skip the term if the field was left blank
                                if term['TVAL'] != "" or term['QCODE'] == '4':
                                    newQuery = None
                                    if term['T-ANDOR'] != 'or':#We can assume it is an AND like addition if it's anything but 'or'
                                        #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                        if   term['QCODE'] == '0': newQuery = queriedForms.filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK) #CONTAINS    
                                        elif term['QCODE'] == '1': newQuery = queriedForms.filter(ref_to_parent_form__record_reference__form_name__icontains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK) #ICONTAINS                                   
                                        elif term['QCODE'] == '2': newQuery = queriedForms.filter(ref_to_parent_form__record_reference__form_name__exact=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK)#MATCHES EXACT                                    
                                        elif term['QCODE'] == '3': newQuery = queriedForms.exclude(ref_to_parent_form__record_reference__form_name__contains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK)#EXCLUDES                                   
                                        elif term['QCODE'] == '4': newQuery = queriedForms.filter(ref_to_parent_form__record_reference__isnull=True, ref_to_parent_form__record_reference_type__pk=rtypePK) #IS_NULL        
                                        queriedForms = newQuery
                                    else:#Otherwise it's an OR statement
                                        #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                        if   term['QCODE'] == '0': newQuery = (formtype.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK))#CONTAINS    
                                        elif term['QCODE'] == '1': newQuery = (formtype.form_set.all().filter(ref_to_parent_form__record_reference__form_name__icontains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK))#ICONTAINS                                   
                                        elif term['QCODE'] == '2': newQuery = (formtype.form_set.all().filter(ref_to_parent_form__record_reference__form_name__exact=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK))#MATCHES EXACT                                    
                                        elif term['QCODE'] == '3': newQuery = (formtype.form_set.all().exclude(ref_to_parent_form__record_reference__form_name__contains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK))#EXCLUDES                                   
                                        elif term['QCODE'] == '4': newQuery = (formtype.form_set.all().filter(ref_to_parent_form__record_reference__isnull=True, ref_to_parent_form__record_reference_type__pk=rtypePK))#IS_NULL 
                                        queriedForms = (newQuery | queriedForms)
                            #==========================================================================================================================================================================================
                            # IF WE ARE LOOKING UP THE RELATIONS FRAT
                            #==========================================================================================================================================================================================
                            elif deepRTYPE == 'FRAT':
                                print >>sys.stderr, "We should be here"
                                #grab the formtype in question
                                deepFormType = FormType.objects.get(pk=FormRecordAttributeType.objects.get(pk=deepPK).form_type.pk)
                                #Now begin modifying the SQL query which each term of each individual query
                                #skip the term if the field was left blank
                                if term['TVAL'] != "" or term['QCODE'] == '4':
                                    newQuery = None
                                    #----------------------------------------------------------
                                    # AND STATEMENT FOR A --TERM--
                                    if term['T-ANDOR'] != 'or':#We can assume it is an AND like addition if it's anything but 'or'
                                        #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                        #First we Get a flattened list of form pk values from the deepFormType
                                        #Then we filter our current formtype queryset's frrt manytomany pks by the pk value list just created 
                                        if   term['QCODE'] == '0': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '1': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__icontains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '2': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '3': 
                                            flattenedSet = list(deepFormType.form_set.all().exclude(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '4': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        queriedForms = newQuery
                                    #--------------------------------------------------------
                                    # OR STATEMENT FOR a --TERM--
                                    else:
                                        #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                        if   term['QCODE'] == '0': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = formtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '1': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__icontains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = formtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '2': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = formtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '3': 
                                            flattenedSet = list(deepFormType.form_set.all().exclude(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = formtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '4': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = formtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        queriedForms = (newQuery | queriedForms)                            
                            #==========================================================================================================================================================================================
                            # IF WE ARE LOOKING UP THE RELATION'S FRRT(Only form ID allowed)
                            #==========================================================================================================================================================================================
                            elif deepRTYPE == 'FRRT':
                                print >>sys.stderr, "We should be here 3"
                                #grab the formtype in question
                                deepFormType = FormType.objects.get(pk=FormRecordReferenceType.objects.get(pk=deepPK).form_type_parent.pk)
                                #Now begin modifying the SQL query which each term of each individual query
                                #skip the term if the field was left blank
                                if term['TVAL'] != "" or term['QCODE'] == '4':
                                    newQuery = None
                                    #----------------------------------------------------------
                                    # AND STATEMENT FOR A --TERM--
                                    if term['T-ANDOR'] != 'or':#We can assume it is an AND like addition if it's anything but 'or'
                                        #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                        #First we Get a flattened list of form pk values from the deepFormType
                                        #Then we filter our current formtype queryset's frrt manytomany pks by the pk value list just created 
                                        if   term['QCODE'] == '0': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #CONTAINS 
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '1': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #ICONTAINS    
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '2': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #EXACT MATCH
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '3': 
                                            flattenedSet = list(deepFormType.form_set.all().exclude(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #EXCLUDES   
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '4': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__isnull=True).values_list('pk', flat=True)) #IS NULL  
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        queriedForms = newQuery
                                    #--------------------------------------------------------
                                    # OR STATEMENT FOR a --TERM--
                                    else:
                                        #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                        if   term['QCODE'] == '0': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = formtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '1': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #ICONTAINS    
                                            newQuery = formtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '2': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #EXACT MATCH
                                            newQuery = formtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '3': 
                                            flattenedSet = list(deepFormType.form_set.all().exclude(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #EXCLUDES 
                                            newQuery = formtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '4': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__isnull=True).values_list('pk', flat=True)) #IS NULL
                                            newQuery = formtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        queriedForms = (newQuery | queriedForms)            
                            #We'll calculate percent by claiming finishing the query is at 50% when complete and at 20% when starting this section.
                            Qpercent = ((rtypeCounter-2) * (50.0/len(masterQueryJSON['query_list'])))        
                            percentDone =  5 + Qpercent +  (tCounter * (Qpercent / len(currentJSONQuery['TERMS'])) )
                            progressData.jsonString = '{"message":"Performing Query # '+ str(rtypeCounter-1) + ' on term: '+term['TVAL']+'","current_query":"'+ currentJSONQuery['RTYPE'] + '","current_term":"'+term['TVAL']+'","percent_done":"'+ str(percentDone) +'","is_complete":"False"}'
                            progressData.save() 
                            tCounter += 1
                    #########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
                    # (Form ID) Lookups
                    #########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
                    elif rtype == "FORMID":
                        tCounter = 0;
                        logging.info("TimerD"+ " : " + str(time.clock()))
                        for term in currentJSONQuery['TERMS']:
                            #Now begin modifying the SQL query which each term of each individual query
                            #skip the term if the field was left blank
                            if term['TVAL'] != "" or term['QCODE'] == '4':
                                newQuery = None
                                print >>sys.stderr, str(formtype.form_set.all().filter(form_name__contains=term['TVAL']))
                                if term['T-ANDOR'] != 'or':#We can assume it is an AND like addition if it's anything but 'or'
                                    print >> sys.stderr, "Is it working?"
                                    #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                    if   term['QCODE'] == '0': newQuery = queriedForms.filter(form_name__contains=term['TVAL']) #CONTAINS    
                                    elif term['QCODE'] == '1': newQuery = queriedForms.filter(form_name__icontains=term['TVAL']) #ICONTAINS                                   
                                    elif term['QCODE'] == '2': newQuery = queriedForms.filter(form_name__exact=term['TVAL'])#MATCHES EXACT                                    
                                    elif term['QCODE'] == '3': newQuery = queriedForms.exclude(form_name__contains=term['TVAL'])#EXCLUDES                                   
                                    elif term['QCODE'] == '4': newQuery = queriedForms.filter(form_name__isnull=True) #IS_NULL        
                                    queriedForms = newQuery
                                else:#Otherwise it's an OR statement
                                    #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                    if   term['QCODE'] == '0': newQuery = (formtype.form_set.all().filter(form_name__contains=term['TVAL']))#CONTAINS    
                                    elif term['QCODE'] == '1': newQuery = (formtype.form_set.all().filter(form_name__icontains=term['TVAL']))#ICONTAINS                                   
                                    elif term['QCODE'] == '2': newQuery = (formtype.form_set.all().filter(form_name__exact=term['TVAL']))#MATCHES EXACT                                    
                                    elif term['QCODE'] == '3': newQuery = (formtype.form_set.all().exclude(form_name__contains=term['TVAL']))#EXCLUDES                                   
                                    elif term['QCODE'] == '4': newQuery = (formtype.form_set.all().filter(form_name__isnull=True))#IS_NULL 
                                    queriedForms = (newQuery | queriedForms)
                            #We'll calculate percent by claiming finishing the query is at 50% when complete and at 20% when starting this section.
                            Qpercent = ((rtypeCounter-2) * (50.0/len(masterQueryJSON['query_list'])))        
                            percentDone =  5 + Qpercent +  (tCounter * (Qpercent / len(currentJSONQuery['TERMS'])) )
                            progressData.jsonString = '{"message":"Performing Query # '+ str(rtypeCounter-1) + ' on term: '+term['TVAL']+'","current_query":"'+ currentJSONQuery['RTYPE'] + '","current_term":"'+term['TVAL']+'","percent_done":"'+ str(percentDone) +'","is_complete":"False"}'
                            progressData.save() 
                            tCounter += 1
                
                            
                   
                    #If this is an AND query--attach it to the masterQuery as so.
                    if currentJSONQuery['Q-ANDOR'] == 'and': 
                        masterQuery = (masterQuery & queriedForms)
                    #If it's an OR query, attach it to the masterQuery as an OR statement
                    elif currentJSONQuery['Q-ANDOR'] == 'or': 
                        masterQuery = (masterQuery | queriedForms)
                    #Otherwise its the first, or a single query and should simply replace the masterQuery
                    #also set the count to this first query so we have one in case there is only one query
                    else: 
                        masterQuery = queriedForms;
         
                #Now make sure our final queried list has distint values--merging querysets has a tendency to create duplicates
                masterQuery = masterQuery.distinct()
                #***RECYCLING BIN*** Make sure our final query gets filtered out with recycled forms(They can potentially be re-added in the above query engine
                masterQuery.filter(flagged_for_deletion=False)
                #Send a message to our AJAX request object
                progressData.jsonString = '{"message":"Running raw SQL","current_query":"","current_term":"''","percent_done":"50","is_complete":"False"}'
                progressData.save()                 
               
               
                masterQueryCount = masterQuery.count()
                
                #Send a message to our AJAX request object
                progressData.jsonString = '{"message":"Loading Queried Forms & Sending generated stats now...","current_query":"","current_term":"''","percent_done":"60","is_complete":"False","stats":"none"}'
                progressData.save()                    

               

                #We need to check the # of rtypes in our header list now--if it's less than 5, then let's add from the ordered list
                #We also need to make sure we aren't adding duplicates of the RTYPES, e.g. if we're looking for a match under "Object Number" and Object Number is already
                #--in our sorted order-num list--let's not re-add it.
                for attType in form_att_type_list:
                    print >>sys.stderr, "AttTypeList:  " + str(attType)
                    matchfound = False;
                    for queryAttType in queryRTYPElist:
                        if attType[2] == queryAttType[2]:
                            matchfound = True
                    if matchfound == False and len(queryRTYPElist) < 5:    
                        #let's arbitrarily add '100' to the order number so that our queries are definitely in front of these
                        queryRTYPElist.append((attType[0] + 100,attType[1],attType[2],attType[3]))
                        
                for q in queryRTYPElist:
                    print >>sys.stderr, "QTypeList:  " + str(q)


                
                #serializeTest = serializers.serialize("json", masterQuery)         
                queryCounter = 0
                logging.info("TEST A")
                logging.info("TEST A END")
                
                
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
                
                print >>sys.stderr, startIndex;
                print >>sys.stderr, endIndex;
                #-----------------------------------------------------------------------------------------------------------
                # Here we need to determine whether or not the form type being queried is hierchical.
                #   --If it is hierachical, then we just organize the masterQuery and sort it with the hierachy in mind
                #   --as well as with its hierchical labels--otherwise just perform a normal sort by its label
                if formtype.is_hierarchical:
                    global hierarchyFormList
                    hierarchyFormList = []
                    #Finally let's organize all of our reference and attribute values to match their provided order number
                    #We want to find all the forms that have no parent element first--these are the top of the nodes
                    #Then we'll organize the forms by hierarchy--which can then be put through the normal ordered query
                    print >>sys.stderr, "TIMER R"+ " : " + str(time.clock())
                    masterQuery = masterQuery.filter(hierarchy_parent=None).exclude(form_number=None, form_name=None)[startIndex:endIndex]
                    print >>sys.stderr, "TIMER RR"+ " : " + str(time.clock())
                    if masterQuery:
                        total = masterQuery.count()
                        for aForm in masterQuery: 
                            queryCounter += 1
                            Qpercent = ( queryCounter * (30/(total*1.0)))
                            finalPercent = (60 + int(Qpercent))
                            progressData.jsonString = '{"SQL":"True","message":"Loading Queried Forms!","current_query":"'+ str(queryCounter) +'","current_term":"'+ str(total) +'","percent_done":"' + str(finalPercent) + '","is_complete":"False","stats":"none"}'
                            progressData.save()
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
                    print >>sys.stderr, "TIMER R"+ " : " + str(time.clock())
                    #sort the formlist by their sort_index
                    masterQuery = masterQuery.order_by('sort_index')[startIndex:endIndex]
                print >>sys.stderr, "TIMER RR"+ " : " + str(time.clock())
                #count the query so we only make one database hit before looping(otherwise each loop would be another hit)
                if masterQuery:
                    total = masterQuery.count()
                    print >>sys.stderr, "TIMER RRR"+ " : " + str(time.clock())
                    for aForm in masterQuery:
                        print >>sys.stderr, "TIMER S"+ " : " + str(time.clock())
                        queryCounter += 1
                        Qpercent = ( queryCounter * (30/(total*1.0)))
                        finalPercent = (60 + int(Qpercent))
                        progressData.jsonString = '{"SQL":"True","message":"Loading Queried Forms!","current_query":"'+ str(queryCounter) +'","current_term":"'+ str(total) +'","percent_done":"' + str(finalPercent) + '","is_complete":"False","stats":"none"}'
                        print >>sys.stderr, "TIMER RRRR"+ " : " + str(time.clock())
                        progressData.save()
                        print >>sys.stderr, "TIMER RRRRR"+ " : " + str(time.clock())
                       # print >>sys.stderr, str(aForm.pk) + ":  <!-- Current Form Pk"
                        rowList = []
                        #Let's loop through each item in the queryRTYPE list and match up the frav's in each queried form so the headers match the form attribute values
                        for rtype in queryRTYPElist:
                            if rtype[1] == 'frat':
                                #print >>sys.stderr, str(rtype[2]) + '  ' + str(aForm.formrecordattributevalue_set.all().filter(record_attribute_type__pk=rtype[2]).count())
                                print >>sys.stderr, "TIMER X"+ " : " + str(time.clock())
                                formRVAL = aForm.formrecordattributevalue_set.all().filter(record_attribute_type__pk=rtype[2])
                                #We need to check for NULL FRAV's here. When a user manually creates new forms, they don't always have FRAVS created for them if they leave it blank
                                if formRVAL.exists():
                                    rowList.append((rtype[0],'frav',formRVAL[0].record_value, formRVAL[0].pk))
                                else:
                                    print >>sys.stderr, "Whoops--something happened. There are no RVALS for 'frats' using: " + str(rtype[2])
                                    #If there isn't an RVAL for this RTYPE then make a new one and return it instead
                                    newFRAV = FormRecordAttributeValue()
                                    newFRAV.record_attribute_type = FormRecordAttributeType.objects.get(pk=rtype[2])
                                    newFRAV.form_parent = aForm
                                    newFRAV.project = aForm.project
                                    newFRAV.record_value = ""
                                    newFRAV.save()
                                    rowList.append((rtype[0],'frav',newFRAV.record_value, newFRAV.pk))
                                print >>sys.stderr, "TIMER Y"+ " : " + str(time.clock())
                            else:
                                #for frrt in aForm.ref_to_parent_form.all():
                                    #print >>sys.stderr, "" + str(frrt.pk)
                                formRVAL = aForm.ref_to_parent_form.all().filter(record_reference_type__pk=rtype[2])
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

                        print >>sys.stderr, "TIMER Z"+ " : " + str(time.clock())
                        #sort the new combined reference ad attribute type list combined
                        rowList = sorted(rowList, key=lambda att: att[0])
                        # print >> sys.stderr, str(rowList)
                        #Now let's handle the thumbnail bit of business for the query
                        #--If the current form IS a media type already, then use itself to grab the thumbnail URI
                        if aForm.form_type.type == 1:
                            thumbnailURI = aForm.get_thumbnail_type()
                        else:
                            #let's find the first media type in the order but offer a default to "NO PREVIEW" if not found
                            thumbnailURI = staticfiles_storage.url("/static/site-images/no-thumb-missing.png")
                            for record in rowList:            
                                #if it's a reference
                                if record[1] == 'frrv' or record[1] == 'frrv-ext':
                                    currentRTYPE = FormRecordReferenceValue.objects.get(pk=int(record[3]))
                                    #if it's not a NoneType reference:
                                    if currentRTYPE.record_reference_type.form_type_reference != None:
                                        #If its a reference to a media type
                                        if currentRTYPE.record_reference_type.form_type_reference.type == 1:
                                            print >> sys.stderr, "WE GOT A MATCH"
                                            #Because a form record reference value is a ManyToMany relationship, we just grab the first one in the list
                                            #TODO this may need to be edited later--because you can't order the selections. I may add another ForeignKey called
                                            #"Thumbnail Reference" which links to a single relation to a form of a media type--this would also
                                            #probably solve the complexity of looping through to grab it as it stands right now
                                            #****WE also have to check for NULL references
                                            if currentRTYPE.record_reference.all().count() > 0:
                                                thumbnailURI = currentRTYPE.record_reference.all()[0].get_thumbnail_type()
                                            break
                                    
                        #we only want the first 5 values from the final ordered list of attributes
                        rowList = rowList[0:5]


                        formList.append([thumbnailURI,str(aForm.pk), aForm, rowList])   
                        print >>sys.stderr, "TIMER ZZ"+ " : " + str(time.clock())
                form_att_type_list, form_list = form_att_type_list, formList
                
                #update our progress bar
                progressData.jsonString = '{"message":"Packaging Query for User","current_query":"","current_term":"","percent_done":"90","is_complete":"False","stats":"none"}'
                progressData.save() 
                
                finishedJSONquery = {}
                
                headerList=[]
                for rtype in queryRTYPElist:
                    rtypeDict = {}
                    rtypeDict["index"] = rtype[0]
                    rtypeDict["rtype"] = rtype[1]
                    rtypeDict["pk"] = rtype[2]
                    rtypeDict["name"] = rtype[3]
                    headerList.append(rtypeDict)

                #update our progress bar
                progressData.jsonString = '{"message":"Packaging Query for User","current_query":"","current_term":"","percent_done":"93","is_complete":"False","stats":"none"}'
                progressData.save() 
                
                finishedJSONquery["rtype_header"] = headerList
                allFormList = []
                counter = 0
                total = len(formList)
                for form in formList:
                    #update our progress bar
                    counter += 1
                    currentPercent = 93 + int((counter*(5.0/total)))
                    progressData.jsonString = '{"message":"Packaging Query for User","current_query":"","current_term":"","percent_done":"'+str(currentPercent)+'","is_complete":"False","stats":"none"}'
                    progressData.save() 
                    
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

                
                finishedJSONquery["form_list"] = allFormList
                finishedJSONquery["formtype"] = formtype.form_type_name
                finishedJSONquery["formtype_pk"] = formtype.pk
                finishedJSONquery["project_pk"] = request.user.permissions.project.pk
                finishedJSONquery["project"] = request.user.permissions.project.name
                finishedJSONquery["pagination_page"] = requestedPageNumber
                finishedJSONquery["resultsCount"] = masterQueryCount 
                finishedJSONquery["currentQuery"] = request.POST['currentQueryJSON']
                #save our stats to the returned JSON
                #convert to JSON
                finishedJSONquery = json.dumps(finishedJSONquery)

                #Update our progress bar
                progressData.jsonString = '{"message":"Finished!","current_query":"","current_term":"","percent_done":"100","is_complete":"True","stats":"none"}'
                progressData.save() 
                print >>sys.stderr,  "Timer End"     
                return HttpResponse(finishedJSONquery, content_type="application/json")
            ERROR_MESSAGE += "Error: You don't have permission to access this FormType from another project"
        ERROR_MESSAGE += "Error: You have not submitted through POST"
    else: ERROR_MESSAGE += "Error: You do not have permission to access querying this project"
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")   

#=======================================================#
#   ACCESS LEVEL :  1       RUN_MASTER_QUERY_ENGINE() *Recycling
#=======================================================#   
def run_master_query_engine(self, request):
    #***************#
    ACCESS_LEVEL = 1
    #***************#
    
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
    
    #Check our user's session and access level
    if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
    
        if request.method == 'POST':
                
            print >>sys.stderr, request.POST
            #Make the AJAX Request Data Model for subsequent AJAX calls
            progressData = AJAXRequestData(uuid=request.POST.get('uuid'), jsonString='{"message":"Loading Json","current_query":"","current_term":"","percent_done":"0","is_complete":"False"}')
            progressData.save()
            
            #We need to loop through EACH project query in the JSON header and create a separate results box for each one
            masterProjectQuery = json.loads(request.POST['master_query'])
            
            masterQueryResults = {}
            all_project_queries = []
            masterQueryResults['final_query_set'] = all_project_queries
            
            query_set = masterProjectQuery['query_list']
            
            globalPercentage = 0
            queryPercentage = 0
            queryPercentageIncrement = 100 / len(query_set)
            queryPercentageCounter = 0
            for query in query_set:
                print >>sys.stderr, "Starting a query?"
                # PROGRESS REPORT *****************************************
                #Setup our percentage monitors for the AJAX progress report
                queryPercentage = (queryPercentageCounter * queryPercentageIncrement)
                queryPercentageCounter += 1
                globalPercentage = queryPercentage
                progressData.jsonString = '{"message":"Performing Query","current_query":"'+query['project_label']+' : '+query['formtype_label']+'","current_term":"","percent_done":"'+str(globalPercentage)+'","is_complete":"False"}'
                progressData.save() 
                #**********************************************************
                
                queryProject = FormProject.objects.get(pk=query['project_pk']) 
                queryFormtype = FormType.objects.get(pk=query['formtype_pk'])
                #If we are querying a project different than the user and it is NOT set to public, then throw an error because it should be private
                if (queryProject.pk != request.user.permissions.project.pk and queryProject.is_public == False) or (queryFormtype.project.pk != request.user.permissions.project.pk and queryFormtype.is_public == False):
                    ERROR_MESSAGE += "Error: You are trying to access a project or formtype that doesn't exist or access is not allowed. This has been logged to the network administrator"
                    #Delete Our progress object
                    print >>sys.stderr, "Hmmm are we exiting here?"
                    progressData.delete();
                    #break the loop and return the security message
                    break;
                #Otherwise continue
                else:

                    #create a dictionary to store the query statistics
                    queryStats = {}
                    queryStats['formtype'] = query['formtype_label']
                    queryStats['formtype_pk'] = query['formtype_pk']
                    queryStats['project'] = query['project_label']
                    queryStats['project_pk'] = query['project_pk']
                    queryList = []
                    queryStats['query_list'] = queryList
                    primaryConstraintList = []
                    
                    print >>sys.stderr,  queryStats['project_pk']  + "  :  "  + query['project_pk']
                    
                    #First let's setup our header field of ordered labels 
                    print >>sys.stderr,  "Timer Start"                
                    form_att_type_list = []
                    #***RECYCLING BIN*** Make sure our RTYPES are filtered by their deletion flags
                    for attType in queryFormtype.formrecordattributetype_set.all().filter(flagged_for_deletion=False).order_by('order_number'):
                        form_att_type_list.append((attType.order_number,'frat',attType.pk,attType.record_type)) 
             
                    #***RECYCLING BIN*** Make sure our RTYPES are filtered by their deletion flags
                    for refType in queryFormtype.ref_to_parent_formtype.all().filter(flagged_for_deletion=False).order_by('order_number'):
                        form_att_type_list.append((refType.order_number,'frrt',refType.pk,refType.record_type)) 

                    #sort the new combined reference ad attribute type list combined
                    form_att_type_list = sorted(form_att_type_list, key=lambda att: att[0])
                    #we only want the first 5 types
                    #form_att_type_list = form_att_type_list[0:5]
                    
                    #Finally let's organize all of our reference and attribute values to match their provided order number
                    formList = []                
                   
                    #Setup our inital queryset that includes all forms
                    masterQuery = queryFormtype.form_set.all().filter(flagged_for_deletion=False) 
                    
                    
                    #Setup a list to hold the attribute types from the query. We want to show the record types that are part of the search terms,
                    #   --rather than the default types that are in order. If there are less than 5 query record types, use the ordered record type list
                    #   --until 5 are met.
                    queryRTYPElist = []
                    uniqueRTYPES = []
                    rtypeCounter = 1
                    #Load the JSON query from POST
                    
                    

                    for term in query['terms']:
        
                        print >>sys.stderr, query
                        #setup a dictionary of key values of the query stats to add to the main querystas dictionary later
                        singleQueryStats = {} 
                        
                        queriedForms = masterQuery
                        #***RECYCLING BIN*** Make sure our Forms are filtered by their deletion flag

                        uniqueQuery = False
                        #Let's not allow any duplicate rtypes in the query rtype list header e.g. we don't want "Object ID" to show up 4 times 
                        #--if the user makes a query that compares it 4 times in 4 separate queries
                        if (term['pk']+ '_' +term['RTYPE']) not in uniqueRTYPES: 
                            uniqueRTYPES.append((term['pk']+ '_' +term['RTYPE']))
                            uniqueQuery = True
                        
                        #We need to check whether or not this query is an AND/OR  or a null,e.g. the first one(so there is no and/or)
                        rtype = term['RTYPE']
                        rtypePK = term['pk']
                        
                        print >>sys.stderr, rtype + " :    <!----------------------------------------------------------------"
                        #########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
                        # (FRAT) FormRecordAttributeType Lookups
                        #########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
                        if rtype == 'FRAT':
                            #store the record type in a new rtype list if unique
                            if uniqueQuery: queryRTYPElist.append((rtypeCounter,'frat',rtypePK,term['LABEL'])) 
                            rtypeCounter += 1
                            tCounter = 0;
                            
                            #store stats
                            singleQueryStats['rtype_name'] = term['LABEL']
                            singleQueryStats['rtype_pk'] = rtypePK
                            singleQueryStats['rtype'] = rtype
                            termStats = []
                            singleQueryStats['all_terms'] = termStats
                            logging.info("TimerA"+ " : " + str(time.clock()))
                            
                            #Now begin modifying the SQL query which each term of each individual query
                            #skip the term if the field was left blank
                            if term['TVAL'] != "" or term['QCODE'] == '4':
                                newQuery = None
                                if term['ANDOR'] != 'or':#We can assume it is an AND like addition if it's anything but 'or'
                                    #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                    if   term['QCODE'] == '0': newQuery = queriedForms.filter(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#CONTAINS    
                                    elif term['QCODE'] == '1': newQuery = queriedForms.filter(formrecordattributevalue__record_value__icontains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#ICONTAINS                                   
                                    elif term['QCODE'] == '2': newQuery = queriedForms.filter(formrecordattributevalue__record_value__exact=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#MATCHES EXACT                                    
                                    elif term['QCODE'] == '3': newQuery = queriedForms.exclude(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#EXCLUDES                                   
                                    elif term['QCODE'] == '4': newQuery = queriedForms.filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=rtypePK)#IS_NULL        
                                    #save stats and query
                                    term['count'] =  newQuery.count()
                                    termStats.append(term)
                                    queriedForms = newQuery
                                else:#Otherwise it's an OR statement
                                    #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                    if   term['QCODE'] == '0': newQuery = (queryFormtype.form_set.all().filter(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK))#CONTAINS    
                                    elif term['QCODE'] == '1': newQuery = (queryFormtype.form_set.all().filter(formrecordattributevalue__record_value__icontains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK))#ICONTAINS                                   
                                    elif term['QCODE'] == '2': newQuery = (queryFormtype.form_set.all().filter(formrecordattributevalue__record_value__exact=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK))#MATCHES EXACT                                    
                                    elif term['QCODE'] == '3': newQuery = (queryFormtype.form_set.all().exclude(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK))#EXCLUDES                                   
                                    elif term['QCODE'] == '4': newQuery = (queryFormtype.form_set.all().filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=rtypePK))#IS_NULL 
                                    #***RECYCLING BIN*** Make sure our NEW query is always filtered by recycling bin flags--All OR statements will need this filter
                                    newQuery = newQuery.filter(flagged_for_deletion=False)
                                    #save stats and query
                                    term['count'] =  newQuery.count()
                                    termStats.append(term)
                                    queriedForms = (newQuery | queriedForms)
                                logging.info("TimerB"+ " : " + str(time.clock()))

                                logging.info("TimerC"+ " : " + str(time.clock()))
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
                            tCounter = 0;
                            
                            #store stats
                            singleQueryStats['rtype_name'] = term['LABEL']
                            singleQueryStats['rtype_pk'] = rtypePK
                            singleQueryStats['rtype'] = rtype
                            termStats = []
                            singleQueryStats['all_terms'] = termStats
                            #get the deep values
                            deepPK, deepRTYPE = term['RTYPE-DEEP'].split('__')
                            print >>sys.stderr, deepPK + "  :  " + deepRTYPE + " <!-------------------------------------------"
                            #==========================================================================================================================================================================================
                            # IF WE ARE JUST LOOKING UP THE RTYPE FORM ID
                            #==========================================================================================================================================================================================
                            #TODO: This also needs to check external reference values if no match is found
                            if deepRTYPE == 'FORMID':
                                print >> sys.stderr, "WTF"
                                #Now begin modifying the SQL query which each term of each individual query
                                #skip the term if the field was left blank
                                if term['TVAL'] != "" or term['QCODE'] == '4':
                                    newQuery = None
                                    if term['ANDOR'] != 'or':#We can assume it is an AND like addition if it's anything but 'or'
                                        #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                        if   term['QCODE'] == '0': newQuery = queriedForms.filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK) #CONTAINS    
                                        elif term['QCODE'] == '1': newQuery = queriedForms.filter(ref_to_parent_form__record_reference__form_name__icontains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK) #ICONTAINS                                   
                                        elif term['QCODE'] == '2': newQuery = queriedForms.filter(ref_to_parent_form__record_reference__form_name__exact=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK)#MATCHES EXACT                                    
                                        elif term['QCODE'] == '3': newQuery = queriedForms.exclude(ref_to_parent_form__record_reference__form_name__contains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK)#EXCLUDES                                   
                                        elif term['QCODE'] == '4': newQuery = queriedForms.filter(ref_to_parent_form__record_reference__isnull=True, ref_to_parent_form__record_reference_type__pk=rtypePK) #IS_NULL        
                                        #save stats and query
                                        term['count'] =  newQuery.count()
                                        termStats.append(term)
                                        queriedForms = newQuery
                                    else:#Otherwise it's an OR statement
                                        #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                        if   term['QCODE'] == '0': newQuery = (queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK))#CONTAINS    
                                        elif term['QCODE'] == '1': newQuery = (queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__form_name__icontains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK))#ICONTAINS                                   
                                        elif term['QCODE'] == '2': newQuery = (queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__form_name__exact=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK))#MATCHES EXACT                                    
                                        elif term['QCODE'] == '3': newQuery = (queryFormtype.form_set.all().exclude(ref_to_parent_form__record_reference__form_name__contains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK))#EXCLUDES                                   
                                        elif term['QCODE'] == '4': newQuery = (queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__isnull=True, ref_to_parent_form__record_reference_type__pk=rtypePK))#IS_NULL 
                                        #***RECYCLING BIN*** Make sure our NEW query is always filtered by recycling bin flags--All OR statements will need this filter
                                        newQuery = newQuery.filter(flagged_for_deletion=False)
                                        #save stats and query
                                        term['count'] =  newQuery.count()
                                        termStats.append(term)
                                        queriedForms = (newQuery | queriedForms)
                            #==========================================================================================================================================================================================
                            # IF WE ARE LOOKING UP THE RELATIONS FRAT
                            #==========================================================================================================================================================================================
                            elif deepRTYPE == 'FRAT':
                                print >>sys.stderr, "We should be here"
                                #grab the formtype in question
                                deepFormType = FormType.objects.filter(pk=FormRecordAttributeType.objects.get(pk=deepPK).form_type.pk)
                                #***RECYCLING BIN*** Make sure our this Deep query FormType is always filtered by recycling bin flags
                                deepFormType = deepFormType.filter(flagged_for_deletion=False)
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
                                        if   term['QCODE'] == '0': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '1': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__icontains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '2': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '3': 
                                            flattenedSet = list(deepFormType.form_set.all().exclude(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '4': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        #save stats and query
                                        term['count'] =  newQuery.count()
                                        termStats.append(term)
                                        queriedForms = newQuery
                                    #--------------------------------------------------------
                                    # OR STATEMENT FOR a --TERM--
                                    else:
                                        #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                        if   term['QCODE'] == '0': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '1': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__icontains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '2': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '3': 
                                            flattenedSet = list(deepFormType.form_set.all().exclude(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '4': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        #***RECYCLING BIN*** Make sure our NEW query is always filtered by recycling bin flags--All OR statements will need this filter
                                        newQuery = newQuery.filter(flagged_for_deletion=False)    
                                        #save stats and query
                                        term['count'] =  newQuery.count()
                                        termStats.append(term)
                                        queriedForms = (newQuery | queriedForms)                            
                            #==========================================================================================================================================================================================
                            # IF WE ARE LOOKING UP THE RELATION'S FRRT(Only form ID allowed)
                            #==========================================================================================================================================================================================
                            elif deepRTYPE == 'FRRT':
                                print >>sys.stderr, "We should be here 3"
                                #grab the formtype in question
                                deepFormType = FormType.objects.get(pk=FormRecordReferenceType.objects.get(pk=deepPK).form_type_parent.pk)
                                #***RECYCLING BIN*** Make sure our this Deep query FormType is always filtered by recycling bin flags
                                deepFormType = deepFormType.filter(flagged_for_deletion=False)
                                
                                #Now begin modifying the SQL query which each term of each individual query
                                #skip the term if the field was left blank
                                if term['TVAL'] != "" or term['QCODE'] == '4':
                                    newQuery = None
                                    #----------------------------------------------------------
                                    # AND STATEMENT FOR A --TERM--
                                    if term['T-ANDOR'] != 'or':#We can assume it is an AND like addition if it's anything but 'or'
                                        #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                        #First we Get a flattened list of form pk values from the deepFormType
                                        #Then we filter our current formtype queryset's frrt manytomany pks by the pk value list just created 
                                        if   term['QCODE'] == '0': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #CONTAINS 
                                            print >>sys.stderr, "LOOK HERE ROBERT"
                                            print >>sys.stderr, flattenedSet
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '1': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #ICONTAINS    
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '2': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #EXACT MATCH
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '3': 
                                            flattenedSet = list(deepFormType.form_set.all().exclude(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #EXCLUDES   
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '4': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__isnull=True).values_list('pk', flat=True)) #IS NULL  
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                               
                                        #save stats and query
                                        term['count'] =  newQuery.count()
                                        termStats.append(term)
                                        queriedForms = newQuery
                                    #--------------------------------------------------------
                                    # OR STATEMENT FOR a --TERM--
                                    else:
                                        #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                        if   term['QCODE'] == '0': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '1': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #ICONTAINS    
                                            newQuery = queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '2': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #EXACT MATCH
                                            newQuery = queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '3': 
                                            flattenedSet = list(deepFormType.form_set.all().exclude(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #EXCLUDES 
                                            newQuery = queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '4': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__isnull=True).values_list('pk', flat=True)) #IS NULL
                                            newQuery = queryFormtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        #***RECYCLING BIN*** Make sure our NEW query is always filtered by recycling bin flags--All OR statements will need this filter
                                        newQuery = newQuery.filter(flagged_for_deletion=False)    
                                        #save stats and query
                                        term['count'] =  newQuery.count()
                                        termStats.append(term)
                                        queriedForms = (newQuery | queriedForms)            

                        #########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
                        # (Form ID) Lookups
                        #########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
                        elif rtype == "FORMID":
                                tCounter = 0;
                                #store stats
                                singleQueryStats['rtype_name'] = term['LABEL']
                                singleQueryStats['rtype_pk'] = rtypePK
                                singleQueryStats['rtype'] = rtype
                                termStats = []
                                singleQueryStats['all_terms'] = termStats
                                logging.info("TimerD"+ " : " + str(time.clock()))

                                #Now begin modifying the SQL query which each term of each individual query
                                #skip the term if the field was left blank
                                if term['TVAL'] != "" or term['QCODE'] == '4':
                                    newQuery = None
                                    print >>sys.stderr, str(queryFormtype.form_set.all().filter(form_name__contains=term['TVAL']))
                                    if term['T-ANDOR'] != 'or':#We can assume it is an AND like addition if it's anything but 'or'
                                        print >> sys.stderr, "Is it working?"
                                        #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                        if   term['QCODE'] == '0': newQuery = queriedForms.filter(form_name__contains=term['TVAL']) #CONTAINS    
                                        elif term['QCODE'] == '1': newQuery = queriedForms.filter(form_name__icontains=term['TVAL']) #ICONTAINS                                   
                                        elif term['QCODE'] == '2': newQuery = queriedForms.filter(form_name__exact=term['TVAL'])#MATCHES EXACT                                    
                                        elif term['QCODE'] == '3': newQuery = queriedForms.exclude(form_name__contains=term['TVAL'])#EXCLUDES                                   
                                        elif term['QCODE'] == '4': newQuery = queriedForms.filter(form_name__isnull=True) #IS_NULL        
                                        #save stats and query
                                        term['count'] =  newQuery.count()
                                        termStats.append(term)
                                        queriedForms = newQuery
                                    else:#Otherwise it's an OR statement
                                        #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                        if   term['QCODE'] == '0': newQuery = (queryFormtype.form_set.all().filter(form_name__contains=term['TVAL']))#CONTAINS    
                                        elif term['QCODE'] == '1': newQuery = (queryFormtype.form_set.all().filter(form_name__icontains=term['TVAL']))#ICONTAINS                                   
                                        elif term['QCODE'] == '2': newQuery = (queryFormtype.form_set.all().filter(form_name__exact=term['TVAL']))#MATCHES EXACT                                    
                                        elif term['QCODE'] == '3': newQuery = (queryFormtype.form_set.all().exclude(form_name__contains=term['TVAL']))#EXCLUDES                                   
                                        elif term['QCODE'] == '4': newQuery = (queryFormtype.form_set.all().filter(form_name__isnull=True))#IS_NULL 
                                        #***RECYCLING BIN*** Make sure our NEW query is always filtered by recycling bin flags--All OR statements will need this filter
                                        newQuery = newQuery.filter(flagged_for_deletion=False)    
                                        #save stats and query
                                        term['count'] =  newQuery.count()
                                        termStats.append(term)
                                        queriedForms = (newQuery | queriedForms)
                
                        queryList.append(singleQueryStats)    
                        masterQuery = queriedForms 

                        singleQueryStats['ANDOR'] = term['ANDOR']
                        singleQueryStats['count'] = masterQuery.count()

                        queryStats['count'] = singleQueryStats['count']



                    
                    #Send a message to our AJAX request object
                    progressData.jsonString = '{"message":"Running raw SQL","current_query":"","current_term":"''","percent_done":"50","is_complete":"False"}'
                    progressData.save()                 
                   
                   
                    jsonStats = json.dumps(queryStats)
                    #Send a message to our AJAX request object
                    progressData.jsonString = '{"message":"Loading Queried Forms & Sending generated stats now...","current_query":"","current_term":"''","percent_done":"60","is_complete":"False","stats":'+jsonStats+'}'
                    progressData.save()                    

                    #Now make sure our final queried list has distint values--merging querysets has a tendency to create duplicates
                    masterQuery = masterQuery.distinct()
                    #***RECYCLING BIN*** A Final redundant recycling bin filter--just to be safe
                    masterQuery = masterQuery.filter(flagged_for_deletion=False)                      

                    #We need to check the # of rtypes in our header list now--if it's less than 5, then let's add from the ordered list
                    #We also need to make sure we aren't adding duplicates of the RTYPES, e.g. if we're looking for a match under "Object Number" and Object Number is already
                    #--in our sorted order-num list--let's not re-add it.
                    for attType in form_att_type_list:
                        print >>sys.stderr, "AttTypeList:  " + str(attType)
                        matchfound = False;
                        for queryAttType in queryRTYPElist:
                            if attType[2] == queryAttType[2]:
                                matchfound = True
                        if matchfound == False:    
                            #let's arbitrarily add '100' to the order number so that our queries are definitely in front of these
                            queryRTYPElist.append((attType[0] + 100,attType[1],attType[2],attType[3]))
                            
                    for q in queryRTYPElist:
                        print >>sys.stderr, "QTypeList:  " + str(q)


                    
                    #serializeTest = serializers.serialize("json", masterQuery)         
                    queryCounter = 0
                    logging.info("TEST A")
                    total = queryStats['count']
                    paginationTotal = total
                    logging.info("TEST A END")
                    
                    print >>sys.stderr, "TIMER HOHOHOHOOHOHOHO  START"
                    #We need to grab ALL the form pk values in a similarly sorted list 
                    paginationQuery = masterQuery.order_by('sort_index')
                    paginationFormList = []
                    if paginationQuery:
                        for form in paginationQuery:
                            paginationFormList.append(form.pk)
                    #print >>sys.stderr, paginationFormList
                    print >>sys.stderr, "TIMER HOHOHOHOOHOHOHO  END"
                    
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
                        masterQuery =  masterQuery.filter(hierarchy_parent=None).exclude(form_number=None, form_name=None)[:25]
                        #CACHE -- this caches the query for the loop
                        if masterQuery:
                            for aForm in masterQuery: 
                                
                                queryCounter += 1
                                Qpercent = ( queryCounter * (30/(total*1.0)))
                                finalPercent = (60 + int(Qpercent))
                                progressData.jsonString = '{"SQL":"True","message":"Loading Queried Forms!","current_query":"'+ str(queryCounter) +'","current_term":"'+ str(total) +'","percent_done":"' + str(finalPercent) + '","is_complete":"False","stats":'+jsonStats+'}'
                                progressData.save()
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
                        masterQuery = masterQuery.order_by('sort_index')[:25]
                        
                        
                    #print >>sys.stderr, masterQuery  
                    #CACHE -- This cache's the query before looping through it
                    if masterQuery:
                        for aForm in masterQuery:
                            queryCounter += 1
                            Qpercent = ( queryCounter * (30/(total*1.0)))
                            finalPercent = (60 + int(Qpercent))
                            progressData.jsonString = '{"SQL":"True","message":"Loading Queried Forms!","current_query":"'+ str(queryCounter) +'","current_term":"'+ str(total) +'","percent_done":"' + str(finalPercent) + '","is_complete":"False","stats":'+jsonStats+'}'
                            progressData.save()
                            print >>sys.stderr, str(aForm.pk) + ":  <!-- Current Form Pk"
                            rowList = []
                            #Let's loop through each item in the queryRTYPE list and match up the frav's in each queried form so the headers match the form attribute values
                            for rtype in queryRTYPElist:
                                if rtype[1] == 'frat':
                                    print >>sys.stderr, str(rtype[2]) + '  ' + str(aForm.formrecordattributevalue_set.all().filter(record_attribute_type__pk=rtype[2]).count())
                                    formRVAL = aForm.formrecordattributevalue_set.all().filter(record_attribute_type__pk=rtype[2])
                                    #We need to check for NULL FRAV's here. When a user manually creates new forms, they don't always have FRAVS created for them if they leave it blank
                                    if formRVAL.exists():
                                        rowList.append((rtype[0],'frav',formRVAL[0].record_value, formRVAL[0].pk))
                                    else:
                                        print >>sys.stderr, "Whoops--something happened. There are no RVALS for 'frats' using: " + str(rtype[2])
                                        #If there isn't an RVAL for this RTYPE then make a new one and return it instead
                                        newFRAV = FormRecordAttributeValue()
                                        newFRAV.record_attribute_type = FormRecordAttributeType.objects.get(pk=rtype[2])
                                        newFRAV.form_parent = aForm
                                        newFRAV.project = aForm.project
                                        newFRAV.record_value = ""
                                        newFRAV.save()
                                        rowList.append((rtype[0],'frav',newFRAV.record_value, newFRAV.pk))
                                else:
                                    print >>sys.stderr, aForm.ref_to_parent_form.all().count()
                                    print >>sys.stderr, aForm.pk
                                    for frrt in aForm.ref_to_parent_form.all():
                                        print >>sys.stderr, "" + str(frrt.pk)
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
                            print >> sys.stderr, str(rowList)
                            #Now let's handle the thumbnail bit of business for the query
                            #--If the current form IS a media type already, then use itself to grab the thumbnail URI
                            if aForm.form_type.type == 1:
                                thumbnailURI = aForm.get_thumbnail_type()
                            else:
                                #let's find the first media type in the order but offer a default to "NO PREVIEW" if not found
                                thumbnailURI = staticfiles_storage.url("/static/site-images/no-thumb-missing.png")
                                for record in rowList:            
                                    #if it's a reference
                                    if record[1] == 'frrv' or record[1] == 'frrv-ext':
                                        currentRTYPE = FormRecordReferenceValue.objects.get(pk=int(record[3]))
                                        #if it's not a NoneType reference:
                                        if currentRTYPE.record_reference_type.form_type_reference != None:
                                            #If its a reference to a media type
                                            if currentRTYPE.record_reference_type.form_type_reference.type == 1:
                                                print >> sys.stderr, "WE GOT A MATCH"
                                                #Because a form record reference value is a ManyToMany relationship, we just grab the first one in the list
                                                #TODO this may need to be edited later--because you can't order the selections. I may add another ForeignKey called
                                                #"Thumbnail Reference" which links to a single relation to a form of a media type--this would also
                                                #probably solve the complexity of looping through to grab it as it stands right now
                                                #****WE also have to check for NULL references
                                                if currentRTYPE.record_reference.all().count() > 0:
                                                    thumbnailURI = currentRTYPE.record_reference.all()[0].get_thumbnail_type()
                                                break
                                        
                            #we only want the first 5 values from the final ordered list of attributes
                            #rowList = rowList[0:5]


                            formList.append([thumbnailURI,str(aForm.pk), aForm, rowList])   
                            
                    form_att_type_list, form_list = form_att_type_list, formList
                    
                    #update our progress bar
                    progressData.jsonString = '{"message":"Packaging Query for User","current_query":"","current_term":"","percent_done":"90","is_complete":"False","stats":'+jsonStats+'}'
                    progressData.save() 
                    
                    finishedJSONquery = {}
                    
                    headerList=[]
                    for rtype in queryRTYPElist:
                        rtypeDict = {}
                        rtypeDict["index"] = rtype[0]
                        rtypeDict["rtype"] = rtype[1]
                        rtypeDict["pk"] = rtype[2]
                        rtypeDict["name"] = rtype[3]
                        headerList.append(rtypeDict)

                    #update our progress bar
                    progressData.jsonString = '{"message":"Packaging Query for User","current_query":"","current_term":"","percent_done":"93","is_complete":"False","stats":'+jsonStats+'}'
                    progressData.save() 
                    
                    finishedJSONquery["rtype_header"] = headerList
                    allFormList = []
                    counter = 0
                    total = len(formList)
                    for form in formList:
                        #update our progress bar
                        counter += 1
                        currentPercent = 93 + int((counter*(5.0/total)))
                        progressData.jsonString = '{"message":"Packaging Query for User","current_query":"","current_term":"","percent_done":"'+str(currentPercent)+'","is_complete":"False","stats":'+jsonStats+'}'
                        progressData.save() 
                        
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

                    
                    finishedJSONquery["form_list"] = allFormList
                    finishedJSONquery["currentQuery"] = request.POST['master_query']
                    finishedJSONquery["totalResultCount"] = paginationTotal
                    finishedJSONquery['formtype'] = query['formtype_label']
                    finishedJSONquery['formtype_pk'] = query['formtype_pk']
                    finishedJSONquery['project'] = query['project_label']
                    finishedJSONquery['project_pk'] = query['project_pk']
                    finishedJSONquery['pagination_form_list'] = paginationFormList
                    finishedJSONquery['query_stats'] = queryStats
                    all_project_queries.append(finishedJSONquery)
                    
            #convert to JSON
            all_project_queries = json.dumps(all_project_queries)

            #Update our progress bar
            progressData.jsonString = '{"message":"Finished!","current_query":"","current_term":"","percent_done":"100","is_complete":"True","stats":''}'
            progressData.save() 
            print >>sys.stderr,  "Timer End"     
            return HttpResponse(all_project_queries, content_type="application/json")

        ERROR_MESSAGE += "Error: You have not submitted through POST"
    else: ERROR_MESSAGE += "Error: You do not have permission to access querying this project"
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")   


#=======================================================#
#   ACCESS LEVEL :  1       RUN_QUERY_ENGINE() *Recycling
#=======================================================#   
def run_query_engine(self, request):
    #***************#
    ACCESS_LEVEL = 1
    #***************#
    
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
    
    #Check our user's session and access level
    if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
    
        if request.method == 'POST':

            #We need to make sure we have permission to deal with the formtype--e.g. it's part of the user's current project
            formtype = FormType.objects.get(pk=request.POST['formtype_id'])
            
            #If the project IDs match, then we're good to go!
            if formtype.project.pk == request.user.permissions.project.pk:
            
                #Make the AJAX Request Data Model for subsequent AJAX calls
                progressData = AJAXRequestData(uuid=request.POST.get('uuid'), jsonString='{"message":"Loading Json","current_query":"","current_term":"","percent_done":"0","is_complete":"False"}')
                progressData.save()
                
                
                
                #create a dictionary to store the query statistics
                queryStats = {}
                queryStats['formtype'] = formtype.form_type_name
                queryStats['formtype_pk'] = formtype.pk
                queryList = []
                queryStats['query_list'] = queryList
                primaryConstraintList = []
                
                
                #First let's setup our header field of ordered labels 
                print >>sys.stderr,  "Timer Start"                
                form_att_type_list = []
                #***RECYCLING BIN*** Make sure our RTYPES are filtered by their deletion flags
                for attType in formtype.formrecordattributetype_set.all().filter(flagged_for_deletion=False).order_by('order_number')[:5]:
                    form_att_type_list.append((attType.order_number,'frat',attType.pk,attType.record_type)) 
         
                #***RECYCLING BIN*** Make sure our RTYPES are filtered by their deletion flags
                for refType in formtype.ref_to_parent_formtype.all().filter(flagged_for_deletion=False).order_by('order_number')[:5]:
                    form_att_type_list.append((refType.order_number,'frrt',refType.pk,refType.record_type)) 

                #sort the new combined reference ad attribute type list combined
                form_att_type_list = sorted(form_att_type_list, key=lambda att: att[0])
                #we only want the first 5 types
                form_att_type_list = form_att_type_list[0:5]
                
                #Finally let's organize all of our reference and attribute values to match their provided order number
                formList = []                
               
                #Setup our inital queryset that includes all forms
                masterQuery = formtype.form_set.all() 
                
                
                #Setup a list to hold the attribute types from the query. We want to show the record types that are part of the search terms,
                #   --rather than the default types that are in order. If there are less than 5 query record types, use the ordered record type list
                #   --until 5 are met.
                queryRTYPElist = []
                uniqueRTYPES = []
                rtypeCounter = 1
                #Load the JSON query from POST
                masterQueryJSON = json.loads(request.POST['query'])
                
                #Update our progressbar to show we're at 10%
                progressData.jsonString = '{"message":"Performing Query","current_query":"","current_term":"","percent_done":"5","is_complete":"False"}'
                progressData.save() 
                
                #Loop through each separate query
                for query in sorted(masterQueryJSON['query_list']):
                    print >>sys.stderr, query
                    #setup a dictionary of key values of the query stats to add to the main querystas dictionary later
                    singleQueryStats = {} 
                    
                    queriedForms = formtype.form_set.all()
                    #***RECYCLING BIN*** Make sure our Forms are filtered by their deletion flags
                    queriedForms.filter(flagged_for_deletion=False)
                    currentJSONQuery = masterQueryJSON['query_list'][query]
                    
                    uniqueQuery = False
                    #Let's not allow any duplicate rtypes in the query rtype list header e.g. we don't want "Object ID" to show up 4 times 
                    #--if the user makes a query that compares it 4 times in 4 separate queries
                    if currentJSONQuery['RTYPE'] not in uniqueRTYPES: 
                        uniqueRTYPES.append(currentJSONQuery['RTYPE'])
                        uniqueQuery = True
                    
                    #We need to check whether or not this query is an AND/OR  or a null,e.g. the first one(so there is no and/or)
                    rtype, rtypePK = currentJSONQuery['RTYPE'].split("-")
                    
                    #store our percentDone variable to update the ajax progress message object
                    percentDone = 0
                    
                    #########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
                    # (FRAT) FormRecordAttributeType Lookups
                    #########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
                    if rtype == 'FRAT':
                        #thisRTYPE = FormRecordAttributeType.objects.get(pk=rtypePK)

                        #store the record type in a new rtype list if unique
                        if uniqueQuery: queryRTYPElist.append((rtypeCounter,'frat',rtypePK,currentJSONQuery['LABEL'])) 
                        rtypeCounter += 1
                        tCounter = 0;
                        #store stats
                        singleQueryStats['rtype_name'] = currentJSONQuery['LABEL']
                        singleQueryStats['rtype_pk'] = rtypePK
                        singleQueryStats['rtype'] = rtype
                        termStats = []
                        singleQueryStats['all_terms'] = termStats
                        logging.info("TimerA"+ " : " + str(time.clock()))
                        for term in currentJSONQuery['TERMS']:
                            #Now begin modifying the SQL query which each term of each individual query
                            #skip the term if the field was left blank
                            if term['TVAL'] != "" or term['QCODE'] == '4':
                                newQuery = None
                                if term['T-ANDOR'] != 'or':#We can assume it is an AND like addition if it's anything but 'or'
                                    #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                    if   term['QCODE'] == '0': newQuery = queriedForms.filter(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#CONTAINS    
                                    elif term['QCODE'] == '1': newQuery = queriedForms.filter(formrecordattributevalue__record_value__icontains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#ICONTAINS                                   
                                    elif term['QCODE'] == '2': newQuery = queriedForms.filter(formrecordattributevalue__record_value__exact=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#MATCHES EXACT                                    
                                    elif term['QCODE'] == '3': newQuery = queriedForms.exclude(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#EXCLUDES                                   
                                    elif term['QCODE'] == '4': newQuery = queriedForms.filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=rtypePK)#IS_NULL        
                                    #save stats and query
                                    term['count'] =  newQuery.count()
                                    termStats.append(term)
                                    queriedForms = newQuery
                                else:#Otherwise it's an OR statement
                                    #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                    if   term['QCODE'] == '0': newQuery = (formtype.form_set.all().filter(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK))#CONTAINS    
                                    elif term['QCODE'] == '1': newQuery = (formtype.form_set.all().filter(formrecordattributevalue__record_value__icontains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK))#ICONTAINS                                   
                                    elif term['QCODE'] == '2': newQuery = (formtype.form_set.all().filter(formrecordattributevalue__record_value__exact=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK))#MATCHES EXACT                                    
                                    elif term['QCODE'] == '3': newQuery = (formtype.form_set.all().exclude(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK))#EXCLUDES                                   
                                    elif term['QCODE'] == '4': newQuery = (formtype.form_set.all().filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=rtypePK))#IS_NULL 
                                    #***RECYCLING BIN*** Make sure our NEW query is always filtered by recycling bin flags--All OR statements will need this filter
                                    newQuery = newQuery.filter(flagged_for_deletion=False)
                                    #save stats and query
                                    term['count'] =  newQuery.count()
                                    termStats.append(term)
                                    queriedForms = (newQuery | queriedForms)
                            logging.info("TimerB"+ " : " + str(time.clock()))
                            #We'll calculate percent by claiming finishing the query is at 50% when complete and at 20% when starting this section.
                            logging.info(rtypeCounter)
                            logging.info(len(masterQueryJSON['query_list']))
                            Qpercent = ((rtypeCounter-2) * (50.0/len(masterQueryJSON['query_list'])))
                            logging.info(Qpercent)
                            logging.info(len(currentJSONQuery['TERMS']))
                            percentDone =  5 + Qpercent +  (tCounter * (Qpercent / len(currentJSONQuery['TERMS'])) )
                            progressData.jsonString = '{"message":"Performing Query # '+ str(rtypeCounter-1) + ' on term: '+term['TVAL']+'","current_query":"'+ currentJSONQuery['RTYPE'] + '","current_term":"'+term['TVAL']+'","percent_done":"'+ str(int(percentDone)) +'","is_complete":"False"}'
                            progressData.save() 
                            tCounter += 1
                            logging.info("TimerC"+ " : " + str(time.clock()))
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
                        #thisRTYPE = FormRecordReferenceType.objects.get(pk=rtypePK)
                        #store the record type in a new rtype list if unique
                        if uniqueQuery: queryRTYPElist.append((rtypeCounter,'frrt',rtypePK,currentJSONQuery['LABEL'])) 
                        rtypeCounter += 1
                        tCounter = 0;

                        #store stats
                        singleQueryStats['rtype_name'] = currentJSONQuery['LABEL'] + currentJSONQuery['DEEP-LABEL']
                        singleQueryStats['rtype_pk'] = rtypePK
                        singleQueryStats['rtype'] = rtype
                        termStats = []
                        singleQueryStats['all_terms'] = termStats
                        logging.info("TimerD"+ " : " + str(time.clock()))
                        
                        #get the deep values
                        deepRTYPE, deepPK = currentJSONQuery['RTYPE-DEEP'].split('-')
                        
                        for term in currentJSONQuery['TERMS']:
                            #==========================================================================================================================================================================================
                            # IF WE ARE JUST LOOKING UP THE RTYPE FORM ID
                            #==========================================================================================================================================================================================
                            #TODO: This also needs to check external reference values if no match is found
                            if deepRTYPE == 'FORMID':
                                #Now begin modifying the SQL query which each term of each individual query
                                #skip the term if the field was left blank
                                if term['TVAL'] != "" or term['QCODE'] == '4':
                                    newQuery = None
                                    if term['T-ANDOR'] != 'or':#We can assume it is an AND like addition if it's anything but 'or'
                                        #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                        if   term['QCODE'] == '0': newQuery = queriedForms.filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK) #CONTAINS    
                                        elif term['QCODE'] == '1': newQuery = queriedForms.filter(ref_to_parent_form__record_reference__form_name__icontains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK) #ICONTAINS                                   
                                        elif term['QCODE'] == '2': newQuery = queriedForms.filter(ref_to_parent_form__record_reference__form_name__exact=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK)#MATCHES EXACT                                    
                                        elif term['QCODE'] == '3': newQuery = queriedForms.exclude(ref_to_parent_form__record_reference__form_name__contains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK)#EXCLUDES                                   
                                        elif term['QCODE'] == '4': newQuery = queriedForms.filter(ref_to_parent_form__record_reference__isnull=True, ref_to_parent_form__record_reference_type__pk=rtypePK) #IS_NULL        
                                        #save stats and query
                                        term['count'] =  newQuery.count()
                                        termStats.append(term)
                                        queriedForms = newQuery
                                    else:#Otherwise it's an OR statement
                                        #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                        if   term['QCODE'] == '0': newQuery = (formtype.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK))#CONTAINS    
                                        elif term['QCODE'] == '1': newQuery = (formtype.form_set.all().filter(ref_to_parent_form__record_reference__form_name__icontains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK))#ICONTAINS                                   
                                        elif term['QCODE'] == '2': newQuery = (formtype.form_set.all().filter(ref_to_parent_form__record_reference__form_name__exact=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK))#MATCHES EXACT                                    
                                        elif term['QCODE'] == '3': newQuery = (formtype.form_set.all().exclude(ref_to_parent_form__record_reference__form_name__contains=term['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK))#EXCLUDES                                   
                                        elif term['QCODE'] == '4': newQuery = (formtype.form_set.all().filter(ref_to_parent_form__record_reference__isnull=True, ref_to_parent_form__record_reference_type__pk=rtypePK))#IS_NULL 
                                        #***RECYCLING BIN*** Make sure our NEW query is always filtered by recycling bin flags--All OR statements will need this filter
                                        newQuery = newQuery.filter(flagged_for_deletion=False)
                                        #save stats and query
                                        term['count'] =  newQuery.count()
                                        termStats.append(term)
                                        queriedForms = (newQuery | queriedForms)
                            #==========================================================================================================================================================================================
                            # IF WE ARE LOOKING UP THE RELATIONS FRAT
                            #==========================================================================================================================================================================================
                            elif deepRTYPE == 'FRAT':
                                print >>sys.stderr, "We should be here"
                                #grab the formtype in question
                                deepFormType = FormType.objects.filter(pk=FormRecordAttributeType.objects.get(pk=deepPK).form_type.pk)
                                #***RECYCLING BIN*** Make sure our this Deep query FormType is always filtered by recycling bin flags
                                deepFormType = deepFormType.filter(flagged_for_deletion=False)
                                deepFormType = deepFormType[0]
                                #Now begin modifying the SQL query which each term of each individual query
                                #skip the term if the field was left blank
                                if term['TVAL'] != "" or term['QCODE'] == '4':
                                    newQuery = None
                                    #----------------------------------------------------------
                                    # AND STATEMENT FOR A --TERM--
                                    if term['T-ANDOR'] != 'or':#We can assume it is an AND like addition if it's anything but 'or'
                                        #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                        #First we Get a flattened list of form pk values from the deepFormType
                                        #Then we filter our current formtype queryset's frrt manytomany pks by the pk value list just created 
                                        if   term['QCODE'] == '0': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '1': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__icontains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '2': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '3': 
                                            flattenedSet = list(deepFormType.form_set.all().exclude(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '4': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        #save stats and query
                                        term['count'] =  newQuery.count()
                                        termStats.append(term)
                                        queriedForms = newQuery
                                    #--------------------------------------------------------
                                    # OR STATEMENT FOR a --TERM--
                                    else:
                                        #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                        if   term['QCODE'] == '0': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = formtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '1': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__icontains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = formtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '2': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = formtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '3': 
                                            flattenedSet = list(deepFormType.form_set.all().exclude(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = formtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '4': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=deepPK).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = formtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        #***RECYCLING BIN*** Make sure our NEW query is always filtered by recycling bin flags--All OR statements will need this filter
                                        newQuery = newQuery.filter(flagged_for_deletion=False)    
                                        #save stats and query
                                        term['count'] =  newQuery.count()
                                        termStats.append(term)
                                        queriedForms = (newQuery | queriedForms)                            
                            #==========================================================================================================================================================================================
                            # IF WE ARE LOOKING UP THE RELATION'S FRRT(Only form ID allowed)
                            #==========================================================================================================================================================================================
                            elif deepRTYPE == 'FRRT':
                                print >>sys.stderr, "We should be here 3"
                                #grab the formtype in question
                                deepFormType = FormType.objects.filter(pk=FormRecordReferenceType.objects.get(pk=deepPK).form_type_parent.pk)
                                #***RECYCLING BIN*** Make sure our this Deep query FormType is always filtered by recycling bin flags
                                deepFormType = deepFormType.filter(flagged_for_deletion=False)
                                deepFormType = deepFormType[0]
                                #Now begin modifying the SQL query which each term of each individual query
                                #skip the term if the field was left blank
                                if term['TVAL'] != "" or term['QCODE'] == '4':
                                    newQuery = None
                                    #----------------------------------------------------------
                                    # AND STATEMENT FOR A --TERM--
                                    if term['T-ANDOR'] != 'or':#We can assume it is an AND like addition if it's anything but 'or'
                                        #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                        #First we Get a flattened list of form pk values from the deepFormType
                                        #Then we filter our current formtype queryset's frrt manytomany pks by the pk value list just created 
                                        if   term['QCODE'] == '0': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #CONTAINS 
                                            print >>sys.stderr, "LOOK HERE ROBERT"
                                            print >>sys.stderr, flattenedSet
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '1': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #ICONTAINS    
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '2': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #EXACT MATCH
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '3': 
                                            flattenedSet = list(deepFormType.form_set.all().exclude(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #EXCLUDES   
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '4': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__isnull=True).values_list('pk', flat=True)) #IS NULL  
                                            newQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                               
                                        #save stats and query
                                        term['count'] =  newQuery.count()
                                        termStats.append(term)
                                        queriedForms = newQuery
                                    #--------------------------------------------------------
                                    # OR STATEMENT FOR a --TERM--
                                    else:
                                        #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                        if   term['QCODE'] == '0': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #CONTAINS    
                                            newQuery = formtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '1': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #ICONTAINS    
                                            newQuery = formtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '2': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #EXACT MATCH
                                            newQuery = formtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '3': 
                                            flattenedSet = list(deepFormType.form_set.all().exclude(ref_to_parent_form__record_reference__form_name__contains=term['TVAL']).values_list('pk', flat=True)) #EXCLUDES 
                                            newQuery = formtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif term['QCODE'] == '4': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__isnull=True).values_list('pk', flat=True)) #IS NULL
                                            newQuery = formtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        #***RECYCLING BIN*** Make sure our NEW query is always filtered by recycling bin flags--All OR statements will need this filter
                                        newQuery = newQuery.filter(flagged_for_deletion=False)    
                                        #save stats and query
                                        term['count'] =  newQuery.count()
                                        termStats.append(term)
                                        queriedForms = (newQuery | queriedForms)            
                            #We'll calculate percent by claiming finishing the query is at 50% when complete and at 20% when starting this section.
                            Qpercent = ((rtypeCounter-2) * (50.0/len(masterQueryJSON['query_list'])))        
                            percentDone =  5 + Qpercent +  (tCounter * (Qpercent / len(currentJSONQuery['TERMS'])) )
                            progressData.jsonString = '{"message":"Performing Query # '+ str(rtypeCounter-1) + ' on term: '+term['TVAL']+'","current_query":"'+ currentJSONQuery['RTYPE'] + '","current_term":"'+term['TVAL']+'","percent_done":"'+ str(percentDone) +'","is_complete":"False"}'
                            progressData.save() 
                            tCounter += 1
                    #########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
                    # (Form ID) Lookups
                    #########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&########################################&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
                    elif rtype == "FORMID":
                        tCounter = 0;
                        #store stats
                        singleQueryStats['rtype_name'] = currentJSONQuery['LABEL']
                        singleQueryStats['rtype_pk'] = rtypePK
                        singleQueryStats['rtype'] = rtype
                        termStats = []
                        singleQueryStats['all_terms'] = termStats
                        logging.info("TimerD"+ " : " + str(time.clock()))
                        for term in currentJSONQuery['TERMS']:
                            #Now begin modifying the SQL query which each term of each individual query
                            #skip the term if the field was left blank
                            if term['TVAL'] != "" or term['QCODE'] == '4':
                                newQuery = None
                                print >>sys.stderr, str(formtype.form_set.all().filter(form_name__contains=term['TVAL']))
                                if term['T-ANDOR'] != 'or':#We can assume it is an AND like addition if it's anything but 'or'
                                    print >> sys.stderr, "Is it working?"
                                    #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                    if   term['QCODE'] == '0': newQuery = queriedForms.filter(form_name__contains=term['TVAL']) #CONTAINS    
                                    elif term['QCODE'] == '1': newQuery = queriedForms.filter(form_name__icontains=term['TVAL']) #ICONTAINS                                   
                                    elif term['QCODE'] == '2': newQuery = queriedForms.filter(form_name__exact=term['TVAL'])#MATCHES EXACT                                    
                                    elif term['QCODE'] == '3': newQuery = queriedForms.exclude(form_name__contains=term['TVAL'])#EXCLUDES                                   
                                    elif term['QCODE'] == '4': newQuery = queriedForms.filter(form_name__isnull=True) #IS_NULL        
                                    #save stats and query
                                    term['count'] =  newQuery.count()
                                    termStats.append(term)
                                    queriedForms = newQuery
                                else:#Otherwise it's an OR statement
                                    #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                    if   term['QCODE'] == '0': newQuery = (formtype.form_set.all().filter(form_name__contains=term['TVAL']))#CONTAINS    
                                    elif term['QCODE'] == '1': newQuery = (formtype.form_set.all().filter(form_name__icontains=term['TVAL']))#ICONTAINS                                   
                                    elif term['QCODE'] == '2': newQuery = (formtype.form_set.all().filter(form_name__exact=term['TVAL']))#MATCHES EXACT                                    
                                    elif term['QCODE'] == '3': newQuery = (formtype.form_set.all().exclude(form_name__contains=term['TVAL']))#EXCLUDES                                   
                                    elif term['QCODE'] == '4': newQuery = (formtype.form_set.all().filter(form_name__isnull=True))#IS_NULL 
                                    #***RECYCLING BIN*** Make sure our NEW query is always filtered by recycling bin flags--All OR statements will need this filter
                                    newQuery = newQuery.filter(flagged_for_deletion=False)    
                                    #save stats and query
                                    term['count'] =  newQuery.count()
                                    termStats.append(term)
                                    queriedForms = (newQuery | queriedForms)
                            #We'll calculate percent by claiming finishing the query is at 50% when complete and at 20% when starting this section.
                            Qpercent = ((rtypeCounter-2) * (50.0/len(masterQueryJSON['query_list'])))        
                            percentDone =  5 + Qpercent +  (tCounter * (Qpercent / len(currentJSONQuery['TERMS'])) )
                            progressData.jsonString = '{"message":"Performing Query # '+ str(rtypeCounter-1) + ' on term: '+term['TVAL']+'","current_query":"'+ currentJSONQuery['RTYPE'] + '","current_term":"'+term['TVAL']+'","percent_done":"'+ str(percentDone) +'","is_complete":"False"}'
                            progressData.save() 
                            tCounter += 1
                
                            
                    
                    logging.info("Timer1"+ " : " + str(time.clock()))
                    #add stats to the query stats
                    singleQueryStats['ANDOR'] = currentJSONQuery['Q-ANDOR']
                    singleQueryStats['count'] = queriedForms.count()
                    logging.info("Timer3"+ " : " + str(time.clock()))
                    queryList.append(singleQueryStats)
                    #If this is an AND query--attach it to the masterQuery as so.
                    if currentJSONQuery['Q-ANDOR'] == 'and': 
                        logging.info("TimerR"+ " : " + str(time.clock()))
                        masterQuery = (masterQuery & queriedForms)
                        singleQueryStats['intersections'] = masterQuery.count()
                        #if this is the last query--go ahead and grab this count for the aggregate query--this helps up from doing another redundant time-consuming masterQuery.count() later
                        if rtypeCounter-1 == len(masterQueryJSON['query_list']): queryStats['count'] = singleQueryStats['intersections']
                        logging.info("TimerU"+ " : " + str(time.clock()) + " : " + str(singleQueryStats['intersections']))
                    #If it's an OR query, attach it to the masterQuery as an OR statement
                    elif currentJSONQuery['Q-ANDOR'] == 'or': 
                        logging.info("TimerX"+ " : " + str(time.clock()))
                        masterQuery = (masterQuery | queriedForms)
                        singleQueryStats['additions'] = masterQuery.count()
                        #if this is the last query--go ahead and grab this count for the aggregate query--this helps up from doing another redundant time-consuming masterQuery.count() later
                        if rtypeCounter-1 == len(masterQueryJSON['query_list']): queryStats['count'] = singleQueryStats['additions']
                        logging.info("TimerZZ"+ " : " + str(time.clock()))
                    #Otherwise its the first, or a single query and should simply replace the masterQuery
                    #also set the count to this first query so we have one in case there is only one query
                    else: 
                        print >> sys.stderr, "Master Query assignment??"
                        masterQuery = queriedForms;
                        queryStats['count'] = singleQueryStats['count']
                    logging.info("TimerF"+ " : " + str(time.clock()))
                   
                    #--------------------------------------------------------------------------------------------------------------------
                    #   CONSTRAINTS
                    #
                    #Let's add a count for our constraints and some information about the constraints
                    #These are just used to flesh out more information for graphs, and don't produce queried results
                    #--Doing it this way will improve the speed of queries significantly, as we don't NEED to get individual database
                    #--record information for each query--just count()'s  -- These will all essentially be 'AND' statements for the query
                    #--!!!Make sure we are using this specific query's queryset and not the amalgamated masterQuery--otherwise each constraint will be affected
                    constraints = []
                    singleQueryStats['constraints'] = constraints
                    counter = 0
                    total = len(masterQueryJSON['constraint_list'])
                    for aConstraint in masterQueryJSON['constraint_list']:
                        print >>sys.stderr, aConstraint
                        logging.info("TimerY START" + " : " + str(time.clock()))
                        constraint = masterQueryJSON['constraint_list'][aConstraint]
                        #Send our progresss update message
                        counter += 1
                        constraintPercentDone = int(percentDone + (counter *(5.0/total)))
                        progressData.jsonString = '{"message":"Performing Query # '+ str(rtypeCounter-1) + ' on constraint: '+constraint['LABEL']+ ' : ' + constraint['TVAL'] +'","current_query":"'+ currentJSONQuery['RTYPE'] + '","current_term":"'+str(percentDone)+'","percent_done":"'+ str(constraintPercentDone) +'","is_complete":"False"}'
                        progressData.save() 
 
                        singleConstraintStat = {}
                        #Only check if the entry box was filled in--if it's blank then do nothing and ignore it
                        if constraint['TVAL'] != "" or constraint['QCODE'] == '4': 
                            #Check whether or not it's a frat or frrt
                            #We don't use an 'else' statement because I want to make sure that if someone edits the json before
                            #sending, that it will do nothing if it doesn't get the proper code
                            rtype, rtypePK = constraint['RTYPE'].split("-")
                            if rtype == 'FRAT':
                                logging.info("TimerZ START" + " : " + str(time.clock()))
                                if   constraint['QCODE'] == '0': constraintQuery = queriedForms.filter(pk__in=list(formtype.form_set.all().filter(formrecordattributevalue__record_value__contains=constraint['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK).values_list('pk', flat=True)))
                                #if   constraint['QCODE'] == '0': constraintQuery = (queriedForms & formtype.form_set.all().filter(formrecordattributevalue__record_value__contains=constraint['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)).count()#CONTAINS  
                                #if   constraint['QCODE'] == '0': constraintQuery = queriedForms.filter(formrecordattributevalue__record_value__contains=constraint['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK).count()#CONTAINS    
                                elif constraint['QCODE'] == '1': constraintQuery = queriedForms.filter(formrecordattributevalue__record_value__icontains=constraint['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#ICONTAINS                                   
                                elif constraint['QCODE'] == '2': constraintQuery = queriedForms.filter(formrecordattributevalue__record_value__exact=constraint['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#MATCHES EXACT                                    
                                elif constraint['QCODE'] == '3': constraintQuery = queriedForms.exclude(formrecordattributevalue__record_value__icontains=constraint['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#EXCLUDES                                   
                                elif constraint['QCODE'] == '4': constraintQuery = queriedForms.filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=rtypePK)#IS_NULL       
                                logging.info("TimerZ END" + "-- : " + str(time.clock()))  
                            elif rtype == 'FORMID':
                                if   constraint['QCODE'] == '0': constraintQuery = queriedForms.filter(form_name__contains=constraint['TVAL']) #CONTAINS    
                                elif constraint['QCODE'] == '1': constraintQuery = queriedForms.filter(form_name__icontains=constraint['TVAL']) #ICONTAINS                                   
                                elif constraint['QCODE'] == '2': constraintQuery = queriedForms.filter(form_name__exact=constraint['TVAL'])#MATCHES EXACT                                    
                                elif constraint['QCODE'] == '3': constraintQuery = queriedForms.exclude(form_name__contains=constraint['TVAL'])#EXCLUDES                                   
                                elif constraint['QCODE'] == '4': constraintQuery = queriedForms.filter(form_name__isnull=True) #IS_NULL          
                            elif rtype == 'FRRT_ID':
                                deepFormType = FormType.objects.filter(pk=FormRecordReferenceType.objects.get(pk=rtypePK).form_type_parent.pk)
                                #***RECYCLING BIN*** Make sure our this Deep query FormType is always filtered by recycling bin flags
                                deepFormType = deepFormType.filter(flagged_for_deletion=False)
                                deepFormType = deepFormType[0]
                                if   constraint['QCODE'] == '0': constraintQuery = queriedForms.filter(ref_to_parent_form__record_reference__form_name__contains=constraint['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK)#CONTAINS    
                                elif constraint['QCODE'] == '1': constraintQuery = queriedForms.filter(ref_to_parent_form__record_reference__form_name__icontains=constraint['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK)#ICONTAINS                                   
                                elif constraint['QCODE'] == '2': constraintQuery = queriedForms.filter(ref_to_parent_form__record_reference__form_name__exact=constraint['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK)#MATCHES EXACT                                    
                                elif constraint['QCODE'] == '3': constraintQuery = queriedForms.exclude(ref_to_parent_form__record_reference__form_name__icontains=constraint['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK)#EXCLUDES                                   
                                elif constraint['QCODE'] == '4': constraintQuery = queriedForms.filter(ref_to_parent_form__record_reference__isnull=True, ref_to_parent_form__record_reference_type__pk=rtypePK).count()#IS_NULL                                           
                            elif rtype == 'DEEP_FRRT':
                                deepFormType = FormType.objects.filter(pk=FormRecordReferenceType.objects.get(pk=rtypePK).form_type_parent.pk)
                                #***RECYCLING BIN*** Make sure our this Deep query FormType is always filtered by recycling bin flags
                                deepFormType = deepFormType.filter(flagged_for_deletion=False)
                                deepFormType = deepFormType[0]                                
                                if   constraint['QCODE'] == '0': 
                                    flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=constraint['TVAL']).values_list('pk', flat=True)) #ICONTAINS    
                                    constraintQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet) 
                                elif constraint['QCODE'] == '1':
                                    flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__icontains=constraint['TVAL']).values_list('pk', flat=True)) #ICONTAINS    
                                    constraintQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)                                    
                                elif constraint['QCODE'] == '2': 
                                    flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__exact=constraint['TVAL']).values_list('pk', flat=True)) #ICONTAINS    
                                    constraintQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet) 
                                elif constraint['QCODE'] == '3':
                                    flattenedSet = list(deepFormType.form_set.all().exclude(ref_to_parent_form__record_reference__form_name__contains=constraint['TVAL']).values_list('pk', flat=True)) #ICONTAINS    
                                    constraintQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                elif constraint['QCODE'] == '4': 
                                    flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__isnull=True).values_list('pk', flat=True)) #ICONTAINS    
                                    constraintQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet) 
                            elif rtype == 'DEEP_FRAT':
                                deepFormType = FormType.objects.filter(pk=FormRecordAttributeType.objects.get(pk=rtypePK).form_type.pk)
                                #***RECYCLING BIN*** Make sure our this Deep query FormType is always filtered by recycling bin flags
                                deepFormType = deepFormType.filter(flagged_for_deletion=False)
                                
                                deepFormType = deepFormType[0]   
                                print >>sys.stderr, deepFormType
                                print >>sys.stderr, rtypePK
                                if   constraint['QCODE'] == '0':
                                    flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__contains=constraint['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK).values_list('pk', flat=True)) #CONTAINS    
                                    constraintQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                elif constraint['QCODE'] == '1':
                                    flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__icontains=constraint['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK).values_list('pk', flat=True)) #CONTAINS    
                                    print >>sys.stderr, "WHAT?!?!?!?!  " + str(len(flattenedSet)) + "   <!--------------------------------------------------"
                                    print >>sys.stderr, flattenedSet
                                    constraintQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                elif constraint['QCODE'] == '2':
                                    flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__exact=constraint['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK).values_list('pk', flat=True)) #CONTAINS    
                                    constraintQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                elif constraint['QCODE'] == '3': 
                                    flattenedSet = list(deepFormType.form_set.all().exclude(formrecordattributevalue__record_value__contains=constraint['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK).values_list('pk', flat=True)) #CONTAINS    
                                    constraintQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                elif constraint['QCODE'] == '4': 
                                    flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=rtypePK).values_list('pk', flat=True)) #CONTAINS    
                                    constraintQuery = queriedForms.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                           
                           #***RECYCLING BIN*** Make sure our NEW Constraints query is always filtered by recycling bin flags
                            constraintQuery = constraintQuery.filter(flagged_for_deletion=False)                                    
                            singleConstraintStat['count'] = constraintQuery.count()
                            singleConstraintStat['name'] = constraint['LABEL']
                            singleConstraintStat['rtype_pk'] = rtypePK
                            singleConstraintStat['rtype'] = rtype
                            singleConstraintStat['qcode'] = constraint['QCODE']
                            singleConstraintStat['tval'] = constraint['TVAL']
                            constraints.append(singleConstraintStat)

                        logging.info("TimerY END" + "-- : " + str(time.clock()))
                        #--------------------------------------------------------------------------------------------------------------------
                        #   PRIMARY CONSTRAINTS
                        #
                        #Let's add a count for our primary constraints and some information about them
                        #These are just used to flesh out more information for graphs, and don't produce queried results
                        #--Doing it this way will improve the speed of queries significantly, as we don't NEED to get individual database
                        #--record information for each query--just count()'s  -- These will all essentially be 'AND' statements for the query
                        #--!!!Make sure we are using this specific query's queryset and not the amalgamated masterQuery--otherwise each constraint will be affected
                        #--This also differs from a normal constraint in that a Primary constraint is seen as another dimensional control over the results.
                        #--This runs within each CONSTRAINT LOOP
                        pCounter = 0
                        if 'primary_constraints' in masterQueryJSON:
                            for aPrimaryConstraint in masterQueryJSON['primary_constraints']:
                                
                                pConstraint = masterQueryJSON['primary_constraints'][aPrimaryConstraint]
                                #Only set up and initialize the dictionary for the first loop through the contraints--we won't need them for successive primary constraint loops--they're the same.
                                #We'll rely on indexing at that point to fill out the data[] array for the constraints
                                if len(primaryConstraintList) < len(masterQueryJSON['primary_constraints']):
                                    print >>sys.stderr, "NEW PRIMARY CONSTRAINT"
                                    newPConstraint = {}
                                    currentDataList = []
                                    newPConstraint['name'] = pConstraint['LABEL']
                                    newPConstraint['qcode'] = pConstraint['QCODE']
                                    newPConstraint['tval'] = pConstraint['TVAL']
                                    newPConstraint['data'] = currentDataList
                                    primaryConstraintList.append(newPConstraint)
                                else:
                                    print >>sys.stderr, "OLD PRIMARY CONSTRAINT:   "+ str(counter) + " : " + str(pCounter) + str(primaryConstraintList)
                                    currentPConstraint = primaryConstraintList[pCounter]
                                    currentDataList = currentPConstraint['data']
                                    
                                #Only check if the entry box was filled in--if it's blank then do nothing and ignore it
                                if pConstraint['TVAL'] != "" or pConstraint['QCODE'] == '4': 
                                    #Check whether or not it's a frat or frrt
                                    #We don't use an 'else' statement because I want to make sure that if someone edits the json before
                                    #sending, that it will do nothing if it doesn't get the proper code
                                    rtype, rtypePK = pConstraint['RTYPE'].split("-")
                                    if rtype == 'FRAT':
                                        logging.info("TimerKK START" + " : " + str(time.clock()))
                                        if   pConstraint['QCODE'] == '0': primaryConstraintQuery = constraintQuery.filter(pk__in=list(formtype.form_set.all().filter(formrecordattributevalue__record_value__contains=pConstraint['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK).values_list('pk', flat=True)))
                                        elif pConstraint['QCODE'] == '1': primaryConstraintQuery = constraintQuery.filter(formrecordattributevalue__record_value__icontains=pConstraint['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#ICONTAINS                                   
                                        elif pConstraint['QCODE'] == '2': primaryConstraintQuery = constraintQuery.filter(formrecordattributevalue__record_value__exact=pConstraint['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#MATCHES EXACT                                    
                                        elif pConstraint['QCODE'] == '3': primaryConstraintQuery = constraintQuery.exclude(formrecordattributevalue__record_value__icontains=pConstraint['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#EXCLUDES                                   
                                        elif pConstraint['QCODE'] == '4': primaryConstraintQuery = constraintQuery.filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=rtypePK)#IS_NULL      
                                    elif rtype == 'FRRT':
                                        if   pConstraint['QCODE'] == '0': primaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__form_name__contains=pConstraint['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK)#CONTAINS    
                                        elif pConstraint['QCODE'] == '1': primaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__form_name__icontains=pConstraint['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK)#ICONTAINS                                   
                                        elif pConstraint['QCODE'] == '2': primaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__form_name__exact=pConstraint['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK)#MATCHES EXACT                                    
                                        elif pConstraint['QCODE'] == '3': primaryConstraintQuery = constraintQuery.exclude(ref_to_parent_form__record_reference__form_name__icontains=pConstraint['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK)#EXCLUDES                                   
                                        elif pConstraint['QCODE'] == '4': primaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__isnull=True, ref_to_parent_form__record_reference_type__pk=rtypePK)#IS_NULL                                                
                                        logging.info("TimerKK END" + "-- : " + str(time.clock()))
                                    elif rtype == 'FORMID':
                                        if   pConstraint['QCODE'] == '0': primaryConstraintQuery = constraintQuery.filter(form_name__contains=pConstraint['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK) #CONTAINS    
                                        elif pConstraint['QCODE'] == '1': primaryConstraintQuery = constraintQuery.filter(form_name__icontains=pConstraint['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK) #ICONTAINS                                   
                                        elif pConstraint['QCODE'] == '2': primaryConstraintQuery = constraintQuery.filter(form_name__exact=pConstraint['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK)#MATCHES EXACT                                    
                                        elif pConstraint['QCODE'] == '3': primaryConstraintQuery = constraintQuery.exclude(form_name__contains=pConstraint['TVAL'], ref_to_parent_form__record_reference_type__pk=rtypePK)#EXCLUDES                                   
                                        elif pConstraint['QCODE'] == '4': primaryConstraintQuery = constraintQuery.filter(form_name__isnull=True, ref_to_parent_form__record_reference_type__pk=rtypePK) #IS_NULL                                      
                                    elif rtype == 'DEEP_FRRT':
                                        deepFormType = FormType.objects.filter(pk=FormRecordReferenceType.objects.get(pk=rtypePK).form_type_parent.pk)
                                        #***RECYCLING BIN*** Make sure our this Deep query FormType is always filtered by recycling bin flags
                                        deepFormType = deepFormType.filter(flagged_for_deletion=False)
                                        deepFormType = deepFormType[0]                                
                                        if   pConstraint['QCODE'] == '0': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__contains=pConstraint['TVAL']).values_list('pk', flat=True)) #ICONTAINS    
                                            primaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet) 
                                        elif pConstraint['QCODE'] == '1':
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__icontains=pConstraint['TVAL']).values_list('pk', flat=True)) #ICONTAINS    
                                            primaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)                                    
                                        elif pConstraint['QCODE'] == '2': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__exact=pConstraint['TVAL']).values_list('pk', flat=True)) #ICONTAINS    
                                            primaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet) 
                                        elif pConstraint['QCODE'] == '3':
                                            flattenedSet = list(deepFormType.form_set.all().exclude(ref_to_parent_form__record_reference__form_name__contains=pConstraint['TVAL']).values_list('pk', flat=True)) #ICONTAINS    
                                            primaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif pConstraint['QCODE'] == '4': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(ref_to_parent_form__record_reference__form_name__isnull=True).values_list('pk', flat=True)) #ICONTAINS    
                                            primaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet) 
                                    elif rtype == 'DEEP_FRAT':
                                        deepFormType = FormType.objects.filter(pk=FormRecordAttributeType.objects.get(pk=rtypePK).form_type.pk)
                                        #***RECYCLING BIN*** Make sure our this Deep query FormType is always filtered by recycling bin flags
                                        deepFormType = deepFormType.filter(flagged_for_deletion=False)
                                        
                                        deepFormType = deepFormType[0]   
                                        print >>sys.stderr, deepFormType
                                        print >>sys.stderr, rtypePK
                                        if   pConstraint['QCODE'] == '0':
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__contains=pConstraint['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK).values_list('pk', flat=True)) #CONTAINS    
                                            primaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif pConstraint['QCODE'] == '1':
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__icontains=pConstraint['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK).values_list('pk', flat=True)) #CONTAINS    
                                            print >>sys.stderr, "WHAT?!?!?!?!  " + str(len(flattenedSet)) + "   <!--------------------------------------------------"
                                            print >>sys.stderr, flattenedSet
                                            primaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif pConstraint['QCODE'] == '2':
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__exact=pConstraint['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK).values_list('pk', flat=True)) #CONTAINS    
                                            primaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif pConstraint['QCODE'] == '3': 
                                            flattenedSet = list(deepFormType.form_set.all().exclude(formrecordattributevalue__record_value__contains=pConstraint['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK).values_list('pk', flat=True)) #CONTAINS    
                                            primaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                        elif pConstraint['QCODE'] == '4': 
                                            flattenedSet = list(deepFormType.form_set.all().filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=rtypePK).values_list('pk', flat=True)) #CONTAINS    
                                            primaryConstraintQuery = constraintQuery.filter(ref_to_parent_form__record_reference__pk__in=flattenedSet)
                                    #***RECYCLING BIN*** Make sure our NEW Constraints query is always filtered by recycling bin flags
                                    primaryConstraintQuery = primaryConstraintQuery.filter(flagged_for_deletion=False)     
                                    newPData = {}
                                    newPData['data_label'] = singleConstraintStat['name'] + ' ' + singleConstraintStat['tval'] +' - ' + singleQueryStats['rtype_name'] + ' ' + singleQueryStats['all_terms'][0]['TVAL']
                                    newPData['group'] = counter
                                    newPData['count'] = primaryConstraintQuery.count()
                                    currentDataList.append(newPData)
                                pCounter += 1    
                    logging.info("TimerG"+ " : " + str(time.clock()))
                    
                #Add any constraints if they exist
                if len(primaryConstraintList) != 0:    
                    queryStats['p_constraints'] = primaryConstraintList   
                
                #print >>sys.stderr, str(masterQuery)                
                #Now make sure our final queried list has distint values--merging querysets has a tendency to create duplicates
                masterQuery = masterQuery.distinct()
                #***RECYCLING BIN*** A Final redundant recycling bin filter--just to be safe
                masterQuery = masterQuery.filter(flagged_for_deletion=False)
                
                
                #print >>sys.stderr, str(masterQuery)
                
                #Send a message to our AJAX request object
                progressData.jsonString = '{"message":"Running raw SQL","current_query":"","current_term":"''","percent_done":"50","is_complete":"False"}'
                progressData.save()                 
               
               
                jsonStats = json.dumps(queryStats)
                #Send a message to our AJAX request object
                progressData.jsonString = '{"message":"Loading Queried Forms & Sending generated stats now...","current_query":"","current_term":"''","percent_done":"60","is_complete":"False","stats":'+jsonStats+'}'
                progressData.save()                    

               

                #We need to check the # of rtypes in our header list now--if it's less than 5, then let's add from the ordered list
                #We also need to make sure we aren't adding duplicates of the RTYPES, e.g. if we're looking for a match under "Object Number" and Object Number is already
                #--in our sorted order-num list--let's not re-add it.
                for attType in form_att_type_list:
                    print >>sys.stderr, "AttTypeList:  " + str(attType)
                    matchfound = False;
                    for queryAttType in queryRTYPElist:
                        if attType[2] == queryAttType[2]:
                            matchfound = True
                    if matchfound == False and len(queryRTYPElist) < 5:    
                        #let's arbitrarily add '100' to the order number so that our queries are definitely in front of these
                        queryRTYPElist.append((attType[0] + 100,attType[1],attType[2],attType[3]))
                        
                for q in queryRTYPElist:
                    print >>sys.stderr, "QTypeList:  " + str(q)


                
                #serializeTest = serializers.serialize("json", masterQuery)         
                queryCounter = 0
                logging.info("TEST A")
                total = queryStats['count']
                paginationTotal = total
                logging.info("TEST A END")
                
                # print >>sys.stderr, str(masterQuery)
                
                
                #-----------------------------------------------------------------------------------------------------------
                # Here we need to determine whether or not the form type being queried is hierchical.
                #   --If it is hierachical, then we just organize the masterQuery and sort it with the hierachy in mind
                #   --as well as with its hierchical labels--otherwise just perform a normal sort by its label
                if formtype.is_hierarchical:
                    global hierarchyFormList
                    hierarchyFormList = []
                    #Finally let's organize all of our reference and attribute values to match their provided order number
                    #We want to find all the forms that have no parent element first--these are the top of the nodes
                    #Then we'll organize the forms by hierarchy--which can then be put through the normal ordered query
                    masterQuery =  masterQuery.filter(hierarchy_parent=None).exclude(form_number=None, form_name=None)[:25]
                    #CACHE -- this caches the query for the loop
                    if masterQuery:
                        for aForm in masterQuery: 
                            
                            queryCounter += 1
                            Qpercent = ( queryCounter * (30/(total*1.0)))
                            finalPercent = (60 + int(Qpercent))
                            progressData.jsonString = '{"SQL":"True","message":"Loading Queried Forms!","current_query":"'+ str(queryCounter) +'","current_term":"'+ str(total) +'","percent_done":"' + str(finalPercent) + '","is_complete":"False","stats":'+jsonStats+'}'
                            progressData.save()
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
                    masterQuery = masterQuery.order_by('sort_index')[:25]
                    
                    
                #print >>sys.stderr, masterQuery  
                #CACHE -- This cache's the query before looping through it
                if masterQuery:
                    for aForm in masterQuery:
                        queryCounter += 1
                        Qpercent = ( queryCounter * (30/(total*1.0)))
                        finalPercent = (60 + int(Qpercent))
                        progressData.jsonString = '{"SQL":"True","message":"Loading Queried Forms!","current_query":"'+ str(queryCounter) +'","current_term":"'+ str(total) +'","percent_done":"' + str(finalPercent) + '","is_complete":"False","stats":'+jsonStats+'}'
                        progressData.save()
                        print >>sys.stderr, str(aForm.pk) + ":  <!-- Current Form Pk"
                        rowList = []
                        #Let's loop through each item in the queryRTYPE list and match up the frav's in each queried form so the headers match the form attribute values
                        for rtype in queryRTYPElist:
                            if rtype[1] == 'frat':
                                print >>sys.stderr, str(rtype[2]) + '  ' + str(aForm.formrecordattributevalue_set.all().filter(record_attribute_type__pk=rtype[2]).count())
                                formRVAL = aForm.formrecordattributevalue_set.all().filter(record_attribute_type__pk=rtype[2])
                                #We need to check for NULL FRAV's here. When a user manually creates new forms, they don't always have FRAVS created for them if they leave it blank
                                if formRVAL.exists():
                                    rowList.append((rtype[0],'frav',formRVAL[0].record_value, formRVAL[0].pk))
                                else:
                                    print >>sys.stderr, "Whoops--something happened. There are no RVALS for 'frats' using: " + str(rtype[2])
                                    #If there isn't an RVAL for this RTYPE then make a new one and return it instead
                                    newFRAV = FormRecordAttributeValue()
                                    newFRAV.record_attribute_type = FormRecordAttributeType.objects.get(pk=rtype[2])
                                    newFRAV.form_parent = aForm
                                    newFRAV.project = project
                                    newFRAV.record_value = ""
                                    newFRAV.save()
                                    rowList.append((rtype[0],'frav',newFRAV.record_value, newFRAV.pk))
                            else:
                                print >>sys.stderr, aForm.ref_to_parent_form.all().count()
                                print >>sys.stderr, aForm.pk
                                for frrt in aForm.ref_to_parent_form.all():
                                    print >>sys.stderr, "" + str(frrt.pk)
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
                        print >> sys.stderr, str(rowList)
                        #Now let's handle the thumbnail bit of business for the query
                        #--If the current form IS a media type already, then use itself to grab the thumbnail URI
                        if aForm.form_type.type == 1:
                            thumbnailURI = aForm.get_thumbnail_type()
                        else:
                            #let's find the first media type in the order but offer a default to "NO PREVIEW" if not found
                            thumbnailURI = staticfiles_storage.url("/static/site-images/no-thumb-missing.png")
                            for record in rowList:            
                                #if it's a reference
                                if record[1] == 'frrv' or record[1] == 'frrv-ext':
                                    currentRTYPE = FormRecordReferenceValue.objects.get(pk=int(record[3]))
                                    #if it's not a NoneType reference:
                                    if currentRTYPE.record_reference_type.form_type_reference != None:
                                        #If its a reference to a media type
                                        if currentRTYPE.record_reference_type.form_type_reference.type == 1:
                                            print >> sys.stderr, "WE GOT A MATCH"
                                            #Because a form record reference value is a ManyToMany relationship, we just grab the first one in the list
                                            #TODO this may need to be edited later--because you can't order the selections. I may add another ForeignKey called
                                            #"Thumbnail Reference" which links to a single relation to a form of a media type--this would also
                                            #probably solve the complexity of looping through to grab it as it stands right now
                                            #****WE also have to check for NULL references
                                            if currentRTYPE.record_reference.all().count() > 0:
                                                thumbnailURI = currentRTYPE.record_reference.all()[0].get_thumbnail_type()
                                            break
                                    
                        #we only want the first 5 values from the final ordered list of attributes
                        rowList = rowList[0:5]


                        formList.append([thumbnailURI,str(aForm.pk), aForm, rowList])   
                        
                form_att_type_list, form_list = form_att_type_list, formList
                
                #update our progress bar
                progressData.jsonString = '{"message":"Packaging Query for User","current_query":"","current_term":"","percent_done":"90","is_complete":"False","stats":'+jsonStats+'}'
                progressData.save() 
                
                finishedJSONquery = {}
                
                headerList=[]
                for rtype in queryRTYPElist:
                    rtypeDict = {}
                    rtypeDict["index"] = rtype[0]
                    rtypeDict["rtype"] = rtype[1]
                    rtypeDict["pk"] = rtype[2]
                    rtypeDict["name"] = rtype[3]
                    headerList.append(rtypeDict)

                #update our progress bar
                progressData.jsonString = '{"message":"Packaging Query for User","current_query":"","current_term":"","percent_done":"93","is_complete":"False","stats":'+jsonStats+'}'
                progressData.save() 
                
                finishedJSONquery["rtype_header"] = headerList
                allFormList = []
                counter = 0
                total = len(formList)
                for form in formList:
                    #update our progress bar
                    counter += 1
                    currentPercent = 93 + int((counter*(5.0/total)))
                    progressData.jsonString = '{"message":"Packaging Query for User","current_query":"","current_term":"","percent_done":"'+str(currentPercent)+'","is_complete":"False","stats":'+jsonStats+'}'
                    progressData.save() 
                    
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

                
                finishedJSONquery["form_list"] = allFormList
                finishedJSONquery["formtype"] = formtype.form_type_name
                finishedJSONquery["formtype_pk"] = formtype.pk
                finishedJSONquery["project_pk"] = request.user.permissions.project.pk
                finishedJSONquery["project"] = request.user.permissions.project.name
                finishedJSONquery["currentQuery"] = request.POST['query']
                finishedJSONquery["totalResultCount"] = paginationTotal
                #convert to JSON
                finishedJSONquery = json.dumps(finishedJSONquery)

                #Update our progress bar
                progressData.jsonString = '{"message":"Finished!","current_query":"","current_term":"","percent_done":"100","is_complete":"True","stats":'+jsonStats+'}'
                progressData.save() 
                print >>sys.stderr,  "Timer End"     
                return HttpResponse(finishedJSONquery, content_type="application/json")
            ERROR_MESSAGE += "Error: You don't have permission to access this FormType from another project"
        ERROR_MESSAGE += "Error: You have not submitted through POST"
    else: ERROR_MESSAGE += "Error: You do not have permission to access querying this project"
    #If anything goes wrong in the process, return an error in the json HTTP Response
    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
    return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")   




##==========================================================================================================================    
##==========================================================================================================================    
##==========================================================================================================================    
##  TEMPLATE VIEWS   ****************************************************************************************************
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
    
    
    
    return HttpResponse(render_to_response('public_frontend/blogpost.html', kwargs, RequestContext(request)))  
    
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
        return HttpResponse(render_to_response('public_frontend/project.html', kwargs, RequestContext(request)))    
    else:
        SECURITY_log_security_issues('views.py - ' + str(sys._getframe().f_code.co_name), "PROJECT IS NOT PUBLIC", request.META)
        raise Http404("Project Does Not Exist!")  

    
#=====================================================================================#
#  FORMTYPE()
#=====================================================================================#       
def formtype(request, **kwargs):
    return HttpResponse(render_to_response('public_frontend/formtype.html', kwargs, RequestContext(request)))
#=====================================================================================#
#   FORM()
#=====================================================================================#       
def form(request, **kwargs):
    return HttpResponse(render_to_response('public_frontend/form.html', kwargs, RequestContext(request)))
#=====================================================================================#
#   WEBPAGE()
#=====================================================================================#       
def webpage(request, **kwargs):
    kwargs['webpage'] = Webpage.objects.get(pk=kwargs['webpage_id'], flagged_for_deletion=False) 
    if kwargs['webpage'].project: 
        kwargs['project_override_template'] = "public_frontend/public_base.html"
        kwargs['project'] = kwargs['webpage'].project

    return HttpResponse(render_to_response('public_frontend/webpage.html', kwargs, RequestContext(request)))

     
     
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
    logger.debug(render_to_response('public_frontend/index.html', kwargs, RequestContext(request)))
    return HttpResponse(render_to_response('public_frontend/index.html', kwargs, RequestContext(request)))    

def dev_index(request, **kwargs):
    logger.info("TESTING PROJECT TENANCY")
    logger.info(request)
    logger.debug(render_to_response('public_frontend/dev_index.html', kwargs, RequestContext(request)))
    
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
     return HttpResponse(render_to_response('public_frontend/queryengine.html', kwargs, RequestContext(request)))
#=====================================================================================#
#   GEOENGINE() 
#=====================================================================================#       
def geoengine( request, **kwargs):
     return HttpResponse(render_to_response('public_frontend/geoengine.html', kwargs, RequestContext(request)))

#=====================================================================================#
#   BROWSEENGINE() 
#=====================================================================================#       
def browseengine(request, **kwargs):
     return HttpResponse(render_to_response('public_frontend/browseengine.html', kwargs, RequestContext(request)))

        
#=====================================================================================#
#   FEATURES()
#=====================================================================================#       
def features(request, **kwargs):
     return HttpResponse(render_to_response('public_frontend/tara_features.html', kwargs, RequestContext(request)))

        
#=====================================================================================#
#   HISTORY()
#=====================================================================================#       
def history(request, **kwargs):
     return HttpResponse(render_to_response('public_frontend/tara_history.html', kwargs, RequestContext(request)))

        
#=====================================================================================#
#   DOCUMENTATION()
#=====================================================================================#       
def documentation(request, **kwargs):
     return HttpResponse(render_to_response('public_frontend/tara_documentation.html', kwargs, RequestContext(request)))

        
#=====================================================================================#
#   CONTACT()
#=====================================================================================#       
def contact(request, **kwargs):
     return HttpResponse(render_to_response('public_frontend/tara_contact.html', kwargs, RequestContext(request)))

        
#=====================================================================================#
#   PROJECT_LIST()
#=====================================================================================#       
def project_list(request, **kwargs):
    project_list = FormProject.objects.filter(is_public=True)
    kwargs['project_list'] = project_list
    return HttpResponse(render_to_response('public_frontend/tara_projects.html', kwargs, RequestContext(request)))

                
     
     
     
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
    else: return HttpResponse(render_to_response('api/api_main.html', kwargs, RequestContext(request)))    
    
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
        return HttpResponse(render_to_response('api/api_blogposts.html', kwargs, RequestContext(request)))
    
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
        projects = FormProject.objects.all()[:10]
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
        return HttpResponse(render_to_response('api/api_projects.html', kwargs, RequestContext(request)))
    
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
        formtype = FormType.objects.get(pk=kwargs['formtype_id'])
        serialized = formtype.serialize_to_dictionary()
    except:
        formtypes = FormType.objects.all()[:10]
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
        return HttpResponse(render_to_response('api/api_formtypes.html', kwargs, RequestContext(request)))

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
        return HttpResponse(render_to_response('api/api_forms.html', kwargs, RequestContext(request)))
    
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
        return HttpResponse(render_to_response('api/api_webpages.html', kwargs, RequestContext(request)))
     