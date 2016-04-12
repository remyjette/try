$(function() {
  var resultsDiv = $("#results");

  $("#submit").on("click", function() {
    resultsDiv.html("");
    var formData = new FormData();
    formData.append('submission', $('#submission')[0].files[0]);

    $.ajax({
      url : 'test/',
      type : 'POST',
      data : formData,
      processData: false,  // tell jQuery not to process the data
      contentType: false,
      success : function(data) {
        var response = JSON.parse(data);
        if (response.error !== undefined) {
          var summaryDiv = $("<div>")
            .addClass("test_summary")
            .html(response.error);
            resultsDiv.append(summaryDiv);
          return;
        }
        _.each(response, function (results, testfile_name) {
          var totalPassed = results.reduce(function(acc, result) {return acc + (result.passed ? 1 : 0);}, 0);
          var summaryDiv = $("<div>")
            .addClass("test_summary")
            .html("Tests Passed: " + totalPassed + "/" + results.length);
          resultsDiv.append(summaryDiv);

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
      }
    });
  });
});
