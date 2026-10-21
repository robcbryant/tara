from django.core.management.base import BaseCommand
from maqluengine.models import *
from django.utils import timezone

class Command(BaseCommand):
    #=======================================================#
    #   ACCESS LEVEL :  TARA ADMIN    BACKUP_PROJECT()
    #=======================================================#     
    
    def handle(self, *args, **kwargs):
        print("We're Testing out our admin command here  :  "  + str(FormProject.objects.all().count()) )
    
    
    def test(self, *args, **kwargs):
        
        ERROR_MESSAGE = ""
        logger.info( request)
                
        #-------------------------------------------------------------------------------------------------
        #   Let's get all of our formtypes and filter them by their own projects last backup date
        
        #NOTES FOR FUTURE CODE:  some_project.last_backup_date = timezone.now()   -- use this to save the project's last date backed up



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

    
        #If anything goes wrong in the process, return an error in the json HTTP Response
        SECURITY_log_security_issues(request.user, 'admin.py - ' + str(sys._getframe().f_code.co_name), ERROR_MESSAGE, request.META)
        return HttpResponse('{"ERROR":"'+ ERROR_MESSAGE +'","row_index":"0","is_complete":"True", "row_total":"0", "row_timer":"0"}',content_type="application/json")       
    