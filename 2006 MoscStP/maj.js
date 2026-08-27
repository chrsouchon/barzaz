function maj()
		{
mois = new Array("01", "02", "03", "04", "05", "06", "07", "08", "09",
			"10", "11", "12")
var maj = new Date(document.lastModified)
var bla = "Stad diweza"
var nav = navigator.appName.substring(0,2)
var lang = "br"
if (nav == "Mi") 
{lang = clientInformation.userLanguage.substring(0,2)}
else
{lang = navigator.language.substring(0,2)};
if (lang == "en") {bla = "Last Updated"}
else
if (lang == "fr") {bla = "Dernière MAJ"}
else
if (lang == "de") {bla = "Zuletzt geaendert"};

document.write("<font size=0>" + bla + " : " +
		maj.getDate() + "." +
		mois[maj.getMonth()] + "." +
		maj.getFullYear() + "<P>");
		}
