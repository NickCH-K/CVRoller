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


from os import chdir, getcwd
wd=getcwd()
chdir(wd+'/example')

#Open up file containing CV layout information
structfile = open('layout.txt','r')
struct = structfile.read()

###Start reading CV layout structure
#####TODO: allow generic line-end characters, not just \n
#####TODO: allow properly formatted JSON structure file to be read in directly
#####TODO: allow comments in structure file

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
        options = [[j.strip() for j in sub('[\'"]','',i).split('=')] for i in meta[0:meta.find('\n')].split(',')]
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
#split into options
meta = meta.split('\n') 
#Remove blank entries from blank lines
meta = [i for i in meta if i]   
#Split along the :, use maxsplit in case : is in an argument
meta = [i.split(':',maxsplit=1) for i in meta]
#Get rid of trailing and leading spaces, and quotation marks
meta = [[sub(r'\\br','  \n',sub('[\'"]','',i.strip())) for i in j] for j in meta]
#turn into a dict
metadict = {i[0]:i[1] for i in meta}
#Clean up
del meta     

###Now to the sections
#####TODO: allow two different versions of same-name section
#Split into sections
struct = struct.split('##')
#lead each one off with "name:" so the given title will fill in a name attribute
struct = ['name: '+i for i in struct]
#####TODO: figure out a better way than establishing \br as an alternate line break to allow line breaks in the options, e.g. for item formats
#Split into attributes
struct = [i.split('\n') for i in struct]
#Remove blank entries from blank lines
struct = [[i for i in j if i] for j in struct]
#Split along the :, use maxsplit in case : is in an argument
struct = [[i.split(':',maxsplit=1) for i in j] for j in struct]
#unless it's a sep or format argument, strip
for k in struct:
    for j in k:
        j[0] = j[0].strip()
        if j[0] not in ['sep','format']:
            j[1] = j[1].strip()
#Get rid of quotation marks and replace the \brs with Markdown line breaks
struct = [[[sub(r'\\br','  \n',sub('[\'"]','',i)) for i in j] for j in k] for k in struct]

#And convert to dict
structdict = OrderedDict()
for j in struct:
    structdict[j[0][1]] = {i[0]:i[1] for i in j}
    #If it's missing a "type" attribute, fill it in with the name
    try: 
        structdict[j[0][1]]['type']
    except:
        structdict[j[0][1]]['type'] = structdict[j[0][1]]['name']
    #Same with title
    try: 
        structdict[j[0][1]]['title']
    except:
        structdict[j[0][1]]['title'] = structdict[j[0][1]]['name']
        #Unless it's a date, default title 'Last updated: '
        if structdict[j[0][1]]['type'] == 'date':
            structdict[j[0][1]]['title'] = 'Last updated: '        
    #And now make sure the name is in lower case
    structdict[j[0][1]]['name'] = structdict[j[0][1]]['name'].lower()
#Clean up
del struct


###Now read in the CV data
#Will be reading it all into this dict
data = {}
# Figure out type of CV file it is
dbtype = metadict['file'][metadict['file'].find('.')+1:]

#####TODO: allow other file types, convert to pandas if not directly readable
if dbtype in ['xlsx','xls']:
    #Open up the xlsx file and get the sheet
    sheet = pandas.read_excel(metadict['file'],dtype={'section':str,'id':str,'attribute':str,'content':str},encoding='utf-8')
if dbtype == 'csv' :
    sheet = pandas.read_csv(metadict['file'],dtype={'section':str,'id':str,'attribute':str,'content':str})
    
#Strip the sections for clarity and lowercase them for matching
sheet['section'].apply(lambda x: x.strip().lower())
#ensure Content column is all strings
sheet['content'].apply(str)
#If attribute is missing, fill it in with 'raw' for typeless data
sheet['attribute'].replace('nan','raw',inplace=True)

#For each section, pull out that data, put it in order, and turn into a dict
#####TODO: note that missing values currently evaluate to the actual string 'nan'
#####rather than a NaN or a Null. Is that right?
#####TODO: allow sections to have their own data-in files, which then get appended to sheetdict
for sec in sheet['section'].unique():
    #Pull out the data
    secdata = sheet[sheet['section']==sec]
    #reindex for referencing later
    seclength = len(secdata.index)
    secdata.reset_index(inplace=True)
    
    #default sorting
    sortvar = 'id'
    sortascending = False
    
    #A head section gets a shared id
    if sec == 'head':
        secdata = secdata.assign(id = '1')
    #Check if 'id' is entirely missing; if so, fill it in with lower=later
    if sum(secdata['id']=='nan') == seclength:
        secdata = secdata.assign(id = list(range(0,seclength)))
    #####TODO: figure out best way to handle if only some is missing

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
       
    #Create an ordered dict to read the observations into
    secdict = OrderedDict({})
        
    #Go through the observations and read them in to the dict
    for i in range(0,seclength):
        #If this is the first time we've seen this id, initialize
        try: 
            secdict[str(secdata.loc[i]['id'])]
        except:
            secdict[str(secdata.loc[i]['id'])] = {'id':secdata.loc[i]['id']}
        secdict[str(secdata.loc[i]['id'])][secdata.loc[i]['attribute']] = secdata.loc[i]['content']
    
    #Implement the ordering
    secdict = OrderedDict(sorted(secdict.items(), key=lambda x: x[1][sortvar],reverse=not sortascending))
    
    #And store
    data[sec] = secdict
        

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
                topop.append(s['name'])
        except:
            ''   
    for p in topop:
        vsd.pop(p)
    
    
    #Go through each section and add its text to the string
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