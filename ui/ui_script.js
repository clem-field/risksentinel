/* Filename: script.js*/

/* fetch data functions */

// $(document).ready(function() {
//     $("#fetch_data").click(function() {
//         $.ajax({
//             url: 'mitre_work/get_srg_stig.py',
//             type: 'GET',
//             success: function(data) {
//                 $("#output").html(data);
//             },
//             error: function(error) {
//                 $("#output").html('Error: ' + error.responseText);
//             }
//         });
//     });
// });
$.ajax({
    type: "POST",
    url: "mitre_work/get_srg_stig.py",
    data: { param: text}
  }).done(function( o ) {
     print('success')
  });
// fetch("mitre_work/get_srg_stig.py", {
//     method: 'POST',
//     headers: {
//         'Content-Type': 'application/json',
//     },
//     body: JSON.stringify({ param: paragraphText })
// })
// .then(response => response.json())
// .then(data => console.log(data));



/* select RAG engine */
const form = document.getElementById('start_rag');
form.addEventListener('submit', function(event)
    {
        event.preventDefault();
        const formData = {};
        new FormData(form).forEach((value, key) => {
            formData[key] = value;
        });
        const rag_engin = value;
        console.log('Engine:  ${rag_engin}');
    });


    /* start RAG */
    $(document).ready(function() {
        $("#start_rag").click(function() {
            $.ajax({
                url: 'mitre_work/setup_environment.py',
                type: 'GET',
                success: function(data) {
                    $("#output").html(data);
                },
                error: function(error) {
                    $("#output").html('Error: ' + error.responseText);
                }
            });
        });
    });

    /* Question from user */
    $(document).ready(function() {
        $("#run_rag").click(function() {
            $.ajax({
                url: 'mitre_work/run_rag.py',
                type: 'GET',
                success: function(data) {
                    $("#output").html(data);
                },
                error: function(error) {
                    $("#output").html('Error: ' + error.responseText);
                }
            });
        });
    });

