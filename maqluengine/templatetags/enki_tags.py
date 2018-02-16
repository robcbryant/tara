from django import template
from maqluengine import *
from maqluengine.models import *
import sys
import random
register = template.Library()

###########################################################################################################
#      ERROR / INFO LOGGER SETUP
###########################################################################################################
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
hdlr = logging.FileHandler('/var/tmp/django-db-log.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 

def post_model_type(model_type):
    #print >>sys.stderr, "++++++++++++++++++++" + model_type.__class__.__name__ + " === ?" + str(FormRecordAttributeType.__name__)
    if model_type.__class__.__name__ == FormRecordAttributeType.__name__:
        return "frat__"
    if model_type.__class__.__name__ == FormRecordReferenceType.__name__:
        return "frrt__"
    if model_type.__class__.__name__ == FormType.__name__:
        return "ft__"
    if model_type.__class__.__name__ == Form.__name__:
        return "f__"
    if model_type.__class__.__name__ == FormRecordAttributeValue.__name__:
        return "frav__"
    if model_type.__class__.__name__ == FormRecordReferenceValue.__name__:
        return "frrv__"
    if model_type.__class__.__name__ == FormProject.__name__:
        return "fp__"
    return "NO_MATCH"

    
#This tag will look through all forms for the curent FormType and find the next highest integer
#TODO: Need to add a check to make sure a FormType object is being passed and not any other form_type
def get_new_form_num(form_type): 
    #Grab all the matches
    form_matches =  Form.objects.filter(form_type__exact = form_type).order_by('form_number')
    #print >>sys.stderr, "++++++++++++++++++++" + str(form_matches)
    #If there are no forms yet, e.g. a new project, then start with 1
    if str(form_matches) == "[]":
        #print >>sys.stderr, "+WTFFF++++++++" + str(form_matches.count)
        return 1

    #Otherwise let's sort all the forms returned by ascending order and grab the first result
    #form_matches = form_matches.objects.order_by('form_number')
    #Increment the new form number and return it
    return form_matches.last().form_number + 1


def getUniqueSessionToken(temp):
    return random.randint(1, 999999)

def isLengthGreaterThan(string,max_length):
    print >>sys.stderr, str(len(string)) + "  is length vs : " + max_length
    if len(string) > int(max_length):
        return 1
    else:
        return 0
        
def get_number_of_cols_needed_to_finish(totalLoopCount, remainingInterations):
    rangeLimit = totalLoopCount - remainingInterations
    return range(rangeLimit)

def print_httpd_log(message):
    print >>sys.stderr, message
    return ""
    
def get_toolbar_title(tool_bar_code):
    title = "Toolbar"
    tool_bar_code, model_ID = tool_bar_code.split('_')
    if tool_bar_code == "Project":
        title = str(FormProject.objects.get(pk=model_ID)) + " Tools"
        
    elif tool_bar_code == "FormType":
        title = "Edit " + str(FormType.objects.get(pk=model_ID))
        
    elif tool_bar_code == "Form":
        title = "Edit " + str(Form.objects.get(pk=model_ID))
        
    elif tool_bar_code == "NewFormType":
        title = "New Form Type Creator"
        
    elif tool_bar_code == "NewForm":
        title = "New " + str(FormType.objects.get(pk=model_ID))
        
    elif tool_bar_code == "CSVImporter":
        title = "Form Type Importer Wizard"
        
    elif tool_bar_code == "NewMediaFormType":
        title = "New Media Type"
        
    elif tool_bar_code == "NewControlGroupFormType":
        title = "New Control Field"        
    return title    
    
def get_url(URLcode, pk_values):
    finalURL = "http://67.205.135.223/"
    pk_values = pk_values.split(',')
    
    if URLcode == "Project":
        finalURL += "admin/project/"+pk_values[0]+"/"
 
    elif URLcode == "FormType":
        finalURL += "admin/project/"+pk_values[0]+"/formtype_editor/"+pk_values[1]+"/"
             
    elif URLcode == "Form":
        finalURL += "admin/project/"+pk_values[0]+"/formtype/"+pk_values[1]+"/form_editor/"+pk_values[2]+"/"
        
    elif URLcode == "NewFormType":
        finalURL += "admin/project/"+pk_values[0]+"/formtype_generator/"
        
    elif URLcode == "NewMediaType":
        finalURL += "admin/project/"+pk_values[0]+"/mediaformtype_generator/"
        
    elif URLcode == "NewForm":
        finalURL += "admin/project/"+pk_values[0]+"/formtype/"+pk_values[1]+"/form_generator/"
        
    elif URLcode == "CSVImporter":
        finalURL += "admin/project/"+pk_values[0]+"/formtype_importer/1/"
    
    elif URLcode == "FormType_VIEW":
        finalURL += "admin/project/"+pk_values[0]+"/formtype/"+pk_values[1]+"/"
      
    return finalURL

def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    #logger.info( "ENKI TAG TEMPLATE TIMER")
    return str(arg1) + str(arg2)

def trim_title(title):
    if len(title) > 17:
        n = len(title) - 17
        title = title[:-n] + "..."
    return title


register.filter('isLengthGreaterThan', isLengthGreaterThan)    
register.filter('getUniqueSessionToken', getUniqueSessionToken)
register.filter('print_httpd_log', print_httpd_log)
register.filter('get_toolbar_title', get_toolbar_title)
register.filter('trim_title', trim_title)    
register.filter('addstr', addstr)    
register.filter('get_url', get_url) 
register.filter('get_number_of_cols_needed_to_finish', get_number_of_cols_needed_to_finish)
register.filter('post_model_type', post_model_type)
register.filter('get_new_form_num', get_new_form_num)



