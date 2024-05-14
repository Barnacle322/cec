let initialPositions = {};
let positions = {};

let courseIds = Array.from(document.querySelectorAll("[id^='timetables-list-']")).map((el) => el.id.split("-")[2]);

courseIds.forEach((courseId) => {
    let timetables_list = document.getElementById(`timetables-list-${courseId}`);
    let submitButton = document.getElementById(`submitButton-${courseId}`);

    initialPositions[courseId] = getPositions(courseId);
    submitButton.disabled = true;
    submitButton.classList.add("hidden");

    new Sortable(timetables_list, {
        handle: ".handle",
        animation: 150,
        ghostClass: "sortable-ghost",
        onEnd: function (evt) {
            positions[courseId] = getPositions(courseId);
            if (JSON.stringify(positions[courseId]) == JSON.stringify(initialPositions[courseId])) {
                submitButton.disabled = true;
                submitButton.classList.add("hidden");
            } else {
                submitButton.disabled = false;
                submitButton.classList.remove("hidden");
            }
        },
    });
});

function getPositions(courseId) {
    let timetables_list = document.getElementById(`timetables-list-${courseId}`);
    return Array.from(timetables_list.querySelectorAll(".timetable-item")).map((timetable, index) => {
        return {
            id: timetable.dataset.id,
            position: index + 1,
        };
    });
}

function submitPositions(courseId) {
    if (positions[courseId].length === 0) {
        console.log("No changes detected");
        return;
    }
    fetch(`/admin/courses/${courseId}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(positions[courseId]),
    })
        .then(() => {
            initialPositions[courseId] = positions[courseId];
            positions[courseId] = [];
            document.getElementById(`submitButton-${courseId}`).disabled = true;
            document.getElementById(`submitButton-${courseId}`).classList.add("hidden");
        })
        .catch((error) => {
            console.error("Error:", error);
        });
}

window.addEventListener("load", function () {
    var selectedCourseGroup = localStorage.getItem("selectedCourseGroup");
    var selectedCourse = localStorage.getItem("selectedCourse");

    if (selectedCourseGroup) {
        setCourseGroupState(selectedCourseGroup);
    }
    if (selectedCourse) {
        setCourseState(selectedCourse);
    }
});

function setCourseGroupState(id) {
    var courseGroups = document.querySelectorAll(".course-group");

    courseGroups.forEach(function (courseGroup) {
        var isGroupSelected = id !== null && courseGroup.id === id;
        courseGroup.style.display = isGroupSelected ? "block" : "none";

        var closeArrow = document.querySelector("#closeArrow-" + courseGroup.id);
        var openArrow = document.querySelector("#openArrow-" + courseGroup.id);

        if (closeArrow && openArrow) {
            closeArrow.style.display = isGroupSelected ? "none" : "block";
            openArrow.style.display = isGroupSelected ? "block" : "none";
        }
    });
}

function setCourseState(id) {
    var courses = document.querySelectorAll(".course");

    courses.forEach(function (course) {
        var isCourseSelected = id !== null && course.id === id;
        course.style.display = isCourseSelected ? "block" : "none";

        var closeArrow = document.querySelector("#closeArrowCourse-" + course.id);
        var openArrow = document.querySelector("#openArrowCourse-" + course.id);

        if (closeArrow && openArrow) {
            closeArrow.style.display = isCourseSelected ? "none" : "block";
            openArrow.style.display = isCourseSelected ? "block" : "none";
        }
    });
}

function toggleCourseGroup(id) {
    var currentSelectedCourseGroup = localStorage.getItem("selectedCourseGroup");
    var newSelectedCourseGroup = currentSelectedCourseGroup === id ? null : id;

    localStorage.setItem("selectedCourseGroup", newSelectedCourseGroup);
    setCourseGroupState(newSelectedCourseGroup);
}

function toggleCourse(id) {
    var currentSelectedCourse = localStorage.getItem("selectedCourse");
    var newSelectedCourse = currentSelectedCourse === id ? null : id;

    localStorage.setItem("selectedCourse", newSelectedCourse);
    setCourseState(newSelectedCourse);
}
