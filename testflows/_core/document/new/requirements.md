# SRS{number} {title}<br>Software Requirements Specification

**Author:** {author}

**Date:** {date}

## Table of Contents

* 1 [Revision History](#revision-history)
* 2 [Introduction](#introduction)
  * 2.1 [Table of Contents](#table-of-contents)
  * 2.2 [Generating HTML version](#generating-html-version)
  * 2.3 [Generating Python Requirements](#generating-python-requirements)
* 3 [Terminology](#terminology)
  * 3.1 [SRS](#srs)
  * 3.2 [Some term that you will use](#some-term-that-you-will-use)
* 4 [Requirements](#requirements)
  * 4.1 [RQ.SRSxxx.Example](#rqsrsxxxexample)
  * 4.2 [RQ.SRSxxx.Example.Subgroup](#rqsrsxxxexamplesubgroup)
* 5 [References](#references)

## Revision History

This document is stored in an electronic form using [Git] source control management software.

## Introduction

This section provides an introduction to the project or the feature.
All [SRS] documents must be uniquely identified by a number. In this
case this document is identified by the number

>    `SRSxxx`

The document number must always be used as a prefix to the document title. For example,

>    `SRSxxx Template`

All the requirements are specified in the [Requirements](#requirements) section.

### Table of Contents

Note that currently the table of contents is generated manually using

```bash
cat SRSxxx_Template.md | tfs document toc
```

command and needs to be updated any time requirement name is changed
or a new requirement is added to this document.

### Generating HTML version

You can easily generate a pretty HTML version of this document using the command.

```bash
cat SRSxxx_Template.md | tfs document convert > SRSxxx_Template.html
```

### Generating Python Requirements

You can convert this [SRS] into the `requirements.py` by using the command.

```bash
cat SRSxxx_Template.md | tfs requirements generate > requirements.py
```

## Terminology

You can define terminolgy using the examples below and you can make them
linkable as [SRS] by defining the links in the [References](#References) section.

### SRS

Software Requirements Specification

### Some term that you will use

Some description of the term that you would like to use.

## Requirements

This section includes all the requirements. This section can be structured in any way one sees fit.

Each requirement is defined by the section that starts with
the following prefix:

>    `RQ.[document id].[requirement name]`

then immediately followed by a one-line block that contains the
the `version` of the requirement.

### RQ.SRSxxx.Example
version: 1.0

This is a long description of the requirement that can include any
relevant information.

The one-line block that follows the requirement defines the `version`
of the requirement. The version is controlled manually and is used
to indicate material changes to the requirement that would
require tests that cover this requirement to be updated.

It is a good practice to use requirement names that are broken
up into groups. It is not recommended to use only numbers
because if the requirement must be moved the numbering will not match.
Therefore, the requirement name should start with the group
name which is then followed by a number if any. For example,

>    `RQ.SRSxxx.Group.Subgroup.1`

### RQ.SRSxxx.Example.Subgroup
version: 1.0

This an example of a sub-requirement of the [RQ.SRSxxx.Example](#rqsrsxxxexample).

## References

* **TestFlows Open-Source Software Testing Framework:** https://testflows.com
* **Git:** https://git-scm.com/

[SRS]: #SRS
[Some term that you will use]: #Sometermthatyouwilluse
[TestFlows Open-Source Software Testing Framework]: https://testflows.com
[Git]: https://git-scm.com/
