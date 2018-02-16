

    function showBusyGraphic(elementToCover){
        $busyIndicator = $('<div id="busy-indicator"><img src="/static/site-images/busy-indicator.gif"></img></div>');
        $(elementToCover).append($busyIndicator);
    }
    
    function removeBusyGraphic(){
        $('#busy-indicator').remove();
    }

 $('#form-type-form').submit( function(e){

        e.preventDefault(); // Keep the form from submitting
        
        var formData = $("#form-type-form").serializeArray();
        
        showBusyGraphic($('#form-type-form'));
        
        $.ajax({ 
             url   : API_URLS.save_formtype,
             type  : "POST",
             data  : formData, // data to be submitted
             success : function(returnedQuery)
             {
                console.log(returnedQuery);
                removeBusyGraphic();
                location.reload();
                
                
             },
            // handle a non-successful response
            fail : function(xhr,errmsg,err) {
                console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
            }
        });        
        
 }); 
 
 $('#new-form-type-form').submit( function(e){

        e.preventDefault(); // Keep the form from submitting
        
        var formData = $("#new-form-type-form").serializeArray();
        showBusyGraphic($('#form-type-form'));
        
        $.ajax({ 
             url   : API_URLS.create_formtype,
             type  : "POST",
             data  : formData, // data to be submitted
             success : function(returnedQuery)
             {
                console.log(returnedQuery);
                removeBusyGraphic();
                location.reload();
                
             },
            // handle a non-successful response
            fail : function(xhr,errmsg,err) {
                console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
            }
        });        
        
 }); 



var attributeTempUniqueID = 0;

$("#add_recordattribute").click(  function () {                        
    $newInputField = $("#formattributegrid").children().first().clone();
    if ($newInputField.css('display') == 'none' ) {$newInputField.show();} 
    
    $newInputField.children()[0].children[1].name = "frat__" + attributeTempUniqueID + "__new";
    $newInputField.children()[0].children[1].value="New Attribute Label";
    $newInputField.children()[0].children[2].children[1].name = "frat__" + attributeTempUniqueID + "__order";
    $newInputField.children()[0].children[2].children[1].value = Math.floor((Math.random() * 900) + 1);    
    $("#formattributegrid").append( $newInputField );
        
    var $newButton = $newInputField.find(".del-field-button");
    $newButton.click( function() {
        $(this).parent().parent().parent().remove()
    });
    
    var $newCheckBox = $newInputField.find(".reference-conversion");
    $newCheckBox.change(function(){
        if(this.checked) {
        //Turn on the form select element
        $(this).parent().children()[2].disabled = false;
        $(this).parent().children()[2].classList.remove("offline")
    } else {
        //turn off the form select element
        $(this).parent().children()[2].disabled = true;  
        $(this).parent().children()[2].classList.add("offline")        
    }
    });
    attributeTempUniqueID += 1;
});



$("#add_recordreference").click(  function () {    
    var $clonedReference = $("#formreferencegrid").children().first().clone();    
    if ($clonedReference.css('display') == 'none' ) {$clonedReference.show();} 
        $clonedReference.children()[1].firstChild.name = "frrt__" + attributeTempUniqueID + "__new";
        $clonedReference.children()[1].firstChild.value="New Reference Field";
        $clonedReference.children()[3].firstChild.name = "nfrrt__" + attributeTempUniqueID + "__ref";
        $clonedReference.children()[4].children[1].name = "nfrrt__" + attributeTempUniqueID + "__order";
        $clonedReference.children()[4].children[1].value = Math.floor((Math.random() * 900) + 1);  
        $clonedReference.appendTo("#formreferencegrid");            
    
    var $newButton = $clonedReference.find(".del-reference-button");
    $newButton.click( function() {
        $clonedReference.remove()
    });
    var $newCheckBox = $clonedReference.find(".reference-conversion");
    $newCheckBox.change(function(){
        if(this.checked) {
        //Turn on the form select element
        $(this).parent().children()[2].disabled = false;
        $(this).parent().children()[2].classList.remove("offline")
    } else {
        //turn off the form select element
        $(this).parent().children()[2].disabled = true;  
        $(this).parent().children()[2].classList.add("offline")        
    }
    });    
    attributeTempUniqueID += 1;
});

$("#add_mediatypereference").click(  function () {    
    var $clonedReference = $("#formmediareferencegrid").children().first().clone();    
    if ($clonedReference.css('display') == 'none' ) {$clonedReference.show(); } 
    $clonedReference.children()[1].firstChild.name = "frrt__" + attributeTempUniqueID + "__new";
    $clonedReference.children()[1].firstChild.value="New Reference Field";
    $clonedReference.children()[3].firstChild.name = "nfrrt__" + attributeTempUniqueID + "__ref";
    $clonedReference.children()[4].children[1].name = "nfrrt__" + attributeTempUniqueID + "__order";
    $clonedReference.children()[4].children[1].value = Math.floor((Math.random() * 900) + 1);
    $clonedReference.appendTo("#formmediareferencegrid");            

    var $newButton = $clonedReference.find(".del-reference-button");
    $newButton.click( function() {
        $clonedReference.remove()
    });
    var $newCheckBox = $clonedReference.find(".reference-conversion");
    $newCheckBox.change(function(){
        if(this.checked) {
        //Turn on the form select element
        $(this).parent().children()[2].disabled = false;
        $(this).parent().children()[2].classList.remove("offline")
    } else {
        //turn off the form select element
        $(this).parent().children()[2].disabled = true;  
        $(this).parent().children()[2].classList.add("offline")        
    }
    });        
    attributeTempUniqueID += 1;
});

$(".del-field-button").click(  function() {
        var $inputParent =  $(this).parent().parent();
            if($inputParent.children()[1].readOnly == false){
                $inputParent.children()[1].readOnly = true;
                $inputParent.children()[1].name = $inputParent.children()[1].name + "__DEL";
            } else {
                $inputParent.children()[1].readOnly = false;
                $inputParent.children()[1].name = $inputParent.children()[1].name.slice(0,-5);
            }
});


$(".reference-conversion").change(function(){
        if(this.checked) {
        //Turn on the form select element
        $(this).parent().children()[2].disabled = false;
        $(this).parent().children()[2].classList.remove("offline")
    } else {
        //turn off the form select element
        $(this).parent().children()[2].disabled = true;  
        $(this).parent().children()[2].classList.add("offline")        
    }
});

function enabledReferenceReload(thisCheckBox) {
    console.log(thisCheckBox);
    if(thisCheckBox.checked) {
        //Turn on the form select element
        $(thisCheckBox).parent().children()[2].disabled = false;
        $(thisCheckBox).parent().children()[2].classList.remove("offline")
    } else {
        //turn off the form select element
        $(thisCheckBox).parent().children()[2].disabled = true;  
        $(thisCheckBox).parent().children()[2].classList.add("offline")        
    }
}



$(".del-reference-button").click(  function() {
        //Grab our parent 'row' <div>
        var $inputParent =  $(this).parent().parent();
            if($inputParent.children()[1].childNodes[0].readOnly == false){
                $inputParent.addClass("up-for-deletion");
                $inputParent.children()[1].childNodes[0].readOnly = true;
                $inputParent.children()[3].childNodes[0].disabled = true;
                $inputParent.children()[1].childNodes[0].name = $inputParent.children()[1].childNodes[0].name + "__DEL";
            } else {
                $inputParent.removeClass("up-for-deletion");
                $inputParent.children()[1].childNodes[0].readOnly = false;
                $inputParent.children()[3].childNodes[0].disabled = false;
                $inputParent.children()[1].childNodes[0].name = $inputParent.children()[1].childNodes[0].name.slice(0,-5);
            }
});

$(".del-mediareference-button").click(  function() {
        //Grab our parent 'row' <div>
        var $inputParent =  $(this).parent().parent();
            if($inputParent.children()[1].childNodes[0].readOnly == false){
                $inputParent.addClass("up-for-deletion");
                $inputParent.children()[1].childNodes[0].readOnly = true;
                $inputParent.children()[3].childNodes[0].disabled = true;
                $inputParent.children()[1].childNodes[0].name = $inputParent.children()[1].childNodes[0].name + "__DEL";
            } else {
                $inputParent.removeClass("up-for-deletion");
                $inputParent.children()[1].childNodes[0].readOnly = false;
                $inputParent.children()[3].childNodes[0].disabled = false;
                $inputParent.children()[1].childNodes[0].name = $inputParent.children()[1].childNodes[0].name.slice(0,-5);
            }
});



