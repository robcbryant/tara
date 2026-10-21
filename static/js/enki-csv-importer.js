  /*
    This JS is used to read a selected CSV file the user provides, and parse it out into a list
    of fields for the user to fill out to import the data into the database.

    TODO: I worry that the POST data might still be too large at times for the WSGI process--we'll see.  
  */
  
    
    var PARSED_JSON = "";
  
  
  
    // Generate 32 char random uuid 
    function gen_uuid() {
        var uuid = ""
        for (var i=0; i < 32; i++) {
            uuid += Math.floor(Math.random() * 16).toString(16); 
        }
        return uuid
    }
    
    $current_file_row_count = 0;
    $uuid = gen_uuid();
    var freq = 1000;

    var avgTimeSum = 0;
    var avgTimeCount = 0;
 


 
    $('#new_form_type').on('submit', function(event){
        event.preventDefault();
        console.log("form submitted!")  // sanity check
        var data = $('#new_form_type').serializeArray();
        $uuid = gen_uuid(); 
        data.push({name: 'uuid', value: $uuid});
        data.push({name: 'row_total', value: $current_file_row_count});
        data.push({name: 'csv_json', value: PARSED_JSON});
        //console.log(PARSED_JSON);
        check_progress(data, $uuid);
        
        
        
    });

    
    
// Add upload progress for multipart forms.
function check_progress(data,uuid) {
    var csv_data = data;
    $.ajax({
            url : API_URLS.import_formtype, // the endpoint
            type : "POST", // http method
            data :  csv_data, // data sent with the post request

            // handle a successful response
            success : function(json) {
              
                //console.log(json); // log the returned json to the console
                console.log("success"); // another sanity check
            }
    });
    
    function update_progress_info() {
        var progress_data = {"uuid": uuid};
        console.log (progress_data);
        $.ajax({
            url : API_URLS.run_check_progress, // the endpoint
            type : "POST", // http method
            data :  progress_data, // data sent with the post request

            // handle a successful response
            success : function(json) {
                console.log(json);
                if (json) {
                    console.log(json);
                    var $progressBar = $('#file-read-progress-bar');
                    var progress = Math.round(parseInt(json.row_index) / parseInt(json.row_total) * 100);
                    avgTimeSum += parseFloat(json.row_timer);
                    avgTimeCount++;
                    var approxTimeLeft = Math.round((json.row_total - json.row_index)*(avgTimeSum/avgTimeCount));
                    //Only update the progress bar if the row doesn't = 0
                    if (json.is_complete == 'True'){
                        $progressBar.addClass('progress-bar-success');
                        $progressBar.removeClass('progress-bar-striped');
                        $progressBar.css('width', 100+'%');
                        $progressBar.html(100+'% -- Database Import Finished');
                        $progressBar.attr('aria-valuenow', 100);                   
                        //window.location.reload();
                    } else if( json.row_index != '0'){
                        //console.log("row index larger than 0");
                        $progressBar.addClass('progress-bar-striped');
                        $progressBar.removeClass('progress-bar-success');
                        $progressBar.css('width', progress+'%');
                        $progressBar.html(progress+'% -- Approximate Time Left: ' + approxTimeLeft + " seconds");
                        $progressBar.attr('aria-valuenow', progress);
                    } else {
                        $progressBar.css('width', 0+'%');
                        $progressBar.html(0+'% -- Approximate Time Left: Calculating...');
                        $progressBar.attr('aria-valuenow', 0);
                    }
                }
                if (json.is_complete == 'False'){
                    //console.log("restarting window timeout");
                    window.setTimeout(update_progress_info, freq);
                    //console.log("pretty sure we just set the timer to run another test");
                } else if (json.is_complete == 'True'){
                    location.reload();
                }
            }
        });
    }
    window.setTimeout(update_progress_info, freq);
   
};  
  
    var headerList = [];
    var workerURI = $('#worker-uri').attr('name');
    $progressBar = $('#file-read-progress-bar');
    $allCheckBoxes = [];
    $allHierarchyCheckBoxes = [];
    $infoBox = $('#info-message');
    console.log(workerURI);
    
    var myWorker = new Worker(workerURI);
   
        myWorker.onmessage = function (message) {
            //console.log(e.data + "<!----");
            if (message.data[0] == -1){
                var headerList = message.data[1];
                for (var i = 0; i < headerList.length; i++){
                    addNewImporterRow(headerList[i], i);
                }  
                //update progress bar to completed
                $progressBar.removeClass('progress-bar-striped');
                $progressBar.addClass('progress-bar-finished');
                $progressBar.html('Successful Load!'); 
                //Update Info panel with results
                $infoBox.html("# of Rows Parsed: " + message.data[2] + "  -- File Size: "+ (message.data[3]/1024) + "kb");
                $infoBox.parent().show();
                $current_file_row_count = parseInt(message.data[2])
                $('#importer-header').show();
                //Update hidden jsonstring for POST to server
                PARSED_JSON = message.data[4];
                
               
                
                //Finally remove the CSV file from the input so it doesn't attach it to POST--we don't need it anymore
                $('#csv').val("");
                //console.log(message.data[4]);
            } else {
                $progressBar.css('width', message.data[0]+'%');
                $progressBar.html(message.data[0]+'%');
                $progressBar.attr('aria-valuenow', message.data[0]);
            }
    }
    
    function readCSVFile(evt) {
        $mainForm = $('#form-type-importer');
        $formRow = $('#cloner');
        $progressBar = $('#file-read-progress-bar');
        //First remove all the child nodes from the form--this is in case they try
        //Two different files without submitting--it will remove the old children
        $mainForm.empty();
        //Reset the progress bar
        $progressBar.addClass('progress-bar-striped');
        $progressBar.removeClass('progress-bar-success');
        $progressBar.css('width', '0%');
        $progressBar.attr('aria-valuenow', 0);
        //Reset Info panel 
        $infoBox.html("Tracking....");
        //Turn on the Form Type Title Input
        $('#read-csv-results').show();
        $('#form-type-title').show();
        $('#form-type-importer').show();
        $('#submit-button').show();

        myWorker.postMessage(evt.target.files[0]);
    }

    function addNewImporterRow(key, counter){

        var validatedRow = key.replace(/_/g, "-");
        var $clonedReference = $("#clone").clone();
        if(counter % 2 == 0){ $clonedReference.addClass("colored-row")}
        
        if ($clonedReference.css('display') == 'none' ) {
            $clonedReference.show();
        } 
        $clonedReference.find(".clone-name").val(validatedRow);
        $clonedReference.find(".clone-name").attr('name', 'record__' +validatedRow+ '__name');
        $clonedReference.find(".clone-isprimary").attr('name', 'record__' +validatedRow+ '__ismainID');
        $clonedReference.find(".clone-ishierarchy").attr('name', 'record__' +validatedRow+ '__ishierarchy');
        $clonedReference.find(".clone-select").attr('name', 'record__' +validatedRow+ '__reftype');
        $clonedReference.find(".clone-isreference").attr('name', 'record__' +validatedRow+ '__isreference');
        //Auto check the first check box
        if (counter == 0) { $clonedReference.find(".clone-isprimary").attr('checked', true); }
        //Add the checkbox listeners for both isprimary check boxes and ishierarchy checkboxes. 
        //--We have to do this because the checkboxes can't share the same name in the form
        //--and we need them all to turn off if one is selected. Only one choice is allowed per formtype
        $allCheckBoxes.push($clonedReference.find(".clone-isprimary"));
        $clonedReference.find(".clone-isprimary").change(function () {
            //ONLY if 'checking' the box
            if(this.checked) {
                //Loop through all the checkboxes except for this one and turn them off
                for (var i = 0; i < $allCheckBoxes.length; i++){
                   //console.log(this.name + "   :   " + $allCheckBoxes[i].prop('name') );
                    if (this.name != $allCheckBoxes[i].prop('name')){
                        $allCheckBoxes[i].prop('checked', false);
                    }
                }
            }
        });
        $allHierarchyCheckBoxes.push($clonedReference.find(".clone-ishierarchy"));
        $clonedReference.find(".clone-ishierarchy").change(function () {
            //ONLY if 'checking' the box
            if(this.checked) {
                //Loop through all the checkboxes except for this one and turn them off
                for (var i = 0; i < $allHierarchyCheckBoxes.length; i++){
                   //console.log(this.name + "   :   " + $allCheckBoxes[i].prop('name') );
                    if (this.name != $allHierarchyCheckBoxes[i].prop('name')){
                        $allHierarchyCheckBoxes[i].prop('checked', false);
                    }
                }
            }
        });
        
        $mainForm.append($clonedReference)
    }
    
    document.getElementById('csv').addEventListener('change', readCSVFile, false);
    
  



