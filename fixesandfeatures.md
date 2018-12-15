Near Term Fixes and Features
============================

Small Fixes/Features
--------------------
* Allow layout file to have two different versions of the same-named section
* Improve method for reading in options and layout structure
* Allow commas in version options
* Currently has heavy reliance on layout file ending lines with \n. Be more flexible
* Allow data to be read in from JSON or other format rather than just Excel or CSV
* Allow other spreadsheet formats
* Get CSV import working, it's broken
* Allow structure file to have comments; omit lines starting with comment character(s?) and update Layout Instructions to match
* Is there a better way of getting line breaks from the layout and data files than forcing people to write \br and turning it into space-space-\n?
* Current implementation uses pandas to read in data as strings, which turns missings into the actual string 'nan'. Is that the best way?
* Allow sections to have their own data-in files (especially .bib for citations), then append that data to the main data already read in before processing.
* Currently, if ID is missing in data, it's filled in with 1 to length. That's fine. But how to handle if only SOME ids are missing?
* Turn the following, already in the code, into callable functions for flexibility: loading in data, constructing 'meat'
*Add LaTeX-out and pandoc-out

Big Fixes/Features
------------------
* recognize citation sections by looking for a s['citestyle'] argument and run the relevant attributes through a CSL to generate the item. This may require pandoc and/or routing through BiBTeX first? Note: https://www.chriskrycho.com/2015/academic-markdown-and-citations.html
* Allow theming! Native themes specific to CVRoller (this actually would be a small fix), or, ideally, working with other CV themes like markdown-cv http://elipapa.github.io/markdown-cv/ or LaTeX moderncv https://www.ctan.org/pkg/moderncv. Add theme option to versions.

Medium/Far Term Fixes and Features
----------------------------------

* Import citations from online databases like ORCID and PubMed
* Add scheduler so that if run on a server, will regularly check for updates to data and re-generate files
* Add uploader or FTP so that the generated CVs can be automatically uploaded to a website
* Program/website that makes it easy to generate layout files so people don't have to learn the language
* Program/website that makes it easy to generate CV data file
* Program/website that lets you make an account and just put all the info on there so it can run
