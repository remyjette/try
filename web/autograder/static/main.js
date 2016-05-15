$(function() {
  var resultsDiv = $("#results");

  $("#submit").on("click", function() {
    resultsDiv.html("");
    var loadingMessage = $("<div>").addClass("test_summary").html("Running tests...");
    resultsDiv.append(loadingMessage);
    var formData = new FormData();
    formData.append('submission', $('#submission')[0].files[0]);

    $.ajax({
      url : 'test/',
      type : 'POST',
      data : formData,
      processData: false,  // tell jQuery not to process the data
      contentType: false,
      success : function(data) {
        resultsDiv.html("");
        var response = JSON.parse(data);
        if (response.error !== undefined) {
          var summaryDiv = $("<div>")
            .addClass("test_summary")
            .html(response.error);
            resultsDiv.append(summaryDiv);
          return;
        }
        _.each(response, function (test_response, testfile_name) {
          var summaryDiv = $("<div>")
            .addClass("test_summary");
          resultsDiv.append(summaryDiv);
          if (test_response.error) {
            summaryDiv.html("Test File " + testfile_name + ": " + test_response.error);
            var resultDiv = $("<div>");
            resultDiv.addClass("test_result").addClass("failed")
              .append("<p>Error Message: <pre>" + test_response.message + "</pre></p>");
            resultsDiv.append(resultDiv);
            return;
          }
          results = test_response.results;
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
        });
      },
      error: function(jqXHR, textStatus, errorThrown) {
        resultsDiv.html("");
        var resultDiv = $("<div>").addClass("failed").addClass("test_result");
        var message = "The following error occurred while trying to run your tests:"
          + "<br /><br />"
          + errorThrown
          + "<br /><br />This is a server error. Your code has not been run.";
        resultDiv.html(message);
        resultsDiv.html(resultDiv);
      }
    });
  });
});
