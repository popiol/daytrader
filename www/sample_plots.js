$(document).ready(function(){
    $.ajax({
        url: "${get_sample_quotes_url}?job_name=train_init"
    }).done(function(data){
        for (comp_code in data) {
            $("#plots").append("<h2>"+comp_code+"</h2>")
            id = 'plot_'+comp_code
            $("#plots").append($("<p>").attr('id', id))
            var chart = new ApexCharts(document.querySelector("#"+id), {
				chart: {
					type: 'line',
					width: '42%',
					height: 200
				},
				series: [{
					name: comp_code,
					data: data[comp_code]
				}]
			});
			chart.render();
        }
    })
})