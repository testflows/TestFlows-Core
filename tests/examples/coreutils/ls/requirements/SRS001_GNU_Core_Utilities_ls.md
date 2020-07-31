# SRS001 GNU Core Utilities Package `ls` Utility<br>Software Requirements Specification

**Author:** Vitaliy Zakaznikov

**Date:** July 19, 2020

## Table of Contents

* 1 [Revision History](#revision-history)
* 2 [Introduction](#introduction)
* 3 [Terminology](#terminology)
  * 3.1 [SRS](#srs)
* 4 [Requirements](#requirements)
  * 4.1 [Generic](#generic)
  * 4.2 [RQ.SRS001-CU.LS](#rqsrs001-culs)
  * 4.3 [RQ.SRS001-CU.LS.Synopsis](#rqsrs001-culssynopsis)
  * 4.4 [RQ.SRS001-CU.LS.Default.Directory](#rqsrs001-culsdefaultdirectory)
* 5 [References](#references)

## Revision History

This document is stored in an electronic form using [Git] source control management software.

## Introduction

This [SRS] covers requirements for the [ls] utility which is a part of [GNU core utilities] package.

## Terminology

### SRS

Software Requirements Specification

## Requirements

### Generic

### RQ.SRS001-CU.LS
version: 1.0

The [ls] utility SHALL list the contents of a directory.

### RQ.SRS001-CU.LS.Synopsis
version: 1.0

The [ls] utility SHALL support the following synopsis.

```bash
SYNOPSIS
       ls [OPTION]... [FILE]...
```

### RQ.SRS001-CU.LS.Default.Directory
version: 1.0

The [ls] utility SHALL by default list information about the contents of the current directory.

## References

* **ls**: https://www.gnu.org/software/coreutils/manual/html_node/ls-invocation.html#ls-invocation
* **GNU core utilities**: https://github.com/coreutils/coreutils
* **Git**: https://git-scm.com/

[ls]: https://www.gnu.org/software/coreutils/manual/html_node/ls-invocation.html#ls-invocation
[GNU core utilities]: https://github.com/coreutils/coreutils
[ClickHouse]: https://clickhouse.tech
[Git]: https://git-scm.com/
[SRS]: #SRS
