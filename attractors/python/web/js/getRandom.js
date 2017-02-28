function getRandomBound() {
	var startDate = new Date(2016, 06, 27) // July ! January is 0
	var currentDate = new Date()
	var dateDayDiff = Math.floor((currentDate - startDate)/(60*60*24*1000))+1
	return dateDayDiff
}

function loadRandomPage() {
	var d = Math.floor(Math.random()*window.b)+1
	var page = d + ".xhtml"
	window.open("http://172.28.195.117/attractors/" + page, "_self")
}

var b = getRandomBound()
