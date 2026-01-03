function showPopup(status) {
    const popup = document.getElementById("votePopup");
    const title = document.getElementById("popupTitle");
    const message = document.getElementById("popupMessage");

    if (status === "success") {
        title.innerText = "Vote Casted Successfully ✔";
        message.innerText = "Thank you for participating in the election.";
    } else {
        title.innerText = "Vote Failed ❌";
        message.innerText = "Invalid details or vote already casted.";
    }

    popup.style.display = "flex";
}

function closePopup() {
    document.getElementById("votePopup").style.display = "none";
}
