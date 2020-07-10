module "sample_plots_html" {
    source = "./www"
    file_name = "sample_plots.html"
    inp = local.common_inputs
}
