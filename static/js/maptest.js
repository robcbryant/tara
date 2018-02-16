/*
 * Create a map with a marker.
 * Creating or dragging the marker sets the latitude and longitude values
 * in the input fields.
 */
;(function($) {

  // We'll insert the map after this element:
  //#Suit_form_tabs is the element used in the django-suit library to represent the tab header: This will ensure it is always
  //placed immediately below the tab selection, but stay regardless of tab--this can change in the future
  var prev_el_selector = '#suit_form_tabs';


  /**
   * Create HTML elements, 
  */ 
  function initMap() {
    $prevEl = $(prev_el_selector);
    if ($prevEl.length == 0) {
        // Can't find where to put the map.
        return false;
    } else {
        $prevEl.after( $('<div id="test-map"></div><div id="help-text"></div><button id="deleteSelectedFeatureButton" type="button">Delete Selected Feature</button>') ); 
        return true;
    };

  };



$(document).ready(function(){
    //If the map initialization succeeds, then continue, otherwise do nothing
    if (initMap()){
        
// ***************************************START OF ALL OPENLAYERS CODE ******************************************* 
       
        var helpText = document.getElementById('help-text');
       
        //Setting up some styles--a little clunky right now but can be fixed later
        var sheet = document.styleSheets[0];
        sheet.insertRule(".edit-mode{top: .5em;left: 4.5em; width:200px;}", 1);
        sheet.insertRule(".ol-touch .edit-mode, .ol-touch .select-mode {top: 80px;}", 1);
        sheet.insertRule("#edit-button, #select-button, #vectorselect-form {height:auto; min-height: 1.375em; margin: 5px; padding: 3px}", 1);
        sheet.insertRule("#select-button{top: .5em; width:50px;}", 1);
        sheet.insertRule("#edit-button {float: left; width: 65px;)", 1);
        sheet.insertRule("#vectorselect-form {border: 0px; width:65px;", 1);
        sheet.insertRule("#vectorselect-form select{border: 0px; width:65px;", 1);
        //**********CREATE ANY NEW APPS/BUTTONS FOR OUR OPENLAYERS APP
        /**
        * Define a namespace for the application extensions(custom buttons).
        */
        window.app = {};
        var app = window.app;
        
        
        
        
        var isUserButtonClick = false;
        /**
        * @constructor
        * @extends {ol.control.Control}
        * @param {Object=} opt_options Control options.
        */
        app.EditModeControl = function(opt_options) {

            var options = opt_options || {};

            //Create Edit Mode Button
            var button_editmode = document.createElement('button');
            button_editmode.innerHTML = 'EDIT';
            button_editmode.className = 'btn btn-danger';
            button_editmode.id = 'edit-button';
            button_editmode.type = 'button';
            button_editmode.title = 'OFF';
            
            //Create Vector Shape Type Drop Down
            var vectorselect_form = document.createElement('form');
            vectorselect_form.className = 'form-inline';
            vectorselect_form.id = 'vectorselect-form';
            vectorselect_form.style.marginBottom = '0px';
            var vectorselect_select = document.createElement('select');
            vectorselect_select.id = 'type';
            vectorselect_select.disabled = true;
            var vectorselect_option_point = document.createElement('option');
            vectorselect_option_point.innerHTML = 'Point';
            vectorselect_option_point.value = 'Point'
            var vectorselect_option_polyline = document.createElement('option');
            vectorselect_option_polyline.innerHTML = 'PolyLine';
            vectorselect_option_polyline.value = 'LineString'
            var vectorselect_option_polygon = document.createElement('option');
            vectorselect_option_polygon.innerHTML = 'Polygon';
            vectorselect_option_polygon.value = 'Polygon'
            var vectorselect_option_circle = document.createElement('option');
            vectorselect_option_circle.innerHTML = 'Cicle';
            vectorselect_option_circle.value = 'Circle'
            vectorselect_form.appendChild(vectorselect_select);
            vectorselect_select.appendChild(vectorselect_option_point);
            vectorselect_select.appendChild(vectorselect_option_polyline);
            vectorselect_select.appendChild(vectorselect_option_polygon);
            vectorselect_select.appendChild(vectorselect_option_circle);
            
            //Create Selection Button
            var button_selectMode = document.createElement('button');
            button_selectMode.innerHTML = 'Select';
            button_selectMode.className = 'btn btn-danger';
            button_selectMode.id = 'select-button';
            button_selectMode.type = 'button';
            button_selectMode.title = 'OFF';
            
            //Self reference variable
            var this_ = this;
            
            
            //Add Listeners/Functions for applicable buttons
            var turnOnSelect = function() {
                if(button_selectMode.title == 'OFF'){
                    //Turning Select Mode On
                    button_selectMode.className = 'btn btn-success';
                    button_selectMode.title = 'ON';
                    addSelectInteraction();
                    checkForOneActiveCPButton(button_selectMode);
                } else {
                    //Turning Select Mode Off
                    button_selectMode.className = 'btn btn-danger';
                    button_selectMode.title = 'OFF';
                    map.removeInteraction(selection);
                }
            };
            
            var turnOnEditMode = function() {
                if(button_editmode.title == 'OFF'){
                    //Turning Edit Mode On
                    button_editmode.title = 'ON';
                    button_editmode.className = 'btn btn-success';
                    addDrawInteraction();
                    typeSelect.disabled = false;
                    checkForOneActiveCPButton(button_editmode);

                } else {
                    //Turning Edit Mode Off
                    button_editmode.title = 'OFF';
                    button_editmode.className = 'btn btn-danger';
                    typeSelect.disabled = true;
                    map.removeInteraction(draw);
                }
            };
            
            //listener for a mouse click
            button_selectMode.addEventListener('click', turnOnSelect, false);
            //This adds a listener for touch devices e.g. phones / tablets
            button_selectMode.addEventListener('touchstart', turnOnSelect, false);
            
            //listener for a mouse click
            button_editmode.addEventListener('click', turnOnEditMode, false);
            //This adds a listener for touch devices e.g. phones / tablets
            button_editmode.addEventListener('touchstart', turnOnEditMode, false);
            
            
            
            //Create container to hold the button in OpenLayers that is addded to the standard controls
            var element = document.createElement('div');
            element.className = 'edit-mode ol-unselectable ol-control';
            element.appendChild(button_editmode);
            element.appendChild(button_selectMode);
            element.appendChild(vectorselect_form);


            ol.control.Control.call(this, {
                element: element,
                target: options.target
            });

        };
        ol.inherits(app.EditModeControl, ol.control.Control);


        var geojsontest_element =  document.getElementById('id_geojson_string');

        var geojson_string = geojsontest_element.innerHTML;
        geojson_string = geojson_string.replace(/'/g, "\"");
        var geojson_format = new ol.format.GeoJSON();
        var geojson_collection;
        try {
            geojson_collection = new ol.Collection(new ol.format.GeoJSON().readFeatures(geojson_string));
        } catch(error) {
            geojsontest_element.innerHTML = '{"type":"FeatureCollection","features":[]}';
            geojson_string = geojsontest_element.innerHTML;
            geojson_collection = new ol.Collection(new ol.format.GeoJSON().readFeatures(geojson_string));
            helpText.innerHTML = "Error parsing geoJSON string. Adding Empty geoJSON to field";     
        }
        
      
        var vectorSource = new ol.source.Vector({
            features: geojson_collection
        });

        var vectorLayer = new ol.layer.Vector({
            source: vectorSource,
            style: new ol.style.Style({
                fill: new ol.style.Fill({
                    color: 'rgba(255, 255, 255, 0.2)'
                }),
                stroke: new ol.style.Stroke({
                    color: '#ffcc33',
                    width: 2
                }),
                image: new ol.style.Circle({
                    radius: 7,
                    fill: new ol.style.Fill({
                        color: '#ffcc33'
                    })
                })
            })
        });
        


        //Set up the tile server / Background image raster
        var raster = new ol.layer.Tile({
        //We are going to set the background tileset to ESRI's satellite imagery using this source()
        source: new ol.source.XYZ({
                attributions: [
                  new ol.Attribution({
                    html: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                  })
                ],
                url: 'http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
              })
        });

        
        
        //This creates the map container and sets it to the div element created with the HTML ID 'test-map'
        var map = new ol.Map({
            //Add our controls
            controls: ol.control.defaults({
              attributionOptions: /** @type {olx.control.AttributionOptions} */ ({
                collapsible: false
              })
            }).extend([new app.EditModeControl(),  new ol.control.ScaleLine({ units: 'degrees'})] ),
            //set the layers to the tile server (raster) and add the initial Vector(shapeFile) layer read from the current Database geojson entry
            layers: [raster,vectorLayer],
            target: 'test-map',
            //This is a default view set that views the whole world from an appropriate zoom level
            view: new ol.View({
              center: [0,0],
              zoom: 2,
              projection: 'EPSG:4326'
            })
        });


        var draw; // global so we can remove it later
        var selection; //ditto
        var typeSelect = document.getElementById('type');
        var saveButton = document.getElementById('saveGeometryButton');
        var deleteFeatureButton = document.getElementById('deleteSelectedFeatureButton');
        
        
        //Control Panel Buttons
        var editButton = document.getElementById('edit-button');
        var selectButton = document.getElementById('select-button');
       
        var controlPanel_Buttons = [editButton, selectButton];
       
        function checkForOneActiveCPButton(buttonToKeepOn){
            for(var i =0; i < controlPanel_Buttons.length; i++){
                if(controlPanel_Buttons[i] != buttonToKeepOn){
                    //Turn the button off if not already off
                    if(controlPanel_Buttons[i].title != "OFF"){
                        controlPanel_Buttons[i].click();
                    }
                }
            }
            
        }
       
       
        function drawEnd(){
            map.removeInteraction(draw);
            editButton.click();
            checkIfOnlyOneVectorDrawn(true)
            
        }
        
        function addDrawInteraction() {

            draw = new ol.interaction.Draw({
                features: geojson_collection,
                type: /** @type {ol.geom.GeometryType} */ (typeSelect.value)
            });
            draw.on('drawend', drawEnd);
            //This activates AFTER drawend--and since we need the information after the eature has been added to the source, this is a better event listener
            vectorSource.on('addfeature', function (event){
                updateFormGeoJSON();
            })
            map.addInteraction(draw);
        }


        //**********Set up all button click events
        typeSelect.onchange = function() {
            map.removeInteraction(draw);
            addDrawInteraction();
        };
        
        
        deleteFeatureButton.onclick = function() {
            //alert(selection.getFeatures().item(0));
            vectorSource.removeFeature(selection.getFeatures().item(0));
            selection.getFeatures().clear();
            checkIfOnlyOneVectorDrawn(false)
            updateFormGeoJSON();
        };

        helpText.onclick = function() {
                helpText.innerHTML = vectorLayer.getSource().getFeatures().length;
        }
        
        function updateFormGeoJSON(){
            var newString = geojson_format.writeFeatures(vectorLayer.getSource().getFeatures());
            document.getElementById('id_geojson_string').innerHTML  = newString;   
        }
        
        function checkIfOnlyOneVectorDrawn(drawingFinished) {
            //If there are too many vectors e.g. at least one
            //Don't let the user add any more
            if(vectorLayer.getSource().getFeatures().length >= 1 || drawingFinished){
                //disable the edit button and show alt text message
                editButton.disabled = true;
                helpText.className = 'bg-danger text-danger';
                helpText.innerHTML = "Only one shape vector allowed per object. In order to add another shape vector. You must delete the current one.";
                helpText.style.fontSize = '1.5em';
                helpText.style.height = '2.0em';
                helpText.style.backgroundColor = '#f2dede';
                helpText.style.color = '#dd8e8e';
                return true;
            //Otherwise we have zero vectors so let the user draw one
            } else {
                editButton.disabled = false;
                helpText.className = '';
                helpText.innerHTML = "";
                helpText.style.backgroundColor = '';
                helpText.style.color = '';
                return false;
            }
        }
        
        function addSelectInteraction(){
            selection = new ol.interaction.Select({
                condition: ol.events.condition.click
            });
            map.addInteraction(selection);
        }

        //Functions that run at startup
        checkIfOnlyOneVectorDrawn(false)

    }//End of If successful initialization clause
    // ***************************************END OF ALL OPENLAYERS CODE ******************************************* 
});



  
})(django.jQuery);



