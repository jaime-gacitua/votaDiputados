from plotly import __version__
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
init_notebook_mode() # run at the start of every ipython notebook
import plotly.plotly as py
import plotly.graph_objs as go


def drawHeatmap(df, date):
    trace = go.Heatmap(z=df.values,
                       x=df.columns,
                       y=df.index,
    #                   zmin=-3.0,
    #                   zmax=1.0,
                       showscale=False,
                       colorscale=[[0,'rgb(166,206,227)'],
                                   [0.25,'rgb(31,120,180)'],
                                   [0.5, 'rgb(227,26,28)'],
                                   [1.0, 'rgb(51,160,44)']],
                      xgap=2,
                      ygap=2)
    data=[trace]
    layout = go.Layout(title='Camara De Diputados - Ultimas 20 Votaciones <br>' + 
                       date + ' Fuente: http://www.camara.cl',
                       width=1200,
                       height=2000,
                       margin=go.Margin(l=300,
                                       r=50,
                                       b=300),
                       showlegend=False,
                       xaxis=dict(tickangle=70),
                       yaxis=dict(dtick=1)

                      )
    figure = go.Figure(data=data, layout=layout)
    iplot(figure)