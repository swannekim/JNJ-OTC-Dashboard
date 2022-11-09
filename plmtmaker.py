#!/usr/bin/env python
# coding: utf-8

# In[ ]:
# Copyright flxblyy 2022

import pandas as pd
import numpy as np

class Placement:
    
    def __init__(self):
        self.finish = 'monthly, weekly placement added'
        
    def readmaster(self):
        # Master Data
        df = pd.read_csv("./datafiles/otcskumaster.csv", engine="python", encoding="utf-8")
        return df
    
    # method to calculate monthly placement in method addmonthly
    def monthly_placement(self, row):
        
        # monthly placement 1 only if total placement count matches total visit count
        if (row["Monthly_PlacementCount"]/row["Monthly_VisitCount"]==1):
            return 1
        elif (row["Monthly_PlacementCount"]/row["Monthly_VisitCount"]<1):
            return 0
        # if no visit in the month, return NaN values
        else:
            return np.nan
    
    def addmonthly(self):
        df1 = self.readmaster()
        
        # change SKU due to OTC list update (2022.11.09)
        df1.loc[df1["SKU_Eng"]=="Tylenol 500mg 10T_R'15", "SKU_Eng"] = "Tylenol 500MG BLST 10S KR"
        df1.loc[df1["EAN_Code"]=="8806469007213", "EAN_Code"] = "8806469025729"
        df1.loc[df1["SKU_Eng"]=="Tylenol ER 650mg 6T'18", "SKU_Eng"] = "TYLENOL 8HR ER 650MG BLST 6S KR"
        df1.loc[df1["EAN_Code"]=="8806469006971", "EAN_Code"] = "8806469026016"
        
        # count how many visit dates exist by OTC(POP_Code), SKU(EAN_Code), month(YearMonth)
        # add column to data
        df1["Monthly_VisitCount"] = df1.groupby(["POP_Code","EAN_Code","YearMonth"])["VisitDate"].transform("count")
        # sum up placement(yes:1, no:0) by OTC(POP_Code), SKU(EAN_Code), month(YearMonth)
        # add column to data
        df1["Monthly_PlacementCount"] = df1.groupby(["POP_Code","EAN_Code","YearMonth"])["placement"].transform("sum")
        # add calculated monthly placement to dataframe
        df1["Monthly_Placement"] = df1.apply(lambda row: self.monthly_placement(row), axis=1)
        
        return df1
    
    # method to calculate weekly placement in method addweekly
    def weekly_placement(self, row):
        # weekly placement 1 only if total placement count matches total visit count
        if (row['Weekly_PlacementCount']/row['Weekly_VisitCount']==1):
            return 1
        elif (row['Weekly_PlacementCount']/row['Weekly_VisitCount']<1):
            return 0
        # if no visit in the week, return NaN values
        else:
            return np.nan
    
    def addweekly(self):
        df2 = self.addmonthly()
        
        # count how many visit dates exist by OTC(POP_Code), SKU(EAN_Code), week(VisitWeek)
        # add column to data
        df2["Weekly_VisitCount"] = df2.groupby(["POP_Code","EAN_Code","VisitWeek"])["VisitDate"].transform("count")
        # sum up placement(yes:1, no:0) by OTC(POP_Code), SKU(EAN_Code), week(VisitWeek)
        # add column to data
        df2["Weekly_PlacementCount"] = df2.groupby(["POP_Code","EAN_Code","VisitWeek"])["placement"].transform("sum")
        # add calculated weekly placement to dataframe
        df2["Weekly_Placement"] = df2.apply(lambda row: self.weekly_placement(row), axis=1)
        
        return df2
    
    def savecsv(self):
        df3 = self.addweekly()
        df3.to_csv("./datafiles/otcskuplacement.csv", index=False, encoding="utf-8-sig")
        print(self.finish)