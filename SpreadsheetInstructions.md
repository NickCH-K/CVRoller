---
title: How to Write a CVRoller Data File
author: Nick Huntington-Klein
---

#How to Write a CVRoller Spreadsheet File

A CVRoller spreadsheet file, identified by the `file` option in the CVRoller Layout file, contains all the necessary information that will be laid out in the CV.

A CVRoller spreadsheet file contains four columns: `section, id, attribute`, and `content`. For example:

|section | id | attribute | content               |
|--------|----|-----------|-----------------------|
| head   |    | name      | My Name               |
| head   |    | email     | me@myplace.com        |
| educ   | 1  | year      | 2008                  |
| educ   | 1  | degree    | BA, Cool College      |
| educ   | 2  | year      | 2014                  |
| educ   | 2  | degree    | PhD, U of Cool        |
| cite   | 1  |           | Me (2018). *Best Journal*. vol. 3, no. 1, pp. 1-4.|

The `section` column tells CVRoller which section name the data will be used for. So all the data with `head` in the `section` column will be applied to the `head` section defined in the layout file. Similarly, all the `educ` data will be used in the section called `educ`.

The `id` column tells CVRoller which rows go together, within a section. So in the `educ` section above, for example, because 2008 and BA, Cool College both have the id 1, it knows that you got your BA in 2008, not your PhD. `id`s only distinguish things within a section, so it's okay that there are some rows with `id = 1` in the `educ` section, and some unrelated rows with `id=1` in the `cite` section. CVRoller won't get confused.

`id` is also used for ordering the items. By default, CVRoller sorts things in decending order, so the highest id will be printed first, unless you use an `order` option in the layout file. So here, your education section will list your 2014 PhD first, and then your 2008 BA. Since new items tend to be added to the end of a spreadsheet, if values for `id` are omitted in a section, then CVRoller will fill them in from low to high, so the last row in the spreasheet will be printed first.

`attribute` tells CVRoller what kind of data we're dealing with in each row. This tells CVRoller how to fill in a `format` option in the layout file. 

If `attribute` is left blank for a section, CVRoller will assume that you want to print the whole item. It will fill in the attribute as `raw`. In the `cite` section here, it will just print that whole citation by itself, without combining it with any other rows.

`content` is whatever you want that attribute to be! `content` accepts plain text or Markdown (note that Markdown can also be used to create links with `[linkname](url)`, or images with `![Alt text](imagepath "Optional title")`. Use `\br` to indicate line breaks.

`content` is very flexible, and will take pretty much anything. That means you can create interactive CVs by putting code in here. For example, if you're building an HTML CV, you could put HTML code here for an embedded video, or an iframe, or whatever. Note that unless that code is Markdown, it will just get used as-is and not be converted into other formats. So if you use HTML to embed an image, that image won't work if you are building a PDF version of your CV.