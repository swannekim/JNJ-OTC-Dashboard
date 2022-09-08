#!/usr/bin/env python
# coding: utf-8

# In[ ]:
# Copyright flxblyy 2022


import pandas as pd

class Distribution:
    
    def __init__(self):
        self.finish = 'monthly, weekly, and filtered distribution rate added'
        # self.data = pd.DataFrame()
        
    def readfile(self):
        # Master Data
        df = pd.read_csv("./datafiles/otcskuplacement.csv", engine="python", encoding="utf-8")
        return df
    
    def addmonthly(self):
        df1 = self.readfile()
        
        # deep copy to protect original dataframe created from plmtmaker
        df2 = df1.copy()
        # multiple rows in same OTC(POP_Code) dropped for calculation
        df2.drop_duplicates(subset=["SKU_Eng","YearMonth","POP_Code"], keep = "first", inplace = True)
        # calculate mean of Monthly_Placement (0 or 1) by SKU and month
        # add column
        df2["Monthly_DistRate"] = df2.groupby(["SKU_Eng","YearMonth"])["Monthly_Placement"].transform("mean")
        
        # merge back into original dataframe
        df3 = pd.merge(df1, df2, how="left")
        df3["Monthly_DistRate"].fillna(method = "ffill", inplace = True)
        
        return df3
        
    def addweekly(self):
        df3 = self.addmonthly()
        
        # deep copy to protect original dataframe created with addmonthly method
        df4 = df3.copy()
        # multiple rows in same OTC(POP_Code) dropped for calculation
        df4.drop_duplicates(subset=["SKU_Eng","VisitWeek","POP_Code"], keep = "first", inplace = True)
        # calculate mean of Weekly_Placement (0 or 1) by Filter, SKU and week
        # add column
        df4["Weekly_DistRate"] = df4.groupby(["SKU_Eng","VisitWeek"])["Weekly_Placement"].transform("mean")
        
        # merge back into original dataframe
        df5 = pd.merge(df3, df4, how="left")
        df5["Weekly_DistRate"].fillna(method = "ffill", inplace = True)
        self.data = df5
        
        return df5
        
    def addfilter(self):
        # df6 = self.data
        df6 = self.addweekly()
        
        # Object Oriented Programming
        print("Select a Unit of Period from <Monthly, Weekly>")
        print("Select a Classification of Pharmacy from <Area, Customer, SalesGroupName, Comments>")
        filterlist = ["Area", "Customer", "SalesGroupName", "Comments"]
        periodlist = ["Monthly", "Weekly"]
        
        while True:
            period = input("Enter unit of period: ")
            otcfilter = input("Enter OTC Filter: ")
            if otcfilter not in filterlist:
                print("Please enter pharmacy filter name on the list.")
                continue
            elif period not in periodlist:
                print("Please enter period unit on the list.")
                continue
            else:
                # exit the loop
                break
                
        # deep copy to protect original dataframe created from plmtmaker
        df7 = df6.copy()
        
        if (period=="Monthly"):
            
            # multiple rows in same OTC(POP_Code) dropped for calculation
            df7.drop_duplicates(subset=[str(otcfilter),"SKU_Eng","YearMonth","POP_Code"], keep = "first", inplace = True)
            # calculate mean of Monthly_Placement (0 or 1) by Filter, SKU and month
            # add column
            df7["M_DistRate_"+str(otcfilter)] = df7.groupby([str(otcfilter),"SKU_Eng","YearMonth"])["Monthly_Placement"].transform("mean")
        
            # merge back into original dataframe
            df8 = pd.merge(df6, df7, how="left")
            df8["M_DistRate_"+str(otcfilter)].fillna(method = "ffill", inplace = True)
        
        elif (period=="Weekly"):
            
            # multiple rows in same Pharmacy(POP_Code) dropped for calculation
            df7.drop_duplicates(subset=[str(otcfilter),"SKU_Eng","VisitWeek","POP_Code"], keep = "first", inplace = True)
            # calculate mean of Monthly_Placement (0 or 1) by Filter, SKU and month
            # add column
            df7["W_DistRate_"+str(otcfilter)] = df7.groupby([str(otcfilter),"SKU_Eng","VisitWeek"])["Weekly_Placement"].transform("mean")
        
            # merge back into original dataframe
            df8 = pd.merge(df6, df7, how="left")
            df8["W_DistRate_"+str(otcfilter)].fillna(method = "ffill", inplace = True)
        
        return df8
    
    def dropsku(self):
        df9 = self.addfilter()
        
        # delete SKUs that have small amount of data by record month
        totalsku = list(df9["SKU_Eng"].unique())
        littlesku = []
        for sku in totalsku:
            skudf = df9[df9["SKU_Eng"]==sku]
            # list up SKUs that only have same or less than 4 months of data
            if(len(skudf["YearMonth"].unique())<=4):
                littlesku.append(sku)
        # cf. include "Children's Tylenol ODG 160mg 12T"
        # new Key SKU
        if str("Children's Tylenol ODG 160mg 12T") in littlesku:
            littlesku.remove("Children's Tylenol ODG 160mg 12T")
        # drop rows that contain any value in the list littlesku
        df10 = df9[df9.SKU_Eng.isin(littlesku)==False]
            
        return df10
    
    def savecsv(self):
        df11 = self.dropsku()
        df11.to_csv("./datafiles/otcskudistrate.csv", index=False, encoding="utf-8-sig")
        print(self.finish)