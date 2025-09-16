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

  let editingTask = null;   // Stores the task being edited
  let tasks = [];           // In-memory tasks (clears on refresh)

  // ====== Rendering Tasks ======
  function renderTasks() {
    // Clear existing tasks
    document.querySelectorAll(".list-container").forEach(container => {
      container.innerHTML = "";
    });

    tasks.forEach(task => {
      const targetColumn = document.querySelector(
        `.status.${task.status.toLowerCase()} .list-container`
      );
      if (!targetColumn) return;

      const taskCard = document.createElement("div");
      taskCard.className = "task-card";
      taskCard.dataset.id = task.id;

      taskCard.innerHTML = `
        <div class="task-content">
          <strong class="${task.status === "done" ? "completed" : ""}">${task.title}</strong><br>
          <small>Due: ${task.deadline || "(≖_≖ )"} ${task.duetime || ""}</small><br>
          <em>Priority: ${task.priority}</em>
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

  // ====== Form Handlers ======
  function openForm(isEdit = false) {
    form.style.display = "flex";

    if (!isEdit) {
      taskNameInput.value   = "";
      dueDateInput.value    = "";
      dueTimeInput.value    = "";
      taskSelect.value      = "Pending";
      prioritySelect.value  = "Important";
      editingTask           = null;
      saveBtn.textContent   = "Add Task";
    }
  }

  function closeForm() {
    form.style.display = "none";
  }

  // ====== Save Task (Add or Edit) ======
  function handleSaveTask(e) {
    e.preventDefault();

    const name = taskNameInput.value.trim();
    if (!name) {
      nameError.textContent = "Please enter a task name.";
      nameError.style.color = "red";
      return;
    }
    nameError.textContent = "";

    if (editingTask) {
      // Update existing task
      const id   = editingTask.dataset.id;
      const task = tasks.find(t => t.id === id);
      if (task) {
        task.title    = name;
        task.deadline = dueDateInput.value;
        task.duetime  = dueTimeInput.value;
        task.status   = taskSelect.value.toLowerCase();
        task.priority = prioritySelect.value;
      }
    } else {
      // Create new task
      const newTask = {
        id: Date.now().toString(),
        title: name,
        deadline: dueDateInput.value,
        duetime: dueTimeInput.value,
        status: taskSelect.value.toLowerCase(),
        priority: prioritySelect.value,
      };
      tasks.push(newTask);
    }

    renderTasks();
    closeForm();
  }

  // ====== Task Options (Edit, Delete, Move) ======
  function handleTaskOptions(e) {
    // Toggle the 3-dot menu
    if (e.target.classList.contains("options-btn")) {
      const menu = e.target.nextElementSibling;
      document.querySelectorAll(".options-menu").forEach(m => {
        if (m !== menu) m.style.display = "none";
      });
      menu.style.display = menu.style.display === "block" ? "none" : "block";
      return;
    }

    // Hide all menus when clicking elsewhere
    document.querySelectorAll(".options-menu").forEach(m => {
      m.style.display = "none";
    });

    // Delete Task
    if (e.target.classList.contains("delete-task")) {
      const task = e.target.closest(".task-card");
      const id   = task.dataset.id;
      if(confirm("Are you sure you want to delete this task?")){
      tasks = tasks.filter(t => t.id !== id);
      renderTasks();
      }
    }

    // Edit Task
    if (e.target.classList.contains("edit-task")) {
      const task = e.target.closest(".task-card");
      const id   = task.dataset.id;
      const taskData = tasks.find(t => t.id === id);

      if (taskData) {
        taskNameInput.value   = taskData.title;
        dueDateInput.value    = taskData.deadline || "";
        dueTimeInput.value    = taskData.duetime || "";
        taskSelect.value      = capitalize(taskData.status);
        prioritySelect.value  = taskData.priority;
        editingTask           = task;
        saveBtn.textContent   = "Edit Task";
        openForm(true);
      }
    }

    // Move Task (Change Status)
    if (e.target.closest(".status-menu li")) {
      const status = e.target.getAttribute("data-status");
      const task   = e.target.closest(".task-card");
      const id     = task.dataset.id;
      const taskData = tasks.find(t => t.id === id);

      if (taskData) {
        taskData.status = status;
        renderTasks();
      }
    }
  }

  // ====== Utilities ======
  function capitalize(word) {
    return word.charAt(0).toUpperCase() + word.slice(1);
  }

  // ====== Event Listeners ======
  addButton.addEventListener("click", () => openForm(false));
  closeBtn.addEventListener("click", closeForm);
  saveBtn.addEventListener("click", handleSaveTask);
  document.addEventListener("click", handleTaskOptions);

  // ====== Initial Load ======
  renderTasks();
});
