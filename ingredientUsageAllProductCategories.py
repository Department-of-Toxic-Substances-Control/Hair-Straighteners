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

# Making the colors to label the ingredient and product categories
ingredientsCategoriesDF = (ingredients.filter(["commonName", "ingredientType1"])
                         .drop_duplicates()
                         )
ingredientsCategories = ingredientsCategoriesDF.ingredientType1.drop_duplicates().tolist()
ingredientColors = sns.color_palette("colorblind", len(ingredientsCategories))
ingredientColorsDF = pd.DataFrame({"ingredientType1": ingredientsCategories, "color": ingredientColors})
ingredientColorsDF2 = ingredientsCategoriesDF.merge(ingredientColorsDF, "inner", "ingredientType1")
ingredientNames = ingredientColorsDF2.commonName.tolist()
ingredientColors2 = ingredientColorsDF2.color.tolist()
ingredientColorsDict = {ingredientNames[i]: ingredientColors2[i] for i in range(len(ingredientNames))}

productCategoriesDF = (data.filter(["category", "Product category | subcategory"])
                       .drop_duplicates()
                       )
productCategories = productCategoriesDF.category.drop_duplicates().tolist()
productColors = sns.color_palette("Set2", len(productCategories))
productColorsDF = pd.DataFrame({"category": productCategories, "color": productColors})
productColorsDF2 = productCategoriesDF.merge(productColorsDF, "inner", "category")
categorySubcategory = productColorsDF2["Product category | subcategory"].tolist()
productColors2 = productColorsDF2.color.tolist()
productColorsDict = {categorySubcategory[i]: productColors2[i] for i in range(len(categorySubcategory))}

"""Plotting the heat map"""
distributionColumnsList = distributionPivot.columns.tolist()
distributionColumnsColors = (pd.Series(distributionColumnsList)
                             .map(ingredientColorsDict)
                             .tolist()
                             )
distributionRowsList = distributionPivot.index.tolist()
distributionRowsColors = (pd.Series(distributionRowsList)
                          .map(productColorsDict)
                          .tolist()
                          )
distributionHeatMap = sns.clustermap(distributionPivot, figsize=(15, 20), cbar_pos=(.95, 0, .05, .2), row_colors=distributionRowsColors, col_colors=distributionColumnsColors, linewidths=1, annot=True, fmt=".0f")
# distributionHeatMap = sns.clustermap(distributionPivot, figsize=(15, 20), cbar_pos=(.95, 0, .05, .2))
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
# %%
"""I'm going to make heat maps that show temporal trends of how certain
chemicals are used in certain product subcategories over time. I'm going to
make 2 heat maps, 1 heat map where the colors represent the Pearson's
correlation coefficient and 1 heat map where the colors represent the total
changes from 2015 to 2025."""
temporalTrendsDF = (data.groupby(["commonName", "Product category | subcategory", "year"])["productID"].nunique()
                    .reset_index(drop=False)
                    .rename(columns={"productID": "numberOfProducts"})
                    )

"""Some combinations might have data like 2015 1 product, 2016 2 products, 2017
2 products, 2019 1 product, etc, and they skip certain years. For each
combination, if there are missing years, I will enter in those missing years
and the number of new products for those missing years as 0."""
allYears = np.arange(2015, 2026).tolist()
allCombinations = (temporalTrendsDF.filter(["commonName", "Product category | subcategory"])
                   .drop_duplicates()
                   )
allCombinations["concatenatedYears"] = "|".join(str(year) for year in allYears)
yearsSplit = allCombinations.concatenatedYears.str.split("|", regex=False, expand=True)
allCombinations = (allCombinations.join(yearsSplit)
                   .drop(columns=["concatenatedYears"])
                   .melt(["commonName", "Product category | subcategory"], var_name="order", value_name="year")
                   .drop(columns=["order"])
                   .drop_duplicates()
                   .astype({"year": "int64"})
                   )
missingYears = (temporalTrendsDF.merge(allCombinations, "outer", ["commonName", "Product category | subcategory", "year"])
                .query("numberOfProducts.isna()")
                )
missingYears.numberOfProducts = 0
temporalTrendsDF = pd.concat([temporalTrendsDF, missingYears], ignore_index=True)

"""Doing linear regression now. I'll do linear regression for each combination,
so I'll need to do this in a groupby fashion."""


def linearRegression(df):
    """
    To be used in a groupby().apply() in which a dataframe is grouped by the
    combination of an ingredient and product category | subcategory. Performs
    linear regression to see if there are any temporal changes in the number
    of new products in this product category | subcategory containing this
    ingredient. Also sees the number of changes between 2015 and 2025 for each
    combination.

    Parameters
    ----------
    df : Grouped pandas dataframe
        Pandas dataframe grouped by product category | subcategory and
        ingredient.

    Returns
    -------
    The same dataframe but with 2 new columns, 1 for the p-value from the
    regression and 1 for the pearson's R.

    """
    regression = stats.linregress(df.year, df.numberOfProducts)
    df["R"] = regression.rvalue
    df["p"] = regression.pvalue
    products2015 = df.loc[df.year == 2015, "numberOfProducts"].tolist()[0]
    products2025 = df.loc[df.year == 2025, "numberOfProducts"].tolist()[0]
    df["change"] = products2025 - products2015
    return df


"""Making the individual dataframes that form the underlying data for the heat
maps showing temporal trends"""
temporalTrendsDF = (temporalTrendsDF.groupby(["commonName", "Product category | subcategory"]).apply(linearRegression)
                    .rename(columns={"commonName": "Ingredient"})
                    )
temporalTrendsDF.loc[temporalTrendsDF.p >= 0.05, "R"] = 0
temporalTrends1 = (temporalTrendsDF.filter(["Ingredient", "Product category | subcategory", "R"])
                   .drop_duplicates()
                   .query("R != 0")
                   )
temporalTrends2 = (temporalTrendsDF.filter(["Ingredient", "Product category | subcategory", "change"])
                   .drop_duplicates()
                   .query("change != 0")
                   )

"""Making the colors to label the rows and columns for the heat map plotting R
values."""
temporalPivot1 = (temporalTrends1.pivot("Product category | subcategory", "Ingredient", "R")
                  .fillna(0)
                  )

categorySubcategoryR = pd.DataFrame({"Product category | subcategory": temporalPivot1.index.tolist()})
categorySubcategoryR_DF = productCategoriesDF.merge(categorySubcategoryR, "inner", "Product category | subcategory")
productCategoriesR = categorySubcategoryR_DF.category.drop_duplicates().tolist()
productColors_R = sns.color_palette("Set2", len(productCategoriesR))
categoryColors_R = pd.DataFrame({"category": productCategoriesR, "color": productColors_R})
categorySubcategoryR_DF = (categorySubcategoryR_DF.merge(categoryColors_R, "inner", "category")
                           .drop(columns=["category"])
                           .drop_duplicates()
                           )
categorySubcategoryR = categorySubcategoryR_DF["Product category | subcategory"].tolist()
categorySubcategoryR_colors = categorySubcategoryR_DF.color.tolist()
productColors_R_dict = {categorySubcategoryR[i]: categorySubcategoryR_colors[i] for i in range(len(categorySubcategoryR))}
temporalHeatMap1RowColors = (pd.Series(temporalPivot1.index.tolist())
                             .map(productColors_R_dict)
                             .tolist()
                             )

ingredientsR = temporalPivot1.columns.tolist()
ingredientsR_DF = (pd.DataFrame({"commonName": ingredientsR})
                   .merge(ingredientsCategoriesDF, "inner", "commonName")
                   )
ingredientsTypesR = ingredientsR_DF.ingredientType1.drop_duplicates().tolist()
ingredientsRcolors = sns.color_palette("colorblind", len(ingredientsTypesR))
ingredientsTypesColorsR_DF = pd.DataFrame({"ingredientType1": ingredientsTypesR, "color": ingredientsRcolors})
ingredientsR_DF = (ingredientsR_DF.merge(ingredientsTypesColorsR_DF, "inner", "ingredientType1")
                   .drop(columns=["ingredientType1"])
                   .drop_duplicates()
                   )
ingredientsR = ingredientsR_DF.commonName.tolist()
ingredientsRcolorsList = ingredientsR_DF.color.tolist()
ingredientsRdict = {ingredientsR[i]: ingredientsRcolorsList[i] for i in range(len(ingredientsR))}
temporalHeatMap1ColumnColors = (pd.Series(temporalPivot1.columns.tolist())
                                .map(ingredientsRdict)
                                .tolist()
                                )

# Plotting the first heat map
temporalHeatMap1 = sns.clustermap(temporalPivot1, cmap="Spectral", figsize=(12, 14), linewidths=2, cbar_pos=(0.9, 0, .025, .2), annot=True, row_colors=temporalHeatMap1RowColors, col_colors=temporalHeatMap1ColumnColors, center=0)
temporalHeatMap1Path = figuresFolder/"Significant temporal trends across product categories, R.png"
if os.path.exists(temporalHeatMap1Path) is False:
    temporalHeatMap1.savefig(temporalHeatMap1Path, dpi=400)
plt.clf()
plt.close()
# %%
"""Making the heat map where I plot the change in new products per year between
2015 and 2025"""
temporalPivot2 = (temporalTrends2.pivot("Product category | subcategory", "Ingredient", "change")
                  .fillna(0)
                  )

ingredientsChange = temporalPivot2.columns.tolist()
ingredientsChangeDF = (pd.DataFrame({"commonName": ingredientsChange})
                       .merge(ingredientsCategoriesDF, "left", "commonName")
                       )
ingredientsTypesChange = ingredientsChangeDF.ingredientType1.drop_duplicates().tolist()
ingredientsChangeColors = sns.color_palette("colorblind", len(ingredientsTypesChange))
ingredientsTypesColorsDF = pd.DataFrame({"ingredientType1": ingredientsTypesChange, "color": ingredientsChangeColors})
ingredientsChangeDF = (ingredientsChangeDF.merge(ingredientsTypesColorsDF, "left", "ingredientType1")
                       .drop(columns=["ingredientType1"])
                       )
temporalHeatMap2ColumnColors = ingredientsChangeDF.color.tolist()

categorySubcategoryChange = temporalPivot2.index.tolist()
categorySubcategoryChangeDF = (pd.DataFrame({"Product category | subcategory": categorySubcategoryChange})
                               .merge(productCategoriesDF, "left", "Product category | subcategory")
                               )
categoryChange = categorySubcategoryChangeDF.category.drop_duplicates().tolist()
categoryChangeColors = sns.color_palette("Set2", len(categoryChange))
categoryChangeDF = pd.DataFrame({"category": categoryChange, "color": categoryChangeColors})
categorySubcategoryChangeDF = (categorySubcategoryChangeDF.merge(categoryChangeDF, "left", "category")
                               .drop(columns=["category"])
                               )
temporalHeatMap2RowColors = categorySubcategoryChangeDF.color.tolist()

temporalHeatMap2 = sns.clustermap(temporalPivot2, cmap="Spectral", figsize=(16, 20), linewidths=4, cbar_pos=(.99, 0, .025, .2), annot=True, fmt=".0f", row_colors=temporalHeatMap2RowColors, col_colors=temporalHeatMap2ColumnColors, center=0)
temporalHeatMap2Path = figuresFolder/"Temporal trends across product categories, 2025 minus 2015.png"
if os.path.exists(temporalHeatMap2Path) is False:
    temporalHeatMap2.savefig(temporalHeatMap2Path, dpi=400)
plt.clf()
plt.close()
# %%
"""I will also make a 4th heat map that is a version of the heat map showing
change in the rate of new products but this time showing only significant
changes with p < 0.05"""
temporalTrends3 = (temporalTrendsDF.query("p < 0.05")
                   .filter(["Ingredient", "Product category | subcategory", "change"])
                   .drop_duplicates()
                   )
temporalPivot3 = (temporalTrends3.pivot("Product category | subcategory", "Ingredient", "change")
                  .fillna(0)
                  )

"""Adding colors to the columns and rows for the heat map"""
ingredientsChange2 = temporalPivot3.columns.tolist()
ingredientsChange2DF = (pd.DataFrame({"commonName": ingredientsChange2})
                        .merge(ingredientsCategoriesDF, "left", "commonName")
                        .merge(ingredientsTypesColorsR_DF, "left", "ingredientType1")
                        .drop(columns=["ingredientType1"])
                        )
temporalTrends3ColumnColors = ingredientsChange2DF.color.tolist()

categorySubcategoryChange2 = temporalPivot3.index.tolist()
categorySubcategoryChange2DF = (pd.DataFrame({"Product category | subcategory": categorySubcategoryChange2})
                                .merge(productCategoriesDF, "left", "Product category | subcategory")
                                .merge(categoryColors_R, "left", "category")
                                .drop(columns=["category"])
                                )
temporalTrends3RowColors = categorySubcategoryChange2DF.color.tolist()

"""Making the actual heat map"""
temporalHeatMap3 = sns.clustermap(temporalPivot3, cmap="Spectral", figsize=(12, 14), linewidths=2, cbar_pos=(0.9, 0, .025, .2), annot=True, fmt=".0f", row_colors=temporalTrends3RowColors, col_colors=temporalTrends3ColumnColors, center=0)

temporalHeatMap4Path = figuresFolder/"Significant temporal trends across product categories, 2025 minus 2015.png"
if os.path.exists(temporalHeatMap4Path) is False:
    temporalHeatMap3.savefig(temporalHeatMap4Path, dpi=400)
plt.clf()
plt.close()
# %%
"""Finally, Brooke wants me to make tables of the number of products in a
product category or subcategory that contains a certain chemical by year. I
already kind of did this with temporalTrendsDF. Let's make 1 table where I
sum by product subcategory and 1 where I sum by product category."""
addToResults = (data.filter(["category", "subcategory", "Product category | subcategory", "ingredientType1", "ingredientType2", "commonName"])
                .drop_duplicates()
                .rename(columns={"commonName": "Ingredient"})
                )
temporalTrendsDF1 = (temporalTrendsDF.merge(addToResults, "inner", ["Product category | subcategory", "Ingredient"])
                     .drop(columns=["Product category | subcategory", "p"])
                     .drop_duplicates()
                     )
temporalTrendsSubcategories = (temporalTrendsDF1.drop(columns=["R", "change"]))
temporalTrendsCategories = (temporalTrendsSubcategories.groupby(["Ingredient", "year", "category"])["numberOfProducts"].sum()
                            .reset_index(drop=False)
                            .merge(addToResults, "inner", ["Ingredient", "category"])
                            .drop(columns=["subcategory", "Product category | subcategory"])
                            .drop_duplicates()
                            )
temporalTrendsSubcategoriesResults = (temporalTrendsDF1.filter(["Ingredient", "ingredientType1", "ingredientType2", "category", "subcategory", "R", "change"])
                                      .drop_duplicates()
                                      )
note = ["This file contains the number of new products in different product",
        "categories and subcategories that contain specific ingredients of",
        "interest in a year. The tab 'Subcategory data' counts products at",
        "the subcategory level, i.e. each row is a combination of a specific",
        "product subcategory and ingredient in a given year. The tab",
        "'Category data' counts products at the category level. I then looked",
        "at temporal trends in the Subcategory data by computing Pearson's",
        "correlation between year and the number of new products for each",
        "product subcategory - ingredient combination. I generated R values",
        "using the linregress() function in the 'stats' module from the 'scipy'",
        "Python package (1.7.3). This function also tests the significance of",
        "the linear regression and the R value using what they call a Welch's",
        "test with a t-distribution, which seems to be a slightly different",
        "version of a typical t-test. I set correlation coefficients with a",
        "p-value > 0.05 to be 0. Besides generating R values, I also",
        "calculated the change in the number of new products per year between",
        "2015 and 2025 for each product subcategory - ingredient combination",
        "by subtracting the number of new products in 2015 from the number of",
        "new products in 2025 for that combination. Therefore, I calculated 2",
        "metrics to represent the change in usage over time of an ingredient",
        "in a product subcategory. I then plotted each metric in a heat map."]
readMe = pd.DataFrame({"Note": note})
resultsPath = outputFolder/"Temporal changes by product type.xlsx"
if os.path.exists(resultsPath) is False:
    with pd.ExcelWriter(resultsPath) as w:
        readMe.to_excel(w, "ReadMe", index=False)
        temporalTrendsSubcategories.to_excel(w, "Subcategory data", index=False)
        temporalTrendsCategories.to_excel(w, "Category data", index=False)
        temporalTrendsSubcategoriesResults.to_excel(w, "Subcategory change", index=False)
