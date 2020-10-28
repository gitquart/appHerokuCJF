from selenium.webdriver.common.by import By
import cassandraSent as bd
import PyPDF2
import uuid
import base64
import time
import json
import os
import sys
import codecs

download_dir='/app/Download'


def appendInfoToFile(path,filename,strcontent):
    txtFile=open(path+filename,'a+')
    txtFile.write(strcontent)
    txtFile.close()

def processRow(browser,strSearch,row):
    pdfDownloaded=False
    for col in range(1,8):
        if col<7:
            if col==1:
                juris_rev=browser.find_elements_by_xpath('//*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']')[0].text
            if col==2:
                filetype=browser.find_elements_by_xpath('//*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']')[0].text
            if col==3:
                subject=browser.find_elements_by_xpath('//*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']')[0].text
            if col==4:
                fileNumber=browser.find_elements_by_xpath('//*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']')[0].text
            if col==5:
                #I remove (') because some text got it and cassandra failed to insert it
                summary=summary=browser.find_elements_by_xpath('//*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']')[0].text
                str(summary).replace("'"," ")
            if col==6:
                date=browser.find_elements_by_xpath('//*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']')[0].text                    

        else:
            #This is the xpath of the link : //*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']/a
            #This find_element method works!
            link=browser.find_element(By.XPATH,'//*[@id="grdSentencias_ctl00__'+str(row)+'"]/td['+str(col)+']/a')
            link.click()
            #Wait until the second window is open and the pdf is downloaded (or not downloaded)
            time.sleep(20)
            if len(browser.window_handles)>1:
                #window_handles changes always
                #If the pdf browser page opens, then the record should be done in Cassandra
                main_window=browser.window_handles[0]
                pdf_window=browser.window_handles[1]
                browser.switch_to_window(pdf_window)
       
                #Build the json by row            
                with open('/app/appcjf/json_sentencia.json') as json_file:
                    json_sentencia = json.load(json_file)

                json_sentencia['id']=str(uuid.uuid4())
                json_sentencia['filenumber']=fileNumber
                data=''
                data=fileNumber.split('/')
                year=0
                year=int(data[1])
                json_sentencia['year']=year
                json_sentencia['filetype']=filetype
                json_sentencia['jurisdictionalreviewer']=juris_rev
                # timestamp accepted for cassandra: yyyy-mm-dd 
                #In web site, the date comes as day-month-year
                dateStr=date.split('/') #0:day,1:month,2:year
                dtDate=dateStr[2]+'-'+dateStr[1]+'-'+dateStr[0]
                json_sentencia['publication_datetime']='1000-01-01'
                json_sentencia['strpublicationdatetime']=dtDate
                json_sentencia['subject']=subject
                json_sentencia['summary']=str(summary).replace("'"," ")    
                #Check if a pdf exists                       
                json_sentencia['lspdfcontent'].clear()
                lsContent=[]
                for file in os.listdir(download_dir):
                    pdfDownloaded=True
                    strFile=file.split('.')[1]
                    if strFile=='PDF' or strFile=='pdf':
                        #content is string
                        lsContent=readPyPDF(file)
       
                #When pdf is done and the record is in cassandra, delete all files in download folder
                #If the pdf is not downloaded but the window is open, save the data without pdf
                if pdfDownloaded==True:
                    for item in lsContent:
                        json_sentencia['lspdfcontent'].append(item)
                    for file in os.listdir(download_dir):
                        os.remove(download_dir+'\\'+file) 

                #Insert information to cassandra
                res=bd.cassandraBDProcess(json_sentencia)
                if res:
                    print('Sentencia added:',str(fileNumber))
                else:
                    print('Keep going...sentencia existed:',str(fileNumber)) 
                    
                browser.close()
                browser.switch_to_window(main_window)    

            else:
                print('The pdf window was not opened',strSearch)
                browser.quit()
                sys.exit(0)  

 

def readPyPDF(file):
    #This procedure produces a b'blabla' string, it has UTF-8
    #PDF files are stored as bytes. Therefore to read or write a PDF file you need to use rb or wb.
    lsContent=[]
    pdfFileObj = open(download_dir+'/'+file, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    pags=pdfReader.numPages
    for x in range(0,pags):
        pageObj = pdfReader.getPage(x)
        #UTF-8 is the right encodeing, I tried ascii and didn't work
        #1. bContent is the actual byte from pdf with utf-8, expected b'bla...'
        bcontent=base64.b64encode(pageObj.extractText().encode('utf-8'))
        lsContent.append(str(bcontent.decode('utf-8')))
                         
    pdfFileObj.close()    
    return lsContent

"""
This is the method to call when fetching the pdf enconded from cassandra which is a list of text
but that text is really bytes.
"""
def decodeFromBase64toNormalTxt(b64content):
    normarlText=base64.b64decode(b64content).decode('utf-8')
    return normarlText
    
    


    


