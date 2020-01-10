var addressRoot = location.protocol+'//'+location.hostname+'/attractors/'

function getLastAttractorNum() {
	var startDate = new Date(2016, 06, 27) // July ! January is 0
	var currentDate = new Date()
	var dateDayDiff = Math.floor((currentDate - startDate)/(60*60*24*1000))+1
	return dateDayDiff
}

function loadDifferentRandomPage(fname) {
	do {
		var d = Math.floor(Math.random()*window.b)+1
		var page = d + ".xhtml"
	} while (page === fname);
	window.open(addressRoot + page, "_self")
}

function loadDifferentRandomMonth(fname) {
	do {
		var d = Math.floor(Math.random()*window.b)+1
		var dDate = new Date(2016, 06, 27)
		dDate.setDate(dDate.getDate() + d)
		var df
		var dd = dDate.getMonth()+1
		if (dd < 10) {
			df = "0" + dd
		}
		else {
			df = "" + dd
		}
		var page = "" + dDate.getFullYear() + df + ".xhtml"
	} while (page === fname);
	window.open(addressRoot + page, "_self")
}

function loadRandomMonth() {
	loadDifferentRandomMonth(window.currentPage[0])
}

function loadRandomPage() {
	loadDifferentRandomPage(window.currentPage[0])
}

function loadPreviousPage() {
	if (window.currentAttractorNum === 1) {
		return true
	}
	var prevAttractorNum = window.currentAttractorNum - 1
	window.open(addressRoot + prevAttractorNum + ".xhtml", "_self")
}

function loadNextPage() {
        if (window.currentAttractorNum === b) {
                return true
        }
        var nextAttractorNum = window.currentAttractorNum + 1
        window.open(addressRoot+ nextAttractorNum + ".xhtml", "_self")
}

var b = getLastAttractorNum()
var currentPage = location.pathname.split("/").slice(-1)
var currentAttractorNum = parseInt(window.currentPage[0].replace(".xhtml", ""))
if (isNaN(currentAttractorNum)) { // Fallback on latest attractor number
	currentAttractorNum = b
}
