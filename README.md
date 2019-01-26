# ISP Coverage Information Web Crawler 

This python web crawler collects the ISP Coverage information from https://geoisp.com/, as well as city and county information from wikipedia. The collected data will be inserted into tables of mysql. More specifically, based on a given state of the US, this script is able to collect the cities and counties information of the given state (e.g., name, geolocation of cities, isp coverage ratio of each city, list of counties of the state, etc.).

Two types of ISP privoder are considered: DSL and Cable. 

## Prerequisites

Python: python version 3.6 or higher is needed, Python library **Beautiful Soup (bs4)**, **requests**, as well as **mysql** are needed.
MySql server end is needed.

## Configuration

To run this script, simply modify several setup arguments in the first several lines of crawler.py, i.e., the target state, and the mysql database related arguments based on your own context and requirement. To run this program, just simpy run the crawler.py script:

```
python crawler.py
```

## Sample Collected Data

The collected data are store in four tables (city, county, covrecord, ispinfo). The sample collected data could find from here: http://web.uvic.ca/~huanwang/images/crawler/

## Authors

* **Huan Wang, Computer Science, UVic, Canada** 
