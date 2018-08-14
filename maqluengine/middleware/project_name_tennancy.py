#===========================================================================
#
#   project_name_tennancy.py   MIDDLEWARE
#
#   This middleware will handle incoming URL requests and redirect them to their appropriate Django
#       path which is a project ID.
#
#   I want each project to have a subdomain, e.g. alhiba.tara.museum.upenn.edu/, and when this
#       middleware receives that request, it will redirect the user to tara.museum.upenn.edu/3/
#       where '3' is the ID of the alhiba project in the database
#
#===========================================================================

from django.urls import reverse
from django.shortcuts import redirect
from maqluengine import views
import sys
from maqluengine.models import *
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


def RedirectToProjectURI(get_response):
    def middleware(request):
        #extract the identifier from the url
        host = request.get_host() # here is the full url, e.g. 'https://alhiba.tara.museum.upenn.edu'
        print( "SANITY CHECK A")
        print( request)
        print( host,file=sys.stderr)
        if not request.path == request.path_info:#This solves an infinite redirect by making sure we aren't redirecting to the same address we are requesting
            try:
                try: 
                    host = host.split(':')[1]  # we remove the protocol part: 'alhiba.tara.museum.upenn.edu'
                    subdomain = host.split('.')[0]  # and now we get the subdomain:'alhiba'
                    
                except: 
                    subdomain = host.split('.')[0]  # and now we get the subdomain:'alhiba'
                print( "SANITY CHECK B")
                logger.info(subdomain)
                logger.info(host)
                print( "SANITY CHECK C")
                #Let's use that subdomain to search for the corresponding project in the database
                #e.g. alhiba has the ID 3
                try: project = FormProject.objects.get(shortname=subdomain)
                except FormProject.DoesNotExist: project = None
                
                #Add it to our request object
                request.session['project'] = project
                #Now return the request to the view with the new 'project' variable
                print(reverse('maqluengine:index'),file=sys.stderr)
                print(request.GET,file=sys.stderr)
                print(reverse('maqluengine:index') + request.path_info)
                #return get_response(request)
                return redirect(request.path_info)
            except IndexError:
                pass
        return get_response(request)
    return middleware