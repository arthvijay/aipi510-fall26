# Data card

RideCast uses the UCI Bike Sharing hourly dataset, `hour.csv`, from the Capital
Bikeshare system in 2011–2012. Source: [UCI dataset](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset),
DOI 10.24432/C5W894. The source license and attribution remain with UCI.

The cleaning pipeline sorts timestamps, removes exact duplicates, checks hours,
categories, target values, and missingness, and converts normalized weather
values to °C, percent humidity, and km/h. Counts are completed rentals and
therefore reflect service availability as well as demand. Historical, aggregate
data does not support station allocation, current inventory, causal claims, or
demographic fairness claims.
