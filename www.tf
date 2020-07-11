module "sample_plots_html" {
    source = "./www"
    file_name = "sample_plots.html"
    inp = local.common_inputs
}

module "sample_plots_js" {
    source = "./www"
    file_name = "sample_plots.js"
    vars = {
        get_sample_quotes_url = module.get_sample_quotes.invoke_url
    }
    inp = local.common_inputs
}
