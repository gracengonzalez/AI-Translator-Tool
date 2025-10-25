function getValue() {
    const inputElement = document.getElementById("sentence");
    const inputValue = inputElement.value;
    document.getElementById("output").innerText = "Input value: " + inputValue;
}

const goButton = document.getElementById("go");
goButton.addEventListener("click", () => {
    getValue();
})