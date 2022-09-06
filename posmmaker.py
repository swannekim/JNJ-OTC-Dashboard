#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import numpy as np
import copy
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class FormPosm:
    
    def __init__(self):
        self.finish = 'posm data formatted'
        
    def readcsv(self):
        # POSM Data
        df = pd.read_csv("./rawdata/OTC_JNJ_POSM.csv", engine="python", encoding="utf-8")
        
        return df
    
    def cleanup(self):
        df1 = self.readcsv()
        
        # Drop columns that only contain one value
        # same value in all the rows of the column
        for col in df1:
            if len(df1[col].unique())==1:
                df1.drop(str(col), axis=1, inplace=True)
                
        # Address to Area column
        df1["Area"] = df1["Address"].replace({"인천시":"경기도", "부천시":"경기도",
                                              "광주시":"전라남도", "광주광역시":"전라남도", "전남":"전라남도",
                                              "대구시":"경상북도", "포항시":"경상북도", "대구광역시":"경상북도",
                                              "구미시":"경상북도", "경북":"경상북도", "경산시":"경상북도",
                                              "부산시":"경상남도", "울산시":"경상남도", "부산광역시":"경상남도", "경남":"경상남도",
                                              "대전시":"충청남도", "세종시":"충청남도"})
        
        # shift column to first position
        first_column = df1.pop("Area")
        # insert column using insert(position,column_name,first_column) function
        df1.insert(3, "Area", first_column)
        # drop original Address column
        df1.drop("Address", axis=1, inplace=True)
        
        # create dictionary for renaming columns
        # key = old name
        # value = new name
        mydict = {"Sales Group Name": "SalesGroupName",
                  "Pop Name": "PopName",
                  "Brand L4": "L4_Brand",
                  "Year of Visit Date": "VisitYear",
                  "Visit Date": "VisitDate",
                  "Display Name": "InvstType",
                  "Q2. POSM 미설치 사유를 선택해주세요.": "NInstalled",
                  "Q3. POSM이 설치되어있는 위치는 어디인가요?": "InstallLoc"
                 }
        # call rename () method
        df1.rename(columns = mydict, inplace=True)
        
        # datetime format
        df1["VisitDate"] = pd.to_datetime(df1["VisitDate"], yearfirst=True)
        
        return df1
    
    def popbrandct(self):
        df2 = self.cleanup()
        
        # add column with visit count by POP and Brand
        df2["BInvstFreq"] = df2.groupby(["PopName", "L4_Brand"])["L4_Brand"].transform("count")
        # df2[df2["BInvstFreq"]>1]
        # sort by visit date (early~late) within sorted POP and Brand
        df2_gsrt = df2.sort_values(["PopName", "L4_Brand", "VisitDate"]).groupby(["PopName", "L4_Brand"])
        df3 = df2_gsrt.apply(lambda x: x) 
        df3.reset_index(inplace=True)
        
        return df3
        
    def taskdates(self):
        odf = self.cleanup()
        
        task = []
        tasks = []
        invstlist = odf["InvstType"].unique()
        
        for invst in invstlist:
            task.append(str(invst))
            task.append(odf[odf["InvstType"]==str(invst)]["VisitDate"].min())
            task.append(odf[odf["InvstType"]==str(invst)]["VisitDate"].max())
            tasks.append(task)
            task = []
        
        # create dataframe with unique tasks, investigation start and end dates
        taskdf = pd.DataFrame(tasks, columns =["task", "start", "end"])
        taskdf.sort_values(by="start", ascending=True, inplace=True, ignore_index=True)
        
        return taskdf

    def execution(self):
        df4 = self.cleanup()
        
        # add column with visit count by POP and Investment Type(Task)
        df4["InvstFreq"] = df4.groupby(["PopName", "InvstType"])["InvstType"].transform("count")
        
        # calculate execution by row
        df4["Execution"] = 0
        for i in range(len(df4)):
            # some value in InstallLoc column: execution = 1
            if (pd.isnull(df4.loc[i, "InstallLoc"])==False):
                df4.loc[i, "Execution"] = 1
            # some value in NInstalled column: execution = 0
            elif (pd.isnull(df4.loc[i, "NInstalled"])==False):
                df4.loc[i, "Execution"] = 0
        
        # cumulative sum of execution
        # for same tasks in one pop, calculate cumulative sum
        df4["ExctCsum"] = df4.groupby(["PopName","InvstType"])["Execution"].cumsum()
        
        # calculate execution
        df4["ExctCalc"] = df4["ExctCsum"]
        for i in range(len(df4)):
            # over 1 in ExctCsum column : POSM calculated as executed
            if (df4.loc[i, "ExctCsum"]>=1):
                df4.loc[i, "ExctCalc"] = 1
            # 0 in ExctCsum column : POSM calculated as executed
            else:
                df4.loc[i, "ExctCalc"] = 0
        
        return df4
    
    def exctrate(self):
        df5 = self.execution()
        
        # ExctCalc : 1 row goes first compared to 0 row
        # VisitDate : from old to new
        # can get first visit date when POSM was executed or when Investigation started
        dfsrt1 = df5.sort_values(["ExctCalc","VisitDate"],ascending=[False, True]).groupby(["InvstType", "PopName"])
        df6 = dfsrt1.apply(lambda x: x) 
        df6.reset_index(inplace=True)
        # multiple rows in same OTC(PopName) dropped for calculation
        df6.drop_duplicates(subset=["InvstType", "PopName"], keep = "first", inplace = True)
        df6["ExctRateMAX"] = df6.groupby(["InvstType"])["ExctCalc"].transform("mean")
        
        # ExctCalc : 0 row goes first compared to 1 row
        # VisitDate : from new to old
        # can get last visit date when POSM was not executed or when Investigation ended
        dfsrt2 = df5.sort_values(["ExctCalc","VisitDate"],ascending=[True, False]).groupby(["InvstType", "PopName"])
        df7 = dfsrt2.apply(lambda x: x) 
        df7.reset_index(inplace=True)
        # multiple rows in same OTC(PopName) dropped for calculation
        df7.drop_duplicates(subset=["InvstType", "PopName"], keep = "first", inplace = True)
        df7["ExctRateMIN"] = df7.groupby(["InvstType"])["ExctCalc"].transform("mean")
        
        # merge back into original dataframe
        df8 = pd.merge(df5, df6, how="left")
        df8["ExctRateMAX"].fillna(method = "ffill", inplace = True)
        df9 = pd.merge(df8, df7, how="left")
        df9["ExctRateMIN"].fillna(method = "ffill", inplace = True)
        df9.drop("index", axis=1, inplace=True)
        
        # add total count of each POSM task since graph shows execution rate
        df9["TotalCount"] = df9.groupby(["InvstType"])["PopName"].transform("nunique")
        # add total count of InstallLoc by each POSM task
        df9["InstallCount"] = df9.groupby(["InvstType","InstallLoc"])["PopName"].transform("nunique")
        # add total count of NInstalled by each POSM task
        df9["NInstallCount"] = df9.groupby(["InvstType","NInstalled"])["PopName"].transform("nunique")
        
        return df9
    
    def exctfig(self):
        df10 = self.exctrate()
        taskdf = self.taskdates()
        
        tasklist = list(taskdf["task"])
        # reversedlist = tasklist[::-1]
        
        df11 = copy.deepcopy(df10)
        # restructure DataFrame in order to make into a graph
        df11.drop_duplicates(subset=["InvstType"], keep = "first", inplace = True)
        
        # add percentage column of execution rate by POSM task
        df11["MIN_ExctRatePCT"] = df11["ExctRateMIN"]*100
        df11["MAX_ExctRatePCT"] = df11["ExctRateMAX"]*100
        
        # add max POSM executed POP count
        df11["MAX_ExctCount"] = round(df11["ExctRateMAX"]*df11["TotalCount"])
        
        # merge tasklists into original dataframe
        merged = pd.merge(df11, taskdf, how="left", left_on="InvstType", right_on="task")
        merged["start"] = merged["start"].dt.date
        merged["end"] = merged["end"].dt.date
        
        subfig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig1 = px.bar(merged, x="InvstType", y=["MIN_ExctRatePCT","MAX_ExctRatePCT"], barmode="group",
                      category_orders={"InvstType": tasklist},
                      text_auto=".3f",
                      labels={"value":"Execution Rate(%)", "TotalCount":"Total Store Count"},
                      hover_data={"variable":False, "InvstType":True, "TotalCount":True},
                      color_discrete_sequence=["#FF6692", "#636EFA", "00CC96"])
        
        fig1.update_yaxes(title=None)
        fig1.update_xaxes(title=None)
        # fig1.show()
        '''
        fig5 = px.line(merged, x="InvstType", y="MAX_ExctCount",
                      category_orders={"InvstType": tasklist},
                      labels={"MAX_ExctCount":"Executed Store Max Count"},
                      hover_data={"MAX_ExctCount":True, "start":True, "end":True})
        fig5.update_traces(line_color="#B6E880")
        fig5.update_traces(yaxis="y2")
        fig5.update_xaxes(categoryorder="array", categoryarray=tasklist)
        '''
        
        fig5 = px.scatter(merged, x="InvstType", y="MAX_ExctCount",
                          category_orders={"InvstType": tasklist},
                          labels={"MAX_ExctCount":"Executed Store Max Count"},
                          color_discrete_sequence=["#B6E880"],
                          hover_data={"MAX_ExctCount":True, "start":True, "end":True})
        fig5.update_traces(marker_size=11, marker_line_color="#00CC96", marker_line_width=2)
        fig5.update_traces(yaxis="y2")
        fig5.update_xaxes(categoryorder="array", categoryarray=tasklist)
        
        subfig.add_traces(fig1.data + fig5.data)
        subfig.layout.xaxis.categoryorder="array"
        subfig.layout.xaxis.categoryarray=tasklist
        subfig.layout.yaxis.title="percentage"
        subfig.layout.yaxis2.title="count"
        subfig.update_layout(height=550, width=1250, title_text="OTC POSM Execution Rate(%) by Tasks")
        # subfig.for_each_trace(lambda t: t.update(line=dict(color=t.marker.color)))
        
        # save html file in static folder
        subfig.write_html("./static/dashboard/posmexct.html")
        
        return subfig
    
    def getfilter(self):
        
        # Object Oriented Programming
        print("Type Year and Month to specify when the Investigation was conducted.")
        while True:
            y = input("Enter Year View Filter: ")
            m = input("Enter Month View Filter: ")
            try:
                year = int(y)
                month = int(m)
                break
            except ValueError:
                print("Please enter in a integer(number) format.")
        
        # format month
        month = "{0:0=2d}".format(int(month))
        
        return year, month
    
    def installed(self):
        df12 = self.exctrate()
        df13 = copy.deepcopy(df12)
        taskdf = self.taskdates()
        year, month = self.getfilter()
        
        # select certain year and month based on start date
        selected = taskdf[taskdf["start"].dt.date>=pd.to_datetime(str(year)+"-"+str(month)+"-01").date()]
        tasklist = list(selected["task"])
        reversedlist = tasklist[::-1]
        
        if (len(reversedlist)//2)>3:
            if (len(reversedlist)%2)==0:
                chartheight = 420*(len(reversedlist)/2)
            else:
                chartheight = 420*((len(reversedlist)//2)+1)
        else:
            if (len(reversedlist)%2)==0:
                chartheight = 450*(len(reversedlist)/2)
            else:
                chartheight = 450*((len(reversedlist)//2)+1)
            
        df13 = df13.dropna(subset=["InstallLoc"])
        
        merged = pd.merge(df13, taskdf, how="left", left_on="InvstType", right_on="task")
        merged["start"] = merged["start"].dt.date
        merged["end"] = merged["end"].dt.date
        mselected = merged[merged["start"]>=pd.to_datetime(str(year)+"-"+str(month)+"-01").date()]
        
        fig2 = px.pie(mselected, names="InstallLoc",
                      facet_col="InvstType", facet_col_wrap=2,
                      facet_col_spacing=0.02,
                      category_orders={"InvstType": reversedlist},
                      height=chartheight, width=1250,
                      hover_data=["InstallCount"],
                      labels={"InstallCount":"Installation Count"},
                      color_discrete_sequence=px.colors.qualitative.Pastel,
                      title="Installed Location by POSM Task (from month"+str(month)+", "+str(year)+")", hole=.2)
        
        fig2.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        
        fig2.update_traces(textposition="inside", textinfo="percent")
        fig2.update_layout(legend=dict(
            yanchor="top", y=0.05,
            xanchor="left", x=0.9
        ), uniformtext_minsize=10, uniformtext_mode="hide")
        
        # fig2.show()
        # save html file in static folder
        fig2.write_html("./static/dashboard/posminstall"+str(year)+str(month)+".html")

        return fig2
    
    def uninstalled(self):
        df14 = self.exctrate()
        df15 = copy.deepcopy(df14)
        taskdf = self.taskdates()
        year, month = self.getfilter()
        
        # select certain year and month based on start date
        selected = taskdf[taskdf["start"].dt.date>=pd.to_datetime(str(year)+"-"+str(month)+"-01").date()]
        tasklist = list(selected["task"])
        reversedlist = tasklist[::-1]
        
        if (len(reversedlist)//2)>3:
            if (len(reversedlist)%2)==0:
                chartheight = 420*(len(reversedlist)/2)
            else:
                chartheight = 420*((len(reversedlist)//2)+1)
        else:
            if (len(reversedlist)%2)==0:
                chartheight = 450*(len(reversedlist)/2)
            else:
                chartheight = 450*((len(reversedlist)//2)+1)
            
        df15 = df15.dropna(subset=["NInstalled"])
        
        merged = pd.merge(df15, taskdf, how="left", left_on="InvstType", right_on="task")
        merged["start"] = merged["start"].dt.date
        merged["end"] = merged["end"].dt.date
        mselected = merged[merged["start"]>=pd.to_datetime(str(year)+"-"+str(month)+"-01").date()]
        
        fig3 = px.pie(mselected, names="NInstalled",
                      facet_col="InvstType", facet_col_wrap=2,
                      facet_col_spacing=0.02,
                      category_orders={"InvstType": reversedlist},
                      height=chartheight, width=1250,
                      hover_data=["NInstallCount"],
                      labels={"NInstallCount":"Non-Installation Count"},
                      color_discrete_sequence=px.colors.qualitative.Pastel,
                      title="Uninstalled Reason by POSM Task (from month"+str(month)+", "+str(year)+")", hole=.2)
        
        fig3.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        
        fig3.update_traces(textposition="inside", textinfo="percent")
        fig3.update_layout(legend=dict(
            yanchor="top", y=0.05,
            xanchor="left", x=0.9
        ), uniformtext_minsize=10, uniformtext_mode="hide")
        
        # fig3.show()
        # save html file in static folder
        fig3.write_html("./static/dashboard/posmuninstall"+str(year)+str(month)+".html")
        
        return fig3
    
    def check(self, row):
        if 1 in row["Execution"]:
            # problem solved: 1
            return 1
        else:
            # problem not solved: 0
            return 0
    
    def multivisit(self):
        df16 = self.exctrate()
        df17 = copy.deepcopy(df16)
        # 같은 task 별로 여러번(한번 이상) 방문한 POP들 중
        # POSM 설치했다가 미설치한 경우, 미설치 사유
        # more than 1 time visit for same POSM task
        mdf = df17[df17["InvstFreq"]>1]
        # for each POP and POSM task group
        # group rows on PopName, InvstType column and get List for Execution column
        gdf = pd.DataFrame(mdf.groupby(["PopName", "InvstType"])["Execution"].apply(list))
        resetdf = gdf.reset_index(level=["PopName", "InvstType"])
        # if there is 1 in execution column, calculate as problem solved
        resetdf["check"] = resetdf.apply(lambda row: self.check(row), axis=1)
        resetdf.drop(labels="Execution", axis=1, inplace=True)
        # cdf = gdf.reset_index(level=["PopName", "InvstType"])
        # merge check column into original dataframe
        merged = pd.merge(mdf, resetdf, how="left", left_on=["PopName", "InvstType"], right_on=["PopName", "InvstType"])
        
        return merged
    
    def unsolved(self):
        df18 = self.multivisit()
        taskdf = self.taskdates()
        
        # select data of POP where each task was never held
        df19 = df18[df18["check"]==0]
        df20 = copy.deepcopy(df19)
        # drop original count columns
        df20.drop(labels="TotalCount", axis=1, inplace=True)
        df20.drop(labels="InstallCount", axis=1, inplace=True)
        df20.drop(labels="NInstallCount", axis=1, inplace=True)
        # add total POP count of NInstalled by each POSM task
        df20["Count"] = df20.groupby(["InvstType","NInstalled"])["PopName"].transform("nunique")
        
        tasklist = list(taskdf["task"])
        reversedlist = tasklist[::-1]
        
        dftasklist = df20["InvstType"].unique()
        selectedlist = []
        for rt in reversedlist:
            if rt in dftasklist:
                selectedlist.append(rt)
        
        if (len(selectedlist)//2)>3:
            if (len(selectedlist)%2)==0:
                chartheight = 420*(len(selectedlist)/2)
            else:
                chartheight = 420*((len(selectedlist)//2)+1)
        else:
            if (len(selectedlist)%2)==0:
                chartheight = 450*(len(selectedlist)/2)
            else:
                chartheight = 450*((len(selectedlist)//2)+1)
        
        fig4 = px.pie(df20, names="NInstalled",
                      facet_col="InvstType", facet_col_wrap=2,
                      facet_col_spacing=0.02,
                      category_orders={"InvstType": selectedlist},
                      height=chartheight, width=1250,
                      hover_data=["Count"],
                      labels={"Count":"Non-Installation Count"},
                      color_discrete_sequence=px.colors.qualitative.Pastel,
                      title="Uninstalled Reason: Pharmacy where POSM task has never been executed", hole=.2)
        
        fig4.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        
        fig4.update_traces(textposition="inside", textinfo="percent")
        fig4.update_layout(legend=dict(
            yanchor="top", y=0.05,
            xanchor="left", x=0.9
        ), uniformtext_minsize=10, uniformtext_mode="hide")
        
        # save html file in static folder
        fig4.write_html("./static/dashboard/posmunsolved.html")
        
        return fig4