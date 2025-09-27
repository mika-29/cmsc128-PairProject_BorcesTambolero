document.addEventListener("DOMContentLoaded", () => {
  // ====== Element References ======
  const addButton       = document.querySelector(".add-task");
  const form            = document.getElementById("addTaskForm");
  const closeBtn        = document.getElementById("closePopUp");
  const saveBtn         = document.getElementById("saveTask");
  const taskNameInput   = document.getElementById("taskName");
  const dueDateInput    = document.getElementById("dueDate");
  const dueTimeInput    = document.getElementById("dueTime");
  const taskSelect      = document.getElementById("task");
  const prioritySelect  = document.getElementById("priority");
  const nameError       = document.getElementById("nameError");

  let editingTask = null;   

  // ====== Rendering Tasks ======
  async function loadTasks() {
    const res = await fetch("/tasks");
    const tasks = await res.json();
    renderTasks(tasks);
  }

  function renderTasks(tasks) {
    document.querySelectorAll(".list-container").forEach(c => (c.innerHTML = ""));

    tasks.forEach(task => {
      const targetColumn = document.querySelector(
        `.status.${task.status} .list-container`
      );
      if (!targetColumn) return;

      const taskCard = document.createElement("div");
      taskCard.className = `task-card priority-${task.priority}`; // add priority class
      taskCard.dataset.id = task.id;
      taskCard.dataset.title = task.title;
      taskCard.dataset.status = task.status;
      taskCard.dataset.deadline = task.deadline || "";
      taskCard.dataset.duetime = task.duetime || "";
      taskCard.dataset.priority = task.priority;

      taskCard.innerHTML = `
        <div class="task-content">
          <strong class="${task.status === "done" ? "completed" : ""}">${task.title}</strong><br>
          <small>Due: ${formatDueDate(task.deadline, task.duetime, task.status)}</small>
        </div>
        <div class="task-options">
          <button class="options-btn">⋮</button>
          <ul class="options-menu">
            <li class="edit-task">Edit</li>
            <li class="delete-task">Delete</li>
            <li class="move-task">
              Change Status
              <ul class="status-menu">
                <li data-status="pending">Pending</li>
                <li data-status="ongoing">Ongoing</li>
                <li data-status="done">Done</li> 
              </ul>
            </li>
          </ul>
        </div>
      `;

      targetColumn.appendChild(taskCard);
    });
  }

  async function handleSaveTask(e) {
    e.preventDefault();

    const taskData = {
      title: taskNameInput.value.trim(),
      deadline: dueDateInput.value,
      duetime: dueTimeInput.value,
      status: taskSelect.value,
      priority: prioritySelect.value,
    };

    if (!taskData.title) {
      nameError.textContent = "Please enter a task name.";
      return;
    }
    nameError.textContent = "";

    if (editingTask) {
      const id = editingTask.dataset.id;
      await fetch(`/tasks/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(taskData),
      });
    } else {
      // add new
      await fetch("/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(taskData),
      });
    }

    editingTask = null;
    taskNameInput.focus();

    closeForm();
    loadTasks();
  }

  function formatDueDate(dateStr, timeStr, status) {
    if (!dateStr) return ""; // no deadline

    const deadline = new Date(`${dateStr}T${timeStr || "00:00"}`);
    const now = new Date();
    const diffMs = deadline - now; 
    const diffHours = diffMs / (1000 * 60 * 60);

    const optionsDate = { month: "short", day: "numeric", year: "numeric" };
    const optionsTime = { hour: "numeric", minute: "2-digit", hour12: true };

    const formattedDate = deadline.toLocaleDateString("en-US", optionsDate);
    const formattedTime = timeStr ? deadline.toLocaleTimeString("en-US", optionsTime) : "";
    const formatted = timeStr ? `${formattedDate} • ${formattedTime}` : formattedDate;

    // If task is already done → just show normal date, no warnings
    if (status === "done") {
      return formatted;
    }

    // Overdue
    if (diffMs < 0) {
      return `<span class="overdue">${formatted} (Overdue)</span>`;
    }

    // Near deadline (within 24h)
    if (diffHours <= 24) {
      return `<span class="near-deadline">${formatted} (Due Soon)</span>`;
    }

    return formatted;
  }
  // ====== Handle Task Options ======
  async function handleTaskOptions(e) {
    if (e.target.classList.contains("options-btn")) {
      const menu = e.target.nextElementSibling; // the ul.options-menu
      menu.classList.toggle("show");
      return; // stop here so it doesn’t trigger other actions
    }

    // DELETE task
    if (e.target.classList.contains("delete-task")) {
      const task = e.target.closest(".task-card");
      const id = task.dataset.id;

      if (confirm("Are you sure you want to delete this task?")) {
        await fetch(`/tasks/${id}`, { method: "DELETE" });
        loadTasks();
      }
    }

    // EDIT task
    if (e.target.classList.contains("edit-task")) {
      const task = e.target.closest(".task-card");
      editingTask = task;

      taskNameInput.value = task.dataset.title || "";
      dueDateInput.value = task.dataset.deadline || "";
      dueTimeInput.value = task.dataset.duetime || "";
      taskSelect.value = task.dataset.status || "pending";
      prioritySelect.value = task.dataset.priority || "important";

      saveBtn.textContent = "Edit Task";
      openForm(true);
    }

    // CHANGE STATUS
    if (e.target.closest(".status-menu li")) {
      const newStatus = e.target.getAttribute("data-status");
      const task = e.target.closest(".task-card");
      const id = task.dataset.id;

      await fetch(`/tasks/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });

      loadTasks();
    }
  }
  // ====== Form Controls ======
  function openForm(isEdit = false) {
    form.style.display = "flex";

    if (!isEdit) {
      taskNameInput.value   = "";
      dueDateInput.value    = "";
      dueTimeInput.value    = "";
      taskSelect.value      = "pending";
      prioritySelect.value  = "important";
      editingTask           = null;
      saveBtn.textContent   = "Add Task";
    }
  }

  function closeForm() {
    form.style.display = "none";
  }

  // ====== Event Listeners ======
  addButton.addEventListener("click", () => openForm(false));
  closeBtn.addEventListener("click", closeForm);
  saveBtn.addEventListener("click", handleSaveTask);
  document.addEventListener("click", handleTaskOptions);

  // ====== Initial Load ======
  loadTasks();
});
