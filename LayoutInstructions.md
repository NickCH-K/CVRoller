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

Head Section
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

Using BibTeX Databases
----------------------

One section option not covered so far is `bib`. `bib` tells CVRoller to import a BibTeX database and use the citations in it as data for this section. Make sure that the database is in BibTeX format, not Better BibTeX. The database can be in .bib or JSON format, with the JSON file formatted according to [this example](https://github.com/brechtm/citeproc-py/blob/master/examples/citeproc_json.py). 

`bib` takes two arguments, separated by commas. The first is the file location of the database, and should end in .bib or .json. The second is the citation style. This option uses CSL formatting. You can select any style available on [this page](https://www.zotero.org/styles). Either download one of the .csl files and then put the filepath in as the option, ending in .csl, or just put in the ID of the citation style and CVRoller will get it for you. Just hover over the style you want, right-click or command-click, select "copy link location", and include this as the option. For example, the very first style on that page gives "https://www.zotero.org/styles/3-biotech". 

CSL files stored on other websites may also work; your mileage may vary. Getting the .csl file from a website will store it on your computer so you can refer to it by filepath naxt time. 

By default, `bib` will use all citations in the database. `bib` can take a third argument of a list of citation keys, separated by semicolons ;. This tells CVRoller which citation keys from the database to use. Alternately, if there is data for the section with a `key` attribute, these will be used as the citation keys to include.

For example, the `bib` option 

`bib: "library.bib", https://www.zotero.org/styles/apa, "frank2012;james2015"`

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

Using moderncv for LaTeX PDF CVs
--------------------------------

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