const API_URL = "http://127.0.0.1:5000/api/dataset";

const datasetContainer = document.getElementById("datasetContainer");

const formContainer = document.getElementById("formContainer");

const addBtn = document.getElementById("addBtn");

const saveBtn = document.getElementById("saveBtn");

const cancelBtn = document.getElementById("cancelBtn");

const formTitle = document.getElementById("formTitle");

const searchInput = document.getElementById("searchInput");

let editIndex = null;

/* =========================
   LOAD DATASET
========================= */

async function loadDataset() {

    datasetContainer.innerHTML = `
        <tr class="state-row">
            <td colspan="4">Loading dataset...</td>
        </tr>
    `;

    try {

        const response = await fetch(API_URL);

        const data = await response.json();

        window.fullDataset = data;

        displayDataset(data);

    } catch (error) {

        console.error(error);

        datasetContainer.innerHTML = `
            <tr class="state-row">
                <td colspan="4">
                    Failed to load dataset.
                </td>
            </tr>
        `;
    }
}

/* =========================
   DISPLAY DATASET
========================= */

function displayDataset(data) {

    datasetContainer.innerHTML = "";

    if (!data.length) {

        datasetContainer.innerHTML = `
            <tr class="state-row">
                <td colspan="4">
                    No matching entries found.
                </td>
            </tr>
        `;

        return;
    }

    data.forEach((item, index) => {

        const row = document.createElement("tr");

        row.innerHTML = `
            <td>
                ${item.topic}
            </td>

            <td>
                <span class="category-badge">
                    ${item.category}
                </span>
            </td>

            <td>
                <div class="questions-cell">
                    ${item.questions.join("<br>")}
                </div>
            </td>

            <td>
                <div class="action-buttons">

                    <button
                        class="edit-btn"
                        onclick="editEntry(${index})"
                    >
                        Edit
                    </button>

                    <button
                        class="delete-btn"
                        onclick="deleteEntry(${index})"
                    >
                        Delete
                    </button>

                </div>
            </td>
        `;

        datasetContainer.appendChild(row);
    });
}

/* =========================
   SEARCH
========================= */

searchInput.addEventListener("input", () => {

    const value = searchInput.value.toLowerCase();

    const filtered = window.fullDataset.filter(item => {

        const topicMatch =
            item.topic.toLowerCase().includes(value);

        const categoryMatch =
            item.category.toLowerCase().includes(value);

        return topicMatch || categoryMatch;
    });

    displayDataset(filtered);
});

/* =========================
   SHOW FORM
========================= */

addBtn.addEventListener("click", () => {

    formContainer.classList.remove("hidden");

    formTitle.innerText = "Add Dataset Entry";

    clearForm();

    editIndex = null;

    formContainer.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
});

/* =========================
   CANCEL FORM
========================= */

cancelBtn.addEventListener("click", () => {

    formContainer.classList.add("hidden");

    clearForm();
});

/* =========================
   SAVE ENTRY
========================= */

saveBtn.addEventListener("click", async () => {

    const entry = {

        topic:
            document.getElementById("topic").value.trim(),

        category:
            document.getElementById("category").value.trim(),

        questions:
            document.getElementById("questions")
                .value
                .split("\n")
                .map(q => q.trim())
                .filter(Boolean),

        keywords:
            document.getElementById("keywords")
                .value
                .split(",")
                .map(k => k.trim())
                .filter(Boolean),

        answer:
            document.getElementById("answer").value.trim(),

        answer_en:
            document.getElementById("answer_en").value.trim()
    };

    try {

        if (editIndex === null) {

            await fetch(`${API_URL}/add`, {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(entry)
            });

        } else {

            await fetch(`${API_URL}/update/${editIndex}`, {

                method: "PUT",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(entry)
            });
        }

        formContainer.classList.add("hidden");

        clearForm();

        loadDataset();

    } catch (error) {

        console.error(error);

        alert("Error saving entry.");
    }
});

/* =========================
   DELETE ENTRY
========================= */

async function deleteEntry(index) {

    const confirmDelete = confirm(
        "Delete this dataset entry?"
    );

    if (!confirmDelete) return;

    try {

        await fetch(`${API_URL}/delete/${index}`, {
            method: "DELETE"
        });

        loadDataset();

    } catch (error) {

        console.error(error);

        alert("Error deleting entry.");
    }
}

/* =========================
   EDIT ENTRY
========================= */

async function editEntry(index) {

    try {

        const response = await fetch(API_URL);

        const data = await response.json();

        const item = data[index];

        formContainer.classList.remove("hidden");

        formTitle.innerText = "Edit Dataset Entry";

        document.getElementById("topic").value =
            item.topic;

        document.getElementById("category").value =
            item.category;

        document.getElementById("questions").value =
            item.questions.join("\n");

        document.getElementById("keywords").value =
            item.keywords.join(", ");

        document.getElementById("answer").value =
            item.answer;

        document.getElementById("answer_en").value =
            item.answer_en;

        editIndex = index;

    } catch (error) {

        console.error(error);

        alert("Error loading entry.");
    }
}

/* =========================
   CLEAR FORM
========================= */

function clearForm() {

    [
        "topic",
        "category",
        "questions",
        "keywords",
        "answer",
        "answer_en"
    ].forEach(id => {

        document.getElementById(id).value = "";
    });
}

/* =========================
   INIT
========================= */

loadDataset();