# Lookback window

Er bestaan geen vaste richtlijnen om een optimale lengte van de lookback window te bepalen. In de literatuur wordt benadrukt dat er geen *one-size-fits-all*-benadering is en dat de keuze voor een lookback window afhankelijk is van de onderzoeksvraag en context. [Benchimol et al. (2025)](https://academic.oup.com/epirev/advance-article-abstract/doi/10.1093/epirev/mxaf019/8416313?login=false)

Een te korte lookback window kan ertoe leiden dat relevante zorgcontacten voor de zorg niet worden meegenomen, terwijl een te lange window kan leiden tot het meenemen van minder relevante of losstaande zorgcontacten — zoals huisartsbezoeken — wat ruis kan geven in de instroomgegevens.

Op basis hiervan is gekozen voor een lookback window van 100 dagen. Deze keuze sluit aan bij eerdere verkennende analyses door de NZA in de ouderenzorg, waaronder de [Monitor Ouderenzorg](https://puc.overheid.nl/nza/doc/PUC_709708_22/1/) en een [verkenningsrapport voor de Eerste Kamer](https://www.eerstekamer.nl/nonav/overig/20230317/nza_rapport_verkenning_in_en/document), waarin een window van 100 dagen wordt gehanteerd. Hoewel deze keuze niet inhoudelijk is onderbouwd in deze bronnen, biedt dit wel een praktische basis voor vergelijkbaarheid van resultaten.

> De lookback window is instelbaar via de parameter `P100D` in de SPARQL query.
