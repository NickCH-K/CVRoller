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

#Had to be installed: citeproc-py, pypandoc

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from re import sub
from collections import OrderedDict, defaultdict
from calendar import month_name
import pypandoc
import json
#####TODO: figure out if we actually need any of this, if not we can avoid importing
#####this unless there's actually a .bib import
from citeproc.py2compat import *

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
    #Otherwise we need pandas
    import pandas
    if dbtype in ['xlsx','xls']:
        #Open up the xlsx file and get the sheet
        sheet = pandas.read_excel(file,dtype={'section':str,'id':str,'attribute':str,'content':str})
    elif dbtype == 'csv' :
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
                        try:
                            sheet = pandas.read_csv(file,dtype={'section':str,'id':str,'attribute':str,'content':str},encoding='utf-8')
                        except:
                            raise ValueError('Unable to find working encoding for '+file)
    else:
        raise ValueError('Filetype for '+file+' not supported.')
    
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

#This function reads in citation data in .bib or .json format using citeproc
#Obviously, this copies heavily from the citeproc example files.
def readcites(filename,style,keys=None):
    #Get packages we only need if doing this
    # Import the citeproc-py classes we'll use below.
    from citeproc import CitationStylesStyle, CitationStylesBibliography
    from citeproc import formatter
    from citeproc import Citation, CitationItem
    import warnings
    
    #Determine which file type we're dealing with
    if filename[filename.find('.')+1:].lower() == 'bib':
        from citeproc.source.bibtex import BibTeX
        #load in data
        #Try encodings until one sticks.
        #####TODO: Suppress warnings here.
        try:
            bib_source = BibTeX(filename)
        except:
            try:
                bib_source = BibTeX(filename,encoding='latin1')
            except:
                try:
                    bib_source = BibTeX(filename,encoding='iso-8859-1')
                except:
                    try:
                        bib_source = BibTeX(filename,encoding='cp1252')
                    except:
                        try:
                            bib_source = BibTeX(filename,encoding='utf-8')
                        except:
                            raise ValueError('Unable to find working encoding for '+filename)    
            
        #####TODO: at this point, go BACK through the BibTeX file and pick up all
        #the attributes and add them, even the ones not supported by citeproc-py
        #Based on BibTeX file formatting, this is likely to be fiddly. So let it error out.
        with open(filename,"r") as f:
            bibtext = f.read()
        
        #Convert it to a format where getoptions can read it. 
        #We need each attribute on a single line,
        #and the commas separating attributes need to be \ns
        #Based on BibTeX file formatting, this is likely to be fiddly. So let it error out.
        try:
            for b in bib_source:
                #Isolate options, which begin after the key and a comma,
                #and go until the } that precedes a new line and an @ (the next key)
                #or the end of the file
                
                #SO! start at {key
                keytext = bibtext[bibtext.find('{'+'long_completed_2015'):]
                #Then jump to after the first comma
                keytext = keytext[keytext.find(',')+1:]
                #Now stop the next time we see a \n@, then, very comma followed by a new line is a new item
                keytext = keytext[:keytext.find('\n@')-1].split(',\n')
                #Then, item names/values are split by the first = sign
                keytext = [i.split('=',maxsplit=1) for i in keytext]
                #Strip whitespce and remove curly braces
                keytext = [[sub('[{}]','',i.strip()) for i in j] for j in keytext]
                #If quotes are used to surround, remove those too
                for i in keytext:
                    if ((i[1][0] in ['"',"'"]) and (i[1][len(i[1])-1] in ['"',"'"])):
                        i[1] = i[1][1:len(i[1])-1]
                    #Make these attributes upper-case
                    if (i[0].lower() in ['doi','isbn','issn','pmid']):
                        i[0] = i[0].upper()
                    
                    #Finally, add these items to bib_source, but only if they're not already there.
                    #don't overwrite anything citeproc-py did.
                    try:
                        bib_source[b][i[0]]
                    except:
                        bib_source[b][i[0]] = i[1]
        except:
            warnings.warn('BibTeX file '+filename+' isn\'t squeaky clean. See layout help file. Couldn\'t import items other than those defined by citeproc-py.')
        
    elif filename[filename.find('.')+1:].lower() == 'json':
        #####TODO: JSON INPUT IS UNTESTED
        import json
        from citeproc.source.json import CiteProcJSON
        #load in data
        with open(filename,'r') as jsonfile:
            jsonbib = json.load(jsonfile)
        bib_source = CiteProcJSON(json.loads(jsonbib))   
        
        #pick up all the attributes and add them, even the ones not supported by citeproc-py
        for b in jsonbib:
            bib_source[b['id']].update(b)
        
    else:
        raise ValueError('Filetype for '+filename+' not supported.')
    
    
    
    #If filepath is specified, use that for style.
    if style.find('.csl') > -1:
        bib_style = CitationStylesStyle(style,validate=False)
    else:
        #Otherwise, load it, save it, bring it in, and at the end, delete it
        import requests
        #Get the file
        csl = requests.get(style)
        #Write it to disk
        ######TODO: Is there a way to use this with the file in memory rather than writing it?
        with open(style[style.rfind('/')+1:]+'.csl',"w") as f:
            f.write(csl.text)
        bib_style = CitationStylesStyle(style[style.rfind('/')+1:]+'.csl',validate=False)
    
    #Create bibliography
    bibliography = CitationStylesBibliography(bib_style, bib_source, formatter.html)
    
    #Register citations. If a predetermined list of keys is given, use those.
    #Otherwise, take all keys in file
    if keys == None:
        bibliography.register(Citation([CitationItem(i) for i in bib_source]))
        #Copy over keys so we can iterate over it later
        keys = bib_source
    else:
        bibliography.register(Citation([CitationItem(i) for i in keys]))
        
    #Try to put in reverse chronological order by getting year and month values, if available
    #while building dictionary
    bibdata = OrderedDict()
    count = 0
    for i in keys:
        #Construct date if possible
        try:
            year = bib_source[i]['issued']['year']
        except:
            year = 0
        try:
            month = bib_source[i]['issued']['month']
        except:
            month = 0
        date = str(year*100+month)
        #Turn each part into a regular dict so the data can be easily accessed later
        bibdata[str(count)] = dict(bib_source[i])
        #Add in the new data. Change <i> and <b> back to Markdown for LaTeX and Word purposes later
        bibdata[str(count)].update({'item':i,'date':date,'raw':str(bibliography.bibliography()[count]).replace('<b>','**').replace('</b>','**').replace('<i>','*').replace('</i>','*')})
        #bibdata[str(count)] = {'item':i,'date':date,'raw':str(bibliography.bibliography()[count])}
        #Add in all values
        #for j in bib_source[i]:
        #    bibdata[j] = bib_source[i][j]
        count = count + 1
    
    return bibdata

#This determines if there is a .bib file to be read, and if so 
#sets things up for the above readcites() function to work.
def arrangecites(vsd,sec,data):
    try:
        #split option
        bibopt = vsd[sec]['bib'].split(',')
        #remove whitespace
        bibopt = [i.strip() for i in bibopt]
        #Remove quotes at beginning and end
        for i in bibopt:
            if ((i[0] in ['"',"'"]) and (i[len(i[1])-1] in ['"',"'"])):
                i = i[1:len(i[1])-1]
        #If there's a list of keys in the option, start the key list!
        keys = []
        try:
            optkeys = bibopt[2].split(';')
            [keys.append(i.strip()) for i in optkeys]
        except:
            ''
        
        #If there's a list of keys in the data, remove them from data but add them to keys
        try:
            for row in data[sec]:
                try:
                    keys.append(data[sec][row]['key'])
                    data[sec].pop(row)
                except:
                    ''
        except:
            ''
        #If neither source had any keys, replace keys with None
        if len(keys) == 0:
            keys = None
        
        #Now get the formatted citation and add to the data
        try:
            data[sec].update(readcites(bibopt[0],bibopt[1],keys))
        except:
            #If it didn't exist up to now, create it
            data[sec] = readcites(bibopt[0],bibopt[1],keys)
        
        #By default, sections with .bib entries are sorted by the date attribute
        #So put that in unless an order is already specified
        try:
            vsd[sec]['order']
        except:
            vsd[sec]['order'] = 'date'
    except:
        ''

 
#This applies a data-sorting order, using assigned via 'order' if given
#or by id if not given.
def sortitems(vsd,sec,data):
    #Make sure we actually have data to sort, we won't for, e.g., text or date
    try:
        #If there's an order attribute for the section, get it and use it
        try: 
            sortoption = vsd[sec]['order']
            #Alphabetical option means sort by the raw content
            if sortoption == 'alphabetical':
                data[sec] = OrderedDict(sorted(data[sec].items(), key=lambda t: t[1]['raw']))
            elif sortoption == 'ascending':
                #Attempt to turn ids to numbers
                try:
                    data[sec] = OrderedDict(sorted(data[sec].items(), key=lambda t: float(t[0])))
                except:
                    #but if that's not possible...
                    data[sec] = OrderedDict(sorted(data[sec].items(), key=lambda t: t[0]))
            else:
                #split at comma
                sortoption = [i.strip() for i in sortoption.split(',')]
                #Descending by default
                try:
                    sortoption[1]
                except:
                    sortoption.append('descending')
                
                #And sort by variable by direction
                if sortoption[1] == 'ascending':
                    data[sec] = OrderedDict(sorted(data[sec].items(), key=lambda t: t[1][sortoption[0]]))
                else:
                    data[sec] = OrderedDict(sorted(data[sec].items(), key=lambda t: t[1][sortoption[0]],reverse=True))                    
        except:
            #By default, sort by id in descending order
            #Attempt to turn ids to numbers
            try:
                data[sec] = OrderedDict(sorted(data[sec].items(), key=lambda t: float(t[0]),reverse=True))
            except:
                #but if that's not possible...
                data[sec] = OrderedDict(sorted(data[sec].items(), key=lambda t: t[0],reverse=True))
    except:
        ''

#This constructs a Markdown text file containing the code for the CV
def buildmd(vsd,data,secframedef,secglue,itemwrapperdef):
    #Go through each section to prepare it individually
    for sec in vsd:
        s = vsd[sec]
        
        #Set section frame to default
        try:
            secframe = s['sectionframe']
        except:
            secframe = secframedef
            
            #####heads get no title by default
            if s['type'] == 'head':
                secframe = '{meat}'
        
        try:
            itemwrapper = s['itemwrapper']
        except:
            itemwrapper = itemwrapperdef
        
        #Default separator between entries, unless one is specified
        try:
            s['sep']
        except:
            s['sep'] = '  \n'
        
        #Time to build the meat!
        
        #Check for special types to be generated not from data.
        if s['type'] == 'date':
            from datetime import datetime
            dt = datetime.now()
            year = dt.year
            month = dt.month
            monthname = month_name[month]
            day = dt.day
            hour = dt.hour
            minute = dt.minute
            second = dt.second
            #Create meat
            s['meat'] = itemwrapper.format(item=s['title']+s['format'].format(year=year,month=month,monthname=monthname,day=day,hour=hour,minute=minute,second=second)+'  \n')
        elif s['type'] == 'text':
            s['meat'] = itemwrapper.format(item=s['text'])
        else:            
            #Check that data actually exists for this section
            try:
                data[sec]
                #####TODO: wrap these in tags so that a template file can get them
                #####This may require doing all of this separately by file-out type
                #Build each entry by plugging each entry's attributes into its format
                #Make it a defaultdict so any missing keys return a blank, not an error
                #format_map, not format(**) to allow defaultdict
                for i in data[sec]:
                    data[sec][i]['itemmeat'] = itemwrapper.format(item=s['format'].format_map(defaultdict(lambda:'',data[sec][i])))
                
                #Build section meat by bringing together each item meat
                s['meat'] = s['sep'].join([data[sec][i]['itemmeat'] for i in data[sec]])           
            except:
                ''
     
        #Build full section
        try:
            s['out'] = secframe.format(title=s['title'],subtitle=s['subtitle']+'  \n  \n',meat=s['meat'])
        except:
            s['out'] = secframe.format(title=s['title'],subtitle='',meat=s['meat'])
        
        #Clean up
        s['meat'] = None     
        
    #Glue together sections for full file
    cv = secglue.join([vsd[sec]['out'] for sec in vsd])
    
    return cv


#####################
##     ACTION!     ##
##   EXCITEMENT!   ##
##   ADVENTURE!    ##
##   THE CODE...   ##
##    BEGINS!      ##
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
                            
#Separate metadata into version information and the rest
#Make sure there are versions
if meta.find('version:') == -1 :
    raise ValueError('Layout structure file must specify at least one version to create.')
#Find the first place where a line begins with either an approved metadata option name
#or the ## starting the sections
#don't count the missings.
versionend = min([i for i in [meta.find('\nfile'),meta.find('##')] if i > 0])
options = meta[0:versionend].split('version:')
meta = meta[versionend:]

#Store versions, files, and types
#First, split the version name from the rest
options = [i.split('\n',maxsplit = 1) for i in options]
#Remove blanks
options = [[i for i in j if i] for j in options if j]
#Twice in case there was an existing single blank string
options = [[i for i in j if i] for j in options if j]
#Get options out and store in a dict
#Title should not have quotes or surrounding spaces in it.
versions = {sub('[\'"]','',i[0]).strip():getoptions(i[1]) for i in options}
#Bring in one more with the file type, if not pre-specified
for v in versions:
    try:
        #Figure out if type is specified. If so, make it lowercase
        versions[v]['type'] = versions[v]['type'].lower()
    except:
        #If not, get it from filename
        #Find the index of the out option, then get the second argument to find filename
        filename = versions[v]['out']
        versions[v]['type'] = filename[filename.find('.')+1:].lower()
#Clean up
del options

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
    #If it's missing a "type" attribute, give it a default
    try: 
        structdict[str(count)]['type']
    except:
        structdict[str(count)]['type'] = 'default'
        #Unless it's named 'head', give that a 'head' type by default
        if structdict[str(count)]['name'] == 'head':
            structdict[str(count)]['type'] = 'head'
    #Same with title
    try: 
        structdict[str(count)]['title']
    except:
        structdict[str(count)]['title'] = structdict[str(count)]['name']
        #Unless it's a date, default title 'Last updated: '
        if structdict[str(count)]['type'] == 'date':
            structdict[str(count)]['title'] = 'Last updated: ' 
        #or a text, default title blank
        if structdict[str(count)]['type'] == 'text':
            structdict[str(count)]['title'] = ''
    #And now for format
    try:
        structdict[str(count)]['format']
    except:
        if structdict[str(count)]['type'] == 'date':
            structdict[str(count)]['format'] = '{monthname} {day}, {year}'
        else:
            #Default format for meat, outside of dates, is just to list all the raw data
            structdict[str(count)]['format'] = '{raw}'

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

#####################
##      BUILD      ##
##       THE       ##
##      FILES      ##
#####################
        
###Loop over each version to create it 
for v in versions:             
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

    #If there's a bib option, bring in the citations!
    for sec in vsd:
        arrangecites(vsd,sec,data)
    
    #Now reorder the data as appropriate
    for sec in vsd:
        sortitems(vsd,sec,data)
        
    #Write finished version to file
    if versions[v]['type'] == 'html':
        #Theme may require name separate
        try:
            for i in data['head']:
                name = data['head'][i]['name']
        except:
            name = ''
        
        #Bring in theme, if present
        try:
            with open(versions[v]['theme'],'r') as jsonfile:
                theme = json.load(jsonfile)
            
            #If parts are overwritten
            try: 
                secglue = versions[v]['sectionglue']
            except:
                secglue = theme['sectionglue']
                
            try:
                secframedef = versions[v]['sectionframe']
            except:
                secframedef = theme['sectionframe']
        except:
            #####TODO: Redo this with modern HTML/CSS protocols like a decent human
            #Fill in with defaults
            theme = {}
            theme['header'] = '<html><head><title>{name} CV</title>{style}<meta http-equiv="Content-Type" content="text/html; charset=utf-8"><body>'
            theme['style'] = ('<style>'
                 '*{font-family: Georgia, serif;'
                 'font-size: medium}'
                 'table.section {'
                 'border: 0px;'
                 'background-color: #FFFFFF;'
                 'width: 70%;'
                 'margin-left: auto;'
                 'margin-right: auto}'
                 '.sectitle {'
                 'text-align: right;'
                 'vertical-align: text-top;'
                 'color: #33cc33;'
                 'width: 20%;'
                 'border-right: solid 1px black;'
                 'padding: 20px}'
                 '.secmeat {'
                 'text-align: left;'
                 'width: 80%;'
                 'padding: 20px;}'
                 'hr.secdiv {'
                 'height: 1px;'
                 'border: 0;'
                 'width: 25%;'
                 'background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0))}'
                 '.abstract {font-size:small}'
                 '.head {'
                 'margin-left: auto;'
                 'margin-right: auto;'
                 'text-align: right}'
                 '.head.name {'
                 'font-size: xx-large;'
                 'color: #33cc33}'
                 '.photo {float:left;'
                 'padding-right: 40px}'
                 '</style>')
            theme['footer'] = '</body></html>'
            
            try: 
                secglue = versions[v]['sectionglue']
            except:
                secglue = ''
    
            try:
                secframedef = versions[v]['sectionframe']
            except:
                secframedef = '<table class = "section"><tr><td class="sectitle">**{title}**</td><td class="secmeat">{subtitle}{meat}</td></tr></table><br/><hr class="secdiv"/><br/>'  

            try:
                itemwrapperdef = versions[v]['itemwrapper']
            except:
                itemwrapperdef = '{item}'  
                
            for sec in vsd:
                #If it's a special title-less format, just put it by itself
                if vsd[sec]['type'] in ['head','date']:
                    try:
                        vsd[sec]['sectionframe']
                    except:
                        vsd[sec]['sectionframe'] = '<table class = "section"><tr><td class="secmeat">{meat}</td></tr></table>'
                
                if vsd[sec]['type'] == 'head':
                    vsd[sec]['secframe'] = '<div class = "head">{meat}</div>'
                
                #Apply span wrappers to each element with the naming convention sectionname-attributename
                #Or just sectionname if it's raw
                #Get full list of attributes in the section
                attlist = []
                try:
                    [[attlist.append(i) for i in data[vsd[sec]['name']][j]] for j in data[vsd[sec]['name']]]
                except:
                    if vsd[sec]['type'] == 'date':
                        attlist = ['year','month','monthname','day','hour','minute','second']
                    else:
                        attlist = ['raw']
                        
                #Limit to unique list
                attlist = list(set(attlist))
                
                #Now, wherever in the format we see the sub code, replace it with the sub code wrapped in a span
                for a in attlist:
                    #Skip the substitution if it's inside parentheses, as that will mess up Markdown translation
                    if vsd[sec]['format'][vsd[sec]['format'].find('{'+a+'}')-1] == '(' and vsd[sec]['format'][vsd[sec]['format'].find('{'+a+'}')+len('{'+a+'}')] == ')':
                        ''
                    else:
                        vsd[sec]['format'] = sub('{'+a+'}','<span class = "'+vsd[sec]['type']+' '+a+'">{'+a+'}</span>',vsd[sec]['format'])
                
                
                
        #Now build it!
        cv = buildmd(vsd,data,secframedef,secglue,itemwrapperdef)
    
        pypandoc.convert_text(theme['header'].format(name=name,style=theme['style'])+cv+theme['footer'],'html',format='md',outputfile='cv.html',encoding='utf-8')
    elif versions[v]['type'] == 'pdf':
        #####TODO: Write out to LaTeX, either on base level or with moderncv
        1
    elif versions[v]['type'] in ['docx','doc']:
        1
    elif versions[v]['type'] in ['md']:
        1
        

###Now to construct each section as markdown

###Then turn the markdown into HTML/LaTeX/etc.    