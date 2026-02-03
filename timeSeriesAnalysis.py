# -*- coding: utf-8 -*-
"""
Created on Mon Feb  2 11:43:23 2026

@author: BChung

I spent a considerable amount of time cleaning the Mintel data and now I can
actually analyze it. This script is intended to do some time series analysis
of the data.
"""
import os
from pathlib import Path
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib as mpl
# mpl.use("agg")

repository = Path(os.getcwd())
repositoryFolder = Path(os.path.dirname(repository))
dataFolder = repositoryFolder/"Data"
outputFolder = dataFolder/"Output"
figuresFolder = outputFolder/"Figures"

dataPath = outputFolder/"Processed data, ready for analysis.xlsx"
dataOG = pd.read_excel(dataPath, "Product - ingredient", dtype={"productID": "string"})
ingredients = pd.read_excel(dataPath, "Ingredients")
# %%
"""Let's calculate some summary statistics, namely the number of products
containing each ingredient over the whole dataset from (inclusive) 2015 to
(inclusive) 2025."""
ingredientLevelCount = dataOG.groupby("commonName")["productID"].nunique()
topLevelCount = dataOG.groupby("ingredientType1")["productID"].nunique()
secondLevelCount = dataOG.groupby("ingredientType2")["productID"].nunique()

"""Cyclosiloxanes are in the most products (7,198 products), with
cyclopentasiloxane being used more frequently (6,576 products) than the 2nd
most frequently used cyclosiloxane (cyclohexasiloxane, 1,432 products) and the
2nd most frequently used ingredient overall (triethanolamine, 3,874 products).

I can also look at tradeoffs between ethanolamines and their salts.
Diethanolamine and the only salt I've found of it are both used in extremely
few products and used in the same number of products (diethanolamine in 5
products, its salt in 4 products). The most frequently used ethanolamine is
triethanolamine, at 3,874 products, followed by monoethanolamine at just 145
products. Triethanolamine is used in 3,874 products while its salts are used
in 417 products, so triethanolamine is used more frequently than its salts. The
most frequently used triethanolamine salt is TEA-lauryl sulfate which was used
in 347 products.

The acrylamide polymers are used in 4,922 products, with polyquaternium-7 being
used the most at 3,704 products, followed by polyquaternium-37 at 1,201
products and polyquaternium-47 at 173 products. 3704 + 1201 + 173 = 5078 which
is greater than 4,922 products, so this suggests that there is some overlap in
the products that contain acrylamide polymers. 3704 + 1201 = 4905 which is less
than 4,922 products, so there might not be much overlap between polyquaternium-7
and polyquaternium-37. I'm guessing that most of the overlap is due to
polyquaternium-47. But we shall see later if I guessed correctly.
"""
# %%
"""Let's first create a time-series plot of the top level ingredient category.
Each line will be for one of the top level categories.

x-axis = year
y-axis = number of new products recorded that year
"""
topLevelByYear = (dataOG.groupby(["year", "ingredientType1"])["productID"].nunique()
                  .reset_index()
                  .rename(columns={"productID": "numberOfProducts"})
                  )
ingredientType1 = ingredients.ingredientType1.drop_duplicates().tolist()

# Test plotting cyclosiloxanes & ethanolamines
"""
cyclosiloxanesDF = topLevelByYear.query("ingredientType1 == 'Cyclosiloxanes'")
cyclosiloxanes_x = cyclosiloxanesDF.year.tolist()
cyclosiloxanes_y = cyclosiloxanesDF.numberOfProducts.tolist()

topLevelTimeSeriesFigure, topLevelTimeSeriesPlot = plt.subplots(figsize=(20, 20), dpi=400)
cyclosiloxanesLine = topLevelTimeSeriesPlot.plot(cyclosiloxanes_x, cyclosiloxanes_y, label="Cyclosiloxanes")

ethanolaminesDF = topLevelByYear.query("ingredientType1 == 'Ethanolamines'")
ethanolamines_x = ethanolaminesDF.year.tolist()
ethanolamines_y = ethanolaminesDF.numberOfProducts.tolist()
ethanolaminesLine = topLevelTimeSeriesPlot.plot(ethanolamines_x, ethanolamines_y, label="Ethanolamines")

topLevelTimeSeriesFigure.clear()
"""
# Doing the actual plotting
topLevelTimeSeriesFigure, topLevelTimeSeriesPlot = plt.subplots(figsize=(8, 8), dpi=400)
topLevelLines = []
for ingredientCategory in ingredientType1:
    dataToPlot = topLevelByYear.loc[topLevelByYear.ingredientType1 == ingredientCategory]
    x = dataToPlot.year
    y = dataToPlot.numberOfProducts
    topLevelLines.append(topLevelTimeSeriesPlot.plot(x, y, label=ingredientCategory))

topLevelTimeSeriesPlot.set_xlabel("Year")
topLevelTimeSeriesPlot.set_ylabel("Number of new products per year")
topLevelTimeSeriesPlot.grid(visible=True)
topLevelTimeSeriesPlot.legend()

topLevelTimeSeriesPath = figuresFolder/"Ingredient category 1 time series.png"
if os.path.exists(topLevelTimeSeriesPath) is False:
    topLevelTimeSeriesFigure.savefig(topLevelTimeSeriesPath, bbox_inches="tight")
plt.clf()
plt.close(topLevelTimeSeriesFigure)
# plt.show()
# %%
"""There are 3 top level categories (cyclosiloxanes, ethanolamines, acrylamide
polymers) that consist of multiple other substances. Let's create a time series
plot for each of these top level categories over all product categories."""
multipleSubstancesTopLevel = ["Cyclosiloxanes", "Ethanolamines", "Acrylamide polymers"]
multipleSubstancesData = dataOG.query("ingredientType1 == @multipleSubstancesTopLevel")

"""Let's plot cyclosiloxanes. For cyclosiloxanes, I'm going to plot (1) each of
the cyclosiloxane ingredient name and (2) total number of new products
containing cyclosiloxanes."""
topLevelMultipleSubstancesFigure, (topLevelCyclosiloxanes, topLevelEthanolamines, topLevelAcrylamides) = plt.subplots(1, 3, figsize=(30, 10), dpi=400)

cyclosiloxanesDF = multipleSubstancesData.query("ingredientType1 == 'Cyclosiloxanes'")
cyclosiloxanesTotalDF = topLevelByYear.query("ingredientType1 == 'Cyclosiloxanes'")
cyclosiloxanesAllProductCats = (cyclosiloxanesDF.groupby(["year", "commonName"])["productID"].nunique()
                                .reset_index()
                                .rename(columns={"productID": "numberOfProducts"})
                                )
cyclosiloxanesLines = [topLevelCyclosiloxanes.plot(cyclosiloxanesTotalDF.year, cyclosiloxanesTotalDF.numberOfProducts, label="Total")]
individualCyclosiloxanes = ["Cyclomethicone", "Cyclotetrasiloxane", "Cyclopentasiloxane", "Cyclohexasiloxane"]
for cyclosiloxane in individualCyclosiloxanes:
    df = cyclosiloxanesAllProductCats.loc[cyclosiloxanesAllProductCats.commonName == cyclosiloxane]
    line = topLevelCyclosiloxanes.plot(df.year, df.numberOfProducts, label=cyclosiloxane)
    cyclosiloxanesLines.append(line)

topLevelCyclosiloxanes.set_xlabel("Year")
topLevelCyclosiloxanes.set_ylabel("Number of new products")
topLevelCyclosiloxanes.legend()
topLevelCyclosiloxanes.grid(visible=True)
topLevelCyclosiloxanes.set_title("Cyclosiloxanes")

"""Plotting ethanolamines. I'll group by ingredientType2"""
ethanolaminesDF = multipleSubstancesData.query("ingredientType1 == 'Ethanolamines'")
ethanolaminesTotalDF = topLevelByYear.query("ingredientType1 == 'Ethanolamines'")
ethanolaminesAllProductCats = (ethanolaminesDF.groupby(["year", "ingredientType2"])["productID"].nunique()
                               .reset_index()
                               .rename(columns={"productID": "numberOfProducts"})
                               )
ethanolaminesLines = [topLevelEthanolamines.plot(ethanolaminesTotalDF.year, ethanolaminesTotalDF.numberOfProducts, label="Total")]
ethanolamineTypes = ["Triethanolamine", "Triethanolamine salts", "Diethanolamine", "Diethanolamine salts", "Ethanolamine"]
for ethanolamineType in ethanolamineTypes:
    df = ethanolaminesAllProductCats.loc[ethanolaminesAllProductCats.ingredientType2 == ethanolamineType]
    topLevelEthanolamines.plot(df.year, df.numberOfProducts, label=ethanolamineType)

topLevelEthanolamines.set_title("Ethanolamines")
topLevelEthanolamines.set_xlabel("Year")
topLevelEthanolamines.grid(visible=True)
topLevelEthanolamines.legend()

"""Plotting acrylamide polymers. I'll group by the common ingredient name"""
acrylamidesDF = multipleSubstancesData.query("ingredientType1 == 'Acrylamide polymers'")
acrylamidesTotalDF = topLevelByYear.query("ingredientType1 == 'Acrylamide polymers'")
acrylamidesAllProductCats = (acrylamidesDF.groupby(["year", "commonName"])["productID"].nunique()
                             .reset_index()
                             .rename(columns={"productID": "numberOfProducts"})
                             )
acrylamideLines = [topLevelAcrylamides.plot(acrylamidesTotalDF.year, acrylamidesTotalDF.numberOfProducts, label="Total")]
acrylamides = ["Polyquaternium-7", "Polyquaternium-37", "Polyquaternium-47"]
for acrylamide in acrylamides:
    df = acrylamidesAllProductCats.loc[acrylamidesAllProductCats.commonName == acrylamide]
    topLevelAcrylamides.plot(df.year, df.numberOfProducts, label=acrylamide)

topLevelAcrylamides.set_title("Acrylamide polymers")
topLevelAcrylamides.set_xlabel("Year")
topLevelAcrylamides.grid(visible=True)
topLevelAcrylamides.legend()

"""Saving the figure"""
multipleSubstancesFigurePath = figuresFolder/"Multiple substances time series.png"
if os.path.exists(multipleSubstancesFigurePath) is False:
    topLevelMultipleSubstancesFigure.savefig(multipleSubstancesFigurePath, bbox_inches="tight")
plt.clf()
plt.close(topLevelMultipleSubstancesFigure)
