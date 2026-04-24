#########
Changelog
#########

This project follows a simple release-oriented changelog. Entries describe the
changes shipped in each tagged version.

It is structured where the most recent changes and versions are at the top of their
respective sections.

Active
======

Here is what has been pushed into the *main* branch of the repository,
but has yet to be released as a version.

Changes:

* Made it so that changelog has a prerelease section
* Fixed top nav and version switcher in documentation pages of GitHub Pages

PreReleases
===========

Here you'll find what is in prerelease tags.
This is cleared when the official release of the
prereleases arrives.
This is mainly for organization purposes.

0.1.1rc1
--------

* Fixed documentation formatting errors
* Added requirements to ``requirements.txt``.
* Modified version system to use ``rc`` instead of ``-test``.
* Modified project urls in ``pyproject.toml``.
* Modified GitHub Pages builder to give a homepage and have a top nav bar.
* Modified packaging to prevent unwanted stuff from being packaged
* Added system for building GitHub Pages
* Modified workflows for better control and structure
* Changed import logic from ``pythorn`` to ``piethorn``
* Updated changelog structure
* Clarified install instructions

Published
=========

Here are the changes made in each version that has a public release.
These will never change.

0.1.0
-----

Initial public release.

Highlights:

* collection helpers for character-oriented data, mappings, ranges, and views
* file and import utilities for project-local path handling
* lightweight logging and progress counters
* math helpers including number-word conversion, timing, and equation parsing
* runtime argument and callable inspection utilities
