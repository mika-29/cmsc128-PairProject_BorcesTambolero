document.addEventListener("DOMContentLoaded", function () {
  const btnNext = document.getElementById("nextBtn");
  const btnBack = document.getElementById("btn-back");
  const step1 = document.getElementById("step1");
  const step2 = document.getElementById("step2");

  btnNext.addEventListener("click", function () {
    const name = document.querySelector("input[name='name']").value.trim();
    const email = document.querySelector("input[name='email']").value.trim();
    const password = document.querySelector("input[name='password']").value;
    const confirm = document.querySelector("input[name='confirm']").value;

    if (!name || !email || !password || !confirm) {
      alert("Please fill in all fields.");
      return;
    }
    if (password !== confirm) {
      alert("Passwords do not match.");
      return;
    }

    // Switch steps using classes
    step1.classList.remove("active-step");
    step1.classList.add("inactive-step");
    step2.classList.add("active-step");
    step2.classList.remove("inactive-step");
  });

  btnBack.addEventListener("click", function () {
    step2.classList.remove("active-step");
    step2.classList.add("inactive-step");
    step1.classList.add("active-step");
    step1.classList.remove("inactive-step");
  });
});


// PREVENT BACK BUTTON CACHING
window.addEventListener("pageshow", function (event) {
  var historyTraversal = event.persisted ||
    (typeof window.performance != "undefined" &&
      window.performance.navigation.type === 2);

  if (historyTraversal) {
    // 1. Reset the form data
    document.getElementById("registerForm").reset();

    // 2. Force the UI back to Step 1
    const step1 = document.getElementById("step1");
    const step2 = document.getElementById("step2");
    
    step2.classList.remove("active-step");
    step2.classList.add("inactive-step");
    step1.classList.add("active-step");
    step1.classList.remove("inactive-step");

    // 3. Force a reload from the server to ensure clean state
    window.location.reload();
  }
});