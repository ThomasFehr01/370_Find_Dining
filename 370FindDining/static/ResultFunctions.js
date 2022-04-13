/**
 * Displays the appropriate number of dollar signs
 * @param rating: The number of dollar signs to be displayed
 */
function dollarSignMaker(rating){
    var result = "";

    if (rating >= 0 && rating <= 4) {
        for(var i = 1; i <= rating; i++)
        {
            result += "$";
        }
    }
    return result;
}


/**
 * Displays the appropriate number of stars
 * @param numStars: the star rating of the restaurant
 */
function starCount(numStars) {
    resetStars();

    var fullStars = Math.floor(numStars);
    var decimal = numStars % 1;

    // count stars added for testing purposes
    var starsAdded = 0;

    // display full stars
    if (fullStars >= 1 && fullStars <= 5) {
        for (var i = 0; i < stars.length; i++) {
            if (i < fullStars) {
                // Changes display from "none" to "inline"
                stars[i].style.display = "inline";
                starsAdded++;
            }
        }
    }

    // display half star
    if (decimal >= 0.5) {
        stars[5].style.display = "inline";
        starsAdded += 0.5;
    }

    return starsAdded;
}


/**
 * Set the visible stars back to zero
 */
function resetStars() {
    for (var i = 0; i < stars.length; i++) {
        stars[i].style.display = "none";
    }
    // reset the half-star display to none
    stars[5]. style.display = "none";
}