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