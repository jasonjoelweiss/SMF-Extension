#  smf.py - Pyuno/LO bridge to implement new functions for LibreOffice Calc
#
#  Copyright (c) 2013 David Capron (drbluesman@yahoo.com)
#
#  license: GNU LGPL
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#
import os, sys, inspect, csv
#Try/except is for LibreOffice Python3.x vs. OpenOffice Python2.x.
#Path appends are for testing in Python shell.
try:
    from urllib.request import Request, urlopen
    from urllib.error import URLError
#    sys.path.append('/usr/lib/libreoffice/program')
except ImportError:
    from urllib2 import Request, urlopen, URLError
#     sys.path.append('/usr/lib/openoffice4/program')
#     if getattr(os.environ, 'URE_BOOTSTRAP', None) is None:
#         os.environ['URE_BOOTSTRAP'] = "vnd.sun.star.pathname:/home/dave/Desktop/aooinstall/en-US/DEBS/install/opt/openoffice4/program/fundamentalrc"
from codecs import iterdecode
import unohelper
from com.smf.ticker.getinfo import XSmf
# Add current directory to path to import yahoo, morningstar and advfn modules
cmd_folder = os.path.realpath(os.path.abspath
                              (os.path.split(inspect.getfile
                                             ( inspect.currentframe() ))[0]))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)
import yahoo
import morningstar
import advfn

class SmfImpl(unohelper.Base, XSmf ):
    """Define the main class for the SMF extension """    
    def __init__( self, ctx ):
        self.ctx = ctx
        self.nyse_list = []
        self.nasdaq_list = []
        self.amex_list = []
        self.exchange_flag = ['0', '0', '0']
        self.yahoo_flag = ['0', '']
        self.keyratio_flag = ['0', '']
        self.financial_flag = ['0', '']
        self.qfinancial_flag = ['0', '']
        #Setup for url calls to ADVFN in 5 5yr chunks, most recent year first.
        self.advfn_start = [21, 16, 11, 6, 1]
        self.advfn_flag = [0, '']
        self.advfn_data = []
    #Following functions are called and mapped by LO through the Xsmf.rdb file.
    def getYahoo( self, ticker, datacode ):
        try:
            x = float(yahoo.fetch_data(self, ticker, datacode))
        except:
            x = yahoo.fetch_data(self, ticker, datacode)
        return x

    def getMorningKey( self, ticker, datacode):
        try:
            x = float(morningstar.fetch_keyratios(self, ticker, datacode))
        except:
            x = morningstar.fetch_keyratios(self, ticker, datacode)
        return x
    
    def getMorningFin( self, ticker, datacode):
        fin_type = ''
        try:
            x = float(morningstar.fetch_financials(self, fin_type, ticker, datacode))
        except:
            x = morningstar.fetch_financials(self, fin_type, ticker, datacode)
        return x
    
    def getMorningQFin( self, ticker, datacode):
        fin_type = 'qtr'
        try:
            x = float(morningstar.fetch_financials(self, fin_type,  ticker, datacode))
        except:
            x = morningstar.fetch_financials(self, fin_type, ticker, datacode)
        return x
    
    def getADVFN( self, ticker, datacode):
        try:
            x = float(advfn.fetch_advfn(self, ticker, datacode))
        except:
            x = advfn.fetch_advfn(self, ticker, datacode)
        return x
    
def find_exchange(self, ticker):
    """Determine exchange ticker is traded on so we can query Morningstar"""
    exch_name = ['nasdaq','nyse','amex']
    #Get exchange lists we don't have already, and return ticker's exchange.
    for exch in exch_name:
        if exch == 'nasdaq':
            if self.exchange_flag[0] == '0':
                    query_nasdaq(self, exch)
                    self.exchange_flag[0] = '1'
            for i in self.nasdaq_list:                
                if ticker == i[0]:
                    return 'XNAS'
        if exch == 'nyse':
            if self.exchange_flag[1] == '0':
                    query_nasdaq(self, exch)
                    self.exchange_flag[1] = '1'
            for i in self.nyse_list:
                if ticker == i[0]:
                    return 'XNYS'
        if exch == 'amex':
            if self.exchange_flag[2] == '0':
                    query_nasdaq(self, exch)
                    self.exchange_flag[2] = '1'
            for i in self.amex_list:
                if ticker == i[0]:
                    return 'XASE'
    return 'Exchange lookup failed. Only NYSE, NASDAQ, and AMEX are supported.'

def query_nasdaq(self, exch_name):
    """Query Nasdaq for list of tickers by exchange"""
    header = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:32.0) Gecko/20100101 Firefox/32.0',}
    url = 'http://www.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=%s&render=download' % (exch_name)
    req = Request(url, headers = header)
    try:
        response = urlopen(req)
    #Catch errors.
    except URLError as e:
        self.exchange_flag[0] = '1'
        if hasattr(e, 'reason'):
            return e.reason
        elif hasattr(e,'code'):
            return 'Error', e.code
    #Setup list(s) of exchange names.
    exch_result = csv.reader(iterdecode(response,'utf-8'))
    if exch_name == 'nasdaq':
        self.nasdaq_list = [row for row in exch_result]
    elif exch_name == 'nyse':
        self.nyse_list = [row for row in exch_result]
    elif exch_name == 'amex':
        self.amex_list = [row for row in exch_result]
    return 'Unknown Exception in query_nasdaq'
    
def createInstance( ctx ):
    return SmfImpl( ctx )

g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation( \
    createInstance,"com.smf.ticker.getinfo.python.SmfImpl",
        ("com.sun.star.sheet.AddIn",),)