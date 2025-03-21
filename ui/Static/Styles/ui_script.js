/* Filename: script.js*/

/* event listener */
let 

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
