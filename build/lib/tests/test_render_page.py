import re
from taxon2wikipedia.render_page import run_pipeline_for_wikipage


# Test if Wikipage is a string


def test_wikipage_in_portuguese():
    wiki_page = run_pipeline_for_wikipage("Q15514411", "pt")

    expected_page = """
{{Título em itálico}}
{{Info/Taxonomia
| imagem                = 
| reino                 = [[Plantae]]
| divisão               = [[Tracheophytes]]
| ordem                 = [[Poales]]
| família               = [[Poaceae]]
| infrarreino           = [[Streptophyta]]
| superdivisão          = [[Embryophytes]]
| subfilo               = [[Euphyllophyta]]
| superdomínio          = [[Biota]]
| género                = [[Cutandia]]
| superdomínio          = [[Cytota]]
| subdomínio            = [[Diaphoretickes]]
| subreino              = [[Viridiplantae]]
| espécie               = [[Cutandia divaricata]]
}}
'''''Cutandia divaricata''''' é uma espécie de planta  da família [[Poaceae]] e do gênero ''[[Cutandia]]''.  <ref name=":ref_0"> {{Citar web|url=https://www.gbif.org/species/4140116|titulo=Cutandia divaricata|acessodata=2022-04-18|website=www.gbif.org|lingua=en}}</ref>
== Taxonomia ==
O táxon foi descrito oficialmente em [[1881]] por [[George Bentham]]. <ref name=":ref_0"/>
A espécie havia sido descrita anteriormente sob o [[basiônimo]] '''''Festuca divaricata''''' (gênero ''[[Festuca]]'') em 1798 por [[René Louiche Desfontaines]]. 
{{Referencias}}
== Ligações externas ==
* [https://www.ipni.org/n/396840-1 ''Cutandia divaricata'' no Índice Internacional de Nomes de Plantas.]
* [https://www.biodiversitylibrary.org/name/Cutandia%20divaricata Documentos sobre ''Cutandia divaricata'' na Biodiversity Heritage Library]
* [https://www.inaturalist.org/taxa/1159197 Observações de ''Cutandia divaricata'' no iNaturalist]
* [https://www.gbif.org/species/4140116 ''Cutandia divaricata'' no GBIF]
   
=== Links externos para sinônimos ===
* [https://www.biodiversitylibrary.org/name/Festuca%20divaricata Documentos sobre ''Festuca divaricata'' na Biodiversity Heritage Library]


{{Controle de autoridade}}
{{esboço-biologia}}
[[Categoria:Cutandia]][[Categoria:Espécies descritas em 1881]]"""

    assert wiki_page == expected_page


def test_wikipage_in_spanish():
    wiki_page = run_pipeline_for_wikipage("Q15514411", "es")

    expected_page = """
{{Ficha de taxón
| imagem                = 
| regnum                 = [[Plantae]]
| unranked_divisio           = [[Spermatophytes]]
| divisio              = [[Tracheophytes]]
| ordo                 = [[Poales]]
| familia               = [[Poaceae]]
| subregnum           = [[Streptophyta]]
| superdivisio         = [[Embryophytes]]
| subphylum               = [[Euphyllophyta]]
| superregnum          = [[Biota]]
| genus                = [[Cutandia]]
| superregnum          = [[Cytota]]
| subregnum            = [[Diaphoretickes]]
| subregnum              = [[Viridiplantae]]
| species               = [[Cutandia divaricata]]
}}
'''''Cutandia divaricata''''' es una especie de planta de la familia [[Poaceae]] y del género ''[[Cutandia]]''.  <ref name=":ref_0"> {{Citar web|url=https://www.gbif.org/species/4140116|título=Cutandia divaricata|fechaacceso=2022-04-18|sitioweb=www.gbif.org}}</ref>
== Taxonomía ==
El taxón fue descrito oficialmente en [[1881]] por [[George Bentham]]. <ref name=":ref_0"/>
La especie había sido descrita anteriormente bajo el [[basónimo]] '''''Festuca divaricata''''' (género ''[[Festuca]]'') en 1798 por [[René Louiche Desfontaines]]. 
==Referencias==
{{listaref}}
== Enlaces externos ==
* [https://www.ipni.org/n/396840-1 ''Cutandia divaricata'' en el Índice Internacional de Nombres de Plantas.]
* [https://www.biodiversitylibrary.org/name/Cutandia%20divaricata Documentos sobre ''Cutandia divaricata'' en la Biodiversity Heritage Library]
* [https://www.inaturalist.org/taxa/1159197 Observaciones de ''Cutandia divaricata'' en iNaturalist]
* [https://www.gbif.org/species/4140116 ''Cutandia divaricata'' en GBIF]
   
=== Enlaces externos para sinónimos ===
* [https://www.biodiversitylibrary.org/name/Festuca%20divaricata Documentos sobre ''Festuca divaricata'' en la Biodiversity Heritage Library]


{{Control de autoridad}}
[[Categoría:Cutandia]][[Categoría:Especies descritas en 1881]]"""

    assert wiki_page == expected_page
