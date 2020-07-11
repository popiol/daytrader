$(document).ready(function(){
    $.ajax({
        url: "${get_sample_quotes_url}?job_name=train_init"
    }).done(function(data){
        for (comp_code in data) {
            $("#plots").append("<h2>"+comp_code+"</h2>")
            $("#plots").append("<p>"+JSON.stringify(data[comp_code])+"</p>")
        }
    })
})