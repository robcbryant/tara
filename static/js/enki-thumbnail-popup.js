

//All we need to do is look for a set class name of image--when we find it, we need to attach a 'hover' event.
//--When the user's cursor hovers over the image element, it will auto generate a new div with the image as the background
//--that will remain on the screen until the user's mouse no longer hovers over the new div--then it will be destroyed.
//This new div element will obviously be larger--the point is to hover over the thumbnail to expand it to easier viewing.


function updateImagePopup(){
     
    $('.enki-img-popup').click( function() {
        //Make sure this el
        //Only make a popup if there isn't one already--otherwise we might get duplicates for some reason

        if ($('.IMG-POPUP').length == 0 && !$(this).hasClass('IMG-404')){
            //duplicate this img element, 
            $newImg = $(this).clone();
            //make it a higher z-level index
            $newImg.css('position', 'absolute');
            $newImg.css('z-index', 100);
            //Set the top of the iamge to the top of the current window view--scrolltop() gets the current
            // top if the user's scrolled down at all
            $newImg.css('top', $(document).scrollTop()+'px');
            //set the width and height to 75% of the screen width
            console.log($(window).width() + "  :  " + $(window).height());

                var newWidth =  parseInt(($(window).width() / 100.0) * 75) + "px"
                $newImg.css('width', newWidth);

            //set it to the center of the page
            console.log($newImg[0].getBoundingClientRect().width );
            var newLeft = parseInt(($(window).width()/2.0) - ($newImg.width()/2.0)) + "px";
            //var newLeft = $(this).offset().left - 10;
            $newImg.css('left', newLeft);
            //add a custom class so we can id it later
            $newImg.addClass('IMG-POPUP');
            $newImg.removeClass('enki-img-popup');
            
            //add it to the body 
            $('body').append($newImg);

            //create a transparent background behind the image to fill the screen
            //We do this after adding the image because the image may increase the documeents height
            $imgBG = $('<div class=""pop-up-bg></div>');
            $imgBG.css('width', $(document).width());
            $imgBG.css('height',$(document).height());
            $imgBG.addClass('img-popup-bg');            
            $('body').append($imgBG);
            
            //set the popup to destroy when clicked
            $newImg.click(function() {
               //Let's add additional protection by making sure we remove ALL instances of .IMG-POPUP in case duplicates 
               //were still made -- redudancy is beauty.
              $('.IMG-POPUP').remove();
              $('.img-popup-bg').remove();                
            });
            
            //set the element to destroy itself when the user stops hovering a mouse cursor over it
            $imgBG.hover(function() {
               //Let's add additional protection by making sure we remove ALL instances of .IMG-POPUP in case duplicates 
               //were still made -- redudancy is beauty.
              $('.IMG-POPUP').remove();
              $('.img-popup-bg').remove();
           });
        }   
        
    });
}

//Go ahead and activate this function for the first time the page loads
updateImagePopup();

//Error handler for images
function imgError(image) {
    image.onerror = "";
    image.src = "/static/site-images/no-thumb-file.png";
    return true;
}