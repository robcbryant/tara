


        //Function to remove the current reference from the form's FRRT widget-FRRT
        function removeReferenceFromFRRV(currentRef){
            $(currentRef).parent().remove();
            //$(currentRef).parent().find('input').attr('name', $(currentRef).parent().find('input').attr('name') += 'DELETE');
        }
        
        

        //This makes the search box disappear when clicking off the box
        $(document).mouseup(function(e) 
{
            var container = $(".search-box-list");

            // if the target of the click isn't the container nor a descendant of the container
            if (!container.is(e.target) && container.has(e.target).length === 0) 
            {
                container.hide();
            }
    
    
        });
    function resizeFRRVFontSize(){
        $('.frrv-container').each(function(){
            
           // console.log('SAAAAANITY TEST');
            //console.log($('.frrv-container').length);
            //console.log($(this));
            //I made a small linear function that will handle the font size(it can be adjusted if multiple widths aren't doing it the proper justice)
            var x = $(this).width();
            //console.log(x);
            
            var newSize = (0.054*x)-1
            //console.log(newSize);
            $(this).find('.frrv-label').css('font-size', newSize);
        });
    }    




    function setNeededHeightOfForm(){
        var largestY = 0;
        $('.layout-container').children().each( function(){
            var thisY = $(this).outerHeight() + $(this).position().top;
            //console.log(thisY);
            if (largestY < thisY) largestY = thisY;
        });
        
        console.log("settomg height: " + largestY);
        $('.layout-container').css('height', largestY+"px");
    }
        //Function to remove the current reference from the form's FRRT widget-FRRT
        function removeReferenceFromFRRV(currentRef){
            $(currentRef).parent().remove();
        }
        
        
        //Function that searches for the given list of forms based upon its formtype
        
        function lookForReferenceForms(searchbox, projectID, formtypeID, parentFormTypeID){
            //First get all the associated data we'll need to send to the server
            var searchString = $(searchbox).val();
            var jsonData = {"projectID" : projectID, "formtypeID" : formtypeID, "query" : searchString};
            console.log(parentFormTypeID);
            console.log (jsonData);
            //Send and AJAX Request
            $.ajax({ 
                     url   : API_URLS.get_forms_search,
                     type  : "POST",
                     data  : jsonData, // data to be submitted
                     success : function(returnedQuery)
                     {
                        console.log(returnedQuery.form_list);
                        //Create a dropdown of no more than 5 items
                        $newSelect = $(searchbox).parent().find('.search-box-list');
                        //Edit the Z-index of the parent widget so that the drop down box shows on top
                        $parentWidget = $newSelect.parent().parent().parent();
                        $parentWidget.css('z-index', '100');
                        $newSelect.empty();
                        $newSelect.hide();
                        //Only do something if "form_list" is in the json data
                        if(returnedQuery['form_list'] != null){
                            for (i=0; i< returnedQuery.form_list.length; i++){
                                var currentForm = returnedQuery.form_list[i];
                                console.log('onclick="addNewFRRVrefToFRRT(this, \''+currentForm.label+'\', '+currentForm.formPK+', '+parentFormTypeID+')"');
                                console.log('<div class="search-box-item first-result"><a style="font-size:10px;"                       onclick="addNewFRRVrefToFRRT(this,   '+currentForm.label+',   '+currentForm.formPK+', '+parentFormTypeID+', '+currentForm.thumbnail+', '+currentForm.url+')">'+ currentForm.label +'</a></div>');
                                if (currentForm.label.length > 24){ 
                                    if (i == 0) $newListItem = $('<div class="search-box-item first-result"><a style="font-size:10px;"  onclick="addNewFRRVrefToFRRT(this, \''+currentForm.label+'\', '+currentForm.formPK+', '+parentFormTypeID+', \''+currentForm.thumbnail+'\', \''+currentForm.url+'\')">'+ currentForm.label +'</a></div>');
                                    else        $newListItem = $('<div class="search-box-item"><a style="font-size:10px;"               onclick="addNewFRRVrefToFRRT(this, \''+currentForm.label+'\', '+currentForm.formPK+', '+parentFormTypeID+', \''+currentForm.thumbnail+'\', \''+currentForm.url+'\')">'+ currentForm.label +'</a></div>');
                                } else {
                                    if (i == 0) $newListItem = $('<div class="search-box-item first-result"><a                          onclick="addNewFRRVrefToFRRT(this, \''+currentForm.label+'\', '+currentForm.formPK+', '+parentFormTypeID+', \''+currentForm.thumbnail+'\', \''+currentForm.url+'\')">'+ currentForm.label +'</a></div>');
                                    else        $newListItem = $('<div class="search-box-item"><a                                       onclick="addNewFRRVrefToFRRT(this, \''+currentForm.label+'\', '+currentForm.formPK+', '+parentFormTypeID+', \''+currentForm.thumbnail+'\', \''+currentForm.url+'\')">'+ currentForm.label +'</a></div>');                           
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
        //This makes the search box disappear when clicking off the box
        $(document).mouseup(function(e) 
{
            var container = $(".search-box-list");
            //Reset the z-indices of the widgets back to 10
            $(container).parent().parent().parent().css('z-index', '10');
            // if the target of the click isn't the container nor a descendant of the container
            if (!container.is(e.target) && container.has(e.target).length === 0) 
            {
                container.hide();
            }
    
    
        });
        
        //Function adds a ref to the FRRT list box
        function addNewFRRVrefToFRRT(currentElement, label, form_id, frrt_id, thumbnail, url){
            console.log(frrt_id);
            $currentWidget = $('.widget-FRRT[pk="'+frrt_id+'"]')
            console.log($currentWidget[0]);
            
            
                $newItem = "";
                if ($currentWidget.hasClass('widget-image-view')) {
                    $newItem = $('#widget-templates .image-view-item').clone(true);
                    if ($currentWidget.find('.frrv-list').children().length > 0)$newItem.hide();
                } else {$newItem = $('#widget-templates .thumb-view-item').clone(true);}
                
                //Set some attributes for the input and label
                $newItem.find('input').val(form_id);
                $newItem.find('.frrv-label').html(label);
                $newItem.find('img').attr('src', thumbnail);
                $newItem.find('a').attr('href', url);
                //Change our name label if the FRRV already exists or not
                if ($currentWidget.attr('msg') == "NEW") $newItem.find('input').attr('name', 'frrvNEW__'+$currentWidget.attr('pk') );
                else $newItem.find('input').attr('name', 'frrv__'+$currentWidget.attr('msg') );
                
                console.log($newItem);
                $currentWidget.find('.frrv-list').append($newItem);
                //Turn off the search box list of forms now that we selected one
                
                $(".search-box-list").hide();          

        }
    
    var Xmin = 0;
    var Xmax = 100;
    var Ymin = 0;
    var Ymax = 100;
    var lastX = 0;
    var lastY = 0;
    $currentWidget = null;
    var minWidth = 0;
    var minHeight = 0;
    
    
    var widgetMouseMove = function(e){
        var currentPosition = $currentWidget.position();
        var parentOffset = $currentWidget.parent().offset();
        var currentParent = $currentWidget.parent()[0];
        
        $currentWidget.css('position', 'absolute');
       // console.log(currentPosition.left);        
        console.log(e.clientX + "  :  " + lastX);
        
        //Get our relative mouse position: This means the position of the mouse cursor within the widget container.
        //  --we can take this same position and apply it to the corner position of the widget itself
        var relativeMousePosX = e.pageX - parentOffset.left;
        var relativeMousePosY = e.pageY - parentOffset.top;
        console.log (relativeMousePosX +" : "+ parentOffset.left);
        
        //Here we need to figure out the relative 'steps' that we will allow the widget to move.
        //  --The X can only be a step of 5% of the total parent div size
        //  --The Y can only be a step of 25px

        //Our raw X step value of 5% is the (total container width / 100) * 5
        var rawXStepVal = (currentParent.offsetWidth / 100) * 5;
        //If it's a label we're changing, the step value will be 2.5%
        if ($currentWidget.attr('type') == 'label') rawXStepVal = (currentParent.offsetWidth / 100) * 2.5;
        
        //We need to round our widget's X position to the closest stepped value of the current mouse position
        var finalSteppedX = Math.floor(relativeMousePosX/rawXStepVal)*rawXStepVal;
        //Our raw Y step value is simply 25px;
        var rawYStepVal = 25;
        //Our steppedY will be the same process as finding the sepped x; we are just finding the nearest multiple of that value
        var finalSteppedY = Math.floor(relativeMousePosY/rawYStepVal)*rawYStepVal;
        
        console.log(currentParent.offsetWidth);
        console.log(currentParent);
        console.log ("rawX: " + rawXStepVal + " and relMousePos: " + relativeMousePosX);
        console.log (finalSteppedX + "  X -- : -- Y  " + finalSteppedY);
        
        if (finalSteppedX < 0) finalSteppedX = 0;
        else if(finalSteppedX > Xmax) finalSteppedX = Xmax;
        
        if (finalSteppedY < 0) finalSteppedY = 0;
        
        
        console.log(String(finalSteppedX/(currentParent.offsetWidth/100))+"%");
        //Now set our widget's left and top position to our new stepped x / y values
        $currentWidget.css('top', finalSteppedY);
        //converting our X BACK to a percentge ensures the widget divs resize on screen resize
        $currentWidget.css('left', String(finalSteppedX/(currentParent.offsetWidth/100))+"%");
        
        setNeededHeightOfForm()
        
    };


    var widgetMouseResize = function(e){
        var currentPosition = $currentWidget.position();
        var parentOffset = $currentWidget.parent().offset();
        var currentParent = $currentWidget.parent()[0];
        
        $currentWidget.css('position', 'absolute');
       // console.log(currentPosition.left);        
        console.log(e.clientX + "  :  " + lastX);
        
        //Get our relative mouse position: This means the position of the mouse cursor within the widget container.
        //  --we can take this same position and apply it to the corner position of the widget itself
        var relativeMousePosX = e.pageX - parentOffset.left;
        var relativeMousePosY = e.pageY - parentOffset.top;
        console.log (relativeMousePosX +" : "+ parentOffset.left);
        
        //Here we need to figure out the relative 'steps' that we will allow the widget to move.
        //  --The X can only be a step of 5% of the total parent div size
        //  --The Y can only be a step of 25px

        
        //Our raw X step value of 5% is the (total container width / 100) * 5
        var rawXStepVal = (currentParent.offsetWidth / 100) * 5;
        //If it's a label we're changing, the step value will be 2.5%
        if ($currentWidget.attr('type') == 'label') rawXStepVal = (currentParent.offsetWidth / 100) * 2.5;
        
        //We need to round our widget's X position to the closest stepped value of the current mouse position
        var finalSteppedX = Math.floor(relativeMousePosX/rawXStepVal)*rawXStepVal;
        //Our raw Y step value is simply 25px;
        var rawYStepVal = 25;
        //Our steppedY will be the same process as finding the sepped x; we are just finding the nearest multiple of that value
        var finalSteppedY = Math.floor(relativeMousePosY/rawYStepVal)*rawYStepVal;
        
        
        //Make sure the resize can't extend past the form bounding box
        if(finalSteppedX > Xmax) finalSteppedX = Xmax;
        
        
        var right = currentPosition.left + $currentWidget.outerWidth();
        var bottom = currentPosition.top + $currentWidget.outerHeight();
        var widthAdjustment = finalSteppedX - right;
        var heightAdjustment = finalSteppedY - bottom;
        
        var finalWidth = ($currentWidget.outerWidth()+widthAdjustment)/(currentParent.offsetWidth/100);
        var finalHeight = $currentWidget.outerHeight()+ heightAdjustment;

        //make sure our final heights and widths are greater than the minimum size of our default widget
        if (finalWidth < minWidth) finalWidth = minWidth;
        if (finalHeight < minHeight) finalHeight = minHeight;
        
        //Make sure the height can't exceed 50 for a dropdown widget
        if ($currentWidget.hasClass('widget-dropdown-view') && finalHeight > 50) finalHeight = 50;
        
        //Now set our widget's width/height to our new stepped x / y values        
        $currentWidget.css('height', finalHeight + 'px');
        //converting our X BACK to a percentge ensures the widget divs resize on screen resize
        $currentWidget.css('width', finalWidth+"%");
        if($currentWidget.hasClass('frat')) $currentWidget.find('textarea').css('height', (finalHeight-25) + "px");
        
        //If we're dealing with a label widget, determine the size of the text based on the width of the label
        if ($currentWidget.attr('type') == 'label'){
            newFontSize = Math.floor($currentWidget.outerWidth()/15);
            if (newFontSize > 27) newFontSize = 27;
            if (newFontSize < 15) newFontSize = 15;
            $currentWidget.find('.widget-label-value').css('font-size', newFontSize + "px")
            $currentWidget.find('.widget-label-value').css('line-height', (newFontSize+10) + "px")
        }
        
        
        setNeededHeightOfForm()
        
    }    

    
    $('.widget-control').mousedown(function(e){
        //While the left mouse button is held down over the widget control, move the widget container according to the mouse movements
        document.addEventListener('mousemove', widgetMouseMove, false);
        console.log(e);
        $currentWidget = $(e.currentTarget).parent();
        
        console.log($currentWidget);
        lastX = e.clientX;
        lastY = e.clientY;
        
        Xmax = $currentWidget.parent().width() - $currentWidget.width();
        Ymax = $currentWidget.parent().height() - $currentWidget.height();
        console.log(Ymax);
        if(Ymax < 0) {
            console.log('to low');
            $currentWidget.parent().css('height', $currentWidget.height());
            Ymax = 0;
        }
    
    });
    $('.widget-resize').mousedown(function(e){
        //While the left mouse button is held down over the widget control, move the widget container according to the mouse movements
        document.addEventListener('mousemove', widgetMouseResize, false);
        console.log(e);
        $currentWidget = $(e.currentTarget).parent();
        
        console.log($currentWidget);
        lastX = e.clientX;
        lastY = e.clientY;
        
        Xmax = $currentWidget.parent().width();
        
        if($currentWidget.hasClass('widget-label')){
            minWidth = 10;
            minHeight = 30;
        } else if ($currentWidget.hasClass('widget-image-view') || $currentWidget.hasClass('widget-thumb-view') ){
            minWidth = 30;
            minHeight = 150;
        } else if ($currentWidget.hasClass('frat')){
            minWidth = 10;
            minHeight = 50;     
        } else  if($currentWidget.hasClass('widget-dropdown-view')){
            minWidth = 10;
            minHeight = 50;
        }
        
       
        
        if(Ymax < 0) {
            console.log('to low');
            $currentWidget.parent().css('height', $currentWidget.height());
            Ymax = 0;
        }
    
    });    
    $(document).mouseup(function(e){
        //While the left mouse button is held down over the wdiget control, move the widget container according to the mouse movements
        document.removeEventListener('mousemove', widgetMouseMove, false);
        document.removeEventListener('mousemove', widgetMouseResize, false);
    });
    
     $('.layout-container textarea').mousedown( function(e){
        $(e.currentTarget).parent().parent().parent().css('width', '15%');
     });
     

    $('.widget-delete').click ( function() {
        
        $(this).parent().remove();
        
    });

    $('#add-label').click( function() {
         $currentLabel = $('#widget-templates .widget-label').clone(true);
         $('.layout-container').append($currentLabel);
         $currentLabel.css('top', ($('.layout-container').outerHeight() + 100) + 'px');
         //Set the height of the form for the ney template layout
         setNeededHeightOfForm();   
    });
    
    
    $('.widget-frrt-convert-to-image-view').click(function() {
        console.log("insanity test");
        $currentWidget = $(this).parent().parent();
        $newImageView = $('#widget-templates .widget-image-view').clone(true);
        $newImageView.css('position', 'absolute');
        $newImageView.css('z-index', '10');
        $newImageView.css('left', $currentWidget.css('left'));
        $newImageView.css('top', $currentWidget.css('top'));
        $newImageView.css('width', $currentWidget.css('width'));
        $newImageView.css('height', $currentWidget.css('height'));
        $newImageView.attr('pk', $currentWidget.attr('pk'));
        $newImageView.attr('ref_pk', $currentWidget.attr('ref_pk'));
        $newImageView.attr('type', 'image-view');
        $newImageView.find('.LABEL').html($currentWidget.find('.LABEL').html());
        if($currentWidget.hasClass('widget-dropdown-view')) $newImageView.css('height', '150px');
        $('.layout-container').append($newImageView);
        $currentWidget.remove();
    });
    
    $('.widget-frrt-convert-to-dropdown-view').click(function() {
        console.log("insanity test");
        $currentWidget = $(this).parent().parent();
        $newDropdownView = $('#widget-templates .widget-dropdown-view').clone(true);
        $newDropdownView.css('position', 'absolute');
        $newDropdownView.css('z-index', '10');
        $newDropdownView.css('left', $currentWidget.css('left'));
        $newDropdownView.css('top', $currentWidget.css('top'));
        $newDropdownView.css('width', $currentWidget.css('width'));
        $newDropdownView.css('height', '50px'); //This is a thumb's max
        $newDropdownView.attr('pk', $currentWidget.attr('pk'));
        $newDropdownView.attr('ref_pk', $currentWidget.attr('ref_pk'));
        $newDropdownView.attr('type', 'dropdown-view');
        $newDropdownView.find('.LABEL').html($currentWidget.find('.LABEL').html());
        
        $('.layout-container').append($newDropdownView);
        $currentWidget.remove();
  
    });
    
    $('.widget-frrt-convert-to-thumb-list').click(function() {
        console.log("insanity test");
        $currentWidget = $(this).parent().parent();
        $newThumbView = $('#widget-templates .widget-thumb-view').clone(true);
        $newThumbView.css('position', 'absolute');
        $newThumbView.css('z-index', '10');
        $newThumbView.css('left', $currentWidget.css('left'));
        $newThumbView.css('top', $currentWidget.css('top'));
        $newThumbView.css('width', $currentWidget.css('width'));
        $newThumbView.css('height', $currentWidget.css('height'));
        $newThumbView.attr('pk', $currentWidget.attr('pk'));
        $newThumbView.attr('ref_pk', $currentWidget.attr('ref_pk'));
        $newThumbView.attr('type', 'thumb-view');
        $newThumbView.find('.LABEL').html($currentWidget.find('.LABEL').html());
        if($currentWidget.hasClass('widget-dropdown-view')) $newThumbView.css('height', '150px');
        $('.layout-container').append($newThumbView);
        $currentWidget.remove();    
    });
    
    $('#save-template').click( function() {
        var jsondata = saveTemplateToJsonString();

        var formData = {"formtype_id":CURRENT_FORMTYPE_PK,"template_json":JSON.stringify(jsondata)};
        console.log(formData);
        $.ajax({ 
             url   : API_URLS.create_template,
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
   


    $(window).bind('resize', function() {
        resizeFRRVFontSize();
    }).trigger('resize');
    
    function resizeFRRVFontSize(){
        $('.frrv-container').each(function(){

            //I made a small linear function that will handle the font size(it can be adjusted if multiple widths aren't doing it the proper justice)
            var x = $(this).width();
            //console.log(x);
            
            var newSize = (0.054*x)-1
            //console.log(newSize);
            $(this).find('.frrv-label').css('font-size', newSize);
        });
    }
     //These listeners need to be added to the 'edit-form' / 'new-form' templates when done
    $('.nav-left').click( function(e) {
            $currentWidget = $(e.currentTarget).parent().parent();
            sizeOfList = $currentWidget.find('.frrv-list').children().length;
            currentIndex = 0;
            
            $currentWidget.find('.frrv-list').children().each( function() {
                console.log(this);
                if ($(this).is(':visible')) currentIndex = $currentWidget.find('.frrv-list').children().index($(this))
            });
            
            nextIndex = 0;
            console.log($(e.currentTarget));
            console.log(currentIndex);
            if (currentIndex == 0) nextIndex = sizeOfList - 1;
            else nextIndex = currentIndex - 1;
           
            
            $currentWidget.find('.frrv-list').children().eq(currentIndex).hide();
            $currentWidget.find('.frrv-list').children().eq(nextIndex).show();
    
    });

    $('.nav-right').click( function(e) {
            $currentWidget = $(e.currentTarget).parent().parent();
            sizeOfList = $currentWidget.find('.frrv-list').children().length;
            currentIndex = 0;
            
            $currentWidget.find('.frrv-list').children().each( function() {
                console.log(this);
                if ($(this).is(':visible')) currentIndex = $currentWidget.find('.frrv-list').children().index($(this))
            });
            
            nextIndex = 0;
            console.log($(e.currentTarget));
            console.log(currentIndex);
            if (currentIndex == sizeOfList - 1) nextIndex = 0;
            else nextIndex = currentIndex + 1;
           
            
            $currentWidget.find('.frrv-list').children().eq(currentIndex).hide(); 
            $currentWidget.find('.frrv-list').children().eq(nextIndex).show();
    });   
    
   function saveTemplateToJsonString(){
        //This function loops through each widget element in the formtype view page, and assigns their values to a formatted string of
        //  --json that is sent back to the server and stored in the formtypes template json field
        //
        //The json has the following format:
        //  -- {
        //         "name_of_template":[
        //                    { "id":"27",       -- The PK of the rtype which will match the widget element's ID tag
        //                      "width":"20%",   -- The width in percentage of the widget
        //                      "height":"20px", -- The height in pixels of the widget
        //                      "top":"20px",    -- The top value in pixels of the widget
        //                      "left":"20%"     -- The left value in percentage of the widget
        //                    },
        //                     ]
        //     }
    
        //TODO: FOR now-- we will ALWAYS edit the DEFAULT template
        //Let's set up our json object to add to our current template object already loaded
        var newTemplate = [];
        
        
        //Let's loop through each element in the main widget container
        $('#form-all-fields-grid .layout-container').children().each( function(){
            var widget = {};
            widget.label = $(this).find('.LABEL').html();
            widget.id = $(this).attr('pk');
            widget.ref_pk = $(this).attr('ref_pk');
            widget.width = Math.floor($(this).outerWidth()/(this.parentNode.offsetWidth/100)) + "%";
            widget.height = Math.floor($(this).outerHeight()) + "px";
            widget.top = Math.floor($(this).position().top) + "px";
            widget.left = Math.floor($(this).position().left/(this.parentNode.offsetWidth/100))+"%";
            widget.type = $(this).attr('type');
            if($(this).attr('type') == 'label') widget.label = $(this).find('.widget-label-value input').val();
            newTemplate.push(widget);
        });
        
        newTemplate = { 'default':newTemplate};
        console.log(newTemplate);
        return newTemplate;
    }
    
    $('#reset-layout').click(function(){
                var left = 0;
                var top = 0;
                console.log('sanity test2');
                $('.layout-container').empty()
                for(var i = 0; i < RTYPE_LIST.length; i++){
                    var rtype = RTYPE_LIST[i];
                   
                    if (rtype.rtype == 'FRAT'){
                        $newFRATView = $('#widget-templates .widget-frat').clone(true);
                        $newFRATView.css('position', 'absolute');
                        $newFRATView.css('left', left+'%');
                        $newFRATView.css('top', top+'px');
                        $newFRATView.css('min-width', '15%');
                        $newFRATView.css('width', '20%');
                        $newFRATView.css('height','50px');
                        $newFRATView.attr('pk', rtype.pk);
                        $newFRATView.attr('type', 'frat');
                        $newFRATView.find('.LABEL').html(rtype.label);
                        $newFRATView.find('textarea').css('width', '100%');
                        $newFRATView.find('textarea').css('height', '25px');

                        $('.layout-container').append($newFRATView);
                        if(left == 75) {left = 0; top+=75;}
                        else {left += 25;}
                    } else {
                        $newThumbView = $('#widget-templates .widget-thumb-view').clone(true);
                        $newThumbView.css('position', 'absolute');
                        $newThumbView.css('z-index', '10');
                        $newThumbView.css('left', left+'%');
                        $newThumbView.css('top', top+'px');
                        $newThumbView.css('width', '25%');
                        $newThumbView.css('height', '150px');
                        $newThumbView.attr('pk', rtype.pk);
                        $newThumbView.attr('ref_pk', rtype.ref_formtype_pk);
                        $newThumbView.attr('type', 'thumb-view');
                        $newThumbView.find('.LABEL').html(rtype.label);

                        $('.layout-container').append($newThumbView);
                        if(left == 75){ left = 0; top+=150;}
                        else {left += 25;}
                    } 
                }
                //Set the height of the form for the ney template layout
                setNeededHeightOfForm();    

    });

    
    //===========================================================================================================================================
    //  This Chunk Below Handles all the initialization of the widgets
    //===========================================================================================================================================
    //vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    
    function loadTemplateJson(){
        //This function loads the json template string provided by the formtype
        //  --This string can contain several templates, but will always have a 'default' template that is initially loaded.
        //  --This allows the admin to create different templates for different purposes--e.g. one template might be better for
        //  ----data-entry while another might make more sense for just viewing the individual forms. All template will be provided
        //  ----to each form django view, but will default to the default template unless the user has a stored preference
        //
        //The json has the following format:
        //  -- {[
        //          {"default":[
        //                    { "id":"27",       -- The PK of the rtype which will match the widget element's ID tag
        //                      "width":"20%",   -- The width in percentage of the widget
        //                      "height":"20px", -- The height in pixels of the widget
        //                      "top":"20px",    -- The top value in pixels of the widget
        //                      "left":"20%"     -- The left value in percentage of the widget
        //                    },
        //                     ]
        //          },
        //          {"new_template":[ {....      --This is any other templates that may have been created
        //                            ....
        //                     } ]
        //          },
        //     ]}
       
       

        //If not a new template
       if(CURRENT_TEMPLATE != "" && CURRENT_TEMPLATE != "None"){
            var template = JSON.parse(CURRENT_TEMPLATE);
            console.log(template);
            console.log("WHAT IS GOING ON");
            var widgets = template['default'];
            //loop through each 
        for (let i = 0; i < widgets.length; i++){
            var widget = widgets[i];
            
            switch (widget.type){
                case 'label':
                    $newLabel = $('#widget-templates .widget-label').clone(true);
                    $newLabel.css('left', widget.left);
                    $newLabel.css('top', widget.top);
                    $newLabel.css('min-width', '15%');
                    $newLabel.css('width', widget.width);
                    $newLabel.css('height', widget.height);
                    if (INITIALIZATION_CODE == 0) $newLabel.find('.LABEL :input').val(widget.label);
                    else $newLabel.find('.LABEL').html(widget.label);
                    $('.layout-container').append($newLabel);
                    break;
                case 'image-view':
                    $newImageView = $(".layout-container .frrt[pk='"+widget.id+"']")
                    //If Not an image-view, then convert it to one
                    if(!$newImageView.hasClass('widget-image-view')) convertFRRTtoImageView($newImageView);
                    $newImageView.css('position', 'absolute');
                    $newImageView.css('z-index', '10');
                    $newImageView.css('left', widget.left);
                    $newImageView.css('top', widget.top);
                    $newImageView.css('width', widget.width);
                    $newImageView.css('height', widget.height);
                    $newImageView.attr('pk', widget.id);
                    $newImageView.attr('ref_pk', widget.ref_pk);
                    //Only add the listener if we aren't editing a template
                    if(INITIALIZATION_CODE != 0)$newImageView.find('.search-box input')[0].addEventListener("input", function(){lookForReferenceForms(this, CURRENT_PROJECT_PK, $(this).parent().parent().parent().attr('ref_pk'),CURRENT_FORMTYPE_PK)});
                    $newImageView.find('.LABEL').html(widget.label);

                    break;
                case 'thumb-view':
                    $newThumbView = $(".layout-container .frrt[pk='"+widget.id+"']")
                    $newThumbView.css('position', 'absolute');
                    $newThumbView.css('z-index', '10');
                    $newThumbView.css('left', widget.left);
                    $newThumbView.css('top', widget.top);
                    $newThumbView.css('width', widget.width);
                    $newThumbView.css('height', widget.height);
                    $newThumbView.attr('pk', widget.id);
                    $newThumbView.attr('ref_pk', widget.ref_pk);
                    //Only add the listener if we aren't editing a template
                    if(INITIALIZATION_CODE != 0)$newThumbView.find('.search-box input')[0].addEventListener("input", function(){lookForReferenceForms(this, CURRENT_PROJECT_PK, $(this).parent().parent().parent().attr('ref_pk'),CURRENT_FORMTYPE_PK);});
                    $newThumbView.find('.LABEL').html(widget.label);

                    break;
                case 'frat':
                    $newFratWidget = $(".layout-container .frat[pk='"+widget.id+"']")
                    console.log(widget.id + "    Why is it not finding this?");
                    console.log($newFratWidget[0]);
                    $newFratWidget.css('position', 'absolute');
                    $newFratWidget.css('z-index', '10');
                    $newFratWidget.css('left', widget.left);
                    $newFratWidget.css('top', widget.top);
                    $newFratWidget.css('min-width', '15%');
                    $newFratWidget.css('width', widget.width);
                    $newFratWidget.css('height', widget.height);
                    $newFratWidget.find('.LABEL').html(widget.label);
                    $newFratWidget.find('textarea').css('width', '100%');
                    $newFratWidget.find('textarea').css('height',  $newFratWidget.find('textarea').parent().parent().parent().outerHeight()-25); 
                    $newFratWidget.attr('pk', widget.id);

                    break;
                case 'dropdown-view':
                    //Just make a blank drop down with no options
                     $currentWidget = $(".layout-container .frrt[pk='"+widget.id+"']"); 
                    $newDropdownView = $('#widget-templates .widget-dropdown-view').clone(true);
                    $newDropdownView.css('position', 'absolute').css('left', widget.left).css('top', widget.top).css('height', widget.height).css('width', widget.width);
                    $newDropdownView.attr('pk', $currentWidget.attr('pk'));
                    $newDropdownView.attr('ref_pk', $currentWidget.attr('ref_pk'));
                    $newDropdownView.attr('type', 'dropdown-view');
                    $newDropdownView.find('.LABEL').html($currentWidget.find('.LABEL').html());
                    $newDropdownView.find('.ext-key input').attr('name', $($currentWidget).find('.ext-key input').attr('name') )
                     $('.layout-container').append($newDropdownView);
                     $currentWidget.remove();
                    //If this is a NEW form, then we need to setup the drop box -- we don't need a rtype list since it's a new form so we use null 
                    if(INITIALIZATION_CODE == 1)setupDropdownWidget(widget, null, $newDropdownView.attr('ref_pk'))
                     break;
            }        

        }      
            
        } else {
            //Do Nothing--it's already initialized
        }
        setNeededHeightOfForm();
        
    }
    
    
    //We only need this function because the default is a thumbview. We'll never need a convert to thumbview function
    function convertFRRTtoImageView(currentWidget) {
        console.log("insanity test");
        //Convert the Widget itself
        $newImageView = $('#widget-templates .widget-image-view').clone(true);
        $newImageView.attr('pk', currentWidget.attr('pk'));
        $newImageView.attr('ref_pk', currentWidget.attr('ref_pk'));
        $newImageView.attr('type', 'image-view');
        $newImageView.find('.LABEL').html(currentWidget.find('.LABEL').html());
        //If the reference to a formtype is "None" or if there isn't one set yet in the FormType editor, then disable this widget's inputs
        if($newImageView.attr('ref_pk') == "None") $newImageView.find(':input').attr('disabled', true);
        //replace the search box with the one from the current widget with attached oninput event listeners
        $searchBox = $newImageView.find('.search-box');
        $searchBox.remove();
        $newImageView.find('.frrv-search').append($(currentWidget).find('.search-box'));       
        $newImageView.find('.ext-key input').attr('name', $(currentWidget).find('.ext-key input').attr('name') )
        //Now convert the list items to the new ones
        $(currentWidget).find('.frrv-list').children().each( function(){            
            $newItem = $('#widget-templates .image-view-item').clone(true);
            $newItem.find('img').attr('src', $(this).find('img').attr('src'))
            $newItem.find('a').attr('href', $(this).find('a').attr('href'))
            $newItem.find('a').html($(this).find('a').html())
            $newItem.find('input').attr('name', $(this).find('input').attr('name'))
            $newItem.find('input').val($(this).find('input').val())
            $newImageView.find('.frrv-list').append($newItem);
            
        
        });
        $('.layout-container').append($newImageView);
        $(currentWidget).remove();
    }
    
    
    function convertFRRTtoDropdownView(currentWidget, formlistjson) {
        console.log(formlistjson);
        //Convert the Widget itself
        $newDropdownView = $('#widget-templates .widget-dropdown-view').clone(true);
        $newDropdownView.attr('pk', currentWidget.attr('pk'));
        $newDropdownView.attr('ref_pk', currentWidget.attr('ref_pk'));
        $newDropdownView.attr('type', 'dropdown-view');
        $newDropdownView.find('.LABEL').html(currentWidget.find('.LABEL').html());
        $newDropdownView.find('.ext-key input').attr('name', $(currentWidget).find('.ext-key input').attr('name') )
        //Now add all the options based on the form list in the json
        $selectBox = $newDropdownView.find('select');
        $selectBox.attr('name', '');
        for(i = 0; i < formlistjson.length; i++){
            
            $selectBox.append('<option value="'+formlistjson[i].form_pk+'">'+formlistjson[i].form_label+'</option>');
        }       
        
        $('.layout-container').append($newDropdownView);
        $(currentWidget).remove();  
        return $newDropdownView;
          
    }
    
    
    function initializeLayout(){
                var left = 0;
                var top = 0;
                console.log('sanity test2');
                $('.layout-container').empty()
                console.log(RTYPE_LIST);
                for(var i = 0; i < RTYPE_LIST.length; i++){
                    var rtype = RTYPE_LIST[i];
                   
                    if (rtype.rtype == 'FRAT'){
                        $newFRATView = $('#widget-templates .widget-frat').clone(true);
                        $newFRATView.css('position', 'absolute');
                        $newFRATView.css('left', left+'%');
                        $newFRATView.css('top', top+'px');
                        $newFRATView.css('min-width', '15%');
                        $newFRATView.css('width', '20%');
                        $newFRATView.css('height','50px');
                        $newFRATView.attr('pk', rtype.pk);
                        $newFRATView.attr('type', 'frat');
                        $newFRATView.find('.LABEL').html(rtype.label);
                        $newFRATView.find('textarea').css('width', '100%');
                        $newFRATView.find('textarea').css('height', '25px');
                        //Add the 'name' tag for the form to submit to POST. We will also default them as new rvals in case there isn't one
                        //which will ensure if there is RVAL later, they will be treated as new RVALS by default('frat__pk#' rather than 'frav_pk#')
                        $newFRATView.find('textarea').attr('name', 'frat__'+rtype.pk)
                        $('.layout-container').append($newFRATView);
                        if(left == 75) {left = 0; top+=75;}
                        else {left += 25;}
                    } else {
                        $newThumbView = $('#widget-templates .widget-thumb-view').clone(true);
                        $newThumbView.css('position', 'absolute');
                        $newThumbView.css('z-index', '10');
                        $newThumbView.css('left', left+'%');
                        $newThumbView.css('top', top+'px');
                        $newThumbView.css('width', '25%');
                        $newThumbView.css('height', '150px');
                        $newThumbView.attr('pk', rtype.pk);
                        $newThumbView.attr('ref_pk', rtype.ref_formtype_pk);
                        $newThumbView.attr('type', 'thumb-view');
                        $newThumbView.find('.LABEL').html(rtype.label); 
                        //If the reference to a formtype is "None" or if there isn't one set yet in the FormType editor, then disable this widget's inputs
                        if($newThumbView.attr('ref_pk') == "None") $newThumbView.find(':input').attr('disabled', true)
                        //Only add the listener if we aren't editing a template
                        if(INITIALIZATION_CODE != 0){
                            $newThumbView.find('.search-box input').attr('ref_rtype', rtype.ref_formtype_pk);
                            $newThumbView.find('.search-box input').attr('parent_rtype', rtype.pk);
                            $newThumbView.find('.search-box input')[0].oninput = function(){  lookForReferenceForms(this, CURRENT_PROJECT_PK, $(this).attr('ref_rtype'),$(this).attr('parent_rtype')) };
                        }
                        //Add the 'name' tag for the form to submit to POST. We will also default them as RTYPE_RTYPEPK_'NEW' 
                        //which will ensure if there is RVAL later, they will be treated as new RVALS by default(changed to not 'NEW' if not)
                        $newThumbView.find('.ext-key input').attr('name', 'frrvNEW__'+rtype.pk+'__ext')
                        $('.layout-container').append($newThumbView);
                        if(left == 75){ left = 0; top+=150;}
                        else {left += 25;}
                    } 
                }
                //Set the height of the form for the ney template layout
                setNeededHeightOfForm();    

    }

    //This needs to be a separate function so each AJAX receives unique instances of variables to use in the loop that calls on this
    function setupDropdownWidget(widget, rtype_list, ref_pk){
        console.log(widget);
        console.log(rtype_list);
        console.log(ref_pk);
        $.ajax({ 
                 url   : API_URLS.get_formtype_forms,
                 type  : "POST",
                 data  : {"formtype_pk" : ref_pk}, // data to be submitted
                 success : function(returnedQuery) {
                     $newDropDownView = $(".layout-container .frrt[pk='"+widget.id+"']");
                     console.log($newDropDownView[0]);
                     console.log(returnedQuery); 
                     //If Not a dropdown-view, then convert it to one
                     $newDropDownView = convertFRRTtoDropdownView($newDropDownView, returnedQuery.form_list); 
                     $newDropDownView.css('position', 'absolute');
                     $newDropDownView.css('z-index', '10');
                     $newDropDownView.css('left', widget.left);
                     $newDropDownView.css('top', widget.top);
                     $newDropDownView.css('width', widget.width);
                     $newDropDownView.css('height', widget.height);
                     $newDropDownView.find('select').attr('name', 'frrvNEW__'+widget.id);
                     
                     $currentWidget = "";
                     //Only setup the options and which ones are selected if we're editing a form
                     //--a new form obviously doesn't have any values made yet
                     if(INITIALIZATION_CODE == 2){
                         for (i = 0; i < rtype_list.length; i++){
                            if (rtype_list[i].rtype == "FRRT"){ 
                                $currentWidget = $('.layout-container').find('.widget-dropdown-view[pk="'+rtype_list[i].rtype_pk+'"]')
                                var rvals = rtype_list[i].rval
                            
                                if (currentRTYPE.rval_pk != "")$currentWidget.attr('msg',rtype_list[i].rval_pk);
                                 if ($currentWidget.hasClass('widget-dropdown-view')){
                                   //Dropdowns only allow ONE option to be selected rather than the typical multiple
                                   //   --They should be used for controlled-term fields in your data
                                   //   --when converting a different widget to this widget, information will be lost if a form is saved
                                   //   --It won't be lost as long as the user never saves a form being edited, but this will only list the
                                   //   --the FIRST item in the rtype list for the user to view in the drop down
                                   $currentSelect = $currentWidget.find('select');
                                   $currentSelect.attr('name', 'frrv__'+rtype_list[i].rval_pk);
                                   if (rvals.length > 0){
                                       var rval = rvals[0];
                                        $currentSelect.children().each( function(){
                                        //console.log(parseInt($(this).val()) + "    :    "  + rval.pk);
                                        if(parseInt($(this).val()) == rval.pk) $currentSelect.val(rval.pk);
                                      
                                        });
                                   }
                                 }
                             }
                         }
                     }
                }
        });          
        
        
    }


    
    function loadForm(rtypes){
        var rtype_list = rtypes;
        console.log(rtype_list);
        rtype_list = rtype_list['rtype_list'];
        
        if(CURRENT_TEMPLATE != "" && CURRENT_TEMPLATE != "None"){
            var widgetList = JSON.parse(CURRENT_TEMPLATE)['default']
            $layoutContiner = $('.layout-container');
            
            //First we need to create the empty widgets with their proper positioning etc.
            for (var i = 0; i < widgetList.length; i++){
                var widget = widgetList[i];
                
                switch (widget.type){
                    case 'label':
                        $newLabel = $('#widget-templates .widget-label').clone(true);
                        $newLabel.css('left', widget.left);
                        $newLabel.css('top', widget.top);
                        $newLabel.css('min-width', '15%');
                        $newLabel.css('width', widget.width);
                        $newLabel.css('height', widget.height);
                        $newLabel.find('.LABEL').html(widget.label);
                        console.log($newLabel[0]);                        
                        $('.layout-container').append($newLabel);
                        break;
                    case 'image-view':
                        $newImageView = $(".layout-container .frrt[pk='"+widget.id+"']")
                        //If Not an image-view, then convert it to one
                        if(!$newImageView.hasClass('widget-image-view')) convertFRRTtoImageView($newImageView);
                        $newImageView.css('position', 'absolute');
                        $newImageView.css('z-index', '10');
                        $newImageView.css('left', widget.left);
                        $newImageView.css('top', widget.top);
                        $newImageView.css('width', widget.width);
                        $newImageView.css('height', widget.height);
                        $('.layout-container').append($newImageView);
                        break;
                    case 'thumb-view':
                        $newThumbView = $(".layout-container .frrt[pk='"+widget.id+"']")
                        $newThumbView.css('position', 'absolute');
                        $newThumbView.css('z-index', '10');
                        $newThumbView.css('left', widget.left);
                        $newThumbView.css('top', widget.top);
                        $newThumbView.css('width', widget.width);
                        $newThumbView.css('height', widget.height);
                        $('.layout-container').append($newThumbView);
                        break;
                    case 'frat':
                        $newFratWidget = $(".layout-container .frat[pk='"+widget.id+"']")
                        $newFratWidget.css('position', 'absolute');
                        $newFratWidget.css('z-index', '10');
                        $newFratWidget.css('left', widget.left);
                        $newFratWidget.css('top', widget.top);
                        $newFratWidget.css('min-width', '15%');
                        $newFratWidget.css('width', widget.width);
                        $newFratWidget.css('height', widget.height);
                        $newFratWidget.find('textarea').css('width', '100%');
                        $newFratWidget.find('textarea').css('height',  $newFratWidget.find('textarea').parent().parent().parent().outerHeight()-25); 
                        $('.layout-container').append($newFratWidget);
                        break;
                    case 'dropdown-view':
                         $currentWidget = $(".layout-container .frrt[pk='"+widget.id+"']");
                         //$currentWidget.css('position', 'absolute').css('left', widget.left).css('top', widget.top).css('height', widget.height).css('width', widget.width);
                        $newDropdownView = $('#widget-templates .widget-dropdown-view').clone(true);
                        $newDropdownView.css('position', 'absolute').css('left', widget.left).css('top', widget.top).css('height', widget.height).css('width', widget.width);
                        $newDropdownView.attr('pk', $currentWidget.attr('pk'));
                        $newDropdownView.attr('ref_pk', $currentWidget.attr('ref_pk'));
                        $newDropdownView.attr('type', 'dropdown-view');
                        $newDropdownView.find('.LABEL').html($currentWidget.find('.LABEL').html());
                        $newDropdownView.find('.ext-key input').attr('name', $($currentWidget).find('.ext-key input').attr('name') )
                         $('.layout-container').append($newDropdownView);
                         $currentWidget.remove();
                         //If the reference to a formtype is "None" or if there isn't one set yet in the FormType editor, then disable this widget's inputs
                         if($newDropdownView.attr('ref_pk') == "None") $newDropdownView.find(':input').attr('disabled', true);
                         else setupDropdownWidget(widget, rtype_list, $newDropdownView.attr('ref_pk'));
                      
                         break;
                }        
            }
        }       

        setNeededHeightOfForm(false);
        resizeFRRVFontSize();      
        loadRVALSIntoWidgets(rtype_list);

    
    }
    
    function loadRVALSIntoWidgets(rtype_list){
        for (i = 0; i < rtype_list.length; i++){
            currentRTYPE = rtype_list[i];
           
            //We have to separate between frat and frrt when looking for the PK #'s -- Why do you ask? Well because they are 2 different Django Models
            //  --with 2 different tables, they can potentially have the same PK value--especially a new project setting up stuff. Originally I used
            //  --the ID attribute of the element, but then I didn't realize the pk values are potentially not unique in this scope
            //console.log(currentRTYPE.rtype_pk);
            if (currentRTYPE.rtype == "FRAT") $currentWidget = $('.layout-container').find('.frat[pk="'+currentRTYPE.rtype_pk+'"]')
            else $currentWidget = $('.layout-container').find('.frrt[pk="'+currentRTYPE.rtype_pk+'"]')
            //console.log($currentWidget);
            //Now that we have our widget, we can determine what type it is and go from there
           if ($currentWidget.hasClass('widget-frat')){
                //Set the default name to  frav__<fratpk>__new. If there isn't a frav currently attached to the frat, it will have it's default
                //  --and later, if there is a frav, it will replace the name with the required one for updating the form!
                 $currentWidget.find('textarea').attr('name', 'frav__'+currentRTYPE.rtype_pk+'__new');
                //Set the value of the widget
                
                $currentWidget.find('textarea').html(currentRTYPE.rval.value);
                $currentWidget.find('textarea').attr('name', 'frav__'+currentRTYPE.rval.pk);
                

           } else if ($currentWidget.hasClass('widget-thumb-view')){
                //Set the value of the widget
                for (b = 0; b < currentRTYPE.rval.length; b++){
                    var rval = currentRTYPE.rval[b];
                    //Clone the appropriate widget and child it to this widgets list view
                    $currentRefItem = $('#widget-templates').find('.thumb-view-item').clone(true);
                    $currentWidget.find('.frrv-list').append($currentRefItem);
                    //Change the Image to this
                    console.log($currentRefItem.find('img'));
                    console.log(rval);
                    $currentRefItem.find('img').attr('src', rval.thumbnail);
                    $currentRefItem.find('a').attr('href', rval.url)
                    $currentRefItem.find('a').html(rval.name)
                    $currentRefItem.find('input').attr('name','frrv__'+currentRTYPE.rval_pk)
                    $currentRefItem.find('input').val(rval.pk);
                }
                console.log($currentWidget.attr('msg'));
                if (currentRTYPE.rval_pk != "")$currentWidget.attr('msg', currentRTYPE.rval_pk);
                console.log($currentWidget.attr('msg') + "  " + $currentWidget.attr('pk'));
                $currentWidget.find('.ext-key input').val(currentRTYPE.ext_key)
                $currentWidget.find('.ext-key input').attr('name', 'frrv__'+currentRTYPE.rval_pk+'__ext')
                $currentWidget.find('.search-box input').attr('ref_rtype', currentRTYPE.ref_formtype);
                $currentWidget.find('.search-box input').attr('parent_rtype', currentRTYPE.rtype_pk);
                $currentWidget.find('.search-box input')[0].oninput = function(){  lookForReferenceForms(this, CURRENT_PROJECT_PK, $(this).attr('ref_rtype'),$(this).attr('parent_rtype')) };
       
           } else if ($currentWidget.hasClass('widget-image-view')){
                //Set the value of the widget
                console.log("INDSANITY TEST");
                for (c = 0; c < currentRTYPE.rval.length; c++){
                    var rval = currentRTYPE.rval[c];
                    //Clone the appropriate widget and child it to this widgets list view
                    $currentRefItem = $('#widget-templates').find('.image-view-item').clone(true);
                    //We need to hide all items after the first
                    if(c>0) $currentRefItem.hide();
                    $currentWidget.find('.frrv-list').append($currentRefItem);
                    //Change the Image to this
                    console.log($currentRefItem.find('img'));
                    console.log(rval);
                    $currentRefItem.find('img').attr('src', rval.thumbnail);
                    $currentRefItem.find('a').attr('href', rval.url)
                    $currentRefItem.find('a').html(rval.name)
                    $currentRefItem.find('input').attr('name','frrv__'+currentRTYPE.rval_pk)
                    $currentRefItem.find('input').val(rval.pk);
                }
                console.log(currentRTYPE.rval_pk);
                console.log($currentWidget.attr('msg'));
                if (currentRTYPE.rval_pk != ""){$currentWidget.attr('msg', currentRTYPE.rval_pk); console.log("WHYARE WE DOING THIS");}
                console.log($currentWidget.attr('msg') + "  " + $currentWidget.attr('pk'));
                $currentWidget.find('.ext-key input').val(currentRTYPE.ext_key)
                $currentWidget.find('.ext-key input').attr('name', 'frrv__'+currentRTYPE.rval_pk+'__ext')
                $currentWidget.find('.search-box input').attr('ref_rtype', currentRTYPE.ref_formtype);
                $currentWidget.find('.search-box input').attr('parent_rtype', currentRTYPE.rtype_pk);
                $currentWidget.find('.search-box input')[0].oninput = function(){  lookForReferenceForms(this, CURRENT_PROJECT_PK, $(this).attr('ref_rtype'),$(this).attr('parent_rtype')) };
         
           } 
           
        }        
        
    }
    
    
    
    function loadRTYPESForForm(){
 
        
            var formData = {"formtype_pk": CURRENT_FORMTYPE_PK};
            console.log(formData);
            $.ajax({ 
                 url   : API_URLS.get_rtypes,
                 type  : "POST",
                 data  : formData, // data to be submitted
                 success : function(returnedQuery)
                 {
                    //Go Ahead and initialize all the widgets with their titles
                    RTYPE_LIST = returnedQuery.rtype_list;
                    initializeLayout();
                    //If we're editing a form we need to also load the RVALS and not just the RTYPES
                    //  --which requires a separate endpoint
                    if(INITIALIZATION_CODE == 2){
                        var jsonData = {"form_pk" : CURRENT_FORM_PK};
                        $.ajax({ 
                                 url   : API_URLS.get_form_rtypes,
                                 type  : "POST",
                                 data  : jsonData, // data to be submitted
                                 success : function(returnedQuery) {console.log(returnedQuery);loadForm(returnedQuery);}
                            });     
                    } else {           
                        //Otherwise just load the template as normal
                        loadTemplateJson();
                    }
                 }
            });          
        
    }



    $(document).ready(loadRTYPESForForm);
    //^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    //===========================================================================================================================================
    //  This Chunk Above Handles all the initialization of the widgets
    //===========================================================================================================================================  