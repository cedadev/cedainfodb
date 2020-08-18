import urllib.request, urllib.error, urllib.parse
import xml.etree.ElementTree as xml
import sys
from datetime import *
from dateutil.parser import *

class SpotXMLReader():
    '''
    Parse XML detailing contents & status of a spot.
    Provide methods for returning:
       storagedCurrentStatus
       timeToArchive
       list of aggregations (by id)
       list of files, by aggregation (give id, name, size)
    '''
    
    def __init__(self, id):
        uri = "http://storaged-monitor.esc.rl.ac.uk/storaged_ceda/CEDA_Fileset_File_Details_XML.php?" + id
        self.xml = urllib.request.urlopen(uri).read()
        self.root = xml.fromstring(self.xml)
        #self.root = self.tree.getroot()
        
    def getXML(self):
        return self.xml
    
    def getSpot(self):
        '''return whole spot object'''
        return self.root
        
    def getSpotSummary(self):
        '''return text report of spot showing status of each aggregation'''
        '''Aggregations labelled SYNCED or CACHED_SYNCED are considered OK'''
        '''
        - For data that is synced / cached_synced:
            - Total Vol
            - total no of files
            - latest time to archive
        '''
        spot_id = self.root.find("spot_id").text
        text = "Spot: %s\n" % spot_id
        
        total_volume = 0
        total_files = 0
        latest_time = datetime(1970, 1, 1, 0, 0, 0,)   
        
        aggregations = self.root.findall(".//aggregation")
        #text += "id\tstoragedCurrentStatus\ttimeToArchive\n"

        for i in aggregations:
            aggregation_id = i.find("aggregation_id").text
            storagedCurrentStatus = i.find("storagedCurrentStatus").text
            if (storagedCurrentStatus == "SYNCED" or storagedCurrentStatus == "CACHED_SYNCED"):
                timeToArchive = i.find("timeToArchive").text
                # record latest time
                time = parse(timeToArchive)
                if time > latest_time:
                    latest_time = time
                for item in i.findall("file"):
                    file_size = item.find("file_size").text
                    total_volume = total_volume + int(file_size)
                    total_files += 1
        
        text += "Total volume: %s\n" % total_volume
        text += "Total files: %s\n" % total_files
        text += "Latest time: %s\n" % latest_time
        return text
        
    def getFilesAsDict(self):
        '''get list of files in spot as dict containing (for each file):
            file_name (key)
            file_size (value)
        '''
        # get list of aggregations
        aggregations = self.root.findall(".//aggregation")
        # get list of files within this aggregation, by file_id
        files = dict()
        for i in aggregations:
            for item in i.findall("file"):
                file_id = item.find("file_id").text
                file_name = item.find("file_name").text
                file_size = item.find("file_size").text
                files[file_id] = {
                    'name': urllib.parse.unquote(file_name),
                    'size': file_size,
                }
        return files
        
    def getFilesAsList(self):
        '''get simple list of all filenames in spot'''
        # get list of aggregations
        aggregations = self.root.findall(".//aggregation")
        # get list of files within this aggregation, by file_name
        files = []
        for i in aggregations:
            for item in i.findall("file"):
                file_name = item.find("file_name").text
                files.append(urllib.parse.unquote(file_name))
        return files
                
def main():
    '''simple driver script takes 1 arg : spot name'''
    reader = SpotXMLReader(sys.argv[1])
    
    if len(sys.argv) > 2 and sys.argv[2] == "xml":
        print(reader.getXML())
    else:
        print(reader.getSpotSummary())
        
if __name__=="__main__":
    main()
    
