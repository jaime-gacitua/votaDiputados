from plotly import __version__
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.plotly as py
import plotly.graph_objs as go

import pandas as pd
import html5lib

from urllib.request import urlopen
from bs4 import BeautifulSoup

from IPython.core.display import display, HTML

import time
import re

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



def getVotingMainList(url):
    df = pd.read_html(url)
    return(df[0])

def getDetailLinks(io, rawHtml=False):
  '''
  Gets the links to the voting details, who voted what.

  io: url or html source
  rawHtml: indicates if its url or html source. Default is an url.

  '''
    
  if rawHtml:
    soup = BeautifulSoup(io, "html.parser")


  else:
    # Setup
    conn = urlopen(io)
    html = conn.read()
    # Open page
    soup = BeautifulSoup(html, 'lxml')
  
  # get Links
  links = soup.find_all('a')

  # count and find relevant links
  count = 0
  link_list = []
  for tag in links:
      link = tag.get('href',None)
      if 'detalle.aspx?prmID' in link:
          count = count + 1
          #print(count, link)
          link_list.append(link)
  
  return(link_list)

def getVotingDetails(url):

  '''
  Given a url for a detailed bill, 
  extracts metadata and who voted what.
  '''

  data = pd.read_html(url)
  votingTotals = data[0]

  dfReturn = []
  count = 0
  for vote in votingTotals:
      if votingTotals.loc[0,vote] > 0:
          count = count + 1
          df = pd.DataFrame(data[count].unstack().reset_index(drop=True))
          df['vote'] = vote[3:]
          dfReturn.append(df)
  
  # Read pareos
  try:
    count = count + 1
    df = data[count]
    df1 = breakPareos(df)
    dfReturn.append(df1)

  except:
    pass

  # Combine results
  dfReturn = pd.concat(dfReturn)
  # Formatting
  dfReturn.dropna(inplace=True)
  dfReturn.reset_index(inplace=True, drop=True)
  dfReturn.columns = ['Person', 'vote']
  dfReturn.vote = dfReturn.vote.str.strip()
  dfReturn.Person = dfReturn.Person.str.strip()
  

  # Read date, using beautifulsoup
  conn = urlopen(url)
  html = conn.read()
  soup = BeautifulSoup(html, 'lxml')
  date = soup(text=re.compile(r'(\d\d de .*)\shrs.')).pop().strip()[:-5].strip()
#    date = parseKeyword(soup, 'Fecha')
  dfReturn['date'] = date

#    print(soup.prettify())

    
  return(dfReturn)

def parseKeyword(soup, word):
  '''
  Helps extract metadata from a bill's details
  NOT WORKING FOR NOW
  '''

  regex = word + r':.+\n \s*</strong>\n\s*(.*)'
  print(regex)
  value = soup(text=re.compile(r'Fecha:.*\n\s*</strong>\n\s*(.*)')).pop().strip()
  return(value)
  
def appendMainValues(mainData, detailData):
  '''
  Pasting the bill metadata next to the detailed values
  '''
  for val in mainData.index:
      detailData[val] = mainData[val]
  return(detailData)


def breakPareos(df):
  '''
  Inside the bills details of who voted,
  special script to parse the pareos.
  '''

  dfs = []
  for col in df:
    aux = pd.DataFrame(df[col].str.split(' con ', expand=True).unstack())
    dfs.append(aux)
 #   display(aux)

  dfs = pd.concat(dfs)
  dfs['vote'] = 'Pareo'

  # formateo
  dfs.dropna(inplace=True)
  dfs.reset_index(inplace=True, drop=True)



  #display(dfs)
  return(dfs)

def getPageLinks(page):
  pages = page.find_all("div", { "class" : "pages" })
  for p in pages:
    linkList = p.find_all('li')
    linkOut = []
    for li in linkList:
      anchors = li.find_all('a')
      for a in anchors:
        link = a.get('href')
        linkOut.append(link)

  return(linkOut)

def handleMantencion(browser, soup, nextPage):

  mantencion = None

  # Check if we got to dummy page
  try:
    mantencion = soup(text=re.compile(r'(Sitio Web Temporalmente en Mantención)')).pop().strip()


  except:
    pass

  # Case we got to dummy page
  if mantencion is not None:
    print('Reached Dummy Page: ', mantencion)

    # Go back
    browser.execute_script("window.history.go(-1)")
    time.sleep(30)

    # Try again.
    # Removed. Now we are recording the failed pages.
#    browser.execute_script(nextPage)
#    time.sleep(90)

  else:
    pass


def getNextPage(browser, nextPage, sleepTime, failed):

  if failed:
    print('Extract Failed')
    browser.execute_script("window.history.go(-1)")
    time.sleep(5)

    # get next page

  print('Getting Next Page. Wait: ', sleepTime, 'seconds' )
  browser.execute_script(nextPage)
  time.sleep(sleepTime)

    # get data of next page to check if it's dummy page
#    page = browser.page_source
#    soup = BeautifulSoup(page, "html.parser")

    # handle dummy page
#    handleMantencion(browser, soup, nextPage)



def readPage(counter, browser, votingDataPage, failedPageIndex):
  print('Starting to Read Page Index', str(counter))
  # Get page source and put into beautifulsoup

  page = browser.page_source
  soup = BeautifulSoup(page, "html.parser")

  failed = False

  try:  
    # Start parsing metadata
    voting_main = getVotingMainList(page)
    
    # Collect detailed links
    link_details = getDetailLinks(page, rawHtml=True)

  #    print(len(voting_main.index))
  #    print(len(link_details))

    # Get all details
    #for i in range(1):
    for i in range(len(voting_main.index)):
        #print(i)
        df_details = getVotingDetails('https://www.camara.cl/trabajamos/' + link_details[i])
        df_details_mainData = appendMainValues(voting_main.loc[i,:], df_details)
        # Append to list
        votingDataPage.append(df_details_mainData)

    failed = False

  except:
    failedPageIndex.append(counter)
    failed = True


  return(votingDataPage, failedPageIndex, soup, failed)  


def getNextLink(browser):
  page = browser.page_source
  soup = BeautifulSoup(page, "html.parser")
  pageLinks = getPageLinks(soup)
  nextPage = [l for l in pageLinks if 'LinkButton4' in l]

  if len(nextPage) > 0:
    nextPage = nextPage.pop()
    finished = False

  else:
    nextPage = None
    finished = True

  return(nextPage, finished)


