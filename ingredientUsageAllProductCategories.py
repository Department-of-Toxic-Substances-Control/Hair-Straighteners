# -*- coding: utf-8 -*-
"""
Created on Tue Feb  3 14:02:23 2026

@author: BChung

This script will combine both linear regression and heat maps to produce heat
maps that show how frequently a certain chemical is used in a product category
or subcategory as well as changes in its use over time.
"""
import os
from pathlib import Path
import pandas as pd
from matplotlib import pyplot as plt
from scipy import stats
import numpy as np
import seaborn as sns

repository = Path(os.getcwd())
repositoryFolder = Path(os.path.dirname(repository))
dataFolder = repositoryFolder/"Data"
outputFolder = dataFolder/"Output"
inputFolder = dataFolder/"Input"
figuresFolder = outputFolder/"Figures"

dataPath = outputFolder/"Processed data, ready for analysis.xlsx"
dataOG = pd.read_excel(dataPath, "Product - ingredient", dtype={"productID": "string"})
ingredients = pd.read_excel(dataPath, "Ingredients", dtype="string")

downloadPath1 = inputFolder/"Mintel download - December 2025.xlsx"
download1 = (pd.read_excel(downloadPath1, usecols=[0, 8, 9, 12, 20], dtype="string")
             .rename(columns={"Claims": "Positioning Claims"})
             )
downloadPath2 = inputFolder/"Mintel download - triethanolamine.xlsx"
download2 = pd.read_excel(downloadPath2, header=6, usecols=[0, 8, 9, 12, 20], dtype="string")
downloadPath3 = inputFolder/"Mintel download.xlsx"
download3 = pd.read_excel(downloadPath3, header=7, usecols=[0, 8, 9, 12, 20], dtype="string")
combinedDownload = (pd.concat([download1, download2, download3], ignore_index=True)
                    .drop_duplicates()
                    .rename(columns={"Record ID": "productID", "Category": "category", "Sub-Category": "subcategory", "Positioning Claims": "claims", "Product Description": "productDescription"})
                    )

"""There are duplicated product entries from these 3 downloads, and that's
pretty fucking annoying. Time to see why they're duplicated.

They became duplicated once I added in the claims and product description
columns, so either 1 of these 2 columns (or both) could cause them to be
duplicated, as in a product ID in 1 download might have a certain set of claims
and then this same product ID in the other download might have more claims, and
same thing with product description.
"""
duplicatedEntries = combinedDownload.loc[combinedDownload.productID.duplicated(False)]

"""Dropping product description. If there are still duplicated entries, then
that means that the claims column is duplicated."""
duplicatedDropDescription = (duplicatedEntries.drop(columns=["productDescription"])
                             .drop_duplicates()
                             )

"""Still duplicated after dropping product description, so it's likely that the
claims column causes the duplication. Dropping the claims column now. If the
claims column is the cause of the duplication, dropping it should remove the
duplicated entries, but if not, then dropping it will still keep the duplicated
entries"""
duplicatedDropClaims = (duplicatedEntries.drop(columns=["claims"])
                        .drop_duplicates()
                        )

"""Well. That didn't remove all the duplications. Seems like the duplications
are caused by both columns with the product description causing most of the
duplications.

Ok, I'll do this. It seems like for certain duplicated pairs, 1 entry has more
claims than the other, so for these pairs, I'll keep the entry with the most
claims. For other pairs, they differ by product description with 1 entry having
newline characters while the other entry does not. So I will keep the longer
claim and the product description without the newline character.
"""


def claimsDescription(df):
    """
    To be used in a groupby().apply() in which the dataframe consists of pairs
    of duplicated product entries. For each pair, take the longer claims and
    the product description without a newline character then assign them to
    new columns for later deduplication.

    Parameters
    ----------
    df : Grouped Pandas dataframe
        Pandas dataframe grouped by product ID.

    Returns
    -------
    The same dataframe but with 2 new columns.

    """
    claims = df["claims"].drop_duplicates().tolist()
    claimsValues = len(claims)
    claimsLen = df["claims"].drop_duplicates().str.len()
    productDescriptions = df["productDescription"].drop_duplicates().tolist()
    productDescriptionsValues = len(productDescriptions)
    if claimsValues == 1:
        claimToUse = claims[0]
    else:
        maxClaimLen = claimsLen.max()
        for claim in claims:
            if len(claim) == maxClaimLen:
                claimToUse = claim
                break

    if productDescriptionsValues == 1:
        descriptionToUse = productDescriptions[0]
    else:
        for description in productDescriptions:
            if "\n" not in description:
                descriptionToUse = description
                break
    df["finalClaims"] = claimToUse
    df["finalDescription"] = descriptionToUse
    return df


duplicatedEntries = (duplicatedEntries.groupby("productID").apply(claimsDescription)
                     .drop(columns=["claims", "productDescription"])
                     .rename(columns={"finalClaims": "claims", "finalDescription": "productDescription"})
                     .drop_duplicates()
                     )
uniqueEntries = combinedDownload.loc[~combinedDownload.productID.duplicated(False)]
combinedDownload = pd.concat([uniqueEntries, duplicatedEntries], ignore_index=True)
combinedDownload.loc[combinedDownload.claims.isna(), "claims"] = "-"
# %%
"""I want to experiment with linear regression for a bit. It seems like if you
do linear regression using ordinary least squares, you can calculate the
parameters for a regression yourself. And it seems like you can do hypothesis
testing with the parameters as well. In terms of hypothesis testing of the
parameters, the hypothesis testing I've found that you can do include an F-test
or a t-test. With the t-test, you generally test whether the slope is
significantly different from 0. Now, scipy.stats does linear regression and as
part of their results, they do a kind of hypothesis testing that they call a
Wald test with a t-distribution. I'm not entirely sure what this kind of test
is.

I'll do some experimenting here, borrowing data from the following webpage
https://stats.libretexts.org/Bookshelves/Introductory_Statistics/Mostly_Harmless_Statistics_(Webb)/12%3A_Correlation_and_Regression/12.02%3A_Simple_Linear_Regression/12.2.01%3A_Hypothesis_Test_for_Linear_Regression
"""
hoursStudied = [20, 16, 20, 18, 17, 16, 15, 17, 15, 16, 15, 17, 16, 17, 14]
grades = [89, 72, 93, 84, 81, 75, 70, 82, 69, 83, 80, 83, 81, 84, 76]

# First, I'm going to do linear regression using scipy
scipyRegress = stats.linregress(hoursStudied, grades)

"""Using the standard error from scipy's regression and the slope, I'll do a
t-test to check if the p-value from an actual t-test would be the same as if
I just use scipy's regression"""
scipyStandardError = scipyRegress.stderr
scipySlope = scipyRegress.slope
t = (scipySlope - 0)/scipyStandardError
df = len(hoursStudied) - 2
twoSidedP = 2*(1 - stats.t.cdf(t, df))
"""So, the p-value I calculated for an actual t-test and the p-value that scipy
gave are extremely similar. Now my next question is, how exactly was their
standard error calculated? I'll calculate the standard error according to the
formula given by Wikipedia and compare that to scipy's standard error
https://en.wikipedia.org/wiki/Student%27s_t-test
"""
gradesMean = np.mean(grades)
hoursMean = np.mean(hoursStudied)
hoursDifferences = np.array(hoursStudied) - hoursMean
denominator = np.sqrt(np.sum(hoursDifferences**2))
gradesEstimate = (scipySlope*np.array(hoursStudied)) + scipyRegress.intercept
gradesDifference = gradesEstimate - np.array(grades)
numerator = np.sqrt(np.sum(gradesDifference**2)/df)
standardError = numerator/denominator
"""My standard error and scipy's standard error are essentially identical, so
I'm pretty confident that scipy properly calculated the standard error. In this
case, my p-value from an actual t-test is pretty similar to scipy's p-value
from a Wald test with a t-distribution, so it seems like the Wald test with a
t-distribution might be like a t-test. But I don't know if this will always
hold true, that these 2 p-values will be essentially similar. I'm going to
conduct a t-test using scipy's standard error from now on just to be sure."""

"""I am curious as to whether the t-like-test that scipy does is also
intended for pearson's R as opposed to just being for the slope. I'm going to
perform a t-test for pearson's R and then compare the p-value for this t-test
to the t-test that scipy did for the slope
"""
R = scipyRegress.rvalue
t_R = R*np.sqrt(df/(1 - (R**2)))
twoSidedP_R = 2*(1 - stats.t.cdf(t_R, df))
"""Interesting that this p-value is identical to the p-value for the slope that
I calculated from a t-test. So I can use the p-value from a linear regression
to see whether the correlation coefficient itself is significant, not just
whether the slope is different from zero."""
# %%
"""Actually analyzing the data now. I'm going to make a heat map showing how
these chemicals are distributed across all product subcategories and all years.
"""
data = dataOG.merge(combinedDownload, "inner", "productID")
data["Product category | subcategory"] = data.category + " | " + data.subcategory
distributionDF = (data.groupby(["commonName", "Product category | subcategory"])["productID"].nunique()
                  .reset_index(drop=False)
                  .rename(columns={"productID": "numberOfProducts", "commonName": "Ingredient"})
                  )
distributionPivot = (distributionDF.pivot(["Product category | subcategory"], "Ingredient", "numberOfProducts")
                     .fillna(0)
                     )

distributionHeatMap = sns.clustermap(distributionPivot, figsize=(15, 20), cbar_pos=(.95, 0, .05, .2))
"""Exporting the heat map"""
distributionHeatMapPath = figuresFolder/"Distribution across product categories.png"
if os.path.exists(distributionHeatMapPath) is False:
    distributionHeatMap.savefig(distributionHeatMapPath, dpi=400)
plt.clf()
plt.close()

"""I'm going to export the dataframe with the product categories, product
description, and marketing claims added in, as Brooke asked me to look for
Japanese/thermal hair straightening/reconditioning products, and I might use
these fields to identify these kinds of products."""

processedDataPath = outputFolder/"Processed data 3.xlsx"
note = ["Previously I have processed the Mintel downloads by cleaning and",
        "separating ingredient lists, cleaning ingredient names, and adding",
        "identifiers to the ingredients of interest. This file contains the",
        "same data but I also added in product description, marketing claims,",
        "and product categories and subcategories, as I also needed these",
        "fields for analysis. Brooke wants me to look for Japanese/thermal",
        "hair straighteners, and as Mintel doesn't have a clear cut category",
        "for this type of product, I will need to identify them using the",
        "Mintel fields for product categories, subcategories, descriptions,",
        "and positioning claims."]
readMe = pd.DataFrame({"Note": note})
if os.path.exists(processedDataPath) is False:
    with pd.ExcelWriter(processedDataPath) as w:
        readMe.to_excel(w, "ReadMe", index=False)
        dataOG.to_excel(w, "Product - ingredient", index=False)
        combinedDownload.to_excel(w, "Other product data", index=False)
        ingredients.to_excel(w, "Ingredients", index=False)
