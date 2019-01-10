CVRoller
=========

This is a script designed to be a generic automatic document compiling language, with an eye on catering to the creation of CVs.

The goal is to have a format for writing document layout structures and data (including from spreadsheet, JSON, .bib, or sites like ORCID or PubMed), then reading in both and spitting out any number of varieties of CV (including website, PDF, and Word).

This project is pretty much ready to go, although there are a few minor features to be filled in, and it currently requires learning the layout language to use. Eventually the goal is to have a system that's easy to use without having to learn too much.

For an explanation of how the CV layout language works, see LayoutInstructions.md. For an explanation on how to put together the CV data file, see CVDataInstructions.md. To figure out how to write your own HTML/CSS theme for CVRoller, see ThemeInstructions.md.

How to Use CVRoller
====================
1. Ensure that you have installed Python, as well as the `citeproc-py` and `pypandoc` packages (both available via `pip`). `pypandoc` also requires that you install `pandoc`, which can be installed separately, done with the `pypandoc` package itself (see `help(pypandoc)`), or if you install `pypandoc` from Anaconda, `pandoc` will be automatically installed.
2. If you want to output PDF files, also ensure that you have installed a LaTeX-to-PDF processor like PDFLatex. The processor should be callable from the command line (which hopefully should be set up automatically when you install LaTeX!). Similarly, if you want to use ORCID to get your citations, make sure you have the `orcid` package installed (also available via `pip`).
3. Read the Instruction files `LayoutInstructions.md` and `CVDataInstructions.md` to see how to construct your CVRoller Layout file and your file(s) of CV data. Also see the files in the `bells_and_whistles_example` and `simple_example` folders for guidance. `bells_and_whistles` includes pretty much every feature CVRoller has to offer, so you can see how everything works, but it's a bit of a mess. `simple_example` is a lot more like what your own CV file is likely to look like.
4. Create a CVRoller Layout file and save it. Put it in a folder.
5. Create any data files you may want - spreadsheets, JSON files, .bib, profile images, themes (check the "themes" folder for some options) etc., and put them in the same folder.
6. Open up CVRoller.py in a Python instance. Go to lines 35 and 36 and tell CVRoller the name of the folder your stuff is in (this can be set to `layoutfolder = ''` if CVRoller.py is in the same folder as your stuff), and the name of your layout file (by default `layoutfile = 'layout.txt'`. By default, if you download the whole repo, this is set to run the example in the `simple_example` folder.
7. Run CVRoller.py! It will output all finished files to the directory specified in `layoutfolder` on line 35.
8. Note that if you're creating a PDF file and you successfully make some .tex output but there's no PDF, try opening the .tex in a LaTeX editor and compiling directly. It will give you more detailed error messages than CVRoller can. One I've run into is not being able to locate fontawesome. This can be fixed by uninstalling the fontawesome package and re-installing it as a *non*-administrator. Another is characters in the original data that LaTeX can't parse, which can be fixed by using more standard characters in the original data.


Near Term Fixes and Features
============================

Makin' Progress! Fixes/Features Added Since First Commit
----------------------------------
* Allow layout file to have two different versions of the same-named section
* Improve method for reading in options and layout structure
* From first-pass code turn important features into callable functions for later flexibility
* Allow structure file to have comments; omit lines starting with comment character(s?) and update Layout Instructions to match
* Allow sections to have their own data-in files (especially .bib for citations), then append that data to the main data already read in before processing.
* Allow data to be read in from JSON or other format rather than spreadsheet
* Add CSV import
* Allow commas in version options
* Import citations from .bib or JSON, format them, order them, display them.
* Turn 'meat' construction into callable functions for flexibility.
* Add LaTeX-out
* Fix many, many LaTeX conversion oddities from pypandoc.
* Suppress citeproc-py warnings for unsupported fields when reading in bibtex files
* Allow version-specific options within a section
* Allow comments that don't start on the first character of the line
* Allow more generic PDF generation without moderncv
* Allow citation import from PubMed, Crossref,and ORCID.

Features that are Completed but Need Testing
----------------------
* JSON citation input
* LaTeX item types other than cvitem
* LaTeX themes and most options for those themes
* LaTeX PDF processors other than pdflatex
* Input files that have various different encodings
* Are there any HTML tags in CSL citation formatting that need to be changed back to Markdown? `<i>` and `<b>` already changed back. But are there others?

Small Fixes/Features to Come
--------------------
* Currently has heavy reliance on layout file ending lines with `\n`. Be more flexible
* Add Word-out
* Put in way of locating layout file other than the placeholder hardcoding.
* Figure out way to allow tables without headers. This should be possible through pandoc with the simple_tables or multiline_tables options but this hasn't been tried yet.
* Figure out the escaping on `##format` arguments in non-moderncv PDF themes. For now it is but a mystery.
* Handle the ORCID id/secret in an easier way than requiring that it be put in in the layout file.
* Allowing citations from multiple different arguments (i.e. a `doi` option AND a `bib` option).
* There's not a way to get a list of someone's PMID's from some sort of repository, is there, like ORCID for DOIs?

Medium/Far Term Fixes and Features to Come
----------------------------------
* Add scheduler so that if run on a server, will regularly check for updates to data and re-generate files
* Add uploader or FTP so that the generated CVs can be automatically uploaded to a website
* Program/website that makes it easy to generate layout files so people don't have to learn the language
* Program/website that makes it easy to generate CV data file
* Program/website that lets you make an account and just put all the info on there so it can run

Original Planned Additions Perhaps Abandoned or Not a Problem
----------------------------------
* Allow other spreadsheet formats <- maybe not necessary, allows CSV, Excel, JSON already
* Current implementation uses pandas to read in data as strings, which turns missings into the actual string 'nan'. Is that the best way?
* Is there a better way of getting line breaks from the layout and data files than forcing people to write \br and turning it into space-space-\n?
* Figure out how to import and use CSL files without having to write them to disk
* Use pypandoc.download_pandoc to install pandoc if it isn't already.