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