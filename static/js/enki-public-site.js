
var elements = $('.side-bar').children();


for (i=0; i< elements.length ; i++) {
    var currentElement = $(elements.get(i));
    console.log(currentElement);
    if (currentElement.hasClass('form-type-group-title')){
        try{
            console.log(elements.get(i+1));
            console.log($(elements.get(i+1)).hasClass('form-type-group-title'));
            if ($(elements.get(i+1)).hasClass('form-type-group-title') || elements.get(i+1) == null){
                console.log('Deleting the damn element...wtf');
                //then delete this formtype group
                currentElement.remove();
            }
        } catch {
            console.log('deleting from a catch error')
            //This means the next element doesn't exist so there are no children formtypes--so delete the group
            currentElement.remove();
        }
    }
}


if ($('.side-bar').children().length > 0){ $('.side-bar').show();} else { console.log('WTF'); $('#main .main').css({'margin':'auto','position':'relative','left':'0','top':'0'}) }



$('.menu-container').hover( 
    //Mouse Enters Hover
    function(){
        $(this).find('.page-list').show();
        $(this).find('.title').addClass('active-title');
    }, 
    //Mouse Leaves Hover
    function(){
        //set the element to hide itself when the user stops hovering a mouse cursor over it
       $(this).find('.page-list').hide();
       $(this).find('.title').removeClass('active-title');
    }
);

