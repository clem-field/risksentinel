<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
<h1 style="color:blue">Setting Up for Local Development<h1>
<h1> Using Node.js</h1>
<p>
    More information about how Node.js works and how to construct it is available at <a href="https://www.geeksforgeeks.org/nodejs/">Geeks for Geeks Node.js</a>
<body>
    <h2>Set up base files </h2>
    <ol>
        <li>Create Node.js environment</li>
            <ol>
                <li>mkdir node-python-exec</li>
                <li>cd node-python-exec</li>
                <li>npm init -y</li>
                <li>npm install express child_process</li>
            </ol>
        <li>Create files</li>
            <ol>
                <li>server.js</li>
                <li>index.html</li>
                <li>script.py</li>
            </ol>
    </ol>    
    <br>
    <h2> Populate base files wit starter code </h2>
    <ol>
        <li>node.js</li>
            <p>
                const express = require("express");<br>
                const { exec } = require("child_process");<br>
                const path = require("path");<br>
                <br>
                const app = express();<br>
                const PORT = 3000;<br>
                <br>
                // Serve static files (HTML, CSS, JS)<br>
                app.use(express.static(path.join(__dirname, "public")));<br>
                <br>
                // Route to execute the Python script<br>
                app.get("/run-python", (req, res) => {<br>
                    exec("python3 script.py", (error, stdout, stderr) => {<br>
                        if (error) {<br>
                            console.error(`Error executing Python script: ${error}`);<br>
                            res.status(500).send(`Error: ${error.message}`);<br>
                            return;<br>
                        }<br>
                        if (stderr) {<br>
                            console.error(`Python script stderr: ${stderr}`);<br>
                            res.status(500).send(`Error: ${stderr}`);<br>
                            return; <br>
                        }<br>
                        res.send(stdout);<br>
                    });<br>
                });<br>
                <br>
                // Start the server
                app.listen(PORT, () => {<br>
                    console.log(`Server running at http://localhost:${PORT}`);<br>
                });<br>
            </p>
        <li>script.py</li>
            <p>
                import datetime<br>
                <br>
                print("Python script executed successfully!")<br>
                print(f"Current Time: {datetime.datetime.now()}")<br>
            </p>
        <li>public/index.html</li>
            <p>
                <!DOCTYPE html><br>
                <html lang="en"><br>
                <head><br>
                    <meta charset="UTF-8"><br>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0"><br>
                    <title>Run Python Script</title><br>
                </head><br>
                <body><br>
                    <h2>Click the button to run the Python script:</h2><br>
                    <button id="runPython">Run Python</button><br>
                    <p id="output"></p><br>
                    <script><br>
                        document.getElementById("runPython").addEventListener("click", function () {<br>
                            fetch("/run-python")<br>
                                .then(response => response.text())<br>
                                .then(data => {<br>
                                    document.getElementById("output").innerText = data;<br>
                                })<br>
                                .catch(error => {<br>
                                    document.getElementById("output").innerText = "Error: " + error;<br>
                                });<br>
                        });<br>
                    </script><br>
                </body><br>
                </html><br>
            </p>
    </ol>
    <h2>How to run</h2>
        <ol>
            <li>cd to risksentinel/node-python-exec</li>
            <li>run \. "$HOME/.nvm/nvm.sh"</li>
            <li>run node server.js</li>
            <li>browser navigation to http://localhost:3000</li>
            <li>click the "run python" button and follow output</li>
        </ol>
    <h2>How It Works</h2>
        <ol>
            <li>The index.html has a button that triggers a fetch request to /run-python.</li>
            <li>The Node.js server.js receives the request and executes script.py using exec().</li>
            <li>The output from the Python script is sent back to the frontend and displayed.</li>
        </ol>
    <h2>How to add features</h2>
        <ol>
            <li>add python script to node-python-exec/*</li>
            <li>Add function to node-python-exec/server.js</li>
            <li>Add function to node-python-exec/node.js</li>
            <li>Add call to function in public/index.html</li>
            <li>test function while running Node.js</li>
        </ol>
<body>
</html>