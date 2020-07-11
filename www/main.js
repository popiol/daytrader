$(document).ready(function(){
    $.ajax({
        url: "${get_sample_quotes_url}"
    }).done(function(data){
        $("#plots").text(data)
    })
})