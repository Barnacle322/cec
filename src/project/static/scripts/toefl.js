document.getElementById("date").addEventListener("blur", checkDate);

function checkDate() {
    var date = document.getElementById("date").value;
    if (date === "") {
        return;
    }
    fetch(`/admin/toefl/check/${date}`)
        .then((response) => response.text())
        .then((data) => {
            console.log(data.toString() == "1");
            if (data == "1") {
                alert("На эту дату уже есть резултаты! Повторное добавление удаляет старые результаты.");
                return;
            }
        });
}
