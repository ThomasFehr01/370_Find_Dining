/**
 * Creates listener for the start page
 */
function windowListener() {
    window.addEventListener("pageshow", function (event) {
        var historyTraversal = event.persisted ||
            (typeof window.performance != "undefined" && window.performance.navigation.type === 2);
        if (historyTraversal) {
            // Handle page restore.
            window.location.reload();
        }
    });
}


/**
 * Get the user's current location
 */
function getLocation() {
    if (navigator.geolocation) {
        if (document.cookie.indexOf('userID=') === -1) {
            navigator.geolocation.getCurrentPosition(storePosition, handleErrors);
        }
    } else {
        //TODO: test this somehow
        document.getElementById("MainDisplay").style.display = "none";
        document.getElementById("LoadingDisplay").style.display = "none";
        document.getElementById("LocationErrorDisplay").style.display = "inline";
        document.getElementById("ErrorText").innerText = "We cannot access your location";
    }
}


/**
 * Stores the users position
 * @param position: the users position/location in latitude and longitude
 */
function storePosition(position){
    userLatitude = position.coords.latitude;
    userLongitude = position.coords.longitude;

    sendLocation(userLatitude, userLongitude);
}


/**
 * Handles the case when the user denies sharing location data
 * @param error: The error thrown
 */
function handleErrors(error){
    //TODO: Find a way to test this????
    document.getElementById("MainDisplay").style.display = "none";
    document.getElementById("LoadingDisplay").style.display = "none";
    document.getElementById("LocationErrorDisplay").style.display = "inline";
    switch (error.code) {
        case 1:
            document.getElementById("ErrorText").innerText = "You denied access to your location";
            break;
        case 2:
            document.getElementById("ErrorText").innerText = "Your location is unavailable";
            break;
        case 3:
            document.getElementById("ErrorText").innerText = "The search for your location timed-out";
            break;
        default:
            document.getElementById("ErrorText").innerText = "We are having trouble accessing your location";
            break;
    }
}


/**
 * Send the user location to the algorithm
 * @param lat: The user's latitude
 * @param long: The user's longitude
 */
function sendLocation(lat, long) {
    var http = new XMLHttpRequest();
    var url = '/location';
    http.open('POST', url, true);

    http.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');

    http.onreadystatechange = function()
    {
        if(http.readyState === 4 && http.status === 200)
        {
            console.log("ok");
        }
    };

    http.send("data="+JSON.stringify({ "latitude": lat, "longitude": long }));
}