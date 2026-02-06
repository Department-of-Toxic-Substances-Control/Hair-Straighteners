# -*- coding: utf-8 -*-
"""
Created on Thu Feb  5 15:25:45 2026

@author: BChung

This script looks for Japanese/thermal hair straightening products from the
Mintel data I've downloaded. Brooke is interested in ethanolamine, DEA, and
ammonium thioglycolate in Japanese/thermal hair straightening products. My
analysis so far indicates that these 3 chemicals are very rarely used in the
products in this dataset, and this could either indicate that the dataset has
relatively few Japanese/thermal hair straightening products or that the dataset
does contain these products but these products actually don't use these 3
chemicals that much. This script looks for these products in this dataset using
key words in product categories, subcategories, descriptions, and positioning
claims.
"""
import os
from pathlib import Path
import pandas as pd

repository = Path(os.getcwd())
repositoryFolder = Path(os.path.dirname(repository))
dataFolder = repositoryFolder/"Data"
inputFolder = dataFolder/"Input"
outputFolder = dataFolder/"Output"

dataPath = outputFolder/"Processed data 3.xlsx"
productDataOG = pd.read_excel(dataPath, "Other product data", dtype="string")
productIngredient = pd.read_excel(dataPath, "Product - ingredient", dtype="string")
# %%
productCategories = productDataOG.category.drop_duplicates().tolist()
productCategoriesTarget = ["Soap & Bath Products", "Hair Products"]
productData = (productDataOG.query("category == @productCategoriesTarget")
               .merge(productIngredient, "inner", "productID")
               .filter(["productID", "category", "subcategory", "claims", "productDescription", "Product", "productVariant", "Brand", "Company", "Ultimate Company", "barCode", "year"])
               .drop_duplicates()
               )
hairProductsSubcategories = productData.loc[productData.category == "Hair Products", "subcategory"].drop_duplicates().tolist()
bathProductsSubcategories = productData.loc[productData.category == "Soap & Bath Products", "subcategory"].drop_duplicates().tolist()

"""Looking at the subcategories for soap & bath products, it doesn't seem like
this overall category is relevant, so I'll drop it. The process for applying
this treatment seems to be applying the hair straightening substance to your
hair, wait a bit, wash the substance off of your hair, apply heat, then apply
a neutralizer. So I'll drop the conditioners subcategory."""
hairSubcategoriesExclude = ['Conditioner', 'Hair Colorants', 'Shampoo',
                            "Hair Styling"]
productData = productData.query("(category == 'Hair Products') & (subcategory != @hairSubcategoriesExclude)")
# %%
"""Looking for japanese hair straighteners."""

brands = productData.Brand.drop_duplicates().tolist()
company = productData.Company.drop_duplicates().tolist()
ultimateCompany = productData["Ultimate Company"].drop_duplicates().tolist()

descriptionRegex = r"[Ss]mooth|[Tt]extur|[Jj]apan|[Hh]eat|[Tt]thermal"
descriptionExclude = r"[Kk]eratin|[Bb]razil|[Hh]eat [Pp]rotect|[Bb]low[ -]?([Oo]ut|[Dd]ry)|[PP]omade|Leave[ -][Ii]n"
nameExclude = r"Volumiz(ing|e)|Condition(er|ing)|Mask|Volume [Mm]aximize"
nameInclude = r"(Anti|Un)-Frizz"
claimsExclude = r"Moisturising / Hydrating|Damaged Hair|Brightening / Illuminating|Time/Speed|UV Protection|Leave-In"
hairStraighteners1 = productData.loc[productData.productDescription.str.contains(descriptionRegex, regex=True)]
hairStraighteners2 = hairStraighteners1.loc[~hairStraighteners1.productDescription.str.contains(descriptionExclude, regex=True)]
hairStraighteners3 = hairStraighteners2.loc[~hairStraighteners2.Product.str.contains(nameExclude, regex=True)]
hairStraighteners4 = hairStraighteners3.loc[~hairStraighteners3.claims.str.contains(claimsExclude, regex=True)]
"""In the end, I narrowed down from 17,331 products to 5 products. I then
manually reviewed these 5 products. They're not Japanese hair straightening
products. So it seems like there are no Japanese hair straightening products
in this dataset."""
