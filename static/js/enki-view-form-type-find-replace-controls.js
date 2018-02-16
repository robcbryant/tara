    function turnOnColumnForEdits(thisButton){
        console.log("Is it working?");
        console.log(thisButton);
        console.log(thisButton.parentNode.parentNode);
        var headerColParent = thisButton.parentNode.parentNode.parentNode;
        var childToCheck = thisButton.parentNode.parentNode
        var colIndex = Array.prototype.indexOf.call(headerColParent.children, childToCheck); 
        console.log(colIndex);
        $allRows = $('#view-table-body').children().first().children();
        console.log($allRows);
        if($(thisButton).hasClass('ON')){
            //remove the ON class
            $(thisButton).removeClass('ON');
        } else {
            //add the ON class
            $(thisButton).addClass('ON');
        }
        //Loop through all rows of the table and get the TD column child that matches this index
        //We start at index 1 to skip the header
        for (i=1; i < $allRows.length ;i++){
              $currentRow = $($allRows[i]);
              console.log($currentRow);
              $currentCol = $currentRow.children().eq(colIndex);
              console.log($currentCol);
              if($(thisButton).hasClass('ON')){
                  //Turn off span
                  $currentCol.children().first().children().first().hide();
                  //Turn on TextArea
                  $currentCol.children().last().children().last().prop('disabled', false);
                  $currentCol.children().last().children().last().show();
              } else {
                  //Turn on span
                  $currentCol.children().first().children().first().show();
                  //Turn off TextArea if it wassn't edited
                  if( !$currentCol.children().first().children().first().hasClass('EDITED')){$currentCol.children().last().prop('disabled', true);}             
                  $currentCol.children().last().children().last().hide();
              }
        }
    
    }
    
    function flagTextareaAsChanged(textElement){
        console.log("WHERE ARE YOU");
        $(textElement.parentNode.children[0]).text($(textElement).val());
        $(textElement.parentNode.children[0]).addClass("EDITED");
        $(textElement.parentNode.children[0]).prop('disabled', false);
    } 
 
 
    $('.button-find-replace').click(function() {
        console.log("sanity check")
        //This function needs to take the search term provided in the "Find" input field (Case sensitive) and replace it with
        //--whatever is entered into the "Replace" field. thiss operation starts with the clicking of the magnifying glass button
        var searchString = $('#find').val();
        var replaceString = $('#replace').val();
        console.log(searchString + "  " + replaceString);
        
        //This will look through all fields in the table that are in edit mode--e.g. if one column is selected--which should be the norm
        //--it will go through every row in that column and perform the replace operation. Because they are text areas, we need to change the .val()
        //--on the jquery object
        
        //Additionally--let's put some robust stats in here to tell the user what just transpired--so they don't have to trust it blindly
        //--e.g. Let's show the user how many matches it found and replaced, and which terms it found and replaced that match in.
        //--e.g. again-- If I search for '9' it may reaplce it in 'Area 9' as well as 'Lot 9' or something similar to that effect.
        //--so let's show the user exactly what is replaced so they don't corrupt their data by blindly following their own simplistic
        //--regex expression they have little control over. They should search replace 'Area 9' with 'Area 8' and not '9' with '8'. Users
        //--will do what they want--so this is to make them aware of their own mistakes =) I'll set up a dictionary of key value lists
        //--and every unique search-term will be a new key with it's value incremented by 1 every timeout
        
        var searchReplaceStats = {};
        
       $('#view-table-body').find('.frav_edit:enabled').each(function () {
           console.log($(this).val());
            //First see if we have a match
            //if we get a -1 there isn't a match
            if($(this).val().search(searchString) != -1){
                //if it exists already--increment the value, otherwise set it to one
                if ($(this).val() in searchReplaceStats){ searchReplaceStats[$(this).val()] += 1;}
                else{searchReplaceStats[$(this).val()] = 1;}
                //We have to create a new regex object to use our search variable for a global replace
                //--otherwise it will search for the string "searchString" and not what that variable actually contains
                $(this).val($(this).val().replace(new RegExp(searchString, "g"), replaceString));
                //Now change the sibling <SPAN> to reflect the same change and add EDITED as a class
                var $sibling = $(this.parentNode.children[0]);
                $sibling.text($(this).val());
                $sibling.addClass("EDITED");
            }
       });
       console.log(searchReplaceStats);
       //Now fill in our stats div with the finished stats
       $findStats = $('.find-replace-stats')
       var statsMessage = "";
       for(key in searchReplaceStats){
        statsMessage += 'Search Term "' + searchString + '" was found in "'+key+'" and replaced: ' + searchReplaceStats[key] + ' times by: "'+replaceString+'"<br>';
       }
       $findStats.html(statsMessage);
        
    });
    
    
    
   
   
    //Need a function that replaces the form's built in functionality and performs an ajax call
    $("#find-replace-form").submit(function(e){
        
        e.preventDefault(); // Keep the form from submitting
        
        //turn the edit textareas off--so the one's not edited are disabled--otherwise we will submit ALL text areas
        //first we need to grab the columns that are turned on(there might be more than 1)
        $('.ON').each( function() {
            turnOnColumnForEdits(this);
        });

        var sForm = $(this);
        $uuid = gen_uuid();
        $sesID = $('#sesID').val();
        var freq = 500;
        var formData = $("#find-replace-form").serializeArray();
        console.log(formData);
        $.ajax({ 
             url   : API_URLS.save_forms_bulk,
             type  : "POST",
             data  : formData, // data to be submitted
             success : function(returnedQuery)
             {
                console.log(returnedQuery);
                //If successful:
                //Update the stats message <div> with the information from the editor
                var htmlString = $('.find-replace-stats').html() + returnedQuery.message + "<br>";
                $('.find-replace-stats').html( htmlString );
                
                //We need to remove all "EDITED" tags from all forms so it's reset for new edits
                $('.EDITED').each( function(){
                    $(this).removeClass('EDITED');
                });
                
             },
                // handle a successful response
                done : function(json) {
                  
                    console.log("!!!!!!!!!!!!!!!!"); // log the returned json to the console
                    console.log("success"); // another sanity check
                },

                // handle a non-successful response
                fail : function(xhr,errmsg,err) {
                    $('#info-message').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: "+errmsg+
                        " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
                    console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
                }
        });
    });


    
    //This let's a user click the 'text' in a table to start editing it in addition to the normal edit button at the top of the table column -- a shortcut essentially
    function editIndividualRecord(thisElement) {
        console.log("Is it working?");
        var headerColParent = thisElement.parentNode.parentNode.parentNode;
        var childToCheck = thisElement.parentNode.parentNode;
        var colIndex = Array.prototype.indexOf.call(headerColParent.children, childToCheck); 
        console.log(colIndex);
        $allRows = $('#view-table-body').children().first().children();
        console.log($allRows);
        var $headerCol = $('#view-table-body').children().first().children().first().children().eq(colIndex).children().first().children().eq(1);
        console.log($headerCol);
        turnOnColumnForEdits($headerCol[0]);
    
    }
 