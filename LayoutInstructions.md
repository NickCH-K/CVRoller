How to Write a CVRoller Layout File
===================================

This document will describe how the CVRoller Layout file works.

CVRoller Layout files are simple text documents that outline the sections of a CV and the options for each section.

Comments can be added to layout files using the percent sign `%`. Any line beginning with `%` will be ignored.

CVRoller Layout File Metadata
------------------------------

Each layout file begins with a block of metadata that contains important information to be applied to the whole document. Here's an example:

```
version: web
    out: "cv.html"
	theme: defaulttheme.txt, titlecolor=#FF0000
version: pdf
    out: "HuntingtonKleinCV.pdf"
	theme: banking
	processor: pdflatex
version: wd
    out: "WordCV.docx"
version: rawMD
    out: "rawmarkdown.md"
file: cvdata.xlsx
```

The metadata block begins by listing all the *versions* of the document to be produced. Here we have three versions: web, pdf, and wd. These names can be anything. I could call the PDF version of the CV myCVforEmail and it would work fine. Each time CVRoller is run, it will generate each of these three versions separately. Each of the versions must go at the top of the metadata block.

Currently supported version variations include HTML, PDF (processed using the moderncv LaTeX package), Word (NOT YET SUPPORTED), or Markdown (which provides the raw Markdown code of the CV without any special formatting or theming). If you'd like to have your HTML-styled CV in PDF or Word format, you can make it as an HTML file, open it up in your browser, and use "Print PDF" or "Save Page As..." to turn it into a PDF or Word document. If you plan to do this you may want to find the option in your theme that lets you set the CV to full page width first.

After the versions, other metadata options can be filled in. 

Options available include:

`file`, which tells CVRoller where to find the information that will actually go in the CV. If `file` is not specified in the metadata, each section must have its own `file` option.

As of this writing, no other metadata options are recognized. ADD MORE.


Versions
------------------------------

CVRoller allows you to build multiple different kinds of CVs at once, whether you want a website and PDF version of the same CV, or if you want certain sections to appear in some versions of the CV but not in others (for example, my PDF CV contains the classes I teach, but I don't list this on my website).

Each version option has the following format:

```
version: name
    out: "fileout.type"
	option: "option"
```

Where name is the key you can use to refer to the version, which we'll be using later when we tell CVRoller when to include or exclude sections. The only required option is `out` which tells CVRoller what file it will be writing to. The indentations for options are not required.

Current supported non-required options include:

`theme`, which selects the theme that will be used for formatting. This can be a theme file location, or for PDFs can be the name of the moderncv theme of choice. Any theme options follow a comma, and take the form `option=value`, such as in `theme: defaulttheme.txt, titlecolor=#FF0000`. 

`sectionglue`, which is by default set to two line breaks (`sectionglue: "\br\br"`), tells CVRoller how to 'glue' sections together, i.e. what goes between them. Use `\br` to indicate line breaks, and otherwise use Markdown.

`sectionframe`, tells CVRoller how to attach a section title, referred to as `{title}` to the `{meat}` of the section, which includes all the data. This is by default set to `sectionframe: "**{title}**\br{meat}"` and can be overriden in individual sections by adding `sectionframe` options to those sections. Use `\br` to indicate line breaks, and otherwise use Markdown.

`processor`, for PDF only, is the name of the TeX-to-PDF converter you'd like to use. The processor must be installed directly, and defaults to PDFLaTeX.

Sections
------------------------------

After the metadata, the CVRoller Layout file contains information on each section of the CV to be included, and the options for each section. Here's an example:

```
##working
version: web, pdf
title: "Working Papers"
subtitle: "Please email me at [nhuntington-klein@fullerton.edu](mailto:nhuntington-klein@fullerton.edu) for working PDFs if not linked."
format@web: "{cite} {extra}\br**Abstract**: {abstract}\br"
sectionframe@web: "**{title}**\br*{subtitle}*\br{meat}"
```

Each section starts with the section name, led off by two hash tags `##`. This name tells CVRoller what CV data to pick up. So this section will use CV information tagged for the `working` section (not case-sensitive). It doesn't matter much what you name your sections, except for the head section (with your name, email, etc.), which either must be called `head`, or should have the `type: head` option.

Options can be version-specific, using the `@` symbol. For example, the `format@web` option here will set the `format` option, but only for the version of the CV named `web`. Similarly, `sectionframe` is only set for `web` here, and left as its default value for `pdf`.

No options are required. A section without any options will simply print out all the section entries in the data that aren't assigned an attribute.

Options available include:

`version` tells CVRoller which CV versions to include this section in, separated by commas. By default, each section is included in all versions. So `version: web, pdf` tells CVRoller to include this section in the CVs named `web` and `pdf` but not any others. Note that if you want the same section to show up in multiple versions but *formatted differently* in each of them (for example, perhaps I want `working` to show up in my wd CV but without the abstract), then you can simply make another copy of `##working` in the layout file, give it `version: wd`, and specify the options differently.

`type` determines the section type. This is useful if you have a theme that refers to different section types. `type` will generally be omitted unless you want to use a particular styling offered by your theme, or unless you want to specify a special kind of section (see below). By default, `type` is set to the section name.

`file` tells CVRoller to open up an a file of additional CV data and use it for this section. All data in the file will be applied to this section, so this requires a separate file containing only data for this section. If there is also data for this section specified in the CV-wide data file, both sources of data will be used.

`title` is the title of the section, to be printed. Similarly, `subtitle` is the subtitle. By default, `title` is the section name and subtitle is blank. Use `\br` to indicate line breaks, and otherwise use Markdown.

`format` gives the layout of each item in the section. In the data, I have `cite, extra,` and `abstract` attributes for each item. The `format` option says how all of these attributes should be arranged into a single entry. By default, `format` is either set by theme, or is simply `{raw}` and will list out each of the items given no attribute. Use `\br` to indicate line breaks, `{attributename}` to indicate where particular attributes should go, and otherwise use Markdown. If you have a section where citation data comes from a BibTeX file (see below), you can refer to the formatted citation in your `format` option using `{raw}`.

`sectionframe` is as discussed above for the versions. This overrides the default `sectionframe` argument for just this section. Note that it can be very difficult to get `sectionframe` to work properly with the theme you've chosen, and generally you just want to let the theme handle this one.

`order` determines the order in which items are displayed. By default, each item is displayed in descending order according to its `id` in the data. `order: ascending` will instead use ascending order, `order: alphabetical` will order the items according to the alphabetical order of the *content* of the item, and `order: attributename, ascending` or `order: attributename, descending` will order items according to the `attributename` attribute of each item (which can be any attribute) in ascending or descending order.

`sep` is similar to the `sectionglue` option from the Verisons section above, except that instead of gluing together sections, this glues together items. By default, this is `\br`, with a line break between each item. But, for example, setting `sep:", "` will list all items on the same line, separated by commas.

`span` and `spanskip`: in HTML-out CVs, each attribute is wrapped in a `<span>` tag so that the CSS can style each attribute. However, this can sometimes lead to problems. For example, if the attribute is a URL and the `<a>` tag is in the `format` argument (as opposed to the preferred method of including a Markdown link in the attribute itself), it won't work to wrap your URL in a `<span>` before sending it to `<a>`! So `span` and `spanskip` allow you to specify which attributes do or do not get `<span>` tags. `span: title, text`, for example, will include `<span>` wrappers *only* for the `title` and `text` attributes, and no others. Alternately, `spanskip: title, text` will include `<span>` wrappers for all attributes *except* title and text.

Special Sections
------------------------------

There are three currently recognized special section types that don't follow normal rules.

The first is `head`, which usually goes first and contains information like name, email, etc.. Some CVRoller variants, such as PDF-out using moderncv, requires that a head section be present.

The second is `text`, which simply prints a text block without reference to the CV data.

```
##tag
type: text
text: "[The File Drawer](http://nickchk.com/filedrawer.html) (Dormant Papers)"
version: web
```

The third is `date`, which prints the current date and/or time:

```
##date
type: date
```

By default, this uses `title: "Last Updated: "` and will print 'Last Updated: MonthName Date, Year'. But this can be customized. A `title` option will change the 'Last Updated: ', and the `format` option, which is by default `'{monthname} {day}, {year}'`, can be used to change how the date/time is, using the attributes `year, month, monthname, day, hour, minute,` or `second`.

Processing Citations
=====================

Using BibTeX Databases
----------------------

One section option not covered so far is `bib`. `bib` tells CVRoller to import a BibTeX database and use the citations in it as data for this section. Make sure that the database is in BibTeX format, not Better BibTeX. The database can be in .bib or JSON format, with the JSON file formatted according to [this example](https://github.com/brechtm/citeproc-py/blob/master/examples/citeproc_json.py). 

`bib` takes two arguments, separated by commas. The first is the file location of the database, and should end in .bib or .json. The second is the citation style. This option uses CSL formatting. You can select any style available on [this page](https://www.zotero.org/styles). Either download one of the .csl files and then put the filepath in as the option, ending in .csl, or just put in the ID of the citation style and CVRoller will get it for you. You can include the full URL of the citation style as shown on the Zotero page, for example "https://www.zotero.org/styles/3-biotech", or just the name of the style itself, for example "3-biotech".

CSL files stored on other websites may also work; your mileage may vary. Getting the .csl file from a website will store it on your computer. If you include just the name of the style itself, like "3-biotech", it will download it the first time you run it, and then use the already-downloaded file every time after that. 

By default, `bib` will use all citations in the database. `bib` can take a third argument of a list of citation keys, separated by semicolons ;. This tells CVRoller which citation keys from the database to use. Alternately, if there is data for the section with a `key` attribute, these will be used as the citation keys to include.

For example, the `bib` option 

`bib: file="library.bib", style=apa, keys="frank2012;james2015"`

will use the APA style with the library.bib database, picking only the citation keys `frank2012` and `james2015`. Alternately, if the section's data included rows with the term `key` in the attribute column, and `frank2012` and `james2015` as rows in the content column, only `frank2012` and `james2015` would be chosen.

By default, citations gathered in this way will be ordered in reverse chronological order according to the `year` and `month` BibTeX attributes (if available). `order: ascending` will give ascending chronological order. Chronological order can be overriden with an `order` option in the section. `order: id` will order according to the the reverse of the order the keys are read in, so with `james2015` first and then `frank2012` in the above example, or in the reverse of the order in which the .bib file itself is written if no keys are specified. `order: id, ascending` will use the actual order the keys are read in.

If designing a `format` option for this section, the formatted citation is stored in the `{raw}` attribute. All other BibTeX attributes will be available using their BibTeX attribute names, other than the ones that citeproc-py processes into its own format. The only exceptions are that `{DOI}`, `{PMID}`, `{ISBN}`, and `{ISSN}` will be capitalized, even if they're not capitalized in the BiBTeX file.

This function uses the [https://github.com/brechtm/citeproc-py](citeproc-py) package, and so any citation cases that cannot be handled by citeproc-by is not guaranteed to be handled by CVRoller. CVRoller will, in addition to what citeproc-py picks up, take every attribute in the BibTeX file and make it available for the CSL style interpreter (citeproc-py will ignore some attributes that styles do use, like `DOI`), or for your `format` option (e.g., citeproc-py will not pick up an `abstract` item). However, for CVRoller to be able to do this, if you're using a .bib file, that .bib file has to be squeaky clean! CVRoller uses a comma followed by a new line to identify a new item. So, every item must end with a comma followed by a new line.

```
@article{key,
    title = {My Paper},
	volume = {3}
	}
```

will work, but 

```
@article{key,
    title = {My Paper}, volume = {3}
	}
```

will not. Similarly, if you have a comma followed by a new line in any of the attributes (for example if you have a paragraph break in an abstract that for some reason ends on a comma), that won't work either.

Using the Crossref Database with ORCID or DOI
----------------------

Another option for getting publications in your CV is by looking them up in the [Crossref](https://www.crossref.org/) database. You can do this either by giving a list of DOIs directly, or by giving your [ORCID](https://orcid.org/), uh, ID, and CVRoller will look up your ID and pick out all the DOIs it finds there.

Take for example

```
doi: doi="10.1111/ssqu.12483;10.1257/pandp.20181114", style="chicago-author-date-16th-edition"
```

This will look up the DOIs `10.1111/ssqu.12483;10.1257` and `10.1257/pandp.20181114` in the Crossref database and format them as citations in the `chicago-author-date-16th-edition` style. DOIs should be separated by a semicolon, and can also be included in the CV data as a `doi` attribute. 

The `style` option here works the exact same as in the `bib` option described in the previous section. Basically, choose one from [this page](https://www.zotero.org/styles). Defaults to APA if not specified.

Here's how using an ORCID looks:

```
doi: orcid = "0000-0002-7352-3991", style = "chicago-author-date-16th-edition", id = "APIidfromORCID", secret = "secretkeyfromORCID"
```

This will pick up all DOIs listed under the ORCID, and then use Crossref to look them all up. To fill in the id and secret (for now, hopefully this process will improve in the future), go to [ORCID Developer Tools](https://orcid.org/developer-tools), enable the public API, and add a client. Then go back to the Developer Tools page, find your client, click "Show details", and copy in the "Client ID" and "Client Secret"

You can, if you like, mix and match. You can include `doi` as well as an ORCID, if, for example, your ORCID account is somehow missing one of your publications:

```
doi: orcid = "0000-0002-7352-3991", doi = "10.1111/ssqu.12483", style = "chicago-author-date-16th-edition", id = "APIidfromORCID", secret = "secretkeyfromORCID
```

By default, citations gathered in this way will be ordered in reverse chronological order according to the `year` and `month` BibTeX attributes (if available). `order: ascending` will give ascending chronological order. Chronological order can be overriden with an `order` option in the section.

If you are just using Crossref to get your citations formatted and print them, you should be good to go! Three short notes, though, if you're planning to use `format` to get at some of the individual attributes of the citation to use them elsewhere:

1. I dropped the `reference` attribute. Took up a lot of space, and were you really going to use this?
2. Crossref sometimes doesn't have all the attributes. In the example `doi:` option above, the abtract for `10.1111/ssqu.12483` is not in Crossref, and so if I have an `{abstract}` substitution in my `format` argument, it will not show up for that one.
3. Crossref returns data in a multi-nested format, with attributes inside attributes inside attributes! Unfortunately, at this moment there's no way to let you access anything but the top level. I've left these nested attributes in there, but if you try to use them you'll get back the full nesting structure. For example, if I include `{issued}` in my `format` argument, it will show me "{'date-parts': [[2018, 2, 12]]}" since the `date-parts` attribute is nested inside `issued`. There's no way to get at `date-parts` by itself.

Using the PubMed Database with PMIDs or PMCIDs
----------------------

The final option for getting publications in your CV is by looking them up in the [PubMed](https://www.ncbi.nlm.nih.gov/pubmed) database. You can do this by giving a list PMID or PMCID values.

Take for example

```
pmid: pmid="4425484;4425485", style = "chicago-author-date-16th-edition", database = "PubMed"
```

This will look up the PMIDs `4425484` and `4425485` in the Crossref database and format them as citations in the `chicago-author-date-16th-edition` style. PMIDs should be separated by a semicolon, and can also be included in the CV data as a `pmid` attribute. 

The `style` option here works the exact same as in the `bib` option described in the previous section. Basically, choose one from [this page](https://www.zotero.org/styles). Defaults to AMA if not specified.

You can use PMCIDs instead of PMIDs if you like. Note that it's still `pmid:` not `pmcid:`, although the IDs themselves are given by `pmcid=`. This time we do need to specify the database.

```
pmid: pmcid="2990724;2990725", style = "chicago-author-date-16th-edition", database = "PMC"
```

By default, citations gathered in this way will be ordered in reverse chronological order according to the `year` and `month` BibTeX attributes (if available). `order: ascending` will give ascending chronological order. Chronological order can be overriden with an `order` option in the section.


Using moderncv for LaTeX PDF CVs
=================================

PDF CVs are built in CVRoller using the moderncv class, the documentation for which can be found [here](https://ctan.org/tex-archive/macros/latex/contrib/moderncv). A few of the moderncv features (such as the included cover letter, or actually using BiBTeX rather than routing the BiBTeX data through citeproc/CSL) are not supported, and for some other features you're going to have to work a bit. 

The basics of what you need to know are the following:

* moderncv has five template themes: `casual`, `classic` (the default in CVRoller), `banking`, `oldstyle`, and `fancy`. Examples of each can be seen [here](https://ctan.org/tex-archive/macros/latex/contrib/moderncv/examples).
* Options that can be set in the `theme` version argument include:
    * `fontsize` (default `fontsize=11pt`)
	* `papersize` (default `papersize=a4paper`)
	* `fontfamily` (default `fontfamily=sans`)
	* `color` (default `color=blue`). This determines the color of the layout lines and boxes, as well as the section titles in the `fancy` template. Options are `black`, `blue`, `burgundy`, `green`, `grey`, `orange`, `purple`, and `red`
	* `pagenumbers` (default `pagenumbers=off`) determines whether or not page numbers are displayed. Set to `pagenumbers=on` to include them.
	* `fontchange` (default `fontchange=off`) indicate that the font will be selected not by default `fontfamily` font but by the `font` argument.
	* `font` (by default the default font of the `fontfamily`) can be any TeX font name. To use this, `fontchange` must be set to on.
	* `scale` (by default `scale=0.75`) determines the value in the `\usepackage[scale=0.75]{geometry}` LaTeX argument.
	* `encoding` (by default `encoding=utf8`) gives the character encoding.
	* `photowidth` (by default `photowidth=64pt`) gives the width of any profile image included, if using a theme that includes a profile image.
	* `photoframe` (by default `photoframe=0.4pt`) gives the width of the border around the profile image.
* When using moderncv, any `format` option for the `head` section will be ignored. To have `head` data properly used in your moderncv template, make sure it is named in the CV data exactly as follows:
    * CV title: `title`.
	* Name: `name`. By default, CVRoller will split this into first and second name, which some moderncv templates handle differently, using the first space in the name. Or, you can do this yourself by specifying `name1` and `name2`.
	* E-mail: `email`.
	* Phone: `phone`, or you can get more specific and specify `mobile`, `fixed`, and/or `fax`.
	* Website: `homepage` or `website`. This can be the URL itself, or you can use Markdown link syntax (which may be handy for your HTML CV) and CVRoller will fish the URL out for you.
	* Address: `address`. If you want to use multiple address fields (which some moderncv templates handle differently) you can specify `address1`, `address2`, and (optional) `address3`.
	* Social media: `linkedin`, `twitter`, `github`. These can be entered as handles alone, as URLs to your profile, or Markdown link syntax for links to your profile.
	* Profile picture: `photo`, `picture`, `profile`, or `image`. This can be just the filename (with path, if it's not in the working directory), or can be Markdown image syntax.
	* Everything else will be rendered as part of the `\extrainfo` moderncv entry, separated by commas.
* If you want to write LaTeX code directly into your layout options or CV data (such as in a `sectionframe` section option), you must properly escape characters. Most pressing, make sure you use `\\` instead of `\`, and `{{` and `}}` instead of `{` and `}`.
* moderncv has many different item types, as detailed in its documentation. These can be selected in CVRoller using the `type` attribute in each section. So, for example, `type: cvitem` will wrap each item in that section in the `\cvitem` LaTeX tag. However, because these item types all require that particular information be placed in specific places, these require either carefully naming your CV data attributes, or working with the `format` option. More information is below. 
* There are four `type` options that do not require much work. One is to simply provide no `type` (or provide one that is unrecognized), and CVRoller will simply ignore the moderncv types and print each item as normal. `type: indent` will use `\cvitem` with a blank title, indenting the item (i.e., `\cvitem{}{text}`. `type: cvlistitem` will include each `raw` element as a numbered list. Finally, `type: hangingindent` will ignore the moderncv types and print each item as normal, but with hanging-indent formatting, which is useful for citation sections. Note that `sectionframe` will typically invalidate `type: hangingindent`.
* Other accepted types are `cvitem`, `cventry`, `cvitemwithcomment`, `cvlistitem`, and `cvcolumn`. moderncv entry types that allow two items in a single entry, like `cvdoubleitem` and `cvlistdoubleitem`, are not currently supported, but can probably be mimicked with `cvcolumn` if you deeply want them.
* To use these accepted item types, you must either name your CV data according to the default item formatting, or set your own `format` option. Note in the below formats the use of triple curly braces. One set of curly braces is for the standard `format` syntax, i.e. `{year}` is replaced with the `year` data. The other two sets are used because, in Python, { is its own escape character, and we want to give LaTeX the curly braces it so desires. In the end, starting with three sets of curly braces, we end up with one to give to LaTeX.
    * The default formatting for `cventry` is `format: {{{year}}}{{{accomplishment}}}{{{detail}}}{{}}{{{description}}}`
	* The default for `cvitemwithcomment` is `format: {{{accomplishment}}}{{{detail}}}{{{comment}}}`
	* The default for `cvlistitem` is `format: {{{raw}}}`
	* The default for both `cvitem` and `cvcolumn` is `{{{itemtitle}}}{{{raw}}}`. Note that this will require each item to have its own id, since CVRoller combines all the information for a given id together before writing an entry. So in the moderncv example where a Master's thesis is given three `\cvitem` entries: one for title, one for description, and one for supervisors, you'd need one id for title, one id for description, and one id for supervisors.