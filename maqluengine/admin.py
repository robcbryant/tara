
#################################################################################################################################################################################################################################################################################################################################
#################################################################################################################################################################################################################################################################################################################################
#################################################################################################################################################################################################################################################################################################################################
#                   NEW ADMIN TO REPLACE OLD
#################################################################################################################################################################################################################################################################################################################################
#
#  *This newer Maqlu Admin System is designed/created by Robert Bryant, based on a designed/created Model structure in Django for Dynamic Entity(or model) creation by end-users
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
from django.urls import reverse
from django.utils.safestring import mark_safe    
from django.urls import resolve

from django.utils.functional import cached_property
from django.contrib.admin import AdminSite
from django.http import HttpResponse
from django.urls import re_path, include
from django.views import generic
from django.http import Http404

from django.core.mail import send_mail, EmailMultiAlternatives
from django.utils.crypto import get_random_string
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.html import strip_tags

import copy

from django.contrib.sessions.models import Session
from django.utils import timezone

from time import sleep
from django.contrib.staticfiles.storage import staticfiles_storage
import json

#DEPRECATED AND PROBABLY SAFE TO DELETE  from django.utils.encoding import smart_text

from django.shortcuts import redirect
import random
import time
from django.core import serializers

import uuid

import zipfile
import io
import contextlib


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






#=======================================================================================================================================================================================================================================
#=======================================================================================================================================================================================================================================
#      CUSTOM ADMIN FUNCTIONS -- used by Admin Views
#=======================================================================================================================================================================================================================================
#=======================================================================================================================================================================================================================================                         

##==========================================================================================================================   
## Temporary Experimental Functions ****************************************************************************************
##==========================================================================================================================                      


def remove_all_form_hierarchy_parent_references(formtype):
    for aForm in formtype.form_set.all():
        aForm.hierarchy_parent = None
        aForm.save()


def CheckPostDataForDeletions(post_data):
    #logger.info( post_data)
    if 'delete-form-type' in post_data:
        FormType.objects.get(pk=post_data.get('delete-form-type')).delete()
        return True
    elif 'delete-form-type-group' in post_data:
        #Rather than delete all the form types under the group, we'll loop through them and unattach them so that
        #   when the form type group is deleted they just go to fall under project again. 
        currentFormTypeGroup = FormTypeGroup.objects.get(pk=post_data.get('delete-form-type-group'))
        for aFormType in currentFormTypeGroup.formtype_set.all():
            aFormType.form_type_group = None
            aFormType.save()
        #Now delete the form type group after its children have been removed
        currentFormTypeGroup.delete()
        return True
    elif 'delete-form' in post_data:
        logger.info( "Deleting")
        formToDelete = Form.objects.get(pk=post_data.get('delete-form'))
        formToDelete.delete()
    else:
        return False

def CheckPostDataForUniqueSessionPOSTSubmit(request):
    #Let's do a check to make sure the user didn't hit the refresh button
    #If we don't have a session id stored--then we are definitely okay to submit data--it's the first time
    if 'sessionID' not in request.session:
       request.session['sessionID'] = " "
       return True
    #If we DO have a session ID already stored, then we need to make sure it's a unique value
    #If they don't match--we're good to go. If the user hits the refresh button, it will send the same id already stored in session
    #This won't allow them to submit form data until they hit the 'submit' button again. refreshing will not allow any action, because a new
    #session id is never sent in POST
    elif request.session['sessionID'] != request.POST['sesID']:
        return True
    else:
        return False

           
#TODO: I'm using this class as a workaround in the template. It's passed in the admin view context_instance
#so I can have a bit more control over the template looping--I know this isn't Django's preferred way
#but it works for now.
class Counter(object):
    count = 0
    
    def set_true(self):
        self.count = 1
        return ''
    def set_false(self):
        self.count = 0
        return ''
        
    def increment(self):
        self.count += 1
        return ''
    
    def decrement(self):
        self.count -= 1
        return ''
       
    def reset(self):
        self.count = 0
        return''
     
    def double(self):
        self.count *= 2
        return ''
        


##==========================================================================================================================   
## Security Functions ****************************************************************************************
##========================================================================================================================== 

def SECURITY_log_security_issues(userInfo, viewname, errormessage, META):
    #This just prints some information to the server log about any errors/attempted hacks that need to be flagged
    FLAG = "!!!! SECURITY FLAG !!!!  ===>  "
    try: FLAG += "User: " + str(userInfo.username) + "  - Access Level: " + str(userInfo.permissions.access_level) + "  - in View: " + viewname + "  -- UserIP: " +  str(META.get('HTTP_X_FORWARDED_FOR', '') or META.get('REMOTE_ADDR')) + " - with Message: " + errormessage
    except Exception as inst: FLAG += str(inst) + "  USER INFO NOT FOUND IN SESSION - in View: " + viewname + "  -- UserIP: " +  str(META.get('HTTP_X_FORWARDED_FOR', '') or META.get('REMOTE_ADDR')) +  " - with Message: " + errormessage
    logger.warning(FLAG)
    new_message = SecurityMessage(content=FLAG)
    new_message.save()

def SECURITY_check_project_access(user, projectID):
    #This returns a check to make sure the user's project code and the database item in question's project code
    #   --match. If they don't, it returns False, if they do it returns True.
    #
    #   *All database EDIT/DELETE 's Must go through this check. Although it can normally be done through a simple Django filter
    #   *   --this redundancy helps trigger warnings or send messages
    if user.permissions.project != projectID:
        return False
    else:
        return True
    
def SECURITY_check_user_permissions(requiredLevel, userLevel):
    #There are currently 5 levels of access for a project: 1-5
    #   Level 5: (Admin)            Project-wide permissions. Can freely edit/create/delete any aspect of that specific project
    #                                   \-Admins are the only user who can create new users and edit/delete sensitive project data
    #   Level 4: (Moderator)        Can EDIT/CREATE/DELETE FormTypes, Forms, all RTYPEs, and all RVALS
    #   Level 3: (Power Data-Entry) Can EDIT FormTypes, EDIT/CREATE/DELETE Forms, and all RVALs   
    #   Level 2: (Soft Data-Entry)  Can EDIT/CREATE Forms, and all RVALs
    #   Level 1: (Researcher)       Can only VIEW all data for project--normally projects will have some data set to "private"
    #                                   \-This gives someone privileged access to browse all PUBLIC and PRIVATE flagged data
    #                                   \-without allowing them to change any aspect of the project
    
    #For additional security let's FORCE int() the values--the view requesting the bool should be doing this anyway
    requiredLevel = int(requiredLevel)
    userLevel = int(userLevel)
    
    userIsIntCheckFlag = False
    requiredIsIntCheckFlag = False
    #Let's make sure they are both values between 1 and 5 for an additional level of security
    for level in range(1,6):
        if requiredLevel == level: requiredIsIntCheckFlag = True
        if userLevel == level: userIsIntCheckFlag = True
        
    #If we for ABSOLUTE sure have 2 ints between 1 and 5, then continue        
    if userIsIntCheckFlag == True and requiredIsIntCheckFlag == True:
        #If the user's permission level is AT LEAST the required permission level, then return TRUE, signally it's okay to give access
        if userLevel >= requiredLevel:
            return True        
    #Otherwise the User does NOT have permission to access the View requesting authentication
    return False
        
##==========================================================================================================================   
## Helper Functions ****************************************************************************************
##==========================================================================================================================        
 
def get_api_endpoints():

    #------------------------------------------------------------------------------------------------------------------------------------
    #:::This endpoint returns a JSON list of all urls to the admin endpoints in a key:value json object for admin views to pass to their
    #   --templates, which the javascript functions will access to get dynamic URLS without having to change them later
    #
    #   This endpoint is not project specific so there is no security by project--only the access level of being an admin user
    #------------------------------------------------------------------------------------------------------------------------------------
    #Make a key value list of our URLS and add them by name
    
    jsonData = {}


    # MASTER ADMIN ENDPOINTS
    jsonData['create_project'] = reverse('maqlu_admin:create_project')
    jsonData['delete_project'] = reverse('maqlu_admin:delete_project')
    jsonData['reset_user_password'] = reverse('maqlu_admin:reset_user_password')
    jsonData['create_project_admin'] = reverse('maqlu_admin:create_project_admin')
    jsonData['delete_user'] = reverse('maqlu_admin:delete_user')
    jsonData['edit_security_message'] = reverse('maqlu_admin:edit_security_message')
    jsonData['create_edit_blogpost'] = reverse('maqlu_admin:create_edit_blogpost')
    jsonData['get_admin_blog_post'] = reverse('maqlu_admin:get_admin_blog_post')
    jsonData['delete_admin_post'] = reverse('maqlu_admin:delete_admin_post')
    
    #Recycling Bin Endpoints
    jsonData['load_recycling_bin'] = reverse('maqlu_admin:load_recycling_bin')
    jsonData['restore_formtype'] = reverse('maqlu_admin:restore_form_type')
    jsonData['recycle_formtype'] = reverse('maqlu_admin:recycle_form_type')
    jsonData['delete_formtype'] = reverse('maqlu_admin:delete_form_type')
    jsonData['restore_form'] = reverse('maqlu_admin:restore_form')
    jsonData['recycle_form'] = reverse('maqlu_admin:recycle_form')
    jsonData['delete_form'] = reverse('maqlu_admin:delete_form')
    jsonData['restore_frat'] = reverse('maqlu_admin:restore_frat')
    jsonData['recycle_frat'] = reverse('maqlu_admin:recycle_frat')
    jsonData['delete_frat'] = reverse('maqlu_admin:delete_frat')
    jsonData['restore_frrt'] = reverse('maqlu_admin:restore_frrt')
    jsonData['recycle_frrt'] = reverse('maqlu_admin:recycle_frrt')
    jsonData['delete_frrt'] = reverse('maqlu_admin:delete_frrt')
    jsonData['recycle_webpage'] = reverse('maqlu_admin:recycle_webpage')
    jsonData['delete_user_profile_query'] = reverse('maqlu_admin:delete_user_profile_query')
    
    
    #Create Endpoints
    jsonData['create_form'] = reverse('maqlu_admin:create_new_form')
    jsonData['create_template'] = reverse('maqlu_admin:create_new_form_type_template')
    jsonData['create_formtype'] = reverse('maqlu_admin:create_new_form_type')
    jsonData['create_new_webpage'] = reverse('maqlu_admin:create_new_webpage')
    
    #Edit Endpoints
    jsonData['save_form'] = reverse('maqlu_admin:save_form_changes')
    jsonData['save_project'] = reverse('maqlu_admin:save_project_changes')
    jsonData['save_formtype'] = reverse('maqlu_admin:save_form_type_changes')
    jsonData['save_template'] = 'NOT AVAILABLE'
    jsonData['save_user'] = reverse('maqlu_admin:modify_project_user')
    jsonData['save_query_user'] = reverse('maqlu_admin:save_user_query')
    jsonData['save_forms_bulk'] = reverse('maqlu_admin:bulk_edit_formtype')
    jsonData['edit_menugroup'] = reverse('maqlu_admin:edit_menugroup')
    
    #Importer/Exporter Tools
    jsonData['import_formtype_forms'] = reverse('maqlu_admin:run_form_type_form_importer')
    jsonData['import_formtype'] = reverse('maqlu_admin:run_form_type_importer') 
    jsonData['import_formtype_rtypes'] = reverse('maqlu_admin:run_new_rtype_importer')     
    jsonData['import_geojson_formtype'] = reverse('maqlu_admin:run_geojson_importer')
    jsonData['export_formtype'] = reverse('maqlu_admin:export_formtype')
    jsonData['export_project'] = reverse('maqlu_admin:export_project')

    #Get Endpoints
    jsonData['get_rtypes'] = reverse('maqlu_admin:get_rtypes')
    jsonData['get_projects'] = reverse('maqlu_admin:get_projects')
    jsonData['get_formtypes'] = reverse('maqlu_admin:get_formtypes')
    jsonData['get_deep_rtypes'] = reverse('maqlu_admin:get_deep_rtypes')
    jsonData['get_form_rtypes'] = reverse('maqlu_admin:get_form_rtypes')
    jsonData['get_users'] = reverse('maqlu_admin:get_user_list')
    jsonData['get_formtype_forms'] = reverse('maqlu_admin:get_formtype_form_list')
    jsonData['get_geo_formtypes'] = reverse('maqlu_admin:get_geospatial_formtypes')
    jsonData['get_geo_formtype_layers'] = reverse('maqlu_admin:get_formtype_geospatial_layers')
    jsonData['get_forms_search'] = reverse('maqlu_admin:get_form_search_list')
    jsonData['get_geo_unique_rtype_rvals'] = reverse('maqlu_admin:get_all_unique_rtype_rvals')
    jsonData['get_geo_category_matches'] = reverse('maqlu_admin:get_geo_category_matches')
    jsonData['get_forms_previous_next'] = reverse('maqlu_admin:get_previous_next_forms')
    jsonData['get_geo_quantity_frat_counter_auto'] = reverse('maqlu_admin:get_geo_quantity_frat_counter_auto')
    jsonData['get_geo_numeric_rtypes'] = reverse('maqlu_admin:get_geo_numeric_rtypes')
    jsonData['get_geo_graduated_applied_classes'] = reverse('maqlu_admin:get_geo_graduated_applied_classes')
    jsonData['get_geo_rules_classes'] = reverse('maqlu_admin:get_geo_rules_classes')
    
    
    #Run Various Tools Endpoints
    jsonData['run_formtype_query_engine'] = ""
    jsonData['run_master_query_engine'] = reverse('maqlu_admin:run_master_query_engine')
    jsonData['run_formtype_query_pagination'] = reverse('maqlu_admin:navigate_query_pagination')
    jsonData['run_master_query_pagination'] = reverse('maqlu_admin:navigate_master_query_pagination')
    jsonData['run_check_username_taken'] = reverse('maqlu_admin:username_taken')
    jsonData['run_check_progress'] = reverse('maqlu_admin:check_progress')
    jsonData['run_check_progress_query'] = reverse('maqlu_admin:check_progress_query')
  
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
        entity_type = FormRecordAttributeType.objects.get(pk=entity_pk) 
        distinct_value_list = entity_type.formrecordattributevalue_set.order_by('record_value').distinct().values_list('record_value', flat=True)
        distinct_value_list = list(distinct_value_list)
        logger.info("****** in the main function")
        logger.info(distinct_value_list)
        #Do some last minute cleanup here, like sorting the lists etc.
        distinct_value_list = list(set(distinct_value_list))            
                  
  
    elif code == "DEEP_FRRT":   # We need to get all the unique form IDs of the FRRT's related FRRTs FormType
        #Load our DEEP FRAT
        entity_type = FormRecordReferenceType.objects.get(pk=entity_pk) 
        test_list = entity_type.formrecordreferencevalue_set.values_list('record_reference__form_name', flat=True)
        test_list = list(set(test_list))
        logger.info(test_list)
        #Do some last minute cleanup here, like sorting the lists etc.
        distinct_value_list = test_list   

    elif code == "DEEP_FORMID":     # We need to get all the unique form IDs of the FRRT's related FormType
        entity_type = FormRecordReferenceType.objects.get(pk=entity_pk)
        test_list = entity_type.formrecordreferencevalue_set.values_list('record_reference__form_name', flat=True)
        test_list = list(set(test_list))
        logger.info(test_list)
        #Do some last minute cleanup here, like sorting the lists etc.
        distinct_value_list = test_list   
    elif code == "FORMID":      # We need to get all the unique form IDs of this current FormType
        entity_type = FormType.objects.get(pk=entity_pk)    
        distinct_value_list = entity_type.form_set.order_by('form_name').distinct().values_list('form_name', flat=True)
    elif code == "FRAT":        #We need to get all the unique values of the provided FRAT's RVALs
        entity_type = FormRecordAttributeType.objects.get(pk=entity_pk)    
        distinct_value_list = entity_type.formrecordattributevalue_set.order_by('record_value').distinct().values_list('record_value', flat=True)
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
        entity_type = FormRecordReferenceType.objects.get(pk=entity_pk) 
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
        entity_type = FormRecordAttributeType.objects.get(pk=back_frat_pk) 
        frrt_ref = FormRecordReferenceType.objects.get(pk=frrt_pk) 
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
                    frat_val = ref_val[0].form_parent.formrecordattributevalue_set.filter(record_attribute_type__pk=back_frat_pk)
                    logger.info( ref_val)
                    logger.info( ref_val.count())
                    if ref_val:
                        values = []
                        logger.info( "Working?")
                        for refval in ref_val:
                            values.append(refval.form_parent.formrecordattributevalue_set.filter(record_attribute_type__pk=back_frat_pk)[0].record_value)
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
#       END OF CUSTOM ADMIN FUNCTIONS
#=======================================================================================================================================================================================================================================
#=======================================================================================================================================================================================================================================        

        
        
#=======================================================================================================================================================================================================================================
#=======================================================================================================================================================================================================================================
#       SETUP CUSTOM ADMIN VIEWS
#=======================================================================================================================================================================================================================================
#=======================================================================================================================================================================================================================================
class MyAdminSite(AdminSite):
    def __init__(self, *args, **kwargs):
        super(MyAdminSite, self).__init__(*args, **kwargs)
        self.name = 'maqlu_admin'
        self.app_name = 'admin'
        logger.warning(self.__dict__)
        


    ##==========================================================================================================================   
    ## AJAX ADMIN API ENDPOINTS ************************************************************************************************
    ##==========================================================================================================================

    
    
    #-------------------------------------------------------------------------------------------------------
    # MASTER ADMIN ENDPOINTS    

    #=======================================================#
    #   ACCESS LEVEL :  MASTER     RESET_USER_PASSWORD()
    #=======================================================#        
    def reset_user_password(self, request):
        logger.info( request.POST)
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint generates a random password for the provided user_pk in the POST data and emails that user the new 
        #   password as well as the admin account. The admin can also provice an optional email addres to send it to in POST
        ERROR_MESSAGE = ""
        #Check our user's session and access level  
        if request.user.permissions.master_admin:
            if request.method == 'POST':   
                if 'user_pk' in request.POST:
                    #Construct our Email
                    newpassword = get_random_string(24)
                    theUser = User.objects.get(pk=request.POST['user_pk'])
                    theUser.set_password(newpassword)
                    theUser.save()
                    subject = "TARA Project: " + theUser.first_name + " ("+theUser.username+") Password Reset"
                    message = "<p><b>Hello " + theUser.first_name + " ("+theUser.username+")! Your password reset was successful! Your new password is:</p></b><p> (>  "+newpassword+"  <)</p><p>Make sure to change your password when you re-login!</p>"
                    message += "<p>Good luck and thanks for using our system! Sorry for the inconvenience!</p>"
                    message += "<p>TARA Administrator</p>"
                    message += "<p><b><h2>THIS IS AN AUTOMATED MESSAGE, PLEASE DO NOT REPLY. TARA DOES NOT RECEIVE INCOMING EMAIL</h2></b></p>"
                    client = "admin@tara.museum.upenn.edu"
                    if request.POST['alt_email'] != "": to = request.POST['alt_email']
                    else: to = theUser.email
                    msg = EmailMultiAlternatives(subject, strip_tags(message), client, [to])
                    msg.attach_alternative(message, "text/html")
                    msg.send()
                    return HttpResponse('{"MESSAGE":"SUCCESS", "sent":"YES"}',content_type="application/json")  
                else: ERROR_MESSAGE += "Error: Your POST data is corrupted or incompatible"
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")   

    #=======================================================#
    #   ACCESS LEVEL :  MASTER     GET_ADMIN_BLOG_POST()
    #=======================================================#        
    def get_admin_blog_post(self, request):
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes in 
 
        ERROR_MESSAGE = ""
        #Check our user's session and access level  
        if request.user.permissions.master_admin:
            if request.method == 'POST':    
                post = BlogPost.objects.get(pk=request.POST['post_pk'])
                postJSON = {}
                postJSON['name'] = post.name
                postJSON['content'] = post.content
                postJSON['image_url'] = post.image.url
                postJSON = json.dumps(postJSON)
                #SUCCESS!!
                return HttpResponse(postJSON, content_type="application/json")         
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")   
        
        
    #=======================================================#
    #   ACCESS LEVEL :  MASTER     EDIT_SECURITY_MESSAGE()
    #=======================================================#        
    def edit_security_message(self, request):
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes in 
 
        ERROR_MESSAGE = ""
        #Check our user's session and access level  
        if request.user.permissions.master_admin:
            if request.method == 'POST':    
                message = SecurityMessage.objects.get(pk=request.POST['message_pk'])
                if request.POST['is_seen'] == 'true': message.seen_by_admin = True
                else: message.seen_by_admin = False;
                message.save()
                #SUCCESS!!
                return HttpResponse('{"MESSAGE":"SUCCESS"}',content_type="application/json")         
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")   

        
    #=======================================================#
    #   ACCESS LEVEL :  MASTER     CREATE_PROJECT()
    #=======================================================#        
    def create_project(self, request):
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes in 
 
        ERROR_MESSAGE = ""
        logger.info( request)
        logger.info( request.POST)
        #Check our user's session and access level  
        if request.user.permissions.master_admin:
            if request.method == 'POST':    
                project = FormProject(name=request.POST['project_name'])
                project.save()
                #SUCCESS!!
                return HttpResponse('{"MESSAGE":"SUCCESS", "pk":"'+str(project.pk)+'", "name":"'+str(project.name)+'"}',content_type="application/json")         
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")   

    #=======================================================#
    #   ACCESS LEVEL :  MASTER     DELETE_PROJECT()
    #=======================================================#        
    def delete_project(self, request):       
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes in 
 
        ERROR_MESSAGE = ""
        logger.info( request)
        logger.info( request.POST)
        #Check our user's session and access level  
        if request.user.permissions.master_admin:
            if request.method == 'POST':   
                if request.user.check_password(request.POST['password']):
                    project = FormProject.objects.get(pk=request.POST['project_pk'])
                    project.delete()
                    #SUCCESS!!
                    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), "This user just deleted this project", request.META)
                    return HttpResponse('{"MESSAGE":"SUCCESS","accepted":"YES"}',content_type="application/json") 
                else:
                    ERROR_MESSAGE += "Error: You gave the incorrect password to delete this project."
                    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
                    return HttpResponse('{"MESSAGE":"'+ERROR_MESSAGE+'","accepted":"NO"}',content_type="application/json") 
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")   

    #=======================================================#
    #   ACCESS LEVEL :  MASTER     DELETE_ADMIN_POST()
    #=======================================================#        
    def delete_admin_post(self, request):       
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes in 
 
        ERROR_MESSAGE = ""
        logger.info( request)
        logger.info( request.POST)
        #Check our user's session and access level  
        if request.user.permissions.master_admin:
            if request.method == 'POST':   
                if request.user.check_password(request.POST['password']):
                    post = BlogPost.objects.get(pk=request.POST['post_pk'])
                    post.delete()
                    #SUCCESS!!
                    return HttpResponse('{"MESSAGE":"SUCCESS","accepted":"YES"}',content_type="application/json") 
                else:
                    ERROR_MESSAGE += "Error: You gave the incorrect password to delete this project."
                    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
                    return HttpResponse('{"MESSAGE":"'+ERROR_MESSAGE+'","accepted":"NO"}',content_type="application/json") 
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")   


    #=======================================================#
    #   ACCESS LEVEL :  MASTER     DELETE_USER()
    #=======================================================#        
    def delete_user(self, request):       
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes in a user PK and PERMANENTLY deletes it from the database--this tool is reserved for ONLY
        #   --the Master Admin--not even projects can delete their own users, because all users have relations to the data--users can
        #   --only be 'switched off' in a sense. As a master admin I can DELETE a user--usually through errors etc.
        #   Requires the admin to retype their password in order to confirm the deletion
 
        ERROR_MESSAGE = ""
        logger.info( request)
        logger.info( request.POST)
        #Check our user's session and access level  
        if request.user.permissions.master_admin:
            if request.method == 'POST':   
                if request.user.check_password(request.POST['password']):
                    user = User.objects.get(pk=request.POST['user_pk'])
                    user.delete()
                    #SUCCESS!!
                    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), "This user just deleted another user", request.META)
                    return HttpResponse('{"MESSAGE":"SUCCESS","accepted":"YES"}',content_type="application/json") 
                else:
                    ERROR_MESSAGE += "Error: You gave the incorrect password to delete this user."
                    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
                    return HttpResponse('{"MESSAGE":"'+ERROR_MESSAGE+'","accepted":"NO"}',content_type="application/json") 
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")   

     #=======================================================#
    #   ACCESS LEVEL :  MASTER     CREATE_PROJECT_ADMIN()
    #=======================================================#        
    def create_project_admin(self, request):       
        logger.info( request.POST)
    #----------------------------------------------------------------------------------------------------------------------------
    #   This endpoint is for a MASTER admin to initialize a level 5 admin user for a new project(or simply add a new one)
    #   It also allows the creation of another MASTER Admin
        ERROR_MESSAGE = ""
        #Check our user's session and access level  
        if request.user.permissions.master_admin:
            if request.method == 'POST':   
                project = FormProject.objects.get(pk=request.POST['project_pk'])
                username = request.POST['username']
                email = request.POST['email']
                if request.POST['is_master'] == "T": is_master = True
                else: is_master = False
                newpassword = get_random_string(24)
                theUser = User()
                theUser.username = username
                theUser.email = email
                theUser.set_password(newpassword)
                theUser.is_staff = True
                theUser.is_active = True
                theUser.save()
                theUser.permissions.project = project
                theUser.permissions.master_admin = is_master
                theUser.permissions.access_level = 5
                theUser.save()
                
                #Construct our Email
                subject = "TARA Project: " + " ("+theUser.username+") New Password"
                message = "<p><b>Hello "+ " ("+theUser.username+")! Welcome to <b>TARA</b>! Your new password is:</p></b><p> (>  "+newpassword+"  <)</p><p>Make sure to change your password when you re-login!</p>"
                message += "<p>Good luck and thanks for using our system!</p>"
                message += "<p>TARA Administrator</p>"
                message += "<p><b><h2>THIS IS AN AUTOMATED MESSAGE, PLEASE DO NOT REPLY. TARA DOES NOT RECEIVE INCOMING EMAIL</h2></b></p>"
                client = "admin@tara.museum.upenn.edu"
                to = theUser.email
                msg = EmailMultiAlternatives(subject, strip_tags(message), client, [to])
                msg.attach_alternative(message, "text/html")
                msg.send()
                return HttpResponse('{"MESSAGE":"SUCCESS","accepted":"YES",  "user_pk":"'+str(theUser.pk)+'"}',content_type="application/json") 
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")   

    #=======================================================#
    #   ACCESS LEVEL :  MASTER     CREATE_EDIT_BLOGPOST()
    #=======================================================#        
    def create_edit_blogpost(self, request):        
        logger.info(request.POST)
    #----------------------------------------------------------------------------------------------------------------------------
    #   This endpoint is for a MASTER admin to initialize a level 5 admin user for a new project(or simply add a new one)
    #   It also allows the creation of another MASTER Admin
        ERROR_MESSAGE = ""
        #Check our user's session and access level  
        if request.user.permissions.master_admin:
            if request.method == 'POST':        
                post_pk = ""
                #If we're making a new blog post
                if request.POST['is_new'] == "T":
                    new_post = BlogPost()
                    new_post.name = request.POST['name']
                    new_post.content = request.POST['content']
                    new_post.created_by = request.user
                    #Quickly save it here so that when we generate a file name for the blog ID it won't be null
                    new_post.save()
                    if len(request.FILES) > 0:
                        new_post.image = request.FILES['image']
                    new_post.save()
                    post_pk = str(new_post.pk)
                #If we're editing an existing blog post
                else:
                    current_post = BlogPost.objects.get(pk=request.POST['post_pk'])
                    current_post.name = request.POST['name']
                    current_post.content = request.POST['content']
                    #Quickly save it here so that when we generate a file name for the blog ID it won't be null
                    current_post.save()
                    if len(request.FILES) > 0:
                        current_post.image = request.FILES['image']
                    current_post.save()
                    
                    post_pk = str(current_post.pk)
                return HttpResponse('{"MESSAGE":"SUCCESS","accepted":"YES",  "blog_pk":"'+post_pk+'"}',content_type="application/json") 
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"       
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")           




        
    #-------------------------------------------------------------------------------------------------------
    # EXPORTER ENDPOINTS

    #=======================================================#
    #   ACCESS LEVEL :  1    EXPORT_PROJECT()
    #=======================================================#     
    def export_project(self, request, **kwargs):
        #***************#
        ACCESS_LEVEL = 1
        #***************#  
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes a Project pk value and returns a .zip file containing either flattened set of .csv files  or .json file export of ALL form types and their
        #   --associated forms/values, etc. It additionally includes a separate CSV
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
        logger.info( request)
        #Check our user's session and access level  
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            project = FormProject.objects.get(pk=request.POST['id'])
            if project.pk == request.user.permissions.project.pk:
            
                #Make the AJAX Request Data Model for subsequent AJAX calls
                progressData = AJAXRequestData(uuid=request.POST.get('uuid'), jsonString='{"row_index":"0","row_total":"0","is_complete":"False","row_timer":"0"}')
                progressData.save()                
                keepAliveTimer = time.process_time()
                
                all_dicts = []
                all_formTypes = FormType.objects.all().filter(project__pk=project.pk)
                

                
                if all_formTypes:
                    counter = 0
                    total_formtypes = len(all_formTypes)
                    percent_formtype_interval = 100.0 / total_formtypes
                    logger.info( percent_formtype_interval)
                    for formtype in all_formTypes:
                        logger.info( "Currently Loading: " + formtype.form_type_name)
                        
                        formtype_pct_done = counter * percent_formtype_interval
                        logger.info( formtype_pct_done)
                        progressData.jsonString = '{"percent_done":"'+str(formtype_pct_done)+'","current_formtype":"'+str(formtype.form_type_name)+'","is_complete":"False", "formtype_total":"'+str(total_formtypes)+'"}'
                        progressData.is_complete = False
                        progressData.save()
                        
                        counter += 1
                        
                        all_forms = formtype.form_set.all().filter(flagged_for_deletion=False)
                        # Load all of our FRATs and FRRTs
                        all_FRATs = formtype.formrecordattributetype_set.all().filter(flagged_for_deletion=False)
                        all_FRRTs = formtype.ref_to_parent_formtype.all().filter(flagged_for_deletion=False)
                        
                        formtype_dict = []
                        formCounter = 0
                        total_forms = len(all_forms)
                        form_pct_interval = percent_formtype_interval/total_forms
                        logger.info( form_pct_interval)
                        #Start loading all the forms by row now
                        if all_forms:
                            for form in all_forms:
                                #-------------------------------------------------------------------------------------------------
                                #   This block handles the AJAX progress calls before every form is processed
                                #vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
                                
                                form_pct_done = formtype_pct_done + (formCounter * form_pct_interval)
                                form_pct_done = int(form_pct_done * 100) / 100.0
                                #We re-initialize the progressData instance so it refreshes the values changed by the checkProgress() function
                                progressData = AJAXRequestData.objects.get(pk=progressData.pk)
                                progressData.jsonString = '{"percent_done":"'+str(form_pct_done)+'","current_formtype":"'+str(formtype.form_type_name)+'","is_complete":"False", "formtype_total":"'+str(total_formtypes)+'", "current_form":"'+str(form.form_name)+'", "total_forms":"'+str(total_forms)+'"}'
                                progressData.is_complete = False
                                #We want to make sure that our timer is set at 5 second itnervals. The AJAX script sets the keep alive variable to True
                                #   --every 1 second. I've set it to 5 seconds here to account for any delays that might occur over the network.
                                #   --Every 5 seconds, this script resets the keep_alive variable to 'False', if it is already False--that means the user exited
                                #   --the process on their AJAX end so we should stop adding this to the database and delete what we've already done.
                                #logger.info( str(time.process_time()) + "  - " + str(keepAliveTimer) + "    :    " + str(progressData.keep_alive))
                                if time.process_time() - keepAliveTimer > 5:
                                    logger.info( str (time.process_time() - keepAliveTimer) + "  : We are at the 5 second interval!  " + str(formCounter) )
                                    #restart the keepAlive timer to the current time
                                    keepAliveTimer = time.process_time()
                                    #delete the data if the user's AJAX end is unresponsive
                                    if progressData.keep_alive == False:
                                        logger.info( "We are deleting our progress now--wish us luck!")
                                        #TODO Delete all formtypes FRAT/FRRTs  that we just tried making
                                        progressData.delete()
                                        #break from loop
                                        logger.info( "Breaking from export function--user/client was unresponsive")
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
                                if all_FRATs:
                                    for FRAT in all_FRATs:
                                        currentFRAV = FRAT.formrecordattributevalue_set.all().filter(form_parent__pk=form.pk)
                                        if currentFRAV.exists():
                                            currentFRAV = currentFRAV[0]
                                            new_row[FRAT.record_type] = currentFRAV.record_value
                                        else:
                                            new_row[FRAT.record_type] = ""
                                if all_FRRTs:
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
                                formtype_dict.append(new_row)
                        all_dicts.append(formtype_dict)
                        
                    
                    logger.info( str(len(all_dicts)) +  "    "  + str(all_dicts[0]))
                    #End our AJAX MEssaging
                    progressData = AJAXRequestData.objects.get(pk=progressData.pk)
                    progressData.jsonString = '{"percent_done":"100","current_formtype":"None","is_complete":"True", "formtype_total":"1", "current_form":"None", "total_forms":"None"}'
                    progressData.is_complete = True
                    progressData.save()
                    
                    #Return the data as the specified format
                    if request.POST['export_format'] == "CSV":
                        #for each dict, let's make a list of CSV files
                        csv_file_list = []
                        for csv_dict in all_dicts:
                            keys = csv_dict[0].keys()
                            csv_file = io.BytesIO()
                            csv_writer = csv.DictWriter(csv_file, fieldnames=keys)
                            csv_writer.writerow(dict((fn,fn) for fn in keys))
                            csv_writer.writerows(csv_dict)
                            csv_file_list.append(csv_file)
                            if len(csv_dict) > 0:
                                logger.info( str(len(csv_file_list)) + "   "  + csv_dict[0]['Form Type Parent'])
                            else:
                                logger.info( str(len(csv_file_list)) + "   "  + str(csv_dict))
                        zipped_file = io.BytesIO()
                        with contextlib.closing(zipfile.ZipFile(zipped_file, 'w')) as f:#TODO We need contextlin() here for py2.6 to 'close' the file. We can remove contextlib() and leave the rest as is for later python versions
                            for i, file in enumerate(csv_file_list):
                                logger.info( str(file))
                                f.writestr("{0}__.csv".format(i), file.getvalue())
                        zipped_file.seek(0)
                        response = HttpResponse(zipped_file, mimetype='application/x-zip-compressed')
                        response['Content-Disposition'] = 'attachment; filename="'+project.name+'__'+request.user.username+'.zip"'
                        progressData.jsonString = '{"row_index":"100","is_complete":"True", "row_total":"100"}'
                        progressData.is_complete = True
                        progressData.save()
                        return response
                    elif request.POST['export_format'] == "JSON":
                        #for each dict, let's make a list of JSON files
                        json_file_list = []
                        for json_dict in all_dicts:
                            json_file = io.BytesIO(json.dumps(json_dict))
                            json_file_list.append(json_file)
                        zipped_file = io.BytesIO()
                        with contextlib.closing(zipfile.ZipFile(zipped_file, 'w')) as f:#TODO We need contextlin() here for py2.6 to 'close' the file. We can remove contextlib() and leave the rest as is for later python versions
                            for i, file in enumerate(json_file_list):
                                logger.info( str(file))
                                f.writestr("{0}__.json".format(i), file.getvalue())
                        zipped_file.seek(0)
                        response = HttpResponse(zipped_file, mimetype='application/x-zip-compressed')
                        response['Content-Disposition'] = 'attachment; filename="'+project.name+'__'+request.user.username+'.zip"'
                        progressData.jsonString = '{"row_index":"100","is_complete":"True", "row_total":"100"}'
                        progressData.is_complete = True
                        progressData.save()
                        return response                  

            else: ERROR_MESSAGE += "Error: You are attempting to access another project's data!"            
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")       
    

    
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
        logger.info( request)
        #Check our user's session and access level  
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            formtype = FormType.objects.get(pk=request.POST['id'])
            if formtype.project.pk == request.user.permissions.project.pk and formtype.flagged_for_deletion == False:

                #Make the AJAX Request Data Model for subsequent AJAX calls
                progressData = AJAXRequestData(uuid=request.POST.get('uuid'), jsonString='{"row_index":"0","row_total":"0","is_complete":"False","row_timer":"0"}')
                progressData.save()                
                keepAliveTimer = time.process_time()
            
                csv_string = ""
                all_forms = formtype.form_set.all().filter(flagged_for_deletion=False)
                # Load all of our FRATs and FRRTs
                all_FRATs = formtype.formrecordattributetype_set.all()
                all_FRRTs = formtype.ref_to_parent_formtype.all()
                
                csv_dict = []
              
                formCounter = 0
                total_forms = len(all_forms)
                form_pct_interval = 100.0 / total_forms
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
                        logger.info( str(time.process_time()) + "  - " + str(keepAliveTimer) + "    :    " + str(progressData.keep_alive))
                        if time.process_time() - keepAliveTimer > 5:
                            logger.info( str (time.process_time() - keepAliveTimer) + "  : We are at the 5 second interval!  " + str(formCounter) )
                            #restart the keepAlive timer to the current time
                            keepAliveTimer = time.process_time()
                            #delete the data if the user's AJAX end is unresponsive
                            if progressData.keep_alive == False:
                                logger.info( "We are deleting our progress now--wish us luck!")
                                #TODO Delete all formtypes FRAT/FRRTs  that we just tried making
                                progressData.delete()
                                #break from loop
                                logger.info( "Breaking from export function--user/client was unresponsive")
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
                progressData.is_complete = True
                progressData.save()                  
                
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
    # RECYLING BIN ENDPOINTS

    #=======================================================#
    #   ACCESS LEVEL :  4     LOAD_RECYCLING_BIN()
    #=======================================================#     
    def load_recycling_bin(self, request):
        #***************#
        ACCESS_LEVEL = 4
        #***************#  
        
        #----------------------------------------------------------------------------------------------------------------------------
        #  Loads the recycling bin
 
        ERROR_MESSAGE = ""
        logger.info( request)
        #Check our user's session and access level  
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            if request.method == 'POST':    
                project = FormProject.objects.get(pk=request.POST['project_pk'])
                if project.pk == request.user.permissions.project.pk:
                    recycleBinJSON = {}
                    recycledItems = []
                    recycleBinJSON['recycled_items'] = recycledItems
                    #First find all FormTypes that are flagged and add them to the list
                    recycledFormTypes = FormType.objects.all().filter(project__pk=project.pk, flagged_for_deletion=True)
                    for formType in recycledFormTypes:
                        currentItem = {}
                        currentItem['item_pk'] = formType.pk
                        currentItem['item_label'] = formType.form_type_name
                        currentItem['item_type'] = "FTYPE"
                        currentItem['date_deleted'] = str(formType.date_last_modified)
                        recycledItems.append(currentItem)
                        
                    #Find all recycled Forms WITHOUT FormType parents that are also recycled(We don't want to list Forms of recycled FormTypes)
                    recycledForms = Form.objects.all().filter(project__pk=project.pk, flagged_for_deletion=True, form_type__flagged_for_deletion=False)
                    for form in recycledForms:
                        currentItem = {}
                        currentItem['item_pk'] = form.pk
                        currentItem['item_label'] = form.form_name
                        currentItem['item_type'] = "FORM"
                        currentItem['parent_form_type'] = form.form_type.form_type_name
                        currentItem['date_deleted'] = str(form.date_last_modified)
                        
                        recycledItems.append(currentItem)      

                    #Find all recycled FRATS without FormType parents that are also recycled
                    recycledFRATs = FormRecordAttributeType.objects.all().filter(project__pk=project.pk, flagged_for_deletion=True, form_type__flagged_for_deletion=False)
                    for FRAT in recycledFRATs:
                        currentItem = {}
                        currentItem['item_pk'] = FRAT.pk
                        currentItem['item_label'] = FRAT.record_type
                        currentItem['item_type'] = "FRAT"
                        currentItem['parent_form_type'] = FRAT.form_type.form_type_name
                        currentItem['date_deleted'] = str(FRAT.date_last_modified)
                        
                        recycledItems.append(currentItem)   
                    #Find all recycled FRATS without FormType parents that are also recycled
                    recycledFRRTs = FormRecordReferenceType.objects.all().filter(project__pk=project.pk, flagged_for_deletion=True, form_type_parent__flagged_for_deletion=False)
                    for FRRT in recycledFRRTs:
                        currentItem = {}
                        currentItem['item_pk'] = FRRT.pk
                        currentItem['item_label'] = FRRT.record_type
                        currentItem['item_type'] = "FRRT"
                        currentItem['parent_form_type'] = FRRT.form_type_parent.form_type_name
                        currentItem['date_deleted'] = str(FRRT.date_last_modified)
                        
                        recycledItems.append(currentItem) 
                    
                    jsonResponse = json.dumps(recycleBinJSON)
                    #SUCCESS!!
                    return HttpResponse(jsonResponse,content_type="application/json") 
                else: ERROR_MESSAGE += "Error: You are attempting to access another project's data!"            
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")   
        
    
    #=======================================================#
    #   ACCESS LEVEL :  4     RECYCLE_FORM_TYPE()
    #=======================================================#     
    def recycle_form_type(self, request):
        #***************#
        ACCESS_LEVEL = 4
        #***************#  
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes a FormType pk value and flags it for the recycling bin so it no longer is shown--hidden from all
        #   --all queries and access until restored by a level 5 access privilege user. It allows for the temporary deletion of 
        #   --'deletion' of database items, but allows for them to be restored effectively like an 'undo' button
        #
        #   This also loops through all childed Forms of the FormType and flags them for recycling. There is no need to flag the childed
        #   --FRATs or FRRTs, because no endpoint or query will allow them to be accessed without their parent Form or FormType requesting them.
        #   --They can be individually flagged, but there is no need to flag them here.
 
        ERROR_MESSAGE = ""
        logger.info( request)
        #Check our user's session and access level  
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            if request.method == 'POST':    
                formtype = FormType.objects.get(pk=request.POST['ID'])
                if formtype.project.pk == request.user.permissions.project.pk:
                    formtype.flagged_for_deletion = True
                    formtype.save()
                    #now flag all of its chlidren forms
                    childForms = formtype.form_set.all()
                    #Load all forms into cache with a single database hit
                    if childForms:
                        for aForm in childForms:
                            aForm.flagged_for_deletion = True
                            aForm.save()
                        
                    #SUCCESS!!
                    return HttpResponse('{"MESSAGE":"SUCCESS!"}',content_type="application/json") 
                else: ERROR_MESSAGE += "Error: You are attempting to access another project's data!"            
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")   
        
    #=======================================================#
    #   ACCESS LEVEL :  3     RECYCLE_FORM()
    #=======================================================#        
    def recycle_form(self, request):
        #***************#
        ACCESS_LEVEL = 3
        #***************#  
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes a Form pk value and flags it for the recycling bin so it no longer is shown--hidden from all
        #   --all queries and access until restored by a level 5 access privilege user. It allows for the temporary deletion of 
        #   --'deletion' of database items, but allows for them to be restored effectively like an 'undo' button
        #
        #
        #   There is no need to flag its childed FRAVs or FRRVs because they can't be accessed without this form 
        #   --requesting access to them
        #
        #   !!TODO!! It may be possible to query them still in the query tools--I'll have to check if their parent Form
        #   --limits the django filters. If not, then we will need to loop through all the rvals and turn their recycle
        #   --flags on.    !!!!!Upon further investigation--it would appear they ARE limited by their Form parent, so let's ignore this.
        #                  !!!!!    --but a little more investigation could be ncessary, so let's leave this open ended for now
        
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level  
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            if request.method == 'POST':    
                form = Form.objects.get(pk=request.POST['ID'])
                if form.project.pk == request.user.permissions.project.pk:
                    form.flagged_for_deletion = True
                    form.save()
                    #SUCCESS!!
                    return HttpResponse('{"MESSAGE":"SUCCESS!"}',content_type="application/json") 
                else: ERROR_MESSAGE += "Error: You are attempting to access another project's data!"            
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")   
       
    #=======================================================#
    #   ACCESS LEVEL :  3     RECYCLE_FRAT()
    #=======================================================#        
    def recycle_frat(self, request):
        #***************#
        ACCESS_LEVEL = 3
        #***************#  
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes a FormRecordAttributeType pk value and flags it for the recycling bin so it no longer is shown--hidden from all
        #   --all queries and access until restored by a level 5 access privilege user. It allows for the temporary deletion of 
        #   --'deletion' of database items, but allows for them to be restored effectively like an 'undo' button
        #
        #   No need to worry about the childed FRAVs because they shouldn't be loaded with the Form without a FRAT anyway.
        
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level  
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            if request.method == 'POST':    
                frat = FormRecordAttributeType.objects.get(pk=request.POST['ID'])
                if frat.project.pk == request.user.permissions.project.pk:
                    frat.flagged_for_deletion = True
                    frat.save()
                    #SUCCESS!!
                    return HttpResponse('{"MESSAGE":"SUCCESS!"}',content_type="application/json") 
                else: ERROR_MESSAGE += "Error: You are attempting to access another project's data!"
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")   

    #=======================================================#
    #   ACCESS LEVEL :  3     RECYCLE_FRRT()
    #=======================================================#        
    def recycle_frrt(self, request):    
        #***************#
        ACCESS_LEVEL = 3
        #***************#  
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes a FormRecordReferenceType pk value and flags it for the recycling bin so it no longer is shown--hidden from all
        #   --all queries and access until restored by a level 5 access privilege user. It allows for the temporary deletion of 
        #   --'deletion' of database items, but allows for them to be restored effectively like an 'undo' button
        #
        #   No need to worry about the childed FRRVs because they shouldn't be loaded with the Form without a FRAT anyway.
 
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level  
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            if request.method == 'POST':    
                frrt = FormRecordReferenceType.objects.get(pk=request.POST['ID'])
                if frrt.project.pk == request.user.permissions.project.pk:
                    frrt.flagged_for_deletion = True
                    frrt.save()
                    #SUCCESS!!
                    return HttpResponse('{"MESSAGE":"SUCCESS!"}',content_type="application/json") 
                else: ERROR_MESSAGE += "Error: You are attempting to access another project's data!"            
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")       


    #=======================================================#
    #   ACCESS LEVEL :  3     RECYCLE_WEBPAGE()
    #=======================================================#        
    def recycle_webpage(self, request):    
        #***************#
        ACCESS_LEVEL = 4
        #***************#  
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes a Webpage pk value and flags it for the recycling bin so it no longer is shown--hidden from all
        #   --all queries and access until restored by a level 5 access privilege user. It allows for the temporary deletion of 
        #   --'deletion' of database items, but allows for them to be restored effectively like an 'undo' button
        
 
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level  
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            if request.method == 'POST':    
                webpage = Webpage.objects.get(pk=request.POST['webpage_pk'])
                if webpage.project.pk == request.user.permissions.project.pk:
                    webpage.flagged_for_deletion = True
                    webpage.save()
                    
                    json_data = {}
                    json_data['menu_list'] = webpage.project.get_webpage_menu_list();
                    json_data['successful'] = "T"
                    json_data = json.dumps(json_data)
                    #SUCCESS!!
                    return HttpResponse(json_data, content_type="application/json") 
                else: ERROR_MESSAGE += "Error: You are attempting to access another project's data!"            
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")       
 

        
    #=======================================================#
    #   ACCESS LEVEL :  4     RESTORE_FORM_TYPE()
    #=======================================================#     
    def restore_form_type(self, request):
        #***************#
        ACCESS_LEVEL = 4
        #***************#  
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes a FormType pk value and flags it for restoring from the recycling bin. It essentially 'undo's the object
        #   --and restores it to its previous state.
        #
        #   This also loops through all childed Forms of the FormType and flags them for restoration. There is no need to flag the childed
        #   --FRATs or FRRTs, because they are left untouched by the recycling endpoint
 
        ERROR_MESSAGE = ""
        logger.info( request)
        #Check our user's session and access level  
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            if request.method == 'POST':    
                formtype = FormType.objects.get(pk=request.POST['ID'])
                if formtype.project.pk == request.user.permissions.project.pk:
                    formtype.flagged_for_deletion = False
                    formtype.save()
                    #now flag all of its chlidren forms
                    childForms = formtype.form_set.all()
                    #Load all forms into cache with a single database hit
                    if childForms:
                        for aForm in childForms:
                            aForm.flagged_for_deletion = False
                            aForm.save()
                        
                    #SUCCESS!!
                    return HttpResponse('{"MESSAGE":"SUCCESS!"}',content_type="application/json") 
                else: ERROR_MESSAGE += "Error: You are attempting to access another project's data!"            
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")   
        
    #=======================================================#
    #   ACCESS LEVEL :  4     RESTORE_FORM()
    #=======================================================#        
    def restore_form(self, request):
        #***************#
        ACCESS_LEVEL = 4
        #***************#  
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes a Form pk value and flags it for restoring from the recycling bin. It essentially 'undo's the object
        #   --and restores it to its previous state.
 
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level  
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            if request.method == 'POST':    
                form = Form.objects.get(pk=request.POST['ID'])
                if form.project.pk == request.user.permissions.project.pk:
                    form.flagged_for_deletion = False
                    form.save()
                    #SUCCESS!!
                    return HttpResponse('{"MESSAGE":"SUCCESS!"}',content_type="application/json") 
                else: ERROR_MESSAGE += "Error: You are attempting to access another project's data!"            
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")   
        
    #=======================================================#
    #   ACCESS LEVEL :  4     RESTORE_FRAT()
    #=======================================================#        
    def restore_frat(self, request):
        #***************#
        ACCESS_LEVEL = 4
        #***************#  
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes a FRAT pk value and flags it for restoring from the recycling bin. It essentially 'undo's the object
        #   --and restores it to its previous state.
 
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level  
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            if request.method == 'POST':    
                frat = FormRecordAttributeType.objects.get(pk=request.POST['ID'])
                if frat.project.pk == request.user.permissions.project.pk:
                    frat.flagged_for_deletion = False
                    frat.save()
                    #SUCCESS!!
                    return HttpResponse('{"MESSAGE":"SUCCESS!"}',content_type="application/json") 
                else: ERROR_MESSAGE += "Error: You are attempting to access another project's data!"
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")   

    #=======================================================#
    #   ACCESS LEVEL :  4     RESTORE_FRRT()
    #=======================================================#        
    def restore_frrt(self, request):    
        #***************#
        ACCESS_LEVEL = 4
        #***************#  
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes a FRRT pk value and flags it for restoring from the recycling bin. It essentially 'undo's the object
        #   --and restores it to its previous state.
 
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level  
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            if request.method == 'POST':    
                frrt = FormRecordReferenceType.objects.get(pk=request.POST['ID'])
                if frrt.project.pk == request.user.permissions.project.pk:
                    frrt.flagged_for_deletion = False
                    frrt.save()
                    #SUCCESS!!
                    return HttpResponse('{"MESSAGE":"SUCCESS!"}',content_type="application/json") 
                else: ERROR_MESSAGE += "Error: You are attempting to access another project's data!"            
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")       
        

    #-------------------------------------------------------------------------------------------------------
    # MODEL DELETION ENDPOINTS

    
    #=======================================================#
    #   ACCESS LEVEL :  5     DELETE_FORM_TYPE()
    #=======================================================#        
    def delete_form_type(self, request):
        #***************#
        ACCESS_LEVEL = 5
        #***************#  
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes in 
 
        ERROR_MESSAGE = ""
        logger.info( request)
        #Check our user's session and access level  
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            if request.method == 'POST':    
                formtype = FormType.objects.get(pk=request.POST['ID'])
                if formtype.project.pk == request.user.permissions.project.pk:
                    formtype.delete()
                    #SUCCESS!!
                    ERROR_MESSAGE += "This user just deleted this FormType  " + formtype.form_type_name
                    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
                    return HttpResponse('{"MESSAGE":"SUCCESS!"}',content_type="application/json") 
                else: ERROR_MESSAGE += "Error: You are attempting to access another project's data!"            
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")   

        
    #=======================================================#
    #   ACCESS LEVEL :  5     DELETE_FORM()
    #=======================================================#        
    def delete_form(self, request):
        #***************#
        ACCESS_LEVEL = 5
        #***************#  
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes in 
 
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level  
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            if request.method == 'POST':    
                form = Form.objects.get(pk=request.POST['ID'])
                if form.project.pk == request.user.permissions.project.pk:
                    form.delete()
                    #SUCCESS!!
                    ERROR_MESSAGE += "This user just deleted this Form  " + form.form_name + " of formtype: " + form.form_type.form_type_name
                    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
                    return HttpResponse('{"MESSAGE":"SUCCESS!"}',content_type="application/json") 
                else: ERROR_MESSAGE += "Error: You are attempting to access another project's data!"            
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")   

        
    #=======================================================#
    #   ACCESS LEVEL :  5     DELETE_FRAT()
    #=======================================================#        
    def delete_frat(self, request):
        #***************#
        ACCESS_LEVEL = 5
        #***************#  
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes in 
 
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level  
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            if request.method == 'POST':    
                frat = FormRecordAttributeType.objects.get(pk=request.POST['ID'])
                if frat.project.pk == request.user.permissions.project.pk:
                    frat.delete()
                    #SUCCESS!!
                    ERROR_MESSAGE += "This user just deleted this FRAT  " + frat.record_type + " of formtype: " + frat.form_type.form_type_name
                    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
                    return HttpResponse('{"MESSAGE":"SUCCESS!"}',content_type="application/json") 
                else: ERROR_MESSAGE += "Error: You are attempting to access another project's data!"
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")   

        
    #=======================================================#
    #   ACCESS LEVEL :  5     DELETE_FRRT()
    #=======================================================#        
    def delete_frrt(self, request):    
        #***************#
        ACCESS_LEVEL = 5
        #***************#  
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes in 
 
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level  
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            if request.method == 'POST':    
                frrt = FormRecordReferenceType.objects.get(pk=request.POST['ID'])
                if frrt.project.pk == request.user.permissions.project.pk:
                    frrt.delete()
                    #SUCCESS!!
                    ERROR_MESSAGE += "This user just deleted this FRRT  " + frrt.record_type + " of formtype: " + frrt.form_type_parent.form_type_name
                    SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
                    return HttpResponse('{"MESSAGE":"SUCCESS!"}',content_type="application/json") 
                else: ERROR_MESSAGE += "Error: You are attempting to access another project's data!"            
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")       
 
    #=======================================================#
    #   ACCESS LEVEL :  4     DELETE_FORM_TYPE_GROUP()
    #=======================================================#        
    def delete_form_type_group(self, request):    
        #***************#
        ACCESS_LEVEL = 4
        #***************#  
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint deletes a form type group -- we don't need to worry about recycling these because they don't take much
        #   --effort to recreate; they are just arbitrary labels
 
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level  
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            if request.method == 'POST':    
                ftg = FormTypeGroup.objects.get(pk=request.POST['ID'])
                if ftg.project.pk == request.user.permissions.project.pk:
                    ftg.delete()
                    #SUCCESS!!
                    return HttpResponse('{"MESSAGE":"SUCCESS!"}',content_type="application/json") 
                else: ERROR_MESSAGE += "Error: You are attempting to access another project's data!"            
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")       
 
 
    #=======================================================#
    #   ACCESS LEVEL :  4     DELETE_USER_PROFILE_QUERY()
    #=======================================================#        
    def delete_user_profile_query(self, request):    
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint deletes a user's saved query. There aren't too many protections needed here--because they can only delete saved queries from
        #   --their on profile.
 
        ERROR_MESSAGE = ""
        if request.method == 'POST':    
            #Get the user's queries and store as a Py Dictionary
            user_queries = request.user.permissions.saved_queries
            user_queries = json.loads(user_queries)
            for query in user_queries:
                if query['label'] == request.POST['label']:
                    user_queries.remove(query)
                    break
            request.user.permissions.saved_queries = json.dumps(user_queries)
            request.user.permissions.save()
            return HttpResponse('{"MESSAGE":"SUCCESS!"}',content_type="application/json") 
        else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")       
 
 
    #-------------------------------------------------------------------------------------------------------
    # MODEL MODIFICATION ENDPOINTS
    
    
    #=======================================================#
    #   ACCESS LEVEL :  4     CREATE_NEW_FORM_TYPE_TEMPLATE()
    #=======================================================#        
    def create_new_form_type_template(self, request):
        #***************#
        ACCESS_LEVEL = 4
        #***************#  
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes in POST data submitted by a user to add a new template to the formtype's existing json object string
        #   --if the template name is the same name as an existing template, it will simply overwrite it.
        #   --First it converts the json string to a python dict and adds a key with the same template name
 
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level  
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            if request.method == 'POST':    
                logger.info( request.POST)
                if 'formtype_id' in request.POST:
                    currentFormType = FormType.objects.get(pk=request.POST['formtype_id'], project=request.user.permissions.project)
                    
                    #Convert the new template in the POST to a python Dict
                    newTemplateString = request.POST['template_json']
                    newTemplateDict = json.loads(newTemplateString)
                    logger.info( currentFormType.template_json)
                    #Convert the formtype's json to a python dict
                    currentTemplateString = currentFormType.template_json
                    if currentTemplateString != "" and currentTemplateString != None:
                        currentTemplateDict = json.loads(currentTemplateString)
                        for key in newTemplateDict:
                            currentTemplateDict[key] = newTemplateDict[key]
                        currentFormType.template_json = json.dumps(currentTemplateDict)
                    else:
                        currentFormType.template_json = newTemplateString
                    
                    currentFormType.save()
                    #SUCCESS!!
                    return HttpResponse('{"MESSAGE":"SUCCESS!"}',content_type="application/json") 
                
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")     
                     
    #=======================================================#
    #   ACCESS LEVEL :  4     CREATE_NEW_FORM_TYPE()
    #=======================================================#        
    def create_new_form_type(self, request):
        #***************#
        ACCESS_LEVEL = 4
        #***************#  
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes in POST data submitted by a the create new form type page. It's similar to the 'edit_form_type' endpoint
        #   --but it only creates new objects in the database rather than edits them. 
        #
        #   It requires a level 4 access to make new form types. We also put in a project restriction on the formtype constrained by the
        #   --project ID in the user's permissions. If the formtype doesn't match the user's project, it will bring up an error page.
 
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level  
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            if request.method == 'POST':    
                logger.info( request.POST)
                post_data = request.POST
            
                newFormType = FormType()
                #Update the form's basic attributes
                newFormType.form_type_name = post_data.get('form_type_name')
                newFormType.project = request.user.permissions.project
                
                #Add the user information - We only set created by in endpoints that create the model for the first time
                newFormType.created_by = request.user
                newFormType.modified_by = request.user
                
                #add the appropriate flag for the formtype's hard-coded type: e.g. is is a media or control group?
                if post_data.get('ft_media_type') != '-1':
                    newFormType.type = 1
                    #also add the media type, e.g. img/pdf/3d etc.
                    newFormType.media_type = post_data.get('ft_media_type')
                    newFormType.file_extension = str(post_data.get('file_extension'))
                    #If there is a URI prefix then add one--otherwise set it to None
                    if 'uri_prefix' in post_data:
                        if post_data['uri_prefix'] != ""  or post_data['uri_prefix'] != " ":
                            newFormType.uri_prefix = post_data['uri_prefix']
                        else:
                            newFormType.uri_prefix = None
                    #Make sure that the hierarchy and group settings are kept null
                    newFormType.form_type_group = None
                    newFormType.is_hierarchical = False
                    #We need to delete all of the child Forms parent references
                    remove_all_form_hierarchy_parent_references(newFormType)
                else:
                    newFormType.type = 0
                    #Update the form type's group
                    #If it's a new group
                    if post_data.get('ft_group') == 'NEW':
                        #Create a new formtype group 
                        newFormTypeGroup = FormTypeGroup(name=request.POST['ft_group_new'], project=newFormType.project)
                        #Add the user information - We only set created by in endpoints that create the model for the first time
                        newFormTypeGroup.created_by = request.user
                        newFormTypeGroup.modified_by = request.user
                        newFormTypeGroup.save()
                        newFormType.form_type_group = newFormTypeGroup
                    #If it's coded to remove the group, then set the field to null
                    elif post_data.get('ft_group') == 'NONE':
                        newFormType.form_type_group = None
                    #Otherwise it's not a new group and not being removed so use the provided value
                    else:
                        newFormType.form_type_group = FormTypeGroup.objects.get(pk=request.POST['ft_group'])
                        logger.info( "WTF!!!!   " + post_data.get('ft_group'))

                        #update the formtypes status as hierarchical
                    if 'is_hierarchical' in post_data:
                        newFormType.is_hierarchical = True
                    else:
                        newFormType.is_hierarchical = False
                    
                newFormType.save()
                
                #Update all of the FormType's FormRecordAttributeTypes
                for key in post_data:
                    splitKey = key.split("__")
                    if len(splitKey) == 3: 
                            code,type_pk,instruction = splitKey
                            #If we are creating a new attribute type
                            if code == "frat" and instruction == "new":
                                newAttributeType = FormRecordAttributeType(record_type=post_data[key])
                                newAttributeType.form_type = newFormType
                                #Add the user information - We only set created by in endpoints that create the model for the first time
                                newAttributeType.created_by = request.user
                                newAttributeType.modified_by = request.user
                                newAttributeType.project = newFormType.project
                                if post_data[code + '__' + type_pk + '__order'] != "":
                                    newAttributeType.order_number = int(post_data[code + '__' + type_pk + '__order'])
                                else:
                                    #We need to give a random order number--if we don't, when Django attempts to order queries, it will get confused
                                    #--if two of the attribute types share the same number. If they have more than 600 unique columns---it won't matter
                                    #--anyway, because order just shows the first 5--this will just help the initial setup if someone doesn't set the 
                                    #--order fields at all.
                                    newAttributeType.order_number = random.randint(399,999)
                                newAttributeType.save()
                            #If we are creating a new reference type
                            if code == "frrt" and instruction == "new":
                                newReferenceType = FormRecordReferenceType(record_type=post_data[key])
                                newReferenceType.form_type_parent = newFormType
                                newReferenceType.project = newFormType.project
                                #Add the user information - We only set created by in endpoints that create the model for the first time
                                newReferenceType.created_by = request.user
                                newReferenceType.modified_by = request.user
                                #we use the auto-incremented temp id used in the javascript form to match the refeerence value for this ref type
                                if post_data["nfrrt__"+type_pk+"__ref"] == "self-reference":
                                    newReferenceType.form_type_reference = newFormType
                                elif post_data["nfrrt__"+type_pk+"__ref"] == "-1":
                                    newReferenceType.form_type_reference = None
                                else:
                                    newReferenceType.form_type_reference = FormType.objects.get(pk=post_data["nfrrt__"+type_pk+"__ref"])
                                    
                                if post_data['n' + code + '__' + type_pk + '__order'] != "":
                                    newReferenceType.order_number = int(post_data['n' + code + '__' + type_pk + '__order'])
                                else:
                                    #See explanation above ^^^^^^^^^ for this random int range
                                    newReferenceType.order_number = random.randint(399,999)
                                newReferenceType.save()
                #SUCCESS!!
                return HttpResponse('{"MESSAGE":"SUCCESS!"}',content_type="application/json") 
                
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")     
                    
                    
    #=======================================================#
    #   ACCESS LEVEL :  3     SAVE_FORM_TYPE_CHANGES()
    #=======================================================#       
    def save_form_type_changes(self, request):
        #***************#
        ACCESS_LEVEL = 3
        #***************#  
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes in POST data submitted by a form type editing page and makes the necessary changes. It also handles
        #   --any tools in the form type editor, e.g. changing a attribute RTYPE to a refrence RTYPE. Another Endpoint handles creating NEW
        #   --formtypes. This is only used for editing.
        #
        #   It requires a level 3 access to make form type changes. We also put in a project restriction on the formtype constrained by the
        #   --project ID in the user's permissions. If the formtype query set is 0 in length, then this endpoint will return an error
 
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level  
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            if request.method == 'POST':    
                deletedObjects = {}

                formTypeToEdit = FormType.objects.get(pk=request.POST['formtype_pk'])
                if formTypeToEdit.project.pk == request.user.permissions.project.pk:
                    
                    post_data = request.POST
                    
                    #Update the form's basic attributes
                    formTypeToEdit.form_type_name = post_data.get('form_type_name')
                    #Add the user information
                    formTypeToEdit.modified_by = request.user
                    #add the appropriate flag for the formtype's har-coded type: e.g. is is a media or control group?
                    logger.info( post_data.get('formtype-type'))
                    if post_data.get('ft_media_type') != '-1':#media
                        formTypeToEdit.type = 1
                        #also add the media type, e.g. img/pdf/3d etc.
                        formTypeToEdit.media_type = post_data.get('ft_media_type')
                        formTypeToEdit.file_extension = post_data.get('file_extension')
                        #If there is a URI prefix then add one--otherwise set it to None
                        if 'uri_prefix' in post_data:
                            if post_data['uri_prefix'] != ""  or post_data['uri_prefix'] != " ":
                                formTypeToEdit.uri_prefix = post_data['uri_prefix']
                            else:
                                formTypeToEdit.uri_prefix = None
                        #Make sure that the hierarchy and group settings are kept null
                        formTypeToEdit.form_type_group = None
                        formTypeToEdit.is_hierarchical = False
                        #We need to delete all of the child Forms parent references
                        remove_all_form_hierarchy_parent_references(formTypeToEdit)
                    else:
                        formTypeToEdit.type = 0 #standard formtype
                        formTypeToEdit.media_type = -1
                        formTypeToEdit.file_extension = ""
                        formTypeToEdit.uri_prefix = ""
                        #Update the form type's group
                        #If it's a new group
                        if post_data.get('ft_group') == 'NEW':
                            #Create a new formtype group 
                            newFormTypeGroup = FormTypeGroup(name=post_data.get('ft_group_new'), project=request.user.permissions.project)
                            #Add the user information
                            newFormTypeGroup.modified_by = request.user
                            newFormTypeGroup.created_by = request.user
                            newFormTypeGroup.save()
                            formTypeToEdit.form_type_group = newFormTypeGroup
                        #If it's coded to remove the group, then set the field to null
                        elif post_data.get('ft_group') == 'NONE':
                            formTypeToEdit.form_type_group = None
                        #Otherwise it's not a new group and not being removed so use the provided value
                        else:
                            formTypeToEdit.form_type_group = FormTypeGroup.objects.get(pk=post_data.get('ft_group'))
                            logger.info( "WTF!!!!   " + post_data.get('ft_group'))
                        #update the formtypes status as hierarchical
                        if 'is_hierarchical' in post_data:
                            formTypeToEdit.is_hierarchical = True
                        else:
                            formTypeToEdit.is_hierarchical = False
                     
                    
                    #Save the formtype
                    formTypeToEdit.save()
                    
                    #Update all of the form's FormRecordAttributeTypes
                    for key in post_data:
                        splitKey = key.split("__")
                        if len(splitKey) > 1:
                            #--------------------------------------------------------------------------------------------------------
                            #Update all of the form's FormRecordAttributeTypes
                            #--------------------------------------------------------------------------------------------------------
                            # $$SS-VALIDATION$$  This "If" checks to make sure no keys that have been removed for different reasons are used going forward $$
                            logging.info("CURRENT KEY: " + key + "Is in deleted objects?")
                            logger.info( "Fucking keys = ??  ",)
                            for akey in deletedObjects:
                                logger.info( akey+", ",)
                            logger.info( " ")
                            
                            if key not in deletedObjects:
                                if len(splitKey) == 2: 
                                    code,type_pk = splitKey
                                    if code == "frat":
                                        currentAttributeType = FormRecordAttributeType.objects.get(pk=type_pk)
                                        currentAttributeType.record_type = post_data[key]
                                        if post_data[key + '__order'] != "":
                                            currentAttributeType.order_number = int(post_data[key + '__order'])
                                        else:
                                            #We need to give a random order number--if we don't, when Django attempts to order queries, it will get confused
                                            #--if two of the attribute types share the same number. If they have more than 600 unique columns---it won't matter
                                            #--anyway, because order just shows the first 5--this will just help the initial setup if someone doesn't set the 
                                            #--order fields at all.
                                            currentAttributeType.order_number = random.randint(399,999)
                                        #Add the user information
                                        currentAttributeType.modified_by = request.user
                                        currentAttributeType.save()
                                        
                                if len(splitKey) == 3: 
                                    code,type_pk,instruction = splitKey
                                    #If we are creating a new attribute type
                                    if code == "frat" and instruction == "new":
                                        newAttributeType = FormRecordAttributeType(record_type=post_data[key])
                                        newAttributeType.form_type = formTypeToEdit
                                        if post_data[code + '__' + type_pk + '__order'] != "":
                                           newAttributeType.order_number = int(post_data[code + '__' + type_pk + '__order'])
                                        else:
                                            #We need to give a random order number--if we don't, when Django attempts to order queries, it will get confused
                                            #--if two of the attribute types share the same number. If they have more than 600 unique columns---it won't matter
                                            #--anyway, because order just shows the first 5--this will just help the initial setup if someone doesn't set the 
                                            #--order fields at all.
                                            newAttributeType.order_number = random.randint(399,999)
                                        #Add the user information
                                        newAttributeType.modified_by = request.user 
                                        newAttributeType.created_by = request.user 
                                        newAttributeType.save()
                                        #TODO: Techincally all related forms to this formtype won't have an attached value until edited on the admin page
                                        #Should I go ahead and add a null attribute value?
                                    #If we are getting an instruction from the user to delete this attribute type then delete it
                                    elif code== "frat" and instruction == "DEL":
                                        #*** RECYCLING BIN ***  pass this FRAT to the recycling bin
                                        recycledFRAT = FormRecordAttributeType.objects.get(pk=type_pk)
                                        recycledFRAT.flagged_for_deletion = True
                                        recycledFRAT.save()
                                    #--------------------------------------------------------------------------------------------------------------
                                    #If we're converting an attribute type into the form number, we'll do that here with the proper instruction
                                    #--------------------------------------------------------------------------------------------------------------
                                    elif code== "frat" and instruction == "switch-id":
                                        #We are going to have to loop through each form of this form type, and switch the values of the form ids and chosen FRAT to replace it with
                                        #--I think it's best to do this rather than make a new FRAT and new FRRVs which require more database actions. We are just swapping values on the existing database items
                                        
                                        #Get the current attribute type we are editing
                                        switchFRAT = FormRecordAttributeType.objects.get(pk=type_pk)
                                        #loop through the forms of this form type
                                        for aForm in formTypeToEdit.form_set.all():
                                            #Store the form's id in a temp variable
                                            oldID = aForm.form_name
                                            #now update the ID with the value of this form's related FRAT
                                            thisFRAV = aForm.formrecordattributevalue_set.all().filter(record_attribute_type=switchFRAT)[0]
                                            logging.info(str(thisFRAV) + " trying to change this ???? to :  " + aForm.form_name)
                                            aForm.form_name = thisFRAV.record_value
                                            aForm.form_number = None
                                            #update the FRAV with the form ID
                                            thisFRAV.record_value = oldID
                                            #Add the user information
                                            thisFRAV.modified_by = request.user
                                            aForm.modified_by = request.user
                                            #save the changes
                                            thisFRAV.save()
                                            aForm.save()
                                        #Finally change the FRAT label to "Old "FormType" ID
                                        switchFRAT.record_type = "Old " + formTypeToEdit.form_type_name + " ID"
                                        #Add the user information
                                        switchFRAT.modified_by = request.user
                                        switchFRAT.save()
                                            
                            #--------------------------------------------------------------------------------------------------------
                            #Update all of the form's FormRecordReferenceTypes
                            #--------------------------------------------------------------------------------------------------------
                             # $$SS-VALIDATION$$  This "If" checks to make sure no keys that have been removed for different reasons are used going forward $$
                            if key not in deletedObjects:
                                if (len(splitKey) == 2):
                                    code,type_pk = splitKey
                                    #If we're changing the label of the reference type or it's order then save those changes here
                                    if code == "frrt":
                                        currentReferenceType = FormRecordReferenceType.objects.get(pk=type_pk)
                                        currentReferenceType.record_type = post_data[key]
                                        if post_data[key + '__order'] != "":
                                            currentReferenceType.order_number = int(post_data[key + '__order'])
                                        else:
                                            #See explanation above ^^^^^^^^^ for this random int range
                                            currentReferenceType.order_number = random.randint(399,999)
                                        #Add the user information
                                        currentReferenceType.modified_by = request.user
                                        currentReferenceType.save()
                                if (len(splitKey) == 3):
                                    code,type_pk,instruction = splitKey
                                    
                                    # #if adding a new record reference type
                                    if code == "frrt" and instruction == "new":
                                        logging.info("FOR F*** SAKE    : " + post_data[key]  + " === " + post_data["nfrrt__"+type_pk+"__ref"])
                                        newReferenceType = FormRecordReferenceType(record_type=post_data[key])
                                        newReferenceType.form_type_parent = formTypeToEdit
                                        #we use the auto-incremented temp id used in the javascript form to match the refeerence value for this ref type
                                        if post_data["nfrrt__"+type_pk+"__ref"] == "-1":
                                          newReferenceType.form_type_reference = None
                                        else:
                                          newReferenceType.form_type_reference = FormType.objects.get(pk=post_data["nfrrt__"+type_pk+"__ref"])
                                       
                                        if post_data['n' + code + '__' + type_pk + '__order'] != "":
                                            newReferenceType.order_number = int(post_data['n' + code + '__' + type_pk + '__order'])
                                        else:
                                            #See explanation above ^^^^^^^^^ for this random int range
                                            newReferenceType.order_number = random.randint(399,999)
                                        #Add the user information
                                        newReferenceType.modified_by = request.user
                                        newReferenceType.created_by = request.user
                                        newReferenceType.save()
                                    # #If we are getting an instruction from the user to delete this reference type then delete it
                                    if code== "frrt" and instruction == "DEL":
                                        #Django will "DELETE CASCADE" autmoatically this object and take care of deleting
                                        #all the FormRecordReferenceValues that are attached to it in a ForeignKey
                                        recycledFRRT = FormRecordReferenceType.objects.get(pk=type_pk)
                                        recycledFRRT.flagged_for_deletion = True
                                        recycledFRRT.save()
                            #----------------------------------------------------------------------------------------
                            #  CHECK FOR ANY FLAGGED RECORD ATTRIBUTE TYPES TO BE CONVERTED TO REFERENCE TYPES
                            #       OR IF THERE ARE ANY REF TYPES THAT NEED TO BE REFRESHED/CHANGED
                            #----------------------------------------------------------------------------------------
                            if (len(splitKey) == 3):
                                code,type_pk,instruction = splitKey
                                #Here we are checking Attribute Types
                                #-------------------------------------
                                #If we have a match instructing to convert this record attribute type to a record reference type--make the conversion
                                if code == 'frat' and instruction == 'is-new-ref':
                                    thisFRAT = FormRecordAttributeType.objects.get(pk=type_pk)
                                    #We need to quickly make any edits to the Attribute Type the User might have made
                                    #--in the same screen, e.g. changing it's label name, or order number. We have to do this now
                                    #--because when we delete the FRAT later--these items will only be updated if the post_data key list
                                    #--happened to have that FRAT key first in line. We ensure any user edits are made to the FRAT now to be safe
                                    #--and to be consistent. It's only two values: order_num  and record_type
                                    newFRRT = FormRecordReferenceType()
                                    newFRRT.record_type = post_data[code+"__"+type_pk]#We use the label from the user form instead
                                    newFRRT.order_number = post_data[code+"__"+type_pk+"__order"]#We use the order_num from the user form instead
                                    newFRRT.is_public = thisFRAT.is_public
                                    newFRRT.project = thisFRAT.project
                                    newFRRT.form_type_parent = thisFRAT.form_type
                                    #Make sure the user didn't set it to "None" so we don't get a server error.
                                    #--Here we can leave it blank if "-1" because this is a new object created and None is the default
                                    if post_data["frat__"+ type_pk +"__new-ref-id"] != "-1":
                                        newFRRT.form_type_reference = FormType.objects.get(pk=post_data["frat__"+ type_pk +"__new-ref-id"])
                                    #Add the user information
                                    newFRRT.modified_by = request.user
                                    newFRRT.created_by = request.user
                                    newFRRT.save()
                                    #Now convert the Record Attribute Type Values attached to this Record Attribute Type to Record Reference Values
                                    #--tied to the newly created Record Reference Type
                                    for thisFRAV in FormRecordAttributeValue.objects.filter(record_attribute_type=thisFRAT):
                                        #logging.info(str(thisFRAV) + " <--FRAV  :  FRAT--> " + str(thisFRAT))
                                        newFRRV = FormRecordReferenceValue()
                                        newFRRV.external_key_reference = thisFRAV.record_value
                                        newFRRV.form_parent = thisFRAV.form_parent
                                        newFRRV.record_reference_type = newFRRT
                                        newFRRV.project = thisFRAV.project
                                        newFRRV.date_created = thisFRAV.date_created
                                        newFRRV.created_by = thisFRAV.created_by
                                        newFRRV.date_last_modified = thisFRAV.date_last_modified
                                        #Add the user information
                                        newFRRV.modified_by = request.user
                                        #We need to save the newFRRV before trying to add manytomany values to it
                                        newFRRV.save()
                                        #Now try and match a reference through the new external value if the User didn't set the Form Type to "None"
                                        #--Once again, we can leave this blank because the FRRV is a new object and None is the default value
                                        if newFRRT.form_type_reference != None:
                                            #And remember--Doh! Because the external key value can contain multiple values separated by comma, we need to take that into account
                                            refValues = newFRRV.external_key_reference.split(",")
                                            for value in refValues:
                                                #Make ABSOLUTE sure that we are looking for form names under the selected FormType and NOT the current FormType
                                                #--I made this devious mistake and it cost me hours and hours of headache down the road to figure out it was something
                                                #--that I fudged up like a month ago. My god.
                                                referenceLookup = newFRRT.form_type_reference.form_set.filter(form_name=value)
                                                logging.info(referenceLookup.count())
                                                if referenceLookup.count() > 0: 
                                                    newFRRV.record_reference.add(referenceLookup[0])
                                        #And save the new object!
                                        newFRRV.save()
                                    #Now delete all old attributes
                                    #--This should delete all attached values as well because they follow the on_delete.CASCADE direction in models.py
                                    #--This we DO delete permanently, because it's being converted to another model in the system--no point in recycling it because it can be
                                    #--re-converted back to a FRAT later
                                    thisFRAT.delete()
                                    #We also need to add the post data key to the deletedObjects Dict() do they aren't used by this script later
                                    #--in the event that the frat__pk  key is after this  post_value key in the dictionary iterations
                                    deletedObjects['frat__'+type_pk] = None
                                    
                                #Here we are checking Reference Type Changes
                                #--------------------------------------------
                                if code == 'frrt' and instruction == 'is-new-ref':
                                    
                                    thisFRRT = FormRecordReferenceType.objects.get(pk=type_pk)
                                    #change the form type reference to newly selected
                                    logging.info("TYPE PK?   : "+type_pk + " old type ref?  " + str(thisFRRT.form_type_reference))
                                    #We need a check here to determine if the Object was set to "None" or not, otherwise we'll get an error trying to lookup a -1 pk value
                                    if post_data["frrt__"+type_pk+"__new-ref-id"] != "-1":
                                        thisFRRT.form_type_reference = FormType.objects.get(pk=post_data["frrt__"+type_pk+"__new-ref-id"])
                                    else:
                                        thisFRRT.form_type_reference = None
                                    #Add the user information
                                    thisFRRT.modified_by = request.user
                                    #save the newly edited FormRecordReferenceType
                                    thisFRRT.save()
                                    logging.info("TYPE NEW?   : "+str(thisFRRT) + "  |  " + str(thisFRRT.form_type_reference))
                                    #now loop through all attached record reference values and attempt to attach them to the new form type form_names
                                    for aFRRV in thisFRRT.formrecordreferencevalue_set.all():
                                        #Add the user information
                                        aFRRV.modified_by = request.user
                                        #Once again, if the form reference type FRRT was set as "None" then we need to set its FRRV's as None as well
                                        if thisFRRT.form_type_reference == None:
                                            aFRRV.record_reference.clear()
                                            aFRRV.save()
                                        #Otherwise, perform the lookup on the given external key value to look up
                                        else:
                                            #Now let's find the matching form of this newly designated form_type if it exists
                                            #And remember--Doh! Because the external key value can contain multiple values separated by comma, we need to take that into account
                                            refValues = aFRRV.external_key_reference.split(",")
                                            for value in refValues:
                                                referenceLookup = thisFRRT.form_type_reference.form_set.filter(form_name=value)
                                                logging.info(referenceLookup.count())
                                                if referenceLookup.count() > 0: 
                                                    aFRRV.record_reference.add(referenceLookup[0])
                                            aFRRV.save()
                                    # $$SS-VALIDATION$$ There's no need to delete anything--we aren't converting entity types--just changing values.
                                    #--What we do need to do however, is ensure that the hidden reference field is not used(it's only used for new fields--not old ones)
                                    #--We have to check this, otherwise if it's iterated over--after this in the post_data, it will revert the change we just made.
                                    #--This should be handled by a 'disabled' tag in the templates, but this is a serverside security measure in case someone
                                    #--hacks the disabled's off in their browser debugger
                                    logging.info("DeletedObjects Adding: "  + 'frrt__'+type_pk+"__ref" + "   with Count @  : " + str(len(deletedObjects)))
                                    deletedObjects['frrt__'+type_pk+"__ref"] = None    
                            #----------------------------------------------------------------------------------------
                            #  CHECK FOR ANY FLAGGED RECORD REFERENCE TYPES TO BE CONVERTED TO ATTRIBUTE TYPES
                            #---------------------------------------------------------------------------------------- 
                            if (len(splitKey) == 3):
                                code,type_pk,instruction = splitKey
                                
                                if code == "frrt" and instruction == "is-new-att":
                                    #We need to make a new attribute type, label it with the reference label, and then loop through all the ref values
                                    #and convert the external key ids to the new attribute values
                                    oldFRRT = FormRecordReferenceType.objects.get(pk=type_pk)
                                    newFRAT = FormRecordAttributeType()
                                    newFRAT.record_type = oldFRRT.record_type
                                    newFRAT.form_type = oldFRRT.form_type_parent
                                    newFRAT.order_number = oldFRRT.order_number
                                    newFRAT.project = oldFRRT.project
                                    newFRAT.is_public = oldFRRT.is_public
                                    #Add the user information
                                    newFRAT.modified_by = request.user
                                    newFRAT.created_by = oldFRRT.created_by
                                    newFRAT.save()
                                    #Now loop through all the FRRVs
                                    for FRRV in oldFRRT.formrecordreferencevalue_set.all():
                                        newFRAV = FormRecordAttributeValue()
                                        newFRAV.record_value  = FRRV.external_key_reference
                                        newFRAV.date_created = FRRV.date_created
                                        newFRAV.date_last_modified = FRRV.date_last_modified
                                        newFRAV.record_attribute_type = newFRAT
                                        newFRAV.form_parent = FRRV.form_parent
                                        newFRAV.project = FRRV.project
                                        #Add the user information
                                        newFRAV.modified_by = request.user
                                        newFRAV.created_by = FRRV.created_by
                                        #Save our new FormRecordAttributeValue, and delete our old FormRecordReferenceValue
                                        newFRAV.save()
                                        #--This we DO delete permanently, because it's being converted to another model in the system--no point in recycling it because it can be
                                        #--re-converted back to a FRRV later
                                        FRRV.delete()
                                    #Once this loop is finished, make sure we delete the old FormRecordReferenceType as well
                                    #--This we DO delete permanently, because it's being converted to another model in the system--no point in recycling it because it can be
                                    #--re-converted back to a FRRT later
                                    oldFRRT.delete()
                                    #Add the FRRT to our garbage pile as well
                                    deletedObjects['frrt__'+type_pk+"__ref"] = None  
                                    deletedObjects['frrt__'+type_pk] = None  
                    return HttpResponse('{"MESSAGE":"Success!"}',content_type="application/json") 
                else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information" 
            else: ERROR_MESSAGE += "Error: You are trying to access the API without using a POST request."
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying form type information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")     

        
    #=======================================================#
    #   ACCESS LEVEL :  5     SAVE_PROJECT_CHANGES()
    #=======================================================#   
    def save_project_changes(self, request):
        #***************#
        ACCESS_LEVEL = 5
        #***************#  
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This endpoint takes in POST data submitted by the Admin Project form and makes any project changes to the database
        #   --Users are handled by a separate form, but basic meta data associated witht he project is stored and modified through this
        #   --Admin API endpoint
        #   
        #   This endpoint also requires level 5 access--ONLY project admins can change any of this information. Everyone else cannot
 
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level  
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
                if request.method == 'POST': 
                    #Only edit the project attached to this User
                    projectToEdit = request.user.permissions.project
                    projectToEdit.name = request.POST.get('project_name')
                    projectToEdit.description = request.POST.get('project_description')
                    projectToEdit.geojson_string = request.POST.get('project_geojson_string')
                    projectToEdit.uri_img = request.POST.get('dam_uri_img')
                    projectToEdit.uri_thumbnail = request.POST.get('dam_uri_thumb')
                    projectToEdit.uri_download = request.POST.get('dam_uri_download')
                    projectToEdit.uri_upload = request.POST.get('dam_uri_upload')
                    projectToEdit.uri_upload_key = request.POST.get('dam_upload_key')
                    #Add the user information
                    projectToEdit.modified_by = request.user
                    projectToEdit.save()
                    return HttpResponse('{"MESSAGE":"Success!"}',content_type="application/json")     
                else: ERROR_MESSAGE += "Error: You must use POST to access this endpoint"
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")     


   #========================================================#
    #   ACCESS LEVEL :  4      RUN_GEOJSON_IMPORTER()
    #=======================================================#       
    def run_geojson_importer(self, request):
        #******************************************#
        ACCESS_LEVEL = 4
        PROJECT = request.user.permissions.project
        #******************************************#   
        
        #-------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # This API Endpoint takes an argument for a gejson file and creates a new formtype for the data. #Coded this on board a plane to Chicago--
        #   --first written out on paper at the classy PHL airport over 2 well-deserved Golden Monkey Ales. Geojson is a standardized format of
        #   --geospatial and associated meta data(attribute data). This will need some tinkering I expect, but 'should' work with a few adjustments
        #   --Also--surprisingly I figured this out in ~30 lines of code which is pretty impressive if I do say so myself.
        #-------------------------------------------------------------------------------------------------------------------------------------------------------------------
        
        
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            #Make sure we only take POST requests        
            if request.method == 'POST':        
                logger.info( "Starting")
                #Make the AJAX Request Data Model for subsequent AJAX calls
                progressData = AJAXRequestData(uuid=request.POST.get('uuid'), jsonString='{"row_index":"0","row_total":"0","is_complete":"False","row_timer":"0"}')
                progressData.save()
                
                listOfFRATS = {}
                geojson = request.POST['geojson']
                geojson = json.loads(geojson)
                logger.info( "json Loaded")
                
                #create the new formtype
                newFormtype = FormType()
                newFormtype.form_type_name = geojson['name']
                newFormtype.geojson_projection = json.dumps(geojson['crs'])
                newFormtype.project = PROJECT
                newFormtype.type = 0
                newFormtype.save()
                
                totalFeatures = len(geojson['features'])
                featureCounter = 0
                counterIncrement = 100.0 / totalFeatures #0.00135
                
                startTimer = time.process_time()
                endTimer = time.process_time()
                for aFeature in geojson['features']:
                    #get current percentage of completion
                    endTimer = time.process_time()
                    
                    #logger.info( "New Form   : " + str(featureCounter) + " out of " +str(totalFeatures)+ "  rows finished!   " + str(counterIncrement))
                    progressData.jsonString = '{"row_index":"'+str(featureCounter)+'","is_complete":"False", "row_timer":"'+str(endTimer-startTimer)+'", "row_total":"'+str(totalFeatures)+'", "percent_done":"'+str(int(featureCounter*counterIncrement))+'"}'
                    progressData.is_complete = False
                    progressData.save()
                    startTimer = time.process_time()
                    featureCounter += 1
                    
                    newForm = Form()
                    newForm.form_geojson_string = json.dumps(aFeature['geometry'])
                    logger.info( str(newForm.form_geojson_string))
                    newForm.form_type = newFormtype
                    newForm.save()
                    for att_label, att_value in aFeature['properties'].items():
                        #logger.info( str(att_label) + "  : "  + str(att_value))
                        #check if the current attribute is our specified form ID
                        if att_label in request.POST:
                            #logger.info( "Found our Label! ^^^^^^^^" + str(att_value) + "  :  " +  aFeature['properties'][att_label])
                            newForm.form_name = str(att_value)
                            newForm.save()
                        else:
                        #Otherwise let's makes FRATs for the formtype
                            if att_label in listOfFRATS:
                                #the FRAT already exists so set our current FRAT to the one that matches
                                newFRAT = FormRecordAttributeType.objects.get(pk=listOfFRATS[att_label])
                            else:
                                #it's a new attribute type(so we're in the first loop iteration)
                                newFRAT = FormRecordAttributeType()
                                newFRAT.record_type = att_label
                                newFRAT.form_parent = newForm
                                newFRAT.form_type = newFormtype
                                newFRAT.order_number = random.randint(1, 999)
                                newFRAT.save()
                                listOfFRATS[att_label] = newFRAT.pk
                            #Make the FRAV for our new form
                            newFRAV = FormRecordAttributeValue()
                            newFRAV.record_value = str(att_value)
                            newFRAV.record_attribute_type = newFRAT
                            newFRAV.form_parent = newForm
                            newFRAV.save()
                progressData.jsonString = '{"row_index":"'+str(featureCounter)+'","is_complete":"True", "row_total":"'+str(totalFeatures)+', "percent_done":"100"}'
                progressData.is_complete = True
                progressData.save()
                return HttpResponse('{"MESSAGE":"Finished the import!"}',content_type="application/json")    
                
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"False", "row_total":"0", "row_timer":"0"}',content_type="application/json")     

      

        
   #========================================================#
    #   ACCESS LEVEL :  4      RUN_NEW_RTYPE_IMPORTER()
    #=======================================================#       
    def run_new_rtype_importer(self, request):
        #******************************************#
        ACCESS_LEVEL = 4
        PROJECT = request.user.permissions.project
        #******************************************#   
        
        #-------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # This API Endpoint takes an argument for a CSV file, HttpContext(e.g. context kwargs passed to the HttpResponse like pk values)........................

        #-------------------------------------------------------------------------------------------------------------------------------------------------------------------
        
        
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            #Make sure we only take POST requests        
            if request.method == 'POST':        
        
               
                #Make the AJAX Request Data Model for subsequent AJAX calls
                progressData = AJAXRequestData(uuid=request.POST.get('uuid'), jsonString='{"row_index":"0","row_total":"0","is_complete":"False","row_timer":"0"}')
                progressData.save()
                
                #kwargs.update({'uuid':progressData.pk})
                
                post_data = request.POST
                
                
                #timerA = time.process_time()
                #logger.info( "Starting Clock: " + str(timerA))
                #Make sure we escape the newline characters from the json string--jscript didn't do it automatically when concatenating the rows together in the clinet-side script
                #We also have to replace all \t 's  in the json strings before loading them because JSON doesn't allow literal TABS --we need to escape them with a "\\"
                #logger.info( post_data.get('csv_json').encode('utf-8').replace('\t', '\\t').replace('\r', '\\r').replace('\n', '\\n'))
                encoded_str = post_data.get('csv_json').replace('\t', '\\t').replace('\r', '\\r').replace('\n', '\\n').encode('utf-8').decode('utf-8')
                csv_json = json.loads(encoded_str)
                
                logger.info( post_data)
               
                #setup Dictionaries for post import  self-referential needs
                #setup a dict for hierarchy value
                hierarchyDict = {}
                #setup a recordreferencevalue dictionary for the form type if a particular reference is self-referencing to this same form type
                selfReferenceList = []
                
                #Get our current FormType
                currentFormType = FormType.objects.all().filter(project=request.user.permissions.project, pk=request.POST['formtype_pk'])[0]
                

                #Each row in the CSV file represents a new 'Form' of the 'currentFormType'
                #Let's make a 'row' counter to help with indexing through the CSV file
                row_index = 0    
                #Let's make an incremental counter for record type orders
                order_counter = 1
                #I'm also going to make a List() of AttributeTypes/ReferenceTypes. This is done so that
                #after 1 iteration of the importer loop, the reference types/ attribute types are already created. We
                #don't need to create them for every row--so after the first row, we reference this list for the reference
                # and attribute values
                typeList = {}
                
                logger.info( "Just making sure things are working still....where's the stop point?")
                main_ID_Field = ""
                keepAliveTimer = time.process_time()
                #logger.info( "Starting row loop: " + str(timerB) + "   Time elapsed = " + str(timerB-timerA))
                #For each row of the CSV
                for row in csv_json:
                    logger.info( "222 Just making sure things are working still....where's the stop point?")
                    timerBeginRow = time.process_time()
                    #logger.info( "Starting a new row: " + str(timerBeginRow))
                    #If we are past index '0' then let's continue with the rest of the importer

                    
                    #Let's get the main ID 
                    if row_index == 0:
                        for key, value in row.items():
                            if 'record__'+key+'__ismainID' in post_data:
                                main_ID_Field = key
                                break
                                
                    currentForm = Form.objects.all().filter(project=request.user.permissions.project, form_type__pk=currentFormType.pk, form_name=row[main_ID_Field])
                    if currentForm.exists():
                        currentForm = currentForm[0]
                        
                    else:
                        logger.info( "Skipping Form--Could not find form name:" + row[main_ID_Field])
                        logger.info( str(currentFormType.pk) + "   " + str(row[main_ID_Field]))
                        continue
      
                    for key, value in row.items():
                        logger.info( key)

                        if key != main_ID_Field:

                            #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@  ADD A RECORD REFERENCE TYPE @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                            #------------------------------------------------------------------------------------------------------------------------
                            #Test if it is a reference type by checking the POST_DATA if 'record__(n)__isreference' exists
                            #If it is a reference Type:
                            if 'record__'+str(key)+'__isreference' in post_data:
                                #We want to make sure we only create the ReferenceType's once--otherwise we populate the database with several 
                                #unecessary copies and relations that muddy everything. So if we're past the first row/iteration of the JSON, the reference types are
                                #already created and stored in a list to reference after
                                if row_index < 1:
                                    #First let's check if the Header Matches an existing RTYPE, If it does--let's use that FRAT instead of making a new one and replace its value with the
                                    #   --one provided in the new data
                                    if FormRecordReferenceType.objects.filter(record_type=post_data.get('record__'+str(key)+'__name'), flagged_for_deletion=False).exists():
                                        #add the attributeType to the typeList so that the attribute value can reference it
                                        typeList[key] = FormRecordReferenceType.objects.get(record_type=post_data.get('record__'+str(key)+'__name'), flagged_for_deletion=False)
                                    else: #create a new FormRecordReferenceType and set "record_type" variable to the header column name
                                        newFormRecordReferenceType = FormRecordReferenceType()
                                        newFormRecordReferenceType.project = PROJECT
                                        newFormRecordReferenceType.is_public = False
                                        newFormRecordReferenceType.record_type = post_data.get('record__'+str(key)+'__name')
                                        #also set "form_type_parent" to the current formType we are importing
                                        newFormRecordReferenceType.form_type_parent = currentFormType
                                        #now set "form_type_reference" to the selected FormTypeReference value in the current importer Column
                                        #if the value == 'default' then set reference to this same FormType
                                        if post_data.get('record__'+str(key)+'__reftype') == 'default':
                                            newFormRecordReferenceType.form_type_reference = currentFormType
                                        #otherwise set it to the given pk value of a FormType object
                                        else:
                                            newFormRecordReferenceType.form_type_reference = FormType.objects.get(pk=post_data.get('record__'+str(key)+'__reftype'))
                                        #Set an arbitrary initial order for the type
                                        newFormRecordReferenceType.order_number = order_counter
                                        order_counter += 1
                                        #save the Record Reference Type
                                        newFormRecordReferenceType.save()
                                        #add it to the list so that the reference value can reference it
                                        typeList[key] = newFormRecordReferenceType
                                #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@  ADD A RECORD REFERENCE VALUE @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                                #-------------------------------------------------------------------------------------------------------------------------
                                
                                #If this form already has a FRRV for this importer(e.g. we are running multiple rows with the same ID) then just reference
                                #   --that existing FRRV and add the new reference, as well as the ext_key
                                possibleFRRV =  currentForm.ref_to_parent_form.all().filter(record_reference_type=typeList[key])
                                if possibleFRRV.exists():
                                    newFormRecordReferenceValue = possibleFRRV[0]
                                    if newFormRecordReferenceValue.external_key_reference == "" or newFormRecordReferenceValue.external_key_reference == None:
                                        newFormRecordReferenceValue.external_key_reference = value
                                    else:
                                        newFormRecordReferenceValue.external_key_reference += "," + value
                                    newFormRecordReferenceValue.save()
                                else:
                                    #Create a new RecordReferenceValue
                                    newFormRecordReferenceValue = FormRecordReferenceValue()
                                    newFormRecordReferenceValue.project = PROJECT
                                    newFormRecordReferenceValue.is_public = False
                                    #set the "external_key_reference" to the column value of the csv row
                                    newFormRecordReferenceValue.external_key_reference = value
                                    #set the "form_parent" to the current row's Form
                                    newFormRecordReferenceValue.form_parent = currentForm                              
                                    #set the "record_reference_type" to the current RecordReferenceType
                                    logging.info("line626      " + str(typeList[key].form_type_reference) + "           :: " + newFormRecordReferenceValue.external_key_reference)
                                    newFormRecordReferenceValue.record_reference_type = typeList[key]
                                    #save the value to give it a pk value
                                    newFormRecordReferenceValue.save()
                                #logging.info("We are about to check the reference for:    " + str(newFormRecordReferenceValue))
                                #If this reference is self-referencing to the same form formtype we're importing, then similar to the hierchy references,
                                #--we need to store a list of the reference value objects to load once the entire form type has been imported. We don't need key values because
                                #--the external key reference is already saved for the lookup on the model.
                                #--I'm using the objects rather pk values because that will save us time on SQL queries later
                                if post_data.get('record__'+str(key)+'__reftype') == 'default':
                                    selfReferenceList.append(newFormRecordReferenceValue)
                                else:
                                    #Now we need to set the value for "record_reference" which will involve a query 
                                    #And since the external key could contain multiple values, we need to split them by the comma delimeter
                                    #logging.info(newFormRecordReferenceValue.external_key_reference + "  : BEFORE SPLIT")
                                    possibleRefValues = newFormRecordReferenceValue.external_key_reference.split(",")    
                                    #logging.info(str(possibleRefValues) + "  : SPLIT")
                                   
                                    #clear our list of refs everytime to ensure we don't double add--it will use the ext key to find them
                                    #   --this isn't the fastest way of doing this, but I need a quick fix for now !!!TODO
                                    newFormRecordReferenceValue.record_reference.clear()
                                    #for all forms in the selected FormType reference
                                    for aForm in newFormRecordReferenceValue.record_reference_type.form_type_reference.form_set.all().prefetch_related():
                                        #if the current external ID value == to the iterated forms "form_num"
                                        #Make sure we convert the INT form-num to a STR first or it will fail the check

                                        for refValue in possibleRefValues:
                                            if refValue == str(aForm.form_number):
                                                #remove this value from future matches to ensure we don't double add it
                                                possibleRefValues.remove(refValue)
                                                #set the current FormRecordReferenceValue.record_reference to the current form in the loop iteration
                                                newFormRecordReferenceValue.record_reference.add(aForm)
                                    #logging.info(newFormRecordReferenceValue.external_key_reference + "  : AFTER SPLIT") 
                                #if there are no matches by the last iteration of the loop,
                                #we can do nothing to leave the record_reference value as "None" (the user can set this later)
                                #This might happen if the user is importing a new form type that references itself, or references
                                #another form type that hasn't yet been imported. The external_key_reference's are still saved
                                #so the user can run another tool to match these keys later once all the Form Types and forms have been
                                #imported through this tool
                                #save the RecordReferenceValue
                                newFormRecordReferenceValue.save()    
                                #timerE = time.process_time()
                                #logger.info( "Ending ref lookup: " + str(timerE) + "   Time elapsed = " + str(timerE-timerD)    )
                            #If it is not a reference type, then we are adding an attribute type instead
                            else:
                                #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@  ADD A RECORD ATTRIBUTE TYPE @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                                #------------------------------------------------------------------------------------------------------------------------
                                #We want to make sure we only create the AttributeType's once--otherwise we populate the database with several 
                                #unecessary copies and relations that muddy everything. So if we're past the first row, the attribute types are
                                #already created and stored in a list to reference after
                                if row_index < 1:
                                    #First let's check if the Header Matches an existing RTYPE, If it does--let's use that FRAT instead of making a new one and replace its value with the
                                    #   --one provided in the new data
                                    if FormRecordAttributeType.objects.filter(record_type=post_data.get('record__'+str(key)+'__name'), flagged_for_deletion=False).exists():
                                        #add the attributeType to the typeList so that the attribute value can reference it
                                        typeList[key] = FormRecordAttributeType.objects.get(record_type=post_data.get('record__'+str(key)+'__name'), flagged_for_deletion=False)
                                    else: #create a new FormRecordAttributeType and set "record_type" variable to the header column name
                                        newFormRecordAttributeType = FormRecordAttributeType()
                                        newFormRecordAttributeType.record_type = post_data.get('record__'+str(key)+'__name')
                                        newFormRecordAttributeType.project = PROJECT
                                        newFormRecordAttributeType.is_public = False
                                        #also set "form_type" to the current formType we are importing
                                        newFormRecordAttributeType.form_type = currentFormType
                                        #Set an arbitrary initial order for the type
                                        newFormRecordAttributeType.order_number = order_counter
                                        order_counter += 1
                                        #save the RecordAttributeType
                                        newFormRecordAttributeType.save()
                                        #add the attributeType to the typeList so that the attribute value can reference it
                                        typeList[key] = newFormRecordAttributeType
                                #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@  ADD A RECORD Attribute VALUE @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                                #-------------------------------------------------------------------------------------------------------------------------
                                #If this form already has a FRAV then override it
                                possibleFRAV =  currentForm.formrecordattributevalue_set.all().filter(record_attribute_type=typeList[key])
                                if possibleFRAV.exists():
                                    newFormRecordAttributeValue = possibleFRAV[0]
                                    newFormRecordAttributeValue.record_value = value
                                    newFormRecordAttributeValue.save()
                                else:                                
                                    #Create a new RecordAttributeValue
                                    newFormRecordAttributeValue = FormRecordAttributeValue()
                                    newFormRecordAttributeValue.project = PROJECT
                                    newFormRecordAttributeValue.is_public = False
                                    #set the "record_value" to the column value of the csv row
                                    newFormRecordAttributeValue.record_value = value
                                    #set the "form_parent" to the current row's Form
                                    newFormRecordAttributeValue.form_parent = currentForm
                                    #set the "record_attribute_type" to the current RecordAttributeType
                                    newFormRecordAttributeValue.record_attribute_type = typeList[key]
                                    #save the RecordAttributeValue
                                    newFormRecordAttributeValue.save()

                    row_index += 1
                    #Upload our progress data object with the current row
                    timerFinishRow = time.process_time()
                    #logger.info( "Ending a row: " + str(timerF) + "   Time elapsed since row start = " + str(timerF-timerC))
                    #We need to update the progessData model because it is updated by another thread as well
                    #--Otherwise this will just ignore the  'keep_alive' flag and quit after 2 timer checks
                    #--I'm not entirely sold on this method--There's a slight....itty bitty...teensy weensy...chance that the other thread
                    #--might be trying to update the AJAX model at the exact time and will be missed here--but as of now, I can't think of a
                    #--better solution and I'm REALLY over working on this importer today.
                    progressData = AJAXRequestData.objects.get(pk=progressData.pk)
                    progressData.jsonString = '{"row_index":"'+str(row_index)+'","is_complete":"False","row_total":"'+post_data.get('row_total')+'","row_timer":"'+str(timerFinishRow-timerBeginRow)+'"}'

                    #We want to make sure that our timer is set at 5 second itnervals. The AJAX script sets the keep alive variable to True
                    #   --every 1 second. I've set it to 5 seconds here to account for any delays that might occur over the network.
                    #   --Every 5 seconds, this script resets the keep_alive variable to 'False', if it is already False--that means the user exited
                    #   --the process on their AJAX end so we should stop adding this to the database and delete what we've already done.
                    #logger.info( str(time.process_time()) + "  - " + str(keepAliveTimer) + "    :    " + str(progressData.keep_alive))
                    if time.process_time() - keepAliveTimer > 5:
                        logger.info( str (time.process_time() - keepAliveTimer) + "  : We are at the 5 second interval!  " + str(row_index) )
                        #restart the keepAlive timer to the current time
                        keepAliveTimer = time.process_time()
                        #delete the data if the user's AJAX end is unresponsive
                        if progressData.keep_alive == False:
                            logger.info( "We are deleting our progress now--wish us luck!")
                            #TODO Delete all formtypes FRAT/FRRTs  that we just tried making
                            progressData.delete()
                            #break from loop
                            break
                        else:
                            progressData.keep_alive = False
                    progressData.save()
                #Now Update the hierchical references if they exist
                #This forloop will only run if the hierarchyDict has been appended to already
                for key, value in hierarchyDict.items():
                    formToModify  =  Form.objects.get(pk=key)
                    try:#Essentially we are trying to grab the form with the given form_name. If no match is found--the TRY statement will leave it as NoneType
                        formToModify.hierarchy_parent = Form.objects.all().filter(form_name=value)[0]
                        #logger.info( "Admin: Line 681: WHAT'S The Name?: " + formToModify.hierarchy_parent)
                        formToModify.save()
                    except:
                        logger.info( "No Hierarchy Match found.")
                #Now Update the self references if they exist
                #This forloop will only run if the selfReferenceList has been populated
                for refValue in selfReferenceList:
                    #Remember that some external key references may be multi-values that are comma seperated, so let's try splitting them by comma
                    #--and looping through them appropriately
                    key_list = refValue.external_key_reference.split(',')
                    for aKey in key_list:
                        try:#Essentially we are trying to grab the form with the given external ID by form_name. If no match is found--the TRY statement will leave it as NoneType
                            refValue.record_reference.add(Form.objects.all().filter(form_name=aKey)[0])
                            refValue.save()
                        except:
                            logger.info( "No Ref Match found.")
                logger.info( "333 Just making sure things are working still....where's the stop point?"   )
                #When we are fininshed, update the progressData to show that
                progressData.jsonString = '{"row_index":"'+str(row_index)+'","is_complete":"True", "row_total":"'+post_data.get('row_total')+'"}'
                progressData.is_complete = True
                progressData.save()
                
                return HttpResponse('{"MESSAGE":"Finished the import!"}',content_type="application/json")    
                
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"False", "row_total":"0", "row_timer":"0"}',content_type="application/json")     

        
    #=======================================================#
    #   ACCESS LEVEL :  4      RUN_FORM_TYPE_IMPORTER()
    #=======================================================#       
    def run_form_type_importer(self, request):
        #******************************************#
        ACCESS_LEVEL = 4
        PROJECT = request.user.permissions.project
        #******************************************#   
        
        #-------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # This API Endpoint takes an argument for a CSV file, HttpContext(e.g. context kwargs passed to the HttpResponse like pk values),
        # -->and finally the POST data submitted by the form_type_importer view. It will match POST column header data customized by
        # -->the user to columns in the CSV file and automatically generate, both a new FormType, and a new Form for each row of the
        # -->CSV file with all the necessary RecordAttribute/ReferenceType's and Values
        #
        # *This function is the bread and butter of importing legacy or foreign database data into the system through CSV files
        # *It uses a CSV file that has been converted into JSON of key:value pairs and passed as a POST argument
        # *This is done as an AJAX request to show progresss of the database import
        #-------------------------------------------------------------------------------------------------------------------------------------------------------------------
        
        #We have the column headers saved in a coded format in the passed POST header argument 'post_data'
        #-------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # form_type_name            --> On the Import Form, this is the name of the new Form Type
        #
        #   *Where (n) is the associated key value for the original header for each row of CSV data, e.g. if n == Object No, then the value in the csv file 
        #   *row for the key "Object No" will match
        # record__(n)__name         --> This represents the RecordAttribute/ReferenceType name field for the model
        # record__(n)__reftype      --> This represents the RecordReferenceType referenced FormType is applicable
        # record__(n)__ismainID     --> This is a fake Bool value. It either exists, which means this particular (n) column is to be used for the form_num/form_name field
        #                               -->or it isn't added to the POST data because it wasn't selected and therefore does not exist, and therefore this particular column
        #                               -->is a RecordAttributeType rather than a RecordReferenceType
        # record__(n)__isreference  --> This is a fake Bool value. It either exists, which means the particular (n) column is to be treated as a RecordReferenceType
        #                               -->or it isn't added to the POST data because it wasn't selected and therefore does not exist, and therefore this particular column
        #                               -->is a RecordAttributeType rather than a RecordReferenceType
        #
        #-------------------------------------------------------------------------------------------------------------------------------------------------------------------
        
        
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            #Make sure we only take POST requests        
            if request.method == 'POST':        
        
               
                #Make the AJAX Request Data Model for subsequent AJAX calls
                progressData = AJAXRequestData(uuid=request.POST.get('uuid'), jsonString='{"row_index":"0","row_total":"0","is_complete":"False","row_timer":"0"}')
                progressData.save()
                
                #kwargs.update({'uuid':progressData.pk})
                
                post_data = request.POST
                
                
                #timerA = time.process_time()
                #logger.info( "Starting Clock: " + str(timerA))
                #Make sure we escape the newline characters from the json string--jscript didn't do it automatically when concatenating the rows together in the clinet-side script
                #We also have to replace all \t 's  in the json strings before loading them because JSON doesn't allow literal TABS --we need to escape them with a "\\"
                encoded_str = post_data.get('csv_json').replace('\t', '\\t').replace('\r', '\\r').replace('\n', '\\n').encode('utf-8').decode('utf-8')
                csv_json = json.loads(encoded_str)
                
                logger.info( post_data)
               
                #setup Dictionaries for post import  self-referential needs
                #setup a dict for hierarchy value
                hierarchyDict = {}
                #setup a recordreferencevalue dictionary for the form type if a particular reference is self-referencing to this same form type
                selfReferenceList = []
                
                #Create a new form type from form_type_name <Input> and attach to current Project #
                newFormType = FormType()
                #Add the project to the FormType relation 'project' and make sure to use the users PROJECT
                newFormType.project = PROJECT
                #Add the name of the FormType to 'form_type_name' model field
                newFormType.form_type_name = post_data['form_type_name']
                
                #add the appropriate flag for the formtype's hard-coded type: e.g. is it a media type? 
                #We're checking whether or not the drop down select on the importer form has chosen a 'media type' if it has, then
                #--we can assume it's a Media Form Type, and proceed. If it isn't one of the int values for a media type, then it's a normal form type
                #--it's also worth noting that Media Form Type's cannot be added to Form Type Groups--they are their own unique Form Type Group
                #--The importer will skip the Form Type Group import if it is a Media Type.
                if post_data.get('ft_media_type') != '-1': #
                    newFormType.type = 1
                    newFormType.media_type = post_data.get('ft_media_type')    
                else: #we'll assume if none of the media types are selected, that it's just a normal form type and proceed
                    newFormType.type = 0        
                    #Update the form type's group
                    #If it's a new group
                    if post_data.get('ft_group') == 'NEW':
                        #Create a new formtype group 
                        
                        newFormTypeGroup = FormTypeGroup(name=post_data.get('ft_group_new'), project=PROJECT)
                        
                        newFormTypeGroup.save()
                        newFormType.form_type_group = newFormTypeGroup
                    #Otherwise it's not a new group and not being removed so use the provided value
                    elif post_data.get('ft_group') != 'NONE':
                        newFormType.form_type_group = FormTypeGroup.objects.get(pk=post_data.get('ft_group'))

                    #update the formtypes status as hierarchical
                    if 'is_hierarchical' in post_data:
                        newFormType.is_hierarchical = True

                    else:
                        newFormType.is_hierarchical = False
                #set privacy of form type
                newFormType.is_public = False
                
                #save the FormType to give it a new pk in the database
                newFormType.save()
                #Each row in the CSV file represents a new 'Form' of the 'newFormType'
                #Let's make a 'row' counter to help with indexing through the CSV file
                row_index = 0    
                #Let's make an incremental counter for record type orders
                order_counter = 1
                #I'm also going to make a List() of AttributeTypes/ReferenceTypes. This is done so that
                #after 1 iteration of the importer loop, the reference types/ attribute types are already created. We
                #don't need to create them for every row--so after the first row, we reference this list for the reference
                # and attribute values
                typeList = {}
                
                logger.info( "Just making sure things are working still....where's the stop point?")
                
                keepAliveTimer = time.process_time()
                #logger.info( "Starting row loop: " + str(timerB) + "   Time elapsed = " + str(timerB-timerA))
                #For each row of the CSV
                for row in csv_json:
                    #logger.info( "222 Just making sure things are working still....where's the stop point?")
                    timerBeginRow = time.process_time()
                    #logger.info( "Starting a new row: " + str(timerBeginRow))
                    #If we are past index '0' then let's continue with the rest of the importer
                    
                    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ CREATE NEW FORM @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                    #-----------------------------------------------------------------------------------------------------------
                    #Create a new Form and attach the newly created 'FormType' to 'form_type' in the 'Form' model
                    newForm = Form()
                    newForm.form_type = newFormType
                    newForm.project = PROJECT
                    newForm.is_public = False
                    #we will worry about adding the form_name / form_number later
                    #save the Form to give it a pk value in the database. Now we can use it for variable assignments later
                    newForm.save()
                    
                    #For each column in the CSV Row and the column headers (essentially all the dict/JSON key values
                    #We setup a bool test to determine if we find a primary id that is selected or not.
                    #--if we don't find a primary id by the time we end the list, set the form's name to the current row counter number
                    foundAMainID = False
                    for key, value in row.items():
                        #timerJ = time.process_time()
                        #logger.info( "Starting col loop: " + str(timerJ))
                        #First check if this column is the unique ID for this form
                        #we'll see if it is by checking the POST_DATA if 'record__(n)__ismainID' exists
                        if 'record__'+str(key)+'__ismainID' in post_data:
                            #If it is, then add this column value to the current Form's "form_number" or "form_name"
                            #Try to add it as an int first, otherwise add it as the form name
                            foundAMainID = True
                            try:
                                newForm.form_number = int(value)
                                newForm.form_name = value
                            except:
                                newForm.form_name = value
                            #save the Form
                            newForm.save()
                        
                        #If it is not the ID field:
                        #If the current column is the value to reference a hierarchy field then add it to our hierarchy Dict
                        #--we will process this later, because if we try now, not all of the self-referencing forms will be imported yet
                        #--and this will more than likely miss a number of them
                        elif 'record__'+str(key)+'__ishierarchy' in post_data:
                            #We add the current Form's pk value for the key, and the reference pk as the value
                            hierarchyDict[str(newForm.pk)] = value
                            
                        #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@  ADD A RECORD REFERENCE TYPE @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                        #------------------------------------------------------------------------------------------------------------------------
                        #Test if it is a reference type by checking the POST_DATA if 'record__(n)__isreference' exists
                        #If it is a reference Type:
                        elif 'record__'+str(key)+'__isreference' in post_data:
                            #We want to make sure we only create the ReferenceType's once--otherwise we populate the database with several 
                            #unecessary copies and relations that muddy everything. So if we're past the first row/iteration of the JSON, the reference types are
                            #already created and stored in a list to reference after
                            if row_index < 1:
                                #create a new FormRecordReferenceType and set "record_type" variable to the header column user-given name value
                                newFormRecordReferenceType = FormRecordReferenceType()
                                newFormRecordReferenceType.project = PROJECT
                                newFormRecordReferenceType.is_public = False
                                newFormRecordReferenceType.record_type = post_data.get('record__'+str(key)+'__name')
                                #also set "form_type_parent" to the current formType we are importing
                                newFormRecordReferenceType.form_type_parent = newFormType
                                #now set "form_type_reference" to the selected FormTypeReference value in the current importer Column
                                #if the value == 'default' then set reference to this same FormType
                                if post_data.get('record__'+str(key)+'__reftype') == 'default':
                                    newFormRecordReferenceType.form_type_reference = newFormType
                                #otherwise set it to the given pk value of a FormType object
                                else:
                                    newFormRecordReferenceType.form_type_reference = FormType.objects.get(pk=post_data.get('record__'+str(key)+'__reftype'))
                                #Set an arbitrary initial order for the type
                                newFormRecordReferenceType.order_number = order_counter
                                order_counter += 1
                                #save the Record Reference Type
                                newFormRecordReferenceType.save()
                                #add it to the list so that the reference value can reference it
                                typeList[key] = newFormRecordReferenceType
                            #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@  ADD A RECORD REFERENCE VALUE @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                            #-------------------------------------------------------------------------------------------------------------------------
                            #Create a new RecordReferenceValue
                            newFormRecordReferenceValue = FormRecordReferenceValue()
                            newFormRecordReferenceValue.project = PROJECT
                            newFormRecordReferenceValue.is_public = False
                            #set the "external_key_reference" to the column value of the csv row
                            newFormRecordReferenceValue.external_key_reference = value
                            #set the "form_parent" to the current row's Form
                            newFormRecordReferenceValue.form_parent = newForm                              
                            #set the "record_reference_type" to the current RecordReferenceType
                            logging.info("line626      " + str(typeList[key].form_type_reference) + "           :: " + newFormRecordReferenceValue.external_key_reference)
                            newFormRecordReferenceValue.record_reference_type = typeList[key]
                            #save the value to give it a pk value
                            newFormRecordReferenceValue.save()
                            #logging.info("We are about to check the reference for:    " + str(newFormRecordReferenceValue))
                            #If this reference is self-referencing to the same form formtype we're importing, then similar to the hierchy references,
                            #--we need to store a list of the reference value objects to load once the entire form type has been imported. We don't need key values because
                            #--the external key reference is already saved for the lookup on the model.
                            #--I'm using the objects rather pk values because that will save us time on SQL queries later
                            if post_data.get('record__'+str(key)+'__reftype') == 'default':
                                selfReferenceList.append(newFormRecordReferenceValue)
                            else:
                                #Now we need to set the value for "record_reference" which will involve a query 
                                #And since the external key could contain multiple values, we need to split them by the comma delimeter
                                #logging.info(newFormRecordReferenceValue.external_key_reference + "  : BEFORE SPLIT")
                                possibleRefValues = newFormRecordReferenceValue.external_key_reference.split(",")    
                                #logging.info(str(possibleRefValues) + "  : SPLIT")
                               
                                #for all forms in the selected FormType reference
                                for aForm in newFormRecordReferenceValue.record_reference_type.form_type_reference.form_set.all().prefetch_related():
                                    #if the current external ID value == to the iterated forms "form_num"
                                    #Make sure we convert the INT form-num to a STR first or it will fail the check

                                    for refValue in possibleRefValues:
                                        if refValue == str(aForm.form_number):
                                            #remove this value from future matches to ensure we don't double add it
                                            possibleRefValues.remove(refValue)
                                            #set the current FormRecordReferenceValue.record_reference to the current form in the loop iteration
                                            newFormRecordReferenceValue.record_reference.add(aForm)
                                #logging.info(newFormRecordReferenceValue.external_key_reference + "  : AFTER SPLIT") 
                            #if there are no matches by the last iteration of the loop,
                            #we can do nothing to leave the record_reference value as "None" (the user can set this later)
                            #This might happen if the user is importing a new form type that references itself, or references
                            #another form type that hasn't yet been imported. The external_key_reference's are still saved
                            #so the user can run another tool to match these keys later once all the Form Types and forms have been
                            #imported through this tool
                            #save the RecordReferenceValue
                            newFormRecordReferenceValue.save()    
                            #timerE = time.process_time()
                            #logger.info( "Ending ref lookup: " + str(timerE) + "   Time elapsed = " + str(timerE-timerD)    )
                        #If it is not a reference type, then we are adding an attribute type instead
                        else:
                            #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@  ADD A RECORD ATTRIBUTE TYPE @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                            #------------------------------------------------------------------------------------------------------------------------
                            #We want to make sure we only create the AttributeType's once--otherwise we populate the database with several 
                            #unecessary copies and relations that muddy everything. So if we're past the first row, the attribute types are
                            #already created and stored in a list to reference after
                            if row_index < 1:
                                #create a new FormRecordAttributeType and set "record_type" variable to the header column name
                                newFormRecordAttributeType = FormRecordAttributeType()
                                newFormRecordAttributeType.record_type = post_data.get('record__'+str(key)+'__name')
                                newFormRecordAttributeType.project = PROJECT
                                newFormRecordAttributeType.is_public = False
                                #also set "form_type" to the current formType we are importing
                                newFormRecordAttributeType.form_type = newFormType
                                #Set an arbitrary initial order for the type
                                newFormRecordAttributeType.order_number = order_counter
                                order_counter += 1
                                #save the RecordAttributeType
                                newFormRecordAttributeType.save()
                                #add the attributeType to the typeList so that the attribute value can reference it
                                typeList[key] = newFormRecordAttributeType
                            #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@  ADD A RECORD Attribute VALUE @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                            #-------------------------------------------------------------------------------------------------------------------------
                            #Create a new RecordAttributeValue
                            newFormRecordAttributeValue = FormRecordAttributeValue()
                            newFormRecordAttributeValue.project = PROJECT
                            newFormRecordAttributeValue.is_public = False
                            #set the "record_value" to the column value of the csv row
                            newFormRecordAttributeValue.record_value = value
                            #set the "form_parent" to the current row's Form
                            newFormRecordAttributeValue.form_parent = newForm
                            #set the "record_attribute_type" to the current RecordAttributeType
                            newFormRecordAttributeValue.record_attribute_type = typeList[key]
                            #save the RecordAttributeValue
                            newFormRecordAttributeValue.save()
                        #timerK = time.process_time()
                        #logger.info( "End of col loop: " + str(timerK) + "   Time elapsed = " + str(timerK-timerJ))
                    #If we didn't find a primary key for this row/form, then add the rox index as the incremental form name/number
                    if foundAMainID == False:
                        newForm.form_number = int(row_index+1)
                        newForm.form_name = str(row_index+1)
                        newForm.save()
                        foundAMainID = False
                    row_index += 1
                    #Upload our progress data object with the current row
                    timerFinishRow = time.process_time()
                    #logger.info( "Ending a row: " + str(timerF) + "   Time elapsed since row start = " + str(timerF-timerC))
                    #We need to update the progessData model because it is updated by another thread as well
                    #--Otherwise this will just ignore the  'keep_alive' flag and quit after 2 timer checks
                    #--I'm not entirely sold on this method--There's a slight....itty bitty...teensy weensy...chance that the other thread
                    #--might be trying to update the AJAX model at the exact time and will be missed here--but as of now, I can't think of a
                    #--better solution and I'm REALLY over working on this importer today.
                    progressData = AJAXRequestData.objects.get(pk=progressData.pk)
                    progressData.jsonString = '{"row_index":"'+str(row_index)+'","is_complete":"False","row_total":"'+post_data.get('row_total')+'","row_timer":"'+str(timerFinishRow-timerBeginRow)+'"}'

                    #We want to make sure that our timer is set at 5 second itnervals. The AJAX script sets the keep alive variable to True
                    #   --every 1 second. I've set it to 5 seconds here to account for any delays that might occur over the network.
                    #   --Every 5 seconds, this script resets the keep_alive variable to 'False', if it is already False--that means the user exited
                    #   --the process on their AJAX end so we should stop adding this to the database and delete what we've already done.
                    #logger.info( str(time.process_time()) + "  - " + str(keepAliveTimer) + "    :    " + str(progressData.keep_alive))
                    if time.process_time() - keepAliveTimer > 5:
                        logger.info( str (time.process_time() - keepAliveTimer) + "  : We are at the 5 second interval!  " + str(row_index) )
                        #restart the keepAlive timer to the current time
                        keepAliveTimer = time.process_time()
                        #delete the data if the user's AJAX end is unresponsive
                        if progressData.keep_alive == False:
                            logger.info( "We are deleting our progress now--wish us luck!")
                            newFormType.delete()
                            progressData.delete()
                            try:
                                newFormTypeGroup.delete()
                            except:
                                #break from loop
                                break
                            #break from loop
                            break
                        else:
                            progressData.keep_alive = False
                    progressData.save()
                #Now Update the hierchical references if they exist
                #This forloop will only run if the hierarchyDict has been appended to already
                for key, value in hierarchyDict.items():
                    formToModify  =  Form.objects.get(pk=key)
                    try:#Essentially we are trying to grab the form with the given form_name. If no match is found--the TRY statement will leave it as NoneType
                        formToModify.hierarchy_parent = Form.objects.all().filter(form_name=value)[0]
                        #logger.info( "Admin: Line 681: WHAT'S The Name?: " + formToModify.hierarchy_parent)
                        formToModify.save()
                    except:
                        logger.info( "No Hierarchy Match found.")
                #Now Update the self references if they exist
                #This forloop will only run if the selfReferenceList has been populated
                for refValue in selfReferenceList:
                    #Remember that some external key references may be multi-values that are comma seperated, so let's try splitting them by comma
                    #--and looping through them appropriately
                    key_list = refValue.external_key_reference.split(',')
                    for aKey in key_list:
                        try:#Essentially we are trying to grab the form with the given external ID by form_name. If no match is found--the TRY statement will leave it as NoneType
                            refValue.record_reference.add(Form.objects.all().filter(form_name=aKey)[0])
                            refValue.save()
                        except:
                            logger.info( "No Ref Match found.")
                logger.info( "333 Just making sure things are working still....where's the stop point?"   )
                #When we are fininshed, update the progressData to show that
                progressData.jsonString = '{"row_index":"'+str(row_index)+'","is_complete":"True", "row_total":"'+post_data.get('row_total')+'"}'
                progressData.is_complete = True
                progressData.save()
                
                return HttpResponse('{"MESSAGE":"Finished the import!"}',content_type="application/json")    
                
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"False", "row_total":"0", "row_timer":"0"}',content_type="application/json")     

                
    #=======================================================#
    #   ACCESS LEVEL :  4      RUN_FORM_TYPE_FORM_IMPORTER()
    #=======================================================#       
    def run_form_type_form_importer(self, request):
        #******************************************#
        ACCESS_LEVEL = 4
        PROJECT = request.user.permissions.project
        #******************************************#   
        
        #-------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # This API Endpoint takes an argument for a CSV file, HttpContext(e.g. context kwargs passed to the HttpResponse like pk values),
        # -->and finally the POST data submitted by the formtype_form_importer view. It will match POST column header data customized by
        # -->the user to columns in the CSV file and automatically generate, both a new FormType, and a new Form for each row of the
        # -->CSV file with all the necessary RecordAttribute/ReferenceType's and Values
        #
        # *This function is for importing a separate CSV of "NEW" forms to an existing formtype with the same RTYPES in the header
        #   --if the RTYPE doesn't exist, it will cease the import and delete everything it made upto that point
        # *It uses a CSV file that has been converted into JSON of key:value pairs and passed as a POST argument
        # *This is done as an AJAX request to show progresss of the database import
        #-------------------------------------------------------------------------------------------------------------------------------------------------------------------
        
        #We have the column headers saved in a coded format in the passed POST header argument 'post_data'
        #-------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # 
        #
        #   *Where (n) is the associated key value for the original header for each row of CSV data, e.g. if n == Object No, then the value in the csv file 
        #   *row for the key "Object No" will match
        # record__(n)__name         --> This represents the RecordAttribute/ReferenceType name field for the model
        # record__(n)__reftype      --> This represents the RecordReferenceType referenced FormType is applicable
        # record__(n)__ismainID     --> This is a fake Bool value. It either exists, which means this particular (n) column is to be used for the form_num/form_name field
        #                               -->or it isn't added to the POST data because it wasn't selected and therefore does not exist, and therefore this particular column
        #                               -->is a RecordAttributeType rather than a RecordReferenceType
        # record__(n)__isreference  --> This is a fake Bool value. It either exists, which means the particular (n) column is to be treated as a RecordReferenceType
        #                               -->or it isn't added to the POST data because it wasn't selected and therefore does not exist, and therefore this particular column
        #                               -->is a RecordAttributeType rather than a RecordReferenceType
        #
        #-------------------------------------------------------------------------------------------------------------------------------------------------------------------
        
        
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            #Make sure we only take POST requests        
            if request.method == 'POST':        
        
               
                #Make the AJAX Request Data Model for subsequent AJAX calls
                progressData = AJAXRequestData(uuid=request.POST.get('uuid'), jsonString='{"row_index":"0","row_total":"0","is_complete":"False","row_timer":"0"}')
                progressData.save()
                
                #kwargs.update({'uuid':progressData.pk})
                
                post_data = request.POST
                
                
                #timerA = time.process_time()
                #logger.info( "Starting Clock: " + str(timerA))
                #Make sure we escape the newline characters from the json string--jscript didn't do it automatically when concatenating the rows together in the clinet-side script
                #We also have to replace all \t 's  in the json strings before loading them because JSON doesn't allow literal TABS --we need to escape them with a "\\"
                #logger.info( post_data.get('csv_json').encode('utf-8').replace('\t', '\\t').replace('\r', '\\r').replace('\n', '\\n'))
                logger.info( request.POST['csv_json'][0:1000])
                logger.info( request.POST['csv_json'][7932427:7934427] + " : " + request.POST['csv_json'][7933427])
                csv_json = json.loads(post_data.get('csv_json').encode('utf-8').replace('\t', '\\t').replace('\r', '\\r').replace('\n', '\\n'))
                #response = HttpResponse(post_data.get('csv_json'), content_type='text/plain')
                #response['Content-Disposition'] = 'attachment; filename="test__'+request.user.username+'.txt"'
                #return response
                #logger.info( post_data)
               
                #setup Dictionaries for post import  self-referential needs
                #setup a dict for hierarchy value
                hierarchyDict = {}
                #setup a recordreferencevalue dictionary for the form type if a particular reference is self-referencing to this same form type
                selfReferenceList = []
                
                currentFormType = FormType.objects.get(pk=request.POST['formtype_pk'])
                
                availableFRATs = currentFormType.formrecordattributetype_set.all()
                availableFRRTs = currentFormType.ref_to_parent_formtype.all()
                
                #queue them up in memory
                logger.info( len(availableFRATs))
                logger.info( len(availableFRRTs))
                
                #Make a dictionary based with the RTYPE names and their objects as values
                FRATs = {}
                FRRTs = {}
                
                for frat in availableFRATs:
                    FRATs[frat.record_type] = frat
                for frrt in availableFRRTs:
                    FRRTs[frrt.record_type] = frrt
                logger.info( FRATs    )
                # $$$SECURITY$$$ If the formtype requested is not part of this user's project, then exist immediately with a warning
                if currentFormType.project.pk == PROJECT.pk:
                
                    #Let's keep track of all the forms we make to delete them all if anything goes wrong
                    allNewForms = []
                    
                    #Each row in the CSV file represents a new 'Form' of the 'currentFormType'
                    
                    #Let's make a 'row' counter to help with indexing through the CSV file
                    row_index = 0    
                    
                    #Let's make an incremental counter for record type orders
                    order_counter = 1                   
                    logger.info( "Just making sure things are working still....where's the stop point?")
                    keepAliveTimer = time.process_time()
                    try:
                        #For each row of the CSV
                        for row in csv_json:
                            row_index += 1
                            #logger.info( "222 Just making sure things are working still....where's the stop point?")
                            timerBeginRow = time.process_time()
                            #logger.info( "Starting a new row: " + str(timerBeginRow))
                            #If we are past index '0' then let's continue with the rest of the importer
                            
                            #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ CREATE NEW FORM @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                            #-----------------------------------------------------------------------------------------------------------
                            #Create a new Form and attach the newly created 'FormType' to 'form_type' in the 'Form' model
                            newForm = Form()
                            newForm.form_type = currentFormType
                            newForm.project = PROJECT
                            newForm.is_public = False
                            #we will worry about adding the form_name / form_number later
                            #save the Form to give it a pk value in the database. Now we can use it for variable assignments later
                            newForm.save()
                            logger.info( "NEW Form PK" + str(newForm.pk))
                            #Add this form to our form list to delete if anything goes wrong
                            allNewForms.append(newForm)
                            
                            col_index = 0
                            
                            #For each column in the CSV Row and the column headers (essentially all the dict/JSON key values
                            #We setup a bool test to determine if we find a primary id that is selected or not.
                            foundAMainID = False
                            for key, value in row.items():
                                col_index += 1
                                #timerJ = time.process_time()
                                #logger.info( "Starting col loop: " + str(key) + " : " + str(value))
                                #First check if this column is the unique ID for this form
                                #we'll see if it is by checking the POST_DATA if 'record__(n)__ismainID' exists
                                if 'record__'+str(key)+'__ismainID' in post_data:
                                    logger.info( "FOUND MAIN ID: " + key)
                                    #If it is, then add this column value to the current Form's  "form_name"
                                    foundAMainID = True
                                    newForm.form_name = value
                                    #save the Form
                                    newForm.save()
                                
                                #If it is not the ID field:
                                else:
                                    #Now we need to check if there is a matching FRAT with the attribute header name
                                    try:
                                        #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@  ADD A RECORD Attribute VALUE @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                                        #-------------------------------------------------------------------------------------------------------------------------
                                        #Create a new RecordAttributeValue
                                        currentKey = request.POST['record__'+str(key)+'__name']
                                        #logger.info( currentKey)
                                        newFormRecordAttributeValue = FormRecordAttributeValue()
                                        newFormRecordAttributeValue.project = PROJECT
                                        newFormRecordAttributeValue.is_public = False
                                        #set the "record_value" to the column value of the csv row
                                        newFormRecordAttributeValue.record_value = value
                                        #set the "form_parent" to the current row's Form
                                        newFormRecordAttributeValue.form_parent = newForm
                                        #set the "record_attribute_type" to the current RecordAttributeType
                                        newFormRecordAttributeValue.record_attribute_type = FRATs[currentKey]
                                        #save the RecordAttributeValue
                                        newFormRecordAttributeValue.save()                                   
                                        
                                    #If there isn't a matching FRAT, then look for a matching FRRT with the same header label
                                    except:
                                        try:
                                            #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@  ADD A RECORD REFERENCE VALUE @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                                            #-------------------------------------------------------------------------------------------------------------------------
                                            #Create a new RecordReferenceValue
                                            newFormRecordReferenceValue = FormRecordReferenceValue()
                                            newFormRecordReferenceValue.project = PROJECT
                                            newFormRecordReferenceValue.is_public = False
                                            #set the "external_key_reference" to the column value of the csv row
                                            newFormRecordReferenceValue.external_key_reference = value
                                            #set the "form_parent" to the current row's Form
                                            newFormRecordReferenceValue.form_parent = newForm                              
                                            #set the "record_reference_type" to the current RecordReferenceType
                                            newFormRecordReferenceValue.record_reference_type = FRRTs[request.POST['record__'+str(key)+'__name']]
                                            #store the references to other forms
                                            possibleRefValues = newFormRecordReferenceValue.external_key_reference.split(",")  
                                            #save the value to give it a pk value
                                            newFormRecordReferenceValue.save()   
                                            #if the current external ID value == to the iterated forms "form_num"
                                            #Make sure we convert the INT form-num to a STR first or it will fail the check
                                            for refValue in possibleRefValues:
                                                possibleFormMatch = newFormRecordReferenceValue.record_reference_type.form_type_reference.form_set.filter(form_name=refValue)
                                                if possibleFormMatch.exists():
                                                    #remove this value from future matches to ensure we don't double add it
                                                    possibleRefValues.remove(refValue)
                                                    #set the current FormRecordReferenceValue.record_reference to the current form in the loop iteration
                                                    #no need to resave because it is saved automatically with the add() command
                                                    newFormRecordReferenceValue.record_reference.add(possibleFormMatch[0])                                   

                                            
                                        #If there are no matches, escape early and delete all currently created forms.
                                        except:
                                            logger.info( "QUITTING")
                                col_index += 1                                                            
                                
                                #Upload our progress data object with the current row
                                timerFinishRow = time.process_time()
                                #logger.info( "Ending a row: " + str(timerF) + "   Time elapsed since row start = " + str(timerF-timerC))
                                #We need to update the progessData model because it is updated by another thread as well
                                #--Otherwise this will just ignore the  'keep_alive' flag and quit after 2 timer checks
                                #--I'm not entirely sold on this method--There's a slight....itty bitty...teensy weensy...chance that the other thread
                                #--might be trying to update the AJAX model at the exact time and will be missed here--but as of now, I can't think of a
                                #--better solution and I'm REALLY over working on this importer today.
                                progressData = AJAXRequestData.objects.get(pk=progressData.pk)
                                progressData.jsonString = '{"row_index":"'+str(row_index)+'","is_complete":"False","row_total":"'+post_data.get('row_total')+'","row_timer":"'+str(timerFinishRow-timerBeginRow)+'"}'

                                #We want to make sure that our timer is set at 5 second itnervals. The AJAX script sets the keep alive variable to True
                                #   --every 1 second. I've set it to 5 seconds here to account for any delays that might occur over the network.
                                #   --Every 5 seconds, this script resets the keep_alive variable to 'False', if it is already False--that means the user exited
                                #   --the process on their AJAX end so we should stop adding this to the database and delete what we've already done.
                                #logger.info( str(time.process_time()) + "  - " + str(keepAliveTimer) + "    :    " + str(progressData.keep_alive))
                                if time.process_time() - keepAliveTimer > 5:
                                    logger.info( str (time.process_time() - keepAliveTimer) + "  : We are at the 5 second interval!  " + str(row_index) )
                                    #restart the keepAlive timer to the current time
                                    keepAliveTimer = time.process_time()
                                    #delete the data if the user's AJAX end is unresponsive
                                    if progressData.keep_alive == False:
                                        logger.info( "We are deleting our progress now--wish us luck!")
                                        #This needs to delete ONLY the forms that have been created. Every form created should be added to a temporary list
                                        #   --for this to access and delete
                                        for thisForm in allNewForms:
                                            thisForm.delete()
                                        progressData.delete()
                                        #break from loop
                                        ERROR_MESSAGE += "Client unresponsive, shutting down import."
                                        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"False", "row_total":"0", "row_timer":"0"}',content_type="application/json")   
                                    else:
                                        progressData.keep_alive = False
                                progressData.save()
                            #logger.info( "End of col loop: " + str(timerK) + "   Time elapsed = " + str(timerK-timerJ))
                            #If we didn't find a primary key for this row/form, then add the rox index as the incremental form name/number
                            if foundAMainID == False:
                                newForm.form_name = str(row_index+1)
                                newForm.save()
                                foundAMainID = False
                            logger.info( "NEW Form Name" + str(newForm.form_name))
                        #When we are fininshed, update the progressData to show that
                        progressData.jsonString = '{"row_index":"'+str(row_index)+'","is_complete":"True", "row_total":"'+post_data.get('row_total')+'"}'
                        progressData.is_complete = True
                        progressData.save()
                        return HttpResponse('{"MESSAGE":"Finished the import!"}',content_type="application/json")    
                    except Exception as e:
                        logger.info( "Something happened!!" + str(type(e)) + " : " + str(e.args) + " : " + str(e) )
                        #Delete all forms in the allFormsList
                        for thisForm in allNewForms:
                            thisForm.delete()
                            logger.info( "Something happened!!" + str(type(e)) + " : " + str(e.args) + " : " + str(e) )
                        #create the error message
                        ERROR_MESSAGE += "Error: Something went wrong. Your action has been logged and sent to the admin" + str(type(e)) + " : " + str(e.args) + " : " + str(e) 
                   
            else: ERROR_MESSAGE += "Error: You do not have permission to access this form type from a different project. Your action has been logged and sent to the admin"   
        else: ERROR_MESSAGE += "Error: You do not have permission to access this tool. Your action has been logged and sent to the admin"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"False", "row_total":"0", "row_timer":"0"}',content_type="application/json")     

    #=======================================================#
    #   ACCESS LEVEL :  2      BULK_EDIT_FORMTYPE()
    #=======================================================#        
    def bulk_edit_formtype(self, request):
        #***************#
        ACCESS_LEVEL = 2
        #***************#  
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This Endpoint works in the formtype viewer--it recieves a list of edits based on the form query and processes those edits
        #   --in bulk. E.g. you can edit the rtype of multiple forms, compared to one at a time in an individual form editor
        
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level  
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):        
            try:
                logger.info( request.POST)
                #This will receive post data containing a series of FRAV or FRRVs that need to be edited
                #Just an extra bit of security to ensure this only processes POST data
                if request.method == 'POST':
                    counter = 0
                    logger.info( request.POST)
                    key_list = request.POST['form_data']
                    key_list = json.loads(key_list)
                    logger.info(key_list)
                    for key in key_list:
                        logger.info( key)
                        splitkey = key.split('__')
                        logger.info( "POST SPLIT")
                        if len(splitkey) > 1:
                            if splitkey[0] == 'frav':
                                logger.info( "POST SPLIT FRAV")
                                currentFRAV = FormRecordAttributeValue.objects.get(pk=splitkey[1])
                                currentFRAV.record_value = key_list[key]
                                #Add the user information
                                currentFRAV.modified_by = request.user
                                currentFRAV.save()
                            else:
                                logger.info( "POST SPLIT ELSE")
                                #Sometimes, if 
                                currentFRRV = FormRecordReferenceValue.objects.get(pk=key.splitkey[1])
                                #set our external key to this key value
                                new_external_key = ""
                                #Empty our list of references, and then add them all new here
                                currentFRAV.record_reference.clear()
                                for reference in post_data.getlist(key):
                                    #make sure we add a null check here--the user might not have chosen a referenced form
                                    if reference != '' or reference != None:
                                        currentFRAV.record_reference.add(Form.objects.get(pk=reference))
                                        new_external_key += str(reference) + ","
                                #remove the trailing comma
                                external_key_reference[:-1]
                            counter += 1
                    return HttpResponse('{"message":"Succesfully updated:'+ str(counter) +' field(s) in the database"}', content_type="application/json")
            except Exception as e:
                ERROR_MESSAGE += '"Something happened and the fields did not update in the database. See Error| '+str(e)+'"'
                
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")  

    #=======================================================#
    #   ACCESS LEVEL :  5        MODIFY_PROJECT_USER()
    #=======================================================#
    def modify_project_user(self, request):
        #***************#
        ACCESS_LEVEL = 5
        #***************#
        #------------------------------------------------------------------------------------------------------------------------------------
        #   :::This function is an admin API Endpoint that accepts json data in POST (and ONLY post) and returns a string of JSON through AJAX
        #
        #   !!!!!! It is ESSENTIAL that we create tight security here.!!!!!!! 
        #   -----------------------------------------------------------------
        #       This view HAS to make sure that ONLY users with proper
        #       --access rights can manipulate user accounts. Because User accounts and their OneToOne Permission Model
        #       --control access, only project 'Admins' or (level 5) can actually edit users and create new ones.
        #
        #   Because Django requires high-level permissions on all of its users to access admin functions, I had to implement
        #       --another layer of control. This should work perfectly find and secure. Essentially, ANY user outside a 'Master Admin'
        #       --can ONLY edit members of their own project. This view handles that by automatically forcing this new user to be part
        #       --of the project of the current user's session.
        #
        #   Additionally, If the user doesn't ahve the correct access level of 5 to do this action, nothing will happen and it will
        #       --return an error explaining what occured. This SHOULDN'T happen--because the javascript allowing this is only installed
        #       --on the client IF they already have the permission level--HOWEVER--if this jscript is downloaded off the GIT or some other
        #       --source and inserted into the page(which should only happen if they already HAVE access to some project on this database)--this
        #       --ensuress that no attack is possible.
        #
        #   Finally, SQL injection should be a Null issue here--I do not allow any raw() SQL to be used in any form to date--so any insertions
        #       --should be automatically cleaned by Django's built-in ORM functions
        #-------------------------------------------------------------------------------------------------------------------------------------
        
        #   POST json will contain a list of 'users' that contain several keys
        #   JSON KEYS : "is_new_user" , "username" , "password" , "access_level", "name" , "title", "email"
        
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            #Make sure we only take POST requests
            if request.method == 'POST':
                #Make sure we have the right key in the POST data
                if 'user_change_list' in request.POST:
                    #Let's grab our json Data and convert it to a python Dictionary
                    userJSON = json.loads(request.POST['user_change_list'])
                    logger.info( userJSON)
                    PROGRESS_MESSAGE = ""
                    DELETE_KEYS = ""
                    #Now loop through each 'user' in the dictionary and continue making edits/or create them
                    for aUser in userJSON['userlist']:
                        #We also now need to make sure that there are the bare mininum of keys needed(username, pass, access_level, and edit/create
                        if 'is_new_user' in aUser and 'username' in aUser and 'password' in aUser and 'access_level' in aUser:
                            #NOW *sigh of exhaustion* let's make sure that the user/pass/access_level isn't blank
                            #    --We have to do this, because if someone hacks the jscript--they can force submit a blank input.
                            #    --This shouldn't have deleterious side-effects--but we're not playing around anyway!
                            if aUser['is_new_user'] != "" and aUser['username'] != "" and aUser['password'] != "" and aUser['access_level'] != "":
                               #OKAY! We are all set to create/edit a user
                               
                                #----CREATING A NEW USER    -------------------------------------------------------------
                                if aUser['is_new_user'] == "T":
                                    #We need to make sure there isn't already a username in the database with the submitted name
                                    if User.objects.all().filter(username=aUser['username']).exists() != True:
                                        newUser = User.objects.create_user(username=aUser['username'],password=aUser['password'])
                                    
                                        #ADD ALL STATIC INFORMATION
                                        newUser.is_staff = True
                                        newUser.is_active = True
                                        #newUser.save()
                                        #ADD USER SUBMITTED INFORMATION
                                        #--SECURITY NEEDS: Make sure to ONLY use the project from the user's own Session data that's already been authorized
                                        #--Also make sure the access level is set, and MAKE sure the access_level is an Integer and not a string
                                        isInt = True
                                        try:
                                            newUser.permissions.access_level = int(aUser['access_level'])
                                        except Exception as inst:
                                            isInt = False
                                        if isInt:
                                            newUser.permissions.project = request.user.permissions.project
                                            newUser.permissions.title = aUser['title']
                                            newUser.email = aUser['email']
                                            #figure out names--if there's more than one space first in list is first name--rest is last name
                                            splitName = aUser['name'].split(' ')
                                            newUser.first_name = splitName[0]
                                            lastName = ""
                                                #start at index 1--we don't need the first name
                                            if len(splitName) > 1:
                                                for i in range(1, len(splitName)):
                                                    lastName += splitName[i]
                                                newUser.last_name = lastName
                                            #If all goes well, save the new User to the database
                                            newUser.save()
                                            PROGRESS_MESSAGE += " Made a new user: " + newUser.username + "    ---   "
                                        else:
                                            #Delete the user and add an error message
                                            newUser.delete()
                                            ERROR_MESSAGE += " Uh Oh! Something happened with: the access level submitted when creating a new user!" +  str(inst) +" --You probably tried submitting a non-int for an integer access level?"
                                    else:
                                        ERROR_MESSAGE += "That username already exists!"
                                    
                                #----EDITING AN EXISTING USER    -------------------------------------------------------------
                                elif aUser['is_new_user'] == "F":
                                    #--SECURITY NEEDS: We have to be mindful here of how access is given to PK lookups, e.g. a user
                                    #   --might have injected a different user PK than is part of this project. We'll filter by the
                                    #   --user's own Project PK to ensure ONLY User PKs attached this project can be modified 
                                    #   --This also ensures no SQL injection can be performed
                                    userToEdit = Permissions.objects.all().filter(user__pk=aUser['user_id'], project__pk = request.user.permissions.project.pk)[0].user
                                    #We can only modify a small subset of the user's fields
                                    isInt = True
                                    try:
                                        userToEdit.permissions.access_level = int(aUser['access_level'])
                                    except:
                                        isInt = False
                                    if isInt:
                                        
                                        #First try and edit the user's name--if it's the same as the current name than skip, and if it's different make sure it's not taken
                                        if userToEdit.username != aUser['username']:
                                            if User.objects.all().filter(username=aUser['username']).exists() == False:
                                                userToEdit.username = aUser['username']
                                            else:
                                                #Just give a simple ERROR MESSAGE
                                                ERROR_MESSAGE += " There was a problem with " + userToEdit + "'s username change. The name: "+ aUser['username'] +" already exists in the database! Try choosing a new one"
                                        userToEdit.permissions.title = aUser['title']
                                        userToEdit.email = aUser['email']      
                                        #figure out names--if there's more than one space first in list is first name--rest is last name
                                        splitName = aUser['name'].split(' ')
                                        if len(splitName) > 0:
                                            userToEdit.first_name = splitName[0]
                                            lastName = ""
                                            #start at index 1--we don't need the first name
                                            for i in range(1, len(splitName)):
                                                lastName += " " + splitName[i]
                                            userToEdit.last_name = lastName
                                        else:
                                            userToEdit.first_name = aUser['name']
                                            userToEdit.last_name = ""
                                        #If all goes well, save the new User to the database
                                        userToEdit.save()
                                        PROGRESS_MESSAGE += " Edited a user: " + userToEdit.username + "    ---   "
                                    else:
                                        ERROR_MESSAGE += " Uh Oh! Something happened with: the access level submitted  when editing a new user"  + " --You probably tried submitting a non-int for an integer access level?"
                                    
                                #----DELETING AN EXISTING USER    -------------------------------------------------------------
                                elif aUser['is_new_user'] == 'DELETE':
                                    #--SECURITY NEEDS: We have to be mindful here of how access is given to PK lookups, e.g. a user
                                    #   --might have injected a different user PK than is part of this project. We'll filter by the
                                    #   --user's own Project PK to ensure ONLY User PKs attached this project can be modified
                                    #   --This also ensures no SQL innjection can be performed
                                    userToDelete = Permissions.objects.all().filter(user__pk=aUser['user_id'], project__pk = request.user.permissions.project.pk)[0].user
                                    logger.info( str(request.user.permissions.project.pk) + " --- " + str(aUser['user_id']))
                                    logger.info( userToDelete)
                                    #userToDelete = userToDelete[0].user
                                    #userToDelete = request.user.permissions.project.permissions_set.all().filter(user__pk = aUser['user_id'])[0].user
                                    logger.info( userToDelete.username + " : " + str(userToDelete.permissions.project))
                                    PROGRESS_MESSAGE += " DELETED a user: " + userToDelete.username + "    ---   "
                                    DELETE_KEYS+= '"DELETED_'+aUser['user_id']+'":"'+ aUser['user_id'] +'",'
                                    userToDelete.delete()
                                
                                else:    
                                    ERROR_MESSAGE += "Error: "+ aUser['username'] +" :  is_edit="+ aUser['is_new_user']+"  :  Hmm--We can't figure out if you're editing or creating a user, something may have happened to the POST data. You didn't try and hack it did you?"
                            else:
                                ERROR_MESSAGE += "Error: You are missing required fields that seem to be blank"
                        else:
                            ERROR_MESSAGE += "Error: You are missing required json keys to continue"
                    #Remove the trailing comma from our DELETE_KEYS if they exist
                    if len(DELETE_KEYS) > 0:
                        DELETE_KEYS = DELETE_KEYS[:-1]
                        DELETE_KEYS = "," + DELETE_KEYS
                    if ERROR_MESSAGE == "":    
                        #Because user objects do not have a last modified/date modified field, we will log each time these occur to the log files in case of any issues that arise
                        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), request.user.username + ': has made user changes --: ' + PROGRESS_MESSAGE, request.META)
                        #Now return a successful JSON response back to the request, if we successfully navigated ALL users
                        return HttpResponse('{"Message":"Successful! '+ PROGRESS_MESSAGE +'"'+ DELETE_KEYS+ '}', content_type="application/json")
                    else:
                        #Because user objects do not have a last modified/date modified field, we will log each time these occur to the log files in case of any issues that arise
                        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), request.user.username + ': has made user changes --: ' + PROGRESS_MESSAGE, request.META)
                        #Return a semi-successful JSON response--It may have added some users, but there may have been errors too
                        return HttpResponse('{"Message":"Successful!--but with errors =( '+ PROGRESS_MESSAGE + ' !!!! ' + ERROR_MESSAGE +' "}', content_type="application/json")
                ERROR_MESSAGE += "Error: You are missing required information in the POST header to create a new User for your project."
            ERROR_MESSAGE += "Error: You have not submitted through POST"
        else:  ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")  
        
    #=======================================================#
    #   ACCESS LEVEL :  2      SAVE_FORM_CHANGES()
    #=======================================================#   
    def save_form_changes(self, request):
        #***************#
        ACCESS_LEVEL = 2
        #***************#
        #------------------------------------------------------------------------------------------------------------------------------------
        #:::This function edits a form. In order to maintain integrity when editing a form--we need to assume
        #   --the worst. In this case someone may be atempting to pass a different pk into this endpoint and edit a new form there.
        #   --this isn't terribly problematic in terms of security--if someone can access this function then they can edit any form in
        #   --their project. We just need to make sure they can ONLY affect forms in their own project. Performing a simple check on the
        #   --form parent pks the submitted RTYPES are child'd to should be enough to deter these shenanigans--but once again--the worst someone can
        #   --do if hijacking this endpoint is add/change new data. They can't delete anything.
        #------------------------------------------------------------------------------------------------------------------------------------
        
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            #Make sure we only take POST requests
            if request.method == 'POST':                        
                logger.info( request.POST)
                post_data = request.POST
                #$$$ SECURITY $$$ Make sure we can ONLY access this form for editing if it is within the user's project space
                formToEdit = Form.objects.get(pk=post_data['form_id'])
                if formToEdit.project.pk == request.user.permissions.project.pk:
                    form_type = formToEdit.form_type
                    #Update the form's basic attributes
                    #Figure out if the input field is a number(int) or a string label
                    #*I'm not particulary fond of using try/catch's to control logic, but apparently it is the
                    #"pythonic" thing to do looking online and the Python Core uses this often it seems
                    try:
                        formToEdit.form_name = post_data.get('form_number')
                        formToEdit.form_number = int(post_data.get('form_number'))
                    except:
                        formToEdit.form_name = post_data.get('form_number')
                        formToEdit.form_number = None            
                    formToEdit.form_geojson_string = post_data.get('form_geojson_string')
                    #Update the hierchical parent reference if relevant
                    if form_type.is_hierarchical:
                        if post_data.get('hierarchical_reference') == 'NONE':
                            formToEdit.hierarchy_parent = None
                        else:
                            formToEdit.hierarchy_parent = Form.objects.get(pk=post_data.get('hierarchical_reference'))

                   
                    for key in post_data:
                        splitKey = key.split("__")
                        #Update all of the form's FormRecordReferenceTypes
                        if len(splitKey) > 1:
                            if len(splitKey) == 2: 
                                code,type_pk = splitKey
                                logger.info( "Getting Close: " + code + " : " + type_pk)
                                
                                #Update all of the form's FormRecordAttributeValues
                                if code == "frav":
                                    currentValue = FormRecordAttributeValue.objects.get(pk=type_pk)
                                    # $$$ SECURITY $$$: Before we make any changes, we need to make sure we are editing a record value that has
                                    #   --the same project parent as the user. The user could inject pks from other projects into this and randomly
                                    #   --attack data.
                                    if currentValue.project.pk == request.user.permissions.project.pk:
                                        currentValue.record_value = post_data[key]
                                        #Add the user information
                                        currentValue.modified_by = request.user
                                        currentValue.save()
                                    else:
                                        ERROR_MESSAGE += "You have attempted to edit a form with an attribute record type that is not part of your project space."
                                        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
                                        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")                                         
                                #If we're editing this particular reference
                                elif code == "frrv":
                                    currentReferenceValue = FormRecordReferenceValue.objects.get(pk=type_pk)
                                    # $$$ SECURITY $$$: Before we make any changes, we need to make sure we are editing a record value that has
                                    #   --the same project parent as the user. The user could inject pks from other projects into this and randomly
                                    #   --attack data.
                                    if currentReferenceValue.project.pk == request.user.permissions.project.pk:
                                        #first clear the manytomany field
                                        currentReferenceValue.record_reference.clear()
                                        #loop through all available selections and add them to the manytomany field
                                        for reference in post_data.getlist(key):
                                            logger.info( reference + "  <!----- ADDING THIS REF")
                                            #make sure we add a null check here--the user might not have chosen a referenced form
                                            if reference != '':
                                                currentReferenceValue.record_reference.add(Form.objects.get(pk=reference))
                                            logger.info( str(currentReferenceValue.record_reference) + "  <!----- ADDED THIS REF")
                                        #Add the user information
                                        currentReferenceValue.modified_by = request.user    
                                        if ('frrv__'+type_pk+'__ext') in request.POST: 
                                            currentReferenceValue.external_key_reference = request.POST['frrv__'+type_pk+'__ext']  
                                        else:
                                            currentReferenceValue.external_key_reference = request.POST[key]                                            
                                        #save the reference value
                                        currentReferenceValue.save()  
                                    else:
                                        ERROR_MESSAGE += "You have attempted to edit a form with a reference record type that is not part of your project space."
                                        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
                                        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")  
                                elif code == "frrvNEW":
                                    #If there isa 'new' FRRV needed, that means the formtype was created manually and not through the csv importer. This is fine, we just
                                    #need to make a new one now and add the necessary attributes to it.
                                    newFRRV = FormRecordReferenceValue()
                                    newFRRV.project = request.user.permissions.project
                                    newFRRV.created_by = request.user
                                    newFRRV.modified_by = request.user
                                    newFRRV.record_reference_type = FormRecordReferenceType.objects.get(pk=type_pk)
                                    newFRRV.form_parent = formToEdit
                                    if ('frrvNEW__'+type_pk+'__ext') in request.POST: 
                                        newFRRV.external_key_reference = request.POST['frrvNEW__'+type_pk+'__ext']
                                    else:
                                        newFRRV.external_key_reference = request.POST[key]
                                    #We have to save the new FRRV to the SQL database before adding new references I think
                                    newFRRV.save()
                                    for reference in post_data.getlist(key):
                                        logger.info( reference + "  <!----- ADDING THIS REF")
                                        #make sure we add a null check here--the user might not have chosen a referenced form
                                        if reference != '':
                                            newFRRV.record_reference.add(Form.objects.get(pk=reference))
                                        logger.info( str(newFRRV.record_reference) + "  <!----- ADDED THIS REF"   )
                                    newFRRV.save()
                                #If we're dealing with a NEW FRAV -- it will be coded as 'frat' instead of 'frav'
                                elif code == "frat":
                                    currentFRAT = FormRecordAttributeType.objects.get(pk=type_pk)
                                    #$$$ SECURITY $$$ -- We need make sure they are trying to add rtype values that are attached to this project
                                    #if they are not, then show an error page and delete this current form.
                                    if currentFRAT.project.pk == request.user.permissions.project.pk:
                                        newformrecordattributevalue = FormRecordAttributeValue(record_value = post_data[key])
                                        newformrecordattributevalue.form_parent=formToEdit
                                        newformrecordattributevalue.record_attribute_type=currentFRAT
                                        #Add the user information - We only set created by in endpoints that create the model for the first time
                                        newformrecordattributevalue.created_by = request.user
                                        newformrecordattributevalue.modified_by = request.user
                                        newformrecordattributevalue.save()
                                    else:
                                        ERROR_MESSAGE += "You have attempted to add a form with a attribute record type that is not part of your project space."
                                        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
                                        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json") 
                    # If we've managed to get this far, then save the form changes. Otherwise some error occured and nothing should be saved
                    #   --in order to maintain database integrity -- this will still not affect individual values--but it will stop some things from changing.
                    #Add the user information
                    formToEdit.modified_by = request.user
                    formToEdit.save()
                    #SUCCESS!!
                    return HttpResponse('{"MESSAGE":"SUCCESS!"}',content_type="application/json") 
                ERROR_MESSAGE += "Error: You are attempting to access a form outside your project space!"                            
            ERROR_MESSAGE += "Error: You have not submitted through POST"
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")      

        
        
        
    #=======================================================#
    #   ACCESS LEVEL :  4       CREATE_NEW_WEBPAGE()
    #=======================================================#      
    def create_new_webpage(self, request):
        #***************#
        ACCESS_LEVEL = 4
        #***************#
        #------------------------------------------------------------------------------------------------------------------------------------
        #:::This function creates a new webpage
        #------------------------------------------------------------------------------------------------------------------------------------
        
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            #Make sure we only take POST requests
            if request.method == 'POST':      
                logger.info(request.POST)
                if request.POST['NEW'] == "T":
    
                    webpage = Webpage()
                    webpage.name = request.POST['name']
                    webpage.content = request.POST['content']
                    if request.POST['menugroup'] != "NONE" and request.POST['menugroup'] == "NEW": 
                        new_menu = Menugroup()
                        new_menu.name = request.POST['menu_name']
                        new_menu.project = request.user.permissions.project
                        new_menu.save()
                        webpage.menugroup = new_menu
                        logger.info("We did it?")
                        logger.info(new_menu)
                    elif request.POST['menugroup'] != "NONE" and request.POST['menugroup'] != "NEW": 
                        webpage.menugroup = Menugroup.objects.get(pk=request.POST['menugroup'])
                    webpage.created_by = request.user
                    webpage.modified_by = request.user
                    webpage.project = request.user.permissions.project
                    webpage.save()
                    
                else:
                    webpage = Webpage.objects.get(pk=request.POST['webpage_pk'], project__pk=request.user.permissions.project.pk)
                    webpage.name = request.POST['name']
                    webpage.content = request.POST['content']
                    if request.POST['menugroup'] != "NONE" and request.POST['menugroup'] == "NEW": 
                        new_menu = Menugroup()
                        new_menu.name = request.POST['menu_name']
                        new_menu.project = request.user.permissions.project
                        new_menu.save()
                        webpage.menugroup = new_menu
                        logger.info("We did it BBBBB?")
                        logger.info(new_menu)
                    elif request.POST['menugroup'] != "NONE" and request.POST['menugroup'] != "NEW": 
                        webpage.menugroup = Menugroup.objects.get(pk=request.POST['menugroup'])
                    else: webpage.menugroup = None
                    webpage.modified_by = request.user
                    webpage.save()

                json_data = {}
                json_data['success'] = "T"
                json_data['menu_pk'] = webpage.menugroup.pk
                json_data['menu_list'] = request.user.permissions.project.get_webpage_menu_list()
                json_data = json.dumps(json_data)
                #SUCCESS!!
                return HttpResponse(json_data, content_type="application/json")   
                
            else: ERROR_MESSAGE += "Error: You have not submitted through POST"
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")      
    


    #=======================================================#
    #   ACCESS LEVEL :  4       EDIT_MENUGROUP()
    #=======================================================#      
    def edit_menugroup(self, request):
        #***************#
        ACCESS_LEVEL = 4
        #***************#
        #------------------------------------------------------------------------------------------------------------------------------------
        #:::This function creates a new webpage
        #------------------------------------------------------------------------------------------------------------------------------------
        
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            #Make sure we only take POST requests
            if request.method == 'POST':      
                logger.info(request.POST)

                menugroup = Menugroup.objects.get(pk=request.POST['menugroup_pk'], project__pk=request.user.permissions.project.pk)
                if request.POST['code'] == "NAME":
                    menugroup.name = request.POST['name']
                    menugroup.save()
                elif request.POST['code'] == "DEL":
                    menugroup.delete()
                else:    
                    if request.POST['code'] != "NONE": 
                        menugroup.parentmenu = Menugroup.objects.get(pk=request.POST['code'])#code is the pk value in this case
                    else: 
                        menugroup.parentmenu = None
                    #remove references from old menus, e.g. if it has submenus, they are now main menus
                    for submenu in menugroup.menugroup_set.all():
                        submenu.parentmenu = None
                        submenu.save();
                    menugroup.save()
                #Now create a list of menu's and pages to return
                new_list = request.user.permissions.project.get_webpage_menu_list()
                #SUCCESS!!
                return HttpResponse('{"SUCCESS":"T", "menu_list":"'+new_list+'", "menu_pk":"'+str(menugroup.pk)+'"}',content_type="application/json")   
                
            else: ERROR_MESSAGE += "Error: You have not submitted through POST"
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")      
    

    
    #=======================================================#
    #   ACCESS LEVEL :  2       CREATE_NEW_FORM()
    #=======================================================#      
    def create_new_form(self, request):
        #***************#
        ACCESS_LEVEL = 2
        #***************#
        #------------------------------------------------------------------------------------------------------------------------------------
        #:::This function creates a new form of the given form type. In order to maintain integrity when creating a new form--we need to assume
        #   --the worst. In this case someone may be atempting to pass a different form-type pk into this endpoint and create a new form there.
        #   --this isn't terribly problematic in terms of security--if someone can access this function then they can edit any form type in
        #   --their project. We just need to make sure they can ONLY affect form types in their own project. Performing a simple check on the
        #   --form_type the submitted RTYPES are child'd to should be enough to deter these shenanigans--but once again--the worst someone can
        #   --do if hijacking this endpoint is add new data. They can't delete anything.
        #------------------------------------------------------------------------------------------------------------------------------------
        
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            #Make sure we only take POST requests
            if request.method == 'POST':      
                #Create New Form with formtype
                post_data = request.POST
                form_type = FormType.objects.get(pk=post_data['formtype_id'])
                #Make sure we're in the user's allowed project space
                if form_type.project.pk == request.user.permissions.project.pk:
                    
                    addedFRAT_pks = {}
                    addedFRRT_pks = {}
                
                    newform = Form(form_name='', form_number=post_data.get('form_number'), form_geojson_string=post_data.get('form_geojson_string'))
                    newform.form_type=form_type 

                    #Add the user information - We only set created by in endpoints that create the model for the first time
                    newform.created_by = request.user
                    newform.modified_by = request.user
                
                    #Figure out if the input field is a number(int) or a string label
                    #"pythonic" thing to do looking online and the Python Core uses this often it seems
                    #*I'm not particulary fond of using try/catch's to control logic, but apparently it is the Python way
                    try:
                        newform.form_name = post_data.get('form_number')
                        newform.form_number = int(post_data.get('form_number'))
                    except:
                        newform.form_name = post_data.get('form_number')
                        newform.form_number = None    
                    #Update the hierchical parent reference if relevant
                    if form_type.is_hierarchical:
                        if post_data.get('hierarchical_reference') == 'NONE':
                            newform.hierarchy_parent = None
                        else:
                            newform.hierarchy_parent = Form.objects.get(pk=post_data.get('hierarchical_reference'))
                    #save the form
                    newform.save()
                    
                    logger.info( request.POST)
                    #Now we need to create all the attributes from the form input
                    for key in post_data:
                        splitKey = key.split("__")
                        if len(splitKey) > 1:
                            if len(splitKey) == 2: 
                            
                                code,type_pk = splitKey
                                logger.info( "Getting Close: " + code + " : " + type_pk)
                                if code == "frat":
                                    currentFRAT = FormRecordAttributeType.objects.get(pk=type_pk)
                                    #$$$ SECURITY $$$ -- We need make sure they are trying to add rtype values that are attached to this project
                                    #if they are not, then show an error page and delete this current form.
                                    if currentFRAT.project.pk == request.user.permissions.project.pk:
                                        newformrecordattributevalue = FormRecordAttributeValue(record_value = post_data[key])
                                        newformrecordattributevalue.form_parent=newform
                                        newformrecordattributevalue.record_attribute_type=currentFRAT
                                        #Add the user information - We only set created by in endpoints that create the model for the first time
                                        newformrecordattributevalue.created_by = request.user
                                        newformrecordattributevalue.modified_by = request.user
                                        newformrecordattributevalue.save()
                                        
                                        addedFRAT_pks[currentFRAT.pk] = "Added"
                                    else:
                                        newform.delete()
                                        ERROR_MESSAGE += "You have attempted to add a form with a attribute record type that is not part of your project space."
                                        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
                                        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")     
                                #Create all references from the form input
                                elif code == "frrvNEW":
                                    currentFRRT = FormRecordReferenceType.objects.get(pk=type_pk)
                                    #$$$ SECURITY $$$ -- We need make sure they are trying to add rtype values that are attached to this project
                                    #if they are not, then show an error page and delete this current form.
                                    if currentFRRT.project.pk == request.user.permissions.project.pk:
                                        newFRRV = FormRecordReferenceValue()
                                        newFRRV.project = request.user.permissions.project
                                        newFRRV.created_by = request.user
                                        newFRRV.modified_by = request.user
                                        newFRRV.record_reference_type = currentFRRT
                                        newFRRV.form_parent = newform
                                        newFRRV.external_key_reference = request.POST['frrvNEW__'+type_pk+'__ext']
                                        #We have to save the new FRRV to the SQL database before adding new references I think
                                        newFRRV.save()
                                        for reference in post_data.getlist(key):
                                            logger.info( reference + "  <!----- ADDING THIS REF")
                                            #make sure we add a null check here--the user might not have chosen a referenced form
                                            if reference != '':
                                                newFRRV.record_reference.add(Form.objects.get(pk=reference))
                                            logger.info( str(newFRRV.record_reference) + "  <!----- ADDED THIS REF"   )
                                        newFRRV.save()
                                        addedFRRT_pks[currentFRRT.pk] = "Added"
                                    else:
                                        newform.delete()
                                        ERROR_MESSAGE += "You have attempted to add a form with a reference record type that is not part of your project space."
                                        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
                                        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")    
                    
                    #Now we're going to make empty FRRTs and FRATs for all the remaining ones attached tot he form type
                    allFRATs = form_type.formrecordattributetype_set.all()
                    allFRRTs = form_type.ref_to_parent_formtype.all()
                    logger.info( addedFRAT_pks)
                    logger.info( addedFRRT_pks)
                    #First make all necessary empty FRATS
                    if allFRATs:
                        for FRAT in allFRATs:
                            if FRAT.pk in addedFRAT_pks:
                                logger.info( "YEP")
                            else:
                                #Make a new FRAV for this FRAT
                                newFRAV = FormRecordAttributeValue(record_value = "")
                                newFRAV.form_parent=newform
                                newFRAV.record_attribute_type=FRAT
                                #Add the user information - We only set created by in endpoints that create the model for the first time
                                newFRAV.created_by = request.user
                                newFRAV.modified_by = request.user
                                newFRAV.save()                                
                    if allFRRTs:
                        for FRRT in allFRRTs:
                            if FRRT.pk in addedFRRT_pks:
                                logger.info( "YEP")
                            else:
                                #Make a new FRRV for this FRRT
                                newFRRV = FormRecordReferenceValue()
                                newFRRV.project = request.user.permissions.project
                                newFRRV.created_by = request.user
                                newFRRV.modified_by = request.user
                                newFRRV.record_reference_type = FRRT
                                newFRRV.form_parent = newform
                                newFRRV.external_key_reference = ""
                                #We have to save the new FRRV to the SQL database before adding new references I think
                                newFRRV.save()
                                
                    #SUCCESS!!
                    return HttpResponse('{"MESSAGE":"SUCCESS!"}',content_type="application/json")   
                ERROR_MESSAGE += "Error: You do not have permission to accesss this project."
            else: ERROR_MESSAGE += "Error: You have not submitted through POST"
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")      
    

    #=======================================================#
    #   ACCESS LEVEL :  1      SAVE_USER_QUERY() *RECYCLING
    #=======================================================#   
    def save_user_query(self, request):
        #***************#
        ACCESS_LEVEL = 1
        #***************#            

        ERROR_MESSAGE = ""
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
        
            #We need to return a json list of all formtype RTYPES that match the provided formtype pk
            if request.method == "POST":
                #We only add queries to the user and nothing else
                currentQueries = request.user.permissions.saved_queries 
                logger.info( currentQueries)
                if currentQueries != "" and currentQueries != None:
                    currentQuery = json.loads(currentQueries)
                    newQuery = {'label':request.POST['new_query_label'], 'query': json.loads(request.POST['new_query']) }
                    currentQuery.append(newQuery)
                    finishedQueryList = json.dumps(currentQuery)
                    request.user.permissions.saved_queries = finishedQueryList     
                    request.user.permissions.save()                    
                    return HttpResponse(finishedQueryList, content_type="application/json" )
                else:
                    
                    allQueries = []
                    newQuery = {'label':request.POST['new_query_label'], 'query': json.loads(request.POST['new_query']) }
                    allQueries.append(newQuery)
                    allQueries = json.dumps(allQueries)
                    request.user.permissions.saved_queries = allQueries
                    request.user.permissions.save()
                    return HttpResponse(allQueries, content_type="application/json" )
            ERROR_MESSAGE += "Error: You have not submitted through POST"
            
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")    
    
    
    #-------------------------------------------------------------------------------------------------------
    # MODEL QUERY ENDPOINTS
    
    #=======================================================#
    #   ACCESS LEVEL :  1      GET_PROJECTS() *RECYCLING
    #=======================================================#   
    def get_projects(self, request):
        #***************#
        ACCESS_LEVEL = 1
        #***************#            
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This Endpoint returns a list of all projects. This is used mainly by the query engine
        #   --to figure out which rtypes to search by when a record reference type is chosen.
        
        
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
        
            #We need to return a json list of all formtype RTYPES that match the provided formtype pk
            if request.method == "POST":
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

            ERROR_MESSAGE += "Error: You have not submitted through POST"
            
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
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
                logger.info( request.POST['project_pk']  + "  :  ")
                if str(request.user.permissions.project.pk) == request.POST['project_pk']:
                    logger.info( "What...?" + str(request.user.permissions.project.pk))
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
                logger.info( request.POST['project_pk']  + "  :  ")
                if str(request.user.permissions.project.pk) == request.POST['project_pk']:
                    logger.info( "What...?" + str(request.user.permissions.project.pk))
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
                logger.info( request.POST['formtype_pk']  + "  :  ")
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
                            #allFRATs = aForm.form_type.formrecordattributetype_set.all()
                            #if allFRATs:
                            #    for FRAT in allFRATs:
                            #        properties[FRAT.record_type]  = FormRecordAttributeValue.objects.get(record_attribute_type=FRAT, form_parent=aForm).record_value
                            feature = {}
                            properties['pk'] = aForm.pk
                            feature['properties'] = properties
                            feature['type'] = "Feature"
                            feature['geometry'] = json.loads(aForm.form_geojson_string)
                            #logger.info( "Loaded Timer")
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
                logger.info(request.POST)
                #Grab the formtype
                if 'formtype_pk' in request.POST:   currentFormType = FormType.objects.get(pk=request.POST['formtype_pk'])
                else:                               currentFormType = FormRecordReferenceType.objects.get(pk=request.POST['frrt-pk']).form_type_reference
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
                                currentDeepRTYPE['parent_pk'] = FRRT.pk
                                rtypeList.append(currentDeepRTYPE)
                            for deepFRRT in FRRT.form_type_reference.ref_to_parent_formtype.all().filter(flagged_for_deletion=False):
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
                        referencingFRRTs = FormRecordReferenceType.objects.filter(form_type_reference__pk=currentFormType.pk, flagged_for_deletion=False)
                        for FRRT in referencingFRRTs:
                            currentRTYPE = {}
                            currentRTYPE['label'] = FRRT.form_type_parent.form_type_name
                            currentRTYPE['pk'] = FRRT.pk
                            currentRTYPE['ref_formtype_pk'] = FRRT.form_type_parent.pk
                            currentRTYPE['rtype'] = 'BACK-FRRT'
                            rtypeList.append(currentRTYPE)     
                            for deepFRAT in FRRT.form_type_parent.formrecordattributetype_set.all().filter(flagged_for_deletion=False):
                                currentDeepRTYPE = {}
                                currentDeepRTYPE['label'] = currentRTYPE['label'] + " :: " + deepFRAT.record_type
                                currentDeepRTYPE['pk'] = str(deepFRAT.pk)+","+str(FRRT.pk)
                                currentDeepRTYPE['rtype'] = 'BACK-DEEP-FRAT'
                                rtypeList.append(currentDeepRTYPE)   
                            for deepFRRT in FRRT.form_type_parent.ref_to_parent_formtype.all().filter(flagged_for_deletion=False):
                                currentDeepRTYPE = {}
                                currentDeepRTYPE['label'] = currentRTYPE['label'] + " :: " + deepFRRT.record_type
                                currentDeepRTYPE['pk'] = str(deepFRRT.pk)+","+str(FRRT.pk)
                                currentDeepRTYPE['rtype'] = 'BACK-DEEP-FRRT'
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
    #   ACCESS LEVEL :  1      GET_FORM_CLASS_STYLES *RECYCLING
    #=======================================================#   
    def get_form_class_styles(self, request):
        #***************#
        ACCESS_LEVEL = 1
        #***************#            
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This Endpoint returns a list of all forms for a provided formtype with a openlayers style associated with each one
        #   --where each form matches a certain value in a specified rtype's rval for that form.
        #   --E.G., If Form 001 has a "Type" field that matches the term "Clay Seal" it will use the style associated with "Clay Seal"
        
        
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
        
            #We need to return a json list of all RVALS that match the provided RTYPE
            if request.method == "POST":
                #Figure out if a FRRT or FRAT was submitted
                logger.info( request.POST)
                code, rtype_pk = request.POST['rtype_pk'].split('-')
                if code == "FRAT": 
                    rtype = FormRecordAttributeType.objects.get(pk=rtype_pk)
                    formtype = rtype.formrecordattributetype_set.all()[0]
                else:              
                    rtype = FormRecordReferenceType.objects.get(pk=rtype_pk)
                    formtype = rtype.formrecordreferencevalue_set.all()[0]
                
                #If the requested formtype isn't the user's project, and flagged as being inaccessible then stop the request
                if rtype.project.pk != request.user.permissions.project.pk and (rtype.flagged_for_deletion == True or rtype.is_public == False):
                    ERROR_MESSAGE += "Error: You are attempting to access records that don't exist. This probably occurred because your client attempted altering the POST data before sending"
                #Otherwise we are in the clear so grab the list and return it
                else:
                    
                    finalJSON = {}
                    form_list = []    
                    
                    if code == "FRAT":
                        allForms = formtype.form_set.all()

                        
                    else:               
                        finalJSON = rtype.form_type_reference.form_set.oder_by('form_name').values('form_name').distinct()
                    #Return the JSON response
                    
                    finalJSON = json.dumps(list(finalJSON))
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
            #logger.info( request.POST)
            #Returns a JSON string to an AJAX request given a provided UUID   
            try:
                currentProcessObject = AJAXRequestData.objects.filter(uuid=request.POST['uuid'])[0]
                logger.info( "Keeping Alive?" )
                currentProcessObject.keep_alive = True
                currentProcessObject.save()
                #If finished, then delete the process object
                if currentProcessObject.is_finished:
                    logger.info( "DELETING OBJECT I GUESS?")
                    currentProcessObject.delete()
                currentJson = currentProcessObject.jsonString
                logger.info( currentProcessObject.jsonString)
                #return the json response      
                return HttpResponse(currentJson, content_type="application/json")  
            except Exception as e:
                logger.info( "Whoops---hmmm.....")
                logger.info( e)
                logger.info( request.POST)
                ERROR_MESSAGE += "Something happened during the check to the Progress Object--it might not have been created yet, and we are checking too quickly..." + str(e)
                return HttpResponse('{"is_complete":"False"}', content_type="application/json")      

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
                    logger.warning(request.POST)
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
                returnedJSON = json.dumps(returnedJSON)
                return HttpResponse(returnedJSON,content_type="application/json") 
            ERROR_MESSAGE += "Error: You have not submitted through POST"
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")        
        
  
    #=======================================================#
    #   ACCESS LEVEL :  5       USERNAME_TAKEN()
    #=======================================================#        
    def username_taken(self, request):
        #***************#
        ACCESS_LEVEL = 5
        #***************#
        #------------------------------------------------------------------------------------------------------------------------------------
        #:::This function just returns a 'true' or 'false' json response if the submitted 'username' string is already taken
        #   --This still requires access level 5 because only the admin who can create and manage users should be using it
        #   --It's not crazy important if someone receives a true or false response--this doesn't change the database, but for
        #   --confidentiality, someone can't just 'guess' someone's username by typing this in over and over again
        #   --a public version would need to lock sessions/users attempting it too many times
        #------------------------------------------------------------------------------------------------------------------------------------
        
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            #Make sure we only take POST requests
            if request.method == 'POST':                        
                if User.objects.all().filter(username=request.POST['username']).exists():
                    return HttpResponse('{"user_exists":"T"}', content_type="application/json")
                else:
                    return HttpResponse('{"user_exists":"F"}', content_type="application/json")

            ERROR_MESSAGE += "Error: You have not submitted through POST"
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
                logger.info( "do something")
                #We need to make sure we have permission to deal with the formtype--e.g. it's part of the user's current project
                formtype = FormType.objects.get(pk=request.POST['formtype_id'])
                
                #If the project IDs match, then we're good to go! Also if it's not the project, but the formtype is set to PUBLIC then we are also good to go
                if formtype.project.pk == request.user.permissions.project.pk or (formtype.project.pk != request.user.permissions.project.pk and formtype.is_public == True):
                
                    #First let's setup our header field of ordered labels 
                    logger.info(  "Timer Start"                )
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
                                formRVAL = aForm.formrecordattributevalue_set.all().filter(record_attribute_type__pk=rtype[2])
                                #We need to check for NULL FRAV's here. When a user manually creates new forms, they don't always have FRAVS created for them if they leave it blank
                                if formRVAL.exists():
                                    rowList.append((rtype[0],'frav',formRVAL[0].record_value, formRVAL[0].pk))
                                else:
                                    logger.info( "Whoops--something happened. There are no RVALS for 'frats' using: " + str(rtype[2]))
                                logger.info( "TIMER Y"+ " : " + str(time.process_time()))
                            else:
                                #for frrt in aForm.ref_to_parent_form.all():
                                    #logger.info( "" + str(frrt.pk))
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
                            thumbnailURI = staticfiles_storage.url("/site-images/no-thumb-missing.png")
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
                                                thumbnailURI = currentRTYPE.record_reference.all()[0].get_ref_thumbnail()
                                            break
                            #Finally--if there aren't any relevant media types in our frrts, let's do a last second check for ANY frrts that are media types
                            #--that AREN'T in our RTYPE list
                            if thumbnailURI == staticfiles_storage.url("/site-images/no-thumb-missing.png"):
                                logger.info("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%    We're TRYING TO GET A THUMBNAIL")
                                currentRVAL = aForm.ref_to_parent_form.filter(record_reference_type__form_type_reference__type=1)
                                logger.info(currentRVAL)
                                if currentRVAL.exists():
                                    #Just get the first one out of the list
                                    if len(currentRVAL[0].record_reference.all()) > 0:
                                        logger.info(currentRVAL[0].record_reference.all()[0].form_name)
                                        thumbnailURI = currentRVAL[0].record_reference.all()[0].get_ref_thumbnail()
                                        

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
                logger.info(request.POST);
                #We need to make sure we have permission to deal with the formtype--e.g. it's part of the user's current project
                formtype = FormType.objects.get(pk=request.POST['formtype_id'])
                
                #If the project IDs match, then we're good to go! Also if it's not the project, but the formtype is set to PUBLIC then we are also good to go
                if formtype.project.pk == request.user.permissions.project.pk or (formtype.project.pk != request.user.permissions.project.pk and formtype.is_public == True):
                
                    #Make the AJAX Request Data Model for subsequent AJAX calls
                    progressData = AJAXRequestData(uuid=request.POST.get('uuid'), jsonString='{"message":"Loading Json","current_query":"","current_term":"","percent_done":"0","is_complete":"False"}')
                    progressData.save()

                    
                    #First let's setup our header field of ordered labels 
                    logger.info(  "Timer Start"                )
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
                        logger.info( query)
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
                            tCounter = 0
                            logging.info("TimerA"+ " : " + str(time.process_time()))
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
                                logging.info("TimerB"+ " : " + str(time.process_time()))
                                #We'll calculate percent by claiming finishing the query is at 50% when complete and at 20% when starting this section.
                                logging.info(rtypeCounter)
                                logging.info(len(masterQueryJSON['query_list']))
                                Qpercent = ((rtypeCounter-2) * (50.0/len(masterQueryJSON['query_list'])))
                                percentDone =  5 + Qpercent +  (tCounter * (Qpercent / len(currentJSONQuery['TERMS'])) )
                                progressData.jsonString = '{"message":"Performing Query # '+ str(rtypeCounter-1) + ' on term: '+term['TVAL']+'","current_query":"'+ currentJSONQuery['RTYPE'] + '","current_term":"'+term['TVAL']+'","percent_done":"'+ str(int(percentDone)) +'","is_complete":"False"}'
                                progressData.save() 
                                tCounter += 1
                                logging.info("TimerC"+ " : " + str(time.process_time()))
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
                            tCounter = 0
                            logging.info("TimerD"+ " : " + str(time.process_time()))
                            
                            #get the deep values
                            try:
                                deepRTYPE, deepPK = currentJSONQuery['RTYPE-DEEP'].split('-')
                            except:
                                deepRTYPE, deepPK = "FORMID",rtypePK
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
                                    logger.info( "We should be here")
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
                                    logger.info( "We should be here 3")
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
                            tCounter = 0
                            logging.info("TimerD"+ " : " + str(time.process_time()))
                            for term in currentJSONQuery['TERMS']:
                                #Now begin modifying the SQL query which each term of each individual query
                                #skip the term if the field was left blank
                                if term['TVAL'] != "" or term['QCODE'] == '4':
                                    newQuery = None
                                    logger.info( str(formtype.form_set.all().filter(form_name__contains=term['TVAL'])))
                                    if term['T-ANDOR'] != 'or':#We can assume it is an AND like addition if it's anything but 'or'
                                        logger.info( "Is it working?")
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
                            masterQuery = queriedForms
             
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
                        endIndex = int(request.POST['numberOfResults'])
                    
                    logger.info( startIndex)
                    logger.info( endIndex)
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
                        logger.info( "TIMER R"+ " : " + str(time.process_time()))
                        masterQuery = masterQuery.filter(hierarchy_parent=None).exclude(form_number=None, form_name=None)[startIndex:endIndex]
                        logger.info( "TIMER RR"+ " : " + str(time.process_time()))
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
                        logger.info( "TIMER R"+ " : " + str(time.process_time()))
                        #sort the formlist by their sort_index
                        logger.info(startIndex)
                        logger.info(endIndex)
                        masterQuery = masterQuery.order_by('sort_index')
                        masterQuery = masterQuery[startIndex:endIndex]
                    logger.info( "TIMER RR"+ " : " + str(time.process_time()))
                    #count the query so we only make one database hit before looping(otherwise each loop would be another hit)
                    if masterQuery:
                        total = masterQuery.count()
                        logger.info( "TIMER RRR"+ " : " + str(time.process_time()))
                        for aForm in masterQuery:
                            logger.info( "TIMER S"+ " : " + str(time.process_time()))
                            queryCounter += 1
                            Qpercent = ( queryCounter * (30/(total*1.0)))
                            finalPercent = (60 + int(Qpercent))
                            progressData.jsonString = '{"SQL":"True","message":"Loading Queried Forms!","current_query":"'+ str(queryCounter) +'","current_term":"'+ str(total) +'","percent_done":"' + str(finalPercent) + '","is_complete":"False","stats":"none"}'
                            logger.info( "TIMER RRRR"+ " : " + str(time.process_time()))
                            progressData.save()
                            logger.info( "TIMER RRRRR"+ " : " + str(time.process_time()))
                           # logger.info( str(aForm.pk) + ":  <!-- Current Form Pk")
                            rowList = []
                            #Let's loop through each item in the queryRTYPE list and match up the frav's in each queried form so the headers match the form attribute values
                            for rtype in queryRTYPElist:
                                if rtype[1] == 'frat':
                                    #logger.info( str(rtype[2]) + '  ' + str(aForm.formrecordattributevalue_set.all().filter(record_attribute_type__pk=rtype[2]).count()))
                                    logger.info( "TIMER X"+ " : " + str(time.process_time()))
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
                                    logger.info( "TIMER Y"+ " : " + str(time.process_time()))
                                else:
                                    #for frrt in aForm.ref_to_parent_form.all():
                                        #logger.info( "" + str(frrt.pk))
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

                            logger.info( "TIMER Z"+ " : " + str(time.process_time()))
                            #sort the new combined reference ad attribute type list combined
                            rowList = sorted(rowList, key=lambda att: att[0])
                            # logger.info( str(rowList))
                            #Now let's handle the thumbnail bit of business for the query
                            #--If the current form IS a media type already, then use itself to grab the thumbnail URI
                            if aForm.form_type.type == 1:
                                thumbnailURI = aForm.get_thumbnail_type()
                            else:
                                #let's find the first media type in the order but offer a default to "NO PREVIEW" if not found
                                thumbnailURI = staticfiles_storage.url("/site-images/no-thumb-missing.png")
                                testURI = staticfiles_storage.url("/site-images/no-thumb-missing.png")
                                for record in rowList:            
                                    #if it's a reference
                                    if record[1] == 'frrv' or record[1] == 'frrv-ext':
                                        currentRTYPE = FormRecordReferenceValue.objects.get(pk=int(record[3]))
                                        #if it's not a NoneType reference:
                                        if currentRTYPE.record_reference_type.form_type_reference != None:
                                            #If its a reference to a media type
                                            if currentRTYPE.record_reference_type.form_type_reference.type == 1:
                                                logger.info( "WE GOT A MATCH------------ " )
                                                logger.info(record)
                                                #Because a form record reference value is a ManyToMany relationship, we just grab the first one in the list
                                                #TODO this may need to be edited later--because you can't order the selections. I may add another ForeignKey called
                                                #"Thumbnail Reference" which links to a single relation to a form of a media type--this would also
                                                #probably solve the complexity of looping through to grab it as it stands right now
                                                #****WE also have to check for NULL references
                                                if currentRTYPE.record_reference.all().count() > 0:
                                                    thumbnailURI = currentRTYPE.record_reference.all()[0].get_ref_thumbnail()
                                                if thumbnailURI != testURI: 
                                                    break
                                                
                                        
                            #we only want the first 5 values from the final ordered list of attributes
                            rowList = rowList[0:5]


                            formList.append([thumbnailURI,str(aForm.pk), aForm, rowList])   
                            logger.info( "TIMER ZZ"+ " : " + str(time.process_time()))
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
                    logger.info(  "Timer End"     )
                    return HttpResponse(finishedJSONquery, content_type="application/json")
                ERROR_MESSAGE += "Error: You don't have permission to access this FormType from another project"
            ERROR_MESSAGE += "Error: You have not submitted through POST"
        else: ERROR_MESSAGE += "Error: You do not have permission to access querying this project"
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")   
 




    #############################################################################################################################################################################################################################
    #############################################################################################################################################################################################################################
    #############################################################################################################################################################################################################################
    #############################################################################################################################################################################################################################

 
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
        
        CS_CONTAINS = '0';
        CONTAINS = '1';
        EXACT_MATCH = '2';
        EXCLUDES = '3';
        IS_NULL = '4';
        ALL_UNIQUE_TERMS = '5';
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
        
            if request.method == 'POST':
                    
                logger.info( request.POST)
                #Make the AJAX Request Data Model for subsequent AJAX calls
                progressDataMessage = {}
                progressDataMessage['message'] = "Loading Query from POST"
                progressDataMessage['current_query'] = ""
                progressDataMessage['current_term'] = ""
                progressDataMessage['percent_done'] = "0"
                progressDataMessage['current_constraint'] = ""
                progressDataMessage['is_complete'] = "False"
                #!!!!!!!!!!!!!!PROGRESS UPDATE
                progressData = AJAXRequestData(uuid=request.POST.get('uuid'), jsonString=json.dumps(progressDataMessage) )
                progressData.is_finished = False
                progressData.save()
                
                try:
                
                    #We need to loop through EACH project query in the JSON header and create a separate results box for each one
                    masterProjectQuery = json.loads(request.POST['master_query'])
                    
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
                        #If we are querying a project different than the user and it is NOT set to public, then throw an error because it should be private
                        if (queryProject.pk != request.user.permissions.project.pk and queryProject.is_public == False) or (queryFormtype.project.pk != request.user.permissions.project.pk and queryFormtype.is_public == False):
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
                            for attType in queryFormtype.formrecordattributetype_set.all().filter(flagged_for_deletion=False).order_by('order_number'):
                                form_att_type_list.append((attType.order_number,'frat',attType.pk,attType.record_type)) 
                     
                            #***RECYCLING BIN*** Make sure our RTYPES are filtered by their deletion flags
                            for refType in queryFormtype.ref_to_parent_formtype.all().filter(flagged_for_deletion=False).order_by('order_number'):
                                form_att_type_list.append((refType.order_number,'frrt',refType.pk,refType.record_type)) 

                            #sort the new combined reference ad attribute type list combined
                            form_att_type_list = sorted(form_att_type_list, key=lambda att: att[0])
                            #we only want the first 5 types
                            form_att_type_list = form_att_type_list[0:5]
                            
                            #Finally let's organize all of our reference and attribute values to match their provided order number
                            formList = []                
                           
                            #Setup our inital queryset that includes all forms
                            masterQuery = queryFormtype.form_set.all().filter(flagged_for_deletion=False)  
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
                                queriedForms = queryFormtype.form_set.all().filter(flagged_for_deletion=False) 

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
                                        logger.info("WE MADE IT!!!!   => QCODE = " + term['QCODE'])
                                        newQuery = None
                                        if term['ANDOR'] != 'or':#We can assume it is an AND like addition if it's anything but 'or'
                                            #Now let's figure out the QCODE, e.g. contains, match exact etc.
                                            if   term['QCODE'] == CONTAINS: newQuery = queriedForms.filter(formrecordattributevalue__record_value__icontains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#CONTAINS    
                                            elif term['QCODE'] == CS_CONTAINS: newQuery = queriedForms.filter(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#ICONTAINS                                   
                                            elif term['QCODE'] == EXACT_MATCH: newQuery = queriedForms.filter(formrecordattributevalue__record_value__exact=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#MATCHES EXACT                                    
                                            elif term['QCODE'] == EXCLUDES: newQuery = queriedForms.exclude(formrecordattributevalue__record_value__contains=term['TVAL'], formrecordattributevalue__record_attribute_type__pk=rtypePK)#EXCLUDES                                   
                                            elif term['QCODE'] == IS_NULL: newQuery = queriedForms.filter(formrecordattributevalue__record_value__isnull=True, formrecordattributevalue__record_attribute_type__pk=rtypePK) | (queryFormtype.form_set.all().filter(formrecordattributevalue__record_value__icontains="", formrecordattributevalue__record_attribute_type__pk=rtypePK))#IS_NULL        
                                            logger.info(masterQuery.query)
                                            logger.info(newQuery.query)
                                            #save stats and query
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
                                            #save stats and query
                                            term['count'] =  newQuery.count()
                                            termStats.append(term)
                                            masterQuery = (newQuery | masterQuery)
                                            singleQueryStats['additions'] = masterQuery.count()
                                            logging.info("TimerB"+ " : " + str(time.process_time()))
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
                                                #***RECYCLING BIN*** Make sure our NEW query is always filtered by recycling bin flags--All OR statements will need this filter
                                                newQuery = newQuery.filter(flagged_for_deletion=False)
                                                #save stats and query
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
                                                #***RECYCLING BIN*** Make sure our NEW query is always filtered by recycling bin flags--All OR statements will need this filter
                                                newQuery = newQuery.filter(flagged_for_deletion=False)
                                                #save stats and query
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
                                                #***RECYCLING BIN*** Make sure our NEW query is always filtered by recycling bin flags--All OR statements will need this filter
                                                newQuery = newQuery.filter(flagged_for_deletion=False)
                                                #save stats and query
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
                                                #***RECYCLING BIN*** Make sure our NEW query is always filtered by recycling bin flags--All OR statements will need this filter
                                                newQuery = newQuery.filter(flagged_for_deletion=False)
                                                #save stats and query
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
                                            deepFormType = FormType.objects.get(pk=FormRecordReferenceType.objects.get(pk=deepPK).form_type_parent.pk, flagged_for_deletion=False)
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
                                                #***RECYCLING BIN*** Make sure our NEW query is always filtered by recycling bin flags--All OR statements will need this filter
                                                newQuery = newQuery.filter(flagged_for_deletion=False)
                                                #save stats and query
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
                                                #***RECYCLING BIN*** Make sure our NEW query is always filtered by recycling bin flags--All OR statements will need this filter
                                                newQuery = newQuery.filter(flagged_for_deletion=False)
                                                #save stats and query
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
                                                #***RECYCLING BIN*** Make sure our NEW query is always filtered by recycling bin flags--All OR statements will need this filter
                                                newQuery = newQuery.filter(flagged_for_deletion=False)
                                                #save stats and query
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
                                                #***RECYCLING BIN*** Make sure our NEW query is always filtered by recycling bin flags--All OR statements will need this filter
                                                newQuery = newQuery.filter(flagged_for_deletion=False)    
                                                #save stats and query
                                                term['count'] =  newQuery.count()
                                                termStats.append(term)
                                                queriedForms = (newQuery | queriedForms)
                        
                                queryList.append(singleQueryStats)  
                                singleQueryStats['ANDOR'] = term['ANDOR']
                                singleQueryStats['count'] = masterQuery.count()
                                queryStats['count'] = singleQueryStats['count']
                               

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
                                                deepFormType = deepFormType.filter(flagged_for_deletion=False)
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

                                            #***RECYCLING BIN*** Make sure our NEW Constraints query is always filtered by recycling bin flags
                                            constraintQuery = constraintQuery.filter(flagged_for_deletion=False)      
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
                                                            deepFormType = deepFormType.filter(flagged_for_deletion=False)
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
                                                       #***RECYCLING BIN*** Make sure our NEW Constraints query is always filtered by recycling bin flags
                                                        constraintQuery = constraintQuery.filter(flagged_for_deletion=False)                             
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
        
                            #Now make sure our final queried list has distint values--merging querysets has a tendency to create duplicates
                            masterQuery = masterQuery.distinct()
                            #***RECYCLING BIN*** A Final redundant recycling bin filter--just to be safe
                            masterQuery = masterQuery.filter(flagged_for_deletion=False)                      
                        

                            
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
                                masterQuery = masterQuery.order_by('sort_index')[:numberOfFormsPerPage]
                                   
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
                                    logger.info('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ ABOUT TO GET THUMBNAILS')
                                    if aForm.form_type.type == 1:
                                        thumbnailURI = aForm.get_thumbnail_type()
                                    else:
                                        #logger.info("LOOKING FOR A FRRT")
                                        #let's find the first media type in the order but offer a default to "NO PREVIEW" if not found
                                        thumbnailURI = staticfiles_storage.url("/site-images/no-thumb-missing.png")
                                        for record in rowList:            
                                            #if it's a reference
                                            if record[1] == 'frrv' or record[1] == 'frrv-ext':
                                                currentRTYPE = FormRecordReferenceValue.objects.get(pk=int(record[3]))
                                                #if it's not a NoneType reference:
                                                if currentRTYPE.record_reference_type.form_type_reference != None:
                                                    #If its a reference to a media type
                                                    if currentRTYPE.record_reference_type.form_type_reference.type == 1:
                                                        #logger.info( "WE GOT A MATCH")
                                                        #Because a form record reference value is a ManyToMany relationship, we just grab the first one in the list
                                                        #TODO this may need to be edited later--because you can't order the selections. I may add another ForeignKey called
                                                        #"Thumbnail Reference" which links to a single relation to a form of a media type--this would also
                                                        #probably solve the complexity of looping through to grab it as it stands right now
                                                        #****WE also have to check for NULL references
                                                        if currentRTYPE.record_reference.all().count() > 0:
                                                            thumbnailURI = currentRTYPE.record_reference.all()[0].get_ref_thumbnail()
                                                        break
                                        #Finally--if there aren't any relevant media types in our frrts, let's do a last second check for ANY frrts that are media types
                                        #--that AREN'T in our RTYPE list
                                        if thumbnailURI == staticfiles_storage.url("/site-images/no-thumb-missing.png"):
                                            #logger.info("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%    We're TRYING TO GET A THUMBNAIL")
                                            currentRVAL = aForm.ref_to_parent_form.filter(record_reference_type__form_type_reference__type=1)
                                            #logger.info(currentRVAL)
                                            if currentRVAL.exists():
                                                #Just get the first one out of the list
                                                if len(currentRVAL[0].record_reference.all()) > 0:
                                                    #logger.info(currentRVAL[0].record_reference.all()[0].form_name)
                                                    thumbnailURI = currentRVAL[0].record_reference.all()[0].get_ref_thumbnail()
                                                    
                                    formList.append([thumbnailURI,str(aForm.pk), aForm, rowList])   
                                    formCounter += 1
                            form_att_type_list, form_list = form_att_type_list, formList
                            
                            #update our progress bar

                            
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
                            finishedJSONquery["currentQuery"] = request.POST['master_query']
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

            ERROR_MESSAGE += "Error: You have not submitted through POST"
        else: ERROR_MESSAGE += "Error: You do not have permission to access querying this project"
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
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            #$$$ SECURITY $$$ Make sure we only take POST requests
            if request.method == 'POST':         
                currentForm = Form.objects.get(pk=request.POST['form_pk'])
                #$$$ SECURITY $$$ Make sure form is in the same project space as the user or refuse the request for the list
                if currentForm.project.pk == request.user.permissions.project.pk or (currentForm.is_public and currentForm.flagged_for_deletion == False):
                    jsonData = {}
                    rtype_list = []
                    jsonData['rtype_list'] = rtype_list
                    jsonData['form_name'] = currentForm.form_name
                    jsonData['form_pk'] = currentForm.pk
                    jsonData['formtype_name'] = currentForm.form_type.form_type_name
                    jsonData['formtype_pk'] = currentForm.form_type.pk
                    #Alright--let's load our RTYPEs from the current Form requested
                    #*** RECYCLING BIN *** Let's filter them out by their recycling flags as well
                    frav_list = currentForm.formrecordattributevalue_set.all().filter(flagged_for_deletion=False)
                    frrv_list = currentForm.ref_to_parent_form.all().filter(flagged_for_deletion=False)
                    
                    #Let's try and grab our backward referencing forms now.
                    back_frrv_list = None
                    back_frrv_list = currentForm.ref_to_value_form.all().filter(flagged_for_deletion=False)
                    if back_frrv_list.count() > 100: back_frrv_list = None
                    
                    
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
                        logger.info(back_frrv_list)
                        flattened_list = back_frrv_list.values('form_parent__pk','form_parent__form_name','form_parent__form_type__pk','form_parent__pk','form_parent__form_type__form_type_name',)
                        formTypeList = {}
                        for FRRV in flattened_list:
                            logger.info(FRRV)
                            #Create Our RVAL
                            newRVAL = {}
                            newRVAL['form_pk'] = FRRV['form_parent__pk']
                            newRVAL['form_name'] = FRRV['form_parent__form_name']
                            newRVAL['thumbnail'] = staticfiles_storage.url("/site-images/no-thumb-file.png") 
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
                logger.info( request.POST)
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
                    jsonData = json.dumps(jsonData)
                    return HttpResponse(jsonData, content_type="application/json")    
                    
                ERROR_MESSAGE += "Error: You do not have permission to accesss this project."
            ERROR_MESSAGE += "Error: You have not submitted through POST"
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")        
    

    #=======================================================#
    #   ACCESS LEVEL :  1       GET_GEO_CATEGORY_MATCHES()   *Recycling            
    #=======================================================#    
    def get_geo_category_matches(self, request):
        #***************#
        ACCESS_LEVEL = 1
        #***************#
        #------------------------------------------------------------------------------------------------------------------------------------
        #:::This endpoint returns a JSON list of the same provided class values with newly attached forms that 
        #   follow their respective class rule
        #
        #   This sorts the query based on what kind of RTYPE we are looking to classify. It can handle this formtype's IDs, it's FRATs, 
        #       it's FRRTs IDs and associated FRATs/FRRTs, and also any backward relations IDs or FRATs.( E.g. if an Object has a relation to
        #       a grid square, but it's not obvious in the grid square form, the Object formtype will be added as a list of query types to use
        #       for this search.
        #
        #------------------------------------------------------------------------------------------------------------------------------------
        
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
            #$$$ SECURITY $$$ Make sure we only take POST requests
            if request.method == 'POST':   
                jsonData = {}
                class_list = []
                jsonData['class_list'] = class_list
                form_color_key = {}
                form_value_key = {}
                jsonData['form_color_key'] = form_color_key
                jsonData['form_value_key'] = form_value_key
                rtype_code = request.POST['rtype_code']
                code, PK = rtype_code.split('-')
                
                classList = json.loads(request.POST['class_list'])

                #This queries this formtype's forms IDs
                if code == "FORMID" :
                    #Let's loop through each of the provided class values, and add the flattened form pks to our list
                    for aClass in classList:
                        new_class = {}
                        new_class['matching_forms'] = list(FormType.objects.get(pk=PK).form_set.all().filter(form_name__icontains=aClass['class_value']).values_list('pk',flat=True).distinct())
                        new_class['class_value'] = aClass['class_value']
                        class_list.append(new_class)
                        for aForm in new_class['matching_forms']:
                            form_color_key[aForm] = aClass['color']
                            form_value_key[aForm] = aClass['class_value']
                #This handles a query on this formtype's FRRT's form IDs
                elif code == "FRRT_ID" :
                    for aClass in classList:
                        new_class = {}
                        new_class['matching_forms'] = list(Form.objects.all().filter(ref_to_parent_form__record_reference__form_name__icontains=aClass['class_value'], ref_to_parent_form__record_reference_type__pk=PK).values_list('pk',flat=True).distinct())
                        new_class['class_value'] = aClass['class_value']
                        class_list.append(new_class)
                        for aForm in new_class['matching_forms']:
                            form_color_key[aForm] = aClass['color']
                            form_value_key[aForm] = aClass['class_value']
                #This handles a query on this formtype's forms FRATs
                elif code == "FRAT" :
                    for aClass in classList:
                        new_class = {}
                        new_class['matching_forms'] = list(Form.objects.all().filter(formrecordattributevalue__record_value__icontains=aClass['class_value'], formrecordattributevalue__record_attribute_type__pk=PK).values_list('pk',flat=True).distinct())
                        new_class['class_value'] = aClass['class_value']
                        class_list.append(new_class)
                        for aForm in new_class['matching_forms']:
                            form_color_key[aForm] = aClass['color']            
                            form_value_key[aForm] = aClass['class_value']                            
                #This handles a query on a forward relation's FRRTs realted IDs
                elif code == "DEEP_FRRT" :
                    parent_formtype = FormType.objects.get(pk=request.POST['formtype_pk'])
                    for aClass in classList:
                        deepfrrt = FormRecordReferenceType.objects.get(pk=PK)
                        flattenedSet = deepfrrt.form_type_parent.form_set.all().filter(ref_to_parent_form__record_reference__form_name__icontains=aClass['class_value'], ref_to_parent_form__record_reference_type__pk=PK) #CONTAINS 
                        flattenedSet = list(flattenedSet.filter(ref_to_parent_form__record_reference_type__pk=PK).values_list('pk', flat=True))
                        new_class = {}
                        new_class['matching_forms'] = list(parent_formtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet).values_list('pk',flat=True).distinct())
                        new_class['class_value'] = aClass['class_value']
                        class_list.append(new_class)
                        for aForm in new_class['matching_forms']:
                            form_color_key[aForm] = aClass['color']
                            form_value_key[aForm] = aClass['class_value']
                #This handles a query on a forward relation's FRAT
                elif code == "DEEP_FRAT" :
                    parent_formtype = FormType.objects.get(pk=request.POST['formtype_pk'])
                    for aClass in classList:
                        flattenedSet = list(Form.objects.all().filter(formrecordattributevalue__record_value__icontains=aClass['class_value'], formrecordattributevalue__record_attribute_type__pk=PK).values_list('pk', flat=True)) #CONTAINS    
                        new_class = {}
                        new_class['matching_forms'] = list(parent_formtype.form_set.all().filter(ref_to_parent_form__record_reference__pk__in=flattenedSet).values_list('pk',flat=True).distinct())
                        new_class['class_value'] = aClass['class_value']
                        class_list.append(new_class)
                        for aForm in new_class['matching_forms']:
                            form_color_key[aForm] = aClass['color']   
                            form_value_key[aForm] = aClass['class_value']
                #This handles if we're doing a query on the backwards relation's form ID
                elif code == "BACK_FRRT" :
                    parent_formtype = FormType.objects.get(pk=request.POST['formtype_pk'])
                    back_frrt = FormRecordReferenceType.objects.get(pk=PK)
                    for aClass in classList:
                        new_class = {}
                        new_class['matching_forms'] = list(parent_formtype.form_set.all().filter(ref_to_value_form__form_parent__form_name__icontains=aClass['class_value']).values_list('pk',flat=True).distinct())
                        for aForm in new_class['matching_forms']:
                            form_color_key[aForm] = aClass['color']
                            form_value_key[aForm] = aClass['class_value']                            
                #This is if we're doing a query on a backwards relation's associated FRAT
                elif code == "BACK_DEEP_FRAT" :
                    parent_formtype = FormType.objects.get(pk=request.POST['formtype_pk'])
                    back_frat_pk, frrt_pk = PK.split(',')
                    frrt_ref = FormRecordReferenceType.objects.get(pk=frrt_pk) 
                    for aClass in classList:
                        flattenedSet = Form.objects.all().filter(formrecordattributevalue__record_value__icontains=aClass['class_value'], formrecordattributevalue__record_attribute_type__pk=back_frat_pk)
                        new_class = {}
                        new_class['class_value'] = aClass['class_value']
                        class_list.append(new_class)
                        for aForm in flattenedSet:
                            testB = aForm.ref_to_parent_form.all().filter(record_reference_type__pk=frrt_pk).values_list('record_reference', flat=True)
                            for test in testB:
                                form_color_key[test] = aClass['color']
                                form_value_key[test] = aClass['class_value']
                    
                    
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
    #   ACCESS LEVEL :  1      GET_ALL_UNIQUE_RTYPE_RVALS *RECYCLING
    #=======================================================#   
    def get_all_unique_rtype_rvals(self, request):
        #***************#
        ACCESS_LEVEL = 1
        #***************#            
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This Endpoint returns a list of all unique values for a given FRAT's RVALS
        #   --For FRATS: get all unique values of all possible FRAVs
        #   --for FRAVs: get all possible form name's attached to the form type reference that
        #   --this particular FRRT can reference
        
        
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
        
            #We need to return a json list of all RVALS that match the provided RTYPE
            if request.method == "POST":
                #Figure out if a FRRT or FRAT was submitted
                logger.info( request.POST)
                finalJSON = {}
                form_rval_list = {}    
                code, entity_pk = request.POST['entity_tag'].split('-')
                parent_formtype = FormType.objects.get(pk=request.POST['formtype_pk'])
                #Setup out necessary lists etc.
                new_form_rval_list = {}
                distinct_value_list = []               
                if   code == "DEEP_FRAT":   # We need to get all the unique rvals of the provided related FRAT
                    #OKAY--So what I want is a list of all relevant FRAVs per Parent Formtype, e.g. I want all the relevant "Object Type"s per "Grid Square" that
                    #   --references the objects. So What I need to do is, for each Grid Square Form, provide a list of all it's referenced objects, FRAVs for the
                    #   --"Object Type" FRAT they are connected to.
                    
                    # Let's loop through each "Grid Square" Form, grab it's relevant FRRV form(s) using the FRRT parent provided--then:
                    #   *for each FRRV's referenced forms(Object Form), Let's grab it's desired FRAV that has our provided DEEP FRAT as its parent and add it to a list
                    #   *attach that list to our current parent form in json 
                    
                    #Load our DEEP FRAT
                    entity_type = FormRecordAttributeType.objects.get(pk=entity_pk) 
                    #Figure out the FRRT referencing the FRAT by crossreferencing it between the provided FormType and FRAT
                    frrt_ref = parent_formtype.ref_to_parent_formtype.all().filter(form_type_reference__pk=entity_type.form_type.pk)[0]
                    #Get our list of forms of this parent formtype
                    forms = parent_formtype.form_set.all();
                    #This If statement simply forces the query to activate before looping through the forms--otherwise we'll be querying every loop which takes far longer
                    if forms:
                        for parent_form in forms:
                            #Try loading the form's FRAV--and if it can't/doesn't exist then fall back to a default value
                            try:
                                #Get our FRRV for this form matching the Parent Form's selected FRRT
                                frrv_forms = parent_form.ref_to_parent_form.filter(record_reference_type__pk=frrt_ref.pk)[0].record_reference.all()
                                #Now loop through it's related forms(usually will just be 1, but there could be multiple as well) if it exists                             
                                if frrv_forms:
                                    values = [] 
                                    for deep_form in frrv_forms:
                                        #For this deep parent form, find the FRAV with a FRAT parent that matches the provided Deep PK
                                        deep_frav_value = deep_form.formrecordattributevalue_set.filter(record_attribute_type__pk=entity_pk)[0].record_value
                                        #Only add this value to our list if it isn't blank--this will make sure we aren't adding arbitrary commas later
                                        if deep_frav_value and deep_frav_value != "":
                                            values.append(deep_frav_value)
                                    #make sure we are only using unique values by converting to a Set and back
                                    values = list(set(values)) 
                                    #add it to our list of distinct values
                                    distinct_value_list.append(",".join(values))
                                    #add it to our form_pk lookup dictionary
                                    new_form_rval_list[parent_form.pk] = ",".join(values)
                            except Exception as inst:
                                logger.warning(inst)
                                #If it fails, just default it to a 'blank' for this form--which means it has no values--in essence a 'default' value
                                new_form_rval_list[parent_form.pk] = ""
                    #Do some last minute cleanup here, like sorting the lists etc.
                    distinct_value_list = list(set(distinct_value_list))            
                    if entity_type.is_numeric: finalJSON['distinct_value_list'] = sorted(list(distinct_value_list), key=lambda e: float(e['record_value']))
                    else : finalJSON['distinct_value_list'] = list(distinct_value_list)                      
              
                elif code == "DEEP_FRRT":   # We need to get all the unique form IDs of the FRRT's related FRRTs FormType
                    # So for this guy I need a list of all the provided DEEP_FRRT's FRRVs referenced form ids(or names) and attach that to each of the parent forms
                    #   I mean..sounds easy enough right? WRONG.
                    #
                    #   Let's keep up the Grid Square metaphor from the previous if block and say I want to loop through all the grid square forms, and then find
                    #   --their relevant deep frrt values
                    #       *Let's loop through the parent grid square forms and grab it's relevant FRRV using the FRRT parent provided, then:
                    #       *for each 
                    
                    #Load our DEEP FRAT
                    entity_type = FormRecordReferenceType.objects.get(pk=entity_pk) 
                    #Figure out the FRRT referencing the DEEP FRRT by crossreferencing it between the provided FormType and FRRT
                    frrt_ref = parent_formtype.ref_to_parent_formtype.all().filter(form_type_reference__pk=entity_type.form_type_parent.pk)[0]
                    #Get our list of forms of this parent formtype
                    forms = parent_formtype.form_set.all();                   
                    #This if is just caching/processing the forms query before looping through it
                    if forms:
                        for parent_form in forms:
                            #Try loading the forms FRRV--and if it can't/doesn't exist then fall back to a default value
                            try:
                                #Get our FRRV for this form matching the parents Form's selected FRRT
                                frrv_forms = parent_form.ref_to_parent_form.filter(record_reference_type__pk=frrt_ref.pk)[0].record_reference.all()
                                #Now loop through it's related forms(usually will be 1, but ca be multiple) if it(they) exist(s)
                                if frrv_forms:
                                    values = []
                                    for deep_form in frrv_forms:
                                        #For this deep parent form, we need to find the frrv with a frrt that matches the provided Deep PK
                                        deep_frrv = deep_form.ref_to_parent_form.filter(record_reference_type__pk=entity_pk)
                                        #This is where we divert from the Deep FRAT code. We're going to have to get a list of the form names of this frrv's ManyToMany 'record_reference' field
                                        #First--we need to check if it exists, if it doesn't exist then just skip it and move on to the next deep_form
                                        if deep_frrv:
                                            deep_frrv_forms = deep_frrv[0].record_reference.all()
                                            for deep_frrv_form in deep_frrv_forms:
                                                values.append(deep_frrv_form.form_name)
                                    #Make sure we only use unique values by converting to a set and back. No double values needed
                                    values = list(set(values))
                                    #make sure we are only using unique values by converting to a Set and back
                                    values = list(set(values)) 
                                    #add it to our list of distinct values
                                    distinct_value_list.append(",".join(values))
                                    #add it to our form_pk lookup dictionary
                                    new_form_rval_list[parent_form.pk] = ",".join(values)
                            except Exception as inst:
                                logger.warning(inst)
                                #If it fails, just default it to a 'blank' for this form--which means it has no values--in essence a 'default' value
                                new_form_rval_list[parent_form.pk] = ""
                    #Do some last minute cleanup here, like sorting the lists etc.
                    distinct_value_list = sorted(list(set(distinct_value_list)))      
                    finalJSON['distinct_value_list'] = distinct_value_list
                elif code == "FRRT_ID":     # We need to get all the unique form IDs of the FRRT's related FormType
                    entity_type = FormRecordReferenceType.objects.get(pk=entity_pk)
                    #Now this is where it gets tricky I think. Normally our form_rval_list is a 1:1 form PK and it's value, but because we are dealing
                    #   --with a FRRT, it can have multiple values, or other forms, assigned to this parent form. We will store it as a key value where
                    #   --the value is a list of values
                    #Test: Get unique values for each form's frrt
                    #When we get a pk/value list of all the form values, we can loop through the dictionary list and add a new
                    #key to a new dict--if the key aleady exists, do a += to the existing key with the new value
                    #After that we need to sort and get ONLY unique values as a separate list--so maybe work in reverse how how we've already
                    #done this here
                    new_form_rval_list = {}
                    test_list = entity_type.formrecordreferencevalue_set.values('record_reference__form_name','form_parent__pk')
                    logger.info( test_list)
                    for pair in test_list:
                        if pair['form_parent__pk'] in new_form_rval_list:
                            new_form_rval_list[pair['form_parent__pk']] = new_form_rval_list[pair['form_parent__pk']] + "," + pair['record_reference__form_name']
                        else:
                            new_form_rval_list[pair['form_parent__pk']] = pair['record_reference__form_name']
                    logger.info( new_form_rval_list)
                    
                    distinct_value_list = sorted( list( set( list( new_form_rval_list.values() ) ) ) )
                    finalJSON['distinct_value_list'] = distinct_value_list
                elif code == "FORMID":      # We need to get all the unique form IDs of this current FormType
                    entity_type = FormType.objects.get(pk=entity_pk)    
                    distinct_value_list = entity_type.form_set.order_by('form_name').values_list('form_name', flat=True).distinct()
                    form_rval_list = entity_type.form_set.values('pk','form_name')   
                    new_form_rval_list = {}
                    for pair in form_rval_list:
                        new_form_rval_list[pair['pk']] = pair['form_name']
                    if entity_type.is_numeric: finalJSON['distinct_value_list'] = sorted(list(distinct_value_list), key=lambda e: float(e['form_name']))
                    else : finalJSON['distinct_value_list'] = list(distinct_value_list)
                elif code == "FRAT":        #We need to get all the unique values of the provided FRAT's RVALs
                    entity_type = FormRecordAttributeType.objects.get(pk=entity_pk)    
                    distinct_value_list = entity_type.formrecordattributevalue_set.order_by('record_value').values_list('record_value', flat=True).distinct()  
                    form_rval_list = entity_type.formrecordattributevalue_set.values('form_parent__pk','record_value')   
                    new_form_rval_list = {}
                    for pair in form_rval_list:
                        new_form_rval_list[pair['form_parent__pk']] = pair['record_value']
                    if entity_type.is_numeric:
                        sorted_list = list(distinct_value_list)
                        sorted_list.sort(key=float)
                        finalJSON['distinct_value_list'] = sorted_list
                    else : finalJSON['distinct_value_list'] = list(distinct_value_list)
                    
                elif code == "BACK_FRRT":
                    #We need a distinct list of the given frrt's formtype_parent form ids
                    #We then need a form list of the CURRENT formtype's forms that have a match
                    #  So using the same Grid Square Metaphor--we have a reverse lookup to "Object Forms" that are referencing a grid square.
                    #       **First let's get a list of all the Grid Squares
                    #       **Then we need a list of all the Object Forms referencing each grid square in a loop and add them to a list to return
                    entity_type = FormRecordReferenceType.objects.get(pk=entity_pk) 
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
                    finalJSON['distinct_value_list'] = list(distinct_value_list)         
                    
                elif code == "BACK_DEEP_FRAT":
                    back_frat_pk, frrt_pk = entity_pk.split(',')
                    entity_type = FormRecordAttributeType.objects.get(pk=back_frat_pk) 
                    frrt_ref = FormRecordReferenceType.objects.get(pk=frrt_pk) 
                    forms = frrt_ref.form_type_reference.form_set.all()
                    #First we need a distinct list of the back frat's unique values
                   
                    #Now we need a list of all the parent formtype(the formtype that's making the backwards request to the back frat) and their values for this FRAT
                    new_form_rval_list = {}#parent_formtype.formrecordattributevalue_set.values('form_parent__pk','record_value')   
                    distinct_value_list = []
                    if forms:
                        for form in forms:
                            try:
                                #Get all the FRRVs linking to this form 
                                ref_val = form.ref_to_value_form.filter(record_reference_type__pk=frrt_pk)
                                #Use the first FRRV from the list (for now)
                                frat_val = ref_val[0].form_parent.formrecordattributevalue_set.filter(record_attribute_type__pk=back_frat_pk)
                                logger.info( ref_val)
                                logger.info( ref_val.count())
                                if ref_val:
                                    values = []
                                    logger.info( "Working?")
                                    for refval in ref_val:
                                        values.append(refval.form_parent.formrecordattributevalue_set.filter(record_attribute_type__pk=back_frat_pk)[0].record_value)
                                    logger.info( "Working?")
                                    values = list(set(values)) 
                                    teststring =  ",".join(values)
                                    logger.info( teststring)
                                    distinct_value_list.append(teststring)
                                    new_form_rval_list[form.pk] = teststring
                            except:
                                new_form_rval_list[form.pk] = ""
                    distinct_value_list = list(set(distinct_value_list))            
                    if entity_type.is_numeric: finalJSON['distinct_value_list'] = sorted(list(distinct_value_list), key=lambda e: float(e['record_value']))
                    else : finalJSON['distinct_value_list'] = list(distinct_value_list)          
                    
                #If the requested entity_type isn't the user's project, and flagged as being inaccessible then stop the request
                if entity_type.project.pk != request.user.permissions.project.pk and (entity_type.flagged_for_deletion == True or entity_type.is_public == False): ERROR_MESSAGE += "Error: You are attempting to access records that don't exist. This probably occurred because your client attempted altering the POST data before sending"
                else:#Otherwise we are in the clear so grab the list and return it
                    #Return the JSON response
                    finalJSON['form_rval_list'] = new_form_rval_list                    
                    finalJSON = json.dumps(finalJSON)
                    return HttpResponse(finalJSON, content_type="application/json" )
                   
                
            else: ERROR_MESSAGE += "Error: You have not submitted through POST"
            
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")    
     
       
    #=======================================================#
    #   ACCESS LEVEL :  1      GET_GEO_QUANTITY_FRAT_COUNTER_AUTO *RECYCLING
    #=======================================================#   
    def get_geo_quantity_frat_counter_auto(self, request):
        #***************#
        ACCESS_LEVEL = 1
        #***************#            
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This Endpoint returns a json/dictionary of formPks and a count number for a given query
        #       --The query is for the quantitities classification in the geo-engine.
        #       --It allows the user to select from a list of the layer/formtype's available FRAT's that are tagged as "is_numeric = true"
        #           --It will sort all the values in a list, find the smallest/largest value and default to a "regular interval" classification
        #           --based on the # of classes provided by the user's request. 
        #               *If it's more than the number of found values, it will divide/round up between the min and max
        #               *If it's less than the number of found values, the classes will still be divided/round up between the max and min
        #           --It will then produce a dictionary of json objects that follow the structure:
        #               { "<form_pk>": {"frat_value":"<numeric value>", "class_color":"<#ffffff>"},
        #                 "<form_pk>": {"frat_value":"<numeric value>", "class_color":"<#ffffff>"}
        #               }
        #           --The client-side javascript will then use this dictionary to loop through the openlayers formtype layer features, 
        #           --and color them according to their PK value in this dictionary
        #
        #
        
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
        
            #We need to return a json list of all RVALS that match the provided RTYPE
            if request.method == "POST":
                #Setup the necessary variables
                finalJSON = {}
                rtype_code = request.POST['rtype_code']
                code, PK = rtype_code.split('-')
                num_of_classes = int(request.POST['num_of_classes'])
                color_list = request.POST['color_list']
                color_list = color_list.split(",")
                logger.info(request.POST['color_list'])
                parent_formtype = FormType.objects.get(pk=request.POST['formtype_pk'])   
                frat = FormRecordAttributeType.objects.get(pk=PK)
                parent_forms = parent_formtype.form_set.all()
                value_list = []
                issues = []
                form_dict = {}
                finalJSON['issues'] = issues
                finalJSON['form_dict'] = form_dict
                #First let's build our dictionary but leave the class value blank
                #We'll need to loop through a list of the forms and build it form by form                
                if parent_forms:
                    num_of_forms = parent_forms.count()
                    #if num_of_classes > num_of_forms: num_of_classes = num_of_forms
                    for form in parent_forms:
                        new_class = {}
                        #Set the frat value of our new dictionary entry
                        #--also check that one exists for the form as a precaution, if not, then give it a blank
                        frat_value = form.formrecordattributevalue_set.filter(record_attribute_type__pk=frat.pk)
                        if frat_value: 
                            new_class['frat_value'] = frat_value[0].record_value
                            try:
                                value_list.append(float(frat_value[0].record_value))
                            except:
                               issues.append("Form " + str(form.form_name) + " does not a valid Float value for its FRAT: "  + str(frat.record_type) + " --value skipped and treated as blank.")
                        else: new_class['frat_value'] = ""    
                        form_dict[form.pk] = new_class

                #Now that we have our dictionary setup, let's classify our number list
                #Idealling, just sort it is as easy as sort() lol 
                value_list.sort()
                #Let's get our min and max which should now be the first and last index of our list
                min_value = value_list[0]
                max_value = value_list[len(value_list)-1]

                class_interval =  (max_value - min_value) / num_of_classes
                final_class_list = []
                #round our interval to a whole number--this rounds it as best possible as a float--truncates it to a whole number by casting int() and then makes it a float again
                class_interval = float(int(round(class_interval))) 
                #Start Our loop--our class structure will look like this:
                #   [  {"max":<#>, "min":<#>},
                #      {"max":<#>, "min":<#>},
                #      {"max":<#>, "min":<#>}
                #   ]
                #
                #   My equal interval range class algorithm is as follows: (pretty simple--not perfect but works)
                #
                #       For Each Loop iteration (n)
                #       range_start =  min + (n x class_interval)
                #       range_end   =  range_start + (class_interval - 1)
                #       --->If last iteration, then range_end = max
                
                for n in range(num_of_classes):
                    new_class = {}
                    new_class['min'] = str(min_value + (n * class_interval))
                    if n < num_of_classes - 1: new_class['max'] = str( float(new_class['min']) + (class_interval - 1 ))
                    else:                      new_class['max'] = str(max_value)
                    #add our color
                    new_class['color'] = color_list[n]
                    final_class_list.append(new_class)
                finalJSON['class_list'] = final_class_list
                
                #   Now let's determine the color for each form's found FRAT value.
                #   --The color_list will be the same length as our class_list so we can use whatever index value from
                #   --our class_list to find the matching color.
                #
                #   First let's loop through our new form dictionary and look up it's value in our class list
                
                for key, value in form_dict.items():
                    val = value['frat_value']
                    logger.info(val)
                    #set our initial default color(transparent)
                    value['color'] = "rgba(0,0,0,0)"
                    #We use a try statement to see if the form has an actual value assigned--if it's "" (blank) it will fail and we'll keep our default as a transparent color passed as a string
                    try: 
                        val = float(val)
                        #It worked! Now loop through our classes and determine which one this value falls in
                        #   --If no range is matched(which should never happen--but just in case--we still have our default value
                        for index, range_set in enumerate(final_class_list):
                            logger.info(float(range_set['min']))
                            logger.info(float(range_set['max']))
                            if val >= float(range_set['min']) and val <= float(range_set['max']):
                                value['color'] = range_set['color']
                                logger.info("FOUND A RANGE ^^")
                            if (index+1) == len(final_class_list) and value['color'] == "rgba(0,0,0,0)": 
                                issues.append("Issue: The value '" + str(val) + "' for pk=" +key+ " Form didn't match the provided ranges")
                    except Exception as e: logger.warning(e)
                #If the requested frat isn't the user's project, and flagged as being inaccessible then stop the request
                if frat.project.pk != request.user.permissions.project.pk and (frat.flagged_for_deletion == True or frat.is_public == False): ERROR_MESSAGE += "Error: You are attempting to access records that don't exist. This probably occurred because your client attempted altering the POST data before sending"
                else:#Otherwise we are in the clear so grab the list and return it
                    #Return the JSON response
                    finalJSON = json.dumps(finalJSON)
                    return HttpResponse(finalJSON, content_type="application/json")
                   
                
            else: ERROR_MESSAGE += "Error: You have not submitted through POST"
            
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")    

        
    #=======================================================#
    #   ACCESS LEVEL :  1      GET_GEO_NUMERIC_RTYPES *RECYCLING
    #=======================================================#   
    def get_geo_numeric_rtypes(self, request):
        #***************#
        ACCESS_LEVEL = 1
        #***************#            
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This Endpoint returns a list of all rtypes (FRATS) for a provided formtype pk if their "is_numeric" flag is set to TRUE.
        
        
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
                        for FRAT in currentFormType.formrecordattributetype_set.all().filter(flagged_for_deletion=False, is_numeric=True):
                            currentRTYPE = {}
                            currentRTYPE['label'] = FRAT.record_type
                            currentRTYPE['pk'] = FRAT.pk
                            currentRTYPE['rtype'] = 'FRAT'
                            rtypeList.append(currentRTYPE)

                    else:
                        #***RECYCLING BIN***  Make sure that the returned FRAT AND FRRTS are filtered by their deletion flags. Don't want them returned in the query
                        for FRAT in currentFormType.formrecordattributetype_set.all().filter(flagged_for_deletion=False, is_public=True, is_numeric=True):
                            currentRTYPE = {}
                            currentRTYPE['label'] = FRAT.record_type
                            currentRTYPE['pk'] = FRAT.pk
                            currentRTYPE['rtype'] = 'FRAT'
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
    #   ACCESS LEVEL :  1      GET_GEO_GRADUATED_APPLIED_CLASSES *RECYCLING
    #=======================================================#   
    def get_geo_graduated_applied_classes(self, request):
        #***************#
        ACCESS_LEVEL = 1
        #***************#            
        
        #----------------------------------------------------------------------------------------------------------------------------
        #  
        
        
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
        
            #We need to return a json list of all formtype RTYPES that match the provided formtype pk
            if request.method == "POST":
                #Grab the formtype
                currentFormType = FormType.objects.get(pk=request.POST['formtype_pk'])
                rtype_code = request.POST['rtype_code']
                class_list = json.loads(request.POST['class_list'])
                issues = []
                #If the requested formtype isn't the user's project, and flagged as being inaccessible then stop the request
                if currentFormType.project.pk != request.user.permissions.project.pk and (currentFormType.flagged_for_deletion == True or currentFormType.is_public == False):
                    ERROR_MESSAGE += "Error: You are attempting to access records that don't exist. This probably occurred because your client attempted altering the POST data before sending"
                #Otherwise we are in the clear so grab the list and return it
                else:
                    rtype, rtype_pk = rtype_code.split('-')
                    if rtype == "FRAT":  
                        form_list = {}
                        for form in currentFormType.form_set.all():
                            value = form.formrecordattributevalue_set.filter(record_attribute_type__pk=rtype_pk)
                            if value.exists(): value = value[0].record_value
                            else: value = ""
                            new_class = {}
                            new_class['color'] = "rgba(0,0,0,0)"
                            new_class['value'] = value
                            #Now let's make sure that our 'value' is a proper number--if not just add our defaults for this form and move to the next
                            try:
                                value = float(value)                            
                                # Now loop through our classes and determine which one this value falls in
                                #   --If no range is matched(which should never happen--but just in case--we still have our default value
                                for index, range_set in enumerate(class_list):
                                    if value >= float(range_set['min']) and value <= float(range_set['max']):                                    
                                        new_class['color'] = range_set['color']
                                        logger.info("FOUND A RANGE ^^")
                                    if (index+1) == len(class_list) and value['color'] == "rgba(0,0,0,0)": 
                                        issues.append("Issue: The value '" + str(val) + "' for pk=" +key+ " Form didn't match the provided ranges")
                            except: pass

                            form_list[form.pk] = new_class
                            
                        #Send off our completed query
                        finalJSON = {}
                        finalJSON['issues'] = issues
                        finalJSON['form_list'] = form_list                    
                        finalJSON = json.dumps(finalJSON)
                        return HttpResponse(finalJSON, content_type="application/json" )                        
            else: ERROR_MESSAGE += "Error: You have not submitted through POST"
            
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")    


    #=======================================================#
    #   ACCESS LEVEL :  1      GET_GEO_RULES_CLASSES *RECYCLING
    #=======================================================#   
    def get_geo_rules_classes(self, request):
        #***************#
        ACCESS_LEVEL = 1
        #***************#            
        
        #----------------------------------------------------------------------------------------------------------------------------
        #   This Endpoint returns a list of all forms of a given formtype with a corresponding color to a provided class if it matches
        #   
        #   --This is incredibly similar to how the master query engine works, but we aren't ripping out a series of counts. We are ripping
        #   ----what amounts to a T/F value for each form in the formtype. It goes by order--so the last class checked will overwrite any
        #   ----previous class tested, so ordering is VERY important, e.g. if a Form is tested for two rules checking for different things
        #   ----but it matches both classes, the latter test will we the test that is returned in the JSON response rather than the former.
        #
        #   --Esentially we will loop through each provided class in the POST data, and run a Django query for each rule or "filter" in Django
        #   ----terms. It will either exists()  or not. If it does not, it's skipped, otherwise it's given the corresponding color of the class
        #   ----checked.
        #
        #   --This will be slightly less complicated than the master query engine, A: I'm better at coding this system, and B: It's not returning
        #   ----a dense list of forms etc. It's only returning simplified and necessary information.
        #
        #   We should have 'formtype_pk'  'class_list'  in our POST data
        
        
        ERROR_MESSAGE = ""
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):
        
            #We need to return a json list of all formtype RTYPES that match the provided formtype pk
            if request.method == "POST":
                logger.info(request.POST)
                #Grab the formtype
                currentFormType = FormType.objects.get(pk=request.POST['formtype_pk'])
                class_list = json.loads(request.POST['class_list'])
                issues = []
                form_list = {}
                #If the requested formtype isn't the user's project, and flagged as being inaccessible then stop the request
                if currentFormType.project.pk != request.user.permissions.project.pk and (currentFormType.flagged_for_deletion == True or currentFormType.is_public == False):
                    ERROR_MESSAGE += "Error: You are attempting to access records that don't exist. This probably occurred because your client attempted altering the POST data before sending"
                #Otherwise we are in the clear so grab the list and return it
                else:
                    #Start looping through our classes and performing the queries, THIS is where the real logic occurs
                    for aClass in class_list:
                        class_color = aClass['color']
                        master_form_set = currentFormType.form_set.all()
                        #Now let's loop through each of our constraints
                        #We'll setup a quick counter so we skip the andor of the first constraint(it's disabled and moot)
                        counter = 0
                        for constraint in aClass['constraints']:
                            RTYPE, RTYPE_PK = constraint['RTYPE'].split('-')
                            QCODE = constraint['QCODE']
                            ANDOR = constraint['ANDOR']
                            RVAL  = constraint['RVAL']
                            forms = currentFormType.form_set.all()
                            logger.info(RVAL)
                            if   RTYPE == "FRAT":
                                if QCODE == "contains":     forms = forms.filter(   formrecordattributevalue__record_attribute_type__pk=RTYPE_PK, formrecordattributevalue__record_value__icontains=RVAL)
                                if QCODE == "contains(cs)": forms = forms.filter(   formrecordattributevalue__record_attribute_type__pk=RTYPE_PK, formrecordattributevalue__record_value__contains=RVAL)
                                if QCODE == "exact":        forms = forms.filter(   formrecordattributevalue__record_attribute_type__pk=RTYPE_PK, formrecordattributevalue__record_value__exact=RVAL)
                                if QCODE == "excludes":     forms = forms.exclude(  formrecordattributevalue__record_attribute_type__pk=RTYPE_PK, formrecordattributevalue__record_value__icontains=RVAL)
                                if QCODE == "null":         forms = forms.filter(Q( formrecordattributevalue__record_attribute_type__pk=RTYPE_PK), Q(formrecordattributevalue__record_value__exact="") | Q(formrecordattributevalue__record_value__isnull) | Q(formrecordattributevalue__record_value__exact=" ")) #Tests for NULL, "" and " " for more reliable redundancy
                            elif RTYPE == "FRRT_ID":
                                if QCODE == "contains":     forms = forms.filter(  ref_to_parent_form__record_reference_type__pk=RTYPE_PK, ref_to_parent_form__record_reference__form_name__icontains=RVAL)
                                if QCODE == "contains(cs)": forms = forms.filter(  ref_to_parent_form__record_reference_type__pk=RTYPE_PK, ref_to_parent_form__record_reference__form_name__contains=RVAL)
                                if QCODE == "exact":        forms = forms.filter(  ref_to_parent_form__record_reference_type__pk=RTYPE_PK, ref_to_parent_form__record_reference__form_name__exact=RVAL)
                                if QCODE == "excludes":     forms = forms.exclude( ref_to_parent_form__record_reference_type__pk=RTYPE_PK, ref_to_parent_form__record_reference__form_name__icontains=RVAL)
                                if QCODE == "null":         forms = forms.filter(Q(ref_to_parent_form__record_reference_type__pk=RTYPE_PK), Q(ref_to_parent_form__record_reference__form_name__exact="") | Q(ref_to_parent_form__record_reference__form_name__isnull) | Q(ref_to_parent_form__record_reference__form_name__exact=" ")) #Tests for NULL, "" and " " for more reliable redundancy
                            elif RTYPE == "DEEP_FRAT":
                                DEEP_PK, PARENT_PK = RTYPE_PK.split(',')
                                deep_frat = FormRecordAttributeType.objects.get(pk=DEEP_PK)
                                deep_parent_forms = deep_frat.form_type.form_set.all()
                                #--So we first look up ALL the forms that have an RVAL that: both matches our provided value && AND &&  have an RTYPE that matches the provided PK(Our Deep PK)
                                #--We only need a flattened list of the PKS
                                if QCODE == "contains":     deep_frat_matches = list(deep_parent_forms.filter(  formrecordattributevalue__record_attribute_type__pk=DEEP_PK, formrecordattributevalue__record_value__icontains=RVAL, ).values_list('pk', flat=True))
                                if QCODE == "contains(cs)": deep_frat_matches = list(deep_parent_forms.filter(  formrecordattributevalue__record_attribute_type__pk=DEEP_PK, formrecordattributevalue__record_value__contains=RVAL, ).values_list('pk', flat=True))
                                if QCODE == "exact":        deep_frat_matches = list(deep_parent_forms.filter(  formrecordattributevalue__record_attribute_type__pk=DEEP_PK, formrecordattributevalue__record_value__xact=RVAL, ).values_list('pk', flat=True))
                                if QCODE == "excludes":     deep_frat_matches = list(deep_parent_forms.exclude( formrecordattributevalue__record_attribute_type__pk=DEEP_PK, formrecordattributevalue__record_value__icontains=RVAL).values_list('pk', flat=True))
                                if QCODE == "null":         deep_frat_matches = list(deep_parent_forms.filter(Q(formrecordattributevalue__record_attribute_type__pk=DEEP_PK), Q(formrecordattributevalue__record_value__isnull) | Q(formrecordattributevalue__record_value__exact="") | Q(formrecordattributevalue__record_value__exact=" ")).values_list('pk', flat=True))
                                #NOW we get all of our parent formtype's forms, and check to see which ones have FRRVs with matching PK references and that match our parent FRRT
                                #   **If we don't check for the original FRRT, then forms that have two different FRRTs referencing the same FormType in question, will falsely be queried.
                                #   **We ONLY want the FRRT of the Parent FormType to look for cross matches--not ANY FRRT
                                forms = forms.filter(ref_to_parent_form__record_reference__pk__in=deep_frat_matches, ref_to_parent_form__record_reference_type__pk=PARENT_PK)
                            elif RTYPE == "DEEP_FRRT":
                                DEEP_PK, PARENT_PK = RTYPE_PK.split(',')
                                #This is kind of ingenious--compared to how I handled it originally with the master query engine
                                #--So we first look up ALL the forms that have an RVAL that: both matches our provided value && AND &&  have an RTYPE that matches the provided PK(Our Deep PK)
                                #--We only need a flattened list of the PKS
                                if QCODE == "contains":     deep_frrt_matches = list(Form.objects.all().filter(  ref_to_parent_form__record_reference_type__pk=DEEP_PK, ref_to_parent_form__record_reference__form_name__icontains=RVAL, ).values_list('pk', flat=True))
                                if QCODE == "contains(cs)": deep_frrt_matches = list(Form.objects.all().filter(  ref_to_parent_form__record_reference_type__pk=DEEP_PK, ref_to_parent_form__record_reference__form_name__contains=RVAL, ).values_list('pk', flat=True))
                                if QCODE == "exact":        deep_frrt_matches = list(Form.objects.all().filter(  ref_to_parent_form__record_reference_type__pk=DEEP_PK, ref_to_parent_form__record_reference__form_name__exact=RVAL, ).values_list('pk', flat=True))
                                if QCODE == "excludes":     deep_frrt_matches = list(Form.objects.all().exclude( ref_to_parent_form__record_reference_type__pk=DEEP_PK, ref_to_parent_form__record_reference__form_name__icontains=RVAL).values_list('pk', flat=True))
                                if QCODE == "null":         deep_frrt_matches = list(Form.objects.all().filter(Q(ref_to_parent_form__record_reference_type__pk=DEEP_PK), Q(ref_to_parent_form__record_reference__form_name__isnull) | Q(ref_to_parent_form__record_reference__form_name__exact="") | Q(ref_to_parent_form__record_reference__form_name__exact=" ")).values_list('pk', flat=True))
                                #NOW we get all of our parent formtype's forms, and check to see which ones have FRRVs with matching PK references and that match our parent FRRT
                                #   **If we don't check for the original FRRT, then forms that have two different FRRTs referencing the same FormType in question, will falsely be queried.
                                #   **We ONLY want the FRRT of the Parent FormType to look for cross matches--not ANY FRRT
                                forms = forms.filter(ref_to_parent_form__record_reference__pk__in=deep_frrt_matches, ref_to_parent_form__record_reference_type__pk=PARENT_PK)
                            elif RTYPE == "FORM_ID":
                                if QCODE == "contains":     forms = forms.filter(  form_name__icontains=RVAL)
                                if QCODE == "contains(cs)": forms = forms.filter(  form_name__contains=RVAL)
                                if QCODE == "exact":        forms = forms.filter(  form_name__exact=RVAL)
                                if QCODE == "excludes":     forms = forms.exclude( form_name__icontains=RVAL)
                                if QCODE == "null":         forms = forms.filter(Q(form_name__contains="") | Q(form_name__isnull) | Q(form_name__contains=" ")) #Tests for NULL, "" and " " for more reliable redundancy                                 
                            elif RTYPE == "BACK_FRRT": #(Or Form IDs that reference this formtype)
                                back_frrt = FormRecordReferenceType.objects.get(pk=RTYPE_PK)
                                back_parent_forms = back_frrt.form_type_parent.form_set.all()
                                if QCODE == "contains":     back_frrt_matches = list( back_parent_forms.filter(  form_name__icontains=RVAL).values_list('pk', flat=True))
                                if QCODE == "contains(cs)": back_frrt_matches = list( back_parent_forms.filter(  form_name__contains=RVAL).values_list('pk', flat=True))
                                if QCODE == "exact":        back_frrt_matches = list( back_parent_forms.filter(  form_name__exact=RVAL).values_list('pk', flat=True))
                                if QCODE == "excludes":     back_frrt_matches = list( back_parent_forms.exclude( form_name__icontains=RVAL).values_list('pk', flat=True))
                                if QCODE == "null":         back_frrt_matches = list( back_parent_forms.filter(Q(form_name__contains="") | Q(form_name__isnull) | Q(form_name__contains=" ")).values_list('pk', flat=True)) #Tests for NULL, "" and " " for more reliable redundancy   
                                forms = forms.filter(ref_to_value_form__form_parent__pk__in=back_frrt_matches, ref_to_value_form__record_reference_type__pk=RTYPE_PK)              
                            elif RTYPE == "BACK_DEEP_FRAT":
                                BACK_FRAT_PK, FRRT_PK = RTYPE_PK.split(',')
                                back_frat = FormRecordAttributeType.objects.get(pk=BACK_FRAT_PK)
                                back_parent_forms = back_frat.form_type.form_set.all()
                                #Get our list of form PKs that have matches to our submitted value
                                if QCODE == "contains":     back_frat_matches = list(back_parent_forms.filter(  formrecordattributevalue__record_attribute_type__pk=BACK_FRAT_PK, formrecordattributevalue__record_value__icontains=RVAL).values_list('pk', flat=True))
                                if QCODE == "contains(cs)": back_frat_matches = list(back_parent_forms.filter(  formrecordattributevalue__record_attribute_type__pk=BACK_FRAT_PK, formrecordattributevalue__record_value__contains=RVAL).values_list('pk', flat=True))
                                if QCODE == "exact":        back_frat_matches = list(back_parent_forms.filter(  formrecordattributevalue__record_attribute_type__pk=BACK_FRAT_PK, formrecordattributevalue__record_value__exact=RVAL).values_list('pk', flat=True))
                                if QCODE == "excludes":     back_frat_matches = list(back_parent_forms.exclude( formrecordattributevalue__record_attribute_type__pk=BACK_FRAT_PK, formrecordattributevalue__record_value__icontains=RVAL).values_list('pk', flat=True))
                                if QCODE == "null":         back_frat_matches = list(back_parent_forms.filter(Q(formrecordattributevalue__record_attribute_type__pk=BACK_FRAT_PK), Q(formrecordattributevalue__record_value__isnull) | Q(formrecordattributevalue__record_value__exact="") | Q(formrecordattributevalue__record_value__exact=" ")).values_list('pk', flat=True))
                                #Now we have to go backwards through the parent formtype form set and similarly to deep frats do the same thing--but through the alternate 'ref_to_value_form' table rather than the 'ref_to_parent_form' table
                                #!!!!!TODO!!!!!  I'm doing this slightly different from past BACK queries--before I looped through each of the above forms, and stored their list of PKs in the FRRT linking back to our parent formtype
                                #******I'm not sure if this way is fast or not--but it does look cleaner at least. 
                                forms = forms.filter(ref_to_value_form__form_parent__pk__in=back_frat_matches, ref_to_value_form__record_reference_type__pk=FRRT_PK)
                            elif RTYPE == "BACK_DEEP_FRRT":  
                                BACK_FRRT_PK, FRRT_PK = RTYPE_PK.split(',')
                                back_frrt = FormRecordReferenceType.objects.get(pk=BACK_FRRT_PK)
                                back_parent_forms = back_frrt.form_type_parent.form_set.all()
                                #Get our list of form PKs that have matches to our submitted value                            
                                if QCODE == "contains":     back_frrt_matches = list(Form.objects.all().filter(  ref_to_parent_form__record_reference_type__pk=BACK_FRRT_PK, ref_to_parent_form__record_reference__form_name__icontains=RVAL, ).values_list('pk', flat=True))
                                if QCODE == "contains(cs)": back_frrt_matches = list(Form.objects.all().filter(  ref_to_parent_form__record_reference_type__pk=BACK_FRRT_PK, ref_to_parent_form__record_reference__form_name__contains=RVAL, ).values_list('pk', flat=True))
                                if QCODE == "exact":        back_frrt_matches = list(Form.objects.all().filter(  ref_to_parent_form__record_reference_type__pk=BACK_FRRT_PK, ref_to_parent_form__record_reference__form_name__exact=RVAL, ).values_list('pk', flat=True))
                                if QCODE == "excludes":     back_frrt_matches = list(Form.objects.all().exclude( ref_to_parent_form__record_reference_type__pk=BACK_FRRT_PK, ref_to_parent_form__record_reference__form_name__icontains=RVAL).values_list('pk', flat=True))
                                if QCODE == "null":         back_frrt_matches = list(Form.objects.all().filter(Q(ref_to_parent_form__record_reference_type__pk=BACK_FRRT_PK), Q(ref_to_parent_form__record_reference__form_name__isnull) | Q(ref_to_parent_form__record_reference__form_name__exact="") | Q(ref_to_parent_form__record_reference__form_name__exact=" ")).values_list('pk', flat=True))
                                #Now we have to go backwards through the parent formtype form set and similarly to deep frrts do the same thing--but through the alternate 'ref_to_value_form' table rather than the 'ref_to_parent_form' table
                                #!!!!!TODO!!!!!  I'm doing this slightly different from past BACK queries--before I looped through each of the above forms, and stored their list of PKs in the FRRT linking back to our parent formtype
                                #******I'm not sure if this way is fast or not--but it does look cleaner at least. 
                                logger.info(back_frrt_matches)
                                forms = forms.filter(ref_to_value_form__form_parent__pk__in=back_frrt_matches, ref_to_value_form__record_reference_type__pk=FRRT_PK)                            
                            logger.info(forms)
                            
                            #Now figure out if we're in the first loop or not--if we are, there is no AND/OR qualifier, otherwise add it
                            if counter == 0: master_form_set = forms
                            else:
                                if   ANDOR == "AND": master_form_set = master_form_set.intersection(forms)
                                elif ANDOR == "OR" : master_form_set = master_form_set.union(forms)
                            counter += 1
                        #Once we've fininshed building our master list of queried forms--let's see if it exists
                        #If there are hits in the database, then let's get a flattened list of those Form PKs and add them to our dictionary
                        #--with the corresponding class color, otherwise do nothing
                        if master_form_set.exists():
                            form_pks = master_form_set.values_list('pk',flat=True)
                            for pk in form_pks: form_list[pk] = {"color":class_color, "value":""}
                    #Send off our completed query
                    finalJSON = {}
                    finalJSON['issues'] = issues
                    finalJSON['form_list'] = form_list                    
                    finalJSON = json.dumps(finalJSON)
                    return HttpResponse(finalJSON, content_type="application/json" )                        
            else: ERROR_MESSAGE += "Error: You have not submitted through POST"
            
        else: ERROR_MESSAGE += "Error: You do not have permission to access modifying user information"
        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'"}',content_type="application/json")    











        
    ##==========================================================================================================================    
    #  ADMIN DJANGO VIEWS   ****************************************************************************************************
    ##==========================================================================================================================    


    #=====================================================================================#
    #   ACCESS LEVEL :  1    TEMPLATE_ACCESS_LEVEL : 3   VIEW_FORM_TYPE() *RECYCLING
    #=====================================================================================#       
    def view_form_type(self, request, **kwargs):
        #************************#
        ACCESS_LEVEL = 1
        TEMPLATE_ACCESS_LEVEL = 3
        #************************#
        #-----------------------------------------------------------------------------------
        #   This view displays the view form type template--or essentially the query engine
        #   --attached to it. It allows the user to look at forms and their details in bulk
        #   --according to their form type, and also allows those forms to be queried by
        #   --the query engine where graphs/charts etc. are produced. All this view needs to
        #   --do is pass a few variables to the template, and display the template. The AJAX
        #   --and template will handle all permissions etc. from there
        ERROR_MESSAGE = ""

        #Setup our variable's we'll pass to the template if allowed
        try:
            project = FormProject.objects.get(pk=kwargs['project_pk'])
            formtype = FormType.objects.get(pk=kwargs['form_type_pk'])
        except:
            raise Http404("This Page Does Not Exist!")    
            
        #*** RECYCLING BIN *** Return a 404 Error if the requsted model instance is flagged for deletion (in the recycling bin)    
        if formtype.flagged_for_deletion == True: raise Http404("This Page Does Not Exist!")
        
        #Make sure the user is trying to access their project and not another project
        #If they are trying to access another project--warn them their action has been logged
        #after redirecting them to a warning page
        if project.pk == request.user.permissions.project.pk and formtype.project.pk == request.user.permissions.project.pk:
            counter = Counter()
            counter.reset()
            kwargs.update({'user': request.user,'has_permission': admin.site.has_permission(request)})
            kwargs.update({'api_urls':get_api_endpoints()})
            kwargs.update({'access_level':TEMPLATE_ACCESS_LEVEL})
            kwargs.update({'user_access':request.user.permissions.access_level})
            kwargs.update({'user_project':request.user.permissions.project})
            kwargs.update({'counter':counter}) 
            kwargs.update({'project':project}) 
            kwargs.update({'formtype':formtype}) 
            kwargs.update({'form':'False'})
            kwargs.update({'toolbar_title_code': 'FormType_' + kwargs['form_type_pk']})
            kwargs.update({'deletable': 'False'})
            logger.info( request)
        else:
            #If anything goes wrong in the process, return an error in the json HTTP Response
            SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), 'Trying to access another project.', request.META)
            return render(request, 'maqluengine/admin_warning.html', kwargs)
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):        
            return render(request, 'maqluengine/view_form_type.html', kwargs)    
        else: ERROR_MESSAGE += "Error: You do not have permission to view this page"
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        kwargs.update({'ERROR_MESSAGE': ERROR_MESSAGE})
        return render(request, 'maqluengine/admin_error.html', kwargs)            
 
    #=====================================================================================#
    #   ACCESS LEVEL :  1    TEMPLATE_ACCESS_LEVEL : 3   QUERY_FORM_TYPE() *RECYCLING
    #=====================================================================================#       
    def query_form_type(self, request, **kwargs):
        #************************#
        ACCESS_LEVEL = 1
        TEMPLATE_ACCESS_LEVEL = 3
        #************************#
        #-----------------------------------------------------------------------------------
        #   This view displays the view form type template--or essentially the query engine
        #   --attached to it. It allows the user to look at forms and their details in bulk
        #   --according to their form type, and also allows those forms to be queried by
        #   --the query engine where graphs/charts etc. are produced. All this view needs to
        #   --do is pass a few variables to the template, and display the template. The AJAX
        #   --and template will handle all permissions etc. from there
        ERROR_MESSAGE = ""

        #Setup our variable's we'll pass to the template if allowed
        try:
            project = FormProject.objects.get(pk=kwargs['project_pk'])
            formtype = FormType.objects.get(pk=kwargs['form_type_pk'])
        except:
            raise Http404("This Page Does Not Exist!")    
            
        #*** RECYCLING BIN *** Return a 404 Error if the requsted model instance is flagged for deletion (in the recycling bin)    
        if formtype.flagged_for_deletion == True: raise Http404("This Page Does Not Exist!")
        
        #Make sure the user is trying to access their project and not another project
        #If they are trying to access another project--warn them their action has been logged
        #after redirecting them to a warning page
        if project.pk == request.user.permissions.project.pk and formtype.project.pk == request.user.permissions.project.pk:
            counter = Counter()
            counter.reset()
            kwargs.update({'user': request.user,'has_permission': admin.site.has_permission(request)})
            kwargs.update({'api_urls':get_api_endpoints()})
            kwargs.update({'access_level':TEMPLATE_ACCESS_LEVEL})
            kwargs.update({'user_access':request.user.permissions.access_level})
            kwargs.update({'user_project':request.user.permissions.project})
            kwargs.update({'counter':counter}) 
            kwargs.update({'project':project}) 
            kwargs.update({'formtype':formtype}) 
            kwargs.update({'form':'False'})
            kwargs.update({'toolbar_title_code': 'FormType_' + kwargs['form_type_pk']})
            kwargs.update({'deletable': 'False'})
            logger.info( request)
            logger.info(kwargs)
        else:
            #If anything goes wrong in the process, return an error in the json HTTP Response
            SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), 'Trying to access another project.', request.META)
            return render(request, 'maqluengine/admin_warning.html', kwargs)
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):        
            return render(request, 'maqluengine/query_form_type.html', kwargs)    
        else: ERROR_MESSAGE += "Error: You do not have permission to view this page"
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        kwargs.update({'ERROR_MESSAGE': ERROR_MESSAGE})
        return render(request, 'maqluengine/admin_error.html', kwargs)            

     #=====================================================================================#
    #   ACCESS LEVEL :  1    TEMPLATE_ACCESS_LEVEL : 3   MASTER_QUERY_ENGINE() *RECYCLING
    #=====================================================================================#       
    def master_query_engine(self, request, **kwargs):
        #************************#
        ACCESS_LEVEL = 1
        TEMPLATE_ACCESS_LEVEL = 3
        #************************#
        #-----------------------------------------------------------------------------------
        #   This view displays the view form type template--or essentially the query engine
        #   --attached to it. It allows the user to look at forms and their details in bulk
        #   --according to their form type, and also allows those forms to be queried by
        #   --the query engine where graphs/charts etc. are produced. All this view needs to
        #   --do is pass a few variables to the template, and display the template. The AJAX
        #   --and template will handle all permissions etc. from there
        ERROR_MESSAGE = ""

        #Setup our variable's we'll pass to the template if allowed
        try:
            project = FormProject.objects.get(pk=kwargs['project_pk'])
        except:
            raise Http404("This Page Does Not Exist!")    
            
        
        #Make sure the user is trying to access their project and not another project
        #If they are trying to access another project--warn them their action has been logged
        #after redirecting them to a warning page
        if project.pk == request.user.permissions.project.pk:
            counter = Counter()
            counter.reset()
            kwargs.update({'user': request.user,'has_permission': admin.site.has_permission(request)})
            kwargs.update({'api_urls':get_api_endpoints()})
            kwargs.update({'access_level':TEMPLATE_ACCESS_LEVEL})
            kwargs.update({'user_access':request.user.permissions.access_level})
            kwargs.update({'user_project':request.user.permissions.project})
            kwargs.update({'counter':counter}) 
            kwargs.update({'project':project})
            kwargs.update({'form':'False'})
            kwargs.update({'toolbar_title_code': 'Project_' + kwargs['project_pk']})
            kwargs.update({'deletable': 'False'})
            
            logger.info( request)
            
            if 'starter_query' in request.GET: kwargs.update({'starter_query':request.GET['starter_query']})
            
            
        else:
            #If anything goes wrong in the process, return an error in the json HTTP Response
            SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), 'Trying to access another project.', request.META)
            return render(request, 'maqluengine/admin_warning.html', kwargs)
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):        
            return render(request, 'maqluengine/master_query_engine.html', kwargs)    
        else: ERROR_MESSAGE += "Error: You do not have permission to view this page"
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        kwargs.update({'ERROR_MESSAGE': ERROR_MESSAGE})
        return render(request, 'maqluengine/admin_error.html', kwargs)            


    #=====================================================================================#  
    #   ACCESS LEVEL :  4   TEMPLATE_ACCESS_LEVEL : 4    GEOJSON_IMPORTER()
    #=====================================================================================#  
    def geojson_importer(self, request, **kwargs):
        #************************#
        ACCESS_LEVEL = 4
        TEMPLATE_ACCESS_LEVEL = 4
        #************************#
        #-----------------------------------------------------------------------------------
        #-----------------------------------------------------------------------------------
        #   This view displays the base template for the CSV importer to create new form types
        #   --and populate them with forms based on rows in the CSV
        #   --Most of the logic is done in an API Endpoint, but the base template provides the necessary
        #   --tools in Jscript to perform all of this.
        #   The Importer works client-side to process the CSV file in JSON and when the user finishes the form,
        #   --it will upload the processed CSV data to the server and run the actual database import
        ERROR_MESSAGE = ""
        
        try:
            project = FormProject.objects.get(pk=kwargs['project_pk'])
        except:
            raise Http404("Project Does Not Exist!")       
            
        if project.pk == request.user.permissions.project.pk:
            counter = Counter()
            counter.reset()
            kwargs.update({'user': request.user,'has_permission': admin.site.has_permission(request)})
            kwargs.update({'api_urls':get_api_endpoints()})
            kwargs.update({'access_level':TEMPLATE_ACCESS_LEVEL})
            kwargs.update({'user_access':request.user.permissions.access_level})
            kwargs.update({'user_project':request.user.permissions.project})
            kwargs.update({'project':project})
            kwargs.update({'form':'False'})
            kwargs.update({'counter':counter})
            kwargs.update({'toolbar_title_code': 'CSVImporter_none'})
            kwargs.update({'deletable': 'False'})
        else:
            #If anything goes wrong in the process, return an error in the json HTTP Response
            SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), 'Trying to access another project.', request.META)
            return render(request, 'maqluengine/admin_warning.html', kwargs)
            
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):        
            return render(request, 'maqluengine/geojson_importer.html', kwargs)    
        else: ERROR_MESSAGE += "Error: You do not have permission to view this page"
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        kwargs.update({'ERROR_MESSAGE': ERROR_MESSAGE})
        return render(request, 'maqluengine/admin_error.html', kwargs)     
        
    #=====================================================================================#  
    #   ACCESS LEVEL :  4   TEMPLATE_ACCESS_LEVEL : 4    FORM_TYPE_IMPORTER()
    #=====================================================================================#  
    def form_type_importer(self, request, **kwargs):
        #************************#
        ACCESS_LEVEL = 4
        TEMPLATE_ACCESS_LEVEL = 4
        #************************#
        #-----------------------------------------------------------------------------------
        #-----------------------------------------------------------------------------------
        #   This view displays the base template for the CSV importer to create new form types
        #   --and populate them with forms based on rows in the CSV
        #   --Most of the logic is done in an API Endpoint, but the base template provides the necessary
        #   --tools in Jscript to perform all of this.
        #   The Importer works client-side to process the CSV file in JSON and when the user finishes the form,
        #   --it will upload the processed CSV data to the server and run the actual database import
        ERROR_MESSAGE = ""
        
        try:
            project = FormProject.objects.get(pk=kwargs['project_pk'])
        except:
            raise Http404("Project Does Not Exist!")       
            
        if project.pk == request.user.permissions.project.pk:
            counter = Counter()
            counter.reset()
            kwargs.update({'user': request.user,'has_permission': admin.site.has_permission(request)})
            kwargs.update({'api_urls':get_api_endpoints()})
            kwargs.update({'access_level':TEMPLATE_ACCESS_LEVEL})
            kwargs.update({'user_access':request.user.permissions.access_level})
            kwargs.update({'user_project':request.user.permissions.project})
            kwargs.update({'project':project})
            kwargs.update({'form':'False'})
            kwargs.update({'counter':counter})
            kwargs.update({'toolbar_title_code': 'CSVImporter_none'})
            kwargs.update({'deletable': 'False'})
        else:
            #If anything goes wrong in the process, return an error in the json HTTP Response
            SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), 'Trying to access another project.', request.META)
            return render(request, 'maqluengine/admin_warning.html', kwargs)
            
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):        
            return render(request, 'maqluengine/new_formtype_importer.html', kwargs)    
        else: ERROR_MESSAGE += "Error: You do not have permission to view this page"
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        kwargs.update({'ERROR_MESSAGE': ERROR_MESSAGE})
        return render(request, 'maqluengine/admin_error.html', kwargs)        
        
    #=====================================================================================#  
    #   ACCESS LEVEL :  4   TEMPLATE_ACCESS_LEVEL : 4    FORMTYPE_FORM_IMPORTER()
    #=====================================================================================#  
    def formtype_form_importer(self, request, **kwargs):
        #************************#
        ACCESS_LEVEL = 4
        TEMPLATE_ACCESS_LEVEL = 4
        #************************#
        #-----------------------------------------------------------------------------------
        #-----------------------------------------------------------------------------------
        #   This view displays the base template for the CSV importer to create new form types
        #   --and populate them with forms based on rows in the CSV
        #   --Most of the logic is done in an API Endpoint, but the base template provides the necessary
        #   --tools in Jscript to perform all of this.
        #   The Importer works client-side to process the CSV file in JSON and when the user finishes the form,
        #   --it will upload the processed CSV data to the server and run the actual database import
        ERROR_MESSAGE = ""
        
        try:
            project = FormProject.objects.get(pk=kwargs['project_pk'])
            formtype = FormType.objects.get(pk=kwargs['form_type_pk'])
        except:
            raise Http404("Project Does Not Exist!")       
            
        if project.pk == request.user.permissions.project.pk:
            counter = Counter()
            counter.reset()
            kwargs.update({'user': request.user,'has_permission': admin.site.has_permission(request)})
            kwargs.update({'api_urls':get_api_endpoints()})
            kwargs.update({'access_level':TEMPLATE_ACCESS_LEVEL})
            kwargs.update({'user_access':request.user.permissions.access_level})
            kwargs.update({'user_project':request.user.permissions.project})
            kwargs.update({'project':project})
            kwargs.update({'form':'False'})
            kwargs.update({'formtype':formtype}) 
            kwargs.update({'toolbar_title_code': 'CSVImporter_none'})
            kwargs.update({'deletable': 'False'})
        else:
            #If anything goes wrong in the process, return an error in the json HTTP Response
            SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), 'Trying to access another project.', request.META)
            return render(request, 'maqluengine/admin_warning.html', kwargs)
            
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):        
            return render(request, 'maqluengine/formtype_form_importer.html', kwargs)    
        else: ERROR_MESSAGE += "Error: You do not have permission to view this page"
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        kwargs.update({'ERROR_MESSAGE': ERROR_MESSAGE})
        return render(request, 'maqluengine/admin_error.html', kwargs)        
                  
    #=====================================================================================#  
    #   ACCESS LEVEL :  4   TEMPLATE_ACCESS_LEVEL : 4    RTYPE_TYPE_IMPORTER()
    #=====================================================================================#  
    def rtype_importer(self, request, **kwargs):
        #************************#
        ACCESS_LEVEL = 4
        TEMPLATE_ACCESS_LEVEL = 4
        #************************#
        
        #-----------------------------------------------------------------------------------
        #-----------------------------------------------------------------------------------
        #
        #
        
        ERROR_MESSAGE = ""
        
        try:
            project = FormProject.objects.get(pk=kwargs['project_pk'])
            formtype = FormType.objects.get(pk=kwargs['form_type_pk'])
        except:
            raise Http404("Project Does Not Exist!")       
            
        if project.pk == request.user.permissions.project.pk:
            counter = Counter()
            counter.reset()
            kwargs.update({'user': request.user,'has_permission': admin.site.has_permission(request)})
            kwargs.update({'api_urls':get_api_endpoints()})
            kwargs.update({'access_level':TEMPLATE_ACCESS_LEVEL})
            kwargs.update({'user_access':request.user.permissions.access_level})
            kwargs.update({'user_project':request.user.permissions.project})
            kwargs.update({'project':project})
            kwargs.update({'form':'False'})
            kwargs.update({'formtype':formtype}) 
            kwargs.update({'toolbar_title_code': 'FormType_' + kwargs['form_type_pk']})
            kwargs.update({'deletable': 'False'})
        else:
            #If anything goes wrong in the process, return an error in the json HTTP Response
            SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), 'Trying to access another project.', request.META)
            return render(request, 'maqluengine/admin_warning.html', kwargs)
            
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):        
            return render(request, 'maqluengine/new_rtype_importer.html', kwargs)    
        else: ERROR_MESSAGE += "Error: You do not have permission to view this page"
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        kwargs.update({'ERROR_MESSAGE': ERROR_MESSAGE})
        return render(request, 'maqluengine/admin_error.html', kwargs)                

        
    #=====================================================================================#  
    #   ACCESS LEVEL :  1   TEMPLATE_ACCESS_LEVEL : 5    PROJECT_HOME()
    #=====================================================================================#          
    def project_home(self, request, **kwargs):
        print(admin.site.has_permission(request), file=sys.stderr)
        print(request.user, file=sys.stderr)
        logger.warning(request)
        logger.warning(kwargs)
        
        #************************#
        ACCESS_LEVEL = 1
        TEMPLATE_ACCESS_LEVEL = 5
        #************************#
        #-----------------------------------------------------------------------------------
        #   This view delivers the project overview of users/stats etc. Only a level 5 admin can edit
        #   --the info on this screen. Although the access level is set to 5 on this view, we allow all
        #   --project users to see this page. Access to modifications are prohibited in the template
        #   --using this access_level passed to the **kwargs however, e.g. save buttons/delete buttons/delete
        #   --will not be generated if someone isn't level 5
     
        ERROR_MESSAGE = ""
                
        try:
            project = FormProject.objects.get(pk=kwargs['project_pk'])
        except:
            raise Http404("Project Does Not Exist!")       
        
        if request.user.permissions.project.pk == project.pk:
            kwargs.update({'user': request.user,'has_permission': admin.site.has_permission(request)})
            kwargs.update({'api_urls':get_api_endpoints()})
            kwargs.update({'access_level':TEMPLATE_ACCESS_LEVEL})
            kwargs.update({'user_access':request.user.permissions.access_level})
            kwargs.update({'user_project':request.user.permissions.project})     
            kwargs.update({'project':project}) 
            kwargs.update({'toolbar_title_code': 'Project_' + kwargs['project_pk']})
            kwargs.update({'form':'False'})
            kwargs.update({'deletable': 'False'})
            kwargs['webpages'] = project.webpage_set.all()
        else: 
            #If anything goes wrong in the process, return an error in the json HTTP Response
            SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), 'Trying to access another project.', request.META)
            return render(request, 'maqluengine/admin_warning.html', kwargs)
            
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):        
            return render(request, 'maqluengine/project_control_panel.html', kwargs)    
        else: ERROR_MESSAGE += "Error: You do not have permission to view this page"
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        kwargs.update({'ERROR_MESSAGE': ERROR_MESSAGE})
        return render(request, 'maqluengine/admin_error.html', kwargs)     
        
    #=====================================================================================#
    #   ACCESS LEVEL :  3    TEMPLATE_ACCESS_LEVEL : 3   EDIT_FORM_TYPE() *RECYCLING
    #=====================================================================================#            
    def edit_form_type(self, request, **kwargs):
        #************************#
        ACCESS_LEVEL = 3
        TEMPLATE_ACCESS_LEVEL = 3
        #************************#
        #------------------------------------------------------------------------------------------------------
        #   This view just displays the form type editor page. Only a level 3 access can see and use this page
        #   --It's not necessary for any lower access to view this page
        
        ERROR_MESSAGE = ""
        try:
            project = FormProject.objects.get(pk=kwargs['project_pk'])
            formtype = FormType.objects.get(pk=kwargs['form_type_pk'])
        except:
            raise Http404("Project Does Not Exist!")     

        #*** RECYCLING BIN *** Return a 404 Error if the requsted model instance is flagged for deletion (in the recycling bin)    
        if formtype.flagged_for_deletion == True: raise Http404("This Page Does Not Exist!")
            
        #Make sure the user is trying to access their project and not another project
        #If they are trying to access another project--warn them their action has been logged
        #after redirecting them to a warning page
        if project.pk == request.user.permissions.project.pk and formtype.project.pk == request.user.permissions.project.pk:
            counter = Counter()
            counter.reset()
            kwargs.update({'user': request.user,'has_permission': admin.site.has_permission(request)})
            kwargs.update({'api_urls':get_api_endpoints()})
            kwargs.update({'access_level':TEMPLATE_ACCESS_LEVEL})
            kwargs.update({'user_access':request.user.permissions.access_level})
            kwargs.update({'user_project':request.user.permissions.project})     
            kwargs.update({'counter':counter})
            kwargs.update({'project':project}) 
            kwargs.update({'formtype':formtype}) 
            kwargs.update({'form':'False'})
            kwargs.update({'toolbar_title_code': 'FormType_' + kwargs['form_type_pk']})
            kwargs.update({'deletable': 'True'})
        else:
            #If anything goes wrong in the process, return an error in the json HTTP Response
            SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), 'Trying to access another project.', request.META)
            return render(request, 'maqluengine/admin_warning.html', kwargs)
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):        
            return render(request, 'maqluengine/edit_form_type.html', kwargs)    
        else: ERROR_MESSAGE += "Error: You do not have permission to view this page"
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        kwargs.update({'ERROR_MESSAGE': ERROR_MESSAGE})
        return render(request, 'maqluengine/admin_error.html', kwargs) 

        
    #=====================================================================================#
    #   ACCESS LEVEL :  4    TEMPLATE_ACCESS_LEVEL : 4   NEW_FORM_TYPE()
    #=====================================================================================#            
    def new_form_type(self, request, **kwargs):
        #************************#
        ACCESS_LEVEL = 4
        TEMPLATE_ACCESS_LEVEL = 4
        #************************#
        #-----------------------------------------------------------------------------------------------
        #   This view show the new form type creator template. It allows users to create new form types
        #   --for their project. Because it is creating a new form type it is limited only to those with
        #   --level 4 access. 
        
        ERROR_MESSAGE = ""
        try:
            project = FormProject.objects.get(pk=kwargs['project_pk'])
        except:
            raise Http404("Project Does Not Exist!")       

        #Make sure the user is trying to access their project and not another project
        #If they are trying to access another project--warn them their action has been logged
        #after redirecting them to a warning page
        if project.pk == request.user.permissions.project.pk:       
            kwargs.update({'user': request.user,'has_permission': admin.site.has_permission(request)})
            kwargs.update({'api_urls':get_api_endpoints()})
            kwargs.update({'access_level':TEMPLATE_ACCESS_LEVEL})
            kwargs.update({'user_access':request.user.permissions.access_level})
            kwargs.update({'user_project':request.user.permissions.project})  
            kwargs.update({'toolbar_title_code': 'NewFormType_none'})
            kwargs.update({'project':project})
            kwargs.update({'form':'False'})
            kwargs.update({'deletable': 'False'})
        else:
            #If anything goes wrong in the process, return an error in the json HTTP Response
            SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), 'Trying to access another project.', request.META)
            return render(request, 'maqluengine/admin_warning.html', kwargs)

        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):        
            return render(request, 'maqluengine/new_form_type.html', kwargs)    
        else: ERROR_MESSAGE += "Error: You do not have permission to view this page"        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        kwargs.update({'ERROR_MESSAGE': ERROR_MESSAGE})
        return render(request, 'maqluengine/admin_error.html', kwargs) 

    #=====================================================================================#
    #   ACCESS LEVEL :  1    TEMPLATE_ACCESS_LEVEL : 2   EDIT_FORM() *RECYCLING
    #=====================================================================================#            
    def edit_form(self, request, **kwargs):
        #************************#
        ACCESS_LEVEL = 1
        TEMPLATE_ACCESS_LEVEL = 2
        #************************#
        #-----------------------------------------------------------------------------------------------
        #   This view shows the page to edit an existing form. Any project user can view this, but only level 2 
        #   --and above can use its functionality to submit data
        
        ERROR_MESSAGE = ""
        try:
            form = Form.objects.get(pk=kwargs['form_pk'])
            form_type = FormType.objects.get(pk=kwargs['form_type_pk'])
            project = FormProject.objects.get(pk=kwargs['project_pk'])
        except:
            raise Http404("Form does not exist")
                #Do something with request here
          
        #*** RECYCLING BIN *** Return a 404 Error if the requsted model instance is flagged for deletion (in the recycling bin)
        if form.flagged_for_deletion == True: raise Http404("This Page Does Not Exist!")
        
        #Make sure the user is trying to access their project and not another project
        #If they are trying to access another project--warn them their action has been logged
        #after redirecting them to a warning page
        if project.pk == request.user.permissions.project.pk and form.project.pk == request.user.permissions.project.pk and form.form_type.pk == form_type.pk:          
            counter = Counter()
            counter.reset()
            
            #Temp function to make displaying the page much faster--remove the database query hits from the actual .html file
            #Need a list of this form's rtypes and a list of this forms rtype values
            logger.info( "TIMER FOR FORM EDIT A")
           
            #*** RECYCLING BIN ***  We need to make sure all the RTYPES and RVALS(by their RTYPE) are filtered out by their deletion flags
            frat_list = form_type.formrecordattributetype_set.all().filter(flagged_for_deletion=False)
            frav_list = form.formrecordattributevalue_set.all().filter(record_attribute_type__flagged_for_deletion=False)
            
            frrt_list = form_type.ref_to_parent_formtype.all().filter(flagged_for_deletion=False)
            frrv_list = form.ref_to_parent_form.all().filter(record_reference_type__flagged_for_deletion=False)
            kwargs.update({'user': request.user,'has_permission': admin.site.has_permission(request)})
            kwargs.update({'api_urls':get_api_endpoints()})
            kwargs.update({'api_urls':get_api_endpoints()})
            kwargs.update({'frat_list':frat_list})
            kwargs.update({'frav_list':frav_list})
            kwargs.update({'frrt_list':frrt_list})
            kwargs.update({'frrv_list':frrv_list})
            logger.info( "TIMER FOR FORM EDIT A")
            kwargs.update({'access_level':TEMPLATE_ACCESS_LEVEL})
            kwargs.update({'user_access':request.user.permissions.access_level})
            kwargs.update({'user_project':request.user.permissions.project})  
            kwargs.update({'formtype':form_type})
            kwargs.update({'form':form})
            kwargs.update({'project':project})
            kwargs.update({'counter':counter})
            kwargs.update({'toolbar_title_code': 'Form_' + kwargs['form_pk']})
            kwargs.update({'deletable': 'True'})
        else:
            SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), 'Trying to access another project.', request.META)
            return render(request, 'maqluengine/admin_warning.html', kwargs)

        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):        
            return render(request, 'maqluengine/edit_form.html', kwargs)    
        else: ERROR_MESSAGE += "Error: You do not have permission to view this page"        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        kwargs.update({'ERROR_MESSAGE': ERROR_MESSAGE})
        return render(request, 'maqluengine/admin_error.html', kwargs) 

        
    #=====================================================================================#
    #   ACCESS LEVEL :  2    TEMPLATE_ACCESS_LEVEL : 2   NEW_FORM() *RECYCLING
    #=====================================================================================#        
    def new_form(self, request, **kwargs):
        #************************#
        ACCESS_LEVEL = 2
        TEMPLATE_ACCESS_LEVEL = 2
        #************************#
        #-----------------------------------------------------------------------------------------------
        #   This view shows the page to edit an existing form. Any project user can view this, but only level 2 
        #   --and above can use its functionality to submit data
        
        ERROR_MESSAGE = ""
        
        try:
            form_type = FormType.objects.get(pk=kwargs['form_type_pk'])
            project = FormProject.objects.get(pk=kwargs['project_pk'])
        except FormType.DoesNotExist:
            raise Http404("Form Type does not exist")

        #*** RECYCLING BIN *** Return a 404 Error if the requsted model instance is flagged for deletion (in the recycling bin)
        #   --we still need to check the formtype to prevent URL hacking
        if form_type.flagged_for_deletion == True: raise Http404("This Page Does Not Exist!")
            
        #Make sure the user is trying to access their project and not another project
        #If they are trying to access another project--warn them their action has been logged
        #after redirecting them to a warning page
        if project.pk == request.user.permissions.project.pk and form_type.project.pk == request.user.permissions.project.pk: 
            kwargs.update({'user': request.user,'has_permission': admin.site.has_permission(request)})
            kwargs.update({'api_urls':get_api_endpoints()})
            kwargs.update({'access_level':TEMPLATE_ACCESS_LEVEL})
            kwargs.update({'user_access':request.user.permissions.access_level})
            kwargs.update({'user_project':request.user.permissions.project})                         
            kwargs.update({'form':'False'})
            kwargs.update({'formtype':form_type})
            kwargs.update({'project':project})
            kwargs.update({'toolbar_title_code': 'NewForm_' + kwargs['form_type_pk']})
            kwargs.update({'deletable': 'False'})
        else:
            SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), 'Trying to access another project.', request.META)
            return render(request, 'maqluengine/admin_warning.html', kwargs)

        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):        
            return render(request, 'maqluengine/new_form.html', kwargs)    
        else: ERROR_MESSAGE += "Error: You do not have permission to view this page"        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        kwargs.update({'ERROR_MESSAGE': ERROR_MESSAGE})
        return render(request, 'maqluengine/admin_error.html', kwargs) 

    #=====================================================================================#
    #   ACCESS LEVEL :  2    TEMPLATE_ACCESS_LEVEL : 2  EDIT_FORM_TYPE_TEMPLATE()  *RECYCLING
    #=====================================================================================#        
    def edit_form_type_template(self, request, **kwargs):
        #************************#
        ACCESS_LEVEL = 2
        TEMPLATE_ACCESS_LEVEL = 2
        #************************#
        #-----------------------------------------------------------------------------------------------
        #   This is a test view for templating views -- TODO!!!!!!!!!!!!!!!!!!!!!!!!!!!
        
        ERROR_MESSAGE = ""
        
        try:
            form_type = FormType.objects.get(pk=kwargs['form_type_pk'])
            project = FormProject.objects.get(pk=kwargs['project_pk'])
        except FormType.DoesNotExist:
            raise Http404("Form Type does not exist")

        #*** RECYCLING BIN *** Return a 404 Error if the requsted model instance is flagged for deletion (in the recycling bin)
        if form_type.flagged_for_deletion == True: raise Http404("This Page Does Not Exist!")
        
        #Make sure the user is trying to access their project and not another project
        #If they are trying to access another project--warn them their action has been logged
        #after redirecting them to a warning page
        if project.pk == request.user.permissions.project.pk and form_type.project.pk == request.user.permissions.project.pk:
            kwargs.update({'user': request.user,'has_permission': admin.site.has_permission(request)})
            kwargs.update({'api_urls':get_api_endpoints()})
            kwargs.update({'access_level':TEMPLATE_ACCESS_LEVEL})
            kwargs.update({'user_access':request.user.permissions.access_level})
            kwargs.update({'user_project':request.user.permissions.project})                         
            kwargs.update({'form':'False'})
            kwargs.update({'formtype':form_type})
            kwargs.update({'project':project})
            kwargs.update({'toolbar_title_code': 'NewForm_' + kwargs['form_type_pk']})
            kwargs.update({'deletable': 'False'})
        else:
            SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), 'Trying to access another project.', request.META)
            return render(request, 'maqluengine/admin_warning.html', kwargs)

        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):        
            return render(request,'maqluengine/edit_formtype_template.html', kwargs)   
        else: ERROR_MESSAGE += "Error: You do not have permission to view this page"        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        kwargs.update({'ERROR_MESSAGE': ERROR_MESSAGE})
        return render(request, 'maqluengine/admin_error.html', kwargs) 

    #=====================================================================================#
    #   ACCESS LEVEL :  5    TEMPLATE_ACCESS_LEVEL : 5  RECYCLING_BIN()  
    #=====================================================================================#        
    def recycling_bin(self, request, **kwargs):
        #************************#
        ACCESS_LEVEL = 5
        TEMPLATE_ACCESS_LEVEL = 5
        #************************#
        #-----------------------------------------------------------------------------------------------
        #   This redirects the Admin to the recycling bin page
        
        ERROR_MESSAGE = ""
        
        try:
            project = FormProject.objects.get(pk=kwargs['project_pk'])
        except FormType.DoesNotExist:
            raise Http404("Project does not exist")

        #Make sure the user is trying to access their project and not another project
        #If they are trying to access another project--warn them their action has been logged
        #after redirecting them to a warning page
        if project.pk == request.user.permissions.project.pk:
            kwargs.update({'user': request.user,'has_permission': admin.site.has_permission(request)})        
            kwargs.update({'api_urls':get_api_endpoints()})
            kwargs.update({'access_level':TEMPLATE_ACCESS_LEVEL})
            kwargs.update({'user_access':request.user.permissions.access_level})
            kwargs.update({'user_project':request.user.permissions.project})     
            kwargs.update({'project':project}) 
            kwargs.update({'toolbar_title_code': 'Project_' + kwargs['project_pk']})
            kwargs.update({'form':'False'})
            kwargs.update({'deletable': 'False'})   
        else:
            SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), 'Trying to access another project.', request.META)
            return render(request, 'maqluengine/admin_warning.html', kwargs)

        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):        
            return render(request, 'maqluengine/recycling_bin.html', kwargs)    
        else: ERROR_MESSAGE += "Error: You do not have permission to view this page"        
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        kwargs.update({'ERROR_MESSAGE': ERROR_MESSAGE})
        return render(request, 'maqluengine/admin_error.html', kwargs) 

        
    #=====================================================================================#
    #   ACCESS LEVEL :  1    TEMPLATE_ACCESS_LEVEL : 3   GEOSPATIAL_ENGINE() 
    #=====================================================================================#       
    def geospatial_engine(self, request, **kwargs):
        #************************#
        ACCESS_LEVEL = 1
        TEMPLATE_ACCESS_LEVEL = 3
        #************************#
        #-----------------------------------------------------------------------------------
        #   This view displays the view form type template--or essentially the query engine
        #   --attached to it. It allows the user to look at forms and their details in bulk
        #   --according to their form type, and also allows those forms to be queried by
        #   --the query engine where graphs/charts etc. are produced. All this view needs to
        #   --do is pass a few variables to the template, and display the template. The AJAX
        #   --and template will handle all permissions etc. from there
        ERROR_MESSAGE = ""

        #Setup our variable's we'll pass to the template if allowed
        try:
            project = FormProject.objects.get(pk=kwargs['project_pk'])
        except:
            raise Http404("This Page Does Not Exist!")    
            
        
        #Make sure the user is trying to access their project and not another project
        #If they are trying to access another project--warn them their action has been logged
        #after redirecting them to a warning page
        if project.pk == request.user.permissions.project.pk:
            counter = Counter()
            counter.reset()
            kwargs.update({'user': request.user,'has_permission': admin.site.has_permission(request)})
            kwargs.update({'api_urls':get_api_endpoints()})
            kwargs.update({'access_level':TEMPLATE_ACCESS_LEVEL})
            kwargs.update({'user_access':request.user.permissions.access_level})
            kwargs.update({'user_project':request.user.permissions.project})
            kwargs.update({'counter':counter}) 
            kwargs.update({'project':project}) 
            kwargs.update({'form':'False'})
            kwargs.update({'toolbar_title_code': 'Project_' + kwargs['project_pk']})
            kwargs.update({'deletable': 'False'})
            logger.info( request)
        else:
            #If anything goes wrong in the process, return an error in the json HTTP Response
            SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), 'Trying to access another project.', request.META)
            return render(request, 'maqluengine/admin_warning.html', kwargs)
        
        #Check our user's session and access level
        if SECURITY_check_user_permissions(ACCESS_LEVEL, request.user.permissions.access_level):        
            return render(request,'maqluengine/geospatial_engine.html', kwargs)    
        else: ERROR_MESSAGE += "Error: You do not have permission to view this page"
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        kwargs.update({'ERROR_MESSAGE': ERROR_MESSAGE})
        return render(request, 'maqluengine/admin_error.html', kwargs)            
         

    ##==========================================================================================================================    
    #  OVERRIDDEN ADMIN DJANGO VIEWS   *****************************************************************************************
    ##==========================================================================================================================            
    def index(self, request, **kwargs):
        #This function is important for security reasons: It essentially ovverides all normal admin index operations
        #--and redirects any logged in user to their respective project's control panel
        #   --The remainder of the built-in admin views will need to be overidden--much like this index
        #   --to make sure that only the custom admin can be used. The reason is that all users have to be "is_staff"
        #   --giving them access to change things. If they find a way into the Django built-in admin, they will be able to affect
        #   --the database in potentially nefarious ways
        #
        #Additionally if we are a MASTER admin, we redirect to the TARA admin console page
        if (request.user.permissions.master_admin):
        
            #Get a list of all logged in user PKs by looking at non-expired sessions that exist NOW
            sessions = Session.objects.filter(expire_date__gte=timezone.now())
            pk_list = []
            # Build a list of user ids from that query
            for session in sessions:
                data = session.get_decoded()
                pk_list.append(data.get('_auth_user_id', None))
            
            projects = FormProject.objects.all()
            users = User.objects.order_by('-permissions__master_admin', 'permissions__project__name', 'username')
            security_messages = SecurityMessage.objects.order_by('-date_created')
            blogposts = BlogPost.objects.filter(project=None).order_by('-date_created')
            kwargs.update({'user': request.user,'has_permission': admin.site.has_permission(request)})
            kwargs.update({'pk_list':pk_list})
            kwargs.update({'api_urls':get_api_endpoints()})
            kwargs.update({'user_access':request.user.permissions.access_level})
            kwargs.update({'user_project':request.user.permissions.project})     
            kwargs.update({'user_list':users})
            kwargs.update({'project_list':projects})
            kwargs.update({'message_list':security_messages})
            kwargs.update({'blogpost_list':blogposts})
            
            return render (request, 'maqluengine/tara_admin_console.html',kwargs)
        else:
            return redirect('maqlu_admin:project_home',project_pk=request.user.permissions.project.pk)

    
    def master_admin_project_redirect(self, request, **kwargs):   
        # This view let's a master admin switch their project ownership to emulate being a level 5 access member of the project
        #   --It expects a project ID in the provided kwargs to the view
        #   --It sets the project of the master admin user to the provided project ID, saves, and then redirects the master-admin to that
        #   --project's admin page
        if (request.user.permissions.master_admin):
            #If an invalid project ID is given then redirect to the main admin page
            try:
                new_project = FormProject.objects.get(pk=kwargs['project_pk'])
                request.user.permissions.project = new_project
                request.user.save()
                return redirect('maqlu_admin:project_home',project_pk=request.user.permissions.project.pk)
            except:
                ERROR_MESSAGE = "Invalid Project ID"
                SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
                kwargs.update({'ERROR_MESSAGE': ERROR_MESSAGE})
                return render(request, 'maqluengine/admin_error.html', kwargs)  
            
        else:
            #Set a security notification because the only people who should get to this view without hacking the url addresses are master_admins
            ERROR_MESSAGE = "Invalid Project ID"
            SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
            kwargs.update({'ERROR_MESSAGE': ERROR_MESSAGE})
            return render(request, 'maqluengine/admin_error.html', kwargs)   


            
    ##==========================================================================================================================    
    #  CUSTOM ADMIN URL PATTERNS   *********************************************************************************************
    ##==========================================================================================================================    
    def get_urls(self):
        #============================================================
        #   HELP WITH URL PATTERNS
        #   --I've found this to be an incredibly frustrating process, but finally discovered the secrets to reversing
        #   --urls by 'name' in these patterns below. Thank God! There are 2 ways to handle this--through a Redirect() in a view
        #   --or through a Reverse() --both link to the same regex expression in the url patterns, but take in args/kwargs differently
        #   --This difference of arguments is what kept me frustrated for several hours--it's not well documented this small issue.
        #   --Here are two examples to show the differerence:
        #       :redirect('maqlu_admin:project_home',project_pk=request.user.permissions.project.pk)
        #       :reverse('maqlu_admin:project_home',kwargs={'project_pk': request.user.permissions.project.pk})
        #   --Also notice that these custom AdminSite views have their own namespace attached to the custom AdminSite
        #   --in this case, it is named "maqlu_admin" in the "MyAdminSite" Class above. Views can be referenced as 'maqlu_admin:<view_name>'
        #
        #   --FOR TEMPLATES:   use this method   {% url 'maqlu_admin:view-name' arg1=v1 arg2=v2 %}
        
        from django.urls import re_path
        urls = super(MyAdminSite, self).get_urls()
        my_urls = [
            #Base Admin Site
            re_path(r'^$', admin.site.admin_view(self.index), name='index'),
            
            #All Admin API Endpoints 

            # MASTER ADMIN Endpoints
            re_path(r'^create_project/$', admin.site.admin_view(self.create_project), name='create_project'),
            re_path(r'^delete_project/$', admin.site.admin_view(self.delete_project), name='delete_project'),
            re_path(r'^reset_user_password/$', admin.site.admin_view(self.reset_user_password), name='reset_user_password'),
            re_path(r'^create_project_admin/$', admin.site.admin_view(self.create_project_admin), name='create_project_admin'),
            re_path(r'^delete_user/$', admin.site.admin_view(self.delete_user), name='delete_user'),
            re_path(r'^edit_security_message/$', admin.site.admin_view(self.edit_security_message), name='edit_security_message'),
            re_path(r'^create_edit_blogpost/$', admin.site.admin_view(self.create_edit_blogpost), name='create_edit_blogpost'),
            re_path(r'^get_admin_blog_post/$', admin.site.admin_view(self.get_admin_blog_post), name='get_admin_blog_post'),
            re_path(r'^delete_admin_post/$', admin.site.admin_view(self.delete_admin_post), name='delete_admin_post'),
            re_path(r'^master_admin_project_redirect/(?P<project_pk>[0-9]+)/$', admin.site.admin_view(self.master_admin_project_redirect), name='master_admin_project_redirect'),
            
            # All Endpoints that return model objects
            re_path(r'^get_user_list/$', admin.site.admin_view(self.get_user_list), name='get_user_list'),
            re_path(r'^get_previous_next_forms/$', admin.site.admin_view(self.get_previous_next_forms), name='get_previous_next_forms'),
            re_path(r'^get_projects/$', admin.site.admin_view(self.get_projects), name='get_projects'),
            re_path(r'^get_formtypes/$', admin.site.admin_view(self.get_formtypes), name='get_formtypes'),
            re_path(r'^get_rtypes/$', admin.site.admin_view(self.get_rtypes), name='get_rtypes'),
            re_path(r'^get_deep_rtypes/$', admin.site.admin_view(self.get_deep_rtypes), name='get_deep_rtypes'),
            re_path(r'^get_formtype_form_list/$', admin.site.admin_view(self.get_formtype_form_list), name='get_formtype_form_list'),
            re_path(r'^get_geospatial_formtypes/$', admin.site.admin_view(self.get_geospatial_formtypes), name='get_geospatial_formtypes'),
            re_path(r'^get_form_rtypes/$', admin.site.admin_view(self.get_form_rtypes), name='get_form_rtypes'),
            re_path(r'^get_formtype_geospatial_layers/$', admin.site.admin_view(self.get_formtype_geospatial_layers), name='get_formtype_geospatial_layers'),
            re_path(r'^get_form_search_list/$', admin.site.admin_view(self.get_form_search_list), name='get_form_search_list'),
            re_path(r'^get_all_unique_rtype_rvals/$', admin.site.admin_view(self.get_all_unique_rtype_rvals), name='get_all_unique_rtype_rvals'),                
            re_path(r'^get_geo_category_matches/$', admin.site.admin_view(self.get_geo_category_matches), name='get_geo_category_matches'),
            re_path(r'^get_geo_quantity_frat_counter_auto/$', admin.site.admin_view(self.get_geo_quantity_frat_counter_auto), name='get_geo_quantity_frat_counter_auto'),
            re_path(r'^get_geo_numeric_rtypes/$', admin.site.admin_view(self.get_geo_numeric_rtypes), name='get_geo_numeric_rtypes'),
            re_path(r'^get_geo_graduated_applied_classes/$', admin.site.admin_view(self.get_geo_graduated_applied_classes), name='get_geo_graduated_applied_classes'),
            re_path(r'^get_geo_rules_classes/$', admin.site.admin_view(self.get_geo_rules_classes), name='get_geo_rules_classes'),
            # All Endpoints that run tools non-database-modification tools
            
            re_path(r'^run_master_query_engine/$', admin.site.admin_view(self.run_master_query_engine), name='run_master_query_engine'),

            # Endpoints for Editing Model objects
            re_path(r'^save_user_query/$', admin.site.admin_view(self.save_user_query), name='save_user_query'),            
            re_path(r'^save_project_changes/$', admin.site.admin_view(self.save_project_changes), name='save_project_changes'),
            re_path(r'^save_form_type_changes/$', admin.site.admin_view(self.save_form_type_changes), name='save_form_type_changes'),
            re_path(r'^save_form_changes/$', admin.site.admin_view(self.save_form_changes), name='save_form_changes'),            
            re_path(r'^modify_project_user/$', admin.site.admin_view(self.modify_project_user), name='modify_project_user'),
            re_path(r'^bulk_edit_formtype/$', admin.site.admin_view(self.bulk_edit_formtype), name='bulk_edit_formtype'),
            re_path(r'^edit_menugroup/$', admin.site.admin_view(self.edit_menugroup), name='edit_menugroup'),
            
            # Endpoints for Creating new model objects 
            re_path(r'^create_new_form/$', admin.site.admin_view(self.create_new_form), name='create_new_form'),
            re_path(r'^create_new_form_type/$', admin.site.admin_view(self.create_new_form_type), name='create_new_form_type'),
            re_path(r'^create_new_form_type_template/$', admin.site.admin_view(self.create_new_form_type_template), name='create_new_form_type_template'),
            re_path(r'^create_new_webpage/$', admin.site.admin_view(self.create_new_webpage), name='create_new_webpage'),
            
            # Endpoints for random tools
            re_path(r'^navigate_query_pagination/$', admin.site.admin_view(self.navigate_query_pagination), name='navigate_query_pagination'),
            re_path(r'^navigate_master_query_pagination/$', admin.site.admin_view(self.navigate_master_query_pagination), name='navigate_master_query_pagination'),
            re_path(r'^check_progress/$', admin.site.admin_view(self.check_progress), name='check_progress'),
            re_path(r'^check_progress_query/$', admin.site.admin_view(self.check_progress_query), name='check_progress_query'),
            re_path(r'^username_taken/$', admin.site.admin_view(self.username_taken), name='username_taken'),
            re_path(r'^debug_tool/$', admin.site.admin_view(self.debug_tool), name='debug_tool'),
            re_path(r'^debug_toolA/$', admin.site.admin_view(self.debug_toolA), name='debug_toolA'),
            
            # Endpoints for the Recycling Bin
            re_path(r'^delete_user_profile_query/$', admin.site.admin_view(self.delete_user_profile_query), name='delete_user_profile_query'),
            re_path(r'^delete_form_type/$', admin.site.admin_view(self.delete_form_type), name='delete_form_type'),
            re_path(r'^delete_form/$', admin.site.admin_view(self.delete_form), name='delete_form'),
            re_path(r'^delete_frat/$', admin.site.admin_view(self.delete_frat), name='delete_frat'),
            re_path(r'^delete_frrt/$', admin.site.admin_view(self.delete_frrt), name='delete_frrt'),
            re_path(r'^delete_form_type_group/$', admin.site.admin_view(self.delete_form_type_group), name='delete_form_type_group'),
            re_path(r'^restore_form_type/$', admin.site.admin_view(self.restore_form_type), name='restore_form_type'),
            re_path(r'^restore_form/$', admin.site.admin_view(self.restore_form), name='restore_form'),
            re_path(r'^restore_frat/$', admin.site.admin_view(self.restore_frat), name='restore_frat'),
            re_path(r'^restore_frrt/$', admin.site.admin_view(self.restore_frrt), name='restore_frrt'),
            re_path(r'^recycle_form_type/$', admin.site.admin_view(self.recycle_form_type), name='recycle_form_type'),
            re_path(r'^recycle_form/$', admin.site.admin_view(self.recycle_form), name='recycle_form'),
            re_path(r'^recycle_frat/$', admin.site.admin_view(self.recycle_frat), name='recycle_frat'),
            re_path(r'^recycle_frrt/$', admin.site.admin_view(self.recycle_frrt), name='recycle_frrt'),
            re_path(r'^recycle_webpage/$', admin.site.admin_view(self.recycle_webpage), name='recycle_webpage'),
            re_path(r'^load_recycling_bin/$', admin.site.admin_view(self.load_recycling_bin), name='load_recycling_bin'),

            #Endpoints for Importing and Exporting data into TARA
            re_path(r'^run_form_type_form_importer/$', admin.site.admin_view(self.run_form_type_form_importer), name='run_form_type_form_importer'),
            re_path(r'^run_form_type_importer/$', admin.site.admin_view(self.run_form_type_importer), name='run_form_type_importer'),
            re_path(r'^run_new_rtype_importer/$', admin.site.admin_view(self.run_new_rtype_importer), name='run_new_rtype_importer'),
            re_path(r'^run_geojson_importer/$', admin.site.admin_view(self.run_geojson_importer), name='run_geojson_importer'),            
            re_path(r'^export_formtype/$', admin.site.admin_view(self.export_formtype), name='export_formtype'),
            re_path(r'^export_project/$', admin.site.admin_view(self.export_project), name='export_project'),

            
            #All Admin Template Views
            re_path(r'^project/(?P<project_pk>[0-9]+)/$', self.admin_view(self.project_home), name='project_home'),
            re_path(r'^project/(?P<project_pk>[0-9]+)/recycling_bin/$', self.admin_view(self.recycling_bin), name='recycling_bin'),
            re_path(r'^project/(?P<project_pk>[0-9]+)/formtype_importer/$', admin.site.admin_view(self.form_type_importer), name='formtype_importer'),
            re_path(r'^project/(?P<project_pk>[0-9]+)/geojson_importer/$', admin.site.admin_view(self.geojson_importer), name='geojson_importer'),
            re_path(r'^project/(?P<project_pk>[0-9]+)/geospatial_engine/$', admin.site.admin_view(self.geospatial_engine), name='geospatial_engine'),
            re_path(r'^project/(?P<project_pk>[0-9]+)/formtype/(?P<form_type_pk>[0-9]+)/rtype_importer/$', admin.site.admin_view(self.rtype_importer), name='rtype_importer'),
            re_path(r'^project/(?P<project_pk>[0-9]+)/formtype/(?P<form_type_pk>[0-9]+)/form_importer/$', admin.site.admin_view(self.formtype_form_importer), name='formtype_form_importer'),
            re_path(r'^project/(?P<project_pk>[0-9]+)/formtype_editor/(?P<form_type_pk>[0-9]+)/$', admin.site.admin_view(self.edit_form_type), name='edit_form_type'),
            re_path(r'^project/(?P<project_pk>[0-9]+)/formtype/(?P<form_type_pk>[0-9]+)/$', admin.site.admin_view(self.view_form_type), name='view_form_type'),
            re_path(r'^project/(?P<project_pk>[0-9]+)/formtype_query_engine/(?P<form_type_pk>[0-9]+)/$', admin.site.admin_view(self.query_form_type), name='query_form_type'),
            re_path(r'^project/(?P<project_pk>[0-9]+)/master_query_engine/$', admin.site.admin_view(self.master_query_engine), name='master_query_engine'),
            re_path(r'^project/(?P<project_pk>[0-9]+)/formtype_generator/$', admin.site.admin_view(self.new_form_type), name='new_form_type'),
            re_path(r'^project/(?P<project_pk>[0-9]+)/formtype/(?P<form_type_pk>[0-9]+)/formtype_template_generator/$', admin.site.admin_view(self.edit_form_type_template), name='edit_form_type_template'),
            re_path(r'^project/(?P<project_pk>[0-9]+)/formtype/(?P<form_type_pk>[0-9]+)/form_generator/$', admin.site.admin_view(self.new_form), name='new_form'),
            re_path(r'^project/(?P<project_pk>[0-9]+)/formtype/(?P<form_type_pk>[0-9]+)/form_editor/(?P<form_pk>[0-9]+)/$', admin.site.admin_view(self.edit_form), name='edit_form')
            
        ]
        
        for aURL in urls:
            logger.info( aURL)
        return my_urls + urls


    ##==========================================================================================================================    
    #  EXPERIMENTAL ENDPOINTS  *************************************************************************************************
    ##==========================================================================================================================      
    
    def debug_toolA(self, request):
        allUsers = User.objects.all()
        
            
        for aUser in allUsers:
            if aUser.first_name == "Robert":
                aUser.permissions.user_project_title = "Or is it working Again?"
                aUser.save()
            
            
        
    def debug_tool(self, request, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="' + 'test' + '.csv"'
        

        writer = csv.writer(response)
        titles = []
        titles.append('__Title__')

        rows = []
        for result in Subject.objects.all():
            row = []
            row_dict = {}
            
            # store title and url
            row_dict[0] = result.title
            
            # controlled properties

            cps = result.subjectcontrolproperty_set.all()
                  
            for each_prop in cps:

                prop_name = each_prop.control_property.property.strip()
                prop_value = each_prop.control_property_value.title.strip()
                if not (prop_name in titles):
                    column_index = len(titles)                        
                    titles.append(prop_name)
                else:
                    column_index = titles.index(prop_name)
                    if column_index in row_dict:
                        prop_value = row_dict[column_index] + '; ' + prop_value
                row_dict[column_index] = "\"" + prop_value +"\""
            
            # free-form properties

            ps = result.subjectproperty_set.all()
                 
            for each_prop in ps:

                prop_name = each_prop.property.property.strip()
                prop_value = each_prop.property_value.strip()
                if not (prop_name in titles):
                    column_index = len(titles)                        
                    titles.append(prop_name)
                else:
                    column_index = titles.index(prop_name)
                    if column_index in row_dict:
                        prop_value = row_dict[column_index] + '; ' + prop_value
                row_dict[column_index] = "\"" + prop_value +"\""                 
                        
            # store row in list
            for i in range(len(titles)):
                if i in row_dict:
                    row.append(row_dict[i])
                else:
                    row.append('')
            rows.append(row)

        # write out the rows, starting with header
        writer.writerow(titles)
        for each_row in rows:
            writer.writerow([unicode(s).encode("utf-8") for s in each_row])
        return response



#=======================================================================================================================================================================================================================================
#=======================================================================================================================================================================================================================================
#      END OF SETUP CUSTOM ADMIN VIEWS
#=======================================================================================================================================================================================================================================
#=======================================================================================================================================================================================================================================


#//////////////////////////////////////////////////////////////////////////////////////////////////
##!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!  
# SET THE ADMIN SITE TO THIS CUSTOM ADMIN  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
##!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!   
admin.site = MyAdminSite() #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
##!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 
#//////////////////////////////////////////////////////////////////////////////////////////////////


#################################################################################################################################################################################################################################################################################################################################
#                   END NEW ADMIN 
#################################################################################################################################################################################################################################################################################################################################
#################################################################################################################################################################################################################################################################################################################################
#################################################################################################################################################################################################################################################################################################################################


