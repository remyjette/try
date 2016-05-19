

$(function () {
  responseDiv = $("#grade_all_response");

  function generateSummary(list, max) {
    var container = $("<div>");

    var summaryDiv = $("<div class='summary'>");
    var createSummaryLine = function(label, value) {
      return "<tr><td>" + label + ":</td><td>" + (+value.toFixed(2)) + "</td></tr>";
    }
    summaryTable = $("<table>");
    summaryTable.append(createSummaryLine("Max Possible", max));
    summaryTable.append(createSummaryLine("Max", d3.max(list)));
    summaryTable.append(createSummaryLine("Min", d3.min(list)));
    summaryTable.append(createSummaryLine("Mean", d3.mean(list)));
    summaryTable.append(createSummaryLine("Median", d3.median(list)));
    summaryTable.append(createSummaryLine("Std. Dev.", d3.deviation(list)));
    summaryDiv.append(summaryTable);

    var histogramDiv = $("<div>").css("display", "inline-block");
    plotHistogram(histogramDiv.get(0), list, 10, max);

    container.append(summaryDiv);
    container.append(histogramDiv);
    return container;
  }

  $("#grade_all_button").on("click", function () {
    var file = $("#grade_all_zip");
    var formData = new FormData();
    formData.append('submissions', file.get(0).files[0]);

    responseDiv.html("<h1>Calculating grades . . .</h1>");

    $.ajax({
      url: 'grade/',
      type: 'POST',
      data: formData,
      processData: false,
      contentType: false,
      success: function(data) {
        responseDiv.html("")
          .append("<h1>Grading complete!</h1>")
          .append("<h2><a href='grade/" + data.csv_id + "'>Download Results</a></h2>");
        var totalScores = data.results.map(function (result) {
          return _.chain(result)
            .omit("_error_types")
            .values()
            .reduce(function (x, y) { return x+y})
            .value();
        });

        var errorCounts = _.chain(data.results)
          .pluck("_error_types")
          .flatten()
          .groupBy(function (x) {return x})
          .mapObject(function (x) {return x.length})
          .value();

        responseDiv.append("<h2>Error Counts:<h2>");
        for (var errorType in errorCounts) {
          if (errorCounts.hasOwnProperty(errorType)) {
            responseDiv.append("<h3>" + errorType + ": " + errorCounts[errorType] + "</h3><br /><br />");
          }
        }
        responseDiv.append("<h1>Summary</h1>")
          .append(generateSummary(totalScores, data.max_score));

        if (data.problems_max) {
          var problems = _(data.problems_max).keys();
          var resultsByProblem = _(_.object(problems, problems)).mapObject(function (problem) {
            return _(data.results).pluck(problem);
          });
          _.each(problems, function (problem) {
            responseDiv.append("<h1>Problem: " + problem + "</h1>")
              .append(generateSummary(resultsByProblem[problem], data.problems_max[problem]));
          });
        }
      }
    });
  });
});

function plotHistogram(element, data, binCount, max) {
  if (data === undefined || data.length === undefined || data.length === 0) {
    //bad data. do nothing
    return;
  }

  //dimensions for the histogram
  var width = 450;
  var height = 300;
  var margin = 40;

  //Use d3.histogram() to divide our data into bins.
  var histogramFunction = d3.layout.histogram();
  histogramFunction.bins(binCount);
  var bins = histogramFunction(data);

  //Figure out the bin with the highest frequency so we know high the y-axis can
  //go, as that axis will represent the frequency
  var highest_frequency = d3.max(bins.map(bin => bin.y));

  var chart = d3.select(element).append("svg")
    .attr("width", width)
    .attr("height", height)
    .append("g")
    .attr("transform", "translate(" + margin + ", " + margin + ")");

  //Now that our chart area has been created and centered in the svg, modify
  //the width and height so we can use it below and know we won't run into the
  //margins
  width -= (margin * 2);
  height -= (margin * 2);

  //set up linear scales for x and y based on the bin objects
  var xScale = d3.scale.linear()
    .domain([d3.min(bins.map(bin => bin.x)), max || d3.max(bins.map(bin => bin.x + bin.dx))])
    .range([0, width]);

  var yScale = d3.scale.linear()
    .domain([0, highest_frequency])
    .range([height, 0]);

  //create the axes
  var xAxis = d3.svg.axis()
    .scale(xScale)
    .orient("bottom")
    .tickSize(3, 3);

  var yAxis = d3.svg.axis()
    .scale(yScale)
    .orient("left");

  //label our axes
  chart.append("g")
  .attr("transform", "translate(0," + height + ")")
  .attr("class", "axis")
  .call(xAxis)
  .append("text")
    .attr("x", width / 2 - margin / 2)
    .attr("y", 30)
    .text("Grade");

  chart.append("g")
  .attr("class", "axis")
  .call(yAxis)
  .append("text")
    .attr("x", -30)
    .attr("y", height / 2 + margin / 2)
    .attr("transform", "rotate(270, -30, " + (height / 2 + margin / 2) + ")")
    .text("Frequency");

  //iterate through the bins and create a rectangle for each to add it to the
  //svg chart
  bins.forEach(function (bin) {
    chart.append("rect")
      .attr("class", "bar")
      .attr("x", xScale(bin.x))
      .attr("y", yScale(bin.y))
      .attr("width", width / bins.length)
      .attr("height", yScale(0) - yScale(bin.y))
      .attr("fill", "skyblue")
      .attr("stroke", "navy")
      .attr("stroke-width", "2px");
  });
}
