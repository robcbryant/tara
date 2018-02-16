
//**************** ENKI-PROJECT-CONTROL-PANEL-MODIFY-USER.js *****************\\

//=================================================================================================================
//  This script handles the creation of users for a project as well as their modification in the project's
//      --control panel. It will only let the project admins (level 5) have access to this feature
//  *Security:
//      1-This script is only included on the page if the Django Template agrees with the access level
//          --This isn't completely safe--someone could steal this script and insert it into the page
//      2-If a user does steal and insert the script--any changes made through the AJAX API ALSO go through
//          --a server-side based verification of the user's level of access. If it doesn't agree with it,
//          --it will NOT make these changes.
//      3-This form, and corresponding Django view/ logic can NEVER create database-wide users with high levels
//          --of access. The default values for all users cannot be modified except on the server, so any database
//          --hacking short of an SQL injection attack will not occur--and even then, the creations are done through
//          --Dango filters, so it will not accept raw SQL regardless.            
//
//
//      This script handles the editing of the table in the user list similarly to the query view, and allows
//          --the creation of new users. The password is set by a field below the username
//==================================================================================================================



// ADD a new user:
// Build a function that creates a new empty row for the table and append() it to the end of the tbody
//  --this row's tds should contain <input type=text>'s to let the user enter the information

function createNewUserRowInTable(){
    //Although, now, I know how many cells there are in a row, in the future there may be more or less--so
    //I'm going to, in the name of sophistication, get a variable that reads the child count of one of the existing <tr>'s
    var numOfCols = $('#user-table .header').children().length;
    $newRow = $('<tr class="_NEWUSER"></tr>');
    //Add the Delete button
    $newRow.append('<td class="user-tool-col"><button onclick="deleteNewUserRow(this)" class="btn" type="button"><span class="glyphicon glyphicon-remove-circle"></span></button></td>');
    //Add the first col--the user glypicon
    $newRow.append('<td><span class="glyphicon glyphicon-user"></span></td>');
    //Add the second col--the access # dropbox
    $newRow.append('<td><select class="_REQUIRED" onchange="checkAllRequiredFieldsHaveInput()"><option value="5">5</option><option value="4">4</option><option value="3">3</option><option value="2">2</option><option value="1" default>1</option></select></td>');
    $newRow.append('<td><span>*</span><input type="text" class="_REQUIRED" oninput="checkAllRequiredFieldsHaveInput()"></input><br><span>*Password </span><input type="password" class="_REQUIRED" oninput="checkAllRequiredFieldsHaveInput()"></input></td>');
    //Start at index 4 because the prios require special modificaiton
    for (i=4;i<numOfCols;i++){
        $newRow.append('<td><input type="text" class="editing"></input></td>');
    }
    //Now sppend this row to the tables <tbody>
    $('#user-table tbody').append($newRow);
    
    //Check all our required fields
    checkAllRequiredFieldsHaveInput();
}
//bind a creation function to our add member button
$('#add-user-btn').click(createNewUserRowInTable);

function deleteNewUserRow(thisButton) {
    $(thisButton).parent().parent().remove();  
}



function checkUserName(){
    //For every new user, let's make sure the username isn't taken aleady
    //We'll need to AJAX the server API to do this
    
    var numOfElementsNeeded = $('#user-table ._NEWUSER').length + $('#user-table ._EDITED').length;
    var numOfElements = 0;
    var numOfSucesses = 0;
    
    var elementsToFix = [];
    //first pull all our names from any new or edited users
    $('#user-table ._NEWUSER').each(function(index, user) {      
        checkName($(user.children[3].children[1]));
    
    });

    //Add any User's being Edited
    $('#user-table ._EDITED').each(function(index, user) {
        //If this not the original username, then run it
        if ($(user.children[3]).find('input').val() != $(user.children[3]).find('input').attr('title')){
            checkName($(user.children[3]).find('input'));
        } else {
        //If it is then give ourselves a name check success
             numOfSucesses ++;
             numOfElements ++;
        }
    });             
    //Start our wait
    wait();
    
    function wait() {
        console.log("listening" + numOfSucesses + " : " + numOfElementsNeeded + "----NumRaqnTrhough:" + numOfElements)
        if ( numOfSucesses == numOfElementsNeeded ) {
            submitUserChangesToServer();
        } else {
            if(numOfElements == numOfElementsNeeded){ return;}
            setTimeout( wait, 250);
        }
    }
    
    function checkName($nameElement) {                    
            var postJSON = {};
            postJSON['username'] = $nameElement.val();
            postJSON['user_id'] = $nameElement.attr('title');
            $.ajax({ 
             url   : API_URLS.run_check_username_taken,
             type  : "POST",
             data  : postJSON, // data to be submitted
             //
             success : function(returnedQuery){
                if (returnedQuery.user_exists != "F") {
                    console.log($nameElement);
                    $nameElement.addClass('MISSING'); 
                     numOfElements ++;
                } else {
                     console.log("Should be adding to Num of Scuccesses");
                     numOfSucesses ++;
                     numOfElements ++;
                     console.log(numOfSucesses);
                }
                    },
             fail : function(xhr,errmsg,err) {
                    numOfElements ++;
                console.log("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: "+errmsg+
                    " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
                console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
             } 
        });           
    }
}


function submitUserChangesToServer(){
    var userChangeList = '{"userlist":[';

    //We need to cycle through each column in each <TR> with the "_NEWUSER" class
    $('#user-table ._NEWUSER').each(function(index, user) {
        var currentUser = '';
        if (index != 0) currentUser = ',{';
        else currentUser = '{';
        currentUser += '"is_new_user":"' +'T'+ '",';
        currentUser += '"access_level":"' + $(user.children[2]).find(':selected').val() + '",';
        currentUser += '"username":"' + $(user.children[3].children[1]).val()+ '",';
        currentUser += '"password":"' + $(user.children[3].children[4]).val() + '",';
        currentUser += '"name":"' + $(user.children[4].children[0]).val() + '",';
        currentUser += '"title":"' + $(user.children[5].children[0]).val() + '",';
        currentUser += '"email":"' + $(user.children[6].children[0]).val() + '"}';
        //Add the user to the change list
        userChangeList += currentUser;
    });

    
    
    //Add any User's being Edited
    $('#user-table ._EDITED').each(function(index, user) {
        var currentUser = '';
        if (index != 0) currentUser = ',{';
        else if (userChangeList != '{"userlist":[') currentUser = ',{'; else currentUser = '{';
        currentUser += '"is_new_user":"' +'F'+ '",';
        currentUser += '"user_id":"' +$(user.children[0].children[0].children[1]).attr('title')+ '",';
        currentUser += '"access_level":"' + $(user.children[2]).find('select').find(':selected').val() + '",';
        currentUser += '"username":"' + $(user.children[3]).find('input').val()+ '",';
        currentUser += '"password":"' + "NULL" + '",';
        currentUser += '"name":"' + $(user.children[4]).find('input').val() + '",';
        currentUser += '"title":"' + $(user.children[5]).find('input').val() + '",';
        currentUser += '"email":"' + $(user.children[6]).find('input').val() + '"}';
        //Add the user to the change list
        userChangeList += currentUser;
    });    
    

    
    //Finally, Add any users being deleted
    $('#user-table ._DELUSER').each(function(index, user) {
        var currentUser = '';
        if (index != 0) currentUser = ',{';
        else if (userChangeList != '{"userlist":[') currentUser = ',{'; else currentUser = '{';
        currentUser += '"is_new_user":"' +'DELETE'+ '",';
        currentUser += '"user_id":"' +$(user.children[0].children[0].children[0]).attr('title')+ '",';
        currentUser += '"access_level":"' + 'DELETE' + '",';
        currentUser += '"username":"' + 'DELETE'+ '",';
        currentUser += '"password":"' + 'DELETE' + '",';
        currentUser += '"name":"' + 'DELETE' + '",';
        currentUser += '"title":"' + 'DELETE' + '",';
        currentUser += '"email":"' + 'DELETE' + '"}';
        //Add the user to the change list
        userChangeList += currentUser;
    });
  
    //First check and see if we are actually submitting anything
    if (userChangeList != '{"userlist":['){
        //Close off our json string
        userChangeList += ']}';
        postJSON = {};
        postJSON['user_change_list'] = userChangeList;
        console.log(userChangeList);
        //Now let's get our AJAX ON!!!!!!
        $.ajax({ 
             url   : API_URLS.save_user,
             type  : "POST",
             data  : postJSON, // data to be submitted
             success : function(returnedQuery)
             {
                 console.log("MADE OUR CHANGES!");
                 //Check for a successful deletion and remove the corresponding rows from the page
                 $.each(returnedQuery, function(key, value) {
/*                     if(key.split('_').length > 1)
                        if(key.split('_')[0] == 'DELETED'){
                            console.log($('._DELUSER').children().first().children().first());
                            console.log($('._DELUSER').children().first().children().first().attr('title'));
                            if ($('._DELUSER').children().first().children().first().attr('title') == value)
                                $('._DELUSER').remove();
                        } */
                    
                });     
                refreshUserPanel();
             },

            // handle a non-successful response
            fail : function(xhr,errmsg,err) {
                console.log("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: "+errmsg+
                    " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
                console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
            }
        });
    }
}



function refreshUserPanel(){
          $.ajax({ 
             url   : API_URLS.get_users,
             type  : "POST",
             data  : postJSON, // data to be submitted
             success : function(returnedQuery)
             {
                //We need to clear the userlist table and refill it with the changes just made
                $('#user-table tbody').children().not('.header').remove()
                for (i=0; i< returnedQuery['userlist'].length; i++){
                    user = returnedQuery['userlist'][i];
                    console.log(user);
                    $newRow = $('<tr class="_EDITUSER"></tr>');
                    $newRow.append($(' <td class="user-tool-col"><div><button class="btn del-user-btn" type="button" title="'+user.user_id+'" onclick="flagUserForDeletion(this)"><span class="glyphicon glyphicon-remove-circle"></span></button><button class="btn edit-user-btn" onclick="turnOnRowForEditing(this)" type="button" title="'+user.user_id+'"><span class="glyphicon glyphicon-pencil"></span></button></div></td>'))
                    $newRow.append($('<td><span class="glyphicon glyphicon-user"></span></td>'))
                    $newRow.append($('<td><span>'+user.access_level+'</span><select class="_REQUIRED" onchange="checkSelectChange(this)" style="display:none;"><option value="5">5</option><option value="4">4</option><option value="3">3</option><option value="2">2</option><option value="1" default>1</option></select></td>'))
                    //Set the value of the access level select to the provided one
                    $newRow.children().last().children().first().children().first().val(user.access_level);
                    //Continue adding rest of columns
                    $newRow.append($('<td><span>'+user.username+'</span><input oninput="checkInputChange(this)" class="_REQUIRED" value="'+user.username+'" title="'+user.username+'" style="display:none"></input></td>'));
                    $newRow.append($('<td><span>'+user.name+'</span><input oninput="checkInputChange(this)"  value="'+user.name+'" style="display:none"></input></td>'));
                    $newRow.append($('<td><span>'+user.title+'</span><input oninput="checkInputChange(this)" value="'+user.title+'" style="display:none"></input></td>'));
                    $newRow.append($('<td><span>'+user.email+'</span><input oninput="checkInputChange(this)" value="'+user.email+'" style="display:none"></input></td>'));
                    //Add row to empty table
                    $('#user-table tbody').append($newRow);
                }
                //Now turn off the submit button again
                $('#submit-user-changes').prop('disabled', true);
             },

            // handle a non-successful response
            fail : function(xhr,errmsg,err) {
                console.log("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: "+errmsg+
                    " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
                console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
            }
        });  
    
}





//----------------------------------------------------------
//On Click Listeners for buttons

$('#submit-user-changes').click(checkUserName);;



$('.del-user-btn').click(flagUserForDeletion);    

function flagUserForDeletion(thisElement){
    if(this == window)
        $row = $(thisElement).parent().parent().parent();
    else
        $row = $(this).parent().parent().parent();
    console.log($row);
    if ($row.hasClass('_EDITUSER')){
        $row.children('td:not(.user-tool-col)').css('background-color','#ff0000');
        $row.removeClass('_EDITUSER');
        $row.addClass('_DELUSER');
    }else if($row.hasClass('_DELUSER')) {
        $row.children('td:not(.user-tool-col)').css('background-color','#ffffff');
        $row.removeClass('_DELUSER');
        $row.addClass('_EDITUSER');        
    }
    checkAllRequiredFieldsHaveInput()
}


$('.edit-user-btn').click(turnOnRowForEditing);
    
 
function turnOnRowForEditing(thisElement){
   //We need to turn on the Input boxes, and turn off the spans that contain the labels 
    if(this == window)
        $row = $(thisElement).parent().parent().parent();
    else
        $row = $(this).parent().parent().parent();
    //make sure we slice off the first <TD> element--which contains the profile glyphicon. We dont' need to try amkign changes to it/hide it etc.
    $cols = $row.children('td:not(.user-tool-col)').slice(1);
    console.log($row[0]);
    //If it is being edited, turn off the inputs
    if ($row.hasClass('EDITING')){
        turnOffRow($row);
    } else {
        //Add the EDITING class
        $row.addClass('EDITING');
        console.log("sanity check");
        //Show the selected inputs for this row
        $cols.children('input').show();
        $cols.children('select').show();
        $cols.children('span').hide();
        //Turn off other edited rows
        $('#user-table').find('tr:not(._NEWUSER)').each(function(index, childRow){
                //We have to use the [0] index to access the raw DOM element for testing equivalency
                if ($(childRow)[0] != $row[0]) turnOffRow($(childRow));
        });
        
    
    }

 
    function turnOffRow($aRow)  {
        console.log($aRow);
        //make sure we slice off the first <TD> element--which contains the profile glyphicon. We dont' need to try amkign changes to it/hide it etc.
        $cols = $aRow.children('td:not(.user-tool-col)').slice(1);
        //Make sure the text of the spans matches the input val() before turning them back on
        $cols.children('span').each(function(index, childSpan){
            console.log(index);
            //If it's the select element then add the value to the span instead
            if(index == 0)$(childSpan).text( $($cols.find('select:selected')).val() );
            else $(childSpan).text( $($cols.children('span').get(index)).find('input').val() );
        });
        //Remove the EDITING class
        $aRow.removeClass('EDITING');
        $cols.children('input').hide();
        $cols.children('select').hide();
        $cols.children('span').show();        
    }


}


//----------------------------------------------------------
//Other Listeners for buttons



//These are our listeners that detect whether or not the user actually edited any existing users--if they only turned edit mode on but didn't change
//  --anything, then it's pointless to send it to the server.
$('#user-table ._EDITUSER input').on('input', function() {
    //Add our flag that an entry was edited for this user
    $(this).parent().parent().addClass('_EDITED');
    //check whether we can submit edits
    checkAllRequiredFieldsHaveInput();    
});

$('#user-table ._EDITUSER select').change(function() {
    //Add the flag that an entry was changed for this user
    $(this).parent().parent().addClass('_EDITED');
    //Enable the save button
    $('#submit-user-changes').prop('disabled', false);
    //check whether we can submit edits
    checkAllRequiredFieldsHaveInput();
});

function checkInputChange(thisElement) {
    //Add our flag that an entry was edited for this user
    $(thisElement).parent().parent().addClass('_EDITED');
    //check whether we can submit edits
    checkAllRequiredFieldsHaveInput();    
}

function checkSelectChange(thisElement){
    //Add the flag that an entry was changed for this user
    $(thisElement).parent().parent().addClass('_EDITED');
    //Enable the save button
    $('#submit-user-changes').prop('disabled', false);
    //check whether we can submit edits
    checkAllRequiredFieldsHaveInput();
}


$('#user-table ._NEWUSER input').on('input', function() {
    //check whether we can submit edits
    checkAllRequiredFieldsHaveInput();
});

$('#user-table ._NEWUSER select').change(function() {
    //check whether we can submit edits
    checkAllRequiredFieldsHaveInput();    
});



//We need a function to check and make sure all required inputs are filled
function checkAllRequiredFieldsHaveInput(){
    $('#user-table ._REQUIRED').each(function(index, thisEntry){       
        if($(thisEntry).val() == "")  {         
           $(thisEntry).addClass('MISSING');
        } else {
           $(thisEntry).removeClass('MISSING');
        }
    });
   
   
   
   //We only need to enable the the save button if there are NO missing
   //The bool returns are only for some needs
   console.log($('#user-table .MISSING').length + "  :  " + $('#user-table ._DELUSER').length  + "  :  " + $('#user-table ._EDITED').length);
   if (     ($('#user-table ._NEWUSER').length > 0 || $('#user-table ._DELUSER').length > 0 || $('#user-table ._EDITED').length > 0 ) && $('#user-table .MISSING').length == 0 )   {
       $('#submit-user-changes').prop('disabled', false);

   } else { 
        $('#submit-user-changes').prop('disabled', true);

   }
   
   
   
}
    
 $('#project-form').submit( function(e){

        e.preventDefault(); // Keep the form from submitting
        
        var formData = $("#project-form").serializeArray();

        $.ajax({ 
             url   : API_URLS.save_project,
             type  : "POST",
             data  : formData, // data to be submitted
             success : function(returnedQuery)
             {
                console.log(returnedQuery);
                
             },
            // handle a non-successful response
            fail : function(xhr,errmsg,err) {
                console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
            }
        });        
        
 }); 

