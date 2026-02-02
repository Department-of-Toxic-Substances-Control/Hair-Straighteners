# -*- coding: utf-8 -*-
"""
Created on Wed Jan 21 15:48:48 2026

@author: BChung

I have already made Mintel queries of the personal care products containing
the ingredients that Brooke is interested in. I also cleaned their ingredient
lists and separated and cleaned their ingredients. I then identified the
ingredient names of the chemicals that Brooke is interested in. I searched
these chemicals on CompTox using the batch search feature. This script is to
process the batch search results slightly so that I can more easily match
ingredients that weren't identified using the batch search with the EU CosIng
database to attempt to identify them a 2nd time.
"""
import os
from pathlib import Path
import pandas as pd

repository = Path(os.getcwd())
repositoryFolder = Path(os.path.dirname(repository))
dataFolder = repositoryFolder/"Data"
inputFolder = dataFolder/"Input"
outputFolder = dataFolder/"Output"

batchPath = inputFolder/"Targeted ingredients batch.xlsx"
batchOG = pd.read_excel(batchPath, "Main Data", dtype="string", usecols=[0, 2, 3, 4, 5])
batchOG.loc[batchOG.SMILES.str.isspace(), "SMILES"] = ""
# %%
found1 = batchOG.query("DTXSID.notna()")
notFound = (batchOG.query("DTXSID.isna()")
            .filter(["INPUT"])
            .rename(columns={"INPUT": "input"})
            )

"""Going to manually match some ingredient names that have actually been found
but are spelled slightly differently
"""
notFound.loc[notFound.input == "cyclopentasiloxane polymeric", "foundName"] = "cyclopentasiloxane"
notFound.loc[notFound.input == "soluble colltriethanolamine", "foundName"] = "Triethanolamine"
notFound = (notFound.merge(found1, "left", left_on="foundName", right_on="INPUT")
            .drop(columns=["INPUT"])
            )
found2 = (notFound.query("DTXSID.notna()")
          .rename(columns={"input": "INPUT"})
          .drop(columns=["foundName"])
          )
notFound2 = (notFound.query("DTXSID.isna()")
             .filter(["input"])
             .drop_duplicates()
             )

found = (pd.concat([found1, found2], ignore_index=True)
         .drop_duplicates()
         )
# %%
"""Going to export the results. There will be 2 tabs

1. Ingredients that were identified from the CompTox batch search
2. Ingredients that were not identified from the CompTox batch search. These
will be matched against a scrape of EU CosIng to identify them.

"""
note = ["After cleaning and splitting the ingredient lists and cleaning the",
        "resulting ingredient names, I have searched the targeted ingredients",
        "on CompTox using the CompTox batch search feature. I then processed",
        "these batch search results. One tab contains the ingredients that",
        "were identified from the batch search while the other tab contains",
        "ingredient names that were not identified. These unidentified",
        "ingredients will be matched against a scrape of the EU CosIng database",
        "to attempt to identify them again."]
readMe = pd.DataFrame({"Note": note})
outputPath = outputFolder/"Processed batch search.xlsx"
if os.path.exists(outputPath) is False:
    with pd.ExcelWriter(outputPath) as w:
        readMe.to_excel(w, "ReadMe", index=False)
        found.to_excel(w, "Identified", index=False)
        notFound2.to_excel(w, "Unidentified", index=False)
