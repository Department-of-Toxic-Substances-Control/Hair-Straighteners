# -*- coding: utf-8 -*-
"""
Created on Fri Dec 26 11:21:14 2025

@author: BChung
This script splits ingredient lists from a Mintel download of products in the
US from January 2015 to December 24, 2025. Products in the Beauty & Personal
Care super-category were downloaded, and products were downloaded if their
ingredient lists contained certain cyclosiloxanes and acrylamide polymers.
"""
import os
from pathlib import Path
import pandas as pd

repository = Path(os.getcwd())
repositoryFolder = Path(os.path.dirname(repository))
dataFolder = repositoryFolder/"Data"
inputFolder = dataFolder/"Input"

dataPath = inputFolder/"Mintel download.xlsx"
original = pd.read_excel(dataPath, header=7, dtype={"Record ID": "string"})
# %%
ingredientProduct = (original.filter(["Record ID", "Ingredients (Standard form)"])
                     .rename(columns={"Record ID": "productID", "Ingredients (Standard form)": "originalIngredientList"})
                     )

"""Removing certain bits in ingredient lists, e.g.
- delimiters that are not commas
- active ingredient substrings at the beginning 
"""
# irregularRegex = r" [Ii]nactive [Ii]ngredient(s)?: | [Ii]nactive [Ii]ngredient(s)? [(]"
inactiveRegex1 = r"(?!,) [Ii]nactive [Ii]ngredient(s)?(: | [(])"
inactiveRegex2 = r"(?=,) [Ii]nactive [Ii]ngredient(s)?(: | [(])"
activeRegex = r"^[Aa]ctive [Ii]ngredient(s)?(: | [(])"
beginningText = r"^(?!(([Ii]n)?[Aa]ctive [Ii]ngredient|,))[a-zA-Z0-9\s]+?:"
ingredientProduct["ingredientList"] = ingredientProduct.originalIngredientList
ingredientProduct["ingredientList"] = (ingredientProduct["ingredientList"].str.replace(inactiveRegex1, ", ", regex=True)
                                       .str.replace(inactiveRegex2, " ", regex=True)
                                       .str.replace(activeRegex, "", regex=True)
                                       .str.replace('^"', "", regex=True)
                                       .str.replace(beginningText, "", regex=True)
                                       .str.strip()
                                       )

# Splitting ingredient lists
# ingredientListDF = (ingredientProduct.filter(["ingredientList"]).drop_duplicates()
#                     .set_index("ingredientList", False)
#                     )

# splitRegex = r", "
# splitDF = (ingredientListDF.ingredientList.str.split(splitRegex, expand=True, regex=True)
#            .reset_index(drop=False)
#            .melt("ingredientList", var_name="ingredientOrder", value_name="originalIngredient")
#            .query("originalIngredient.notna()")
#            )
# ingredientsOnly = (splitDF.filter(["originalIngredient"])
#                    .reset_index(drop=True)
#                    .drop_duplicates()
#                    )

# regexRemove = r"([Ii]n)?[Aa]ctive [Ii]ngredient(s)?(:| \()"
# ingredientsOnly["cleanName"] = ingredientsOnly.originalIngredient.str.replace(regexRemove, "")
