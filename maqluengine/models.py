
 
###########################################################################################################
###########################################################################################################
###########################################################################################################
#                   NEW DATABASE SCHEMA TO REPLACE OLD
###########################################################################################################
#
#  *This newer Maqlu Model.py file  section/schema is designed/created by Robert Bryant, as a Dynamic Entity(or model) creation by end-users
#  *This is created on behalf of an UPENN Museum project directed by Holly Pittman, and Steve Tinney
#  *Licensing has not yet been determined by the project so distribution is not allowed until source is made available on GIT with an associated license file
#
# 
#
#==================================================================================================================================================

import re
import sys
from django.db import models
from django.contrib.auth.models import User
from django.contrib.staticfiles.storage import staticfiles_storage
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
from django.conf import settings

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


#=======================================================================================================================================================
#
#   --MODEL DESIGN NOTES--
#
#   Think of this schema as a single generic entity type that can be customized as any number of new entity types based on the created content. Rather
#   than having multiple hard-coded models or entity types in the database that require migrations when changing, I designed a single 'entity type' that
#   can extend itself into as many unique entity types as necessary. This solves the complications of having to hard-code new models and structure when
#   different projects require different configurations of data in the same database. Users essentially configure their own organization and templates.
#   
#   |||DATABASE SCHEME DESIGN BRIEF|||
#   ==================================
#   --The Form Parent represents the top hiearchy of the entity groupings. Each project has its own set of entities, which are crafted as "Form Types"
#   --Form Types are templates of attached attribute types that individual Forms reference. e.g. an "Object" Form Type would hold all of the necessary
#   ----entry fields for each "Object" Form. Each individual "Object" Form would attach unique values to those "Object" Form Type attributes. The structure
#   ----follows the outline below:
#
#        FormTypeGroup          __FormProjectParent__--------------------------------------------FormProjectParent
#                 \            /      |       \                                                     ||
#                  \          /       |        \                                                    ||
#                 ____FormType     FormType     FormType____                                        ||
#                /         |       |      |       |         \                                       \/
#               /          |       |      |       |          \                                etc. etc. etc.          
#        _____Form_____   Form    Form  Form     Form        Form
#       /       |      \            |     |        |           |
#      /        |       \           V     V        V           V
# RecType    RecType     RecType    {  etc. etc. etc.  .......
#    |          |          |        {  etc. etc. etc.  .......
# RecValue   RecValue    RecValue   {  etc. etc. etc.  .......
#
#
#   In terms of database visualization, it's best to think of:
#       --A Project Form as a way to collect FormTypes into one package.
#       --A FormType would be the equivalent of a traditional database table
#       --A Form would be the equivalent of a row in a traditional database table
#       --FormAttributeType and FormReferenceType would represent the column headings in a traditional database table
#       --FormAttributeValue and FormReferenceValue would represent the individual cells in a traditional database table
#   *Although the database schema doesn't actually look this way, it's best to visualize it this way as it operates similarly to the end user
#
#   *Note: It is also best to think of the FormType model as a way to replace the UrOnline static entity types: Object, Location, Media, File, Person.
#           --Project is a way to organize each projects 'entities' into their own bundle--So in theory, UrOnline could recreate its hard coded entity types
#           --through this new system.
#
#   Each model has a foreign key to the parent project which servers as another indexed column for lookups. This helps ensure the security
#       --and segmentation of different project data in the databasem which should, in theory, speed up SQL queries
#
#
#=======================================================================================================================================================



class FormProject(models.Model):
    #----------------------------
    # Modifiable Variables
    name = models.CharField('Project Name', max_length=50)    
    description = models.TextField(blank=True, null=True)
    
    uri_img = models.CharField(max_length=255, blank=True, null=True, default="")
    #URI Variables
    uri_thumbnail = models.CharField(max_length=255, blank=True, null=True, default="")
    uri_download = models.CharField(max_length=255, blank=True, null=True, default="")
    uri_upload = models.CharField(max_length=255, blank=True, null=True, default="")
    uri_upload_key = models.CharField(max_length=255, blank=True, null=True, default="")
    geojson_string = models.TextField(blank=True, null=True)
    
    #-----------------------------
    # Restrictive Access variables
    is_public = models.BooleanField(default=False)
    
    #----------------------------
    # Read-only Variables
    date_created = models.DateTimeField(auto_now = False, auto_now_add = True,blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='project_ref_to_user_creator', blank = True, null=True,on_delete=models.SET_NULL)
    date_last_modified = models.DateTimeField(auto_now = True, auto_now_add = False,blank=True, null=True)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='project_ref_to_user_modifier', blank = True, null=True,on_delete=models.SET_NULL)
    
    def __str__(self):
        return self.name

class FormTypeGroup(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    #----------------------------
    # Read-only Attributes
    date_created = models.DateTimeField(auto_now = False, auto_now_add = True,blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='formtypegroup_ref_to_user_creator', blank = True, null=True,on_delete=models.SET_NULL)
    date_last_modified = models.DateTimeField(auto_now = True, auto_now_add = False,blank=True, null=True)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='formtypegroup_ref_to_user_modifier', blank = True, null=True,on_delete=models.SET_NULL)
    project = models.ForeignKey(FormProject, on_delete=models.CASCADE)
    def __str__(self):
        return self.name
        
class FormType(models.Model):
    #----------------------------
    # Modifiable Variables
    form_type_name = models.CharField(max_length=50, blank=True, null=True)
    type = models.IntegerField()#What kind of harcoded form type is it: e.g. 0= standard, 1= Media, 2= Geospatial Vector 3= Geospatial Raster
    media_type = models.IntegerField(default=-1) #is is an image 0, a pdf 1, or somethings else
    file_extension = models.CharField(max_length=10, blank=True, null=True, default="")
    uri_prefix = models.CharField(max_length=20, blank=True, null=True, default="")
    is_hierarchical = models.BooleanField(default=False)#determines whether or not the formtype's forms follow a hierchical structure
    is_numeric = models.BooleanField(default=False)
    
    #----------------------------
    # Templating 
    template_json = models.TextField(blank=True, null=True)
    
    #-----------------------------
    # Restrictive Access variables
    is_public = models.BooleanField(default=False)
    
    #----------------------------
    # Read-only Attributes
    date_created = models.DateTimeField(auto_now = False, auto_now_add = True,blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='formtype_ref_to_user_creator', blank = True, null=True,on_delete=models.SET_NULL)
    date_last_modified = models.DateTimeField(auto_now = True, auto_now_add = False,blank=True, null=True)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='formtype_ref_to_user_modifier', blank = True, null=True,on_delete=models.SET_NULL)
    
    #----------------------------
    # Model Relation Variables
    project = models.ForeignKey(FormProject, on_delete=models.CASCADE)
    form_type_group = models.ForeignKey(FormTypeGroup, on_delete=models.SET_NULL, blank=True, null=True)
    
    #----------------------------
    # Recycling Bin Flag
    flagged_for_deletion = models.BooleanField(default=False, null=False, blank=False)
        
    def __str__(self):
        if self.form_type_name is not None:
            return self.form_type_name
        else:
            return "No Label"                     

    def string_list_hierarchy(self):
        global formList
        formList = []
        #We want to find all the forms that have no parent element first--these are the top of the nodes
        for aForm in self.form_set.filter(hierarchy_parent=None):
            logger.info( aForm.get_hierarchy_label() + "<!-----")
            formList.append([aForm.pk,aForm.get_hierarchy_label()])
            #Make a recursive function to search through all children
            def find_children(currentParentForm):          
                global formList
                for currentChild in currentParentForm.form_set.all():
                    logger.info( currentChild.get_hierarchy_label() + "<!-----")
                    formList.append([currentChild.pk,currentChild.get_hierarchy_label()])
                    find_children(currentChild)
            find_children(aForm)
        logger.info( formList)
        return formList

    

                
class FormRecordAttributeType(models.Model):
    #----------------------------
    # Modifiable Variables
    record_type = models.CharField(max_length=50, blank=True, null=True)
    form_type = models.ForeignKey(FormType, on_delete=models.CASCADE, blank=True)
    order_number = models.IntegerField(unique=False, blank=True, null=True)
    is_numeric = models.BooleanField(default=False)
    #-----------------------------
    # Restrictive Access variables
    project = models.ForeignKey(FormProject, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)

    #----------------------------
    # Read-only Attributes
    date_created = models.DateTimeField(auto_now = False, auto_now_add = True,blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='frat_ref_to_user_creator', blank = True, null=True,on_delete=models.SET_NULL)
    date_last_modified = models.DateTimeField(auto_now = True, auto_now_add = False,blank=True, null=True)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='frat_ref_to_user_modifier', blank = True, null=True,on_delete=models.SET_NULL)
    
    #----------------------------
    # Recycling Bin Flag
    flagged_for_deletion = models.BooleanField(default=False, null=False, blank=False)
            
    def __str__(self):
        if self.record_type is not None:
            return self.record_type
        else:
            return "No Label"
    def save(self, *args, **kwargs):
        self.project = self.form_type.project
        super(FormRecordAttributeType, self).save(*args, **kwargs)
        
        
class FormRecordReferenceType(models.Model):
    #----------------------------
    # Modifiable Variables
    record_type = models.CharField(max_length=50, blank=True, null=True)
    order_number = models.IntegerField(unique=False, blank=True, null=True)
    
    #-----------------------------
    # Restrictive Access variables
    is_public = models.BooleanField(default=False)	
    project = models.ForeignKey(FormProject, on_delete=models.CASCADE)
    #----------------------------
    # Model Relation Variables
    form_type_parent = models.ForeignKey(FormType, related_name='ref_to_parent_formtype', on_delete=models.CASCADE, blank=True, null=True)
    form_type_reference = models.ForeignKey(FormType, related_name='ref_to_value_formtype', on_delete=models.SET_NULL, blank=True, null = True)

    #----------------------------
    # Read-only Attributes
    date_created = models.DateTimeField(auto_now = False, auto_now_add = True,blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='frrt_ref_to_user_creator', blank = True, null=True,on_delete=models.SET_NULL)
    date_last_modified = models.DateTimeField(auto_now = True, auto_now_add = False,blank=True, null=True)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='frrt_ref_to_user_modifier', blank = True, null=True,on_delete=models.SET_NULL)
    
    #----------------------------
    # Recycling Bin Flag
    flagged_for_deletion = models.BooleanField(default=False, null=False, blank=False)
            
    def __str__(self):
        if self.record_type is not None:
            return self.record_type
        else:
            return "No Label"
    def save(self, *args, **kwargs):
        self.project = self.form_type_parent.project
        logging.info("In Models Before save  :" + str(self.form_type_reference) + str(self.record_type) )
        super(FormRecordReferenceType, self).save(*args, **kwargs)
        logging.info("In Models AFTER save  :" + str(self.form_type_reference) + str(self.record_type))
        
        
class Form(models.Model):
    #----------------------------
    # Modifiable Variables
    form_name = models.CharField(max_length=50, blank=True, null=True)
    form_number = models.IntegerField(unique=False, blank=True, null=True)
    form_geojson_string = models.TextField(blank=True, null=True)
    hierarchy_parent = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True) #This is used for hierchical relations
    
    #-----------------------------
    # Restrictive Access variables
    is_public = models.BooleanField(default=False)
    project = models.ForeignKey(FormProject, on_delete=models.CASCADE)
    
    #----------------------------
    # Read-only Attributes
    date_created = models.DateTimeField(auto_now = False, auto_now_add = True,blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='form_ref_to_user_creator', blank = True, null=True,on_delete=models.SET_NULL)
    date_last_modified = models.DateTimeField(auto_now = True, auto_now_add = False,blank=True, null=True)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='form_ref_to_user_modifier', blank = True, null=True,on_delete=models.SET_NULL)
    
    #----------------------------------------
    # unique index for alpha-numeric sorting
    #^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    #       --This field is an incredibly important indexed field for sorting forms.
    #       --Because the form_name CANNOT be unique when multiple projects--or formtypes may need a form ID as, e.g. "1"
    #       --we need this unique value, which is simply the "<form_name>---<form_pk>"
    #       --The form_name must be in front to ensure proper alphanumeric sorting.
    #       --The form_pk is in the back to ensure this sort index will always be unique
    #       --A non-unique field would require far too much time to sort--hence I made this one.
    sort_index = models.CharField(max_length=255, unique=True)
    
    #----------------------------
    # Model Relation Variables
    form_type = models.ForeignKey(FormType, on_delete=models.CASCADE)
    
    #----------------------------
    # Recycling Bin Flag
    flagged_for_deletion = models.BooleanField(default=False, null=False, blank=False)
            
    def __str__(self):
        if self.form_number is not None:
           return str(self.form_number)
        elif self.form_name is not None:
            return self.form_name
        else:
           return "No Form Num"
    def get_ref_thumbnail(self):
        #--If the current form IS a media type already, then use itself to grab the thumbnail URI
        if self.form_type.type == 1:
           return self.get_thumbnail_type()
        else:
           #offer a default to "NO PREVIEW" if not found
           return staticfiles_storage.url("/static/site-images/no-thumb-missing.png")
        
    
    def get_hierarchy_label(self):
        logging.info("We're in the get hierarchy label function")
        label = ""
        currentParent = self.hierarchy_parent
        while currentParent != None:
            logging.info("Current Parent: " + str(currentParent) + "   This Form Name: " + str(self))
            label+="&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            currentParent = currentParent.hierarchy_parent

        label += '<span class="glyphicon glyphicon-triangle-right"></span>' + str(self)

        return label

    def get_thumbnail_type(self):
        if self.form_type.media_type == 3: #3D File
            return staticfiles_storage.url("/static/site-images/no-thumb-3D.png")
        elif self.form_type.media_type == 2: #PDF File
            return staticfiles_storage.url("/static/site-images/no-thumb-pdf.png")
        elif self.form_type.media_type == 1: #IMG File
            if self.form_type.uri_prefix != None or self.form_type.uri_prefix != "":
                return self.form_type.project.uri_thumbnail + self.form_type.uri_prefix + self.form_name  + self.form_type.file_extension  
            else:
                return self.form_type.project.uri_thumbnail + self.form_name + self.form_type.file_extension  
        else: #Other File Type
            return staticfiles_storage.url("/static/site-images/no-thumb-file.png")   
            
    def save(self, *args, **kwargs):
        #This save() override makes sure that every form has the same project as its formtype
        #   UUID: This function additionally creates the unique index value for sorting. Because we can't
        #   --have access to the PK value until AFTER the Form is saved in SQL, we first use a UUID value
        #   --and then use the pk value after it's saved.
        #   When the Form is edited later, we shorten it to the PK value (e.g. if it is not null)
        self.project = self.form_type.project
        if self.form_name != None:
            self.sort_index = self.form_name + "---" + str(uuid.uuid4())
        else:
            self.sort_index = "Empty---" + str(uuid.uuid4())
        super(Form, self).save(*args, **kwargs)
        #After saving the form, we are read to use the newly created PK value to create our sort Index
        #and then we need to be sure to save again.
        if self.form_name != None:
            self.sort_index = self.form_name + "---" + str(self.pk)
        else:
            self.sort_index = "Empty---" + str(self.pk)
        super(Form, self).save(*args, **kwargs)

class FormRecordAttributeValue(models.Model):
    #----------------------------
    # Modifiable Variables
    record_value = models.TextField(blank=True, null=True)
    #----------------------------
    # Read-only Attributes
    date_created = models.DateTimeField(auto_now = False, auto_now_add = True,blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='formatt_ref_to_user_creator', blank = True, null=True,on_delete=models.SET_NULL)
    date_last_modified = models.DateTimeField(auto_now = True, auto_now_add = False,blank=True, null=True)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='formatt_ref_to_user_modifier', blank = True, null=True,on_delete=models.SET_NULL)
    #----------------------------
    # Model Relation Variables
    record_attribute_type = models.ForeignKey(FormRecordAttributeType, on_delete=models.CASCADE)
    form_parent = models.ForeignKey(Form, null=True, blank=True, on_delete=models.CASCADE)
    project = models.ForeignKey(FormProject, on_delete=models.CASCADE)
    
    #----------------------------
    # Recycling Bin Flag
    flagged_for_deletion = models.BooleanField(default=False, null=False, blank=False)
        
    def __str__(self):
        if self.record_value is not None:
            return self.record_value
        else:
            return ""
    def save(self, *args, **kwargs):
        self.project = self.record_attribute_type.project
        super(FormRecordAttributeValue, self).save(*args, **kwargs)
        
class FormRecordReferenceValue(models.Model):
    #----------------------------
    # Model Relation Variables
    #This foreignKey stores the reference to another Form e.g. the Lot Sheet Number that this Lithic Object is attached to
    record_reference = models.ManyToManyField(Form, related_name='ref_to_value_form', blank=True, null=True)
    #This ID is for the external number reference to another form. E.g. if I'm importing data from an old project that has its
    #--own set of foreign keys, those foreign keys are stored here and used to find the references, because this database will have it's own
    #--set of foreign key / primary key ids
    external_key_reference = models.CharField(max_length=250, null=True, blank=True)
    #This foreignKey stores the actual Form, that this Reference is for, e.g. This is a specific Object Sheet entry
    form_parent = models.ForeignKey(Form, related_name='ref_to_parent_form', on_delete=models.CASCADE)
    #This is referencing the Record Reference Type that is associated with the Form Type of this Form
    record_reference_type = models.ForeignKey(FormRecordReferenceType, on_delete=models.CASCADE)
    project = models.ForeignKey(FormProject, on_delete=models.CASCADE)
    #----------------------------
    # Read-only Attributes
    date_created = models.DateTimeField(auto_now = False, auto_now_add = True,blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='formref_ref_to_user_creator', blank = True, null=True,on_delete=models.SET_NULL)
    date_last_modified = models.DateTimeField(auto_now = True, auto_now_add = False,blank=True, null=True)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='formref_ref_to_user_modifier', blank = True, null=True,on_delete=models.SET_NULL)
    
    #----------------------------
    # Recycling Bin Flag
    flagged_for_deletion = models.BooleanField(default=False, null=False, blank=False)
            
    def save(self, *args, **kwargs):
        self.project = self.form_parent.project
        super(FormRecordReferenceValue, self).save(*args, **kwargs)



#---------------------------------------------------------------------------------------------------------------------
#This extends the BaseUser model Django uses for authentication--I'm extending it to add special security variables
#   --This is necessary to ensure all users are tied to one project and access level--everytime an Admin view loads
#   --It MUST check the user in the current session and make absolute sure that they accessing a project that they
#   --belong to AS WELL as make sure they have acess permissions within that project to access that page, e.g. make 
#   --make changes to their project's database records.
class Permissions(models.Model):
    #Link it to the User Model
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    #Every user MUST have a project, and access level set for that project
    project = models.ForeignKey(FormProject, null=True, blank=True, on_delete=models.CASCADE)
    access_level = models.IntegerField(null=True, blank=True)
    
    #Some meta fields to describe the user
    job_title = models.CharField('Enter a Title', max_length=100)

    #Some stored user data(These will hold JSON strings)
    custom_templates = models.TextField(blank=True, null=True)
    saved_queries = models.TextField(blank=True, null=True)
    
@receiver(post_save, sender=User)
def create_user_permissions(sender, instance, created, **kwargs):
    if created:
        Permissions.objects.create(user=instance)
        

@receiver(post_save, sender=User)
def save_user_permissions(sender, instance, **kwargs):
    instance.permissions.save()



#---------------------------------------------------------------------------------------------------------------------        
#This model stores temporary objects that are part of a long-running process that can return json
#to a request to update ongoing progress, e.g. if the user is importing a large CSV file into the database,
#this model will store the regularly updated progress that returns with susbequent AJAX requests to update 
#a progress bar for a server-side process.
#
#   --These have a generated UUID and should be considered temporary. Once the process is complete, it should
#       make a final send for an AJAX request and delete the current object. Keeping it as an object model should
#       allow for multiple users running separate processes at the same time and keep it organized    
class AJAXRequestData(models.Model):
    uuid = models.CharField(max_length=32)
    is_finished = models.BooleanField(default=False)
    keep_alive = models.BooleanField(default=True)
    jsonString = models.TextField()
    def __str__(self):   
        return str(uuid)


        
    
###########################################################################################################
#                   END NEW DATABASE SCHEMA 
###########################################################################################################
###########################################################################################################
###########################################################################################################

















