// Applications Management Script
class ApplicationsManager {
    constructor() {
        this.selectedItems = new Set();
        this.activeCourseFilters = new Set();
        this.init();
    }

    init() {
        this.setupSearch();
        this.setupBulkActions();
        this.setupCourseFilters();
        this.setupArchiveOld();
        this.updateStats();
    }

    // Search functionality
    setupSearch() {
        const searchInputs = document.querySelectorAll("[data-search]");
        searchInputs.forEach((input) => {
            input.addEventListener("input", (e) => {
                const tableId = e.target.dataset.search;
                const searchTerm = e.target.value.toLowerCase();
                this.filterTable(tableId, searchTerm);
            });
        });
    }

    filterTable(tableId, searchTerm = "") {
        const table = document.getElementById(tableId);
        if (!table) return;

        const searchInput = document.querySelector(`[data-search="${tableId}"]`);
        if (searchInput && !searchTerm) {
            searchTerm = searchInput.value.toLowerCase();
        }

        const tbody = table.querySelector("tbody");
        const rows = tbody.querySelectorAll("tr");
        let visibleCount = 0;

        rows.forEach((row) => {
            const text = row.textContent.toLowerCase();
            const courseCell = row.querySelector("[data-course]");
            const course = courseCell ? courseCell.dataset.course : "";

            // Check search term match
            const matchesSearch = !searchTerm || text.includes(searchTerm);

            // Check course filter match (only for registration table)
            let matchesCourseFilter = true;
            if (tableId === "registration-table" && this.activeCourseFilters.size > 0) {
                matchesCourseFilter = false;
                const courseCategory = this.getCourseCategory(course);
                for (const activeFilter of this.activeCourseFilters) {
                    if (activeFilter === courseCategory) {
                        matchesCourseFilter = true;
                        break;
                    }
                }
            }

            if (matchesSearch && matchesCourseFilter) {
                row.style.display = "";
                visibleCount++;
            } else {
                row.style.display = "none";
            }
        });

        // Update count
        const countEl = document.getElementById(`${tableId}-count`);
        if (countEl) {
            countEl.textContent = visibleCount;
        }
    }

    // Map course names to categories
    getCourseCategory(courseName) {
        const upperCourse = courseName.toUpperCase();
        if (upperCourse.includes("АНГЛИЙСКИЙ") || upperCourse.includes("TOEFL") || upperCourse.includes("IELTS")) {
            return "Курсы Английского";
        }
        return courseName;
    }

    // Bulk actions
    setupBulkActions() {
        // Select all checkboxes
        const selectAllCheckboxes = document.querySelectorAll("[data-select-all]");
        selectAllCheckboxes.forEach((checkbox) => {
            checkbox.addEventListener("change", (e) => {
                const tableId = e.target.dataset.selectAll;
                this.selectAll(tableId, e.target.checked);
            });
        });

        // Individual checkboxes
        const itemCheckboxes = document.querySelectorAll("[data-item-id]");
        itemCheckboxes.forEach((checkbox) => {
            checkbox.addEventListener("change", (e) => {
                const id = e.target.dataset.itemId;
                const type = e.target.dataset.itemType;
                if (e.target.checked) {
                    this.selectedItems.add(`${type}-${id}`);
                } else {
                    this.selectedItems.delete(`${type}-${id}`);
                }
                this.updateBulkActionButtons();
            });
        });

        // Bulk action buttons
        const bulkButtons = document.querySelectorAll("[data-bulk-action]");
        bulkButtons.forEach((button) => {
            button.addEventListener("click", (e) => {
                const action = e.currentTarget.dataset.bulkAction;
                this.performBulkAction(action);
            });
        });
    }

    selectAll(tableId, checked) {
        const table = document.getElementById(tableId);
        if (!table) return;

        const checkboxes = table.querySelectorAll("[data-item-id]");
        checkboxes.forEach((checkbox) => {
            checkbox.checked = checked;
            const id = checkbox.dataset.itemId;
            const type = checkbox.dataset.itemType;
            if (checked) {
                this.selectedItems.add(`${type}-${id}`);
            } else {
                this.selectedItems.delete(`${type}-${id}`);
            }
        });
        this.updateBulkActionButtons();
    }

    updateBulkActionButtons() {
        const count = this.selectedItems.size;
        const bulkButtons = document.querySelectorAll("[data-bulk-action]");
        const selectedCount = document.getElementById("selected-count");

        if (selectedCount) {
            selectedCount.textContent = count;
        }

        bulkButtons.forEach((button) => {
            button.disabled = count === 0;
            button.classList.toggle("opacity-50", count === 0);
            button.classList.toggle("cursor-not-allowed", count === 0);
        });
    }

    async performBulkAction(action) {
        if (this.selectedItems.size === 0) return;

        const items = Array.from(this.selectedItems).map((item) => {
            const [type, id] = item.split("-");
            return { type, id };
        });

        if (!confirm(`Архивировать ${items.length} заявок?`)) {
            return;
        }

        try {
            const response = await fetch("/admin/applications/bulk_archive", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ items }),
            });

            const data = await response.json();

            if (data.success) {
                // Clear selection and uncheck all
                this.selectedItems.clear();
                document.querySelectorAll("[data-item-id]").forEach((cb) => (cb.checked = false));
                document.querySelectorAll("[data-select-all]").forEach((cb) => (cb.checked = false));
                this.updateBulkActionButtons();

                // Reload page to show updated data
                window.location.reload();
            } else {
                alert("Произошла ошибка при архивировании");
            }
        } catch (error) {
            console.error("Bulk action failed:", error);
            alert("Произошла ошибка при выполнении операции");
        }
    }

    // Toggle application status
    async toggleApplication(element, type, id, isBulk = false) {
        try {
            const response = await fetch(`/admin/applications/toggle_handle/${type}/${id}`, {
                method: "POST",
            });

            const data = await response.json();

            if (data.error) {
                console.error(data.error);
                if (!isBulk) {
                    alert("Ошибка: " + data.error);
                }
                return;
            }

            if (!isBulk && element) {
                const row = element.closest("tr");
                if (data.handled) {
                    row.classList.add("opacity-50", "transition-opacity");
                    element.textContent = "Вернуть";
                    element.classList.remove("bg-sky-500", "hover:bg-sky-400");
                    element.classList.add("bg-green-500", "hover:bg-green-400");
                } else {
                    row.classList.remove("opacity-50");
                    element.textContent = "Скрыть";
                    element.classList.remove("bg-green-500", "hover:bg-green-400");
                    element.classList.add("bg-sky-500", "hover:bg-sky-400");
                }

                // Update stats
                this.updateStats();
            }
        } catch (error) {
            console.error("Toggle failed:", error);
            if (!isBulk) {
                alert("Произошла ошибка при выполнении операции");
            }
        }
    }

    // Course filter pills
    setupCourseFilters() {
        // Extract unique courses from the table
        const table = document.getElementById("registration-table");
        if (!table) return;

        const courseCategories = new Set();
        const courseCells = table.querySelectorAll("[data-course]");
        courseCells.forEach((cell) => {
            const course = cell.dataset.course;
            if (course) {
                const category = this.getCourseCategory(course);
                courseCategories.add(category);
            }
        });

        // Generate filter pills
        const filterContainer = document.getElementById("course-filters");
        if (!filterContainer || courseCategories.size === 0) return;

        courseCategories.forEach((category) => {
            const pill = document.createElement("button");
            pill.className =
                "filter-pill rounded-full border-2 border-blue-300 bg-white px-4 py-2 text-sm font-medium text-blue-700 transition hover:bg-blue-50";
            pill.textContent = category;
            pill.dataset.course = category;

            pill.addEventListener("click", () => {
                this.toggleCourseFilter(category, pill);
            });

            filterContainer.appendChild(pill);
        });
    }

    toggleCourseFilter(course, pillElement) {
        if (this.activeCourseFilters.has(course)) {
            this.activeCourseFilters.delete(course);
            pillElement.classList.remove("bg-blue-500", "text-white", "border-blue-500");
            pillElement.classList.add("bg-white", "text-blue-700", "border-blue-300");
        } else {
            this.activeCourseFilters.add(course);
            pillElement.classList.remove("bg-white", "text-blue-700", "border-blue-300");
            pillElement.classList.add("bg-blue-500", "text-white", "border-blue-500");
        }

        this.filterTable("registration-table");
    }

    // Archive old applications
    setupArchiveOld() {
        const archiveButton = document.getElementById("archive-old-btn");
        if (!archiveButton) return;

        archiveButton.addEventListener("click", async () => {
            if (!confirm("Архивировать все заявки старше 30 дней?")) {
                return;
            }

            try {
                const response = await fetch("/admin/applications/archive_old", {
                    method: "POST",
                });

                const data = await response.json();

                if (data.success) {
                    alert(
                        `Архивировано заявок: ${data.archived_count}\nКурсы: ${data.registrations}, TOEFL: ${data.toefl}`,
                    );
                    window.location.reload();
                } else {
                    alert("Произошла ошибка при архивировании");
                }
            } catch (error) {
                console.error("Archive old failed:", error);
                alert("Произошла ошибка при выполнении операции");
            }
        });
    }

    // Update statistics
    updateStats() {
        const tables = ["registration-table", "toefl-table"];
        tables.forEach((tableId) => {
            const table = document.getElementById(tableId);
            if (!table) return;

            const visibleRows = Array.from(table.querySelectorAll("tbody tr")).filter(
                (row) => row.style.display !== "none",
            );

            const countEl = document.getElementById(`${tableId}-count`);
            if (countEl) {
                countEl.textContent = visibleRows.length;
            }
        });
    }
}

// Initialize when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
    window.appManager = new ApplicationsManager();
});

// Expose toggleApplication globally for inline onclick
function toggleApplication(element, type, id) {
    if (window.appManager) {
        window.appManager.toggleApplication(element, type, id);
    }
}
