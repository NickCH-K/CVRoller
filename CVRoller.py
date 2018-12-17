# -*- coding: utf-8 -*-
"""
This is the main file for the automatic CV generator CVRoller.
More specifically, this file outlines a method for reading in a flexible
automatic-document structure file,
as well as a data file, 
and filling in that structure file with the data, then outputting a file.

It's a generic automatic-document generator that happens to be designed for CVs.

@author: nhuntington-klein@fullerton.edu
"""

from re import sub
import pandas
from collections import OrderedDict, defaultdict
from markdown import markdown
from datetime import datetime
from calendar import month_name
import codecs
import json

#####################
##     USEFUL      ##
##   FUNCTIONS     ##
#####################

#This function takes a block of options text and returns those options in a dict
def getoptions(block):
    #Break by row
    out = block.split('\n')
    #Remove blank entries from blank lines
    out = [i for i in out if i]  
    #Split along the :, use maxsplit in case : is in an argument
    out = [i.split(':',maxsplit=1) for i in out]
    #Get rid of trailing and leading spaces
    #and replace \br with line ending space-space-\n
    #####TODO: figure out a better way than establishing \br as an alternate line break to allow line breaks in the options, e.g. for item formats
    out = [[sub(r'\\br','  \n',i.strip()) for i in j] for j in out]
    #and if the option content begins and ends with quotes, get rid of them
    #as that's intended to report the info inside
    for j in out:
        if ((j[1][0] in ['"',"'"]) and (j[1][len(j[1])-1] in ['"',"'"])):
            j[1] = j[1][1:len(j[1])-1]
    #turn into a dict
    outdict = {i[0]:i[1] for i in out}
    return outdict

#This function recursively calculates the depth of a dict, in order to tell
#what kind of JSON file is being opened
#Lifted straight from https://www.geeksforgeeks.org/python-find-depth-of-a-dictionary/
def dict_depth(dic, level = 1): 
    if not isinstance(dic, dict) or not dic: 
        return level 
    return max(dict_depth(dic[key], level + 1) 
                               for key in dic)             

#This function reads in a CV data file and returns it in a dict
def readdata(file,secname):
    ###Now read in the CV data
    #Will be reading it all into this dict
    data = {}
    # Figure out type of CV file it is
    dbtype = file[file.find('.')+1:]

    #####TODO: allow other file types, convert to pandas if not directly readable
    if dbtype in ['xlsx','xls']:
        #Open up the xlsx file and get the sheet
        sheet = pandas.read_excel(file,dtype={'section':str,'id':str,'attribute':str,'content':str})
    if dbtype == 'csv' :
        #Some encoding issues on Windows. Try a few.
        try:
            sheet = pandas.read_csv(file,dtype={'section':str,'id':str,'attribute':str,'content':str})
        except:
            try:
                sheet = pandas.read_csv(file,dtype={'section':str,'id':str,'attribute':str,'content':str},encoding='latin1')
            except:
                try:
                    sheet = pandas.read_csv(file,dtype={'section':str,'id':str,'attribute':str,'content':str},encoding='iso-8859-1')
                except:
                    try:
                        sheet = pandas.read_csv(file,dtype={'section':str,'id':str,'attribute':str,'content':str},encoding='cp1252')
                    except:
                        raise ValueError('Unable to find working encoding for '+file)
    if dbtype == 'json' :
        with open(file,'r') as jsonfile:
            sheet = json.load(jsonfile)
        #Check how many levels deep it goes.
        #Properly formatted, if it's got the section label, it should go 3 deep
        #If it doesn't, it should go 2.
        #Anything else and it's improperly formatted!
        #Note that dict_depth reports what I refer to as "depth" here +1, so it's really
        #3 and 4 we look for
        jsondepth = dict_depth(sheet)
        if jsondepth == 3:
            sheet = {secname:sheet}
        elif jsondepth not in [3,4]:
            raise ValueError('JSON Data Improperly formatted. See help file.')
        return sheet
    
    try:
        #Strip the sections for clarity and lowercase them for matching
        sheet['section'].apply(lambda x: x.strip().lower())
    except:
        #If section is missing, this is a single-section file. Assign section
        sheet['section'] = secname

    #If id, attribute, or content are missing, data is improperly formatted.
    for s in ['id','attribute','content']:
        try:
            sheet[s]
        except:
            raise ValueError(s+' column missing from '+file)

    
    #ensure Content column is all strings
    sheet['content'].apply(str)
    #As is the ID column, in case string IDs are appended later
    sheet['id'].apply(str)
    #If attribute is missing, fill it in with 'raw' for typeless data
    sheet['attribute'].replace('nan','raw',inplace=True)

    #For each section, pull out that data and turn into a dict
    #####TODO: note that missing values currently evaluate to the actual string 'nan'
    #####rather than a NaN or a Null. Is that right?
    for sec in sheet['section'].unique():
        #Pull out the data
        secdata = sheet[sheet['section']==sec]
        #reindex for referencing later
        seclength = len(secdata.index)
        secdata.reset_index(inplace=True)
        
        #A head section gets a shared id
        if sec == 'head':
            secdata = secdata.assign(id = '1')
            #Check if 'id' is entirely missing; if so, fill it in with lower=later
        if sum(secdata['id']=='nan') == seclength:
            secdata = secdata.assign(id = list(range(0,seclength)))
       
        #Create an ordered dict to read the observations into
        secdict = OrderedDict({})
        
        #Go through the observations and read them in to the dict
        for i in range(0,seclength):
            #If this is the first time we've seen this id, initialize
            try: 
                secdict[str(secdata.loc[i]['id'])]
            except:
                secdict[str(secdata.loc[i]['id'])] = {'id':str(secdata.loc[i]['id'])}
            secdict[str(secdata.loc[i]['id'])][secdata.loc[i]['attribute']] = secdata.loc[i]['content']
    
        #And store
        data[sec] = secdict
    
    return data

#This constructs a Markdown text file containing the code for the CV
def buildmd(vsd,data,secframedef,secglue):
    #Go through each section to prepare it individually
    for sec in vsd:
        s = vsd[sec]
        
        #Set section frame to default
        try:
            secframe = s['sectionframe']
        except:
            secframe = secframedef
            
            #####heads and text inserts get no title by default
            if s['type'] in ['head','text']:
                secframe = '{meat}'
        
        #Default separator between entries, unless one is specified
        try:
            s['sep']
        except:
            s['sep'] = '  \n'
        
        #Time to build the meat!
        
        #Check for special types to be generated not from data.
        #####TODO: recognize citation sections by looking for a s['citestyle'] argument
        #####and run the relevant attributes through a CSL to generate the item
        #####Note: https://www.chriskrycho.com/2015/academic-markdown-and-citations.html
        #####May have to use bibtex and locate a bst file for LaTeX?
        if s['type'] == 'date':
            dt = datetime.now()
            year = dt.year
            month = dt.month
            monthname = month_name[month]
            day = dt.day
            hour = dt.hour
            minute = dt.minute
            second = dt.second
            #Allow custom format, but if none available use a default
            try:
                s['format']
            except:
                s['format'] = '{monthname} {day}, {year}'
            s['meat'] = s['title']+s['format'].format(year=year,month=month,monthname=monthname,day=day,hour=hour,minute=minute,second=second)+'  \n'
        elif s['type'] == 'text':
            s['meat'] = s['text']
        else:
            #Default format for meat, outside of dates, is just to list all the raw data
            try:
                s['format']
            except:
                s['format'] = '{raw}'
            
            #Check that data actually exists for this section
            try:
                data[sec]
                #####TODO: wrap these in tags so that a template file can get them
                #####This may require doing all of this separately by file-out type
                #Build each entry by plugging each entry's attributes into its format
                #Make it a defaultdict so any missing keys return a blank, not an error
                #format_map, not format(**) to allow defaultdict
                for i in data[sec]:
                    data[sec][i]['itemmeat'] = s['format'].format_map(defaultdict(lambda:'',data[sec][i]))
                
                #Build section meat by bringing together each item meat
                s['meat'] = s['sep'].join([data[sec][i]['itemmeat'] for i in data[sec]])           
            except:
                ''
     
        #Build full section
        try:
            s['out'] = secframe.format(title=s['title'],subtitle=s['subtitle'],meat=s['meat'])
        except:
            s['out'] = secframe.format(title=s['title'],meat=s['meat'])
        
        #Clean up
        s['meat'] = None     
        
    #Glue together sections for full file
    cv = secglue.join([vsd[sec]['out'] for sec in vsd])
    
    return cv

#####################
##     ACTION!     ##
##   EXCITEMENT!   ##
##   ADVENTURE!    ##
#####################
        
#####TODO: this is a placeholder; include more generic way of locating location file
from os import chdir, getcwd
wd=getcwd()
chdir(wd+'/example')

#####################
##      READ       ##
##       IN        ##
##    METADATA     ##
#####################

#Open up file containing CV layout information
structfile = open('layout.txt','r')
struct = structfile.read()

###Start reading CV layout structure
#####TODO: allow generic line-end characters, not just \n
#####TODO: allow properly formatted JSON structure file to be read in directly
#####TODO: allow comments in structure file

#Remove comments from structure file - lines that start with %.
#Count how many comments we have and edit that many lines out
for i in range(0,struct.count('\n%')):
    #Cut from the occurrence of the % to the end of the line
    struct = struct[0:struct.find('\n%')+1]+struct[struct.find('\n%')+1:][struct[struct.find('\n%')+1:].find('\n')+1:]
#The above procedure doesn't work if there's a comment on the first line
if struct[0] == '%':
    struct = struct[struct.find('\n')+1:]

#Isolate metadata - everything before the first #
meta = struct[0:struct.find('##')]
#Take out of struct
struct = struct[struct.find('##')+2:]
                                            
#Store versions, files, and types
versions = {}
#Get the names of all the CV versions and their output designations
if meta.find('version:') == -1 :
    raise ValueError('Layout structure file must specify at least one version to create.')
else:
    while meta.find('version:') > -1:
        #Cut to start of versions
        meta = meta[meta.find('version:')+8:]
        #Cut the options into segments
        options = [[j.strip() for j in i.split('=')] for i in meta[0:meta.find('\n')].split(',')]
        #if the option content begins and ends with quotes, get rid of them
        #as that's intended to report the info inside
        for o in options:
            #Make sure it's not the name
            if len(o) > 1:
                if ((o[1][0] in ['"',"'"]) and (o[1][len(o[1])-1] in ['"',"'"])):
                    o[1] = o[1][1:len(o[1])-1]
        #Bring in one more with the file type, if not pre-specified
        try:
            #Figure out if type is specified
            [o[0] for o in options].index('type')
        except:
            #If not, get it from filename
            #Find the index of the out option, then get the second argument to find filename
            filename = options[[o[0] for o in options].index('out')][1]
            options.append(['type',filename[filename.find('.')+1:]])
        #Store options as a dict
        optdict = {o[0]:o[1] for o in options[1:]}
        #and add to dict of versions
        versions[options[0][0]] = optdict       
        #And cut to next one
        meta = meta[meta.find('\n')+1:]

#Within metadata, parse all the meta-options
metadict = getoptions(meta)
#Clean up
del meta     

#####################
##      READ       ##
##       IN        ##
##    STRUCTURE    ##
#####################

###Now to the sections
#####TODO: allow two different versions of same-name section
#Split into sections
struct = struct.split('##')
#lead each one off with "name:" so the given title will fill in a name attribute
struct = ['name: '+i for i in struct]
#Split into attributes in a dict
#And convert to dict
structdict = OrderedDict()
count = 1
for i in struct:
    #Name the structures generically to allow the same section name to appear twice
    #(which we want so it can be different in different versions)
    structdict[str(count)] = getoptions(i)

    #Filling in missing values:
    #If it's missing a "type" attribute, fill it in with the name
    try: 
        structdict[str(count)]['type']
    except:
        structdict[str(count)]['type'] = structdict[str(count)]['name']
    #Same with title
    try: 
        structdict[str(count)]['title']
    except:
        structdict[str(count)]['title'] = structdict[str(count)]['name']
        #Unless it's a date, default title 'Last updated: '
        if structdict[str(count)]['type'] == 'date':
            structdict[str(count)]['title'] = 'Last updated: '        
    #And now make sure the name is in lower case for matching
    structdict[str(count)]['name'] = structdict[str(count)]['name'].lower()
    
    count = count + 1
#Clean up
del struct

#####################
##      READ       ##
##       IN        ##
##    CV DATA      ##
#####################

#Read in main data file if present
try:
    data = readdata(metadict['file'],'')
except:
    data = OrderedDict({})
    
#Go through each section. If it has a file specified, add that in
for sec in structdict:
    try: 
        #See if file option is specified. If it is, read it in
        addldata = readdata(structdict[sec]['file'],structdict[sec]['name'])
        #See if section already exists in data. 
        try:
            #If it is, append it.
            data[structdict[sec]['name']].update(addldata[structdict[sec]['name']])
        except:
            # If not, create the section
            data[structdict[sec]['name']] = addldata[structdict[sec]['name']]    
    except:
        ''

######TODO: Fix ordering! Worked before, but it was broken to allow different orderings
######for different versions of same section. Old code:
'''
    #If there's an order attribute for the section, get it and use it
    try: 
        sortoption = structdict[sec]['order']
        #Alphabetical option means sort by the content
        if sortoption == 'alphabetical':
            sortvar = secdata.loc[1]['attribute']
            sortascending = True
        elif sortoption == 'ascending':
            sortascending = True
        else:
            #split at comma
            sortoption = [i.strip() for i in sortoption.split(',')]
            sortvar = sortoption[0]
            if sortoption[1] == 'ascending':
                sortascending = True
    except:
        ''
'''

#####################
##      BUILD      ##
##       THE       ##
##      FILES      ##
#####################

###Loop over each version to create it 
for v in versions:   
    #####TODO: bring in theme gluing together the sections
    #####and setting theming, e.g. styling, from versions[v]['theme']
    ###Until then, some placeholder default glue
    try: 
        secglue = versions[v]['sectionglue']
    except:
        secglue = '\n\n'
    
    #####TODO: bring in theme gluing together the sections
    #####until then, default section frame, or whatever is set in the structure
    try:
        secframedef = versions[v]['sectionframe']
    except:
        secframedef = '**{title}**  \n{meat}'        
        
    #Create a version-specific version of the structure
    vsd = structdict
    #Drop all sections that aren't used in this version
    #Construct this topop array to avoid manipulating an OrderedDict in iteration. Better way?
    topop = []
    for sec in structdict:
        s = structdict[sec]
        #If there's no version option, keep it in by default
        try: 
            secversions = s['version'].split(',')
            secversions = [i.strip() for i in secversions]
            if not v in secversions:
                topop.append(sec)
        except:
            ''   
    for p in topop:
        vsd.pop(p)
    
    #Now remake vsd with named top-level keys
    vsd = OrderedDict({vsd[sec]['name']:vsd[sec] for sec in vsd})
    
    #Now build it!
    cv = buildmd(vsd,data,secframedef,secglue)
    
    #If it asks for the raw code, save it.
    try:
        raw = open(versions[v]['raw'],"w")
        raw.write(cv)
        raw.close()
    except:
        ''
    
    #Write finished version to file
    #####TODO: If it turns out that the meat and sections need to be constructed differently
    #####based on which type it is (for example, because type tags need to be applied differently)
    #####then swap the nesting so this if statement is on the outside, and all the gluing
    #####happens inside, or perhaps in a function to be referenced in the if statement.
    if versions[v]['type'] == 'html':
        #####TODO: bring in theme for outlining structure of file, using the markdown-cv package http://elipapa.github.io/markdown-cv/ ?. For now...
        cv = '<html><head><title>CV</title></head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"><body>'+markdown(cv,extensions=['markdown.extensions.tables'])+'</body></html>'
        
        output_file = codecs.open(versions[v]['out'], "w",
                          encoding="utf-8",
                          errors="xmlcharrefreplace"
                          )
        output_file.write(cv)
        #####TODO: figure out what is necessary to get tables to actually work here
    elif versions[v]['type'] == 'pdf':
        #####TODO: Write out to LaTeX, either on base level or with 
        1
    elif versions[v]['type'] in ['docx','doc']:
        1
        

###Now to construct each section as markdown

###Then turn the markdown into HTML/LaTeX/etc.    