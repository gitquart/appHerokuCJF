import json
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import SimpleStatement
import os

pathToHere=os.getcwd()
              
def cassandraBDProcess(json_sentencia):
     
    sent_added=False

    #Connect to Cassandra
    objCC=CassandraConnection()
    cloud_config= {
        'secure_connect_bundle': pathToHere+'\\secure-connect-dbquart.zip'
    }
    
    auth_provider = PlainTextAuthProvider(objCC.cc_user,objCC.cc_pwd)
    cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
    session = cluster.connect()
    session.default_timeout=70
    row=''
    fileNumber=json_sentencia['filenumber']
    #Check wheter or not the record exists, check by numberFile and date
    #Date in cassandra 2020-09-10T00:00:00.000+0000
    querySt="select id from thesis.tbcourtdecisioncjf where filenumber='"+str(fileNumber)+"'  ALLOW FILTERING"
                
    future = session.execute_async(querySt)
    row=future.result()
        
    if row: 
        sent_added=False
        cluster.shutdown()
    else:        
        #Insert Data as JSON
        jsonS=json.dumps(json_sentencia,ensure_ascii=True)           
        insertSt="INSERT INTO thesis.tbcourtdecisioncjf JSON '"+jsonS+"';" 
        future = session.execute_async(insertSt)
        future.result()  
        sent_added=True
        cluster.shutdown()     
                    
                         
    return sent_added

   
class CassandraConnection():
    cc_user='quartadmin'
    cc_keyspace='thesis'
    cc_pwd='P@ssw0rd33'
    cc_databaseID='9de16523-0e36-4ff0-b388-44e8d0b1581f'
        

