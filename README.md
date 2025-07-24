# taxon2wikipedia

An automatic page builder for taxa on ptwiki. 

## Updates
 
 * 2024-11-15 --> Parsing of Reflora was discontinued for simplicity and maintenability. 

## Set up and CLI usage

Set up pywikibot as per [this tutorial](https://www.mediawiki.org/wiki/Manual:Pywikibot/Installation).

```
python3 ~/Apps/pywikibot/pwb.py ~/Apps/pywikibot/generate_user_files


```

Install the package 

```
pip install -e . 
```

Create a page for the new taxon given the Wikidata QID