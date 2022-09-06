#!/usr/bin/env python
# coding: utf-8

# In[ ]:
# Copyright flxblyy 2022


import pandas as pd
import numpy as np
import copy
import plotly.express as px
import datetime
from plotly.subplots import make_subplots
import plotly.graph_objects as go

class DistGraph:
    
    def __init__(self):
        self.finish = 'monthly, weekly, and filtered distribution graph created'
        self.keysku = ["Tylenol 500mg 10T_R'15", "Tylenol Cold-S 325mg 10T'16",
                      "Nicorette Cool Mint 2mg 30s", "Nicorette Cool Mint 4mg 30s",
                      "Listerine Coolmint 750ml_CR (KR0318)",
                      "Rogaine Foam 60ml_3packs_Male", "Rogaine Foam 60ml_Male"]
        # colors by Brands: Tylenol C, Tylenol P Nicorette, Listerine, Rogaine
        self.cdmap = {"Tylenol Cold-S 325mg 10T'16": "#FFA15A",
                      "Tylenol 500mg 10T_R'15": "#EF553B",
                      "Tylenol ER 650mg 6T'18": "#FF7D6B",
                      "Tylenol 500mg 30T'19": "#FF7D6B",
                      "Women's Tylenol 500mg 10T'15": "#FF7D6B",
                      "Tylenol Chewable 80mg 10T_GSL'15_v2": "#FF7D6B",
                      "Nicorette Cool Mint 2mg 30s": "#00CC96",
                      "Nicorette Cool Mint 4mg 30s": "#00CC96",
                      "Nicorette Invisi Patch 10mg": "#B6E880",
                      "Nicorette Invisi Patch 15mg": "#B6E880",
                      "Nicorette Invisi Patch 25mg": "#B6E880",
                      "Listerine Coolmint 750ml_CR (KR0318)": "#19D3F3",
                      "Rogaine Foam 60ml_3packs_Male": "#636EFA", 
                      "Rogaine Foam 60ml_Male": "#636EFA"}
        # Area orders
        self.arealist = ["서울시","경기도","충청북도","충청남도","경상북도","경상남도","전라북도","전라남도","강원도","제주도"]
        # need to edit start and end month/week according to data file
        self.figlinems = "2021-01-01"
        self.figlineme = "2022-08-01"
        self.figlinews = 1
        self.figlinewe = 52
    
    def readfile(self):
        # Distribution Rate Data
        df = pd.read_csv("./datafiles/otcskudistrate.csv", engine="python", encoding="utf-8")
        return df
    
    def monthly(self):
        mdf = self.readfile()
        
        # protect original datafile
        df1 = mdf.copy()
        # restructure DataFrame in order to make into a graph
        df1.drop_duplicates(subset=["SKU_Eng","YearMonth"], keep = "first", inplace = True)
        # int64 format YYYYMM to string
        df1["YearMonth"] = df1["YearMonth"].astype(str)
        # YYYYMM format to datetime format
        df1["YearMonth"] = pd.to_datetime(df1.loc[df1["YearMonth"].str[-2:] != "13","YearMonth"], format="%Y%m", errors="coerce")
        # datetime format to %Y-%m : plotlyauto-set available format
        df1["YYYYMM"] = df1["YearMonth"].dt.strftime("%Y-%m")
        df1 = df1.sort_values(by="YYYYMM")
        
        # add percentage column of monthly distribution rate by SKU
        df1["MonthlyPCT"] = df1["Monthly_DistRate"]*100
        
        # reorder SKU labels by mean of the total period
        meandf = df1.copy()
        # Monthly Distribution Percentage mean value by SKU
        grpdf = meandf.groupby(["SKU_Eng"])["MonthlyPCT"].agg(["mean"])
        # sort descending
        srtdf = grpdf.sort_values(by="mean", ascending=False)
        # sorted SKU list
        srtlst = srtdf.index.get_level_values(0).tolist()
        
        return df1, srtlst
    
    def savempctcsv(self):
        mydf = self.monthly()[0]
        
        selected = mydf[["SKU_Eng", "EAN_Code", "YYYYMM", "MonthlyPCT"]]
        # change dataframe from long to wide format
        widedf = selected.pivot(index=["SKU_Eng","EAN_Code"], columns="YYYYMM", values="MonthlyPCT")
        widedf.reset_index(inplace=True)
        widedf = widedf.rename_axis(None, axis=1)
        
        lastcol = widedf.iloc[:,-1]
        pycol = widedf.iloc[:,-13]
        pmcol = widedf.iloc[:,-2]
        
        # last month distribution percentage versus past year pct
        widedf["vsPY"] = (lastcol-pycol)
        # last month distriubtion percentage verses past month pct
        widedf["vsPM"] = (lastcol-pmcol)
        
        # save as "./datafiles/otcsku_mpct.csv"
        widedf.to_csv("./datafiles/otcsku_mpct.csv", index=False, encoding="utf-8-sig")
        print("monthly distribution percentage datafile created")
    
    def monthlyfig(self):
        mdf1, skulst = self.monthly()
        
        fig1 = px.line(mdf1, x="YYYYMM", y="MonthlyPCT", color="SKU_Eng",
                       category_orders={"SKU_Eng" : skulst},
                       hover_data={"SKU_Eng":True, "YYYYMM":True, "MonthlyPCT":":.3f"},
                       color_discrete_map=self.cdmap,
                       height=550, width=1250,
                       title="Monthly Distribution Rate(%)")
        
        # make key SKU in a bold text
        bold = self.keysku
        fig1.for_each_trace(lambda t: t.update(name = '<b>' + t.name +'</b>') if t.name in bold else())
        
        # Add buttons that add horizontal target lines by Brand
        linetyp = [dict(type="line", xref="x", yref="y",
                        y0=85, y1=85, x0=self.figlinems, x1=self.figlineme,
                        line=dict(color="MediumPurple", dash="dot"))]
        linetyc = [dict(type="line", xref="x", yref="y",
                        y0=95, y1=95, x0=self.figlinems, x1=self.figlineme,
                        line=dict(color="MediumPurple", dash="dot"))]
        linerog = [dict(type="line", xref="x", yref="y",
                        y0=60, y1=60, x0=self.figlinems, x1=self.figlineme,
                        line=dict(color="MediumPurple", dash="dot"))]
        linenic = [dict(type="line", xref="x", yref="y",
                        y0=90, y1=90, x0=self.figlinems, x1=self.figlineme,
                        line=dict(color="MediumPurple", dash="dot"))]
        linelis = [dict(type="line", xref="x", yref="y",
                        y0=80, y1=80, x0=self.figlinems, x1=self.figlineme,
                        line=dict(color="MediumPurple", dash="dot"))]
        
        fig1.update_layout(
            updatemenus=[
                dict(
                    buttons=[
                    dict(label="None",
                         method="relayout",
                         args=["shapes", []]),
                    dict(label="Tylenol P",
                         method="relayout",
                         args=["shapes", linetyp]),
                    dict(label="Tylenol C",
                         method="relayout",
                         args=["shapes", linetyc]),
                    dict(label="Nicorette",
                         method="relayout",
                         args=["shapes", linenic]),
                    dict(label="Rogaine",
                         method="relayout",
                         args=["shapes", linerog]),
                    dict(label="Listerine",
                         method="relayout",
                         args=["shapes", linelis]),
                    ],
                    type="buttons",
                    direction="right",
                    pad={"r": 10, "t": 10},
                    showactive=True,
                    x=0.8,
                    xanchor="left",
                    y=1.19,
                    yanchor="top"
                )
            ]
        )
        
        fig1.update_layout(
            annotations=[
                dict(text="target PCT",
                     xref="paper", yref="paper",
                     x=0.78, y=1.14,
                     align="left", showarrow=False)
            ]
        )
        
        # fig1.show()
        # save html file in static folder
        fig1.write_html("./static/dashboard/monthly.html")
        
        return fig1
    
    def weekly(self):
        wdf = self.readfile()
        # protect original datafile
        df2 = wdf.copy()
        # restructure DataFrame in order to make into a graph
        df2.drop_duplicates(subset=["SKU_Eng","VisitWeek"], keep = "first", inplace = True)
        df2 = df2.sort_values(by="VisitWeek")
        
        # add percentage column of weekly distribution rate by SKU
        df2["WeeklyPCT"] = df2["Weekly_DistRate"]*100
        
        # reorder SKU labels by mean of the total period
        meandf = df2.copy()
        # Weekly Distribution Percentage mean value by SKU
        grpdf = meandf.groupby(["SKU_Eng"])["WeeklyPCT"].agg(["mean"])
        # sort descending
        srtdf = grpdf.sort_values(by="mean", ascending=False)
        # sorted SKU list
        srtlst = srtdf.index.get_level_values(0).tolist()
        
        return df2, srtlst
    
    def weeklyfig(self):
        wdf2, skulst = self.weekly()
        
        fig2 = px.line(wdf2, x="VisitWeek", y="WeeklyPCT", color="SKU_Eng",
                       category_orders={"SKU_Eng" : skulst},
                       hover_data={"SKU_Eng":True, "VisitWeek":True, "WeeklyPCT":":.3f"},
                       color_discrete_map=self.cdmap,
                       height=550, width=1250,
                       title="Weekly Distribution Rate(%)")
        
        # make key SKU in a bold text
        bold = self.keysku
        fig2.for_each_trace(lambda t: t.update(name = '<b>' + t.name +'</b>') if t.name in bold else())
        
        # Add buttons that add horizontal target lines by Brand
        linetyp = [dict(type="line", xref="x", yref="y",
                        y0=85, y1=85, x0=self.figlinews, x1=self.figlinewe,
                        line=dict(color="MediumPurple", dash="dot"))]
        linetyc = [dict(type="line", xref="x", yref="y",
                        y0=95, y1=95, x0=self.figlinews, x1=self.figlinewe,
                        line=dict(color="MediumPurple", dash="dot"))]
        linerog = [dict(type="line", xref="x", yref="y",
                        y0=60, y1=60, x0=self.figlinews, x1=self.figlinewe,
                        line=dict(color="MediumPurple", dash="dot"))]
        linenic = [dict(type="line", xref="x", yref="y",
                        y0=90, y1=90, x0=self.figlinews, x1=self.figlinewe,
                        line=dict(color="MediumPurple", dash="dot"))]
        linelis = [dict(type="line", xref="x", yref="y",
                        y0=80, y1=80, x0=self.figlinews, x1=self.figlinewe,
                        line=dict(color="MediumPurple", dash="dot"))]
        
        fig2.update_layout(
            updatemenus=[
                dict(
                    buttons=[
                    dict(label="None",
                         method="relayout",
                         args=["shapes", []]),
                    dict(label="Tylenol P",
                         method="relayout",
                         args=["shapes", linetyp]),
                    dict(label="Tylenol C",
                         method="relayout",
                         args=["shapes", linetyc]),
                    dict(label="Nicorette",
                         method="relayout",
                         args=["shapes", linenic]),
                    dict(label="Rogaine",
                         method="relayout",
                         args=["shapes", linerog]),
                    dict(label="Listerine",
                         method="relayout",
                         args=["shapes", linelis]),
                    ],
                    type="buttons",
                    direction="right",
                    pad={"r": 10, "t": 10},
                    showactive=True,
                    x=0.8,
                    xanchor="left",
                    y=1.19,
                    yanchor="top"
                )
            ]
        )
        
        fig2.update_layout(
            annotations=[
                dict(text="target PCT",
                     xref="paper", yref="paper",
                     x=0.78, y=1.14,
                     align="left", showarrow=False)
            ]
        )
        
        # fig2.show()
        # save html file in static folder
        fig2.write_html("./static/dashboard/weekly.html")
        
        return fig2
    
    def getfilter(self):
        ldf = self.readfile()
        # protect original datafile
        df3 = ldf.copy()
        
        # get last column(= selected filter column) of DataFrame
        fdistrate = df3.iloc[:,-1:]
        fname = fdistrate.columns.values.tolist()
        fname = str(fname[0])
        # split column name by _ and put into list
        fchar = fname.split('_')
        # first element of filter column : M or W
        fperiod = str(fchar[0])
        # last element of filter column : pharmacy filter name
        fpharm = str(fchar[-1])
        
        return fperiod, fpharm, fname
        
    
    def filtered(self):
        fdf = self.readfile()
        # protect original datafile
        df4 = fdf.copy()
        # get filters
        period, pharm, fdistrate = self.getfilter()
        
        if (str(pharm)=="Area"):
            fcw=2
            fheight=2300
        elif (str(pharm)=="Customer") | (str(pharm)=="SalesGroupName"):
            fcw=2
            fheight=550
        elif (str(pharm)=="Comments"):
            fcw=2
            fheight=1000
        else:
            pass
        
        # get area list
        arealst = self.arealist
        
        if (period=="M"):
            
            # get sorted SKU list
            skulst = self.monthly()[1]
            
            # restructure DataFrame in order to make into a graph
            df4.drop_duplicates(subset=[str(pharm),"SKU_Eng","YearMonth"], keep = "first", inplace = True)
            # int64 format YYYYMM to string
            df4["YearMonth"] = df4["YearMonth"].astype(str)
            # YYYYMM format to datetime format
            df4["YearMonth"] = pd.to_datetime(df4.loc[df4["YearMonth"].str[-2:] != "13","YearMonth"], format="%Y%m", errors="coerce")
            # datetime format to %Y-%m : plotlyauto-set available format
            df4["YYYYMM"] = df4["YearMonth"].dt.strftime("%Y-%m")
            df4 = df4.sort_values(by="YYYYMM")
            
            # add percentage column of monthly distribution rate by SKU
            df4[str("M"+str(pharm)+"PCT")] = df4[str(fdistrate)]*100
            
            if (str(pharm)=="Area"):
                # facet plots with pharmacy classification filter
                fig3 = px.line(df4, x="YYYYMM", y=str("M"+str(pharm)+"PCT"), color="SKU_Eng",
                               facet_col=str(pharm), facet_col_wrap=fcw,
                               facet_col_spacing=0.07, facet_row_spacing=0.05,
                               category_orders={"SKU_Eng" : skulst, "Area" : arealst},
                               hover_data={"SKU_Eng":True, "YYYYMM":True, str("M"+str(pharm)+"PCT"):":.3f", str(pharm):False},
                               color_discrete_map=self.cdmap,
                               height=fheight, width=1250,
                               title=str("Monthly Distribution Rate(%) by "+str(pharm)))
            
            else:
                # facet plots with pharmacy classification filter
                fig3 = px.line(df4, x="YYYYMM", y=str("M"+str(pharm)+"PCT"), color="SKU_Eng",
                               facet_col=str(pharm), facet_col_wrap=fcw,
                               facet_col_spacing=0.07,
                               category_orders={"SKU_Eng" : skulst},
                               hover_data={"SKU_Eng":True, "YYYYMM":True, str("M"+str(pharm)+"PCT"):":.3f", str(pharm):False},
                               color_discrete_map=self.cdmap,
                               height=fheight, width=1250,
                               title=str("Monthly Distribution Rate(%) by "+str(pharm)))
            
            # deep copy for original value protection
            figlinestart = copy.deepcopy(self.figlinems)
            figlineend = copy.deepcopy(self.figlineme)
        
        elif (period=="W"):
            
            # get sorted SKU list
            skulst = self.weekly()[1]
            
            # restructure DataFrame in order to make into a graph
            df4.drop_duplicates(subset=[str(pharm),"SKU_Eng","VisitWeek"], keep = "first", inplace = True)
            df4 = df4.sort_values(by="VisitWeek")
            
            # add percentage column of monthly distribution rate by SKU
            df4[str("W"+str(pharm)+"PCT")] = df4[str(fdistrate)]*100
            
            if (str(pharm)=="Area"):
                # facet plots with pharmacy classification filter
                fig3 = px.line(df4, x="VisitWeek", y=str("W"+str(pharm)+"PCT"), color="SKU_Eng",
                               facet_col=str(pharm), facet_col_wrap=fcw,
                               facet_col_spacing=0.07, facet_row_spacing=0.05,
                               category_orders={"SKU_Eng" : skulst, "Area" : arealst},
                               hover_data={"SKU_Eng":True, "VisitWeek":True, str("W"+str(pharm)+"PCT"):":.3f", str(pharm):False},
                               color_discrete_map=self.cdmap,
                               height=fheight, width=1250,
                               title=str("Weekly Distribution Rate(%) by "+str(pharm)))
            else:
                # facet plots with pharmacy classification filter
                fig3 = px.line(df4, x="VisitWeek", y=str("W"+str(pharm)+"PCT"), color="SKU_Eng",
                               facet_col=str(pharm), facet_col_wrap=fcw,
                               facet_col_spacing=0.07,
                               category_orders={"SKU_Eng" : skulst},
                               hover_data={"SKU_Eng":True, "VisitWeek":True, str("W"+str(pharm)+"PCT"):":.3f", str(pharm):False},
                               color_discrete_map=self.cdmap,
                               height=fheight, width=1250,
                               title=str("Weekly Distribution Rate(%) by "+str(pharm)))
            
            # deep copy for original value protection
            figlinestart = copy.deepcopy(self.figlinews)
            figlineend = copy.deepcopy(self.figlinewe)
            
        else:
            pass
        
        # make key SKU in a bold text
        bold = self.keysku
        fig3.for_each_trace(lambda t: t.update(name = '<b>' + t.name +'</b>') if t.name in bold else())
        # only leave the categorized name from selected filter
        fig3.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        # show axis values in all subplots
        fig3.update_xaxes(showticklabels=True)
        fig3.update_yaxes(showticklabels=True)
        
        # fig3.show()
        # save html file in static folder
        htmlname = str("./static/dashboard/"+str(period)+str(pharm)+".html")
        fig3.write_html(htmlname)
        
        return fig3