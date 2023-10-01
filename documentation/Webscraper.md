# Webscraper


## Overview

To assist in collecting data I will be writing a robust webscraper capable of crawling xml maps for instances where the documentation is not easily consumable in pdf or text form. It should have all the loaders and splitters from langchain so most every document type will be consumable for entry into our vectorstores.

## TODO

- Write a webscraper using selenium webdrivers that collects all http requests to capture dynamically loaded information
- Create a pipeline to use the vectorstore tooling for parsing
- Create a bs4 parser to parse html data.
- Create an exit pipeline for parsed data to be used in data set generation or stored in the vectorstore.
- Create the tooling for an agent to scrape a specific target.

## Blue sky

- Create a set of commands that allow AutoGPT to pilot the scraper to automate data collection.
