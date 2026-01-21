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
import re

repository = Path(os.getcwd())
repositoryFolder = Path(os.path.dirname(repository))
dataFolder = repositoryFolder/"Data"
inputFolder = dataFolder/"Input"

dataPath = inputFolder/"Mintel download.xlsx"
importDtype = {"Record ID": "string", "Bar Code": "string"}
original1 = pd.read_excel(dataPath, header=7, dtype=importDtype)

dataPath2 = inputFolder/"Mintel download - December 2025.xlsx"
original2 = pd.read_excel(dataPath2, dtype=importDtype)

dataPath3 = inputFolder/"Mintel download - triethanolamine.xlsx"
original3 = pd.read_excel(dataPath3, header=6, dtype=importDtype)

original = (pd.concat([original1, original2, original3])
            .drop_duplicates()
            .reset_index(drop=True)
            )
original["Date Published"] = pd.to_datetime(original["Date Published"])
original = original.drop_duplicates()
original.loc[original["Bar Code"].isna(), "Bar Code"] = ""
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
inactiveRegex3 = r" inactive( ingredients)?: "
activeRegex1 = r"^[Aa]ctive [Ii]ngredients?: "
activeRegex2 = r"^[Aa]ctive [Ii]ngredients? \("
activeRegex3 = r"\)? (sunscreen lip balm|AM Restore|antiperspirant dry)[^:]*?: [Aa]ctive [Ii]ngredients? \("
middleActiveInactive = r" ([Ii]n)?[Aa]ctive [Ii]ngredients?: "
# beginningText = r"^([a-zA-Z0-9\s']|[-/&()+!])+?(?!(([Ii]n)?[Aa]ctive [Ii]ngredient|,)):"
beginningText = r"^([a-zA-Z0-9\s']|[-/&()+!])+?(?!(([Ii]n)?[Aa]ctive [Ii]ngredient|,))(:| \()"
mayContain1 = r"\+\s?/?\s?-? (all shades )?may( also)? con(ta|at)in:? \(|\+/-\s?may \(|\+/- \(|\+-/ may contain \(|\+/- may contain [^(]*\("
mayContain2 = r"may (also )?contain \(?"
laPrairiePatent = r"(, )?[Ii]\d{2} \*new patent pending for [Ll][Aa] [Pp]r?airie.*$"
POREfessional_og = "The POREfessional (Super Setter Long-Lasting Makeup Setting Spray|Good Cleanup Pore-Purifying Foaming Cleanser)"
irregularDelimiters1 = r" \(?or|and|(and/or)\)? | \+ | & |,\* | (brown eyeliner/brow pencil|eyebrow cream|(eye|brow) pencil|Norvina Chroma Stix Makeup Pencil Violet|(shade |gold shimmer |prisma glass )?0?\([2-9]\)|highlighter|lip (stick|gloss|liner)|sinner - rose|Velvet Noir Major Volume Mascara|No 00N12802 GALifornia Sunny Golden-Pink Blush|Aveeno Baby Daily Moisture Lotion|Natural Lip Balm ingredients|Strawberry Lip Butter|foil|Highliner Gel Eye Crayon|Nude Skincare Perfect Cleanse Omega cleansing Jelly|Fleur|glitter|anti-perspirant|\*[Hh]adasei-3 The Liquid Silk Canvas|dermatologist solutions powerful-strength line-reducing dark circle-diminishing vitamin C eye serum|Secret Powder Fresh Antiperspirant Deodorant Invisible Solid Stick|Shimmering Skin Perfector Pressed Highlighter in Pink Pyrite/Aquamarine/Citrine/Coral Crystal ingredients|Water Drench Hyaluronic Cloud Cream Hydrating Moisturizer - active ingredients|L'Absolu Rouge Cream Lipstick in the shade 274 French Tea|\(Plant Based\) \*{3}napiers aqua formula aqua bomb makeup removing cleansing balm|Body Exotics Japanese Camellia Body Oil Blend|Clear Improvement Active Charcoal Mask to Clear Pores|loveshine high-shine caring lipstick in the shade 44 nude lavalliere|Deluxe Sample Crushed Oil-Infused Gloss in shade In the Buff|rouge pur couture satin colour lipstick in the shade nu muse|master lab intensive soothing care centella asiatica soothing care mask sheet|Mascara Volume Effet Faux Cils Haute Densité Mascara in the shade No\.1 Noir|blacktop/bourbon/chianti/confectionette/coronation/midnight emerald/mist/obsidian/sapphires|Chocolate Bon Bons Eye Shadow Collection/almond truffle/pecan praline/mocha/bordeaux|The POREfessional [^:]+?|galifornia golden pink blusher|strawberry/cherry/original classic|Hope in a Jar Barrier Restore Cream: Unavailable Amazing Grace Hydrating Shower Gel|amazonian clay matte eye shadow palette dreamer/natural beauty/multi-tasker/force of nature|Full-Size Extra Plump Lip Serum in the shade Bare Pink): "
irregularDelimiters2 = r"\) (Deluxe melted \b\w+\b liquified( \b\w+\b){2,3} lipstick -( \b\w+\b){2,4} ingredients|photo finish.*) \("
irregularDelimiters3 = r" ((green apple |cranberry )?beary( lip)?|nudies bloom|Rouge Pur Couture|Make Out Ready|PlushtTint Moisturizing|\*coconut/plant/starch/vegetable derived|hoola matte|le vestiaire des|Advanced Night Repair|Lip Glass/Clear: unavailable LipGlass|Under\(cover\) Perfecting|Wanderful World Blush/willa|Hoola Matte|coconut intensely|viatmin e overnight)[^:]*?: "
irregularDelimiters4 = r"\) (smashbox be|Charlotte's Magic|Hollywood Beauty|Hello FAB|Pure Color|Galifornia Sunny|[Ss]oft [Gg]lam|almond/best coast|brow power|Chocolate Bon Bons|Mini Long-Wear Cream|amazonian clay matte|Glitter/Cinnamon Sugar|\*synthetic Marshmallow|Deluxe Shadow|Moisturizing Renewal|Pressed [Pp]igments|glamour dust|Nudies Glow)[^:]+?: "
irregularDelimiters5 = r"[ \n](Midnight Recovery|prisma glass|strawberry/cherry|\*Korres Santorini|Retinol Skin-Renewing|sugar rush lip|Lip Glass|iginal formula|scarlet poppy|revolution lip|acne clearing|dermalogica (age smart )?multivitamin|Infallible Original|Super Healthy Skin|modern renaissance|the professional pore|makeup revolution loose|Cold-Pressed 100%|vital skin-strengthening|broad spectrum spf 28|[Aa]dvanced [Cc]eramide [Cc]apsules|powerful-strength line-reducing|\*does not|dermatologist solutions|pro-collagen naked|Dessin du Regard|pure color|Tata Harper|SplashTint|revolution (satin|highlighter|cream)|spa of the world|\*Guarana caffeine|Mini Highlighting|Whipped Moisturizing|photo op|Superhero No-Tug|Charlotte's Magic|BADgal BANG|midnight recovery|Powerful-Strength Dark Circle|Royal Blowout Heat|lines liberated|base tape|Cellular Recovery|Mascara Volume|multi-perfecting|rouge pur couture|Fab\.Me Leave-In|eyes to kill|\*(extracted from larch tree|coconut/vegetable/soybean)|Fiery Pink Pepper|gold 007 crystalline|Lustreglass)[^:]+?: "
irregularDelimiters6 = r"(Sunset yellow Re-Charge)[^:]+: "
irregularDelimiters7 = r"(/or|(Part B|gentle action application pads|bond reconstructing treatment|intensive moisture repair mask|face/chin strip|rock 'n' kohl|MODSST01 moroccanoil treatment|dermalogica age smart.*|amika obliphica the wizard multi-benefit primer|(the )?(PORE|pore)fessional.*[Pp]rimer|line blurfector instant wrinkle blurring primer|long-wear cream shadow stick in golden bronze|Superactive Capsules Essential Ceramides \+|deodorant|Highliner Matte Gel Eye Crayon|liner ingredients):) "
spfDelimiters = r"[ \n]([Dd]ouble-duty|[Dd]aily (Sunscreen|moisturizer)|Fermitif Neck Renewal|dermalogica dynamic|acne complex|Ultimate Sun Protector|Protective Fortifying|Environmental Shield|\*organic ingredient Spring Break|smoothness lip care|Moisturizing Renewal|intense therapy|city skin|[Tt]otal [Pp]rotective|dynamic skin|Clear Shield|Mineral Sun|Resist Super-Light|Clear Stick|Revitalizing Supreme\+|facial fuel|CC Crème|Clinique|Multi-Protect|repairwear|5% vitamin c sheer|(eight hour )?lip protectant|Sun Drops).+?(spf|SPF)\s?\d{2}\+?( [Aa]ctive( ingredients)?|/inactive ingredients| Custom-Repair Moisturizer| (PA|pa)\+{2,4})?[^:]*?:( [Aa]ctive ([Ii]ngredients )?\()?"
essentialOilsDelimiters = "Essential Oils \(Essential\) (A Perfect World|High-Potency Night-[Aa]-Mins|Acne Treatment|GinZing Oil-Free)?[^:]+?:( [Aa]ctive ([Ii]ngredients )?\()?"
ingredientProduct["ingredientList"] = ingredientProduct.originalIngredientList
ingredientProduct["ingredientList"] = (ingredientProduct["ingredientList"].str.replace(inactiveRegex1, ", ", regex=True)
                                       .str.replace(inactiveRegex2, " ", regex=True)
                                       .str.replace(inactiveRegex3, ", ", regex=True)
                                       .str.replace(activeRegex1, "", regex=True)
                                       .str.replace(activeRegex2, "", regex=True)
                                       .str.replace(activeRegex3, ", ", regex=True)  # For delimiters that may start with a closing parentheses, space, some text, a colon, space, and ends with active ingredient and an open parenthesis
                                       .str.replace('^"', "", regex=True)
                                       .str.replace(r"^[Aa]qua \(.+?\)", "Aqua", regex=True)
                                       .str.replace(beginningText, "", regex=True)
                                       .str.replace(mayContain1, "", regex=True)
                                       .str.replace(mayContain2, "", regex=True)
                                       .str.replace(laPrairiePatent, "", regex=True)
                                       .str.replace("\n", " ", regex=True)
                                       .str.replace(irregularDelimiters1, ", ", regex=True)  # For (1) and, (2) or, (3) and/or, and (4) for delimiters that starts with a space and a word and ends with a colon and space
                                       .str.replace(irregularDelimiters2, ", ", regex=True)  # For delimiters that starts with a closing parenthesis and ends with an open parenthesis
                                       .str.replace(irregularDelimiters3, ", ", regex=True)  # For delimiters that starts with a space and word and ends with a colon and space
                                       .str.replace(irregularDelimiters4, ", ", regex=True)  # For delimiters that starts with a closing parenthesis and space and ends with a colon and space
                                       .str.replace(irregularDelimiters5, ", ", regex=True)  # Similar to irregularDelimiters1, for delimiters that starts with a space and word and ends with a colon and space
                                       .str.replace(irregularDelimiters6, ", ", regex=True)  # For when there is a comma, miscellaneous text that ends with a colon and space and then an actual ingredient name, so there are effectively 2 delimiters (a comma and miscellaneous text) in one
                                       .str.replace(irregularDelimiters7, ", ", regex=True)  # For other delimiters that prevent proper separation of the targeted ingredients, such as "/or" acting as a delimiter
                                       .str.replace(spfDelimiters, ", ", regex=True)  # For delimiters that starts with a space and word, contains spf or SPF, a colon, and can end with active ingredient or active ingredient followed by a space and an open parenthesis
                                       .str.replace(essentialOilsDelimiters, ", ", regex=True)  # For delimiters that starts with a space and Essential Oils (Essential), followed by some words, and ends with a colon
                                       .str.replace(middleActiveInactive, ", ", regex=True)  # For when (in)active ingredient, ending with a colon and space, is in the middle of an ingredient list
                                       .str.replace("dimethiconol TEA-dodecylbenzenesulfonate", "dimethiconol, TEA-dodecylbenzenesulfonate", regex=False)
                                       .str.replace("Squalane Triethanolamine", "Squalane, Triethanolamine", regex=False)
                                       .str.replace("TEA- lauryl sulfate", "TEA-lauryl sulfate", regex=False)
                                       .str.replace("Polyquaternium-7 (Fabric Softeners)", "Polyquaternium-7", regex=False)
                                       .str.replace("polyquaternium-37 (3000 MPA.S)", "polyquaternium-37", regex=False)
                                       .str.replace("2-oleamido-1, ", "2-oleamido-1,", regex=False)
                                       .str.replace(r"Acetamidoethyl PG-trimonium Chloride[^:]+?: Aqua", "Acetamidoethyl PG-trimonium Chloride, Aqua", regex=True)
                                       .str.replace(r"Acetamidoethyl PG-trimonium Chloride[^:]+?: Talc", "Acetamidoethyl PG-trimonium Chloride, Talc", regex=True)
                                       .str.replace(r"Acetamidoethyl PG-trimonium Chloride[^:]+?: Dimethicone", "Acetamidoethyl PG-trimonium Chloride, Dimethicone", regex=True)
                                       .str.replace(r"Alcohol Denat\.[^:]+?: Aqua", "Alcohol Denat\., Aqua", regex=True)
                                       .str.replace(r"Allantoin[^:]+?: Aqua", "Allantoin, Aqua", regex=True)
                                       .str.replace(r"Aloe Vera Leaf Extract[^:]+?: Aqua", "Aloe Vera Leaf Extract, Aqua", regex=True)
                                       .str.replace(r"Aloe Vera Leaf Extract[^:]+?: Cetyl Ethylhexanoate", "Aloe Vera Leaf Extract, Cetyl Ethylhexanoate", regex=True)
                                       .str.replace(r"Aloe Vera Leaf Extract[^:]+?: Caprylic/Capric Triglyceride", "Aloe Vera Leaf Extract, Caprylic/Capric Triglyceride", regex=True)
                                       .str.replace(r"Alpha-isomethyl Ionone[^:]+?: Aqua", "Alpha-isomethyl Ionone, Aqua", regex=True)
                                       .str.replace(r"Alpha-isomethyl Ionone[^:]+?: Vitis Vinifera Seed Oil", "Alpha-isomethyl Ionone, Vitis Vinifera Seed Oil", regex=True)
                                       .str.replace(r"Alpha-isomethyl Ionone[^:]+?: Hydrofluorocarbon 152a", "Alpha-isomethyl Ionone, Hydrofluorocarbon 152a", regex=True)
                                       .str.replace(r"Aluminum Powder[^:]+?: Cyclopentasiloxane", "Aluminum Powder, Cyclopentasiloxane", regex=True)
                                       .str.replace(r"BHT[^:]+?: Cyclopentasiloxane", "BHT, Cyclopentasiloxane", regex=True)
                                       .str.replace(r"Benzyl Benzoate[^:]+?: Cyclopentasiloxane", "Benzyl Benzoate, Cyclopentasiloxane", regex=True)
                                       .str.replace(r"Butylene Glycol[^:]+?: Cyclopentasiloxane", "Butylene Glycol, Cyclopentasiloxane", regex=True)
                                       .str.replace(r"CI 15985[^:]+?: Cyclopentasiloxane", "CI 15985, Cyclopentasiloxane", regex=True)
                                       .str.replace(r"CI 16255[^:]+?: Cyclopentasiloxane", "CI 16255, Cyclopentasiloxane", regex=True)
                                       .str.replace(r"CI 19140[^:]+?: Cyclopentasiloxane", "CI 19140, Cyclopentasiloxane", regex=True)
                                       .str.replace(r"CI 42090[^:]+?: Cyclopentasiloxane", "CI 42090, Cyclopentasiloxane", regex=True)
                                       .str.replace(r"CI 47005[^:]+?: Cyclopentasiloxane", "CI 47005, Cyclopentasiloxane", regex=True)
                                       .str.replace(r"CI 75470[^:]+?: Cyclopentasiloxane", "CI 75470, Cyclopentasiloxane", regex=True)
                                       .str.replace(r"CI 77007[^:]+?: Cyclopentasiloxane", "CI 77007, Cyclopentasiloxane", regex=True)
                                       .str.replace(r"CI 77266[^:]+?: Cyclopentasiloxane", "CI 77266, Cyclopentasiloxane", regex=True)
                                       .str.replace(r"CI 77491[^:]+?: Cyclopentasiloxane", "CI 77491, Cyclopentasiloxane", regex=True)
                                       .str.replace(r"CI 77492[^:]+?: Cyclopentasiloxane", "CI 77492, Cyclopentasiloxane", regex=True)
                                       .str.replace(r"CI 77499[^:]+?: Cyclopentasiloxane", "CI 77499, Cyclopentasiloxane", regex=True)
                                       .str.replace(r"CI 77510[^:]+?: Cyclopentasiloxane", "CI 77510, Cyclopentasiloxane", regex=True)
                                       .str.replace(r"Titanium Dioxide[^:]+?: Cyclopentasiloxane", "Titanium Dioxide, Cyclopentasiloxane", regex=True)
                                       .str.replace("CI 77492)) Pore No More Pore Refiner Primer (Cyclopentasiloxane", "CI 77492, Cyclopentasiloxane", regex=False)
                                       .str.replace("CI 77499 (Black 11)) Double Take Eyeliner: pencil (Cyclopentasiloxane", "CI 77499, Cyclopentasiloxane", regex=False)
                                       .str.replace("Cinnamyl Alcohol blow-dry spray: Cyclopentasiloxane", "Cinnamyl Alcohol, Cyclopentasiloxane", regex=False)
                                       .str.replace("Citric Acid pure colour frizz-fighting gloss: Cyclopentasiloxane", "Citric Acid, Cyclopentasiloxane", regex=False)
                                       .str.replace("Cyclopentasiloxane 2: Isobutane", "Cyclopentasiloxane, Isobutane", regex=False)
                                       .str.replace("Ethylhexylglycerin) color correting face primer (Cyclopentasiloxane", "Ethylhexylglycerin, Cyclopentasiloxane", regex=False)
                                       .str.replace(r"(ILN|T3333|VGC03T|hair oil other)[^:]+?: Cyclopentasiloxane", "Cyclopentasiloxane", regex=True)
                                       .str.replace(r"Methylisothiazolinone[^:]+?: Cyclopentasiloxane", "Methylisothiazolinone, Cyclopentasiloxane", regex=True)
                                       .str.replace(r"Phenoxyethanol[^:]+?: Cyclopentasiloxane", "Phenoxyethanol, Cyclopentasiloxane", regex=True)
                                       .str.replace("disteardmonium hectorite cyclopentasiloxane", "disteardmonium hectorite, cyclopentasiloxane", regex=False)
                                       .str.replace("Iodopropynyl Butylcarbamate oil: Cyclopentasiloxane", "Iodopropynyl Butylcarbamate, Cyclopentasiloxane", regex=False)
                                       .str.replace("Sodium Phytate illuminate: Cyclopentasiloxane", "Sodium Phytate, Cyclopentasiloxane", regex=False)
                                       .str.replace("Tocopherol seal: Cyclopentasiloxane", "Tocopherol, Cyclopentasiloxane", regex=False)
                                       .str.replace("cyclopentasiloxane &dimethicone", "cyclopentasiloxane, dimethicone", regex=False)
                                       .str.replace(r", in the shade.+? \(", ", ", regex=True)
                                       .str.replace(r", Cyclopentasiloxane \*[a-zA-Z]+?\b", ", Cyclopentasiloxane, ", regex=True)
                                       .str.replace("pencil (Cyclopentasiloxane", "Cyclopentasiloxane", regex=False)
                                       .str.replace("Cyclopentasiloxane)", "Cyclopentasiloxane", regex=False)  #
                                       .str.replace(r"ILN ?[0-9]{5}[^:]+?: Petrolatum", "Petrolatum", regex=True)
                                       .str.replace(r"Petrolatum \(\w+\)", "Petrolatum", regex=True)
                                       .str.replace(r"Petrolatum (Active", "Petrolatum", regex=False)
                                       .str.replace(r"(?<!CI )[0-9]{5}[^:]+?: Petrolatum", "Petrolatum", regex=True)
                                       .str.replace(r"CI 19140[^:]+?: Petrolatum", "CI 19140, Petrolatum", regex=True)
                                       .str.replace(r"Isopropyl Titanium Triisostearate[^:]+?: Petrolatum", "Isopropyl Titanium Triisostearate, Petrolatum", regex=True)
                                       .str.replace(r"Titanium Dioxide[^:]+?: Petrolatum", "Titanium Dioxide, Petrolatum", regex=True)
                                       .str.replace(r"Tocopherol[^:]+?: Petrolatum", "Tocopherol, Petrolatum", regex=True)
                                       .str.replace(r",{2,10}", ", ", regex=True)
                                       .str.replace(r" {2,10}", " ", regex=True)
                                       .str.strip()
                                       )

"""For some reason, Pandas couldn't remove the regex activeRegex2. I'm just
going to remove it manually in a for loop"""
for index, row in ingredientProduct.iterrows():
    ingredientList = row.ingredientList
    ingredientProduct.loc[index, "ingredientList"] = re.sub(activeRegex2, "", ingredientList)

# Splitting ingredient lists
ingredientListDF = (ingredientProduct.filter(["ingredientList"]).drop_duplicates()
                    .set_index("ingredientList", False)
                    )

splitRegex = r", "
splitDF = (ingredientListDF.ingredientList.str.split(splitRegex, expand=True, regex=True)
           .reset_index(drop=False)
           .melt("ingredientList", var_name="ingredientOrder", value_name="name1")
           .query("name1.notna()")
           )
splitDF.ingredientOrder = splitDF.ingredientOrder + 1
splitDF = splitDF.loc[~(splitDF.name1.str.isspace() | (splitDF.name1 == ""))]
splitDF.name1 = splitDF.name1.str.strip()

ingredientsOnly = (splitDF.filter(["name1"])
                   .reset_index(drop=True)
                   .drop_duplicates()
                   )
ingredientsOnly["ogNameLength"] = ingredientsOnly.name1.str.len()
ingredientsOnly = ingredientsOnly.sort_values(["ogNameLength", "name1"], ascending=[False, True])

# Cleaning ingredient names
inTheShade = r"in the shade .*?\("
ingredientsOnly["name2"] = ingredientsOnly.name1.str.replace(inTheShade, "")
shimmerShades = r"shimmer (and metallic )?shades "
ingredientsOnly["name2"] = ingredientsOnly.name2.str.replace(shimmerShades, "")
shade = r'shade \d (" )?\('
ingredientsOnly["name2"] = ingredientsOnly.name2.str.replace(shade, "")
multipleIngredients = ["Salix alba (willow) bark extract/sodium laureth sulfate",
                       "water (aqua) & erytritol & homarine HCL",
                       "Cocoyl Hydrolyzed Keratin and/or Sorbitan Oleate and/or Isostearic Acid (Hydrolysed)",
                       "Sodium Hyaluronate) Elements (Inactive) (Aqua",
                       "CI 77499 (Black 11) brown eyeliner/brow pencil: Synthetic Beeswax (Artificial)",
                       "Borojoa patinoi fruit juice (and) Camellia sinensis leaf extract (and) Cinchona succirubra bark extract (and) Ginkgo biloba leaf extract (and) Guazuma ulmifolia leaf extract (and) Rosmarinus officinalis leaf extract (and) Serenoa serrulata fruit extract (and) Thymus vulgaris flower/leaf/stem extract (and) Tropaeolum majus flower/leaf/stem extract (and) hydrolyzed wheat protein",
                       "Pseudozyma epicola (and) Argania spinosa kernel oil (and) Camellia japonica seed oil (and) Camellia sinensis seed oil (and) sunflower seed oil (and) sweet almond oil ferment extract filtrate",
                       "Gossypium Herbaceum Seed Oil and/or Linum Usitatissimum Seed Oil) Ascorbic Acid (Infused) (Aqua",
                       "Glycine soja seed extract (and) Triticum vulgare germ extract (and) hydrolyzed soy extract (and) hydrolyzed yeast protein (and) hydrolyzed wheat protein",
                       "Titanium Dioxide) eyebrow cream: Paraffinum Liquidum (Liquid)",
                       "CI 77499 (Black 11)) eye pencil: Paraffinum Liquidum (Liquid)",
                       "CI 77266 (Nano) Norvina Chroma Stix Makeup Pencil Violet: Isododecane",
                       "Synthetic Fluorphlogopite (Artificial) 2: Calcium Titanium Borosilicate",
                       "CI 77491) highlighter: Synthetic Beeswax (Artificial)",
                       "CI 77499 (Black 11) lip stick: Paraffinum Liquidum (Liquid)",
                       "Hydroxycitronellal and/or Benzyl Salicylate and/or Parfum and/or L-limonene (Supplement)",
                       "CI 77499 (Black 11) sinner - rose: Ricinus Communis (Castor) Seed Oil"
                       "Aluminum Powder (Powdered) Velvet Noir Major Volume Mascara: Aqua"
                       "Hydrogenated Jojoba Oil (Hydrogenated) luminous oils coconut oil & lavender ingredients: Aqua"
                       "CI 61570 (Green) sweet lemon and gardenia: Aqua",
                       "Charcoal Powder (Powdered) Cocos Nucifera Fruit",
                       "Aloe Barbadensis Leaf (Essential) (Citrus Medica Limonum Fruit Oil (Essential)",
                       "Titanium Dioxide) Deluxe melted chocolate liquified long wear lipstick - Chocolate Honey ingredients (Ricinus Communis (Castor) Seed Oil",
                       "Phenoxyethanol Essential Oils (Essential) Sucrose (Organic)",
                       "Biotin/folic Acid/cyanocobalamin/niacinamide/pantothenic Acid/Pyridoxine/Riboflavin/Thiamine/Yeast Polypeptides",
                       "Parfum *Korres Santorini grape fruit extract Apothecary Wild Rose Night-Brightening Sleeping Facial: Aqua",
                       "Pentaerythrityl Tetra-Di-t-Butyl Hydroxyhydrocinnamate Retinol Skin-Renewing Daily Micro-Dose Serum: Aqua",
                       "CI 16035 Niacin Panthenol Tocopherol ^amino-peptide Camellia Sinensis Leaf (Green) Aloe Barbadensis Leaf",
                       "Sodium Benzoate *BioCell Collagen CG providing hydrolyzed collagen type II peptides chondroitin sulfate ",
                       "aluminum hydroxide benzimidazole diamond amidoethyl urea carbamoyl propyl polymethylsilsesquioxane",
                       "CI 42090 (Lake)) pressed pigments (the butterfly/soft center/workaholic/chourico/tea time) talc",
                       "Triethoxycaprylylsilane Aloe Barbadensis Leaf Niacin Tocopherol Camellia Sinensis Leaf (Green)",
                       "Titanium Dioxide Niacin Panthenol ***amino-peptide Tocopherol Camellia Sinensis Leaf (Green)",
                       "Triethoxycaprylylsilane Aloe Barbadensis Leaf Niacin Tocopherol Camellia Sinensis Leaf (Green)",
                       "magnesium nitrate/methylchloroisothiazolinone/magnesium chloride/methylisothiazolinone"
                       ]
notIngredients = ["ILN49183 Limited Edition Glow Eyeshadow Palette: unavailable Limited Edition Lipstick in Red Ribbon/Sneak Peek: unavailable Limited Edition Lip Gloss in Dazzle Me: unavailable Limited Edition Multi-Use Blush Stick in Rose Gold: unavailable Re-Nutriv Intensive Smoothing H",
                  "Palette - Chantilly - Brûlée - Pecan - Rose Bud - Warm Ginger - Cognac - Amaretto - Black Currant - Soft Pearl - Iced Rose - Begonia - C",
                  "9 Beyond", "1) / dusty rose matte (5) / chestnut brown",
                  "782573/48 exfoliate", "Additive)", "Allergen)"
                  ]
ingredientsOnly.loc[ingredientsOnly.name1.isin(multipleIngredients), "multipleIngredients"] = True
ingredientsOnly.loc[ingredientsOnly.name1 == "fuzzy haze (Talc)", "name2"] = "Talc"
ingredientsOnly.loc[ingredientsOnly.name1 == "C13-15 alkane (hemisqualane)", "name2"] = "hemisqualane"
ingredientsOnly.loc[ingredientsOnly.name1 == "vitamin D (calciferol)", "name2"] = "calciferol"
ingredientsOnly.loc[ingredientsOnly.name1 == "Palmitamide MEA (Sweet", "name2"] = "Palmitamide MEA"
ingredientsOnly.loc[ingredientsOnly.name1.str.contains(r"\)$", regex=True) & ~ingredientsOnly.name1.str.contains(r"\(", regex=True), "name2"] = ingredientsOnly.name2.str.rstrip(")")
ingredientsOnly.loc[ingredientsOnly.name1.str.contains(r"^\(", regex=True), "name2"] = ingredientsOnly.name2.str.lstrip("(")
ingredientsOnly.loc[ingredientsOnly.name1.str.contains(r"^\).+?\($", regex=True), "name2"] = ingredientsOnly.name2.str.strip("()")
ingredientsOnly.loc[ingredientsOnly.name1.str.contains(r"^\)", regex=True), "name2"] = ingredientsOnly.name2.str.strip("()")
ingredientsOnly.loc[ingredientsOnly.name1.str.contains(r"\($", regex=True), "name2"] = ingredientsOnly.name2.str.strip("()")
ingredientsOnly["name2"] = ingredientsOnly.name2.str.strip()
ingredientsOnly.loc[ingredientsOnly.name1 == "Triethanolamine **potential allergen", "name2"] = "Triethanolamine"
ingredientsOnly.loc[ingredientsOnly.name1 == "Cyclohexasiloxane *certified", "name2"] = "Cyclohexasiloxane"
ingredientsOnly.loc[ingredientsOnly.name1.str.contains(r"^\*CO ", regex=True), "name2"] = ingredientsOnly.name2.str.replace("^\*CO ", "", regex=True)
ingredientsOnly = ingredientsOnly.loc[~ingredientsOnly.name2.str.contains(r"^80(-CHI|\d{4} Essential Oils$)")]
ingredientsOnly.loc[ingredientsOnly.name1.str.contains(r"^([02356789]\d|1[0123789]).+?: "), "name2"] = ingredientsOnly.name2.str.replace(r"^\d{2}.+?: ", "", regex=True)
ingredientsOnly.loc[ingredientsOnly.name1 == "2029705 eye pencil iron oxides (CI 77499)", "name2"] = "CI 77499"
ingredientsOnly = ingredientsOnly.loc[~ingredientsOnly.name2.str.contains(r"^(2\d{4}|385|4[135])")]
ingredientsOnly.loc[ingredientsOnly.name1.str.contains(r"^#1\d.+?: "), "name2"] = ingredientsOnly.name2.str.replace(r"^#1\d.+?: ", "", regex=True)
ingredientsOnly.loc[ingredientsOnly.name1.str.contains(r"^1[45]\d+? CI", regex=True), "name2"] = ingredientsOnly.name2.str.replace("^1[45]\d+? ", "", regex=True)
ingredientsOnly.loc[ingredientsOnly.name1.str.contains(r"\(Cosmetic Colorant\)?$", regex=True), "name2"] = ingredientsOnly.name2.str.replace(r"\(Cosmetic Colorant\)?$", "", regex=True)
ingredientsOnly["name2"] = ingredientsOnly.name2.str.strip()
ingredientsOnly.loc[ingredientsOnly.name1.str.contains(r"^1[456].+?: ") & ~((ingredientsOnly.name1 == "149174 *all shades (CI 75470 (Cosmetic Colorant)) pink champagne: Mica") | ingredientsOnly.name1.str.contains(r"16339\d CI")), "name2"] = ingredientsOnly.name2.str.replace(r"^1[456].+?: ", "", regex=True)
ingredientsOnly = ingredientsOnly.loc[~ingredientsOnly.name2.str.contains(r"^18\d{2}")]
ingredientsOnly.loc[ingredientsOnly.name1.str.contains(r"^: ", regex=True), "name2"] = ingredientsOnly.name2.str.replace("^: ", "", regex=True)
ingredientsOnly.loc[ingredientsOnly.name1.str.contains(r"^<ILN.+?>.+: ", regex=True) & ~ingredientsOnly.name1.str.contains("CI \d{5}", regex=True), "name2"] = ingredientsOnly.name2.str.replace(r"^<ILN.+?>.+: ", "", regex=True)
ingredientsOnly.loc[ingredientsOnly.name1.str.contains(r"^ASABU.+?: "), "name2"] = ingredientsOnly.name2.str.replace(r"^ASABU.+?: ", "", regex=True)
ingredientsOnly = ingredientsOnly.loc[~ingredientsOnly.name1.str.contains(r"^A[FPSWY]") & (ingredientsOnly.name1 != "<iln:bj014002a?")]
ingredientsOnly = ingredientsOnly.loc[~ingredientsOnly.name1.str.contains(r"^0\d")]
ingredientsOnly.loc[ingredientsOnly.name1.str.contains(r"^0E111.+?: ", regex=True), "name2"] = ingredientsOnly.name2.str.replace(r"^0E111.+?: ", "", regex=True)
ingredientsOnly.loc[ingredientsOnly.name1.str.contains(r"^1 \(", regex=True), "name2"] = ingredientsOnly.name2.str.replace(r"^1 \(", "", regex=True)
ingredientsOnly.loc[ingredientsOnly.name1.str.contains(r"^/.+?: ", regex=True), "name2"] = ingredientsOnly.name2.str.replace(r"^/.+?: ", "", regex=True)
ingredientsOnly = ingredientsOnly.loc[~(ingredientsOnly.name1.str.contains(r"1\d{2}.+\*") & ~(ingredientsOnly.name1.str.contains("CI \d{5}")))]
ingredientsOnly.loc[ingredientsOnly.name1 == "1082536PR20) superfood treatment (Aqua", "name2"] = "Aqua"
ingredientsOnly.loc[ingredientsOnly.name1 == "110771 PT1 aqua/water", "name2"] = "aqua"
ingredientsOnly = ingredientsOnly.loc[~(ingredientsOnly.name1.str.contains(r"^1\d{2}") & ~ingredientsOnly.name1.str.contains(r"[Aa]qua|CI"))]
ingredientsOnly.loc[ingredientsOnly.name1.str.contains(r"^(\*|-or )"), "name2"] = ingredientsOnly.name2.str.replace(r"^(\*|-or )", "", regex=True)
ingredientsOnly.loc[ingredientsOnly.name1 == "2 (Paraffinum Liquidum (Liquid))", "name2"] = "Paraffinum Liquidum"
ingredientsOnly.loc[ingredientsOnly.name1.str.contains(r"^2 \(") & (ingredientsOnly.name2 != "Paraffinum Liquidum"), "name2"] = ingredientsOnly.name2.str.replace(r"^2 \(", "", regex=True)
ingredientsOnly.loc[ingredientsOnly.name1.str.contains(r"^[56] \("), "name2"] = ingredientsOnly.name2.str.replace(r"^[56] \(", "", regex=True)
ingredientsOnly.loc[ingredientsOnly.name2.str.contains(r"^4\d{5}.+?: "), "name2"] = ingredientsOnly.name2.str.replace(r"^4\d{5}.+?: ", "", regex=True)
ingredientsOnly.loc[ingredientsOnly.name2.str.contains(r"^B(\d|E).*?: "), "name2"] = ingredientsOnly.name2.str.replace(r"^B(\d|E).*?: ", "", regex=True)
ingredientsOnly = ingredientsOnly.loc[~ingredientsOnly.name2.str.contains(r"^B[ABFOSV]")]
ingredientsOnly.loc[ingredientsOnly.name2.str.contains(r"\*+[a-zA-Z]*$", regex=True), "name2"] = ingredientsOnly.name2.str.replace(r"\*[a-zA-Z]+$", "", regex=True)
ingredientsOnly.name2 = ingredientsOnly.name2.str.strip()
ingredientsOnly.loc[ingredientsOnly.name2 == "Acetamidoethyl PG-trimonium Chloride W", "name2"] = "Acetamidoethyl PG-trimonium Chloride"
ingredientsOnly = ingredientsOnly.loc[~ingredientsOnly.name2.isin(["Active", "Active Pharmaceutical Ingredients"])]

"""I'm going to identify ingredient names with words enclosed in parentheses"""
parenthesesRegex = r" \(\b\w+\b\)"
ingredientsParentheses = ingredientsOnly.loc[ingredientsOnly.name1.str.contains(parenthesesRegex, regex=True)]
ingredientsOnly["name2"] = ingredientsOnly.name2.str.replace(parenthesesRegex, "")

"""There are some 'ingredient names' that mostly consist of numbers. I'll
remove these if they don't contain CI and so don't describe pigments"""
ingredientsWithNumbers = ingredientsOnly.loc[ingredientsOnly.name2.str.contains(r"\d")]
ingredientsWithNumbersList = ingredientsWithNumbers.name2.drop_duplicates().tolist()
notPigments = []
for ingredient in ingredientsWithNumbersList:
    totalCharacters = len(ingredient)
    totalDigits = sum(character.isdigit() for character in ingredient)
    digitsFraction = totalDigits/totalCharacters
    if (digitsFraction >= 0.5 or "F.I.L" in ingredient or "FIL" in ingredient) and "CI" not in ingredient and "Talc" not in ingredient:
        # Kinda weird that Talc is also in names with primarily digits. Let's keep Talc
        notPigments.append([ingredient, "Remove"])
notPigmentsDF = pd.DataFrame(notPigments, columns=["name2", "Remove"])
ingredientsOnly = (ingredientsOnly.merge(notPigmentsDF, "left", "name2")
                   .query("Remove != 'Remove'")
                   .drop(columns=["Remove"])
                   .query("name1 != @notIngredients")
                   )

ingredientsOnly = ingredientsOnly.query("name2 != ''")
ingredientsOnly["cleanNameLength"] = ingredientsOnly.name2.str.len()
ingredientsOnly = ingredientsOnly.sort_values(["cleanNameLength", "ogNameLength", "name2"], ascending=[False, False, True], ignore_index=True)
"""Ok, at this point, I can't spend more time manually editing delimiters to
more cleanly split ingredients. This is way too time-consuming now. I'll just
stop manually editing delimiters like this"""
# %%
"""Extracting the targeted ingredients. This is to ensure that the targeted
ingredients can be identified later on"""
targetedRegex = r"[Cc]yclo(methicone|(tetra|penta|hexa)siloxane)|[Pp]etrolatum|[Aa]mmonium [Tt]hioglycolate|(([Tt]r|[Dd])i)?[Ee]thanolamine|[MDT]EA|[Pp]olyquaternium[- ][34]?7(?!\d)|[Mm]ethacrylamidopropyltrimethylammonium [Cc]hloride|MAPTAC"
targetedIngredientsDF = ingredientsOnly.loc[ingredientsOnly.name2.str.contains(targetedRegex)]


cyclomethiconeDF = targetedIngredientsDF.loc[targetedIngredientsDF.name2.str.contains(r"[Cc]yclomethicone")]
cyclomethiconeDF["targetedIngredient"] = "Cyclomethicone"

cyclotetrasiloxaneDF = targetedIngredientsDF.loc[targetedIngredientsDF.name2.str.contains(r"[Cc]yclotetrasiloxane")]
cyclotetrasiloxaneDF["targetedIngredient"] = "Cyclotetrasiloxane"
cyclotetrasiloxaneDF = cyclotetrasiloxaneDF.query("name2 != 'Trifluoropropyl Cyclotetrasiloxane'")

cyclopentasiloxaneDF = targetedIngredientsDF.loc[targetedIngredientsDF.name2.str.contains(r"[Cc]yclopentasiloxane")]
cyclopentasiloxaneDF["targetedIngredient"] = "Cyclopentasiloxane"
cyclopentasiloxaneDF = cyclopentasiloxaneDF.query("name2 != 'Trifluoropropyl Cyclopentasiloxane'")

cyclohexasiloxaneDF = targetedIngredientsDF.loc[targetedIngredientsDF.name2.str.contains(r"[Cc]yclohexasiloxane")]
cyclohexasiloxaneDF["targetedIngredient"] = "Cyclohexasiloxane"

petrolatumDF = targetedIngredientsDF.loc[targetedIngredientsDF.name2.str.contains(r"[Pp]etrolatum")]
petrolatumDF["targetedIngredient"] = "Petrolatum"
petrolatumDF["name2"] = "Petrolatum"

ammoniumThioglycolateDF = targetedIngredientsDF.loc[targetedIngredientsDF.name2.str.contains(r"[Aa]mmonium [Tt]hioglycolate")]
ammoniumThioglycolateDF["targetedIngredient"] = "Ammonium Thioglycolate"

ethanolamineDF = targetedIngredientsDF.loc[targetedIngredientsDF.name2.str.contains(r"(?<!\w)[Ee]thanolamine|MEA")]
ethanolamineDF["targetedIngredient"] = "Ethanolamine"
"""It seems like the ingredient names that contain 'MEA' and 'amide' have
ethanolamine as a component that's covalently bonded to form an amide rather
than having ethanolamine as its standalone substance. I'm going to remove
ingredients with 'MEA' and 'amide', then.

I'm also going to scrap 'Disodium Oleamido MEA-sulfosuccinate', 'Dimethyl MEA',
and 'acemide MEA' (which is likely a mispelling of 'acetamide MEA'), and
'MEA-borate' for the same reason as above
"""
ethanolamineDF = ethanolamineDF.loc[~(ethanolamineDF.name2.str.contains(r"MEA") & ethanolamineDF.name2.str.contains(r"amide"))]
ethanolamineDF = ethanolamineDF.loc[~ethanolamineDF.name2.isin(["Disodium Oleamido MEA-sulfosuccinate", "Dimethyl MEA", "acemide MEA", "MEA-borate"])]

diethanolamineDF = targetedIngredientsDF.loc[targetedIngredientsDF.name2.str.contains(r"[Dd]iethanolamine|DEA")]
diethanolamineDF["targetedIngredient"] = "Diethanolamine"
"""And the same thing seems to be true with ethanolamine, where there are
ingredient names that contain both 'amide' and 'DEA' and they seem to use DEA
as part of an amide rather than having DEA as its own standalone molecule.
Going to remove ingredients with 'DEA' and 'amide' as well"""
diethanolamineDF = diethanolamineDF.loc[~(diethanolamineDF.name2.str.contains(r"DEA") & diethanolamineDF.name2.str.contains(r"amide"))]

triethanolamineDF = targetedIngredientsDF.loc[targetedIngredientsDF.name2.str.contains(r"[Tt]riethanolamine|TEA")]
triethanolamineDF["targetedIngredient"] = "Triethanolamine"

polyquat7DF = targetedIngredientsDF.loc[targetedIngredientsDF.name2.str.contains(r"[Pp]olyquaternium[- ]7(?!\d)")]
polyquat7DF["targetedIngredient"] = "Polyquaternium-7"

polyquat37DF = targetedIngredientsDF.loc[targetedIngredientsDF.name2.str.contains(r"[Pp]olyquaternium[- ]37")]
polyquat37DF["targetedIngredient"] = "Polyquaternium-37"

polyquat47DF = targetedIngredientsDF.loc[targetedIngredientsDF.name2.str.contains(r"[Pp]olyquaternium[- ]47")]
polyquat47DF["targetedIngredient"] = "Polyquaternium-47"

maptacDF = targetedIngredientsDF.loc[targetedIngredientsDF.name2.str.contains(r"[Mm]ethacrylamidopropyltrimethylammonium|MAPTAC")]
maptacDF["targetedIngredient"] = "Methacrylamidopropyltrimethylammonium Chloride"
"""Huh. So MAPTAC isn't found in Beauty & Personal Care products on Mintel at
all. I repeated a search with just MAPTAC on Mintel for this date range and
the search, again, revealed no products."""
dfsConcat = [cyclomethiconeDF, cyclotetrasiloxaneDF, cyclopentasiloxaneDF,
             cyclohexasiloxaneDF, petrolatumDF, ammoniumThioglycolateDF,
             ethanolamineDF, diethanolamineDF, triethanolamineDF, polyquat7DF,
             polyquat37DF, polyquat47DF]
targetedIngredientsDF = pd.concat(dfsConcat, ignore_index=True)

# Creating a dataframe of product - targeted ingredient combinations
productTarget = (ingredientProduct.merge(splitDF, "left", "ingredientList")
                 .merge(targetedIngredientsDF, "inner", "name1")
                 .filter(["productID", "ingredientOrder", "name2", "targetedIngredient"])
                 .drop_duplicates()
                 )
# %%
"""I'm going to export the following dataframes
- dataframe with product ID, original ingredient list, product category &
subcategory, bar code, product name, product variant, brand, company, ultimate
company, date published
- original ingredient list, clean ingredient list
- clean ingredient list, name1, name2, ingredient order of name1
- separated & cleaned ingredients
- the targeted ingredients, fields are clean ingredient name, targeted
ingredient
- product & targeted ingredients, fields are product ID, bar code, product
category & subcategory, clean ingredient name, targeted ingredient

"""
ingredientsOnly2 = (pd.concat([ingredientsOnly, targetedIngredientsDF])
                    .filter(["name1", "name2"])
                    .drop_duplicates()
                    )
originalColumnsKeep = ["Record ID", "Product", "Product Variant", "Brand",
                       "Company", "Ultimate Company", "Bar Code",
                       "Ingredients (Standard form)", "Date Published"]
originalColumnsRename = {"Ingredients (Standard form)": "originalIngredientList",
                         "Bar Code": "barCode", "Record ID": "productID",
                         "Product Variant": "productVariant",
                         "Date Published": "datePublished"}
narrowedOriginal = (original.filter(originalColumnsKeep)
                    .rename(columns=originalColumnsRename)
                    )
newOriginalColumns = narrowedOriginal.columns.tolist()
duplicatedEntries = narrowedOriginal.loc[narrowedOriginal.productID.duplicated(), "productID"].drop_duplicates().tolist()
numberDuplicatedEntriesList = []
for duplicated in duplicatedEntries:
    filteredDataframe = narrowedOriginal.loc[narrowedOriginal.productID == duplicated]
    numberDuplicatedEntries = filteredDataframe.shape[0]
    for column in newOriginalColumns:
        if (filteredDataframe[column].isna().empty == False) and (numberDuplicatedEntries == 2):
            notEmptyValue = filteredDataframe.loc[filteredDataframe[column].notna(), column].drop_duplicates().tolist()[0]
            narrowedOriginal.loc[narrowedOriginal.productID == duplicated, column] = notEmptyValue
        elif numberDuplicatedEntries != 2:
            numberDuplicatedEntriesList.append(numberDuplicatedEntries)
    
narrowedOriginal = narrowedOriginal.drop_duplicates(ignore_index=True)

ingredientListConverter = ingredientProduct.filter(["originalIngredientList", "ingredientList"])
splitDF2 = (splitDF.merge(ingredientsOnly2, "inner", "name1")
            .drop_duplicates()
            )
ingredientNames = (ingredientsOnly2.filter(["name2"])
                   .drop_duplicates()
                   )
targetedIngredientsDF2 = (targetedIngredientsDF.filter(["name2"])
                          .drop_duplicates()
                          )
productTarget2 = (productTarget.merge(narrowedOriginal, "inner", "productID")
                  .drop(columns=["originalIngredientList"])
                  )

note = ["This is the processed data from some Mintel queries intended to",
        "analyze certain ingredients in personal care products. 3 separate",
        "queries were made: (1) one with all the targeted ingredients",
        "except for triethanolamine from January 2015 to nearly the end of,",
        "but not fully encompassing, December 2025; (2) one with all the",
        "targeted ingredients, except for triethanolamine, for December 2025;",
        "and (3) products with triethanolamine from January 2015 to December",
        "2025. For each query, products in the Mintel 'Super-Category' of ",
        "'Beauty & Personal Care' and with a 'Market' of 'USA' (likely",
        "indicating that the product was bought from a brick-and-mortar store",
        "in the US) were selected. For the first 2 queries, the following",
        "ingredients were searched",
        "Ingredient Search matches one or more of [Cyclomethicone; Cyclotetrasiloxane; Cyclomethicone; Cyclopentasiloxane; Cyclohexasiloxane; Cyclomethicone; Petrolatum; Ammonium Thioglycolate; Diethanolamine; Ethanolamine; Ethanolamine; Polyquaternium-7; Polyquaternium-37; Polyquaternium-47; Methacrylamidopropyltrimethylammonium Chloride; Methacrylamidopropyltrimethylammonium Chloride] as the Ingredients",
        "",
        "Note how many ingredient names appear duplicated. The common name",
        "'D4' is another synonym for Cyclotetrasiloxane, and this common name",
        "also appeared in the same string with Cyclomethicone when I chose",
        "ingredients for filtering in the Mintel interface. Cyclomethicone",
        "also appeared by itself. Hence, this is why you see 'Cyclomethicone'",
        "appear multiple times in the ingredient filter. Ethanolamine also",
        "appeared twice because I searched for 'Ethanolamine' by itself as a",
        "string and then I searched for 'MEA', and 'MEA' also appeared with",
        "'Ethanolamine' in the same string.",
        ""
        "For the 3rd query, the ingredient names searched were the following",
        "Ingredient Search matches one or more of [Triethanolamine; Triethanolamine] as the Ingredients",
        ""
        "Again, you see that 'Triethanolamine' appeared twice. While filtering",
        "for this ingredient in the Mintel interface, I first searched for",
        "'Triethanolamine', and then I searched for 'TEA'. 'Triethanolamine'",
        "appeared by itself but it also appeared in the same string with 'TEA',",
        "resulting in 'Triethanolamine' appearing twice here.",
        "",
        "I combined the 3 downloads into a single table and then processed the",
        "ingredient lists. The processing was done in 3 steps: (1) cleaning",
        "ingredient lists of various textual artifacts that can mess with",
        "clean separation of ingredients, such as 'active ingredient',",
        "'inactive ingredient', product names present within an ingredient",
        "list, and certain pairs of ingredients that are separated by text",
        "other than a simple comma and space; (2) separating the cleaned",
        "ingredient lists; (3) cleaning the separated names. Ingredient lists",
        "from the Mintel downloads were either 'on pack' (how they were written",
        "on the product packaging) or 'standard form' (converted to more",
        "standardized names used by other products in Mintel). I processed only",
        "the standardized ingredient lists. After subjecting the standardized",
        "ingredient lists through the 1st step, this created 2 kinds of",
        "ingredient lists, an 'originalIngredientList' that was the original",
        "standardized ingredient list as downloaded from Mintel and a field",
        "called 'ingredientList' which is the ingredient list after going",
        "through step 1. This cleaned ingredient list is then separated in",
        "step 2 into individual ingredient names, and these ingredient names",
        "are called 'name1'. Many of these names still had various textual",
        "artifacts, so I then cleaned them in step 3, producing cleaner names",
        "that I call 'name2'. I have tried my best to clean the ingredient",
        "lists and names, but many of them likely still contain artifacts that",
        "would prevent them from being identified on CompTox or other",
        "chemical databases."]
readMe = pd.DataFrame({"Note": note})
outputPath = dataFolder/"Output"/"Processed Mintel downloads.xlsx"
if os.path.exists(outputPath) is False:
    with pd.ExcelWriter(outputPath) as w:
        readMe.to_excel(w, "ReadMe", index=False)
        narrowedOriginal.to_excel(w, "Original data", index=False)
        ingredientListConverter.to_excel(w, "Cleaning ingredient lists", index=False)
        splitDF2.to_excel(w, "Separating ingredient lists", index=False)
        ingredientsOnly2.to_excel(w, "Cleaning ingredient names", index=False)
        ingredientNames.to_excel(w, "Cleaned names", index=False)
        productTarget2.to_excel(w, "Product - target", index=False)
        targetedIngredientsDF2.to_excel(w, "Targeted ingredients", index=False)
