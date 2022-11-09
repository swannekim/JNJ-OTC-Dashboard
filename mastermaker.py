#!/usr/bin/env python
# coding: utf-8

# In[ ]:
# Copyright flxblyy 2022


import pandas as pd

class FormMaster:
    
    def __init__(self):
        self.finish = 'master data formed'
        
    def readcsvs(self):
        # Pharmacy Data
        # going to use: Area, Sales Group Name, Customer, Comments
        pharmacylst = pd.read_csv("./datafiles/Pharmacy_List_OTC_POP6.csv", engine="python", encoding="utf-8")
        # OTC SKU POP6 Data
        otcskuraw = pd.read_csv("./datafiles/rawotcsku.csv", engine="python", encoding="utf-8")
        # SKU Hierachy File
        skuntshier = pd.read_csv("./datafiles/NTS_SKU_OTC.csv", engine="python", encoding="utf-8")
        return pharmacylst, otcskuraw, skuntshier
    
    def show(self, num):
        pharmacy, otcprdt, skunts = self.readcsvs()
        if num==1:
            print(len(pharmacy))
            print(pharmacy.columns)
            return pharmacy
        if num==2:
            print(len(otcprdt))
            print(otcprdt.columns)
            return otcprdt
        if num==3:
            print(len(skunts))
            print(skunts.columns)
            return skunts
    
    def cleanup(self):
        pharmacy, otcprdt, skunts = self.readcsvs()
        skuhier = skunts.drop(['January', 'February', 'March', 'April', 'May', 'June', 'July'], axis=1)
        
        # drop the columns where all elements are NaN
        pharmacy.dropna(axis=1, how='all', inplace=True)
        # drop Last Visit column that contains 28 NaN values
        pharmacy.dropna(subset=['Last Visit'], inplace=True)
        
        # merge pharmacy file to otcprdt file according to Pop Name
        df1 = pd.merge(otcprdt, pharmacy, how='left', left_on='Pop Name', right_on='POP Name')
        # drop rows will null values in POP Name column
        df1.dropna(subset=['POP Name'], inplace=True)
        
        # check for correct merge
        if len(df1)==len(otcprdt):
            pass
        
        # Drop the columns with same values
        # can edit this part according to change of data files
        df2 = df1.copy()
        # print(df2.columns)
        
        if (df2['Channel_x'].equals(df2['Channel_y'])==True):
            df2.drop('Channel_y', axis=1, inplace=True)
            df2.rename(columns={'Channel_x':'Channel'}, inplace=True)
        if (df2['Sales Group Name_x'].equals(df2['Sales Group Name_y'])==True):
            df2.drop('Sales Group Name_y', axis=1, inplace=True)
            df2.rename(columns={'Sales Group Name_x':'SalesGroupName'}, inplace=True)
        else:
            sgn_etc = df2[df2['Sales Group Name_y']=='ETC']
            sgn_uneq = df2[df2['Sales Group Name_x']!=df2['Sales Group Name_y']]
            if (sgn_etc.equals(sgn_uneq)==True):
                df2.drop('Sales Group Name_y', axis=1, inplace=True)
                df2.rename(columns={'Sales Group Name_x':'SalesGroupName'}, inplace=True)
        if (df2['Customer_x'].equals(df2['Customer_y'])==True):
            df2.drop('Customer_y', axis=1, inplace=True)
            df2.rename(columns={'Customer_x':'Customer'}, inplace=True)
        if (df2['Retail Environment Ps'].equals(df2['Retail Environment (PS)'])==True):
            df2.drop('Retail Environment (PS)', axis=1, inplace=True)
            df2.rename(columns={'Retail Environment Ps':'RetailEnvPS'}, inplace=True) 
        if (df2['Pop Name'].equals(df2['POP Name'])==True):
            df2.drop('Pop Name', axis=1, inplace=True)
            df2.rename(columns={'POP Name':'POP_Name'}, inplace=True)
        # Drop Lat and Long since it is all composed of 0
        df2.drop(['Longitude','Latitude'], axis=1, inplace=True)
        
        # Address to Area column
        df2["Area"] = df2["Address"].replace({"인천시":"경기도", "부천시":"경기도",
                                             "광주시":"전라남도", "광주광역시":"전라남도", "전남":"전라남도",
                                             "대구시":"경상북도", "포항시":"경상북도", "대구광역시":"경상북도",
                                             "구미시":"경상북도", "경북":"경상북도", "경산시":"경상북도",
                                             "부산시":"경상남도", "울산시":"경상남도", "부산광역시":"경상남도", "경남":"경상남도",
                                             "대전시":"충청남도", "세종시":"충청남도"})
        
        # Drop columns that only contain one value
        # same value in all the rows of the column
        df3 = df2.copy()
        # print(df3.columns)
        for col in df3:
            if len(df2[col].unique())==1:
                df3.drop(str(col), axis=1, inplace=True)
        
        # Only Select Columns to be used for Dashboard and Data Analysis
        # OTC Store & SKU columns
        df4 = df3[["SalesGroupName", "Customer", "POPDB_ID", "POP Code", "POP_Name", "Area", "Comments", "External Store Code",
                   "Brand L4", "Sku Code", "Sku English", "Visit Date", "Last Visit", "입점 여부"]]
        
        # drop duplicated EAN Codes (due to multiple SKUs
        # only leave the first row
        single_hier = skuhier.drop_duplicates(subset = ['EAN Code'], keep = 'first')
        
        # merge based on SKU and EAN
        # both mean same content(88code), but different column names in each dataframe
        df5 = pd.merge(df4, single_hier, how='left', left_on='Sku Code', right_on='EAN Code')
        # 88 Code is expressed as EAN Code in JNJ, so leave column name as EAN
        if (df5['Sku Code'].equals(df5['EAN Code'])==True):
            df5.drop('Sku Code', axis=1, inplace=True)
        
        # drop one of the same columns
        if (df5["Brand L4"].equals(df5["Product Hierarchy L4"])==True):
            df5.drop("Brand L4", axis=1, inplace=True)
            
        # drop "SKU Code" column
        df5.drop("SKU Code", axis=1, inplace=True)
            
        # rename columns to one without space
        df5.rename(columns={'POP Code':'POP_Code',
                    'External Store Code':'ExternalStoreCode',
                    'Sku English':'SKU_Eng',
                    'Visit Date':'VisitDate',
                    'Last Visit':'LastVisit',
                    '입점 여부':'placement',
                    'Last Visit':'LastVisit',
                    'Product Hierarchy L2':'L2_RegFranchise',
                    'Product Hierarchy L3':'L3_Franchise',
                    'Product Hierarchy L4':'L4_Brand',
                    'Product Hierarchy L5':'L5_Subcategory',
                    'Product Hierarchy L6':'L6_Platform',
                    'Product Hierarchy L7':'L7_Variance',
                    'Product Hierarchy L8':'L8_PackSize',
                    'EAN Code':'EAN_Code'
                   }, inplace=True)
            
        return df5
    
    def plmtmap(self):
        df6 = self.cleanup()
        # map 1,0 to placement
        df6['placement'] = df6['placement'].map({'Yes':1, 'No':0})
        
        return df6
    
    def timefmt(self):
        df7 = self.plmtmap()
        # turn column values into same datetime format
        df7['VisitDate'] = pd.to_datetime(df7['VisitDate'], yearfirst=True)
        df7['LastVisit'] = pd.to_datetime(df7['LastVisit'], yearfirst=True)
        df7['YearMonth'] = df7["VisitDate"].dt.strftime("%Y%m")
        
        # add Week of Visit Column
        # deprecated: df7['VisitWeek'] = df7['VisitDate'].dt.weekofyear
        df7['VisitWeek'] = df7['VisitDate'].dt.isocalendar().week
        
        return df7
    
    def savecsv(self):
        df8 = self.timefmt()
        df8.to_csv("./datafiles/otcskumaster.csv", index=False, encoding="utf-8-sig")
        print(self.finish)