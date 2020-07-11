$(document).ready(function(){
    alert("yfty")
    $.ajax({
        url: "${get_sample_quotes_url}?job_name=train_init"
    }).done(function(data){
        alert(data)
        $("#plots").text(data)
    })
})