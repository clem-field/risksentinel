/* Filename: script.js*/

/* Setup App */
const express = require("express");
const { exec } = require("child_process");
const path = require("path");

const app = express();
const PORT = 3000;

// Serve static files (HTML, CSS, JS)
app.use(express.static(path.join(__dirname, "public")));

// Route to execute the Python script
app.get("/run-python", (req, res) => {
    exec("python3 script.py", (error, stdout, stderr) => {
        if (error) {
            console.error(`Error executing Python script: ${error}`);
            res.status(500).send(`Error: ${error.message}`);
            return;
        }
        if (stderr) {
            console.error(`Python script stderr: ${stderr}`);
            res.status(500).send(`Error: ${stderr}`);
            return;
        }
        res.send(stdout);
    });
});

// Start the server
app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});

/* event listener */


/* fetch data functions */
function fetch_data() {
    alert("fetch data function called");
    const d = new Date();
    document.getElementById("time").innerHTML = d;
};

/* select RAG engine */
function engine_selected() {
    var engine = document.getElementById('engine_choice').value;
    if (engine == "----") {
        alert("cannot be default");
    } else {
        alert(engine);
        start_rag()
    }
};

/* start RAG */
function start_rag() {
    alert("starting rag")
};

/* Question from user */
function ask_question() {
    var question = document.getElementById('ragInput').value;
    if (question == "") {
        alert("No question detected");
    } else {
        alert("answering question ");
        document.getElementById('ragForm').reset();
        answer_question();
    }
};

/* Answer Question */
function answer_question() {
    var answerForm = document.getElementById("ragAnswer");
    if (answerForm.style.display === "none") {
        answerForm.style.display = "block";
    } 
};

/* exiting rag */
function exit_rag() {
    alert("Exiting RAG")
};
