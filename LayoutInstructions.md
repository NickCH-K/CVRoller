How to Write a CVRoller Layout File
===================================

This document will describe how the CVRoller Layout file works.

CVRoller Layout files are simple text documents that outline the sections of a CV and the options for each section.

CVRoller Layout File Metadata
------------------------------

Each layout file begins with a block of metadata that contains important information to be applied to the whole document. Here's an example:

```
version: web, out="cv.html", raw="cv.md"
version: pdf, out="HuntingtonKleinCV.pdf"
version: wd, out="WordCV.docx"
file: cvdata.xlsx
```

The metadata block begins by listing all the *versions* of the document to be produced. Here we have three versions: web, pdf, and wd. These names can be anything. I could call the PDF version of the CV myCVforEmail and it would work fine. Each time CVRoller is run, it will generate each of these three versions separately. Each of the versions must go at the top of the metadata block.

After the versions, other metadata options can be filled in. The only required option is `file`, which tells CVRoller where to find the information that will actually go in the CV.

As of this writing, no other metadata options are recognized. ADD MORE.

Versions
------------------------------

CVRoller allows you to build multiple different kinds of CVs at once, whether you want a website and PDF version of the same CV, or if you want certain sections to appear in some versions of the CV but not in others (for example, my PDF CV contains the classes I teach, but I don't list this on my website).

Each version option has the following format:

```
version: name, out="fileout.type", option="option"
```

Where name is the key you can use to refer to the version, which we'll be using later when we tell CVRoller when to include or exclude sections. The only required option is `out` which tells CVRoller what file it will be writing to. 

Current supported non-required options include:

`raw="file.md"` tells CVRoller to save the raw compiled Markdown code for this CV variant to file.

`sectionglue`, which is by default set to two line breaks (`\br\br`), tells CVRoller how to 'glue' sections together, i.e. what goes between them. Use `\br` to indicate line breaks, and otherwise use Markdown.

`sectionframe`, tells CVRoller how to attach a section title, referred to as `{title}` to the `{meat}` of the section, which includes all the data. This is by default set to `**{title}**\br{meat}` and can be overriden in individual sections by adding `sectionframe` options to those sections. Use `\br` to indicate line breaks, and otherwise use Markdown. Commas are not currently supported FIX THIS.

Head Section
------------------------------

After the metadata, the CVRoller Layout file contains information on each section of the CV to be included, and the options for each section. Here's an example:

```
##working
version: web, pdf
type: cites
title: "Working Papers"
subtitle: "Please email me at [nhuntington-klein@fullerton.edu](mailto:nhuntington-klein@fullerton.edu) for working PDFs if not linked."
format: "{cite} {extra}\br**Abstract**: {abstract}\br"
sectionframe: "**{title}**\br*{subtitle}*\br{meat}"
```

Each section starts with the section name, led off by two hash tags `##`. This name tells CVRoller what CV data to pick up. So this section will use CV information tagged for the `working` section (not case-sensitive).

No options are required. A section without any options will simply print out all the section entries in the data that aren't assigned an attribute.

Options available include:

`version` tells CVRoller which CV versions to include this section in, separated by commas. By default, each section is included in all versions. So `version: web, pdf` tells CVRoller to include this section in the CVs named `web` and `pdf` but not any others. Note that if you want the same section to show up in multiple versions but *formatted differently* in each of them (for example, perhaps I want `working` to show up in my wd CV but without the abstract), then you can simply make another copy of `##working` in the layout file, give it `version: wd`, and specify the options differently.

`type` determines the section type. This is useful if you have a theme that refers to different section types, and want multiple sections formatted with the same type. By default, `type` is set to the section name.

`title` is the title of the section, to be printed. Similarly, `subtitle` is the subtitle. By default, `title` is the section name and subtitle is blank. Use `\br` to indicate line breaks, and otherwise use Markdown.

`format` gives the layout of each item in the section. In the data, I have `cite, extra,` and `abstract` attributes for each item. The `format` option says how all of these attributes should be arranged into a single entry. By default, `format` is either set by theme, or is simply `{raw}` and will list out each of the items given no attribute. Use `\br` to indicate line breaks, `{attributename}` to indicate where particular attributes should go, and otherwise use Markdown.

`sectionframe` is as discussed above for the versions. This overrides the default `sectionframe` argument for just this section.

`order` determines the order in which items are displayed. By default, each item is displayed in descending order according to its `id` in the data. `order: ascending` will instead use ascending order, `order: alphabetical` will order the items according to the alphabetical order of the *content* of the item, and `order: attributename, ascending` or `order: attributename, descending` will order items according to the `attributename` attribute of each item (which can be any attribute) in ascending or descending order.

`sep` is similar to the `sectionglue` option from the Verisons section above, except that instead of gluing together sections, this glues together items. By default, this is `\br`, with a line break between each item. But, for example, setting `sep:", "` will list all items on the same line, separated by commas.

Special Sections
------------------------------

There are three currently recognized special section types that don't follow normal rules.

The first is `head`, which usually goes first and contains information like name, email, etc.. the only difference with `head` is that, by default, it does not print a section title.

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