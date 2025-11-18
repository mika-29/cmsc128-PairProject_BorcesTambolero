document.addEventListener("DOMContentLoaded", () => {
  // ====== Element References ====== (delegate)
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
  // ====== Collaborative Lists & Tasks ======
  const addCollabBtn = document.getElementById("addCollabBtn");
  const collabForm = document.getElementById("addCollabForm");
  const closeCollabBtn = document.getElementById("closeCollabPopUp");
  const saveCollabBtn = document.getElementById("saveCollabList");
  const collabListsContainer = document.querySelector(".collab-lists");
  const personalBtn = document.getElementById("personalBtn"); 
  const collabBtn = document.getElementById("collabBtn");
  const personalContainer = document.getElementById("personalContainer");
  const collabContainer = document.getElementById("collabContainer");
  const collabExpanded = document.getElementById("collabExpanded");
  const collabPendingTask = document.getElementById("collabPendingTask");
  const collabOngoingTask = document.getElementById("collabOngoingTask");
  const collabDoneTask = document.getElementById("collabDoneTask");
  const collabOverview = document.getElementById("collabOverview");
  let currentCollabListId = null;
  
  personalBtn.addEventListener("click", () => { 
    personalContainer.classList.remove("hidden"); 
    collabContainer.classList.add("hidden"); 
    collabExpanded.classList.add('hidden');
    currentCollabListId = null;
    personalBtn.classList.add("active");
    collabBtn.classList.remove("active");
  }); 
     
  collabBtn.addEventListener("click", () => { 
    personalContainer.classList.add("hidden"); 
    collabContainer.classList.remove("hidden"); 
    // keep expanded hidden until a list is opened
    collabExpanded.classList.add('hidden');
    currentCollabListId = null;
    collabBtn.classList.add("active"); 
    personalBtn.classList.remove("active");
  });

  // Show/hide Add Collab button depending on view
  function updateCollabButton() {
    addCollabBtn.style.display = collabContainer.classList.contains("hidden") ? "none" : "block";
  }
  updateCollabButton();
  personalBtn.addEventListener("click", updateCollabButton);
  collabBtn.addEventListener("click", updateCollabButton);

  // Open/Close collab form
  addCollabBtn.addEventListener("click", () => collabForm.classList.remove("hidden"));
  closeCollabBtn.addEventListener("click", () => collabForm.classList.add("hidden"));

 // Save new collaborative list (append to UI)
  saveCollabBtn.addEventListener("click", async () => {
    const title = document.getElementById("collabTitle").value.trim();
    const email = document.getElementById("addUserEmail").value.trim();

    if (!title || !email) {
      return alert("Please fill out both fields");
    }

    try {
      const response = await fetch("/collab/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: title,
          emails: [email] // wrap in array as your backend expects
        })
      });

      if (!response.ok) {
        // try to surface a JSON error message, fall back to text/html
        let errMsg;
        try {
          const j = await response.json();
          errMsg = j.error || JSON.stringify(j);
        } catch (e) {
          errMsg = await response.text();
        }
        alert(`Failed to create list: ${errMsg}`);
        return;
      }

      const data = await response.json();

      // Append new list to UI
      const newCard = document.createElement("div");
      newCard.classList.add("collab-list-card");
      newCard.dataset.listId = data.list_id; // use the list_id returned from backend
      newCard.innerHTML = `
        <h3>${title}</h3>
        <p>Added user: ${email}</p>
        <button class="open-collab">Open</button>
        <div class="collab-tasks hidden">
          <div class="tasks-container"></div>
          <button class="add-collab-task">Add Task</button>
        </div>
      `;
      collabListsContainer.appendChild(newCard);

      // Wire up listeners for the newly created card (uses same helper as loadCollabLists)
      attachCollabCardListeners();

      // Reset form
      collabForm.classList.add("hidden");
      document.getElementById("collabTitle").value = "";
      document.getElementById("addUserEmail").value = "";

    } catch (err) {
      console.error(err);
      alert("Failed to create collaborative list. Check console for details.");
    }
  });

  // Load all collaborative lists for current user
  async function loadCollabLists() {
    collabListsContainer.innerHTML = "";
    const res = await fetch("/collab/mylists");
    const lists = await res.json();

    lists.forEach(list => {
      const card = document.createElement("div");
      card.className = "collab-list-card";
      card.dataset.listId = list.id;

      card.innerHTML = `
        <h3>${list.title}</h3>
        <button class="open-collab">Open</button>
        <div class="collab-tasks hidden">
          <div class="tasks-container"></div>
          <button class="add-collab-task">Add Task</button>
        </div>
      `;

      collabListsContainer.appendChild(card);
    });

    attachCollabCardListeners();
  }

  // Ensure collaborative list overview is centered and toggles properly
  function attachCollabCardListeners() {
    document.querySelectorAll(".collab-list-card").forEach(card => {
      const openBtn = card.querySelector(".open-collab");
      openBtn.addEventListener("click", async () => {
        // Hide the collabOverview and show the kanban layout
        collabOverview.classList.add("hidden");
        collabExpanded.classList.remove("hidden");

        // Set the currently active collab list ID
        currentCollabListId = card.dataset.listId;

        // Clear the kanban columns
        collabPendingTask.innerHTML = "";
        collabOngoingTask.innerHTML = "";
        collabDoneTask.innerHTML = "";

        // Load tasks for the selected collaborative list
        await loadCollabTasks(currentCollabListId);
      });
    });
  }

  // Add a back button to return to the collabOverview
  const backToOverviewBtn = document.createElement("button");
  backToOverviewBtn.textContent = "Back to Overview";
  backToOverviewBtn.className = "back-to-overview";
  collabExpanded.appendChild(backToOverviewBtn);
  backToOverviewBtn.addEventListener("click", () => {
    collabOverview.classList.remove("hidden");
    collabExpanded.classList.add("hidden");
    currentCollabListId = null;
  });

  // Load tasks for a specific collaborative list and render in Kanban columns
  async function loadCollabTasks(listId, board) {
    const useMain = !board;
    if (useMain) {
      collabPendingTask.innerHTML = '';
      collabOngoingTask.innerHTML = '';
      collabDoneTask.innerHTML = '';
    } else {
      board.querySelectorAll('.list-container').forEach(c => c.innerHTML = '');
    }

    const res = await fetch(`/collab/tasks/${listId}`);
    if (!res.ok) {
      const text = await res.text();
      console.error('Failed to load collab tasks:', text);
      return;
    }
    const tasks = await res.json();

    tasks.forEach(task => {
      const taskCard = document.createElement("div");
      taskCard.className = `task-card priority-${task.priority}`;
      taskCard.dataset.taskId = task.id;
      taskCard.innerHTML = `
        <strong>${task.title}</strong>
        <small>Status: ${task.status}</small>
        <button class="delete-task">Delete</button>
      `;

      if (useMain) {
        if (task.status === 'pending') collabPendingTask.appendChild(taskCard);
        else if (task.status === 'ongoing') collabOngoingTask.appendChild(taskCard);
        else collabDoneTask.appendChild(taskCard);
      } else {
        const col = board.querySelector(`.list-container[data-status="${task.status}"]`);
        if (col) col.appendChild(taskCard);
      }

      // Delete task
      taskCard.querySelector(".delete-task").addEventListener("click", async () => {
        await fetch(`/collab/tasks/${task.id}`, { method: "DELETE" });
        taskCard.remove();
      });
    });
  }

  // Initial load
  loadCollabLists();


  let editingTask = null;   

  // ====== Rendering Tasks ======                              //fetches tasks from backend and sends them to renderTasks 
  async function loadTasks(sortBy = "date_added") {
    const res = await fetch(`/tasks?sort=${sortBy}`);          //gastorya sa backend, GET /tasks 
    if (!res.ok) {
      const text = await res.text();
      console.error("Failed to load tasks:", text);
      alert("Failed to load tasks. See console for details.");
      return;
    }
    const tasks = await res.json();
    renderTasks(tasks);
    setSortDropdown(sortBy);
  }

  function renderTasks(tasks) {
    //tasks.sort((a,b) => new Date(b.createdAt) - new Date(a.createdAt));
    document.querySelectorAll(".list-container").forEach(c => (c.innerHTML = ""));

    tasks.forEach(task => {                            //builds a task card and puts it in the correct status column 
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

  function setSortDropdown(value) {
    const dropdown = document.getElementById("sort");
    if (dropdown) dropdown.value = value;
  }

  async function handleSaveTask(e) {                  //handles form submission (adding or editing taks)
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
      const res = await fetch(`/tasks/${id}`, {         //PUT request, updates data 
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(taskData),
      });
      if (!res.ok) {
        const text = await res.text();
        console.error("Failed to update task:", text);
        alert("Failed to update task. See console for details.");
        return;
      }
    } else {
      taskData.createdAt = new Date().toISOString();
      // add new
      if (currentCollabListId) {
        // create a collaborative task
        const res = await fetch("/collab/tasks", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            list_id: currentCollabListId,
            title: taskData.title,
            status: taskData.status,
            priority: taskData.priority,
            deadline: taskData.deadline,
            duetime: taskData.duetime
          })
        });
        if (!res.ok) {
          const text = await res.text();
          console.error("Failed to save collaborative task:", text);
          alert("Failed to save task. See console for details.");
          return;
        }

        // reload collab tasks for current list
        await loadCollabTasks(currentCollabListId);
      } else {
        const res = await fetch("/tasks", {              //POST request, adds database 
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(taskData),
        });
        if (!res.ok) {
          const text = await res.text();
          console.error("Failed to save task:", text);
          alert("Failed to save task. See console for details.");
          return;
        }
      }
    }

    editingTask = null;
    taskNameInput.focus();

    closeForm();
    loadTasks();         //reload UI 
  }

  function formatDueDate(dateStr, timeStr, status) {             //makes deadlines readable and applies warnings 
    if (!dateStr) return "No deadline set"; // no deadline

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
  async function handleTaskOptions(e) {            //edit,delete,change status 
    if (e.target.classList.contains("options-btn")) { //toggle menu 
      const menu = e.target.nextElementSibling; // the ul.options-menu
      menu.classList.toggle("show");
      return; // stop here so it doesn’t trigger other actions
    }

    // DELETE task
    if (e.target.classList.contains("delete-task")) {
      const task = e.target.closest(".task-card");
      const id = task.dataset.id; 

      if (confirm("Are you sure you want to delete this task?")) {
        //Temporarily hide task from UI 
        task.style.display = "none"; 

        //Show toast and store info 
        showToast(`Task "${task.dataset.title}" deleted`, { id, element: task, title: task.dataset.title, }); 
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

      await fetch(`/tasks/${id}`, {         //PUT request for status 
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),      //object into JSON string to send into backend 
      });

      loadTasks();
    }
  }
  // ====== Form Controls ======
  function openForm(isEdit = false) {             //popup the hidden form "flex" 
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

  // ====== Event Listeners ====== for buttons to work 
  addButton.addEventListener("click", () => openForm(false));
  closeBtn.addEventListener("click", closeForm);
  saveBtn.addEventListener("click", handleSaveTask);
  document.addEventListener("click", handleTaskOptions);

  // Sidebar sort dropdown
  document.getElementById("sortForm").addEventListener("change", function (e) {
    const sortValue = e.target.value;
    // reload tasks based on selected sort
    loadTasks(sortValue);
  });



  // ====== Initial Load ======
  loadTasks();

  //=====Toast Logic=====
  const toast = document.getElementById("toast");
  const toastMessage = document.getElementById("toast-message");
  const undoBtn = document.getElementById("undo-btn"); 

  let deleteTimeout = null;
  let pendingDelete = null; //holds the task waiting for permanent deletion 

    function showToast(message, task) {
      toastMessage.textContent = message;
      toast.classList.remove("hidden");

    // Clear previous timeout if exists
    if (deleteTimeout) clearTimeout(deleteTimeout);

    // Store task info to restore on undo
    pendingDelete = task;

    // Auto-hide after 5s and permanently delete
    deleteTimeout = setTimeout(async () => {
      if (pendingDelete) {
        await fetch(`/tasks/${pendingDelete.id}`, { method: "DELETE" });    //DELETE request 
        pendingDelete = null;
        loadTasks();
      }
      toast.classList.add("hidden");
    }, 5000);
  }

  undoBtn.addEventListener("click", () => {
    if (pendingDelete) {
      // Restore tasks visually
      pendingDelete.element.style.display = ""; 
      pendingDelete = null;
    }
    if (deleteTimeout) clearTimeout(deleteTimeout);
    toast.classList.add("hidden");
  });
});