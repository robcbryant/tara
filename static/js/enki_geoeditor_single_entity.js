
proj4.defs("EPSG:32638","+proj=utm +zone=38 +ellps=WGS84 +datum=WGS84 +units=m +no_defs");

var MAP;

$(document).ready(function(){
   
// ***************************************START OF ALL OPENLAYERS CODE ******************************************* 
   
var prev_el_selector = '#geospatial';
$prevEl = $(prev_el_selector);
$prevEl.prepend( $('<div id="test-map" class="col-md-12"></div>') ); 

   
        var helpText = document.getElementById('gis-help-text-box');      
        
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
            var button_editmode = $('<button class="gis-button gis-button-off" id="gis-button-edit" type="button" title="OFF"><span class="glyphicon glyphicon-pencil"></span></button>')
         
            //Create Vector Shape Type Drop Down
            var vectorselect_form = document.createElement('form');
            vectorselect_form.className = 'gis-button';
            vectorselect_form.id = 'gis-vector-select';
            vectorselect_form.style.marginBottom = '0px';
            var vectorselect_select = document.createElement('select');
            vectorselect_select.id = 'gis-vector-select-type';
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
            var button_selectMode = $('<button class="gis-button gis-button-off" id="gis-button-select" type="button" title="OFF"><span class="glyphicon glyphicon-hand-up"></span></button>')

            
            //Create Delete Button
            var button_delfeature = $('<button class="gis-button gis-button-del" id="gis-button-del-feature" type="button" title="OFF"><span class="glyphicon glyphicon-trash"></span></button>')
           
           //Create load all formtype features button
           var button_addAllLayers = $('<button class="gis-button" style="width: 11%;background-color: #44caa3;" id="gis-button-add-layers" type="button" title="OFF"><span class="glyphicon glyphicon-plus"></span><span class="glyphicon glyphicon-list"></span></button>')
           
            //Self reference variable
            var this_ = this;
            
            
            //Add Listeners/Functions for applicable buttons

            
            var addAllFormTypeLayers = function() {
                var postJSON = [];
                postJSON.push( {name:'formtype_pk', value:CURRENT_FORMTYPE_PK});
                $.ajax({ 
                 url   : API_URLS.get_geo_formtype_layers,
                 type  : "POST",
                 data  : postJSON, // data to be submitted

                 success : function(returnedQuery){
                        console.log(returnedQuery);
                        var geojson_collection;
                        var geojson_object = new ol.format.GeoJSON();
                        try {
                            geojson_object = new ol.format.GeoJSON().readFeatures(returnedQuery);
                            console.log(geojson_object.readProjection);
                            geojson_collection = new ol.Collection(geojson_object);
                        } catch(error) {
                            console.log(error);
                            geojsontest_element.innerHTML = '{"type":"FeatureCollection","features":[]}';
                            geojson_string = JSON.stringify(returnedQuery);
                            geojson_collection = new ol.Collection(new ol.format.GeoJSON().readFeatures(geojson_string));
                            helpText.innerHTML = "Error parsing geoJSON string. Adding Empty geoJSON to field";     
                        }
                        var test = new ol.source.Vector({
                            features: geojson_collection,
                            wrapX: false
                        });


                        var templayer = new ol.layer.Vector({
                            source: test,
                            style: new ol.style.Style({
                                fill: new ol.style.Fill({
                                    color: 'rgba(255, 255, 255, 0.2)'
                                }),
                                stroke: new ol.style.Stroke({
                                    color: '#ffccdd',
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
                        
                        MAP.addLayer(templayer);
                    }
                });    
            };
            

            
            var deleteFeature = function() {
                //Make sure there are features in the selection to delete
                if(typeof selection != 'undefined'){
                    vectorSource.removeFeature(selection.getFeatures().item(0));
                    selection.getFeatures().clear();
                    checkIfOnlyOneVectorDrawn(false)
                    updateFormGeoJSON();
                }
            };
            
            var turnOnSelect = function() {
                if(button_selectMode[0].title == 'OFF'){
                    //Turning Select Mode On
                    button_selectMode[0].className = 'gis-button gis-button-on';
                    button_selectMode[0].title = 'ON';
                    addSelectInteraction();
                    checkForOneActiveCPButton(button_selectMode[0]);
                } else {
                    //Turning Select Mode Off
                    button_selectMode[0].className = 'gis-button gis-button-off';
                    button_selectMode[0].title = 'OFF';
                    MAP.removeInteraction(selection[0]);
                }
            };
            
            var turnOnEditMode = function() {
                if(button_editmode[0].title == 'OFF'){
                    //Turning Edit Mode On
                    button_editmode[0].title = 'ON';
                    button_editmode[0].className = 'gis-button gis-button-on';
                    addDrawInteraction();
                    typeSelect.disabled = false;
                    checkForOneActiveCPButton(button_editmode[0]);

                } else {
                    //Turning Edit Mode Off
                    button_editmode[0].title = 'OFF';
                    button_editmode[0].className = 'gis-button gis-button-off';
                    typeSelect.disabled = true;
                    MAP.removeInteraction(draw);
                }
            };
            
            //listener for a mouse click
            button_delfeature[0].addEventListener('click', deleteFeature, false);
            //This adds a listener for touch devices e.g. phones / tablets
            button_delfeature[0].addEventListener('touchstart', deleteFeature, false);
            
            //listener for a mouse click
            button_selectMode[0].addEventListener('click', turnOnSelect, false);
            //This adds a listener for touch devices e.g. phones / tablets
            button_selectMode[0].addEventListener('touchstart', turnOnSelect, false);
            
            //listener for a mouse click
            button_editmode[0].addEventListener('click', turnOnEditMode, false);
            //This adds a listener for touch devices e.g. phones / tablets
            button_editmode[0].addEventListener('touchstart', turnOnEditMode, false);
            
            //listener for a mouse click
            button_addAllLayers[0].addEventListener('click', addAllFormTypeLayers, false);
            //This adds a listener for touch devices e.g. phones / tablets
            button_addAllLayers[0].addEventListener('touchstart', addAllFormTypeLayers, false);            
            
            //Create container to hold the button in OpenLayers that is addded to the standard controls
            var element = document.createElement('div');
            element.className = 'edit-mode ol-unselectable ol-control';
            element.appendChild(button_editmode[0]);
            element.appendChild(vectorselect_form);
            element.appendChild(button_selectMode[0]);
            element.appendChild(button_delfeature[0]);
            element.appendChild(button_addAllLayers[0]);



            ol.control.Control.call(this, {
                element: element,
                target: options.target
            });

        };
        ol.inherits(app.EditModeControl, ol.control.Control);


        var geojsontest_element =  document.getElementById('id_geojson_string');

        var geojson_string = geojsontest_element.innerHTML;
        console.log(geojson_string);
        geojson_string = geojson_string.replace(/'/g, "\"");

        //var geojson_format = new ol.format.GeoJSON();
        var geojson_collection;
        var geojson_object = new ol.format.GeoJSON();
        try {
            geojson_object = new ol.format.GeoJSON().readFeatures(geojson_string);
            console.log(geojson_object.readProjection);
            geojson_collection = new ol.Collection(geojson_object);
        } catch(error) {
            console.log(error);
            try {
                geojsontest_element.innerHTML = DEFAULT_GEOJSON;
                geojson_collection = new ol.Collection(new ol.format.GeoJSON().readFeatures(geojson_string));
            }catch(err) {
                geojsontest_element.innerHTML = '{"type":"FeatureCollection","features":[]}'
                geojson_collection =  new ol.Collection(new ol.format.GeoJSON().readFeatures('{"type":"FeatureCollection","features":[]}'));
            }

           
            helpText.innerHTML = "Error parsing geoJSON string. Adding Empty geoJSON to field";     
        }
        

        var testProjection = new ol.proj.Projection({
            code: 'EPSG:32638',
            units: 'm'
        });
        
        var vectorSource = new ol.source.Vector({
            features: geojson_collection,
            wrapX: false
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
                    projection: 'EPSG:3857',
                    wrapX: false,
                    attributions: [
                      new ol.Attribution({
                        html: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                      })
                    ],
                    url: 'http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
                  })
           // extent: ol.proj.get("EPSG:4326").getExtent()
                
        });


        
        //This creates the map container and sets it to the div element created with the HTML ID 'test-map'
        MAP = new ol.Map({
            //Add our controls
            controls: ol.control.defaults({
              attributionOptions: /** @type {olx.control.AttributionOptions} */ ({
                collapsible: false
              })
            }).extend([new app.EditModeControl(),  new ol.control.ScaleLine({ units: 'metric'})] ),
            //set the layers to the tile server (raster) and add the initial Vector(shapeFile) layer read from the current Database geojson entry
            layers: [raster,vectorLayer],
            target: 'test-map',
            //This is a default view set that views the whole world from an appropriate zoom level
            view: new ol.View({
              projection: testProjection,
              center: [0,0],
              zoom: 1,
            })
        });

        //This sets the map to start over where the current feature--if it exists--lies.
        if (vectorSource.getFeatures().length > 0){
            MAP.getView().fit(vectorSource.getFeatures()[0].getGeometry(), MAP.getSize());
        } 
        
        var draw; // global so we can remove it later
        var selection; //ditto
        var typeSelect = document.getElementById('gis-vector-select-type');
        
       // var saveButton = document.getElementById('saveGeometryButton');
        //var deleteFeatureButton = document.getElementById('deleteSelectedFeatureButton');
        
        
        //Control Panel Buttons
        var editButton = document.getElementById('gis-button-edit');
        var selectButton = document.getElementById('gis-button-select');
       
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
            MAP.removeInteraction(draw);
            editButton.click();
            checkIfOnlyOneVectorDrawn(true)
            
        }
        
        function addDrawInteraction() {

            draw = new ol.interaction.Draw({
                features: geojson_collection,
                type: /** @type {ol.geom.GeometryType} */ (typeSelect.value)
            });
            draw.on('drawend', drawEnd);
            //This activates AFTER drawend--and since we need the information after the feature has been added to the source, this is a better event listener
            vectorSource.on('addfeature', function (event){
                updateFormGeoJSON();
            })
            MAP.addInteraction(draw);
        }


        //**********Set up all button click events
        typeSelect.onchange = function() {
            MAP.removeInteraction(draw);
            addDrawInteraction();
        };
        

        helpText.onclick = function() {
                helpText.innerHTML = vectorLayer.getSource().getFeatures().length;
        }
        
        function updateFormGeoJSON(){
            var geojsoninstance = new ol.format.GeoJSON();
            var newString = geojsoninstance.writeFeatures(vectorLayer.getSource().getFeatures());
            document.getElementById('id_geojson_string').innerHTML  = newString;   
        }
        
        function checkIfOnlyOneVectorDrawn(drawingFinished) {
            //If there are too many vectors e.g. at least one
            //Don't let the user add any more
            if(vectorLayer.getSource().getFeatures().length >= 1 || drawingFinished){
                //disable the edit button and show alt text message
                editButton.disabled = true;
                helpText.className = 'gis-status-warning';
                helpText.innerHTML = "Only one shape vector allowed per object. In order to add another shape vector. You must delete the current one.";
                return true;
            //Otherwise we have zero vectors so let the user draw one
            } else {
                editButton.disabled = false;
                helpText.className = 'gis-status-okay';
                helpText.innerHTML = "No Problems Detected";
                return false;
            }
        }
        
        function addSelectInteraction(){
            selection = new ol.interaction.Select({
                condition: ol.events.condition.click
            });
            MAP.addInteraction(selection);
        }

        //Functions that run at startup
        checkIfOnlyOneVectorDrawn(false)

        
        
       var highlight;
       
      var displayFeatureInfo = function(pixel) {

        var feature = MAP.forEachFeatureAtPixel(pixel, function(feature) {
          return feature;
        });

        var info = document.getElementById('gis-help-text-box');
        if (feature) {
            var newString = ""
            var props = feature.getProperties();
            Object.keys(props).forEach(function(key){
                
                newString += "<div><span>"+key+"</span>::<span>"+props[key]+"</span></div>"
            });
          info.innerHTML = newString;
        } else {
          info.innerHTML = '&nbsp;';
        }


      };

      MAP.on('pointermove', function(evt) {
        if (evt.dragging) {
          return;
        }
        var pixel = MAP.getEventPixel(evt.originalEvent);
        displayFeatureInfo(pixel);
      });

      MAP.on('click', function(evt) {
        displayFeatureInfo(evt.pixel);
      });        
        
        
        
        
    // ***************************************END OF ALL OPENLAYERS CODE ******************************************* 
});




        
