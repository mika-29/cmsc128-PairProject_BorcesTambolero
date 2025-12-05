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
  const deleteModal = document.getElementById("deleteModal");
  const confirmDeleteBtn = document.getElementById("confirmDeleteBtn");
  const cancelDeleteBtn = document.getElementById("cancelDeleteBtn");

  let taskToDeleteElement = null; // Stores the DOM element
  let taskToDeleteId = null;      // Stores the ID
  let editingTask = null;   

  // ====== Rendering Tasks ======                              
  async function loadTasks(sortBy = "date_added") {
    const res = await fetch(`/tasks?sort=${sortBy}`);
    const tasks = await res.json();
    renderTasks(tasks);
    setSortDropdown(sortBy);
  }

  function renderTasks(tasks) {
    document.querySelectorAll(".list-container").forEach(c => (c.innerHTML = ""));

    tasks.forEach(task => {
      const targetColumn = document.querySelector(
        `.status.${task.status} .list-container`
      );
      if (!targetColumn) return;

      const taskCard = document.createElement("div");
      taskCard.className = `task-card priority-${task.priority}`; 
      
      // --- ENABLE DRAGGING HERE ---
      taskCard.setAttribute("draggable", "true"); 
      // ----------------------------

      taskCard.dataset.id = task.id;
      taskCard.dataset.title = task.title;
      taskCard.dataset.status = task.status;
      taskCard.dataset.deadline = task.deadline || "";
      taskCard.dataset.duetime = task.duetime || "";
      taskCard.dataset.priority = task.priority;
      taskCard.dataset.createdAt = task.createdAt || "";

      taskCard.innerHTML = `
        <div class="task-content">
          <strong class="${task.status === "done" ? "completed" : ""}">${task.title}</strong><br>
          <small>Due: ${formatDueDate(task.deadline, task.duetime, task.status)}</small>
          <br>
          <small class="created-date">Created: ${new Date(task.created_at).toLocaleString()}</small>
        </div>
        <div class="task-options">
          <button class="options-btn">⋮</button>
          <ul class="options-menu">
            <li class="edit-task">Edit</li>
            <li class="delete-task">Delete</li>
          </ul>
        </div>
      `;

      // Add drag event listener directly to the new card
      taskCard.addEventListener("dragstart", dragStart);
      
      targetColumn.appendChild(taskCard);
    });
  }

  function setSortDropdown(value) {
    const dropdown = document.getElementById("sort");
    if (dropdown) dropdown.value = value;
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
      taskData.createdAt = new Date().toISOString();
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
    if (!dateStr) return "No deadline set"; 

    const deadline = new Date(`${dateStr}T${timeStr || "00:00"}`);
    const now = new Date();
    const diffMs = deadline - now; 
    const diffHours = diffMs / (1000 * 60 * 60);

    const optionsDate = { month: "short", day: "numeric", year: "numeric" };
    const optionsTime = { hour: "numeric", minute: "2-digit", hour12: true };

    const formattedDate = deadline.toLocaleDateString("en-US", optionsDate);
    const formattedTime = timeStr ? deadline.toLocaleTimeString("en-US", optionsTime) : "";
    const formatted = timeStr ? `${formattedDate} • ${formattedTime}` : formattedDate;

    if (status === "done") {
      return formatted;
    }

    if (diffMs < 0) {
      return `<span class="overdue">${formatted} (Overdue)</span>`;
    }

    if (diffHours <= 24) {
      return `<span class="near-deadline">${formatted} (Due Soon)</span>`;
    }

    return formatted;
  }

  // ====== Handle Task Options ======
  async function handleTaskOptions(e) {
    if (e.target.classList.contains("options-btn")) {
      const menu = e.target.nextElementSibling; 
      menu.classList.toggle("show");
      return; 
    }

    if (e.target.classList.contains("delete-task")) {
      const task = e.target.closest(".task-card");
      const id = task.dataset.id; 

      // Close the dropdown menu
      const menu = e.target.closest(".options-menu");
      if(menu) menu.classList.remove("show");

      // STORE the task info and OPEN the custom modal
      taskToDeleteElement = task;
      taskToDeleteId = id;
      deleteModal.style.display = "flex";
    }

    if (e.target.classList.contains("edit-task")) {
      const menu = e.target.closest(".options-menu");
      if (menu) menu.classList.remove("show"); 
      
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

    // if (e.target.closest(".status-menu li")) {
    //   const newStatus = e.target.getAttribute("data-status");
    //   const task = e.target.closest(".task-card");
    //   const id = task.dataset.id;

    //   await fetch(`/tasks/${id}`, {
    //     method: "PUT",
    //     headers: { "Content-Type": "application/json" },
    //     body: JSON.stringify({ status: newStatus }),
    //   });
    //   loadTasks();
    // }
  }

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

  addButton.addEventListener("click", () => openForm(false));
  closeBtn.addEventListener("click", closeForm);
  saveBtn.addEventListener("click", handleSaveTask);
  document.addEventListener("click", handleTaskOptions);

  document.getElementById("sortForm").addEventListener("change", function (e) {
    const sortValue = e.target.value;
    loadTasks(sortValue);
  });

  loadTasks();

  //===== Toast Logic =====
  const toast = document.getElementById("toast");
  const toastMessage = document.getElementById("toast-message");
  const undoBtn = document.getElementById("undo-btn"); 

  let deleteTimeout = null;
  let pendingDelete = null; 

  function showToast(message, task) {
      toastMessage.textContent = message;
      toast.classList.remove("hidden");

    if (deleteTimeout) clearTimeout(deleteTimeout);
    pendingDelete = task;

    deleteTimeout = setTimeout(async () => {
      if (pendingDelete) {
        await fetch(`/tasks/${pendingDelete.id}`, { method: "DELETE" });
        pendingDelete = null;
        loadTasks();
      }
      toast.classList.add("hidden");
    }, 5000);
  }

  undoBtn.addEventListener("click", () => {
    if (pendingDelete) {
      pendingDelete.element.style.display = ""; 
      pendingDelete = null;
    }
    if (deleteTimeout) clearTimeout(deleteTimeout);
    toast.classList.add("hidden");
  });

  // ==========================================
  // DRAG AND DROP LOGIC (NEW SECTION)
  // ==========================================
  
  let draggedTask = null;

  function dragStart(e) {
      draggedTask = this;
      // Use a timeout to keep the element visible while dragging starts, then hide for effect
      setTimeout(() => this.classList.add("dragging"), 0);
  }

  const columns = document.querySelectorAll(".status");

  columns.forEach(column => {
      column.addEventListener("dragover", (e) => {
          e.preventDefault();
          const afterElement = getDragAfterElement(column.querySelector(".list-container"), e.clientY);
          const listContainer = column.querySelector(".list-container");
          
          if (afterElement == null) {
              listContainer.appendChild(draggedTask);
          } else {
              listContainer.insertBefore(draggedTask, afterElement);
          }
      });

      column.addEventListener("drop", async (e) => {
          e.preventDefault();
          draggedTask.classList.remove("dragging");

          const listContainer = column.querySelector(".list-container");
          const containerId = listContainer.id; 
          let newStatus = "";

          // Determine status based on the container ID
          if (containerId === "pendingTaks") newStatus = "pending";
          else if (containerId === "ongoingTaks") newStatus = "ongoing";
          else if (containerId === "doneTaks") newStatus = "done";

          // If status changed, update the backend
          if (newStatus && draggedTask.dataset.status !== newStatus) {
              const taskId = draggedTask.dataset.id;
              
              // Optimistic UI update
              draggedTask.dataset.status = newStatus;

              // Check if completed style needs update
              const titleStrong = draggedTask.querySelector("strong");
              if (newStatus === "done") {
                  titleStrong.classList.add("completed");
              } else {
                  titleStrong.classList.remove("completed");
              }

              // Send update to server
              await fetch(`/tasks/${taskId}/status`, {
                  method: "PATCH", // Ensure backend has this PATCH route
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ status: newStatus })
              });
              
              // Optional: reload tasks to confirm sort order or specific formatting
              // loadTasks(); 
          }
      });
  });

  function getDragAfterElement(container, y) {
      const draggableElements = [...container.querySelectorAll('.task-card:not(.dragging)')];

      return draggableElements.reduce((closest, child) => {
          const box = child.getBoundingClientRect();
          const offset = y - box.top - box.height / 2;
          if (offset < 0 && offset > closest.offset) {
              return { offset: offset, element: child };
          } else {
              return closest;
          }
      }, { offset: Number.NEGATIVE_INFINITY }).element;
  }

  // ==========================================
// DELETE 
// ==========================================

// --- Cancel Delete ---
  cancelDeleteBtn.addEventListener("click", () => {
      deleteModal.style.display = "none";
      taskToDeleteElement = null;
      taskToDeleteId = null;
  });

  // --- Confirm Delete ---
  confirmDeleteBtn.addEventListener("click", () => {
      if (taskToDeleteElement && taskToDeleteId) {
          taskToDeleteElement.style.display = "none"; 
          showToast(
              `Task "${taskToDeleteElement.dataset.title}" deleted`, 
              { 
                  id: taskToDeleteId, 
                  element: taskToDeleteElement, 
                  title: taskToDeleteElement.dataset.title 
              }
          );
      }
      // Close the modal
      deleteModal.style.display = "none";
      
      // Reset variables
      taskToDeleteElement = null;
      taskToDeleteId = null;
  });
});

