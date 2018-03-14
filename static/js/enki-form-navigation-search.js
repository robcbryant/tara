//===================================================================================================================================================================================
//
//  This essentially adds an API/AJAX based search bar to locate forms by their name/ID
//
//  --As the user types letters into the search box, it will automatically query the server for a list of forms of that formtype (the first 5 results)
//  --using a case-insensitive 'icontains' filter. It displays them in a pop up drown down that when clicked on, links the user to the appropriate form page by its given ID
//
//===================================================================================================================================================================================


$('#form-nav-search-form').submit(function(e){
     e.preventDefault();
     $target = $('#search-box-list').children().first();
     if (typeof $target.children().first().attr('href') !== "undefined") window.location.href = $target.children().first().attr('href');
    //Else do nothing
});


 function queryServerForMatchingForms(searchbox, projectID, formtypeID){
    //First get all the associated data we'll need to send to the server
    var searchString = $(searchbox).val();
    var jsonData = {"projectID" : projectID, "formtypeID" : formtypeID, "query" : searchString};
    console.log(jsonData);
    //Send and AJAX Request
    $.ajax({ 
             url   : API_URLS.get_forms_search,
             type  : "POST",
             data  : jsonData, // data to be submitted
             success : function(returnedQuery)
             {
                //$("#search-box-list").show();
                console.log(returnedQuery.form_list);
                //Create a dropdown of no more than 5 items
                $newSelect = $($(searchbox).parent().children().first());
                console.log($newSelect);
                $newSelect.empty();
                $newSelect.hide();
                //Only do something if "form_list" is in the json data
                if(returnedQuery['form_list'] != null){
                    for (i=0; i< returnedQuery.form_list.length; i++){
                        var currentForm = returnedQuery.form_list[i];
                        if (currentForm.label.length > 24){ 
                            if (i == 0) $newListItem = $('<div class="search-box-item first-result"><a style="font-size:10px;" href="/admin/project/'+currentForm.projectPK +'/formtype/'+ currentForm.formtypePK +'/form_editor/'+ currentForm.formPK +'/">'+ currentForm.label +'</a>(Press Enter to Go)</div>');
                            else        $newListItem = $('<div class="search-box-item"><a style="font-size:10px;" href="/admin/project/'+currentForm.projectPK +'/formtype/'+ currentForm.formtypePK +'/form_editor/'+ currentForm.formPK +'/">'+ currentForm.label +'</a></div>');
                        } else {
                            if (i == 0) $newListItem = $('<div class="search-box-item first-result"><a href="/admin/project/'+currentForm.projectPK +'/formtype/'+ currentForm.formtypePK +'/form_editor/'+ currentForm.formPK +'/">'+ currentForm.label +'</a>(Press Enter to Go)</div>');
                            else        $newListItem = $('<div class="search-box-item"><a href="/admin/project/'+currentForm.projectPK +'/formtype/'+ currentForm.formtypePK +'/form_editor/'+ currentForm.formPK +'/">'+ currentForm.label +'</a></div>');                           
                        }
                        $newSelect.append($newListItem);
                    }
                    //For another robust solution--let's modify the text size to be smaller if it's longer than 30 characterSet
                    $newSelect.children().each( function() {
                       if ($(this).children().first().text().length > 30) $(this).children().first().addClass('form-nav-search-sml-txt'); 
                    });
                    $newSelect.show();
                }
             },

            // handle a non-successful response
            fail : function(xhr,errmsg,err) {
                console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
            }
        });    
    
}
 

 $(document).mouseup(function(e) 
{
    var container = $("#search-box-list");
    var adminToolBarContainer = $('#form-quick-search-tool .admin-search-list');
    // if the target of the click isn't the container nor a descendant of the container
    if ((!container.is(e.target) || !adminToolBarContainer.is(e.target) ) && (container.has(e.target).length === 0 || adminToolBarContainer.has(e.target).length == 0)) 
    {
        container.hide();
        adminToolBarContainer.hide();
    }
    
    
}); 


//This function will locate the previous and next buttons and give them their appropriate url address based on
//--an API endpoint 'get_previous_next_form'
function loadPreviousAndNextFormValues(){
    
    //setup our json
        var jsonData = {"project_pk" : CURRENT_PROJECT_PK, "formtype_pk" : CURRENT_FORMTYPE_PK, "form_pk" : CURRENT_FORM_PK};
        //Setup our element variables for editing
        $previousLink = $('#previous-form-link');
        $nextLink = $('#next-form-link');
        //Only run this function IF the elements above exist. If they don't, then don't run it. Otherwise we're sending the
        //server empty data and it will error. This doesn't affect performance or functionality, I just hate seeing the error and
        //a wasted AJAX request in the console for no reason. This function only needs to run on 'edit_form' which makes me think maybe
        //it should be its own js file separate from the admin toolbar search
        if ($previousLink.length && $nextLink.length){ //checking the elements length will be '0' if it doesn't exist, and therefore false
        
            //perform our AJAX request to the endpoint to get the values
            $.ajax({ 
                     url   : API_URLS.get_forms_previous_next,
                     type  : "POST",
                     data  : jsonData, // data to be submitted
                     success : function(returnedQuery)
                     {
                        console.log(returnedQuery);
                        //if our returned query contains an 'ERROR' key, then create fake links with a '#'
                        if (returnedQuery['ERROR']){
                            $previousLink.attr("href", "#");
                            $nextLink.attr("href", "#");
                        //Otherwise we are in the clear--edit our links/labels!
                        } else {
                            //Handle the Previous Form Link--and make the font size adaptive to the length of the label
                            $previousLink.attr("href", "/admin/project/"+returnedQuery.project_pk+"/formtype/"+returnedQuery.formtype_pk+"/form_editor/"+returnedQuery.previous_pk+"/");
                            if(returnedQuery.previous_label.length >= 12)$previousLink.parent().css('font-size', '12px');
                            if(returnedQuery.previous_label.length > 16) {$previousLink.parent().prepend(returnedQuery.previous_label.substring(0,12)+"...");$previousLink.parent().prop('title', returnedQuery.previous_label);}
                            else $previousLink.parent().prepend(returnedQuery.previous_label);
                            
                            //Handle the Next Form Link--and make the font size adaptive to the length of the label
                            $nextLink.attr("href", "/admin/project/"+returnedQuery.project_pk+"/formtype/"+returnedQuery.formtype_pk+"/form_editor/"+returnedQuery.next_pk+"/");
                            if(returnedQuery.next_label.length >= 12)$nextLink.parent().css('font-size', '12px');
                            if(returnedQuery.next_label.length > 16) {$nextLink.parent().append(returnedQuery.next_label.substring(0,12)+"..."); $nextLink.parent().prop('title', returnedQuery.next_label);} 
                            else $nextLink.parent().append(returnedQuery.next_label);
                        }
                     },

                    // handle a non-successful response
                    fail : function(xhr,errmsg,err) {
                        console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
                        $previousLink.attr("href", "#");
                        $nextLink.attr("href", "#");
                    }
            });   
        }
}





//We have to do this last -- AFTER the CSRF token is created

$(document).ready(loadPreviousAndNextFormValues);