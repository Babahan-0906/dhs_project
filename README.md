# Talking Global: KAIST Internationalization Discourse, 2006–2025

This repository contains the codebase, analytical scripts, and interactive visualizations for the digital history project in HSS207 / DHS211 (Introduction to Digital History) at KAIST, Spring 2026.

## Live Interactive Essay and Dashboard
The interactive essay and data explorer are hosted on GitHub Pages:
https://babahan-0906.github.io/dhs_project/

## Project Overview

### Research Question
How did KAIST's internationalization language in official communications shift between 2006 and 2025, and did it lead, track, or lag the actual growth of international student enrollment?

### Argument
KAIST's internationalization language was driven primarily by leadership and policy initiatives rather than enrollment numbers. The discourse peaked early (2008–2010) during the World-Class University presidency and the 2009 ICU merger. It remained decoupled from actual enrollment statistics (holding flat even as student numbers fell during the COVID-19 pandemic) and was subsequently displaced by an AI and entrepreneurship-focused agenda.

## Repository Structure

* **scripts/**: Python scripts for data collection, term-frequency analysis, and HTML byproduct building.
  * `collect_news.py`: Scrapes the KAIST News Center English news corpus.
  * `wayback_scraper.py`: Queries the Internet Archive Wayback Machine to retrieve historical captures of KAIST English site structures.
  * `analyze_text.py`: Analyzes normalized term frequencies.
  * `analyze_html.py`: Analyzes Wayback HTML structure and navigation menus.
  * `event_analysis.py`: Conducts policy event window analysis and correlations.
  * `visualize.py`: Generates the analysis charts.
  * `build_interactive.py`: Compiles the final interactive HTML essay and explorer pages.
* **output/**: Data deliverables and compiled interactive pages.
  * `index.html`: The interactive themed essay with Chart.js visualization.
  * `explore.html`: The data explorer dashboard.
  * `term_frequency_by_year.csv`: Normalized term frequencies.
  * `term_frequency_institutional.csv`: Genre-controlled term frequencies.

## Script Usage & Workflow

### 1. Data Collection
* **News Corpus**: Run `python scripts/collect_news.py` to scrape articles from the news center.
* **Wayback Archive**: Run `python scripts/wayback_scraper.py` to fetch historical website snapshots from the Wayback Machine API.

### 2. Analysis & Visualization
* Run `python scripts/analyze_text.py` and `python scripts/analyze_html.py` to calculate word frequencies and compile nav menu metrics.
* Run `python scripts/event_analysis.py` to compute correlations and lag values around key policy timelines.
* Run `python scripts/visualize.py` to generate the trend and enrollment comparison charts.

### 3. Build Web Essay
* Run `python scripts/build_interactive.py` to compile the final interactive static HTML pages in the `output/` folder.

## Dataset Link
The raw text datasets, Wayback Machine scrape logs, and enrollment data are stored on Google Drive:
https://drive.google.com/drive/folders/16ibQqPZIcSHLkVHY7WgEcuYdKdBs9E48?usp=sharing
