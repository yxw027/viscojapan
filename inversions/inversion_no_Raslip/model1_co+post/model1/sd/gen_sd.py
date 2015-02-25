import viscojapan as vj

sites = vj.EpochalFileReader('../obs/cumu_post_with_seafloor.h5')['sites']

vj.tsana.GenUniformOnshoreSDWithInfiniteSeafloorSD(
    sites = sites,
    days = range(1621),
    sd_co_hor = 2.,
    sd_co_ver = 2.,
    sd_post_hor = 1.,
    sd_post_ver = 1.,                 
    sd_seafloor = 1.).save('sd_uniform.h5')
    