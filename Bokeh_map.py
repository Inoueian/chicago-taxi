import numpy as np
import scipy
import pandas as pd
import matplotlib.pyplot as plt
import pickle
from bokeh.plotting import figure, save, show
from bokeh.models import (GMapPlot, GMapOptions, ColumnDataSource,
                          Patch, Patches, Range1d, LogColorMapper,
                          HoverTool, PanTool, WheelZoomTool,
                          BoxSelectTool, SaveTool, CustomJS)
from bokeh.embed import components
from bokeh.resources import CDN
from bokeh.layouts import widgetbox, column, row
from bokeh.io import curdoc
from bokeh.palettes import RdYlBu11 as palette
from bokeh.palettes import Spectral6
from bokeh.models import Select, Slider
import ast

#pick only the relevant columns
df_from = pd.read_csv('df_from.csv')
df_to = pd.read_csv('df_to.csv')

df_from['x'] = df_from['x'].apply(ast.literal_eval)
df_from['y'] = df_from['y'].apply(ast.literal_eval)
df_to['x'] = df_to['x'].apply(ast.literal_eval)
df_to['y'] = df_to['y'].apply(ast.literal_eval)

source_from = ColumnDataSource(df_from)
source_to = ColumnDataSource(df_to)

# ### Add Google Maps
google_api_key = 'AIzaSyB7XKt5IZGuihEgsWnnYTl8BPME8qtXgYc'
map_options = GMapOptions(lat=41.88, lng=-87.62, map_type="roadmap", zoom=12)
plot = GMapPlot(x_range=Range1d(), y_range=Range1d(), map_options=map_options)
plot.api_key = google_api_key

color_mapper = LogColorMapper(palette=palette, high=255.)
glyph = Patches(xs='x', ys='y', fill_alpha=0.5,
               fill_color={'field': 'adj_density', 'transform': color_mapper})
gsource = source_from
plot.add_glyph(gsource, glyph)

hover = HoverTool(tooltips=[('census tract', "@geoid10"),
                           ('total', "@adj_count")])

plot.add_tools(hover, PanTool(), WheelZoomTool(), BoxSelectTool(), SaveTool())

dir_select = Select(value='from the Loop', title='direction',
                   options=['from the Loop', 'to the Loop'])
fee_select = Slider(value=0., start=0., end=5., step=1.,
                    title='fee (dollars)')

dir_callback = CustomJS(args=dict(gsource=gsource, source_from=source_from,
                                  source_to=source_to, fee_select=fee_select), code="""
    var dir = cb_obj.value
    var fee = fee_select.value
    var data = gsource.data
    
    adj_count = data['adj_count']
    adj_density = data['adj_density']
    
    if (dir == 'from the Loop') {
        count = source_from.data['count']
        density = source_from.data['density']
        avg = source_from.data['avg']
    } else {
        count = source_to.data['count']
        density = source_to.data['density']
        avg = source_from.data['avg']
    }
    
    for (i = 0; i < count.length; i++) {
        if (data['loop'][i] == 0) {
            adj_count[i] = count[i] * (1. - 0.5 * fee / avg[i])
            adj_density[i] = density[i] * (1. - 0.5 * fee / avg[i])
        }
    }

    gsource.change.emit()
""")

fee_callback = CustomJS(args=dict(gsource=gsource, source_from=source_from,
                                  source_to=source_to, dir_select=dir_select), code="""
    var dir = dir_select.value
    var fee = cb_obj.value
    var data = gsource.data
    
    adj_count = data['adj_count']
    adj_density = data['adj_density']
    
    if (dir == 'from the Loop') {
        count = source_from.data['count']
        density = source_from.data['density']
        avg = source_from.data['avg']
    } else {
        count = source_to.data['count']
        density = source_to.data['density']
        avg = source_from.data['avg']
    }
    
    for (i = 0; i < count.length; i++) {
        if (data['loop'][i] == 0) {
            adj_count[i] = count[i] * (1. - (0.5 * fee) / avg[i])
            adj_density[i] = density[i] * (1. - (0.5 * fee) / avg[i])
        }
    }

    gsource.change.emit()
""")

dir_select.js_on_change('value', dir_callback)
fee_select.js_on_change('value', fee_callback)

inputs = widgetbox(dir_select, fee_select)
#curdoc().add_root(row(inputs, plot))

script, div = components(row(inputs, plot))
with open('bokeh_map.txt', 'w') as f:
    f.write(script)
    f.write(div)
