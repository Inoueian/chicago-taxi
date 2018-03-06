import numpy as np
import pandas as pd
from bokeh.plotting import figure, show
from bokeh.models import (ColumnDataSource, HoverTool, PanTool,
                          WheelZoomTool, BoxSelectTool, SaveTool, CustomJS)
from bokeh.models.widgets import Select, Slider
from bokeh.embed import components
from bokeh.io import curdoc
from bokeh.layouts import widgetbox, column, row
from bokeh.palettes import Spectral6

df_ratios = pd.read_csv('Data/Ratios.csv')
df_ratios['census_tract'] = df_ratios['census_tract'].apply(str)
df_ratios = df_ratios.set_index('census_tract')

# We need average fares for the 36 major census tracts. Ignore the rest for the purpose of this plot. The other tracts make up less than 10% of all rides.
df_avg = pd.read_csv('GetAvg/stats_3.csv')

# Put the major census tracts in 4 distinct groups.
NORTH = ['17031071400', '17031071500', '17031080100', '17031080201',
         '17031080202', '17031080300', '17031081000', '17031081100',
         '17031081201', '17031081202', '17031081300', '17031081401',
         '17031081402', '17031081403', '17031081500', '17031081600',
         '17031081700', '17031081800', '17031842200']
WEST = ['17031243500', '17031280100', '17031281900', '17031833000',
        '17031833100', '17031838100', '17031841900', '17031842300',
        '17031980000']
LOOP = ['17031320100', '17031320400', '17031320600', '17031839000',
        '17031839100']
SOUTH =['17031330100', '17031841000', '17031980100']

def findDirection(row):
    """Assign group to each census tract."""
    tract = str(int(row['census_tract']))
    if tract in NORTH:
        return 'N'
    elif tract in WEST:
        return 'W'
    elif tract in LOOP:
        return 'L'
    else:
        return 'S'

df_avg['region'] = df_avg.apply(findDirection, axis=1)
df_avg['census_tract'] = df_avg['census_tract'].apply(str)
df_avg = df_avg.join(df_ratios[['ratio_from', 'ratio_to']], on='census_tract')

avg_source = ColumnDataSource(df_avg)

def traffic(region, fee=0, elasticity=0.5):
    if region == 'L': #no decrease for this
        return tuple(df_avg[df_avg['region']=='L'][['ratio_from', 'ratio_to']].sum())
    array = df_avg[df_avg['region']==region][['avg', 'ratio_from', 'ratio_to']].values
    total_from = 0
    total_to = 0
    for avg, ratio_from, ratio_to in array:
        #calculate the ratio of traffic decrease
        ratio = elasticity * (fee / avg)
        total_from += ratio_from * (1 - ratio)
        total_to += ratio_to * (1 - ratio)
    return total_from, total_to

total_from = sum([traffic(region)[0] for region in ['N', 'W', 'L', 'S']])
total_to = sum([traffic(region)[1] for region in ['N', 'W', 'L', 'S']])

def total_traffic(fee=0, elasticity=0.5):
    value_from = sum([traffic(region, fee, elasticity)[0]
                      for region in ['N', 'W', 'L', 'S']])
    value_to = sum([traffic(region, fee, elasticity)[1]
                      for region in ['N', 'W', 'L', 'S']])
    return value_from / total_from, value_to / total_to

TOOLS = "pan, box_zoom, wheel_zoom, reset, save"

#set up initial data
regions = ['N', 'W', 'L', 'S']
direction_dict = {'from the Loop': 0,
                  'to the Loop': 1}
direction0 = 'from the Loop'
elasticity0 = 0.5
x = np.linspace(0, 5, 51)
df_line = pd.DataFrame(x, columns=['x'])
df_line['total'] = df_line['x'].apply(lambda x: total_traffic(x, elasticity0)[direction_dict[direction0]])
for region in regions:
    df_line[region] = df_line['x'].apply(lambda x: traffic(region, x, elasticity0)[direction_dict[direction0]])
source = ColumnDataSource(df_line)

#set up plot
colorwheel = Spectral6
p_line = figure(tools=TOOLS, title="Taxi traffic reduction by region",
                x_range=(0, 5), y_range=(0, 1),
                x_axis_label="fee (dollars)",
                y_axis_label="proportion of taxi rides")
p_line.line('x', 'total', source=source, line_width=2,
            line_color=colorwheel[0], legend='Total')
p_line.line('x', 'N', source=source, line_width=2,
            line_color=colorwheel[1], legend='North')
p_line.line('x', 'W', source=source, line_width=2,
            line_color=colorwheel[2], legend='West')
p_line.line('x', 'S', source=source, line_width=2,
            line_color=colorwheel[3], legend='South')
p_line.line('x', 'L', source=source, line_width=2,
            line_color=colorwheel[4], legend='Loop')
p_line.legend
hover_line = HoverTool(tooltips=[("(x,y)", "($x, $y)")])    
p_line.add_tools(hover_line)

dir_select = Select(value='from the Loop', title='direction',
                   options=['from the Loop', 'to the Loop'])
elas_select = Slider(value=0.5, start=0., end=1., step=0.1,
                    title='price elasticity')

dir_callback = CustomJS(args=dict(source=source, avg_source=avg_source,
                                 elas_select=elas_select), code="""
    var data = source.data
    var dir = cb_obj.value
    var elas = elas_select.value
    var avg_data = avg_source.data

    regions = avg_data['region']
    avgs = avg_data['avg']
    if (dir == 'from the Loop') {
        var ratios = avg_data['ratio_from']
    } else {
        var ratios = avg_data['ratio_to']
    }
    sum = ratios.reduce((a, b) => a + b, 0)

    x = data['x']
    total = data['total']
    N = data['N']
    W = data['W']
    S = data['S']
    L = data['L']

    for (i = 0; i < x.length; i++) {
        N[i] = 0
        W[i] = 0
        S[i] = 0
        L[i] = 0
        for (j = 0; j < regions.length; j++) {
            if (regions[j] == 'N') {
                N[i] += ratios[j] * (1 - elas * x[i] / avgs[j])
            } else if (regions[j] == 'W') {
                W[i] += ratios[j] * (1 - elas * x[i] / avgs[j])
            } else if (regions[j] == 'S') {
                S[i] += ratios[j] * (1 - elas * x[i] / avgs[j])
            } else {
                L[i] += ratios[j]
            }
        }
        N[i] = N[i] / sum
        W[i] = W[i] / sum
        S[i] = S[i] / sum
        L[i] = L[i] / sum
        total[i] = N[i] + W[i] + S[i] + L[i]
    }
    source.change.emit()
""")

elas_callback = CustomJS(args=dict(source=source, avg_source=avg_source,
                              dir_select=dir_select), code="""
    var data = source.data
    var avg_data = avg_source.data
    var dir = dir_select.value
    var elas = cb_obj.value
    
    regions = avg_data['region']
    avgs = avg_data['avg']
    if (dir == 'from the Loop') {
        var ratios = avg_data['ratio_from']
    } else {
        var ratios = avg_data['ratio_to']
    }
    sum = ratios.reduce((a, b) => a + b, 0)
    
    x = data['x']
    total = data['total']
    N = data['N']
    W = data['W']
    S = data['S']
    L = data['L']
    
    for (i = 0; i < x.length; i++) {
        N[i] = 0
        W[i] = 0
        S[i] = 0
        L[i] = 0
        for (j = 0; j < regions.length; j++) {
            if (regions[j] == 'N') {
                N[i] += ratios[j] * (1 - elas * x[i] / avgs[j])
            } else if (regions[j] == 'W') {
                W[i] += ratios[j] * (1 - elas * x[i] / avgs[j])
            } else if (regions[j] == 'S') {
                S[i] += ratios[j] * (1 - elas * x[i] / avgs[j])
            } else {
                L[i] += ratios[j]
            }
        }
        N[i] = N[i] / sum
        W[i] = W[i] / sum
        S[i] = S[i] / sum
        L[i] = L[i] / sum
        total[i] = N[i] + W[i] + S[i] + L[i]
    }
    source.change.emit()
""")

dir_select.js_on_change('value', dir_callback)
elas_select.js_on_change('value', elas_callback)

inputs = widgetbox(dir_select, elas_select)
#curdoc().add_root(row(inputs, p_line))

script, div = components(row(inputs, p_line))
print(script)
print(div)
