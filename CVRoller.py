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
#If you want to get publication info from ORCID you must install the orcid package

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from re import sub
from collections import OrderedDict, defaultdict
from calendar import month_name
from copy import deepcopy
import pypandoc
import json
#####TODO: figure out if we actually need any of this, if not we can avoid importing
#####citeproc-py unless there's actually a .bib import
from citeproc.py2compat import *


#####################
##     USEFUL      ##
##   FUNCTIONS     ##
#####################

#####################
##      FCN:       ##
##     READ        ##
##    OPTIONS      ##
#####################
def getoptions(block,line='\n',sep=':'):
    #if passed what is already a dict, send it back
    if isinstance(block,dict):
        return block
    else:
        #Break by row
        out = block.split(line)
        #Remove blank entries from blank lines
        #and strip early, in case a line is just a tab or space or something
        out = [i.strip() for i in out if i.strip()]  
        #Split along the :, use maxsplit in case : is in an argument
        out = [i.split(sep,maxsplit=1) for i in out]
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

#####################
##      FCN:       ##
##     REMOVE      ##
##   COMMENTS      ##
#####################
def remove_comments(block):
    #Add \n so that it can catch a comment on the first line
    block = '\n'+block
    #Then, allow comments that don't start on the first character of the line by getting rid of
    #whitespace between a new line and a %
    block = sub('\n+[ \t]+?%','\n%',block)
    #Count how many comments we have and edit that many lines out
    for i in range(0,block.count('\n%')):
        #Cut from the occurrence of the % to the end of the line
        block = block[0:block.find('\n%')+1]+block[block.find('\n%')+1:][block[block.find('\n%')+1:].find('\n')+1:]
    return block

#####################
##      FCN:       ##
##   CHECK DICT    ##
##     DEPTH       ##
#####################
#Lifted straight from https://www.geeksforgeeks.org/python-find-depth-of-a-dictionary/
def dict_depth(dic, level = 1): 
    if not isinstance(dic, dict) or not dic: 
        return level 
    return max(dict_depth(dic[key], level + 1) 
                               for key in dic)             

#####################
##      FCN:       ##
##    READ CV      ##
##      DATA       ##
#####################
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
                sheet = pandas.read_csv(file,dtype={'section':str,'id':str,'attribute':str,'content':str},encoding='cp1252')
            except:
                try:
                    sheet = pandas.read_csv(file,dtype={'section':str,'id':str,'attribute':str,'content':str},encoding='latin1')
                except:
                    try:
                        sheet = pandas.read_csv(file,dtype={'section':str,'id':str,'attribute':str,'content':str},encoding='iso-8859-1')
                    except:
                        try:
                            sheet = pandas.read_csv(file,dtype={'section':str,'id':str,'attribute':str,'content':str},encoding='utf-8')
                        except:
                            raise ValueError('Unable to find working encoding for '+file)
    
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

#####################
##      FCN:       ##
##     READ        ##
##     BIBTEX      ##
#####################
#Obviously, this copies heavily from the citeproc example files.
def readcites(filename,style,keys=None):
    #Get packages we only need if doing this
    # Import the citeproc-py classes we'll use below.
    from citeproc import CitationStylesStyle, CitationStylesBibliography
    from citeproc import formatter
    from citeproc import Citation, CitationItem
    import warnings
    
    #Create full list of attributes to append later
    allatts = {}
    
    #Check if it's a list being sent in from doi
    if isinstance(filename,list):
        from citeproc.source.json import CiteProcJSON
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            bib_source = CiteProcJSON(filename)   
        
        #Keep the original data around to fill back in later after the processing
        allatts = {i['id']:i for i in filename}
        
        #Prune and edit
        #Create topop array to avoid modifying an iterable
        for a in allatts:
            #we don't need references, remove to clean up a bit
            #Can't use other dicts either, but leave them be for now, maybe they can be accessed later.
            #with some crazy syntax
            try:
                allatts[a].pop('reference')
            except:
                pass
            
            #and if it's not a string, make it one. It won't be a pleasant result but at least you'll
            #see why it's not working and avoid error messages
            for i in allatts[a]:
                if not isinstance(allatts[a][i],str):
                    allatts[a][i] = str(allatts[a][i])
    #If it's not a list it should be a filename. Determine which file type we're dealing with
    elif filename[filename.find('.')+1:].lower() == 'bib':
        from citeproc.source.bibtex import BibTeX
        #load in data
        #Try encodings until one sticks.
        try:
            #Catch warnings because otherwise it warns for every unsupported
            #Bibtex attribute type. But we fix this later by bringing them in manually
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                bib_source = BibTeX(filename)
        except:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    bib_source = BibTeX(filename,encoding='latin1')
            except:
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        bib_source = BibTeX(filename,encoding='iso-8859-1')
                except:
                    try:
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            bib_source = BibTeX(filename,encoding='cp1252')
                    except:
                        try:
                            with warnings.catch_warnings():
                                warnings.simplefilter("ignore")
                                bib_source = BibTeX(filename,encoding='utf-8')
                        except:
                            raise ValueError('Unable to find working encoding for '+filename)    
            
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
                keytext = bibtext[bibtext.find('{'+b):]
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
                    
                keytext = {i[0]:i[1] for i in keytext}
                allatts.update({b:keytext})
        except:
            warnings.warn('BibTeX file '+filename+' isn\'t squeaky clean. See layout help file. Couldn\'t import items other than those defined by citeproc-py.')
        
    elif filename[filename.find('.')+1:].lower() == 'json':
        #####TODO: JSON FILE INPUT IS UNTESTED
        from citeproc.source.json import CiteProcJSON
        #load in data
        with open(filename,'r') as jsonfile:
            jsonbib = json.load(jsonfile)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            bib_source = CiteProcJSON(jsonbib)   

        #Keep the original data around to fill back in later after the processing
        allatts = {i['id']:i for i in jsonbib}
        
        for a in allatts:            
            #If it's not a string, make it one. It won't be a pleasant result but at least you'll
            #see why it's not working and avoid error messages
            for i in allatts[a]:
                if not isinstance(allatts[a][i],str):
                    allatts[a][i] = str(allatts[a][i]) 
    else:
        raise ValueError('Filetype for '+filename+' not supported.')
    
    
    
    #If filepath is specified, use that for style.
    if style.find('.csl') > -1:
        bib_style = CitationStylesStyle(style,validate=False)
    elif style.find('/') > -1:
        #If a URL is specified, use that.
        #Otherwise, load it, save it, bring it in        
        import requests
        #Get the file
        csl = requests.get(style)
        #Write it to disk
        with open(style[style.rfind('/')+1:]+'.csl',"w") as f:
            f.write(csl.text)
        bib_style = CitationStylesStyle(style[style.rfind('/')+1:]+'.csl',validate=False)
    else:
        #If it's just the name alone, check for a file, and if it's not there, download it
        try: 
            bib_style = CitationStylesStyle(style+'.csl',validate=False)
        except:
            import requests
            #Get the file
            csl = requests.get('https://www.zotero.org/styles/'+style)
            #Write it to disk
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
        #Add into that dict everything from keytext, but favor bibdata if item names compete!
        bibdata[str(count)] = dict(list(allatts[i].items())+list(bibdata[str(count)].items()))
        #Add in the new data. Change <i> and <b> back to Markdown for LaTeX and Word purposes later
        bibdata[str(count)].update({'item':i,'date':date,'raw':str(bibliography.bibliography()[count]).replace('<b>','**').replace('</b>','**').replace('<i>','*').replace('</i>','*')})
        #bibdata[str(count)] = {'item':i,'date':date,'raw':str(bibliography.bibliography()[count])}
        #Add in all values
        #for j in bib_source[i]:
        #    bibdata[j] = bib_source[i][j]
        count = count + 1
    
    return bibdata

#####################
##      FCN:       ##
##      PREP       ##
##     BIBTEX      ##
#####################
#This determines if there is a .bib file to be read, and if so 
#sets things up for the above readcites() function to work.
def arrangecites(vsd,sec,data):
    try:
        #get the bib options
        bibopt = getoptions(vsd[sec]['bib'],line=',',sep='=')
        
        #If style is missing, default to APA
        try:
            bibopt['style']
        except:
            bibopt['style'] = 'apa'
        
        #If there's a list of keys in the option, start the key list!
        keys = []
        try:
            optkeys = bibopt['keys'].split(';')
            [keys.append(i.strip()) for i in optkeys]
        except:
            pass
        
        #If there's a list of keys in the data, remove them from data but add them to keys
        try:
            for row in data[sec]:
                try:
                    keys.append(data[sec][row]['key'])
                    data[sec].pop(row)
                except:
                    pass
        except:
            pass
        #If neither source had any keys, replace keys with None
        if len(keys) == 0:
            keys = None
        #Now get the formatted citation and add to the data
        try:
            data[sec].update(readcites(bibopt['file'],bibopt['style'],keys))
        except:
            #If it didn't exist up to now, create it
            data[sec] = readcites(bibopt['file'],bibopt['style'],keys)
            
        #By default, sections with .bib entries are sorted by the date attribute
        #So put that in unless an order is already specified
        try:
            vsd[sec]['order']
        except:
            vsd[sec]['order'] = 'date'
    except:
        pass

#####################
##      FCN:       ##
##       DOI       ##
##      CITES      ##
#####################
def arrangedoi(vsd,sec,data):
    try:
        #get options
        doiopt = getoptions(vsd[sec]['doi'],line=',',sep='=')
        
        #If style is missing, default to APA
        try:
            doiopt['style']
        except:
            doiopt['style'] = 'apa'
        
        #if missing lang option, default to en-US. So USA-centric of me!
        try:
            doiopt['lang']
        except:
            doiopt['lang']='en-US'
        
        #If there's a list of keys in the option, start the key list!
        keys = []
        try:
            optkeys = doiopt['doi'].split(';')
            [keys.append(i.strip()) for i in optkeys]
        except:
            pass
        
        #If there's a list of DOIs in the data, remove them from data but add them to keys
        try:
            for row in data[sec]:
                try:
                    keys.append(data[sec][row]['doi'])
                    data[sec].pop(row)
                except:
                    pass
        except:
            pass
        
        #If there's an orcid, get keys from there!
        try:
            doiopt['orcid']
            import orcid
            
            #Open up API
            api = orcid.PublicAPI(doiopt['id'], doiopt['orcid'], sandbox=False)
            #Get search token for public API
            search_token = api.get_search_token_from_orcid()
            #Search for records from that orcid
            summary = api.read_record_public(doiopt['orcid'], 'activities',search_token)
            
            #It will append a thorny path item to the end of 'works'
            summary['works'].pop('path')
            
            #Go through and get the DOIs if ya find em
            #'group' is where the data actually is
            for i in summary['works']['group']:
                #look in external ids, and then to external-id within
                for j in i['external-ids']['external-id']:
                    #check that it's a DOI and if it is add it.
                    if j['external-id-type'] == 'doi':
                        keys.append(j['external-id-value'])
        except:
            pass
        
        #Now get the formatted citation and add to the data
        import requests
        
        #create basic numeric ids
        idnumber = 0
        #and compile them together
        doidata = []
        for k in keys:
            #Get the JSON with ALL the data in case it's needed for something in format
            #and also to get date for ordering
            citedata = requests.get('http://dx.doi.org/'+k,headers={'Accept':'application/citeproc+json'})
            citedata = json.loads(citedata.text)
            
            #Add the id to the data
            citedata['id'] = str(idnumber)
            
            #Remove all jats tags added by crossref
            for i in citedata:
                if isinstance(citedata[i],str):
                    if citedata[i].find('jats:') > -1:
                        #Remove opening and closing jats tags
                        citedata[i] = sub('</*?jats:.+?>','',citedata[i])
            
            #And add to doidata
            doidata.append(citedata)
            
            idnumber = idnumber + 1
        
        #clean up
        del citedata
        
        #Now get the formatted citation and add to the data
        try:
            data[sec].update(readcites(doidata,doiopt['style']))
        except:
            #If it didn't exist up to now, create it
            data[sec] = readcites(doidata,doiopt['style'])
        
        #By default, sections with .bib entries are sorted by the date attribute
        #So put that in unless an order is already specified
        try:
            vsd[sec]['order']
        except:
            vsd[sec]['order'] = 'date'
        
    except:
        pass

#####################
##      FCN:       ##
##     PUBMED      ##
##      CITES      ##
#####################
def arrangepmid(vsd,sec,data):
    try:
        #get options
        pmidopt = getoptions(vsd[sec]['pmid'],line=',',sep='=')
        
        #If style is missing, default to AMA
        try:
            pmidopt['style']
        except:
            pmidopt['style'] = 'american-medical-association'
        
        try:
            pmidopt['database'] = pmidopt['database'].lower()
        except:
            pmidopt['database'] = 'pubmed'
        
        #If there's a list of keys in the option, start the key list!
        keys = []
        if pmidopt['database'] == 'pubmed':
            try:
                optkeys = pmidopt['pmid'].split(';')
                [keys.append(str(i).strip()) for i in optkeys]
            except:
                pass
        elif pmidopt['database'] == 'pmc':
            try:
                optkeys = pmidopt['pmcid'].split(';')
                [keys.append(str(i).strip()) for i in optkeys]
            except:
                pass
        
        #If there's a list of keys in the data, remove them from data but add them to keys
        try:
            for row in data[sec]:
                if pmidopt['database'] == 'pubmed':
                    try:
                        keys.append(str(data[sec][row]['pmid']))
                        data[sec].pop(row)
                    except:
                        pass
                elif pmidopt['database'] == 'pmc':
                     try:
                        keys.append(str(data[sec][row]['pmcid']))
                        data[sec].pop(row)
                     except:
                        pass                   
        except:
            pass
        
        
        #Remove duplicates
        
        #Now get the formatted citation and add to the data
        import requests
        
        #Call from PMID API
        pmidcall = requests.get('https://api.ncbi.nlm.nih.gov/lit/ctxp/v1/'+pmidopt['database']+'/?format=csl&id='+'&id='.join(keys))
        
        #And convert to JSON, conveniently already in the exact format citeproc needs
        pmiddata = json.loads(pmidcall.text)
        
        #clean up
        del pmidcall

        #Citeproc expects a list here, and if there was only one key we won't have one.
        #so make one!
        if len(keys) == 1:
            pmiddata = [pmiddata]
        
        #Now get the formatted citation and add to the data
        try:
            data[sec].update(readcites(pmiddata,pmidopt['style']))
        except:
            #If it didn't exist up to now, create it
            data[sec] = readcites(pmiddata,pmidopt['style'])
        
        #By default, sections with .bib entries are sorted by the date attribute
        #So put that in unless an order is already specified
        try:
            vsd[sec]['order']
        except:
            vsd[sec]['order'] = 'date'
        
    except:
        pass

#####################
##      FCN:       ##
##      SORT       ##
##      DATA       ##
#####################
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
        pass

#####################
##      FCN:       ##
##     DEFAULT     ##
##    THEMING      ##
#####################
def defaulttheme(format, v, vsd):
    if format == 'html':
        #####TODO: Redo this with modern HTML/CSS <div> protocols like a decent human
        #Fill in with defaults
        theme = {}
        theme['header'] = '<html><head><title>{name} CV</title>{style}<meta http-equiv="Content-Type" content="text/html; charset=utf-8"><body>'
        theme['style'] = ('<style>'
             '*{font-family: Georgia, serif;'
             'font-size: medium}'
             'div.section {'
             'border: 0px;'
             'background-color: #FFFFFF;'
             'display: table;'
             'max-width: 70%;'
             'min-width: 70%;'
             'width: 70%;'
             'margin-left: auto;'
             'margin-right: auto}'
             '.sectitle {'
             'text-align: right;'
             'vertical-align: text-top;'
             'color: #009933;'
             'width: 20%;'
             'display: table-cell;'
             'border-right: solid 1px black;'
             'padding: 20px}'
             '.secmeat {'
             'text-align: left;'
             'width: 80%;'
             'display: table-cell;'
             'padding: 20px;}'
             'hr.secdiv {'
             'height: 1px;'
             'border: 0;'
             'width: 25%;'
             'background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0))}'
             '.abstract {font-size:small}'
             '.head.name {'
             'font-size: xx-large;'
             'color: #009933}'
             '.photo {float:left;'
             'padding-right: 40px}'
             '</style>')
        theme['footer'] = '</body></html>'
        
        try: 
            secglue = v['sectionglue']
        except:
            secglue = '\n'

        try:
            secframedef = v['sectionframe']
        except:
            secframedef = '<div class = "section"><div class="sectitle">**{title}**</div><div class="secmeat">{subtitle}{meat}</div></div><br/><hr class="secdiv"/><br/>'  

        try:
            itemwrapperdef = v['itemwrapper']
        except:
            itemwrapperdef = '{item}'  
            
        for sec in vsd:
            #If it's a special title-less format, just put it by itself
            if vsd[sec]['type'] in ['head','date']:
                try:
                    vsd[sec]['sectionframe']
                except:
                    vsd[sec]['sectionframe'] = '<div class = "section"><div class="secmeat">{meat}</div></div>'

    elif format == 'pdf':
        #Note that some strange decisions here, like the % comment lines
        #are to avoid weird pandoc quirks where \ and [ and ] aren't formatted correctly.
        theme = {}
        #{{ and }} evaluate to text { and }. { and } alone work with .format, {{{ and }}} are .format surrounded by a LaTeX {} wrapper.
        theme['header'] = ('%Starting CV document\n'
             '\\documentclass[{fontsize},{papersize},{fontfamily}]{moderncv}\n'
             '\\moderncvstyle{{template}}\n'
             '\\moderncvcolor{{color}}\n'
             '{pagenumbers}\\nopagenumbers{\n'
             '{fontchange}\\renewcommand{\\familydefault}{{font}}\n'
             '\\usepackage[{encoding}]{inputenc}\n'
             '\\usepackage{hanging}\n'
             '\\usepackage[scale={scale}]{geometry}\n')

        theme['options'] = ('fontsize: 11pt\n'
             'papersize: a4paper\n'
             'fontfamily: sans\n'
             'template: classic\n'
             'color: blue\n'
             'pagenumbers: "" \n'
             'fontchange: %\n'
             'font: \\sfdefault\n'
             'scale: 0.75\n'
             'encoding: utf8\n'
             'photowidth: 64pt\n'
             'photoframe: 0.4pt\n')
        
        #No escaping necessary on footer because it is never .formatted
        theme['footer'] = ('%Footer for document\n'
             '\\end{document}\n')
        
        try: 
            secglue = v['sectionglue']
        except:
            secglue = '\n'

        try:
            secframedef = v['sectionframe']
        except:
            secframedef = '\n\\section{{{title}}}  \n{subtitle}  \n{meat}'

        try:
            itemwrapperdef = v['itemwrapper']
        except:
            itemwrapperdef = '{item}\n'  
            
        for sec in vsd:
            #The 'indent' type is just cvitem with a blank first entry
            if vsd[sec]['type'] == 'indent':
                vsd[sec]['itemwrapper'] = '\\cvitem{{}}{{{item}}}'
                        
            #If it's a special format, lead with the \command, fill in the brackets with the format option
            if vsd[sec]['type'] in ['cventry','cvitemwithcomment','cvlistitem','cvitem','cvcolumn']:
                try:
                    vsd[sec]['itemwrapper']
                except:
                    vsd[sec]['itemwrapper'] = '\\'+vsd[sec]['type']+'{item}'
            
            #If it's got a bib option but no specified frame, make it a hanging indent
            try:
                vsd[sec]['bib']
                vsd[sec]['sectionframe'] = '\n\\section{{{title}}}  \n{subtitle}  \n \\begin{{hangparas}}{{.25in}}{{1}} \n {meat} \n \\end{{hangparas}}\n'
            except:
                #Or if it's got the hangingindent type
                if vsd[sec]['type'] == 'hangingindent':
                    try:
                        vsd[sec]['sectionframe']
                    except:
                        vsd[sec]['sectionframe'] = '\n\\section{{{title}}}  \n{subtitle}  \n \\begin{{hangparas}}{{.25in}}{{1}} \n {meat} \n \\end{{hangparas}}\n'
            
            #cvcolumn needs to be surrounded with \begin{cvcolumns}
            if vsd[sec]['type'] == 'cvcolumn':
                try: 
                    vsd[sec]['sectionframe']
                except:
                    vsd[sec]['sectionframe'] = '\n\\section{{{title}}}  \n{subtitle}  \n \\begin{{cvcolumns}} \n {meat} \n \\end{{cvcolumns}}\n'
            
            #If it has a sep option, we don't want that \n after {item}
            try:
                vsd[sec]['sep']
                vsd[sec]['itemwrapper'] = '{item}'
            except:
                #If it doesn't have a sep option, note that for every specified type we don't want
                #line breaks after, since it turns into an invalid double-break
                #So just do '\n' instead of the default '  \n'
                if vsd[sec]['type'] in ['cventry','cvitemwithcomment','cvlistitem','cvitem','cvcolumn','indent']:
                    vsd[sec]['sep']='\n'
            
            #Special moderncv item formats
            #Note triple - {s, two of which are for the LaTeX {, and the third is for .format
            try:
                vsd[sec]['format']
            except:
                if vsd[sec]['type'] == 'cventry':
                    vsd[sec]['format'] = '{{{year}}}{{{accomplishment}}}{{{detail}}}{{}}{{{description}}}'
                elif vsd[sec]['type'] == 'cvitemwithcomment':
                    vsd[sec]['format'] = '{{{accomplishment}}}{{{detail}}}{{{comment}}}'
                elif vsd[sec]['type'] == 'cvlistitem':
                    vsd[sec]['format'] = '{{{raw}}}'
                elif vsd[sec]['type'] in ['cvitem','cvcolumn']:
                    vsd[sec]['format'] = '{{{itemtitle}}}{{{raw}}}'
            
        return theme, secglue, secframedef, itemwrapperdef
    
    elif format == 'md':
        #no theme to speak of
        theme = None
        
        #basic defaults
        try: 
            secglue = v['sectionglue']
        except:
            secglue = '  \n  \n'
            
        try:
            secframedef = v['sectionframe']
        except:
            secframedef = '{title}  \n=========\n {subtitle}  \n{meat}'  

        try:
            itemwrapperdef = v['itemwrapper']
        except:
            itemwrapperdef = '* {item}'  

        for sec in vsd:
            #If it's a special title-less format, just put it by itself
            if vsd[sec]['type'] in ['head','date']:
                try:
                    vsd[sec]['sectionframe']
                except:
                    vsd[sec]['sectionframe'] = '{meat}'
                
            #If there's any sort of weird sep, get rid of the item wrapper
            try:
                vsd[sec]['sep']
                vsd[sec]['itemwrapper'] = '{item}'
            except:
                pass
                    
    return theme, secglue, secframedef, itemwrapperdef

#####################
##      FCN:       ##
##     APPLY       ##
##     THEME       ##
#####################
def applytheming(theme,themeopts,secglue,secframedef,itemwrapperdef,vsd):

    #Allow options to be set, if there's an options section
    try:
        #First, turn content of theme options into dict
        theme['options'] = getoptions(theme['options'])
        #Then, overwrite default options with any user-specified options
        for i in themeopts:
            theme['options'][i] = themeopts[i]
        
        #Insert those options into any part of the theming.
        for i in theme:
            #'options' is a dict not a str, so don't do it there
            if not i == 'options':
                #use sub while looping through existing options rather than format because there are other {}s to not be translated yet (like style)
                for j in theme['options']:
                    theme[i] = sub('{'+j+'}',theme['options'][j],theme[i])
        
    except:
        pass
    
    #Allow user to overwrite parts, and offer defaults if the theme omits them.
    try: 
        secglue = versions[v]['sectionglue']
    except:
        try:
            secglue = theme['sectionglue']
        except:
            pass
        
    try:
        secframedef = versions[v]['sectionframe']
    except:
        try: 
            secframedef = theme['sectionframe']
        except:
            pass
    
    try:
        itemwrapperdef = versions[v]['itemwrapper']
    except:
        try: 
            itemwrapperdef = theme['itemwrapper']
        except:
            pass  
    
    #If theme contains any section-specific theming, bring that in
    for i in theme:
        #If the key is attribute:section that's how we know!
        if i.find('@') > -1:
            #split into attribute and section
            modify = i.split('@')
            #find any sections with that type and modify them.
            for sec in vsd:
                if vsd[sec]['type'] == modify[1]:
                    vsd[sec][modify[0]] = theme[i]
                    
    return theme, themeopts, secglue, secframedef, itemwrapperdef

#####################
##      FCN:       ##
##     BUILD       ##
##     MD CV       ##
#####################
def buildmd(vsd,data,secframedef,secglue,itemwrapperdef,type):
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
                #Build each entry by plugging each entry's attributes into its format
                #Make it a defaultdict so any missing keys return a blank, not an error
                #format_map, not format(**) to allow defaultdict
                for i in data[sec]:
                    data[sec][i]['itemmeat'] = itemwrapper.format(item=s['format'].format_map(defaultdict(lambda:'',data[sec][i])))
                
                #Build section meat by bringing together each item meat
                s['meat'] = s['sep'].join([data[sec][i]['itemmeat'] for i in data[sec]])
                
                #Clean up
                [data[sec][i].pop('itemmeat') for i in data[sec]]
            except:
                pass
        
        
        #If it's latex, preconvert everything to avoid double-conversion
        if type == 'pdf':
            s['title'] = pypandoc.convert_text(s['title'],'latex',format='md',encoding='utf-8')
            #This process will insert a \r\n, take that out
            s['title'] = s['title'][0:-2]
            
            #no-wrap to avoid weird line breaks around character 70.
            s['meat'] = pypandoc.convert_text(s['meat'],'latex',format='md',encoding='utf-8',extra_args=['--no-wrap'])
            try: 
                s['subtitle'] = pypandoc.convert_text(s['subtitle'],'latex',format='md',encoding='utf-8',extra_args=['--no-wrap'])
                s['subtitle'] = s['subtitle'][0:-2]
            except:
                pass
        
        #Build full section
        try:
            s['out'] = secframe.format(title=s['title'],subtitle=s['subtitle']+'  \n  \n',meat=s['meat'])
        except:
            s['out'] = secframe.format(title=s['title'],subtitle='',meat=s['meat'])
        
        '''
        #If it's LaTeX, preconvert each section for links, etc.
        #no-wrap to avoid weird line breaks around character 70.
        if type == 'pdf':
            s['out'] = pypandoc.convert_text(s['out'],'latex',format='md',encoding='utf-8',extra_args=['--no-wrap'])
        '''    
            
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
#TODO: don't hardcode the name of the layout file
with open('layout.txt','r') as structfile:
    struct = structfile.read()

###Start reading CV layout structure
#####TODO: allow generic line-end characters, not just \n

#Remove comments from structure file - lines that start with %.
struct = remove_comments(struct)

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

    #Filling in missing values with defaults:
    #If it's missing a "type" attribute, give it its name, in lower-case, as a default
    try: 
        structdict[str(count)]['type']
    except:
        structdict[str(count)]['type'] = structdict[str(count)]['name'].lower()
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
        pass

#####################
##      BUILD      ##
##       THE       ##
##      FILES      ##
#####################
        
###Loop over each version to create it 
for v in versions:             
    #Create a version-specific copy of the structure.
    #we're gonna overwrite this a lot so do a deep copy
    vsd = deepcopy(structdict)
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
            pass   
    #Limit the vsd to just the sections that are actually in this version        
    for p in topop:
        vsd.pop(p)
    
    #Now remake vsd with named top-level keys
    vsd = OrderedDict({vsd[sec]['name']:vsd[sec] for sec in vsd})
    
    #If there are section-specific attributes, apply them
    for sec in vsd:
        #Create a separate dictionary for updating so the dict isn't modified while looping over it
        optionsupdate = {}
        for att in vsd[sec]:
            #Check for the @-sign that inidcates a version-specific attribute
            if att.find('@') > -1:
                #Check if it applies to this section
                if att[att.find('@')+1:] == v:
                    #write over the original attribute
                    optionsupdate.update({att[:att.find('@')]: vsd[sec][att]})
        vsd[sec].update(optionsupdate)
        #clean up
        del optionsupdate
    
        #Other section-specific processing
        #If there's a bib option, bring in the citations!
        arrangecites(vsd,sec,data)
        
        #If there's a doi option, bring in the citations!
        arrangedoi(vsd,sec,data)
        
        #If there's a pmid option, bring in the citations!
        arrangepmid(vsd,sec,data)
        
        #Now reorder the data as appropriate
        sortitems(vsd,sec,data)
        
                    
        
        
    #Write finished version to file
    #####################
    ##      BUILD      ##
    ##       THE       ##
    ##      HTML       ##
    #####################
    if versions[v]['type'] == 'html':
        #Theme may require name separate
        try:
            for i in data['head']:
                name = data['head'][i]['name']
        except:
            name = ''
        
        #Bring in theme, if present
        try:
            #Split up options
            themeopts = getoptions('themetitle='+versions[v]['theme'],line=',',sep='=')
            
            with open(themeopts['themetitle'],'r') as themefile:
                themetext = themefile.read()
            
            ###Start reading theme layout structure

            #Remove comments from theme file - lines that start with %.
            #First, start the file with a \n so that it can pick up any comments on line 1
            themetext = remove_comments(themetext)

            ###Now to the theme sections
            #Split into sections
            themetext = themetext.split('##')
            #The first line of each section is the key, the rest is the text
            theme = {}
            [theme.update({i[0:i.find('\n')]:i[i.find('\n')+1:]}) for i in themetext]                    
            
            #Defaults to be easily overriden
            secglue = ''
            secframedef = '<table class = "section"><tr><td class="sectitle">**{title}**</td><td class="secmeat">{subtitle}{meat}</td></tr></table><br/><hr class="secdiv"/><br/>'  
            itemwrapperdef = '{item}'
            
            theme,themeopts,secglue,secframedef,itemwrapperdef = applytheming(theme,themeopts,secglue,secframedef,itemwrapperdef,vsd)
            
        except:
            theme, secglue, secframedef, itemwrapperdef = defaulttheme('html',versions[v],vsd)
                
            
        #Apply span wrappers to each element with the naming convention sectionname-attributename
        #Or just sectionname if it's raw
        for sec in vsd:
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
            
            #If there's a span or spanskip attribute, modify the attribute list that gets a span
            try:
                #Look for a span attribute. Split and strip it
                attkeep = vsd[sec]['span'].split(',')
                attkeep = [i.strip() for i in attkeep]
                #Keep only the parts of attlist that are also in attkeep
                attlist = list(set(attlist) & set(attkeep))
                
                #Clean up
                del attkeep
            except:
                pass
            #Now for spanskip
            try:
                #Look for a spanskip attribute. Split and strip it
                attdrop = vsd[sec]['spanskip'].split(',')
                attdrop = [i.strip() for i in attdrop]
                #Keep only parts of attlist that are NOT in attdrop
                attlist = list(set(attlist) - set(attdrop))
                
                #clean up
                del attdrop
            except:
                pass
                
            
            #Now, wherever in the format we see the sub code, replace it with the sub code wrapped in a span
            for a in attlist:
                #Skip the substitution if it's inside parentheses, as that will mess up Markdown translation
                if vsd[sec]['format'][vsd[sec]['format'].find('{'+a+'}')-1] == '(' and vsd[sec]['format'][vsd[sec]['format'].find('{'+a+'}')+len('{'+a+'}')] == ')':
                    ''
                else:
                    vsd[sec]['format'] = sub('{'+a+'}','<span class = "'+vsd[sec]['type']+' '+a+'">{'+a+'}</span>',vsd[sec]['format'])
                
        #Now build it!
        cv = buildmd(vsd,data,secframedef,secglue,itemwrapperdef,versions[v]['type'])
    
        pypandoc.convert_text(theme['header'].format(name=name,style=theme['style'])+cv+theme['footer'],'html',format='md',outputfile=versions[v]['out'],encoding='utf-8')
    #####################
    ##      BUILD      ##
    ##       THE       ##
    ##       PDF       ##
    #####################
    elif versions[v]['type'] == 'pdf':
        try:
            themeopts = getoptions('template='+versions[v]['theme'],line=',',sep='=')
        except:
            pass
        
        #Check if we're dealing with moderncv pdf or from a template file
        pdftype = 'moderncv'
        try:
            if versions[v]['theme'].find('.') > -1:
                pdftype = 'cvroller'
        except:
            pass
        
        #####################
        ##      BUILD      ##
        ##     MODERNCV    ##
        ##       PDF       ##
        #####################
        if pdftype == 'moderncv':        
        
            #Get defaults
            theme, secglue, secframedef, itemwrapperdef = defaulttheme('pdf',versions[v],vsd)
            
            #We need theme['options'] to be a dict before going to apply theming
            theme['options'] = getoptions(theme['options'])
            
            #for pagenumbers and fontchange, 'on' and 'off' translate to 'no comment' and 'comment', respectively
            try:
                if themeopts['pagenumbers'] == 'on':
                    theme['options']['pagenumbers'] = '%'
                themeopts.pop('pagenumbers')
            except:
                pass
            try:
                if themeopts['fontchange'] == 'on':
                    theme['options']['fontchange'] = ' '
                themeopts.pop('fontchange')
            except:
                pass
            
            #Do the format for the head section by hand
            vsd['head']['out'] = ''
            #It only allows one extrainfo, so compile them and put them all in at the end
            extrainfo = ''
            for i in data['head']:
                for j in data['head'][i]:
                    if j in ['title','address','quote']:
                        vsd['head']['out'] = vsd['head']['out'] + '\\'+j+'{'+data['head'][i][j]+'}\n'
                    elif j in ['email']:
                        #Preconvert to get rid of any link framing, doesn't work here
                        emailadd = data['head'][i][j][:]
                        #Just the parts in the parentheses
                        if emailadd.find('(') > -1:
                            emailadd = emailadd[emailadd.find('(')+1:emailadd.find(')')]
                        #And if you've got a mailto:, drop that
                        if emailadd.find('mailto:') > -1:
                            emailadd = emailadd[emailadd.find(':')+1:]
                        #and add 
                        vsd['head']['out'] = vsd['head']['out'] + '\\'+j+'{'+emailadd+'}\n'
                    elif j in ['mobile','fixed','fax']:
                        phoneformat = sub('[ -]','~',data['head'][i][j])
                        vsd['head']['out'] = vsd['head']['out'] + '\\phone['+j+']{'+phoneformat+'}\n'
                    elif j in ['phone']:
                        phoneformat = sub('[ -]','~',data['head'][i][j])
                        vsd['head']['out'] = vsd['head']['out'] + '\\phone{'+phoneformat+'}\n'
                    elif j in ['linkedin','twitter','github']:
                        #preconvert to get rid of any link framing
                        handle = data['head'][i][j][:]
                        #Just the parts in the parentheses
                        if handle.find('(') > -1:
                            handle = handle[handle.find('(')+1:handle.find(')')]
                        #If the whole thing ends with a slash, get rid of it
                        if handle[-1:] == '/':
                            handle = handle[0:-1]
                        #Just the part after the last slash
                        if handle.find('/') > -1:
                            handle = handle[handle.rfind('/')+1:]
                        vsd['head']['out'] = vsd['head']['out'] + '\\social['+j+']{'+handle+'}\n'
                    elif j in ['homepage','website']:
                        #Preconvert to get rid of any link framing, doesn't work here
                        url = data['head'][i][j][:]
                        #Just the parts in the parentheses
                        if url.find('(') > -1:
                            url = url[url.find('(')+1:url.find(')')]
                        vsd['head']['out'] = vsd['head']['out'] + '\\homepage'+'{'+url+'}\n'
                    elif j in ['address1']:
                        #Multi-part addresses
                        try:
                            vsd['head']['out'] = vsd['head']['out'] + '\\address{'+data['head'][i][j]+'}{'+data['head'][i]['address2']+'}{'+data['head'][i]['address3']+'}\n'
                        except:
                            vsd['head']['out'] = vsd['head']['out'] + '\\address{'+data['head'][i][j]+'}{'+data['head'][i]['address2']+'}\n'
                    elif j in ['name']:
                        #split in two
                        namesplit = data['head'][i][j].split(' ',maxsplit=1)
                        namesplit.append('')
                        vsd['head']['out'] = vsd['head']['out'] + '\\name{'+namesplit[0]+'}{'+namesplit[1]+'}\n'
                    elif j in ['name1']:
                        vsd['head']['out'] = vsd['head']['out'] + '\\name{'+data['head'][i][j]+'}{'+data['head'][i]['name2']+'}\n'
                    elif j in ['photo','picture','profile','image']:
                        #Preformat to get rid of any ! image framing, doesn't work here.
                        imgloc = data['head'][i][j][:]
                        #Just the parts in the parentheses
                        if imgloc.find('(') > -1:
                            imgloc = imgloc[imgloc.find('(')+1:imgloc.find(')')]
                        vsd['head']['out'] = vsd['head']['out'] + '\\photo['+theme['options']['photowidth']+']['+theme['options']['photoframe']+']{'+imgloc+'}\n'
                    elif j in ['id']:
                        pass
                        #Skip id.
                    else:
                        #If it's the first extrainfo
                        if len(extrainfo) == 0:
                            extrainfo = data['head'][i][j]
                        else:
                            extrainfo = ', '.join([extrainfo,data['head'][i][j]])
                        
            #If there was any extrainfo, add it
            if len(extrainfo) > 0:
                vsd['head']['out'] = vsd['head']['out'] + '\\extrainfo{'+extrainfo+'}\n'
            #The head section must end with the beginning of the document
            docbegin = ('%Document beginning\n'
                        '\\begin{document}\n'
                        '\\makecvtitle')
            vsd['head']['out'] = vsd['head']['out'] + docbegin
            #Add the head to the header which will also not be translated by pandoc
            theme['header'] = theme['header'] + '\n' + vsd['head']['out']
            #and make sure that buildmd doesn't process the header
            vsd.pop('head')
            
            #and apply theming
            theme,themeopts,secglue,secframedef,itemwrapperdef = applytheming(theme,themeopts,secglue,secframedef,itemwrapperdef,vsd)
                   
            #Now build it!
            cv = buildmd(vsd,data,secframedef,secglue,itemwrapperdef,versions[v]['type'])
            
            #Save the PDF both as a PDF and as a raw .tex file
            #open up and save to a .tex file with the same filename as the eventual pdf but a .tex extension
            with open(versions[v]['out'][0:versions[v]['out'].rfind('.')]+'.tex','w',encoding='utf-8') as texfile:
                texfile.write(theme['header']+cv+theme['footer'])
            
            #Figure out which LaTeX compiler is going to be used
            try:
                versions[v]['processor'] = versions[v]['processor'].lower()
            except:
                versions[v]['processor'] = 'pdflatex'
                
            #and then call it directly to generate the PDF.
            import subprocess
            subprocess.call(versions[v]['processor']+' '+versions[v]['out'][0:versions[v]['out'].rfind('.')]+'.tex')
      
        #####################
        ##      BUILD      ##
        ##      OTHER      ##
        ##       PDF       ##
        #####################
        else:
            #Theme may require name separate
            try:
                for i in data['head']:
                    name = data['head'][i]['name']
            except:
                name = ''
            
            #Bring in theme, which there must be, otherwise would have defaulted to moderncv
            #Split up options
            themeopts = getoptions('themetitle='+versions[v]['theme'],line=',',sep='=')
            
            with open(themeopts['themetitle'],'r') as themefile:
                themetext = themefile.read()
            
            ###Start reading theme layout structure

            #Remove comments from theme file - lines that start with %.
            themetext = remove_comments(themetext)
            ###Now to the theme sections
            #Split into sections
            themetext = themetext.split('##')
            #The first line of each section is the key, the rest is the text
            theme = {}
            [theme.update({i[0:i.find('\n')]:i[i.find('\n')+1:]}) for i in themetext]                    
            
            #Defaults to be easily overriden
            secglue = '\n'
            secframedef = '\n\\section*{{{title}}}  \n{subtitle}  \n{meat}'  
            itemwrapperdef = '{item}\n'

            for sec in vsd:
                #If it has a sep option, we don't want that \n after {item}
                try:
                    vsd[sec]['sep']
                    vsd[sec]['itemwrapper'] = '{item}'
                except:
                    pass
            
            theme,themeopts,secglue,secframedef,itemwrapperdef = applytheming(theme,themeopts,secglue,secframedef,itemwrapperdef,vsd)
            
            #Now build it!
            cv = buildmd(vsd,data,secframedef,secglue,itemwrapperdef,versions[v]['type'])
        
            #Save the PDF both as a PDF and as a raw .tex file
            #open up and save to a .tex file with the same filename as the eventual pdf but a .tex extension
            with open(versions[v]['out'][0:versions[v]['out'].rfind('.')]+'.tex','w',encoding='utf-8') as texfile:
                texfile.write(theme['header']+cv+theme['footer'])
            
            #Figure out which LaTeX compiler is going to be used
            try:
                versions[v]['processor'] = versions[v]['processor'].lower()
            except:
                versions[v]['processor'] = 'pdflatex'
                
            #and then call it directly to generate the PDF.
            import subprocess
            subprocess.call(versions[v]['processor']+' '+versions[v]['out'][0:versions[v]['out'].rfind('.')]+'.tex')

    #####################
    ##      BUILD      ##
    ##       THE       ##
    ##      WORD       ##
    #####################
    elif versions[v]['type'] in ['docx','doc']:
        1
    #####################
    ##      BUILD      ##
    ##       THE       ##
    ##      MARKDOWN   ##
    #####################
    elif versions[v]['type'] in ['md']:
        theme, secglue, secframedef, itemwrapperdef = defaulttheme('md',versions[v],vsd)

        #Now build it!
        cv = buildmd(vsd,data,secframedef,secglue,itemwrapperdef,versions[v]['type'])
    
        pypandoc.convert_text(cv,'md',format='md',outputfile=versions[v]['out'],encoding='utf-8',extra_args=['--no-wrap'])
