# -*- coding: utf-8 -*-
"""
Created on Mon Jan 26 13:04:00 2026

@author: BChung

I have already wrangled the CosIng database. In this script, I will match the
ingredients that weren't identified with the CompTox batch search to CosIng. I
will search up the CAS RNs for the ingredients that were identified in this
script on CompTox. I will then create a copy of the dataset that is finally
ready for analysis.
"""

import os
from pathlib import Path
import pandas as pd
import requests
from config import CompToxAPIkey

repository = Path(os.getcwd())
repositoryFolder = Path(os.path.dirname(repository))
dataFolder = repositoryFolder/"Data"
inputFolder = dataFolder/"Input"
outputFolder = dataFolder/"Output"

batchSearchPath = outputFolder/"Processed batch search.xlsx"
CosIngPath = outputFolder/"Cleaned CosIng database - scraped on January 21, 2026.xlsx"
batchSearchFile = pd.ExcelFile(batchSearchPath)
CosIngFile = pd.ExcelFile(CosIngPath)
# %%
unidentifiedBatch = pd.read_excel(batchSearchFile, "Unidentified", dtype="string")
CosIng = (pd.read_excel(CosIngFile, "Substances", dtype="string")
          .drop(columns=["Type", "Annex", "EC"])
          .drop_duplicates()
          )
unidentifiedBatch["uppercase"] = unidentifiedBatch.input.str.upper()

unidentifiedBatch = unidentifiedBatch.merge(CosIng, "left", left_on="uppercase", right_on="INCI")
"""TEA-cocoyl alaninate doesn't have a CAS RN on CompTox, PubChem, or CAS
Common Chemistry."""

"""Now, I'm going to batch search the 7 CAS RNs that were found on the CompTox
API"""
CASRNlist = unidentifiedBatch.loc[unidentifiedBatch.CASRN != "-", "CASRN"].drop_duplicates().tolist()
CASRNstring = "\n".join(CASRNlist)
searchURL = "https://comptox.epa.gov/ctx-api/chemical/search/equal/"
headers = {"accept": "application/json", "content-type": "application/json",
           "x-api-key": CompToxAPIkey}
query = requests.post(searchURL, headers=headers, data=CASRNstring)
if query.status_code == 200:
    queryDF = (pd.json_normalize(query.json())
               .filter(["dtxsid", "casrn", "smiles", "preferredName"])
               .rename(columns={"dtxsid": "DTXSID", "smiles": "SMILES", "casrn": "CASRN"})
               )
    """I can see that the CAS RN values that CompTox use match the ones that
    are on CosIng for these substances perfectly 1:1.
    
    I'm also going to drop certain substances
    
    TEA-dodecylbenzenesulfonate has a CAS RN on CosIng of 68411-31-4, but this
    CAS RN refers to a mixture of a variety of anions of alkylbenzenesulfonates
    instead of specifically doedcylbenzenesulfonate.
    """
    unidentifiedBatch = (unidentifiedBatch.merge(queryDF, "left", "CASRN")
                         .query("CASRN != '68411-31-4'")
                         )
# %%
identifiedBatch = (pd.read_excel(batchSearchFile, "Identified", dtype="string")
                   .rename(columns={"PREFERRED_NAME": "preferredName"})
                   )
identifiedNow = (pd.concat([unidentifiedBatch, identifiedBatch])
                 .reset_index(drop=True)
                 )
identifiedNow.loc[identifiedNow["input"].notna(), "ingredientName"] = identifiedNow["input"]
identifiedNow.loc[identifiedNow["INPUT"].notna(), "ingredientName"] = identifiedNow["INPUT"]

identifiedNow = identifiedNow.drop(columns=["input", "INPUT", "uppercase", "INCI"])
# %%
"""Taking a closer look at the ingredients with DEA or TEA in their names to
see if they are amides or salts of DEA and TEA"""
DEA_TEA_inNames = identifiedNow.loc[identifiedNow.ingredientName.str.contains(r"[DT]EA")]
"""So, judging by SMILES, I can see that the ones with SMILES all have DEA or
TEA in a non-bond (ionic bond) with another (anionic) component. Some of their
preferred names contain variations of 'compounds with', so I can assume that
names that contain 'compounds with' are salts. Of the 5 ingredient names that
don't have SMILES, 3 of them contain 'compounds with', so these 3 are likely
salts. I'm assuming that all of the compounds in this dataframe are salts of
either diethanolamine or triethanolamine. There are no amides here"""
# %%
mintelPath = outputFolder/"Processed Mintel downloads.xlsx"
mintelDataDtypes = {"productID": "string", "ingredientOrder": "int16",
                    "name2": "string", "targetedIngredient": "string", "Product": "string",
                    "productVariant": "string", "Brand": "string", "Company": "string",
                    "Ultimate Company": "string", "barCode": "string"}
productTarget = (pd.read_excel(mintelPath, "Product - target", dtype=mintelDataDtypes)
                 .rename(columns={"name2": "ingredientName", "targetedIngredient": "ingredientType2"})
                 )
targetedIngredientTypes = (productTarget.filter(["ingredientName", "ingredientType2"])
                           .drop_duplicates()
                           )

"""Re-categorizing the ingredients. I'll create 2 levels of categories

Top level: cyclosiloxanes, ethanolamines (and salts), other stuff

2nd level: cyclosiloxanes, ethanolamines, ethanolamine salts, other stuff
"""
targetedIngredientTypes.loc[targetedIngredientTypes.ingredientName.str.contains(r"[Cc]yclo"), "ingredientType1"] = "Cyclosiloxanes"
targetedIngredientTypes.loc[targetedIngredientTypes.ingredientName.str.contains(r"[DT]EA|[Ee]thanolamine"), "ingredientType1"] = "Ethanolamines"
targetedIngredientTypes.loc[targetedIngredientTypes.ingredientName.str.contains(r"[Pp]olyquaternium"), "ingredientType1"] = "Acrylamide polymers"
targetedIngredientTypes.loc[targetedIngredientTypes.ingredientType1.isna(), "ingredientType1"] = targetedIngredientTypes.ingredientType2
targetedIngredientTypes = targetedIngredientTypes[["ingredientName", "ingredientType1", "ingredientType2"]]

targetedIngredientTypes.loc[targetedIngredientTypes.ingredientType1 != "Ethanolamines", "ingredientType2"] = targetedIngredientTypes.ingredientType1
targetedIngredientTypes.loc[targetedIngredientTypes.ingredientName.str.contains(r"^TEA"), "ingredientType2"] = "Triethanolamine salts"
targetedIngredientTypes.loc[targetedIngredientTypes.ingredientName.str.contains(r"^DEA"), "ingredientType2"] = "Diethanolamine salts"

productTarget = (productTarget.drop(columns=["ingredientType2"])
                 .drop_duplicates()
                 .merge(targetedIngredientTypes, "inner", "ingredientName")
                 )

identifiedNow2 = identifiedNow.merge(targetedIngredientTypes, "inner", "ingredientName")
identifiedNow2.loc[identifiedNow2.DTXSID.isna(), "DTXSID"] = "-"
identifiedNow2.loc[identifiedNow2.SMILES.isna(), "SMILES"] = "-"
identifiedNow2.loc[identifiedNow2.preferredName.isna(), "preferredName"] = "-"

"""Creating a common ingredient name so that I can make plots later using the
common ingredient name"""
identifiedNow2.loc[identifiedNow2.ingredientName.str.contains(r"[Cc]yclopentasiloxane"), "commonName"] = "Cyclopentasiloxane"
identifiedNow2.loc[identifiedNow2.ingredientName.str.contains(r"TEA-lauryl [Ss]ulfate"), "commonName"] = "TEA-lauryl sulfate"
identifiedNow2.loc[identifiedNow2.ingredientName.str.contains(r"[Tt]riethanolamine"), "commonName"] = "Triethanolamine"
identifiedNow2.loc[identifiedNow2.ingredientName.str.contains(r"[Pp]olyquaternium-37"), "commonName"] = "Polyquaternium-37"
identifiedNow2.loc[identifiedNow2.commonName.isna(), "commonName"] = identifiedNow2.ingredientName
identifiedNow2 = identifiedNow2.iloc[:, [4, 7, 5, 6, 3, 1, 0, 2]]

"""So identifiedNow2 has (1) chemical identifiers, (2) the types of
ingredients I'm looking for, including whether they are salts of DEA or TEA,
and (3) a common ingredient name I can use for plotting. productTarget has
the original product data including product identifiers, names, brands, and
categories. Let's combine them into a single dataframe containing all the raw
data that I will use for my analysis later."""
productTarget = (productTarget.merge(identifiedNow2, "inner", ["ingredientName", "ingredientType1", "ingredientType2"])
                 .drop(columns=["SMILES"])
                 .drop_duplicates()
                 )

productTarget["year"] = productTarget.datePublished.dt.year
productTarget.loc[productTarget.barCode.isna(), "barCode"] = "-"
productTarget = productTarget.iloc[:, [0, 2, 1, 12, 3, 4, 5, 6, 7, 8, 9, 16, 10, 11, 13, 14, 15]]
# %%
"""Now, the data is clean enough that I can start analyzing it. I'm gonna
export the following dataframes

productTarget - combinations of products and targeted ingredients
identifiedNow2 - information specific to each ingredient, namely how I
categorized them and their identifiers
"""
note = ["This is the Mintel data that was further processed. Prior to this",
        "step, I cleaned and splitted ingredient lists and further cleaned",
        "individual ingredient names and identified some of these ingredients",
        "on CompTox. In this step, I identified the remaining unidentified",
        "targeted ingredients using CosIng, re-categorized them, and extracted",
        "the year from the published date of each product entry. This dataset",
        "should now be ready for analysis.",
        "",
        "The main dataset to be analyzed later is 'Product - ingredient',",
        "containing combinations of products and the targeted ingredients.",
        "Information related to each ingredient (how I categorized them,",
        "chemical identifiers, and SMILES structures) are in the tab 'Ingredients'."]

readMe = pd.DataFrame({"Note": note})

outputPath = outputFolder/"Processed data, ready for analysis.xlsx"
if os.path.exists(outputPath) is False:
    with pd.ExcelWriter(outputPath) as w:
        readMe.to_excel(w, "ReadMe", index=False)
        productTarget.to_excel(w, "Product - ingredient", index=False)
        identifiedNow2.to_excel(w, "Ingredients", index=False)
