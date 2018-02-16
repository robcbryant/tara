//####################################################################################################################################
//
//      This script controls the search functions for the FormType. It stores the query as custom JSON to send to the server to unpack
//      --it also handles the controls to add new search terms and queries or delete them
//
//####################################################################################################################################




// Generate 32 char random uuid 
function gen_uuid() {
    var uuid = ""
    for (var i=0; i < 32; i++) {
        uuid += Math.floor(Math.random() * 16).toString(16); 
    }
    return uuid
}

//Progress check variables
var progress_uuid;
var freq = 500;
var errorcount = 0;
var queryFinishedFasterThanAJAXCall = false;
var alreadyHaveStats = false;

 //***************************************************************************************************************
 // These functions handle converting the user form data into a json string to pass to the server through AJAX
 //***************************************************************************************************************


function RecordSearchJSON(){
    //We need to loop through each search in the search form element, and parse out their children to store the
    //json string needed for the server.
    
    var jsonString = '{"query_list":{';
    
    //First let's get a list of all the queries by the "__Q" code
    $allQueries = $("#search-form").find(".__Q");
    //Let's loop through each query found and add it to the json string
    var counter = 1;
    $allQueries.each( function(index, query){
        jsonString += '"query_'+counter+'":{';
        counter += 1;
        //Add the initial values
        jsonString += '"LABEL":"' + $(query).find(".__RTYPE").find("option:selected").html() + '",';
        jsonString += '"RTYPE":"' + $(query).find(".__RTYPE").find(":selected").val() + '",';
        jsonString += '"Q-ANDOR":"'+$(query).find(".__Q-AO").find(":selected").val() + '",';
        //Add any deep searches 
        var deepLabel =$(query).find(".__RTYPE-DEEP").find(":selected").val();
        var deepRtype =$(query).find(".__RTYPE-DEEP").find("option:selected").html();
        //Obviously we only want to do this IF there are deep values
        if (deepLabel != null && deepRtype != null){
            jsonString += '"RTYPE-DEEP":"'+ deepLabel + '",';
            jsonString += '"DEEP-LABEL":"' + deepRtype + '",';
        }
        //Now add all the individual terms
        //We start with the defaut "-A"'s
        jsonString += '"TERMS":[{"T-ANDOR":"' + $(query).find(".__T-AO-A").val() + '",';
        jsonString += '"QCODE":"' + $(query).find(".__QCODE-A").find(":selected").val() + '",';
        jsonString += '"TVAL":"' + $(query).find(".__TVAL-A").val() + '"},';
        $allTerms = $(query).find(".__T");

        $allTerms.each( function (index, term) {
            //Now fill in the rest of the terms if they exist
            jsonString += '{';
            jsonString += '"T-ANDOR":"' + $(term).find(".__T-AO").find(":selected").val() + '",';
            jsonString += '"QCODE":"' + $(term).find(".__QCODE").find(":selected").val() + '",';
            jsonString += '"TVAL":"' + $(term).find(".__TVAL").val() + '"},';
        });
        //Remove the trailing comma from the TERM list--we're already at the end.
        jsonString = jsonString.slice(0,-1);
        //Add the closing bracket for term list
        jsonString += ']';
        //add the end of a query bracket with a comma
        jsonString += '},';
    });
    //Remove the trailing comma from the Query List--we're now at the end
    jsonString = jsonString.slice(0,-1);
    
     //Start loading all the constraints
    $allConstraints = $('#search-form').find(".single-constraint");
    if ($allConstraints.length > 0){
        jsonString += '},"constraint_list":{';
        counter = 1;
        var pcCounter = 1;
        var primary_constraints_string = ',"primary_constraints":{';
        $allConstraints.each( function(index, constraint){
            //If we're dealing with a primary constraint
            if ($(constraint).find(".__PRIMARY").is(':checked')){
                primary_constraints_string += '"pc_'+pcCounter+'":{';
                pcCounter+=1;
                primary_constraints_string += '"LABEL":"' + $(constraint).find(".__RTYPE").find("option:selected").html() + '",';
                primary_constraints_string += '"RTYPE":"'+ $(constraint).find(".__RTYPE").find(":selected").val() + '",';
                primary_constraints_string += '"QCODE":"' + $(constraint).find(".__QCODE").find(":selected").val() + '",'; 
                primary_constraints_string += '"TVAL":"' + $(constraint).find(".__TVAL").val() + '"},';          
            //Otherwise it's a basic constraint
            } else {
                jsonString += '"constraint_'+counter+'":{'; 
                counter += 1;
                //Add the initial values
                jsonString += '"LABEL":"' + $(constraint).find(".__RTYPE").find("option:selected").html() + '",';
                jsonString += '"RTYPE":"'+ $(constraint).find(".__RTYPE").find(":selected").val() + '",';
                jsonString += '"QCODE":"' + $(constraint).find(".__QCODE").find(":selected").val() + '",'; 
                jsonString += '"TVAL":"' + $(constraint).find(".__TVAL").val() + '"},';   
            }
        });
        //Remove the trailing comma from the Constraints List--we're now at the end
        jsonString = jsonString.slice(0,-1); 
    }
    //Close off the constraint or previous term list
    jsonString += "}";
    
    //If we have primary constraints, add them now
    if(pcCounter > 1){
        //Remove the trailing comma from the Constraints List--we're now at the end
        primary_constraints_string = primary_constraints_string.slice(0,-1);    
        //Close off the constraint list
        primary_constraints_string += "}";    
        //Add it to the jsonString
        jsonString += primary_constraints_string;
    }

    
    //Add the final bracket to close the JSON
    jsonString += '}';
    console.log(jsonString);
    var json = jQuery.parseJSON(jsonString);
    console.log(JSON.stringify(json, null, 4));
    
    return jsonString;
    
    
}
 
  //***************************************************************************************
  //This is the actual function that sets up the ajax query to the server
  //***************************************************************************************
$("#search-form").find('form.query-engine').submit(function(e){
    e.preventDefault(); // Keep the form from submitting
    var sForm = $(this);
    var queryJSON = RecordSearchJSON();
    progress_uuid = gen_uuid();
    $sesID = $('#sesID').val();

    var formData = $("#search-form").serializeArray();

    formData.push({name: 'uuid', value: progress_uuid});
    formData.push({name: 'query', value: queryJSON});
    formData.push({name: 'sesID', value: progress_uuid});
    formData.push({name: 'formtype_id', value: $('#FORMTYPE_ID').attr('title')});
    formData.push({name: 'project_id', value: $('#PROJECT_ID').attr('title')});
    console.log(progress_uuid);
    
    showBusyGraphic($('#view-table'));
     
    $.ajax({ 
         url   : API_URLS.run_formtype_query_engine,
         type  : "POST",
         data  : formData, // data to be submitted
         success : function(returnedQuery)
         {
            console.log(returnedQuery);
            queryFinishedFasterThanAJAXCall = true;
            
            var $progressBar = $('#query-progress-bar');
            $progressBar.addClass('progress-bar-success');
            $progressBar.removeClass('progress-bar-striped');
            $progressBar.css('width', 100+'%');
            $progressBar.html(100+'% -- Database Import Finished');
            $progressBar.attr('aria-valuenow', 100); 
            $('#view-table-body').children().first().empty();
            //Setup our initial pagination
            buildPageNavigationBar(returnedQuery.totalResultCount, 1, returnedQuery.currentQuery);
            //Create the new table of the query results
            rebuildQueryResultsTable(returnedQuery);
            removeBusyGraphic();

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
    
    
    
    alreadyHaveStats = false;
    
    
    //Start our progress check
    window.setTimeout(update_progress_info, freq);
 });

 
 
 
 

    

 
  //***************************************************************************************
 // These functions handle building the Chart.js graphs of the query results
 //*************************************************************************************** 

function createNewChart(jsondata){
    //Clear our chart space (we do this because due to the AJAX, the page does not refresh. If the user submits another query, this
    //--container needs to be cleared as a precaution.
     $('#query-graphs').empty()


        $labels = [];
        $counts = [];
        $colors = [];
        
        //--------------------------------
        //For our constraints chart
        //
        
        
        //These represent the color coded bars - these are the query count 'dataset labels' -- each dataset loop grabs a title from here by index 
        //-- this should be the length of the # of queries
        $constraintDataSetLabels = [];
        
        //These represent an axis and are labeled by the constraint term -- they stay the same between each query set
        $constraintLabels = []; 
        //Fill this out by looping through the first query(there is always at least ONE so we use the origin
        //--all queries have the same labels so it won't matter which one we use
        for(c=0;c<jsondata.query_list[0].constraints.length;c++) $constraintLabels.push(jsondata.query_list[0].constraints[c].name + "\n" + jsondata.query_list[0].constraints[c].tval);

        //These represent the counts that match up with the static list of the $constraintDatasetLabels
        $constraintDataSetCounts = [];
        
        //Thesea re the matching dataset colors
        $constraintDataSetColors = [];
        


    //LOOP THROUGH ALL OUR QUERY STATS
    for(q=0; q < jsondata.query_list.length; q++){
        //We're given JSON as the returned data--we need to convert that to a set of lists for the chat js to use
        $mainLabel = "";
        $currentQueryColor = 'rgba(' + (Math.floor(Math.random()*(245-115+1))+115) +','+(Math.floor(Math.random()*(245-115+1))+115)+','+(Math.floor(Math.random()*(255-225+1))+225)+', 1)';
        $thisQuery = jsondata.query_list[q];
        
        $constraintDatasetLabel = $thisQuery.rtype_name;
        
        
        //Setup our labels and counts
        for(t=0;t<$thisQuery.all_terms.length;t++){
            $thisTerm = $thisQuery.all_terms[t];
            //Update the constraint dataset label
            $constraintDatasetLabel += " : " + $thisTerm.TVAL ;
            $qcode = '';
            //Translate the QCODE
            if($thisTerm.QCODE == 0) $qcode = 'contains'; else if($thisTerm.QCODE == 1)$qcode = 'contains(CS)'; else if($thisTerm.QCODE == 2)$qcode = 'exactly'; else if($thisTerm.QCODE == 3)$qcode = 'excludes'; else if($thisTerm.QCODE == 4)$qcode = 'is Null'; 
            if(t == 0)$labels.push($thisQuery.rtype_name + " : "+ $qcode +" :" + $thisTerm.TVAL);
            else $labels.push($thisTerm['T-ANDOR'] + " : " + $thisQuery.rtype_name + " " + $qcode +" : '" + $thisTerm.TVAL+"'");
            $counts.push($thisTerm.count);
            if (jsondata.query_list.length == 1) $colors.push('rgba(' + (Math.floor(Math.random()*(245-115+1))+115) +','+(Math.floor(Math.random()*(245-115+1))+115)+','+(Math.floor(Math.random()*(255-225+1))+225)+', 1)');        
            else $colors.push($currentQueryColor);
        }
        
        if ($thisQuery.ANDOR == 'or' && q != jsondata.query_list.length - 1) {
            $labels.push("Count After Above Additions");
            $counts.push($thisQuery.additions);
            $colors.push('rgba(' + (Math.floor(Math.random()*(245-115+1))+115) +','+(Math.floor(Math.random()*(245-115+1))+115)+','+(Math.floor(Math.random()*(255-225+1))+225)+', 1)');        
        } else if ($thisQuery.ANDOR == 'and') {
            $labels.push("Count After Above Intersection");
            $counts.push($thisQuery.intersections);
            $colors.push('rgba(' + (Math.floor(Math.random()*(245-115+1))+115) +','+(Math.floor(Math.random()*(245-115+1))+115)+','+(Math.floor(Math.random()*(255-225+1))+225)+', 1)');        
        }
        
        //SETUP THE CONSTRAINTS BAR GRAPH
        //We need to loop through each query and find its constraint values
        //the constraint indexes should match exactly with the number of total datasets
        //Add a new dataset label
        $constraintDataSetLabels.push($constraintDatasetLabel);
        $constraintCounts = [];      
        for(c=0;c<$thisQuery.constraints.length;c++){
            $thisConstraint = $thisQuery.constraints[c];
            $constraintCounts.push(parseInt($thisConstraint.count));
        }
        //Now push the final list of counts if they exist
        if ($constraintCounts.length > 0){
            $constraintDataSetCounts.push($constraintCounts);
        }
        //Now add a color for the dataset
        $constraintDataSetColors.push('rgba(' + (Math.floor(Math.random()*(245-115+1))+115) +','+(Math.floor(Math.random()*(245-115+1))+115)+','+(Math.floor(Math.random()*(255-225+1))+225)+', 1)');        
        //Now we'll have a label, and a matching index of a list of counts to use in the graph

    }   
    
    
    
    //-------------------------------------
    //  ADD BASIC GRAPH
    //
        //Label the data
        $mainLabel = jsondata.formtype + " Query ";
        //Add a total count if there is atleast one query with atleast 2 terms
        if(jsondata.query_list.length > 1 || jsondata.query_list[0].all_terms.length > 1){
            $labels.push("Total Count of Matches");
            $counts.push(jsondata.count);
            $colors.push('rgba(' + (Math.floor(Math.random()*(245-115+1))+115) +','+(Math.floor(Math.random()*(245-115+1))+115)+','+(Math.floor(Math.random()*(255-225+1))+225)+', 1)');        
        }
        //Setup a blank chart
        $emptyChartParent = $('<div class="canvas-parent"></div>');
        $emptyChart = $('<canvas id="myChart" width="400" height="400"></canvas>');
        $emptyChartParent.append($emptyChart);
        

                  
                        
        var myBarChart = new Chart( $emptyChart, {
            type: 'horizontalBar',
            data: {
                    labels: $labels,
                    datasets: [{
                        data: $counts,
                        backgroundColor: $colors,
                        label: $mainLabel,
                        }]
                    },
            legend: {
                display: false
            },
            options: {
                title:{display: false},
                barDatasetSpacing : 10,
                barValueSpacing : 10,
                responsive: true,
                maintainAspectRatio: false,
                scales: {

                    yAxes: [{
                        categoryPercentage: 1.0,
                        barPercentage: 1.0,
                        
                        ticks: {
                            beginAtZero:true
                        }
                    }]
                }
            }
            });
            
        //Finally, add the chart to the query graphs container
        $('#query-graphs').append($emptyChartParent);
        
    //-------------------------------------
    //  ADD CONSTRAINTS GRAPH
    //
        //Only make this graph if there are constraints to run
        if ($constraintCounts.length > 0){
            //Label the data
            $mainLabel = jsondata.formtype + " Query ";

            //create our datasets
            $constraintDataSets = [];
            
            for(i = 0; i < $constraintDataSetLabels.length; i++){
                var newDataset = {
                    label: $constraintDataSetLabels[i],
                    backgroundColor: $constraintDataSetColors[i],
                    data: $constraintDataSetCounts[i]
                };
                $constraintDataSets.push(newDataset);
            }
            //Setup a blank chart
            $emptyChartParent = $('<div class="canvas-parent"></div>');
            $emptyChart = $('<canvas id="myChart" width="400" height="400"></canvas>');
            $emptyChartParent.append($emptyChart);
     
            var myBarChart = new Chart( $emptyChart, {
                type: 'horizontalBar',
                data: {
                        labels: $constraintLabels,
                        datasets: $constraintDataSets
                        },
                legend: {
                    display: false
                },
                options: {
                    title:{display: false},
                    barDatasetSpacing : 10,
                    barValueSpacing : 10,
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {

                        yAxes: [{
                            categoryPercentage: 1.0,
                            barPercentage: 1.0,
                            
                            ticks: {
                                beginAtZero:true
                            }
                        }]
                    }
                }
                });
                
            //Finally, add the chart to the query graphs container
            $('#query-graphs').append($emptyChartParent);
        }  
        
    //-------------------------------------
    //  ADD PIE GRAPHs for constraints
    //   

    //This is a little tricky--we need to split up the constraint datasets into separate graphs
    //--Essentially we'll be making as many pie charts as there are constraints
    //--Each pie chart will represent the same index count/color from all constraint datasets
    //--The labels--although a separate one dimensional list--still have the same index
    //--We can keep using the existing constraints labels to use as the "Main Label" of each chart--they will also have the same index
    //--FINALLY: we need to add a new pie chart for each new set of data--(not the same as a dataset)
    
    //This will only draw pie charts if there are constraints ran
    for(i=0;i< $constraintLabels.length;i++){
        
        $thisMainLabel = $constraintLabels[i];
        $colorsList = [];
        $countsList = [];
        $labelsList = [];
        
        //Load the counts, colors, and labels
        //This will be determined by how many queries there were--or the length of a single dataset(any dataset, they're the same size) in ANY constraintDataSet list 
        //We'll use the first dataset in the list for the count   -- index[0]
        for(a=0;a< $constraintDataSetCounts.length;a++){ //For each constraint
            //Now we need to add the [i] index from the constraint loop from each dataset
            $colorsList.push($constraintDataSetColors[a]);
            $countsList.push($constraintDataSetCounts[a][i]);
            $labelsList.push($constraintDataSetLabels[a]);
                
        }
        
        
        //Setup a blank chart
        $emptyChartParent = $('<div class="canvas-parent" style="width:46%;"></div>');
        $emptyChart = $('<canvas id="myChart" width="400" height="400"></canvas>');
        $emptyChartParent.append($emptyChart);
            
        var myPieChart = new Chart( $emptyChart, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: $countsList,
                    backgroundColor: $colorsList,
                    label: $thisMainLabel
                }],
                labels: $labelsList
            },
            options: {
                cutoutPercentage: 40,
                title: {
                    display: true,
                    text:$thisMainLabel
                },
                responsive: true,
                tooltips: {
                    callbacks: {
                        label: function(tooltipItem, data) {
                            var allData = data.datasets[tooltipItem.datasetIndex].data;
                            var tooltipLabel = data.labels[tooltipItem.index];
                            var tooltipData = allData[tooltipItem.index];
                            var total = 0;
                            for (var i in allData) {
                                total += allData[i];
                            }
                            var tooltipPercentage = Math.round((tooltipData / total) * 100);
                            return tooltipLabel + ': ' + tooltipData + ' (' + tooltipPercentage + '%)';
                        }
                    }
                }
            }
        });
        //Finally, add the chart to the query graphs container
        $('#query-graphs').append($emptyChartParent);
    
    
    }
    
    //-------------------------------------
    //  BUILD THE PRIMARY CONSTRAINTS GRAPHS
    //   
    //Only do this if there are p_constraints to be run
    if ('p_constraints' in jsondata){
        console.log
        var datasetsColors = [];
        var allDataSets = [];
        var mainLabels = [];//This is the left side of graph: one for each p constraint--this will match with each data[] array in a datset
        

        var numOfGroups = jsondata.p_constraints[0].data.length;
        
        //Generate our colors
        for(i=0; i < jsondata.p_constraints[0].data.length; i++){
            //go ahead and add our matching colors for the groups--we only need one list of colors because each dataset will share them
            datasetsColors.push('rgba(' + (Math.floor(Math.random()*(245-215+1))+115) +','+(Math.floor(Math.random()*(245-215+1))+115)+','+(Math.floor(Math.random()*(255-225+1))+225)+', 1)');    
            //Create an empty dataset for each item in the array
            allDataSets.push({
                  label: jsondata.p_constraints[0].data[i].data_label,
                  backgroundColor:datasetsColors[i],
                  data: []
            });
        }       
        
        
        
        //Loop through each primary constraint
        for (i = 0; i < jsondata.p_constraints.length; i++){
            var currentConstraint = jsondata.p_constraints[i];
            //Add the label for this section
            mainLabels.push(currentConstraint.name + " " + currentConstraint.tval);
            //loop through this section's data and fill out the datasets as necessary
            //each loop represents a single pass of each dataset--so we have to fill out the data[] values through pushing
            var currentData = [];
            for (a = 0; a < currentConstraint.data.length; a++){
                var currentData = currentConstraint.data[a];
                //Add the count according to group
                allDataSets[a].data.push(parseInt(currentData.count));
            }
        }

        //Setup a blank chart
        var height = "400";
        if(numOfGroups >= 2 && jsondata.p_constraints.length >= 2) height = "1000"; 
        $emptyChartParent = $('<div class="canvas-parent"></div>');
        $emptyChart = $('<canvas id="myChart" width="400" height="'+height+'"></canvas>');
        $emptyChartParent.append($emptyChart);
 
        var myBarChart = new Chart( $emptyChart, {
            type: 'horizontalBar',
            data: {
                    labels: mainLabels,
                    datasets: allDataSets
                    },
            legend: {
                display: false
            },
            options: {
                title:{display: false},
                barDatasetSpacing : 10,
                barValueSpacing : 10,
                responsive: true,
                maintainAspectRatio: false,
                scales: {

                    yAxes: [{
                        categoryPercentage: 1.0,
                        barPercentage: 1.0,
                        
                        ticks: {
                            beginAtZero:true
                        }
                    }]
                }
            }
            });
            
        //Finally, add the chart to the query graphs container
        $('#query-graphs').append($emptyChartParent);
         
        
        
        
        //-----------------------------
        //Now add the pie charts
        


        //Loop through each primary constraint -- each one will be a new pie chart
        for (i = 0; i < jsondata.p_constraints.length; i++){
            var currentConstraint = jsondata.p_constraints[i];        

            var thisMainLabel = mainLabels[i];
            $countsList = [];
            $labelsList = [];
            
            //Load the counts, and labels
            //We'll use the first dataset in the list for the count   -- index[0]
            for(a=0;a < currentConstraint.data.length;a++){ //For each constraint
                $countsList.push(parseInt(currentConstraint.data[a].count));
                $labelsList.push(currentConstraint.data[a].data_label);
                    
            }
            
            
            //Setup a blank chart
              
            var pieHeight = "400";
            if(numOfGroups >= 2 && jsondata.p_constraints.length >= 2) pieHeight = "800"; 
            $emptyChartParent = $('<div class="canvas-parent" style="width:46%;"></div>');
            $emptyChart = $('<canvas id="myChart" width="400" height="'+pieHeight+'"></canvas>');
            $emptyChartParent.append($emptyChart);
                
            var myPieChart = new Chart( $emptyChart, {
                type: 'doughnut',
                data: {
                    datasets: [{
                        data: $countsList,
                        backgroundColor: datasetsColors,
                        label: $thisMainLabel
                    }],
                    labels: $labelsList
                },
                options: {
                    cutoutPercentage: 40,
                    title: {
                        display: true,
                        text: thisMainLabel
                    },
                    responsive: true,
                    tooltips: {
                        callbacks: {
                            label: function(tooltipItem, data) {
                                var allData = data.datasets[tooltipItem.datasetIndex].data;
                                var tooltipLabel = data.labels[tooltipItem.index];
                                var tooltipData = allData[tooltipItem.index];
                                var total = 0;
                                for (var i in allData) {
                                    total += allData[i];
                                }
                                var tooltipPercentage = Math.round((tooltipData / total) * 100);
                                return tooltipLabel + ': ' + tooltipData + ' (' + tooltipPercentage + '%)';
                            }
                        }
                    }
                }
            });
            //Finally, add the chart to the query graphs container
            $('#query-graphs').append($emptyChartParent);
    
    
        }
        
        
        
        
    }
    
    
    
    
    
}
 
 
 //***************************************************************************************
 // These functions handle building out the query form the user
 //***************************************************************************************
 
 
//A counter used to create a unique ID for each search and term
var attributeQueryUniqueID = 1;
var attributeTermUniqueID = 1;

$("#add-query").click( function(){
    
    //Clone the entire hidden Query Element
    $newQuery = $($("#search-form").children().first().children()[3].children[0].children[0]).clone();
    console.log($newQuery);
    //Add it to the DOM
    $($("#search-form").children()[0].children[3].children[0]).append( $newQuery );
    
    //Turn on its visibility
    if ($newQuery.css('display') == 'none' ) {$newQuery.show();} 
    //We also need to add the "__T" class to new terms
    $newQuery.addClass("__Q");
    //Add the functionality to the Delete button
    $delQueryButton = $newQuery.children().first().click( function(){
       //Delete the entire query
       $(this).parent().remove();
    });
    //Add the functionality to the Add Term button
    $addTermButton = $($newQuery.children()[4]).click( function(){
       //Clone the child Term Element of the current Query Element
       $currentQuery = $($(this).parent().children()[3]);
       $newTerm = $currentQuery.children().first().clone();
       //Add it to the Query parent
       $currentQuery.append($newTerm);       
       //Turn on its visibility
       if ($newTerm.css('display') == 'none' ) {$newTerm.show();} 
       //We also need to add the "__T" class to new terms
       $newTerm.addClass("__T");
       //Add the functionality to the delete term button
       $delTermButton = $newTerm.children().first().click( function(){
            //Delete the entire query
            $(this).parent().remove();
        });
    });
    //Find the dom element of the new __RTYPE and add the change listener
    $rtypeSelect = $($newQuery.children()[2].children[1].children[0])
    //Make sure the new query has the deep search listener
    $rtypeSelect.change(addDeepSearchListener);
    
});



$(".and-or-add-btn").click(function (){
       //Clone the child Term Element of the current Query Element
       $currentQuery = $($(this).parent().children()[1]);
       $newTerm = $currentQuery.children().first().clone();
       //Add it to the Query parent
       $currentQuery.append($newTerm);       
       //Turn on its visibility
       if ($newTerm.css('display') == 'none' ) {$newTerm.show();}
       //We also need to add the "__T" class to new terms
       $newTerm.addClass("__T");
       $delTermButton = $newTerm.children().first().click( function(){
            //Delete the entire query
            $(this).parent().remove();
        });       
});

$("#add-constraint").click( function(){

       //Clone the child Term Element of the current Query Element
       $currentConstraint = $($(this).parent().children()[1]);
       $newConstraint = $currentConstraint.children().first().clone();
       //Add it to the Query parent
       $currentConstraint.append($newConstraint);       
       //Turn on its visibility
       if ($newConstraint.children().first().css('display') == 'none' ) {$newConstraint.children().first().show();}

       $delTermButton = $newConstraint.children().first().click( function(){
            //Delete the entire query
            $(this).parent().remove();
        });       
        
});



//Need a function that listens to each FRAT/FRRT selection input. On every 'onchange'
//--if the option selected is a FRRT, then we need to ask an admin AJAX page to send a list of that formtype's attributes and/or reference values
//--Then we'll fill in a a new select box below it with this relation's available attributes to query
//--Finally it needs to be appended to the direct parent of this selection's onchange event that calls for this once the AJAX request returns
//--successfully. If the user selects another non-FRRT term in the parent select, then delete this new child select IF it exists, otherwise do nothing
$('.formtype-select .__RTYPE').change(addDeepSearchListener);

function addDeepSearchListener() {
    console.log( $(this))
    var rtypeCode = $(this).find(":selected").val().split('-');
    var selectParent = this.parentNode;
    var newSelect = selectParent.children[1];
    var rtypeLabel = $(this).find("option:selected").html();
    console.log(newSelect);
    
    //Always remove the last newSelect if it exists--that way if we choose another frrt, it will still remove the old box--or remove i if it's frat--it won't matter
    if (newSelect != null){$(newSelect).remove();}
    if (rtypeCode[0] == 'FRRT'){
       
        var frrt = {"frrt-pk":rtypeCode[1]}
       //Send and AJAX Request
        $.ajax({ 
                 url   : API_URLS.get_rtypes,
                 type  : "POST",
                 data  : frrt, // data to be submitted
                 success : function(returnedQuery)
                 {
                    queryFinishedFasterThanAJAXCall = true;
                    $newSelect = $('<select class="__RTYPE-DEEP"><option value="FORMID-0">'+ rtypeLabel +' ID </option></select>');
                    for (i=0; i< returnedQuery.rtype_list.length; i++){
                        currentRTYPE = returnedQuery.rtype_list[i];
                        $newOption = $('<option value="'+ currentRTYPE.rtype +'-'+ currentRTYPE.pk +'"> : '+  currentRTYPE.label +'</option>');
                        $newSelect.append($newOption);
                    }
                    //Now add the new select to the parent
                    $(selectParent).append($newSelect);
                 },

                // handle a non-successful response
                fail : function(xhr,errmsg,err) {
                    console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
                }
            });      
    } 
    
};





    function update_progress_info() {
        console.log("Trying again?");
        $.getJSON(API_URLS.run_check_progress_query, {'uuid': progress_uuid}, function(data, status){
            console.log("UPDATE PROGRESS FUNCTION");
            console.log(status);
            console.log(data);
            console.log(queryFinishedFasterThanAJAXCall);
            //console.log(status);
            if (data) {
                //console.log("we got data!");
                var $progressBar = $('#query-progress-bar');
                var progress = data.percent_done;
                if (data.is_complete == 'True'){
                    
                } else if( data.percent_done != '0' && queryFinishedFasterThanAJAXCall == false){
                    $progressBar.addClass('progress-bar-striped');
                    $progressBar.removeClass('progress-bar-success');
                    $progressBar.css('width', progress+'%');
                    if (data.SQL != 'True') $progressBar.html(progress+'% -- ' + data.message);
                    else $progressBar.html(progress+'% -- ' + data.current_query + ' out of ' + data.current_term + ' forms -- ' + data.message)
                    $progressBar.attr('aria-valuenow', progress);
                } else {
                    $progressBar.css('width', 0+'%');
                    $progressBar.html(0+'% -- Starting...');
                    $progressBar.attr('aria-valuenow', 0);
                }
                
                if(data.hasOwnProperty('stats') && alreadyHaveStats != true){
                    //Make sure we only do this once
                    alreadyHaveStats = true;
                    //Create the new charts of the query results
                    createNewChart(data.stats);
                }
                if(data.hasOwnProperty('ERROR')){
                    errorcount++;
                } else {
                    errorcount = 0;
                }
                
            }
            if (data.is_complete == 'False' && errorcount <= 5){
                //console.log("restarting window timeout");
                window.setTimeout(update_progress_info, freq);
                //console.log("pretty sure we just set the timer to run another test");
            }
        });
    };












