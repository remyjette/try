$(function() {
  var summaryDiv = $("#summary");
  var resultsDiv = $("#results");

  $("#submit").on("click", function() {
    summaryDiv.html("");
    resultsDiv.html("");
    var formData = new FormData();
    formData.append('test-file', $('#test-file')[0].files[0]);

    $.ajax({
      url : 'test/',
      type : 'POST',
      data : formData,
      processData: false,  // tell jQuery not to process the data
      contentType: false,
      success : function(data) {
        var results = JSON.parse(data);
        var totalPassed = results.reduce(function(acc, result) {return acc + (result.passed ? 1 : 0);}, 0);
        summaryDiv.html("Tests Passed: " + totalPassed + "/" + results.length);
        results.forEach(function (result) {
          var resultDiv = $("<div>");
          resultDiv.addClass("test_result").addClass(result.passed ? "passed" : "failed");
          resultDiv.append("<p class='test_name'>Test Name: " + result.name + "</p>");
          if (!result.passed) {
            resultDiv.append("<p>Error Message: <pre>" + result.message + "</pre></p>");
            //resultDiv.append("<p>Error Message: " + result.message.replace(/\n/g, "<br />") + "</p>")
          }
          resultsDiv.append(resultDiv);
        });
      }
    });
  });
});
