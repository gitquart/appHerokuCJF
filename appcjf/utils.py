
def appendInfoToFile(path,filename,strcontent):
    txtFile=open(path+filename,'a+')
    txtFile.write(strcontent)
    txtFile.close()