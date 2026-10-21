
//This is just a simple AJAX request that tests whether the PDF loads in the iframe viewer--if it isn't found, then
//It provides the <embed></embed> with the attached alternate serve PDF which shows a "No PDF found" message

/*  $clonedEmbed = $('#iframe-container-clone').clone();
 $clonedEmbed.show();

 console.log("Trying before");
// If missing.png is missing, it is replaced by replacement.png
  $clonedEmbed.on('error', function(){
    $(this).attr( "src", $('#iframe-container').attr('altsrc') );
    console.log("Trying to change src value");
  });
  
    $clonedEmbed.appendTo($('#iframe-container').parent());
   */
/*     var http = new XMLHttpRequest();
    http.open('HEAD', $('#iframe-container').attr('src'), false);
    http.send();
    if (http.status == 404){
        $parent = $('#iframe-container').parent()
        $('#iframe-container').remove();
        $parent.append(newElement);
    } */

/* $.get( $('#iframe-container').attr('src')).done(function () {
}).fail(function () {
   $parent = $('#iframe-container').parent()
   $('#iframe-container').remove();
   $parent.append(newElement);
}); */

/* var xhr = $.ajax({
        type: 'HEAD',
        url: $('#iframe-container-clone').attr('src'),
        crossDomain: true,
        success: function () {
            console.log("We got it?   :" + $('#iframe-container-clone').attr('src'));
        },
        error: function () {
            console.log("Unable to connect to secure checkout.  ");
            console.log(xhr.status);
            return false;
        },
        statusCode: {
              404: function (response) {
            console.log('PLEASE GOD');
            
            }
        }    
    }).done(function(data, statusText, xhr){
  console.log(xhr.status);                //200
  console.log(xhr.getAllResponseHeaders()); //Detail header info
}); */


