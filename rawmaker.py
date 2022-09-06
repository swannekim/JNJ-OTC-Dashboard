#!/usr/bin/env python
# coding: utf-8

# In[ ]:
# Copyright flxblyy 2022


import pandas as pd

class RawCsv:
    
    def __init__(self, startyr, endyr):
        self.df = pd.DataFrame()
        self.startyr = startyr
        self.endyr = endyr
        self.finish = "raw data formed"
    
    def startyr(self):
        return self._startyr
    
    def endyr(self):
        return self._endyr
        
    def concatsort(self):
        # Reading CSV files in a loop
        # data should be in the same file path
        # same string format of file names are needed
        file_name = "./rawdata/OTC_JNJ_Product_{}.csv"
        # concat: join DataFrames vertically (axis=0)
        # range (start, end+1)
        range_startyr = self.startyr
        range_endyr = self.endyr+1
        df = pd.concat([pd.read_csv(file_name.format(i), engine="python", encoding="utf-8") for i in range(range_startyr, range_endyr)], axis=0)
        sorteddf = df.sort_values(by=["Pop Name","Sku English"], ascending=True, na_position='first', ignore_index=True)
        return sorteddf

    def savecsv(self):
        df2 = self.concatsort()
        df2.to_csv("./datafiles/rawotcsku.csv", index=False, encoding="utf-8-sig")
        print(self.finish)