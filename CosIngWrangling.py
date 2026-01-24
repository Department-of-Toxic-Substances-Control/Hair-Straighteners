# -*- coding: utf-8 -*-
"""
Created on Thu Jan 22 10:19:48 2026

@author: BChung

This script wrangles the CosIng data that I scraped on January 21, 2026 into a
more machine-friendly format.
"""
import os
from pathlib import Path
import pandas as pd

repository = Path(os.getcwd())
repositoryFolder = Path(os.path.dirname(repository))
dataFolder = repositoryFolder/"Data"
inputFolder = dataFolder/"Input"
outputFolder = dataFolder/"Output"

CosIngPath = inputFolder/"CosIng_Functions - scraped January 21, 2026.csv"
CosIngOG = (pd.read_csv(CosIngPath, dtype="string", usecols=[2, 3, 4, 5, 6, 7])
            .drop_duplicates()
            )
# %%
functionURLs = (CosIngOG.filter(["Function"])
                .rename(columns={"Function": "functionURL"})
                .drop_duplicates()
                .reset_index(drop=True)
                )

functionSplit = (functionURLs.functionURL.str.split("/+", expand=True)
                 .rename(columns={8: "function"})
                 .filter(["function"])
                 )
functionSplit.loc[functionSplit.function.str.contains("%20", regex=False), "function"] = functionSplit.function.str.replace("%20", " ")

functionDF = functionURLs.join(functionSplit)

CosIng = (CosIngOG.merge(functionDF, "inner", left_on="Function", right_on="functionURL")
          .drop(columns=["Function"])
          .drop_duplicates()
          )
CosIng.loc[CosIng.CAS.isna(), "CAS"] = "-"
CosIng.loc[CosIng.EC_No.isna(), "EC_No"] = "-"
CosIng.loc[~CosIng.EC_No.str.contains(r"[0-9]"), "EC_No"] = "-"
CosIng.loc[CosIng.Annex.isna(), "Annex"] = "-"
CosIngColumns = CosIng.columns.tolist()
for column in CosIngColumns:
    CosIng[column] = CosIng[column].str.strip()

CosIngNoFunctions = (CosIng.drop(columns=["function", "functionURL"])
                     .drop_duplicates()
                     )
# %%
CosIngNoFunctions2 = CosIngNoFunctions.copy()
CosIngNoFunctions2.loc[CosIngNoFunctions2.EC_No.str.contains("287/896-9"), "EC_No"] = CosIngNoFunctions2.EC_No.str.replace("287/896-9", "287-896-9")
CosIngNoFunctions2.loc[CosIngNoFunctions2.EC_No.str.contains("204-846-3,,231-926-5"), "EC_No"] = CosIngNoFunctions2.EC_No.str.replace("204-846-3,,231-926-5", "204-846-3, - ,231-926-5")
CosIngNoFunctions2.loc[CosIngNoFunctions2.EC_No.str.contains("- 230-636-6"), "EC_No"] = CosIngNoFunctions2.EC_No.str.replace("- 230-636-6", "- / 230-636-6")
CosIngNoFunctions2.loc[CosIngNoFunctions2.INCI == "LEPISTA NUDA FERMENT EXTRACT", "CAS"] = "-"
CosIngNoFunctions2.loc[CosIngNoFunctions2.CAS.str.contains("100209- 50-5"), "CAS"] = CosIngNoFunctions2.CAS.str.replace("100209- 50-5", "100209-50-5")
CosIngNoFunctions2.loc[CosIngNoFunctions2.EC_No.str.contains("288-342-9 1I)", regex=False), "EC_No"] = CosIngNoFunctions2.EC_No.str.replace("288-342-9 1I)", "- / 288-342-9 ", regex=False)
CosIngNoFunctions2.loc[CosIngNoFunctions2.INCI == "DISODIUM PHENYL DIBENZIMIDAZOLE TETRASULFONATE", "EC_No"] = "429-750-0"
CosIngNoFunctions2.loc[CosIngNoFunctions2.INCI == "PROPYLAL", "EC_No"] = "208-021-9"
CosIngNoFunctions2.loc[CosIngNoFunctions2.EC_No.str.contains("307-272-2"), "EC_No"] = CosIngNoFunctions2.EC_No.str.replace("307-272-2", "307-273-8")
CosIngNoFunctions2.loc[CosIngNoFunctions2.INCI == "SODIUM GLYCEROPHOSPHATE", "CAS"] = CosIngNoFunctions2.CAS.str.replace("17603-42-8-39951-36-5", "17603-42-8 / 39951-36-5")
CosIngNoFunctions2.loc[CosIngNoFunctions2.INCI == "SODIUM GLYCEROPHOSPHATE", "EC_No"] = "215-613-0 / 216-304-3 / 241-577-0 / 254-713-9 / -"

"""Separating out concatenated CAS RNs and EC numbers"""
CASRNregex = r"[1-9][0-9]{1,6}-[0-9]{2}-[0-9](?![0-9])"
CosIngWithCAS = CosIngNoFunctions2.loc[CosIngNoFunctions2.CAS.str.contains(CASRNregex)]

# Determining the delimiter that separates CAS RNs
CosIngCASlist = CosIngWithCAS.CAS.drop_duplicates().tolist()
CosIngAllConcatenatedCAS = "".join(CosIngCASlist)
CosIngCASchars = set(list(CosIngAllConcatenatedCAS))
alphabet = set(list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"))
CosIngCASchars2 = CosIngCASchars - alphabet
numbers = set(list("0123456789"))
CosIngCASchars3 = CosIngCASchars2 - numbers
"""Ok, delimiters seem to be a forward slash, comma, or semicolon"""
CASdelimiter = r" *[,;/]+ *"

"""Determining the delimiters that separate EC numbers and see if they are the
same as the delimiters for CAS RNs"""
ECregex = r"[1-9][0-9]{2}-[0-9]{3}-[0-9](?![0-9])"
CosIngWithEC = CosIngNoFunctions2.loc[CosIngNoFunctions2.EC_No.str.contains(ECregex)]

CosIngEClist = CosIngWithEC.EC_No.drop_duplicates().tolist()
CosIngAllConcatenatedEC = "".join(CosIngEClist)
CosIngECchars = set(list(CosIngAllConcatenatedEC))
CosIngECchars2 = CosIngECchars - alphabet
CosIngECchars3 = CosIngECchars2 - numbers
"""Delimiter seems to be the same as for CAS RNs"""

"""Ok so, I see that the EC and CAS RN fields sometimes each contain no values,
1 value, or multiple concatenated values that are delimited by a comma, forward
slash, or semicolon. I've seen the following cases so far

1. a field has one value and the other field has multiple values
2. both fields have the same number of values. This has 2 variations
2a. each field has a single value
2b. each field has multiple values
3. a field has no values while the other field has at least one value

So I'll do this. For case (1), I will treat this substance so that there is a
one-to-many match between the field that has a single value and the field that
has multiple values. For case (2a), I will treat both fields so that they have
a one-to-one relationship. For case (2b), I will carefully match a value from
one field with a value from the other field based on both value's positions
within each field. For example, the 1st value from the CAS field will be
matched with the 1st value from the EC field, the 2nd value from the CAS field
with the 2nd value from the EC field, etc,.
"""
splitIndexColumns = ["Type", "INCI", "Annex"]
CosIngWithCAS = (CosIngWithCAS.set_index(splitIndexColumns)
                 .CAS.str.split(CASdelimiter, expand=True)
                 .reset_index()
                 .melt(splitIndexColumns, var_name="order", value_name="individualCAS")
                 .query("individualCAS.notna() & individualCAS != ''")
                 )
CosIngWithCAS = CosIngWithCAS.loc[~CosIngWithCAS.individualCAS.str.isspace()]
numOfCAS = (CosIngWithCAS.groupby(splitIndexColumns)["individualCAS"].count()
            .reset_index()
            .rename(columns={"individualCAS": "numberOfValues"})
            )
CosIngWithCAS = CosIngWithCAS.merge(numOfCAS, "inner", splitIndexColumns)
CosIngMultipleCAS = CosIngWithCAS.query("numberOfValues > 1")

CosIngWithEC = (CosIngWithEC.set_index(splitIndexColumns)
                 .EC_No.str.split(CASdelimiter, expand=True)
                 .reset_index()
                 .melt(splitIndexColumns, var_name="order", value_name="individualEC")
                 .query("individualEC.notna() & individualEC != ''")
                 )
CosIngWithEC = CosIngWithEC.loc[~CosIngWithEC.individualEC.str.isspace()]
numOfEC = (CosIngWithEC.groupby(splitIndexColumns)["individualEC"].count()
           .reset_index()
           .rename(columns={"individualEC": "numberOfValues"})
           )
CosIngWithEC = CosIngWithEC.merge(numOfEC, "inner", splitIndexColumns)
CosIngMultipleEC = CosIngWithEC.query("numberOfValues > 1")

"""Matching substances with the same number of values for EC and CAS and each
field has multiple values. These entries consist of substances where each field
consists of at least 1 value that follows the normal EC or CAS number formats,
but there are also values that are nonexistent and only exists in the database
as a dash. For example, there might be a substance with 2 EC values that
properly follow the EC number format and 2 CAS values where only 1 value
properly follows the CAS number format and the other value is simply a dash."""
CosIng_multipleECandCAS_sameValues = CosIngMultipleCAS.merge(CosIngMultipleEC, "inner", ["Type", "INCI", "Annex", "order", "numberOfValues"])

"""Matching substances where EC and CAS each have a single value. This only
includes substances where the values properly follow their respective formats.
"""
CosIngSingleCAS = (CosIngWithCAS.query("numberOfValues == 1")
                   .drop(columns=["order", "numberOfValues"])
                   )
CosIngSingleEC = (CosIngWithEC.query("numberOfValues == 1")
                  .drop(columns=["order", "numberOfValues"])
                  )
CosIng_singleECandCAS_validFormats = CosIngSingleCAS.merge(CosIngSingleEC, "inner", splitIndexColumns)

"""So I've matched substances with the same number of values for EC and CAS.
Let's also match together other substances that haven't been matched so far.
The following cases can still exist

1. Substances where 1 field has 1 single valid value and the other field has
multiple values
2. Substances where 1 field has no values and the other field has at least 1
valid value, either 1 valid value or multiple values and 1 or more of them are
valid
3. Substances where both fields have no valid values
"""
CosIng_matchedECandCASsoFar = pd.concat([CosIng_multipleECandCAS_sameValues, CosIng_singleECandCAS_validFormats])
allSubstanceINCI = set(CosIngNoFunctions2.INCI.tolist())
matchedINCIsoFar = set(CosIng_matchedECandCASsoFar.INCI.tolist())
stillUnmatchedINCI = allSubstanceINCI - matchedINCIsoFar
CosIng_singleValidEC_multipleCAS = CosIngSingleEC.merge(CosIngMultipleCAS, "inner", splitIndexColumns)
CosIng_singleValidCAS_multipleEC = CosIngSingleCAS.merge(CosIngMultipleEC, "inner", splitIndexColumns)
CosIng_singleValidValue_multipleValues = (pd.concat([CosIng_singleValidEC_multipleCAS, CosIng_singleValidCAS_multipleEC])
                                          .drop_duplicates()
                                          )

CosIngNoEC = CosIngNoFunctions2.loc[CosIngNoFunctions2.EC_No == "-"]
CosIng_noEC_validCAS = (CosIngNoEC.merge(CosIngWithCAS, "inner", splitIndexColumns)
                        .drop(columns=["CAS"])
                        .rename(columns={"EC_No": "individualEC"})
                        .drop_duplicates()
                        )
CosIngNoCAS = CosIngNoFunctions2.loc[CosIngNoFunctions2.CAS == "-"]
CosIng_noCAS_validEC = (CosIngNoCAS.merge(CosIngWithEC, "inner", splitIndexColumns)
                        .drop(columns=["EC_No"])
                        .rename(columns={"CAS": "individualCAS"})
                        .drop_duplicates()
                        )
CosIng_noValues_validValues = (pd.concat([CosIng_noEC_validCAS, CosIng_noCAS_validEC])
                               .drop_duplicates()
                               )

CosIng_bothNoValidValues = (CosIngNoFunctions2.query("(CAS == '-') & (EC_No == '-')")
                            .rename(columns={"CAS": "individualCAS", "EC_No": "individualEC"})
                            .drop_duplicates()
                            )

CosIng_matchedECandCASsoFar2 = (pd.concat([CosIng_multipleECandCAS_sameValues, CosIng_singleECandCAS_validFormats, CosIng_singleValidValue_multipleValues, CosIng_noValues_validValues, CosIng_bothNoValidValues])
                                .drop_duplicates()
                                )
matchedINCIsoFar2 = set(CosIng_matchedECandCASsoFar2.INCI.tolist())
stillUnmatchedINCI2 = allSubstanceINCI - matchedINCIsoFar2

"""There are 17 INCI names whose EC and CAS are still unmatched. These
substances have mismatches in the numbers of values of EC and CAS where each
field has at least 2 values instead of 1 value, so you can't assign the single
value in a single-value field to all the values in a field with multiple
values. I'll still match them by position anyway, but if there are values that
are still unmatched because the other field has too few values, then I'll let
them remain unmatched."""
CosIngStillUnmatched = CosIngNoFunctions2.loc[CosIngNoFunctions2.INCI.isin(stillUnmatchedINCI2)]
CosIngWithCASunmatched = CosIngWithCAS.loc[CosIngWithCAS.INCI.isin(stillUnmatchedINCI2)]
CosIngWithCASunmatched = CosIngWithCASunmatched.drop(columns=["numberOfValues"])
CosIngWithECunmatched = CosIngWithEC.loc[CosIngWithEC.INCI.isin(stillUnmatchedINCI2)]
CosIngWithECunmatched = CosIngWithECunmatched.drop(columns=["numberOfValues"])
CosIngFinalMatch = CosIngWithCASunmatched.merge(CosIngWithECunmatched, "outer", ["Type", "INCI", "Annex", "order"])
CosIngFinalMatch.loc[CosIngFinalMatch.individualCAS.isna(), "individualCAS"] = "-"
CosIngFinalMatch.loc[CosIngFinalMatch.individualEC.isna(), "individualEC"] = "-"

CosIngIdentifiersFull = (pd.concat([CosIng_multipleECandCAS_sameValues, CosIng_singleECandCAS_validFormats, CosIng_singleValidValue_multipleValues, CosIng_noValues_validValues, CosIng_bothNoValidValues, CosIngFinalMatch])
                         .drop(columns=["order", "numberOfValues"])
                         .drop_duplicates()
                         .reset_index(drop=True)
                         )

"""Final sanity check to ensure that there are no ingredients that went missing
in this process"""
finalSubstances = set(CosIngIdentifiersFull.INCI.tolist())
missingInitial = allSubstanceINCI - finalSubstances
"""The set missingInitial is empty, so there are no substances that went
missing while I was trying to associate EC and CAS RNs with each other by
position."""
# %%
"""Now that I've fully associated identifiers based on position, let's clean
identifiers off of miscellaneous bits of string"""
CosIngCleaningIdentifiers = CosIngIdentifiersFull.copy()

CAScapture = r"([1-9][0-9]{1,6}-[0-9]{2}-[0-9])"
CosIngCAS = (CosIngCleaningIdentifiers.individualCAS.str.extract(CAScapture)
             .rename(columns={0: "cleanCASRN"})
             )

ECcapture = r"([1-9][0-9]{2}-[0-9]{3}-[0-9])"
CosIngEC = (CosIngCleaningIdentifiers.individualEC.str.extract(ECcapture)
            .rename(columns={0: "cleanEC"})
            )
CosIngCleaningIdentifiers = (CosIngCleaningIdentifiers.join(CosIngCAS)
                             .join(CosIngEC)
                             .drop(columns=["individualCAS", "individualEC"])
                             .rename(columns={"cleanCASRN": "CASRN", "cleanEC": "EC"})
                             )
CosIngCleaningIdentifiers.loc[CosIngCleaningIdentifiers.CASRN.isna(), "CASRN"] = "-"
CosIngCleaningIdentifiers.loc[CosIngCleaningIdentifiers.EC.isna(), "EC"] = "-"

CosIngFull = (CosIngCleaningIdentifiers.merge(CosIng, "inner", ["Type", "INCI", "Annex"])
              .drop(columns=["functionURL", "CAS", "EC_No"])
              .drop_duplicates()
              )
# %%
"""And I'm done wrangling the CosIng database. Now I'm going to export the
wrangled database."""

note = ["This is a scrape of the EU CosIng database. The database was scraped",
        "on January 21, 2026. I then spent the next 2 days wrangling it.",
        "The chemical identifiers used here are CAS RNs and EC numbers. There",
        "are many substances that have multiple values of one or both types of",
        "identifiers, and these values are concatenated by commas, forward",
        "slashes, or semicolons. For these substances, I associate the values",
        "of one identifier with the values from the other identifier based on",
        "the positions of each value within each field. For example, if a",
        "substance has 3 CAS RNs and 3 EC numbers, I associated the 1st CAS",
        "RN with the 1st EC, the 2nd CAS RN with the 2nd EC, and the 3rd CAS",
        "RN with the 3rd EC. There are certain substances that have",
        "mismatches in the number of values of each identifier type, such as",
        "certain substances with only 1 CAS RN but 3 EC numbers or vice versa",
        "or substances with 2 CAS RNs and 3 EC numbers. The former are",
        "cases where one identifier has 1 value while the other identifier",
        "has multiple; for these cases, I simply assumed this single value",
        "with all values from the other identifier. The latter are cases where",
        "each identifier has multiple values but one identifier has more values;",
        "for these cases, I continued matching values based on their positions,",
        "but there inevitably were values that remained unmatched. For example,",
        "if a substance has 2 CAS RNs and 3 EC numbers, the 1st CAS RN was",
        "matched with the 1st EC number, the 2nd CAS RN with the 2nd EC,",
        "but I left the 3rd EC unmatched to any CAS RNs because there was no",
        "3rd CAS RN. There were also substances where either one or both",
        "identifiers had no values; if these substances have 1 identifier with",
        "multiple values and another identifier with no values, then I simply",
        "splitted the identifier with multiple values.",
        "",
        "I then cleaned each identifier off of substrings at the end, such as",
        "'(generic)'. For substances that don't have one or both identifiers,",
        "I assigned a simple dash '-' for the nonexistent identifier(s).",
        "",
        "Hope this work will be useful later on."]
readMe = pd.DataFrame({"Note": note})
cleanedDatabasePath = outputFolder/"Cleaned CosIng database - scraped on January 21, 2026.xlsx"
if os.path.exists(cleanedDatabasePath) is False:
    with pd.ExcelWriter(cleanedDatabasePath) as w:
        readMe.to_excel(w, index=False)
        CosIngFull.to_excel(w, "Substance - function", index=False)
        CosIngCleaningIdentifiers.to_excel(w, "Substances", index=False)
        functionDF.to_excel(w, "Functions", index=False)
