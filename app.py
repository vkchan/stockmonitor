from flask import Flask, render_template, request, redirect
import quandl
import pandas as pd
import requests
import datetime
from dateutil.relativedelta import relativedelta
from bokeh.embed import components
from bokeh.models import Range1d
from bokeh.plotting import figure
from bokeh.resources import INLINE
from bokeh.util.browser import view
from bokeh.util.string import encode_utf8
from math import pi

app = Flask(__name__)
app.vars = {}

@app.route('/')
def main():
#    app.vars['quotes_df'] = quandl.get_table("WIKI/PRICES")
    return redirect('/index')

@app.route('/index',methods=['GET','POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    else:
        app.vars['ticker'] = request.form['ticker']
        return redirect('/plot')

@app.route('/plot',methods=['GET','POST'])
def plot():
    try:
        # The chart params allows you to set some of the features of this chart.
        chart_params = {
                'title': app.vars['ticker']+' Price History',
                'colors' : {'up':'Green', 'down': 'Red'},
                'size' : {'height': 500 ,'width': 1000},
        }
        # Download data from Quandl
        end_date = datetime.datetime.now()
        start_date = end_date - relativedelta(years=5)
        df = quandl.Datatable('WIKI/PRICES').data(params={'ticker': app.vars['ticker'], 'date': {'gte': start_date}}).to_pandas()
        # select the tools we want
        TOOLS = 'pan,crosshair,wheel_zoom,box_zoom,reset,save'

        # build our figures
        p = figure(x_axis_type='datetime', tools=TOOLS, plot_width=chart_params['size']['width'], plot_height=chart_params['size']['height'], title = chart_params['title'])
        p.xaxis.major_label_orientation = pi/4
        p.grid.grid_line_alpha=0.3
        mids = (df.open + df.close)/2
        spans = abs(df.close - df.open)
        inc = df.close > df.open
        dec = df.open >= df.close
        half_day_in_ms_width = 12*60*60*1000 # half day in ms
        # Each candle consists of a rectangle and a segment.
        p.segment(df.date, df.high, df.date, df.low, color='black')
        # Add the rectangles of the candles going up in price
        p.rect(df.date[inc], mids[inc], half_day_in_ms_width, spans[inc], fill_color=chart_params['colors']['up'], line_color='black')
        # Add the rectangles of the candles going down in price
        p.rect(df.date[dec], mids[dec], half_day_in_ms_width, spans[dec], fill_color=chart_params['colors']['down'], line_color='black')

        # Generate Javascript, CSS HTML tags
        js_resources = INLINE.render_js()
        css_resources = INLINE.render_css()
        # Generate HTML script and DIV plot component
        script, div = components(p)
        # Render HTML page dynamically with the plot
        return encode_utf8(render_template('embed.html', plot_script=script, plot_div=div, js_resources=js_resources, css_resources=css_resources))
    except Exception as e:
        raise
        return render_template('error.html')

if __name__ == '__main__':
    with open('quandl_api.key') as f:
        quandl.ApiConfig.api_key = f.read().strip()
    app.run(host='0.0.0.0')
