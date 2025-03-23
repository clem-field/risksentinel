const express = require("express");
const { exec } = require("child_process");
const path = require("path");

const app = express();
const PORT = 3000;



// Serve static files (HTML, CSS, JS)
app.use(express.static(path.join(__dirname, "public")));

// Route to execute the Python script
// app.get("/run-python", (req, res) => {
//     exec("python3 script.py", (error, stdout, stderr) => {
//         if (error) {
//             console.error(`Error executing Python script: ${error}`);
//             res.status(500).send(`Error: ${error.message}`);
//             return;
//         }
//         if (stderr) {
//             console.error(`Python script stderr: ${stderr}`);
//             res.status(500).send(`Error: ${stderr}`);
//             return;
//         }
//         res.send(stdout);
//     });
// });

/* Fetch Data */
app.get("/data-fetcher", (req, res) => {
    exec("python3 data_fetcher.py", (error, stdout, stderr) => {
        if (error) {
            console.error(`Error fetching data: ${error}`);
            res.status(500).send(`Error: ${error.message}`);
            data_response();
            return;
        }
        if (stderr) {
            console.error(`Fetching data script stderr: ${stderr}`);
            res.status(500).send(`Error: ${stderr}`);
            data_response();
            return;
        }
        res.send(stdout);
    });
});

/* Start Engine */
app.get("/start-engine", (req, res) => {
    exec("python3 setup_environment.py", (error, stdout, stderr) => {
        if (error) {
            console.error(`Error starting environment: ${error}`);
            res.status(500).send(`Error: ${error.message}`);
            start_engine();
            return;
        }
        if (stderr) {
            console.error(`Fetching starting environment stderr: ${stderr}`);
            res.status(500).send(`Error: ${stderr}`);
            start_engine();
            return;
        }
        res.send(stdout);
    });
});


/* Answer Question */
function answer_question() {
    var answerForm = document.getElementById("ragAnswer");
    if (answerForm.style.display === "none") {
        answerForm.style.display = "block";
    } 
};
/* data Response block */
function data_response() {
    var answerForm = document.getElementById("dataResponse");
    if (answerForm.style.display === "none") {
        answerForm.style.display = "block";
    } 
};
/* Starting Engine Block */
function start_engine() {
    var answerForm = document.getElementById("engineResponse");
    if (answerForm.style.display === "none") {
        answerForm.style.display = "block";
    } 
};

function do_something(){
    //do something
    return;
};

// Start the server
app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});