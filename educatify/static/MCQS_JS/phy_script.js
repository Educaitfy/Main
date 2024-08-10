let questions = [];
let currentQuestionIndex = 0;
let score = 0;

document.addEventListener("DOMContentLoaded", () => {
  const questionElement = document.getElementById("question");
  const answerButtons = document.getElementById("answer-buttons");
  const nextButton = document.getElementById("next-btn");
  const prevButton = document.getElementById("prev-btn");

  // Fetch questions from the server once
  fetch("/PHY_questions")
    .then((response) => response.json())
    .then((data) => {
      questions = data;
      startQuiz();
    });

  // Event listener for the "Next" button, added only once
  nextButton.addEventListener("click", () => {
    if (nextButton.innerHTML === "Attempt again!") {
      startQuiz();
    } else if (nextButton.innerHTML == "Go back to Dashboard") {
      window.location.href = "/back";
    } else {
      currentQuestionIndex++;
      if (currentQuestionIndex < questions.length) {
        showQuestion();
      } else {
        showScore();
      }
    }
  });

  // Event listener for the "Previous" button
  prevButton.addEventListener("click", () => {
    if (currentQuestionIndex > 0) {
      currentQuestionIndex--;
      showQuestion();
    }
  });

  function startQuiz() {
    currentQuestionIndex = 0;
    score = 0;
    nextButton.innerHTML = "Next";
    nextButton.style.display = "none";
    prevButton.style.display = "none";
    const dashboardButton = document.getElementById("dashboard-btn");
    if (dashboardButton) {
      dashboardButton.remove(); // Remove the "Go back to Dashboard" button if it exists
    }
    showQuestion();
  }

  function showQuestion() {
    resetState();
    let currentQuestion = questions[currentQuestionIndex];
    questionElement.innerHTML = `${currentQuestionIndex + 1}. ${
      currentQuestion.question
    }`;

    currentQuestion.answers.forEach((answer) => {
      const button = document.createElement("button");
      button.innerHTML = answer.text;
      button.classList.add("btn");
      answerButtons.appendChild(button);
      button.addEventListener("click", () =>
        selectAnswer(button, currentQuestion)
      );
    });

    prevButton.style.display = currentQuestionIndex === 0 ? "none" : "block";
    nextButton.innerHTML =
      currentQuestionIndex === questions.length - 1 ? "Submit" : "Next";
  }

  function resetState() {
    nextButton.style.display = "none";
    prevButton.style.display = currentQuestionIndex === 0 ? "none" : "block";
    while (answerButtons.firstChild) {
      answerButtons.removeChild(answerButtons.firstChild);
    }
  }

  function selectAnswer(button, question) {
    const isCorrect = question.answers.find(
      (answer) => answer.text === button.innerHTML
    ).correct;
    if (isCorrect) {
      button.classList.add("correct");
      score++;
    } else {
      button.classList.add("incorrect");
    }

    Array.from(answerButtons.children).forEach((btn) => {
      const answer = question.answers.find(
        (answer) => answer.text === btn.innerHTML
      );
      if (answer.correct) {
        btn.classList.add("correct");
      }
      btn.disabled = true;
    });
    nextButton.style.display = "block";
  }

  function showScore() {
    resetState();
    questionElement.innerHTML = `You scored ${score} out of ${questions.length}!`;
    nextButton.style.display = "none";
    nextButton.insertAdjacentHTML(
      "afterend",
      '<button id="dashboard-btn" class="btn">Go back to Subj Mcqs</button>'
    );
    const dashboardButton = document.getElementById("dashboard-btn");
    dashboardButton.addEventListener("click", () => {
      window.location.href = "/SubjMCQs"; // Redirect to the dashboard route
    });
    if (prevButton) {
      prevButton.remove(); // Remove the "Go back to Dashboard" button if it exists
    }

    // Send score to the server
    fetch("/save_physics_score", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ score: score }),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        if (data.error) {
          console.error("Error saving score:", data.error);
        } else {
          console.log("Score saved successfully:", data.message);
        }
      })
      .catch((error) => {
        console.error("Error:", error);
      });
  }
});
