point_lyr = QgsProject.instance().mapLayersByName('Brown_Marmorated_Stink_Bug - (Halyomorpha_halys) (1999_2023) — PointLayer')[0]
raster_lyr = QgsProject.instance().mapLayersByName('023_30m_cdls')[0]


params = {
    'COLUMN_PREFIX' : 'fid',
    'INPUT' : point_lyr,
    'OUTPUT' : 'crop',
    'RASTERCOPY': raster_lyr

}

result = processing.run('native:rastersampling', params)

result_lyr = result['OUTPUT']
QgsProject.instance().addMapLayer(result_lyr)