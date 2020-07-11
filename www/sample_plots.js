$(document).ready(function(){
    $.ajax({
        url: "${get_sample_quotes_url}?job_name=train_init"
    }).done(function(data){
        $("#plots").text(data)
    })
})