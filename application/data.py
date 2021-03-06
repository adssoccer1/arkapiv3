import requests
import csv
import pandas as pd
import io
import json
from datetime import datetime as dt
import math
from .models import *
from requests import ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError
import time

def init_app(app):
    # add multiple commands in a bulk
    app.cli.add_command(app.cli.command()(updateData))

def updateData():
    
    tickerToLinkDict = {"ARKK": "https://ark-funds.com/wp-content/fundsiteliterature/csv/ARK_INNOVATION_ETF_ARKK_HOLDINGS.csv", "ARKQ": "https://ark-funds.com/wp-content/fundsiteliterature/csv/ARK_AUTONOMOUS_TECHNOLOGY_&_ROBOTICS_ETF_ARKQ_HOLDINGS.csv", "ARKG": "https://ark-funds.com/wp-content/fundsiteliterature/csv/ARK_GENOMIC_REVOLUTION_MULTISECTOR_ETF_ARKG_HOLDINGS.csv", "ARKF" : "https://ark-funds.com/wp-content/fundsiteliterature/csv/ARK_FINTECH_INNOVATION_ETF_ARKF_HOLDINGS.csv", "ARKW" :"https://ark-funds.com/wp-content/fundsiteliterature/csv/ARK_NEXT_GENERATION_INTERNET_ETF_ARKW_HOLDINGS.csv" , "PRINT":"https://ark-funds.com/wp-content/fundsiteliterature/csv/THE_3D_PRINTING_ETF_PRNT_HOLDINGS.csv", "IZRL":"https://ark-funds.com/wp-content/fundsiteliterature/csv/ARK_ISRAEL_INNOVATIVE_TECHNOLOGY_ETF_IZRL_HOLDINGS.csv" }
    
    putDataInDB(ArkkTable, "ARKK", tickerToLinkDict)
    ArkkHoldings = ArkkTable.query.all()
    
    putDataInDB(ArkqTable, "ARKQ", tickerToLinkDict)
    ArkqHoldings = ArkqTable.query.all()
    
    putDataInDB(ArkgTable, "ARKG", tickerToLinkDict)
    ArkgHoldings = ArkgTable.query.all()
    
    putDataInDB(ArkfTable, "ARKF", tickerToLinkDict)
    ArkfHoldings = ArkfTable.query.all()
    
    putDataInDB(ArkwTable, "ARKW", tickerToLinkDict)
    ArkwHoldings = ArkwTable.query.all()
    
    putDataInDB(PrintTable, "PRINT", tickerToLinkDict)
    PRINTHoldings = PrintTable.query.all()
    
    putDataInDB(IzrlTable, "IZRL", tickerToLinkDict)
    IZRLHoldings = IzrlTable.query.all()

    return [ArkkHoldings,ArkqHoldings, ArkgHoldings, ArkfHoldings, ArkwHoldings, PRINTHoldings, IZRLHoldings]

def putDataInDB(tableName, fundTicker, tickerToLinkDict):
    if len(tableName.query.all()) > 0:
        tableName.query.delete()

    req = requests.get(tickerToLinkDict[fundTicker])
        
    s = req.content.decode('utf-8')
    ArkkData = pd.read_csv(io.StringIO(s))
    
    
    
    counter = 0
    for row in ArkkData.itertuples():
        counter += 1
        if(type(row.company) != str):
            break
        

        
        replacement = None
        for i in row:
            if type(i) == float and math.isnan(i):
                replacement = "----"
                print(i , "was a nan and has been replaced with ---- in row", row)
    
        print(row.ticker, "and", row.cusip)
        ticker = ""
        jsonResponse = None
        marketCap = -1
        logo = ""
        weburl = ""
        shareOutstanding = -1
        
        FiftyTwoWeekHigh = -1
        FiftyTwoWeekLow = -1
        ytdPriceReturnDaily = -1
        FiveDayPriceReturnDaily = -1
        ThirteenWeekPriceReturnDaily = -1
        TwentySixWeekPriceReturnDaily = -1
        price = -1
        if(replacement is not None):  #there is no ticker
            ticker = replacement + str(counter)
        else:
            
            ticker = row.ticker
            
            r = requests.get('https://finnhub.io/api/v1/stock/profile2?cusip='+row.cusip+'&token=bsjiihnrh5r9fp4arl20')
            
            print("     status code for profile: ", r.status_code)
            if r.status_code == 200:
                jsonResponse = r.json()
                if len(jsonResponse) > 0:

                    marketCap = jsonResponse['marketCapitalization']
                    logo = jsonResponse['logo']
                    weburl = jsonResponse['weburl']
                    shareOutstanding = jsonResponse['shareOutstanding']
                else:
                    print("error at profile json was empty response")

            time.sleep(1)


            r = requests.get('https://finnhub.io/api/v1/stock/metric?symbol=' + ticker + '&metric=price&token=bsjiihnrh5r9fp4arl20')
            print("     status code for financial data request: ", r.status_code)
            if r.status_code == 200:
                jsonResponse = r.json()
                #    print("     " , jsonResponse)
                if len(jsonResponse['metric']) > 0:
                    FiftyTwoWeekHigh = jsonResponse['metric']['52WeekHigh']
                    FiftyTwoWeekLow = jsonResponse['metric']['52WeekLow']
                    ytdPriceReturnDaily = jsonResponse['metric']['yearToDatePriceReturnDaily']
                    FiveDayPriceReturnDaily = jsonResponse['metric']['5DayPriceReturnDaily']
                    ThirteenWeekPriceReturnDaily = jsonResponse['metric']['13WeekPriceReturnDaily']
                    TwentySixWeekPriceReturnDaily = jsonResponse['metric']['26WeekPriceReturnDaily']
                else:
                    print("error at financial data. json was empty response")

            time.sleep(1)

            r = requests.get('https://finnhub.io/api/v1/quote?symbol='+ticker+'&token=bsjiihnrh5r9fp4arl20')
            print("     status code for price request: ", r.status_code)
            if r.status_code == 200:
                jsonResponse = r.json()
                if len(jsonResponse) > 0:
                    price = jsonResponse['c']
                else:
                    print("error at price. json was empty response")


        time.sleep(1)

        new_stock = tableName(ticker=ticker, date=dt.now(), shares=row.shares, cusip=row.cusip, companyName=row.company, marketCap=marketCap, logo=logo, weburl=weburl, shareOutstanding=shareOutstanding, fiftyTwoWeekHigh=FiftyTwoWeekHigh, fiftyTwoWeekLow=FiftyTwoWeekLow, ytdPriceReturnDaily=ytdPriceReturnDaily, fiveDayPriceReturnDaily=FiveDayPriceReturnDaily, thirteenWeekPriceReturnDaily=ThirteenWeekPriceReturnDaily, twentySixWeekPriceReturnDaily=TwentySixWeekPriceReturnDaily, price=price)
        db.session.add(new_stock)
    db.session.commit()

def initDBv2():
    
    
    new_stock = ArkkTable(date=dt.now(), cusip="asdf", companyName="lwjnjw", ticker="lwjnjw", logo="asdF", weburl="asdfa", value=1, shares=1, weight=1, price=1, marketCap=1, FullTimeEmployees=1, PERatio=1, EPS=1, DividendYield=1, QuarterlyEarningsGrowthYOY=1, QuarterlyRevenueGrowthYOY=1, fiftyTwoWeekHigh=1,fiftyTwoWeekLow=1, fiftyDayMovingAverage=1, twohundredDayMovingAverage=1, PercentInsiders=1, PercentInstitutions=1, avg10Volume=1, avg30Volume=1, year5ChangePercent=1, year2ChangePercent=1, year1ChangePercent=1, month6ChangePercent=1, month3ChangePercent=1, month1ChangePercent=1, day5ChangePercent=1, nextEarningsDate="asfd", shareOutstanding= 1)
    db.session.add(new_stock)

    new_stock1 = ArkqTable(date=dt.now(), cusip="asdf", companyName="lwjnjw", ticker="lwjnjw", logo="asdF", weburl="asdfa", value=1, shares=1, weight=1, price=1, marketCap=1, FullTimeEmployees=1, PERatio=1, EPS=1, DividendYield=1, QuarterlyEarningsGrowthYOY=1, QuarterlyRevenueGrowthYOY=1, fiftyTwoWeekHigh=1,fiftyTwoWeekLow=1, fiftyDayMovingAverage=1, twohundredDayMovingAverage=1, PercentInsiders=1, PercentInstitutions=1, avg10Volume=1, avg30Volume=1, year5ChangePercent=1, year2ChangePercent=1, year1ChangePercent=1, month6ChangePercent=1, month3ChangePercent=1, month1ChangePercent=1, day5ChangePercent=1, nextEarningsDate="asfd", shareOutstanding= 1)
    db.session.add(new_stock1)

    new_stock2 = ArkgTable(date=dt.now(), cusip="asdf", companyName="lwjnjw", ticker="lwjnjw", logo="asdF", weburl="asdfa", value=1, shares=1, weight=1, price=1, marketCap=1, FullTimeEmployees=1, PERatio=1, EPS=1, DividendYield=1, QuarterlyEarningsGrowthYOY=1, QuarterlyRevenueGrowthYOY=1, fiftyTwoWeekHigh=1,fiftyTwoWeekLow=1, fiftyDayMovingAverage=1, twohundredDayMovingAverage=1, PercentInsiders=1, PercentInstitutions=1, avg10Volume=1, avg30Volume=1, year5ChangePercent=1, year2ChangePercent=1, year1ChangePercent=1, month6ChangePercent=1, month3ChangePercent=1, month1ChangePercent=1, day5ChangePercent=1, nextEarningsDate="asfd", shareOutstanding= 1)
    db.session.add(new_stock2)
    
    new_stock3 = ArkfTable(date=dt.now(), cusip="asdf", companyName="lwjnjw", ticker="lwjnjw", logo="asdF", weburl="asdfa", value=1, shares=1, weight=1, price=1, marketCap=1, FullTimeEmployees=1, PERatio=1, EPS=1, DividendYield=1, QuarterlyEarningsGrowthYOY=1, QuarterlyRevenueGrowthYOY=1, fiftyTwoWeekHigh=1,fiftyTwoWeekLow=1, fiftyDayMovingAverage=1, twohundredDayMovingAverage=1, PercentInsiders=1, PercentInstitutions=1, avg10Volume=1, avg30Volume=1, year5ChangePercent=1, year2ChangePercent=1, year1ChangePercent=1, month6ChangePercent=1, month3ChangePercent=1, month1ChangePercent=1, day5ChangePercent=1, nextEarningsDate="asfd", shareOutstanding= 1)
    db.session.add(new_stock3)

    new_stock4 = ArkwTable(date=dt.now(), cusip="asdf", companyName="lwjnjw", ticker="lwjnjw", logo="asdF", weburl="asdfa", value=1, shares=1, weight=1, price=1, marketCap=1, FullTimeEmployees=1, PERatio=1, EPS=1, DividendYield=1, QuarterlyEarningsGrowthYOY=1, QuarterlyRevenueGrowthYOY=1, fiftyTwoWeekHigh=1,fiftyTwoWeekLow=1, fiftyDayMovingAverage=1, twohundredDayMovingAverage=1, PercentInsiders=1, PercentInstitutions=1, avg10Volume=1, avg30Volume=1, year5ChangePercent=1, year2ChangePercent=1, year1ChangePercent=1, month6ChangePercent=1, month3ChangePercent=1, month1ChangePercent=1, day5ChangePercent=1, nextEarningsDate="asfd", shareOutstanding= 1)
    db.session.add(new_stock4)
    
    new_stock5 = PrintTable(date=dt.now(), cusip="asdf", companyName="lwjnjw", ticker="lwjnjw", logo="asdF", weburl="asdfa", value=1, shares=1, weight=1, price=1, marketCap=1, FullTimeEmployees=1, PERatio=1, EPS=1, DividendYield=1, QuarterlyEarningsGrowthYOY=1, QuarterlyRevenueGrowthYOY=1, fiftyTwoWeekHigh=1,fiftyTwoWeekLow=1, fiftyDayMovingAverage=1, twohundredDayMovingAverage=1, PercentInsiders=1, PercentInstitutions=1, avg10Volume=1, avg30Volume=1, year5ChangePercent=1, year2ChangePercent=1, year1ChangePercent=1, month6ChangePercent=1, month3ChangePercent=1, month1ChangePercent=1, day5ChangePercent=1, nextEarningsDate="asfd", shareOutstanding= 1)
    db.session.add(new_stock5)

    new_stock6 = IzrlTable(date=dt.now(), cusip="asdf", companyName="lwjnjw", ticker="lwjnjw", logo="asdF", weburl="asdfa", value=1, shares=1, weight=1, price=1, marketCap=1, FullTimeEmployees=1, PERatio=1, EPS=1, DividendYield=1, QuarterlyEarningsGrowthYOY=1, QuarterlyRevenueGrowthYOY=1, fiftyTwoWeekHigh=1,fiftyTwoWeekLow=1, fiftyDayMovingAverage=1, twohundredDayMovingAverage=1, PercentInsiders=1, PercentInstitutions=1, avg10Volume=1, avg30Volume=1, year5ChangePercent=1, year2ChangePercent=1, year1ChangePercent=1, month6ChangePercent=1, month3ChangePercent=1, month1ChangePercent=1, day5ChangePercent=1, nextEarningsDate="asfd", shareOutstanding= 1)
    db.session.add(new_stock6)
    
    new_stock7 = AllStocks(date=dt.now(), heldInFunds="asfasf", cusip="asdf", companyName="lwjnjw", ticker="lwjnjw", logo="asdF", weburl="asdfa", value=1, shares=1, weight=1, price=1, marketCap=1, FullTimeEmployees=1, PERatio=1, EPS=1, DividendYield=1, QuarterlyEarningsGrowthYOY=1, QuarterlyRevenueGrowthYOY=1, fiftyTwoWeekHigh=1,fiftyTwoWeekLow=1, fiftyDayMovingAverage=1, twohundredDayMovingAverage=1, PercentInsiders=1, PercentInstitutions=1, avg10Volume=1, avg30Volume=1, year5ChangePercent=1, year2ChangePercent=1, year1ChangePercent=1, month6ChangePercent=1, month3ChangePercent=1, month1ChangePercent=1, day5ChangePercent=1, nextEarningsDate="asfd", shareOutstanding= 1)
    db.session.add(new_stock7)
    
    db.session.commit()


def initDB():
    new_stock = ArkkTable(ticker="jhgf", date=dt.now(), shares=10, cusip="sdfg", companyName="lwjnjw", marketCap=234, logo="afasfsadf", weburl="asfssfd", shareOutstanding="12343", fiftyTwoWeekHigh=234, fiftyTwoWeekLow=234, ytdPriceReturnDaily=234, fiveDayPriceReturnDaily=1234, thirteenWeekPriceReturnDaily=123, twentySixWeekPriceReturnDaily=134, price=4312)
    db.session.add(new_stock)
        
    new_stock1 = ArkqTable(ticker="jhgf", date=dt.now(), shares=10, cusip="sdfg", companyName="lwjnjw", marketCap=234, logo="afasfsadf", weburl="asfssfd", shareOutstanding="12343", fiftyTwoWeekHigh=234, fiftyTwoWeekLow=234, ytdPriceReturnDaily=234, fiveDayPriceReturnDaily=1234, thirteenWeekPriceReturnDaily=123, twentySixWeekPriceReturnDaily=134, price=4312)
    db.session.add(new_stock1)

    new_stock2 = ArkgTable(ticker="jhgf", date=dt.now(), shares=10, cusip="sdfg", companyName="lwjnjw", marketCap=234, logo="afasfsadf", weburl="asfssfd", shareOutstanding="12343", fiftyTwoWeekHigh=234, fiftyTwoWeekLow=234, ytdPriceReturnDaily=234, fiveDayPriceReturnDaily=1234, thirteenWeekPriceReturnDaily=123, twentySixWeekPriceReturnDaily=134, price=4312)
    db.session.add(new_stock2)
    new_stock3 = ArkfTable(ticker="jhgf", date=dt.now(), shares=10, cusip="sdfg", companyName="lwjnjw", marketCap=234, logo="afasfsadf", weburl="asfssfd", shareOutstanding="12343", fiftyTwoWeekHigh=234, fiftyTwoWeekLow=234, ytdPriceReturnDaily=234, fiveDayPriceReturnDaily=1234, thirteenWeekPriceReturnDaily=123, twentySixWeekPriceReturnDaily=134, price=4312)
    db.session.add(new_stock3)
    new_stock4 = ArkwTable(ticker="jhgf", date=dt.now(), shares=10, cusip="sdfg", companyName="lwjnjw", marketCap=234, logo="afasfsadf", weburl="asfssfd", shareOutstanding="12343", fiftyTwoWeekHigh=234, fiftyTwoWeekLow=234, ytdPriceReturnDaily=234, fiveDayPriceReturnDaily=1234, thirteenWeekPriceReturnDaily=123, twentySixWeekPriceReturnDaily=134, price=4312)
    db.session.add(new_stock4)
    new_stock5 = PrintTable(ticker="jhgf", date=dt.now(), shares=10, cusip="sdfg", companyName="lwjnjw", marketCap=234, logo="afasfsadf", weburl="asfssfd", shareOutstanding="12343", fiftyTwoWeekHigh=234, fiftyTwoWeekLow=234, ytdPriceReturnDaily=234, fiveDayPriceReturnDaily=1234, thirteenWeekPriceReturnDaily=123, twentySixWeekPriceReturnDaily=134, price=4312)
    db.session.add(new_stock5)
    new_stock6 = IzrlTable(ticker="jhgf", date=dt.now(), shares=10, cusip="sdfg", companyName="lwjnjw", marketCap=234, logo="afasfsadf", weburl="asfssfd", shareOutstanding="12343", fiftyTwoWeekHigh=234, fiftyTwoWeekLow=234, ytdPriceReturnDaily=234, fiveDayPriceReturnDaily=1234, thirteenWeekPriceReturnDaily=123, twentySixWeekPriceReturnDaily=134, price=4312)
    db.session.add(new_stock6)
    db.session.commit()




#------------------------------------------------------------------------------------------------------#

def getDataFromDB(tableName, fundTicker):
    table = tableName.query.all()
    print(table)
    if len(table) == 0:
        print("table is empty")
        return
    dict = {"timestamp" : dt.now(), "fundTicker" : fundTicker,  "holdings" : [] }
    for row in table:
        #info = AllStocks.query.filter_by(companyName=row.companyName).first()
        info = row
        rowDict = {"ticker" : info.ticker , "weight": info.weight, "value" : info.value,  "company": info.companyName, "cusip": info.cusip, "shares" : info.shares, "marketCap" : info.marketCap, "logo" : info.logo, "weburl" : info.weburl, "sharesOutstandig" : info.shareOutstanding,"price": info.price, "FullTimeEmployees":info.FullTimeEmployees, "PERatio":info.PERatio, "EPS":info.EPS, "DividendYield":info.DividendYield, "QuarterlyEarningsGrowthYOY":info.QuarterlyEarningsGrowthYOY, "QuarterlyRevenueGrowthYOY":info.QuarterlyRevenueGrowthYOY, "fiftyTwoWeekHigh":info.fiftyTwoWeekHigh, "fiftyTwoWeekLow":info.fiftyTwoWeekLow, "fiftyDayMovingAverage":info.fiftyDayMovingAverage, "twohundredDayMovingAverage":info.twohundredDayMovingAverage, "PercentInsiders":info.PercentInsiders,"PercentInstitutions":info.PercentInstitutions, "avg10Volume":info.avg10Volume, "avg30Volume":info.avg30Volume, "year5ChangePercent":info.year5ChangePercent, "year2ChangePercent":info.year2ChangePercent, "year1ChangePercent":info.year1ChangePercent, "month6ChangePercent":info.month6ChangePercent, "month3ChangePercent":info.month3ChangePercent, "month1ChangePercent":info.month1ChangePercent, "day5ChangePercent":info.day5ChangePercent, "nextEarningsDate":info.nextEarningsDate}
        dict["holdings"].append(rowDict)
    return dict

def getDatafromAllStocks():
    table = AllStocks.query.all()
    if len(table) == 0:
        print("table is empty")
        return
    dict = {"timestamp" : dt.now(), "fundTicker" : "not applicable",  "holdings" : [] }
    for row in table:
        #info = AllStocks.query.filter_by(companyName=row.companyName).first()
        info = row
        rowDict = {"ticker" : info.ticker , "weight": info.weight, "value" : info.value,  "company": info.companyName, "cusip": info.cusip, "shares" : info.shares, "heldinFunds" : info.heldInFunds, "marketCap" : info.marketCap, "logo" : info.logo, "weburl" : info.weburl, "sharesOutstandig" : info.shareOutstanding,"price": info.price, "FullTimeEmployees":info.FullTimeEmployees, "PERatio":info.PERatio, "EPS":info.EPS, "DividendYield":info.DividendYield, "QuarterlyEarningsGrowthYOY":info.QuarterlyEarningsGrowthYOY, "QuarterlyRevenueGrowthYOY":info.QuarterlyRevenueGrowthYOY, "fiftyTwoWeekHigh":info.fiftyTwoWeekHigh, "fiftyTwoWeekLow":info.fiftyTwoWeekLow, "fiftyDayMovingAverage":info.fiftyDayMovingAverage, "twohundredDayMovingAverage":info.twohundredDayMovingAverage, "PercentInsiders":info.PercentInsiders,"PercentInstitutions":info.PercentInstitutions, "avg10Volume":info.avg10Volume, "avg30Volume":info.avg30Volume, "year5ChangePercent":info.year5ChangePercent, "year2ChangePercent":info.year2ChangePercent, "year1ChangePercent":info.year1ChangePercent, "month6ChangePercent":info.month6ChangePercent, "month3ChangePercent":info.month3ChangePercent, "month1ChangePercent":info.month1ChangePercent, "day5ChangePercent":info.day5ChangePercent, "nextEarningsDate":info.nextEarningsDate}
        dict["holdings"].append(rowDict)
    return dict



"""
    
    def putARKQinDB():
    ArkqTable.query.delete()
    
    req = requests.get("https://ark-funds.com/wp-content/fundsiteliterature/csv/ARK_AUTONOMOUS_TECHNOLOGY_&_ROBOTICS_ETF_ARKQ_HOLDINGS.csv")
    
    s = req.content.decode('utf-8')
    data = pd.read_csv(io.StringIO(s))
    
    counter = 0
    for row in data.itertuples():
    counter += 1
    if(type(row.company) != str):
    break
    
    replacement = None
    for i in row:
    if type(i) == float and math.isnan(i):
    replacement = "----"
    print(i , "was a nan and has been replaced with ---- in row", row)
    
    ticker = ""
    if(replacement is not None):
    ticker = replacement + str(counter)
    else:
    ticker = row.ticker
    
    new_stock = ArkqTable(ticker=ticker, date=dt.now(), shares=row.shares, cusip=row.cusip, companyName=row.company)
    db.session.add(new_stock)
    db.session.commit()
    
    #ARKG
    def putARKGinDB():
    ArkgTable.query.delete()
    
    req = requests.get("https://ark-funds.com/wp-content/fundsiteliterature/csv/ARK_GENOMIC_REVOLUTION_MULTISECTOR_ETF_ARKG_HOLDINGS.csv")
    
    s = req.content.decode('utf-8')
    data = pd.read_csv(io.StringIO(s))
    
    counter = 0
    for row in data.itertuples():
    counter += 1
    if(type(row.company) != str):
    break
    
    replacement = None
    for i in row:
    if type(i) == float and math.isnan(i):
    replacement = "----"
    print(i , "was a nan and has been replaced with ---- in row", row)
    
    ticker = ""
    if(replacement is not None):
    ticker = replacement + str(counter)
    else:
    ticker = row.ticker
    
    new_stock = ArkgTable(ticker=ticker, date=dt.now(), shares=row.shares, cusip=row.cusip, companyName=row.company)
    db.session.add(new_stock)
    db.session.commit()
    
    
    #ARKF
    def putARKFinDB():
    ArkfTable.query.delete()
    
    req = requests.get("https://ark-funds.com/wp-content/fundsiteliterature/csv/ARK_FINTECH_INNOVATION_ETF_ARKF_HOLDINGS.csv")
    
    s = req.content.decode('utf-8')
    data = pd.read_csv(io.StringIO(s))
    
    counter = 0
    for row in data.itertuples():
    counter += 1
    if(type(row.company) != str):
    break
    
    replacement = None
    for i in row:
    if type(i) == float and math.isnan(i):
    replacement = "----"
    print(i , "was a nan and has been replaced with ---- in row", row)
    
    ticker = ""
    if(replacement is not None):
    ticker = replacement + str(counter)
    else:
    ticker = row.ticker
    
    new_stock = ArkfTable(ticker=ticker, date=dt.now(), shares=row.shares, cusip=row.cusip, companyName=row.company)
    db.session.add(new_stock)
    db.session.commit()
    
    #ARKW
    def putARKWinDB():
    ArkwTable.query.delete()
    
    req = requests.get("https://ark-funds.com/wp-content/fundsiteliterature/csv/ARK_NEXT_GENERATION_INTERNET_ETF_ARKW_HOLDINGS.csv")
    
    s = req.content.decode('utf-8')
    data = pd.read_csv(io.StringIO(s))
    
    counter = 0
    for row in data.itertuples():
    counter += 1
    if(type(row.company) != str):
    break
    
    replacement = None
    for i in row:
    if type(i) == float and math.isnan(i):
    replacement = "----"
    print(i , "was a nan and has been replaced with ---- in row", row)
    
    ticker = ""
    if(replacement is not None):
    ticker = replacement + str(counter)
    else:
    ticker = row.ticker
    
    new_stock = ArkwTable(ticker=ticker, date=dt.now(), shares=row.shares, cusip=row.cusip, companyName=row.company)
    db.session.add(new_stock)
    db.session.commit()
    
    #PRINT
    def putPRINTinDB():
    PrintTable.query.delete()
    
    req = requests.get("https://ark-funds.com/wp-content/fundsiteliterature/csv/THE_3D_PRINTING_ETF_PRNT_HOLDINGS.csv")
    
    s = req.content.decode('utf-8')
    data = pd.read_csv(io.StringIO(s))
    
    counter = 0
    for row in data.itertuples():
    counter += 1
    if(type(row.company) != str):
    break
    
    replacement = None
    for i in row:
    if type(i) == float and math.isnan(i):
    replacement = "----"
    print(i , "was a nan and has been replaced with ---- in row", row)
    
    ticker = ""
    if(replacement is not None):
    ticker = replacement + str(counter)
    else:
    ticker = row.ticker
    
    new_stock = PrintTable(ticker=ticker, date=dt.now(), shares=row.shares, cusip=row.cusip, companyName=row.company)
    db.session.add(new_stock)
    db.session.commit()
    
    
    
    def putIZRLinDB():
    IzrlTable.query.delete()
    
    req = requests.get("https://ark-funds.com/wp-content/fundsiteliterature/csv/ARK_ISRAEL_INNOVATIVE_TECHNOLOGY_ETF_IZRL_HOLDINGS.csv")
    
    s = req.content.decode('utf-8')
    data = pd.read_csv(io.StringIO(s))
    
    counter = 0
    for row in data.itertuples():
    counter += 1
    if(type(row.company) != str):
    break
    
    replacement = None
    for i in row:
    if type(i) == float and math.isnan(i):
    replacement = "----"
    print(i , "was a nan and has been replaced with ---- in row", row)
    
    ticker = ""
    if(replacement is not None):
    ticker = replacement + str(counter)
    else:
    ticker = row.ticker
    
    new_stock = IzrlTable(ticker=ticker, date=dt.now(), shares=row.shares, cusip=row.cusip, companyName=row.company)
    db.session.add(new_stock)
    db.session.commit()
"""
"""___________________________________________________________________________________________"""
"""
def getARKQDatafromDB():
    table = ArkqTable.query.all()
    dict = {"timestamp" : table[0].date, "fundTicker" : "ARKQ",  "holdings" : [] }
    for row in table:
        rowDict = {"ticker" : row.ticker , "company": row.companyName, "cusip": row.cusip, "shares" : row.shares}
        dict["holdings"].append(rowDict)
    return dict

def getARKGDatafromDB():
    table = ArkgTable.query.all()
    dict = {"timestamp" : table[0].date, "fundTicker" : "ARKG",  "holdings" : [] }
    for row in table:
        rowDict = {"ticker" : row.ticker , "company": row.companyName, "cusip": row.cusip, "shares" : row.shares}
        dict["holdings"].append(rowDict)
    return dict

def getARKFDatafromDB():
    table = ArkfTable.query.all()
    dict = {"timestamp" : table[0].date, "fundTicker" : "ARKF",  "holdings" : [] }
    for row in table:
        rowDict = {"ticker" : row.ticker , "company": row.companyName, "cusip": row.cusip, "shares" : row.shares}
        dict["holdings"].append(rowDict)
    return dict

def getARKWDatafromDB():
    table = ArkwTable.query.all()
    dict = {"timestamp" : table[0].date, "fundTicker" : "ARKW",  "holdings" : [] }
    for row in table:
        rowDict = {"ticker" : row.ticker , "company": row.companyName, "cusip": row.cusip, "shares" : row.shares}
        dict["holdings"].append(rowDict)
    return dict

def getPRINTDatafromDB():
    table = PrintTable.query.all()
    dict = {"timestamp" : table[0].date, "fundTicker" : "PRINT",  "holdings" : [] }
    for row in table:
        rowDict = {"ticker" : row.ticker , "company": row.companyName, "cusip": row.cusip, "shares" : row.shares}
        dict["holdings"].append(rowDict)
    return dict

def getIZRLDatafromDB():
    table = IzrlTable.query.all()
    dict = {"timestamp" : table[0].date, "fundTicker" : "IZRL",  "holdings" : [] }
    for row in table:
        rowDict = {"ticker" : row.ticker , "company": row.companyName, "cusip": row.cusip, "shares" : row.shares}
        dict["holdings"].append(rowDict)
    return dict
    
"""
"""
def getARKKData():
    req = requests.get("https://ark-funds.com/wp-content/fundsiteliterature/csv/ARK_INNOVATION_ETF_ARKK_HOLDINGS.csv")

    s = req.content.decode('utf-8')
    ArkkData = pd.read_csv(io.StringIO(s))
    
    #begin building dictionary to return in JSON response
    ArkkDict = {"timestamp" : ArkkData['date'][0], "fundTicker" : "ARKK",  "holdings" : [] }

    for row in ArkkData.itertuples():
        if(type(row.company) != str):
            break
        
        replacement = None
        for i in row:
            if type(i) == float and math.isnan(i):
                replacement = "----"
                print(i , "was a nan and has been replaced with ---- in row", row)
                            
        ticker = ""
        if(replacement is not None):
            ticker = replacement
        else:
            ticker = row.ticker
                                                
        #new_stock = ArkkTable(ticker=ticker, date=ArkkData['date'][0], shares=row.shares, cusip=row.cusip, companyName=row.company)
        #db.session.add(new_stock)

        stock = {"ticker" : ticker , "company": row.company,'cusip': row.cusip, 'shares':row.shares}
        ArkkDict["holdings"].append(stock)

    print("dcitionary: ", ArkkDict)
    return(ArkkDict)


def getARKQData():
    req = requests.get("https://ark-funds.com/wp-content/fundsiteliterature/csv/ARK_AUTONOMOUS_TECHNOLOGY_&_ROBOTICS_ETF_ARKQ_HOLDINGS.csv")
    
    s = req.content.decode('utf-8')
    ArkkData = pd.read_csv(io.StringIO(s))
    
    #begin building dictionary to return in JSON response
    ArkkDict = {"timestamp" : ArkkData['date'][0], "fundTicker" : "ARKQ",  "holdings" : [] }
    
    for row in ArkkData.itertuples():
        if(type(row.company) != str):
            break
        stock = {"ticker" : row.ticker , "company": row.company,'cusip': row.cusip, 'shares':row.shares}
        ArkkDict["holdings"].append(stock)
    
    print("dcitionary: ", ArkkDict)
    return(ArkkDict)

def getARKWData():
    req = requests.get("https://ark-funds.com/wp-content/fundsiteliterature/csv/ARK_NEXT_GENERATION_INTERNET_ETF_ARKW_HOLDINGS.csv")
    
    s = req.content.decode('utf-8')
    ArkkData = pd.read_csv(io.StringIO(s))
    
    #begin building dictionary to return in JSON response
    ArkkDict = {"timestamp" : ArkkData['date'][0], "fundTicker" : "ARKW",  "holdings" : [] }
    
    for row in ArkkData.itertuples():
        if(type(row.company) != str):
            break
        stock = {"ticker" : row.ticker , "company": row.company,'cusip': row.cusip, 'shares':row.shares}
        ArkkDict["holdings"].append(stock)
    
    print("dcitionary: ", ArkkDict)
    return(ArkkDict)


def getARKGData():
    req = requests.get("https://ark-funds.com/wp-content/fundsiteliterature/csv/ARK_GENOMIC_REVOLUTION_MULTISECTOR_ETF_ARKG_HOLDINGS.csv")
    
    s = req.content.decode('utf-8')
    ArkkData = pd.read_csv(io.StringIO(s))
    
    #begin building dictionary to return in JSON response
    ArkkDict = {"timestamp" : ArkkData['date'][0], "fundTicker" : "ARKG",  "holdings" : [] }
    
    for row in ArkkData.itertuples():
        if(type(row.company) != str):
            break
        stock = {"ticker" : row.ticker , "company": row.company,'cusip': row.cusip, 'shares':row.shares}
        ArkkDict["holdings"].append(stock)
    
    print("dcitionary: ", ArkkDict)
    return(ArkkDict)

def getARKFData():
    req = requests.get("https://ark-funds.com/wp-content/fundsiteliterature/csv/ARK_FINTECH_INNOVATION_ETF_ARKF_HOLDINGS.csv")
    
    s = req.content.decode('utf-8')
    ArkkData = pd.read_csv(io.StringIO(s))
    
    #begin building dictionary to return in JSON response
    ArkkDict = {"timestamp" : ArkkData['date'][0], "fundTicker" : "ARKF",  "holdings" : [] }
    
    for row in ArkkData.itertuples():
        if(type(row.company) != str):
            break
        stock = {"ticker" : row.ticker , "company": row.company,'cusip': row.cusip, 'shares':row.shares}
        ArkkDict["holdings"].append(stock)
    
    print("dcitionary: ", ArkkDict)
    return(ArkkDict)

def getPRINTData():
    req = requests.get("https://ark-funds.com/wp-content/fundsiteliterature/csv/THE_3D_PRINTING_ETF_PRNT_HOLDINGS.csv")
    
    s = req.content.decode('utf-8')
    ArkkData = pd.read_csv(io.StringIO(s))
    
    #begin building dictionary to return in JSON response
    ArkkDict = {"timestamp" : ArkkData['date'][0], "fundTicker" : "PRINT",  "holdings" : [] }
    
    for row in ArkkData.itertuples():
        if(type(row.company) != str):
            break
        stock = {"ticker" : row.ticker , "company": row.company,'cusip': row.cusip, 'shares':row.shares}
        ArkkDict["holdings"].append(stock)
    
    print("dcitionary: ", ArkkDict)
    return(ArkkDict)
def getIZRLData():
    req = requests.get("https://ark-funds.com/wp-content/fundsiteliterature/csv/ARK_ISRAEL_INNOVATIVE_TECHNOLOGY_ETF_IZRL_HOLDINGS.csv")
    
    s = req.content.decode('utf-8')
    ArkkData = pd.read_csv(io.StringIO(s))
    
    #begin building dictionary to return in JSON response
    ArkkDict = {"timestamp" : ArkkData['date'][0], "fundTicker" : "IZRL",  "holdings" : [] }
    
    for row in ArkkData.itertuples():
        if(type(row.company) != str):
            break
        stock = {"ticker" : row.ticker , "company": row.company,'cusip': row.cusip, 'shares':row.shares}
        ArkkDict["holdings"].append(stock)

    return(ArkkDict)
    
    """

